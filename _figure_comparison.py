"""Figura de comparacion del paper: los modelos de referencia frente al nuestro.

QUE ES ESTO
-----------
El paper necesita una imagen que muestre las comparaciones. Esta es la de P1,
el subproblema de riesgo ordinal que asigna el rubro:

  trivial      clase mayoritaria del pliegue de entrenamiento, sin variables
  clasico      regresion logistica ordinal sobre la antiguedad (el asignado)
  propuesta    el agente de este trabajo, EN COLOR DISTINTIVO

La metrica es el F1 macro, que PROTOCOLO_VALIDACION.md congelo como la que
decide, y la linea de referencia es el trivial: por debajo de esa raya no hay
nada que publicar.

DE DONDE SALEN LOS NUMEROS
--------------------------
De ningun sitio a mano. El script importa _baseline.py y vuelve a correr la
misma validacion cruzada estratificada y agrupada por fabricante, con la misma
particion congelada. Si _baseline.py cambia, la figura cambia con el.

La barra de la propuesta se lee de data/figure_comparison_proposal.csv, que
nace vacio: mientras lo este, la barra se dibuja como hueco marcado -contorno
del color distintivo y la palabra pendiente- y NUNCA con un valor inventado.

    python _figura_comparacion.py
    python _figura_comparacion.py --salida "C:\\ruta\\del\\paper\\Figures"

CONVENCION: codigo y pantalla en ASCII, como el resto del repositorio; el
LaTeX que se escribe lleva tildes porque es texto del paper, y se guarda en
UTF-8.
"""

from __future__ import annotations

import argparse
import os
import sys

import _baseline as bl

PROPOSAL_PATH = os.path.join("data", "figure_comparison_proposal.csv")
DEFAULT_OUTPUT = os.path.join("docs", "figuras")

# Color distintivo de la propuesta. El resto de la figura es gris, para que la
# barra nuestra se lea sola incluso impresa en blanco y negro (es la unica con
# contorno grueso y trama).
PROPOSAL_COLOR = "1F4E9C"

METRIC = "f1_macro"


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------

def measure():
    """Corre la validacion cruzada de _baseline.py y devuelve lo que se pinta."""
    data = bl.load()
    pliegues, k, _nota = bl.stratified_partition(data)
    res = bl.evaluate(data, pliegues)
    cv = res["cv"]
    return {
        "k": k,
        "n": len(data),
        "trivial": cv["b0"][METRIC],
        "clasico": cv["b1"][METRIC],
        "exactitud": (cv["b0"]["exactitud"], cv["b1"]["exactitud"]),
        "ordinal": (cv["b0"]["error_ordinal_medio"],
                    cv["b1"]["error_ordinal_medio"]),
    }


