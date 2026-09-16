"""Catalogo de fabricantes, generaciones y modelos de CPU (data/es/cpu_manufacturers.json).

Este modulo es lo que hace que MIGRA-IA sea ADAPTATIVO: resuelve lo que el usuario
escribe ("tengo un CJ1M-CPU13", "un Allen Bradley SLC 5/04") a una ficha concreta
-- marca, familia/generacion, posicion en la cronologia del fabricante y fuente
oficial -- para que TODA respuesta posterior quede anclada a ESE equipo y no
derive al ejemplo por defecto.

Reglas de rigor (heredadas del documento fuente):
- Nunca se expanden rangos ("CJ2M-CPU11 a CPU15" se conserva entero): completar
  los codigos intermedios seria inventar numeros de parte (Regla 13, Sec. 8).
- Si el modelo no esta en el catalogo, se devuelve estado 'no_catalogado' con una
  advertencia explicita, en lugar de aproximar.
- Cada ficha arrastra sus etiquetas de fuente y su URL oficial para poder citarlas.

El detalle NO se vuelca al prompt: el system prompt lleva un indice compacto
(`indice_para_prompt`) y el agente pide el resto con las herramientas
`identify_cpu` y `query_catalog`, que delegan en `identificar` y `ficha`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from . import config, knowledge

# Prefijos cronologicos que el documento antepone al nombre de la familia.
_STAGE_PREFIXES = ("historica - ", "historico - ", "legado - ", "actual - ")

# Un token de modelo mas corto que esto no se busca como subcadena suelta: "084"
# o "184" (Modicon) generarian falsos positivos dentro de cualquier numero.
_MIN_LARGO_SUBCADENA = 5

# Alias frecuentes que el personal tecnico usa y que no aparecen literalmente en
# el nombre de la marca. Solo abreviaturas de marca reales, no modelos.
_BRAND_ALIAS = {
    "Rockwell Automation / Allen-Bradley": ["allen bradley", "allenbradley"],
    "Emerson (legado GE Fanuc / GE Intelligent Platforms)": ["ge fanuc", "gefanuc"],
    "B&R Industrial Automation": ["b r", "br automation", "bernecker"],
}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _norm(text: str) -> str:
    """Minusculas sin acentos, con separadores unificados a un espacio."""
    t = _strip_accents((text or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _compact(text: str) -> str:
    """Solo letras y digitos: 'CPU 315-2 DP' y 'cpu315-2dp' colapsan al mismo valor."""
    return re.sub(r"[^a-z0-9]", "", _strip_accents((text or "").lower()))


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Carga y cachea el catalogo de fabricantes desde disco."""
    with open(config.CPU_MANUFACTURERS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _clean_family(family: str) -> str:
    """Quita el prefijo de etapa: 'Actual - SIMATIC S7-1500' -> 'SIMATIC S7-1500'.

    Compara sin acentos: el documento escribe 'Histórica - ...' con tilde.
    """
    bajo = _strip_accents(family.lower())
    for pref in _STAGE_PREFIXES:
        if bajo.startswith(pref):
            return family[len(pref):].strip()
    return family.strip()


def _stage(family: str) -> str:
    """Clasifica la generacion segun el prefijo que use el documento."""
    bajo = _strip_accents(family.lower())
    if bajo.startswith(("historica - ", "historico - ", "legado - ")):
        return "historica"
    if bajo.startswith("actual - "):
        return "actual"
    return "intermedia"


@lru_cache(maxsize=1)
def _alias_by_brand() -> dict[str, list[str]]:
    """Deriva los alias de cada marca de su propio nombre, mas los manuales.

    'Emerson (legado GE Fanuc / GE Intelligent Platforms)' produce
    ['emerson', 'ge fanuc', 'ge intelligent platforms', ...].
    """
    alias: dict[str, list[str]] = {}
    for fab in load_catalog()["manufacturers"]:
        brand = fab["brand"]
        crudos = {brand}
        # Texto fuera y dentro de los parentesis, por separado.
        fuera = re.sub(r"\([^)]*\)", " ", brand)
        dentro = " ".join(re.findall(r"\(([^)]*)\)", brand))
        for bloque in (fuera, dentro):
            bloque = re.sub(r"\b(legado|legacy)\b", " ", bloque, flags=re.IGNORECASE)
            crudos.update(p for p in bloque.split("/"))
        # Primera palabra significativa ('Rockwell', 'Mitsubishi', 'Phoenix').
        primera = _norm(fuera).split(" ")
        if primera and len(primera[0]) >= 4:
            crudos.add(primera[0])
        normalizados = {_norm(c) for c in crudos}
        normalizados.update(_BRAND_ALIAS.get(brand, []))
        alias[brand] = sorted((a for a in normalizados if len(a) >= 3), key=len, reverse=True)
    return alias


def _sources_of(etiquetas) -> list[dict]:
    """Convierte etiquetas [S1d] en fichas citables con descripcion y URL."""
    catalog = load_catalog()
    fichas = []
    for et in etiquetas or []:
        f = catalog["sources"].get(et)
        if f:
            fichas.append({"label": et, "description": f["description"], "url": f["url"]})
        else:
            fichas.append({"label": et, "description": "", "url": ""})
    return fichas


# --------------------------------------------------------------------------- #
# Identificacion: texto libre -> marca / familia / modelo
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _model_index() -> list[tuple[str, str, int, str]]:
    """(modelo_compacto, marca, indice_generacion, modelo_original), mas largo primero.

    Buscar del token mas largo al mas corto evita que 'CPU 314' se lleve la
    coincidencia cuando el usuario escribio 'CPU 314ST - 314-6CF23'.
    """
    entradas = []
    for fab in load_catalog()["manufacturers"]:
        for i, gen in enumerate(fab["generations"]):
            for modelo in gen["models"]:
                # El documento escribe algunos modelos con su equivalencia entre
                # parentesis ('SLC 5/03 (1747-L532)'): son el MISMO dato escrito de
                # dos formas, y el usuario puede citar cualquiera de las dos.
                variantes = {modelo}
                variantes.add(re.sub(r"\([^)]*\)", " ", modelo))
                variantes.update(re.findall(r"\(([^)]*)\)", modelo))
                for variante in variantes:
                    comp = _compact(variante)
                    if comp:
                        entradas.append((comp, fab["brand"], i, modelo))
    return sorted(entradas, key=lambda e: len(e[0]), reverse=True)


@lru_cache(maxsize=1)
def _family_index() -> list[tuple[str, str, int, str]]:
    """(familia_normalizada, marca, indice_generacion, familia_limpia), mas larga primero."""
    entradas = []
    for fab in load_catalog()["manufacturers"]:
        for i, gen in enumerate(fab["generations"]):
            limpia = _clean_family(gen["family"])
            # La familia puede venir compuesta: 'SIMATIC S5-135U / S5-155U'.
            partes = [limpia] + limpia.split("/")
            # El usuario suele citar solo el designador: 'M580' por 'Modicon M580',
            # 's7-1500' por 'SIMATIC S7-1500'. Se indexan los segmentos con digito
            # (un designador real) y largo suficiente para no chocar entre marcas.
            partes += [s for s in re.split(r"[\s/]+", limpia)
                       if len(s) >= 4 and any(c.isdigit() for c in s)]
            for parte in partes:
                norm = _norm(parte)
                if len(norm) >= 3:
                    entradas.append((norm, fab["brand"], i, limpia))
    return sorted(entradas, key=lambda e: len(e[0]), reverse=True)


def _find_brand(consulta_norm: str) -> str | None:
    """Devuelve la marca cuyo alias mas largo aparezca en la consulta."""
    best, largo = None, 0
    for brand, alias in _alias_by_brand().items():
        for a in alias:
            if len(a) > largo and re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", consulta_norm):
                best, largo = brand, len(a)
    return best


def _by_brand(brand: str) -> dict:
    for fab in load_catalog()["manufacturers"]:
        if fab["brand"] == brand:
            return fab
    raise KeyError(brand)


def _describe_generation(fab: dict, index_: int) -> dict:
    """Ficha de una generacion con su lugar en la cronologia del fabricante."""
    gens = fab["generations"]
    gen = gens[index_]
    posteriores = [
        {"family": _clean_family(g["family"]), "stage": _stage(g["family"]),
         "models_text": g["models_text"]}
        for g in gens[index_ + 1:]
    ]
    actuales = [
        {"family": _clean_family(g["family"]), "models_text": g["models_text"],
         "sources": _sources_of(g["sources"])}
        for g in gens if _stage(g["family"]) == "actual"
    ]
    # Cuatro fabricantes del documento no marcan ninguna generacion como 'Actual'.
    # Se ofrece la ultima listada, diciendo expresamente que la fuente no la declara
    # vigente: es un indicio cronologico, no una afirmacion de estado comercial.
    current_note = ""
    if not actuales and gens:
        ultima = gens[-1]
        actuales = [{"family": _clean_family(ultima["family"]),
                     "models_text": ultima["models_text"],
                     "sources": _sources_of(ultima["sources"])}]
        current_note = ("El documento fuente no marca ninguna generacion de este "
                       "fabricante como 'Actual'; se muestra la ultima de la "
                       "cronologia. Verifica el estado comercial con el fabricante.")
    return {
        "family": _clean_family(gen["family"]),
        "familia_documento": gen["family"],
        "stage": _stage(gen["family"]),
        "posicion": f"{index_ + 1} de {len(gens)}",
        "modelos_documentados": gen["models_text"],
        "remark": gen["remark"],
        "sources": _sources_of(gen["sources"]),
        "generaciones_posteriores": posteriores,
        "generaciones_actuales_del_fabricante": actuales,
        "nota_generacion_actual": current_note,
    }


def _documented_target(contenido: dict, family: str | None) -> dict | None:
    """Ruta de migracion que la guia publica para la familia de ORIGEN concreta.

    Es mas precisa que 'la generacion actual del fabricante': la guia distingue,
    por ejemplo, S7-200 -> S7-1200 de S7-300/400 -> S7-1500, y SLC 500 ->
    CompactLogix 5380 de PLC-5 -> ControlLogix.
    """
    if not family:
        return None
    fam = _norm(family)
    for origin in contenido.get("origins") or []:
        if not isinstance(origin, dict):
            continue
        for parte in origin["origin"].split("/"):
            p = _norm(parte)
            if len(p) >= 3 and re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", fam):
                return {
                    "origen_en_guia": origin["origin"],
                    "destino": origin["route"],
                    "critical_aspects": origin.get("critical_aspects", ""),
                }
    return None


def _guide_route(brand: str, family: str | None = None) -> dict | None:
    """Cruza la marca del catalogo con la ruta metodologica de MIGRA-IA-GUIA-001.

    El catalogo dice QUE existe y en que orden; la guia dice COMO se migra. Solo
    5 de las 30 marcas tienen ruta publicada en la guia.
    """
    for alias in _alias_by_brand().get(brand, []):
        res = knowledge.query("manufacturer", alias)
        contenido = res.get("contenido")
        if isinstance(contenido, dict) and "brand" in contenido:
            return {
                "marca_en_guia": contenido["brand"],
                "legacy_software": contenido.get("legacy_software"),
                "target_software": contenido.get("target_software"),
                "legacy_networks": contenido.get("legacy_networks"),
                "typical_risk": contenido.get("typical_risk"),
                "destino_documentado": _documented_target(contenido, family),
                "citation": res.get("citation"),
            }
    return None


def identify(text: str) -> dict:
    """Resuelve texto libre a marca / familia / modelo del catalogo.

    Busca de lo mas especifico a lo mas general (modelo -> familia -> marca) y
    NUNCA aproxima: si no hay coincidencia devuelve 'no_catalogado' con la
    advertencia correspondiente.
    """
    consulta = (text or "").strip()
    if not consulta:
        return {"consulta": consulta, "status": "sin_consulta",
                "confidence_level": "no_determinado",
                "warning": "No se recibio texto que identificar."}

    norm = _norm(consulta)
    comp = _compact(consulta)
    catalog = load_catalog()
    base = {"consulta": consulta, "cita_catalogo": catalog["document"]["title"],
            "version_catalogo": catalog["document"]["version"]}

    # 1) Modelo exacto de CPU.
    for modelo_comp, brand, i, modelo in _model_index():
        coincide = modelo_comp == comp or (
            len(modelo_comp) >= _MIN_LARGO_SUBCADENA and modelo_comp in comp
        )
        if coincide:
            fab = _by_brand(brand)
            desc = _describe_generation(fab, i)
            return {**base, "status": "modelo_exacto", "confidence_level": "alta_confianza",
                    "brand": brand, "classification": fab["classification"],
                    "modelo_identificado": modelo,
                    **desc,
                    "ruta_migracion_guia": _guide_route(brand, desc["family"]),
                    "nota_verificacion": "Confirmar el numero de parte contra la placa "
                                         "fisica y la fuente oficial antes de especificar."}

    # 2) Familia / generacion.
    for family_norm, brand, i, family in _family_index():
        if re.search(rf"(?<![a-z0-9]){re.escape(family_norm)}(?![a-z0-9])", norm):
            fab = _by_brand(brand)
            desc = _describe_generation(fab, i)
            return {**base, "status": "family", "confidence_level": "confianza_media",
                    "brand": brand, "classification": fab["classification"],
                    "familia_identificada": family,
                    **desc,
                    "ruta_migracion_guia": _guide_route(brand, desc["family"]),
                    "dato_faltante": "Modelo exacto de CPU: pedirlo o solicitar foto de la placa."}

    # 3) Solo marca.
    brand = _find_brand(norm)
    if brand:
        fab = _by_brand(brand)
        return {**base, "status": "brand", "confidence_level": "confianza_media",
                "brand": brand, "classification": fab["classification"],
                "generations": [
                    {"n": g["n"], "family": _clean_family(g["family"]),
                     "stage": _stage(g["family"]), "models_text": g["models_text"]}
                    for g in fab["generations"]
                ],
                "ruta_migracion_guia": _guide_route(brand),
                "dato_faltante": "Familia y modelo exacto de CPU: pedirlos o solicitar "
                                 "foto de la placa."}

    # 4) Sin coincidencia: se dice, no se aproxima.
    return {**base, "status": "no_catalogado", "confidence_level": "no_determinado",
            "brand": None,
            "warning": "Ni la marca ni el modelo aparecen en el catalogo de 30 "
                           "fabricantes. NO infieras una equivalencia: pide la placa, "
                           "declara el dato como no verificado y remite a la "
                           "documentacion oficial del fabricante.",
            "marcas_disponibles": [f["brand"] for f in catalog["manufacturers"]]}


def profile(brand: str, family: str | None = None) -> dict:
    """Cronologia completa de una marca, o el detalle de una de sus generaciones."""
    consulta = f"{brand} {family}" if family else brand
    res = identify(consulta)
    if res["status"] == "no_catalogado":
        return res
    return res


def current_generations(brand: str) -> dict:
    """Familias vigentes de una marca, con sus modelos documentados y sus fuentes.

    `identificar()` solo devuelve esta informacion cuando ademas reconoce una
    familia o un modelo concretos. El paso 13 del procedimiento necesita poder
    preguntar solo por la marca, para ofrecer las plataformas actuales de otros
    fabricantes como alternativa.
    """
    try:
        fab = _by_brand(brand)
    except KeyError:
        return {"brand": brand, "families": [],
                "error": f"'{brand}' no figura en el catalogo de fabricantes."}
    gens = fab["generations"]
    actuales = [g for g in gens if _stage(g["family"]) == "actual"]
    note = ""
    if not actuales and gens:
        # Mismo criterio que `_describir_generacion`: se ofrece la ultima de la
        # cronologia diciendo que la fuente no la declara vigente.
        actuales = [gens[-1]]
        note = ("El documento fuente no marca ninguna generacion de este fabricante "
                "como 'Actual'; se muestra la ultima de la cronologia. Verifica el "
                "estado comercial con el fabricante.")
    return {
        "brand": fab["brand"],
        "classification": fab["classification"],
        "families": [
            {"family": _clean_family(g["family"]),
             "modelos_documentados": g["models_text"],
             "sources": _sources_of(g["sources"])}
            for g in actuales
        ],
        "note": note,
    }


_PALABRAS_VACIAS = {
    "tengo", "una", "unos", "unas", "con", "del", "los", "las", "por", "para",
    "que", "plc", "cpu", "brand", "model", "family", "serie", "controlador",
    "equipo", "planta", "maquina", "mi", "el", "la", "un", "de", "y", "es",
}


def suggestions(text: str, limite: int = 6) -> list[dict]:
    """Familias del catalogo que comparten algo con lo que escribio el usuario.

    Sirve para el caso en que `identificar()` no reconoce el equipo: en vez de
    dejar al usuario con un 'no lo encuentro', se le ofrecen las entradas REALES
    del catalogo que se le parecen para que confirme cual es. No selecciona
    ninguna ni completa nada: solo pregunta. Un error de tecleo tipo 'S7 1300'
    devuelve asi las familias S7 que si existen.
    """
    tokens = {t for t in _norm(text).split() if len(t) >= 2 and t not in _PALABRAS_VACIAS}
    if not tokens:
        return []
    # Si el usuario escribio algun nombre ('micrologix', 's7'), la coincidencia
    # tiene que incluirlo. Sin esta condicion, 'MicroLogix 1200' sugeriria un
    # SIMATIC S7-1200 solo porque ambos llevan el numero 1200: una pista falsa.
    con_letras = {t for t in tokens if not t.isdigit()}
    puntuadas: list[tuple[int, dict]] = []
    for fab in load_catalog()["manufacturers"]:
        for gen in fab["generations"]:
            family = _clean_family(gen["family"])
            campo = _norm(f"{fab['brand']} {family} {gen['models_text']}")
            propios = set(campo.split())
            comunes = tokens & propios
            if not comunes:
                continue
            if con_letras and not (comunes & con_letras):
                continue
            # Un token que ademas es parte del nombre de la familia pesa mas que
            # uno que solo aparece en la lista de modelos.
            peso = len(comunes) + sum(1 for t in comunes if t in _norm(family).split())
            puntuadas.append((peso, {
                "brand": fab["brand"],
                "family": family,
                "stage": _stage(gen["family"]),
                "modelos_documentados": gen["models_text"],
                "coincide_en": sorted(comunes),
            }))
    puntuadas.sort(key=lambda p: -p[0])
    return [d for _, d in puntuadas[:limite]]


def product_type(classification: str) -> str:
    """Agrupa las clasificaciones del catalogo para comparar cosas comparables.

    El catalogo usa etiquetas finas ('PLC', 'PLC/PAC', 'IPC / Industrial
    Computer'). Para ofrecer alternativas basta distinguir el controlador de
    programa almacenado del equipo basado en PC.
    """
    c = _norm(classification)
    if "plc" in c or "pac" in c:
        return "plc"
    if "ipc" in c or "pc" in c or "embedded" in c:
        return "pc"
    return "otro"


# --------------------------------------------------------------------------- #
# Anclaje: bloque que fija el equipo en consulta para el resto del dialogo
# --------------------------------------------------------------------------- #
def anchor(ident: dict) -> str:
    """Texto compacto que se inyecta en el contexto tras identificar el equipo.

    Es la pieza que impide que el agente responda con la marca del ejemplo por
    defecto: a partir de aqui, cada respuesta se refiere a ESTE equipo.
    """
    if not ident or ident.get("status") in (None, "sin_consulta"):
        return ""

    if ident["status"] == "no_catalogado":
        return (
            "EQUIPO EN CONSULTA: NO CATALOGADO.\n"
            f"El usuario reporto: '{ident.get('consulta', '')}'.\n"
            f"{ident['warning']}\n"
            "Mientras no se identifique, toda recomendacion es preliminar y debe "
            "declararse como tal."
        )

    lineas = [
        "EQUIPO EN CONSULTA (catalogo de fabricantes verificado). Toda respuesta a "
        "partir de aqui se refiere a ESTE equipo: no uses otra marca como ejemplo "
        "por defecto ni traslades rutas de un fabricante a otro.",
        f"- Reportado por el usuario: '{ident.get('consulta', '')}'",
        f"- Marca: {ident['brand']} ({ident.get('classification', '')})",
    ]
    if ident.get("modelo_identificado"):
        lineas.append(
            f"- Modelo localizado en el catalogo: {ident['modelo_identificado']} "
            "(tal como lo lista el documento fuente, que abrevia los modelos "
            "sucesivos de una misma fila)"
        )
    if ident.get("family"):
        lineas.append(
            f"- Familia/generacion: {ident['family']} "
            f"(etapa {ident.get('stage')}, posicion {ident.get('posicion')} en la cronologia)"
        )
        lineas.append(f"- Modelos documentados de esa generacion: {ident['modelos_documentados']}")
        if ident.get("remark"):
            lineas.append(f"- Observacion del catalogo: {ident['remark']}")
        actuales = ident.get("generaciones_actuales_del_fabricante") or []
        if actuales:
            target = "; ".join(f"{a['family']} ({a['models_text']})" for a in actuales)
            lineas.append(f"- Generacion actual del MISMO fabricante: {target}")
        if ident.get("nota_generacion_actual"):
            lineas.append(f"- AVISO: {ident['nota_generacion_actual']}")
    elif ident.get("generations"):
        fams = "; ".join(f"{g['family']} [{g['stage']}]" for g in ident["generations"])
        lineas.append(f"- Cronologia de la marca: {fams}")

    if ident.get("stage") == "actual":
        lineas.append(
            "- ATENCION: esta generacion es la ACTUAL del fabricante segun el catalogo. "
            "No propongas migrarla a si misma: aqui procede plan preventivo, "
            "actualizacion de firmware o ampliacion, no una migracion de plataforma."
        )

    path = ident.get("ruta_migracion_guia")
    if path:
        doc_target = path.get("destino_documentado")
        if doc_target:
            lineas.append(
                f"- Ruta de migracion documentada para esta familia de origen "
                f"('{doc_target['origen_en_guia']}'): -> {doc_target['destino']}. "
                f"{doc_target['critical_aspects']}"
            )
        lineas.append(
            f"- Ruta metodologica ({path['citation']}): software {path['legacy_software']} -> "
            f"{path['target_software']}; redes heredadas {path['legacy_networks']}; "
            f"riesgo tipico: {path['typical_risk']}"
        )
    else:
        lineas.append(
            "- La guia MIGRA-IA-GUIA-001 no publica ruta de migracion para esta marca: "
            "aplica la metodologia de 6 etapas de forma generica y apoyate en la "
            "documentacion oficial del fabricante."
        )

    fuentes = ident.get("sources") or []
    if fuentes:
        cites = "; ".join(f"[{f['label']}] {f['url']}" for f in fuentes if f.get("url"))
        lineas.append(f"- Fuentes oficiales citables: {cites}")
    if ident.get("dato_faltante"):
        lineas.append(f"- DATO FALTANTE: {ident['dato_faltante']}")
    lineas.append(
        "- Los modelos listados son los que el catalogo documenta; no completes "
        "codigos intermedios de un rango ni inventes sufijos."
    )
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
def prompt_index() -> str:
    """Marcas y familias que el agente puede reconocer, sin volcar 469 modelos."""
    catalog = load_catalog()
    doc = catalog["document"]
    lineas = [
        f"CATALOGO DE FABRICANTES Y CPU: {doc['title']} ({doc['version']}). "
        f"{len(catalog['manufacturers'])} fabricantes, "
        f"{sum(len(f['generations']) for f in catalog['manufacturers'])} generaciones "
        f"documentadas con modelos reales y fuente oficial.",
        "Resuelve lo que diga el usuario con `identify_cpu` (texto libre de placa) y "
        "amplia con `query_catalog` (marca, familia). Marcas y familias:",
    ]
    for fab in catalog["manufacturers"]:
        fams = "; ".join(_clean_family(g["family"]) for g in fab["generations"])
        lineas.append(f"- {fab['brand']} [{fab['classification']}]: {fams}")
    lineas.append(
        "Si el equipo del usuario NO esta en esta lista, dilo explicitamente y pide la "
        "placa: no lo asimiles a la marca mas parecida."
    )
    return "\n".join(lineas)

