"""Baseline reproducible: riesgo ordinal y prioridad de reemplazo.

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

ROOT = Path(__file__).resolve().parent
from migra_ia import config

DATA = ROOT / "data" / "platform_lifecycle.csv"
PARTITION = ROOT / "data" / "lifecycle_partition.json"


def D(key: str) -> str:
    """Texto del informe en el idioma de esta ejecucion."""
    return config.doc_tools().get(key, key)


def output_path() -> Path:
    """Donde va el informe de este idioma. La ruta la declara el idioma."""
    return ROOT / D("bl_path")

# Fecha de referencia FIJA. Las clases se derivan comparando fechas contra ella,
# asi que usar "hoy" haria que las etiquetas cambiaran solas con el calendario y
# el entregable dejaria de ser reproducible.
FECHA_REF = (2026, 9, 4)

# No hay ningun paso estocastico: el ajuste arranca en ceros y el numero de
# iteraciones es fijo. La semilla se declara para el registro y para dejar
# constancia de que NO hace falta.
SEED = 42

# Hiperparametros del clasico. Fijos y declarados: con nueve filas, buscarlos
# sobre la propia particion seria ajustar la busqueda a la validacion.
ITERATIONS = 4000
STEP = 0.05
L2 = 1.0

# Escala ordinal de obsolescencia. Es la misma que usa el motor en M01
# (migra_ia/interactive.py::_f_lifecycle), para que el subproblema P1 y el
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

def _parse_date(bruto: str) -> tuple[tuple[int, int, int] | None, str]:
    """Devuelve (fecha, regla aplicada). La regla se imprime para que un humano
    pueda auditar cada conversion: son formatos heterogeneos escritos a mano.

    Cuando una celda trae dos fechas ('ult. pedido' / 'ult. envio') se toma la
    PRIMERA, que es la que usa la propia tabla para calcular Vida_comercial.
    """
    s = (bruto or "").strip()
    if not s or s.lower() in {"n.d.", "nd", "n/d", "-"}:
        return None, D("bl_rule_empty")

    note = ""
    if "/" in s and re.search(r"\d{2}-\d{4}.*/.*\d{2}-\d{4}", s):
        s, note = s.split("/")[0].strip(), D("bl_rule_two_dates")

    s = re.sub(r"\(.*?\)", "", s).replace(">=", "").strip()

    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:                                          # 18/5/2015, 01-10-2023
        d, mes, a = (int(x) for x in m.groups())
        if d > 12:
            return (a, mes, d), D("bl_rule_day_first") + note
        return (a, mes, d), D("bl_rule_ambiguous") + note

    m = re.match(r"^(\d{1,2})-(\d{4})$", s)        # 09-2013
    if m:
        return (int(m.group(2)), int(m.group(1)), 1), D("bl_rule_mm_yyyy") + note

    m = re.match(r"^([a-z]{3})-(\d{2})$", s.lower())   # jun-17, mar-32
    if m and m.group(1) in MESES:
        aa = int(m.group(2))
        anio = 2000 + aa if aa < 50 else 1900 + aa
        return (anio, MESES[m.group(1)], 1), D("bl_rule_mmm_yy") + note

    m = re.match(r"^(\d{4})$", s)                  # 2022
    if m:
        return (int(m.group(1)), 1, 1), D("bl_rule_year_only") + note

    return None, D("bl_rule_unknown") % repr(bruto)


@dataclass
class Platform:
    manufacturer: str
    platform: str
    release: int
    announcement: tuple[int, int, int] | None
    end_of_manufacturing: tuple[int, int, int] | None
    end_of_spare_parts: tuple[int, int, int] | None
    commercial_life: int | None
    total_support: int | None
    level: str
    rules: dict[str, str] = field(default_factory=dict)
    missing_datum: list[str] = field(default_factory=list)

    @property
    def age_years(self) -> int:
        return FECHA_REF[0] - self.release

    @property
    def class_label(self) -> int:
        """Etiqueta ordinal derivada de las fechas contra FECHA_REF.

        El orden de las comprobaciones es el de la escala: se pregunta primero
        por el estado mas avanzado. Si el fin de repuestos no se conoce, NO se
        supone: la plataforma se queda en la clase que sus fechas conocidas
        sostienen y el hueco se anota como dato faltante, que es el mismo
        principio que aplica el cuestionario del agente.
        """
        if self.end_of_spare_parts and self.end_of_spare_parts <= FECHA_REF:
            return 4
        if self.end_of_manufacturing and self.end_of_manufacturing <= FECHA_REF:
            return 3
        if self.announcement and self.announcement <= FECHA_REF:
            return 2
        return 1


def load() -> list[Platform]:
    filas = list(csv.DictReader(DATA.read_text(encoding="utf-8").splitlines(), delimiter=";"))
    plataformas: list[Platform] = []
    for f in filas:
        rules, faltan, fechas = {}, [], {}
        for col in ("end_of_life_announcement", "end_of_manufacturing", "end_of_spare_parts"):
            fecha, regla = _parse_date(f[col])
            fechas[col], rules[col] = fecha, regla
            if fecha is None:
                faltan.append(col)
        plataformas.append(Platform(
            manufacturer=f["manufacturer"].strip(),
            platform=f["platform"].strip(),
            release=int(f["release"]),
            announcement=fechas["end_of_life_announcement"],
            end_of_manufacturing=fechas["end_of_manufacturing"],
            end_of_spare_parts=fechas["end_of_spare_parts"],
            commercial_life=int(f["commercial_life_years"]) if f["commercial_life_years"].strip() else None,
            total_support=int(f["total_support_years"]) if f["total_support_years"].strip() else None,
            level=f["level"].strip(),
            rules=rules,
            missing_datum=faltan,
        ))
    return plataformas


# --------------------------------------------------------------------------
# Particion con restriccion de agrupamiento
# --------------------------------------------------------------------------

def partition(data: list[Platform]) -> list[dict]:
    """Leave-one-manufacturer-out. Se conserva solo como CONTRASTE.

    Agrupa pero no estratifica: el pliegue de Mitsubishi queda puro (sus dos
    plataformas son clase 4) y ningun modelo puede acertarlo. Sirve justamente
    para ensenar lo que la estratificacion evita.
    """
    marcas = sorted({p.manufacturer for p in data})
    return [{
        "fold": i,
        "test_brands": brand,
        "test": [p.platform for p in data if p.manufacturer == brand],
        "train": [p.platform for p in data if p.manufacturer != brand],
    } for i, brand in enumerate(marcas)]


def stratified_partition(data: list[Platform],
                              k_max: int = 5) -> tuple[list[dict], int, str]:
    """Esquema asignado por el rubro: estratificado por nivel de obsolescencia,
    manteniendo la restriccion de agrupamiento.

    La unidad de observacion decide la variante. El rubro habla de agrupar por
    "caso de migracion" porque supone componentes que comparten caso; aqui cada
    fila es una plataforma independiente y no hay casos, asi que la unidad
    que juega ese papel es el FABRICANTE: dos plataformas de una marca
    comparten politica de soporte (Tabla 3) y se parecen entre si por eso.

    Una marca entera cae siempre del mismo lado -si se partiera, la fuga vuelve
    por la puerta de atras- y se busca la k mas alta en la que TODO pliegue de
    prueba contenga las dos clases. Reparto determinista: las marcas se ordenan
    por cuantas muestras de la clase minoritaria aportan y cada una va al
    pliegue donde MENOS desvia el reparto del ideal, contando TODAS las clases.
    Mirar solo la minoritaria no sirve: dejaba a Mitsubishi solo en su pliegue,
    con sus dos clase 4 y ninguna clase 3.
    """
    clases_totales = sorted({p.class_label for p in data})
    minoritaria = min(clases_totales, key=lambda c: sum(p.class_label == c for p in data))
    groupings: dict[str, list[Platform]] = {}
    for p in data:
        groupings.setdefault(p.manufacturer, []).append(p)

    order = sorted(groupings,
                   key=lambda g: (-sum(p.class_label == minoritaria for p in groupings[g]),
                                  -len(groupings[g]), g))

    for k in range(min(k_max, len(groupings)), 1, -1):
        ideal = {c: sum(p.class_label == c for p in data) / k for c in clases_totales}
        cubos: list[list[str]] = [[] for _ in range(k)]
        conteo = [{c: 0 for c in clases_totales} for _ in range(k)]

        def _cost(j: int, g: str) -> float:
            aporte = {c: sum(p.class_label == c for p in groupings[g]) for c in clases_totales}
            return sum((conteo[j][c] + aporte[c] - ideal[c]) ** 2 for c in clases_totales)

        for g in order:
            i = min(range(k), key=lambda j: (_cost(j, g), sum(conteo[j].values()), j))
            cubos[i].append(g)
            for p in groupings[g]:
                conteo[i][p.class_label] += 1

        completo = all(cubos[j] and all(conteo[j][c] > 0 for c in clases_totales)
                       for j in range(k))
        if completo:
            pliegues = []
            for i, marcas in enumerate(cubos):
                test = [p.platform for g in marcas for p in groupings[g]]
                pliegues.append({
                    "fold": i,
                    "test_brands": " + ".join(sorted(marcas)),
                    "test": test,
                    "train": [p.platform for p in data
                                      if p.platform not in set(test)],
                })
            # Se devuelven los DATOS de la nota, no la frase: el informe la
            # quiere en el idioma de la sesion y el archivo de datos en el
            # canonico.
            return pliegues, k, (k, len(clases_totales),
                                 sum(1 for g in groupings
                                     if any(p.class_label == minoritaria
                                            for p in groupings[g])),
                                 minoritaria)

    return partition(data), len(groupings), None


# --------------------------------------------------------------------------
# B0: baseline trivial
# --------------------------------------------------------------------------

def b0_trivial(entrenamiento: list[Platform]) -> int:
    """Clase mayoritaria del pliegue de entrenamiento. No mira ninguna variable.

    Empate: gana la clase mas baja, por regla fija y no por orden de aparicion,
    para que el resultado no dependa del orden del archivo.
    """
    cuenta = Counter(p.class_label for p in entrenamiento)
    tope = max(cuenta.values())
    return min(c for c, n in cuenta.items() if n == tope)


# --------------------------------------------------------------------------
# B1: el clasico asignado por el rubro -- logistica ordinal
# --------------------------------------------------------------------------

def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


@dataclass
class OrdinalLogistic:
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

    def probabilities(self, x: float) -> list[float]:
        z = (x - self.media) / self.escala
        acum = [_sigmoid(c - self.beta * z) for c in self.cortes] + [1.0]
        previo, probs = 0.0, []
        for a in acum:
            probs.append(max(a - previo, 1e-12))
            previo = a
        return probs

    def predict(self, x: float) -> int:
        probs = self.probabilities(x)
        return self.clases[probs.index(max(probs))]


def _log_likelihood(params: list[float], xs: list[float], ys: list[int],
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
        acum = [_sigmoid(c - beta * x) for c in cortes] + [1.0]
        previo, probs = 0.0, []
        for a in acum:
            probs.append(max(a - previo, 1e-12))
            previo = a
        total += math.log(probs[clases.index(y)])
    return total - L2 * beta * beta          # penalizacion L2 sobre la pendiente


def b1_ordinal_logistic(entrenamiento: list[Platform]) -> OrdinalLogistic:
    """Ajuste por ascenso de gradiente con gradiente numerico.

    Determinista de principio a fin: arranca en ceros, paso y numero de
    iteraciones fijos, sin barajado ni muestreo. Con dos o tres parametros y
    ocho filas esto converge de sobra y evita depender de un optimizador
    externo cuya version cambiaria el resultado.
    """
    clases = sorted({p.class_label for p in entrenamiento})
    xs_bruto = [float(p.age_years) for p in entrenamiento]
    media = sum(xs_bruto) / len(xs_bruto)
    var = sum((x - media) ** 2 for x in xs_bruto) / len(xs_bruto)
    escala = math.sqrt(var) if var > 0 else 1.0
    xs = [(x - media) / escala for x in xs_bruto]
    ys = [p.class_label for p in entrenamiento]

    n_params = 1 + max(len(clases) - 2, 0) + 1
    params = [0.0] * n_params
    h = 1e-5
    for _ in range(ITERATIONS):
        base = _log_likelihood(params, xs, ys, clases)
        grad = []
        for i in range(n_params):
            sube = list(params)
            sube[i] += h
            grad.append((_log_likelihood(sube, xs, ys, clases) - base) / h)
        params = [p + STEP * g for p, g in zip(params, grad)]

    corte0, incrementos, beta = params[0], params[1:-1], params[-1]
    cortes, actual = [], corte0
    for inc in incrementos:
        cortes.append(actual)
        actual += math.exp(inc)
    cortes.append(actual)
    cortes = cortes[:len(clases) - 1]
    return OrdinalLogistic(clases, cortes, beta, media, escala)


# --------------------------------------------------------------------------
# Metricas: las que declara el paper para P1
# --------------------------------------------------------------------------

def metrics(reales: list[int], predichas: list[int]) -> dict[str, float]:
    n = len(reales)
    accuracy = sum(r == p for r, p in zip(reales, predichas)) / n
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
        "exactitud": round(accuracy, 3),
        "f1_macro": round(sum(f1s) / len(f1s), 3),
        "error_ordinal_medio": round(error_ordinal, 3),
    }


def _mean_sd(valores: list[float]) -> tuple[float, float]:
    """Media y desviacion tipica MUESTRAL (n-1), que es la que se reporta en
    validacion cruzada: los k pliegues son una muestra, no la poblacion."""
    n = len(valores)
    media = sum(valores) / n
    if n < 2:
        return media, 0.0
    var = sum((v - media) ** 2 for v in valores) / (n - 1)
    return media, math.sqrt(var)


def evaluate(data: list[Platform], pliegues: list[dict]) -> dict:
    by_name = {p.platform: p for p in data}
    reales, pred_b0, pred_b1, detail, modelos = [], [], [], [], []
    by_fold = []

    for pl in pliegues:
        entrena = [by_name[n] for n in pl["train"]]
        test = [by_name[n] for n in pl["test"]]
        c0 = b0_trivial(entrena)
        modelo = b1_ordinal_logistic(entrena)
        modelos.append({
            "fold": pl["fold"], "brand": pl["test_brands"],
            "beta": round(modelo.beta, 3),
            "cortes": [round(c, 3) for c in modelo.cortes],
        })
        f_reales, f_b0, f_b1 = [], [], []
        for p in test:
            p1 = modelo.predict(float(p.age_years))
            reales.append(p.class_label)
            pred_b0.append(c0)
            pred_b1.append(p1)
            f_reales.append(p.class_label)
            f_b0.append(c0)
            f_b1.append(p1)
            detail.append({
                "platform": p.platform, "brand": p.manufacturer,
                "age_years": p.age_years, "real": p.class_label, "b0": c0, "b1": p1,
            })
        by_fold.append({
            "brand": pl["test_brands"], "n": len(test),
            "b0": metrics(f_reales, f_b0), "b1": metrics(f_reales, f_b1),
        })

    summary = {}
    for key in ("b0", "b1"):
        summary[key] = {}
        for m in ("exactitud", "f1_macro", "error_ordinal_medio"):
            media, sd = _mean_sd([f[key][m] for f in by_fold])
            summary[key][m] = (round(media, 3), round(sd, 3))

    return {"b0": metrics(reales, pred_b0), "b1": metrics(reales, pred_b1),
            "cv": summary, "por_pliegue": by_fold,
            "detail": detail, "models": modelos}


# --------------------------------------------------------------------------
# Casilla 6: auditoria de fuga
# --------------------------------------------------------------------------

def audit_leakage(data: list[Platform]) -> list[dict]:
    """Comprueba, columna por columna, si puede entrar como variable.

    Las dos primeras no son opinion: la identidad se verifica con aritmetica
    sobre los propios datos y el conteo se imprime.
    """
    findings = []
    for col, attribute, source in (
        ("commercial_life_years", "commercial_life", "end_of_manufacturing"),
        ("total_support_years", "total_support", "end_of_spare_parts"),
    ):
        checked = matching = 0
        for p in data:
            value, fecha = getattr(p, attribute), getattr(p, source)
            if value is None or fecha is None:
                continue
            checked += 1
            matching += (fecha[0] - p.release) == value
        findings.append({
            "columna": col, "veredicto": D("bl_excluded"),
            "motivo": D("bl_leak_identity") % (matching, checked, col, source),
        })

    findings += [
        {"columna": D("bl_leak_dates_col"),
         "veredicto": D("bl_excluded_pl"),
         "motivo": D("bl_leak_dates")},
        {"columna": "level",
         "veredicto": D("bl_excluded"),
         "motivo": D("bl_leak_level")},
        {"columna": "manufacturer",
         "veredicto": D("bl_excluded_var"),
         "motivo": D("bl_leak_manufacturer")},
        {"columna": D("bl_leak_age_col"),
         "veredicto": D("bl_admitted"),
         "motivo": D("bl_leak_age")},
    ]
    return findings


# --------------------------------------------------------------------------
# Informe
# --------------------------------------------------------------------------

def _versions() -> list[str]:
    try:
        output = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                capture_output=True, text=True, timeout=60).stdout
        return sorted(l.strip() for l in output.splitlines() if l.strip())
    except Exception:                                          # noqa: BLE001
        return []


def _wrap(text: str, ancho: int) -> list[str]:
    palabras, lineas, actual = text.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > ancho:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def k_note_text(k_args, lang: str | None = None) -> str:
    """La nota del techo de k, en el idioma pedido."""
    from migra_ia import config
    textos = (config.doc_tools_in(lang) if lang else config.doc_tools())
    if k_args is None:
        return textos.get("bl_k_none", "bl_k_none")
    return textos.get("bl_k_note", "bl_k_note") % k_args


def report(data, pliegues, res, fuga, versiones, k_note="") -> str:
    L: list[str] = []
    a = L.append
    ref = "%04d-%02d-%02d" % FECHA_REF

    a("=" * 74)
    a(D("bl_title"))
    a("=" * 74)
    a(D("bl_ref_line") % (ref, SEED))
    a(D("bl_covered"))
    a("")

    # ---- casilla 1 -------------------------------------------------------
    a(D("bl_s1"))
    a("-" * 74)
    a(D("bl_file") % DATA.relative_to(ROOT).as_posix())
    a(D("bl_origin"))
    a(D("bl_samples") % len(data))
    a(D("bl_brands") % len({p.manufacturer for p in data}))
    cuenta = Counter(p.class_label for p in data)
    a(D("bl_classes") % (len(cuenta), len(CLASES)))
    for c in sorted(CLASES):
        n = cuenta.get(c, 0)
        a(D("bl_class_line") % (c, D("lf_class_%d" % c), n)
          + ("" if n else D("bl_no_samples")))
    a("")
    a(D("bl_balance") % " / ".join(D("bl_class_n") % (c, n)
                                   for c, n in sorted(cuenta.items())))
    a("")
    a(D("bl_bias"))
    a("")
    a(D("bl_dates_title"))
    for p in data:
        a(D("bl_date_line") % (p.platform[:34], p.release, p.age_years, p.class_label))
        for col, regla in p.rules.items():
            a(f"        {col:<28s} {regla}")
    faltan = [(p.platform, p.missing_datum) for p in data if p.missing_datum]
    a("")
    a(D("bl_missing") % len(faltan))
    for name, cols in faltan:
        a(f"     {name}: {', '.join(cols)}")
    a("")

    # ---- casilla 2 -------------------------------------------------------
    a(D("bl_s2"))
    a("-" * 74)
    a(D("bl_scheme"))
    a(D("bl_grouping"))
    a(D("bl_strat"))
    a(D("bl_saved") % PARTITION.relative_to(ROOT).as_posix())
    a(D("bl_folds") % len(pliegues))
    for pl in pliegues:
        a(D("bl_fold_line") % (pl["fold"], pl["test_brands"],
                               len(pl["test"]), len(pl["train"])))
    a("")
    for linea in _wrap("  " + k_note, 72):
        a(f"  {linea}")
    a("")
    a(D("bl_prep"))
    a("")
    a(D("bl_loo"))
    a("")

    # ---- casillas 3 y 4 --------------------------------------------------
    a(D("bl_s34"))
    a("-" * 74)
    a(D("bl_b0"))
    a(D("bl_b1"))
    a(D("bl_b1_params") % (L2, STEP, ITERATIONS))
    a("")
    a(D("bl_cv_title") % len(pliegues))
    a(D("bl_cv_head") % ("", D("bl_col_acc"), D("bl_col_f1"), D("bl_col_err")))
    for label, key in ((D("bl_b0_label"), "b0"), (D("bl_b1_label"), "b1")):
        c = res["cv"][key]
        a(f"  {label:<12s} "
          f"{c['exactitud'][0]:>9.3f} +-{c['exactitud'][1]:<5.3f} "
          f"{c['f1_macro'][0]:>9.3f} +-{c['f1_macro'][1]:<5.3f} "
          f"{c['error_ordinal_medio'][0]:>9.3f} +-{c['error_ordinal_medio'][1]:<5.3f}")
    a("")
    a(D("bl_main_metric"))
    a("")
    a(D("bl_per_fold"))
    a(D("bl_fold_head") % (D("bl_col_fold"), D("bl_col_n"), D("bl_col_acc_b0"),
                           D("bl_col_acc_b1"), D("bl_col_f1_b0"), D("bl_col_f1_b1")))
    for f in res["por_pliegue"]:
        a(f"     {f['brand']:<34s} {f['n']:>2d} "
          f"{f['b0']['exactitud']:>10.3f} {f['b1']['exactitud']:>10.3f} "
          f"{f['b0']['f1_macro']:>8.3f} {f['b1']['f1_macro']:>8.3f}")
    a("")
    a(D("bl_dispersion"))
    a("")
    a(D("bl_micro_title"))
    a(D("bl_micro_head") % ("", D("bl_col_acc"), D("bl_col_f1"), D("bl_col_err")))
    for label, key in ((D("bl_b0_label"), "b0"), (D("bl_b1_label"), "b1")):
        m = res[key]
        a(f"  {label:<12s} {m['exactitud']:>10.3f} {m['f1_macro']:>10.3f} "
          f"{m['error_ordinal_medio']:>14.3f}")
    a(D("bl_micro_note"))
    a("")
    a(D("bl_coef_title"))
    a(D("bl_coef_head") % (D("bl_col_testfold"), "beta"))
    for m in res["models"]:
        a(f"     {m['brand']:<34s} {m['beta']:>8.3f}   {m['cortes']}")
    a("")
    a(D("bl_beta_note"))
    a("")
    a(D("bl_pred_title"))
    a(D("bl_pred_head") % (D("bl_col_platform"), D("bl_col_brand"), D("bl_col_age"),
                           D("bl_col_real"), "B0", "B1"))
    for d in res["detail"]:
        a(f"     {d['platform'][:34]:<34s} {d['brand']:<12s} {d['age_years']:>6d} "
          f"{d['real']:>5d} {d['b0']:>4d} {d['b1']:>4d}")
    a("")
    if res["cv"]["b1"]["exactitud"][0] <= res["cv"]["b0"]["exactitud"][0]:
        a(D("bl_reading_lose"))
    else:
        a(D("bl_reading_win"))
    a("")

    # ---- casilla 5 -------------------------------------------------------
    a(D("bl_s5"))
    a("-" * 74)
    a(D("bl_seed") % SEED)
    a(D("bl_seed_use"))
    a(D("bl_python") % (platform.python_version(), platform.system()))
    a(D("bl_deps"))
    a(D("bl_frozen") % len(versiones))
    for v in versiones:
        a(f"     {v}")
    a("")

    # ---- casilla 6 -------------------------------------------------------
    a(D("bl_s6"))
    a("-" * 74)
    for h in fuga:
        a(f"  [{h['veredicto']}] {h['columna']}")
        for linea in _wrap(h["motivo"], 68):
            a(f"      {linea}")
    admitidas = [h for h in fuga if h["veredicto"] == D("bl_admitted")]
    a("")
    a(D("bl_leak_result") % len(admitidas))
    a(D("bl_leak_tail"))
    a("")
    a(D("bl_bank"))
    a("")

    # ---- P2 --------------------------------------------------------------
    a(D("bl_holdout") % len(pliegues))
    a("")
    a(D("bl_s7"))
    a("-" * 74)
    a(D("bl_p2"))
    a("")
    a(D("bl_p2_circular"))
    a("")
    a(D("bl_p2_todo"))
    a("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Baseline reproducible del proyecto.")
    ap.add_argument("--md", action="store_true",
                    help="escribe el documento del idioma activo")
    args = ap.parse_args()

    data = load()
    pliegues, k, k_args = stratified_partition(data)
    PARTITION.write_text(json.dumps({
        "scheme": "estratificada por nivel de obsolescencia, agrupada por fabricante",
        "k": k,
        # El archivo de datos no tiene idioma: la nota va en el canonico.
        "k_note": k_note_text(k_args, config.CANONICAL_LANGUAGE),
        "grouping": "manufacturer",
        "preprocessing": "ajustado dentro de cada pliegue (media y escala del entrenamiento)",
        "reference_date": "%04d-%02d-%02d" % FECHA_REF,
        "seed": SEED,
        "origin": "data/platform_lifecycle.csv",
        "allowed_variable": "antiguedad = 2026 - release",
        "folds": pliegues,
        "labels": {p.platform: p.class_label for p in data},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    res = evaluate(data, pliegues)
    fuga = audit_leakage(data)
    text = report(data, pliegues, res, fuga, _versions(), k_note_text(k_args))
    print(text)

    if args.md:
        destino = output_path()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            D("bl_doc_title") + "\n\n"
            + config.doc_language_line("bl") + "\n\n"
            + D("bl_doc_intro") + "\n\n"
            + "```\n" + text + "```\n", encoding="utf-8")
        print(D("bl_written") % destino.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
