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
from . import fabricantes

# Pasos en los que la demo lee lo que escribe el usuario en vez de ignorarlo.
PASO_NOMBRE = 1
PASO_EQUIPO = 2

_TEXTO_FIN = (
    "La demostracion ya termino. Pulsa **Modo demo** para reiniciarla con otro "
    "equipo, o configura tu `ANTHROPIC_API_KEY` y abre un **Caso real (API)** para "
    "un diagnostico conversacional completo sobre tu propia maquina."
)

_SIN_RUTA = "(a confirmar en la documentacion oficial del fabricante)"


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
        "sw_legado": ruta.get("software_legado") or f"el software original de {marca} {_SIN_RUTA}",
        "sw_objetivo": ruta.get("software_objetivo") or f"el entorno actual de {marca} {_SIN_RUTA}",
        "redes": ruta.get("redes_heredadas") or "las redes del equipo, a levantar en sitio",
        "riesgo_tipico": ruta.get("riesgo_tipico")
        or "conversion del programa, direccionamiento y comunicaciones, a evaluar con la documentacion oficial",
        "cita_guia": ruta.get("cita", "Guia MIGRA-IA-GUIA-001"),
        "fuente_texto": fuente_texto or "sin fuente en el catalogo para este equipo",
        "nota_actual": ident.get("nota_generacion_actual", ""),
        "nombre": "tecnico",
    }


