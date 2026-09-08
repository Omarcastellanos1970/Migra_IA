"""Demo interactiva: el motor real operado por el usuario, sin API ni clave.

Es el unico modo de demostracion del artefacto. No imita al agente
conversacional -eso solo puede hacerlo el modelo-, sino que expone la parte
DETERMINISTA del agente y la pone a trabajar con los datos de quien la ejecuta,
sin caso grabado de por medio:

  - el equipo se identifica contra el catalogo verificado (`fabricantes.py`);
  - las preguntas, sus opciones y sus ramas adaptativas salen del cuestionario
    maestro (`data/cuestionario.json`), no se escriben aqui;
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

from .caso import Caso
from .herramientas import ejecutar_herramienta
from .nucleo import aprobador_pendiente
from . import cuestionario, fabricantes, procedimiento, scoring

CITA = "Cuestionario maestro MIGRA-IA (Secciones A-Q)"

# Fases de la sesion interactiva.
F_EQUIPO = "equipo"
F_PREGUNTAS = "preguntas"
F_RIESGO = "riesgo"
F_DECISION = "decision"
F_DESTINO = "destino"
F_GUIA = "guia"
F_FIN = "fin"

_DESCONOCIDO = {"no se conoce", "no se ha consultado", "no se ha medido",
                "no se lleva registro", "no se ha probado"}


def _es_desconocido(valor) -> bool:
    return str(valor or "").strip().lower() in _DESCONOCIDO


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
    ("F06", lambda r: r.get("F01") == "Si"),
    ("F07", lambda r: r.get("F01") == "Si"),
    ("F12", lambda r: r.get("F01") in ("No", "No se conoce")),
    ("F13", lambda r: r.get("F01") in ("No", "No se conoce")),
    ("N02", None), ("N03", None), ("N05", None), ("N06", None),
    ("G01", None), ("O07", None), ("O08", None), ("O02", None),
    ("L01", None), ("L03", None), ("L07", None),
    ("P01", None), ("P04", None),
]

# Preguntas de rama que el cuestionario declara sin opciones: son de si/no y se
# presentan con las opciones estandar, sin inventarles texto.
_OPCIONES_SI_NO = ["Si", "No", "No se conoce"]


def _pregunta(codigo: str) -> dict | None:
    p = cuestionario.pregunta(codigo)
    if p is None:
        return None
    p = dict(p)
    if not p.get("opciones") and p.get("tipo") not in ("numero", "texto"):
        p["opciones"] = list(_OPCIONES_SI_NO)
    return p


def _pendientes(respuestas: dict) -> list[str]:
    """Codigos que faltan por preguntar, respetando las ramas adaptativas."""
    faltan = []
    for codigo, condicion in GUION:
        if codigo in respuestas:
            continue
        if condicion is not None and not condicion(respuestas):
            continue
        if _pregunta(codigo) is None:
            continue
        faltan.append(codigo)
    return faltan


# --------------------------------------------------------------------------- #
# Reglas de puntuacion, una por factor, segun la guia del mapa de decision
# --------------------------------------------------------------------------- #
def _rango(valor, escala: list[str]) -> int | None:
    """Posicion de una respuesta dentro de una escala ordenada."""
    v = str(valor or "").strip().lower()
    for i, op in enumerate(escala):
        if v == op.lower():
            return i
    return None


def _cap(valor: float) -> float:
    return float(max(0, min(100, round(valor, 1))))


def _f_ciclo_vida(r: dict) -> dict | None:
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
    return {"valor": tabla[m01],
            "justificacion": f"M01: estado declarado por el fabricante = '{m01}'."}


def _f_repuestos(r: dict) -> dict | None:
    m04, m06, c10 = r.get("M04"), r.get("M06"), r.get("C10")
    base = {"Si, sin problema": 10, "Si, pero con plazo largo": 45,
            "Solo por pedido especial": 65, "No": 95}.get(m04)
    if base is None and _es_desconocido(m06):
        return None
    if base is None:
        base = 50
    partes = [f"M04: '{m04}'."]
    # La guia exige contrastar el plazo de entrega con la parada tolerable: un
    # repuesto que llega despues de lo que la planta aguanta no cubre el riesgo.
    escala_m06 = ["En existencia en la planta o local", "Menos de 2 semanas",
                  "De 2 a 8 semanas", "Mas de 8 semanas", "No se consigue"]
    escala_c10 = ["Menos de 1 hora", "1 a 4 horas", "4 a 12 horas",
                  "12 a 24 horas", "Mas de 24 horas"]
    rm, rc = _rango(m06, escala_m06), _rango(c10, escala_c10)
    if rm is not None and rc is not None and rm >= 2:
        base = max(base, 85)
        partes.append(f"M06 '{m06}' frente a C10 '{c10}': el repuesto llega despues "
                      "de lo que la linea tolera, asi que la estrategia de repuesto "
                      "no cubre el riesgo por si sola.")
    elif rm is not None:
        partes.append(f"M06: '{m06}'.")
    return {"valor": _cap(base), "justificacion": " ".join(partes)}


def _f_soporte(r: dict) -> dict | None:
    m09, m07 = r.get("M09"), r.get("M07")
    base = {"Si, vigente": 10, "Vencido": 60, "No": 85}.get(m09)
    if base is None and _es_desconocido(m07):
        return None
    if base is None:
        base = 55
    ajuste = {"Si, del fabricante": -15, "Si, de tercero certificado": -5,
              "Si, de tercero sin certificar": 5, "No": 15}.get(m07, 0)
    return {"valor": _cap(base + ajuste),
            "justificacion": f"M09 contrato de soporte: '{m09}'; M07 servicio de "
                             f"reparacion: '{m07}'."}


def _f_software(r: dict) -> dict | None:
    n02, n03, n05, n06 = r.get("N02"), r.get("N03"), r.get("N05"), r.get("N06")
    if all(x is None for x in (n02, n03, n05, n06)):
        return None
    valor = 20.0
    partes = []
    so = {"Windows XP": 25, "Windows 7": 20, "Windows 10": 0, "Windows 11": 0,
          "Linux": 0, "Maquina virtual sobre un equipo moderno": 0}.get(n02, 10)
    if so:
        partes.append(f"N02 sistema operativo '{n02}'")
    valor += so
    lic = {"Original con licencia vigente": 0, "Original con licencia vencida": 15,
           "Licencia flotante en servidor": 5, "Llave fisica (dongle)": 15,
           "Version de demostracion o limitada": 20, "No se tiene licencia": 30}.get(n03, 10)
    if lic:
        partes.append(f"N03 licencia '{n03}'")
    valor += lic
    ada = {"Si, ya probado con este PLC": 0, "Si, pero sin probar": 10, "No": 25}.get(n05, 10)
    if ada:
        partes.append(f"N05 adaptador '{n05}'")
    valor += ada
    pwd = {"Si, todas": 0, "Parcialmente": 15, "No": 30, "No hay contrasenas": 0}.get(n06, 15)
    if pwd:
        partes.append(f"N06 contrasenas '{n06}'")
    valor += pwd
    return {"valor": _cap(valor),
            "justificacion": "Barrera de acceso al programa: " + "; ".join(partes) + "."}


def _f_respaldo(r: dict) -> dict | None:
    f01 = r.get("F01")
    if f01 is None:
        return None
    if f01 == "No":
        return {"valor": 100.0,
                "justificacion": "F01: no existe copia del programa. Prioridad 1: "
                                 "recuperarlo antes de cualquier decision."}
    if _es_desconocido(f01):
        return {"valor": 90.0,
                "justificacion": "F01: no se sabe si existe copia. Regla 3: un respaldo "
                                 "que no se puede verificar se trata como ausente."}
    abre, compila = r.get("F06"), r.get("F07")
    if abre == "No":
        return {"valor": 100.0,
                "justificacion": "F01 declara copia, pero F06: el respaldo NO abre. "
                                 "Se puntua como si no existiera (Regla 3)."}
    if compila == "No":
        return {"valor": 90.0,
                "justificacion": "F06 abre pero F07: no compila sin errores. No cuenta "
                                 "como respaldo verificado (Regla 3)."}
    if abre == "Si" and compila == "Si":
        return {"valor": 15.0,
                "justificacion": "F01, F06 y F07: existe copia, abre y compila. "
                                 "Respaldo verificado."}
    return {"valor": 70.0,
            "justificacion": f"F01 declara copia, pero su verificacion esta incompleta "
                             f"(F06='{abre}', F07='{compila}'). Sin verificar no cuenta "
                             "como respaldo (Regla 3)."}


_REDES_LEGADO = {"mpi", "profibus dp", "profibus pa", "devicenet", "controlnet",
                 "cc-link", "as-interface", "rs-232", "rs-485"}


def _lista(valor) -> list[str]:
    if isinstance(valor, list):
        return valor
    return [p.strip() for p in str(valor or "").split(",") if p.strip()]


def _f_compatibilidad(r: dict) -> dict | None:
    g01, o07, o08, o02 = r.get("G01"), r.get("O07"), r.get("O08"), r.get("O02")
    if all(x is None for x in (g01, o07, o08, o02)):
        return None
    valor = 20.0
    partes = []
    redes = [x.lower() for x in _lista(g01)]
    if any("propietaria" in x for x in redes):
        valor += 30
        partes.append("G01 incluye una red propietaria")
    elif any(x in _REDES_LEGADO for x in redes):
        valor += 15
        partes.append(f"G01 redes de generacion anterior ({', '.join(_lista(g01))})")
    lenguajes = [x.lower() for x in _lista(o07)]
    if any("propietarios" in x for x in lenguajes):
        valor += 20
        partes.append("O07 incluye bloques propietarios del fabricante de la maquina")
    if any(("awl" in x or "stl" in x or "instrucciones" in x) for x in lenguajes):
        valor += 15
        partes.append("O07 incluye lista de instrucciones (AWL/STL), sin conversion automatica garantizada")
    if any(("grafcet" in x or "sfc" in x or "graph" in x) for x in lenguajes):
        valor += 10
        partes.append("O07 incluye GRAFCET/SFC")
    if o08 == "Si":
        valor += 25
        partes.append("O08 usa librerias propietarias")
    if str(o02).strip().lower().startswith("si"):
        valor += 20
        partes.append("O02 hay control de movimiento o ejes sincronizados")
    if not partes:
        partes.append("sin arrastre relevante declarado en G01, O02, O07 ni O08")
    return {"valor": _cap(valor),
            "justificacion": "Cuanto arrastra el cambio: " + "; ".join(partes) + "."}


def _causa_raiz_externa(r: dict) -> list[str]:
    """Indicios de que la falla NO es del controlador, sino de su entorno.

    Es la regla que mas cambia el diagnostico: la guia del factor exige buscarla
    ANTES de puntuar alto el historial, porque sustituir el PLC sin corregirla
    reproduce la falla en el equipo nuevo.
    """
    causas = []
    p01 = str(r.get("P01") or "")
    if p01 in ("Entre 40 y 50 C", "Mayor a 50 C"):
        causas.append(f"P01 temperatura del tablero '{p01}'")
    energia = [x.lower() for x in _lista(r.get("P04"))]
    if any("tierra dudosa" in x or "tierra dudosa o inexistente" in x for x in energia):
        causas.append("P04 puesta a tierra dudosa o inexistente")
    if any("variaciones" in x or "armonicos" in x or "cortes" in x for x in energia):
        causas.append("P04 calidad de energia deficiente")
    if r.get("L07") == "Si":
        causas.append("L07 la maquina pierde el programa, los datos o la hora sin energia "
                      "(bateria o respaldo de memoria agotado)")
    return causas


def _f_historial(r: dict) -> dict | None:
    l01, l03 = r.get("L01"), r.get("L03")
    if l01 is None and l03 is None:
        return None
    try:
        paros = int(str(l01).strip())
    except (TypeError, ValueError):
        paros = None
    if paros is None:
        valor = 45.0
        partes = ["L01 sin numero de paros registrado"]
    else:
        valor = 10.0 if paros == 0 else 30.0 if paros <= 2 else 50.0 if paros <= 5 else 70.0
        partes = [f"L01 {paros} paros no programados en 12 meses"]
    valor += {"En aumento": 20, "Estable": 0, "En disminucion": -10,
              "Sin fallas registradas": -15}.get(l03, 5)
    if l03:
        partes.append(f"L03 tendencia '{l03}'")
    causas = _causa_raiz_externa(r)
    if causas:
        valor = min(valor, 55.0)
        partes.append("CAUSA RAIZ EXTERNA no corregida (" + "; ".join(causas) +
                      "): estas fallas no son atribuibles al controlador, asi que el "
                      "factor se limita. Corregirla es previo a cualquier sustitucion")
    return {"valor": _cap(valor), "justificacion": "; ".join(partes) + "."}


def _f_criticidad(r: dict) -> dict | None:
    c08, c10, q04 = r.get("C08"), r.get("C10"), r.get("Q04")
    base = {"Baja: puede detenerse varios dias": 20,
            "Media: afecta parcialmente la produccion": 45,
            "Alta: afecta una linea importante": 70,
            "Critica: detiene la planta o presenta riesgo de seguridad": 95}.get(c08)
    if base is None:
        return None
    valor = base + {"Menos de 1 hora": 20, "1 a 4 horas": 15, "4 a 12 horas": 10,
                    "12 a 24 horas": 5, "Mas de 24 horas": 0}.get(c10, 0)
    valor += {"No hay ventana disponible": 15, "En el paro anual de planta o vacaciones": 10,
              "Fines de semana": 5}.get(q04, 0)
    return {"valor": _cap(valor),
            "justificacion": f"C08 criticidad '{c08}'; C10 parada tolerable '{c10}'; "
                             f"Q04 ventana de intervencion '{q04}'."}


REGLAS = {
    "estado_ciclo_vida": _f_ciclo_vida,
    "disponibilidad_repuestos": _f_repuestos,
    "soporte_fabricante": _f_soporte,
    "disponibilidad_software": _f_software,
    "disponibilidad_respaldo": _f_respaldo,
    "compatibilidad_sistemas": _f_compatibilidad,
    "historial_fallas": _f_historial,
    "criticidad_productiva": _f_criticidad,
}


def factores(respuestas: dict) -> tuple[dict, list[str]]:
    """Traduce las respuestas a los 8 factores de `scoring.py`.

    Devuelve (factores, omitidos). Un factor sin datos suficientes se OMITE: el
    motor renormaliza los pesos y el hueco se declara como dato faltante, en
    lugar de rellenarlo con una suposicion.
    """
    calculados, omitidos = {}, []
    for clave in scoring.PESOS:
        regla = REGLAS.get(clave)
        res = regla(respuestas) if regla else None
        if res is None:
            omitidos.append(clave)
        else:
            calculados[clave] = res
    return calculados, omitidos


# --------------------------------------------------------------------------- #
# Decision: que alternativa corresponde a este caso
# --------------------------------------------------------------------------- #
def _sin_respaldo(r: dict) -> bool:
    if r.get("F01") == "No" or _es_desconocido(r.get("F01")):
        return True
    return r.get("F06") == "No" or r.get("F07") == "No"


def _programa_irrecuperable(r: dict) -> bool:
    """Sin respaldo Y sin via para leerlo del PLC: la reconstruccion se impone."""
    return _sin_respaldo(r) and (r.get("N06") == "No" or r.get("F13") == "No"
                                 or r.get("N05") == "No")


def decidir(respuestas: dict, riesgo: dict) -> dict:
    """Aplica el mapa de decision del cuestionario a este caso concreto.

    No inventa criterios: para cada alternativa comprueba condiciones basadas en
    los mismos codigos que el mapa cita, y devuelve el texto de la alternativa
    tal como esta publicado en `data/cuestionario.json`.
    """
    mapa = cuestionario.cargar()["mapa_decision"]["criterios_alternativa"]
    por_nombre = {a["alternativa"]: a for a in mapa}

    orden: list[tuple[str, str]] = []
    causas = _causa_raiz_externa(respuestas)
    if causas:
        orden.append((
            "Correccion de causa raiz (sin cambiar el controlador)",
            "Se evalua PRIMERO porque hay causa raiz externa sin corregir: "
            + "; ".join(causas) + ". Sustituir el controlador sin corregirla "
            "reproduce la falla en el equipo nuevo."))

    if _sin_respaldo(respuestas):
        orden.append((
            "Migracion a plataforma moderna" if not _programa_irrecuperable(respuestas)
            else "Reconstruccion del programa",
            "No hay respaldo verificado (F01/F06/F07)"
            + (" y no hay via para leer el programa del PLC (N05/N06/F13): el programa "
               "debe reconstruirse a partir del levantamiento funcional."
               if _programa_irrecuperable(respuestas)
               else ": la prioridad 1 es recuperarlo antes de cualquier decision.")))

    ciclo = respuestas.get("M01")
    plazo_insuficiente = (_rango(respuestas.get("M06"),
                                 ["En existencia en la planta o local", "Menos de 2 semanas",
                                  "De 2 a 8 semanas", "Mas de 8 semanas", "No se consigue"]) or 0) >= 2
    if ciclo in ("Descontinuado, aun con soporte y repuestos",
                 "Descontinuado y sin soporte (fin de vida)"):
        if plazo_insuficiente:
            orden.append((
                "Migracion a plataforma moderna",
                f"M01 '{ciclo}' y M06 con plazo mayor que la parada tolerable: el "
                "repuesto no cubre el riesgo, y la obsolescencia no se revierte "
                "reparando."))
        else:
            orden.append((
                "Repuesto directo (mismo modelo)",
                f"M01 '{ciclo}', pero el repuesto llega dentro de la parada tolerable: "
                "sirve como continuidad, con la migracion planificada en paralelo."))
    elif ciclo == "Anuncio de descontinuacion (phase-out)":
        orden.append((
            "Hardware equivalente o sustitucion parcial",
            f"M01 '{ciclo}': hay tiempo para planificar, pero no para ignorarlo."))
    elif ciclo in ("Activo, en comercializacion", "En madurez, ya existe un sucesor"):
        orden.append((
            "Reparacion del equipo existente",
            f"M01 '{ciclo}': el producto sigue vivo, la obsolescencia no es el problema."))

    if respuestas.get("Q04") == "No hay ventana disponible":
        orden.append((
            "Operacion temporal controlada",
            "Q04 no hay ventana de intervencion: cualquier plan definitivo necesita "
            "una fecha, y mientras tanto el riesgo se declara y se acepta por escrito."))

    # Sin duplicar alternativas, conservando el orden de prioridad.
    vistas, ruta = set(), []
    for nombre, porque in orden:
        if nombre in vistas or nombre not in por_nombre:
            continue
        vistas.add(nombre)
        ruta.append({**por_nombre[nombre], "porque_en_este_caso": porque})
    return {
        "clasificacion": riesgo.get("clasificacion"),
        "puntuacion": riesgo.get("puntuacion"),
        "ruta": ruta,
        "migrar": any(a["alternativa"] in ("Migracion a plataforma moderna",
                                           "Reconstruccion del programa") for a in ruta),
        "sin_respaldo": _sin_respaldo(respuestas),
        "irrecuperable": _programa_irrecuperable(respuestas),
    }


# --------------------------------------------------------------------------- #
# Presentacion y lectura de respuestas
# --------------------------------------------------------------------------- #
def _render_pregunta(p: dict, n: int, total: int) -> str:
    cabecera = (f"**Pregunta {n} de {total}** · Seccion {p['seccion']} — "
                f"{p['seccion_titulo']}  ·  `{p['codigo']}`")
    lineas = [cabecera, "", f"**{p['texto']}**", ""]
    tipo = p.get("tipo")
    if tipo == "numero":
        lineas.append("_Responde con un numero._")
    elif tipo in ("texto",):
        lineas.append("_Responde con tus palabras._")
    else:
        for i, op in enumerate(p.get("opciones") or [], 1):
            lineas.append(f"{i}. {op}")
        lineas.append("")
        if tipo == "seleccion_multiple":
            lineas.append("_Puedes elegir varias: escribe los numeros separados por "
                          "comas (p. ej. `1,4,7`)._")
        else:
            lineas.append("_Responde con el numero de la opcion, o escribela._")
    if p.get("regla_adaptativa"):
        lineas += ["", f"*{p['regla_adaptativa']}*"]
    return "\n".join(lineas)


def _interpretar(p: dict, texto: str):
    """Convierte lo escrito en el valor de la respuesta, o None si no se entiende."""
    t = (texto or "").strip()
    if not t:
        return None
    tipo = p.get("tipo")
    opciones = p.get("opciones") or []

    if tipo == "numero":
        limpio = t.replace(",", ".").split()[0]
        try:
            return str(int(float(limpio)))
        except ValueError:
            return None
    if tipo == "texto" or not opciones:
        return t

    def una(fragmento: str):
        f = fragmento.strip()
        if not f:
            return None
        if f.isdigit():
            i = int(f)
            return opciones[i - 1] if 1 <= i <= len(opciones) else None
        bajo = f.lower()
        for op in opciones:
            if op.lower() == bajo:
                return op
        # Coincidencia parcial: solo si es inequivoca, para no elegir por el usuario.
        parciales = [op for op in opciones if bajo in op.lower()]
        return parciales[0] if len(parciales) == 1 else None

    if tipo == "seleccion_multiple":
        elegidas = [una(f) for f in t.split(",")]
        elegidas = [e for e in elegidas if e]
        return elegidas or None
    return una(t)


def _guardar(caso: Caso, p: dict, valor) -> None:
    texto_valor = ", ".join(valor) if isinstance(valor, list) else str(valor)
    ejecutar_herramienta(caso, "guardar_respuestas", {"respuestas": [{
        "seccion": p["seccion"],
        "codigo": p["codigo"],
        "pregunta": p["texto"],
        "valor": texto_valor,
        "nivel_confianza": "no_determinado" if _es_desconocido(texto_valor) else "confianza_media",
        "fuente": "respuesta del usuario en la demo interactiva",
    }]}, aprobador_pendiente)


def _salida(texto: str, caso: Caso, estado: dict, acciones=None, fin=False) -> dict:
    return {"texto": texto, "acciones": acciones or [], "resumen": caso.resumen(),
            "fin": fin, "interactivo": True, "estado": estado}


# --------------------------------------------------------------------------- #
# Fases
# --------------------------------------------------------------------------- #
def iniciar() -> dict:
    """Texto de apertura y estado inicial de la sesion interactiva."""
    total = len([c for c, _ in GUION if _pregunta(c)])
    return {
        "texto": (
            "**[DEMO INTERACTIVA — sin clave de API]**\n\n"
            "Aqui no hay un caso grabado: **respondes tu y el motor trabaja con tus "
            "datos.** Las preguntas, sus opciones y sus ramas salen del cuestionario "
            "maestro; la puntuacion la calcula el motor de riesgo real sobre lo que "
            "contestes; y si procede migrar, te guio por el procedimiento de 50 pasos y su extension P1-P7 "
            "con la CPU que tu elijas.\n\n"
            f"Son unas {total} preguntas, y el recorrido se adapta: segun respondas, "
            "unas se abren y otras no se preguntan.\n\n"
            "Una advertencia honesta: **no puedo conversar en lenguaje libre.** Para "
            "eso hace falta el modelo, y eso es el **Caso real (API)**. Lo que si es "
            "real aqui es el motor: identificacion contra el catalogo, puntuacion, "
            "mapa de decision, procedimiento y expediente trazable.\n\n"
            "Empecemos por lo que ancla todo lo demas: **que equipo vas a diagnosticar?** "
            "Escribe marca, familia y modelo (p. ej. `Siemens S7-300 CPU 315-2 DP`)."
        ),
        "estado": {"fase": F_EQUIPO, "respuestas": {}},
    }


def _fase_equipo(caso: Caso, texto: str, estado: dict) -> dict:
    ident = fabricantes.identificar(texto)
    catalogado = ident["estado"] in ("modelo_exacto", "familia", "marca")
    estado["intento_equipo"] = True
    if not catalogado:
        parecidas = fabricantes.sugerencias(texto, limite=5)
        cuerpo = (f"**No encuentro '{texto.strip()}' en el catalogo verificado de 30 "
                  "fabricantes**, y no voy a asimilarlo a la marca mas parecida.")
        if parecidas:
            cuerpo += "\n\nLo que si tengo y se parece:\n\n" + "\n".join(
                f"{i}. **{s['marca']} {s['familia']}** — {s['modelos_documentados']}"
                for i, s in enumerate(parecidas, 1))
            cuerpo += ("\n\nEscribe el numero o el nombre completo. Si no es ninguna, "
                       "escribe `continuar` y sigo con el equipo sin identificar.")
            estado["sugerencias"] = [f"{s['marca']} {s['familia']}" for s in parecidas]
        else:
            cuerpo += ("\n\nEscribe el equipo corregido, o `continuar` para seguir con "
                       "el hardware marcado como no verificado.")
        return _salida(cuerpo, caso, estado)

    caso.fijar_equipo(ident)
    acciones = ["identificar_cpu"]
    ejecutar_herramienta(caso, "registrar_activo", {
        "tipo": "cpu",
        "descripcion": f"CPU {ident.get('modelo_identificado') or ident.get('familia') or texto.strip()}",
        "fabricante": ident.get("marca") or "",
        "modelo": ident.get("modelo_identificado") or "",
        "nivel_confianza": "confianza_media",
        "notas": f"Declarado por el usuario: '{texto.strip()}'.",
    }, aprobador_pendiente)
    acciones.append("registrar_activo")

    estado["fase"] = F_PREGUNTAS
    estado["ctx"] = {"marca": ident.get("marca"), "familia": ident.get("familia"),
                     "modelo": ident.get("modelo_identificado"),
                     "etiqueta": f"{ident.get('marca')} {ident.get('familia') or ''}".strip()}
    cabeza = fabricantes.anclaje(ident)
    siguiente = _siguiente_pregunta(estado)
    return _salida(cabeza + "\n\n---\n\n" + siguiente, caso, estado, acciones)


def _siguiente_pregunta(estado: dict) -> str:
    faltan = _pendientes(estado["respuestas"])
    if not faltan:
        return ""
    codigo = faltan[0]
    estado["actual"] = codigo
    p = _pregunta(codigo)
    hechas = len(estado["respuestas"])
    return _render_pregunta(p, hechas + 1, hechas + len(faltan))


def _fase_preguntas(caso: Caso, texto: str, estado: dict) -> dict:
    codigo = estado.get("actual")
    p = _pregunta(codigo) if codigo else None
    if p is None:
        estado["fase"] = F_RIESGO
        return _fase_riesgo(caso, estado)

    valor = _interpretar(p, texto)
    if valor is None:
        return _salida(
            "No entendi esa respuesta. " + _render_pregunta(p, len(estado["respuestas"]) + 1,
                                                            len(estado["respuestas"]) + len(_pendientes(estado["respuestas"]))),
            caso, estado)

    estado["respuestas"][codigo] = valor
    _guardar(caso, p, valor)

    siguiente = _siguiente_pregunta(estado)
    if not siguiente:
        estado["fase"] = F_RIESGO
        return _fase_riesgo(caso, estado, acciones=["guardar_respuestas"])
    eco = ", ".join(valor) if isinstance(valor, list) else valor
    return _salida(f"Anotado — `{codigo}`: **{eco}**\n\n---\n\n{siguiente}",
                   caso, estado, ["guardar_respuestas"])


def _fase_riesgo(caso: Caso, estado: dict, acciones=None) -> dict:
    respuestas = estado["respuestas"]
    calculados, omitidos = factores(respuestas)
    acciones = list(acciones or [])

    for clave in omitidos:
        ejecutar_herramienta(caso, "registrar_dato_faltante", {
            "descripcion": f"Factor '{scoring.ETIQUETAS_FACTOR.get(clave, clave)}' sin datos "
                           "suficientes para puntuarlo",
            "impacto": "El factor se omite y los pesos se renormalizan; la recomendacion "
                       "queda como preliminar en ese aspecto.",
        }, aprobador_pendiente)
        acciones.append("registrar_dato_faltante")

    salida_tool = ejecutar_herramienta(caso, "calcular_riesgo_obsolescencia",
                                       {"factores": calculados}, aprobador_pendiente)
    acciones.append("calcular_riesgo_obsolescencia")
    riesgo = caso.riesgo or {}
    estado["riesgo"] = {"puntuacion": riesgo.get("puntuacion"),
                        "clasificacion": riesgo.get("clasificacion")}

    filas = "\n".join(
        f"| {d['factor']} | {d['peso']:.2f} | {d['valor']:.0f} | {d['justificacion']} |"
        for d in riesgo.get("detalle_factores", []))
    texto = (
        f"## Riesgo de obsolescencia: **{riesgo.get('puntuacion')} / 100 — "
        f"{riesgo.get('clasificacion')}**\n\n"
        "Calculado por el motor real (`scoring.py`, Seccion 6) sobre **tus** respuestas. "
        "Cada factor lleva la justificacion con los codigos que lo sustentan:\n\n"
        "| Factor | Peso | Valor | Por que |\n|---|---|---|---|\n" + filas
    )
    if omitidos:
        texto += ("\n\n**Factores omitidos por falta de datos:** "
                  + ", ".join(scoring.ETIQUETAS_FACTOR.get(o, o) for o in omitidos)
                  + ". Los pesos se renormalizan sobre los factores disponibles: no se "
                    "penaliza ni se inventa lo que no se sabe, y el hueco queda "
                    "registrado como dato faltante en el expediente.")
    estado["fase"] = F_DECISION
    return _salida(texto + "\n\n---\n\nPulsa **Enviar** para ver que alternativa "
                           "corresponde a este caso.", caso, estado, acciones)


def _fase_decision(caso: Caso, estado: dict) -> dict:
    decision = decidir(estado["respuestas"], estado.get("riesgo") or {})
    estado["decision"] = decision

    partes = ["## Que procede en tu caso\n",
              "Aplico el mapa de decision del cuestionario. El orden importa: "
              "no es una lista de opciones, es una secuencia.\n"]
    for i, alt in enumerate(decision["ruta"], 1):
        partes.append(f"### {i}. {alt['alternativa']}")
        partes.append(f"**Por que en tu caso:** {alt['porque_en_este_caso']}")
        if alt.get("advertencias"):
            partes.append("**Advertencias:**")
            partes += [f"- {a}" for a in alt["advertencias"]]
        partes.append("")
    if not decision["ruta"]:
        partes.append("_Con las respuestas dadas no se cumple ningun criterio de forma "
                      "clara. Faltan datos: revisa los factores omitidos._")

    if decision["migrar"]:
        acciones = []
        disparador = ("sin_acceso_al_programa" if decision["irrecuperable"]
                      else "cpu_obsoleta")
        ejecutar_herramienta(caso, "iniciar_guia_migracion", {
            "disparador": disparador,
            "motivo": "Derivado del mapa de decision sobre las respuestas del usuario.",
            "decidido_por": "sugerencia_del_agente_aceptada",
            "sin_respaldo": decision["sin_respaldo"],
        }, aprobador_pendiente)
        acciones.append("iniciar_guia_migracion")
        estado["fase"] = F_DESTINO
        partes.append("---\n")
        partes.append("Como procede cambiar la CPU, **abro el modo guia** del "
                      "procedimiento de migracion. Pulsa **Enviar** y te presento las "
                      "opciones de CPU destino.")
        return _salida("\n".join(partes), caso, estado, acciones)

    estado["fase"] = F_FIN
    partes.append("---\n")
    partes.append("En tu caso **no procede cambiar la CPU todavia**, asi que no abro el "
                  "procedimiento de migracion. Pulsa **Enviar** para el informe final.")
    return _salida("\n".join(partes), caso, estado)


def _fuente_de_destino(destino: str, familias: list[dict], ruta: dict) -> str:
    """URL oficial de la familia destino, no la de cualquier familia vigente.

    Un fabricante puede tener varias generaciones actuales (Siemens tiene S7-1200
    y S7-1500). Tomar la primera de la lista citaria una fuente que no
    corresponde al destino elegido, que es peor que no citar ninguna.
    """
    objetivo = set(_norm_tokens(destino))
    mejor, mejor_peso = "", 0
    for fam in familias:
        comunes = objetivo & set(_norm_tokens(fam.get("familia", "")))
        peso = len(comunes)
        if peso > mejor_peso:
            fuentes = [f.get("url", "") for f in (fam.get("fuentes") or []) if f.get("url")]
            if fuentes:
                mejor, mejor_peso = fuentes[0], peso
    if mejor:
        return mejor
    # Sin coincidencia clara no se inventa una URL: se cita la guia metodologica.
    return ruta.get("cita", "")


def _norm_tokens(texto: str) -> list[str]:
    limpio = "".join(c.lower() if c.isalnum() else " " for c in str(texto or ""))
    return [t for t in limpio.split() if len(t) >= 2]


def _fase_destino(caso: Caso, texto: str, estado: dict) -> dict:
    ident = caso.equipo_identificado or {}
    if not estado.get("opciones_mostradas"):
        estado["opciones_mostradas"] = True
        opciones = procedimiento.opciones_destino(ident, limite_alternativas=8)
        estado["alternativas"] = [a["marca"] for a in
                                 (opciones.get("marca_alternativa", {}).get("mostradas") or [])]
        return _salida(
            procedimiento.texto_opciones(ident, limite_alternativas=8)
            + "\n\n---\n\n**Tu decision.** Escribe `A` para seguir con "
              f"**{ident.get('marca')}**, o `B` y el nombre de la marca que quieras "
              "evaluar (p. ej. `B OMRON`).",
            caso, estado)

    eleccion = (texto or "").strip()
    bajo = eleccion.lower()
    opciones = procedimiento.opciones_destino(ident, limite_alternativas=30)
    misma = opciones.get("misma_marca", {})

    if bajo.startswith("a"):
        familias = misma.get("familias_actuales") or []
        ruta = misma.get("ruta_publicada_para_el_origen") or {}
        destino = ruta.get("destino") or (familias[0]["familia"] if familias else "")
        fuente = _fuente_de_destino(destino, familias, ruta)
        marca_destino = ident.get("marca")
        justificacion = ("Continuidad de plataforma: conserva software, redes, repuestos "
                         "y personal formado, y existe herramienta oficial de conversion.")
    elif bajo.startswith("b"):
        pedida = eleccion[1:].strip(" .:-")
        todas = (opciones.get("marca_alternativa", {}).get("mostradas") or [])
        elegida = None
        for a in todas:
            if pedida and pedida.lower() in a["marca"].lower():
                elegida = a
                break
        if elegida is None:
            return _salida(
                "No reconoci esa marca entre las alternativas del catalogo. Escribe `B` "
                "seguido del nombre tal como aparece en la lista, o `A` para seguir con "
                f"**{ident.get('marca')}**.", caso, estado)
        fam = elegida["familias_actuales"][0]
        marca_destino, destino = elegida["marca"], fam["familia"]
        fuente = (fam.get("fuentes") or [{}])[0].get("url", "")
        justificacion = ("Eleccion del usuario: plataforma actual de otro fabricante. "
                         "Implica reescritura completa del programa, software y licencias "
                         "nuevos y capacitacion del personal.")
    else:
        return _salida("No entendi la eleccion. Escribe `A` para la misma marca, o `B` y "
                       "el nombre de la marca alternativa.", caso, estado)

    ejecutar_herramienta(caso, "fijar_cpu_destino", {
        "marca": marca_destino, "familia": destino,
        "justificacion": justificacion, "fuente": fuente,
    }, aprobador_pendiente)

    cambio = (caso.migracion or {}).get("cambio_marca")
    estado["fase"] = F_GUIA
    aviso = (
        "**Cambio de marca registrado.** Los pasos 21 y 22 (migrar con la herramienta "
        "oficial y revisar su reporte) quedan marcados como **no aplicables**: entre "
        "fabricantes distintos no existe conversion, el programa se reescribe desde cero."
        if cambio else
        "**Misma marca.** El procedimiento se mantiene completo: los pasos 21 y 22 si "
        "aplican, con la herramienta oficial de conversion del fabricante."
    )
    # Si la marca tiene ruta de conversion publicada, se anuncia aqui: es el momento
    # en que el usuario decide, y saber que la herramienta existe cambia la decision.
    resumen_ruta = procedimiento.texto_ruta_resumen(caso)
    if resumen_ruta:
        aviso += "\n\n" + resumen_ruta
    return _salida(
        f"Destino fijado: **{marca_destino} {destino}**.\n\n{aviso}\n\n---\n\n"
        "Empieza el recorrido de el procedimiento (57 pasos: 50 del documento + P1-P7). Pulsa **Enviar** para el primero.",
        caso, estado, ["fijar_cpu_destino"])


def _fase_guia(caso: Caso, texto: str, estado: dict) -> dict:
    ctx = procedimiento.contexto(caso)
    t = (texto or "").strip().lower()
    actual = estado.get("paso_guia")

    if actual and t in ("hecho", "listo", "completado", "ok", "si"):
        ejecutar_herramienta(caso, "marcar_paso_migracion",
                             {"paso": actual, "estado": "completado",
                              "nota": "Declarado cumplido por el usuario en la demo."},
                             aprobador_pendiente)
    elif actual and t in ("no aplica", "no_aplica", "na"):
        ejecutar_herramienta(caso, "marcar_paso_migracion",
                             {"paso": actual, "estado": "no_aplica",
                              "nota": "Declarado no aplicable por el usuario."},
                             aprobador_pendiente)
    elif actual and t in ("bloqueado", "no puedo", "no"):
        ejecutar_herramienta(caso, "marcar_paso_migracion",
                             {"paso": actual, "estado": "bloqueado",
                              "nota": "El usuario no puede cerrarlo ahora."},
                             aprobador_pendiente)
    elif actual and t in ("informe", "terminar", "fin"):
        estado["fase"] = F_FIN
        return _fase_fin(caso, estado)

    siguiente = procedimiento.siguiente(caso)
    if siguiente is None:
        estado["fase"] = F_FIN
        return _fase_fin(caso, estado)

    estado["paso_guia"] = siguiente["clave"]
    avance = procedimiento.estado(caso)
    cuerpo = procedimiento.texto_paso(siguiente["clave"], ctx)
    # Los pasos que la ruta del fabricante especializa (13, 20, 21, 22 y 23 en Siemens)
    # se muestran con sus sub-pasos concretos; el resto queda igual que siempre.
    cuerpo += procedimiento.texto_ruta_para_paso(siguiente["clave"], caso, ctx)
    if siguiente.get("prerrequisitos_pendientes"):
        cuerpo += ("\n\n🚧 **Este paso no puede ejecutarse todavia:** faltan los pasos "
                   + ", ".join(str(x) for x in siguiente["prerrequisitos_pendientes"])
                   + ". El procedimiento lo impide, no es criterio mio.")
    pie = (f"\n\n---\n\n*Avance: {avance['cerrados']} de {avance['total_pasos']} "
           f"({avance['porcentaje']}%) · fase {avance['fase_actual']}*\n\n"
           "Escribe **`hecho`** para cerrarlo, **`no aplica`**, **`bloqueado`**, "
           "o **`informe`** para terminar y generar el informe.")
    return _salida(cuerpo + pie, caso, estado, ["marcar_paso_migracion"] if actual else [])


def _fase_fin(caso: Caso, estado: dict) -> dict:
    ident = caso.equipo_identificado or {}
    riesgo = caso.riesgo or {}
    decision = estado.get("decision") or {}
    mig = caso.migracion or {}
    destino = (mig.get("destino") or {})
    resumen = caso.resumen()

    ruta = "\n".join(f"{i}. **{a['alternativa']}** — {a['porque_en_este_caso']}"
                     for i, a in enumerate(decision.get("ruta", []), 1)) or "Sin ruta determinada."
    detalle = "\n".join(f"- {d['factor']} (peso {d['peso']:.2f}): {d['valor']:.0f} — "
                        f"{d['justificacion']}"
                        for d in riesgo.get("detalle_factores", []))
    equipo = f"{ident.get('marca')} {ident.get('familia') or ''}".strip() or "equipo sin identificar"

    cuerpo = (
        f"## 1. Identificacion\nCaso interactivo. {equipo}"
        + (f" ({ident.get('modelo_identificado')})" if ident.get("modelo_identificado") else "")
        + ".\n\n"
        "## 2. Resumen ejecutivo\nDiagnostico construido sobre las respuestas dadas por "
        "el usuario en la demo interactiva, con el motor de riesgo y el mapa de decision "
        "reales.\n\n"
        f"## 3. Informacion confirmada\n{len(resumen['respuestas_registradas'])} respuestas "
        f"registradas: {', '.join(resumen['respuestas_registradas'])}.\n\n"
        "## 4. Informacion no confirmada\nTodas las respuestas provienen de la declaracion "
        "del usuario; ninguna esta verificada contra placa, manual ni fuente oficial.\n\n"
        "## 5. Datos faltantes\n"
        + ("\n".join(f"- {d}" for d in resumen["datos_faltantes"]) or "Ninguno registrado.")
        + "\n\n"
        f"## 6. Estado y puntuacion de obsolescencia\n{riesgo.get('puntuacion')} / 100 — "
        f"**{riesgo.get('clasificacion')}**.\n\n{detalle}\n\n"
        "## 7. Riesgos\nLos que se desprenden de los factores anteriores.\n\n"
        f"## 8. Alternativas\n{ruta}\n\n"
        "## 9. Recomendacion principal\n"
        + (f"Migrar a **{destino.get('marca')} {destino.get('familia')}**"
           + (" (cambio de marca: reescritura completa del programa)"
              if mig.get("cambio_marca") else " (misma marca: conversion con herramienta oficial)")
           if destino else "No procede cambiar la CPU con los datos actuales.")
        + "\n\n"
        "## 10. Hardware preliminar\nSin numeros de catalogo confirmados: deben "
        "verificarse con el fabricante y su herramienta oficial de seleccion.\n\n"
        "## 11. Plan de respaldo, migracion y retorno\n"
        + (f"Procedimiento MIGRA-IA-PROC-050, avance {procedimiento.estado(caso)['cerrados']} "
           f"de {procedimiento.total_pasos()} pasos (50 del documento mas la extension "
           "P1-P7 de construccion del programa)."
           if mig.get("activa") else "No abierto.")
        + "\n\n"
        "## 12. Plan de pruebas\nFAT (pasos 31-33) y SAT (pasos 42-44) del procedimiento.\n\n"
        "## 13. Nivel de confianza y fuentes\nConfianza media. Fuentes: respuestas del "
        "usuario y catalogo verificado de fabricantes. Este informe procede de una "
        "demostracion interactiva determinista, sin intervencion de un modelo de lenguaje."
    )
    ejecutar_herramienta(caso, "generar_informe", {
        "titulo": f"Diagnostico interactivo — {equipo}",
        "nivel_confianza_global": "confianza_media",
        "resumen": f"{riesgo.get('clasificacion')}; ruta de decision aplicada sobre las "
                   "respuestas del usuario.",
        "cuerpo_markdown": cuerpo,
    }, aprobador_pendiente)

    estado["fase"] = F_FIN
    return _salida(
        "## Informe generado\n\n"
        "Se guardo en la carpeta `casos/` junto al expediente JSON, con las 13 secciones "
        "de la estructura estandar.\n\n"
        "Fijate en lo que acaba de pasar: **ningun modelo de lenguaje ha intervenido.** "
        "La identificacion salio del catalogo verificado, la puntuacion del motor de "
        "riesgo sobre tus respuestas, la recomendacion del mapa de decision y el paso a "
        "paso del procedimiento. Mismo caso, mismo resultado, siempre.\n\n"
        "Para el dialogo en lenguaje libre -que es lo unico que esto no puede hacer- "
        "esta el **Caso real (API)**.",
        caso, estado, ["generar_informe"], fin=True)


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def responder(caso: Caso, texto: str, estado: dict | None) -> dict:
    """Avanza la sesion interactiva un turno, segun la fase en que este."""
    estado = dict(estado or {"fase": F_EQUIPO, "respuestas": {}})
    fase = estado.get("fase", F_EQUIPO)

    if fase == F_EQUIPO:
        # 'continuar' solo salta la identificacion DESPUES de haberlo intentado:
        # si no, un Enviar en vacio al arrancar arrancaria el caso sin equipo.
        if (texto or "").strip().lower() in ("continuar", "seguir"):
            if not estado.get("intento_equipo"):
                return _salida(
                    "Necesito el equipo antes de empezar: es lo que ancla todo el "
                    "diagnostico.\n\nEscribe **marca, familia y modelo** de tu PLC "
                    "(p. ej. `Siemens S7-300 CPU 315-2 DP`).", caso, estado)
            estado["fase"] = F_PREGUNTAS
            estado.setdefault("ctx", {})
            return _salida(
                "De acuerdo: sigo con el equipo **sin identificar**. Todo lo que diga "
                "sobre hardware queda como preliminar y no verificado.\n\n---\n\n"
                + _siguiente_pregunta(estado), caso, estado)
        return _fase_equipo(caso, texto, estado)
    if fase == F_PREGUNTAS:
        return _fase_preguntas(caso, texto, estado)
    if fase == F_RIESGO:
        return _fase_riesgo(caso, estado)
    if fase == F_DECISION:
        return _fase_decision(caso, estado)
    if fase == F_DESTINO:
        return _fase_destino(caso, texto, estado)
    if fase == F_GUIA:
        return _fase_guia(caso, texto, estado)
    return _fase_fin(caso, estado)
