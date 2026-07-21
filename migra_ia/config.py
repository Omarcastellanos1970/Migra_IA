"""Configuracion central de MIGRA-IA."""

from __future__ import annotations

from pathlib import Path

# --- Identidad del agente (Seccion 1 del documento de diseno) ---
AGENTE_NOMBRE = "MIGRA-IA"
AGENTE_CODIGO = "MIGRA-AI-001"
AGENTE_VERSION = "0.1.0"

# --- Modelo de Claude ---
# Se usa Opus 4.8 con pensamiento adaptativo por ser una tarea de razonamiento
# tecnico sensible. No cambiar el ID salvo indicacion expresa.
MODELO = "claude-opus-4-8"
MAX_TOKENS = 16000
EFFORT = "high"          # low | medium | high | xhigh | max
THINKING = {"type": "adaptive"}

# --- Rutas del proyecto ---
RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / "data"
DIR_CASOS = RAIZ / "casos"
RUTA_CUESTIONARIO = DIR_DATOS / "cuestionario.json"

DIR_CASOS.mkdir(parents=True, exist_ok=True)

# --- Mensaje de identificacion (Seccion 1) ---
MENSAJE_BIENVENIDA = (
    "MIGRA-IA v{version}\n"
    "Agente inteligente para diagnostico de obsolescencia y migracion de "
    "sistemas de automatizacion industrial.\n"
    "IMPORTANTE: las recomendaciones deben ser verificadas por personal tecnico "
    "autorizado antes de intervenir equipos reales."
).format(version=AGENTE_VERSION)
