"""Figura principal: el verificador en el lazo (subproblema P3).

QUE ES ESTO
-----------
La pauta del taller pide UNA figura principal por proyecto, disenada antes de
tener los numeros: ejes rotulados, linea de referencia dibujada, y se llena
cuando lleguen los datos. Nos toca esta:

  eje X   numero de iteraciones de correccion
  eje Y   proporcion de programas que pasan el verificador
  que demuestra   que el verificador en el lazo sube el acierto, y en que
                  iteracion deja de subir
  linea de referencia   la generacion sin verificador, iteracion cero

Este script es la unica fuente de la figura. Lee data/figura_p3_verificador.csv
y escribe, sin que nadie teclee un numero a mano:

  Figura_P3_verificador_ES.tex   bloque figure+pgfplots para el paper en espanol
  Figure_P3_verifier_EN.tex      el mismo, en ingles
  figura_p3_verificador.svg      vista previa para abrir en el navegador

    python _figura_p3.py                     # escribe en docs/figuras
    python _figura_p3.py --salida "C:\\ruta"  # ademas, en la carpeta del paper

MIENTRAS NO HAYA DATOS
----------------------
El CSV nace vacio a proposito. Con celdas vacias el script emite la figura en
MODO DISENO: los ejes, la rejilla, las dos referencias externas publicadas y un
aviso de que la curva esta pendiente. No dibuja ninguna curva inventada. En
cuanto el CSV tenga una sola fila con datos, esa parte de la curva aparece y el
aviso se mantiene hasta que no quede ninguna iteracion sin medir.

LAS DOS REFERENCIAS EXTERNAS
----------------------------
47 % sin verificacion externa y 72 % con ella son de Fakih et al. (LLM4PLC), la
misma linea base que ya cita el plan de evaluacion del paper. No son resultados
de este trabajo y la figura las rotula como ajenas.

CONVENCION: el codigo y lo que se imprime en pantalla van en ASCII, como el
resto del repositorio; el LaTeX que se escribe en disco lleva tildes porque es
texto del paper, y se guarda declarando UTF-8.
"""

from __future__ import annotations

import argparse
import os
import sys

RUTA_CSV = os.path.join("data", "figura_p3_verificador.csv")
SALIDA_POR_DEFECTO = os.path.join("docs", "figuras")

# Referencias externas publicadas. Clave de cita tal como esta en ref.bib.
REF_SIN_VERIFICADOR = 47.0
REF_CON_VERIFICACION = 72.0
REF_CITA = "fakih2024llm4plc"

# Una iteracion "deja de subir" cuando gana menos de esto respecto a la previa.
UMBRAL_MESETA = 2.0


# --------------------------------------------------------------------------
# Lectura y validacion
# --------------------------------------------------------------------------

