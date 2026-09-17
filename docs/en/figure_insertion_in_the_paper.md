# Figures prepared for the paper — recipes ready, NOT applied

**Select language:** [Español](../figuras/insercion_en_el_paper.md) · [English](figure_insertion_in_the_paper.md)
Status: **prepared and not applied**. The paper has not been touched. These
recipes exist so that inserting is a single step whenever it is decided, and so
that it can be undone just as fast.

Reason for the wait: the paper goes to **exactly six pages** and since
2026-09-04 it carries **+145 words that have not been measured**. Adding figures
without having compiled would be deciding blind.

---

## What the paper ALREADY has and compares

**Table I is already an image that shows comparisons**: 14 related works × 6
capabilities, with Harvey balls and a final row "This work". If the requirement
of the master's degree refers to comparing the proposal with the state of the
art, **it is met and it costs zero pages**. What Table I does not compare is the
performance of our model against its baselines: that is what Figure A is for.

---

## Figure A — comparison of models on P1 *(the one that answers the requirement)*

Files: `Figura_P1_comparacion_ES.tex` · `Figure_P1_comparison_EN.tex`
Generator: `_figure_comparison.py` · Label: `fig:comparacion`

Three bars over the same frozen split (n=9, k=2), on the metric that decides,
the macro $F_1$:

| Model | macro $F_1$ | Color |
|---|---|---|
| Trivial (majority class) | 0.402 ±0.038 | light grey — **it is the reference line** |
| Classic (ordinal logistic) | 0.688 ±0.442 | dark grey |
| **Proposal (agent with RAG)** | **pending** | **blue `#1F4E9C`, thick outline** |

Our bar goes in a distinctive color and, as long as it is not measured, it is
drawn as a **gap marked with the word "pendiente"**, never with an invented
number. The figures for the trivial and the classic model are not written by
hand: the script imports `_baseline.py` and runs the cross-validation again.

The error bars overlap, and the caption says so: the advantage of the classic
model is an indication that the age carries signal, not proof that the model
works.

---

## Figure B — curve of the verifier in the loop, P3 *(the one from the anatomy guideline)*

Files: `Figura_P3_verificador_ES.tex` · `Figure_P3_verifier_EN.tex`
Generator: `_figure_p3.py` · Label: `fig:verificador`

Proportion of programs that pass the verifier against correction iterations. Own
reference: iteration zero, with no verifier. External references as dotted
lines: 47 % and 72 % from Fakih *et al.*, labelled as belonging to others. Today
it is **in design mode**: labelled axes and a curve pending the case bank.

⚠️ **The two figures together are ~0.9 of a column.** In a six-page paper that
is already tight, the prudent move is to go in with one. A has real numbers
today; B does not.

---

## What it costs to insert

| Item | Figure A | Figure B |
|---|---|---|
| New preamble lines | 2 (shared with B) | 2 (shared with A) |
| `\input` call per language | 1 | 1 |
| New prose | ~27 words ES · ~23 EN | ~36 words ES · ~29 EN |
| Space | ~0.45 column | ~0.45 column |
| New references in `ref.bib` | **0** | **0** |

Neither of them adds references: B cites Fakih, whom the paper already cites six
times. The invariant of **26 cited references** does not move.

---

## Edit 1 — preamble, for either of the two (both `.tex` files)

`Paper_Tesis.tex` line 16 and `Paper_Tesis_EN.tex` line 16 have
`\usepackage{tikz}`. Below it:

```latex
\usepackage{pgfplots}       % figuras generadas por el repositorio MIGRA-IA
\pgfplotsset{compat=1.18}
```

`pgfplots` comes with Overleaf as standard and rests on `tikz`, already loaded
by the Harvey balls of Table I. The color is provided by `xcolor`, also loaded.

---

## Edit 2 — Figure A

**ES**, `Paper_Tesis.tex` line 357, the subsection *Técnica candidata* ends with
"…justificada si supera a ambos bajo la misma partición." Right after it, in the
same paragraph:

```latex
La Fig.~\ref{fig:comparacion} sitúa ese contraste: la propuesta solo cuenta
si su barra supera la del modelo clásico y, antes que nada, la línea del
trivial.
```

And after closing the paragraph:

```latex
\input{Figures/Figura_P1_comparacion_ES}
```

**EN**, `Paper_Tesis_EN.tex` line 352, "…beats both under the same partition."
After it:

```latex
Fig.~\ref{fig:comparacion} frames that contrast: the proposal counts only if
its bar clears the classical model and, above all, the trivial reference line.
```

```latex
\input{Figures/Figure_P1_comparison_EN}
```

---

## Edit 3 — Figure B

**ES**, `Paper_Tesis.tex` line 375, the evaluation plan ends with "…se valora
con una rúbrica de evaluadores expertos." After it:

```latex
La Fig.~\ref{fig:verificador} fija la forma en que se reportará ese
resultado: los ejes y las líneas de referencia quedan decididos antes de
ejecutar el banco de casos, de modo que la curva no pueda elegirse después.
```

```latex
\input{Figures/Figura_P3_verificador_ES}
```

**EN**, `Paper_Tesis_EN.tex` line 369, "…assessed with a rubric applied by
expert evaluators." After it:

```latex
Fig.~\ref{fig:verificador} fixes how that result will be reported: axes and
reference lines are decided before the case bank is executed, so that the
curve cannot be chosen afterwards.
```

```latex
\input{Figures/Figure_P3_verifier_EN}
```

⚠️ **The backslash of `\input`.** On 2026-08-04 three of the four calls were
written without it and the tables did not come out in the PDF. When applying
this, check it.

---

## After applying

1. Regenerate the ZIP files with Python's `zipfile` —never `Compress-Archive`,
   which writes paths with a backslash and Overleaf does not read them as
   folders—. Each inserted figure adds one entry: from 4 to 5, or to 6 with
   both.
2. Compile the ES one in Overleaf and count pages.
3. If it comes out at 7: the identified cut is **the prose of Section II** (545
   words about a Table I that already compares), **never Section III** and not
   the note on the use of AI.

## To undo it

Remove the two preamble lines, the sentence and the `\input` of each language.
The `.tex` files of the figures can stay in `Figures\`: if nobody calls them,
they do not appear and they are not packaged.

## If the numbers change

No figure `.tex` file is edited by hand. The output path is each person's own
paper folder: replace the placeholder with yours.

```
python _figure_comparison.py --output "RUTA\DE\LA\CARPETA\DEL\PAPER\Figures"
python _figure_p3.py          --output "RUTA\DE\LA\CARPETA\DEL\PAPER\Figures"
```

The bar for the proposal is filled in from `data\figure_comparison_proposal.csv`;
the verifier curve, from `data\figure_p3_verifier.csv`. The trivial and the
classic model are not written anywhere: they come out of running `_baseline.py`.
