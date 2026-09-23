"""Reproduce TODOS los numeros de la entrega del taller con un solo comando.

    python _reproduce.py

Que produce (todo se regenera desde cero en cada ejecucion):

    results/tabla2.json        valores por semilla y por pliegue de cada modelo
    results/tabla2.tex         la Tabla II en LaTeX
    results/fig1.pdf           F1 macro por modelo (media +- sd sobre pliegues)
    results/fig_perdida.pdf    curva de perdida del modelo profundo, por semilla
    results/resultados.md      tabla, lectura y limites
    results/errores/           matrices de confusion y los cinco peores casos
    logs/decisiones.jsonl      una linea por decision del metodo propuesto
                               y de su ablacion

Subproblema P1: clase ordinal de obsolescencia (1-4) de una plataforma PLC.
Datos, particion y metrica son los ya congelados en PROTOCOLO_VALIDACION.md:
9 plataformas (data/platform_lifecycle.csv), 2 pliegues agrupados por
fabricante (data/lifecycle_partition.json), unica variable admisible la
antiguedad, metrica principal F1 macro.

Modelos, todos con la MISMA particion y las MISMAS semillas:

    trivial      clase mayoritaria del entrenamiento (_baseline.b0_trivial)
    logistica    logistica ordinal (_baseline.b1_ordinal_logistic)
    arbol        arbol de decision de profundidad 1 (stump) sobre la antiguedad
    mlp          red neuronal 1-8-1, tanh, entrenada por descenso de gradiente
    propuesto    el agente en lazo: percibir -> recuperar -> decidir -> verificar
    ablacion     el mismo lazo con la funcion 'recuperar' desactivada

Semillas: solo el MLP tiene pasos aleatorios (inicializacion de pesos). Los
demas son deterministas y dan lo mismo con cualquier semilla; se corren igual
con las tres para que la comparacion sea literalmente con las mismas semillas.
"""
from __future__ import annotations

import json
import math
import platform as _platform
import random
import sys
from pathlib import Path

import _baseline as bl

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
ERRORES = RESULTS / "errores"
LOGS = ROOT / "logs"
PARTICION = ROOT / "data" / "lifecycle_partition.json"
POLITICAS = ROOT / "data" / "politicas_fabricante.json"

SEMILLAS = [42, 7, 2026]
CLASES = [1, 2, 3, 4]

# --------------------------------------------------------------------------
# Segundo clasico: arbol de decision de profundidad 1 (stump)
# --------------------------------------------------------------------------

def ajustar_arbol(entrena):
    """Prueba cada punto medio entre antiguedades consecutivas y se queda con
    el umbral que mas acierta en entrenamiento. Empate: el umbral mas bajo."""
    xs = sorted({p.age_years for p in entrena})
    candidatos = [(a + b) / 2 for a, b in zip(xs, xs[1:])] or [xs[0]]
    mejor = None
    for u in candidatos:
        izq = [p.class_label for p in entrena if p.age_years <= u]
        der = [p.class_label for p in entrena if p.age_years > u]
        ci = max(set(izq), key=lambda c: (izq.count(c), -c)) if izq else None
        cd = max(set(der), key=lambda c: (der.count(c), -c)) if der else None
        aciertos = izq.count(ci) + der.count(cd)
        if mejor is None or aciertos > mejor[0]:
            mejor = (aciertos, u, ci, cd)
    _, u, ci, cd = mejor
    ci = ci if ci is not None else cd
    cd = cd if cd is not None else ci
    return {"umbral": u, "izq": ci, "der": cd}


def predecir_arbol(m, p):
    return m["izq"] if p.age_years <= m["umbral"] else m["der"]


# --------------------------------------------------------------------------
# Modelo profundo: MLP 1-8-1
# --------------------------------------------------------------------------

OCULTAS = 8
EPOCAS = 3000
PASO = 0.1


