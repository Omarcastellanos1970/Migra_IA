"""Verificacion interna del motor de riesgo: baselines, sensibilidad e influencia.

No necesita clave de API ni casos de campo: todo lo que se mide sale del propio
motor determinista, asi que el informe es reproducible en cualquier maquina.

Uso:
    python _evaluation.py                  # informe en pantalla
    python _evaluation.py --md             # ademas escribe el documento del idioma
    python _evaluation.py --samples 20000 --seed 7

Que mide, y por que:

  1. BASELINES. La propuesta (8 factores con los pesos de la Seccion 6) no
     significa nada sin algo con que compararla. Se construyen dos:
       B0  regla trivial: un solo dato (M01, estado de ciclo de vida).
       B1  los mismos 8 factores con pesos uniformes (0.125 cada uno).
     Si B1 reproduce a la propuesta, los pesos elegidos a mano no aportan y
     hay que decirlo.

  2. SENSIBILIDAD DE LOS PESOS. Perturbacion de un peso a la vez (+-20%, +-50%)
     y Monte Carlo sobre los ocho a la vez. Responde a la pregunta obvia de un
     revisor: "y si los pesos fueran otros?".

  3. INFLUENCIA POR PREGUNTA. Barrido de todas las opciones documentadas de
     cada pregunta, una a la vez, para ver cuanto mueve la puntuacion.

  4. INFLUENCIA SOBRE LA RUTA. El mismo barrido, pero mirando si cambia la
     alternativa recomendada. Una pregunta puede no mover el numero y aun asi
     cambiar la recomendacion, o al reves; separar las dos cosas evita dar por
     inutil una pregunta que si trabaja.

  5. MONOTONIA. Sobre las escalas ordinales que el propio motor declara: al
     empeorar una respuesta el riesgo no deberia bajar.

  6. MARGEN AL UMBRAL. Cuanto puede moverse cada escenario antes de cambiar de
     clasificacion (umbrales 20/40/60/80).

  7. RELACION PUNTUACION / DECISION. Se fuerza la puntuacion a los extremos
     dejando las respuestas intactas, para ver si la recomendacion depende
     realmente del numero que se le presenta al usuario.

Ninguna de estas medidas sustituye a la validacion de campo, que sigue
pendiente por falta de casos reales. Esto es VERIFICACION, no VALIDACION: dice
que el motor se comporta como su diseno declara, no que su diseno acierte.
"""
from __future__ import annotations

import argparse
import random
import statistics
from contextlib import contextmanager
from pathlib import Path

from migra_ia import config, interactive, questionnaire, scoring
import _interactive_run as run
from _interactive_run import ESCENARIOS

ROOT = Path(__file__).resolve().parent
UMBRALES = [20, 40, 60, 80]


def D(key: str) -> str:
    """Texto del informe en el idioma de esta ejecucion."""
    return config.doc_tools().get(key, key)


def output_path() -> Path:
    return ROOT / D("ev_path")


def L10N(clas: str) -> str:
    """La clasificacion, para MOSTRARLA. Lo que se compara sigue siendo canonico."""
    return scoring.risk_label(clas)

# Valores de referencia publicados en ARTIFACT.md. Si el motor deja de
# producirlos, el informe se detiene en vez de publicar cifras que no cuadran.
ESPERADO = {"critical": 85.0, "healthy": 11.8}


# --------------------------------------------------------------------------- #
# Resolucion de escenarios: de lo que el usuario escribe al dict que ve el motor
# --------------------------------------------------------------------------- #
def resolve(esc: dict) -> dict:
    """Traduce las entradas del escenario al dict de respuestas del motor.

    Reutiliza `_interpretar` del propio modulo interactivo, de modo que no hay
    una segunda interpretacion que pueda divergir de la real.
    """
    resueltas: dict = {}
    for code, text in esc["answers"].items():
        p = interactive._question(code)
        if p is None:
            raise SystemExit(D("ev_bad_code") % code)
        # El escenario se escribe con las opciones canonicas; aqui se dice en el
        # idioma de la sesion, igual que en el recorrido headless.
        value = interactive._interpret(p, run._dicho_en_el_idioma(code, text))
        if value is None:
            raise SystemExit(D("ev_bad_answer") % (code, repr(text)))
        resueltas[code] = value
    return resueltas


@contextmanager
def weights(nuevos):
    """Ejecuta el bloque con otro juego de pesos y restaura los originales."""
    if nuevos is None:
        yield
        return
    originales = scoring.WEIGHTS
    scoring.WEIGHTS = nuevos
    try:
        yield
    finally:
        scoring.WEIGHTS = originales


