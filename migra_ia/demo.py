"""Modo demostracion adaptativo (sin API key).

A diferencia de la version anterior -un guion fijo sobre un caso Siemens-, esta
demo LEE el equipo que escribe el usuario, lo identifica contra el catalogo de 30
fabricantes (`fabricantes.py`) y construye el recorrido con los datos reales de
ESA marca: su familia y posicion en la cronologia, su software legado y objetivo,
sus redes heredadas, la generacion actual del MISMO fabricante y su fuente oficial.

Lo que NO cambia es el razonamiento, y es lo que la demostracion quiere ensenar:
descartar la causa raiz externa antes de culpar a la obsolescencia, exigir respaldo
verificado antes de tocar nada, y contrastar el plazo de suministro de un repuesto
contra la parada que la linea tolera.

Sigue usando el MOTOR REAL: cada paso invoca las herramientas verdaderas sobre el
expediente, de modo que el riesgo se calcula con scoring.py y el informe se genera
de verdad. Sirve para presentar el agente sin gastar tokens ni requerir clave.
"""

from __future__ import annotations

import re

from .caso import Caso
from .herramientas import ejecutar_herramienta
from .nucleo import aprobador_pendiente
from . import fabricantes, procedimiento

# Pasos en los que la demo lee lo que escribe el usuario en vez de ignorarlo.
PASO_NOMBRE = 1
PASO_EQUIPO = 2

_TEXTO_FIN = (
    "La demostracion ya termino. Pulsa **Modo demo** para reiniciarla con otro "
    "equipo, o configura tu `ANTHROPIC_API_KEY` y abre un **Caso real (API)** para "
    "un diagnostico conversacional completo sobre tu propia maquina."
)

_SIN_RUTA = "(a confirmar en la documentacion oficial del fabricante)"

# Palabras con las que la interfaz avanza de paso: no son una respuesta del usuario.
_AVANCE = {"", "continuar", "siguiente", "ok", "si", "sigue", "adelante", "next", "."}

_NOTA_NO_LEIDO = (
    "> ⚠️ **He leido lo que escribiste, pero en modo demo no puedo responderte a eso.** "
    "Este recorrido solo lee dos cosas tuyas: tu nombre y tu equipo. El resto son las "
    "respuestas de un caso de referencia ya grabado, y por eso sigo con el guion en "
    "lugar de contestarte. Para un dialogo real, en el que cada respuesta tuya cambie "
    "lo que digo, necesitas **Caso real (API)** con tu `ANTHROPIC_API_KEY`.\n\n---\n\n"
)


_INVITACION_CORREGIR = (
    "\n\n---\n\n**No arranco el recorrido sobre un equipo que no he podido "
    "identificar.** Escribe el equipo corregido y lo vuelvo a intentar. Si prefieres "
    "seguir de todos modos, escribe **`continuar`** y avanzo dejando el hardware "
    "marcado como no verificado."
)


def _es_respuesta_real(texto: str) -> bool:
    """True si el usuario escribio algo que esperaba que el agente leyera.

    Distingue 'continuar' o un Enter suelto -que solo avanzan- de una pregunta o
    una respuesta de verdad, que la demo no puede atender y no debe ignorar en
    silencio.
    """
    t = (texto or "").strip().lower().rstrip(".!?")
    return bool(t) and t not in _AVANCE and len(t) > 3


# --------------------------------------------------------------------------- #
# Contexto del equipo: lo que hace que el recorrido sea de TU marca
# --------------------------------------------------------------------------- #
def extraer_nombre(texto: str) -> str:
    """Saca el nombre de una frase como 'Mi nombre es Carlos, si estoy autorizado'."""
    t = (texto or "").strip()
    m = re.search(r"(?:me llamo|mi nombre es|soy)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ]+)", t, re.IGNORECASE)
    if m:
        return m.group(1).strip().capitalize()
    # Sin formula reconocible: primera palabra que parezca un nombre.
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3,}", t)
    return palabras[0].capitalize() if palabras else "tecnico"


def construir_contexto(texto_equipo: str) -> dict:
    """Traduce lo que escribio el usuario en los datos con los que se arma el guion."""
    ident = fabricantes.identificar(texto_equipo)
    ruta = ident.get("ruta_migracion_guia") or {}
    catalogado = ident["estado"] in ("modelo_exacto", "familia", "marca")
    marca = ident.get("marca") or "el fabricante reportado"

    familia = ident.get("familia") or ""
    modelo = ident.get("modelo_identificado") or ""
    if familia and modelo:
        etiqueta = f"{marca} {familia} ({modelo})"
    elif familia:
        etiqueta = f"{marca} {familia}"
    elif catalogado:
        etiqueta = marca
    else:
        etiqueta = (texto_equipo or "el equipo reportado").strip()

    actuales = ident.get("generaciones_actuales_del_fabricante") or []
    destino_texto = "; ".join(f"{a['familia']} ({a['modelos_texto']})" for a in actuales)
    es_actual = ident.get("etapa") == "actual"

    # De donde sale el destino, en orden de autoridad:
    # 1) la ruta que la guia publica para ESTA familia de origen (la mas precisa:
    #    distingue S7-200 -> S7-1200 de S7-300/400 -> S7-1500);
    # 2) si el equipo YA es la generacion actual, no hay destino: es continuidad;
    # 3) la unica generacion actual del fabricante;
    # 4) varias generaciones actuales: no se elige por el usuario.
    destino_doc = (ruta.get("destino_documentado") or {}) if ruta else {}
    if destino_doc.get("destino"):
        destino_familia = destino_doc["destino"]
    elif es_actual:
        destino_familia = f"continuidad en la propia plataforma {familia}"
    elif len(actuales) == 1:
        destino_familia = actuales[0]["familia"]
    elif actuales:
        destino_familia = (
            "la familia actual de " + marca + " que corresponda ("
            + ", ".join(a["familia"] for a in actuales) + ")"
        )
    else:
        destino_familia = "la plataforma actual del mismo fabricante"

    fuentes = [f for f in (ident.get("fuentes") or []) if f.get("url")]
    fuente_texto = "; ".join(f"[{f['etiqueta']}] {f['url']}" for f in fuentes)

    return {
        "ident": ident,
        "consulta": (texto_equipo or "").strip(),
        "catalogado": catalogado,
        "marca": marca,
        "clasificacion": ident.get("clasificacion", ""),
        "familia": familia or "familia por confirmar",
        "modelo": modelo,
        # Valores para ESCRIBIR en el expediente. Cuando el equipo no esta
        # catalogado no se guarda el texto de relleno ('el fabricante reportado',
        # 'familia por confirmar'): eso convertiria una etiqueta de pantalla en un
        # dato del caso. Se guarda lo que el usuario escribio, tal cual.
        "marca_dato": marca if catalogado else "",
        "familia_dato": familia if catalogado else "",
        "confianza_equipo": "confianza_media" if catalogado else "no_determinado",
        # Fragmentos listos para usar dentro de una frase afirmativa. Sin esto se
        # producen frases como 'la familia familia por confirmar figura
        # descontinuada', que ademas afirma un estado de ciclo de vida sobre una
        # familia que no se ha identificado.
        "familia_frase": (
            f"la familia **{familia}**" if catalogado and familia
            else "el equipo del caso de referencia"
        ),
        "marca_frase": marca if catalogado else "el fabricante del equipo",
        "etiqueta": etiqueta,
        "posicion": ident.get("posicion", ""),
        "etapa": ident.get("etapa", ""),
        "modelos_generacion": ident.get("modelos_documentados", ""),
        "observacion": ident.get("observacion", ""),
        "destino_familia": destino_familia,
        "destino_texto": destino_texto or _SIN_RUTA,
        "es_actual": es_actual,
        "origen_en_guia": destino_doc.get("origen_en_guia", ""),
        "aspectos_criticos": destino_doc.get("aspectos_criticos", ""),
        "tiene_ruta_guia": bool(ruta),
        "sw_legado": ruta.get("software_legado")
        or (f"el software original de {marca} {_SIN_RUTA}" if catalogado
            else f"el software original del fabricante {_SIN_RUTA}"),
        "sw_objetivo": ruta.get("software_objetivo")
        or (f"el entorno actual de {marca} {_SIN_RUTA}" if catalogado
            else f"el entorno de ingenieria actual del fabricante {_SIN_RUTA}"),
        "redes": ruta.get("redes_heredadas") or "las redes del equipo, a levantar en sitio",
        "riesgo_tipico": ruta.get("riesgo_tipico")
        or "conversion del programa, direccionamiento y comunicaciones, a evaluar con la documentacion oficial",
        "cita_guia": ruta.get("cita", "Guia MIGRA-IA-GUIA-001"),
        "fuente_texto": fuente_texto or "sin fuente en el catalogo para este equipo",
        "nota_actual": ident.get("nota_generacion_actual", ""),
        "nombre": "tecnico",
    }