def ajustar_mlp(entrena, semilla):
    """Clasificador binario entre las dos clases presentes (3 y 4), que son
    las unicas del conjunto. Devuelve el modelo y la curva de perdida (BCE
    media de entrenamiento en cada epoca)."""
    clases = sorted({p.class_label for p in entrena})
    baja, alta = clases[0], clases[-1]
    xs = [float(p.age_years) for p in entrena]
    media = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - media) ** 2 for x in xs) / len(xs)) or 1.0
    zs = [(x - media) / sd for x in xs]
    ys = [1.0 if p.class_label == alta else 0.0 for p in entrena]

    rnd = random.Random(semilla)
    w1 = [rnd.gauss(0, 0.5) for _ in range(OCULTAS)]
    b1 = [0.0] * OCULTAS
    w2 = [rnd.gauss(0, 0.5) for _ in range(OCULTAS)]
    b2 = 0.0
    n = len(zs)
    curva = []
    for _ in range(EPOCAS):
        g_w1 = [0.0] * OCULTAS
        g_b1 = [0.0] * OCULTAS
        g_w2 = [0.0] * OCULTAS
        g_b2 = 0.0
        perdida = 0.0
        for z, y in zip(zs, ys):
            h = [math.tanh(w1[j] * z + b1[j]) for j in range(OCULTAS)]
            o = bl._sigmoid(sum(w2[j] * h[j] for j in range(OCULTAS)) + b2)
            o = min(max(o, 1e-12), 1 - 1e-12)
            perdida -= y * math.log(o) + (1 - y) * math.log(1 - o)
            d = o - y
            g_b2 += d
            for j in range(OCULTAS):
                g_w2[j] += d * h[j]
                dh = d * w2[j] * (1 - h[j] ** 2)
                g_w1[j] += dh * z
                g_b1[j] += dh
        curva.append(perdida / n)
        for j in range(OCULTAS):
            w1[j] -= PASO * g_w1[j] / n
            b1[j] -= PASO * g_b1[j] / n
            w2[j] -= PASO * g_w2[j] / n
        b2 -= PASO * g_b2 / n
    modelo = {"w1": w1, "b1": b1, "w2": w2, "b2": b2, "media": media,
              "sd": sd, "baja": baja, "alta": alta}
    return modelo, curva


def predecir_mlp(m, p):
    z = (p.age_years - m["media"]) / m["sd"]
    h = [math.tanh(m["w1"][j] * z + m["b1"][j]) for j in range(OCULTAS)]
    o = bl._sigmoid(sum(m["w2"][j] * h[j] for j in range(OCULTAS)) + m["b2"])
    return m["alta"] if o >= 0.5 else m["baja"]


# --------------------------------------------------------------------------
# Metodo propuesto: el agente en lazo, cuatro funciones
# --------------------------------------------------------------------------

# Cortes de antiguedad (anios) entre clases 1|2|3|4. NO se aprenden de los
# datos: salen de las medias de intervalo entre generaciones ya publicadas en
# el proyecto (7,0 anios en general y 10,5 en gama alta): 7,0 / 7,0+10,5 /
# 2 x (7,0+10,5). Por eso el lazo no tiene fase de entrenamiento.
CORTES = (7.0, 17.5, 35.0)


def percibir(p):
    """Observacion admisible: solo la antiguedad (lo que deja la auditoria de
    fuga) y el fabricante, que es la clave para consultar su politica."""
    return {"plataforma": p.platform, "fabricante": p.manufacturer,
            "antiguedad": p.age_years}


def recuperar(obs, politicas, activa=True):
    """Consulta la politica de repuestos del fabricante. Si la funcion esta
    desactivada (ablacion) o el fabricante no la declara, no hay evidencia y
    el lazo no la supone."""
    if not activa:
        return {"activa": False, "anios_repuestos": None, "fuente": None}
    anios = politicas.get(obs["fabricante"])
    fuente = f"data/politicas_fabricante.json#{obs['fabricante']}" if anios is not None else None
    return {"activa": True, "anios_repuestos": anios, "fuente": fuente}


def decidir(obs):
    edad = obs["antiguedad"]
    for clase, corte in zip((1, 2, 3), CORTES):
        if edad <= corte:
            return clase
    return 4


