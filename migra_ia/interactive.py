"""Demo interactiva: el motor real operado por el usuario, sin API ni clave.

Es el unico modo de demostracion del artefacto. No imita al agente
conversacional -eso solo puede hacerlo el modelo-, sino que expone la parte
DETERMINISTA del agente y la pone a trabajar con los datos de quien la ejecuta,
sin caso grabado de por medio:

  - el equipo se identifica contra el catalogo verificado (`fabricantes.py`);
  - las preguntas, sus opciones y sus ramas adaptativas salen del cuestionario
    maestro (`data/es/questionnaire.json`), no se escriben aqui;
  - la puntuacion de riesgo la calcula el motor real (`scoring.py`) a partir de
    las respuestas dadas, con una justificacion que cita los codigos usados;
  - la alternativa recomendada aplica el mapa de decision del cuestionario;
  - si procede migrar, el procedimiento de 50 pasos (`procedimiento.py`) guia
    con la CPU destino que el usuario elige.

Lo unico que no puede hacer sin el modelo es conversar en lenguaje libre, y lo
dice de forma explicita en lugar de fingirlo. A cambio es reproducible: el mismo
caso da el mismo resultado siempre, que es lo que necesita una evaluacion de
artefacto.

Las reglas de puntuacion no son una invencion de este modulo: cada factor sigue
la `guia` que el propio `mapa_decision` publica para el, y cada puntuacion viaja
con la justificacion y los codigos de pregunta que la sustentan.
"""

from __future__ import annotations

from .case import Case
from .tools import run_tool
from .core import pending_approver
from . import questionnaire, manufacturers, procedure, scoring


def T(key: str) -> str:
    """Texto de la demo en el idioma de esta peticion.

    La demo interactiva no pasa por el modelo: este modulo escribe su texto, asi
    que tambien es contenido y vive en data/<idioma>/interactive.json.
    """
    from . import config
    return config.interactive_text().get(key, key)


def C(key: str) -> tuple:
    """Palabras que el usuario puede teclear para un mando, en su idioma."""
    return tuple(s.strip().lower() for s in T(key).split(","))



CITA = "Cuestionario maestro MIGRA-IA (Secciones A-Q)"

# Fases de la sesion interactiva.
F_EQUIPO = "equipo"
F_PREGUNTAS = "questions"
F_RISK = "risk"
F_DECISION = "decision"
F_TARGET = "destino"
F_GUIDE = "guide"
F_FIN = "fin"

def _unknown_values():
    return {T("i035"), T("i036"), T("i037"),
                T("i038"), T("i039")}


def _is_unknown(value) -> bool:
    return str(value or "").strip().lower() in _unknown_values()


# --------------------------------------------------------------------------- #
# Guion de preguntas: solo las que alimentan los 8 factores y la decision
# --------------------------------------------------------------------------- #
# Cada entrada es (codigo, condicion). `condicion` recibe las respuestas dadas y
# decide si la pregunta procede: asi se respetan las ramas adaptativas del
# cuestionario (Seccion 3.1) en vez de preguntarlo todo siempre.
GUION: list[tuple[str, object]] = [
    ("C08", None), ("C10", None), ("Q04", None),
    ("M01", None), ("M04", None), ("M06", None), ("M09", None), ("M07", None),
    ("F01", None),
    ("F06", lambda r: r.get("F01") == T("yes")),
    ("F07", lambda r: r.get("F01") == T("yes")),
    ("F12", lambda r: r.get("F01") in (T("no"), T("i098"))),
    ("F13", lambda r: r.get("F01") in (T("no"), T("i099"))),
    ("N02", None), ("N03", None), ("N05", None), ("N06", None),
    ("G01", None), ("O07", None), ("O08", None), ("O02", None),
    ("L01", None), ("L03", None), ("L07", None),
    ("P01", None), ("P04", None),
]

# Preguntas de rama que el cuestionario declara sin opciones: son de si/no y se
# presentan con las opciones estandar, sin inventarles texto.
def _yes_no_options():
    return [T("yes"), T("no"), T("i040")]


def _question(code: str) -> dict | None:
    p = questionnaire.question(code)
    if p is None:
        return None
    p = dict(p)
    if not p.get("options") and p.get("type") not in ("numero", "text"):
        p["options"] = list(_yes_no_options())
    return p


def _pending(answers: dict) -> list[str]:
    """Codigos que faltan por preguntar, respetando las ramas adaptativas."""
    faltan = []
    for code, condition in GUION:
        if code in answers:
            continue
        if condition is not None and not condition(answers):
            continue
        if _question(code) is None:
            continue
        faltan.append(code)
    return faltan


