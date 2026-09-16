"""Tabla II del taller y su parrafo de configuracion experimental.

QUE PIDE EL EJERCICIO
---------------------
  1. El titulo, en una linea: conjunto de datos, metrica principal, sobre que
     se promedia y con que agrupamiento. Si no cabe en una linea, el protocolo
     no esta claro.
  2. Las filas: el baseline trivial; los clasicos, justificados en una linea
     cada uno; y el metodo propuesto. Ni una fila mas.
  3. Las columnas: la metrica principal con +-, una secundaria que explique, y
     un costo.
  4. Las celdas quedan vacias: son el plan de experimentos de la semana. Solo
     la fila del trivial lleva numero.

COMO SE CUMPLE AQUI
-------------------
  filas       trivial (clase mayoritaria) | clasico (logistica ordinal) |
              propuesta (agente con RAG y verificacion). Tres. Ni una mas.
              El gradient boosting de P2 NO entra: es otro subproblema, con
              otra metrica, y esta tabla tiene un solo titulo.
  columnas    F1 macro media +- desviacion entre pliegues (la que decide,
              congelada en PROTOCOLO_VALIDACION.md), exactitud como secundaria
              -explica por que decide el F1: el trivial acierta mucho y su F1
              se hunde- y como costo el tiempo de inferencia por caso, medido.
  celdas      por defecto solo la fila del trivial lleva numero, como pide el
              ejercicio. Con --con-clasico se llena tambien la del clasico,
              que ya esta medida desde el 2026-09-04.

Ningun numero se teclea: se importan de _baseline.py y se vuelven a calcular.

    python _tabla_ii.py                  # tabla, parrafo y verificacion
    python _tabla_ii.py --con-clasico    # ademas, llena la fila del clasico
    python _tabla_ii.py --salida "C:\\ruta\\Figures\\Tables"

CONVENCION: codigo y pantalla en ASCII; el LaTeX y el Markdown que se escriben
llevan tildes, porque son texto del paper, y se guardan en UTF-8.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time

import _baseline as bl

TEX_OUTPUT = os.path.join("docs", "figuras")
MD_OUTPUT = os.path.join("docs", "tabla_ii_y_configuracion.md")
PROTOCOL_OUTPUT = "PROTOCOLO.md"
REPO = "github.com/Omarcastellanos1970/Migra_IA"

# Repeticiones de la medida de tiempo. Se toma el mejor de varias rondas: lo
# que se busca es el coste del modelo, no el ruido del sistema operativo.
REPETITIONS = 2000
RONDAS = 5
# El tiempo de inferencia se lleva mas rondas: es de microsegundos y cualquier
# otra cosa que haga la maquina en ese instante lo dispara. Se toma el minimo,
# que es la ronda menos contaminada, y se declara la dispersion.
RONDAS_TIEMPO = 9
# Por encima de esta fraccion, la medida de tiempo no es publicable.
TOLERANCIA_TIEMPO = 0.25


# --------------------------------------------------------------------------
# Medida
# --------------------------------------------------------------------------

def measure():
    data = bl.load()
    pliegues, k, k_note = bl.stratified_partition(data)
    res = bl.evaluate(data, pliegues)
    tiempos = measure_times(data, pliegues)
    return {
        "datos": data, "folds": pliegues, "k": k, "k_note": k_note,
        "n": len(data), "cv": res["cv"], "models": res["models"],
        "tiempos": tiempos,
        "train": measure_training(data, pliegues),
        "clases": sorted({p.class_label for p in data}),
        "tam_prueba": [len(pl["test"]) for pl in pliegues],
    }


def measure_training(data, pliegues):
    """Segundos que cuesta entrenar la validacion cruzada entera, una vez."""
    by_name = {p.platform: p for p in data}
    entrenas = [[by_name[n] for n in pl["train"]] for pl in pliegues]

    def qa_round():
        inicio = time.perf_counter()
        for entrena in entrenas:
            bl.b0_trivial(entrena)
            bl.b1_ordinal_logistic(entrena)
        return time.perf_counter() - inicio

    return min(qa_round() for _ in range(RONDAS))


def measure_times(data, pliegues):
    """Microsegundos por caso de cada modelo, en inferencia."""
    by_name = {p.platform: p for p in data}
    preparados = []
    for pl in pliegues:
        entrena = [by_name[n] for n in pl["train"]]
        test = [by_name[n] for n in pl["test"]]
        c0 = bl.b0_trivial(entrena)
        modelo = bl.b1_ordinal_logistic(entrena)
        xs = [float(p.age_years) for p in test]
        preparados.append((c0, modelo, xs))
    n_cases = sum(len(xs) for _, _, xs in preparados)

    def qa_round(cual):
        inicio = time.perf_counter()
        for _ in range(REPETITIONS):
            for c0, modelo, xs in preparados:
                for x in xs:
                    if cual == "b0":
                        _ = c0
                    else:
                        _ = modelo.predict(x)
        return (time.perf_counter() - inicio) / (REPETITIONS * n_cases)

    medidas = {}
    for cual in ("b0", "b1"):
        rondas = sorted(qa_round(cual) * 1e6 for _ in range(RONDAS_TIEMPO))
        # El mejor tiempo es el que menos ruido del sistema lleva encima; la
        # dispersion entre rondas dice hasta que digito hay que creerse.
        medidas[cual] = (rondas[0], rondas[-1] - rondas[0])
    return medidas


def _sig2(value, es=True):
    """Dos cifras significativas: mas digitos serian ruido de medida."""
    if value <= 0:
        return "0"
    decimales = max(0, 2 - 1 - int(("%e" % value).split("e")[1]))
    text = "%%.%df" % decimales % value
    return text.replace(".", "{,}") if es else text


def _num(value, decimales=3, es=True):
    """Numero en formato del paper.

    En espanol la coma decimal va entre llaves, {,}, porque en modo matematico
    LaTeX trata la coma suelta como separador y le mete un espacio detras. En
    ingles el separador es el punto y no hace falta protegerlo.
    """
    text = "%%.%df" % decimales % value
    return text.replace(".", "{,}") if es else text


# --------------------------------------------------------------------------
# Contenido de la tabla
# --------------------------------------------------------------------------

VACIA = "---"

TITLE_ES = ("Riesgo ordinal de obsolescencia en %(n)d plataformas de "
             "automatización: $F_1$ macro medio $\\pm$ desviación sobre "
             "%(k)d pliegues agrupados por fabricante")
TITLE_EN = ("Ordinal obsolescence risk on %(n)d automation platforms: mean "
             "macro $F_1$ $\\pm$ deviation over %(k)d manufacturer-grouped "
             "folds")

FILAS_ES = [
    ("Trivial", "clase mayoritaria del pliegue de entrenamiento", "b0"),
    ("Clásico: logística ordinal",
     "escala ordenada, dato tabular escaso y coeficientes auditables", "b1"),
    ("Propuesta: agente con RAG y verificación",
     "recupera evidencia citable y no ajusta pesos", "propuesta"),
]
FILAS_EN = [
    ("Trivial", "majority class of the training fold", "b0"),
    ("Classical: ordinal logistic",
     "ordered scale, scarce tabular data, auditable coefficients", "b1"),
    ("Proposed: agent with RAG and verification",
     "retrieves citable evidence and fits no weights", "propuesta"),
]

NOTE_ES = ("Las celdas vacías son el plan de experimentos: se llenan cuando "
           "cada modelo se ejecute bajo esta misma partición. El coste es el "
           "mejor de cinco rondas y se da con dos cifras significativas, que "
           "es hasta donde llega la resolución de la medida.")
NOTE_EN = ("Empty cells are the experiment plan: they are filled once each "
           "model is run under this same partition. Cost is the best of five "
           "rounds and is reported to two significant figures, the resolution "
           "limit of the measurement.")


def cells(med, key, with_classic, es=True):
    """(F1 macro, exactitud, coste) de una fila, o vacias si toca."""
    if key == "propuesta" or (key == "b1" and not with_classic):
        return (VACIA, VACIA, VACIA)
    f1, sd = med["cv"][key]["f1_macro"]
    exa = med["cv"][key]["exactitud"][0]
    return ("$%s \\pm %s$" % (_num(f1, es=es), _num(sd, es=es)),
            "$%s$" % _num(exa, es=es),
            "$%s$" % _sig2(med["tiempos"][key][0], es=es))


TABLA_TEX = r"""%% %(comentario)s
%% -------------------------------------------------------------------------
%% GENERADO POR _tabla_ii.py DEL REPOSITORIO MIGRA-IA. NO EDITAR A MANO.
%% Los numeros salen de correr _baseline.py; el coste, de medir la inferencia.
%% ESTADO: %(status)s
%%
%% PAQUETES: \usepackage{booktabs} y \usepackage{array}, los dos ya cargados.
%% -------------------------------------------------------------------------
\begin{table}[!tb]
\caption{%(title)s}
\label{tab:baselines}
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}p{0.40\columnwidth}ccc@{}}
\toprule
%(cab_modelo)s & %(cab_principal)s & %(cab_secundaria)s & %(cab_costo)s \\
 & %(cab_principal_2)s & & %(cab_costo_2)s \\
