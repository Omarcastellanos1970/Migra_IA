"""Herramientas (tools) de MIGRA-IA y su despachador.

Las definiciones son esquemas JSON para la API de Claude. El despachador aplica
cada llamada sobre el expediente (Caso), lo persiste tras cada accion y devuelve
un resultado en texto JSON que el modelo lee en el siguiente turno.
"""

from __future__ import annotations

import json
from datetime import datetime

from .caso import Caso
from .scoring import calcular_riesgo, PESOS
from . import config, conocimiento, cuestionario, fabricantes, procedimiento

NIVELES = ["confirmado", "alta_confianza", "confianza_media", "baja_confianza", "no_determinado"]

# --------------------------------------------------------------------------- #
# Definiciones de herramientas (input_schema)
# --------------------------------------------------------------------------- #
TOOLS = [
    {
        "name": "guardar_respuestas",
        "description": (
            "Registra una o varias respuestas del cuestionario en el expediente. "
            "Usala cada vez que el usuario aporte datos relevantes. Cada respuesta "
            "debe etiquetarse con su nivel de confianza y su fuente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "answers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "description": "Letra de la seccion, ej. 'D'"},
                            "code": {"type": "string", "description": "Codigo de la pregunta, ej. 'D03'"},
                            "question": {"type": "string"},
                            "value": {"type": "string", "description": "Respuesta del usuario"},
                            "confidence_level": {"type": "string", "enum": NIVELES},
                            "source": {"type": "string", "description": "Placa, manual, foto, verbal, etc."},
                        },
                        "required": ["section", "code", "question", "value", "confidence_level"],
                    },
                }
            },
            "required": ["answers"],
        },
    },
    {
        "name": "registrar_activo",
        "description": (
            "Registra un activo del sistema (CPU/PLC, modulo de E/S, HMI, variador, "
            "servo, sensor, actuador, etc.) con sus datos de placa. Devuelve el ID "
            "unico del activo (AST-...). Nunca inventes numeros de catalogo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "cpu | modulo_io | hmi | variador | servo | sensor | actuador | red | otro"},
                "description": {"type": "string"},
                "manufacturer": {"type": "string"},
                "model": {"type": "string"},
                "catalog_reference": {"type": "string"},
                "status": {"type": "string"},
                "confidence_level": {"type": "string", "enum": NIVELES},
                "notes": {"type": "string"},
            },
            "required": ["type", "description"],
        },
    },
    {
        "name": "registrar_evidencia",
        "description": "Registra una evidencia aportada por el usuario (fotografia, manual, plano, respaldo, lista de E/S). Devuelve el ID unico (EVD-...).",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "foto | manual | plano | respaldo | lista_io | otro"},
                "description": {"type": "string"},
                "confidence_level": {"type": "string", "enum": NIVELES},
            },
            "required": ["type", "description"],
        },
    },
    {
        "name": "registrar_dato_faltante",
        "description": "Registra un dato critico ausente que impide o limita una recomendacion final (Seccion 11).",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "impacto": {"type": "string", "description": "Que decision queda bloqueada o degradada sin este dato"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "registrar_bandera_seguridad",
        "description": "Registra una bandera de seguridad, p. ej. cuando la migracion puede afectar funciones de seguridad y se requiere revision de un especialista en seguridad funcional.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "calcular_riesgo_obsolescencia",
        "description": (
            "Calcula la puntuacion de riesgo de obsolescencia (0-100) ponderando los "
            "ocho factores de la Seccion 6. Provee solo los factores para los que tengas "
            "justificacion real; los omitidos no se penalizan. Cada factor requiere un "
            "valor 0-100 (mayor = mas riesgo) y una justificacion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "factors": {
                    "type": "object",
                    "description": "Claves validas: " + ", ".join(PESOS.keys()),
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number"},
                            "justificacion": {"type": "string"},
                        },
                        "required": ["value", "justificacion"],
                    },
                }
            },
            "required": ["factors"],
        },
    },
    {
        "name": "resumen_caso",
        "description": "Devuelve el estado actual del expediente (respuestas, activos, evidencias, datos faltantes, banderas, riesgo). Usala para recordar que informacion ya esta registrada.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "consultar_guia",
        "description": (
            "Consulta la base de referencia interna (Guia MIGRA-IA-GUIA-001) para "
            "conducir el diagnostico de forma estructurada y FUNDAMENTAR Y CITAR cada "
            "recomendacion. Contiene: metodologia de 6 etapas (diagnostico, ingenieria, "
            "construccion, FAT, corte/SAT, cierre), 24 capitulos, rutas de migracion por "
            "fabricante (Siemens, Rockwell, Mitsubishi, Schneider, Omron), una biblioteca "
            "de 20 pruebas, 22 plantillas y anexos de gestion. Devuelve el fragmento "
            "pedido junto con su cita. Consultala antes de proponer alternativas, "
            "equivalencias por fabricante o planes de prueba."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "enum": [
                        "indice", "methodology", "stage", "chapter", "manufacturer",
                        "matriz_fabricantes", "test", "template", "anexo", "case",
                        "principios", "entregables", "guide",
                    ],
                    "description": "Parte de la guia a consultar.",
                },
                "key": {
                    "type": "string",
                    "description": (
                        "Identificador dentro del tema: numero o titulo de capitulo; id o "
                        "numero de etapa; id o dispositivo de prueba; letra o nombre de "
                        "plantilla/anexo; id o titulo de caso; marca o familia de fabricante "
                        "(p. ej. 'Siemens' o 'S7-300'). Omitela para obtener el indice del tema."
                    ),
                },
            },
            "required": ["tema"],
        },
    },
    {
        "name": "identificar_cpu",
        "description": (
            "PRIMERA HERRAMIENTA a usar en cuanto el usuario mencione un equipo. "
            "Resuelve texto libre de placa ('un Allen Bradley SLC 5/04', 'CJ1M-CPU13', "
            "'schneider m580') contra el catalogo de 30 fabricantes, 130 generaciones y "
            "469 modelos reales de CPU. Devuelve marca, familia/generacion, posicion en "
            "la cronologia del fabricante, modelos documentados de esa generacion, la "
            "generacion actual del MISMO fabricante y las fuentes oficiales citables. "
            "Ancla el caso: a partir de su resultado, TODA respuesta debe referirse a ese "
            "equipo. Si devuelve 'no_catalogado', dilo y pide la placa; no aproximes a la "
            "marca mas parecida."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": (
                        "Lo que dijo el usuario sobre el equipo, tal cual: marca, familia "
                        "y/o modelo. Puede ser una frase completa."
                    ),
                }
            },
            "required": ["text"],
        },
    },
    {
        "name": "consultar_catalogo",
        "description": (
            "Consulta el catalogo de fabricantes y CPU: la cronologia completa de una "
            "marca (de la generacion mas antigua a la actual) o el detalle de una de sus "
            "generaciones, con modelos documentados y fuentes oficiales. Usala para situar "
            "el equipo en su ciclo de vida, para saber que generacion del MISMO fabricante "
            "es la actual y para citar la fuente. No inventes modelos que no devuelva."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand": {
                    "type": "string",
                    "description": "Marca del catalogo, p. ej. 'Siemens', 'OMRON', 'Fuji Electric'.",
                },
                "family": {
                    "type": "string",
                    "description": "Opcional: familia o generacion concreta, p. ej. 'S7-300', 'MELSEC-Q', 'PFC200'.",
                },
            },
            "required": ["brand"],
        },
    },
    {
        "name": "consultar_cuestionario",
        "description": (
            "Consulta el cuestionario maestro adaptativo: el detalle exacto de las "
            "preguntas (texto, opciones y regla adaptativa) y, sobre todo, el mapa de "
            "decision que enlaza cada respuesta con el factor de riesgo que alimenta y "
            "con los criterios de cada alternativa (correccion de causa raiz, reparacion, "
            "repuesto directo, hardware equivalente, migracion, reconstruccion, operacion "
            "temporal). Consultala ANTES de abrir una seccion nueva del diagnostico, para "
            "preguntar con las opciones reales y aplicar su regla adaptativa, y ANTES de "
            "puntuar un factor o proponer una alternativa, para justificarla con criterio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "enum": [
                        "indice", "section", "question", "decision_map",
                        "factor", "criteria", "prioridades", "buscar",
                    ],
                    "description": "Parte del cuestionario a consultar.",
                },
                "key": {
                    "type": "string",
                    "description": (
                        "Identificador dentro del tema: letra o titulo de seccion (p. ej. "
                        "'M' o 'ciclo de vida'); codigo de pregunta (p. ej. 'M06'); clave del "
                        "factor de riesgo (" + ", ".join(PESOS.keys()) + "); nombre de la "
                        "alternativa (p. ej. 'migracion'); o texto libre para 'buscar'. "
                        "Omitela para obtener el indice del tema."
                    ),
                },
            },
            "required": ["tema"],
        },
    },
    {
        "name": "consultar_procedimiento",
        "description": (
            "Consulta el procedimiento de migracion de 50 pasos (MIGRA-IA-PROC-050): el "
            "paso a paso que se sigue UNA VEZ QUE SE DECIDE cambiar la CPU. Cada paso trae "
            "su criterio de salida, la evidencia que debe quedar, quien lo ejecuta, sus "
            "prerrequisitos y lo que exige antes de tocar la maquina. Usa 'triggers' "
            "para saber si el caso ya justifica abrir el modo guia; 'opciones_destino' en "
            "el paso 13 para presentar las CPU candidatas del mismo fabricante y las "
            "plataformas de marcas alternativas; 'ruta_fabricante' cuando el programa de "
            "origen SI es accesible (contrasenas conocidas y respaldo que abre y compila) "
            "y hay que migrar igual por obsolescencia o falta de repuestos: devuelve la "
            "secuencia concreta de herramientas de esa marca, que especializa los pasos "
            "21 a 23; 'ruta_cambio_marca' cuando el destino elegido es de OTRA marca y "
            "el programa de origen SI es accesible: devuelve el metodo de porte, que "
            "especializa los pasos 11, 12, 18, 21 y 32; 'siguiente' para saber que paso "
            "toca; 'bloqueos' antes de proponer "
            "cualquier intervencion fisica. Cita siempre el paso: 'Procedimiento "
            "MIGRA-IA-PROC-050, paso N'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "enum": [
                        "step", "phase", "triggers", "opciones_destino",
                        "ruta_fabricante", "ruta_cambio_marca", "status", "siguiente",
                        "bloqueos", "huecos", "document",
                    ],
                    "description": "Parte del procedimiento a consultar.",
                },
                "key": {
                    "type": "string",
                    "description": (
                        "Numero de paso (1 a 50) para el tema 'step'; id de fase "
                        "(levantamiento, seleccion_e_ingenieria, conversion, fat, "
                        "corte_y_puesta_en_marcha, cierre) o numero de paso para 'phase'; "
                        "nombre de la marca para 'ruta_fabricante' (si se omite, se toma "
                        "la marca del equipo ya identificado en el expediente). "
                        "Omitela en los demas temas."
                    ),
                },
            },
            "required": ["tema"],
        },
    },
    {
        "name": "iniciar_guia_migracion",
        "description": (
            "Abre el modo guia del procedimiento de 50 pasos. Llamala en el momento en que "
            "se decide cambiar la CPU: por obsolescencia, por contrasena desconocida, "
            "porque el programa anterior no se puede copiar ni abrir, o porque el usuario "
            "lo decide. A partir de esta llamada el agente deja de diagnosticar y acompana "
            "paso a paso. Declara `sin_respaldo` cuando no exista programa de origen "
            "recuperable: eso cambia el contenido de varios pasos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {
                    "type": "string",
                    "enum": ["cpu_obsoleta", "contrasena_desconocida",
                             "sin_acceso_al_programa", "decision_del_usuario"],
                },
                "motivo": {"type": "string", "description": "Por que se abre, en una linea."},
                "decidido_por": {
                    "type": "string",
                    "enum": ["usuario", "sugerencia_del_agente_aceptada"],
                    "description": "Quien tomo la decision de cambiar la CPU.",
                },
                "sin_respaldo": {
                    "type": "boolean",
                    "description": "True si no hay programa de origen recuperable ni verificable.",
                },
            },
            "required": ["trigger", "motivo"],
        },
    },
    {
        "name": "fijar_cpu_destino",
        "description": (
            "Registra la CPU de reemplazo que ELIGIO EL USUARIO en el paso 13, con su "
            "justificacion y su fuente. Nunca la elijas tu: presenta antes las opciones con "
            "`consultar_procedimiento` (tema 'opciones_destino') y espera la decision. Si la "
            "marca elegida es distinta a la de origen, el procedimiento activa solo la "
            "variante de cambio de marca (los pasos 21 y 22 dejan de aplicar)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "family": {"type": "string", "description": "Familia o plataforma destino."},
                "model": {
                    "type": "string",
                    "description": "Modelo exacto SOLO si el catalogo lo documenta o el "
                                   "usuario lo aporta. No completes codigos.",
                },
                "justificacion": {"type": "string"},
                "source": {"type": "string", "description": "URL o cita de la fuente oficial."},
            },
            "required": ["brand", "family", "justificacion"],
        },
    },
    {
        "name": "marcar_paso_migracion",
        "description": (
            "Registra el estado de un paso del procedimiento en el expediente, con la "
            "evidencia que lo sustenta. Marca 'completado' solo cuando se cumple el criterio "
            "de salida del paso; 'no_aplica' cuando una variante lo desactiva; 'bloqueado' "
            "cuando falta un prerrequisito."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "step": {"type": "string",
                         "description": "Clave del paso: '1' a '50' del documento, o "
                                        "'P1' a 'P7' de la extension de construccion "
                                        "del programa."},
                "status": {
                    "type": "string",
                    "enum": ["pendiente", "en_curso", "completado", "no_aplica", "bloqueado"],
                },
                "note": {"type": "string"},
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Evidencia aportada por el usuario para cerrar el paso.",
                },
            },
            "required": ["step", "status"],
        },
    },
    {
        "name": "solicitar_aprobacion_humana",
        "description": (
            "Solicita aprobacion explicita del personal autorizado ANTES de entregar "
            "instrucciones de intervencion sobre el equipo real (Regla 11). Presenta la "
            "accion propuesta y sus riesgos; el operador aprueba o rechaza en consola."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "accion_propuesta": {"type": "string"},
                "risks": {"type": "string"},
                "puede_detener_produccion": {"type": "boolean"},
            },
            "required": ["accion_propuesta", "risks"],
        },
    },
    {
        "name": "generar_informe",
        "description": (
            "Genera y guarda el informe tecnico trazable en formato Markdown siguiendo "
            "la estructura de la Seccion 9. Devuelve la ruta del archivo. Incluye el "
            "cuerpo completo del informe ya redactado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "cuerpo_markdown": {"type": "string", "description": "Informe completo en Markdown, con las 13 secciones de la estructura estandar."},
                "nivel_confianza_global": {"type": "string", "enum": NIVELES},
                "resumen": {"type": "string", "description": "Resumen de una linea del informe."},
            },
            "required": ["title", "cuerpo_markdown", "nivel_confianza_global"],
        },
    },
]