# --------------------------------------------------------------------------- #
# Reglas de puntuacion, una por factor, segun la guia del mapa de decision
# --------------------------------------------------------------------------- #
def _span(value, escala: list[str]) -> int | None:
    """Posicion de una respuesta dentro de una escala ordenada."""
    v = str(value or "").strip().lower()
    for i, op in enumerate(escala):
        if v == op.lower():
            return i
    return None


def _cap(value: float) -> float:
    return float(max(0, min(100, round(value, 1))))


def _f_lifecycle(r: dict) -> dict | None:
    m01 = r.get("M01")
    tabla = {
        "Activo, en comercializacion": 10,
        "En madurez, ya existe un sucesor": 30,
        "Anuncio de descontinuacion (phase-out)": 55,
        "Descontinuado, aun con soporte y repuestos": 75,
        "Descontinuado y sin soporte (fin de vida)": 95,
    }
    if m01 not in tabla:
        # La guia lo dice expresamente: si M01 no se conoce, se OMITE el factor
        # y se registra el dato faltante, en lugar de suponer un estado.
        return None
    return {"value": tabla[m01],
            "justificacion": f"{T('i001')}{m01}'."}


def _f_spare_parts(r: dict) -> dict | None:
    m04, m06, c10 = r.get("M04"), r.get("M06"), r.get("C10")
    base = {"Si, sin problema": 10, "Si, pero con plazo largo": 45,
            "Solo por pedido especial": 65, "No": 95}.get(m04)
    if base is None and _is_unknown(m06):
        return None
    if base is None:
        base = 50
    partes = [f"M04: '{m04}'."]
    # La guia exige contrastar el plazo de entrega con la parada tolerable: un
    # repuesto que llega despues de lo que la planta aguanta no cubre el riesgo.
    escala_m06 = [T("i041"), T("i042"),
                  T("i043"), T("i044"), T("i045")]
    escala_c10 = [T("i046"), "1 a 4 horas", "4 a 12 horas",
                  "12 a 24 horas", T("i047")]
    rm, rc = _span(m06, escala_m06), _span(c10, escala_c10)
    if rm is not None and rc is not None and rm >= 2:
        base = max(base, 85)
        partes.append(f"M06 '{m06}' frente a C10 '{c10}{T('i002')}")
    elif rm is not None:
        partes.append(f"M06: '{m06}'.")
    return {"value": _cap(base), "justificacion": " ".join(partes)}


def _f_support(r: dict) -> dict | None:
    m09, m07 = r.get("M09"), r.get("M07")
    base = {"Si, vigente": 10, "Vencido": 60, "No": 85}.get(m09)
    if base is None and _is_unknown(m07):
        return None
    if base is None:
        base = 55
    ajuste = {"Si, del fabricante": -15, "Si, de tercero certificado": -5,
              "Si, de tercero sin certificar": 5, "No": 15}.get(m07, 0)
    return {"value": _cap(base + ajuste),
            "justificacion": f"{T('i003')}{m09}{T('i004')}{m07}'."}


def _f_software(r: dict) -> dict | None:
    n02, n03, n05, n06 = r.get("N02"), r.get("N03"), r.get("N05"), r.get("N06")
    if all(x is None for x in (n02, n03, n05, n06)):
        return None
    value = 20.0
    partes = []
    so = {"Windows XP": 25, "Windows 7": 20, "Windows 10": 0, "Windows 11": 0,
          "Linux": 0, "Maquina virtual sobre un equipo moderno": 0}.get(n02, 10)
    if so:
        partes.append(f"N02 sistema operativo '{n02}'")
    value += so
    lic = {"Original con licencia vigente": 0, "Original con licencia vencida": 15,
           "Licencia flotante en servidor": 5, "Llave fisica (dongle)": 15,
           "Version de demostracion o limitada": 20, "No se tiene licencia": 30}.get(n03, 10)
    if lic:
        partes.append(f"N03 licencia '{n03}'")
    value += lic
    ada = {"Si, ya probado con este PLC": 0, "Si, pero sin probar": 10, "No": 25}.get(n05, 10)
    if ada:
        partes.append(f"N05 adaptador '{n05}'")
    value += ada
    pwd = {"Si, todas": 0, "Parcialmente": 15, "No": 30, "No hay contrasenas": 0}.get(n06, 15)
    if pwd:
        partes.append(f"N06 contrasenas '{n06}'")
    value += pwd
    return {"value": _cap(value),
            "justificacion": T("i081") + "; ".join(partes) + "."}


