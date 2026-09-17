"""Construccion del prompt del sistema de MIGRA-IA.

El TEXTO del prompt ya no vive aqui: vive en `data/<idioma>/system_prompt.md`,
junto al resto del contenido del agente. Lo que el prompt dice es contenido, no
codigo, y tenerlo en el mismo sitio que el cuestionario y la guia consigue dos
cosas: que cada archivo este escrito en una sola lengua, y que anadir un idioma
sea traducir un archivo en vez de tocar el modulo.

Este modulo se queda con lo que si es codigo: cargar la plantilla del idioma en
curso y rellenar sus seis huecos con los indices que el agente necesita ver
---secciones del cuestionario, criterios, metodologia, base de referencia,
catalogo de fabricantes y procedimiento---, mas la identidad del agente.

La plantilla codifica la identidad (Sec. 1), las reglas obligatorias (Sec. 8),
los niveles de confianza (Sec. 7), la estructura de respuesta (Sec. 9), el arbol
de decision (Sec. 10) y el principio de cuestionario adaptativo (Sec. 3.1).
"""

from __future__ import annotations

from functools import lru_cache

from . import config, knowledge, questionnaire, manufacturers, procedure


@lru_cache(maxsize=len(config.LANGUAGES))
def _template(lang: str) -> str:
    return config.system_prompt_path(lang).read_text(encoding="utf-8")


@lru_cache(maxsize=len(config.LANGUAGES))
def _build(lang: str) -> str:
    """Arma el prompt de un idioma concreto y lo cachea.

    Fija el idioma mientras construye, para que los seis indices salgan del
    mismo idioma que la plantilla: un prompt con la plantilla en un idioma y el
    cuestionario en otro seria exactamente la mezcla que el proyecto no admite.
    """
    token = config.set_language(lang)
    try:
        return _template(lang).format(
            agent=config.AGENT_NAME,
            code=config.AGENT_CODE,
            version=config.AGENT_VERSION,
            sections=questionnaire.prompt_index(),
            criterios=questionnaire.prompt_criteria(),
            metodologia=knowledge.methodology_summary(),
            base_index=knowledge.prompt_index(),
            catalog_index=manufacturers.prompt_index(),
            procedure_index=procedure.prompt_index(),
        )
    finally:
        config.reset_language(token)


def build_system_prompt() -> str:
    """Prompt del sistema en el idioma de esta peticion."""
    return _build(config.language())


@lru_cache(maxsize=len(config.LANGUAGES))
def _initial_message(lang: str) -> str:
    return config.initial_message_path(lang).read_text(encoding="utf-8").strip()


def initial_user_message() -> str:
    """Mensaje que arranca la conversacion, en el idioma de esta peticion.

    El agente habla primero: este es el turno de usuario que lo provoca. Lo
    comparten el CLI y la app web.
    """
    return _initial_message(config.language())
