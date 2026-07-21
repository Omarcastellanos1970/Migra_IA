"""Nucleo compartido: ejecuta un turno del agente sin depender de la consola.

Lo usa la app web. El CLI (agente.py) tiene su propio bucle con streaming, pero
ambos comparten el mismo prompt, herramientas y expediente.
"""

from __future__ import annotations

from . import config
from .caso import Caso
from .herramientas import TOOLS, ejecutar_herramienta


def aprobador_pendiente(caso: Caso, entrada: dict) -> bool:
    """Aprobador para la web: por seguridad, NO aprueba automaticamente.

    Registra la solicitud como pendiente para que la interfaz la muestre y el
    operador la confirme por otra via. El default seguro es 'no aprobado'.
    """
    caso.aprobaciones_pendientes.append(
        {"accion": entrada.get("accion_propuesta"), "riesgos": entrada.get("riesgos")}
    )
    return False


def ejecutar_turno(client, system: str, messages: list, caso: Caso, aprobador=None) -> dict:
    """Ejecuta un turno completo (encadenando herramientas) y devuelve el resultado.

    Muta `messages` in place. Devuelve:
        {"texto": <respuesta del agente>, "acciones": [nombres de herramientas],
         "resumen": <resumen del expediente>}
    """
    if aprobador is None:
        aprobador = aprobador_pendiente

    textos: list[str] = []
    acciones: list[str] = []

    while True:
        respuesta = client.messages.create(
            model=config.MODELO,
            max_tokens=config.MAX_TOKENS,
            system=system,
            thinking=config.THINKING,
            output_config={"effort": config.EFFORT},
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": respuesta.content})

        for bloque in respuesta.content:
            if bloque.type == "text":
                textos.append(bloque.text)

        if respuesta.stop_reason != "tool_use":
            break

        resultados = []
        for bloque in respuesta.content:
            if bloque.type == "tool_use":
                acciones.append(bloque.name)
                salida = ejecutar_herramienta(caso, bloque.name, bloque.input, aprobador)
                resultados.append(
                    {"type": "tool_result", "tool_use_id": bloque.id, "content": salida}
                )
        messages.append({"role": "user", "content": resultados})

    caso.guardar()
    return {
        "texto": "\n\n".join(t for t in textos if t.strip()),
        "acciones": acciones,
        "resumen": caso.resumen(),
    }


def nuevo_cliente():
    """Crea el cliente de Anthropic (lee ANTHROPIC_API_KEY del entorno)."""
    import anthropic  # import perezoso: el motor se puede importar sin el paquete

    return anthropic.Anthropic()