def _f_backup(r: dict) -> dict | None:
    f01 = r.get("F01")
    if f01 is None:
        return None
    if f01 == T("no"):
        return {"value": 100.0,
                "justificacion": T("i057")}
    if _is_unknown(f01):
        return {"value": 90.0,
                "justificacion": T("i058")}
    abre, compila = r.get("F06"), r.get("F07")
    if abre == T("no"):
        return {"value": 100.0,
                "justificacion": T("i059")}
    if compila == T("no"):
        return {"value": 90.0,
                "justificacion": T("i060")}
    if abre == T("yes") and compila == T("yes"):
        return {"value": 15.0,
                "justificacion": "F01, F06 y F07: existe copia, abre y compila. "
                                 "Respaldo verificado."}
    return {"value": 70.0,
            "justificacion": f"{T('i005')}{abre}', F07='{compila}{T('i006')}"}


_REDES_LEGADO = {"mpi", "profibus dp", "profibus pa", "devicenet", "controlnet",
                 "cc-link", "as-interface", "rs-232", "rs-485"}


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return value
    return [p.strip() for p in str(value or "").split(",") if p.strip()]


def _f_compatibility(r: dict) -> dict | None:
    g01, o07, o08, o02 = r.get("G01"), r.get("O07"), r.get("O08"), r.get("O02")
    if all(x is None for x in (g01, o07, o08, o02)):
        return None
    value = 20.0
    partes = []
    redes = [x.lower() for x in _as_list(g01)]
    if any("propietaria" in x for x in redes):
        value += 30
        partes.append(T("i061"))
    elif any(x in _REDES_LEGADO for x in redes):
        value += 15
        partes.append(f"{T('i007')}{', '.join(_as_list(g01))})")
    languages = [x.lower() for x in _as_list(o07)]
    if any("propietarios" in x for x in languages):
        value += 20
        partes.append(T("i062"))
    if any(("awl" in x or "stl" in x or "instrucciones" in x) for x in languages):
        value += 15
        partes.append(T("i063"))
    if any(("grafcet" in x or "sfc" in x or "graph" in x) for x in languages):
        value += 10
        partes.append("O07 incluye GRAFCET/SFC")
    if o08 == T("yes"):
        value += 25
        partes.append("O08 usa librerias propietarias")
    if str(o02).strip().lower().startswith("si"):
        value += 20
        partes.append(T("i064"))
    if not partes:
        partes.append(T("i065"))
    return {"value": _cap(value),
            "justificacion": T("i082") + "; ".join(partes) + "."}


def _external_root_cause(r: dict) -> list[str]:
    """Indicios de que la falla NO es del controlador, sino de su entorno.

    Es la regla que mas cambia el diagnostico: la guia del factor exige buscarla
    ANTES de puntuar alto el historial, porque sustituir el PLC sin corregirla
    reproduce la falla en el equipo nuevo.
    """
    causas = []
    p01 = str(r.get("P01") or "")
    if p01 in ("Entre 40 y 50 C", "Mayor a 50 C"):
        causas.append(f"{T('i008')}{p01}'")
    energia = [x.lower() for x in _as_list(r.get("P04"))]
    if any("tierra dudosa" in x or "tierra dudosa o inexistente" in x for x in energia):
        causas.append("P04 puesta a tierra dudosa o inexistente")
    if any("variaciones" in x or "armonicos" in x or "cortes" in x for x in energia):
        causas.append(T("i066"))
    if r.get("L07") == T("yes"):
        causas.append(T("i067"))
    return causas


def _f_history(r: dict) -> dict | None:
    l01, l03 = r.get("L01"), r.get("L03")
    if l01 is None and l03 is None:
        return None
    try:
        paros = int(str(l01).strip())
    except (TypeError, ValueError):
        paros = None
    if paros is None:
        value = 45.0
        partes = [T("i068")]
    else:
        value = 10.0 if paros == 0 else 30.0 if paros <= 2 else 50.0 if paros <= 5 else 70.0
        partes = [f"L01 {paros}{T('i009')}"]
    value += {"En aumento": 20, "Estable": 0, "En disminucion": -10,
              "Sin fallas registradas": -15}.get(l03, 5)
    if l03:
        partes.append(f"L03 tendencia '{l03}'")
    causas = _external_root_cause(r)
    if causas:
        value = min(value, 55.0)
        partes.append(T("i100") + "; ".join(causas) +
                      T("i083"))
    return {"value": _cap(value), "justificacion": "; ".join(partes) + "."}


