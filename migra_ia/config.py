"""Configuracion central de MIGRA-IA."""

from __future__ import annotations

import os
from pathlib import Path

# --- Identidad del agente (Seccion 1 del documento de diseno) ---
AGENT_NAME = "MIGRA-IA"
AGENT_CODE = "MIGRA-AI-001"
AGENT_VERSION = "0.4.0"

# --- Modelo de Claude ---
# Se usa Opus 4.8 con pensamiento adaptativo por ser una tarea de razonamiento
# tecnico sensible. No cambiar el ID salvo indicacion expresa.
MODEL = "claude-opus-4-8"
MAX_TOKENS = 16000
EFFORT = "high"          # low | medium | high | xhigh | max
THINKING = {"type": "adaptive"}

# --- Idioma del contenido ---
# El agente existe en espaniol y en ingles. Los IDENTIFICADORES del codigo son
# unicos y estan en ingles; lo que cambia con el idioma es el CONTENIDO, que
# vive en data/<idioma>/. Por defecto espaniol (decision D1 del glosario), para
# que nada cambie a quien ya usa el agente.
LANGUAGES = ("es", "en")
LANGUAGE = os.environ.get("MIGRA_IA_LANG", "es").strip().lower()

# --- Rutas del proyecto ---
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CASES_DIR = ROOT / "cases"
CONTENT_DIR = DATA_DIR / LANGUAGE

# Decision D5 del glosario: un idioma NUNCA se sirve como respaldo del otro.
# Devolver contenido en espaniol a quien pidio ingles daria una pantalla con
# los dos idiomas mezclados, que es justo lo que el proyecto no admite. Por eso
# aqui se falla de forma ruidosa en vez de recurrir a un respaldo silencioso.
if LANGUAGE not in LANGUAGES:
    raise SystemExit(
        "MIGRA_IA_LANG=%r no es un idioma valido; los admitidos son: %s"
        % (LANGUAGE, ", ".join(LANGUAGES)))
if not CONTENT_DIR.is_dir():
    raise SystemExit(
        "Falta el contenido del idioma %r: no existe %s. Un idioma solo se "
        "ofrece cuando sus archivos estan completos." % (LANGUAGE, CONTENT_DIR))

QUESTIONNAIRE_PATH = CONTENT_DIR / "questionnaire.json"
KNOWLEDGE_BASE_PATH = CONTENT_DIR / "knowledge_base.json"
CPU_MANUFACTURERS_PATH = CONTENT_DIR / "cpu_manufacturers.json"
PROCEDURE_PATH = CONTENT_DIR / "migration_procedure.json"

CASES_DIR.mkdir(parents=True, exist_ok=True)

# --- Mensaje de identificacion (Seccion 1) ---
WELCOME_MESSAGE = (
    "MIGRA-IA v{version}\n"
    "Agente inteligente para diagnostico de obsolescencia y migracion de "
    "sistemas de automatizacion industrial.\n"
    "IMPORTANTE: las recomendaciones deben ser verificadas por personal tecnico "
    "autorizado antes de intervenir equipos reales."
).format(version=AGENT_VERSION)