def read_proposal(path):
    """(media, sd) de la propuesta, o None si todavia no se ha medido."""
    if not os.path.exists(path):
        return None
    cabecera = None
    with open(path, "r", encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            campos = [c.strip() for c in linea.split(",")]
            if cabecera is None:
                cabecera = campos
                continue
            if campos[0] != METRIC:
                continue
            if len(campos) < 3 or campos[1] == "":
                return None
            media = float(campos[1])
            sd = float(campos[2]) if campos[2] != "" else 0.0
            if not 0.0 <= media <= 1.0:
                raise SystemExit(
                    "ERROR: la media de la propuesta es %.3f y el F1 macro va "
                    "de 0 a 1" % media)
            if sd < 0.0:
                raise SystemExit("ERROR: la desviacion no puede ser negativa")
            return (media, sd)
    return None


# --------------------------------------------------------------------------
# Textos
# --------------------------------------------------------------------------

TEXTOS = {
    "ES": {
        "archivo": "Figura_P1_comparacion_ES.tex",
        "title": "Figura -- Comparacion de modelos en P1. Version en espanol.",
        "ylabel": r"$F_1$ macro",
        "trivial": r"Trivial\\\scriptsize(clase mayoritaria)",
        "clasico": r"Clásico\\\scriptsize(log. ordinal)",
        "propuesta": r"\textbf{Propuesta}\\\scriptsize(agente con RAG)",
        "referencia": r"referencia: el trivial",
        "pendiente": r"pendiente",
        "caption": (
            r"Comparación de modelos en el subproblema P1 (riesgo ordinal), "
            r"sobre la misma partición estratificada y agrupada por fabricante "
            r"($n=%(n)d$, $k=%(k)d$). La métrica es el $F_1$ macro, la que "
            r"decide; la línea discontinua marca el valor del modelo trivial, "
            r"por debajo del cual no hay resultado publicable. Las barras de "
            r"error son la desviación entre pliegues: se solapan, de modo que "
            r"la ventaja del modelo clásico es indicio de que la antigüedad "
            r"lleva señal y no evidencia de que el modelo funcione. %(cierre)s"),
        "cierre_pendiente": (
            r"La barra de la propuesta, en color, queda vacía hasta medirla "
            r"bajo esa misma partición."),
        "cierre_medida": (
            r"La propuesta, en color, se midió bajo esa misma partición."),
    },
    "EN": {
        "archivo": "Figure_P1_comparison_EN.tex",
        "title": "Figure -- Model comparison on P1. English version.",
        "ylabel": r"Macro $F_1$",
        "trivial": r"Trivial\\\scriptsize(majority class)",
        "clasico": r"Classical\\\scriptsize(ordinal log.)",
        "propuesta": r"\textbf{Proposed}\\\scriptsize(agent with RAG)",
        "referencia": r"reference: the trivial model",
        "pendiente": r"pending",
        "caption": (
            r"Model comparison on subproblem P1 (ordinal risk), over the same "
            r"stratified, manufacturer-grouped partition ($n=%(n)d$, "
            r"$k=%(k)d$). The metric is the macro $F_1$, the deciding one; the "
            r"dashed line marks the trivial model, below which no result is "
            r"publishable. Error bars are the between-fold deviation: they "
            r"overlap, so the advantage of the classical model is an "
            r"indication that age carries signal, not evidence that the model "
            r"works. %(cierre)s"),
        "cierre_pendiente": (
            r"The proposal's bar, in color, stays empty until it is measured "
            r"under that same partition."),
        "cierre_medida": (
            r"The proposal, in color, was measured under that same partition."),
    },
}


# --------------------------------------------------------------------------
# LaTeX
# --------------------------------------------------------------------------

TEX_HEADER = r"""%% %(title)s
%% -------------------------------------------------------------------------
%% GENERADO POR _figura_comparacion.py DEL REPOSITORIO MIGRA-IA.
%% NO EDITAR A MANO: cualquier cambio se pierde al regenerar.
%% Las cifras del trivial y del clasico salen de correr _baseline.py; la de la
%% propuesta, de data/figure_comparison_proposal.csv.
%%
%% PAQUETES NECESARIOS EN EL PREAMBULO DEL .tex PRINCIPAL:
%%   \usepackage{pgfplots}      NUEVO
%%   \pgfplotsset{compat=1.18}  NUEVO
%%   \usepackage[table]{xcolor} ya esta (Tabla I)
%%
%% ESTADO: %(status)s
%% -------------------------------------------------------------------------
\definecolor{migrapropuesta}{HTML}{%(color)s}
"""

CUERPO_TEX = r"""\begin{figure}[!tb]
\centering
\begin{tikzpicture}
\begin{axis}[
  ybar,
  width=\columnwidth,
  height=0.52\columnwidth,
  bar width=15pt,
  ymin=0, ymax=1.0,
  ytick={0,0.2,0.4,0.6,0.8,1.0},
  ylabel={%(ylabel)s},
  symbolic x coords={trivial,clasico,propuesta},
  xtick=data,
  xticklabels={%(etq_trivial)s, %(etq_clasico)s, %(etq_propuesta)s},
  xticklabel style={align=center, font=\footnotesize},
  tick label style={font=\footnotesize},
  label style={font=\footnotesize},
  enlarge x limits=0.28,
  grid=major,
  grid style={gray!22, line width=0.3pt},
  axis line style={gray!60},
  error bars/error bar style={gray!70, line width=0.6pt},
]

%% --- Linea de referencia: el modelo trivial ------------------------------
\addplot[sharp plot, dashed, black!65, line width=0.8pt, forget plot]
  coordinates {(trivial,%(ref)s) (propuesta,%(ref)s)};
\node[anchor=south east, font=\tiny, text=black!65]
  at (axis cs:propuesta,%(ref_etq)s) {%(referencia)s};

%% --- Los dos modelos de referencia, en gris ------------------------------
\addplot+[ybar, draw=black!70, fill=gray!35, error bars/.cd,
          y dir=both, y explicit]
  coordinates {
    (trivial,%(trivial)s) +- (0,%(trivial_sd)s)
    (clasico,%(clasico)s) +- (0,%(clasico_sd)s)
  };

%(bloque_propuesta)s
\end{axis}
\end{tikzpicture}
\caption{%(caption)s}
\label{fig:comparacion}
\end{figure}
"""

PROPUESTA_PENDIENTE = r"""%% --- La propuesta: hueco marcado, no hay medida todavia ------------------
\addplot[ybar, draw=migrapropuesta, line width=1pt, dashed,
         fill=migrapropuesta!8, forget plot]
  coordinates {(propuesta,1.0)};
\node[rotate=90, font=\scriptsize\itshape, text=migrapropuesta]
  at (axis cs:propuesta,0.5) {%(pendiente)s};
"""

PROPUESTA_MEDIDA = r"""%% --- La propuesta, en color distintivo -----------------------------------
\addplot+[ybar, draw=migrapropuesta, line width=1pt, fill=migrapropuesta!75,
          error bars/.cd, y dir=both, y explicit]
  coordinates {(propuesta,%(value)s) +- (0,%(sd)s)};
"""


def build_tex(idioma, med, proposal):
    t = TEXTOS[idioma]
    ref = med["trivial"][0]
    if proposal is None:
        status = ("MODO DISENO: la propuesta aun no esta medida; su barra va "
                  "como hueco.")
        bloque = PROPUESTA_PENDIENTE % {"pendiente": t["pendiente"]}
        cierre = t["cierre_pendiente"]
    else:
        status = "Propuesta medida: %.3f +-%.3f" % proposal
        bloque = PROPUESTA_MEDIDA % {"value": "%.3f" % proposal[0],
                                     "sd": "%.3f" % proposal[1]}
        cierre = t["cierre_medida"]

    cabecera = TEX_HEADER % {"title": t["title"], "status": status,
                               "color": PROPOSAL_COLOR}
    cuerpo = CUERPO_TEX % {
        "ylabel": t["ylabel"],
        "etq_trivial": t["trivial"],
        "etq_clasico": t["clasico"],
        "etq_propuesta": t["propuesta"],
        "ref": "%.3f" % ref,
        "ref_etq": "%.3f" % (ref + 0.02),
        "referencia": t["referencia"],
        "trivial": "%.3f" % med["trivial"][0],
        "trivial_sd": "%.3f" % med["trivial"][1],
        "clasico": "%.3f" % med["clasico"][0],
        "clasico_sd": "%.3f" % med["clasico"][1],
        "bloque_propuesta": bloque,
        "caption": t["caption"] % {"n": med["n"], "k": med["k"],
                                   "cierre": cierre},
    }
    return cabecera + cuerpo, status


# --------------------------------------------------------------------------
# Vista previa en SVG
# --------------------------------------------------------------------------

SVG_ANCHO, SVG_ALTO = 660, 430
M_IZQ, M_RIGHT, M_SUP, M_INF = 82, 26, 26, 78
ANCHO_BARRA = 78


def _py(v):
    return M_SUP + (1.0 - v) * (SVG_ALTO - M_SUP - M_INF)


def build_svg(med, proposal):
    x0, x1 = M_IZQ, SVG_ANCHO - M_RIGHT
    y0, y1 = _py(0.0), _py(1.0)
    centros = [x0 + (x1 - x0) * f for f in (0.18, 0.5, 0.82)]
    color = "#" + PROPOSAL_COLOR

    p = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" font-family="Georgia, serif">'
         % (SVG_ANCHO, SVG_ALTO, SVG_ANCHO, SVG_ALTO),
         '<rect width="100%" height="100%" fill="#ffffff"/>']

    for i in range(6):
        v = i * 0.2
        y = _py(v)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#dcdcdc" stroke-width="1"/>' % (x0, y, x1, y))
        p.append('<text x="%.1f" y="%.1f" font-size="12" fill="#555" '
                 'text-anchor="end">%.1f</text>' % (M_IZQ - 9, y + 4, v))
    p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#888" '
             'stroke-width="1.2"/>' % (x0, y0, x1, y0))
    p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#888" '
             'stroke-width="1.2"/>' % (x0, y0, x0, y1))
    p.append('<text transform="translate(22,%.1f) rotate(-90)" font-size="13" '
             'fill="#222" text-anchor="middle">F1 macro</text>'
             % ((y0 + y1) / 2.0))

    def bar(cx, value, sd, relleno, borde, thickness, discontinua=False):
        h = (y0 - _py(value))
        trazo = ' stroke-dasharray="6,4"' if discontinua else ''
        p.append('<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="%s" '
                 'stroke="%s" stroke-width="%s"%s/>'
                 % (cx - ANCHO_BARRA / 2.0, _py(value), ANCHO_BARRA, h,
                    relleno, borde, thickness, trazo))
        if sd:
            arriba, abajo = _py(min(value + sd, 1.0)), _py(max(value - sd, 0.0))
            p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="#777" stroke-width="1.3"/>'
                     % (cx, arriba, cx, abajo))
            for y in (arriba, abajo):
                p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                         'stroke="#777" stroke-width="1.3"/>'
                         % (cx - 9, y, cx + 9, y))

    bar(centros[0], med["trivial"][0], med["trivial"][1], "#d9d9d9", "#666", "1")
    bar(centros[1], med["clasico"][0], med["clasico"][1], "#a8a8a8", "#444", "1")
    if proposal is None:
        bar(centros[2], 1.0, 0.0, "#f2f5fb", color, "2", True)
        p.append('<text transform="translate(%.1f,%.1f) rotate(-90)" '
                 'font-size="13" fill="%s" font-style="italic" '
                 'text-anchor="middle">pendiente</text>'
                 % (centros[2] + 4, _py(0.5), color))
    else:
        bar(centros[2], proposal[0], proposal[1], color, color, "2")

    yref = _py(med["trivial"][0])
    p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#444" '
             'stroke-width="1.4" stroke-dasharray="7,4"/>'
             % (x0, yref, x1, yref))
    p.append('<text x="%.1f" y="%.1f" font-size="11" fill="#444" '
             'text-anchor="end">linea de referencia: el trivial</text>'
             % (x1 - 4, yref - 6))

    etiquetas = [("Trivial", "(clase mayoritaria)", "#333"),
                 ("Clasico", "(log. ordinal)", "#333"),
                 ("Propuesta", "(agente con RAG)", color)]
    for cx, (arriba, abajo, col) in zip(centros, etiquetas):
        peso = "bold" if col == color else "normal"
        p.append('<text x="%.1f" y="%.1f" font-size="13" fill="%s" '
                 'font-weight="%s" text-anchor="middle">%s</text>'
                 % (cx, y0 + 22, col, peso, arriba))
        p.append('<text x="%.1f" y="%.1f" font-size="11" fill="#777" '
                 'text-anchor="middle">%s</text>' % (cx, y0 + 39, abajo))
    p.append('</svg>')
    return "\n".join(p)