def _bloque_identificacion(ctx: dict, cierre: bool = True) -> str:
    """Lo que el agente 've' del equipo: se muestra tal cual para que sea auditable."""
    if not ctx["catalogado"]:
        base = (
            f"**No encuentro '{ctx['consulta']}' en el catalogo verificado de 30 "
            "fabricantes.** Y eso es exactamente lo que debo decirte: no voy a "
            "asimilarlo a la marca mas parecida ni a trasladarle la ruta de otro "
            "fabricante."
        )
        # Antes de pedir la placa, se ofrecen las entradas REALES del catalogo que
        # se parecen a lo escrito. Un error de tecleo ('S7 1300') se resuelve aqui
        # en lugar de arrastrar un recorrido entero sobre un equipo sin identificar.
        parecidas = fabricantes.sugerencias(ctx["consulta"], limite=5)
        if parecidas:
            filas = "\n".join(
                f"- **{s['marca']} {s['familia']}** — modelos documentados: "
                f"{s['modelos_documentados']}"
                for s in parecidas
            )
            base += (
                "\n\nLo que si tengo en el catalogo y se parece a lo que escribiste:\n\n"
                f"{filas}\n\n"
                "**Es alguna de estas?** Escribela tal cual y el recorrido se rehace "
                "sobre ella. Si no es ninguna, hara falta una **foto de la placa** con "
                "el numero de parte exacto."
            )
        else:
            base += (
                "\n\nHara falta una **foto de la placa** con el numero de parte exacto."
            )
        if not cierre:
            return base
        return base + (
            "\n\nSigo el recorrido con la metodologia generica de 6 etapas, pero todo "
            "lo que diga sobre hardware queda como **preliminar y no verificado**."
        )

    lineas = [
        f"Identificado contra el catalogo: **{ctx['etiqueta']}**"
        + (f" — {ctx['clasificacion']}." if ctx["clasificacion"] else "."),
    ]
    if ctx["posicion"]:
        lineas.append(
            f"- Generacion **{ctx['posicion']}** en la cronologia de {ctx['marca']} "
            f"(etapa {ctx['etapa']})."
        )
    if ctx["modelos_generacion"]:
        lineas.append(f"- Modelos documentados de esa generacion: {ctx['modelos_generacion']}.")
    if ctx["observacion"]:
        lineas.append(f"- Nota del catalogo: {ctx['observacion']}")
    lineas.append(f"- Plataforma actual del **mismo fabricante**: {ctx['destino_texto']}.")
    if ctx["nota_actual"]:
        lineas.append(f"- ⚠️ {ctx['nota_actual']}")
    if ctx["es_actual"]:
        lineas.append(
            "- ⚠️ **Este equipo YA es la generacion actual de su fabricante.** No tendria "
            "sentido proponerte migrarlo a si mismo: en un caso real esto seria un "
            "**diagnostico preventivo** (firmware, repuestos, respaldo, obsolescencia de "
            "la periferia y del software de programacion), no una migracion de plataforma. "
            "Continuo el recorrido para que veas el metodo completo."
        )
    if ctx["origen_en_guia"]:
        lineas.append(
            f"- Ruta de migracion documentada para '{ctx['origen_en_guia']}': "
            f"**→ {ctx['destino_familia']}**."
            + (f" {ctx['aspectos_criticos']}" if ctx["aspectos_criticos"] else "")
        )
    if ctx["tiene_ruta_guia"]:
        lineas.append(
            f"- Ruta de software segun {ctx['cita_guia']}: **{ctx['sw_legado']} → "
            f"{ctx['sw_objetivo']}**; redes heredadas: {ctx['redes']}."
        )
    else:
        lineas.append(
            f"- La guia MIGRA-IA-GUIA-001 no publica ruta de migracion para {ctx['marca']}: "
            "aplico la metodologia generica y remito a la documentacion oficial."
        )
    lineas.append(f"- Fuente: {ctx['fuente_texto']}")
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Guion: se construye con el contexto del equipo del usuario
# --------------------------------------------------------------------------- #
def paso_inicial() -> dict:
    """Paso 0: no depende del equipo todavia."""
    return {
        "texto": (
            "**[MODO DEMOSTRACION — sin clave de API]**\n\n"
            "Hola, soy MIGRA-IA. Asisto paso a paso al personal tecnico para "
            "diagnosticar la obsolescencia de un equipo y orientarlo hacia la "
            "solucion: reparacion, repuesto, **hardware equivalente** o "
            "**migracion** a una plataforma moderna.\n\n"
            "**Esta demostracion lee dos cosas tuyas: tu nombre y TU equipo.** Con la "
            "marca, familia y modelo que escribas, el recorrido se arma desde el "
            "**catalogo verificado de 30 fabricantes, 130 generaciones y 469 modelos "
            "reales de CPU**: su software, sus redes, su plataforma destino y su fuente "
            "oficial. Las herramientas y el calculo de riesgo son los reales: el "
            "expediente del panel derecho se llena de verdad.\n\n"
            "**Los demas datos son los de un caso de referencia**, no tus respuestas: "
            "a partir del equipo, el recorrido te los va presentando y tu solo pulsas "
            "Enviar para avanzar. Por eso no te hare preguntas cuya respuesta no vaya a "
            "leer.\n\n"
            "Para un diagnostico real, en el que el agente se adapte a **cada una** de "
            "tus respuestas, usa **Caso real (API)** con tu `ANTHROPIC_API_KEY`.\n\n"
            "Para empezar: **cual es tu nombre** y estas autorizado para acceder o "
            "modificar el sistema, o solo para diagnostico?"
        ),
        "tools": [],
    }


