"""Base de conocimiento de MIGRA-IA (Guia MIGRA-IA-GUIA-001).

Carga la guia integral de migracion (data/base_conocimiento.json) y expone
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
    for et in base["metodologia"]["etapas"]:
        lineas.append(f"{et['n']}. {et['nombre']} [{et['id']}]: {et['objetivo']}")
    return "\n".join(lineas)


def indice_para_prompt() -> str:
    """Indice compacto de lo que el agente puede consultar con `consultar_guia`.

    Da al modelo las CLAVES validas sin volcar el contenido completo.
    """
    base = cargar_base()
    g = base["guia"]
    capitulos = "; ".join(f"{c['n']}={c['titulo']}" for c in base["capitulos"])
    fabricantes = "; ".join(r["marca"] for r in base["fabricantes"]["rutas"])
    pruebas = "; ".join(f"{p['id']} {p['dispositivo']}" for p in base["biblioteca_pruebas"])
    plantillas = "; ".join(f"{t['id']}={t['nombre']}" for t in base["plantillas"])
    anexos = "; ".join(f"{a['id']} {a['nombre']}" for a in base["anexos_gestion"])
    casos = "; ".join(f"{c['id']} {c['titulo']}" for c in base["casos_estudio"])
    return (
        f"BASE DE REFERENCIA: {g['titulo']} ({g['codigo']} v{g['version']}). "
        f"Citala como '{g['cita']}, cap. N' o por seccion.\n"
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
        return [{"n": c["n"], "titulo": c["titulo"], "etapa": c["etapa"]} for c in base["capitulos"]]
    k = _norm(str(clave))
    # 1) coincidencia exacta por numero; 2) subcadena en el titulo.
    for c in base["capitulos"]:
        if k == str(c["n"]):
            return c
    for c in base["capitulos"]:
        if k in _norm(c["titulo"]):
            return c
    return None


def _buscar_etapa(base: dict, clave):
    etapas = base["metodologia"]["etapas"]
    if clave in (None, ""):
        return base["metodologia"]
    k = _norm(str(clave))
    # 1) coincidencia exacta por numero o id; 2) subcadena en el nombre.
    for et in etapas:
        if k == str(et["n"]) or k == _norm(et["id"]):
            return et
    for et in etapas:
        if k in _norm(et["nombre"]):
            return et
    return None


def _buscar_fabricante(base: dict, clave):
    rutas = base["fabricantes"]["rutas"]
    if clave in (None, ""):
        return {"nota": base["fabricantes"]["nota"], "marcas": [r["marca"] for r in rutas]}
    k = _norm(str(clave))
    for r in rutas:
        if k in _norm(r["marca"]):
            return {**r, "procedimiento_recomendado": base["fabricantes"]["procedimiento_recomendado"], "nota": base["fabricantes"]["nota"]}
    # buscar tambien por familia de origen (p. ej. "S7-300", "PLC-5")
    for r in rutas:
        for o in r["origenes"]:
            if k in _norm(o["origen"]):
                return {"marca": r["marca"], "coincidencia": o, "procedimiento_recomendado": base["fabricantes"]["procedimiento_recomendado"], "nota": base["fabricantes"]["nota"]}
    return None


def _buscar_prueba(base: dict, clave):
    pruebas = base["biblioteca_pruebas"]
    if clave in (None, ""):
        return [{"id": p["id"], "dispositivo": p["dispositivo"]} for p in pruebas]
    k = _norm(str(clave))
    for p in pruebas:
        if k == _norm(p["id"]):
            return p
    for p in pruebas:
        if k in _norm(p["dispositivo"]):
            return p
    return None


def _buscar_plantilla(base: dict, clave):
    plantillas = base["plantillas"]
    if clave in (None, ""):
        return plantillas
    k = _norm(str(clave))
    for t in plantillas:
        if k == _norm(t["id"]):
            return t
    for t in plantillas:
        if k in _norm(t["nombre"]):
            return t
    return None


def _buscar_anexo(base: dict, clave):
    anexos = base["anexos_gestion"]
    if clave in (None, ""):
        return anexos
    k = _norm(str(clave))
    for a in anexos:
        if k == _norm(a["id"]):
            return a
    for a in anexos:
        if k in _norm(a["nombre"]):
            return a
    return None


def _buscar_caso(base: dict, clave):
    casos = base["casos_estudio"]
    if clave in (None, ""):
        return [{"id": c["id"], "titulo": c["titulo"]} for c in casos]
    k = _norm(str(clave))
    for c in casos:
        if k == _norm(c["id"]):
            return c
    for c in casos:
        if k in _norm(c["titulo"]):
            return c
    return None


def consultar(tema: str, clave=None) -> dict:
    """Devuelve el fragmento de la guia pedido. Estructura estable para el modelo.

    `tema` (obligatorio) y `clave` (opcional) provienen de la herramienta
    `consultar_guia`. Siempre devuelve un dict con 'cita' para trazabilidad.
    """
    base = cargar_base()
    cita = base["guia"]["cita"]
    t = _norm(tema)

    despacho = {
        "indice": lambda: {"indice": indice_para_prompt()},
        "guia": lambda: base["guia"],
        "principios": lambda: {"principios_rectores": base["principios_rectores"]},
        "entregables": lambda: {"entregables_minimos": base["entregables_minimos"],
                                 "criterios_salida_por_etapa": base["criterios_salida_por_etapa"]},
        "metodologia": lambda: base["metodologia"],
        "etapa": lambda: _buscar_etapa(base, clave),
        "capitulo": lambda: _buscar_capitulo(base, clave),
        "fabricante": lambda: _buscar_fabricante(base, clave),
        "fabricantes": lambda: _buscar_fabricante(base, clave),
        "matriz_fabricantes": lambda: {"matriz_verificacion": base["fabricantes"]["matriz_verificacion"]},
        "prueba": lambda: _buscar_prueba(base, clave),
        "biblioteca_pruebas": lambda: _buscar_prueba(base, clave),
        "plantilla": lambda: _buscar_plantilla(base, clave),
        "plantillas": lambda: _buscar_plantilla(base, clave),
        "anexo": lambda: _buscar_anexo(base, clave),
        "anexos": lambda: _buscar_anexo(base, clave),
        "caso": lambda: _buscar_caso(base, clave),
        "casos": lambda: _buscar_caso(base, clave),
    }

    handler = despacho.get(t)
    if handler is None:
        return {"error": f"tema desconocido: {tema}", "temas_validos": sorted(despacho.keys()), "cita": cita}

    resultado = handler()
    if resultado is None:
        return {"error": f"no se encontro '{clave}' en el tema '{tema}'", "cita": cita}
    return {"tema": t, "clave": clave, "cita": cita, "contenido": resultado}
