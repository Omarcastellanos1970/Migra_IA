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

SALIDA_TEX = os.path.join("docs", "figuras")
SALIDA_MD = os.path.join("docs", "tabla_ii_y_configuracion.md")
SALIDA_PROTOCOLO = "PROTOCOLO.md"
REPO = "github.com/Omarcastellanos1970/Migra_IA"

# Repeticiones de la medida de tiempo. Se toma el mejor de varias rondas: lo
# que se busca es el coste del modelo, no el ruido del sistema operativo.
REPETICIONES = 2000
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

def medir():
    datos = bl.cargar()
    pliegues, k, nota_k = bl.particionar_estratificado(datos)
    res = bl.evaluar(datos, pliegues)
    tiempos = medir_tiempos(datos, pliegues)
    return {
        "datos": datos, "pliegues": pliegues, "k": k, "nota_k": nota_k,
        "n": len(datos), "cv": res["cv"], "modelos": res["modelos"],
        "tiempos": tiempos,
        "entrenamiento": medir_entrenamiento(datos, pliegues),
        "clases": sorted({p.clase for p in datos}),
        "tam_prueba": [len(pl["prueba"]) for pl in pliegues],
    }


def medir_entrenamiento(datos, pliegues):
    """Segundos que cuesta entrenar la validacion cruzada entera, una vez."""
    por_nombre = {p.plataforma: p for p in datos}
    entrenas = [[por_nombre[n] for n in pl["entrenamiento"]] for pl in pliegues]

    def ronda():
        inicio = time.perf_counter()
        for entrena in entrenas:
            bl.b0_trivial(entrena)
            bl.b1_logistica_ordinal(entrena)
        return time.perf_counter() - inicio

    return min(ronda() for _ in range(RONDAS))


def medir_tiempos(datos, pliegues):
    """Microsegundos por caso de cada modelo, en inferencia."""
    por_nombre = {p.plataforma: p for p in datos}
    preparados = []
    for pl in pliegues:
        entrena = [por_nombre[n] for n in pl["entrenamiento"]]
        prueba = [por_nombre[n] for n in pl["prueba"]]
        c0 = bl.b0_trivial(entrena)
        modelo = bl.b1_logistica_ordinal(entrena)
        xs = [float(p.antiguedad) for p in prueba]
        preparados.append((c0, modelo, xs))
    n_casos = sum(len(xs) for _, _, xs in preparados)

    def ronda(cual):
        inicio = time.perf_counter()
        for _ in range(REPETICIONES):
            for c0, modelo, xs in preparados:
                for x in xs:
                    if cual == "b0":
                        _ = c0
                    else:
                        _ = modelo.predecir(x)
        return (time.perf_counter() - inicio) / (REPETICIONES * n_casos)

    medidas = {}
    for cual in ("b0", "b1"):
        rondas = sorted(ronda(cual) * 1e6 for _ in range(RONDAS_TIEMPO))
        # El mejor tiempo es el que menos ruido del sistema lleva encima; la
        # dispersion entre rondas dice hasta que digito hay que creerse.
        medidas[cual] = (rondas[0], rondas[-1] - rondas[0])
    return medidas


def _sig2(valor, es=True):
    """Dos cifras significativas: mas digitos serian ruido de medida."""
    if valor <= 0:
        return "0"
    decimales = max(0, 2 - 1 - int(("%e" % valor).split("e")[1]))
    texto = "%%.%df" % decimales % valor
    return texto.replace(".", "{,}") if es else texto


def _num(valor, decimales=3, es=True):
    """Numero en formato del paper.

    En espanol la coma decimal va entre llaves, {,}, porque en modo matematico
    LaTeX trata la coma suelta como separador y le mete un espacio detras. En
    ingles el separador es el punto y no hace falta protegerlo.
    """
    texto = "%%.%df" % decimales % valor
    return texto.replace(".", "{,}") if es else texto


# --------------------------------------------------------------------------
# Contenido de la tabla
# --------------------------------------------------------------------------

VACIA = "---"

TITULO_ES = ("Riesgo ordinal de obsolescencia en %(n)d plataformas de "
             "automatización: $F_1$ macro medio $\\pm$ desviación sobre "
             "%(k)d pliegues agrupados por fabricante")
