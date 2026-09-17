"""Configuracion central de MIGRA-IA."""

from __future__ import annotations

import contextvars
import json
import os
from functools import lru_cache
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

# --- Rutas del proyecto ---
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CASES_DIR = ROOT / "cases"
CASES_DIR.mkdir(parents=True, exist_ok=True)

# --- Idioma del contenido ---
# El agente existe en espaniol y en ingles. Los IDENTIFICADORES del codigo son
# unicos y estan en ingles; lo que cambia con el idioma es el CONTENIDO, que
# vive en data/<idioma>/.
#
# El idioma NO es del proceso, es de la PETICION. Un mismo servidor atiende a
# la vez a alguien que eligio espaniol y a alguien que eligio ingles, asi que
# se guarda en una variable de contexto: cada hilo de peticion lleva la suya y
# los demas siguen viendo el valor por defecto. Guardarlo en una constante leida
# al importar obligaria a un proceso por idioma, y entonces el selector no
# podria existir.
LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = os.environ.get("MIGRA_IA_LANG", "es").strip().lower()

# Idioma CANONICO: aquel en el que el codigo COMPARA los valores ---las opciones
# del cuestionario, las clases de riesgo, los nombres de las alternativas---.
# Es el castellano porque es el idioma en que se guardan en el expediente y con
# el que estan etiquetados los 188 casos: traducir el dato almacenado romperia
# ese historial. Lo que se traduce es la presentacion, nunca la comparacion.
CANONICAL_LANGUAGE = "es"

# Los archivos que un idioma necesita para considerarse completo. El prompt del
# sistema esta aqui a proposito: es contenido del agente, no codigo, y tenerlo
# en data/<idioma>/ deja cada archivo escrito en una sola lengua.
CONTENT_FILES = ("questionnaire.json", "knowledge_base.json",
                 "cpu_manufacturers.json", "migration_procedure.json",
                 "system_prompt.md", "initial_message.txt",
                 "prompt_labels.json", "ui.json",
                 "tool_descriptions.json")

_language: contextvars.ContextVar[str] = contextvars.ContextVar(
    "migra_ia_language", default=DEFAULT_LANGUAGE)


def language() -> str:
    """Idioma del contenido para esta peticion."""
    return _language.get()


def set_language(lang: str):
    """Fija el idioma de esta peticion y devuelve el testigo para deshacerlo."""
    lang = (lang or "").strip().lower()
    if lang not in LANGUAGES:
        raise ValueError(
            "idioma %r no admitido; los admitidos son: %s"
            % (lang, ", ".join(LANGUAGES)))
    return _language.set(lang)


def reset_language(token) -> None:
    """Deshace un set_language, para no dejar el idioma pegado al hilo."""
    _language.reset(token)


def content_dir(lang: str | None = None) -> Path:
    """Carpeta del contenido del idioma pedido.

    Decision D5 del glosario: un idioma NUNCA se sirve como respaldo del otro.
    Devolver contenido en espaniol a quien pidio ingles daria una pantalla con
    los dos idiomas mezclados, que es justo lo que el proyecto no admite. Por
    eso aqui se falla de forma ruidosa en vez de recurrir a un respaldo
    silencioso.
    """
    lang = lang or language()
    if lang not in LANGUAGES:
        raise ValueError(
            "idioma %r no admitido; los admitidos son: %s"
            % (lang, ", ".join(LANGUAGES)))
    carpeta = DATA_DIR / lang
    if not carpeta.is_dir():
        raise FileNotFoundError(
            "Falta el contenido del idioma %r: no existe %s. Un idioma solo se "
            "ofrece cuando sus archivos estan completos." % (lang, carpeta))
    return carpeta


def questionnaire_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "questionnaire.json"


def knowledge_base_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "knowledge_base.json"


def cpu_manufacturers_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "cpu_manufacturers.json"


def procedure_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "migration_procedure.json"


def system_prompt_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "system_prompt.md"


def initial_message_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "initial_message.txt"


def prompt_labels_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "prompt_labels.json"


def ui_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "ui.json"


