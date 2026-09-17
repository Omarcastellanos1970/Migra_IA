"""Extrae del codigo las tablas completas de puntuacion de los 8 factores.

Las constantes que convierten una respuesta en un valor 0-100 viven dentro de
las funciones `_f_*` de `migra_ia/interactive.py`. Este script las lee del
arbol sintactico del propio modulo, de modo que el documento generado no puede
divergir del motor: si alguien cambia un numero en el codigo, el documento
cambia en la siguiente corrida.

    python _scoring_rules.py          # resumen en pantalla
    python _scoring_rules.py --md     # escribe el documento del idioma activo

Lo que el arbol sintactico SI captura: las tablas de consulta literales
(respuesta -> numero), los valores de arranque y los incrementos constantes.

Lo que NO captura, y por eso va descrito a mano en NOTAS: los cruces entre
codigos (repuestos contrasta M06 con C10), los topes (historial se limita si
hay causa raiz externa) y las condiciones de omision. Esos se explican en
prosa y se verifican ejecutando el motor.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

from migra_ia import config, questionnaire, scoring

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "migra_ia" / "interactive.py"


def D(key: str) -> str:
    """Texto del documento en el idioma de esta ejecucion."""
    return config.doc_tools().get(key, key)


def output_path() -> Path:
    """Donde va el documento de este idioma. La ruta la declara el idioma."""
    return ROOT / D("sr_path")


def _answer_text(code: str | None, canonico: str) -> str:
    """La respuesta de la tabla, dicha en el idioma del documento."""
    return questionnaire.option_in(code, canonico) if code else canonico

# Nombre de la funcion que implementa cada factor de scoring.PESOS.
FUNCTION = {
    "estado_ciclo_vida": "_f_lifecycle",
    "disponibilidad_repuestos": "_f_spare_parts",
    "soporte_fabricante": "_f_support",
    "disponibilidad_software": "_f_software",
    "disponibilidad_respaldo": "_f_backup",
    "compatibilidad_sistemas": "_f_compatibility",
    "historial_fallas": "_f_history",
    "criticidad_productiva": "_f_criticality",
}

# Las notas describen lo que el arbol sintactico NO captura. Viven en
# data/<idioma>/doc_tools.json, con la clave sr_note_<factor>.
_NOTAS_VIEJAS = {
    "estado_ciclo_vida":
        "Tabla directa sobre M01. Si M01 es 'No se conoce' el factor NO se "
        "puntua: se omite, los pesos se renormalizan y el hueco se registra "
        "como dato faltante. Es la unica forma de que el motor no suponga un "
        "estado que nadie declaro.",
    "disponibilidad_repuestos":
        "M04 fija la base. Despues hay un CRUCE que la tabla no muestra: se "
        "compara el plazo de entrega (M06) con la parada que la linea tolera "
        "(C10). Si M06 esta en 'De 2 a 8 semanas' o peor, la base se eleva a "
        "un minimo de 85, porque un repuesto que llega despues de lo que la "
        "planta aguanta no cubre el riesgo por si solo.",
    "soporte_fabricante":
        "M09 (contrato vigente) fija la base y M07 (servicio de reparacion) "
        "la ajusta hacia arriba o hacia abajo. Si M09 no se conoce, la base "
        "queda en 55 salvo que M07 tampoco se conozca, en cuyo caso el factor "
        "se omite.",
    "disponibilidad_software":
        "ACUMULADOR: **arranca en 20** y suma las cuatro tablas de arriba "
        "(N02 + N03 + N05 + N06). Un valor no listado suma el defecto "
        "indicado. El resultado se acota a 0-100. El factor solo se omite si "
        "los cuatro codigos faltan a la vez.",
    "disponibilidad_respaldo":
        "CONDICIONAL EN CASCADA, no hay tabla. Se evalua en este orden y se "
        "detiene en la primera que se cumpla:\n\n"
        "| Situacion | Valor |\n|---|---|\n"
        "| F01 no se respondio | *factor omitido* |\n"
        "| F01 = No (no existe copia) | 100 |\n"
        "| F01 no se conoce | 90 |\n"
        "| F06 = No (el respaldo no abre) | 100 |\n"
        "| F07 = No (no compila) | 90 |\n"
        "| F06 = Si y F07 = Si (verificado) | 15 |\n"
        "| verificacion incompleta | 70 |\n\n"
        "La logica es la Regla 3 de la guia: un respaldo que no se puede "
        "verificar se trata como ausente. Por eso 'no se sabe' (90) puntua "
        "casi como 'no existe' (100), y solo el respaldo que abre Y compila "
        "baja a 15.",
    "compatibilidad_sistemas":
        "ACUMULADOR, no hay tabla. **Arranca en 20** y suma por cada cosa que "
        "el cambio arrastra:\n\n"
        "| Condicion | Suma |\n|---|---|\n"
        "| G01 incluye una red propietaria | +30 |\n"
        "| G01 incluye red de generacion anterior* | +15 |\n"
        "| O07 incluye bloques propietarios | +20 |\n"
        "| O07 incluye lista de instrucciones (AWL/STL) | +15 |\n"
        "| O07 incluye GRAFCET / SFC / GRAPH | +10 |\n"
        "| O08 = Si (librerias propietarias) | +25 |\n"
        "| O02 = Si (control de movimiento) | +20 |\n\n"
        "Las dos de G01 son excluyentes: propietaria tiene prioridad sobre "
        "legado. Las de O07 se acumulan entre si. Se acota a 0-100.\n\n"
        "*Redes consideradas de generacion anterior: MPI, Profibus DP, "
        "Profibus PA, DeviceNet, ControlNet, CC-Link, AS-Interface, RS-232, "
        "RS-485.",
    "historial_fallas":
        "L01 (numero de paros en 12 meses) fija el escalon, que es un "
        "condicional y no una tabla:\n\n"
        "| Paros en L01 | Valor |\n|---|---|\n"
        "| 0 | 10 |\n| 1 a 2 | 30 |\n| 3 a 5 | 50 |\n| mas de 5 | 70 |\n"
        "| sin numero legible | 45 |\n\n"
        "Sobre ese escalon se suma la tabla de L03 de arriba. Despues se "
        "aplica un TOPE: si hay causa raiz externa sin corregir (tablero "
        "caliente, mala puesta a tierra, energia deficiente, bateria "
        "agotada), el factor se **limita a 55**, porque esas fallas no son "
        "atribuibles al controlador y sustituirlo no las corrige. Es el "
        "unico factor cuyo valor puede BAJAR por una regla de diseno.",
    "criticidad_productiva":
        "C08 (criticidad de la maquina) fija la base; C10 (parada tolerable) "
        "y Q04 (ventana de intervencion) la suben. Si C08 no se conoce, el "
        "factor se omite entero.",
}


def _number(nodo):
    """Valor numerico de un literal, incluido el negativo (UnaryOp USub)."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if (isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub)
            and isinstance(nodo.operand, ast.Constant)
            and isinstance(nodo.operand.value, (int, float))):
        return -nodo.operand.value
    return None


