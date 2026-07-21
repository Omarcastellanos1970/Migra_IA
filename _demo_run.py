"""Recorrido headless del MODO DEMO (sin API key).

Ejecuta los 13 pasos guionizados sobre un expediente real, mostrando el texto
del agente y las herramientas verdaderas que se invocan en cada paso, y al final
imprime el resumen del expediente (riesgo, activos, faltantes, banderas, etc.).
"""

from __future__ import annotations

import json

from migra_ia.caso import Caso
from migra_ia import demo


def main() -> None:
    caso = Caso()
    caso.guardar()
    print("=" * 68)
    print("MODO DEMO (sin clave) — recorrido completo")
    print("Caso:", caso.case_id)
    print("Pasos guionizados:", len(demo.DEMO_PASOS))
    print("=" * 68)

    for i in range(len(demo.DEMO_PASOS)):
        paso = demo.ejecutar_paso(caso, i)
        primera_linea = paso["texto"].strip().splitlines()[0]
        print(f"\n[{i + 1:>2}/{len(demo.DEMO_PASOS)}] {primera_linea[:88]}")
        if paso["acciones"]:
            print("       herramientas reales -> " + ", ".join(paso["acciones"]))

    print("\n" + "=" * 68)
    print("RESUMEN FINAL DEL EXPEDIENTE (generado por el motor real)")
    print("=" * 68)
    print(json.dumps(caso.resumen(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