def _bloque_identificacion(ctx: dict) -> str:
    """Lo que el agente 've' del equipo: se muestra tal cual para que sea auditable."""
    if not ctx["catalogado"]:
        return (
            f"**No encuentro '{ctx['consulta']}' en el catalogo verificado de 30 "
            "fabricantes.** Y eso es exactamente lo que debo decirte: no voy a "
            "asimilarlo a la marca mas parecida ni a trasladarle la ruta de otro "
            "fabricante. Necesito una **foto de la placa** con el numero de parte "
            "exacto.\n\nSigo el recorrido con la metodologia generica de 6 etapas, "
            "pero todo lo que diga sobre hardware queda como **preliminar y no "
            "verificado**."
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
            "**Esta demostracion SI lee tu equipo.** Es un recorrido guiado de 16 "
            "pasos con respuestas preparadas, pero la marca, la familia, el modelo, "
            "el software, las redes y la plataforma destino salen del **catalogo "
            "verificado de 30 fabricantes, 130 generaciones y 469 modelos reales de "
            "CPU**, segun lo que tu escribas. Las herramientas y el calculo de riesgo "
            "son los reales: el expediente del panel derecho se llena de verdad.\n\n"
            "(Para un dialogo completo, adaptado a cada una de tus respuestas y no "
            "solo al equipo, usa **Caso real (API)** con tu `ANTHROPIC_API_KEY`.)\n\n"
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
                "Existe copia del programa del PLC? Se conoce la contrasena, y estan "
                f"disponibles **{ctx['sw_legado']}** y el cable de programacion para "
                "intentar leerlo?"
            ),
            "tools": [
                ("registrar_activo", {
                    "tipo": "cpu",
                    "descripcion": f"CPU {equipo}",
                    "fabricante": marca,
                    "modelo": ctx["modelo"] or familia,
                    "estado": "Operando con fallas",
                    "nivel_confianza": "confianza_media" if ctx["catalogado"] else "no_determinado",
                    "notas": f"Reportado por el usuario: '{ctx['consulta']}'. "
                             "Falla intermitente.",
                }),
                ("guardar_respuestas", {"respuestas": [
                    {"seccion": "D", "codigo": "D01", "pregunta": "Fabricante del PLC",
                     "valor": marca, "nivel_confianza": "confianza_media", "fuente": "verbal"},
                    {"seccion": "D", "codigo": "D02", "pregunta": "Familia del PLC",
                     "valor": familia, "nivel_confianza": "confianza_media", "fuente": "verbal"},
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
                f"esta generacion lo habitual es encontrar **{ctx['redes']}**. Es tu "
                "caso? Que tan critica es la maquina para la produccion?"
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
                "Ultima parte antes de evaluar: la migracion afectaria funciones de "
                "seguridad (paros de emergencia, cortinas, PLC de seguridad)? Y cual es "
                "tu objetivo principal?"
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
                f"Que dice {marca} hoy sobre la familia **{familia}**: sigue a la venta o "
                "esta descontinuada? Consiguen repuestos, en cuanto tiempo llegan, y "
                "**cuanto tiempo puede estar parada esta maquina**?"
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
                "Ahora el historial. Cuantos paros no programados han tenido en el "
                "ultimo ano, van a mas o a menos, y que se ha danado? Una pregunta rara "
                "pero importante: **la maquina pierde la hora o el programa al quitarle "
                "la energia**?"
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
                    "descripcion": f"Estado de ciclo de vida de la familia {familia} "
                                   f"({marca}) sin verificar en fuente oficial",
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
                f"el {marca} sin corregir la temperatura y la tierra, el equipo nuevo "
                "volveria a fallar. Lo registro como causa raiz probable.\n\n"
                "Aviso importante: **cambiar esa bateria con la CPU sin energia puede "
                "borrar el programa**, y aqui no hay respaldo verificado. Primero el "
                "respaldo, despues la bateria. Sin excepcion.\n\n"
                "Ultimo bloque: podrian abrir el programa hoy mismo? Que PC, que "
                "software y que licencia tienen?"
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
                        f"M01: familia {familia} declarada descontinuada, aun con soporte y "
                        "repuestos. Pendiente de verificar en fuente oficial del fabricante."},
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
        # --- 12: procedimiento por etapas -------------------------------------
        {
            "texto": (
                f"**Procedimiento de migracion por etapas** ({familia} → {destino}):\n\n"
                "1. **Respaldo y aseguramiento** — recuperar y verificar el programa, HMI "
                "y parametros de drives; guardar copia con checksum.\n"
                "2. **Levantamiento** — inventario completo de E/S, redes, direcciones y "
                "funciones especiales (PID, conteo, posicionamiento).\n"
                f"3. **Arquitectura destino** — seleccionar CPU y periferia {destino}, "
                f"definir redes partiendo de {ctx['redes']}.\n"
                "4. **Mapa de senales** — tabla de conversion de direccionamiento "
                f"{familia} → {destino} (entradas, salidas, marcas, datos).\n"
                f"5. **Conversion del programa** — migrar con {ctx['sw_objetivo']}, revisar "
                "bloques, resolver instrucciones no equivalentes, conservar simbolos y "
                f"comentarios. Vigilar: {ctx['riesgo_tipico']}\n"
                "6. **Lista de materiales (BOM) preliminar** — hardware, licencias y "
                "accesorios (a cotizar con referencias verificadas).\n"
                "7. **Pruebas FAT** — en banco, con simulacion de E/S, antes de tocar la "
                "planta.\n"
                "8. **Puesta en marcha (SAT)** — ventana de parada planificada, pruebas de "
                "seguridad con especialista, verificacion de la secuencia.\n"
                "9. **Plan de retorno** — dejar la CPU original y el respaldo listos para "
                "revertir si el arranque falla.\n\n"
                "Cada etapa que toque seguridad requiere validacion del especialista "
                "(bandera activa)."
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
                f"**B) Cargar el programa en la CPU nueva ({destino}):** solo con respaldo "
                "verificado, aprobacion y maquina detenida y bloqueada (LOTO). Se detalla "
                "tras la aprobacion.\n\n"
                "No invento nombres de menus ni de botones de esta version del software: "
                "sigue el manual oficial del fabricante para cada paso."
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
            # Aqui nace la adaptacion: el resto del guion se arma con ESTE equipo.
            nombre = ctx.get("nombre", "tecnico")
            ctx = construir_contexto(texto_usuario)
            ctx["nombre"] = nombre
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

    total = 2 + len(construir_pasos(ctx)) if ctx.get("ident") else None
    return {
        "texto": paso["texto"],
        "acciones": acciones,
        "resumen": caso.resumen(),
        "fin": total is not None and indice >= total - 1,
        "demo": True,
        "ctx": ctx,
    }