def verificar(obs, evidencia, clase):
    """Contrasta la decision con la evidencia recuperada.

    Regla: una plataforma en clase 3 (descontinuada con repuestos) pasa a 4 si
    su antiguedad supera el corte de fin de vida MENOS los anios de repuestos
    que garantiza su fabricante. Politica corta = el fin de vida llega antes.
    Ademas marca para revision humana todo cambio y todo caso a menos de dos
    anios de un corte.
    """
    final, avisos = clase, []
    anios = evidencia["anios_repuestos"]
    corte_efectivo = CORTES[2]
    if anios is not None:
        corte_efectivo = CORTES[2] - anios
        if clase == 3 and obs["antiguedad"] > corte_efectivo:
            final = 4
            avisos.append(f"politica de {anios} anios de repuestos: 3 -> 4")
    if final not in CLASES:
        avisos.append("clase fuera de escala")
    margen = min(abs(obs["antiguedad"] - c) for c in (*CORTES[:2], corte_efectivo))
    revision = final != clase or margen < 2
    return {"clase": final, "avisos": avisos, "margen_anios": round(margen, 1),
            "corte_fin_de_vida": corte_efectivo, "revision_humana": revision}


def lazo(p, politicas, recuperar_activa=True):
    obs = percibir(p)
    ev = recuperar(obs, politicas, recuperar_activa)
    clase = decidir(obs)
    ver = verificar(obs, ev, clase)
    return ver["clase"], {"percibir": obs, "recuperar": ev,
                          "decidir": clase, "verificar": ver}


# --------------------------------------------------------------------------
# Corrida
# --------------------------------------------------------------------------

MODELOS = ["trivial", "logistica", "arbol", "mlp", "propuesto", "ablacion"]
NOMBRES = {
    "trivial": "Trivial (clase mayoritaria)",
    "logistica": "Clasico 1: logistica ordinal",
    "arbol": "Clasico 2: arbol de profundidad 1",
    "mlp": "Profundo: MLP 1-8-1",
    "propuesto": "Propuesto: agente en lazo",
    "ablacion": "Ablacion: lazo sin 'recuperar'",
}


def correr():
    data = bl.load()
    por_nombre = {p.platform: p for p in data}
    pliegues = json.loads(PARTICION.read_text(encoding="utf-8"))["folds"]
    politicas = json.loads(POLITICAS.read_text(encoding="utf-8"))[
        "anios_repuestos_tras_fin_fabricacion"]

    salida = {m: {} for m in MODELOS}
    curvas = {}
    decisiones = []
    predicciones = {m: {} for m in MODELOS}

    for semilla in SEMILLAS:
        random.seed(semilla)
        for m in MODELOS:
            salida[m][semilla] = {"pliegues": []}
            predicciones[m][semilla] = []
        for pl in pliegues:
            entrena = [por_nombre[n] for n in pl["train"]]
            prueba = [por_nombre[n] for n in pl["test"]]
            reales = [p.class_label for p in prueba]

            c0 = bl.b0_trivial(entrena)
            logit = bl.b1_ordinal_logistic(entrena)
            arbol = ajustar_arbol(entrena)
            mlp, curva = ajustar_mlp(entrena, semilla)
            curvas[(semilla, pl["fold"])] = curva

            preds = {
                "trivial": [c0 for _ in prueba],
                "logistica": [logit.predict(float(p.age_years)) for p in prueba],
                "arbol": [predecir_arbol(arbol, p) for p in prueba],
                "mlp": [predecir_mlp(mlp, p) for p in prueba],
                "propuesto": [],
                "ablacion": [],
            }
            for variante, activa in (("propuesto", True), ("ablacion", False)):
                for p in prueba:
                    clase, traza = lazo(p, politicas, activa)
                    preds[variante].append(clase)
                    decisiones.append({
                        "variante": variante, "semilla": semilla,
                        "pliegue": pl["fold"], **traza,
                        "clase_final": clase, "clase_real": p.class_label,
                        "acierto": clase == p.class_label,
                    })
            for m in MODELOS:
                met = bl.metrics(reales, preds[m])
                salida[m][semilla]["pliegues"].append({"pliegue": pl["fold"], **met})
                for p, y in zip(prueba, preds[m]):
                    predicciones[m][semilla].append(
                        {"plataforma": p.platform, "real": p.class_label, "predicha": y})
        for m in MODELOS:
            f1 = [x["f1_macro"] for x in salida[m][semilla]["pliegues"]]
            ex = [x["exactitud"] for x in salida[m][semilla]["pliegues"]]
            mf, sf = bl._mean_sd(f1)
            me, se = bl._mean_sd(ex)
            salida[m][semilla].update({"f1_macro_media": round(mf, 3), "f1_macro_sd": round(sf, 3),
                                       "exactitud_media": round(me, 3), "exactitud_sd": round(se, 3)})
    for m in MODELOS:
        medias = [salida[m][s]["f1_macro_media"] for s in SEMILLAS]
        sds = [salida[m][s]["f1_macro_sd"] for s in SEMILLAS]
        exs = [salida[m][s]["exactitud_media"] for s in SEMILLAS]
        mm, sm = bl._mean_sd(medias)
        salida[m]["agregado"] = {
            "f1_macro_media": round(mm, 3),
            "f1_macro_sd_entre_pliegues": round(sum(sds) / len(sds), 3),
            "f1_macro_sd_entre_semillas": round(sm, 3),
            "exactitud_media": round(sum(exs) / len(exs), 3),
        }
    return salida, curvas, decisiones, predicciones, data, politicas


