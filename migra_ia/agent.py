"""Bucle conversacional de MIGRA-IA (interfaz de linea de comandos).

Ejecuta un ciclo agentico manual sobre la API de Claude: el modelo conduce el
cuestionario adaptativo paso a paso, invoca herramientas para registrar datos y
calcular riesgo, y todo queda persistido en el expediente del caso.

Uso:
    python -m migra_ia.agente            # nuevo caso
    python -m migra_ia.agente CAS-2026-000123   # continuar un caso existente
"""

from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv  # opcional

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

import anthropic

from . import config
from .case import Case
from .prompt import build_system_prompt, initial_user_message
from .tools import TOOLS, run_tool

_SEED = initial_user_message()

AGENT_COLOR = "\033[96m"   # cian
COLOR_TENUE = "\033[90m"    # gris
RESET = "\033[0m"


def _agent_turn(client, system, messages, case) -> None:
    """Ejecuta un turno completo del agente: puede encadenar varias herramientas."""
    while True:
        print(f"\n{AGENT_COLOR}MIGRA-IA:{RESET} ", end="", flush=True)
        with client.messages.stream(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system,
            thinking=config.THINKING,
            output_config={"effort": config.EFFORT},
            tools=TOOLS,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            answer = stream.get_final_message()
        print()

        messages.append({"role": "assistant", "content": answer.content})

        if answer.stop_reason != "tool_use":
            break

        # Ejecutar todas las herramientas solicitadas en este turno.
        resultados = []
        for bloque in answer.content:
            if bloque.type == "tool_use":
                print(f"{COLOR_TENUE}  [registro: {bloque.name}]{RESET}")
                output = run_tool(case, bloque.name, bloque.input)
                resultados.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": output,
                    }
                )
        messages.append({"role": "user", "content": resultados})


def main() -> None:
    print(config.WELCOME_MESSAGE)
    print(f"{COLOR_TENUE}(escribe /salir para terminar, /resumen para ver el estado del caso){RESET}\n")

    # Nuevo caso o continuar uno existente.
    if len(sys.argv) > 1:
        case = Case.load(sys.argv[1])
        print(f"Caso cargado: {case.case_id}")
    else:
        case = Case()
        case.save()
        print(f"Nuevo caso abierto: {case.case_id}")

    try:
        client = anthropic.Anthropic()
    except Exception as exc:  # noqa: BLE001
        print(f"\nNo se pudo inicializar el cliente de Anthropic: {exc}")
        print("Configura la variable de entorno ANTHROPIC_API_KEY (ver .env.example).")
        return

    system = build_system_prompt()
    messages: list[dict] = [{"role": "user", "content": _SEED}]

    # Primer turno: el agente se presenta y abre el diagnostico.
    _agent_turn(client, system, messages, case)

    while True:
        try:
            entry = input(f"\n{COLOR_TENUE}Tu respuesta:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesion interrumpida.")
            break

        if not entry:
            continue
        if entry.lower() in ("/salir", "/exit", "/quit"):
            break
        if entry.lower() == "/resumen":
            import json

            print(json.dumps(case.summary(), ensure_ascii=False, indent=2))
            continue

        messages.append({"role": "user", "content": entry})
        _agent_turn(client, system, messages, case)

    path = case.save()
    print(f"\nExpediente guardado en: {path}")
    if case.reports:
        print("Informes generados:")
        for inf in case.reports:
            print(f"  - {inf['route']}")


if __name__ == "__main__":
    main()
