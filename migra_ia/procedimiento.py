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

El detalle NO se vuelca al prompt: el system prompt lleva un indice compacto
(`indice_para_prompt`) y el agente pide lo que necesita con la herramienta
`consultar_procedimiento`, que delega en `consultar`.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import config

CITA = "Procedimiento MIGRA-IA-PROC-050 (50 pasos)"

ROLES = {
    "tecnico": "Tecnico de mantenimiento",
    "ingenieria": "Ingenieria de automatizacion",
    "especialista_seguridad": "Especialista en seguridad funcional",
    "responsable": "Responsable de la instalacion",
}

ESTADOS_PASO = ("pendiente", "en_curso", "completado", "no_aplica", "bloqueado")


@lru_cache(maxsize=1)
def cargar() -> dict:
    """Carga y cachea el procedimiento desde disco."""
    with open(config.RUTA_PROCEDIMIENTO, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(texto) -> str:
    return str(texto or "").strip().lower()


# --------------------------------------------------------------------------- #
# Acceso basico
# --------------------------------------------------------------------------- #
def orden() -> list[str]:
    """Claves de los pasos en el orden en que se recorren.

    No es 1..50: la extension de construccion del programa (P1-P7) se intercala
    tras el paso 20. Toda la logica de avance va por esta lista, nunca por el
    numero, para que el documento original conserve su numeracion.
    """
    return list(cargar()["orden"])


def total_pasos() -> int:
    return len(orden())


def _clave(x) -> str:
    return str(x).strip().upper() if not str(x).strip().isdigit() else str(int(str(x).strip()))


def paso_bruto(clave) -> dict | None:
    """Paso tal cual esta en el JSON, sin adaptar a las variantes del caso."""
    c = _clave(clave)
    for p in cargar()["pasos"]:
        if p["clave"] == c:
            return p
    return None


def fase(clave) -> dict | None:
    """Fase por id, por nombre, o por la clave de un paso que contiene."""
    datos = cargar()
    c = _clave(clave)
    for f in datos["fases"]:
        if c in [str(x) for x in f["pasos"]]:
            return f
    n = _norm(clave)
    for f in datos["fases"]:
        if _norm(f["id"]) == n or n in _norm(f["nombre"]):
            return f
    return None


def disparadores() -> list[dict]:
    return cargar()["disparadores"]


def huecos_declarados() -> list[dict]:
    """Lo que el documento fuente no cubre. Se declara, no se rellena inventando."""
    return cargar()["huecos_declarados"]


# --------------------------------------------------------------------------- #
# Contexto del caso: que variantes aplican
# --------------------------------------------------------------------------- #
def contexto(caso) -> dict:
    """Deriva del expediente las variantes que cambian el contenido de los pasos."""
    mig = getattr(caso, "migracion", None) or {}
    ident = getattr(caso, "equipo_identificado", None) or {}
    destino = mig.get("destino") or {}
    return {
        "activa": bool(mig.get("activa")),
        "cambio_marca": bool(mig.get("cambio_marca")),
        "sin_respaldo": bool(mig.get("sin_respaldo")),
        "equipo": ident.get("modelo_identificado") or ident.get("familia") or "",
        "marca": ident.get("marca") or "",
        "familia": ident.get("familia") or "",
        "destino": destino.get("familia") or "",
        "marca_destino": destino.get("marca") or "",
    }


def detectar_disparadores(caso) -> list[dict]:
    """Disparadores que el expediente ya sostiene, con la evidencia que los apoya.

    No decide nada: solo reporta lo que el caso permite afirmar, para que el
    agente proponga abrir el modo guia y el usuario resuelva.
    """
    activos: list[dict] = []
    ident = getattr(caso, "equipo_identificado", None) or {}
    riesgo = getattr(caso, "riesgo", None) or {}
    texto_libre = " ".join(
        _norm(r.get("valor")) for r in (getattr(caso, "respuestas", {}) or {}).values()
    )
    faltantes = " ".join(
        _norm(d.get("descripcion")) for d in (getattr(caso, "datos_faltantes", []) or [])
    )
    banderas = " ".join(
        _norm(b.get("texto")) for b in (getattr(caso, "banderas", []) or [])
    )
    todo = f"{texto_libre} {faltantes} {banderas}"

    por_id = {d["id"]: d for d in disparadores()}

    etapa = _norm(ident.get("etapa"))
    clasificacion = _norm(riesgo.get("clasificacion"))
    if etapa in ("historica", "intermedia") or clasificacion in ("riesgo alto", "riesgo critico"):
        motivo = []
        if etapa in ("historica", "intermedia"):
            motivo.append(f"la generacion del equipo esta clasificada como '{etapa}' en el catalogo")
        if clasificacion in ("riesgo alto", "riesgo critico"):
            motivo.append(f"el motor de riesgo da '{riesgo.get('clasificacion')}'")
        activos.append({**por_id["cpu_obsoleta"], "evidencia_en_el_caso": "; ".join(motivo)})

    if any(p in todo for p in ("contrasena", "password", "clave de la cpu", "bloqueada")):
        activos.append({**por_id["contrasena_desconocida"],
                        "evidencia_en_el_caso": "el expediente menciona una contrasena "
                                                "desconocida o una CPU bloqueada"})

    if any(p in todo for p in ("sin respaldo", "no hay respaldo", "respaldo no verificado",
                               "no se puede abrir", "proyecto corrupto", "sin licencia",
                               "sin adaptador", "no se conoce si hay respaldo")):
        activos.append({**por_id["sin_acceso_al_programa"],
                        "evidencia_en_el_caso": "el expediente reporta que el programa "
                                                "no se puede copiar, abrir o verificar"})

    # Sin duplicar por id, conservando el primero encontrado.
    vistos: set[str] = set()
    unicos = []
    for d in activos:
        if d["id"] not in vistos:
            vistos.add(d["id"])
            unicos.append(d)
    return unicos


# --------------------------------------------------------------------------- #
# Un paso, ya adaptado al caso
# --------------------------------------------------------------------------- #
def paso(clave, ctx: dict | None = None) -> dict | None:
    """Paso con sus variantes ya resueltas segun el contexto del caso."""
    base = paso_bruto(clave)
    if base is None:
        return None
    ctx = ctx or {}
    p = dict(base)
    p["rol_legible"] = ROLES.get(p["rol"], p["rol"])
    p["cita"] = (f"{CITA}, extension de construccion del programa, paso {p['etiqueta']}"
                 if p.get("extension") else f"{CITA}, paso {p['etiqueta']}")

    aplica = True
    avisos: list[str] = []

    if ctx.get("cambio_marca") and base.get("variante_cambio_marca"):
        texto = base["variante_cambio_marca"]
        avisos.append(f"CAMBIO DE MARCA: {texto}")
        if texto.startswith("NO APLICA"):
            aplica = False
    if ctx.get("sin_respaldo") and base.get("variante_sin_respaldo"):
        texto = base["variante_sin_respaldo"]
        avisos.append(f"SIN RESPALDO VERIFICADO: {texto}")
        if texto.startswith("NO APLICA"):
            aplica = False

    p["aplica"] = aplica
    p["avisos"] = avisos
    p["exigencias"] = [k for k, v in p["requiere"].items() if v]
    return p


def texto_paso(clave, ctx: dict | None = None) -> str:
    """Render en Markdown de un paso, listo para mostrarselo al tecnico."""
    p = paso(clave, ctx)
    if p is None:
        return f"No existe el paso {clave} en el procedimiento."
    f = fase(p["clave"]) or {}
    try:
        posicion = orden().index(p["clave"]) + 1
    except ValueError:
        posicion = "?"
    lineas = [
        f"**Paso {p['etiqueta']} ({posicion} de {total_pasos()}) — {p['titulo'].rstrip('.')}**",
        f"*Fase {f.get('nombre', '')} · lo ejecuta: {p['rol_legible']}*",
        "",
        p["detalle"],
        "",]
    if p.get("extension"):
        lineas += [
            "> **Paso de la extension de construccion del programa.** El documento "
            "original de 50 pasos cubre convertir un programa existente, no escribirlo. "
            f"Base metodologica: {p.get('origen_metodologico', '')}.",
            "",
        ]
    lineas += [
        f"**Se da por terminado cuando:** {p['criterio_salida']}",
        "**Evidencia que debe quedar:**",
    ]
    lineas += [f"- {e}" for e in p["evidencia"]]
    if p["prerrequisitos"]:
        lineas.append("")
        lineas.append("**Antes de este paso deben estar cerrados:** "
                      + ", ".join(f"paso {x}" for x in p["prerrequisitos"]))
    if p["exigencias"]:
        etiquetas = {
            "aprobacion_humana": "aprobacion humana registrada",
            "maquina_detenida": "maquina detenida",
            "loto": "bloqueo y etiquetado (LOTO)",
            "especialista_seguridad": "especialista en seguridad funcional presente",
        }
        lineas.append("")
        lineas.append("⚠️ **Exige antes de ejecutarlo:** "
                      + "; ".join(etiquetas[e] for e in p["exigencias"]) + ".")
    if p.get("bloqueante"):
        lineas.append("🚧 **Paso bloqueante:** no se avanza hasta cerrarlo.")
    for aviso in p["avisos"]:
        lineas.append("")
        lineas.append(f"> {aviso}")
    if p.get("nota_agente"):
        lineas.append("")
        lineas.append(f"*Nota: {p['nota_agente']}*")
    if not p["aplica"]:
        lineas.append("")
        lineas.append("**Este paso NO aplica en este caso** por la variante indicada: "
                      "marcalo como `no_aplica` y sigue al siguiente.")
    lineas.append("")
    lineas.append(f"_{p['cita']}_")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Avance: que sigue y que esta bloqueado
# --------------------------------------------------------------------------- #
def _estado_de(caso, clave) -> str:
    mig = getattr(caso, "migracion", None) or {}
    return (mig.get("pasos", {}).get(_clave(clave), {}) or {}).get("estado", "pendiente")


def _cerrado(estado: str) -> bool:
    return estado in ("completado", "no_aplica")


def estado(caso) -> dict:
    """Avance del procedimiento en este caso."""
    ctx = contexto(caso)
    claves = orden()
    total = len(claves)
    por_estado = {e: [] for e in ESTADOS_PASO}
    for c in claves:
        por_estado[_estado_de(caso, c)].append(c)
    cerrados = len(por_estado["completado"]) + len(por_estado["no_aplica"])
    sig = siguiente(caso)
    return {
        "activa": ctx["activa"],
        "total_pasos": total,
        "cerrados": cerrados,
        "porcentaje": round(100 * cerrados / total, 1),
        "completados": por_estado["completado"],
        "no_aplican": por_estado["no_aplica"],
        "en_curso": por_estado["en_curso"],
        "bloqueados": por_estado["bloqueado"],
        "siguiente": sig["etiqueta"] if sig else None,
        "fase_actual": (fase(sig["clave"]) or {}).get("nombre") if sig else "procedimiento completo",
        "variantes": {"cambio_marca": ctx["cambio_marca"], "sin_respaldo": ctx["sin_respaldo"]},
    }


def siguiente(caso) -> dict | None:
    """Primer paso no cerrado, con el detalle de lo que le falta para poder ejecutarse."""
    ctx = contexto(caso)
    for c in orden():
        if _cerrado(_estado_de(caso, c)):
            continue
        p = paso(c, ctx)
        pendientes = [r for r in p["prerrequisitos"] if not _cerrado(_estado_de(caso, r))]
        p["prerrequisitos_pendientes"] = pendientes
        p["ejecutable"] = not pendientes
        return p
    return None


def bloqueos(caso) -> list[dict]:
    """Pasos que no pueden ejecutarse todavia y por que.

    Sirve para que el agente no proponga tocar la maquina antes de tiempo: el
    paso 35 (reemplazo fisico) depende del respaldo verificado y del plan de
    retorno, y esa dependencia es una regla del procedimiento, no un criterio
    del modelo.
    """
    ctx = contexto(caso)
    fuera = []
    for c in orden():
        if _cerrado(_estado_de(caso, c)):
            continue
        p = paso(c, ctx)
        pendientes = [r for r in p["prerrequisitos"] if not _cerrado(_estado_de(caso, r))]
        if pendientes:
            fuera.append({
                "paso": p["etiqueta"],
                "titulo": p["titulo"],
                "prerrequisitos_pendientes": pendientes,
                "bloqueante": bool(p.get("bloqueante")),
            })
    return fuera


# --------------------------------------------------------------------------- #
# Paso 13: las dos opciones de CPU destino
# --------------------------------------------------------------------------- #
def opciones_destino(ident: dict | None, limite_alternativas: int = 8) -> dict:
    """Construye las dos opciones que el agente ofrece en el paso 13.

    Opcion A sale de la cronologia del propio fabricante y, cuando la guia
    publica una ruta para la familia de origen, de esa ruta. Opcion B ofrece las
    plataformas actuales de otras marcas A NIVEL DE FAMILIA: el catalogo no
    publica atributos comparables por modelo, asi que la equivalencia modelo a
    modelo no se afirma, se remite a la herramienta oficial del fabricante.
    """
    from . import fabricantes  # import diferido: evita ciclo en la carga del paquete

    marco = cargar()["opciones_cpu_destino"]
    salida = {
        "paso": marco["paso"],
        "regla": marco["regla"],
        "misma_marca": dict(marco["opciones"][0]),
        "marca_alternativa": dict(marco["opciones"][1]),
    }

    ident = ident or {}
    marca = ident.get("marca")
    if not marca:
        salida["advertencia"] = (
            "El equipo de origen no esta identificado contra el catalogo. Sin marca "
            "y familia no se puede proponer una plataforma destino: pide la placa "
            "antes de continuar con el paso 13."
        )
        return salida

    # --- Opcion A: la generacion actual del mismo fabricante -----------------
    actuales = ident.get("generaciones_actuales_del_fabricante") or []
    ruta = ident.get("ruta_migracion_guia") or {}
    documentado = (ruta or {}).get("destino_documentado") or {}
    salida["misma_marca"].update({
        "marca": marca,
        "familia_origen": ident.get("familia"),
        "familias_actuales": [
            {"familia": a["familia"],
             "modelos_documentados": a["modelos_texto"],
             "fuentes": a.get("fuentes", [])}
            for a in actuales
        ],
        "ruta_publicada_para_el_origen": documentado or None,
        "software_objetivo": ruta.get("software_objetivo"),
        "redes_heredadas": ruta.get("redes_heredadas"),
        "riesgo_tipico": ruta.get("riesgo_tipico"),
        "cita": ruta.get("cita"),
        "nota_generacion_actual": ident.get("nota_generacion_actual") or "",
    })

    # --- Opcion B: plataformas actuales de otras marcas ---------------------
    catalogo = fabricantes.cargar_catalogo()
    tipo_origen = fabricantes.tipo_de_producto(ident.get("clasificacion", ""))
    mismo_tipo: list[dict] = []
    otro_tipo: list[dict] = []
    for fab in catalogo["fabricantes"]:
        if fab["marca"] == marca:
            continue
        act = fabricantes.generaciones_actuales(fab["marca"])
        if not act.get("familias"):
            continue
        registro = {
            "marca": act["marca"],
            "clasificacion": act["clasificacion"],
            "familias_actuales": act["familias"],
            "nota": act.get("nota", ""),
        }
        # Se comparan cosas comparables: un equipo basado en PC no se ofrece como
        # alternativa de un PLC sin decirlo. Los demas quedan disponibles aparte.
        if fabricantes.tipo_de_producto(fab["clasificacion"]) == tipo_origen:
            mismo_tipo.append(registro)
        else:
            otro_tipo.append(registro)

    salida["marca_alternativa"].update({
        "criterio_de_lista": f"Marcas del catalogo del mismo tipo de producto que el equipo "
                             f"de origen ({ident.get('clasificacion')}), excluyendo {marca}.",
        "total_del_mismo_tipo": len(mismo_tipo),
        "mostradas": mismo_tipo[:limite_alternativas],
        "resto_disponible": [a["marca"] for a in mismo_tipo[limite_alternativas:]],
        "otro_tipo_de_producto": [
            {"marca": a["marca"], "clasificacion": a["clasificacion"]} for a in otro_tipo
        ],
    })
    return salida


def texto_opciones(ident: dict | None, limite_alternativas: int = 6) -> str:
    """Render en Markdown de las dos opciones, para el paso 13."""
    o = opciones_destino(ident, limite_alternativas)
    if "advertencia" in o:
        return f"⚠️ {o['advertencia']}"

    a = o["misma_marca"]
    b = o["marca_alternativa"]
    lineas = [
        f"**Paso {o['paso']} — elegir la CPU de reemplazo.** Aqui la decision es tuya. "
        "Te presento las dos vias con sus consecuencias:",
        "",
        f"### Opcion A — seguir con {a['marca']}",
    ]
    ruta = a.get("ruta_publicada_para_el_origen")
    if ruta:
        lineas.append(f"La guia publica una ruta para tu familia de origen "
                      f"(**{ruta['origen_en_guia']}**): destino **{ruta['destino']}**.")
        if ruta.get("aspectos_criticos"):
            lineas.append(f"Aspectos criticos: {ruta['aspectos_criticos']}")
    for fam in a["familias_actuales"]:
        fuentes = "; ".join(f["url"] for f in fam.get("fuentes", []) if f.get("url"))
        lineas.append(f"- **{fam['familia']}** — modelos documentados: {fam['modelos_documentados']}"
                      + (f"\n  Fuente: {fuentes}" if fuentes else ""))
    if a.get("software_objetivo"):
        lineas.append(f"- Software objetivo: **{a['software_objetivo']}**; "
                      f"redes heredadas: {a.get('redes_heredadas')}; "
                      f"riesgo tipico: {a.get('riesgo_tipico')}")
    if a.get("nota_generacion_actual"):
        lineas.append(f"- ⚠️ {a['nota_generacion_actual']}")
    lineas.append("A favor: " + " · ".join(a["a_favor"]))
    lineas.append("En contra: " + " · ".join(a["en_contra"]))

    lineas += ["", "### Opcion B — cambiar de marca", b["que_ofrece"], ""]
    for alt in b["mostradas"]:
        fams = "; ".join(f"**{f['familia']}** ({f['modelos_documentados']})"
                         for f in alt["familias_actuales"])
        lineas.append(f"- **{alt['marca']}** — {fams}")
    if b["resto_disponible"]:
        lineas.append(f"- Y {len(b['resto_disponible'])} marcas mas del mismo tipo en el "
                      "catalogo: " + ", ".join(b["resto_disponible"]) + ".")
    if b.get("otro_tipo_de_producto"):
        otras = ", ".join(f"{a['marca']} ({a['clasificacion']})"
                          for a in b["otro_tipo_de_producto"][:6])
        lineas.append(f"- De otro tipo de producto, si te interesa evaluarlo: {otras}.")
    lineas.append("")
    lineas.append("A favor: " + " · ".join(b["a_favor"]))
    lineas.append("En contra: " + " · ".join(b["en_contra"]))
    lineas.append("")
    lineas.append(f"⚠️ **Limite del agente:** {b['limite_duro']} {b['soporte_de_datos']}")
    lineas.append("")
    lineas.append(f"_{o['regla']}_")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Indice compacto para el system prompt
# --------------------------------------------------------------------------- #
def indice_para_prompt() -> str:
    """Indice del procedimiento: da las claves validas sin volcar el contenido."""
    datos = cargar()
    doc = datos["documento"]
    fases = "; ".join(f"{f['id']} (pasos {f['pasos'][0]}-{f['pasos'][-1]}, etapa {f['etapa_guia']})"
                      for f in datos["fases"])
    disp = "; ".join(f"{d['id']} = {d['titulo']}" for d in datos["disparadores"])
    titulos = "; ".join(f"{p['etiqueta']}={p['titulo'].rstrip('.')}" for p in datos["pasos"])
    return (
        f"PROCEDIMIENTO DE MIGRACION: {doc['titulo']} ({doc['id']}, "
        f"{doc['total_pasos']} pasos). Citalo como '{CITA}, paso N'.\n"
        f"CUANDO SE ABRE: al decidir cambiar la CPU. Disparadores: {disp}.\n"
        f"Fases: {fases}.\n"
        "Consultalo con `consultar_procedimiento` (tema, clave). Temas: paso (clave = "
        "numero), fase (clave = id), disparadores, opciones_destino (las dos opciones "
        "de CPU del paso 13), estado (avance del caso), siguiente (paso que toca), "
        "bloqueos, huecos.\n"
        f"Pasos: {titulos}."
    )


# --------------------------------------------------------------------------- #
# Despachador
# --------------------------------------------------------------------------- #
def consultar(tema: str, clave=None, caso=None) -> dict:
    """Punto unico de consulta, como en `conocimiento.consultar`."""
    t = _norm(tema)
    ctx = contexto(caso) if caso is not None else {}

    if t == "paso":
        p = paso(clave, ctx) if clave is not None else None
        if p is None:
            return {"error": f"Paso no encontrado: {clave}. Validos: 1 a {total_pasos()}."}
        return {"tema": "paso", "cita": p["cita"], "contenido": p,
                "texto": texto_paso(p["n"], ctx)}

    if t == "fase":
        f = fase(clave)
        if f is None:
            return {"error": f"Fase no encontrada: {clave}."}
        return {"tema": "fase", "cita": CITA, "contenido": {
            **f, "pasos_detalle": [{"paso": str(n), "titulo": paso_bruto(n)["titulo"]} for n in f["pasos"]]}}

    if t in ("disparadores", "disparador"):
        contenido = {"catalogo": disparadores()}
        if caso is not None:
            contenido["activos_en_el_caso"] = detectar_disparadores(caso)
        return {"tema": "disparadores", "cita": CITA, "contenido": contenido}

    if t in ("opciones_destino", "opciones", "opciones_cpu"):
        ident = clave if isinstance(clave, dict) else getattr(caso, "equipo_identificado", None)
        return {"tema": "opciones_destino", "cita": CITA,
                "contenido": opciones_destino(ident),
                "texto": texto_opciones(ident)}

    if t == "estado":
        if caso is None:
            return {"error": "El tema 'estado' necesita un caso abierto."}
        return {"tema": "estado", "cita": CITA, "contenido": estado(caso)}

    if t in ("siguiente", "siguiente_paso"):
        if caso is None:
            return {"error": "El tema 'siguiente' necesita un caso abierto."}
        s = siguiente(caso)
        if s is None:
            return {"tema": "siguiente", "cita": CITA,
                    "contenido": {"mensaje": "Los 50 pasos estan cerrados."}}
        return {"tema": "siguiente", "cita": s["cita"], "contenido": s,
                "texto": texto_paso(s["clave"], ctx)}

    if t == "bloqueos":
        if caso is None:
            return {"error": "El tema 'bloqueos' necesita un caso abierto."}
        return {"tema": "bloqueos", "cita": CITA, "contenido": bloqueos(caso)}

    if t in ("huecos", "huecos_declarados"):
        return {"tema": "huecos", "cita": CITA, "contenido": huecos_declarados()}

    if t in ("documento", "procedimiento"):
        return {"tema": "documento", "cita": CITA, "contenido": cargar()["documento"]}

    return {"error": f"Tema no reconocido: {tema}. Validos: paso, fase, disparadores, "
                     "opciones_destino, estado, siguiente, bloqueos, huecos, documento."}
