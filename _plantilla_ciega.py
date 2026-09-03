"""Plantilla ciega para validacion por juicio experto, y su lectura posterior.

POR QUE EXISTE
--------------
El motor es determinista: las mismas respuestas dan siempre el mismo numero.
Eso es reproducibilidad, no acierto. Para saber si el resultado es razonable
hace falta contrastarlo con criterio humano, y el proyecto no dispone de casos
de campo con desenlace conocido.

Lo que si hay son los cinco casos de estudio de la guia MIGRA-IA-GUIA-001
(`data/base_conocimiento.json`), que son EXTERNOS al motor: no los escribio el
autor del codigo. Este script los presenta a los coautores **en ciego**:

  - se les da la situacion del equipo,
  - se les OCULTA el titulo (que nombra el destino), la estrategia seguida,
    los riesgos y las pruebas del caso,
  - se les oculta cualquier salida del motor,
  - y se les pide que respondan el mismo cuestionario que responde el agente.

Despues, `comparar` alimenta el motor con las respuestas de cada coautor y mide
dos cosas distintas:

  A. CONCORDANCIA ENTRE EXPERTOS. Si dos especialistas leen el mismo caso y sus
     respuestas llevan al motor a conclusiones distintas, el problema no es el
     motor: es que el cuestionario admite lecturas distintas. Ese es el
     resultado con mas valor cientifico de todo el ejercicio.

  B. CONCORDANCIA CON EL DESENLACE DOCUMENTADO. Los cinco casos de la guia
     terminaron en migracion. Se comprueba si el motor, alimentado con las
     respuestas de cada experto, tambien la propone.

LIMITACION QUE HAY QUE DECLARAR EN EL PAPER
-------------------------------------------
Los cinco casos terminan en el mismo desenlace, asi que B por si sola no
discrimina: un motor que dijera "migrar" siempre acertaria las cinco veces. B
solo sirve como comprobacion de que no falla en lo evidente. El resultado que
si discrimina es A.

USO
---
    python _plantilla_ciega.py generar
        Escribe docs/plantilla_casos_ciegos.md (esto es lo que se envia) y
        _plantilla_clave.json (esto NO se envia: es el mapa caso -> id real).

    python _plantilla_ciega.py comparar respuestas_ana.md respuestas_luis.md
        Lee las plantillas rellenadas y emite el informe de concordancia.
        Con --md lo escribe ademas en docs/concordancia_expertos.md
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from pathlib import Path

from migra_ia import conocimiento, interactivo, scoring

RAIZ = Path(__file__).resolve().parent
PLANTILLA = RAIZ / "docs" / "plantilla_casos_ciegos.md"
CLAVE = RAIZ / "_plantilla_clave.json"
SEMILLA_ORDEN = 20260902

LINEA_RESPUESTA = re.compile(r"^\s*([A-Z][0-9]{2})\s*=\s*(.*?)\s*$")
CABECERA_CASO = re.compile(r"^##\s+Caso\s+(\d+)\s*$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Generacion de la plantilla
# --------------------------------------------------------------------------- #
def casos_ciegos():
    """Los 5 casos de la guia, barajados y despojados de lo que revela el final.

    Del caso solo sobrevive `situacion`. El titulo se recorta antes de los dos
    puntos porque la parte de la derecha nombra el destino ("S7-300 a S7-1500"),
    y `estrategia`, `riesgos` y `pruebas` se descartan enteros.
    """
    base = conocimiento.cargar_base()
    casos = list(base["casos_estudio"])
    random.Random(SEMILLA_ORDEN).shuffle(casos)
    salida = []
    for i, c in enumerate(casos, 1):
        contexto = c["titulo"].split(":")[0].strip()
        salida.append({
            "n": i,
            "id_real": c["id"],
            "contexto": contexto,
            "situacion": c["situacion"],
        })
    return salida


def bloque_preguntas() -> list[str]:
    """Las preguntas del guion real del motor, con sus opciones numeradas."""
    L = []
    for codigo, condicion in interactivo.GUION:
        p = interactivo._pregunta(codigo)
        if p is None:
            continue
        nota = ""
        if codigo in ("F06", "F07"):
            nota = "   *(responda solo si F01 = Si)*"
        elif codigo in ("F12", "F13"):
            nota = "   *(responda solo si F01 = No o No se conoce)*"
        L.append("**%s.** %s%s" % (codigo, p.get("texto", ""), nota))
        tipo = p.get("tipo")
        opciones = p.get("opciones") or []
        if tipo == "numero":
            L.append("  _escriba un numero_")
        elif not opciones:
            L.append("  _escriba su respuesta_")
        else:
            enum = "  ".join("%d) %s" % (i, op) for i, op in enumerate(opciones, 1))
            L.append("  " + enum)
            if tipo == "seleccion_multiple":
                L.append("  _puede marcar varias, separadas por coma (ej. 1,3)_")
        L.append("")
        L.append("`%s = `" % codigo)
        L.append("")
    return L


def generar() -> None:
    casos = casos_ciegos()
    L = [
        "# MIGRA-IA - Valoracion ciega de casos",
        "",
        "Gracias por ayudar con esto. Son cinco casos y toma alrededor de una hora.",
        "",
        "## Que se le pide",
        "",
        "Lea la situacion de cada caso y responda el cuestionario **con su propio",
        "criterio profesional**, como lo haria ante ese equipo en planta.",
        "",
        "## Tres reglas que hacen valido el ejercicio",
        "",
        "1. **No ejecute el agente MIGRA-IA antes de terminar.** El objetivo es",
        "   comparar su criterio contra el del programa; si ve la salida primero,",
        "   el resultado ya no mide nada.",
        "2. **No consulte con los demas coautores hasta entregar.** Lo que se mide",
        "   es cuanto coinciden ustedes de forma independiente.",
        "3. **Si un dato no se puede saber con lo que dice el caso, respondalo como",
        "   'No se conoce'.** No lo adivine. Que falte informacion es un resultado",
        "   valido y el motor lo trata como tal.",
        "",
        "## Como responder",
        "",
        "Escriba el **numero** de la opcion despues del `=`, dentro de las comillas",
        "invertidas. Por ejemplo: `` `M01 = 4` ``. Tambien puede escribir el texto",
        "completo de la opcion si lo prefiere.",
        "",
        "Guarde el archivo como `respuestas_SUNOMBRE.md` y devuelvalo.",
        "",
        "---",
        "",
    ]
    preguntas = bloque_preguntas()
    for c in casos:
        L += [
            "## Caso %d" % c["n"],
            "",
            "**Contexto:** %s" % c["contexto"],
            "",
            "**Situacion:** %s" % c["situacion"],
            "",
            "### Cuestionario - Caso %d" % c["n"],
            "",
        ]
        L += preguntas
        L += ["---", ""]

    PLANTILLA.parent.mkdir(parents=True, exist_ok=True)
    PLANTILLA.write_text("\n".join(L), encoding="utf-8")

    CLAVE.write_text(json.dumps(
        {"semilla_orden": SEMILLA_ORDEN,
         "nota": "NO enviar este archivo a los coautores: mapea cada caso ciego "
                 "a su id en la guia, que revela el desenlace.",
         "mapa": {str(c["n"]): c["id_real"] for c in casos}},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("Plantilla   : %s" % PLANTILLA)
    print("Clave local : %s   (NO enviar)" % CLAVE)
    print("")
    print("Casos incluidos, en el orden barajado:")
    for c in casos:
        print("  Caso %d  <- guia %s  (%s)" % (c["n"], c["id_real"], c["contexto"]))
    print("")
    print("Se ocultan: titulo completo, estrategia, riesgos y pruebas de cada caso.")


# --------------------------------------------------------------------------- #
# Lectura de plantillas rellenadas
# --------------------------------------------------------------------------- #
def leer_plantilla(ruta: Path):
    """Devuelve {n_caso: {codigo: valor_resuelto}} a partir de un archivo lleno."""
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    casos: dict[int, dict] = {}
    actual = None
    for linea in texto.splitlines():
        m = CABECERA_CASO.match(linea.strip())
        if m:
            actual = int(m.group(1))
            casos.setdefault(actual, {})
            continue
        if actual is None:
            continue
        cuerpo = linea.strip().strip("`").strip()
        m = LINEA_RESPUESTA.match(cuerpo)
        if not m:
            continue
        codigo, crudo = m.group(1), m.group(2).strip()
        if not crudo:
            continue  # sin responder
        p = interactivo._pregunta(codigo)
        if p is None:
            continue
        valor = interactivo._interpretar(p, crudo)
        if valor is None:
            # No se adivina: la respuesta se descarta y queda como no contestada,
            # que es justo lo que el motor sabe tratar como dato faltante.
            n_ops = len(p.get("opciones") or [])
            rango = ("1 a %d" % n_ops) if n_ops else "texto libre"
            print("  aviso: %s, caso %d, %s = %r no es valido (opciones: %s). "
                  "Queda sin responder." % (ruta.name, actual, codigo, crudo, rango))
            continue
        casos[actual][codigo] = valor
    return casos


def evaluar(respuestas: dict):
    """Puntuacion, clasificacion, ruta y decision del motor para esas respuestas."""
    calculados, omitidos = interactivo.factores(respuestas)
    r = scoring.calcular_riesgo(calculados)
    d = interactivo.decidir(respuestas, {"puntuacion": r.puntuacion,
                                         "clasificacion": r.clasificacion})
    return {
        "puntuacion": r.puntuacion,
        "clasificacion": r.clasificacion,
        "migrar": bool(d["migrar"]),
        "ruta": [a["alternativa"] for a in d["ruta"]],
        "omitidos": omitidos,
        "respondidas": len(respuestas),
    }


def comparar(rutas: list[Path], escribir_md: bool) -> None:
    if not rutas:
        raise SystemExit("Indique al menos un archivo de respuestas.")
    clave = json.loads(CLAVE.read_text(encoding="utf-8"))["mapa"] if CLAVE.exists() else {}

    L = []

    def w(linea=""):
        print(linea)
        L.append(linea)

    lecturas = {}
    for ruta in rutas:
        if not ruta.exists():
            raise SystemExit("No existe: %s" % ruta)
        lecturas[ruta.stem] = leer_plantilla(ruta)

    w("=" * 74)
    w("CONCORDANCIA ENTRE EXPERTOS - MIGRA-IA")
    w("=" * 74)
    w("Participantes: %s" % ", ".join(lecturas))
    w("")

    numeros = sorted({n for c in lecturas.values() for n in c})
    resumen_acuerdo = []

    for n in numeros:
        w("CASO %d%s" % (n, "   (guia %s)" % clave.get(str(n), "?") if clave else ""))
        w("-" * 74)
        evals = {}
        for quien, casos in lecturas.items():
            resp = casos.get(n)
            if not resp:
                w("  %-14s sin responder" % quien)
                continue
            e = evaluar(resp)
            evals[quien] = e
            w("  %-14s %5.1f  %-18s migrar=%-5s  respondidas=%d  omitidos=%d"
              % (quien, e["puntuacion"], e["clasificacion"], e["migrar"],
                 e["respondidas"], len(e["omitidos"])))
            w("  %-14s ruta: %s" % ("", " > ".join(e["ruta"]) or "(vacia)"))
        if len(evals) >= 2:
            puntos = [e["puntuacion"] for e in evals.values()]
            clases = {e["clasificacion"] for e in evals.values()}
            migrars = {e["migrar"] for e in evals.values()}
            rutas_d = {tuple(e["ruta"]) for e in evals.values()}
            w("")
            w("  dispersion   : %.1f .. %.1f  (amplitud %.1f, sd %.2f)"
              % (min(puntos), max(puntos), max(puntos) - min(puntos),
                 statistics.pstdev(puntos)))
            w("  clasificacion: %s" % ("UNANIME (%s)" % list(clases)[0]
                                       if len(clases) == 1
                                       else "DISCREPA -> " + ", ".join(sorted(clases))))
            w("  decision     : %s" % ("UNANIME (migrar=%s)" % list(migrars)[0]
                                       if len(migrars) == 1
                                       else "DISCREPA"))
            w("  ruta         : %s" % ("unanime" if len(rutas_d) == 1
                                       else "%d rutas distintas" % len(rutas_d)))
            resumen_acuerdo.append({
                "caso": n, "amplitud": max(puntos) - min(puntos),
                "clase_unanime": len(clases) == 1,
                "decision_unanime": len(migrars) == 1,
                "ruta_unanime": len(rutas_d) == 1,
                "migrar_todos": all(e["migrar"] for e in evals.values()),
            })
        w("")

    if resumen_acuerdo:
        w("=" * 74)
        w("RESUMEN")
        w("=" * 74)
        tot = len(resumen_acuerdo)
        w("  A. Concordancia entre expertos (lo que discrimina)")
        w("     clasificacion unanime : %d de %d casos"
          % (sum(r["clase_unanime"] for r in resumen_acuerdo), tot))
        w("     decision unanime      : %d de %d casos"
          % (sum(r["decision_unanime"] for r in resumen_acuerdo), tot))
        w("     ruta unanime          : %d de %d casos"
          % (sum(r["ruta_unanime"] for r in resumen_acuerdo), tot))
        w("     amplitud media de puntuacion: %.1f puntos"
          % statistics.mean(r["amplitud"] for r in resumen_acuerdo))
        w("")
        w("  B. Concordancia con el desenlace documentado (los 5 casos migraron)")
        w("     el motor propone migrar para todos los expertos: %d de %d casos"
          % (sum(r["migrar_todos"] for r in resumen_acuerdo), tot))
        w("     AVISO: los 5 casos comparten desenlace, asi que B no discrimina.")
        w("     Un motor que dijera 'migrar' siempre sacaria el mismo resultado.")
        w("")

    if escribir_md:
        destino = RAIZ / "docs" / "concordancia_expertos.md"
        destino.write_text(
            "# Concordancia entre expertos - MIGRA-IA\n\n"
            "Generado por `_plantilla_ciega.py comparar`.\n\n"
            "```\n" + "\n".join(L) + "\n```\n", encoding="utf-8")
        print("Informe escrito en %s" % destino)


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Plantilla ciega de validacion experta")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generar", help="escribe la plantilla en blanco")
    c = sub.add_parser("comparar", help="lee plantillas rellenadas y mide concordancia")
    c.add_argument("archivos", nargs="+", type=Path)
    c.add_argument("--md", action="store_true")
    args = ap.parse_args()

    if args.cmd == "generar":
        generar()
    else:
        comparar(args.archivos, args.md)


if __name__ == "__main__":
    main()