def tool_descriptions_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "tool_descriptions.json"


@lru_cache(maxsize=len(LANGUAGES))
def _tool_descriptions(lang: str) -> dict:
    with open(tool_descriptions_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def tool_descriptions() -> dict:
    """Descripciones de las herramientas en el idioma de esta peticion."""
    return _tool_descriptions(language())


def interactive_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "interactive.json"


@lru_cache(maxsize=len(LANGUAGES))
def _interactive_text(lang: str) -> dict:
    with open(interactive_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def interactive_text() -> dict:
    """Texto de la demo interactiva en el idioma de esta peticion."""
    return _interactive_text(language())


def messages_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "messages.json"


@lru_cache(maxsize=len(LANGUAGES))
def _messages(lang: str) -> dict:
    with open(messages_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def messages() -> dict:
    """Mensajes que emiten los modulos, en el idioma de esta peticion."""
    return _messages(language())


@lru_cache(maxsize=len(LANGUAGES))
def _ui(lang: str) -> dict:
    with open(ui_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def ui() -> dict:
    """Textos de la interfaz web en el idioma de esta peticion."""
    return _ui(language())


@lru_cache(maxsize=len(LANGUAGES))
def _labels(lang: str) -> dict:
    with open(prompt_labels_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def labels() -> dict:
    """Rotulos con los que el codigo arma los indices del prompt.

    El contenido sale de los archivos de datos; esto es el andamiaje que lo
    rodea ---'que decide:', 'BASE DE REFERENCIA:'--- y por eso tambien
    depende del idioma: si se quedara fijo en el codigo, el prompt ingles
    saldria con contenido en ingles y rotulos en castellano.
    """
    return _labels(language())


def doc_tools_path(lang: str | None = None) -> Path:
    return content_dir(lang) / "doc_tools.json"


@lru_cache(maxsize=len(LANGUAGES))
def _doc_tools(lang: str) -> dict:
    with open(doc_tools_path(lang), encoding="utf-8") as fh:
        return json.load(fh)


def doc_tools() -> dict:
    """Texto de los guiones que ESCRIBEN documentacion.

    No esta en CONTENT_FILES a proposito: no es contenido del agente y su falta
    no debe esconder un idioma del selector. Es texto de herramientas de
    trabajo, pero alguien lo lee, asi que tambien va por idioma.
    """
    return _doc_tools(language())


def available_languages() -> tuple[str, ...]:
    """Idiomas que se pueden OFRECER: los que tienen sus cuatro archivos.

    Es lo que alimenta el selector. Un idioma a medio traducir no aparece,
    en vez de aparecer y fallar al elegirlo.
    """
    completos = []
    for lang in LANGUAGES:
        carpeta = DATA_DIR / lang
        if carpeta.is_dir() and all((carpeta / f).is_file() for f in CONTENT_FILES):
            completos.append(lang)
    return tuple(completos)


# El idioma por defecto si tiene que ser valido al arrancar: un MIGRA_IA_LANG
# mal escrito debe detenerse aqui y no en mitad de una conversacion.
if DEFAULT_LANGUAGE not in LANGUAGES:
    raise SystemExit(
        "MIGRA_IA_LANG=%r no es un idioma valido; los admitidos son: %s"
        % (DEFAULT_LANGUAGE, ", ".join(LANGUAGES)))
if DEFAULT_LANGUAGE not in available_languages():
    raise SystemExit(
        "El idioma por defecto %r no esta completo en %s. Un idioma solo se "
        "ofrece cuando sus archivos estan completos."
        % (DEFAULT_LANGUAGE, DATA_DIR / DEFAULT_LANGUAGE))

# --- Mensaje de identificacion (Seccion 1) ---
WELCOME_MESSAGE = (
    "MIGRA-IA v{version}\n"
    "Agente inteligente para diagnostico de obsolescencia y migracion de "
    "sistemas de automatizacion industrial.\n"
    "IMPORTANTE: las recomendaciones deben ser verificadas por personal tecnico "
    "autorizado antes de intervenir equipos reales."
).format(version=AGENT_VERSION)
