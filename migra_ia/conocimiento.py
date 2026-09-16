"""Base de conocimiento de MIGRA-IA (Guia MIGRA-IA-GUIA-001).

Carga la guia integral de migracion (data/es/knowledge_base.json) y expone
consultas para que el agente estructure el diagnostico por las seis etapas de la
metodologia y fundamente y CITE cada recomendacion (metodologia, capitulos, rutas
por fabricante, biblioteca de pruebas, plantillas y anexos de gestion).

El detalle NO se vuelca al prompt: el system prompt lleva solo un indice compacto
(`indice_para_prompt`) y el agente pide el detalle bajo demanda con la herramienta
`consultar_guia`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def cargar_base() -> dict:
    """Carga y cachea la base de conocimiento desde disco."""
    with open(config.RUTA_BASE_CONOCIMIENTO, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(texto: str) -> str:
    return (texto or "").strip().lower()


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
def resumen_metodologia() -> str:
    """Texto breve con las seis etapas y su objetivo (backbone del prompt)."""
    base = cargar_base()
    lineas = []
    for et in base["methodology"]["stages"]:
        lineas.append(f"{et['n']}. {et['name']} [{et['id']}]: {et['objective']}")
    return "\n".join(lineas)


def indice_para_prompt() -> str:
    """Indice compacto de lo que el agente puede consultar con `consultar_guia`.

    Da al modelo las CLAVES validas sin volcar el contenido completo.
    """
    base = cargar_base()
    g = base["guide"]
    capitulos = "; ".join(f"{c['n']}={c['title']}" for c in base["chapters"])
    fabricantes = "; ".join(r["brand"] for r in base["manufacturers"]["routes"])
    pruebas = "; ".join(f"{p['id']} {p['device']}" for p in base["test_library"])
    plantillas = "; ".join(f"{t['id']}={t['name']}" for t in base["templates"])
    anexos = "; ".join(f"{a['id']} {a['name']}" for a in base["management_annexes"])
    casos = "; ".join(f"{c['id']} {c['title']}" for c in base["case_studies"])
    return (
        f"BASE DE REFERENCIA: {g['title']} ({g['code']} v{g['version']}). "
        f"Citala como '{g['citation']}, cap. N' o por seccion.\n"
        "Consultala con la herramienta `consultar_guia` (tema, clave). Temas y claves:\n"
        f"- metodologia: seis etapas (diagnostico, ingenieria, construccion, fat, corte_sat, cierre).\n"
        f"- etapa (clave = id o numero): detalle de una etapa.\n"
        f"- capitulo (clave = numero o titulo). Capitulos: {capitulos}.\n"
        f"- fabricante (clave = marca): {fabricantes}. Ademas 'matriz_fabricantes'.\n"
        f"- prueba (clave = id o dispositivo): {pruebas}.\n"
        f"- plantilla (clave = letra o nombre): {plantillas}.\n"
        f"- anexo (clave = id o nombre): {anexos}.\n"
        f"- caso (clave = id o titulo): {casos}.\n"
        f"- principios | entregables | guia: informacion transversal."
    )


# --------------------------------------------------------------------------- #
# Consulta (usada por la herramienta consultar_guia)
# --------------------------------------------------------------------------- #
def _buscar_capitulo(base: dict, clave):
    if clave in (None, ""):
        return [{"n": c["n"], "title": c["title"], "stage": c["stage"]} for c in base["chapters"]]
    k = _norm(str(clave))
    # 1) coincidencia exacta por numero; 2) subcadena en el titulo.
    for c in base["chapters"]:
        if k == str(c["n"]):
            return c
    for c in base["chapters"]:
        if k in _norm(c["title"]):
            return c
    return None


def _buscar_etapa(base: dict, clave):
    etapas = base["methodology"]["stages"]
    if clave in (None, ""):
        return base["methodology"]
    k = _norm(str(clave))
    # 1) coincidencia exacta por numero o id; 2) subcadena en el nombre.
    for et in etapas:
        if k == str(et["n"]) or k == _norm(et["id"]):
            return et
    for et in etapas:
        if k in _norm(et["name"]):
            return et
    return None


def _buscar_fabricante(base: dict, clave):
    rutas = base["manufacturers"]["routes"]
    if clave in (None, ""):
        return {"note": base["manufacturers"]["note"], "marcas": [r["brand"] for r in rutas]}
    k = _norm(str(clave))
    for r in rutas:
        if k in _norm(r["brand"]):
            return {**r, "recommended_procedure": base["manufacturers"]["recommended_procedure"], "note": base["manufacturers"]["note"]}
    # buscar tambien por familia de origen (p. ej. "S7-300", "PLC-5")
    for r in rutas:
        for o in r["origins"]:
            if k in _norm(o["origin"]):
                return {"brand": r["brand"], "coincidencia": o, "recommended_procedure": base["manufacturers"]["recommended_procedure"], "note": base["manufacturers"]["note"]}
    return None


def _buscar_prueba(base: dict, clave):
    pruebas = base["test_library"]
    if clave in (None, ""):
        return [{"id": p["id"], "device": p["device"]} for p in pruebas]
    k = _norm(str(clave))
    for p in pruebas:
        if k == _norm(p["id"]):
            return p
    for p in pruebas:
        if k in _norm(p["device"]):
            return p
    return None


def _buscar_plantilla(base: dict, clave):
    plantillas = base["templates"]
    if clave in (None, ""):
        return plantillas
    k = _norm(str(clave))
    for t in plantillas:
        if k == _norm(t["id"]):
            return t
    for t in plantillas:
        if k in _norm(t["name"]):
            return t
    return None


def _buscar_anexo(base: dict, clave):
    anexos = base["management_annexes"]
    if clave in (None, ""):
        return anexos
    k = _norm(str(clave))
    for a in anexos:
        if k == _norm(a["id"]):
            return a
    for a in anexos:
        if k in _norm(a["name"]):
            return a
    return None


def _buscar_caso(base: dict, clave):
    casos = base["case_studies"]
    if clave in (None, ""):
        return [{"id": c["id"], "title": c["title"]} for c in casos]
    k = _norm(str(clave))
    for c in casos:
        if k == _norm(c["id"]):
            return c
    for c in casos:
        if k in _norm(c["title"]):
            return c
    return None


def consultar(tema: str, clave=None) -> dict:
    """Devuelve el fragmento de la guia pedido. Estructura estable para el modelo.

    `tema` (obligatorio) y `clave` (opcional) provienen de la herramienta
    `consultar_guia`. Siempre devuelve un dict con 'citation' para trazabilidad.
    """
    base = cargar_base()
    cita = base["guide"]["citation"]
    t = _norm(tema)

    despacho = {
        "indice": lambda: {"indice": indice_para_prompt()},
        "guide": lambda: base["guide"],
        "principios": lambda: {"guiding_principles": base["guiding_principles"]},
        "entregables": lambda: {"minimum_deliverables": base["minimum_deliverables"],
                                 "stage_exit_criteria": base["stage_exit_criteria"]},
        "methodology": lambda: base["methodology"],
        "stage": lambda: _buscar_etapa(base, clave),
        "chapter": lambda: _buscar_capitulo(base, clave),
        "manufacturer": lambda: _buscar_fabricante(base, clave),
        "manufacturers": lambda: _buscar_fabricante(base, clave),
        "matriz_fabricantes": lambda: {"verification_matrix": base["manufacturers"]["verification_matrix"]},
        "test": lambda: _buscar_prueba(base, clave),
        "test_library": lambda: _buscar_prueba(base, clave),
        "template": lambda: _buscar_plantilla(base, clave),
        "templates": lambda: _buscar_plantilla(base, clave),
        "anexo": lambda: _buscar_anexo(base, clave),
        "annexes": lambda: _buscar_anexo(base, clave),
        "case": lambda: _buscar_caso(base, clave),
        "cases": lambda: _buscar_caso(base, clave),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "citation": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{clave}' en el tema '{tema}'", "citation": cita}
    return {"tema": t, "key": clave, "citation": cita, "contenido": resultado}
