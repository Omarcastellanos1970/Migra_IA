"""Base de conocimiento de MIGRA-IA (Guia MIGRA-IA-GUIA-001).

Carga la guia integral de migracion (data/es/knowledge_base.json) y expone
consultas para que el agente estructure el diagnostico por las seis etapas de la
metodologia y fundamente y CITE cada recomendacion (metodologia, capitulos, rutas
por fabricante, biblioteca de pruebas, plantillas y anexos de gestion).

El detalle NO se vuelca al prompt: el system prompt lleva solo un indice compacto
(`indice_para_prompt`) y el agente pide el detalle bajo demanda con la herramienta
`query_guide`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def load_base() -> dict:
    """Carga y cachea la base de conocimiento desde disco."""
    with open(config.KNOWLEDGE_BASE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(text: str) -> str:
    return (text or "").strip().lower()


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
def methodology_summary() -> str:
    """Texto breve con las seis etapas y su objetivo (backbone del prompt)."""
    base = load_base()
    lineas = []
    for et in base["methodology"]["stages"]:
        lineas.append(f"{et['n']}. {et['name']} [{et['id']}]: {et['objective']}")
    return "\n".join(lineas)


def prompt_index() -> str:
    """Indice compacto de lo que el agente puede consultar con `query_guide`.

    Da al modelo las CLAVES validas sin volcar el contenido completo.
    """
    base = load_base()
    g = base["guide"]
    capitulos = "; ".join(f"{c['n']}={c['title']}" for c in base["chapters"])
    manufacturers = "; ".join(r["brand"] for r in base["manufacturers"]["routes"])
    pruebas = "; ".join(f"{p['id']} {p['device']}" for p in base["test_library"])
    plantillas = "; ".join(f"{t['id']}={t['name']}" for t in base["templates"])
    anexos = "; ".join(f"{a['id']} {a['name']}" for a in base["management_annexes"])
    cases = "; ".join(f"{c['id']} {c['title']}" for c in base["case_studies"])
    return (
        f"BASE DE REFERENCIA: {g['title']} ({g['code']} v{g['version']}). "
        f"Citala como '{g['citation']}, cap. N' o por seccion.\n"
        "Consultala con la herramienta `query_guide` (tema, clave). Temas y claves:\n"
        f"- metodologia: seis etapas (diagnostico, ingenieria, construccion, fat, corte_sat, cierre).\n"
        f"- etapa (clave = id o numero): detalle de una etapa.\n"
        f"- capitulo (clave = numero o titulo). Capitulos: {capitulos}.\n"
        f"- fabricante (clave = marca): {manufacturers}. Ademas 'matriz_fabricantes'.\n"
        f"- prueba (clave = id o dispositivo): {pruebas}.\n"
        f"- plantilla (clave = letra o nombre): {plantillas}.\n"
        f"- anexo (clave = id o nombre): {anexos}.\n"
        f"- caso (clave = id o titulo): {cases}.\n"
        f"- principios | entregables | guia: informacion transversal."
    )


# --------------------------------------------------------------------------- #
# Consulta (usada por la herramienta query_guide)
# --------------------------------------------------------------------------- #
def _find_chapter(base: dict, key):
    if key in (None, ""):
        return [{"n": c["n"], "title": c["title"], "stage": c["stage"]} for c in base["chapters"]]
    k = _norm(str(key))
    # 1) coincidencia exacta por numero; 2) subcadena en el titulo.
    for c in base["chapters"]:
        if k == str(c["n"]):
            return c
    for c in base["chapters"]:
        if k in _norm(c["title"]):
            return c
    return None


def _find_stage(base: dict, key):
    etapas = base["methodology"]["stages"]
    if key in (None, ""):
        return base["methodology"]
    k = _norm(str(key))
    # 1) coincidencia exacta por numero o id; 2) subcadena en el nombre.
    for et in etapas:
        if k == str(et["n"]) or k == _norm(et["id"]):
            return et
    for et in etapas:
        if k in _norm(et["name"]):
            return et
    return None


def _find_manufacturer(base: dict, key):
    rutas = base["manufacturers"]["routes"]
    if key in (None, ""):
        return {"note": base["manufacturers"]["note"], "marcas": [r["brand"] for r in rutas]}
    k = _norm(str(key))
    for r in rutas:
        if k in _norm(r["brand"]):
            return {**r, "recommended_procedure": base["manufacturers"]["recommended_procedure"], "note": base["manufacturers"]["note"]}
    # buscar tambien por familia de origen (p. ej. "S7-300", "PLC-5")
    for r in rutas:
        for o in r["origins"]:
            if k in _norm(o["origin"]):
                return {"brand": r["brand"], "coincidencia": o, "recommended_procedure": base["manufacturers"]["recommended_procedure"], "note": base["manufacturers"]["note"]}
    return None


def _find_test(base: dict, key):
    pruebas = base["test_library"]
    if key in (None, ""):
        return [{"id": p["id"], "device": p["device"]} for p in pruebas]
    k = _norm(str(key))
    for p in pruebas:
        if k == _norm(p["id"]):
            return p
    for p in pruebas:
        if k in _norm(p["device"]):
            return p
    return None


def _find_template(base: dict, key):
    plantillas = base["templates"]
    if key in (None, ""):
        return plantillas
    k = _norm(str(key))
    for t in plantillas:
        if k == _norm(t["id"]):
            return t
    for t in plantillas:
        if k in _norm(t["name"]):
            return t
    return None


def _find_annex(base: dict, key):
    anexos = base["management_annexes"]
    if key in (None, ""):
        return anexos
    k = _norm(str(key))
    for a in anexos:
        if k == _norm(a["id"]):
            return a
    for a in anexos:
        if k in _norm(a["name"]):
            return a
    return None


def _find_case(base: dict, key):
    cases = base["case_studies"]
    if key in (None, ""):
        return [{"id": c["id"], "title": c["title"]} for c in cases]
    k = _norm(str(key))
    for c in cases:
        if k == _norm(c["id"]):
            return c
    for c in cases:
        if k in _norm(c["title"]):
            return c
    return None


def query(tema: str, key=None) -> dict:
    """Devuelve el fragmento de la guia pedido. Estructura estable para el modelo.

    `tema` (obligatorio) y `clave` (opcional) provienen de la herramienta
    `query_guide`. Siempre devuelve un dict con 'citation' para trazabilidad.
    """
    base = load_base()
    cita = base["guide"]["citation"]
    t = _norm(tema)

    despacho = {
        "indice": lambda: {"indice": prompt_index()},
        "guide": lambda: base["guide"],
        "principios": lambda: {"guiding_principles": base["guiding_principles"]},
        "entregables": lambda: {"minimum_deliverables": base["minimum_deliverables"],
                                 "stage_exit_criteria": base["stage_exit_criteria"]},
        "methodology": lambda: base["methodology"],
        "stage": lambda: _find_stage(base, key),
        "chapter": lambda: _find_chapter(base, key),
        "manufacturer": lambda: _find_manufacturer(base, key),
        "manufacturers": lambda: _find_manufacturer(base, key),
        "matriz_fabricantes": lambda: {"verification_matrix": base["manufacturers"]["verification_matrix"]},
        "test": lambda: _find_test(base, key),
        "test_library": lambda: _find_test(base, key),
        "template": lambda: _find_template(base, key),
        "templates": lambda: _find_template(base, key),
        "anexo": lambda: _find_annex(base, key),
        "annexes": lambda: _find_annex(base, key),
        "case": lambda: _find_case(base, key),
        "cases": lambda: _find_case(base, key),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "citation": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{key}' en el tema '{tema}'", "citation": cita}
    return {"tema": t, "key": key, "citation": cita, "contenido": resultado}
