"""Smoke test no interactivo: ejecuta UN turno real contra la API de Claude.

Confirma end-to-end que:
  - se lee la ANTHROPIC_API_KEY del .env
  - el cliente de Anthropic se crea
  - el system prompt + herramientas producen una respuesta
  - el expediente del caso se guarda

Uso:  ejecutar con el python del entorno virtual (.venv/Scripts/python.exe)
"""

from __future__ import annotations

import sys
import traceback

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from migra_ia import config
from migra_ia.case import Case
from migra_ia.prompt import build_system_prompt, INITIAL_USER_MESSAGE
from migra_ia import core


def main() -> int:
    print("=== SMOKE TEST MIGRA-IA ===")
    print(f"Modelo: {config.MODEL} | effort={config.EFFORT} | thinking={config.THINKING}")

    try:
        client = core.new_client()
    except Exception as exc:  # noqa: BLE001
        print(f"[FALLO] No se pudo crear el cliente: {exc}")
        return 1

    case = Case()
    case.save()
    print(f"Caso abierto: {case.case_id}")

    system = build_system_prompt()
    messages = [{"role": "user", "content": INITIAL_USER_MESSAGE}]

    try:
        resultado = core.run_turn(client, system, messages, case)
    except Exception as exc:  # noqa: BLE001
        print(f"[FALLO] Error durante el turno contra la API: {exc}")
        traceback.print_exc()
        return 2

    print("\n--- RESPUESTA DEL AGENTE ---")
    print(resultado["text"][:2000])
    print("\n--- HERRAMIENTAS INVOCADAS ---")
    print(resultado["acciones"] or "(ninguna en este turno)")
    print("\n[OK] Turno end-to-end completado. Expediente:", case.case_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
