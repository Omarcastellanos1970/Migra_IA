"""Verificacion interna del motor de riesgo: baselines, sensibilidad e influencia.

No necesita clave de API ni casos de campo: todo lo que se mide sale del propio
motor determinista, asi que el informe es reproducible en cualquier maquina.

Uso:
    python _evaluacion.py                  # informe en pantalla
    python _evaluacion.py --md             # ademas escribe docs/evaluacion_interna.md
    python _evaluacion.py --muestras 20000 --semilla 7

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

from migra_ia import interactivo, scoring
from _interactivo_run import ESCENARIOS

RAIZ = Path(__file__).resolve().parent
UMBRALES = [20, 40, 60, 80]

# Valores de referencia publicados en ARTIFACT.md. Si el motor deja de
# producirlos, el informe se detiene en vez de publicar cifras que no cuadran.
ESPERADO = {"critico": 85.0, "sano": 11.8}


# --------------------------------------------------------------------------- #
# Resolucion de escenarios: de lo que el usuario escribe al dict que ve el motor
# --------------------------------------------------------------------------- #
def resolver(esc: dict) -> dict:
    """Traduce las entradas del escenario al dict de respuestas del motor.

    Reutiliza `_interpretar` del propio modulo interactivo, de modo que no hay
    una segunda interpretacion que pueda divergir de la real.
    """
    resueltas: dict = {}
    for codigo, texto in esc["respuestas"].items():
        p = interactivo._pregunta(codigo)
        if p is None:
            raise SystemExit("El codigo " + codigo + " no existe en cuestionario.json")
        valor = interactivo._interpretar(p, texto)
        if valor is None:
            raise SystemExit("No se pudo interpretar " + codigo + "=" + repr(texto))
        resueltas[codigo] = valor
    return resueltas


@contextmanager
def pesos(nuevos):
    """Ejecuta el bloque con otro juego de pesos y restaura los originales."""
    if nuevos is None:
        yield
        return
    originales = scoring.PESOS
    scoring.PESOS = nuevos
    try:
        yield
    finally:
        scoring.PESOS = originales


def puntuar(respuestas: dict, w=None):
    """Puntuacion, clasificacion y factores omitidos, con los pesos indicados."""
    with pesos(w):
        calculados, omitidos = interactivo.factores(respuestas)
        r = scoring.calcular_riesgo(calculados)
    return r.puntuacion, r.clasificacion, omitidos


def migra(respuestas: dict, punt: float, clas: str) -> bool:
    """Decision del mapa de decision para este caso."""
    d = interactivo.decidir(respuestas, {"puntuacion": punt, "clasificacion": clas})
    return bool(d["migrar"])


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
PESOS_UNIFORMES = {k: 1.0 / len(scoring.PESOS) for k in scoring.PESOS}

# B0: la regla que se le ocurre a cualquiera en cinco minutos. Un solo dato.
_M01_MIGRAR = {"Descontinuado, aun con soporte y repuestos",
               "Descontinuado y sin soporte (fin de vida)"}


def baseline_trivial(respuestas: dict):
    """B0: solo mira M01. Puntuacion = valor del factor de ciclo de vida."""
    f = interactivo._f_ciclo_vida(respuestas)
    punt = None if f is None else float(f["valor"])
    return punt, respuestas.get("M01") in _M01_MIGRAR


# --------------------------------------------------------------------------- #
# Analisis
# --------------------------------------------------------------------------- #
def margen_umbral(punt: float):
    """Distancia al umbral de clasificacion mas cercano."""
    dist, u = min((abs(punt - u), u) for u in UMBRALES)
    return round(dist, 1), str(u)


def sensibilidad_individual(respuestas: dict, base_clas: str):
    """Mueve un peso a la vez y observa si cambia la clasificacion."""
    filas = []
    for clave in list(scoring.PESOS):
        fila = {"factor": clave, "peso": scoring.PESOS[clave], "cambios": []}
        for pct in (-50, -20, 20, 50):
            w = dict(scoring.PESOS)
            w[clave] = max(0.0, w[clave] * (1 + pct / 100))
            punt, clas, _ = puntuar(respuestas, w)
            fila["%+d%%" % pct] = punt
            if clas != base_clas:
                fila["cambios"].append("%+d%% -> %s" % (pct, clas))
        filas.append(fila)
    return filas


def sensibilidad_montecarlo(respuestas: dict, base_clas: str,
                            muestras: int, semilla: int):
    """Perturba los ocho pesos a la vez, uniforme en [0.5, 1.5], y renormaliza."""
    rnd = random.Random(semilla)
    puntos, estables = [], 0
    for _ in range(muestras):
        w = {k: v * rnd.uniform(0.5, 1.5) for k, v in scoring.PESOS.items()}
        total = sum(w.values())
        w = {k: v / total for k, v in w.items()}
        punt, clas, _ = puntuar(respuestas, w)
        puntos.append(punt)
        if clas == base_clas:
            estables += 1
    return {
        "muestras": muestras,
        "estabilidad": round(100.0 * estables / muestras, 1),
        "min": round(min(puntos), 1),
        "max": round(max(puntos), 1),
        "media": round(statistics.mean(puntos), 1),
        "desv": round(statistics.pstdev(puntos), 2),
    }


def influencia_por_pregunta(respuestas: dict):
    """Barre todas las opciones de cada pregunta y mide el rango que produce."""
    filas = []
    for codigo, actual in respuestas.items():
        p = interactivo._pregunta(codigo)
        opciones = (p or {}).get("opciones") or []
        if not opciones:
            continue
        vals = []
        for op in opciones:
            prueba = dict(respuestas)
            prueba[codigo] = [op] if p.get("tipo") == "seleccion_multiple" else op
            punt, _, _ = puntuar(prueba)
            vals.append(punt)
        filas.append({
            "codigo": codigo,
            "texto": (p or {}).get("texto", ""),
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


def ruta_decision(respuestas: dict):
    """Secuencia de alternativas que el mapa de decision propone para este caso."""
    punt, clas, _ = puntuar(respuestas)
    d = interactivo.decidir(respuestas, {"puntuacion": punt, "clasificacion": clas})
    return tuple(a["alternativa"] for a in d["ruta"])


def influencia_en_decision(respuestas: dict):
    """Codigos cuyo cambio de opcion altera la ruta del mapa de decision.

    Complementa el barrido de puntuacion: una pregunta puede no mover el numero
    y aun asi cambiar la recomendacion, o al reves.
    """
    mueven, inertes = [], []
    for codigo in respuestas:
        p = interactivo._pregunta(codigo)
        opciones = (p or {}).get("opciones") or []
        if not opciones:
            continue
        rutas, puntos = set(), set()
        for op in opciones:
            prueba = dict(respuestas)
            prueba[codigo] = [op] if p.get("tipo") == "seleccion_multiple" else op
            punt, _, _ = puntuar(prueba)
            puntos.add(punt)
            rutas.add(ruta_decision(prueba))
        if len(rutas) > 1:
            mueven.append((codigo, len(rutas)))
        elif len(puntos) == 1:
            inertes.append(codigo)
    return mueven, inertes


def monotonia(respuestas: dict):
    """Al empeorar una respuesta ordinal, el riesgo no deberia ir al reves."""
    filas = []
    for codigo, escala, direccion in ORDINALES:
        p = interactivo._pregunta(codigo)
        documentadas = (p or {}).get("opciones") or []
        faltan = [op for op in escala if op not in documentadas]
        serie, violaciones = [], []
        for op in escala:
            prueba = dict(respuestas)
            prueba[codigo] = op
            punt, _, _ = puntuar(prueba)
            serie.append((op, punt))
        for (a, va), (b, vb) in zip(serie, serie[1:]):
            if direccion == "sube" and vb < va - 1e-9:
                violaciones.append("'%s' (%s) -> '%s' (%s): baja" % (a, va, b, vb))
            if direccion == "baja" and vb > va + 1e-9:
                violaciones.append("'%s' (%s) -> '%s' (%s): sube" % (a, va, b, vb))
        filas.append({"codigo": codigo, "direccion": direccion, "serie": serie,
                      "violaciones": violaciones, "no_documentadas": faltan})
    return filas


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Verificacion interna del motor MIGRA-IA")
    ap.add_argument("--md", action="store_true", help="escribe docs/evaluacion_interna.md")
    ap.add_argument("--muestras", type=int, default=5000)
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()

    casos = {n: resolver(e) for n, e in ESCENARIOS.items()}
    L = []

    def w(linea=""):
        print(linea)
        L.append(linea)

    w("=" * 74)
    w("VERIFICACION INTERNA DEL MOTOR - MIGRA-IA")
    w("=" * 74)
    w("Sin clave de API, sin datos de campo. Determinista y reproducible.")
    w("")

    # --- 0. Anclaje contra las cifras publicadas -------------------------- #
    w("0. ANCLAJE CONTRA ARTIFACT.md")
    w("-" * 74)
    for nombre, esperado in ESPERADO.items():
        punt, clas, _ = puntuar(casos[nombre])
        ok = abs(punt - esperado) < 1e-9
        w("  %-8s %-12s %6.1f  esperado %s  (%s)"
          % ("OK" if ok else "DIFIERE", nombre, punt, esperado, clas))
        if not ok:
            raise SystemExit("El motor ya no reproduce las cifras publicadas en "
                             "ARTIFACT.md. Revisa el cambio antes de seguir.")
    w("")

    # --- 1. Baselines ----------------------------------------------------- #
    w("1. BASELINE vs PROPUESTA")
    w("-" * 74)
    w("  AVISO: son 3 filas pero 2 casos independientes. 'otra_marca' es 'critico'")
    w("  con otro destino -las mismas 24 respuestas-, asi que sus tres cifras")
    w("  coinciden por construccion y no por coincidencia. No cuenta como")
    w("  evidencia adicional.")
    w("")
    w("  %-12s %12s %13s %11s   decision" % ("caso", "B0 trivial", "B1 uniforme", "propuesta"))
    tabla_base = []
    for nombre, resp in casos.items():
        p_prop, c_prop, _ = puntuar(resp)
        p_uni, c_uni, _ = puntuar(resp, PESOS_UNIFORMES)
        p_triv, m_triv = baseline_trivial(resp)
        m_prop = migra(resp, p_prop, c_prop)
        tabla_base.append({"caso": nombre, "b1": p_uni, "prop": p_prop})
        d = ("migrar" if m_prop else "no migrar")
        if m_triv != m_prop:
            d += "  (B0 dice: %s)" % ("migrar" if m_triv else "no migrar")
        w("  %-12s %12s %13.1f %11.1f   %s" % (nombre, p_triv, p_uni, p_prop, d))
    w("")
    dif = [f for f in tabla_base if abs(f["b1"] - f["prop"]) >= 0.05]
    if dif:
        w("  Los pesos de la Seccion 6 SI cambian el resultado frente a pesos")
        w("  uniformes en: " + ", ".join("%s (%s vs %s)" % (f["caso"], f["b1"], f["prop"])
                                         for f in dif))
    else:
        w("  ATENCION: pesos uniformes reproducen la propuesta en todos los casos.")
        w("  Los pesos elegidos a mano no aportan nada medible en este conjunto.")
    w("")

    # --- 2. Sensibilidad -------------------------------------------------- #
    w("2. SENSIBILIDAD DE LOS PESOS")
    w("-" * 74)
    for nombre, resp in casos.items():
        if nombre == "otra_marca":
            continue  # identico a 'critico' en puntuacion; solo cambia el destino
        p_base, c_base, _ = puntuar(resp)
        w("  [%s]  base = %s (%s)" % (nombre, p_base, c_base))
        for fila in sensibilidad_individual(resp, c_base):
            marca = "  <-- cambia de clase" if fila["cambios"] else ""
            w("    %-26s peso %.2f  -50%%:%6.1f  -20%%:%6.1f  +20%%:%6.1f  +50%%:%6.1f%s"
              % (fila["factor"], fila["peso"], fila["-50%"], fila["-20%"],
                 fila["+20%"], fila["+50%"], marca))
        m = sensibilidad_montecarlo(resp, c_base, args.muestras, args.semilla)
        w("    Monte Carlo (%d muestras, pesos x U(0.5,1.5) renormalizados):"
          % m["muestras"])
        w("      puntuacion %s .. %s   media %s   sd %s"
          % (m["min"], m["max"], m["media"], m["desv"]))
        w("      la clasificacion se mantiene en %s%% de las muestras" % m["estabilidad"])
        w("")

    # --- 3. Influencia ---------------------------------------------------- #
    w("3. INFLUENCIA DE CADA PREGUNTA (escenario 'critico')")
    w("-" * 74)
    infl = influencia_por_pregunta(casos["critico"])
    w("  %-5s %7s %7s %7s  pregunta" % ("cod", "rango", "min", "max"))
    for f in infl[:12]:
        w("  %-5s %7.1f %7.1f %7.1f  %s" % (f["codigo"], f["rango"], f["min"],
                                            f["max"], f["texto"][:42]))
    sin_efecto = [f["codigo"] for f in infl if f["rango"] == 0]
    if sin_efecto:
        w("")
        w("  Sin efecto sobre la puntuacion: " + ", ".join(sin_efecto))
        w("  (no implica que sean inutiles: ver seccion 4, pueden mover la ruta)")
    w("")

    # --- 4. Influencia sobre la ruta de decision ------------------------- #
    w("4. INFLUENCIA SOBRE LA RUTA DE DECISION")
    w("-" * 74)
    w("  Una pregunta puede no mover el numero y aun asi cambiar la recomendacion.")
    inertes_por_caso = {}
    for nombre, resp in casos.items():
        if nombre == "otra_marca":
            continue
        mueven, inertes = influencia_en_decision(resp)
        inertes_por_caso[nombre] = set(inertes)
        w("  [%s] ruta base: %s" % (nombre, " > ".join(ruta_decision(resp))))
        w("    cambian la ruta: " + (", ".join("%s (%d rutas)" % m for m in mueven)
                                     if mueven else "ninguna"))
        w("    no mueven ni puntuacion ni ruta: "
          + (", ".join(inertes) if inertes else "ninguna"))
    comunes = set.intersection(*inertes_por_caso.values()) if inertes_por_caso else set()
    if comunes:
        w("")
        w("  Inertes en TODOS los escenarios probados: " + ", ".join(sorted(comunes)))
        w("  Revisar si estan implementadas o solo declaradas en el mapa de decision.")
    w("")

    # --- 5. Monotonia ----------------------------------------------------- #
    w("5. MONOTONIA SOBRE ESCALAS ORDINALES (escenario 'critico')")
    w("-" * 74)
    for f in monotonia(casos["critico"]):
        flecha = "riesgo debe subir" if f["direccion"] == "sube" else "riesgo debe bajar"
        w("  [%s] %s" % (f["codigo"], flecha))
        w("    " + " -> ".join(str(v) for _, v in f["serie"]))
        if f["no_documentadas"]:
            w("    AVISO: opciones ausentes de cuestionario.json: "
              + ", ".join(f["no_documentadas"]))
        w("    " + ("sin violaciones" if not f["violaciones"]
                    else "VIOLACIONES: " + "; ".join(f["violaciones"])))
    w("")

    # --- 6. Margen -------------------------------------------------------- #
    w("6. MARGEN HASTA EL UMBRAL MAS CERCANO (20/40/60/80)")
    w("-" * 74)
    for nombre, resp in casos.items():
        punt, clas, _ = puntuar(resp)
        dist, u = margen_umbral(punt)
        w("  %-12s %6.1f (%s) a %s puntos del umbral %s" % (nombre, punt, clas, dist, u))
    w("")

    # --- 7. Relacion puntuacion / decision -------------------------------- #
    w("7. RELACION ENTRE LA PUNTUACION Y LA DECISION")
    w("-" * 74)
    w("  Se fuerza la puntuacion a los extremos dejando las respuestas intactas.")
    resp = casos["critico"]
    p0, c0, _ = puntuar(resp)
    for etiqueta, pp in (("puntuacion real", p0), ("forzada a 0", 0.0),
                         ("forzada a 100", 100.0)):
        w("    %-18s (%s) -> migrar = %s"
          % (etiqueta, scoring.clasificar(pp), migra(resp, pp, scoring.clasificar(pp))))
    w("")

    print("")
    if args.md:
        destino = RAIZ / "docs" / "evaluacion_interna.md"
        destino.write_text(
            "# Verificacion interna del motor MIGRA-IA\n\n"
            "Generado por `_evaluacion.py`. Reproducible: mismas respuestas, "
            "mismos numeros, sin clave de API.\n\n"
            "Semilla Monte Carlo: `%d` - muestras: `%d`.\n\n" % (args.semilla, args.muestras)
            + "```\n" + "\n".join(L) + "\n```\n",
            encoding="utf-8")
        print("Informe escrito en " + str(destino))


if __name__ == "__main__":
    main()