def _code_read(nodo):
    """Codigo de pregunta del argumento de `.get(...)`, si se puede determinar.

    Tambien lo ve a traves de `_canon("M09", m09)`, que es como el motor lleva
    la respuesta a su opcion canonica antes de compararla: el codigo esta ahi,
    en el primer argumento.
    """
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.Name):
        return nodo.id.upper()          # variables locales m01, n03, c08...
    if (isinstance(nodo, ast.Call) and nodo.args
            and isinstance(nodo.args[0], ast.Constant)
            and isinstance(nodo.args[0].value, str)):
        return nodo.args[0].value
    return None


def tables_of(function_name: str):
    """Tablas literales respuesta -> numero, con su valor por defecto.

    Se recorren los nodos `Call` de la forma `{...}.get(x)` o `{...}.get(x, N)`,
    de manera que la tabla y su defecto salen del MISMO nodo. Emparejarlos por
    posicion en dos listas separadas los desalinea en cuanto una tabla no lleva
    defecto, que es justo lo que pasa en soporte y en criticidad.
    """
    arbol = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next((n for n in ast.walk(arbol)
               if isinstance(n, ast.FunctionDef) and n.name == function_name), None)
    if fn is None:
        return []
    encontradas = []
    for nodo in ast.walk(fn):
        if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "get" and isinstance(nodo.func.value, ast.Dict)):
            continue
        d = nodo.func.value
        filas, ok = [], True
        for k, v in zip(d.keys, d.values):
            value = _number(v)
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)) or value is None:
                ok = False
                break
            filas.append((k.value, value))
        if not ok or not filas:
            continue
        defecto = _number(nodo.args[1]) if len(nodo.args) > 1 else None
        encontradas.append({
            "filas": filas,
            "defecto": defecto,
            "code": _code_read(nodo.args[0]) if nodo.args else None,
        })
    return encontradas


def codes_of(function_name: str):
    """Codigos de pregunta que la funcion lee."""
    arbol = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next((n for n in ast.walk(arbol)
               if isinstance(n, ast.FunctionDef) and n.name == function_name), None)
    vistos = []
    if fn is None:
        return vistos
    for nodo in ast.walk(fn):
        if (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
                and len(nodo.value) == 3 and nodo.value[0].isalpha()
                and nodo.value[0].isupper() and nodo.value[1:].isdigit()):
            if nodo.value not in vistos:
                vistos.append(nodo.value)
    return vistos


def main() -> None:
    ap = argparse.ArgumentParser(description="Tablas de puntuacion de los 8 factores")
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()

    L = []

    def w(linea=""):
        print(linea)
        L.append(linea)

    w(D("sr_title"))
    w("")
    w(D("sr_intro1"))
    w("")
    w(D("sr_intro2"))
    w("")

    etiquetas = scoring.factor_labels()
    for key, peso in scoring.WEIGHTS.items():
        label = etiquetas.get(key, key)
        fn = FUNCTION[key]
        w("## %s" % label)
        w("")
        w(D("sr_weight_line")
          % (peso, fn, ", ".join("`%s`" % c for c in codes_of(fn)) or D("sr_none")))
        w("")
        tablas = tables_of(fn)
        if tablas:
            for t in tablas:
                if len(tablas) > 1:
                    w(D("sr_according") % (t["code"] or "?"))
                    w("")
                w(D("sr_table_head"))
                w("|---|---|")
                for text, value in t["filas"]:
                    w("| %s | %s |" % (_answer_text(t["code"], text),
                                       ("%+g" % value) if value < 0 else "%g" % value))
                if t["defecto"] is not None:
                    w(D("sr_other") % t["defecto"])
                else:
                    w(D("sr_unknown"))
                w("")
        else:
            w(D("sr_no_table"))
            w("")
        w(D("sr_notes") % D("sr_note_%s" % key))
        w("")

    w("---")
    w("")
    w(D("sr_tail_title"))
    w("")
    w(D("sr_tail"))
    w("")

    if args.md:
        target = output_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(L) + "\n", encoding="utf-8")
        print("")
        print(D("sr_written") % target)


if __name__ == "__main__":
    main()
