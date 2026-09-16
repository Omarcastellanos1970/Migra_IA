"""Cuestionario maestro adaptativo de MIGRA-IA (data/es/questionnaire.json).

Carga el cuestionario y expone consultas para que el agente sepa QUE preguntar,
POR QUE lo pregunta y QUE decision alimenta cada respuesta. Incluye el bloque
`mapa_decision`, que enlaza cada pregunta con el factor de riesgo que nutre
(migra_ia/scoring.py) y con los criterios de cada alternativa (reparar, repuesto,
equivalente, migrar, reconstruir, operacion temporal).

Igual que la base de conocimiento, el detalle NO se vuelca al prompt: el system
prompt lleva un indice compacto (`indice_para_prompt`) mas los criterios de
decision (`criterios_para_prompt`), y el agente pide el detalle bajo demanda con
la herramienta `query_questionnaire`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config
from .scoring import FACTOR_LABELS, WEIGHTS

# Claves donde viven listas de preguntas dentro de una seccion. Las secciones de
# inventario (E, J) usan en su lugar listas de campos por registro.
_CLAVES_PREGUNTAS = ("questions", "branch_yes", "branch_no", "final_questions")
_CLAVES_CAMPOS = ("fields_by_module", "fields_by_device")


@lru_cache(maxsize=len(config.LANGUAGES))
def _load(lang: str) -> dict:
    with open(config.questionnaire_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def load() -> dict:
    """Carga y cachea el cuestionario del idioma de esta peticion.

    La cache va indexada POR IDIOMA, no por proceso: un mismo servidor puede
    tener los dos cargados a la vez y atender simultaneamente a quien eligio
    espaniol y a quien eligio ingles.
    """
    return _load(config.language())


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def _section_items(sec: dict) -> list[dict]:
    """Aplana en una lista todas las preguntas o campos de una seccion.

    Devuelve entradas normalizadas con 'code' y 'text', conservando el resto
    de atributos (tipo, opciones, regla_adaptativa, ejemplo...) tal cual.
    """
    items: list[dict] = []
    for key in _CLAVES_PREGUNTAS:
        for p in sec.get(key, []):
            entry = dict(p)
            if key in ("branch_yes", "branch_no"):
                entry["branch"] = "si" if key == "branch_yes" else "no"
            items.append(entry)
    for key in _CLAVES_CAMPOS:
        for c in sec.get(key, []):
            entry = dict(c)
            entry.setdefault("code", "")
            # Las secciones de inventario describen campos, no preguntas.
            entry.setdefault("text", c.get("field", ""))
            items.append(entry)
    return items


def _all_questions() -> dict[str, dict]:
    """Indice {codigo: pregunta} de todo el cuestionario, con su seccion."""
    index_: dict[str, dict] = {}
    for sec in load()["sections"]:
        for item in _section_items(sec):
            code = item.get("code") or ""
            if code:
                index_[code.upper()] = {**item, "section": sec["id"], "seccion_titulo": sec["title"]}
    return index_


def question(code: str) -> dict | None:
    """Pregunta del cuestionario por su codigo (p. ej. 'M01'), con su seccion.

    Devuelve el item tal cual esta en `data/es/questionnaire.json`, incluidas las de
    las ramas adaptativas. Es la via para que otros modulos presenten el texto y
    las opciones REALES sin duplicarlos en el codigo.
    """
    return _all_questions().get((code or "").strip().upper())


def _code_range(items: list[dict]) -> str:
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
def prompt_index() -> str:
    """Indice de secciones con su rango de codigos y QUE decide cada una."""
    cuest = load()
    lineas = []
    for sec in cuest["sections"]:
        items = _section_items(sec)
        lineas.append(f"[{sec['id']}] {sec['title']} ({_code_range(items)}, {len(items)} items)")
        que_decide = sec.get("what_it_decides")
        if que_decide:
            lineas.append(f"     que decide: {que_decide}")
    return "\n".join(lineas)


def prompt_criteria() -> str:
    """Criterios de decision (reparar vs. migrar) y reglas de prioridad."""
    mapa = load().get("decision_map", {})
    lineas = []
    for regla in mapa.get("priority_rules", []):
        lineas.append(f"  {regla}")
    lineas.append("")
    lineas.append("  ALTERNATIVAS, en el orden en que deben evaluarse:")
    for alt in mapa.get("alternative_criteria", []):
        brand = "  *" if alt.get("evaluate_first") else "  -"
        lineas.append(f"{brand} {alt['alternative']}")
        favorables = "; ".join(alt.get("favorable_conditions", []))
        if favorables:
            lineas.append(f"      a favor: {favorables}")
        advertencias = " ".join(alt.get("advertencias", []))
        if advertencias:
            lineas.append(f"      ojo: {advertencias}")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Consulta (usada por la herramienta query_questionnaire)
# --------------------------------------------------------------------------- #
def _find_section(cuest: dict, key):
    sections = cuest["sections"]
    if key in (None, ""):
        return [{"id": s["id"], "title": s["title"], "what_it_decides": s.get("what_it_decides", "")} for s in sections]
    k = _norm(str(key))
    # 1) coincidencia exacta por letra de seccion; 2) subcadena en el titulo.
    for s in sections:
        if k == _norm(s["id"]):
            return {**s, "items": _section_items(s)}
    for s in sections:
        if k in _norm(s["title"]):
            return {**s, "items": _section_items(s)}
    # 3) si pasaron un codigo de pregunta (p. ej. 'M06'), devolver su seccion.
    question = _all_questions().get(k.upper())
    if question:
        for s in sections:
            if s["id"] == question["section"]:
                return {**s, "items": _section_items(s)}
    return None


def _find_question(cuest: dict, key):
    questions = _all_questions()
    if key in (None, ""):
        return [{"code": c, "text": p.get("text", "")} for c, p in questions.items()]
    k = _norm(str(key))
    exacta = questions.get(k.upper())
    if exacta:
        return exacta
    coincidencias = [p for c, p in questions.items() if k in _norm(p.get("text", ""))]
    return coincidencias or None


def _find_factor(cuest: dict, key):
    """Devuelve un factor de riesgo con su peso vivo y las preguntas que lo nutren.

    El peso NO se duplica en el JSON: se toma de migra_ia/scoring.py para que
    cuestionario y motor de puntuacion no puedan desincronizarse.
    """
    factors = cuest.get("decision_map", {}).get("risk_factors", [])
    questions = _all_questions()

    def _expand(f: dict) -> dict:
        detail = []
        for code in f.get("questions", []):
            p = questions.get(code.upper())
            detail.append({"code": code, "text": p.get("text", "") if p else "(codigo no encontrado)"})
        return {
            "key": f["key"],
            "label": FACTOR_LABELS.get(f["key"], f["key"]),
            "peso": WEIGHTS.get(f["key"]),
            "guide": f.get("guide", ""),
            "questions": detail,
        }

    if key in (None, ""):
        return [_expand(f) for f in factors]
    k = _norm(str(key))
    for f in factors:
        if k == _norm(f["key"]) or k in _norm(FACTOR_LABELS.get(f["key"], "")):
            return _expand(f)
    return None


def _find_criterion(cuest: dict, key):
    alternativas = cuest.get("decision_map", {}).get("alternative_criteria", [])
    if key in (None, ""):
        return alternativas
    k = _norm(str(key))
    for alt in alternativas:
        if k in _norm(alt["alternative"]):
            return alt
    return None


def _find_text(cuest: dict, key):
    """Busqueda libre por texto en preguntas y reglas adaptativas."""
    if key in (None, ""):
        return None
    k = _norm(str(key))
    resultados = []
    for code, p in _all_questions().items():
        if k in _norm(p.get("text", "")) or k in _norm(p.get("adaptive_rule", "")):
            resultados.append({
                "code": code,
                "section": p["section"],
                "text": p.get("text", ""),
                "adaptive_rule": p.get("adaptive_rule", ""),
            })
    return resultados or None


def query(tema: str, key=None) -> dict:
    """Devuelve el fragmento del cuestionario pedido, con estructura estable.

    `tema` (obligatorio) y `clave` (opcional) provienen de la herramienta
    `query_questionnaire`.
    """
    cuest = load()
    cita = f"Cuestionario maestro MIGRA-IA v{cuest['version']}"
    t = _norm(tema)

    despacho = {
        "indice": lambda: {"indice": prompt_index()},
        "section": lambda: _find_section(cuest, key),
        "sections": lambda: _find_section(cuest, key),
        "question": lambda: _find_question(cuest, key),
        "questions": lambda: _find_question(cuest, key),
        "decision_map": lambda: cuest.get("decision_map", {}),
        "factor": lambda: _find_factor(cuest, key),
        "factors": lambda: _find_factor(cuest, key),
        "criteria": lambda: _find_criterion(cuest, key),
        "alternative": lambda: _find_criterion(cuest, key),
        "prioridades": lambda: {"priority_rules": cuest.get("decision_map", {}).get("priority_rules", [])},
        "buscar": lambda: _find_text(cuest, key),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "citation": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{key}' en el tema '{tema}'", "citation": cita}
    return {"tema": t, "key": key, "citation": cita, "contenido": resultado}