def score(answers: dict, w=None):
    """Puntuacion, clasificacion y factores omitidos, con los pesos indicados."""
    with weights(w):
        calculados, omitidos = interactive.factors(answers)
        r = scoring.compute_risk(calculados)
    return r.score, r.classification, omitidos


def migrate(answers: dict, punt: float, clas: str) -> bool:
    """Decision del mapa de decision para este caso."""
    d = interactive.decide(answers, {"puntuacion": punt, "classification": clas})
    return bool(d["migrar"])


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
PESOS_UNIFORMES = {k: 1.0 / len(scoring.WEIGHTS) for k in scoring.WEIGHTS}

# B0: la regla que se le ocurre a cualquiera en cinco minutos. Un solo dato.
_M01_MIGRATE = {"Descontinuado, aun con soporte y repuestos",
               "Descontinuado y sin soporte (fin de vida)"}


def trivial_baseline(answers: dict):
    """B0: solo mira M01. Puntuacion = valor del factor de ciclo de vida."""
    f = interactive._f_lifecycle(answers)
    punt = None if f is None else float(f["value"])
    # La comparacion va contra la opcion canonica, como en el motor.
    return punt, interactive._canon("M01", answers.get("M01")) in _M01_MIGRATE


# --------------------------------------------------------------------------- #
# Analisis
# --------------------------------------------------------------------------- #
def threshold_margin(punt: float):
    """Distancia al umbral de clasificacion mas cercano."""
    dist, u = min((abs(punt - u), u) for u in UMBRALES)
    return round(dist, 1), str(u)


def individual_sensitivity(answers: dict, base_clas: str):
    """Mueve un peso a la vez y observa si cambia la clasificacion."""
    filas = []
    for key in list(scoring.WEIGHTS):
        row = {"factor": key, "peso": scoring.WEIGHTS[key], "cambios": []}
        for pct in (-50, -20, 20, 50):
            w = dict(scoring.WEIGHTS)
            w[key] = max(0.0, w[key] * (1 + pct / 100))
            punt, clas, _ = score(answers, w)
            row["%+d%%" % pct] = punt
            if clas != base_clas:
                row["cambios"].append("%+d%% -> %s" % (pct, clas))
        filas.append(row)
    return filas


def montecarlo_sensitivity(answers: dict, base_clas: str,
                            samples: int, seed: int):
    """Perturba los ocho pesos a la vez, uniforme en [0.5, 1.5], y renormaliza."""
    rnd = random.Random(seed)
    puntos, estables = [], 0
    for _ in range(samples):
        w = {k: v * rnd.uniform(0.5, 1.5) for k, v in scoring.WEIGHTS.items()}
        total = sum(w.values())
        w = {k: v / total for k, v in w.items()}
        punt, clas, _ = score(answers, w)
        puntos.append(punt)
        if clas == base_clas:
            estables += 1
    return {
        "muestras": samples,
        "estabilidad": round(100.0 * estables / samples, 1),
        "min": round(min(puntos), 1),
        "max": round(max(puntos), 1),
        "mean": round(statistics.mean(puntos), 1),
        "desv": round(statistics.pstdev(puntos), 2),
    }


def influence_by_question(answers: dict):
    """Barre todas las opciones de cada pregunta y mide el rango que produce."""
    filas = []
    for code, actual in answers.items():
        p = interactive._question(code)
        options = (p or {}).get("options") or []
        if not options:
            continue
        vals = []
        for op in options:
            test = dict(answers)
            test[code] = [op] if p.get("type") == "seleccion_multiple" else op
            punt, _, _ = score(test)
            vals.append(punt)
        filas.append({
            "code": code,
            "text": (p or {}).get("text", ""),
            "actual": ", ".join(actual) if isinstance(actual, list) else actual,
            "min": min(vals), "max": max(vals),
            "rango": round(max(vals) - min(vals), 1),
        })
    return sorted(filas, key=lambda f: f["rango"], reverse=True)


# Escalas ordinales tomadas literalmente del motor (`interactivo.py`). La
# direccion dice hacia donde deberia moverse el riesgo al avanzar en la escala.
ORDINALES = [
    ("M01", ["Activo, en comercializacion",
             "En madurez, ya existe un sucesor",
             "Anuncio de descontinuacion (phase-out)",
             "Descontinuado, aun con soporte y repuestos",
             "Descontinuado y sin soporte (fin de vida)"], "sube"),
    ("M06", ["En existencia en la planta o local", "Menos de 2 semanas",
             "De 2 a 8 semanas", "Mas de 8 semanas", "No se consigue"], "sube"),
    ("C10", ["Menos de 1 hora", "1 a 4 horas", "4 a 12 horas",
             "12 a 24 horas", "Mas de 24 horas"], "baja"),
]


