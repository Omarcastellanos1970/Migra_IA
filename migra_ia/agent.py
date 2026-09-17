"""Bucle conversacional de MIGRA-IA (interfaz de linea de comandos).

Ejecuta un ciclo agentico manual sobre la API de Claude: el modelo conduce el
cuestionario adaptativo paso a paso, invoca herramientas para registrar datos y
calcular riesgo, y todo queda persistido en el expediente del caso.

Uso:
    python -m migra_ia.agent            # nuevo caso
    python -m migra_ia.agent CAS-2026-000123   # continuar un caso existente
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
from .tools import tools, run_tool


def C(key: str) -> tuple:
    """Palabras que el usuario puede teclear para un mando, en su idioma."""
    return tuple(s.strip().lower() for s in M(key).split(","))


def M(key: str) -> str:
    """Mensaje de este modulo en el idioma de esta peticion."""
    from . import config
    return config.messages().get(key, key)


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
            tools=tools(),
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
    print(f"{COLOR_TENUE}{M('ag001')}{RESET}\n")

    # Nuevo caso o continuar uno existente.
    if len(sys.argv) > 1:
        case = Case.load(sys.argv[1])
        print(f"{M('ag005')}{case.case_id}")
    else:
        case = Case()
        case.save()
        print(f"{M('ag006')}{case.case_id}")

    try:
        client = anthropic.Anthropic()
    except Exception as exc:  # noqa: BLE001
        print(f"{M('ag002')}{exc}")
        print(M("ag004"))
        return

    system = build_system_prompt()
    messages: list[dict] = [{"role": "user", "content": _SEED}]

    # Primer turno: el agente se presenta y abre el diagnostico.
    _agent_turn(client, system, messages, case)

    while True:
        try:
            entry = input(f"\n{COLOR_TENUE}{M('ag003')}{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(M("ag007"))
            break

        if not entry:
            continue
        # Los mandos se aceptan en los dos idiomas; lo que cambia es cual se
        # documenta. Un usuario ingles no tiene por que saber que es "/salir".
        if entry.lower() in C("ag_cmd_exit"):
            break
        if entry.lower() in C("ag_cmd_summary"):
            import json

            print(json.dumps(case.summary(), ensure_ascii=False, indent=2))
            continue

        messages.append({"role": "user", "content": entry})
        _agent_turn(client, system, messages, case)

    path = case.save()
    print(f"{M('ag008')}{path}")
    if case.reports:
        print(M("ag009"))
        for inf in case.reports:
            print(f"  - {inf['route']}")


if __name__ == "__main__":
    main()