# --------------------------------------------------------------------------
# Escritura
# --------------------------------------------------------------------------

def matriz(filas):
    clases = sorted({f["real"] for f in filas} | {f["predicha"] for f in filas})
    return {"clases": clases,
            "filas_real_columnas_predicha": [[sum(f["real"] == r and f["predicha"] == c for f in filas)
                                              for c in clases] for r in clases]}


def escribir(salida, curvas, decisiones, predicciones, data, politicas):
    RESULTS.mkdir(exist_ok=True)
    ERRORES.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    fmt = lambda v: f"{v:.3f}".replace(".", ",")

    versiones = {"python": sys.version.split()[0], "sistema": f"{_platform.system()} {_platform.release()}",
                 "procesador": _platform.processor()}
    try:
        import matplotlib
        versiones["matplotlib"] = matplotlib.__version__
    except ImportError:
        pass

    tabla = {"subproblema": "P1 - clase ordinal de obsolescencia", "metrica_principal": "F1 macro",
             "particion": "data/lifecycle_partition.json (2 pliegues agrupados por fabricante)",
             "semillas": SEMILLAS, "entorno": versiones,
             "modelos": {m: {"nombre": NOMBRES[m], **{str(s): salida[m][s] for s in SEMILLAS},
                             "agregado": salida[m]["agregado"]} for m in MODELOS}}
    (RESULTS / "tabla2.json").write_text(json.dumps(tabla, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # --- tabla2.tex
    lineas = [r"\begin{table}[!t]", r"\centering",
              r"\caption{P1: F1 macro (media $\pm$ desv. entre pliegues, promedio de 3 semillas)}",
              r"\label{tab:tabla2}", r"\begin{tabular}{lccc}", r"\hline",
              r"Modelo & F1 macro & Exactitud & sd entre semillas \\", r"\hline"]
    for m in MODELOS:
        a = salida[m]["agregado"]
        lineas.append(f"{NOMBRES[m]} & ${fmt(a['f1_macro_media']).replace(',', '{,}')} \\pm "
                      f"{fmt(a['f1_macro_sd_entre_pliegues']).replace(',', '{,}')}$ & "
                      f"{fmt(a['exactitud_media'])} & {fmt(a['f1_macro_sd_entre_semillas'])} \\\\")
    lineas += [r"\hline", r"\end{tabular}", r"\end{table}"]
    (RESULTS / "tabla2.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # --- decisiones
    with (LOGS / "decisiones.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for d in decisiones:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # --- errores: matrices
    matrices = {m: {str(s): matriz(predicciones[m][s]) for s in SEMILLAS} for m in MODELOS}
    (ERRORES / "matrices_confusion.json").write_text(
        json.dumps(matrices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# Matrices de confusion (P1, pliegues de prueba agregados)", "",
          "Filas = clase real, columnas = clase predicha. Semilla 42; los modelos "
          "deterministas dan la misma matriz con las tres semillas (ver "
          "`matrices_confusion.json`), el MLP se muestra con las tres.", ""]
    for m in MODELOS:
        semillas = SEMILLAS if m == "mlp" else [42]
        for s in semillas:
            mt = matrices[m][str(s)]
            md.append(f"## {NOMBRES[m]}" + (f" - semilla {s}" if m == "mlp" else ""))
            md.append("")
            md.append("| real \\ predicha | " + " | ".join(str(c) for c in mt["clases"]) + " |")
            md.append("|---" * (len(mt["clases"]) + 1) + "|")
            for c, fila in zip(mt["clases"], mt["filas_real_columnas_predicha"]):
                md.append(f"| {c} | " + " | ".join(str(v) for v in fila) + " |")
            md.append("")
    (ERRORES / "matrices_confusion.md").write_text("\n".join(md), encoding="utf-8")

    # --- errores: cinco peores casos del metodo propuesto
    prop = [d for d in decisiones if d["variante"] == "propuesto" and d["semilla"] == 42]
    prop.sort(key=lambda d: (d["acierto"], d["verificar"]["margen_anios"]))
    peores = ["# Los cinco peores casos del metodo propuesto (semilla 42)", "",
              "Orden: primero los errores; despues los aciertos mas cercanos a un corte "
              "(menor margen en anios = decision mas fragil).", "",
              "| # | Plataforma | Antig. | Real | Predicha | Margen (anios) | Politica | Avisos |",
              "|---|---|---|---|---|---|---|---|"]
    for i, d in enumerate(prop[:5], 1):
        pol = d["recuperar"]["anios_repuestos"]
        peores.append(f"| {i} | {d['percibir']['plataforma']} | {d['percibir']['antiguedad']} | "
                      f"{d['clase_real']} | {d['clase_final']} | {d['verificar']['margen_anios']} | "
                      f"{'n.d.' if pol is None else str(pol) + ' anios'} | "
                      f"{'; '.join(d['verificar']['avisos']) or '-'} |")
    (ERRORES / "peores_casos.md").write_text("\n".join(peores) + "\n", encoding="utf-8")

    # --- figuras
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 3.6))
    medias = [salida[m]["agregado"]["f1_macro_media"] for m in MODELOS]
    errs = [salida[m]["agregado"]["f1_macro_sd_entre_pliegues"] for m in MODELOS]
    colores = ["#9e9e9e", "#9e9e9e", "#9e9e9e", "#6b8fb5", "#1F4E9C", "#b5c7e3"]
    ax.bar(range(len(MODELOS)), medias, yerr=errs, capsize=4, color=colores, edgecolor="#333")
    ax.set_xticks(range(len(MODELOS)))
    ax.set_xticklabels(["Trivial", "Logistica\nordinal", "Arbol\nprof. 1", "MLP\n1-8-1",
                        "Propuesto", "Ablacion\n(sin recuperar)"], fontsize=8)
    ax.set_ylabel("F1 macro")
    ax.set_ylim(0, 1.3)
    for i, v in enumerate(medias):
        ax.text(i, 0.03, f"{v:.3f}", ha="center", fontsize=8, color="white" if i in (4,) else "black")
    ax.set_title("P1: F1 macro, media +- sd entre pliegues (3 semillas)", fontsize=9)
    fig.tight_layout()
    fig.savefig(RESULTS / "fig1.pdf")
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(7, 3), sharey=True)
    for k, ax in enumerate(axs):
        for s in SEMILLAS:
            ax.plot(curvas[(s, k)], label=f"semilla {s}", linewidth=1)
        ax.set_title(f"MLP, pliegue {k}", fontsize=9)
        ax.set_xlabel("epoca")
    axs[0].set_ylabel("perdida BCE (entrenamiento)")
    axs[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "fig_perdida.pdf")
    plt.close(fig)

    # --- resultados.md
    r = ["# Resultados - P1 (se regenera con `python _reproduce.py`)", "",
         "Metrica principal: **F1 macro**. Media +- desviacion muestral entre los 2 pliegues, "
         "promediada sobre las semillas " + ", ".join(map(str, SEMILLAS)) + ".", "",
         "| Modelo | F1 macro | Exactitud | sd entre semillas |", "|---|---|---|---|"]
    for m in MODELOS:
        a = salida[m]["agregado"]
        r.append(f"| {NOMBRES[m]} | {fmt(a['f1_macro_media'])} +- {fmt(a['f1_macro_sd_entre_pliegues'])} | "
                 f"{fmt(a['exactitud_media'])} | {fmt(a['f1_macro_sd_entre_semillas'])} |")
    p, ab = salida["propuesto"]["agregado"], salida["ablacion"]["agregado"]
    r += ["", "## Ablacion", "",
          f"Quitar la funcion `recuperar` (la consulta de la politica de repuestos del fabricante) "
          f"cambia el F1 macro de {fmt(p['f1_macro_media'])} a {fmt(ab['f1_macro_media'])}. "
          "Misma particion, mismas semillas, mismo codigo: la unica diferencia es el argumento "
          "`recuperar_activa`. Detalle por decision en `logs/decisiones.jsonl` (campo `variante`).", "",
          "## Las cuatro funciones del lazo", "",
          "1. **percibir**: toma solo la antiguedad (unica variable que deja la auditoria de fuga) y el fabricante.",
          "2. **recuperar**: consulta `data/politicas_fabricante.json` (anios de repuestos que garantiza el fabricante) y cita la fuente; si no hay dato, no lo supone.",
          "3. **decidir**: aplica los cortes 7,0 / 17,5 / 35,0 anios, derivados de medias ya publicadas, sin entrenar con estos datos.",
          "4. **verificar**: contrasta la decision con la evidencia (una clase 3 pasa a 4 si la antiguedad supera 35 menos los anios de repuestos del fabricante) y marca para revision humana los cambios y los casos a menos de 2 anios de un corte.",
          "", "## Limites que hay que leer junto a los numeros", "",
          "- **n = 9 plataformas en 2 pliegues.** Cada pliegue tiene 4-5 casos: un solo acierto mueve el F1 de un pliegue en decenas de puntos. Las desviaciones son grandes y se solapan.",
          "- **La regla de `verificar` se formulo despues de ver el unico fallo de la variante sin recuperacion** (MELSEC AnS/QnAS, 2026-09-14). No estaba congelada en el protocolo, asi que el resultado del metodo propuesto es **optimista**: falta validarlo en datos que no se hayan mirado.",
          "- La misma regla produce un **falso positivo** (S7-300, politica de 10 anios): ver `results/errores/peores_casos.md`.",
          "- El MLP es un modelo profundo sobre una sola variable y 4-5 filas de entrenamiento: esta declarado para cumplir el protocolo, no porque el tamanio del conjunto lo justifique. La sd entre semillas mide cuanto depende de la inicializacion.",
          "- Las etiquetas se derivan de fechas (etiqueta provisional por regla, no juicio de panel).",
          "", "## Entorno", ""] + [f"- {k}: {v}" for k, v in versiones.items()]
    (RESULTS / "resultados.md").write_text("\n".join(r) + "\n", encoding="utf-8")


def main():
    salida, curvas, decisiones, predicciones, data, politicas = correr()
    escribir(salida, curvas, decisiones, predicciones, data, politicas)
    for m in MODELOS:
        a = salida[m]["agregado"]
        print(f"{NOMBRES[m]:<36} F1 macro {a['f1_macro_media']:.3f} +- "
              f"{a['f1_macro_sd_entre_pliegues']:.3f}  (sd semillas {a['f1_macro_sd_entre_semillas']:.3f})")
    print(f"decisiones registradas: {len(decisiones)} -> logs/decisiones.jsonl")
    print("salidas en results/")


if __name__ == "__main__":
    main()