def decision_route(answers: dict):
    """Secuencia de alternativas que el mapa de decision propone para este caso."""
    punt, clas, _ = score(answers)
    d = interactive.decide(answers, {"puntuacion": punt, "classification": clas})
    return tuple(a["alternative"] for a in d["route"])


def decision_influence(answers: dict):
    """Codigos cuyo cambio de opcion altera la ruta del mapa de decision.

    Complementa el barrido de puntuacion: una pregunta puede no mover el numero
    y aun asi cambiar la recomendacion, o al reves.
    """
    mueven, inertes = [], []
    for code in answers:
        p = interactive._question(code)
        options = (p or {}).get("options") or []
        if not options:
            continue
        rutas, puntos = set(), set()
        for op in options:
            test = dict(answers)
            test[code] = [op] if p.get("type") == "seleccion_multiple" else op
            punt, _, _ = score(test)
            puntos.add(punt)
            rutas.add(decision_route(test))
        if len(rutas) > 1:
            mueven.append((code, len(rutas)))
        elif len(puntos) == 1:
            inertes.append(code)
    return mueven, inertes


def monotonicity(answers: dict):
    """Al empeorar una respuesta ordinal, el riesgo no deberia ir al reves."""
    filas = []
    for code, escala, direction in ORDINALES:
        p = interactive._question(code)
        documentadas = (questionnaire.question(code, config.CANONICAL_LANGUAGE)
                        or {}).get("options") or []
        faltan = [op for op in escala if op not in documentadas]
        serie, violations = [], []
        for op in escala:
            test = dict(answers)
            # La escala esta declarada en canonico; se dice en el idioma activo
            # para que el motor la lea igual que cualquier otra respuesta y para
            # que el documento la muestre en su lengua.
            test[code] = questionnaire.option_in(code, op)
            punt, _, _ = score(test)
            serie.append((questionnaire.option_in(code, op), punt))
        for (a, va), (b, vb) in zip(serie, serie[1:]):
            if direction == "sube" and vb < va - 1e-9:
                violations.append(D("ev_violation_down") % (a, va, b, vb))
            if direction == "baja" and vb > va + 1e-9:
                violations.append(D("ev_violation_up") % (a, va, b, vb))
        filas.append({"code": code, "direccion": direction, "serie": serie,
                      "violaciones": violations, "no_documentadas": faltan})
    return filas


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Verificacion interna del motor MIGRA-IA")
    ap.add_argument("--md", action="store_true",
                    help="escribe el documento del idioma activo")
    ap.add_argument("--samples", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cases = {n: resolve(e) for n, e in ESCENARIOS.items()}
    L = []

    def w(linea=""):
        print(linea)
        L.append(linea)

    w("=" * 74)
    w(D("ev_title"))
    w("=" * 74)
    w(D("ev_subtitle"))
    w("")

    # --- 0. Anclaje contra las cifras publicadas -------------------------- #
    w(D("ev_s0"))
    w("-" * 74)
    for name, esperado in ESPERADO.items():
        punt, clas, _ = score(cases[name])
        ok = abs(punt - esperado) < 1e-9
        w(D("ev_anchor_line")
          % (D("ev_anchor_ok") if ok else D("ev_anchor_bad"),
             name, punt, esperado, L10N(clas)))
        if not ok:
            raise SystemExit(D("ev_anchor_abort"))
    w("")

    # --- 1. Baselines ----------------------------------------------------- #
    w(D("ev_s1"))
    w("-" * 74)
    w(D("ev_s1_warn"))
    w("")
    w(D("ev_s1_head") % (D("ev_col_case"), D("ev_col_b0"),
                         D("ev_col_b1"), D("ev_col_prop")))
    tabla_base = []
    for name, resp in cases.items():
        p_prop, c_prop, _ = score(resp)
        p_uni, c_uni, _ = score(resp, PESOS_UNIFORMES)
        p_triv, m_triv = trivial_baseline(resp)
        m_prop = migrate(resp, p_prop, c_prop)
        tabla_base.append({"case": name, "b1": p_uni, "prop": p_prop})
        d = (D("ev_migrate") if m_prop else D("ev_no_migrate"))
        if m_triv != m_prop:
            d += D("ev_b0_says") % (D("ev_migrate") if m_triv else D("ev_no_migrate"))
        w("  %-12s %12s %13.1f %11.1f   %s" % (name, p_triv, p_uni, p_prop, d))
    w("")
    dif = [f for f in tabla_base if abs(f["b1"] - f["prop"]) >= 0.05]
    if dif:
        w(D("ev_weights_matter")
          % ", ".join("%s (%s vs %s)" % (f["case"], f["b1"], f["prop"]) for f in dif))
    else:
        w(D("ev_weights_flat"))
    w("")

    # --- 2. Sensibilidad -------------------------------------------------- #
    w(D("ev_s2"))
    w("-" * 74)
    for name, resp in cases.items():
        if name == "other_brand":
            continue  # identico a 'critical' en puntuacion; solo cambia el destino
        p_base, c_base, _ = score(resp)
        w(D("ev_base_line") % (name, p_base, L10N(c_base)))
        for row in individual_sensitivity(resp, c_base):
            brand = D("ev_class_change") if row["cambios"] else ""
            w(D("ev_sens_line")
              % (row["factor"], row["peso"], row["-50%"], row["-20%"],
                 row["+20%"], row["+50%"], brand))
        m = montecarlo_sensitivity(resp, c_base, args.samples, args.seed)
        w(D("ev_mc_line") % m["muestras"])
        w(D("ev_mc_range") % (m["min"], m["max"], m["mean"], m["desv"]))
        w(D("ev_mc_stable") % m["estabilidad"])
        w("")

    # --- 3. Influencia ---------------------------------------------------- #
    w(D("ev_s3"))
    w("-" * 74)
    infl = influence_by_question(cases["critical"])
    w(D("ev_s3_head") % (D("ev_col_code"), D("ev_col_range"),
                         D("ev_col_min"), D("ev_col_max")))
    for f in infl[:12]:
        w("  %-5s %7.1f %7.1f %7.1f  %s" % (f["code"], f["rango"], f["min"],
                                            f["max"], f["text"][:42]))
    sin_efecto = [f["code"] for f in infl if f["rango"] == 0]
    if sin_efecto:
        w("")
        w(D("ev_no_effect") % ", ".join(sin_efecto))
        w(D("ev_no_effect_note"))
    w("")

    # --- 4. Influencia sobre la ruta de decision ------------------------- #
    w(D("ev_s4"))
    w("-" * 74)
    w(D("ev_s4_intro"))
    inert_per_case = {}
    for name, resp in cases.items():
        if name == "other_brand":
            continue
        mueven, inertes = decision_influence(resp)
        inert_per_case[name] = set(inertes)
        w(D("ev_route_base") % (name, " > ".join(decision_route(resp))))
        w(D("ev_route_change")
          % (", ".join(D("ev_routes_count") % m for m in mueven)
             if mueven else D("ev_none_f")))
        w(D("ev_route_inert")
          % (", ".join(inertes) if inertes else D("ev_none_f")))
    comunes = set.intersection(*inert_per_case.values()) if inert_per_case else set()
    if comunes:
        w("")
        w(D("ev_inert_all") % ", ".join(sorted(comunes)))
        w(D("ev_inert_note"))
    w("")

    # --- 5. Monotonia ----------------------------------------------------- #
    w(D("ev_s5"))
    w("-" * 74)
    for f in monotonicity(cases["critical"]):
        flecha = D("ev_must_rise") if f["direccion"] == "sube" else D("ev_must_fall")
        w("  [%s] %s" % (f["code"], flecha))
        w("    " + " -> ".join(str(v) for _, v in f["serie"]))
        if f["no_documentadas"]:
            w(D("ev_missing_options") % ", ".join(f["no_documentadas"]))
        w("    " + (D("ev_no_violations") if not f["violaciones"]
                    else D("ev_violations") % "; ".join(f["violaciones"])))
    w("")

    # --- 6. Margen -------------------------------------------------------- #
    w(D("ev_s6"))
    w("-" * 74)
    for name, resp in cases.items():
        punt, clas, _ = score(resp)
        dist, u = threshold_margin(punt)
        w(D("ev_margin_line") % (name, punt, L10N(clas), dist, u))
    w("")

    # --- 7. Relacion puntuacion / decision -------------------------------- #
    w(D("ev_s7"))
    w("-" * 74)
    w(D("ev_s7_intro"))
    resp = cases["critical"]
    p0, c0, _ = score(resp)
    for label, pp in ((D("ev_real_score"), p0), (D("ev_forced_0"), 0.0),
                         (D("ev_forced_100"), 100.0)):
        w(D("ev_forced_line")
          % (label, L10N(scoring.classify(pp)),
             migrate(resp, pp, scoring.classify(pp))))
    w("")

    print("")
    if args.md:
        target = output_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            D("ev_doc_title") + "\n\n"
            + config.doc_language_line("ev") + "\n\n"
            + D("ev_doc_intro") + "\n\n"
            + D("ev_doc_seed") % (args.seed, args.samples) + "\n\n"
            + "```\n" + "\n".join(L) + "\n```\n",
            encoding="utf-8")
        print(D("ev_written") % target)


if __name__ == "__main__":
    main()