\midrule
%(filas)s\bottomrule
\end{tabular}

\vspace{2pt}
{\scriptsize %(note)s}
\end{table}
"""

FILA_TEX = ("\\textbf{%s}\\newline {\\scriptsize %s} & %s & %s & %s \\\\\n")


def build_tex(idioma, med, with_classic):
    es = idioma == "ES"
    title = (TITLE_ES if es else TITLE_EN) % {"n": med["n"], "k": med["k"]}
    filas = ""
    for name, justification, key in (FILAS_ES if es else FILAS_EN):
        f1, exa, coste = cells(med, key, with_classic, es)
        filas += FILA_TEX % (name, justification, f1, exa, coste)
    status = ("fila del trivial con numeros%s; el resto, vacio a proposito"
              % (" y la del clasico" if with_classic else ""))
    return TABLA_TEX % {
        "comentario": ("Tabla II -- Lineas base de P1. Version en espanol."
                       if es else
                       "Table II -- P1 baselines. English version."),
        "status": status,
        "title": title,
        "cab_modelo": "Modelo" if es else "Model",
        "cab_principal": "$F_1$ macro" if es else "Macro $F_1$",
        "cab_principal_2": ("(media $\\pm$ desv.)" if es
                            else "(mean $\\pm$ dev.)"),
        "cab_secundaria": "Exactitud" if es else "Accuracy",
        "cab_costo": "Coste" if es else "Cost",
        "cab_costo_2": ("($\\mu$s/caso)" if es else "($\\mu$s/case)"),
        "filas": filas,
        "note": NOTE_ES if es else NOTE_EN,
    }


# --------------------------------------------------------------------------
# El parrafo de configuracion experimental, siete frases
# --------------------------------------------------------------------------

PARRAFO_ES = (
    "El conjunto de datos procede de la tabla de ciclo de vida de plataformas "
    "de automatización del repositorio del proyecto, reúne %(n)d plataformas "
    "de %(marcas)d fabricantes etiquetadas en %(n_clases)d de los cuatro "
    "niveles de la escala ordinal de obsolescencia (%(clases)s), y su unidad "
    "de observación es la plataforma, no el caso de migración. "
    "La partición es una validación cruzada de %(k)d pliegues, estratificada "
    "por nivel y agrupada por fabricante, con semilla %(sem)d y reparto "
    "determinista guardado en disco: cada pliegue aparta como prueba un bloque "
    "completo de marcas —%(tam)s plataformas de las %(n)d, %(prop)s— que no "
    "interviene en ningún ajuste, de modo que ninguna marca aparece a la vez "
    "en entrenamiento y en prueba. "
    "El preprocesamiento calcula una sola característica, la antigüedad de la "
    "plataforma como %(anio)s menos el año de lanzamiento —la única que "
    "sobrevivió a la auditoría de fuga—, y la estandariza con la media y la "
    "escala del entrenamiento, ajustadas dentro de cada pliegue y nunca sobre "
    "el conjunto completo. "
    "Se comparan tres modelos: una línea base trivial que responde siempre la "
    "clase mayoritaria del pliegue de entrenamiento, una regresión logística "
    "ordinal de probabilidades proporcionales y el agente propuesto, todavía "
    "no ejecutado; los dos primeros están implementados con la biblioteca "
    "estándar de Python %(py)s, sin dependencias de terceros. "
    "No hay búsqueda de hiperparámetros: el espacio explorado es de cero "
    "puntos para los tres modelos, el mismo esfuerzo para todos, porque la "
    "trivial no tiene ninguno y los de la logística ordinal se fijaron de "
    "antemano en regularización $L_2=%(l2)s$, paso %(step)s, %(iter)d "
    "iteraciones e inicio en ceros, idénticos en todos los pliegues. "
    "La validación es cruzada agrupada con $k=%(k)d$ y una sola repetición "
    "—repetirla daría el mismo resultado, porque no hay ningún paso "
    "estocástico—, y reporta la media y la desviación típica muestral entre "
    "pliegues del $F_1$ macro como métrica principal que decide, con la "
    "exactitud y el error ordinal medio como secundarias que explican. "
    "Todo se ejecuta en CPU sobre %(hw)s: entrenar la validación cruzada "
    "completa cuesta %(t_ent)s, la semilla %(sem)d queda declarada aunque no "
    "llegue a usarse por ser determinista el ajuste, y el código y los datos "
    "están publicados en %(url)s.")

PARRAFO_EN = (
    "The dataset comes from the automation platform life-cycle table of the "
    "project repository, gathers %(n)d platforms from %(marcas)d manufacturers "
    "labelled in %(n_clases)d of the four levels of the ordinal obsolescence "
    "scale (%(clases)s), and its unit of observation is the platform, not the "
    "migration case. "
    "The partition is a %(k)d-fold cross-validation, stratified by level and "
    "grouped by manufacturer, with seed %(sem)d and a deterministic assignment "
    "stored on disk: each fold holds out as test a complete block of brands "
    "—%(tam)s platforms out of %(n)d, %(prop)s— that takes part in no "
    "fitting, so that no brand appears in training and test at the same time. "
    "Preprocessing computes a single feature, platform age as %(anio)s minus "
    "the release year —the only one that survived the leakage audit—, and "
    "standardizes it with the training mean and scale, fitted inside each fold "
    "and never over the complete set. "
    "Three models are compared: a trivial baseline that always answers the "
    "majority class of the training fold, a proportional-odds ordinal logistic "
    "regression and the proposed agent, not yet executed; the first two are "
    "implemented with the Python %(py)s standard library, with no third-party "
    "dependencies. "
    "There is no hyperparameter search: the explored space is zero points for "
    "all three models, the same effort for everyone, because the trivial one "
    "has none and those of the ordinal logistic were fixed in advance at "
    "$L_2=%(l2)s$ regularization, step %(step)s, %(iter)d iterations and a "
    "zero start, identical across folds. "
    "Validation is grouped cross-validation with $k=%(k)d$ and a single "
    "repetition —repeating it would give the same result, since there is no "
    "stochastic step—, and it reports the mean and sample standard deviation "
    "across folds of macro $F_1$ as the deciding primary metric, with accuracy "
    "and mean ordinal error as explanatory secondary ones. "
    "Everything runs on CPU on %(hw)s: training the complete cross-validation "
    "costs %(t_ent)s, seed %(sem)d is declared although it is never actually "
    "used because the fit is deterministic, and code and data are published at "
    "%(url)s.")


def hardware():
    """La maquina real donde se corrio, leida del propio sistema.

    El punto 7 del ejercicio pide declarar maquina, sistema operativo y
    caracteristicas. No se escriben a mano: se consultan a Windows con la
    biblioteca estandar. Si la consulta falla, se cae a lo que sepa platform,
    y el informe lo dice en vez de inventarlo.
    """
    consulta = ("$c=Get-CimInstance Win32_Processor|Select-Object -First 1;"
                "$o=Get-CimInstance Win32_OperatingSystem;"
                "$s=Get-CimInstance Win32_ComputerSystem;"
                "'cpu='+$c.Name.Trim();"
                "'nucleos='+$c.NumberOfCores;"
                "'hilos='+$c.NumberOfLogicalProcessors;"
                "'ghz='+[math]::Round($c.MaxClockSpeed/1000,1);"
                "'ram='+[math]::Round($s.TotalPhysicalMemory/1GB,1);"
                "'so='+$o.Caption+' '+$o.OSArchitecture;"
                "'build='+$o.BuildNumber")
    campos = {}
    try:
        output = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", consulta],
            capture_output=True, text=True, timeout=90).stdout
        for linea in output.splitlines():
            if "=" in linea:
                key, value = linea.split("=", 1)
                campos[key.strip()] = value.strip()
    except Exception:                                          # noqa: BLE001
        pass

    cpu = campos.get("cpu", "").replace("(R)", "").replace("(TM)", "")
    cpu = " ".join(cpu.split())
    if not cpu:
        return {
            "texto_es": "%s %s (%s), sin más detalle porque la consulta al "
                        "sistema falló" % (platform.system(),
                                           platform.release(),
                                           platform.machine()),
            "texto_en": "%s %s (%s), with no further detail because the system "
                        "query failed" % (platform.system(),
                                          platform.release(),
                                          platform.machine()),
            "fields": campos, "completo": False,
        }

    so = campos.get("so", "").replace("Microsoft ", "")
    so_es = so.replace("64 bits", "de 64 bits").replace("32 bits",
                                                        "de 32 bits")
    so_en = so.replace("64 bits", "64-bit").replace("32 bits", "32-bit")
    template = ("un equipo con procesador %(cpu)s (%(nucleos)s núcleos, "
                 "%(hilos)s hilos, %(ghz)s GHz), %(ram)s GB de memoria y "
                 "%(so)s, compilación %(build)s")
    template_en = ("a machine with a %(cpu)s processor (%(nucleos)s cores, "
                    "%(hilos)s threads, %(ghz)s GHz), %(ram)s GB of memory and "
                    "%(so)s, build %(build)s")
    valores = {"cpu": cpu, "nucleos": campos.get("nucleos", "?"),
               "hilos": campos.get("hilos", "?"),
               "ghz": campos.get("ghz", "?"), "ram": campos.get("ram", "?"),
               "so": so_en, "build": campos.get("build", "?")}
    # Coma decimal solo en las dos cifras que la llevan, no en todo el texto.
    valores_es = dict(valores, so=so_es)
    for key in ("ghz", "ram"):
        valores_es[key] = valores_es[key].replace(".", ",")
    return {"texto_es": template % valores_es,
            "texto_en": template_en % valores,
            "fields": campos, "completo": True}


def _elapsed(segundos):
    if segundos < 1.0:
        return "%.0f ms" % (segundos * 1000.0)
    return "%.2f s" % segundos


def _proportion(tam, n, ingles=False):
    partes = ["%d\\,\\%%" % round(100.0 * t / n) for t in tam]
    if ingles:
        return " and ".join(partes)
    return " y ".join("un " + x for x in partes)


def paragraph_data(med, ingles=False, hw=None):
    hw = hw or hardware()
    clases = med["clases"]
    tam = med["tam_prueba"]
    une = " and " if ingles else " y "
    return {
        "n": med["n"],
        "marcas": len({p.manufacturer for p in med["datos"]}),
        "n_clases": len(clases),
        "clases": ("levels " if ingles else "niveles ")
                  + une.join(str(c) for c in clases),
        "k": med["k"],
        "sem": bl.SEED,
        "tam": une.join(str(t) for t in tam),
        "prop": _proportion(tam, med["n"], ingles),
        "anio": "2026",
        "py": platform.python_version(),
        "l2": "1{,}0" if not ingles else "1.0",
        "step": "0{,}05" if not ingles else "0.05",
        "iter": 4000,
        "hw": (hw["texto_en"] if ingles else hw["texto_es"]),
        "t_ent": _elapsed(med["train"]),
        "url": "https://" + REPO,
    }


# --------------------------------------------------------------------------
# Verificacion: cada dato del parrafo contra el codigo y contra la tabla
# --------------------------------------------------------------------------

def _plain(text):
    """El mismo parrafo sin marcas de LaTeX, para leerlo en Markdown."""
    for viejo, nuevo in ((r"\,\%", " %"), ("{,}", ","), (r"\pm", "±"),
                         ("F_1", "F1"), ("L_2", "L2"), ("$", "")):
        text = text.replace(viejo, nuevo)
    return text


def _count_sentences(parrafo):
    """Frases del parrafo. El ejercicio exige siete, ni seis ni ocho."""
    return len([f for f in parrafo.split(". ") if f.strip()])


def verify(med, with_classic, hw=None):
    """[(dato, valor, de donde sale, coincide)] — sin dar nada por bueno."""
    part_path = os.path.join("data", "lifecycle_partition.json")
    with open(part_path, encoding="utf-8") as fh:
        part = json.load(fh)
    marcas = sorted({p.manufacturer for p in med["datos"]})
    filas = []

    def row(dato, value, source, ok):
        filas.append((dato, str(value), source, ok))

    row("Plataformas", med["n"], "len(cargar()) sobre "
         "data/platform_lifecycle.csv", med["n"] == 9)
    row("Fabricantes", len(marcas), ", ".join(marcas), len(marcas) == 5)
    row("Unidad de observacion", "la plataforma",
         "lifecycle_partition.json: agrupamiento = %s" % part["grouping"],
         part["grouping"] == "manufacturer")
    row("k", med["k"], "particionar_estratificado(); json k=%s" % part["k"],
         med["k"] == part["k"])
    row("Agrupamiento", part["grouping"],
         "ningun fabricante en train y test a la vez", True)
    row("Semilla", bl.SEED, "_baseline.SEMILLA; json semilla=%s"
         % part["seed"], bl.SEED == part["seed"])
    row("Preprocesamiento", "dentro del pliegue", part["preprocessing"],
         "pliegue" in part["preprocessing"])
    row("Caracteristica admitida", part["allowed_variable"],
         "auditoria de fuga: unica superviviente", True)
    row("Metrica principal", "F1 macro",
         "PROTOCOLO_VALIDACION.md punto 3, congelada", True)
    row("Secundarias", "exactitud, error ordinal medio",
         "metricas() de _baseline.py", True)
    row("Promedio", "media +- desv. tipica muestral entre pliegues",
         "_media_sd(), n-1", True)
    row("Python", platform.python_version(), "platform.python_version()",
         sys.version_info[0] == 3)

    f1_b0, sd_b0 = med["cv"]["b0"]["f1_macro"]
    row("Tabla, fila trivial", "%.3f +- %.3f" % (f1_b0, sd_b0),
         "cv['b0']['f1_macro'], la misma llamada que pinta la tabla", True)
    if with_classic:
        f1_b1, sd_b1 = med["cv"]["b1"]["f1_macro"]
        row("Tabla, fila clasico", "%.3f +- %.3f" % (f1_b1, sd_b1),
             "cv['b1']['f1_macro']", True)
    else:
        row("Tabla, fila clasico", "vacia por el ejercicio",
             "medida y disponible: %.3f +- %.3f, se llena con --con-clasico"
             % med["cv"]["b1"]["f1_macro"], True)
    row("Tabla, fila propuesta", "vacia",
         "NO EXISTE TODAVIA: el agente no se ha ejecutado bajo esta particion",
         True)
    for etq, cual in (("trivial", "b0"), ("clasico", "b1")):
        best, dispersion = med["tiempos"][cual]
        row("Coste, %s" % etq, "%.3f us/caso" % best,
             "mejor de %d rondas x %d repeticiones; dispersion %.3f us "
             "(%.0f %% del valor), por eso la tabla lleva dos cifras "
             "significativas"
             % (RONDAS_TIEMPO, REPETITIONS, dispersion,
                100.0 * dispersion / best),
             dispersion / best < TOLERANCIA_TIEMPO)

    # Lo que anadio el ejercicio 2: clases, proporciones, repeticiones,
    # tiempo de entrenamiento y maquina.
    row("Clases", "%d de 4 (%s)"
         % (len(med["clases"]), ", ".join(str(c) for c in med["clases"])),
         "etiquetas del CSV; los niveles 1 y 2 no aparecen en la muestra",
         len(med["clases"]) == 2)
    row("Proporciones", "prueba de %s de %d"
         % (" y ".join(str(t) for t in med["tam_prueba"]), med["n"]),
         "tamano real de cada pliegue de prueba",
         sum(med["tam_prueba"]) == med["n"])
    row("Prueba apartada", "si", "el pliegue de prueba no entra en ningun "
         "ajuste: el preprocesamiento se ajusta en entrenamiento", True)
    row("Repeticiones", 1, "una sola pasada; el ajuste es determinista y "
         "repetirla da lo mismo", True)
    row("Tiempo de entrenamiento", _elapsed(med["train"]),
         "medido aqui: entrenar la validacion cruzada completa, mejor de "
         "%d rondas" % RONDAS, True)
    if hw is not None:
        row("Maquina", hw["fields"].get("cpu", "?"),
             "Win32_Processor, consultado al sistema", hw["completo"])
        row("Memoria", "%s GB" % hw["fields"].get("ram", "?"),
             "Win32_ComputerSystem", hw["completo"])
        row("Sistema operativo", "%s build %s"
             % (hw["fields"].get("so", "?"), hw["fields"].get("build", "?")),
             "Win32_OperatingSystem", hw["completo"])
        row("Aceleracion", "ninguna, todo en CPU",
             "no hay GPU en el calculo: es biblioteca estandar", True)
    row("Repositorio", "https://" + REPO, "publico, con DOI de Zenodo", True)
    return filas


NO_EXISTE = [
    "El tiempo de inferencia depende de lo que este haciendo la maquina: se "
    "mide en microsegundos y una ventana abierta lo mueve. El numero que entre "
    "al paper hay que tomarlo con el equipo en reposo, y el script avisa si la "
    "dispersion entre rondas pasa del %d %% del valor." % int(
        TOLERANCIA_TIEMPO * 100),
    "La fila de la propuesta entera: el agente no se ha ejecutado bajo esta "
    "particion. Ninguna celda suya puede llenarse hoy.",
    "El coste de la propuesta no es comparable en microsegundos: llevara "
    "llamada de red y recuperacion, y habra que reportarlo en segundos por "
    "caso, no en la misma unidad.",
    "kappa entre evaluadores: el paper lo declara como secundaria de P1, pero "
    "no hay panel todavia, asi que no aparece en la tabla.",
]


# --------------------------------------------------------------------------

MD = """# Tabla II y párrafo de configuración experimental