def _f_criticality(r: dict) -> dict | None:
    c08, c10, q04 = r.get("C08"), r.get("C10"), r.get("Q04")
    base = {"Baja: puede detenerse varios dias": 20,
            "Media: afecta parcialmente la produccion": 45,
            "Alta: afecta una linea importante": 70,
            "Critica: detiene la planta o presenta riesgo de seguridad": 95}.get(c08)
    if base is None:
        return None
    value = base + {"Menos de 1 hora": 20, "1 a 4 horas": 15, "4 a 12 horas": 10,
                    "12 a 24 horas": 5, "Mas de 24 horas": 0}.get(c10, 0)
    value += {"No hay ventana disponible": 15, "En el paro anual de planta o vacaciones": 10,
              "Fines de semana": 5}.get(q04, 0)
    return {"value": _cap(value),
            "justificacion": f"C08 criticidad '{c08}'; C10 parada tolerable '{c10}{T('i010')}{q04}'."}


REGLAS = {
    "estado_ciclo_vida": _f_lifecycle,
    "disponibilidad_repuestos": _f_spare_parts,
    "soporte_fabricante": _f_support,
    "disponibilidad_software": _f_software,
    "disponibilidad_respaldo": _f_backup,
    "compatibilidad_sistemas": _f_compatibility,
    "historial_fallas": _f_history,
    "criticidad_productiva": _f_criticality,
}


def factors(answers: dict) -> tuple[dict, list[str]]:
    """Traduce las respuestas a los 8 factores de `scoring.py`.

    Devuelve (factores, omitidos). Un factor sin datos suficientes se OMITE: el
    motor renormaliza los pesos y el hueco se declara como dato faltante, en
    lugar de rellenarlo con una suposicion.
    """
    calculados, omitidos = {}, []
    for key in scoring.WEIGHTS:
        regla = REGLAS.get(key)
        res = regla(answers) if regla else None
        if res is None:
            omitidos.append(key)
        else:
            calculados[key] = res
    return calculados, omitidos


# --------------------------------------------------------------------------- #
# Decision: que alternativa corresponde a este caso
# --------------------------------------------------------------------------- #
def _without_backup(r: dict) -> bool:
    if r.get("F01") == T("no") or _is_unknown(r.get("F01")):
        return True
    return r.get("F06") == T("no") or r.get("F07") == T("no")


def _unrecoverable_program(r: dict) -> bool:
    """Sin respaldo Y sin via para leerlo del PLC: la reconstruccion se impone."""
    return _without_backup(r) and (r.get("N06") == T("no") or r.get("F13") == T("no")
                                 or r.get("N05") == T("no"))


def decide(answers: dict, risk: dict) -> dict:
    """Aplica el mapa de decision del cuestionario a este caso concreto.

    No inventa criterios: para cada alternativa comprueba condiciones basadas en
    los mismos codigos que el mapa cita, y devuelve el texto de la alternativa
    tal como esta publicado en `data/es/questionnaire.json`.
    """
    mapa = questionnaire.load()["decision_map"]["alternative_criteria"]
    by_name = {a["alternative"]: a for a in mapa}

    order: list[tuple[str, str]] = []
    causas = _external_root_cause(answers)
    if causas:
        order.append((
            T("i084"),
            T("i119")
            + "; ".join(causas) + T("i101")))

    if _without_backup(answers):
        order.append((
            "Migracion a plataforma moderna" if not _unrecoverable_program(answers)
            else T("i102"),
            T("i103")
            + (T("i120")
               if _unrecoverable_program(answers)
               else T("i121"))))

    ciclo = answers.get("M01")
    plazo_insuficiente = (_span(answers.get("M06"),
                                 [T("i104"), T("i105"),
                                  T("i106"), T("i107"), T("i108")]) or 0) >= 2
    if ciclo in (T("i069"),
                 T("i070")):
        if plazo_insuficiente:
            order.append((
                "Migracion a plataforma moderna",
                f"M01 '{ciclo}{T('i011')}"))
        else:
            order.append((
                "Repuesto directo (mismo modelo)",
                f"M01 '{ciclo}{T('i012')}"))
    elif ciclo == "Anuncio de descontinuacion (phase-out)":
        order.append((
            "Hardware equivalente o sustitucion parcial",
            f"M01 '{ciclo}{T('i013')}"))
    elif ciclo in ("Activo, en comercializacion", T("i109")):
        order.append((
            T("i122"),
            f"M01 '{ciclo}{T('i014')}"))

    if answers.get("Q04") == "No hay ventana disponible":
        order.append((
            "Operacion temporal controlada",
            T("i085")))

    # Sin duplicar alternativas, conservando el orden de prioridad.
    vistas, path = set(), []
    for name, porque in order:
        if name in vistas or name not in by_name:
            continue
        vistas.add(name)
        path.append({**by_name[name], "porque_en_este_caso": porque})
    return {
        "classification": risk.get("classification"),
        "puntuacion": risk.get("puntuacion"),
        "route": path,
        "migrar": any(a["alternative"] in ("Migracion a plataforma moderna",
                                           T("i123")) for a in path),
        "sin_respaldo": _without_backup(answers),
        "irrecuperable": _unrecoverable_program(answers),
    }


