"""Contrasta las caracteristicas de dominio que pide el rubro con las que el
proyecto realmente define, alimenta y usa.

Casilla 3 del entregable: "las caracteristicas de dominio definidas y
justificadas, o la decision de ir con el dato crudo documentada".

El documento se genera leyendo el cuestionario y las tablas de puntuacion que a
su vez se extraen del codigo, de modo que no pueda divergir del motor: si
manana un factor deja de leer un codigo, este documento lo dice en la siguiente
corrida.

    python _caracteristicas.py          # resumen en pantalla
    python _caracteristicas.py --md     # escribe docs/caracteristicas_dominio.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CUESTIONARIO = RAIZ / "data" / "cuestionario.json"
REGLAS = RAIZ / "docs" / "reglas_de_puntuacion.md"
SALIDA = RAIZ / "docs" / "caracteristicas_dominio.md"

# Lo que el rubro nombra como caracteristicas candidatas del rubro, y el codigo del
# cuestionario que las recoge. Escrito a mano porque es la correspondencia entre
# dos vocabularios: el del rubro y el del proyecto.
CANDIDATAS = [
    ("Anos desde lanzamiento", ["C05", "D07"],
     "Ano de fabricacion y de instalacion. Esta en la placa del equipo y es "
     "anterior a cualquier evento de fin de vida, asi que no puede contaminarse "
     "con la etiqueta."),
    ("Fin de soporte", ["M03", "M02"],
     "Ano de fin de soporte y de fin de venta declarados por el fabricante. "
     "Ambos opcionales en el cuestionario: se piden 'si se conoce'."),
    ("Estado en el catalogo del fabricante", ["M01"],
     "La que el dominio manda: es la variable que un gerente de planta ya usa "
     "para decidir."),
    ("Repuestos", ["M04", "M05", "M06"],
     "Disponibilidad de repuesto nuevo, de mercado secundario y plazo de entrega."),
    ("Protocolo", ["G01"],
     "Redes que utiliza la maquina. Determina cuanto arrastra el cambio."),
    ("Criticidad", ["C08", "C10", "Q01"],
     "Criticidad de la maquina, parada tolerable y coste de hora parada."),
]


def codigos_usados() -> dict[str, tuple[list[str], str]]:
    """Factor -> codigos que lee, extraido del documento que genera el codigo."""
    texto = REGLAS.read_text(encoding="utf-8")
    factores: dict[str, list[str]] = {}
    actual = None
    for linea in texto.splitlines():
        m = re.match(r"^## (.+)$", linea)
        if m:
            actual = m.group(1).strip()
        m = re.search(r"lee: (.+)$", linea)
        if m and actual:
            peso = re.search(r"Peso ([\d.]+)", linea)
            factores[actual] = (re.findall(r"[A-Q]\d{2}", m.group(1)),
                                peso.group(1) if peso else "?")
    return factores


def preguntas() -> dict[str, str]:
    d = json.loads(CUESTIONARIO.read_text(encoding="utf-8"))
    fuera: dict[str, str] = {}

    def rec(o):
        if isinstance(o, dict):
            if "codigo" in o and "texto" in o:
                fuera[o["codigo"]] = o["texto"]
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(d)
    return fuera


def informe() -> str:
    factores = codigos_usados()
    usados = {c for cs, _ in factores.values() for c in cs}
    textos = preguntas()

    L: list[str] = []
    a = L.append
    a("# Caracteristicas de dominio - el rubro")
    a("")
    a("Generado por `_caracteristicas.py` leyendo `data/cuestionario.json` y")
    a("`docs/reglas_de_puntuacion.md`, que a su vez se extrae del arbol sintactico")
    a("del motor. Si un factor deja de leer un codigo, este documento cambia solo.")
    a("")
    a("Casilla 3 del entregable. La decision esta tomada y es esta: **no se va con")
    a("el dato crudo**. El proyecto define caracteristicas de dominio -conocimiento")
    a("de ingenieria convertido en numero- y las pondera; lo que sigue dice cuales,")
    a("con que peso, y cuales se recogen y no se usan.")
    a("")
    a("## Las candidatas del rubro, contra lo que el motor hace")
    a("")
    a("| Caracteristica | Codigos | Estado |")
    a("|---|---|---|")
    huerfanas: list[tuple[str, list[str]]] = []
    for nombre, codigos, _ in CANDIDATAS:
        dentro = [c for c in codigos if c in usados]
        fuera = [c for c in codigos if c not in usados and c in textos]
        if dentro:
            estado = f"**Usada** por el motor ({', '.join(dentro)})"
            if fuera:
                estado += f"; {', '.join(fuera)} se preguntan y no se usan"
                huerfanas.append((nombre, fuera))
        else:
            estado = f"**Se pregunta y NO se usa** ({', '.join(fuera)})"
            huerfanas.append((nombre, fuera))
        a(f"| {nombre} | {', '.join(codigos)} | {estado} |")
    a("")
    for nombre, codigos, justificacion in CANDIDATAS:
        a(f"**{nombre}.** {justificacion}")
        a("")

    a("## Los ocho factores del motor y lo que leen")
    a("")
    a("Estos son los que estan implementados y ponderados. Los pesos son los de la")
    a("Seccion 6 del paper y no se tocan sin actualizarlo.")
    a("")
    a("| Factor | Peso | Codigos que lee |")
    a("|---|---|---|")
    for factor, (cs, peso) in factores.items():
        a(f"| {factor} | {peso} | {', '.join(cs)} |")
    a("")

    a("## Huecos: lo que se recoge y se tira")
    a("")
    if huerfanas:
        a("El cuestionario pide estos datos al tecnico, los guarda en el expediente")
        a("y **ningun factor los lee**. Es la misma clase de defecto que F12, pero")
        a("sobre las dos caracteristicas que el rubro nombra primero:")
        a("")
        for nombre, codigos in huerfanas:
            for c in codigos:
                a(f"- `{c}` — {textos.get(c, '(sin texto)')[:88]}  \\[{nombre}\\]")
        a("")
        a("Cerrarlo obliga a tocar `scoring.py`, cuyos ocho factores y pesos son los")
        a("que describe el paper. Es decision editorial, no tecnica, y esta anotada")
        a("como tal.")
    else:
        a("Ninguno: todas las candidatas del rubro alimentan algun factor.")
    a("")

    a("## En la tabla de ciclo de vida solo sobrevive una")
    a("")
    a("Lo anterior es el cuestionario, que es donde vive el conocimiento de dominio")
    a("del proyecto. El conjunto tabular con el que se entrena el baseline de P1 es")
    a("otro -`data/ciclo_vida_plataformas.csv`, nueve plataformas- y ahi la")
    a("auditoria de fuga deja **una sola variable admisible: la antiguedad**. No es")
    a("una eleccion de modelado: las demas columnas o definen la etiqueta o son")
    a("metadato del proceso de recoleccion. Ver la seccion 6 de")
    a("`docs/baseline_reproducible.md`.")
    a("")
    a("De ahi que la ampliacion del conjunto sea la tarea que desbloquea el resto:")
    a("mientras la tabla tenga nueve filas y una variable, las caracteristicas de")
    a("dominio estan definidas pero no se pueden ejercitar.")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()
    texto = informe()
    print(texto)
    if args.md:
        SALIDA.write_text(texto + "\n", encoding="utf-8")
        print(f"\nEscrito {SALIDA.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