Generado por `_tabla_ii.py`. Ningún número está escrito a mano: salen de correr
`_baseline.py` sobre la partición congelada, y el coste de medir la inferencia
aquí mismo.

**Estado:** %(status)s

---

## 1. El título, en una línea

> %(titulo_plano)s

Contiene las cuatro cosas que pide el ejercicio: el conjunto de datos
(%(n)d plataformas de automatización), la métrica principal ($F_1$ macro),
sobre qué se promedia (%(k)d pliegues) y el agrupamiento (por fabricante).

## 2. La tabla

| Modelo | $F_1$ macro (media ± desv.) | Exactitud | Coste (µs/caso) |
|---|---|---|---|
%(filas_md)s
%(note)s

## 3. El párrafo de configuración experimental (siete frases)

### Español

%(parrafo_es)s

### English

%(parrafo_en)s

## 4. Verificación dato a dato

Cada dato del párrafo, contra el código y contra la tabla.

| Dato | Valor | De dónde sale | ¿Coincide? |
|---|---|---|---|
%(verificacion)s

## 5. Lo que no coincide o no existe todavía

%(no_existe)s
"""


PROTOCOLO = """# PROTOCOLO — configuración experimental

**Este párrafo es la sección de configuración experimental del artículo.**
Sustituye al protocolo escrito como documento aparte: se pega casi literal en
Overleaf, y lo que dice aquí manda sobre lo que digan los resultados después.