# --------------------------------------------------------------------------- #
# Presentacion y lectura de respuestas
# --------------------------------------------------------------------------- #
def _render_question(p: dict, n: int, total: int) -> str:
    cabecera = (f"**Pregunta {n} de {total}** · Seccion {p['section']} — "
                f"{p['seccion_titulo']}  ·  `{p['code']}`")
    lineas = [cabecera, "", f"**{p['text']}**", ""]
    kind = p.get("type")
    if kind == "numero":
        lineas.append(T("i071"))
    elif kind in ("text",):
        lineas.append(T("i086"))
    else:
        for i, op in enumerate(p.get("options") or [], 1):
            lineas.append(f"{i}. {op}")
        lineas.append("")
        if kind == "seleccion_multiple":
            lineas.append(T("i110"))
        else:
            lineas.append(T("i111"))
    if p.get("adaptive_rule"):
        lineas += ["", f"*{p['adaptive_rule']}*"]
    return "\n".join(lineas)


def _interpret(p: dict, text: str):
    """Convierte lo escrito en el valor de la respuesta, o None si no se entiende."""
    t = (text or "").strip()
    if not t:
        return None
    kind = p.get("type")
    options = p.get("options") or []

    if kind == "numero":
        limpio = t.replace(",", ".").split()[0]
        try:
            return str(int(float(limpio)))
        except ValueError:
            return None
    if kind == "texto" or not options:
        return t

    def single(fragment: str):
        f = fragment.strip()
        if not f:
            return None
        if f.isdigit():
            i = int(f)
            return options[i - 1] if 1 <= i <= len(options) else None
        bajo = f.lower()
        for op in options:
            if op.lower() == bajo:
                return op
        # Coincidencia parcial: solo si es inequivoca, para no elegir por el usuario.
        parciales = [op for op in options if bajo in op.lower()]
        return parciales[0] if len(parciales) == 1 else None

    if kind == "seleccion_multiple":
        elegidas = [single(f) for f in t.split(",")]
        elegidas = [e for e in elegidas if e]
        return elegidas or None
    return single(t)


def _save(case: Case, p: dict, value) -> None:
    value_text = ", ".join(value) if isinstance(value, list) else str(value)
    run_tool(case, "save_answers", {"answers": [{
        "section": p["section"],
        "code": p["code"],
        "question": p["text"],
        "value": value_text,
        "confidence_level": "no_determinado" if _is_unknown(value_text) else "confianza_media",
        "source": T("i112"),
    }]}, pending_approver)


def _output(text: str, case: Case, status: dict, actions=None, fin=False) -> dict:
    return {"text": text, "acciones": actions or [], "resumen": case.summary(),
            "fin": fin, "interactivo": True, "status": status}


# --------------------------------------------------------------------------- #
# Fases
# --------------------------------------------------------------------------- #
def start() -> dict:
    """Texto de apertura y estado inicial de la sesion interactiva."""
    total = len([c for c, _ in GUION if _question(c)])
    return {
        "text": (
            f"{T('i015')}{total}{T('i016')}"
        ),
        "status": {"phase": F_EQUIPO, "answers": {}},
    }


def _phase_equipment(case: Case, text: str, status: dict) -> dict:
    ident = manufacturers.identify(text)
    catalogado = ident["status"] in ("modelo_exacto", "family", "brand")
    status["intento_equipo"] = True
    if not catalogado:
        parecidas = manufacturers.suggestions(text, limite=5)
        cuerpo = (f"{T('i017')}{text.strip()}{T('i018')}")
        if parecidas:
            cuerpo += T("i087") + "\n".join(
                f"{i}. **{s['brand']} {s['family']}** — {s['modelos_documentados']}"
                for i, s in enumerate(parecidas, 1))
            cuerpo += (T("i072"))
            status["sugerencias"] = [f"{s['brand']} {s['family']}" for s in parecidas]
        else:
            cuerpo += (T("i073"))
        return _output(cuerpo, case, status)

    case.set_equipment(ident)
    actions = ["identify_cpu"]
    run_tool(case, "register_asset", {
        "type": "cpu",
        "description": f"CPU {ident.get('modelo_identificado') or ident.get('family') or text.strip()}",
        "manufacturer": ident.get("brand") or "",
        "model": ident.get("modelo_identificado") or "",
        "confidence_level": "confianza_media",
        "notes": f"{T('i019')}{text.strip()}'.",
    }, pending_approver)
    actions.append("register_asset")

    status["phase"] = F_PREGUNTAS
    status["ctx"] = {"brand": ident.get("brand"), "family": ident.get("family"),
                     "model": ident.get("modelo_identificado"),
                     "label": f"{ident.get('brand')} {ident.get('family') or ''}".strip()}
    cabeza = manufacturers.anchor(ident)
    next_step = _next_question(status)
    return _output(cabeza + "\n\n---\n\n" + next_step, case, status, actions)


