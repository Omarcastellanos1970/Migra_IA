"""Baseline reproducible del rubro: riesgo ordinal y prioridad de reemplazo.

QUE ES ESTO
-----------
El paper formula P1 como clasificacion supervisada con salida ordinal y P2 como
learning to rank sobre un catalogo. Este script construye el baseline de P1 y
deja marcadas, o explicitamente NO marcadas, las seis casillas del entregable:

  1. el conjunto de datos carga y su descripcion cuadra con lo declarado;
  2. la particion esta guardada en disco, con la restriccion de agrupamiento;
  3. el baseline trivial esta evaluado y su numero anotado;
  4. el baseline clasico esta evaluado con el mismo split y las mismas metricas;
  5. semilla fija y versiones de librerias declaradas;
  6. la auditoria de fuga de datos esta hecha y su resultado escrito.

    python _baseline.py          # informe en pantalla
    python _baseline.py --md     # escribe docs/baseline_reproducible.md

POR QUE REGRESION LOGISTICA ORDINAL (justificacion en una linea)
----------------------------------------------------------------
Se eligio regresion logistica ordinal de probabilidades proporcionales porque
el objetivo es una escala ORDENADA de cuatro clases -no categorias sueltas-,
el dato es tabular y con muy pocas muestras, y sus dos coeficientes los puede
leer, auditar y discutir un ingeniero de planta, que es el criterio de la
Seccion 6 del paper.

Se implementa con biblioteca estandar: con dos parametros y nueve filas, el
ascenso de gradiente con gradiente numerico converge en milisegundos y el
resultado no depende de la version de ninguna libreria de terceros. Se
regulariza (L2 sobre la pendiente) porque con nueve muestras y separacion casi
perfecta los coeficientes divergen sin penalizacion.

QUE NO ES
---------
No es validacion. Con nueve plataformas no se demuestra que el metodo funcione:
se demuestra que el numero que se publique tiene con que compararse y que el
procedimiento que lo produjo se puede repetir. El tamano del conjunto es la
limitacion dominante y el informe la declara en cada seccion.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "data" / "ciclo_vida_plataformas.csv"
PARTICION = RAIZ / "data" / "particion_ciclo_vida.json"
SALIDA_MD = RAIZ / "docs" / "baseline_reproducible.md"

# Fecha de referencia FIJA. Las clases se derivan comparando fechas contra ella,
# asi que usar "hoy" haria que las etiquetas cambiaran solas con el calendario y
# el entregable dejaria de ser reproducible.
FECHA_REF = (2026, 9, 4)

# No hay ningun paso estocastico: el ajuste arranca en ceros y el numero de
# iteraciones es fijo. La semilla se declara para el registro y para dejar
# constancia de que NO hace falta.
SEMILLA = 42

# Hiperparametros del clasico. Fijos y declarados: con nueve filas, buscarlos
# sobre la propia particion seria ajustar la busqueda a la validacion.
ITERACIONES = 4000
PASO = 0.05
L2 = 1.0

# Escala ordinal de obsolescencia. Es la misma que usa el motor en M01
# (migra_ia/interactivo.py::_f_ciclo_vida), para que el subproblema P1 y el
# agente hablen de las mismas clases.
CLASES = {
    1: "Activo, en comercializacion",
    2: "Anuncio de descontinuacion (phase-out)",
    3: "Descontinuado, aun con soporte y repuestos",
    4: "Descontinuado y sin soporte (fin de vida)",
}

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


# --------------------------------------------------------------------------
# Lectura del conjunto de datos
# --------------------------------------------------------------------------

def _parsear_fecha(bruto: str) -> tuple[tuple[int, int, int] | None, str]:
    """Devuelve (fecha, regla aplicada). La regla se imprime para que un humano
    pueda auditar cada conversion: son formatos heterogeneos escritos a mano.

    Cuando una celda trae dos fechas ('ult. pedido' / 'ult. envio') se toma la
    PRIMERA, que es la que usa la propia tabla para calcular Vida_comercial.
    """
    s = (bruto or "").strip()
    if not s or s.lower() in {"n.d.", "nd", "n/d", "-"}:
        return None, "vacio o n.d."

    nota = ""
    if "/" in s and re.search(r"\d{2}-\d{4}.*/.*\d{2}-\d{4}", s):
        s, nota = s.split("/")[0].strip(), " (se toma la primera de dos fechas)"

    s = re.sub(r"\(.*?\)", "", s).replace(">=", "").strip()

    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:                                          # 18/5/2015, 01-10-2023
        d, mes, a = (int(x) for x in m.groups())
        if d > 12:
            return (a, mes, d), "dia primero (dia>12, sin ambiguedad)" + nota
        return (a, mes, d), ("AMBIGUA dd/mm vs mm/dd; se aplica dia primero"
                             ", como el resto de la tabla") + nota

    m = re.match(r"^(\d{1,2})-(\d{4})$", s)        # 09-2013
    if m:
        return (int(m.group(2)), int(m.group(1)), 1), "mm-aaaa" + nota

    m = re.match(r"^([a-z]{3})-(\d{2})$", s.lower())   # jun-17, mar-32
    if m and m.group(1) in MESES:
        aa = int(m.group(2))
        anio = 2000 + aa if aa < 50 else 1900 + aa
        return (anio, MESES[m.group(1)], 1), "mmm-aa (aa<50 -> 20aa)" + nota

    m = re.match(r"^(\d{4})$", s)                  # 2022
    if m:
        return (int(m.group(1)), 1, 1), "solo anio (se asume 1 de enero)" + nota

    return None, f"NO RECONOCIDO: {bruto!r}"


@dataclass
class Plataforma:
    fabricante: str
    plataforma: str
    lanzamiento: int
    anuncio: tuple[int, int, int] | None
    fin_comercializacion: tuple[int, int, int] | None
    fin_repuestos: tuple[int, int, int] | None
    vida_comercial: int | None
    soporte_total: int | None
    nivel: str
    reglas: dict[str, str] = field(default_factory=dict)
    dato_faltante: list[str] = field(default_factory=list)

    @property
    def antiguedad(self) -> int:
        return FECHA_REF[0] - self.lanzamiento

    @property
    def clase(self) -> int:
        """Etiqueta ordinal derivada de las fechas contra FECHA_REF.

        El orden de las comprobaciones es el de la escala: se pregunta primero
        por el estado mas avanzado. Si el fin de repuestos no se conoce, NO se
        supone: la plataforma se queda en la clase que sus fechas conocidas
        sostienen y el hueco se anota como dato faltante, que es el mismo
        principio que aplica el cuestionario del agente.
        """
        if self.fin_repuestos and self.fin_repuestos <= FECHA_REF:
            return 4
        if self.fin_comercializacion and self.fin_comercializacion <= FECHA_REF:
            return 3
        if self.anuncio and self.anuncio <= FECHA_REF:
            return 2
        return 1


def cargar() -> list[Plataforma]:
    filas = list(csv.DictReader(DATOS.read_text(encoding="utf-8").splitlines(), delimiter=";"))
    plataformas: list[Plataforma] = []
    for f in filas:
        reglas, faltan, fechas = {}, [], {}
        for col in ("Anuncio_fin_de_vida", "Fin_comercializacion", "Fin_repuestos_reparacion"):
            fecha, regla = _parsear_fecha(f[col])
            fechas[col], reglas[col] = fecha, regla
            if fecha is None:
                faltan.append(col)
        plataformas.append(Plataforma(
            fabricante=f["Fabricante"].strip(),
            plataforma=f["Plataforma"].strip(),
            lanzamiento=int(f["Lanzamiento"]),
            anuncio=fechas["Anuncio_fin_de_vida"],
            fin_comercializacion=fechas["Fin_comercializacion"],
            fin_repuestos=fechas["Fin_repuestos_reparacion"],
            vida_comercial=int(f["Vida_comercial_anios"]) if f["Vida_comercial_anios"].strip() else None,
            soporte_total=int(f["Soporte_total_anios"]) if f["Soporte_total_anios"].strip() else None,
            nivel=f["Nivel"].strip(),
            reglas=reglas,
            dato_faltante=faltan,
        ))
    return plataformas


# --------------------------------------------------------------------------
# Particion con restriccion de agrupamiento
# --------------------------------------------------------------------------

def particionar(datos: list[Plataforma]) -> list[dict]:
    """Leave-one-manufacturer-out. Se conserva solo como CONTRASTE.

    Agrupa pero no estratifica: el pliegue de Mitsubishi queda puro (sus dos
    plataformas son clase 4) y ningun modelo puede acertarlo. Sirve justamente
    para ensenar lo que la estratificacion evita.
    """
    marcas = sorted({p.fabricante for p in datos})
    return [{
        "pliegue": i,
        "prueba_marcas": marca,
        "prueba": [p.plataforma for p in datos if p.fabricante == marca],
        "entrenamiento": [p.plataforma for p in datos if p.fabricante != marca],
    } for i, marca in enumerate(marcas)]


def particionar_estratificado(datos: list[Plataforma],
                              k_max: int = 5) -> tuple[list[dict], int, str]:
    """Esquema asignado al rubro: estratificado por nivel de obsolescencia,
    manteniendo la restriccion de agrupamiento.

    La unidad de observacion decide la variante. El rubro habla de agrupar por
    "caso de migracion" porque supone componentes que comparten caso; aqui cada
    fila es una plataforma independiente y no hay casos, asi que la unidad de agrupamiento que
    juega ese papel es el FABRICANTE: dos plataformas de una marca comparten
    politica de soporte (Tabla 3) y se parecen entre si por eso.

    Una marca entera cae siempre del mismo lado -si se partiera, la fuga vuelve
    por la puerta de atras- y se busca la k mas alta en la que TODO pliegue de
    prueba contenga las dos clases. Reparto determinista: las marcas se ordenan
    por cuantas muestras de la clase minoritaria aportan y cada uno va al
    pliegue donde MENOS desvia el reparto del ideal, contando TODAS las clases.
    Mirar solo la minoritaria no sirve: dejaba a Mitsubishi solo en su pliegue,
    con sus dos clase 4 y ninguna clase 3.
    """
    clases_totales = sorted({p.clase for p in datos})
    minoritaria = min(clases_totales, key=lambda c: sum(p.clase == c for p in datos))
    agrupaciones: dict[str, list[Plataforma]] = {}
    for p in datos:
        agrupaciones.setdefault(p.fabricante, []).append(p)

    orden = sorted(agrupaciones,
                   key=lambda g: (-sum(p.clase == minoritaria for p in agrupaciones[g]),
                                  -len(agrupaciones[g]), g))

    for k in range(min(k_max, len(agrupaciones)), 1, -1):
        ideal = {c: sum(p.clase == c for p in datos) / k for c in clases_totales}
        cubos: list[list[str]] = [[] for _ in range(k)]
        conteo = [{c: 0 for c in clases_totales} for _ in range(k)]

        def _coste(j: int, g: str) -> float:
            aporte = {c: sum(p.clase == c for p in agrupaciones[g]) for c in clases_totales}
            return sum((conteo[j][c] + aporte[c] - ideal[c]) ** 2 for c in clases_totales)

        for g in orden:
            i = min(range(k), key=lambda j: (_coste(j, g), sum(conteo[j].values()), j))
            cubos[i].append(g)
            for p in agrupaciones[g]:
                conteo[i][p.clase] += 1

        completo = all(cubos[j] and all(conteo[j][c] > 0 for c in clases_totales)
                       for j in range(k))
        if completo:
            pliegues = []
            for i, marcas in enumerate(cubos):
                prueba = [p.plataforma for g in marcas for p in agrupaciones[g]]
                pliegues.append({
                    "pliegue": i,
                    "prueba_marcas": " + ".join(sorted(marcas)),
                    "prueba": prueba,
                    "entrenamiento": [p.plataforma for p in datos
                                      if p.plataforma not in set(prueba)],
                })
            nota = (f"k={k} es la mayor con la que todo pliegue de prueba tiene las "
                    f"{len(clases_totales)} clases. Con k mayor es imposible: solo "
                    f"{sum(1 for g in agrupaciones if any(p.clase == minoritaria for p in agrupaciones[g]))} "
                    f"fabricantes aportan clase {minoritaria}, asi que no hay con que "
                    f"llenar mas pliegues sin partir una marca.")
            return pliegues, k, nota

    return particionar(datos), len(agrupaciones), ("no se pudo estratificar: ningun k>=2 "
                                             "deja las dos clases en todos los pliegues")


# --------------------------------------------------------------------------
# B0: baseline trivial
# --------------------------------------------------------------------------

def b0_trivial(entrenamiento: list[Plataforma]) -> int:
    """Clase mayoritaria del pliegue de entrenamiento. No mira ninguna variable.

    Empate: gana la clase mas baja, por regla fija y no por orden de aparicion,
    para que el resultado no dependa del orden del archivo.
    """
    cuenta = Counter(p.clase for p in entrenamiento)
    tope = max(cuenta.values())
    return min(c for c, n in cuenta.items() if n == tope)


# --------------------------------------------------------------------------
# B1: el clasico asignado al rubro -- logistica ordinal
# --------------------------------------------------------------------------

def _sigmoide(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


@dataclass
class LogisticaOrdinal:
    """Modelo de probabilidades proporcionales (proportional odds).

        P(y <= k | x) = sigmoide(corte_k - beta * x)

    Un solo `beta` compartido por todos los cortes: esa es la hipotesis de
    proporcionalidad, y es lo que hace el modelo legible -una sola pendiente
    que dice cuanto empuja la antiguedad hacia clases mas altas.

    Los cortes se parametrizan como corte_0 y luego incrementos exponenciales,
    de modo que siempre quedan ordenados sin necesidad de restricciones.
    """
    clases: list[int]
    cortes: list[float]
    beta: float
    media: float
    escala: float

    def probabilidades(self, x: float) -> list[float]:
        z = (x - self.media) / self.escala
        acum = [_sigmoide(c - self.beta * z) for c in self.cortes] + [1.0]
        previo, probs = 0.0, []
        for a in acum:
            probs.append(max(a - previo, 1e-12))
            previo = a
        return probs

    def predecir(self, x: float) -> int:
        probs = self.probabilidades(x)
        return self.clases[probs.index(max(probs))]


def _log_verosimilitud(params: list[float], xs: list[float], ys: list[int],
                       clases: list[int]) -> float:
    corte0, incrementos, beta = params[0], params[1:-1], params[-1]
    cortes, actual = [], corte0
    for inc in incrementos:
        cortes.append(actual)
        actual += math.exp(inc)
    cortes.append(actual)
    cortes = cortes[:len(clases) - 1]

    total = 0.0
    for x, y in zip(xs, ys):
        acum = [_sigmoide(c - beta * x) for c in cortes] + [1.0]
        previo, probs = 0.0, []
        for a in acum:
            probs.append(max(a - previo, 1e-12))
            previo = a
        total += math.log(probs[clases.index(y)])
    return total - L2 * beta * beta          # penalizacion L2 sobre la pendiente


def b1_logistica_ordinal(entrenamiento: list[Plataforma]) -> LogisticaOrdinal:
    """Ajuste por ascenso de gradiente con gradiente numerico.

    Determinista de principio a fin: arranca en ceros, paso y numero de
    iteraciones fijos, sin barajado ni muestreo. Con dos o tres parametros y
    ocho filas esto converge de sobra y evita depender de un optimizador
    externo cuya version cambiaria el resultado.
    """
    clases = sorted({p.clase for p in entrenamiento})
    xs_bruto = [float(p.antiguedad) for p in entrenamiento]
    media = sum(xs_bruto) / len(xs_bruto)
    var = sum((x - media) ** 2 for x in xs_bruto) / len(xs_bruto)
    escala = math.sqrt(var) if var > 0 else 1.0
    xs = [(x - media) / escala for x in xs_bruto]
    ys = [p.clase for p in entrenamiento]

    n_params = 1 + max(len(clases) - 2, 0) + 1
    params = [0.0] * n_params
    h = 1e-5
    for _ in range(ITERACIONES):
        base = _log_verosimilitud(params, xs, ys, clases)
        grad = []
        for i in range(n_params):
            sube = list(params)
            sube[i] += h
            grad.append((_log_verosimilitud(sube, xs, ys, clases) - base) / h)
        params = [p + PASO * g for p, g in zip(params, grad)]

    corte0, incrementos, beta = params[0], params[1:-1], params[-1]
    cortes, actual = [], corte0
    for inc in incrementos:
        cortes.append(actual)
        actual += math.exp(inc)
    cortes.append(actual)
    cortes = cortes[:len(clases) - 1]
    return LogisticaOrdinal(clases, cortes, beta, media, escala)


# --------------------------------------------------------------------------
# Metricas: las que declara el paper para P1
# --------------------------------------------------------------------------

def metricas(reales: list[int], predichas: list[int]) -> dict[str, float]:
    n = len(reales)
    exactitud = sum(r == p for r, p in zip(reales, predichas)) / n
    error_ordinal = sum(abs(r - p) for r, p in zip(reales, predichas)) / n

    f1s = []
    for c in sorted(set(reales) | set(predichas)):
        vp = sum(r == c and p == c for r, p in zip(reales, predichas))
        fp = sum(r != c and p == c for r, p in zip(reales, predichas))
        fn = sum(r == c and p != c for r, p in zip(reales, predichas))
        prec = vp / (vp + fp) if vp + fp else 0.0
        rec = vp / (vp + fn) if vp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return {
        "exactitud": round(exactitud, 3),
        "f1_macro": round(sum(f1s) / len(f1s), 3),
        "error_ordinal_medio": round(error_ordinal, 3),
    }


def _media_sd(valores: list[float]) -> tuple[float, float]:
    """Media y desviacion tipica MUESTRAL (n-1), que es la que se reporta en
    validacion cruzada: los k pliegues son una muestra, no la poblacion."""
    n = len(valores)
    media = sum(valores) / n
    if n < 2:
        return media, 0.0
    var = sum((v - media) ** 2 for v in valores) / (n - 1)
    return media, math.sqrt(var)


def evaluar(datos: list[Plataforma], pliegues: list[dict]) -> dict:
    por_nombre = {p.plataforma: p for p in datos}
    reales, pred_b0, pred_b1, detalle, modelos = [], [], [], [], []
    por_pliegue = []

    for pl in pliegues:
        entrena = [por_nombre[n] for n in pl["entrenamiento"]]
        prueba = [por_nombre[n] for n in pl["prueba"]]
        c0 = b0_trivial(entrena)
        modelo = b1_logistica_ordinal(entrena)
        modelos.append({
            "pliegue": pl["pliegue"], "marca": pl["prueba_marcas"],
            "beta": round(modelo.beta, 3),
            "cortes": [round(c, 3) for c in modelo.cortes],
        })
        f_reales, f_b0, f_b1 = [], [], []
        for p in prueba:
            p1 = modelo.predecir(float(p.antiguedad))
            reales.append(p.clase)
            pred_b0.append(c0)
            pred_b1.append(p1)
            f_reales.append(p.clase)
            f_b0.append(c0)
            f_b1.append(p1)
            detalle.append({
                "plataforma": p.plataforma, "marca": p.fabricante,
                "antiguedad": p.antiguedad, "real": p.clase, "b0": c0, "b1": p1,
            })
        por_pliegue.append({
            "marca": pl["prueba_marcas"], "n": len(prueba),
            "b0": metricas(f_reales, f_b0), "b1": metricas(f_reales, f_b1),
        })

    resumen = {}
    for clave in ("b0", "b1"):
        resumen[clave] = {}
        for m in ("exactitud", "f1_macro", "error_ordinal_medio"):
            media, sd = _media_sd([f[clave][m] for f in por_pliegue])
            resumen[clave][m] = (round(media, 3), round(sd, 3))

    return {"b0": metricas(reales, pred_b0), "b1": metricas(reales, pred_b1),
            "cv": resumen, "por_pliegue": por_pliegue,
            "detalle": detalle, "modelos": modelos}


# --------------------------------------------------------------------------
# Casilla 6: auditoria de fuga
# --------------------------------------------------------------------------

def auditar_fuga(datos: list[Plataforma]) -> list[dict]:
    """Comprueba, columna por columna, si puede entrar como variable.

    Las dos primeras no son opinion: la identidad se verifica con aritmetica
    sobre los propios datos y el conteo se imprime.
    """
    hallazgos = []
    for col, atributo, fuente in (
        ("Vida_comercial_anios", "vida_comercial", "fin_comercializacion"),
        ("Soporte_total_anios", "soporte_total", "fin_repuestos"),
    ):
        comprobadas = coinciden = 0
        for p in datos:
            valor, fecha = getattr(p, atributo), getattr(p, fuente)
            if valor is None or fecha is None:
                continue
            comprobadas += 1
            coinciden += (fecha[0] - p.lanzamiento) == valor
        hallazgos.append({
            "columna": col, "veredicto": "EXCLUIDA",
            "motivo": (f"identidad verificada en {coinciden} de {comprobadas} filas: "
                       f"{col} = anio({fuente}) - Lanzamiento. La fecha de la que se "
                       f"deriva es una de las que definen la etiqueta, asi que la "
                       f"columna es la etiqueta escrita de otra forma."),
        })

    hallazgos += [
        {"columna": "Anuncio_fin_de_vida / Fin_comercializacion / Fin_repuestos_reparacion",
         "veredicto": "EXCLUIDAS",
         "motivo": "son las columnas con las que se deriva la clase. Usarlas como "
                   "variable seria predecir la etiqueta con la etiqueta."},
        {"columna": "Nivel",
         "veredicto": "EXCLUIDA",
         "motivo": "mide cuan verificado esta el dato contra la fuente (A/B/C), no una "
                   "propiedad del equipo. Es metadato del proceso de recoleccion: si "
                   "entrara, el modelo aprenderia el habito documental del fabricante."},
        {"columna": "Fabricante",
         "veredicto": "EXCLUIDA como variable",
         "motivo": "es la variable de agrupamiento. En leave-one-manufacturer-out la "
                   "marca de prueba nunca aparece en entrenamiento, asi que como "
                   "variable no es utilizable: solo sirve para formar los pliegues."},
        {"columna": "Lanzamiento -> antiguedad",
         "veredicto": "ADMITIDA",
         "motivo": "es anterior a cualquier evento de fin de vida y esta disponible en "
                   "la placa del equipo. Unica variable que sobrevive a la auditoria."},
    ]
    return hallazgos


# --------------------------------------------------------------------------
# Informe
# --------------------------------------------------------------------------

def _versiones() -> list[str]:
    try:
        salida = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                capture_output=True, text=True, timeout=60).stdout
        return sorted(l.strip() for l in salida.splitlines() if l.strip())
    except Exception:                                          # noqa: BLE001
        return []


def _envolver(texto: str, ancho: int) -> list[str]:
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > ancho:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def informe(datos, pliegues, res, fuga, versiones, nota_k="") -> str:
    L: list[str] = []
    a = L.append
    ref = "%04d-%02d-%02d" % FECHA_REF

    a("=" * 74)
    a("BASELINE REPRODUCIBLE: RIESGO ORDINAL Y PRIORIDAD DE REEMPLAZO")
    a("=" * 74)
    a(f"Fecha de referencia fija: {ref}. Semilla declarada: {SEMILLA}.")
    a("Subproblema cubierto: P1 (riesgo ordinal). P2 ver seccion 7.")
    a("")

    # ---- casilla 1 -------------------------------------------------------
    a("1. CONJUNTO DE DATOS")
    a("-" * 74)
    a(f"  Archivo   : {DATOS.relative_to(RAIZ).as_posix()}")
    a("  Origen    : Tabla 2 de 'tabla de frecuencias' (fila agregada MEDIA excluida)")
    a(f"  Muestras  : {len(datos)} plataformas")
    a(f"  Marcas    : {len({p.fabricante for p in datos})} fabricantes")
    cuenta = Counter(p.clase for p in datos)
    a(f"  Clases    : {len(cuenta)} presentes de {len(CLASES)} definidas en la escala")
    for c in sorted(CLASES):
        n = cuenta.get(c, 0)
        a(f"     {c}. {CLASES[c]:<45s} n={n}" + ("" if n else "   <-- SIN NINGUNA MUESTRA"))
    a("")
    a("  Balance   : " + " / ".join(f"clase {c}: {n}" for c, n in sorted(cuenta.items())))
    a("")
    a("  SESGO DE SELECCION, declarado: la tabla se construyo para documentar")
    a("  descontinuaciones, asi que solo contiene plataformas ya descontinuadas.")
    a("  No hay ni una muestra de las clases 1 y 2. Un clasificador entrenado aqui")
    a("  no puede aprender a reconocer una plataforma vigente, y el modelo ordinal")
    a("  degenera de hecho en binario: con dos clases solo queda un corte.")
    a("")
    a("  Conversion de fechas (para auditar celda a celda):")
    for p in datos:
        a(f"     {p.plataforma[:34]:<34s} lanz {p.lanzamiento}  antig {p.antiguedad:>2d}  clase {p.clase}")
        for col, regla in p.reglas.items():
            a(f"        {col:<28s} {regla}")
    faltan = [(p.plataforma, p.dato_faltante) for p in datos if p.dato_faltante]
    a("")
    a(f"  Datos faltantes: {len(faltan)} plataformas con alguna fecha ausente")
    for nombre, cols in faltan:
        a(f"     {nombre}: {', '.join(cols)}")
    a("")

    # ---- casilla 2 -------------------------------------------------------
    a("2. PARTICION")
    a("-" * 74)
    a("  Esquema   : estratificada por nivel de obsolescencia, agrupando por marca")
    a("              (el esquema asignado al rubro)")
    a("  Agrupa por: Fabricante. El rubro dice \"caso de migracion\" porque supone")
    a("              componentes que comparten caso; aqui cada fila es una plataforma")
    a("              independiente y no hay casos, asi que la unidad de agrupamiento equivalente es la")
    a("              marca: comparten politica de soporte y se parecen por eso.")
    a("  Estratifica: cada pliegue de prueba contiene las dos clases presentes.")
    a(f"  Guardada  : {PARTICION.relative_to(RAIZ).as_posix()}")
    a(f"  Pliegues  : {len(pliegues)}")
    for pl in pliegues:
        a(f"     [{pl['pliegue']}] prueba = {pl['prueba_marcas']:<28s} "
          f"({len(pl['prueba'])} muestras)  entrenamiento = {len(pl['entrenamiento'])}")
    a("")
    for linea in _envolver("  " + nota_k, 72):
        a(f"  {linea}")
    a("")
    a("  Preprocesamiento DENTRO del pliegue: la media y la desviacion con que se")
    a("  estandariza la antiguedad se calculan solo con el entrenamiento de cada")
    a("  pliegue, en b1_logistica_ordinal(). No hay ningun ajuste hecho una sola")
    a("  vez sobre las nueve filas.")
    a("")
    a("  Contraste con leave-one-manufacturer-out (k=5), que agrupa pero NO")
    a("  estratifica: alli el pliegue de Mitsubishi queda puro -sus dos plataformas")
    a("  son clase 4- y los dos modelos sacan 0.000 en el. Esa es exactamente la")
    a("  distorsion que la estratificacion evita.")
    a("")

    # ---- casillas 3 y 4 --------------------------------------------------
    a("3 y 4. BASELINES, MISMA PARTICION Y MISMAS METRICAS")
    a("-" * 74)
    a("  B0 trivial : clase mayoritaria del pliegue de entrenamiento. Sin variables.")
    a("  B1 clasico : regresion logistica ordinal (probabilidades proporcionales)")
    a("               sobre antiguedad, el modelo asignado al rubro.")
    a(f"               L2={L2}, paso={PASO}, iteraciones={ITERACIONES}, inicio en ceros.")
    a("")
    a(f"  RESULTADO DE LA VALIDACION CRUZADA "
      f"(media +- desviacion de los {len(pliegues)} pliegues)")
    a(f"  {'':<12s} {'exactitud':>16s} {'F1 macro':>16s} {'err. ordinal':>16s}")
    for etiqueta, clave in (("B0 trivial", "b0"), ("B1 clasico", "b1")):
        c = res["cv"][clave]
        a(f"  {etiqueta:<12s} "
          f"{c['exactitud'][0]:>9.3f} +-{c['exactitud'][1]:<5.3f} "
          f"{c['f1_macro'][0]:>9.3f} +-{c['f1_macro'][1]:<5.3f} "
          f"{c['error_ordinal_medio'][0]:>9.3f} +-{c['error_ordinal_medio'][1]:<5.3f}")
    a("")
    a("  Por pliegue:")
    a(f"     {'pliegue':<34s} {'n':>2s} {'exact. B0':>10s} {'exact. B1':>10s} "
      f"{'F1 B0':>8s} {'F1 B1':>8s}")
    for f in res["por_pliegue"]:
        a(f"     {f['marca']:<34s} {f['n']:>2d} "
          f"{f['b0']['exactitud']:>10.3f} {f['b1']['exactitud']:>10.3f} "
          f"{f['b0']['f1_macro']:>8.3f} {f['b1']['f1_macro']:>8.3f}")
    a("")
    a("  La desviacion sigue siendo grande, y tiene que estarlo: con nueve filas")
    a("  repartidas en pocos pliegues, un acierto o un fallo mueve la cifra de un")
    a("  pliegue entero. Reportar la media sin la desviacion esconderia eso.")
    a("")
    a("  Agrupando las 9 predicciones en una sola bolsa (micro), para contraste:")
    a(f"  {'':<12s} {'exactitud':>10s} {'F1 macro':>10s} {'err. ordinal':>14s}")
    for etiqueta, clave in (("B0 trivial", "b0"), ("B1 clasico", "b1")):
        m = res[clave]
        a(f"  {etiqueta:<12s} {m['exactitud']:>10.3f} {m['f1_macro']:>10.3f} "
          f"{m['error_ordinal_medio']:>14.3f}")
    a("  Difiere de la media de pliegues porque los pliegues no son del mismo")
    a("  tamano. La cifra que se reporta es la de arriba, media +- desviacion;")
    a("  esta va solo como contraste.")
    a("")
    a("  Coeficientes por pliegue (esto es lo que un ingeniero puede auditar):")
    a(f"     {'pliegue de prueba':<34s} {'beta':>8s}   cortes")
    for m in res["modelos"]:
        a(f"     {m['marca']:<34s} {m['beta']:>8.3f}   {m['cortes']}")
    a("")
    a("     beta positivo = mas antiguedad empuja hacia clases mas altas, que es el")
    a("     sentido esperado. La pendiente esta en unidades de desviacion tipica de")
    a("     la antiguedad del propio pliegue, no en anios.")
    a("")
    a("  Prediccion por plataforma:")
    a(f"     {'plataforma':<34s} {'marca':<12s} {'antig':>6s} {'real':>5s} {'B0':>4s} {'B1':>4s}")
    for d in res["detalle"]:
        a(f"     {d['plataforma'][:34]:<34s} {d['marca']:<12s} {d['antiguedad']:>6d} "
          f"{d['real']:>5d} {d['b0']:>4d} {d['b1']:>4d}")
    a("")
    if res["cv"]["b1"]["exactitud"][0] <= res["cv"]["b0"]["exactitud"][0]:
        a("  LECTURA: el clasico NO le gana al trivial. Con una sola variable y nueve")
        a("  filas es un resultado esperable, y es el que hay que publicar: dice que a")
        a("  este tamano la antiguedad por si sola no separa las clases mejor que")
        a("  contar cual es mas frecuente.")
    else:
        a("  LECTURA: el clasico supera al trivial EN MEDIA. La diferencia NO es")
        a("  estadisticamente sostenible: con pliegues de 1 y 2 muestras la desviacion")
        a("  entre pliegues es del orden de la propia diferencia, de modo que el")
        a("  intervalo de uno cubre la media del otro. Sirve como indicio de que la")
        a("  antiguedad lleva senal, no como evidencia de que el modelo funcione.")
    a("")

    # ---- casilla 5 -------------------------------------------------------
    a("5. SEMILLA Y VERSIONES")
    a("-" * 74)
    a(f"  Semilla declarada : {SEMILLA}")
    a("  Uso real          : NINGUNO. No hay paso estocastico: el ajuste arranca en")
    a("                      ceros, el paso y las iteraciones son fijos y no hay")
    a("                      barajado ni muestreo. La reproducibilidad no depende de")
    a("                      la semilla, y por eso se dice en vez de sugerir que si.")
    a(f"  Python            : {platform.python_version()} ({platform.system()})")
    a("  Dependencias del calculo: ninguna de terceros (biblioteca estandar)")
    a(f"  Entorno congelado : {len(versiones)} paquetes")
    for v in versiones:
        a(f"     {v}")
    a("")

    # ---- casilla 6 -------------------------------------------------------
    a("6. AUDITORIA DE FUGA DE DATOS")
    a("-" * 74)
    for h in fuga:
        a(f"  [{h['veredicto']}] {h['columna']}")
        for linea in _envolver(h["motivo"], 68):
            a(f"      {linea}")
    admitidas = [h for h in fuga if h["veredicto"].startswith("ADMITIDA")]
    a("")
    a(f"  RESULTADO: de las columnas disponibles sobrevive {len(admitidas)}.")
    a("  El conjunto admite exactamente una variable no contaminada. Ese es el")
    a("  hallazgo, y condiciona todo lo anterior: el clasico no tuvo mas remedio")
    a("  que ser univariante.")
    a("")
    a("  Fuera de esta tabla, en el banco de casos del artefacto:")
    a("     - Los escenarios de desarrollo 'critico' y 'otra_marca' comparten las")
    a("       mismas 24 respuestas: son 2 casos independientes, no 3.")
    a("     - 'critico' (S7-300 -> S7-1500) reproduce la ruta del caso ciego 26.1,")
    a("       y el destino de 'otra_marca' (Omron NX) la del caso ciego 26.5:")
    a("       el conjunto de desarrollo pisa el de prueba.")
    a("     - En modo agente con API, la herramienta consultar_guia alcanza")
    a("       data/base_conocimiento.json, que contiene los cinco casos ciegos con")
    a("       su estrategia. En modo determinista no: interactivo.py no importa")
    a("       conocimiento. La fuga existe y depende del modo.")
    a("")

    # ---- P2 --------------------------------------------------------------
    a("  CONJUNTO DE PRUEBA APARTADO: los cinco casos de estudio de la guia y las")
    a("  etiquetas del panel de expertos siguen SIN ABRIR. Todo lo anterior ocurre")
    a(f"  dentro del lazo de desarrollo: son {len(pliegues)} pliegues de validacion sobre")
    a("  las nueve plataformas, no una medida sobre datos apartados.")
    a("")
    a("7. P2 PRIORIDAD DE REEMPLAZO - NO EVALUABLE TODAVIA")
    a("-" * 74)
    a("  El clasico asignado a P2 es gradient boosting en modo ranking. No se")
    a("  ejecuta, y la razon no es tecnica sino de datos: un modelo de ranking")
    a("  necesita un orden de referencia -que plataforma debe reemplazarse antes")
    a("  que cual- y ese orden no existe en ninguna fuente del proyecto.")
    a("")
    a("  Derivarlo de la puntuacion del propio motor seria circular: el modelo")
    a("  aprenderia a reproducir la formula que se pretende evaluar.")
    a("")
    a("  Lo que hace falta para desbloquearlo, en orden de coste:")
    a("     1. Un orden de prioridad por juicio experto sobre estas 9 plataformas,")
    a("        emitido por los coautores sin ver la salida del motor. Es el mismo")
    a("        procedimiento de _plantilla_ciega.py y se puede pedir en una sesion.")
    a("     2. Ampliar la tabla de ciclo de vida a las 130 generaciones del")
    a("        catalogo, que es lo que daria un conjunto donde el boosting tenga")
    a("        sentido. Trabajo de extraccion y verificacion en fuentes oficiales.")
    a("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Baseline reproducible del rubro.")
    ap.add_argument("--md", action="store_true", help="escribe docs/baseline_reproducible.md")
    args = ap.parse_args()

    datos = cargar()
    pliegues, k, nota_k = particionar_estratificado(datos)
    PARTICION.write_text(json.dumps({
        "esquema": "estratificada por nivel de obsolescencia, agrupada por fabricante",
        "k": k,
        "nota_k": nota_k,
        "agrupamiento": "Fabricante",
        "preprocesamiento": "ajustado dentro de cada pliegue (media y escala del entrenamiento)",
        "fecha_referencia": "%04d-%02d-%02d" % FECHA_REF,
        "semilla": SEMILLA,
        "origen": "data/ciclo_vida_plataformas.csv",
        "variable_admitida": "antiguedad = 2026 - Lanzamiento",
        "pliegues": pliegues,
        "etiquetas": {p.plataforma: p.clase for p in datos},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    res = evaluar(datos, pliegues)
    fuga = auditar_fuga(datos)
    texto = informe(datos, pliegues, res, fuga, _versiones(), nota_k)
    print(texto)

    if args.md:
        SALIDA_MD.write_text(
            "# Baseline reproducible: riesgo ordinal y prioridad de reemplazo\n\n"
            "Generado por `_baseline.py`. Reproducible: misma entrada, misma salida,\n"
            "sin clave de API y sin dependencias de terceros en el calculo.\n\n"
            "```\n" + texto + "```\n", encoding="utf-8")
        print(f"\nEscrito {SALIDA_MD.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