def paso_nombre(ctx: dict) -> dict:
    """Paso 1: usa el nombre que escribio el usuario y pide el equipo."""
    return {
        "texto": (
            f"Gracias, {ctx['nombre']}. Trabajaremos en **modo diagnostico**: no dare "
            "instrucciones de intervencion sin aprobacion de personal autorizado.\n\n"
            "Ahora lo importante: **que controlador tienes?** Dime **marca, familia y "
            "modelo de la CPU** — por ejemplo `Allen Bradley SLC 5/04`, "
            "`Omron CJ1M-CPU13`, `Mitsubishi Q06HCPU` o `Siemens CPU 315-2 DP`. "
            "Si no lo sabes, una foto de la placa me sirve."
        ),
        "tools": [
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "A", "codigo": "A01", "pregunta": "Nombre del responsable",
                 "valor": ctx["nombre"], "nivel_confianza": "confirmado", "fuente": "verbal"},
                {"seccion": "A", "codigo": "A07", "pregunta": "Autorizacion",
                 "valor": "Solo autorizado para diagnostico", "nivel_confianza": "confirmado",
                 "fuente": "verbal"},
            ]}),
        ],
    }


def construir_pasos(ctx: dict) -> list[dict]:
    """Guion completo desde el paso 2, ya con los datos del equipo del usuario."""
    marca, familia, destino = ctx["marca"], ctx["familia"], ctx["destino_familia"]
    equipo = ctx["etiqueta"]

    return [
        # --- 2: identificacion contra el catalogo (nucleo adaptativo) ---------
        {
            "texto": (
                _bloque_identificacion(ctx)
                + "\n\nLo mas critico ahora es otra cosa: **no hay respaldo verificado "
                "del programa**. Lo marco como dato faltante prioritario.\n\n"
                "---\n"
                "A partir de aqui el recorrido usa un **caso de referencia** con "
                "respuestas ya preparadas, para mostrarte el metodo completo sin gastar "
                "API. Pulsa **Enviar** para avanzar de paso.\n\n"
                "Primer dato del caso: **no se sabe si existe copia del programa**, "
                f"**no se conoce la contrasena** de la CPU, y hay {ctx['sw_legado']} "
                "pero con el adaptador de programacion sin probar."
            ),
            "tools": [
                ("registrar_activo", {
                    "tipo": "cpu",
                    "descripcion": f"CPU {equipo}",
                    "fabricante": ctx["marca_dato"],
                    "modelo": ctx["modelo"] or ctx["familia_dato"],
                    "estado": "Operando con fallas",
                    "nivel_confianza": ctx["confianza_equipo"],
                    "notas": f"Reportado por el usuario: '{ctx['consulta']}'. "
                             "Falla intermitente.",
                }),
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "D", "codigo": "D01", "pregunta": "Fabricante del PLC",
                     "valor": ctx["marca_dato"] or f"sin identificar; el usuario escribio "
                                                   f"'{ctx['consulta']}'",
                     "nivel_confianza": ctx["confianza_equipo"], "fuente": "verbal"},
                    {"seccion": "D", "codigo": "D02", "pregunta": "Familia del PLC",
                     "valor": ctx["familia_dato"] or "sin identificar: pendiente de la placa",
                     "nivel_confianza": ctx["confianza_equipo"], "fuente": "verbal"},
                    {"seccion": "C", "codigo": "C07", "pregunta": "Estado actual",
                     "valor": "Operando con fallas", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                ]}),
                ("registrar_dato_faltante", {
                    "descripcion": "Respaldo del programa del PLC sin verificar",
                    "impacto": "Bloquea cualquier descarga o migracion segura hasta recuperarlo.",
                }),
            ],
        },
        # --- 3: respaldo y redes ---------------------------------------------
        {
            "texto": (
                "Entendido: no se conoce si hay respaldo. La **prioridad 1** pasa a ser "
                "recuperar el programa antes de cualquier otra accion.\n\n"
                f"Sigamos con las comunicaciones y la criticidad. En equipos {marca} de "
                f"esta generacion lo habitual es encontrar **{ctx['redes']}**, y es lo "
                "que reporta el caso de referencia. La maquina es de **criticidad "
                "alta**: afecta una linea importante de produccion."
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "F", "codigo": "F01", "pregunta": "Existe copia del programa?",
                     "valor": "No se conoce", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                    {"seccion": "G", "codigo": "G01", "pregunta": "Redes utilizadas",
                     "valor": ctx["redes"], "nivel_confianza": "confianza_media", "fuente": "verbal"},
                ]}),
            ],
        },
        # --- 4: criticidad y objetivo ----------------------------------------
        {
            "texto": (
                f"Anotado: **criticidad alta** y redes **{ctx['redes']}** (determinante "
                "para elegir una plataforma destino que las conserve o las convierta).\n\n"
                "Ultima parte antes de evaluar. En el caso de referencia **no se sabe** "
                "si la migracion afectaria funciones de seguridad (paros de emergencia, "
                "cortinas, PLC de seguridad), y el objetivo declarado es **reducir el "
                "riesgo de parada y evaluar la migracion**."
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "C", "codigo": "C08", "pregunta": "Criticidad de la maquina",
                     "valor": "Alta: afecta una linea importante",
                     "nivel_confianza": "confianza_media", "fuente": "verbal"},
                    {"seccion": "K", "codigo": "K01", "pregunta": "Que desea realizar?",
                     "valor": "Reducir riesgo de parada; evaluar migracion",
                     "nivel_confianza": "confirmado", "fuente": "verbal"},
                ]}),
            ],
        },
        # --- 5: bandera de seguridad y apertura de la seccion M ---------------
        {
            "texto": (
                "Como no se conoce si la migracion afecta la seguridad, activo una "
                "**bandera de seguridad funcional**: cualquier cambio que la toque "
                "requiere revision de un especialista.\n\n"
                "Todavia **no puedo puntuar el riesgo**: me falta la evidencia que lo "
                "sustenta. Consulto el cuestionario para abrir la **Seccion M** (ciclo "
                "de vida, soporte y repuestos), que es la que mas pesa en la decision.\n\n"
                f"Los datos de ciclo de vida del caso de referencia: {ctx['familia_frase']} "
                "figura **descontinuada**, aunque aun con soporte; los repuestos solo se "
                "consiguen **por pedido especial** y tardan **de 2 a 8 semanas**; y la "
                "maquina tolera **de 4 a 12 horas** parada."
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "I", "codigo": "I07",
                     "pregunta": "La migracion afectara funciones de seguridad?",
                     "valor": "No se conoce", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                ]}),
                ("registrar_bandera_seguridad", {
                    "texto": "REVISION OBLIGATORIA POR ESPECIALISTA EN SEGURIDAD FUNCIONAL"}),
                ("consultar_cuestionario", {"tema": "seccion", "clave": "M"}),
            ],
        },
        # --- 6: hallazgo del plazo de suministro ------------------------------
        {
            "texto": (
                "Aqui aparece el primer hallazgo duro. Cruzo dos respuestas:\n\n"
                "- **M06** — un repuesto critico tarda **de 2 a 8 semanas** en llegar.\n"
                "- **C10** — la maquina solo tolera **de 4 a 12 horas** parada.\n\n"
                "El repuesto llega **entre 20 y 300 veces mas tarde** de lo que la linea "
                "aguanta. Conclusion, y la digo sin rodeos: **la estrategia de repuesto "
                "no cubre este riesgo por si sola**. Solo serviria con una CPU ya "
                "comprada y en el estante.\n\n"
                "Ahora el historial del caso de referencia: **6 paros** no programados en "
                "el ultimo ano, **en aumento**, con danos en la bateria o el respaldo de "
                "memoria y en bornes y conectores. Y el dato que lo cambia todo: **la "
                "maquina pierde la hora al quitarle la energia**.\n\n"
                "(En un caso real esta es una de las preguntas que mas informacion da, y "
                "por eso el agente la hace siempre.)"
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "M", "codigo": "M01",
                     "pregunta": "Estado del producto declarado por el fabricante",
                     "valor": "Descontinuado, aun con soporte y repuestos",
                     "nivel_confianza": "confianza_media",
                     "fuente": "verbal (pendiente de verificar en la pagina de ciclo de vida del fabricante)"},
                    {"seccion": "M", "codigo": "M04", "pregunta": "Se consiguen repuestos nuevos?",
                     "valor": "Solo por pedido especial", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "M", "codigo": "M05",
                     "pregunta": "Se consiguen repuestos usados o reacondicionados?",
                     "valor": "Si, sin garantia", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "M", "codigo": "M06",
                     "pregunta": "Plazo de entrega tipico de un repuesto critico",
                     "valor": "De 2 a 8 semanas", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "M", "codigo": "M07", "pregunta": "Existe servicio de reparacion?",
                     "valor": "Si, de tercero certificado", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "M", "codigo": "M09",
                     "pregunta": "Existe contrato de soporte vigente?",
                     "valor": "No", "nivel_confianza": "confirmado", "fuente": "verbal"},
                    {"seccion": "C", "codigo": "C10",
                     "pregunta": "Tiempo maximo permitido de parada",
                     "valor": "4 a 12 horas", "nivel_confianza": "confirmado", "fuente": "verbal"},
                ]}),
                ("registrar_dato_faltante", {
                    "descripcion": (
                        f"Estado de ciclo de vida de la familia {familia} ({marca}) sin "
                        "verificar en fuente oficial" if ctx["catalogado"] else
                        "Estado de ciclo de vida: no puede verificarse mientras el equipo "
                        "no este identificado contra el catalogo"),
                    "impacto": "El factor de mayor peso (0.20) se apoya en una declaracion "
                               "verbal; hay que confirmarlo en la pagina de ciclo de vida "
                               "del fabricante.",
                }),
            ],
        },
        # --- 7: causa raiz externa (el giro del diagnostico) ------------------
        {
            "texto": (
                "**Atencion, esto cambia el diagnostico.** Perder la hora al quitar la "
                "energia es el sintoma clasico de una **bateria de respaldo agotada** "
                "(L07), no de un PLC obsoleto. Y el tablero a **45 C con los filtros sin "
                "mantenimiento** (P01, P02) acorta la vida de la electronica y explica "
                "fallas intermitentes.\n\n"
                "Regla del agente, y va en serio: **antes de atribuir las fallas a la "
                "obsolescencia hay que descartar la causa raiz externa.** Si cambiaramos "
                f"el PLC {marca} sin corregir la temperatura y la tierra, el equipo nuevo "
                "volveria a fallar. Lo registro como causa raiz probable.\n\n"
                "Aviso importante: **cambiar esa bateria con la CPU sin energia puede "
                "borrar el programa**, y aqui no hay respaldo verificado. Primero el "
                "respaldo, despues la bateria. Sin excepcion.\n\n"
                "Ultimo bloque de datos del caso: hay una PC compartida con "
                f"{ctx['sw_legado']}, pero sobre **Windows 7**, con licencia por **llave "
                "fisica**, el adaptador **sin probar** y la **contrasena desconocida**."
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "L", "codigo": "L01",
                     "pregunta": "Paros no programados en los ultimos 12 meses",
                     "valor": "6", "nivel_confianza": "baja_confianza",
                     "fuente": "estimacion del tecnico (sin registro digital)"},
                    {"seccion": "L", "codigo": "L02", "pregunta": "Duracion promedio de esos paros",
                     "valor": "1 a 4 horas", "nivel_confianza": "baja_confianza",
                     "fuente": "estimacion"},
                    {"seccion": "L", "codigo": "L03",
                     "pregunta": "Evolucion de la frecuencia de fallas",
                     "valor": "En aumento", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                    {"seccion": "L", "codigo": "L04", "pregunta": "Componentes que han fallado",
                     "valor": "Bateria o respaldo de memoria; cableado, bornes o conectores",
                     "nivel_confianza": "confianza_media", "fuente": "verbal"},
                    {"seccion": "L", "codigo": "L07",
                     "pregunta": "Pierde el programa o la hora al quitar la energia?",
                     "valor": "Si", "nivel_confianza": "confirmado",
                     "fuente": "observado por el tecnico"},
                    {"seccion": "L", "codigo": "L08",
                     "pregunta": "Existe registro historico de mantenimiento?",
                     "valor": "Si, en papel", "nivel_confianza": "confirmado", "fuente": "verbal"},
                    {"seccion": "P", "codigo": "P01", "pregunta": "Temperatura dentro del tablero",
                     "valor": "Entre 40 y 50 C (medida: 45 C)", "nivel_confianza": "confirmado",
                     "fuente": "medicion con termometro"},
                    {"seccion": "P", "codigo": "P02",
                     "pregunta": "Ventilacion, filtros o climatizacion del tablero",
                     "valor": "Si, sin mantenimiento (filtros saturados)",
                     "nivel_confianza": "confirmado", "fuente": "inspeccion visual"},
                    {"seccion": "P", "codigo": "P04", "pregunta": "Calidad de la energia electrica",
                     "valor": "Sin UPS; puesta a tierra dudosa",
                     "nivel_confianza": "confianza_media", "fuente": "verbal"},
                ]}),
                ("registrar_dato_faltante", {
                    "descripcion": "Causa raiz externa probable no corregida: bateria agotada "
                                   "(L07), tablero a 45 C con filtros saturados (P01/P02) y "
                                   "puesta a tierra dudosa (P04)",
                    "impacto": "Mientras no se corrijan, cualquier controlador nuevo volvera a "
                               "fallar; condiciona la lectura del historial de fallas.",
                }),
            ],
        },
        # --- 8: software, licencias y contrasena ------------------------------
        {
            "texto": (
                "Tercer hallazgo, y este bloquea la Prioridad 1. Para leer el programa "
                "hacen falta cuatro cosas y **tres estan en duda**:\n\n"
                "| Requisito | Estado |\n"
                "|---|---|\n"
                f"| PC con {ctx['sw_legado']} | Si, compartida — pero sobre **Windows 7**, "
                "sin soporte (N02) |\n"
                "| Licencia | **Llave fisica (dongle)** (N03): si se pierde o se dana, el "
                "proyecto queda inaccesible |\n"
                "| Cable / adaptador | Adaptador de programacion **sin probar** con este "
                "PLC (N05) |\n"
                "| Contrasena de la CPU | **No se conoce** (N06) |\n\n"
                "La contrasena es la que mas pesa: si no aparece, recuperar el programa "
                "puede ser imposible y la balanza se inclina hacia **reconstruir**, que "
                "es la salida mas cara y lenta. Antes de llegar ahi, la via correcta es "
                "pedir el proyecto fuente al fabricante de la maquina o al integrador — "
                "nunca saltarse la proteccion.\n\n"
                "Con la economia ya tengo lo necesario para puntuar. Calculo el riesgo…"
            ),
            "tools": [
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "N", "codigo": "N01",
                     "pregunta": "Existe PC con el software instalado?",
                     "valor": f"Si, compartida ({ctx['sw_legado']})",
                     "nivel_confianza": "confirmado", "fuente": "verbal"},
                    {"seccion": "N", "codigo": "N02", "pregunta": "Sistema operativo de esa PC",
                     "valor": "Windows 7", "nivel_confianza": "confirmado", "fuente": "verbal"},
                    {"seccion": "N", "codigo": "N03", "pregunta": "Tipo de licencia del software",
                     "valor": "Llave fisica (dongle)", "nivel_confianza": "confirmado",
                     "fuente": "verbal"},
                    {"seccion": "N", "codigo": "N05",
                     "pregunta": "Cable o adaptador de programacion",
                     "valor": "Si, pero sin probar", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "N", "codigo": "N06",
                     "pregunta": "Se conocen las contrasenas del proyecto?",
                     "valor": "No", "nivel_confianza": "confirmado", "fuente": "verbal"},
                    {"seccion": "N", "codigo": "N07",
                     "pregunta": "Quien posee el proyecto fuente original?",
                     "valor": "El fabricante de la maquina", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "Q", "codigo": "Q01",
                     "pregunta": "Costo aproximado de una hora de parada",
                     "valor": "Aprox. 1200 USD/hora (estimacion)", "nivel_confianza": "baja_confianza",
                     "fuente": "estimacion de produccion"},
                    {"seccion": "Q", "codigo": "Q04",
                     "pregunta": "Cuando puede intervenirse la maquina?",
                     "valor": "En el paro anual de planta", "nivel_confianza": "confirmado",
                     "fuente": "verbal"},
                    {"seccion": "Q", "codigo": "Q05",
                     "pregunta": "Anos que se espera que la maquina siga en produccion",
                     "valor": "De 5 a 10 anos", "nivel_confianza": "confianza_media",
                     "fuente": "verbal"},
                    {"seccion": "Q", "codigo": "Q07",
                     "pregunta": "Otras maquinas con el mismo PLC obsoleto",
                     "valor": "3 maquinas mas en la planta", "nivel_confianza": "confirmado",
                     "fuente": "verbal"},
                ]}),
                ("registrar_dato_faltante", {
                    "descripcion": f"Contrasena de la CPU {equipo} desconocida (N06) y proyecto "
                                   "fuente en poder del fabricante de la maquina (N07)",
                    "impacto": "Si no se obtiene, la recuperacion del programa puede ser inviable "
                               "y la alternativa se desplaza hacia reconstruccion.",
                }),
            ],
        },
        # --- 9: calculo de riesgo con el motor real ---------------------------
        {
            "texto": (
                "**Riesgo calculado.** Mira el panel: la puntuacion sale del motor real "
                "(los 8 factores ponderados de la Seccion 6).\n\n"
                "Fijate en un detalle: **cada factor cita la pregunta que lo sustenta**, "
                "no mi opinion.\n\n"
                "Un matiz honesto sobre el **historial de fallas**: lo puntuo en 60 y no "
                "mas alto porque buena parte de esas fallas tiene **causa raiz externa** "
                "(bateria, temperatura, tierra). Cargarselas al PLC seria un error de "
                "diagnostico que costaria una migracion innecesaria.\n\n"
                "Ahora la decision: **reparar o migrar?**"
            ),
            "tools": [
                ("calcular_riesgo_obsolescencia", {"factores": {
                    "estado_ciclo_vida": {"valor": 75, "justificacion":
                        (f"M01: familia {familia} declarada descontinuada, aun con soporte y "
                         "repuestos. Pendiente de verificar en fuente oficial del fabricante."
                         if ctx["catalogado"] else
                         "M01: el caso de referencia declara el equipo descontinuado, aun con "
                         "soporte y repuestos. El equipo NO esta identificado contra el "
                         "catalogo, asi que este factor se apoya solo en la declaracion "
                         "verbal y queda pendiente de la placa.")},
                    "disponibilidad_repuestos": {"valor": 85, "justificacion":
                        "M04 solo por pedido especial y M06 de 2 a 8 semanas frente a C10 de "
                        "4 a 12 horas de parada tolerable: el plazo excede con mucho la "
                        "ventana. Sin repuesto en existencia."},
                    "soporte_fabricante": {"valor": 60, "justificacion":
                        "M09 sin contrato de soporte vigente; M07 existe reparacion de tercero "
                        "certificado, lo que amortigua el riesgo."},
                    "disponibilidad_software": {"valor": 70, "justificacion":
                        f"N01/N02 {ctx['sw_legado']} sobre Windows 7 sin soporte; N03 licencia "
                        "por llave fisica; N05 adaptador sin probar; N06 contrasena de la CPU "
                        "desconocida."},
                    "disponibilidad_respaldo": {"valor": 100, "justificacion":
                        "F01 sin respaldo verificado del programa; nada permite recargarlo hoy."},
                    "compatibilidad_sistemas": {"valor": 50, "justificacion":
                        f"G01 {ctx['redes']}; riesgo tipico de conversion: {ctx['riesgo_tipico']}"},
                    "historial_fallas": {"valor": 60, "justificacion":
                        "L01 seis paros y L03 en aumento, pero L07 (bateria agotada) y P01/P04 "
                        "(45 C, tierra dudosa) apuntan a causa raiz externa aun no corregida: "
                        "no todo es atribuible al controlador."},
                    "criticidad_productiva": {"valor": 85, "justificacion":
                        "C08 criticidad alta, C10 solo 4-12 horas de parada tolerable, Q01 unos "
                        "1200 USD/hora y Q04 unica ventana en el paro anual."},
                }}),
            ],
        },
        # --- 10: alternativas y recomendacion ---------------------------------
        {
            "texto": (
                "**Reparar o migrar?** No es una eleccion entre dos cosas: es un orden. "
                "Recorro las alternativas con el mapa de decision y digo por que cada "
                "una sirve o no **en tu caso concreto**.\n\n"
                "| # | Alternativa | Veredicto aqui |\n"
                "|---|---|---|\n"
                "| 1 | **Corregir la causa raiz** | **SI, y primero.** Bateria (L07), "
                "filtros y 45 C (P01/P02), tierra (P04). Barato e inmediato. Sin esto, "
                "un PLC nuevo vuelve a fallar |\n"
                "| 2 | **Reparacion** | Parcial. Hay taller certificado (M07), pero no "
                "revierte la obsolescencia: M01 ya esta descontinuado |\n"
                "| 3 | **Repuesto directo** | **NO cubre el riesgo.** M06 de 2 a 8 "
                "semanas contra C10 de 4 a 12 horas. Solo valdria con la CPU ya en el "
                "estante |\n"
                "| 4 | **Hardware equivalente** | Viable como puente, con la misma "
                "limitacion de suministro |\n"
                f"| 5 | **Migracion a {destino}** | **SI, planificada.** Q05 quedan 5-10 "
                "anos de vida util, Q04 hay ventana en el paro anual y Q07 son 4 maquinas "
                "iguales: plan por etapas y repuestos compartidos |\n"
                "| 6 | **Reconstruccion** | Ultimo recurso. Se activaria solo si no "
                "aparecen la contrasena (N06) ni el proyecto fuente (N07) |\n\n"
                "**Recomendacion en tres tiempos, en este orden:**\n\n"
                "1. **Ahora** — recuperar y verificar el respaldo (Prioridad 1: sin el no "
                "se puede ni cambiar la bateria sin arriesgar el programa) y pedir el "
                "proyecto fuente al fabricante de la maquina.\n"
                "2. **Esta semana** — corregir la causa raiz: bateria, limpieza de "
                "filtros y ventilacion, revision de la puesta a tierra. Comprar una CPU "
                "de repuesto para cubrir las 2-8 semanas de suministro.\n"
                f"3. **Proximo paro anual** — migrar a **{destino}**, empezando por esta "
                "maquina como piloto de las 4.\n\n"
                "Te muestro las equivalencias."
            ),
            "tools": [("consultar_cuestionario", {"tema": "criterios"})],
        },
        # --- 11: equivalencias, ya de la marca correcta -----------------------
        {
            "texto": (
                "**Sugerencia de equivalencias (preliminar — a verificar).**\n\n"
                "| Elemento actual | Candidato equivalente | Criterio |\n"
                "|---|---|---|\n"
                f"| CPU {equipo} | Familia **{destino}** del mismo fabricante | Continuidad "
                "de plataforma, herramientas y repuestos; mayor memoria y rendimiento |\n"
                f"| Periferia y modulos de E/S de {familia} | Periferia de la familia "
                f"{destino} | Mismos tipos de senal (DI/DO/AI/AO); reutilizacion de "
                "cableado por canal a verificar |\n"
                f"| {ctx['sw_legado']} | **{ctx['sw_objetivo']}** | Ruta de conversion del "
                f"programa; riesgo tipico: {ctx['riesgo_tipico']} |\n"
                f"| Redes: {ctx['redes']} | Redes soportadas por {destino} (o pasarela) | "
                "Conservar la red de campo o convertirla con modulo/gateway |\n\n"
                f"Modelos que el catalogo documenta para **{destino}**: "
                f"{ctx['destino_texto']}.\n"
                f"Fuente: {ctx['fuente_texto']}\n\n"
                "⚠️ **Importante (regla del agente):** estas son familias candidatas por "
                "criterio tecnico; **no confirmo numeros de catalogo exactos** ni "
                "completo codigos que el catalogo no liste. Deben verificarse con el "
                "fabricante y su herramienta oficial de seleccion/migracion, y validarse "
                "contra E/S, memoria, tiempo de ciclo y funciones especiales reales."
            ),
            "tools": [],
        },
        # --- 12: se toma la decision y se ABRE EL MODO GUIA -------------------
        {
            "texto": (
                "**Aqui es donde el agente cambia de papel.**\n\n"
                "Hasta este punto he diagnosticado. El caso reune dos motivos para "
                f"cambiar la CPU: {ctx['familia_frase']} esta descontinuada, y la "
                "**contrasena de la CPU es desconocida**, asi que el programa anterior "
                "no se puede copiar ni abrir.\n\n"
                "La decision es tuya, no mia. En un caso real te preguntaria aqui si "
                "quieres migrar. En el caso de referencia la respuesta es **si**, asi que "
                "abro el **modo guia**: a partir de ahora te acompano por el "
                "**procedimiento de 50 pasos** (MIGRA-IA-PROC-050) mas la extension "
                "**P1-P7** de construccion del programa, uno a uno, con su criterio "
                "de cierre y la evidencia que debe quedar.\n\n"
                "Mira el panel: el expediente ya registra que el modo guia esta abierto, "
                "con su disparador. Y como no hay programa recuperable, queda declarada la "
                "variante **sin respaldo verificado**, que cambia el contenido de varios "
                "pasos mas adelante."
            ),
            "tools": [
                ("iniciar_guia_migracion", {
                    "disparador": "contrasena_desconocida",
                    "motivo": f"Familia {familia} descontinuada y contrasena de la CPU "
                              "desconocida: el programa no se puede copiar ni abrir.",
                    "decidido_por": "sugerencia_del_agente_aceptada",
                    "sin_respaldo": True,
                }),
            ],
        },
        # --- 13: paso 13 del procedimiento, las dos opciones de CPU -----------
        {
            "texto": (
                "Primer punto de decision de la guia. No lo resuelvo yo:\n\n"
                + procedimiento.texto_opciones(ctx["ident"], limite_alternativas=5)
            ),
            "tools": [],
        },
        # --- 14: el usuario elige y se registra el destino ---------------------
        # Sin equipo catalogado no hay destino que registrar: el paso 13 queda
        # bloqueado. Registrar una plataforma inventada aqui contradiria lo que el
        # agente acaba de decir en el paso anterior y ensuciaria el expediente.
        {
            "texto": (
                f"En el caso de referencia se elige la **Opcion A**: seguir con {marca}, "
                f"destino **{destino}**.\n\n"
                "Queda registrado en el expediente con su justificacion y su fuente. Como "
                "la marca no cambia, el procedimiento se mantiene completo: los pasos 21 y "
                "22 (migrar con la herramienta oficial del fabricante y revisar su reporte) "
                "**si aplican**.\n\n"
                "Si hubieras elegido otra marca, esos dos pasos se habrian marcado como **no "
                "aplicables** y el programa se reescribiria desde cero. Esa diferencia no la "
                "improviso: viene declarada paso por paso en el procedimiento."
            ) if ctx["catalogado"] else (
                "**El paso 13 se queda abierto, y con razon.**\n\n"
                f"No puedo elegir una CPU destino para '{ctx['consulta']}' porque el equipo "
                "de origen no esta en el catalogo verificado. Registrar aqui una plataforma "
                "seria inventarla.\n\n"
                "El procedimiento marca el paso 13 como **bloqueado** hasta que llegue la "
                "**foto de la placa** con el numero de parte exacto. Los pasos que no "
                "dependen del destino (levantamiento de E/S, redes, funcionamiento del "
                "proceso) si pueden avanzar mientras tanto.\n\n"
                "Esto es lo que un plan generico no hace: seguir adelante como si supiera."
            ),
            "tools": ([
                ("fijar_cpu_destino", {
                    "marca": marca,
                    "familia": destino,
                    "justificacion": f"Ruta publicada por el fabricante para la familia de "
                                     f"origen {familia}; conserva software, redes y "
                                     "ecosistema de repuestos.",
                    "fuente": ctx["fuente_texto"],
                }),
            ] if ctx["catalogado"] else [
                ("marcar_paso_migracion", {
                    "paso": 13, "estado": "bloqueado",
                    "nota": "Equipo de origen no catalogado: sin marca ni familia "
                            "verificadas no se propone plataforma destino.",
                }),
                ("registrar_dato_faltante", {
                    "descripcion": "Placa del equipo con el numero de parte exacto",
                    "impacto": "Bloquea el paso 13 del procedimiento (seleccion de la CPU "
                               "de reemplazo) y todos los pasos que dependen de el.",
                }),
            ]),
        },
        # --- 15: arranque del recorrido, sin repetir el diagnostico -----------
        {
            "texto": (
                "**Arranca el recorrido de los 50 pasos.** Lo primero que hago es *no* "
                "hacerte perder el tiempo: los pasos 1, 2, 4, 6, 8, 9 y 10 preguntan cosas "
                "que el diagnostico ya registro, asi que los cierro citando de donde salen, "
                "en lugar de volver a preguntartelas.\n\n"
                f"- Paso 1 (identificar el sistema) → cerrado con la identificacion de "
                f"{ctx['etiqueta']} contra el catalogo.\n"
                f"- Paso 2 (estado de obsolescencia) → cerrado: familia descontinuada, "
                "repuestos de 2 a 8 semanas.\n"
                f"- Paso 4 (versiones de software) → cerrado: {ctx['sw_legado']}.\n"
                "- Paso 6 (funcionamiento del proceso) → cerrado con lo levantado en el "
                "diagnostico.\n"
                f"- Pasos 8, 9 y 10 (comunicaciones, red y dependencias) → cerrados: "
                f"{ctx['redes']}.\n\n"
                "Fijate en el paso 6: **con la contrasena perdida, deja de ser papeleo y "
                "pasa a ser la fuente principal** de la que saldra el programa nuevo. El "
                "procedimiento lo dice explicitamente en su variante sin respaldo."
            ),
            "tools": [
                ("marcar_paso_migracion", {"paso": 1, "estado": "completado",
                    "nota": "Cerrado con la identificacion del equipo contra el catalogo.",
                    "evidencia": ["Ficha del catalogo de fabricantes"]}),
                ("marcar_paso_migracion", {"paso": 2, "estado": "completado",
                    "nota": "Familia descontinuada; repuestos de 2 a 8 semanas.",
                    "evidencia": ["Seccion M del cuestionario"]}),
                ("marcar_paso_migracion", {"paso": 4, "estado": "completado",
                    "nota": f"Software legado: {ctx['sw_legado']}.",
                    "evidencia": ["Seccion N del cuestionario"]}),
                ("marcar_paso_migracion", {"paso": 6, "estado": "en_curso",
                    "nota": "Sin respaldo recuperable, este paso es la fuente principal "
                            "de la especificacion del sistema nuevo."}),
                ("marcar_paso_migracion", {"paso": 8, "estado": "completado",
                    "nota": f"Redes: {ctx['redes']}.", "evidencia": ["Seccion G"]}),
                ("marcar_paso_migracion", {"paso": 9, "estado": "completado",
                    "nota": "Arquitectura de red levantada.", "evidencia": ["Seccion G"]}),
                ("marcar_paso_migracion", {"paso": 10, "estado": "completado",
                    "nota": "Dependencias externas identificadas.", "evidencia": ["Secciones G y H"]}),
            ],
        },
        # --- 16: el paso que toca, con su criterio de cierre -------------------
        {
            "texto": (
                "Y este es el paso que toca ahora. Asi se ve **cada uno** de los 50: que "
                "hay que hacer, cuando se da por terminado, que evidencia debe quedar y "
                "quien lo ejecuta.\n\n"
                + procedimiento.texto_paso(3, {"sin_respaldo": True})
            ),
            "tools": [],
        },
        # --- 13: guia paso a paso para principiante ---------------------------
        {
            "texto": (
                f"**Guia paso a paso (nivel principiante) — adaptada a tu equipo {marca}.**\n\n"
                "Como la Prioridad 1 es recuperar el respaldo, te dejo el procedimiento "
                "detallado, como si fuera la primera vez que lo haces. En un caso real, "
                "antes del detalle operativo pediria **aprobacion humana**.\n\n"
                f"**A) Crear el respaldo del programa ({familia} con {ctx['sw_legado']}):**\n\n"
                "1. Consigue autorizacion del responsable y confirma que puedes conectarte "
                "sin detener la produccion.\n"
                "2. Prepara la PC con el software y la **version correcta**, el cable o "
                "adaptador de programacion adecuado y su driver.\n"
                "3. Conecta el cable entre la PC y el puerto de programacion del PLC.\n"
                "4. Abre el software y crea un proyecto vacio para recibir el programa.\n"
                "5. Ponte **en linea**: elige la interfaz y la direccion del PLC y "
                "comprueba que responde.\n"
                "6. **SUBE/LEE TODO** desde el PLC hacia la PC: programa, configuracion de "
                "hardware, y simbolos y comentarios si existen.\n"
                "7. Guarda el proyecto con un nombre claro (equipo + fecha) y anota la "
                "version exacta del software.\n"
                "8. **VERIFICA** el respaldo: que abra sin errores y que compile. Anota "
                "tamano o checksum.\n"
                "9. Guarda **al menos dos copias** en lugares distintos.\n\n"
                "Si la CPU tiene contrasena y no se conoce — que es tu caso (N06) — "
                "**detente y escala**. Si el respaldo no se puede verificar, tratalo como "
                "**sin respaldo**.\n\n"
                f"**B) Cargar el programa en la CPU nueva ({destino}):** eso no es un "
                "apartado suelto, son los pasos **35 a 38** del procedimiento (reemplazo "
                "fisico, verificacion electrica, descarga y prueba de E/S punto por punto), "
                "y **estan bloqueados** hasta que se cierren sus prerrequisitos. Te lo "
                "enseno en el paso siguiente.\n\n"
                "No invento nombres de menus ni de botones de esta version del software: "
                "sigue el manual oficial del fabricante para cada paso."
            ),
            "tools": [],
        },
        # --- 18: los bloqueos, la parte que evita el accidente ----------------
        {
            "texto": (
                "**Por que no puedo darte todavia el detalle de cargar la CPU nueva.**\n\n"
                "El procedimiento declara prerrequisitos por paso, y no son criterio mio: "
                "estan en la fuente. Esto es lo que el expediente dice ahora mismo:\n\n"
                "- **Paso 35 — reemplazo fisico.** Bloqueado: faltan el paso 3 (respaldo), "
                "el 5 (respaldo verificado), el 33 (plan de retorno) y el 34 (ventana de "
                "parada autorizada). Ademas exige **aprobacion humana, maquina detenida y "
                "LOTO**, y esta marcado como **irreversible**.\n"
                "- **Paso 33 — plan de retorno.** Es **bloqueante**: sin el no se avanza.\n"
                "- **Paso 28 — funciones de seguridad.** Exige **especialista en seguridad "
                "funcional**; yo identifico y advierto, no doy instrucciones.\n"
                "- **Paso 41 — provocar fallas controladas.** Exige aprobacion y "
                "especialista presente.\n\n"
                "En tu caso el paso 5 no se puede cerrar: **la contrasena es desconocida**. "
                "El procedimiento no lo esquiva, lo dice: detenerse, escalar, y si el "
                "programa no se recupera, reconstruirlo a partir del levantamiento "
                "funcional. Por eso el paso 6 quedo marcado como el critico.\n\n"
                "Esto es lo que separa una lista de buenas intenciones de una guia: **sabe "
                "cuando decirte que no.**"
            ),
            "tools": [],
        },
        # --- 14: aprobacion humana --------------------------------------------
        {
            "texto": (
                "Antes de entregar el detalle operativo sobre el equipo real, solicito "
                "**aprobacion humana** (Regla 11). Mira el panel: queda registrada en el "
                "expediente con su marca de tiempo.\n\n"
                "Advertencia obligatoria: recuperar el respaldo y cambiar la bateria "
                "**pueden requerir detener la maquina**, y una maniobra mal hecha puede "
                "borrar el programa."
            ),
            "tools": [
                ("solicitar_aprobacion_humana", {
                    "accion_propuesta": f"Conectarse a la CPU {equipo} para subir y verificar "
                                        "el respaldo del programa, y posteriormente sustituir "
                                        "la bateria de respaldo.",
                    "riesgos": "Perdida del programa si la bateria se retira sin respaldo "
                               "verificado; posible parada de la linea; contrasena de la CPU "
                               "desconocida.",
                    "puede_detener_produccion": True,
                }),
            ],
        },
        # --- 15: informe final -------------------------------------------------
        {
            "texto": (
                "Cierro con el **informe tecnico trazable** (estructura de 13 secciones). "
                "Se guarda en la carpeta `casos/` junto al expediente JSON: cada dato "
                "lleva su nivel de confianza y la pregunta que lo sustenta.\n\n"
                "Eso es todo el recorrido. Fijate en lo que acaba de pasar: **el "
                "diagnostico se construyo sobre TU marca y TU generacion**, con la "
                "plataforma destino del mismo fabricante y su fuente oficial — no sobre "
                "un ejemplo prefijado."
            ),
            "tools": [
                ("generar_informe", {
                    "titulo": f"Diagnostico de obsolescencia y plan de migracion — {equipo} (DEMO)",
                    "nivel_confianza_global": "confianza_media",
                    "resumen": f"Riesgo alto; corregir causa raiz, recuperar respaldo y migrar "
                               f"a {destino} por etapas.",
                    "cuerpo_markdown": (
                        f"## 1. Identificacion\nCaso de demostracion. CPU {equipo}.\n"
                        f"Identificacion contra el catalogo de fabricantes: {ctx['fuente_texto']}\n\n"
                        "## 2. Resumen ejecutivo\nControlador obsoleto operando con fallas "
                        "intermitentes, **sin respaldo verificado** del programa y con "
                        "**causa raiz externa no corregida** (bateria, temperatura, tierra).\n\n"
                        f"## 3. Informacion confirmada\nMarca {ctx['marca']}, familia "
                        f"{familia}"
                        + (f", modelo {ctx['modelo']}" if ctx["modelo"] else "")
                        + f". Generacion {ctx['posicion']} de la cronologia del fabricante. "
                        f"Redes {ctx['redes']}. Criticidad alta; parada tolerable 4-12 h.\n\n"
                        "## 4. Informacion no confirmada\nEstado de ciclo de vida declarado "
                        "verbalmente; historial de paros estimado sin registro digital.\n\n"
                        "## 5. Datos faltantes\nRespaldo verificado; contrasena de la CPU; "
                        "proyecto fuente; verificacion oficial del ciclo de vida.\n\n"
                        "## 6. Estado y puntuacion de obsolescencia\nRiesgo alto (ver "
                        "puntuacion ponderada en el expediente, motor de la Seccion 6).\n\n"
                        "## 7. Riesgos\nTecnico: falla de CPU sin respaldo y con contrasena "
                        "desconocida. Productivo: suministro de repuestos de 2 a 8 semanas "
                        "frente a 4-12 h de parada tolerable. Economico: unos 1200 USD por "
                        "hora de parada. Seguridad: revision obligatoria por especialista.\n\n"
                        "## 8. Alternativas\n(1) Correccion de causa raiz — procede y es lo "
                        "primero; (2) reparacion — no revierte la obsolescencia; (3) repuesto "
                        "directo — no cubre el riesgo por plazo de suministro; (4) hardware "
                        f"equivalente — puente viable; (5) migracion a {destino} — procede, "
                        "planificada; (6) reconstruccion — ultimo recurso.\n\n"
                        "## 9. Recomendacion principal\nEn tres tiempos: (1) recuperar y "
                        "verificar el respaldo y solicitar el proyecto fuente; (2) corregir la "
                        "causa raiz y asegurar un repuesto en existencia; (3) migrar a "
                        f"{destino} en el paro anual, con esta maquina como piloto.\n\n"
                        "## 10. Equivalencias preliminares (a verificar)\n"
                        f"{familia} -> {destino} ({ctx['destino_texto']}); "
                        f"{ctx['sw_legado']} -> {ctx['sw_objetivo']}. NO se confirman numeros "
                        "de catalogo: deben verificarse oficialmente.\n\n"
                        "## 11. Plan de respaldo, migracion y retorno\nRespaldo verificado -> "
                        "levantamiento -> arquitectura destino -> mapa de senales -> conversion "
                        "del programa -> BOM preliminar -> plan de retorno.\n\n"
                        "## 12. Plan de pruebas\nFAT en banco con simulacion de E/S; SAT en "
                        "ventana de parada con pruebas de seguridad por especialista.\n\n"
                        "## 13. Nivel de confianza y fuentes\nConfianza media. Fuentes: "
                        "declaracion verbal del tecnico y catalogo de fabricantes verificado "
                        f"({ctx['fuente_texto']}). Pendiente: placa, respaldo y lista de E/S."
                    ),
                }),
            ],
        },
    ]


