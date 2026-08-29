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
                "respuestas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "seccion": {"type": "string", "description": "Letra de la seccion, ej. 'D'"},
                            "codigo": {"type": "string", "description": "Codigo de la pregunta, ej. 'D03'"},
                            "pregunta": {"type": "string"},
                            "valor": {"type": "string", "description": "Respuesta del usuario"},
                            "nivel_confianza": {"type": "string", "enum": NIVELES},
                            "fuente": {"type": "string", "description": "Placa, manual, foto, verbal, etc."},
                        },
                        "required": ["seccion", "codigo", "pregunta", "valor", "nivel_confianza"],
                    },
                }
            },
            "required": ["respuestas"],
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
                "tipo": {"type": "string", "description": "cpu | modulo_io | hmi | variador | servo | sensor | actuador | red | otro"},
                "descripcion": {"type": "string"},
                "fabricante": {"type": "string"},
                "modelo": {"type": "string"},
                "referencia_catalogo": {"type": "string"},
                "estado": {"type": "string"},
                "nivel_confianza": {"type": "string", "enum": NIVELES},
                "notas": {"type": "string"},
            },
            "required": ["tipo", "descripcion"],
        },
    },
    {
        "name": "registrar_evidencia",
        "description": "Registra una evidencia aportada por el usuario (fotografia, manual, plano, respaldo, lista de E/S). Devuelve el ID unico (EVD-...).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "description": "foto | manual | plano | respaldo | lista_io | otro"},
                "descripcion": {"type": "string"},
                "nivel_confianza": {"type": "string", "enum": NIVELES},
            },
            "required": ["tipo", "descripcion"],
        },
    },
    {
        "name": "registrar_dato_faltante",
        "description": "Registra un dato critico ausente que impide o limita una recomendacion final (Seccion 11).",
        "input_schema": {
            "type": "object",
            "properties": {
                "descripcion": {"type": "string"},
                "impacto": {"type": "string", "description": "Que decision queda bloqueada o degradada sin este dato"},
            },
            "required": ["descripcion"],
        },
    },
    {
        "name": "registrar_bandera_seguridad",
        "description": "Registra una bandera de seguridad, p. ej. cuando la migracion puede afectar funciones de seguridad y se requiere revision de un especialista en seguridad funcional.",
        "input_schema": {
            "type": "object",
            "properties": {"texto": {"type": "string"}},
            "required": ["texto"],
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
                "factores": {
                    "type": "object",
                    "description": "Claves validas: " + ", ".join(PESOS.keys()),
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "valor": {"type": "number"},
                            "justificacion": {"type": "string"},
                        },
                        "required": ["valor", "justificacion"],
                    },
                }
            },
            "required": ["factores"],
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
                        "indice", "metodologia", "etapa", "capitulo", "fabricante",
                        "matriz_fabricantes", "prueba", "plantilla", "anexo", "caso",
                        "principios", "entregables", "guia",
                    ],
                    "description": "Parte de la guia a consultar.",
                },
                "clave": {
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
                "texto": {
                    "type": "string",
                    "description": (
                        "Lo que dijo el usuario sobre el equipo, tal cual: marca, familia "
                        "y/o modelo. Puede ser una frase completa."
                    ),
                }
            },
            "required": ["texto"],
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
                "marca": {
                    "type": "string",
                    "description": "Marca del catalogo, p. ej. 'Siemens', 'OMRON', 'Fuji Electric'.",
                },
                "familia": {
                    "type": "string",
                    "description": "Opcional: familia o generacion concreta, p. ej. 'S7-300', 'MELSEC-Q', 'PFC200'.",
                },
            },
            "required": ["marca"],
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
                        "indice", "seccion", "pregunta", "mapa_decision",
                        "factor", "criterios", "prioridades", "buscar",
                    ],
                    "description": "Parte del cuestionario a consultar.",
                },
                "clave": {
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
            "prerrequisitos y lo que exige antes de tocar la maquina. Usa 'disparadores' "
            "para saber si el caso ya justifica abrir el modo guia; 'opciones_destino' en "
            "el paso 13 para presentar las CPU candidatas del mismo fabricante y las "
            "plataformas de marcas alternativas; 'siguiente' para saber que paso toca; "
            "'bloqueos' antes de proponer cualquier intervencion fisica. Cita siempre el "
            "paso: 'Procedimiento MIGRA-IA-PROC-050, paso N'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "enum": [
                        "paso", "fase", "disparadores", "opciones_destino",
                        "estado", "siguiente", "bloqueos", "huecos", "documento",
                    ],
                    "description": "Parte del procedimiento a consultar.",
                },
                "clave": {
                    "type": "string",
                    "description": (
                        "Numero de paso (1 a 50) para el tema 'paso'; id de fase "
                        "(levantamiento, seleccion_e_ingenieria, conversion, fat, "
                        "corte_y_puesta_en_marcha, cierre) o numero de paso para 'fase'. "
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
                "disparador": {
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
            "required": ["disparador", "motivo"],
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
                "marca": {"type": "string"},
                "familia": {"type": "string", "description": "Familia o plataforma destino."},
                "modelo": {
                    "type": "string",
                    "description": "Modelo exacto SOLO si el catalogo lo documenta o el "
                                   "usuario lo aporta. No completes codigos.",
                },
                "justificacion": {"type": "string"},
                "fuente": {"type": "string", "description": "URL o cita de la fuente oficial."},
            },
            "required": ["marca", "familia", "justificacion"],
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
                "paso": {"type": "string",
                         "description": "Clave del paso: '1' a '50' del documento, o "
                                        "'P1' a 'P7' de la extension de construccion "
                                        "del programa."},
                "estado": {
                    "type": "string",
                    "enum": ["pendiente", "en_curso", "completado", "no_aplica", "bloqueado"],
                },
                "nota": {"type": "string"},
                "evidencia": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Evidencia aportada por el usuario para cerrar el paso.",
                },
            },
            "required": ["paso", "estado"],
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
                "riesgos": {"type": "string"},
                "puede_detener_produccion": {"type": "boolean"},
            },
            "required": ["accion_propuesta", "riesgos"],
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
                "titulo": {"type": "string"},
                "cuerpo_markdown": {"type": "string", "description": "Informe completo en Markdown, con las 13 secciones de la estructura estandar."},
                "nivel_confianza_global": {"type": "string", "enum": NIVELES},
                "resumen": {"type": "string", "description": "Resumen de una linea del informe."},
            },
            "required": ["titulo", "cuerpo_markdown", "nivel_confianza_global"],
        },
    },
]