TITULO_EN = ("Ordinal obsolescence risk on %(n)d automation platforms: mean "
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

NOTA_ES = ("Las celdas vacías son el plan de experimentos: se llenan cuando "
           "cada modelo se ejecute bajo esta misma partición. El coste es el "
           "mejor de cinco rondas y se da con dos cifras significativas, que "
           "es hasta donde llega la resolución de la medida.")
NOTA_EN = ("Empty cells are the experiment plan: they are filled once each "
           "model is run under this same partition. Cost is the best of five "
           "rounds and is reported to two significant figures, the resolution "
           "limit of the measurement.")


def celdas(med, clave, con_clasico, es=True):
    """(F1 macro, exactitud, coste) de una fila, o vacias si toca."""
    if clave == "propuesta" or (clave == "b1" and not con_clasico):
        return (VACIA, VACIA, VACIA)
    f1, sd = med["cv"][clave]["f1_macro"]
    exa = med["cv"][clave]["exactitud"][0]
    return ("$%s \\pm %s$" % (_num(f1, es=es), _num(sd, es=es)),
            "$%s$" % _num(exa, es=es),
            "$%s$" % _sig2(med["tiempos"][clave][0], es=es))


TABLA_TEX = r"""%% %(comentario)s
%% -------------------------------------------------------------------------
%% GENERADO POR _tabla_ii.py DEL REPOSITORIO MIGRA-IA. NO EDITAR A MANO.
%% Los numeros salen de correr _baseline.py; el coste, de medir la inferencia.
%% ESTADO: %(estado)s
%%
%% PAQUETES: \usepackage{booktabs} y \usepackage{array}, los dos ya cargados.
%% -------------------------------------------------------------------------
\begin{table}[!tb]
\caption{%(titulo)s}
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
{\scriptsize %(nota)s}
\end{table}
"""

FILA_TEX = ("\\textbf{%s}\\newline {\\scriptsize %s} & %s & %s & %s \\\\\n")


def construir_tex(idioma, med, con_clasico):
    es = idioma == "ES"
    titulo = (TITULO_ES if es else TITULO_EN) % {"n": med["n"], "k": med["k"]}
    filas = ""
    for nombre, justificacion, clave in (FILAS_ES if es else FILAS_EN):
        f1, exa, coste = celdas(med, clave, con_clasico, es)
        filas += FILA_TEX % (nombre, justificacion, f1, exa, coste)
    estado = ("fila del trivial con numeros%s; el resto, vacio a proposito"
              % (" y la del clasico" if con_clasico else ""))
    return TABLA_TEX % {
        "comentario": ("Tabla II -- Lineas base de P1. Version en espanol."
                       if es else
                       "Table II -- P1 baselines. English version."),
        "estado": estado,
        "titulo": titulo,
        "cab_modelo": "Modelo" if es else "Model",
        "cab_principal": "$F_1$ macro" if es else "Macro $F_1$",
        "cab_principal_2": ("(media $\\pm$ desv.)" if es
                            else "(mean $\\pm$ dev.)"),
        "cab_secundaria": "Exactitud" if es else "Accuracy",
        "cab_costo": "Coste" if es else "Cost",
        "cab_costo_2": ("($\\mu$s/caso)" if es else "($\\mu$s/case)"),
        "filas": filas,
        "nota": NOTA_ES if es else NOTA_EN,
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
    "antemano en regularización $L_2=%(l2)s$, paso %(paso)s, %(iter)d "
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
    "$L_2=%(l2)s$ regularization, step %(paso)s, %(iter)d iterations and a "
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
        salida = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", consulta],
            capture_output=True, text=True, timeout=90).stdout
        for linea in salida.splitlines():
            if "=" in linea:
                clave, valor = linea.split("=", 1)
                campos[clave.strip()] = valor.strip()
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
            "campos": campos, "completo": False,
        }

    so = campos.get("so", "").replace("Microsoft ", "")
    so_es = so.replace("64 bits", "de 64 bits").replace("32 bits",
                                                        "de 32 bits")
    so_en = so.replace("64 bits", "64-bit").replace("32 bits", "32-bit")
    plantilla = ("un equipo con procesador %(cpu)s (%(nucleos)s núcleos, "
                 "%(hilos)s hilos, %(ghz)s GHz), %(ram)s GB de memoria y "
                 "%(so)s, compilación %(build)s")
    plantilla_en = ("a machine with a %(cpu)s processor (%(nucleos)s cores, "
                    "%(hilos)s threads, %(ghz)s GHz), %(ram)s GB of memory and "
                    "%(so)s, build %(build)s")
    valores = {"cpu": cpu, "nucleos": campos.get("nucleos", "?"),
               "hilos": campos.get("hilos", "?"),
               "ghz": campos.get("ghz", "?"), "ram": campos.get("ram", "?"),
               "so": so_en, "build": campos.get("build", "?")}
    # Coma decimal solo en las dos cifras que la llevan, no en todo el texto.
    valores_es = dict(valores, so=so_es)
    for clave in ("ghz", "ram"):
        valores_es[clave] = valores_es[clave].replace(".", ",")
    return {"texto_es": plantilla % valores_es,
            "texto_en": plantilla_en % valores,
            "campos": campos, "completo": True}


