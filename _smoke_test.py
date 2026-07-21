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
from migra_ia.caso import Caso
from migra_ia.prompt import construir_system_prompt, MENSAJE_INICIAL_USUARIO
from migra_ia import nucleo


def main() -> int:
    print("=== SMOKE TEST MIGRA-IA ===")
    print(f"Modelo: {config.MODELO} | effort={config.EFFORT} | thinking={config.THINKING}")

    try:
        client = nucleo.nuevo_cliente()
    except Exception as exc:  # noqa: BLE001
        print(f"[FALLO] No se pudo crear el cliente: {exc}")
        return 1

    caso = Caso()
    caso.guardar()
    print(f"Caso abierto: {caso.case_id}")

    system = construir_system_prompt()
    messages = [{"role": "user", "content": MENSAJE_INICIAL_USUARIO}]

    try:
        resultado = nucleo.ejecutar_turno(client, system, messages, caso)
    except Exception as exc:  # noqa: BLE001
        print(f"[FALLO] Error durante el turno contra la API: {exc}")
        traceback.print_exc()
        return 2

    print("\n--- RESPUESTA DEL AGENTE ---")
    print(resultado["texto"][:2000])
    print("\n--- HERRAMIENTAS INVOCADAS ---")
    print(resultado["acciones"] or "(ninguna en este turno)")
    print("\n[OK] Turno end-to-end completado. Expediente:", caso.case_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