def leer_csv(ruta):
    """Devuelve [(iteracion, pasan, total)] con None donde no hay medida."""
    if not os.path.exists(ruta):
        raise SystemExit("ERROR: no existe %s" % ruta)
    filas = []
    cabecera = None
    with open(ruta, "r", encoding="utf-8") as fh:
        for numero, linea in enumerate(fh, 1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            campos = [c.strip() for c in linea.split(",")]
            if cabecera is None:
                cabecera = campos
                continue
            if len(campos) < 3:
                raise SystemExit(
                    "ERROR: la linea %d del CSV tiene %d campos, se esperaban "
                    "al menos 3" % (numero, len(campos)))
            it = int(campos[0])
            pasan = int(campos[1]) if campos[1] != "" else None
            total = int(campos[2]) if campos[2] != "" else None
            filas.append((it, pasan, total))
    if not filas:
        raise SystemExit("ERROR: el CSV no tiene ninguna fila de datos")
    return filas


def validar(filas):
    """Lista de problemas que impiden emitir la figura. Vacia = todo bien."""
    problemas = []
    esperado = 0
    for it, pasan, total in filas:
        if it != esperado:
            problemas.append(
                "las iteraciones deben ir de 0 en adelante sin huecos; "
                "aparecio %d donde tocaba %d" % (it, esperado))
        esperado += 1
        if (pasan is None) != (total is None):
            problemas.append(
                "iteracion %d: pasan y total van juntos, o los dos vacios o "
                "los dos con valor" % it)
            continue
        if pasan is None:
            continue
        if total <= 0:
            problemas.append(
                "iteracion %d: el total debe ser mayor que cero" % it)
        elif pasan < 0 or pasan > total:
            problemas.append(
                "iteracion %d: pasan=%d fuera del rango 0..%d"
                % (it, pasan, total))
    totales = set(t for _, _, t in filas if t is not None)
    if len(totales) > 1:
        problemas.append(
            "el banco de casos cambia de tamano entre iteraciones (%s); la "
            "curva dejaria de ser comparable" % sorted(totales))
    return problemas


def puntos_medidos(filas):
    """[(iteracion, porcentaje)] solo de las iteraciones ya medidas."""
    return [(it, 100.0 * pasan / total)
            for it, pasan, total in filas if pasan is not None]


def buscar_meseta(puntos, umbral=UMBRAL_MESETA):
    """Primera iteracion cuya mejora sobre la anterior no llega al umbral."""
    for i in range(1, len(puntos)):
        if puntos[i][1] - puntos[i - 1][1] < umbral:
            return puntos[i][0]
    return None


# --------------------------------------------------------------------------
# Textos de cada idioma
# --------------------------------------------------------------------------

TEXTOS = {
    "ES": {
        "archivo": "Figura_P3_verificador_ES.tex",
        "titulo_comentario":
            "Figura 1 -- Verificador en el bucle (P3). Version en espanol.",
        "xlabel": r"Iteraciones de corrección",
        "ylabel": r"Programas que pasan el verificador (\%)",
        "leyenda_curva": r"Agente propuesto (verificador en el bucle)",
        "leyenda_ref_propia": r"Sin verificador (iteración 0)",
        "leyenda_ref_sin": r"Fakih \emph{et al.}: sin verificación (47\,\%)",
        "leyenda_ref_con": r"Fakih \emph{et al.}: con verificación (72\,\%)",
        "meseta": r"deja de subir",
        "pendiente": (r"Ejes fijados en el diseño;\\"
                      r"la curva se traza al cerrar\\el banco de casos"),
        "caption_diseno": (
            r"Proporción de programas generados que pasan el verificador en "
            r"función del número de iteraciones de corrección (subproblema "
            r"P3). La línea de referencia es la generación sin verificador, "
            r"es decir el valor en la iteración cero. Las líneas punteadas "
            r"reproducen los valores publicados por Fakih \emph{et al.} "
            r"\cite{%s}, que no son resultados de este trabajo. Los ejes y "
            r"las referencias quedan fijados en el diseño del experimento; la "
            r"curva se traza cuando concluya la ejecución del banco de casos."
            % REF_CITA),
        "caption_datos": (
            r"Proporción de programas generados que pasan el verificador en "
            r"función del número de iteraciones de corrección (subproblema "
            r"P3). La línea de referencia es la generación sin verificador, "
            r"es decir el valor en la iteración cero. Las líneas punteadas "
            r"reproducen los valores publicados por Fakih \emph{et al.} "
            r"\cite{%s}, que no son resultados de este trabajo."
            % REF_CITA),
        "caption_meseta": (
            r" La mejora se agota en la iteración %d, donde la ganancia cae "
            r"por debajo de %s puntos porcentuales."),
    },
    "EN": {
        "archivo": "Figure_P3_verifier_EN.tex",
        "titulo_comentario":
            "Figure 1 -- Verifier in the loop (P3). English version.",
        "xlabel": r"Correction iterations",
        "ylabel": r"Programs passing the verifier (\%)",
        "leyenda_curva": r"Proposed agent (verifier in the loop)",
        "leyenda_ref_propia": r"No verifier (iteration 0)",
        "leyenda_ref_sin": r"Fakih \emph{et al.}: no verification (47\,\%)",
        "leyenda_ref_con": r"Fakih \emph{et al.}: with verification (72\,\%)",
        "meseta": r"stops rising",
        "pendiente": (r"Axes fixed at design time;\\"
                      r"the curve is drawn once the\\case bank is completed"),
        "caption_diseno": (
            r"Share of generated programs that pass the verifier as a "
            r"function of the number of correction iterations (subproblem "
            r"P3). The reference line is generation without a verifier, that "
            r"is, the value at iteration zero. Dotted lines reproduce the "
            r"values reported by Fakih \emph{et al.} \cite{%s}, which are not "
            r"results of this work. Axes and reference lines are fixed at "
            r"design time; the curve is drawn once the case bank has been "
            r"executed." % REF_CITA),
        "caption_datos": (
            r"Share of generated programs that pass the verifier as a "
            r"function of the number of correction iterations (subproblem "
            r"P3). The reference line is generation without a verifier, that "
            r"is, the value at iteration zero. Dotted lines reproduce the "
            r"values reported by Fakih \emph{et al.} \cite{%s}, which are not "
            r"results of this work." % REF_CITA),
        "caption_meseta": (
            r" The gain is exhausted at iteration %d, where the improvement "
            r"falls below %s percentage points."),
    },
}


# --------------------------------------------------------------------------
# LaTeX
# --------------------------------------------------------------------------

CABECERA_TEX = r"""%% %(titulo)s
%% -------------------------------------------------------------------------
%% GENERADO POR _figura_p3.py DEL REPOSITORIO MIGRA-IA. NO EDITAR A MANO:
%% cualquier cambio se pierde al regenerar. Los numeros salen de
%% data/figura_p3_verificador.csv; para llenar la figura se completa ese CSV
%% y se vuelve a ejecutar el script.
%%
%% PAQUETES NECESARIOS EN EL PREAMBULO DEL .tex PRINCIPAL:
%%   \usepackage{tikz}          ya esta (circulos Harvey de la Tabla I)
%%   \usepackage{pgfplots}      NUEVO
%%   \pgfplotsset{compat=1.18}  NUEVO
%% Si falta alguno, la figura NO compila.
%%
%% ESTADO: %(estado)s
%% -------------------------------------------------------------------------
"""

CUERPO_TEX = r"""\begin{figure}[!tb]
\centering
\begin{tikzpicture}
\begin{axis}[
  width=\columnwidth,
  height=0.70\columnwidth,
  xlabel={%(xlabel)s},
  ylabel={%(ylabel)s},
  xmin=-0.2, xmax=%(xmax)s,
  ymin=0, ymax=100,
  xtick={%(xtick)s},
  ytick={0,20,40,60,80,100},
  grid=major,
  grid style={gray!22, line width=0.3pt},
  axis line style={gray!60},
  tick label style={font=\footnotesize},
  label style={font=\footnotesize},
  legend style={font=\scriptsize, at={(0.98,0.03)}, anchor=south east,
                draw=gray!50, fill=white, fill opacity=0.88, text opacity=1,
                row sep=1pt},
  legend cell align=left,
]

%% --- Referencias externas publicadas (no son resultados de este trabajo) ---
\addplot[densely dotted, gray!70, line width=0.7pt, forget plot]
  coordinates {(-0.2,%(ref_con)s) (%(xmax)s,%(ref_con)s)};
\addplot[densely dotted, gray!70, line width=0.7pt, forget plot]
  coordinates {(-0.2,%(ref_sin)s) (%(xmax)s,%(ref_sin)s)};
\node[anchor=west, font=\tiny, text=gray!70] at (axis cs:-0.1,%(ref_con_etq)s)
  {%(leyenda_ref_con)s};
\node[anchor=west, font=\tiny, text=gray!70] at (axis cs:-0.1,%(ref_sin_etq)s)
  {%(leyenda_ref_sin)s};

%(bloque_datos)s
\end{axis}
\end{tikzpicture}
\caption{%(caption)s}
\label{fig:verificador}
\end{figure}
"""

BLOQUE_PENDIENTE = r"""%% --- Curva propia: PENDIENTE. No se dibuja nada inventado. ---------------
\node[align=center, font=\scriptsize\itshape, text=gray!75]
  at (axis cs:%(centro_x)s,22) {%(pendiente)s};
\addlegendimage{black, mark=*, mark size=1.4pt, line width=0.9pt}
\addlegendentry{%(leyenda_curva)s}
\addlegendimage{dashed, black!70, line width=0.8pt}
\addlegendentry{%(leyenda_ref_propia)s}
"""

BLOQUE_DATOS = r"""%% --- Linea de referencia propia: la iteracion cero, sin verificador -------
\addplot[dashed, black!70, line width=0.8pt]
  coordinates {(-0.2,%(base)s) (%(xmax)s,%(base)s)};
\addlegendentry{%(leyenda_ref_propia)s}

%% --- Curva medida --------------------------------------------------------
\addplot[black, mark=*, mark size=1.4pt, line width=0.9pt]
  coordinates {%(coordenadas)s};
\addlegendentry{%(leyenda_curva)s}
%(meseta)s%(aviso)s"""

MARCA_MESETA = r"""
%% --- Iteracion en la que la mejora se agota -------------------------------
\draw[gray!60, dashed, line width=0.5pt]
  (axis cs:%(x)s,0) -- (axis cs:%(x)s,%(y)s);
\node[anchor=south, font=\tiny, text=gray!75] at (axis cs:%(x)s,%(y_etq)s)
  {%(texto)s};
"""

AVISO_PARCIAL = r"""
\node[align=center, font=\scriptsize\itshape, text=gray!75]
  at (axis cs:%(centro_x)s,12) {%(pendiente)s};
"""


def construir_tex(idioma, filas, puntos, meseta):
    t = TEXTOS[idioma]
    xmax = filas[-1][0] + 0.2
    xtick = ",".join(str(it) for it, _, _ in filas)
    centro_x = filas[-1][0] / 2.0
    completo = len(puntos) == len(filas)

    if not puntos:
        estado = "MODO DISENO: el CSV no tiene ninguna medida todavia."
        bloque = BLOQUE_PENDIENTE % {
            "centro_x": centro_x,
            "pendiente": t["pendiente"],
            "leyenda_curva": t["leyenda_curva"],
            "leyenda_ref_propia": t["leyenda_ref_propia"],
        }
        caption = t["caption_diseno"]
    else:
        estado = ("%d de %d iteraciones medidas." % (len(puntos), len(filas))
                  + ("" if completo else " Figura AUN INCOMPLETA."))
        coords = " ".join("(%g,%.1f)" % (it, v) for it, v in puntos)
        marca = ""
        if meseta is not None:
            y_meseta = dict(puntos)[meseta]
            marca = MARCA_MESETA % {
                "x": meseta,
                "y": "%.1f" % y_meseta,
                "y_etq": "%.1f" % min(y_meseta + 2.0, 94.0),
                "texto": t["meseta"],
            }
        aviso = "" if completo else AVISO_PARCIAL % {
            "centro_x": centro_x, "pendiente": t["pendiente"]}
        bloque = BLOQUE_DATOS % {
            "base": "%.1f" % puntos[0][1],
            "xmax": xmax,
            "leyenda_ref_propia": t["leyenda_ref_propia"],
            "leyenda_curva": t["leyenda_curva"],
            "coordenadas": coords,
            "meseta": marca,
            "aviso": aviso,
        }
        caption = t["caption_datos"]
        if meseta is not None:
            caption += t["caption_meseta"] % (meseta, ("%g" % UMBRAL_MESETA))

    cabecera = CABECERA_TEX % {"titulo": t["titulo_comentario"],
                               "estado": estado}
    cuerpo = CUERPO_TEX % {
        "xlabel": t["xlabel"],
        "ylabel": t["ylabel"],
        "xmax": xmax,
        "xtick": xtick,
        "ref_con": REF_CON_VERIFICACION,
        "ref_sin": REF_SIN_VERIFICADOR,
        "ref_con_etq": REF_CON_VERIFICACION + 3.0,
        "ref_sin_etq": REF_SIN_VERIFICADOR + 3.0,
        "leyenda_ref_con": t["leyenda_ref_con"],
        "leyenda_ref_sin": t["leyenda_ref_sin"],
        "bloque_datos": bloque,
        "caption": caption,
    }
    return cabecera + cuerpo, estado


# --------------------------------------------------------------------------
# Vista previa en SVG (sin dependencias: la misma figura, para el navegador)
# --------------------------------------------------------------------------

SVG_ANCHO, SVG_ALTO = 660, 420
M_IZQ, M_DER, M_SUP, M_INF = 78, 24, 26, 58


def _px(it, it_max):
    return M_IZQ + (it / float(it_max)) * (SVG_ANCHO - M_IZQ - M_DER)


def _py(valor):
    return M_SUP + (1.0 - valor / 100.0) * (SVG_ALTO - M_SUP - M_INF)


def construir_svg(filas, puntos, meseta):
    it_max = filas[-1][0]
    x0, x1 = _px(0, it_max), _px(it_max, it_max)
    y0, y1 = _py(0), _py(100)
    p = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" font-family="Georgia, serif">'
         % (SVG_ANCHO, SVG_ALTO, SVG_ANCHO, SVG_ALTO),
         '<rect width="100%" height="100%" fill="#ffffff"/>']

    for v in range(0, 101, 20):
        y = _py(v)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#dcdcdc" stroke-width="1"/>' % (x0, y, x1, y))
        p.append('<text x="%.1f" y="%.1f" font-size="12" fill="#555" '
                 'text-anchor="end">%d</text>' % (M_IZQ - 9, y + 4, v))
    for it, _, _ in filas:
        x = _px(it, it_max)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#dcdcdc" stroke-width="1"/>' % (x, y1, x, y0))
        p.append('<text x="%.1f" y="%.1f" font-size="12" fill="#555" '
                 'text-anchor="middle">%d</text>' % (x, y0 + 20, it))

    p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#888" '
             'stroke-width="1.2"/>' % (x0, y0, x1, y0))
    p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#888" '
             'stroke-width="1.2"/>' % (x0, y0, x0, y1))
    p.append('<text x="%.1f" y="%.1f" font-size="13" fill="#222" '
             'text-anchor="middle">Iteraciones de correccion</text>'
             % ((x0 + x1) / 2.0, SVG_ALTO - 14))
    p.append('<text transform="translate(20,%.1f) rotate(-90)" font-size="13" '
             'fill="#222" text-anchor="middle">Programas que pasan el '
             'verificador (%%)</text>' % ((y0 + y1) / 2.0))

    for valor, etiqueta in ((REF_CON_VERIFICACION,
                             "Fakih et al.: con verificacion (72%)"),
                            (REF_SIN_VERIFICADOR,
                             "Fakih et al.: sin verificacion (47%)")):
        y = _py(valor)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#999" '
                 'stroke-width="1.2" stroke-dasharray="2,3"/>' % (x0, y, x1, y))
        p.append('<text x="%.1f" y="%.1f" font-size="11" fill="#999">%s</text>'
                 % (x0 + 6, y - 5, etiqueta))

    if puntos:
        base = puntos[0][1]
        yb = _py(base)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#444" '
                 'stroke-width="1.4" stroke-dasharray="7,4"/>'
                 % (x0, yb, x1, yb))
        p.append('<text x="%.1f" y="%.1f" font-size="11" fill="#444" '
                 'text-anchor="end">Sin verificador (iteracion 0)</text>'
                 % (x1 - 4, yb - 6))
        trazo = " ".join("%.1f,%.1f" % (_px(it, it_max), _py(v))
                         for it, v in puntos)
        p.append('<polyline points="%s" fill="none" stroke="#111" '
                 'stroke-width="2"/>' % trazo)
        for it, v in puntos:
            p.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="#111"/>'
                     % (_px(it, it_max), _py(v)))
        if meseta is not None:
            xm = _px(meseta, it_max)
            ym = _py(dict(puntos)[meseta])
            p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="#888" stroke-width="1" stroke-dasharray="4,3"/>'
                     % (xm, y0, xm, ym))
            p.append('<text x="%.1f" y="%.1f" font-size="11" fill="#666" '
                     'text-anchor="middle">deja de subir</text>'
                     % (xm, ym - 10))
    if len(puntos) < len(filas):
        p.append('<text x="%.1f" y="%.1f" font-size="13" fill="#8a8a8a" '
                 'font-style="italic" text-anchor="middle">Ejes fijados en el '
                 'diseno; la curva se traza al cerrar el banco de casos</text>'
                 % ((x0 + x1) / 2.0, _py(20)))
    p.append('</svg>')
    return "\n".join(p)