# --------------------------------------------------------------------------- #
# Despachador
# --------------------------------------------------------------------------- #
def _ok(**kwargs) -> str:
    return json.dumps({"status": "ok", **kwargs}, ensure_ascii=False)


def ejecutar_herramienta(caso: Caso, nombre: str, entrada: dict, aprobador=None) -> str:
    """Ejecuta una herramienta sobre el expediente y persiste el resultado.

    `aprobador` es un callable opcional (caso, entrada) -> bool usado por la
    herramienta de aprobacion humana. Si es None, se usa el aprobador de consola.
    Devuelve una cadena JSON que se envia al modelo como tool_result.
    """
    try:
        if nombre == "guardar_respuestas":
            codigos = []
            for r in entrada.get("answers", []):
                caso.guardar_respuesta(
                    seccion=r.get("section", ""),
                    codigo=r["code"],
                    pregunta=r.get("question", ""),
                    valor=r.get("value", ""),
                    nivel_confianza=r.get("confidence_level", "confianza_media"),
                    fuente=r.get("source", ""),
                )
                codigos.append(r["code"])
            resultado = _ok(registradas=codigos)

        elif nombre == "registrar_activo":
            aid = caso.registrar_activo(entrada)
            # Anclaje automatico: si el activo es la CPU/PLC, se identifica contra el
            # catalogo y la ficha viaja de vuelta al modelo en el mismo tool_result.
            # Asi la adaptacion a la marca no depende de que el modelo decida consultar.
            extra = {}
            if entrada.get("type", "").lower() in ("cpu", "plc", "controlador", "pac"):
                texto = " ".join(
                    str(entrada.get(c, ""))
                    for c in ("manufacturer", "model", "catalog_reference", "description")
                ).strip()
                ident = fabricantes.identificar(texto)
                caso.fijar_equipo(ident)
                extra = {
                    "identificacion_catalogo": ident,
                    "anclaje": fabricantes.anclaje(ident),
                }
            resultado = _ok(id_activo=aid, **extra)

        elif nombre == "identificar_cpu":
            ident = fabricantes.identificar(entrada.get("text", ""))
            caso.fijar_equipo(ident)
            resultado = json.dumps(
                {"status": "ok", "identificacion": ident,
                 "anclaje": fabricantes.anclaje(ident)},
                ensure_ascii=False,
            )

        elif nombre == "consultar_catalogo":
            res = fabricantes.ficha(entrada.get("brand", ""), entrada.get("family"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "registrar_evidencia":
            eid = caso.registrar_evidencia(entrada)
            resultado = _ok(id_evidencia=eid)

        elif nombre == "registrar_dato_faltante":
            caso.registrar_dato_faltante(entrada["description"], entrada.get("impacto", ""))
            resultado = _ok(mensaje="dato faltante registrado")

        elif nombre == "registrar_bandera_seguridad":
            caso.registrar_bandera(entrada["text"])
            resultado = _ok(mensaje="bandera registrada")

        elif nombre == "calcular_riesgo_obsolescencia":
            res = calcular_riesgo(entrada.get("factors", {}))
            caso.guardar_riesgo(res.to_dict())
            resultado = _ok(**res.to_dict())

        elif nombre == "resumen_caso":
            resultado = json.dumps(caso.resumen(), ensure_ascii=False)

        elif nombre == "consultar_guia":
            res = conocimiento.consultar(entrada.get("tema", ""), entrada.get("key"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "consultar_cuestionario":
            res = cuestionario.consultar(entrada.get("tema", ""), entrada.get("key"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "consultar_procedimiento":
            res = procedimiento.consultar(
                entrada.get("tema", ""), entrada.get("key"), caso=caso
            )
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "iniciar_guia_migracion":
            caso.iniciar_migracion(
                disparador=entrada["trigger"],
                motivo=entrada.get("motivo", ""),
                decidido_por=entrada.get("decidido_por", "usuario"),
            )
            if entrada.get("sin_respaldo"):
                caso.declarar_sin_respaldo(True)
            # El primer paso viaja de vuelta en el mismo tool_result: el modo guia
            # arranca sin depender de que el modelo decida hacer otra consulta.
            sig = procedimiento.siguiente(caso)
            resultado = json.dumps(
                {"status": "ok",
                 "migracion": caso.migracion,
                 "avance": procedimiento.estado(caso),
                 "primer_paso": sig,
                 "texto_primer_paso": procedimiento.texto_paso(
                     sig["key"], procedimiento.contexto(caso)) if sig else ""},
                ensure_ascii=False,
            )

        elif nombre == "fijar_cpu_destino":
            destino = caso.fijar_destino(
                marca=entrada["brand"],
                familia=entrada["family"],
                modelo=entrada.get("model", ""),
                justificacion=entrada.get("justificacion", ""),
                fuente=entrada.get("source", ""),
            )
            cambio = caso.migracion.get("cambio_marca", False)
            con_codigo = procedimiento.contexto(caso).get("con_codigo_fuente", False)
            if cambio and con_codigo:
                consecuencia = (
                    "Cambio de marca CON el programa de origen accesible: los pasos 21 y 22 "
                    "dejan de aplicar, pero el trabajo NO empieza de cero. Pide el tema "
                    "'ruta_cambio_marca': el programa original es la especificacion y la "
                    "ruta especializa los pasos 11, 12, 18, 21 y 32. Revisa tambien las "
                    "variantes de los pasos 14, 19, 23, 24, 25 y 48.")
            elif cambio:
                consecuencia = (
                    "Cambio de marca SIN acceso al programa de origen: los pasos 21 y 22 "
                    "dejan de aplicar y el sistema se reconstruye por la extension P1-P7, "
                    "como desarrollo nuevo. Revisa las variantes de los pasos 14, 19 y 48.")
            else:
                consecuencia = (
                    "Misma marca: el procedimiento sigue completo, con herramienta oficial "
                    "de conversion en los pasos 21 y 22.")
            resultado = json.dumps(
                {"status": "ok",
                 "destino": destino,
                 "cambio_marca": cambio,
                 "consecuencia": consecuencia,
                 "avance": procedimiento.estado(caso)},
                ensure_ascii=False,
            )

        elif nombre == "marcar_paso_migracion":
            n = str(entrada["step"]).strip()
            ctx = procedimiento.contexto(caso)
            p = procedimiento.paso(n, ctx)
            if p is None:
                resultado = json.dumps(
                    {"status": "error",
                     "mensaje": f"El paso {n} no existe. Validos: 1 a 50, y P1 a P7.",
                     "validos": procedimiento.orden()},
                    ensure_ascii=False,
                )
            else:
                pendientes = [
                    r for r in p["prerequisites"]
                    if (caso.migracion or {}).get("steps", {}).get(str(r), {}).get("status")
                    not in ("completado", "no_aplica")
                ]
                if entrada["status"] == "completado" and pendientes:
                    # No se cierra un paso saltandose sus prerrequisitos: la
                    # dependencia es del procedimiento, no criterio del modelo.
                    resultado = json.dumps(
                        {"status": "rechazado",
                         "mensaje": f"El paso {n} no puede cerrarse: faltan los pasos "
                                    f"{pendientes}. Cierralos o marcalos 'no_aplica' antes.",
                         "prerrequisitos_pendientes": pendientes},
                        ensure_ascii=False,
                    )
                else:
                    caso.marcar_paso(n, entrada["status"], entrada.get("note", ""),
                                     entrada.get("evidence"))
                    sig = procedimiento.siguiente(caso)
                    resultado = json.dumps(
                        {"status": "ok",
                         "avance": procedimiento.estado(caso),
                         "siguiente_paso": sig["label"] if sig else None,
                         "texto_siguiente_paso": procedimiento.texto_paso(
                             sig["key"], ctx) if sig else "Todos los pasos estan cerrados."},
                        ensure_ascii=False,
                    )

        elif nombre == "solicitar_aprobacion_humana":
            aprob = aprobador or _aprobacion_consola
            aprobado = bool(aprob(caso, entrada))
            caso.auditoria.append(
                {
                    "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "accion": "human_approval",
                    "detail": {"accion": entrada.get("accion_propuesta"), "aprobado": aprobado},
                }
            )
            resultado = _ok(aprobado=aprobado)

        elif nombre == "generar_informe":
            resultado = _generar_informe(caso, entrada)

        else:
            resultado = json.dumps(
                {"status": "error", "mensaje": f"herramienta desconocida: {nombre}"},
                ensure_ascii=False,
            )
    except Exception as exc:  # noqa: BLE001 - devolver el error al modelo, no romper el bucle
        resultado = json.dumps(
            {"status": "error", "mensaje": f"{type(exc).__name__}: {exc}"},
            ensure_ascii=False,
        )

    caso.guardar()
    return resultado


def _aprobacion_consola(caso: Caso, entrada: dict) -> bool:
    """Aprobador por defecto: pide confirmacion explicita en consola (CLI)."""
    print("\n" + "=" * 68)
    print("  SOLICITUD DE APROBACION HUMANA (personal autorizado)")
    print("=" * 68)
    print(f"Accion propuesta: {entrada.get('accion_propuesta', '')}")
    print(f"Riesgos:          {entrada.get('risks', '')}")
    if entrada.get("puede_detener_produccion"):
        print("ADVERTENCIA: esta accion PODRIA DETENER LA PRODUCCION.")
    respuesta = input("Aprueba esta accion? [s/N]: ").strip().lower()
    return respuesta in ("s", "si", "sí", "y", "yes")


def _generar_informe(caso: Caso, entrada: dict) -> str:
    """Escribe el informe tecnico en Markdown y lo registra en el expediente."""
    iid_previo = f"INF-{datetime.now().year}-{len(caso.informes) + 1:06d}"
    nombre_archivo = f"{caso.case_id}_{iid_previo}.md"
    ruta = config.DIR_CASOS / nombre_archivo

    encabezado = (
        f"# {entrada.get('title', 'Informe tecnico MIGRA-IA')}\n\n"
        f"- Caso: {caso.case_id}\n"
        f"- Agente: {config.AGENTE_NOMBRE} v{config.AGENTE_VERSION}\n"
        f"- Fecha: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
        f"- Nivel de confianza global: {entrada.get('nivel_confianza_global', 'no_determinado')}\n"
        f"- Aprobacion humana: PENDIENTE (este informe es una asistencia tecnica; "
        f"debe ser verificado por personal autorizado antes de intervenir).\n\n"
        "---\n\n"
    )
    ruta.write_text(encabezado + entrada.get("cuerpo_markdown", ""), encoding="utf-8")
    iid = caso.registrar_informe(str(ruta), entrada.get("resumen", ""))
    return _ok(id_informe=iid, ruta=str(ruta))
