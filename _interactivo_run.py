"""Recorrido headless de la DEMO INTERACTIVA (sin API key).

Simula a un usuario respondiendo, para comprobar de punta a punta que el motor
real trabaja con esas respuestas: identificacion contra el catalogo, puntuacion
de riesgo, mapa de decision, eleccion de CPU destino y procedimiento de 50 pasos.

    python _interactivo_run.py                 # caso critico, misma marca
    python _interactivo_run.py sano            # caso sin obsolescencia
    python _interactivo_run.py otra_marca      # migracion con cambio de marca
"""

from __future__ import annotations

import json
import sys

from migra_ia.caso import Caso
from migra_ia import interactivo

# Respuestas por codigo. Lo que un usuario elegiria en cada escenario.
ESCENARIOS = {
    "critico": {
        "equipo": "Siemens S7-300 CPU 315-2 DP",
        "destino": "A",
        "respuestas": {
            "C08": "Alta: afecta una linea importante",
            "C10": "4 a 12 horas",
            "Q04": "En el paro anual de planta o vacaciones",
            "M01": "Descontinuado, aun con soporte y repuestos",
            "M04": "Solo por pedido especial",
            "M06": "De 2 a 8 semanas",
            "M09": "No",
            "M07": "Si, de tercero sin certificar",
            "F01": "No",
            "F12": "Si",
            "F13": "No",
            "N02": "Windows 7",
            "N03": "Llave fisica (dongle)",
            "N05": "Si, pero sin probar",
            "N06": "No",
            "G01": "1,2",
            "O07": "1,3",
            "O08": "Si",
            "O02": "No",
            "L01": "6",
            "L03": "En aumento",
            "L07": "Si",
            "P01": "Entre 40 y 50 C",
            "P04": "1,7",
        },
    },
    "sano": {
        "equipo": "Siemens S7-1500 CPU 1515-2 PN",
        "destino": "A",
        "respuestas": {
            "C08": "Baja: puede detenerse varios dias",
            "C10": "Mas de 24 horas",
            "Q04": "En cualquier momento",
            "M01": "Activo, en comercializacion",
            "M04": "Si, sin problema",
            "M06": "En existencia en la planta o local",
            "M09": "Si, vigente",
            "M07": "Si, del fabricante",
            "F01": "Si",
            "F06": "Si",
            "F07": "Si",
            "N02": "Windows 11",
            "N03": "Original con licencia vigente",
            "N05": "Si, ya probado con este PLC",
            "N06": "Si, todas",
            "G01": "4",
            "O07": "1,4",
            "O08": "No",
            "O02": "No",
            "L01": "0",
            "L03": "Sin fallas registradas",
            "L07": "No",
            "P01": "Menor a 30 C",
            "P04": "5,6",
        },
    },
}
ESCENARIOS["otra_marca"] = {**ESCENARIOS["critico"], "destino": "B OMRON"}


def main() -> None:
    nombre = sys.argv[1] if len(sys.argv) > 1 else "critico"
    esc = ESCENARIOS.get(nombre)
    if esc is None:
        print(f"Escenario desconocido: {nombre}. Validos: {', '.join(ESCENARIOS)}")
        return

    caso = Caso()
    caso.guardar()
    print("=" * 70)
    print(f"DEMO INTERACTIVA — escenario '{nombre}'")
    print("Caso:  ", caso.case_id)
    print("Equipo:", esc["equipo"])
    print("=" * 70)

    apertura = interactivo.iniciar()
    estado = apertura["estado"]
    print("\n[apertura]", apertura["texto"].splitlines()[0])

    entradas = [esc["equipo"]]
    turno = 0
    while True:
        turno += 1
        if turno > 120:
            print("\n!! demasiados turnos, se corta")
            break
        entrada = entradas.pop(0) if entradas else _siguiente_entrada(estado, esc)
        paso = interactivo.responder(caso, entrada, estado)
        estado = paso["estado"]
        cabecera = paso["texto"].strip().splitlines()[0]
        marca = f" -> {', '.join(paso['acciones'])}" if paso["acciones"] else ""
        print(f"[{turno:>3}] entrada={entrada!r:<42} {cabecera[:70]}{marca}")
        if paso["fin"]:
            break

    print("\n" + "=" * 70)
    print("RESULTADO (motor real, sin modelo de lenguaje)")
    print("=" * 70)
    r = caso.resumen()
    print("riesgo    :", r["riesgo"]["puntuacion"], "-", r["riesgo"]["clasificacion"])
    print("respuestas:", len(r["respuestas_registradas"]))
    print("faltantes :", len(r["datos_faltantes"]))
    print("migracion :", json.dumps(r["migracion"], ensure_ascii=False)
          if r["migracion"] else "no abierta")
    print("informes  :", r["num_informes"])


def _siguiente_entrada(estado: dict, esc: dict) -> str:
    """Lo que 'escribiria' el usuario, segun la fase y la pregunta en curso."""
    fase = estado.get("fase")
    if fase == interactivo.F_PREGUNTAS:
        codigo = estado.get("actual")
        return esc["respuestas"].get(codigo, "1")
    if fase == interactivo.F_DESTINO:
        return esc["destino"] if estado.get("opciones_mostradas") else "continuar"
    if fase == interactivo.F_GUIA:
        return "hecho"
    return "continuar"


if __name__ == "__main__":
    main()