VISTA_HTML = """<!doctype html>
<html lang="es"><meta charset="utf-8">
<title>Figura 1 - Verificador en el bucle</title>
<style>
 body{font:15px Georgia,serif;color:#222;background:#faf9f7;margin:0;
      padding:32px;display:flex;flex-direction:column;align-items:center}
 figure{margin:0;max-width:720px}
 figcaption{font-size:13px;color:#444;line-height:1.5;margin-top:14px;
            text-align:justify}
 .nota{font-size:12px;color:#777;margin-top:22px;max-width:720px;
       border-top:1px solid #ddd;padding-top:12px;line-height:1.5}
 h1{font-size:17px;margin:0 0 18px}
</style>
<h1>Figura 1 &mdash; Vista previa del dise&ntilde;o</h1>
<figure>
%(svg)s
<figcaption>%(pie)s</figcaption>
</figure>
<p class="nota">%(estado)s Vista previa generada por
<code>_figura_p3.py</code> desde <code>data/figura_p3_verificador.csv</code>.
La versi&oacute;n que se compila en el paper es el <code>.tex</code> con
pgfplots, generado por este mismo script.</p>
</html>
"""

PIE_VISTA = ("Proporcion de programas generados que pasan el verificador frente "
             "al numero de iteraciones de correccion (subproblema P3). La linea "
             "de referencia es la generacion sin verificador, la iteracion cero. "
             "Las lineas punteadas son los valores publicados por Fakih et al., "
             "que no son resultados de este trabajo.")


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Genera la figura principal (verificador en el lazo)")
    ap.add_argument("--salida", action="append", default=None,
                    help="carpeta donde escribir los .tex; se puede repetir")
    ap.add_argument("--csv", default=RUTA_CSV)
    args = ap.parse_args()

    # docs/figuras es la vista oficial del proyecto: solo se toca cuando los
    # datos son los canonicos. Con un --csv de prueba, la salida va unicamente
    # a donde diga --salida, para no ensuciar la vista previa buena.
    canonico = os.path.abspath(args.csv) == os.path.abspath(RUTA_CSV)
    destinos = list(args.salida or [])
    if canonico and SALIDA_POR_DEFECTO not in destinos:
        destinos.append(SALIDA_POR_DEFECTO)
    if not destinos:
        destinos.append(SALIDA_POR_DEFECTO)
    destino_vista = SALIDA_POR_DEFECTO if canonico else destinos[0]

    filas = leer_csv(args.csv)
    problemas = validar(filas)
    if problemas:
        print("La figura NO se genero. El CSV tiene %d problema(s):"
              % len(problemas))
        for p in problemas:
            print("  - %s" % p)
        return 1

    puntos = puntos_medidos(filas)
    meseta = buscar_meseta(puntos)

    print("Figura principal: el verificador en el lazo (P3)")
    print("  eje X  iteraciones de correccion: 0 a %d" % filas[-1][0])
    print("  eje Y  programas que pasan el verificador, 0 a 100 %")
    print("  referencia propia   la iteracion cero, sin verificador")
    print("  referencia externa  %g %% y %g %% de Fakih et al. (%s)"
          % (REF_SIN_VERIFICADOR, REF_CON_VERIFICACION, REF_CITA))
    print("  medidas en el CSV   %d de %d iteraciones"
          % (len(puntos), len(filas)))
    if meseta is not None:
        print("  deja de subir en la iteracion %d (gana menos de %g puntos)"
              % (meseta, UMBRAL_MESETA))
    print("")

    escritos = []
    for destino in destinos:
        if not os.path.isdir(destino):
            os.makedirs(destino)
        for idioma in ("ES", "EN"):
            texto, estado = construir_tex(idioma, filas, puntos, meseta)
            ruta = os.path.join(destino, TEXTOS[idioma]["archivo"])
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(texto)
            escritos.append(ruta)

    svg = construir_svg(filas, puntos, meseta)
    _, estado = construir_tex("ES", filas, puntos, meseta)
    ruta_svg = os.path.join(destino_vista, "figura_p3_verificador.svg")
    with open(ruta_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    escritos.append(ruta_svg)
    ruta_html = os.path.join(destino_vista, "figura_p3_verificador.html")
    with open(ruta_html, "w", encoding="utf-8") as fh:
        fh.write(VISTA_HTML % {"svg": svg, "pie": PIE_VISTA, "estado": estado})
    escritos.append(ruta_html)

    print("Estado: %s" % estado)
    print("Escritos %d archivos:" % len(escritos))
    for r in escritos:
        print("  %s" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
