"""Configuracion central de MIGRA-IA."""

from __future__ import annotations

import os
from pathlib import Path

# --- Identidad del agente (Seccion 1 del documento de diseno) ---
AGENTE_NOMBRE = "MIGRA-IA"
AGENTE_CODIGO = "MIGRA-AI-001"
AGENTE_VERSION = "0.4.0"

# --- Modelo de Claude ---
# Se usa Opus 4.8 con pensamiento adaptativo por ser una tarea de razonamiento
# tecnico sensible. No cambiar el ID salvo indicacion expresa.
MODELO = "claude-opus-4-8"
MAX_TOKENS = 16000
EFFORT = "high"          # low | medium | high | xhigh | max
THINKING = {"type": "adaptive"}

# --- Idioma del contenido ---
# El agente existe en espaniol y en ingles. Los IDENTIFICADORES del codigo son
# unicos y estan en ingles; lo que cambia con el idioma es el CONTENIDO, que
# vive en data/<idioma>/. Por defecto espaniol (decision D1 del glosario), para
# que nada cambie a quien ya usa el agente.
IDIOMAS = ("es", "en")
IDIOMA = os.environ.get("MIGRA_IA_LANG", "es").strip().lower()

# --- Rutas del proyecto ---
RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / "data"
DIR_CASOS = RAIZ / "cases"
DIR_CONTENIDO = DIR_DATOS / IDIOMA

# Decision D5 del glosario: un idioma NUNCA se sirve como respaldo del otro.
# Devolver contenido en espaniol a quien pidio ingles daria una pantalla con
# los dos idiomas mezclados, que es justo lo que el proyecto no admite. Por eso
# aqui se falla de forma ruidosa en vez de recurrir a un respaldo silencioso.
if IDIOMA not in IDIOMAS:
    raise SystemExit(
        "MIGRA_IA_LANG=%r no es un idioma valido; los admitidos son: %s"
        % (IDIOMA, ", ".join(IDIOMAS)))
if not DIR_CONTENIDO.is_dir():
    raise SystemExit(
        "Falta el contenido del idioma %r: no existe %s. Un idioma solo se "
        "ofrece cuando sus archivos estan completos." % (IDIOMA, DIR_CONTENIDO))

RUTA_CUESTIONARIO = DIR_CONTENIDO / "questionnaire.json"
RUTA_BASE_CONOCIMIENTO = DIR_CONTENIDO / "knowledge_base.json"
RUTA_FABRICANTES_CPU = DIR_CONTENIDO / "cpu_manufacturers.json"
RUTA_PROCEDIMIENTO = DIR_CONTENIDO / "migration_procedure.json"

DIR_CASOS.mkdir(parents=True, exist_ok=True)

# --- Mensaje de identificacion (Seccion 1) ---
MENSAJE_BIENVENIDA = (
    "MIGRA-IA v{version}\n"
    "Agente inteligente para diagnostico de obsolescencia y migracion de "
    "sistemas de automatizacion industrial.\n"
    "IMPORTANTE: las recomendaciones deben ser verificadas por personal tecnico "
    "autorizado antes de intervenir equipos reales."
).format(version=AGENTE_VERSION)
