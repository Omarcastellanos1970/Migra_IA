"""Recorrido headless de la DEMO INTERACTIVA (sin API key).

Simula a un usuario respondiendo, para comprobar de punta a punta que el motor
real trabaja con esas respuestas: identificacion contra el catalogo, puntuacion
de riesgo, mapa de decision, eleccion de CPU destino y procedimiento de 50 pasos.

    python _interactive_run.py                 # caso critico, misma marca
    python _interactive_run.py sano            # caso sin obsolescencia
    python _interactive_run.py otra_marca      # cambio de marca sin acceso al codigo
    python _interactive_run.py otra_marca_con_codigo   # cambio de marca con el codigo

El escenario se escribe con las opciones en castellano, que es el idioma
canonico del proyecto, y se dice en el idioma de la sesion (MIGRA_IA_LANG): el
mismo caso tiene que dar la misma puntuacion en los dos.
"""

from __future__ import annotations

import json
import sys

from migra_ia.case import Case
from migra_ia import config, interactive, questionnaire, scoring


def M(key: str) -> str:
    """Rotulo del guion en el idioma de la sesion (data/<idioma>/messages.json)."""
    return config.messages().get(key, key)

# Respuestas por codigo. Lo que un usuario elegiria en cada escenario.
ESCENARIOS = {
    "critical": {
        "equipo": "Siemens S7-300 CPU 315-2 DP",
        "destino": "A",
        "answers": {
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
    "healthy": {
        "equipo": "Siemens S7-1500 CPU 1515-2 PN",
        "destino": "A",
        "answers": {
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
ESCENARIOS["other_brand"] = {**ESCENARIOS["critical"], "destino": "B OMRON"}

# Mismo equipo descontinuado, pero con las contrasenas y el programa en la mano, y
# aun asi se migra a otra marca. Es el cruce que activa la ruta de cambio de marca:
# no hay conversor entre fabricantes, pero tampoco se empieza de cero.
ESCENARIOS["other_brand_with_code"] = {
    **ESCENARIOS["critical"],
    "destino": "B OMRON",
    "answers": {**ESCENARIOS["critical"]["answers"],
                   "F01": "Si", "F06": "Si", "F07": "Si", "N06": "Si, todas"},
}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "critical"
    esc = ESCENARIOS.get(name)
    if esc is None:
        print(f"{M('rn001')}{name}{M('rn002')}{', '.join(ESCENARIOS)}")
        return

    case = Case()
    case.save()
    print("=" * 70)
    print(f"{M('rn003')}'{name}'")
    print(M("rn004"), case.case_id)
    print(M("rn005"), esc["equipo"])
    print("=" * 70)

    apertura = interactive.start()
    status = apertura["status"]
    print("\n" + M("rn006"), apertura["text"].splitlines()[0])

    entradas = [esc["equipo"]]
    turn = 0
    while True:
        turn += 1
        if turn > 120:
            print(M("rn007"))
            break
        entry = entradas.pop(0) if entradas else _next_entry(status, esc)
        step = interactive.answer(case, entry, status)
        status = step["status"]
        cabecera = step["text"].strip().splitlines()[0]
        brand = f" -> {', '.join(step['acciones'])}" if step["acciones"] else ""
        print(f"[{turn:>3}] {M('rn015')}{entry!r:<42} {cabecera[:70]}{brand}")
        if step["fin"]:
            break

    print("\n" + "=" * 70)
    print(M("rn008"))
    print("=" * 70)
    r = case.summary()
    # La clasificacion se guarda en el idioma canonico; lo que se muestra es su
    # etiqueta traducida, igual que en la demo.
    print(M("rn009"), r["risk"]["puntuacion"], "-",
          scoring.risk_label(r["risk"]["classification"]))
    print(M("rn010"), len(r["respuestas_registradas"]))
    print(M("rn011"), len(r["missing_data"]))
    print(M("rn012"), json.dumps(r["migration"], ensure_ascii=False)
          if r["migration"] else M("rn013"))
    print(M("rn014"), r["num_informes"])


def _dicho_en_el_idioma(code: str, value: str) -> str:
    """La respuesta canonica, dicha como la tecleria un usuario de este idioma.

    Busca la opcion por su POSICION, que es la misma en los dos cuestionarios.
    Lo que no es una opcion ---un numero, una lista como "1,2"--- pasa tal cual.
    """
    if config.language() == config.CANONICAL_LANGUAGE:
        return value
    pregunta = questionnaire.question(code, config.CANONICAL_LANGUAGE) or {}
    # Incluye las opciones de si/no que el codigo pone a las preguntas de rama.
    canonicas = interactive._canonical_options(code)
    locales = (interactive._question(code) or {}).get("options") or []
    if not canonicas or len(locales) < len(canonicas):
        return value
    # La coma solo separa respuestas cuando la pregunta admite varias: hay
    # opciones que llevan coma dentro ("Descontinuado, aun con soporte...").
    partes = (value.split(",") if pregunta.get("type") == "seleccion_multiple"
              else [value])
    dichas = []
    for parte in partes:
        p = parte.strip()
        if p.isdigit():
            dichas.append(p)
            continue
        elegida = p
        for i, op in enumerate(canonicas):
            if op.strip().lower() == p.lower():
                elegida = locales[i]
                break
        dichas.append(elegida)
    return ", ".join(dichas)


def _next_entry(status: dict, esc: dict) -> str:
    """Lo que 'escribiria' el usuario, segun la fase y la pregunta en curso."""
    phase = status.get("phase")
    if phase == interactive.F_PREGUNTAS:
        code = status.get("actual")
        return _dicho_en_el_idioma(code, esc["answers"].get(code, "1"))
    seguir = interactive.C("cmd_continue")[0]
    if phase == interactive.F_TARGET:
        return esc["destino"] if status.get("opciones_mostradas") else seguir
    if phase == interactive.F_GUIDE:
        return interactive.C("cmd_done")[0]
    return seguir


if __name__ == "__main__":
    main()
