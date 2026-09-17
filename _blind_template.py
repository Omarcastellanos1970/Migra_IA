"""Plantilla ciega para validacion por juicio experto, y su lectura posterior.

POR QUE EXISTE
--------------
El motor es determinista: las mismas respuestas dan siempre el mismo numero.
Eso es reproducibilidad, no acierto. Para saber si el resultado es razonable
hace falta contrastarlo con criterio humano, y el proyecto no dispone de casos
de campo con desenlace conocido.

Lo que si hay son los cinco casos de estudio de la guia MIGRA-IA-GUIA-001
(`data/es/knowledge_base.json`), que son EXTERNOS al motor: no los escribio el
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
    python _blind_template.py generate
        Escribe docs/plantilla_casos_ciegos.md (esto es lo que se envia) y
        _plantilla_clave.json (esto NO se envia: es el mapa caso -> id real).

    python _blind_template.py compare respuestas_ana.md respuestas_luis.md
        Lee las plantillas rellenadas y emite el informe de concordancia.
        Con --md lo escribe ademas en docs/concordancia_expertos.md
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import statistics
from pathlib import Path

from migra_ia import knowledge, interactive, scoring

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "docs" / "plantilla_casos_ciegos.md"
KEY = ROOT / "_plantilla_clave.json"
SEED_ENV = "MIGRA_SEMILLA_ORDEN"


def order_seed(given: int | None = None) -> int:
    """La semilla del barajado NO se guarda en el repositorio.

    Con ella se reproduce el orden de los casos y, por tanto, el mapa de cada
    caso ciego a su id en la guia: quien la tenga puede deshacer el ciego. Se
    toma de --semilla, del entorno o de la clave local, que esta en
    .gitignore; si no hay ninguna, se exige darla.
    """
    if given is not None:
        return int(given)
    del_entorno = os.environ.get(SEED_ENV)
    if del_entorno:
        return int(del_entorno)
    if KEY.exists():
        try:
            return int(json.loads(KEY.read_text(encoding="utf-8"))["semilla_orden"])
        except (KeyError, ValueError):
            pass
    raise SystemExit(
        "Falta la semilla del barajado. Pasa --semilla N o exporta %s. "
        "No se escribe aqui a proposito: quien la tenga deshace el ciego."
        % SEED_ENV)


ANSWER_LINE = re.compile(r"^\s*([A-Z][0-9]{2})\s*=\s*(.*?)\s*$")
CASE_HEADER = re.compile(r"^##\s+Caso\s+(\d+)\s*$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Generacion de la plantilla
# --------------------------------------------------------------------------- #
def blind_cases(seed: int):
    """Los 5 casos de la guia, barajados y despojados de lo que revela el final.

    Del caso solo sobrevive `situacion`. El titulo se recorta antes de los dos
    puntos porque la parte de la derecha nombra el destino ("S7-300 a S7-1500"),
    y `estrategia`, `riesgos` y `pruebas` se descartan enteros.
    """
    base = knowledge.load_base()
    cases = list(base["case_studies"])
    random.Random(seed).shuffle(cases)
    output = []
    for i, c in enumerate(cases, 1):
        context = c["title"].split(":")[0].strip()
        output.append({
            "n": i,
            "id_real": c["id"],
            "contexto": context,
            "situation": c["situation"],
        })
    return output


def question_block() -> list[str]:
    """Las preguntas del guion real del motor, con sus opciones numeradas."""
    L = []
    for code, condition in interactive.GUION:
        p = interactive._question(code)
        if p is None:
            continue
        note = ""
        if code in ("F06", "F07"):
            note = "   *(responda solo si F01 = Si)*"
        elif code in ("F12", "F13"):
            note = "   *(responda solo si F01 = No o No se conoce)*"
        L.append("**%s.** %s%s" % (code, p.get("text", ""), note))
        kind = p.get("type")
        options = p.get("options") or []
        if kind == "numero":
            L.append("  _escriba un numero_")
        elif not options:
            L.append("  _escriba su respuesta_")
        else:
            enum = "  ".join("%d) %s" % (i, op) for i, op in enumerate(options, 1))
            L.append("  " + enum)
            if kind == "seleccion_multiple":
                L.append("  _puede marcar varias, separadas por coma (ej. 1,3)_")
        L.append("")
        L.append("`%s = `" % code)
        L.append("")
    return L


def generate(given_seed: int | None = None) -> None:
    seed = order_seed(given_seed)
    cases = blind_cases(seed)
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
    questions = question_block()
    for c in cases:
        L += [
            "## Caso %d" % c["n"],
            "",
            "**Contexto:** %s" % c["contexto"],
            "",
            "**Situacion:** %s" % c["situation"],
            "",
            "### Cuestionario - Caso %d" % c["n"],
            "",
        ]
        L += questions
        L += ["---", ""]

    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE.write_text("\n".join(L), encoding="utf-8")

    KEY.write_text(json.dumps(
        {"semilla_orden": seed,
         "note": "NO enviar este archivo a los coautores: mapea cada caso ciego "
                 "a su id en la guia, que revela el desenlace.",
         "mapa": {str(c["n"]): c["id_real"] for c in cases}},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("Plantilla   : %s" % TEMPLATE)
    print("Clave local : %s   (NO enviar)" % KEY)
    print("")
    print("Casos incluidos, en el orden barajado:")
    for c in cases:
        print("  Caso %d  <- guia %s  (%s)" % (c["n"], c["id_real"], c["contexto"]))
    print("")
    print("Se ocultan: titulo completo, estrategia, riesgos y pruebas de cada caso.")


# --------------------------------------------------------------------------- #
# Lectura de plantillas rellenadas
# --------------------------------------------------------------------------- #
def read_template(path: Path):
    """Devuelve {n_caso: {codigo: valor_resuelto}} a partir de un archivo lleno."""
    text = path.read_text(encoding="utf-8", errors="replace")
    cases: dict[int, dict] = {}
    actual = None
    for linea in text.splitlines():
        m = CASE_HEADER.match(linea.strip())
        if m:
            actual = int(m.group(1))
            cases.setdefault(actual, {})
            continue
        if actual is None:
            continue
        cuerpo = linea.strip().strip("`").strip()
        m = ANSWER_LINE.match(cuerpo)
        if not m:
            continue
        code, crudo = m.group(1), m.group(2).strip()
        if not crudo:
            continue  # sin responder
        p = interactive._question(code)
        if p is None:
            continue
        value = interactive._interpret(p, crudo)
        if value is None:
            # No se adivina: la respuesta se descarta y queda como no contestada,
            # que es justo lo que el motor sabe tratar como dato faltante.
            n_ops = len(p.get("options") or [])
            rango = ("1 a %d" % n_ops) if n_ops else "texto libre"
            print("  aviso: %s, caso %d, %s = %r no es valido (opciones: %s). "
                  "Queda sin responder." % (path.name, actual, code, crudo, rango))
            continue
        cases[actual][code] = value
    return cases


def evaluate(answers: dict):
    """Puntuacion, clasificacion, ruta y decision del motor para esas respuestas."""
    calculados, omitidos = interactive.factors(answers)
    r = scoring.compute_risk(calculados)
    d = interactive.decide(answers, {"puntuacion": r.score,
                                         "classification": r.classification})
    return {
        "puntuacion": r.score,
        "classification": r.classification,
        "migrar": bool(d["migrar"]),
        "route": [a["alternative"] for a in d["route"]],
        "omitidos": omitidos,
        "respondidas": len(answers),
    }


def compare(rutas: list[Path], write_md: bool) -> None:
    if not rutas:
        raise SystemExit("Indique al menos un archivo de respuestas.")
    key = json.loads(KEY.read_text(encoding="utf-8"))["mapa"] if KEY.exists() else {}

    L = []

    def w(linea=""):
        print(linea)
        L.append(linea)

    lecturas = {}
    for path in rutas:
        if not path.exists():
            raise SystemExit("No existe: %s" % path)
        lecturas[path.stem] = read_template(path)

    w("=" * 74)
    w("CONCORDANCIA ENTRE EXPERTOS - MIGRA-IA")
    w("=" * 74)
    w("Participantes: %s" % ", ".join(lecturas))
    w("")

    numeros = sorted({n for c in lecturas.values() for n in c})
    agreement_summary = []

    for n in numeros:
        w("CASO %d%s" % (n, "   (guia %s)" % key.get(str(n), "?") if key else ""))
        w("-" * 74)
        evals = {}
        for quien, cases in lecturas.items():
            resp = cases.get(n)
            if not resp:
                w("  %-14s sin responder" % quien)
                continue
            e = evaluate(resp)
            evals[quien] = e
            w("  %-14s %5.1f  %-18s migrar=%-5s  respondidas=%d  omitidos=%d"
              % (quien, e["puntuacion"], e["classification"], e["migrar"],
                 e["respondidas"], len(e["omitidos"])))
            w("  %-14s ruta: %s" % ("", " > ".join(e["route"]) or "(vacia)"))
        if len(evals) >= 2:
            puntos = [e["puntuacion"] for e in evals.values()]
            clases = {e["classification"] for e in evals.values()}
            migrars = {e["migrar"] for e in evals.values()}
            rutas_d = {tuple(e["route"]) for e in evals.values()}
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
            agreement_summary.append({
                "case": n, "amplitud": max(puntos) - min(puntos),
                "clase_unanime": len(clases) == 1,
                "decision_unanime": len(migrars) == 1,
                "ruta_unanime": len(rutas_d) == 1,
                "migrar_todos": all(e["migrar"] for e in evals.values()),
            })
        w("")

    if agreement_summary:
        w("=" * 74)
        w("RESUMEN")
        w("=" * 74)
        tot = len(agreement_summary)
        w("  A. Concordancia entre expertos (lo que discrimina)")
        w("     clasificacion unanime : %d de %d casos"
          % (sum(r["clase_unanime"] for r in agreement_summary), tot))
        w("     decision unanime      : %d de %d casos"
          % (sum(r["decision_unanime"] for r in agreement_summary), tot))
        w("     ruta unanime          : %d de %d casos"
          % (sum(r["ruta_unanime"] for r in agreement_summary), tot))
        w("     amplitud media de puntuacion: %.1f puntos"
          % statistics.mean(r["amplitud"] for r in agreement_summary))
        w("")
        w("  B. Concordancia con el desenlace documentado (los 5 casos migraron)")
        w("     el motor propone migrar para todos los expertos: %d de %d casos"
          % (sum(r["migrar_todos"] for r in agreement_summary), tot))
        w("     AVISO: los 5 casos comparten desenlace, asi que B no discrimina.")
        w("     Un motor que dijera 'migrar' siempre sacaria el mismo resultado.")
        w("")

    if write_md:
        target = ROOT / "docs" / "concordancia_expertos.md"
        target.write_text(
            "# Concordancia entre expertos - MIGRA-IA\n\n"
            "Generado por `_plantilla_ciega.py comparar`.\n\n"
            "```\n" + "\n".join(L) + "\n```\n", encoding="utf-8")
        print("Informe escrito en %s" % target)


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Plantilla ciega de validacion experta")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="escribe la plantilla en blanco")
    g.add_argument("--seed", type=int, default=None,
                   help="semilla del barajado; si falta se busca en %s "
                        "o en la clave local" % SEED_ENV)
    c = sub.add_parser("compare", help="lee plantillas rellenadas y mide concordancia")
    c.add_argument("files", nargs="+", type=Path)
    c.add_argument("--md", action="store_true")
    args = ap.parse_args()

    if args.cmd == "generate":
        generate(args.seed)
    else:
        compare(args.files, args.md)


if __name__ == "__main__":
    main()