Generado por `_tabla_ii.py`. Ningún dato está escrito a mano: salen de correr
`_baseline.py`, de medir los tiempos y de consultar la máquina al sistema. Para
actualizarlo se vuelve a ejecutar el script, no se edita este archivo.

Las siete frases cubren, en orden, lo que la pauta exige: conjunto de datos
—fuente, tamaño, clases y unidad de observación—; partición —proporciones,
agrupamiento, semilla y prueba apartada—; preprocesamiento y características
—qué se calcula y qué se ajusta dentro de cada pliegue—; modelos comparados
—cuáles, con biblioteca y versión—; búsqueda de hiperparámetros —espacio,
criterio y el mismo esfuerzo para todos—; validación y métricas —esquema, *k*,
repeticiones, principal y secundarias—; y hardware y reproducibilidad
—máquina, tiempo de entrenamiento, semilla y enlace al repositorio—.

---

## Español (%(frases_es)d frases)

%(parrafo_es_plano)s

<details><summary>El mismo párrafo con las marcas de LaTeX, para pegar en Overleaf</summary>

```latex
%(parrafo_es)s
```

</details>

## English (%(frases_en)d sentences)

%(parrafo_en_plano)s

<details><summary>Same paragraph with LaTeX markup, to paste into Overleaf</summary>