def _next_question(status: dict) -> str:
    faltan = _pending(status["answers"])
    if not faltan:
        return ""
    code = faltan[0]
    status["actual"] = code
    p = _question(code)
    hechas = len(status["answers"])
    return _render_question(p, hechas + 1, hechas + len(faltan))


def _phase_questions(case: Case, text: str, status: dict) -> dict:
    code = status.get("actual")
    p = _question(code) if code else None
    if p is None:
        status["phase"] = F_RISK
        return _phase_risk(case, status)

    value = _interpret(p, text)
    if value is None:
        return _output(
            T("i088") + _render_question(p, len(status["answers"]) + 1,
                                                            len(status["answers"]) + len(_pending(status["answers"]))),
            case, status)

    status["answers"][code] = value
    _save(case, p, value)

    next_step = _next_question(status)
    if not next_step:
        status["phase"] = F_RISK
        return _phase_risk(case, status, actions=["save_answers"])
    eco = ", ".join(value) if isinstance(value, list) else value
    return _output(f"Anotado — `{code}`: **{eco}**\n\n---\n\n{next_step}",
                   case, status, ["save_answers"])


def _phase_risk(case: Case, status: dict, actions=None) -> dict:
    answers = status["answers"]
    calculados, omitidos = factors(answers)
    actions = list(actions or [])

    for key in omitidos:
        run_tool(case, "register_missing_data", {
            "description": f"Factor '{scoring.factor_labels().get(key, key)}{T('i020')}",
            "impacto": T("i089"),
        }, pending_approver)
        actions.append("register_missing_data")

    tool_output = run_tool(case, "compute_obsolescence_risk",
                                       {"factors": calculados}, pending_approver)
    actions.append("compute_obsolescence_risk")
    risk = case.risk or {}
    status["risk"] = {"puntuacion": risk.get("puntuacion"),
                        "classification": risk.get("classification")}

    filas = "\n".join(
        f"| {d['factor']} | {d['peso']:.2f} | {d['value']:.0f} | {d['justificacion']} |"
        for d in risk.get("detalle_factores", []))
    text = (
        f"{T('i021')}{risk.get('puntuacion')} / 100 — {risk.get('classification')}{T('i022')}" + filas
    )
    if omitidos:
        text += (T("i090")
                  + ", ".join(scoring.factor_labels().get(o, o) for o in omitidos)
                  + T("i074"))
    status["phase"] = F_DECISION
    return _output(text + T("i075"), case, status, actions)


def _phase_decision(case: Case, status: dict) -> dict:
    decision = decide(status["answers"], status.get("risk") or {})
    status["decision"] = decision

    partes = [T("i048"),
              T("i049")]
    for i, alt in enumerate(decision["route"], 1):
        partes.append(f"### {i}. {alt['alternative']}")
        partes.append(f"{T('i023')}{alt['porque_en_este_caso']}")
        if alt.get("advertencias"):
            partes.append("**Advertencias:**")
            partes += [f"- {a}" for a in alt["advertencias"]]
        partes.append("")
    if not decision["route"]:
        partes.append(T("i076"))

    if decision["migrar"]:
        actions = []
        trigger = ("sin_acceso_al_programa" if decision["irrecuperable"]
                      else "cpu_obsoleta")
        run_tool(case, "start_migration_guide", {
            "trigger": trigger,
            "motivo": T("i091"),
            "decidido_por": "sugerencia_del_agente_aceptada",
            "sin_respaldo": decision["sin_respaldo"],
        }, pending_approver)
        actions.append("start_migration_guide")
        status["phase"] = F_TARGET
        partes.append("---\n")
        partes.append(T("i077"))
        return _output("\n".join(partes), case, status, actions)

    status["phase"] = F_FIN
    partes.append("---\n")
    partes.append(T("i050"))
    return _output("\n".join(partes), case, status)