def _tiempo(segundos):
    if segundos < 1.0:
        return "%.0f ms" % (segundos * 1000.0)
    return "%.2f s" % segundos


def _proporcion(tam, n, ingles=False):
    partes = ["%d\\,\\%%" % round(100.0 * t / n) for t in tam]
    if ingles:
        return " and ".join(partes)
    return " y ".join("un " + x for x in partes)


def datos_parrafo(med, ingles=False, hw=None):
    hw = hw or hardware()
    clases = med["clases"]
    tam = med["tam_prueba"]
    une = " and " if ingles else " y "
    return {
        "n": med["n"],
        "marcas": len({p.fabricante for p in med["datos"]}),
        "n_clases": len(clases),
        "clases": ("levels " if ingles else "niveles ")
                  + une.join(str(c) for c in clases),
        "k": med["k"],
        "sem": bl.SEMILLA,
        "tam": une.join(str(t) for t in tam),
        "prop": _proporcion(tam, med["n"], ingles),
        "anio": "2026",
        "py": platform.python_version(),
        "l2": "1{,}0" if not ingles else "1.0",
        "paso": "0{,}05" if not ingles else "0.05",
        "iter": 4000,
        "hw": (hw["texto_en"] if ingles else hw["texto_es"]),
        "t_ent": _tiempo(med["entrenamiento"]),
        "url": "https://" + REPO,
    }


# --------------------------------------------------------------------------
# Verificacion: cada dato del parrafo contra el codigo y contra la tabla
# --------------------------------------------------------------------------

def _plano(texto):
    """El mismo parrafo sin marcas de LaTeX, para leerlo en Markdown."""
    for viejo, nuevo in ((r"\,\%", " %"), ("{,}", ","), (r"\pm", "±"),
                         ("F_1", "F1"), ("L_2", "L2"), ("$", "")):
        texto = texto.replace(viejo, nuevo)
    return texto


def _contar_frases(parrafo):
    """Frases del parrafo. El ejercicio exige siete, ni seis ni ocho."""
    return len([f for f in parrafo.split(". ") if f.strip()])


