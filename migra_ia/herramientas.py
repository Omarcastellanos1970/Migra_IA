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
from . import config

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
            resultado = _ok(id_activo=aid)

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