# --------------------------------------------------------------------------- #
# Despachador
# --------------------------------------------------------------------------- #
def _ok(**kwargs) -> str:
    return json.dumps({"estado": "ok", **kwargs}, ensure_ascii=False)


def ejecutar_herramienta(caso: Caso, nombre: str, entrada: dict, aprobador=None) -> str:
    """Ejecuta una herramienta sobre el expediente y persiste el resultado.

    `aprobador` es un callable opcional (caso, entrada) -> bool usado por la
    herramienta de aprobacion humana. Si es None, se usa el aprobador de consola.
    Devuelve una cadena JSON que se envia al modelo como tool_result.
    """
    try:
        if nombre == "guardar_respuestas":
            codigos = []
            for r in entrada.get("respuestas", []):
                caso.guardar_respuesta(
                    seccion=r.get("seccion", ""),
                    codigo=r["codigo"],
                    pregunta=r.get("pregunta", ""),
                    valor=r.get("valor", ""),
                    nivel_confianza=r.get("nivel_confianza", "confianza_media"),
                    fuente=r.get("fuente", ""),
                )
                codigos.append(r["codigo"])
            resultado = _ok(registradas=codigos)

        elif nombre == "registrar_activo":
            aid = caso.registrar_activo(entrada)
            # Anclaje automatico: si el activo es la CPU/PLC, se identifica contra el
            # catalogo y la ficha viaja de vuelta al modelo en el mismo tool_result.
            # Asi la adaptacion a la marca no depende de que el modelo decida consultar.
            extra = {}
            if entrada.get("tipo", "").lower() in ("cpu", "plc", "controlador", "pac"):
                texto = " ".join(
                    str(entrada.get(c, ""))
                    for c in ("fabricante", "modelo", "referencia_catalogo", "descripcion")
                ).strip()
                ident = fabricantes.identificar(texto)
                caso.fijar_equipo(ident)
                extra = {
                    "identificacion_catalogo": ident,
                    "anclaje": fabricantes.anclaje(ident),
                }
            resultado = _ok(id_activo=aid, **extra)

        elif nombre == "identificar_cpu":
            ident = fabricantes.identificar(entrada.get("texto", ""))
            caso.fijar_equipo(ident)
            resultado = json.dumps(
                {"estado": "ok", "identificacion": ident,
                 "anclaje": fabricantes.anclaje(ident)},
                ensure_ascii=False,
            )

        elif nombre == "consultar_catalogo":
            res = fabricantes.ficha(entrada.get("marca", ""), entrada.get("familia"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "registrar_evidencia":
            eid = caso.registrar_evidencia(entrada)
            resultado = _ok(id_evidencia=eid)

        elif nombre == "registrar_dato_faltante":
            caso.registrar_dato_faltante(entrada["descripcion"], entrada.get("impacto", ""))
            resultado = _ok(mensaje="dato faltante registrado")

        elif nombre == "registrar_bandera_seguridad":
            caso.registrar_bandera(entrada["texto"])
            resultado = _ok(mensaje="bandera registrada")

        elif nombre == "calcular_riesgo_obsolescencia":
            res = calcular_riesgo(entrada.get("factores", {}))
            caso.guardar_riesgo(res.to_dict())
            resultado = _ok(**res.to_dict())

        elif nombre == "resumen_caso":
            resultado = json.dumps(caso.resumen(), ensure_ascii=False)

        elif nombre == "consultar_guia":
            res = conocimiento.consultar(entrada.get("tema", ""), entrada.get("clave"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "consultar_cuestionario":
            res = cuestionario.consultar(entrada.get("tema", ""), entrada.get("clave"))
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "consultar_procedimiento":
            res = procedimiento.consultar(
                entrada.get("tema", ""), entrada.get("clave"), caso=caso
            )
            resultado = json.dumps(res, ensure_ascii=False)

        elif nombre == "iniciar_guia_migracion":
            caso.iniciar_migracion(
                disparador=entrada["disparador"],
                motivo=entrada.get("motivo", ""),
                decidido_por=entrada.get("decidido_por", "usuario"),
            )
            if entrada.get("sin_respaldo"):
                caso.declarar_sin_respaldo(True)
            # El primer paso viaja de vuelta en el mismo tool_result: el modo guia
            # arranca sin depender de que el modelo decida hacer otra consulta.
            sig = procedimiento.siguiente(caso)
            resultado = json.dumps(
                {"estado": "ok",
                 "migracion": caso.migracion,
                 "avance": procedimiento.estado(caso),
                 "primer_paso": sig,
                 "texto_primer_paso": procedimiento.texto_paso(
                     sig["clave"], procedimiento.contexto(caso)) if sig else ""},
                ensure_ascii=False,
            )

        elif nombre == "fijar_cpu_destino":
            destino = caso.fijar_destino(
                marca=entrada["marca"],
                familia=entrada["familia"],
                modelo=entrada.get("modelo", ""),
                justificacion=entrada.get("justificacion", ""),
                fuente=entrada.get("fuente", ""),
            )
            cambio = caso.migracion.get("cambio_marca", False)
            resultado = json.dumps(
                {"estado": "ok",
                 "destino": destino,
                 "cambio_marca": cambio,
                 "consecuencia": (
                     "Cambio de marca: los pasos 21 y 22 dejan de aplicar y el programa "
                     "se reescribe desde cero. Revisa las variantes de los pasos 14, 19 y 48."
                     if cambio else
                     "Misma marca: el procedimiento sigue completo, con herramienta oficial "
                     "de conversion en los pasos 21 y 22."),
                 "avance": procedimiento.estado(caso)},
                ensure_ascii=False,
            )

        elif nombre == "marcar_paso_migracion":
            n = str(entrada["paso"]).strip()
            ctx = procedimiento.contexto(caso)
            p = procedimiento.paso(n, ctx)
            if p is None:
                resultado = json.dumps(
                    {"estado": "error",
                     "mensaje": f"El paso {n} no existe. Validos: 1 a 50, y P1 a P7.",
                     "validos": procedimiento.orden()},
                    ensure_ascii=False,
                )
            else:
                pendientes = [
                    r for r in p["prerrequisitos"]
                    if (caso.migracion or {}).get("pasos", {}).get(str(r), {}).get("estado")
                    not in ("completado", "no_aplica")
                ]
                if entrada["estado"] == "completado" and pendientes:
                    # No se cierra un paso saltandose sus prerrequisitos: la
                    # dependencia es del procedimiento, no criterio del modelo.
                    resultado = json.dumps(
                        {"estado": "rechazado",
                         "mensaje": f"El paso {n} no puede cerrarse: faltan los pasos "
                                    f"{pendientes}. Cierralos o marcalos 'no_aplica' antes.",
                         "prerrequisitos_pendientes": pendientes},
                        ensure_ascii=False,
                    )
                else:
                    caso.marcar_paso(n, entrada["estado"], entrada.get("nota", ""),
                                     entrada.get("evidencia"))
                    sig = procedimiento.siguiente(caso)
                    resultado = json.dumps(
                        {"estado": "ok",
                         "avance": procedimiento.estado(caso),
                         "siguiente_paso": sig["etiqueta"] if sig else None,
                         "texto_siguiente_paso": procedimiento.texto_paso(
                             sig["clave"], ctx) if sig else "Todos los pasos estan cerrados."},
                        ensure_ascii=False,
                    )

        elif nombre == "solicitar_aprobacion_humana":
            aprob = aprobador or _aprobacion_consola
            aprobado = bool(aprob(caso, entrada))
            caso.auditoria.append(
                {
                    "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "accion": "aprobacion_humana",
                    "detalle": {"accion": entrada.get("accion_propuesta"), "aprobado": aprobado},
                }
            )
            resultado = _ok(aprobado=aprobado)

        elif nombre == "generar_informe":
            resultado = _generar_informe(caso, entrada)

        else:
            resultado = json.dumps(
                {"estado": "error", "mensaje": f"herramienta desconocida: {nombre}"},
                ensure_ascii=False,
            )
    except Exception as exc:  # noqa: BLE001 - devolver el error al modelo, no romper el bucle
        resultado = json.dumps(
            {"estado": "error", "mensaje": f"{type(exc).__name__}: {exc}"},
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
    print(f"Riesgos:          {entrada.get('riesgos', '')}")
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
        f"# {entrada.get('titulo', 'Informe tecnico MIGRA-IA')}\n\n"
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