VISTA_HTML = """<!doctype html>
<html lang="es"><meta charset="utf-8">
<title>Figura de comparacion - P1</title>
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
<h1>Figura de comparaci&oacute;n &mdash; P1, riesgo ordinal</h1>
<figure>
%(svg)s
<figcaption>%(pie)s</figcaption>
</figure>
<p class="note">%(status)s Las cifras del trivial y del cl&aacute;sico se
recalculan corriendo <code>_baseline.py</code>; ninguna est&aacute; escrita a
mano. La versi&oacute;n que se compila en el paper es el <code>.tex</code> con
pgfplots, generado por este mismo script.</p>
</html>
"""


def view_caption(med):
    return ("Comparacion de modelos en el subproblema P1, sobre la misma "
            "particion estratificada y agrupada por fabricante (n=%d, k=%d). "
            "La metrica es el F1 macro, la que decide. La raya discontinua es "
            "el modelo trivial: por debajo no hay resultado publicable. Las "
            "barras de error son la desviacion entre pliegues y se solapan, "
            "asi que la ventaja del clasico es un indicio, no una prueba."
            % (med["n"], med["k"]))


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Figura de comparacion de modelos en P1")
    ap.add_argument("--output", action="append", default=None)
    ap.add_argument("--proposal", default=PROPOSAL_PATH)
    args = ap.parse_args()

    canonico = os.path.abspath(args.proposal) == os.path.abspath(PROPOSAL_PATH)
    destinos = list(args.output or [])
    if canonico and DEFAULT_OUTPUT not in destinos:
        destinos.append(DEFAULT_OUTPUT)
    if not destinos:
        destinos.append(DEFAULT_OUTPUT)
    view_target = DEFAULT_OUTPUT if canonico else destinos[0]

    med = measure()
    proposal = read_proposal(args.proposal)

    print("Figura de comparacion de P1")
    print("  metrica que decide  F1 macro")
    print("  particion           estratificada y agrupada por fabricante, "
          "n=%d, k=%d" % (med["n"], med["k"]))
    print("  trivial   %.3f +-%.3f   <- linea de referencia"
          % med["trivial"])
    print("  clasico   %.3f +-%.3f" % med["clasico"])
    if proposal is None:
        print("  propuesta SIN MEDIR: barra en hueco, color distintivo #%s"
              % PROPOSAL_COLOR)
    else:
        print("  propuesta %.3f +-%.3f   color distintivo #%s"
              % (proposal[0], proposal[1], PROPOSAL_COLOR))
    print("  secundarias  exactitud %.3f vs %.3f | error ordinal %.3f vs %.3f"
          % (med["exactitud"][0][0], med["exactitud"][1][0],
             med["ordinal"][0][0], med["ordinal"][1][0]))
    print("")

    escritos = []
    for target in destinos:
        if not os.path.isdir(target):
            os.makedirs(target)
        for idioma in ("ES", "EN"):
            text, status = build_tex(idioma, med, proposal)
            path = os.path.join(target, TEXTOS[idioma]["archivo"])
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            escritos.append(path)

    svg = build_svg(med, proposal)
    _, status = build_tex("ES", med, proposal)
    svg_path = os.path.join(view_target, "figura_p1_comparacion.svg")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    escritos.append(svg_path)
    html_path = os.path.join(view_target, "figura_p1_comparacion.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(VISTA_HTML % {"svg": svg, "pie": view_caption(med),
                               "status": status})
    escritos.append(html_path)

    print("Estado: %s" % status)
    print("Escritos %d archivos:" % len(escritos))
    for r in escritos:
        print("  %s" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