def _target_source(target: str, familias: list[dict], path: dict) -> str:
    """URL oficial de la familia destino, no la de cualquier familia vigente.

    Un fabricante puede tener varias generaciones actuales (Siemens tiene S7-1200
    y S7-1500). Tomar la primera de la lista citaria una fuente que no
    corresponde al destino elegido, que es peor que no citar ninguna.
    """
    objetivo = set(_norm_tokens(target))
    best, mejor_peso = "", 0
    for fam in familias:
        comunes = objetivo & set(_norm_tokens(fam.get("family", "")))
        peso = len(comunes)
        if peso > mejor_peso:
            fuentes = [f.get("url", "") for f in (fam.get("sources") or []) if f.get("url")]
            if fuentes:
                best, mejor_peso = fuentes[0], peso
    if best:
        return best
    # Sin coincidencia clara no se inventa una URL: se cita la guia metodologica.
    return path.get("citation", "")


def _norm_tokens(text: str) -> list[str]:
    limpio = "".join(c.lower() if c.isalnum() else " " for c in str(text or ""))
    return [t for t in limpio.split() if len(t) >= 2]


def _phase_target(case: Case, text: str, status: dict) -> dict:
    ident = case.equipment_identified or {}
    if not status.get("opciones_mostradas"):
        status["opciones_mostradas"] = True
        options = procedure.target_options(ident, limite_alternativas=8)
        status["alternatives"] = [a["brand"] for a in
                                 (options.get("marca_alternativa", {}).get("mostradas") or [])]
        return _output(
            procedure.options_text(ident, limite_alternativas=8)
            + f"{T('i024')}{ident.get('brand')}{T('i025')}",
            case, status)

    choice = (text or "").strip()
    bajo = choice.lower()
    options = procedure.target_options(ident, limite_alternativas=30)
    misma = options.get("misma_marca", {})

    if bajo.startswith("a"):
        familias = misma.get("familias_actuales") or []
        path = misma.get("ruta_publicada_para_el_origen") or {}
        target = path.get("destino") or (familias[0]["family"] if familias else "")
        source = _target_source(target, familias, path)
        target_brand = ident.get("brand")
        justification = (T("i051"))
    elif bajo.startswith("b"):
        pedida = choice[1:].strip(" .:-")
        todas = (options.get("marca_alternativa", {}).get("mostradas") or [])
        elegida = None
        for a in todas:
            if pedida and pedida.lower() in a["brand"].lower():
                elegida = a
                break
        if elegida is None:
            return _output(
                f"{T('i026')}{ident.get('brand')}**.", case, status)
        fam = elegida["familias_actuales"][0]
        target_brand, target = elegida["brand"], fam["family"]
        source = (fam.get("sources") or [{}])[0].get("url", "")
        porte = procedure.context(case).get("con_codigo_fuente")
        justification = (
            T("i092")
            + (T("i113")
               if porte else
               T("i114")))
    else:
        return _output(T("i093"), case, status)

    run_tool(case, "set_target_cpu", {
        "brand": target_brand, "family": target,
        "justificacion": justification, "source": source,
    }, pending_approver)

    cambio = (case.migration or {}).get("cambio_marca")
    with_code = procedure.context(case).get("con_codigo_fuente")
    status["phase"] = F_GUIDE
    # Cambiar de marca no significa lo mismo con el programa de origen en la mano que
    # sin el: en el primer caso hay especificacion de la que partir y en el segundo no.
    if cambio and with_code:
        aviso = (
            T("i052")
        )
    elif cambio:
        aviso = (
            T("i078")
        )
    else:
        aviso = (
            T("i079")
        )
    # Si la marca tiene ruta de conversion publicada, se anuncia aqui: es el momento
    # en que el usuario decide, y saber que la herramienta existe cambia la decision.
    route_summary = procedure.route_summary_text(case)
    if route_summary:
        aviso += "\n\n" + route_summary
    return _output(
        f"Destino fijado: **{target_brand} {target}**.\n\n{aviso}{T('i027')}",
        case, status, ["set_target_cpu"])


