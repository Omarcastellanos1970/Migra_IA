"""Nucleo compartido: ejecuta un turno del agente sin depender de la consola.

Lo usa la app web. El CLI (agente.py) tiene su propio bucle con streaming, pero
ambos comparten el mismo prompt, herramientas y expediente.
"""

from __future__ import annotations

from . import config
from .case import Case
from .tools import tools, run_tool


def pending_approver(case: Case, entry: dict) -> bool:
    """Aprobador para la web: por seguridad, NO aprueba automaticamente.

    Registra la solicitud como pendiente para que la interfaz la muestre y el
    operador la confirme por otra via. El default seguro es 'no aprobado'.
    """
    case.pending_approvals.append(
        {"accion": entry.get("accion_propuesta"), "risks": entry.get("risks")}
    )
    return False


def run_turn(client, system: str, messages: list, case: Case, approver=None) -> dict:
    """Ejecuta un turno completo (encadenando herramientas) y devuelve el resultado.

    Muta `messages` in place. Devuelve:
        {"text": <respuesta del agente>, "acciones": [nombres de herramientas],
         "resumen": <resumen del expediente>}
    """
    if approver is None:
        approver = pending_approver

    textos: list[str] = []
    actions: list[str] = []

    while True:
        answer = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system,
            thinking=config.THINKING,
            output_config={"effort": config.EFFORT},
            tools=tools(),
            messages=messages,
        )
        messages.append({"role": "assistant", "content": answer.content})

        for bloque in answer.content:
            if bloque.type == "text":
                textos.append(bloque.text)

        if answer.stop_reason != "tool_use":
            break

        resultados = []
        for bloque in answer.content:
            if bloque.type == "tool_use":
                actions.append(bloque.name)
                output = run_tool(case, bloque.name, bloque.input, approver)
                resultados.append(
                    {"type": "tool_result", "tool_use_id": bloque.id, "content": output}
                )
        messages.append({"role": "user", "content": resultados})

    case.save()
    return {
        "text": "\n\n".join(t for t in textos if t.strip()),
        "acciones": actions,
        "resumen": case.summary(),
    }


def new_client():
    """Crea el cliente de Anthropic (lee ANTHROPIC_API_KEY del entorno)."""
    import anthropic  # import perezoso: el motor se puede importar sin el paquete

    return anthropic.Anthropic()