# --------------------------------------------------------------------------- #
# Ejecucion
# --------------------------------------------------------------------------- #
def total_pasos(ctx: dict | None = None) -> int:
    """Numero de pasos del recorrido (2 fijos + los que dependen del equipo)."""
    return 2 + len(construir_pasos(ctx or construir_contexto("")))


def ejecutar_paso(caso: Caso, indice: int, texto_usuario: str = "", ctx: dict | None = None) -> dict:
    """Ejecuta el paso `indice` sobre el expediente real, adaptado al equipo.

    `texto_usuario` es lo que la persona acaba de escribir: en el paso 1 se usa su
    nombre y en el paso 2 se identifica su equipo contra el catalogo. `ctx` es el
    contexto ya construido, que la app conserva entre pasos.

    Devuelve {"texto", "acciones", "resumen", "fin", "demo", "ctx"}.
    """
    ctx = dict(ctx) if ctx else {}

    if indice == 0:
        paso = paso_inicial()
    elif indice == PASO_NOMBRE:
        ctx["nombre"] = extraer_nombre(texto_usuario)
        paso = paso_nombre(ctx)
    else:
        if indice == PASO_EQUIPO:
            ya_intentado = bool(ctx.get("ident"))
            if ya_intentado and not _es_respuesta_real(texto_usuario):
                # Segunda vuelta y el usuario pulsa Enviar sin corregir: acepta
                # seguir con el equipo sin identificar. Se conserva el ctx anterior.
                pass
            else:
                # Aqui nace la adaptacion: el resto del guion se arma con ESTE equipo.
                nombre = ctx.get("nombre", "tecnico")
                ctx = construir_contexto(texto_usuario)
                ctx["nombre"] = nombre
                if not ctx["catalogado"]:
                    # No se arranca un recorrido completo sobre un equipo que no se
                    # ha podido identificar: primero se ofrece corregirlo.
                    return {
                        "texto": _bloque_identificacion(ctx, cierre=False) + _INVITACION_CORREGIR,
                        "acciones": [],
                        "resumen": caso.resumen(),
                        "fin": False,
                        "demo": True,
                        "repetir": True,
                        "ctx": ctx,
                    }
        if not ctx.get("ident"):
            ctx = {**construir_contexto(texto_usuario), "nombre": ctx.get("nombre", "tecnico")}
        pasos = construir_pasos(ctx)
        i = indice - PASO_EQUIPO
        if i >= len(pasos):
            return {"texto": _TEXTO_FIN, "acciones": [], "resumen": caso.resumen(),
                    "fin": True, "demo": True, "ctx": ctx}
        paso = pasos[i]

    acciones: list[str] = []
    for nombre_tool, entrada in paso["tools"]:
        ejecutar_herramienta(caso, nombre_tool, entrada, aprobador_pendiente)
        acciones.append(nombre_tool)

    texto = paso["texto"]
    if indice > PASO_EQUIPO and _es_respuesta_real(texto_usuario):
        # El usuario escribio algo de verdad y la demo no lo va a leer. Callarselo
        # y seguir con el guion es lo que hace que el recorrido se sienta roto.
        texto = _NOTA_NO_LEIDO + texto

    total = 2 + len(construir_pasos(ctx)) if ctx.get("ident") else None
    return {
        "texto": texto,
        "acciones": acciones,
        "resumen": caso.resumen(),
        "fin": total is not None and indice >= total - 1,
        "demo": True,
        "ctx": ctx,
    }