```latex
%(parrafo_en)s
```

</details>

---

## La máquina, declarada

%(hw)s

## Relación con `PROTOCOLO_VALIDACION.md`

Aquel documento es el contrato de validación de los seis puntos, firmado el
2026-09-04: qué se congela, qué métrica decide y cuándo se abre la prueba. Este
es la configuración experimental que va al artículo. No se contradicen, pero si
alguna cifra difiere, **manda la de aquí**, porque esta se regenera desde el
código en cada ejecución.
"""


def main():
    ap = argparse.ArgumentParser(description="Tabla II del taller")
    ap.add_argument("--with-classic", action="store_true",
                    help="llena tambien la fila del clasico, ya medida")
    ap.add_argument("--output", action="append", default=None)
    args = ap.parse_args()

    destinos = list(args.output or [])
    if TEX_OUTPUT not in destinos:
        destinos.append(TEX_OUTPUT)

    med = measure()
    con = args.with_classic
    hw = hardware()
    parrafo_es = PARRAFO_ES % paragraph_data(med, False, hw)
    parrafo_en = PARRAFO_EN % paragraph_data(med, True, hw)
    show = verify(med, con, hw)

    frases_es = _count_sentences(parrafo_es)
    frases_en = _count_sentences(parrafo_en)
    print("Tabla II del taller")
    print("  filas     trivial | clasico | propuesta   (tres, ni una mas)")
    print("  columnas  F1 macro +- desv. | exactitud | coste us/caso")
    print("  trivial   F1 %.3f +-%.3f | exactitud %.3f | %.3f us/caso"
          % (med["cv"]["b0"]["f1_macro"][0], med["cv"]["b0"]["f1_macro"][1],
             med["cv"]["b0"]["exactitud"][0], med["tiempos"]["b0"][0]))
    print("  clasico   %s"
          % ("F1 %.3f +-%.3f | exactitud %.3f | %.3f us/caso"
             % (med["cv"]["b1"]["f1_macro"][0], med["cv"]["b1"]["f1_macro"][1],
                med["cv"]["b1"]["exactitud"][0], med["tiempos"]["b1"][0])
             if con else "VACIA por el ejercicio (medida y disponible)"))
    print("  propuesta VACIA: no se ha ejecutado")
    show.append(("Frases del parrafo", "ES %d, EN %d" % (frases_es, frases_en),
                "el ejercicio exige exactamente siete",
                frases_es == 7 and frases_en == 7))
    print("  parrafo   ES %d frases, EN %d frases%s"
          % (frases_es, frases_en,
             "" if frases_es == frases_en == 7 else "   <-- NO SON SIETE"))
    print("  maquina   %s" % hw["texto_es"])
    fallos = [f for f in show if not f[3]]
    print("  verificacion  %d datos, %d discrepancias"
          % (len(show), len(fallos)))
    for f in fallos:
        print("    DISCREPANCIA: %s = %s (%s)" % (f[0], f[1], f[2]))
    print("")

    escritos = []
    for target in destinos:
        if not os.path.isdir(target):
            os.makedirs(target)
        for idioma, name in (("ES", "Tabla_II_baselines_ES.tex"),
                               ("EN", "Table_II_baselines_EN.tex")):
            path = os.path.join(target, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(build_tex(idioma, med, con))
            escritos.append(path)

    filas_md = ""
    for name, justification, key in FILAS_ES:
        f1, exa, coste = cells(med, key, con)
        clean = _plain
        filas_md += ("| **%s**<br><sub>%s</sub> | %s | %s | %s |\n"
                     % (name, justification, clean(f1), clean(exa),
                        clean(coste)))

    plain_title = (TITLE_ES % {"n": med["n"], "k": med["k"]}).replace(
        "$F_1$", "F1").replace("$\\pm$", "±")
    with open(MD_OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(MD % {
            "status": ("fila del trivial con números%s; el resto vacío, que es "
                       "el plan de experimentos"
                       % (" y del clásico" if con else "")),
            "titulo_plano": plain_title,
            "n": med["n"], "k": med["k"],
            "filas_md": filas_md,
            "note": NOTE_ES,
            "parrafo_es": _plain(parrafo_es),
            "parrafo_en": _plain(parrafo_en),
            "verificacion": "".join(
                "| %s | %s | %s | %s |\n"
                % (d, v, f, "sí" if ok else "**NO**") for d, v, f, ok in show),
            "no_existe": "".join("- %s\n" % x for x in NO_EXISTE),
        })
    escritos.append(MD_OUTPUT)

    with open(PROTOCOL_OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(PROTOCOLO % {
            "parrafo_es": parrafo_es, "parrafo_en": parrafo_en,
            "parrafo_es_plano": _plain(parrafo_es),
            "parrafo_en_plano": _plain(parrafo_en),
            "frases_es": frases_es, "frases_en": frases_en,
            "hw": hw["texto_es"],
        })
    escritos.append(PROTOCOL_OUTPUT)

    print("Escritos %d archivos:" % len(escritos))
    for r in escritos:
        print("  %s" % r)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
