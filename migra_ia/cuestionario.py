"""Cuestionario maestro adaptativo de MIGRA-IA (data/cuestionario.json).

Carga el cuestionario y expone consultas para que el agente sepa QUE preguntar,
POR QUE lo pregunta y QUE decision alimenta cada respuesta. Incluye el bloque
`mapa_decision`, que enlaza cada pregunta con el factor de riesgo que nutre
(migra_ia/scoring.py) y con los criterios de cada alternativa (reparar, repuesto,
equivalente, migrar, reconstruir, operacion temporal).

Igual que la base de conocimiento, el detalle NO se vuelca al prompt: el system
prompt lleva un indice compacto (`indice_para_prompt`) mas los criterios de
decision (`criterios_para_prompt`), y el agente pide el detalle bajo demanda con
la herramienta `consultar_cuestionario`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config
from .scoring import ETIQUETAS_FACTOR, PESOS

# Claves donde viven listas de preguntas dentro de una seccion. Las secciones de
# inventario (E, J) usan en su lugar listas de campos por registro.
_CLAVES_PREGUNTAS = ("preguntas", "rama_si", "rama_no", "preguntas_finales")
_CLAVES_CAMPOS = ("campos_por_modulo", "campos_por_dispositivo")


@lru_cache(maxsize=1)
def cargar() -> dict:
    """Carga y cachea el cuestionario desde disco."""
    with open(config.RUTA_CUESTIONARIO, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(texto: str) -> str:
    return (texto or "").strip().lower()


def _items_de_seccion(sec: dict) -> list[dict]:
    """Aplana en una lista todas las preguntas o campos de una seccion.

    Devuelve entradas normalizadas con 'codigo' y 'texto', conservando el resto
    de atributos (tipo, opciones, regla_adaptativa, ejemplo...) tal cual.
    """
    items: list[dict] = []
    for clave in _CLAVES_PREGUNTAS:
        for p in sec.get(clave, []):
            entrada = dict(p)
            if clave in ("rama_si", "rama_no"):
                entrada["rama"] = "si" if clave == "rama_si" else "no"
            items.append(entrada)
    for clave in _CLAVES_CAMPOS:
        for c in sec.get(clave, []):
            entrada = dict(c)
            entrada.setdefault("codigo", "")
            # Las secciones de inventario describen campos, no preguntas.
            entrada.setdefault("texto", c.get("campo", ""))
            items.append(entrada)
    return items


def _todas_las_preguntas() -> dict[str, dict]:
    """Indice {codigo: pregunta} de todo el cuestionario, con su seccion."""
    indice: dict[str, dict] = {}
    for sec in cargar()["secciones"]:
        for item in _items_de_seccion(sec):
            codigo = item.get("codigo") or ""
            if codigo:
                indice[codigo.upper()] = {**item, "seccion": sec["id"], "seccion_titulo": sec["titulo"]}
    return indice


def _rango_codigos(items: list[dict]) -> str:
    """Etiqueta compacta del rango de codigos de una seccion (p. ej. 'M01-M10')."""
    codigos = [i["codigo"] for i in items if i.get("codigo")]
    if not codigos:
        return "campos por registro"
    if len(codigos) == 1:
        return codigos[0]
    return f"{codigos[0]}-{codigos[-1]}"


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
def indice_para_prompt() -> str:
    """Indice de secciones con su rango de codigos y QUE decide cada una."""
    cuest = cargar()
    lineas = []
    for sec in cuest["secciones"]:
        items = _items_de_seccion(sec)
        lineas.append(f"[{sec['id']}] {sec['titulo']} ({_rango_codigos(items)}, {len(items)} items)")
        que_decide = sec.get("que_decide")
        if que_decide:
            lineas.append(f"     que decide: {que_decide}")
    return "\n".join(lineas)


def criterios_para_prompt() -> str:
    """Criterios de decision (reparar vs. migrar) y reglas de prioridad."""
    mapa = cargar().get("mapa_decision", {})
    lineas = []
    for regla in mapa.get("reglas_de_prioridad", []):
        lineas.append(f"  {regla}")
    lineas.append("")
    lineas.append("  ALTERNATIVAS, en el orden en que deben evaluarse:")
    for alt in mapa.get("criterios_alternativa", []):
        marca = "  *" if alt.get("evaluar_primero") else "  -"
        lineas.append(f"{marca} {alt['alternativa']}")
        favorables = "; ".join(alt.get("condiciones_favorables", []))
        if favorables:
            lineas.append(f"      a favor: {favorables}")
        advertencias = " ".join(alt.get("advertencias", []))
        if advertencias:
            lineas.append(f"      ojo: {advertencias}")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Consulta (usada por la herramienta consultar_cuestionario)
# --------------------------------------------------------------------------- #
def _buscar_seccion(cuest: dict, clave):
    secciones = cuest["secciones"]
    if clave in (None, ""):
        return [{"id": s["id"], "titulo": s["titulo"], "que_decide": s.get("que_decide", "")} for s in secciones]
    k = _norm(str(clave))
    # 1) coincidencia exacta por letra de seccion; 2) subcadena en el titulo.
    for s in secciones:
        if k == _norm(s["id"]):
            return {**s, "items": _items_de_seccion(s)}
    for s in secciones:
        if k in _norm(s["titulo"]):
            return {**s, "items": _items_de_seccion(s)}
    # 3) si pasaron un codigo de pregunta (p. ej. 'M06'), devolver su seccion.
    pregunta = _todas_las_preguntas().get(k.upper())
    if pregunta:
        for s in secciones:
            if s["id"] == pregunta["seccion"]:
                return {**s, "items": _items_de_seccion(s)}
    return None


def _buscar_pregunta(cuest: dict, clave):
    preguntas = _todas_las_preguntas()
    if clave in (None, ""):
        return [{"codigo": c, "texto": p.get("texto", "")} for c, p in preguntas.items()]
    k = _norm(str(clave))
    exacta = preguntas.get(k.upper())
    if exacta:
        return exacta
    coincidencias = [p for c, p in preguntas.items() if k in _norm(p.get("texto", ""))]
    return coincidencias or None


def _buscar_factor(cuest: dict, clave):
    """Devuelve un factor de riesgo con su peso vivo y las preguntas que lo nutren.

    El peso NO se duplica en el JSON: se toma de migra_ia/scoring.py para que
    cuestionario y motor de puntuacion no puedan desincronizarse.
    """
    factores = cuest.get("mapa_decision", {}).get("factores_riesgo", [])
    preguntas = _todas_las_preguntas()

    def _expandir(f: dict) -> dict:
        detalle = []
        for codigo in f.get("preguntas", []):
            p = preguntas.get(codigo.upper())
            detalle.append({"codigo": codigo, "texto": p.get("texto", "") if p else "(codigo no encontrado)"})
        return {
            "clave": f["clave"],
            "etiqueta": ETIQUETAS_FACTOR.get(f["clave"], f["clave"]),
            "peso": PESOS.get(f["clave"]),
            "guia": f.get("guia", ""),
            "preguntas": detalle,
        }

    if clave in (None, ""):
        return [_expandir(f) for f in factores]
    k = _norm(str(clave))
    for f in factores:
        if k == _norm(f["clave"]) or k in _norm(ETIQUETAS_FACTOR.get(f["clave"], "")):
            return _expandir(f)
    return None


def _buscar_criterio(cuest: dict, clave):
    alternativas = cuest.get("mapa_decision", {}).get("criterios_alternativa", [])
    if clave in (None, ""):
        return alternativas
    k = _norm(str(clave))
    for alt in alternativas:
        if k in _norm(alt["alternativa"]):
            return alt
    return None


def _buscar_texto(cuest: dict, clave):
    """Busqueda libre por texto en preguntas y reglas adaptativas."""
    if clave in (None, ""):
        return None
    k = _norm(str(clave))
    resultados = []
    for codigo, p in _todas_las_preguntas().items():
        if k in _norm(p.get("texto", "")) or k in _norm(p.get("regla_adaptativa", "")):
            resultados.append({
                "codigo": codigo,
                "seccion": p["seccion"],
                "texto": p.get("texto", ""),
                "regla_adaptativa": p.get("regla_adaptativa", ""),
            })
    return resultados or None


def consultar(tema: str, clave=None) -> dict:
    """Devuelve el fragmento del cuestionario pedido, con estructura estable.

    `tema` (obligatorio) y `clave` (opcional) provienen de la herramienta
    `consultar_cuestionario`.
    """
    cuest = cargar()
    cita = f"Cuestionario maestro MIGRA-IA v{cuest['version']}"
    t = _norm(tema)

    despacho = {
        "indice": lambda: {"indice": indice_para_prompt()},
        "seccion": lambda: _buscar_seccion(cuest, clave),
        "secciones": lambda: _buscar_seccion(cuest, clave),
        "pregunta": lambda: _buscar_pregunta(cuest, clave),
        "preguntas": lambda: _buscar_pregunta(cuest, clave),
        "mapa_decision": lambda: cuest.get("mapa_decision", {}),
        "factor": lambda: _buscar_factor(cuest, clave),
        "factores": lambda: _buscar_factor(cuest, clave),
        "criterios": lambda: _buscar_criterio(cuest, clave),
        "alternativa": lambda: _buscar_criterio(cuest, clave),
        "prioridades": lambda: {"reglas_de_prioridad": cuest.get("mapa_decision", {}).get("reglas_de_prioridad", [])},
        "buscar": lambda: _buscar_texto(cuest, clave),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "cita": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{clave}' en el tema '{tema}'", "cita": cita}
    return {"tema": t, "clave": clave, "cita": cita, "contenido": resultado}
