"""Procedimiento de migracion de 50 pasos (MIGRA-IA-PROC-050).

Es la tercera pieza de la base del agente. El cuestionario dice QUE preguntar, la
guia dice QUE criterios aplicar, y este modulo dice QUE HACER, en orden, una vez
que se decide cambiar la CPU.

El modo guia se abre en un momento concreto: cuando el caso reune un disparador
(CPU obsoleta, contrasena desconocida, sin acceso al programa) o el usuario
decide cambiar de CPU. A partir de ahi el agente deja de diagnosticar y acompana
paso a paso, con un criterio de salida y una evidencia por paso.

Dos variantes cambian el contenido de varios pasos y por eso se resuelven aqui y
no en el prompt:
  - `cambio_marca`: entre fabricantes distintos no hay herramienta de conversion,
    de modo que los pasos 21 y 22 no aplican y el programa se reescribe.
  - `sin_respaldo`: sin programa de origen, el levantamiento funcional (paso 6)
    pasa a ser la fuente principal de la especificacion.

Las dos se cruzan con una tercera condicion, `con_codigo_fuente`, que no es una
variante sino el reverso de `sin_respaldo`: hay programa que leer. De ese cruce
salen las dos rutas que ESPECIALIZAN el procedimiento, y son excluyentes:
  - misma marca + codigo accesible -> `rutas_por_fabricante`: se convierte con las
    herramientas oficiales de la marca.
  - otra marca + codigo accesible -> `ruta_cambio_de_marca`: no hay conversor entre
    fabricantes, asi que se PORTA con el programa original como especificacion.
Sin codigo accesible no hay ruta: se reconstruye a ciegas por la extension P1-P7.

El detalle NO se vuelca al prompt: el system prompt lleva un indice compacto
(`indice_para_prompt`) y el agente pide lo que necesita con la herramienta
`query_procedure`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config

CITA = "Procedimiento MIGRA-IA-PROC-050 (50 pasos)"

ROLES = {
    "tecnico": "Tecnico de mantenimiento",
    "ingenieria": "Ingenieria de automatizacion",
    "safety_specialist": "Especialista en seguridad funcional",
    "responsable": "Responsable de la instalacion",
}

STEP_STATUSES = ("pendiente", "en_curso", "completado", "no_aplica", "bloqueado")


@lru_cache(maxsize=len(config.LANGUAGES))
def _load(lang: str) -> dict:
    with open(config.procedure_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def load() -> dict:
    """Carga y cachea el procedimiento del idioma de esta peticion.

    La cache va indexada POR IDIOMA: un mismo proceso sirve los dos a la vez.
    """
    return _load(config.language())


def _norm(text) -> str:
    return str(text or "").strip().lower()


# --------------------------------------------------------------------------- #
# Acceso basico
# --------------------------------------------------------------------------- #
def order() -> list[str]:
    """Claves de los pasos en el orden en que se recorren.

    No es 1..50: la extension de construccion del programa (P1-P7) se intercala
    tras el paso 20. Toda la logica de avance va por esta lista, nunca por el
    numero, para que el documento original conserve su numeracion.
    """
    return list(load()["order"])


def total_steps() -> int:
    return len(order())


def _key(x) -> str:
    return str(x).strip().upper() if not str(x).strip().isdigit() else str(int(str(x).strip()))


def raw_step(key) -> dict | None:
    """Paso tal cual esta en el JSON, sin adaptar a las variantes del caso."""
    c = _key(key)
    for p in load()["steps"]:
        if p["key"] == c:
            return p
    return None


def phase(key) -> dict | None:
    """Fase por id, por nombre, o por la clave de un paso que contiene."""
    data = load()
    c = _key(key)
    for f in data["phases"]:
        if c in [str(x) for x in f["steps"]]:
            return f
    n = _norm(key)
    for f in data["phases"]:
        if _norm(f["id"]) == n or n in _norm(f["name"]):
            return f
    return None


def triggers() -> list[dict]:
    return load()["triggers"]


def declared_gaps() -> list[dict]:
    """Lo que el documento fuente no cubre. Se declara, no se rellena inventando."""
    return load()["declared_gaps"]


# --------------------------------------------------------------------------- #
# Contexto del caso: que variantes aplican
# --------------------------------------------------------------------------- #
def context(case) -> dict:
    """Deriva del expediente las variantes que cambian el contenido de los pasos."""
    mig = getattr(case, "migration", None) or {}
    ident = getattr(case, "equipment_identified", None) or {}
    target = mig.get("destino") or {}
    without_backup = bool(mig.get("sin_respaldo"))
    return {
        "activa": bool(mig.get("activa")),
        "cambio_marca": bool(mig.get("cambio_marca")),
        "sin_respaldo": without_backup,
        # El reverso de 'sin_respaldo': hay programa que convertir, asi que los pasos
        # 21 y 22 aplican en su forma plena y la ruta por fabricante esta habilitada.
        "con_codigo_fuente": (not without_backup) and accessible_code(case)["accesible"],
        "equipo": ident.get("modelo_identificado") or ident.get("family") or "",
        "brand": ident.get("brand") or "",
        "family": ident.get("family") or "",
        "destino": target.get("family") or "",
        "marca_destino": target.get("brand") or "",
    }


# --------------------------------------------------------------------------- #
# Acceso al programa de origen: lo que decide entre convertir y reconstruir
# --------------------------------------------------------------------------- #
def _value(case, code: str) -> str:
    """Valor normalizado de una respuesta del cuestionario, o cadena vacia."""
    resp = (getattr(case, "answers", None) or {}).get(code) or {}
    return _norm(resp.get("value"))


def _affirmative(text: str) -> bool:
    return text.startswith("si") or text.startswith("sí")


def _negative(text: str) -> bool:
    return text.startswith("no") and not text.startswith("no se conoce")


def accessible_code(case) -> dict:
    """Determina si el programa de origen se puede abrir y convertir.

    No basta con que exista un archivo: la Regla 3 del cuestionario solo cuenta
    como respaldo el que ABRE (F06) y COMPILA (F07). Devuelve tambien que
    evidencia falta, para que el agente lo pida en vez de darlo por hecho.
    """
    if case is None:
        return {"accesible": False, "evidence": [], "por_confirmar": [], "motivo": "sin caso"}

    n06, f16 = _value(case, "N06"), _value(case, "F16")
    f01, f06, f07 = _value(case, "F01"), _value(case, "F06"), _value(case, "F07")

    contrasena_ok = (
        n06.startswith("si, todas")
        or n06.startswith("no hay contrasenas")
        or _affirmative(f16)
    )
    respaldo_ok = _affirmative(f01)

    evidence, to_confirm = [], []
    if contrasena_ok:
        evidence.append(f"contrasenas conocidas (N06/F16: '{n06 or f16}')")
    if respaldo_ok:
        evidence.append("existe copia del programa (F01)")
    for cod, val, label in (("F06", f06, "el respaldo abre"),
                               ("F07", f07, "el respaldo compila")):
        if _affirmative(val):
            evidence.append(f"{label} ({cod})")
        elif _negative(val):
            return {"accesible": False, "evidence": evidence, "por_confirmar": [],
                    "motivo": f"{cod} es negativa: {label} no se cumple"}
        else:
            to_confirm.append(f"{cod} ({label})")

    accesible = contrasena_ok and respaldo_ok
    motivo = "" if accesible else "faltan contrasenas conocidas o copia verificada del programa"
    return {"accesible": accesible, "evidence": evidence,
            "por_confirmar": to_confirm, "motivo": motivo}


def obsolescence_without_spares(case) -> dict:
    """Senales de fin de vida y de falta de repuestos que justifican migrar."""
    if case is None:
        return {"hay": False, "evidence": []}

    m01, m04 = _value(case, "M01"), _value(case, "M04")
    m05, m06 = _value(case, "M05"), _value(case, "M06")
    m09 = _value(case, "M09")

    evidence = []
    if m01.startswith(("descontinuado", "anuncio de descontinuacion")):
        evidence.append(f"estado declarado por el fabricante (M01): '{m01}'")
    if _negative(m04):
        evidence.append("no se consiguen repuestos nuevos (M04)")
    elif m04.startswith("solo por pedido") or m04.startswith("si, pero con plazo largo"):
        evidence.append(f"repuestos nuevos restringidos (M04: '{m04}')")
    if _negative(m05) or m05.startswith("escasos"):
        evidence.append(f"mercado secundario insuficiente (M05: '{m05}')")
    if m06.startswith("no se consigue") or m06.startswith("mas de 8 semanas"):
        evidence.append(f"plazo de entrega inviable (M06: '{m06}')")
    if m09.startswith("vencido") or _negative(m09):
        evidence.append(f"sin contrato de soporte vigente (M09: '{m09}')")

    return {"hay": bool(evidence), "evidence": evidence}


def detect_triggers(case) -> list[dict]:
    """Disparadores que el expediente ya sostiene, con la evidencia que los apoya.

    No decide nada: solo reporta lo que el caso permite afirmar, para que el
    agente proponga abrir el modo guia y el usuario resuelva.
    """
    assets: list[dict] = []
    ident = getattr(case, "equipment_identified", None) or {}
    risk = getattr(case, "risk", None) or {}
    free_text = " ".join(
        _norm(r.get("value")) for r in (getattr(case, "answers", {}) or {}).values()
    )
    faltantes = " ".join(
        _norm(d.get("description")) for d in (getattr(case, "missing_data", []) or [])
    )
    flags = " ".join(
        _norm(b.get("text")) for b in (getattr(case, "flags", []) or [])
    )
    todo = f"{free_text} {faltantes} {flags}"

    por_id = {d["id"]: d for d in triggers()}

    stage = _norm(ident.get("stage"))
    classification = _norm(risk.get("classification"))
    if stage in ("historica", "intermedia") or classification in ("riesgo alto", "riesgo critico"):
        motivo = []
        if stage in ("historica", "intermedia"):
            motivo.append(f"la generacion del equipo esta clasificada como '{stage}' en el catalogo")
        if classification in ("riesgo alto", "riesgo critico"):
            motivo.append(f"el motor de riesgo da '{risk.get('classification')}'")
        assets.append({**por_id["cpu_obsoleta"], "evidencia_en_el_caso": "; ".join(motivo)})

    # Obsolescencia CON el programa accesible: se convierte, no se reconstruye.
    acceso = accessible_code(case)
    obsol = obsolescence_without_spares(case)
    if acceso["accesible"] and (obsol["hay"] or any(a["id"] == "cpu_obsoleta" for a in assets)):
        motivo = list(obsol["evidence"]) + list(acceso["evidence"])
        if acceso["por_confirmar"]:
            motivo.append("queda por confirmar: " + ", ".join(acceso["por_confirmar"]))
        assets.append({**por_id["obsolescencia_con_acceso_al_codigo"],
                        "evidencia_en_el_caso": "; ".join(motivo)})

    # Si el programa es accesible, la mencion suelta de una contrasena en el texto
    # libre no significa que este perdida: seria justo el diagnostico contrario.
    if not acceso["accesible"] and any(
        p in todo for p in ("contrasena", "password", "clave de la cpu", "bloqueada")
    ):
        assets.append({**por_id["contrasena_desconocida"],
                        "evidencia_en_el_caso": "el expediente menciona una contrasena "
                                                "desconocida o una CPU bloqueada"})

    if any(p in todo for p in ("sin respaldo", "no hay respaldo", "respaldo no verificado",
                               "no se puede abrir", "proyecto corrupto", "sin licencia",
                               "sin adaptador", "no se conoce si hay respaldo")):
        assets.append({**por_id["sin_acceso_al_programa"],
                        "evidencia_en_el_caso": "el expediente reporta que el programa "
                                                "no se puede copiar, abrir o verificar"})

    # Sin duplicar por id, conservando el primero encontrado.
    vistos: set[str] = set()
    unicos = []
    for d in assets:
        if d["id"] not in vistos:
            vistos.add(d["id"])
            unicos.append(d)
    return unicos


# --------------------------------------------------------------------------- #
# Un paso, ya adaptado al caso
# --------------------------------------------------------------------------- #
def step(key, ctx: dict | None = None) -> dict | None:
    """Paso con sus variantes ya resueltas segun el contexto del caso."""
    base = raw_step(key)
    if base is None:
        return None
    ctx = ctx or {}
    p = dict(base)
    p["rol_legible"] = ROLES.get(p["role"], p["role"])
    p["citation"] = (f"{CITA}, extension de construccion del programa, paso {p['label']}"
                 if p.get("extension") else f"{CITA}, paso {p['label']}")

    aplica = True
    avisos: list[str] = []

    if ctx.get("cambio_marca") and base.get("brand_change_variant"):
        text = base["brand_change_variant"]
        avisos.append(f"CAMBIO DE MARCA: {text}")
        if text.startswith("NO APLICA"):
            aplica = False
    if ctx.get("sin_respaldo") and base.get("no_backup_variant"):
        text = base["no_backup_variant"]
        avisos.append(f"SIN RESPALDO VERIFICADO: {text}")
        if text.startswith("NO APLICA"):
            aplica = False

    p["aplica"] = aplica
    p["avisos"] = avisos
    p["exigencias"] = [k for k, v in p["requires"].items() if v]
    return p


def step_text(key, ctx: dict | None = None) -> str:
    """Render en Markdown de un paso, listo para mostrarselo al tecnico."""
    p = step(key, ctx)
    if p is None:
        return f"No existe el paso {key} en el procedimiento."
    f = phase(p["key"]) or {}
    try:
        position = order().index(p["key"]) + 1
    except ValueError:
        position = "?"
    lineas = [
        f"**Paso {p['label']} ({position} de {total_steps()}) — {p['title'].rstrip('.')}**",
        f"*Fase {f.get('name', '')} · lo ejecuta: {p['rol_legible']}*",
        "",
        p["detail"],
        "",]
    if p.get("extension"):
        lineas += [
            "> **Paso de la extension de construccion del programa.** El documento "
            "original de 50 pasos cubre convertir un programa existente, no escribirlo. "
            f"Base metodologica: {p.get('methodological_origin', '')}.",
            "",
        ]
    lineas += [
        f"**Se da por terminado cuando:** {p['exit_criterion']}",
        "**Evidencia que debe quedar:**",
    ]
    lineas += [f"- {e}" for e in p["evidence"]]
    if p["prerequisites"]:
        lineas.append("")
        lineas.append("**Antes de este paso deben estar cerrados:** "
                      + ", ".join(f"paso {x}" for x in p["prerequisites"]))
    if p["exigencias"]:
        etiquetas = {
            "human_approval": "aprobacion humana registrada",
            "machine_stopped": "maquina detenida",
            "loto": "bloqueo y etiquetado (LOTO)",
            "safety_specialist": "especialista en seguridad funcional presente",
        }
        lineas.append("")
        lineas.append("⚠️ **Exige antes de ejecutarlo:** "
                      + "; ".join(etiquetas[e] for e in p["exigencias"]) + ".")
    if p.get("blocking"):
        lineas.append("🚧 **Paso bloqueante:** no se avanza hasta cerrarlo.")
    for aviso in p["avisos"]:
        lineas.append("")
        lineas.append(f"> {aviso}")
    if p.get("agent_note"):
        lineas.append("")
        lineas.append(f"*Nota: {p['agent_note']}*")
    if not p["aplica"]:
        lineas.append("")
        lineas.append("**Este paso NO aplica en este caso** por la variante indicada: "
                      "marcalo como `no_aplica` y sigue al siguiente.")
    lineas.append("")
    lineas.append(f"_{p['citation']}_")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Avance: que sigue y que esta bloqueado
# --------------------------------------------------------------------------- #
def _status_of(case, key) -> str:
    mig = getattr(case, "migration", None) or {}
    return (mig.get("steps", {}).get(_key(key), {}) or {}).get("status", "pendiente")


def _closed(status: str) -> bool:
    return status in ("completado", "no_aplica")


def status(case) -> dict:
    """Avance del procedimiento en este caso."""
    ctx = context(case)
    claves = order()
    total = len(claves)
    by_status = {e: [] for e in STEP_STATUSES}
    for c in claves:
        by_status[_status_of(case, c)].append(c)
    cerrados = len(by_status["completado"]) + len(by_status["no_aplica"])
    sig = next_step(case)
    return {
        "activa": ctx["activa"],
        "total_steps": total,
        "cerrados": cerrados,
        "porcentaje": round(100 * cerrados / total, 1),
        "completados": by_status["completado"],
        "no_aplican": by_status["no_aplica"],
        "en_curso": by_status["en_curso"],
        "bloqueados": by_status["bloqueado"],
        "siguiente": sig["label"] if sig else None,
        "fase_actual": (phase(sig["key"]) or {}).get("name") if sig else "procedimiento completo",
        "variants": {"cambio_marca": ctx["cambio_marca"],
                      "sin_respaldo": ctx["sin_respaldo"],
                      "con_codigo_fuente": ctx["con_codigo_fuente"]},
    }


def next_step(case) -> dict | None:
    """Primer paso no cerrado, con el detalle de lo que le falta para poder ejecutarse."""
    ctx = context(case)
    for c in order():
        if _closed(_status_of(case, c)):
            continue
        p = step(c, ctx)
        pendientes = [r for r in p["prerequisites"] if not _closed(_status_of(case, r))]
        p["prerrequisitos_pendientes"] = pendientes
        p["ejecutable"] = not pendientes
        return p
    return None


def blocks(case) -> list[dict]:
    """Pasos que no pueden ejecutarse todavia y por que.

    Sirve para que el agente no proponga tocar la maquina antes de tiempo: el
    paso 35 (reemplazo fisico) depende del respaldo verificado y del plan de
    retorno, y esa dependencia es una regla del procedimiento, no un criterio
    del modelo.
    """
    ctx = context(case)
    fuera = []
    for c in order():
        if _closed(_status_of(case, c)):
            continue
        p = step(c, ctx)
        pendientes = [r for r in p["prerequisites"] if not _closed(_status_of(case, r))]
        if pendientes:
            fuera.append({
                "step": p["label"],
                "title": p["title"],
                "prerrequisitos_pendientes": pendientes,
                "blocking": bool(p.get("blocking")),
            })
    return fuera


# --------------------------------------------------------------------------- #
# Paso 13: las dos opciones de CPU destino
# --------------------------------------------------------------------------- #
def target_options(ident: dict | None, limite_alternativas: int = 8) -> dict:
    """Construye las dos opciones que el agente ofrece en el paso 13.

    Opcion A sale de la cronologia del propio fabricante y, cuando la guia
    publica una ruta para la familia de origen, de esa ruta. Opcion B ofrece las
    plataformas actuales de otras marcas A NIVEL DE FAMILIA: el catalogo no
    publica atributos comparables por modelo, asi que la equivalencia modelo a
    modelo no se afirma, se remite a la herramienta oficial del fabricante.
    """
    from . import manufacturers  # import diferido: evita ciclo en la carga del paquete

    marco = load()["target_cpu_options"]
    output = {
        "step": marco["step"],
        "rule": marco["rule"],
        "misma_marca": dict(marco["options"][0]),
        "marca_alternativa": dict(marco["options"][1]),
    }

    ident = ident or {}
    brand = ident.get("brand")
    if not brand:
        output["warning"] = (
            "El equipo de origen no esta identificado contra el catalogo. Sin marca "
            "y familia no se puede proponer una plataforma destino: pide la placa "
            "antes de continuar con el paso 13."
        )
        return output

    # --- Opcion A: la generacion actual del mismo fabricante -----------------
    actuales = ident.get("generaciones_actuales_del_fabricante") or []
    path = ident.get("ruta_migracion_guia") or {}
    documentado = (path or {}).get("destino_documentado") or {}
    output["misma_marca"].update({
        "brand": brand,
        "familia_origen": ident.get("family"),
        "familias_actuales": [
            {"family": a["family"],
             "modelos_documentados": a["models_text"],
             "sources": a.get("sources", [])}
            for a in actuales
        ],
        "ruta_publicada_para_el_origen": documentado or None,
        "target_software": path.get("target_software"),
        "legacy_networks": path.get("legacy_networks"),
        "typical_risk": path.get("typical_risk"),
        "citation": path.get("citation"),
        "nota_generacion_actual": ident.get("nota_generacion_actual") or "",
    })

    # --- Opcion B: plataformas actuales de otras marcas ---------------------
    catalog = manufacturers.load_catalog()
    origin_kind = manufacturers.product_type(ident.get("classification", ""))
    same_kind: list[dict] = []
    other_kind: list[dict] = []
    for fab in catalog["manufacturers"]:
        if fab["brand"] == brand:
            continue
        act = manufacturers.current_generations(fab["brand"])
        if not act.get("families"):
            continue
        registro = {
            "brand": act["brand"],
            "classification": act["classification"],
            "familias_actuales": act["families"],
            "note": act.get("note", ""),
        }
        # Se comparan cosas comparables: un equipo basado en PC no se ofrece como
        # alternativa de un PLC sin decirlo. Los demas quedan disponibles aparte.
        if manufacturers.product_type(fab["classification"]) == origin_kind:
            same_kind.append(registro)
        else:
            other_kind.append(registro)

    output["marca_alternativa"].update({
        "criterio_de_lista": f"Marcas del catalogo del mismo tipo de producto que el equipo "
                             f"de origen ({ident.get('classification')}), excluyendo {brand}.",
        "total_del_mismo_tipo": len(same_kind),
        "mostradas": same_kind[:limite_alternativas],
        "resto_disponible": [a["brand"] for a in same_kind[limite_alternativas:]],
        "otro_tipo_de_producto": [
            {"brand": a["brand"], "classification": a["classification"]} for a in other_kind
        ],
    })
    return output


def options_text(ident: dict | None, limite_alternativas: int = 6) -> str:
    """Render en Markdown de las dos opciones, para el paso 13."""
    o = target_options(ident, limite_alternativas)
    if "warning" in o:
        return f"⚠️ {o['warning']}"

    a = o["misma_marca"]
    b = o["marca_alternativa"]
    lineas = [
        f"**Paso {o['step']} — elegir la CPU de reemplazo.** Aqui la decision es tuya. "
        "Te presento las dos vias con sus consecuencias:",
        "",
        f"### Opcion A — seguir con {a['brand']}",
    ]
    path = a.get("ruta_publicada_para_el_origen")
    if path:
        lineas.append(f"La guia publica una ruta para tu familia de origen "
                      f"(**{path['origen_en_guia']}**): destino **{path['destino']}**.")
        if path.get("critical_aspects"):
            lineas.append(f"Aspectos criticos: {path['critical_aspects']}")
    for fam in a["familias_actuales"]:
        fuentes = "; ".join(f["url"] for f in fam.get("sources", []) if f.get("url"))
        lineas.append(f"- **{fam['family']}** — modelos documentados: {fam['modelos_documentados']}"
                      + (f"\n  Fuente: {fuentes}" if fuentes else ""))
    if a.get("target_software"):
        lineas.append(f"- Software objetivo: **{a['target_software']}**; "
                      f"redes heredadas: {a.get('legacy_networks')}; "
                      f"riesgo tipico: {a.get('typical_risk')}")
    if a.get("nota_generacion_actual"):
        lineas.append(f"- ⚠️ {a['nota_generacion_actual']}")
    lineas.append("A favor: " + " · ".join(a["pros"]))
    lineas.append("En contra: " + " · ".join(a["cons"]))

    lineas += ["", "### Opcion B — cambiar de marca", b["what_it_offers"], ""]
    for alt in b["mostradas"]:
        fams = "; ".join(f"**{f['family']}** ({f['modelos_documentados']})"
                         for f in alt["familias_actuales"])
        lineas.append(f"- **{alt['brand']}** — {fams}")
    if b["resto_disponible"]:
        lineas.append(f"- Y {len(b['resto_disponible'])} marcas mas del mismo tipo en el "
                      "catalogo: " + ", ".join(b["resto_disponible"]) + ".")
    if b.get("otro_tipo_de_producto"):
        otras = ", ".join(f"{a['brand']} ({a['classification']})"
                          for a in b["otro_tipo_de_producto"][:6])
        lineas.append(f"- De otro tipo de producto, si te interesa evaluarlo: {otras}.")
    lineas.append("")
    lineas.append("A favor: " + " · ".join(b["pros"]))
    lineas.append("En contra: " + " · ".join(b["cons"]))
    lineas.append("")
    lineas.append(f"⚠️ **Limite del agente:** {b['hard_limit']} {b['data_support']}")
    lineas.append("")
    lineas.append(f"_{o['rule']}_")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Rutas de conversion por fabricante: especializan los pasos 21, 22 y 23
# --------------------------------------------------------------------------- #
def manufacturer_routes() -> dict:
    """Bloque completo de rutas por fabricante, con su condicion de uso."""
    return load().get("routes_by_manufacturer", {})


def manufacturer_route(brand=None, case=None, ctx: dict | None = None) -> dict | None:
    """Ruta de conversion de una marca, ya contrastada con el caso.

    Devuelve None si la marca no tiene ruta publicada: eso se declara, no se
    improvisa. Cuando la familia de origen del caso no coincide con la que la
    ruta cubre, la devuelve igual pero con el aviso correspondiente.
    """
    bloque = manufacturer_routes()
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    buscada = _norm(brand or ctx.get("brand"))
    if not buscada:
        return None

    for r in bloque.get("routes", []):
        if _norm(r["brand"]) != buscada:
            continue
        path = dict(r)
        family = _norm(ctx.get("family")) or _norm(ctx.get("equipo"))
        covers = [_norm(f) for f in r.get("source_families", [])]
        path["aplica_a_origen"] = (not family) or any(
            f in family or family in f for f in covers
        )
        avisos = []
        if not path["aplica_a_origen"]:
            avisos.append(
                f"La ruta esta escrita para {', '.join(r['source_families'])} y el equipo "
                f"del caso es '{ctx.get('family') or ctx.get('equipo')}'. Aplica solo el "
                "tramo que corresponda; no la presentes completa como si fuera su ruta."
            )
        if ctx.get("sin_respaldo"):
            avisos.append(
                "El caso corre con la variante 'sin_respaldo': NO hay programa que "
                "convertir y esta ruta no aplica. Se reconstruye por la extension P1-P7."
            )
        if ctx.get("cambio_marca"):
            avisos.append(
                "El caso va a otra marca: entre fabricantes distintos no hay herramienta "
                "de conversion y esta ruta NO aplica. Con el programa de origen accesible "
                "el porte se guia por la ruta de cambio de marca (tema "
                "'ruta_cambio_marca'); sin el, se reconstruye por la extension P1-P7."
            )
        path["avisos"] = avisos
        return path
    return None


def manufacturer_route_text(brand=None, case=None, ctx: dict | None = None) -> str:
    """Render en Markdown de la ruta de conversion de una marca."""
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    bloque = manufacturer_routes()
    r = manufacturer_route(brand, case, ctx)
    if r is None:
        disponibles = ", ".join(x["brand"] for x in bloque.get("routes", [])) or "ninguna"
        return (
            f"No hay ruta de conversion publicada para '{brand or ctx.get('brand') or '?'}'. "
            f"Marcas con ruta: {disponibles}. Para las demas rige el paso 21 generico "
            "(usar primero las herramientas oficiales del fabricante) y la limitacion se "
            "declara al usuario en vez de improvisar una secuencia."
        )

    lineas = [
        f"**Ruta de conversion — {r['title']} ({r['brand']})**",
        "",
        f"> {r['principle']}",
        "",
        f"*Especializa los pasos {', '.join(r['applies_to_steps'])} del {CITA}.*",
        "",
    ]
    for aviso in r.get("avisos", []):
        lineas += [f"⚠️ {aviso}", ""]

    ramas = r.get("branches", {})
    for p in r["steps"]:
        cabecera = f"**{p['n']} — {p['title']}**"
        if p.get("branch"):
            cabecera += f"  *(solo si {ramas.get(p['branch'], p['branch'])})*"
        lineas += [
            cabecera,
            f"*Especializa el paso {p['specializes_step']} del procedimiento.*",
            "",
            p["detail"],
            "",
            f"**Se da por terminado cuando:** {p['exit_criterion']}",
        ]
        if p.get("agent_note"):
            lineas.append(f"*Nota: {p['agent_note']}*")
        lineas.append("")

    if r.get("rules"):
        lineas.append("**Reglas que rigen toda la ruta:**")
        lineas += [f"- {x['rule']}" for x in r["rules"]]
        lineas.append("")

    lineas.append("**Fuentes:**")
    for f in r.get("sources", []):
        lineas.append(f"- [{f['type']}] {f['description']} — {f['url']}")
    lineas += ["", f"_{CITA}, rutas por fabricante: {r['id']}_"]
    return "\n".join(lineas)


def brand_change_route(case=None, ctx: dict | None = None) -> dict | None:
    """Ruta de porte hacia otra marca, ya contrastada con el caso.

    Es UNA sola ruta para cualquier par de marcas, porque describe el metodo y no
    las equivalencias concretas: esas dependen del par y se construyen contra los
    manuales de los dos fabricantes. Devuelve None si el caso no cumple las dos
    condiciones a la vez -destino de otra marca y programa de origen accesible-,
    que es justo cuando ofrecerla seria enganoso.
    """
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    if not (ctx.get("cambio_marca") and ctx.get("con_codigo_fuente")):
        return None
    bloque = load().get("brand_change_route")
    if not bloque:
        return None
    path = dict(bloque)
    path["aplica_a_origen"] = True
    avisos = []
    if ctx.get("brand") and ctx.get("marca_destino"):
        avisos.append(
            f"Porte de {ctx['brand']} a {ctx['marca_destino']}: la ruta describe el "
            "metodo, no las equivalencias de ese par concreto. Las tablas se construyen "
            "contra los manuales oficiales de las dos marcas."
        )
    path["avisos"] = avisos
    return path


def brand_change_route_text(case=None, ctx: dict | None = None) -> str:
    """Render en Markdown de la ruta de porte entre fabricantes distintos."""
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    bloque = load().get("brand_change_route", {})
    r = brand_change_route(case, ctx)
    if r is None:
        return (
            "La ruta de cambio de marca no aplica a este caso: pide las dos condiciones "
            "a la vez, destino de OTRA marca (paso 13) y programa de origen accesible y "
            "verificado. Sin acceso al codigo el programa se reconstruye por la extension "
            "P1-P7; dentro de la misma marca rige la ruta del fabricante (tema "
            f"'ruta_fabricante'). Condicion de uso: {bloque.get('usage_condition', '')}"
        )

    lineas = [
        f"**Ruta de cambio de marca — {r['title']}**",
        "",
        f"> {r['principle']}",
        "",
        f"*Especializa los pasos {', '.join(r['applies_to_steps'])} del {CITA}, y se apoya "
        "en la extension P1-P7 para escribir el programa nuevo.*",
        "",
    ]
    for aviso in r.get("avisos", []):
        lineas += [f"⚠️ {aviso}", ""]

    for x in r["steps"]:
        lineas += [
            f"**{x['n']} — {x['title']}**",
            f"*Especializa el paso {x['specializes_step']} del procedimiento.*",
            "",
            x["detail"],
            "",
            f"**Se da por terminado cuando:** {x['exit_criterion']}",
        ]
        if x.get("agent_note"):
            lineas.append(f"*Nota: {x['agent_note']}*")
        lineas.append("")

    if r.get("rules"):
        lineas.append("**Reglas que rigen toda la ruta:**")
        lineas += [f"- {x['rule']}" for x in r["rules"]]
        lineas.append("")
    lineas += [f"**Limite duro:** {r.get('hard_limit', '')}", "", "**Fuentes:**"]
    for f in r.get("sources", []):
        lineas.append(f"- [{f['type']}] {f['description']} — {f['url']}")
    lineas += ["", f"_{CITA}, ruta de cambio de marca: {r['id']}_"]
    return "\n".join(lineas)


def _case_path(case=None, ctx: dict | None = None) -> dict | None:
    """La ruta que aplica al caso: la de la marca, la de cambio de marca, o ninguna.

    Son excluyentes y el orden importa: si el destino es de otra marca, la ruta del
    fabricante de origen ya no dice nada util sobre el porte.
    """
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    if ctx.get("sin_respaldo"):
        return None
    if ctx.get("cambio_marca"):
        return brand_change_route(case, ctx)
    r = manufacturer_route(None, case, ctx)
    if r is None or not r.get("aplica_a_origen"):
        return None
    return r


def route_for_step(key, case=None, ctx: dict | None = None) -> dict | None:
    """Sub-pasos de la ruta que aplica al caso y especializan UN paso concreto.

    Devuelve None cuando ninguna de las dos rutas aplica: sin programa que leer
    (`sin_respaldo`), marca sin ruta publicada, equipo de origen que la ruta no
    cubre, o cambio de marca sin acceso al codigo. En esos casos decirlo a medias
    seria peor que callarlo.
    """
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    r = _case_path(case, ctx)
    if r is None:
        return None

    c = _key(key)
    sub = [p for p in r["steps"] if _key(p["specializes_step"]) == c]
    rules = [x for x in r.get("rules", []) if c in [_key(n) for n in x["affects_steps"]]]
    # Los pasos 20 y 22 no tienen sub-paso propio pero si regla que los gobierna:
    # callarlos seria perder justo el aviso de que el hardware no se convierte.
    if not sub and not rules:
        return None
    return {"route": r, "sub_pasos": sub, "rules": rules}


def route_for_step_text(key, case=None, ctx: dict | None = None) -> str:
    """Bloque en Markdown con los sub-pasos de marca de un paso. Vacio si no aplica."""
    d = route_for_step(key, case, ctx)
    if d is None:
        return ""
    r, sub, rules = d["route"], d["sub_pasos"], d["rules"]
    ramas = r.get("branches", {})

    regla_sola = "*Regla de la ruta que gobierna este paso.*"
    if r.get("type") == "cambio_de_marca":
        title = f"**Ruta de cambio de marca — {r['title']}**"
        encabezado = ("*Lo que este paso significa cuando el destino es de otra marca y "
                      "el programa de origen SI se puede leer.*" if sub else regla_sola)
    else:
        title = f"**Ruta {r['brand']} — {r['title']}**"
        encabezado = (f"*Lo que este paso significa para un "
                      f"{', '.join(r['source_families'])}.*" if sub else regla_sola)
    lineas = ["", "---", "", title, encabezado, ""]
    for p in sub:
        cabecera = f"**{p['n']} · {p['title']}**"
        if p.get("branch"):
            cabecera += f"  *(solo si {ramas.get(p['branch'], p['branch'])})*"
        lineas += [cabecera, "", p["detail"], "",
                   f"**Se da por terminado cuando:** {p['exit_criterion']}"]
        if p.get("agent_note"):
            lineas.append(f"*Nota: {p['agent_note']}*")
        lineas.append("")
    for x in rules:
        lineas += [f"> **Regla de la ruta:** {x['rule']}", ""]
    return "\n".join(lineas).rstrip()


def route_summary_text(case=None, ctx: dict | None = None) -> str:
    """Resumen de la ruta para anunciarla al fijar el destino. Vacio si no aplica."""
    ctx = ctx if ctx is not None else (context(case) if case is not None else {})
    r = _case_path(case, ctx)
    if r is None:
        return ""

    steps_with_route = sorted({_key(n) for n in r["applies_to_steps"]},
                            key=lambda x: (len(x), x))
    if r.get("type") == "cambio_de_marca":
        cabecera = ("**El destino es de otra marca y el programa de origen si se puede "
                    "leer: aplica la ruta de porte entre fabricantes.**")
    else:
        cabecera = (f"**Hay una ruta de conversion publicada para {r['brand']}: "
                    f"{r['title']}.**")
    lineas = [
        cabecera,
        "",
        f"> {r['principle']}",
        "",
        "La veras desglosada al llegar a los pasos "
        + ", ".join(steps_with_route) + " del procedimiento.",
    ]
    for aviso in r.get("avisos", []):
        lineas += ["", f"⚠️ {aviso}"]
    if ctx.get("destino"):
        avisos = [p for p in r["steps"]
                  if p.get("branch") == "destino_tia_portal" and p.get("agent_note")]
        if avisos and "1200" in str(ctx.get("destino", "")) + str(ctx.get("equipo", "")):
            lineas += ["", f"⚠️ {avisos[0]['agent_note']}"]
    return "\n".join(lineas)


def prompt_index() -> str:
    """Indice del procedimiento: da las claves validas sin volcar el contenido."""
    data = load()
    doc = data["document"]
    phases = "; ".join(f"{f['id']} (pasos {f['steps'][0]}-{f['steps'][-1]}, etapa {f['guide_stage']})"
                      for f in data["phases"])
    disp = "; ".join(f"{d['id']} = {d['title']}" for d in data["triggers"])
    marcas = "; ".join(
        f"{r['brand']} ({' , '.join(r['source_families'])} -> {' / '.join(r['target_families'])})"
        for r in data.get("routes_by_manufacturer", {}).get("routes", [])
    ) or "ninguna publicada todavia"
    titulos = "; ".join(f"{p['label']}={p['title'].rstrip('.')}" for p in data["steps"])
    return (
        f"PROCEDIMIENTO DE MIGRACION: {doc['title']} ({doc['id']}, "
        f"{doc['total_steps']} pasos). Citalo como '{CITA}, paso N'.\n"
        f"CUANDO SE ABRE: al decidir cambiar la CPU. Disparadores: {disp}.\n"
        f"Fases: {phases}.\n"
        "Consultalo con `query_procedure` (tema, clave). Temas: paso (clave = "
        "numero), fase (clave = id), disparadores, opciones_destino (las dos opciones "
        "de CPU del paso 13), ruta_fabricante (clave = marca), ruta_cambio_marca, "
        "estado (avance del caso), siguiente (paso que toca), bloqueos, huecos.\n"
        f"RUTAS DE CONVERSION POR MARCA (especializan los pasos 21-23): {marcas}. "
        "Se usan SOLO cuando el programa de origen es accesible y verificado "
        "(disparador 'obsolescencia_con_acceso_al_codigo'). Para las demas marcas rige "
        "el paso 21 generico y esa limitacion SE DECLARA, no se rellena inventando.\n"
        "RUTA DE CAMBIO DE MARCA (tema 'ruta_cambio_marca', especializa los pasos 11, 12, "
        "18, 21 y 32): aplica cuando el destino es de OTRA marca Y el programa de origen "
        "es accesible. Entre fabricantes no hay conversor, pero con la fuente en la mano "
        "el trabajo NO empieza de cero: el programa original es la ESPECIFICACION y se "
        "porta contra ella. El agente NO publica equivalencias de instrucciones entre "
        "marcas: propone la tabla y pide verificarla contra los manuales de las dos.\n"
        f"Pasos: {titulos}."
    )


# --------------------------------------------------------------------------- #
# Despachador
# --------------------------------------------------------------------------- #
def query(tema: str, key=None, case=None) -> dict:
    """Punto unico de consulta, como en `conocimiento.consultar`."""
    t = _norm(tema)
    ctx = context(case) if case is not None else {}

    if t == "step":
        p = step(key, ctx) if key is not None else None
        if p is None:
            return {"error": f"Paso no encontrado: {key}. Validos: 1 a {total_steps()}."}
        return {"tema": "step", "citation": p["citation"], "contenido": p,
                "text": step_text(p["n"], ctx)}

    if t == "phase":
        f = phase(key)
        if f is None:
            return {"error": f"Fase no encontrada: {key}."}
        return {"tema": "phase", "citation": CITA, "contenido": {
            **f, "pasos_detalle": [{"step": str(n), "title": raw_step(n)["title"]} for n in f["steps"]]}}

    if t in ("triggers", "trigger"):
        contenido = {"catalogo": triggers()}
        if case is not None:
            contenido["activos_en_el_caso"] = detect_triggers(case)
        return {"tema": "triggers", "citation": CITA, "contenido": contenido}

    if t in ("opciones_destino", "options", "opciones_cpu"):
        ident = key if isinstance(key, dict) else getattr(case, "equipment_identified", None)
        return {"tema": "opciones_destino", "citation": CITA,
                "contenido": target_options(ident),
                "text": options_text(ident)}

    if t in ("ruta_fabricante", "route", "routes_by_manufacturer", "routes"):
        bloque = manufacturer_routes()
        brand = key if isinstance(key, str) else None
        r = manufacturer_route(brand, case, ctx)
        contenido = {
            "usage_condition": bloque.get("usage_condition"),
            "coverage": bloque.get("coverage"),
            "marcas_con_ruta": [x["brand"] for x in bloque.get("routes", [])],
            "route": r,
        }
        if r is None:
            contenido["acceso_al_codigo"] = accessible_code(case) if case is not None else None
        return {"tema": "ruta_fabricante", "citation": f"{CITA}, rutas por fabricante",
                "contenido": contenido,
                "text": manufacturer_route_text(brand, case, ctx)}

    if t in ("ruta_cambio_marca", "brand_change_route", "cambio_marca"):
        bloque = load().get("brand_change_route", {})
        r = brand_change_route(case, ctx)
        contenido = {
            "usage_condition": bloque.get("usage_condition"),
            "coverage": bloque.get("coverage"),
            "hard_limit": bloque.get("hard_limit"),
            "route": r,
        }
        if r is None:
            contenido["por_que_no_aplica"] = {
                "cambio_marca": bool(ctx.get("cambio_marca")),
                "con_codigo_fuente": bool(ctx.get("con_codigo_fuente")),
                "acceso_al_codigo": accessible_code(case) if case is not None else None,
            }
        return {"tema": "ruta_cambio_marca", "citation": f"{CITA}, ruta de cambio de marca",
                "contenido": contenido,
                "text": brand_change_route_text(case, ctx)}

    if t == "status":
        if case is None:
            return {"error": "El tema 'status' necesita un caso abierto."}
        return {"tema": "status", "citation": CITA, "contenido": status(case)}

    if t in ("siguiente", "siguiente_paso"):
        if case is None:
            return {"error": "El tema 'siguiente' necesita un caso abierto."}
        s = next_step(case)
        if s is None:
            return {"tema": "siguiente", "citation": CITA,
                    "contenido": {"mensaje": "Los 50 pasos estan cerrados."}}
        return {"tema": "siguiente", "citation": s["citation"], "contenido": s,
                "text": step_text(s["key"], ctx)}

    if t == "bloqueos":
        if case is None:
            return {"error": "El tema 'bloqueos' necesita un caso abierto."}
        return {"tema": "bloqueos", "citation": CITA, "contenido": blocks(case)}

    if t in ("huecos", "declared_gaps"):
        return {"tema": "huecos", "citation": CITA, "contenido": declared_gaps()}

    if t in ("document", "procedure"):
        return {"tema": "document", "citation": CITA, "contenido": load()["document"]}

    return {"error": f"Tema no reconocido: {tema}. Validos: paso, fase, disparadores, "
                     "opciones_destino, ruta_fabricante, ruta_cambio_marca, estado, "
                     "siguiente, bloqueos, huecos, documento."}
