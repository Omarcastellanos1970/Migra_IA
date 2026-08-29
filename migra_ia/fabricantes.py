"""Catalogo de fabricantes, generaciones y modelos de CPU (data/fabricantes_cpu.json).

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
`identificar_cpu` y `consultar_catalogo`, que delegan en `identificar` y `ficha`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from . import config, conocimiento

# Prefijos cronologicos que el documento antepone al nombre de la familia.
_PREFIJOS_ETAPA = ("historica - ", "historico - ", "legado - ", "actual - ")

# Un token de modelo mas corto que esto no se busca como subcadena suelta: "084"
# o "184" (Modicon) generarian falsos positivos dentro de cualquier numero.
_MIN_LARGO_SUBCADENA = 5

# Alias frecuentes que el personal tecnico usa y que no aparecen literalmente en
# el nombre de la marca. Solo abreviaturas de marca reales, no modelos.
_ALIAS_MARCA = {
    "Rockwell Automation / Allen-Bradley": ["allen bradley", "allenbradley"],
    "Emerson (legado GE Fanuc / GE Intelligent Platforms)": ["ge fanuc", "gefanuc"],
    "B&R Industrial Automation": ["b r", "br automation", "bernecker"],
}


def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _norm(texto: str) -> str:
    """Minusculas sin acentos, con separadores unificados a un espacio."""
    t = _sin_acentos((texto or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _compacto(texto: str) -> str:
    """Solo letras y digitos: 'CPU 315-2 DP' y 'cpu315-2dp' colapsan al mismo valor."""
    return re.sub(r"[^a-z0-9]", "", _sin_acentos((texto or "").lower()))


@lru_cache(maxsize=1)
def cargar_catalogo() -> dict:
    """Carga y cachea el catalogo de fabricantes desde disco."""
    with open(config.RUTA_FABRICANTES_CPU, encoding="utf-8") as fh:
        return json.load(fh)


def _familia_limpia(familia: str) -> str:
    """Quita el prefijo de etapa: 'Actual - SIMATIC S7-1500' -> 'SIMATIC S7-1500'.

    Compara sin acentos: el documento escribe 'Histórica - ...' con tilde.
    """
    bajo = _sin_acentos(familia.lower())
    for pref in _PREFIJOS_ETAPA:
        if bajo.startswith(pref):
            return familia[len(pref):].strip()
    return familia.strip()


def _etapa(familia: str) -> str:
    """Clasifica la generacion segun el prefijo que use el documento."""
    bajo = _sin_acentos(familia.lower())
    if bajo.startswith(("historica - ", "historico - ", "legado - ")):
        return "historica"
    if bajo.startswith("actual - "):
        return "actual"
    return "intermedia"


@lru_cache(maxsize=1)
def _alias_por_marca() -> dict[str, list[str]]:
    """Deriva los alias de cada marca de su propio nombre, mas los manuales.

    'Emerson (legado GE Fanuc / GE Intelligent Platforms)' produce
    ['emerson', 'ge fanuc', 'ge intelligent platforms', ...].
    """
    alias: dict[str, list[str]] = {}
    for fab in cargar_catalogo()["fabricantes"]:
        marca = fab["marca"]
        crudos = {marca}
        # Texto fuera y dentro de los parentesis, por separado.
        fuera = re.sub(r"\([^)]*\)", " ", marca)
        dentro = " ".join(re.findall(r"\(([^)]*)\)", marca))
        for bloque in (fuera, dentro):
            bloque = re.sub(r"\b(legado|legacy)\b", " ", bloque, flags=re.IGNORECASE)
            crudos.update(p for p in bloque.split("/"))
        # Primera palabra significativa ('Rockwell', 'Mitsubishi', 'Phoenix').
        primera = _norm(fuera).split(" ")
        if primera and len(primera[0]) >= 4:
            crudos.add(primera[0])
        normalizados = {_norm(c) for c in crudos}
        normalizados.update(_ALIAS_MARCA.get(marca, []))
        alias[marca] = sorted((a for a in normalizados if len(a) >= 3), key=len, reverse=True)
    return alias


def _fuentes_de(etiquetas) -> list[dict]:
    """Convierte etiquetas [S1d] en fichas citables con descripcion y URL."""
    catalogo = cargar_catalogo()
    fichas = []
    for et in etiquetas or []:
        f = catalogo["fuentes"].get(et)
        if f:
            fichas.append({"etiqueta": et, "descripcion": f["descripcion"], "url": f["url"]})
        else:
            fichas.append({"etiqueta": et, "descripcion": "", "url": ""})
    return fichas


# --------------------------------------------------------------------------- #
# Identificacion: texto libre -> marca / familia / modelo
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _indice_modelos() -> list[tuple[str, str, int, str]]:
    """(modelo_compacto, marca, indice_generacion, modelo_original), mas largo primero.

    Buscar del token mas largo al mas corto evita que 'CPU 314' se lleve la
    coincidencia cuando el usuario escribio 'CPU 314ST - 314-6CF23'.
    """
    entradas = []
    for fab in cargar_catalogo()["fabricantes"]:
        for i, gen in enumerate(fab["generaciones"]):
            for modelo in gen["modelos"]:
                # El documento escribe algunos modelos con su equivalencia entre
                # parentesis ('SLC 5/03 (1747-L532)'): son el MISMO dato escrito de
                # dos formas, y el usuario puede citar cualquiera de las dos.
                variantes = {modelo}
                variantes.add(re.sub(r"\([^)]*\)", " ", modelo))
                variantes.update(re.findall(r"\(([^)]*)\)", modelo))
                for variante in variantes:
                    comp = _compacto(variante)
                    if comp:
                        entradas.append((comp, fab["marca"], i, modelo))
    return sorted(entradas, key=lambda e: len(e[0]), reverse=True)


@lru_cache(maxsize=1)
def _indice_familias() -> list[tuple[str, str, int, str]]:
    """(familia_normalizada, marca, indice_generacion, familia_limpia), mas larga primero."""
    entradas = []
    for fab in cargar_catalogo()["fabricantes"]:
        for i, gen in enumerate(fab["generaciones"]):
            limpia = _familia_limpia(gen["familia"])
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
                    entradas.append((norm, fab["marca"], i, limpia))
    return sorted(entradas, key=lambda e: len(e[0]), reverse=True)


def _buscar_marca(consulta_norm: str) -> str | None:
    """Devuelve la marca cuyo alias mas largo aparezca en la consulta."""
    mejor, largo = None, 0
    for marca, alias in _alias_por_marca().items():
        for a in alias:
            if len(a) > largo and re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", consulta_norm):
                mejor, largo = marca, len(a)
    return mejor


def _por_marca(marca: str) -> dict:
    for fab in cargar_catalogo()["fabricantes"]:
        if fab["marca"] == marca:
            return fab
    raise KeyError(marca)


def _describir_generacion(fab: dict, indice: int) -> dict:
    """Ficha de una generacion con su lugar en la cronologia del fabricante."""
    gens = fab["generaciones"]
    gen = gens[indice]
    posteriores = [
        {"familia": _familia_limpia(g["familia"]), "etapa": _etapa(g["familia"]),
         "modelos_texto": g["modelos_texto"]}
        for g in gens[indice + 1:]
    ]
    actuales = [
        {"familia": _familia_limpia(g["familia"]), "modelos_texto": g["modelos_texto"],
         "fuentes": _fuentes_de(g["fuentes"])}
        for g in gens if _etapa(g["familia"]) == "actual"
    ]
    # Cuatro fabricantes del documento no marcan ninguna generacion como 'Actual'.
    # Se ofrece la ultima listada, diciendo expresamente que la fuente no la declara
    # vigente: es un indicio cronologico, no una afirmacion de estado comercial.
    nota_actual = ""
    if not actuales and gens:
        ultima = gens[-1]
        actuales = [{"familia": _familia_limpia(ultima["familia"]),
                     "modelos_texto": ultima["modelos_texto"],
                     "fuentes": _fuentes_de(ultima["fuentes"])}]
        nota_actual = ("El documento fuente no marca ninguna generacion de este "
                       "fabricante como 'Actual'; se muestra la ultima de la "
                       "cronologia. Verifica el estado comercial con el fabricante.")
    return {
        "familia": _familia_limpia(gen["familia"]),
        "familia_documento": gen["familia"],
        "etapa": _etapa(gen["familia"]),
        "posicion": f"{indice + 1} de {len(gens)}",
        "modelos_documentados": gen["modelos_texto"],
        "observacion": gen["observacion"],
        "fuentes": _fuentes_de(gen["fuentes"]),
        "generaciones_posteriores": posteriores,
        "generaciones_actuales_del_fabricante": actuales,
        "nota_generacion_actual": nota_actual,
    }


def _destino_documentado(contenido: dict, familia: str | None) -> dict | None:
    """Ruta de migracion que la guia publica para la familia de ORIGEN concreta.

    Es mas precisa que 'la generacion actual del fabricante': la guia distingue,
    por ejemplo, S7-200 -> S7-1200 de S7-300/400 -> S7-1500, y SLC 500 ->
    CompactLogix 5380 de PLC-5 -> ControlLogix.
    """
    if not familia:
        return None
    fam = _norm(familia)
    for origen in contenido.get("origenes") or []:
        if not isinstance(origen, dict):
            continue
        for parte in origen["origen"].split("/"):
            p = _norm(parte)
            if len(p) >= 3 and re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", fam):
                return {
                    "origen_en_guia": origen["origen"],
                    "destino": origen["ruta"],
                    "aspectos_criticos": origen.get("aspectos_criticos", ""),
                }
    return None


def _ruta_guia(marca: str, familia: str | None = None) -> dict | None:
    """Cruza la marca del catalogo con la ruta metodologica de MIGRA-IA-GUIA-001.

    El catalogo dice QUE existe y en que orden; la guia dice COMO se migra. Solo
    5 de las 30 marcas tienen ruta publicada en la guia.
    """
    for alias in _alias_por_marca().get(marca, []):
        res = conocimiento.consultar("fabricante", alias)
        contenido = res.get("contenido")
        if isinstance(contenido, dict) and "marca" in contenido:
            return {
                "marca_en_guia": contenido["marca"],
                "software_legado": contenido.get("software_legado"),
                "software_objetivo": contenido.get("software_objetivo"),
                "redes_heredadas": contenido.get("redes_heredadas"),
                "riesgo_tipico": contenido.get("riesgo_tipico"),
                "destino_documentado": _destino_documentado(contenido, familia),
                "cita": res.get("cita"),
            }
    return None


def identificar(texto: str) -> dict:
    """Resuelve texto libre a marca / familia / modelo del catalogo.

    Busca de lo mas especifico a lo mas general (modelo -> familia -> marca) y
    NUNCA aproxima: si no hay coincidencia devuelve 'no_catalogado' con la
    advertencia correspondiente.
    """
    consulta = (texto or "").strip()
    if not consulta:
        return {"consulta": consulta, "estado": "sin_consulta",
                "nivel_confianza": "no_determinado",
                "advertencia": "No se recibio texto que identificar."}

    norm = _norm(consulta)
    comp = _compacto(consulta)
    catalogo = cargar_catalogo()
    base = {"consulta": consulta, "cita_catalogo": catalogo["documento"]["titulo"],
            "version_catalogo": catalogo["documento"]["version"]}

    # 1) Modelo exacto de CPU.
    for modelo_comp, marca, i, modelo in _indice_modelos():
        coincide = modelo_comp == comp or (
            len(modelo_comp) >= _MIN_LARGO_SUBCADENA and modelo_comp in comp
        )
        if coincide:
            fab = _por_marca(marca)
            desc = _describir_generacion(fab, i)
            return {**base, "estado": "modelo_exacto", "nivel_confianza": "alta_confianza",
                    "marca": marca, "clasificacion": fab["clasificacion"],
                    "modelo_identificado": modelo,
                    **desc,
                    "ruta_migracion_guia": _ruta_guia(marca, desc["familia"]),
                    "nota_verificacion": "Confirmar el numero de parte contra la placa "
                                         "fisica y la fuente oficial antes de especificar."}

    # 2) Familia / generacion.
    for familia_norm, marca, i, familia in _indice_familias():
        if re.search(rf"(?<![a-z0-9]){re.escape(familia_norm)}(?![a-z0-9])", norm):
            fab = _por_marca(marca)
            desc = _describir_generacion(fab, i)
            return {**base, "estado": "familia", "nivel_confianza": "confianza_media",
                    "marca": marca, "clasificacion": fab["clasificacion"],
                    "familia_identificada": familia,
                    **desc,
                    "ruta_migracion_guia": _ruta_guia(marca, desc["familia"]),
                    "dato_faltante": "Modelo exacto de CPU: pedirlo o solicitar foto de la placa."}

    # 3) Solo marca.
    marca = _buscar_marca(norm)
    if marca:
        fab = _por_marca(marca)
        return {**base, "estado": "marca", "nivel_confianza": "confianza_media",
                "marca": marca, "clasificacion": fab["clasificacion"],
                "generaciones": [
                    {"n": g["n"], "familia": _familia_limpia(g["familia"]),
                     "etapa": _etapa(g["familia"]), "modelos_texto": g["modelos_texto"]}
                    for g in fab["generaciones"]
                ],
                "ruta_migracion_guia": _ruta_guia(marca),
                "dato_faltante": "Familia y modelo exacto de CPU: pedirlos o solicitar "
                                 "foto de la placa."}

    # 4) Sin coincidencia: se dice, no se aproxima.
    return {**base, "estado": "no_catalogado", "nivel_confianza": "no_determinado",
            "marca": None,
            "advertencia": "Ni la marca ni el modelo aparecen en el catalogo de 30 "
                           "fabricantes. NO infieras una equivalencia: pide la placa, "
                           "declara el dato como no verificado y remite a la "
                           "documentacion oficial del fabricante.",
            "marcas_disponibles": [f["marca"] for f in catalogo["fabricantes"]]}


def ficha(marca: str, familia: str | None = None) -> dict:
    """Cronologia completa de una marca, o el detalle de una de sus generaciones."""
    consulta = f"{marca} {familia}" if familia else marca
    res = identificar(consulta)
    if res["estado"] == "no_catalogado":
        return res
    return res


def generaciones_actuales(marca: str) -> dict:
    """Familias vigentes de una marca, con sus modelos documentados y sus fuentes.

    `identificar()` solo devuelve esta informacion cuando ademas reconoce una
    familia o un modelo concretos. El paso 13 del procedimiento necesita poder
    preguntar solo por la marca, para ofrecer las plataformas actuales de otros
    fabricantes como alternativa.
    """
    try:
        fab = _por_marca(marca)
    except KeyError:
        return {"marca": marca, "familias": [],
                "error": f"'{marca}' no figura en el catalogo de fabricantes."}
    gens = fab["generaciones"]
    actuales = [g for g in gens if _etapa(g["familia"]) == "actual"]
    nota = ""
    if not actuales and gens:
        # Mismo criterio que `_describir_generacion`: se ofrece la ultima de la
        # cronologia diciendo que la fuente no la declara vigente.
        actuales = [gens[-1]]
        nota = ("El documento fuente no marca ninguna generacion de este fabricante "
                "como 'Actual'; se muestra la ultima de la cronologia. Verifica el "
                "estado comercial con el fabricante.")
    return {
        "marca": fab["marca"],
        "clasificacion": fab["clasificacion"],
        "familias": [
            {"familia": _familia_limpia(g["familia"]),
             "modelos_documentados": g["modelos_texto"],
             "fuentes": _fuentes_de(g["fuentes"])}
            for g in actuales
        ],
        "nota": nota,
    }


_PALABRAS_VACIAS = {
    "tengo", "una", "unos", "unas", "con", "del", "los", "las", "por", "para",
    "que", "plc", "cpu", "marca", "modelo", "familia", "serie", "controlador",
    "equipo", "planta", "maquina", "mi", "el", "la", "un", "de", "y", "es",
}


def sugerencias(texto: str, limite: int = 6) -> list[dict]:
    """Familias del catalogo que comparten algo con lo que escribio el usuario.

    Sirve para el caso en que `identificar()` no reconoce el equipo: en vez de
    dejar al usuario con un 'no lo encuentro', se le ofrecen las entradas REALES
    del catalogo que se le parecen para que confirme cual es. No selecciona
    ninguna ni completa nada: solo pregunta. Un error de tecleo tipo 'S7 1300'
    devuelve asi las familias S7 que si existen.
    """
    tokens = {t for t in _norm(texto).split() if len(t) >= 2 and t not in _PALABRAS_VACIAS}
    if not tokens:
        return []
    # Si el usuario escribio algun nombre ('micrologix', 's7'), la coincidencia
    # tiene que incluirlo. Sin esta condicion, 'MicroLogix 1200' sugeriria un
    # SIMATIC S7-1200 solo porque ambos llevan el numero 1200: una pista falsa.
    con_letras = {t for t in tokens if not t.isdigit()}
    puntuadas: list[tuple[int, dict]] = []
    for fab in cargar_catalogo()["fabricantes"]:
        for gen in fab["generaciones"]:
            familia = _familia_limpia(gen["familia"])
            campo = _norm(f"{fab['marca']} {familia} {gen['modelos_texto']}")
            propios = set(campo.split())
            comunes = tokens & propios
            if not comunes:
                continue
            if con_letras and not (comunes & con_letras):
                continue
            # Un token que ademas es parte del nombre de la familia pesa mas que
            # uno que solo aparece en la lista de modelos.
            peso = len(comunes) + sum(1 for t in comunes if t in _norm(familia).split())
            puntuadas.append((peso, {
                "marca": fab["marca"],
                "familia": familia,
                "etapa": _etapa(gen["familia"]),
                "modelos_documentados": gen["modelos_texto"],
                "coincide_en": sorted(comunes),
            }))
    puntuadas.sort(key=lambda p: -p[0])
    return [d for _, d in puntuadas[:limite]]


def tipo_de_producto(clasificacion: str) -> str:
    """Agrupa las clasificaciones del catalogo para comparar cosas comparables.

    El catalogo usa etiquetas finas ('PLC', 'PLC/PAC', 'IPC / Industrial
    Computer'). Para ofrecer alternativas basta distinguir el controlador de
    programa almacenado del equipo basado en PC.
    """
    c = _norm(clasificacion)
    if "plc" in c or "pac" in c:
        return "plc"
    if "ipc" in c or "pc" in c or "embedded" in c:
        return "pc"
    return "otro"


# --------------------------------------------------------------------------- #
# Anclaje: bloque que fija el equipo en consulta para el resto del dialogo
# --------------------------------------------------------------------------- #
def anclaje(ident: dict) -> str:
    """Texto compacto que se inyecta en el contexto tras identificar el equipo.

    Es la pieza que impide que el agente responda con la marca del ejemplo por
    defecto: a partir de aqui, cada respuesta se refiere a ESTE equipo.
    """
    if not ident or ident.get("estado") in (None, "sin_consulta"):
        return ""

    if ident["estado"] == "no_catalogado":
        return (
            "EQUIPO EN CONSULTA: NO CATALOGADO.\n"
            f"El usuario reporto: '{ident.get('consulta', '')}'.\n"
            f"{ident['advertencia']}\n"
            "Mientras no se identifique, toda recomendacion es preliminar y debe "
            "declararse como tal."
        )

    lineas = [
        "EQUIPO EN CONSULTA (catalogo de fabricantes verificado). Toda respuesta a "
        "partir de aqui se refiere a ESTE equipo: no uses otra marca como ejemplo "
        "por defecto ni traslades rutas de un fabricante a otro.",
        f"- Reportado por el usuario: '{ident.get('consulta', '')}'",
        f"- Marca: {ident['marca']} ({ident.get('clasificacion', '')})",
    ]
    if ident.get("modelo_identificado"):
        lineas.append(
            f"- Modelo localizado en el catalogo: {ident['modelo_identificado']} "
            "(tal como lo lista el documento fuente, que abrevia los modelos "
            "sucesivos de una misma fila)"
        )
    if ident.get("familia"):
        lineas.append(
            f"- Familia/generacion: {ident['familia']} "
            f"(etapa {ident.get('etapa')}, posicion {ident.get('posicion')} en la cronologia)"
        )
        lineas.append(f"- Modelos documentados de esa generacion: {ident['modelos_documentados']}")
        if ident.get("observacion"):
            lineas.append(f"- Observacion del catalogo: {ident['observacion']}")
        actuales = ident.get("generaciones_actuales_del_fabricante") or []
        if actuales:
            destino = "; ".join(f"{a['familia']} ({a['modelos_texto']})" for a in actuales)
            lineas.append(f"- Generacion actual del MISMO fabricante: {destino}")
        if ident.get("nota_generacion_actual"):
            lineas.append(f"- AVISO: {ident['nota_generacion_actual']}")
    elif ident.get("generaciones"):
        fams = "; ".join(f"{g['familia']} [{g['etapa']}]" for g in ident["generaciones"])
        lineas.append(f"- Cronologia de la marca: {fams}")

    if ident.get("etapa") == "actual":
        lineas.append(
            "- ATENCION: esta generacion es la ACTUAL del fabricante segun el catalogo. "
            "No propongas migrarla a si misma: aqui procede plan preventivo, "
            "actualizacion de firmware o ampliacion, no una migracion de plataforma."
        )

    ruta = ident.get("ruta_migracion_guia")
    if ruta:
        destino_doc = ruta.get("destino_documentado")
        if destino_doc:
            lineas.append(
                f"- Ruta de migracion documentada para esta familia de origen "
                f"('{destino_doc['origen_en_guia']}'): -> {destino_doc['destino']}. "
                f"{destino_doc['aspectos_criticos']}"
            )
        lineas.append(
            f"- Ruta metodologica ({ruta['cita']}): software {ruta['software_legado']} -> "
            f"{ruta['software_objetivo']}; redes heredadas {ruta['redes_heredadas']}; "
            f"riesgo tipico: {ruta['riesgo_tipico']}"
        )
    else:
        lineas.append(
            "- La guia MIGRA-IA-GUIA-001 no publica ruta de migracion para esta marca: "
            "aplica la metodologia de 6 etapas de forma generica y apoyate en la "
            "documentacion oficial del fabricante."
        )

    fuentes = ident.get("fuentes") or []
    if fuentes:
        cites = "; ".join(f"[{f['etiqueta']}] {f['url']}" for f in fuentes if f.get("url"))
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
def indice_para_prompt() -> str:
    """Marcas y familias que el agente puede reconocer, sin volcar 469 modelos."""
    catalogo = cargar_catalogo()
    doc = catalogo["documento"]
    lineas = [
        f"CATALOGO DE FABRICANTES Y CPU: {doc['titulo']} ({doc['version']}). "
        f"{len(catalogo['fabricantes'])} fabricantes, "
        f"{sum(len(f['generaciones']) for f in catalogo['fabricantes'])} generaciones "
        f"documentadas con modelos reales y fuente oficial.",
        "Resuelve lo que diga el usuario con `identificar_cpu` (texto libre de placa) y "
        "amplia con `consultar_catalogo` (marca, familia). Marcas y familias:",
    ]
    for fab in catalogo["fabricantes"]:
        fams = "; ".join(_familia_limpia(g["familia"]) for g in fab["generaciones"])
        lineas.append(f"- {fab['marca']} [{fab['clasificacion']}]: {fams}")
    lineas.append(
        "Si el equipo del usuario NO esta en esta lista, dilo explicitamente y pide la "
        "placa: no lo asimiles a la marca mas parecida."
    )
    return "\n".join(lineas)