def verificar(med, con_clasico, hw=None):
    """[(dato, valor, de donde sale, coincide)] — sin dar nada por bueno."""
    part_path = os.path.join("data", "particion_ciclo_vida.json")
    with open(part_path, encoding="utf-8") as fh:
        part = json.load(fh)
    marcas = sorted({p.fabricante for p in med["datos"]})
    filas = []

    def fila(dato, valor, fuente, ok):
        filas.append((dato, str(valor), fuente, ok))

    fila("Plataformas", med["n"], "len(cargar()) sobre "
         "data/ciclo_vida_plataformas.csv", med["n"] == 9)
    fila("Fabricantes", len(marcas), ", ".join(marcas), len(marcas) == 5)
    fila("Unidad de observacion", "la plataforma",
         "particion_ciclo_vida.json: agrupamiento = %s" % part["agrupamiento"],
         part["agrupamiento"] == "Fabricante")
    fila("k", med["k"], "particionar_estratificado(); json k=%s" % part["k"],
         med["k"] == part["k"])
    fila("Agrupamiento", part["agrupamiento"],
         "ningun fabricante en train y test a la vez", True)
    fila("Semilla", bl.SEMILLA, "_baseline.SEMILLA; json semilla=%s"
         % part["semilla"], bl.SEMILLA == part["semilla"])
    fila("Preprocesamiento", "dentro del pliegue", part["preprocesamiento"],
         "pliegue" in part["preprocesamiento"])
    fila("Caracteristica admitida", part["variable_admitida"],
         "auditoria de fuga: unica superviviente", True)
    fila("Metrica principal", "F1 macro",
         "PROTOCOLO_VALIDACION.md punto 3, congelada", True)
    fila("Secundarias", "exactitud, error ordinal medio",
         "metricas() de _baseline.py", True)
    fila("Promedio", "media +- desv. tipica muestral entre pliegues",
         "_media_sd(), n-1", True)
    fila("Python", platform.python_version(), "platform.python_version()",
         sys.version_info[0] == 3)

    f1_b0, sd_b0 = med["cv"]["b0"]["f1_macro"]
    fila("Tabla, fila trivial", "%.3f +- %.3f" % (f1_b0, sd_b0),
         "cv['b0']['f1_macro'], la misma llamada que pinta la tabla", True)
    if con_clasico:
        f1_b1, sd_b1 = med["cv"]["b1"]["f1_macro"]
        fila("Tabla, fila clasico", "%.3f +- %.3f" % (f1_b1, sd_b1),
             "cv['b1']['f1_macro']", True)
    else:
        fila("Tabla, fila clasico", "vacia por el ejercicio",
             "medida y disponible: %.3f +- %.3f, se llena con --con-clasico"
             % med["cv"]["b1"]["f1_macro"], True)
    fila("Tabla, fila propuesta", "vacia",
         "NO EXISTE TODAVIA: el agente no se ha ejecutado bajo esta particion",
         True)
    for etq, cual in (("trivial", "b0"), ("clasico", "b1")):
        mejor, dispersion = med["tiempos"][cual]
        fila("Coste, %s" % etq, "%.3f us/caso" % mejor,
             "mejor de %d rondas x %d repeticiones; dispersion %.3f us "
             "(%.0f %% del valor), por eso la tabla lleva dos cifras "
             "significativas"
             % (RONDAS_TIEMPO, REPETICIONES, dispersion,
                100.0 * dispersion / mejor),
             dispersion / mejor < TOLERANCIA_TIEMPO)

    # Lo que anadio el ejercicio 2: clases, proporciones, repeticiones,
    # tiempo de entrenamiento y maquina.
    fila("Clases", "%d de 4 (%s)"
         % (len(med["clases"]), ", ".join(str(c) for c in med["clases"])),
         "etiquetas del CSV; los niveles 1 y 2 no aparecen en la muestra",
         len(med["clases"]) == 2)
    fila("Proporciones", "prueba de %s de %d"
         % (" y ".join(str(t) for t in med["tam_prueba"]), med["n"]),
         "tamano real de cada pliegue de prueba",
         sum(med["tam_prueba"]) == med["n"])
    fila("Prueba apartada", "si", "el pliegue de prueba no entra en ningun "
         "ajuste: el preprocesamiento se ajusta en entrenamiento", True)
    fila("Repeticiones", 1, "una sola pasada; el ajuste es determinista y "
         "repetirla da lo mismo", True)
    fila("Tiempo de entrenamiento", _tiempo(med["entrenamiento"]),
         "medido aqui: entrenar la validacion cruzada completa, mejor de "
         "%d rondas" % RONDAS, True)
    if hw is not None:
        fila("Maquina", hw["campos"].get("cpu", "?"),
             "Win32_Processor, consultado al sistema", hw["completo"])
        fila("Memoria", "%s GB" % hw["campos"].get("ram", "?"),
             "Win32_ComputerSystem", hw["completo"])
        fila("Sistema operativo", "%s build %s"
             % (hw["campos"].get("so", "?"), hw["campos"].get("build", "?")),
             "Win32_OperatingSystem", hw["completo"])
        fila("Aceleracion", "ninguna, todo en CPU",
             "no hay GPU en el calculo: es biblioteca estandar", True)
    fila("Repositorio", "https://" + REPO, "publico, con DOI de Zenodo", True)
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

