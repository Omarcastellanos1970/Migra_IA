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
from .caso import Caso
from .prompt import construir_system_prompt, MENSAJE_INICIAL_USUARIO
from .herramientas import TOOLS, ejecutar_herramienta

_SEMILLA = MENSAJE_INICIAL_USUARIO

COLOR_AGENTE = "\033[96m"   # cian
COLOR_TENUE = "\033[90m"    # gris
RESET = "\033[0m"


def _turno_agente(client, system, messages, caso) -> None:
    """Ejecuta un turno completo del agente: puede encadenar varias herramientas."""
    while True:
        print(f"\n{COLOR_AGENTE}MIGRA-IA:{RESET} ", end="", flush=True)
        with client.messages.stream(
            model=config.MODELO,
            max_tokens=config.MAX_TOKENS,
            system=system,
            thinking=config.THINKING,
            output_config={"effort": config.EFFORT},
            tools=TOOLS,
            messages=messages,
        ) as stream:
            for texto in stream.text_stream:
                print(texto, end="", flush=True)
            respuesta = stream.get_final_message()
        print()

        messages.append({"role": "assistant", "content": respuesta.content})

        if respuesta.stop_reason != "tool_use":
            break

        # Ejecutar todas las herramientas solicitadas en este turno.
        resultados = []
        for bloque in respuesta.content:
            if bloque.type == "tool_use":
                print(f"{COLOR_TENUE}  [registro: {bloque.name}]{RESET}")
                salida = ejecutar_herramienta(caso, bloque.name, bloque.input)
                resultados.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": salida,
                    }
                )
        messages.append({"role": "user", "content": resultados})


def main() -> None:
    print(config.MENSAJE_BIENVENIDA)
    print(f"{COLOR_TENUE}(escribe /salir para terminar, /resumen para ver el estado del caso){RESET}\n")

    # Nuevo caso o continuar uno existente.
    if len(sys.argv) > 1:
        caso = Caso.cargar(sys.argv[1])
        print(f"Caso cargado: {caso.case_id}")
    else:
        caso = Caso()
        caso.guardar()
        print(f"Nuevo caso abierto: {caso.case_id}")

    try:
        client = anthropic.Anthropic()
    except Exception as exc:  # noqa: BLE001
        print(f"\nNo se pudo inicializar el cliente de Anthropic: {exc}")
        print("Configura la variable de entorno ANTHROPIC_API_KEY (ver .env.example).")
        return

    system = construir_system_prompt()
    messages: list[dict] = [{"role": "user", "content": _SEMILLA}]

    # Primer turno: el agente se presenta y abre el diagnostico.
    _turno_agente(client, system, messages, caso)

    while True:
        try:
            entrada = input(f"\n{COLOR_TENUE}Tu respuesta:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesion interrumpida.")
            break

        if not entrada:
            continue
        if entrada.lower() in ("/salir", "/exit", "/quit"):
            break
        if entrada.lower() == "/resumen":
            import json

            print(json.dumps(caso.resumen(), ensure_ascii=False, indent=2))
            continue

        messages.append({"role": "user", "content": entrada})
        _turno_agente(client, system, messages, caso)

    ruta = caso.guardar()
    print(f"\nExpediente guardado en: {ruta}")
    if caso.informes:
        print("Informes generados:")
        for inf in caso.informes:
            print(f"  - {inf['ruta']}")


if __name__ == "__main__":
    main()
