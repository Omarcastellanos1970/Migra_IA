# Figuras preparadas para el paper — recetas listas, SIN aplicar

Estado: **preparadas y no aplicadas**. El paper no se ha tocado. Estas recetas
existen para que insertar sea un solo paso cuando se decida, y para poder
deshacerlo igual de rápido.

Motivo de la espera: el paper va a **seis páginas exactas** y desde el
2026-09-04 arrastra **+145 palabras sin medir**. Añadir figuras sin haber
compilado sería decidir a ciegas.

---

## Lo que el paper YA tiene y compara

**La Tabla I ya es una imagen que muestra comparaciones**: 14 trabajos
relacionados × 6 capacidades, con círculos Harvey y una fila final «Este
trabajo». Si el requisito del máster se refiere a comparar la propuesta con el
estado del arte, **está cumplido y cuesta cero páginas**. Lo que la Tabla I no
compara es el rendimiento de nuestro modelo contra sus líneas base: para eso
es la Figura A.

---

## Figura A — comparación de modelos en P1 *(la que responde al requisito)*

Archivos: `Figura_P1_comparacion_ES.tex` · `Figure_P1_comparison_EN.tex`
Generador: `_figura_comparacion.py` · Etiqueta: `fig:comparacion`

Tres barras sobre la misma partición congelada (n=9, k=2), en la métrica que
decide, el $F_1$ macro:

| Modelo | $F_1$ macro | Color |
|---|---|---|
| Trivial (clase mayoritaria) | 0,402 ±0,038 | gris claro — **es la línea de referencia** |
| Clásico (logística ordinal) | 0,688 ±0,442 | gris oscuro |
| **Propuesta (agente con RAG)** | **pendiente** | **azul `#1F4E9C`, contorno grueso** |

La barra nuestra va en color distintivo y, mientras no esté medida, se dibuja
como **hueco marcado con la palabra «pendiente»**, nunca con un número
inventado. Las cifras del trivial y del clásico no están escritas a mano: el
script importa `_baseline.py` y vuelve a correr la validación cruzada.

Las barras de error se solapan, y el pie lo dice: la ventaja del clásico es
indicio de que la antigüedad lleva señal, no prueba de que el modelo funcione.

---

## Figura B — curva del verificador en el lazo, P3 *(la de la pauta de anatomía)*

Archivos: `Figura_P3_verificador_ES.tex` · `Figure_P3_verifier_EN.tex`
Generador: `_figura_p3.py` · Etiqueta: `fig:verificador`

Proporción de programas que pasan el verificador contra iteraciones de
corrección. Referencia propia: la iteración cero, sin verificador. Referencias
externas punteadas: 47 % y 72 % de Fakih *et al.*, rotuladas como ajenas. Hoy
está **en modo diseño**: ejes rotulados y curva pendiente del banco de casos.

⚠️ **Las dos figuras juntas son ~0,9 de columna.** En un paper de seis páginas
que ya va justo, lo prudente es entrar con una. La A tiene números reales hoy;
la B no.

---

## Lo que cuesta insertar

| Concepto | Figura A | Figura B |
|---|---|---|
| Líneas nuevas de preámbulo | 2 (compartidas con B) | 2 (compartidas con A) |
| Llamada `\input` por idioma | 1 | 1 |
| Prosa nueva | ~27 palabras ES · ~23 EN | ~36 palabras ES · ~29 EN |
| Espacio | ~0,45 columna | ~0,45 columna |
| Referencias nuevas en `ref.bib` | **0** | **0** |

Ninguna de las dos añade referencias: la B cita a Fakih, que el paper ya cita
seis veces. El invariante de **26 referencias citadas** no se mueve.

---

## Edición 1 — preámbulo, para cualquiera de las dos (los dos `.tex`)

`Paper_Tesis.tex` línea 16 y `Paper_Tesis_EN.tex` línea 16 tienen
`\usepackage{tikz}`. Debajo:

```latex
\usepackage{pgfplots}       % figuras generadas por el repositorio MIGRA-IA
\pgfplotsset{compat=1.18}
```

`pgfplots` está en Overleaf de serie y se apoya en `tikz`, ya cargado por los
círculos Harvey de la Tabla I. El color lo aporta `xcolor`, también cargado.

---

## Edición 2 — Figura A

**ES**, `Paper_Tesis.tex` línea 357, la subsección *Técnica candidata* termina
en «…justificada si supera a ambos bajo la misma partición.» Justo después, en
el mismo párrafo:

```latex
La Fig.~\ref{fig:comparacion} sitúa ese contraste: la propuesta solo cuenta
si su barra supera la del modelo clásico y, antes que nada, la línea del
trivial.
```

Y tras cerrar el párrafo:

```latex
\input{Figures/Figura_P1_comparacion_ES}
```

**EN**, `Paper_Tesis_EN.tex` línea 352, «…beats both under the same
partition.» Después:

```latex
Fig.~\ref{fig:comparacion} frames that contrast: the proposal counts only if
its bar clears the classical model and, above all, the trivial reference line.
```

```latex
\input{Figures/Figure_P1_comparison_EN}
```

---

## Edición 3 — Figura B

**ES**, `Paper_Tesis.tex` línea 375, el plan de evaluación termina en «…se
valora con una rúbrica de evaluadores expertos.» Después:

```latex
La Fig.~\ref{fig:verificador} fija la forma en que se reportará ese
resultado: los ejes y las líneas de referencia quedan decididos antes de
ejecutar el banco de casos, de modo que la curva no pueda elegirse después.
```

```latex
\input{Figures/Figura_P3_verificador_ES}
```

**EN**, `Paper_Tesis_EN.tex` línea 369, «…assessed with a rubric applied by
expert evaluators.» Después:

```latex
Fig.~\ref{fig:verificador} fixes how that result will be reported: axes and
reference lines are decided before the case bank is executed, so that the
curve cannot be chosen afterwards.
```

```latex
\input{Figures/Figure_P3_verifier_EN}
```

⚠️ **La barra invertida de `\input`.** El 2026-08-04 tres de las cuatro
llamadas estaban escritas sin ella y las tablas no salieron en el PDF. Al
aplicar esto, comprobarlo.

---

## Después de aplicar

1. Regenerar los ZIP con `zipfile` de Python —nunca `Compress-Archive`, que
   escribe rutas con barra invertida y Overleaf no las lee como carpetas—.
   Cada figura insertada suma una entrada: de 4 a 5, o a 6 con las dos.
2. Compilar la ES en Overleaf y contar páginas.
3. Si sale 7: el recorte identificado es **la prosa de la Sección II**
   (545 palabras sobre una Tabla I que ya compara), **nunca la Sección III**
   ni la nota de uso de IA.

## Para deshacer

Quitar las dos líneas de preámbulo, la frase y el `\input` de cada idioma. Los
`.tex` de las figuras pueden quedarse en `Figures\`: si nadie los llama, no
aparecen ni se empaquetan.

## Si cambian los números

No se edita a mano ningún `.tex` de figura. La ruta de salida es la carpeta
del paper de cada quien: sustituir la marca por la suya.

```
python _figura_comparacion.py --salida "RUTA\DE\LA\CARPETA\DEL\PAPER\Figures"
python _figura_p3.py          --salida "RUTA\DE\LA\CARPETA\DEL\PAPER\Figures"
```

La barra de la propuesta se llena en `data\figura_comparacion_propuesta.csv`;
la curva del verificador, en `data\figura_p3_verificador.csv`. El trivial y el
clásico no se escriben en ningún sitio: salen de correr `_baseline.py`.