def _phase_guide(case: Case, text: str, status: dict) -> dict:
    ctx = procedure.context(case)
    t = (text or "").strip().lower()
    actual = status.get("paso_guia")

    if actual and t in C("cmd_done"):
        run_tool(case, "mark_migration_step",
                             {"step": actual, "status": "completado",
                              "note": T("i094")},
                             pending_approver)
    elif actual and t in C("cmd_na"):
        run_tool(case, "mark_migration_step",
                             {"step": actual, "status": "no_aplica",
                              "note": T("i116")},
                             pending_approver)
    elif actual and t in C("cmd_blocked"):
        run_tool(case, "mark_migration_step",
                             {"step": actual, "status": "bloqueado",
                              "note": T("i125")},
                             pending_approver)
    elif actual and t in C("cmd_report"):
        status["phase"] = F_FIN
        return _phase_end(case, status)

    next_step = procedure.next_step(case)
    if next_step is None:
        status["phase"] = F_FIN
        return _phase_end(case, status)

    status["paso_guia"] = next_step["key"]
    avance = procedure.status(case)
    cuerpo = procedure.step_text(next_step["key"], ctx)
    # Los pasos que la ruta del caso especializa se muestran con sus sub-pasos
    # concretos: 13, 20, 21, 22 y 23 con la ruta Siemens; 11, 12, 18, 21 y 32 con la
    # ruta de cambio de marca. El resto queda igual que siempre.
    cuerpo += procedure.route_for_step_text(next_step["key"], case, ctx)
    if next_step.get("prerrequisitos_pendientes"):
        cuerpo += (T("i095")                 + ", ".join(str(x) for x in next_step["prerrequisitos_pendientes"])
                   + T("i080"))
    pie = (f"\n\n---\n\n*Avance: {avance['cerrados']} de {avance['total_steps']} ({avance['porcentaje']}%) · fase {avance['fase_actual']}{T('i028')}")
    return _output(cuerpo + pie, case, status, ["mark_migration_step"] if actual else [])


def _phase_end(case: Case, status: dict) -> dict:
    ident = case.equipment_identified or {}
    risk = case.risk or {}
    decision = status.get("decision") or {}
    mig = case.migration or {}
    target = (mig.get("destino") or {})
    summary = case.summary()

    path = "\n".join(f"{i}. **{a['alternative']}** — {a['porque_en_este_caso']}"
                     for i, a in enumerate(decision.get("route", []), 1)) or T("i053")
    detail = "\n".join(f"- {d['factor']} (peso {d['peso']:.2f}): {d['value']:.0f} — "
                        f"{d['justificacion']}"
                        for d in risk.get("detalle_factores", []))
    equipo = f"{ident.get('brand')} {ident.get('family') or ''}".strip() or T("i054")

    cuerpo = (
        f"## 1. Identificacion\nCaso interactivo. {equipo}"
        + (f" ({ident.get('modelo_identificado')})" if ident.get("modelo_identificado") else "")
        + f"{T('i029')}{len(summary['respuestas_registradas'])} respuestas registradas: {', '.join(summary['respuestas_registradas'])}{T('i030')}"
        + ("\n".join(f"- {d}" for d in summary["missing_data"]) or "Ninguno registrado.")
        + f"{T('i031')}{risk.get('puntuacion')} / 100 — **{risk.get('classification')}**.\n\n{detail}{T('i032')}{path}\n\n## 9. Recomendacion principal\n"
        + (f"Migrar a **{target.get('brand')} {target.get('family')}**"
           + ((T("i128")
                if procedure.context(case).get("con_codigo_fuente") else
                T("i129"))
              if mig.get("cambio_marca") else T("i127"))
           if target else T("i126"))
        + T("i096")
        + (f"Procedimiento MIGRA-IA-PROC-050, avance {procedure.status(case)['cerrados']} de {procedure.total_steps()}{T('i033')}"
           if mig.get("activa") else T("i097"))
        + T("i055")
    )
    run_tool(case, "generate_report", {
        "title": f"Diagnostico interactivo — {equipo}",
        "nivel_confianza_global": "confianza_media",
        "resumen": f"{risk.get('classification')}{T('i034')}",
        "cuerpo_markdown": cuerpo,
    }, pending_approver)

    status["phase"] = F_FIN
    return _output(
        T("i056"),
        case, status, ["generate_report"], fin=True)


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def answer(case: Case, text: str, status: dict | None) -> dict:
    """Avanza la sesion interactiva un turno, segun la fase en que este."""
    status = dict(status or {"phase": F_EQUIPO, "answers": {}})
    phase = status.get("phase", F_EQUIPO)

    if phase == F_EQUIPO:
        # 'continuar' solo salta la identificacion DESPUES de haberlo intentado:
        # si no, un Enviar en vacio al arrancar arrancaria el caso sin equipo.
        if (text or "").strip().lower() in C("cmd_continue"):
            if not status.get("intento_equipo"):
                return _output(
                    T("i117"), case, status)
            status["phase"] = F_PREGUNTAS
            status.setdefault("ctx", {})
            return _output(
                T("i118")
                + _next_question(status), case, status)
        return _phase_equipment(case, text, status)
    if phase == F_PREGUNTAS:
        return _phase_questions(case, text, status)
    if phase == F_RISK:
        return _phase_risk(case, status)
    if phase == F_DECISION:
        return _phase_decision(case, status)
    if phase == F_TARGET:
        return _phase_target(case, text, status)
    if phase == F_GUIDE:
        return _phase_guide(case, text, status)
    return _phase_end(case, status)