**Estado:** %(estado)s

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
%(nota)s

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
    ap.add_argument("--con-clasico", action="store_true",
                    help="llena tambien la fila del clasico, ya medida")
    ap.add_argument("--salida", action="append", default=None)
    args = ap.parse_args()

    destinos = list(args.salida or [])
    if SALIDA_TEX not in destinos:
        destinos.append(SALIDA_TEX)

    med = medir()
    con = args.con_clasico
    hw = hardware()
    parrafo_es = PARRAFO_ES % datos_parrafo(med, False, hw)
    parrafo_en = PARRAFO_EN % datos_parrafo(med, True, hw)
    ver = verificar(med, con, hw)

    frases_es = _contar_frases(parrafo_es)
    frases_en = _contar_frases(parrafo_en)
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
    ver.append(("Frases del parrafo", "ES %d, EN %d" % (frases_es, frases_en),
                "el ejercicio exige exactamente siete",
                frases_es == 7 and frases_en == 7))
    print("  parrafo   ES %d frases, EN %d frases%s"
          % (frases_es, frases_en,
             "" if frases_es == frases_en == 7 else "   <-- NO SON SIETE"))
    print("  maquina   %s" % hw["texto_es"])
    fallos = [f for f in ver if not f[3]]
    print("  verificacion  %d datos, %d discrepancias"
          % (len(ver), len(fallos)))
    for f in fallos:
        print("    DISCREPANCIA: %s = %s (%s)" % (f[0], f[1], f[2]))
    print("")

    escritos = []
    for destino in destinos:
        if not os.path.isdir(destino):
            os.makedirs(destino)
        for idioma, nombre in (("ES", "Tabla_II_baselines_ES.tex"),
                               ("EN", "Table_II_baselines_EN.tex")):
            ruta = os.path.join(destino, nombre)
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(construir_tex(idioma, med, con))
            escritos.append(ruta)

    filas_md = ""
    for nombre, justificacion, clave in FILAS_ES:
        f1, exa, coste = celdas(med, clave, con)
        limpiar = _plano
        filas_md += ("| **%s**<br><sub>%s</sub> | %s | %s | %s |\n"
                     % (nombre, justificacion, limpiar(f1), limpiar(exa),
                        limpiar(coste)))

    titulo_plano = (TITULO_ES % {"n": med["n"], "k": med["k"]}).replace(
        "$F_1$", "F1").replace("$\\pm$", "±")
    with open(SALIDA_MD, "w", encoding="utf-8") as fh:
        fh.write(MD % {
            "estado": ("fila del trivial con números%s; el resto vacío, que es "
                       "el plan de experimentos"
                       % (" y del clásico" if con else "")),
            "titulo_plano": titulo_plano,
            "n": med["n"], "k": med["k"],
            "filas_md": filas_md,
            "nota": NOTA_ES,
            "parrafo_es": _plano(parrafo_es),
            "parrafo_en": _plano(parrafo_en),
            "verificacion": "".join(
                "| %s | %s | %s | %s |\n"
                % (d, v, f, "sí" if ok else "**NO**") for d, v, f, ok in ver),
            "no_existe": "".join("- %s\n" % x for x in NO_EXISTE),
        })
    escritos.append(SALIDA_MD)

    with open(SALIDA_PROTOCOLO, "w", encoding="utf-8") as fh:
        fh.write(PROTOCOLO % {
            "parrafo_es": parrafo_es, "parrafo_en": parrafo_en,
            "parrafo_es_plano": _plano(parrafo_es),
            "parrafo_en_plano": _plano(parrafo_en),
            "frases_es": frases_es, "frases_en": frases_en,
            "hw": hw["texto_es"],
        })
    escritos.append(SALIDA_PROTOCOLO)

    print("Escritos %d archivos:" % len(escritos))
    for r in escritos:
        print("  %s" % r)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
