"""Recorrido headless del MODO DEMO adaptativo (sin API key).

Ejecuta el recorrido completo sobre un expediente real, mostrando el texto del
agente y las herramientas verdaderas que se invocan en cada paso, y al final
imprime el resumen del expediente (riesgo, activos, faltantes, banderas, etc.).

El equipo se pasa como argumento, y es lo que hace que el recorrido cambie:

    python _demo_run.py "Allen Bradley SLC 5/04"
    python _demo_run.py "omron CJ1M-CPU13"
    python _demo_run.py            # sin argumento: Siemens CPU 315-2 DP
"""

from __future__ import annotations

import json
import sys

from migra_ia.caso import Caso
from migra_ia import demo

EQUIPO_POR_DEFECTO = "Siemens CPU 315-2 DP"
NOMBRE_POR_DEFECTO = "Carlos"


def main() -> None:
    equipo = sys.argv[1] if len(sys.argv) > 1 else EQUIPO_POR_DEFECTO

    caso = Caso()
    caso.guardar()
    print("=" * 68)
    print("MODO DEMO ADAPTATIVO (sin clave) — recorrido completo")
    print("Caso:  ", caso.case_id)
    print("Equipo:", equipo)
    print("=" * 68)

    # Lo que 'escribiria' el usuario en cada paso que la demo si lee.
    entradas = {demo.PASO_NOMBRE: NOMBRE_POR_DEFECTO, demo.PASO_EQUIPO: equipo}

    ctx: dict = {}
    i = 0
    while True:
        paso = demo.ejecutar_paso(caso, i, entradas.get(i, "continuar"), ctx)
        ctx = paso.pop("ctx", ctx)
        primera_linea = paso["texto"].strip().splitlines()[0]
        print(f"\n[{i + 1:>2}] {primera_linea[:88]}")
        if paso["acciones"]:
            print("     herramientas reales -> " + ", ".join(paso["acciones"]))
        if paso["fin"]:
            break
        i += 1

    print("\n" + "=" * 68)
    print("EQUIPO IDENTIFICADO CONTRA EL CATALOGO")
    print("=" * 68)
    print(f"Marca:   {ctx.get('marca')}")
    print(f"Familia: {ctx.get('familia')}  (generacion {ctx.get('posicion')}, "
          f"etapa {ctx.get('etapa')})")
    print(f"Destino: {ctx.get('destino_familia')}")
    print(f"Fuente:  {ctx.get('fuente_texto')}")

    print("\n" + "=" * 68)
    print("RESUMEN FINAL DEL EXPEDIENTE (generado por el motor real)")
    print("=" * 68)
    print(json.dumps(caso.resumen(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
