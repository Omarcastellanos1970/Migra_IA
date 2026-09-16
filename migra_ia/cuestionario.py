"""Cuestionario maestro adaptativo de MIGRA-IA (data/es/questionnaire.json).

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
_CLAVES_PREGUNTAS = ("questions", "branch_yes", "branch_no", "final_questions")
_CLAVES_CAMPOS = ("fields_by_module", "fields_by_device")


@lru_cache(maxsize=1)
def cargar() -> dict:
    """Carga y cachea el cuestionario desde disco."""
    with open(config.RUTA_CUESTIONARIO, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(texto: str) -> str:
    return (texto or "").strip().lower()


def _items_de_seccion(sec: dict) -> list[dict]:
    """Aplana en una lista todas las preguntas o campos de una seccion.

    Devuelve entradas normalizadas con 'code' y 'text', conservando el resto
    de atributos (tipo, opciones, regla_adaptativa, ejemplo...) tal cual.
    """
    items: list[dict] = []
    for clave in _CLAVES_PREGUNTAS:
        for p in sec.get(clave, []):
            entrada = dict(p)
            if clave in ("branch_yes", "branch_no"):
                entrada["branch"] = "si" if clave == "branch_yes" else "no"
            items.append(entrada)
    for clave in _CLAVES_CAMPOS:
        for c in sec.get(clave, []):
            entrada = dict(c)
            entrada.setdefault("code", "")
            # Las secciones de inventario describen campos, no preguntas.
            entrada.setdefault("text", c.get("field", ""))
            items.append(entrada)
    return items


def _todas_las_preguntas() -> dict[str, dict]:
    """Indice {codigo: pregunta} de todo el cuestionario, con su seccion."""
    indice: dict[str, dict] = {}
    for sec in cargar()["sections"]:
        for item in _items_de_seccion(sec):
            codigo = item.get("code") or ""
            if codigo:
                indice[codigo.upper()] = {**item, "section": sec["id"], "seccion_titulo": sec["title"]}
    return indice


def pregunta(codigo: str) -> dict | None:
    """Pregunta del cuestionario por su codigo (p. ej. 'M01'), con su seccion.

    Devuelve el item tal cual esta en `data/es/questionnaire.json`, incluidas las de
    las ramas adaptativas. Es la via para que otros modulos presenten el texto y
    las opciones REALES sin duplicarlos en el codigo.
    """
    return _todas_las_preguntas().get((codigo or "").strip().upper())


def _rango_codigos(items: list[dict]) -> str:
    """Etiqueta compacta del rango de codigos de una seccion (p. ej. 'M01-M10')."""
    codigos = [i["code"] for i in items if i.get("code")]
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
    for sec in cuest["sections"]:
        items = _items_de_seccion(sec)
        lineas.append(f"[{sec['id']}] {sec['title']} ({_rango_codigos(items)}, {len(items)} items)")
        que_decide = sec.get("what_it_decides")
        if que_decide:
            lineas.append(f"     que decide: {que_decide}")
    return "\n".join(lineas)


def criterios_para_prompt() -> str:
    """Criterios de decision (reparar vs. migrar) y reglas de prioridad."""
    mapa = cargar().get("decision_map", {})
    lineas = []
    for regla in mapa.get("priority_rules", []):
        lineas.append(f"  {regla}")
    lineas.append("")
    lineas.append("  ALTERNATIVAS, en el orden en que deben evaluarse:")
    for alt in mapa.get("alternative_criteria", []):
        marca = "  *" if alt.get("evaluate_first") else "  -"
        lineas.append(f"{marca} {alt['alternative']}")
        favorables = "; ".join(alt.get("favorable_conditions", []))
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
    secciones = cuest["sections"]
    if clave in (None, ""):
        return [{"id": s["id"], "title": s["title"], "what_it_decides": s.get("what_it_decides", "")} for s in secciones]
    k = _norm(str(clave))
    # 1) coincidencia exacta por letra de seccion; 2) subcadena en el titulo.
    for s in secciones:
        if k == _norm(s["id"]):
            return {**s, "items": _items_de_seccion(s)}
    for s in secciones:
        if k in _norm(s["title"]):
            return {**s, "items": _items_de_seccion(s)}
    # 3) si pasaron un codigo de pregunta (p. ej. 'M06'), devolver su seccion.
    pregunta = _todas_las_preguntas().get(k.upper())
    if pregunta:
        for s in secciones:
            if s["id"] == pregunta["section"]:
                return {**s, "items": _items_de_seccion(s)}
    return None


def _buscar_pregunta(cuest: dict, clave):
    preguntas = _todas_las_preguntas()
    if clave in (None, ""):
        return [{"code": c, "text": p.get("text", "")} for c, p in preguntas.items()]
    k = _norm(str(clave))
    exacta = preguntas.get(k.upper())
    if exacta:
        return exacta
    coincidencias = [p for c, p in preguntas.items() if k in _norm(p.get("text", ""))]
    return coincidencias or None


def _buscar_factor(cuest: dict, clave):
    """Devuelve un factor de riesgo con su peso vivo y las preguntas que lo nutren.

    El peso NO se duplica en el JSON: se toma de migra_ia/scoring.py para que
    cuestionario y motor de puntuacion no puedan desincronizarse.
    """
    factores = cuest.get("decision_map", {}).get("risk_factors", [])
    preguntas = _todas_las_preguntas()

    def _expandir(f: dict) -> dict:
        detalle = []
        for codigo in f.get("questions", []):
            p = preguntas.get(codigo.upper())
            detalle.append({"code": codigo, "text": p.get("text", "") if p else "(codigo no encontrado)"})
        return {
            "key": f["key"],
            "label": ETIQUETAS_FACTOR.get(f["key"], f["key"]),
            "peso": PESOS.get(f["key"]),
            "guide": f.get("guide", ""),
            "questions": detalle,
        }

    if clave in (None, ""):
        return [_expandir(f) for f in factores]
    k = _norm(str(clave))
    for f in factores:
        if k == _norm(f["key"]) or k in _norm(ETIQUETAS_FACTOR.get(f["key"], "")):
            return _expandir(f)
    return None


def _buscar_criterio(cuest: dict, clave):
    alternativas = cuest.get("decision_map", {}).get("alternative_criteria", [])
    if clave in (None, ""):
        return alternativas
    k = _norm(str(clave))
    for alt in alternativas:
        if k in _norm(alt["alternative"]):
            return alt
    return None


def _buscar_texto(cuest: dict, clave):
    """Busqueda libre por texto en preguntas y reglas adaptativas."""
    if clave in (None, ""):
        return None
    k = _norm(str(clave))
    resultados = []
    for codigo, p in _todas_las_preguntas().items():
        if k in _norm(p.get("text", "")) or k in _norm(p.get("adaptive_rule", "")):
            resultados.append({
                "code": codigo,
                "section": p["section"],
                "text": p.get("text", ""),
                "adaptive_rule": p.get("adaptive_rule", ""),
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
        "section": lambda: _buscar_seccion(cuest, clave),
        "sections": lambda: _buscar_seccion(cuest, clave),
        "question": lambda: _buscar_pregunta(cuest, clave),
        "questions": lambda: _buscar_pregunta(cuest, clave),
        "decision_map": lambda: cuest.get("decision_map", {}),
        "factor": lambda: _buscar_factor(cuest, clave),
        "factors": lambda: _buscar_factor(cuest, clave),
        "criteria": lambda: _buscar_criterio(cuest, clave),
        "alternative": lambda: _buscar_criterio(cuest, clave),
        "prioridades": lambda: {"priority_rules": cuest.get("decision_map", {}).get("priority_rules", [])},
        "buscar": lambda: _buscar_texto(cuest, clave),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "citation": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{clave}' en el tema '{tema}'", "citation": cita}
    return {"tema": t, "key": clave, "citation": cita, "contenido": resultado}
