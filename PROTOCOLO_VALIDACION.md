# Protocolo de validación — riesgo ordinal y prioridad de reemplazo

**Firmado el 2026-09-04.** Desde esta fecha el protocolo manda: si un resultado
posterior no gusta, se reporta igual. Cambiar cualquiera de los seis puntos
obliga a anotar aquí qué se cambió, cuándo y por qué, antes de volver a correr
nada.

Lo que sigue está escrito para pegarse casi literal en la metodología del paper.

---

## El contrato — media página, para pegar en la metodología

> Esta es la versión que va al paper. Todo lo que sigue después es anexo de
> trabajo: justifica cada decisión y da los archivos donde comprobarla, pero no
> se publica.

La **unidad de observación** es la plataforma de control. La **restricción de
agrupamiento** es el fabricante, y ninguna marca se reparte entre entrenamiento y
prueba, porque dos plataformas de una misma marca comparten política de ciclo de
vida y repartirlas dejaría que el modelo la reconociera del otro lado. La
**semilla**, 42, queda declarada aunque no se use: no hay ningún paso
estocástico. Los índices de la partición están guardados en el repositorio.

El **esquema** es validación cruzada estratificada por nivel de obsolescencia
manteniendo el agrupamiento, con **k = 2** y **una sola repetición**. La *k* no
es una elección: solo dos fabricantes aportan muestras de la clase superior, de
modo que no hay con qué llenar un tercer pliegue estratificado sin partir un
rubro. Repetir no aportaría nada mientras no exista aleatoriedad. El
**preprocesamiento se ajusta dentro de cada pliegue**, nunca una sola vez sobre
el conjunto completo.

Las **métricas quedan congeladas** antes de las corridas finales. En la
clasificación ordinal la principal es el **$F_1$ macro** ---y no la exactitud,
que con clases desbalanceadas premia a quien siempre responde la mayoritaria---,
con la exactitud, el error ordinal medio y la concordancia entre evaluadores
como secundarias. En el ordenamiento la principal es la **precisión en los tres
primeros puestos**, con la posición media de los candidatos que la referencia
sitúa en cabeza y el desplazamiento medio de puesto como secundarias.

**No se permite búsqueda de hiperparámetros**: están fijados y declarados, y con
un conjunto de este tamaño buscarlos sobre la propia partición ajustaría la
búsqueda a la validación. El baseline trivial no tiene ninguno, de modo que el
esfuerzo de búsqueda es cero para ambos modelos y la comparación es justa.

Todo resultado se **reporta como media y desviación típica sobre los pliegues**,
nunca como el mejor número de una corrida, y acompañado de la procedencia de la
etiqueta con que se obtuvo.

El **conjunto de prueba** permanece apartado y **se abre una sola vez**, en la
**revisión final previa a la publicación en Zenodo**, con el protocolo ya
cerrado. Lo que salga es lo que se publica: si obligara a cambiar el modelo, ese
cambio empieza un protocolo nuevo y el conjunto deja de ser válido para él.

---

## Anexo de trabajo

### 1. La partición

**Unidad de observación:** la plataforma de control (una CPU y su familia), no
el componente ni la planta. Nueve unidades en
`data/ciclo_vida_plataformas.csv`, derivadas de la Tabla 2 de obsolescencia.

**Restricción de agrupamiento:** el **fabricante**. Dos plataformas de una misma
marca comparten política de ciclo de vida, de modo que repartirlas entre
entrenamiento y prueba dejaría que el modelo aprenda la política y la reconozca
del otro lado. Ninguna marca se parte nunca.

> El rubro enuncia el agrupamiento como «caso de migración» porque supone
> componentes que comparten caso. Aquí cada fila es una plataforma
> independiente y no hay casos, así que la unidad de agrupamiento equivalente es la marca. Queda
> declarado como desviación del enunciado, no como omisión.

**Semilla:** `42`, declarada. **No se usa**: no hay ningún paso estocástico —
el ajuste arranca en ceros, el paso y las iteraciones son fijos, y no hay
barajado ni muestreo. Se dice explícitamente en vez de sugerir que la
reproducibilidad depende de ella.

**Índices guardados:** `data/particion_ciclo_vida.json`, con el esquema, la *k*,
el motivo del techo de *k*, el ámbito del preprocesamiento y las etiquetas.

**Fecha de referencia:** `2026-09-04`, fija. Las clases se derivan comparando
fechas contra ella; usar «hoy» haría que las etiquetas cambiaran solas con el
calendario.

### 2. El esquema de validación

**Validación cruzada estratificada por nivel de obsolescencia, agrupada por
fabricante.** **k = 2**, que es la mayor posible: solo dos fabricantes aportan
muestras de la clase 4 (Mitsubishi con dos, Rockwell con una), así que no hay
con qué llenar un tercer pliegue estratificado sin partir una marca.

- Pliegue 0 — prueba: Mitsubishi + Schneider + Siemens (5 muestras)
- Pliegue 1 — prueba: Omron + Rockwell (4 muestras)

**Repeticiones: 1.** Repetir no aporta nada porque no hay aleatoriedad: la misma
entrada da la misma salida, comprobado con dos corridas byte a byte idénticas.
Si en algún momento entra un componente estocástico, este punto pasa a exigir
**5 repeticiones con semillas 42, 43, 44, 45 y 46**, y el reporte pasa a
promediar sobre pliegues *y* semillas.

**Preprocesamiento dentro del pliegue.** La media y la escala con que se
estandariza la antigüedad se calculan **solo con el entrenamiento de cada
pliegue** (`b1_logistica_ordinal()`). No hay ningún ajuste hecho una sola vez
sobre las nueve filas.

### 3. Las métricas — congeladas desde hoy

| Subproblema | Principal (decide) | Secundarias (explican) |
|---|---|---|
| **P1** riesgo ordinal | **F1 macro** | exactitud · error ordinal medio |
| **P2** prioridad de reemplazo | **precisión en los 3 primeros** | posición media de los que la referencia pone en cabeza · desplazamiento medio de puesto |

**Por qué la principal de P1 es F1 macro y no la exactitud:** las clases están
desbalanceadas (6 de clase 3, 3 de clase 4) y no hay ninguna muestra de las
clases 1 y 2, de modo que la exactitud premia al que siempre dice «clase 3».

**Por qué la de P2 es precisión en los 3 primeros:** la decisión que el agente
apoya es con qué se empieza cuando el presupuesto no alcanza para todo; acertar
la cola no cambia ninguna decisión.

Las dos métricas de P2 se adaptan de su forma habitual, porque P2 es una
permutación completa y no una recuperación con un solo elemento relevante. La
adaptación está escrita en el docstring de `metricas_ranking()`.

### 4. La búsqueda permitida

**Ninguna.** Los hiperparámetros del clásico están fijados y declarados —
`L2 = 1.0`, paso `0.05`, `4000` iteraciones, inicio en ceros — y no se buscan.
Con nueve filas, buscarlos sobre la propia partición sería ajustar la búsqueda a
la validación, que es la forma más común de inflar un resultado sin darse cuenta.

El baseline trivial no tiene hiperparámetros, así que **el esfuerzo de búsqueda
es cero para los dos modelos**, que es la forma de que la comparación sea justa.

Si más adelante el conjunto crece hasta permitir búsqueda, este punto exige:
misma malla, mismo presupuesto de evaluaciones para todos los modelos, y la
búsqueda **anidada** dentro del pliegue de entrenamiento.

### 5. La forma de reporte

**Media ± desviación típica muestral (n−1) sobre los pliegues.** Nunca el mejor
número de una corrida. La cifra agrupada (micro, las nueve predicciones en una
bolsa) puede acompañar como contraste, siempre etiquetada como tal y nunca en
lugar de la media.

La tabla por pliegue se publica junto al resumen: es lo que enseña la
dispersión que una media sola esconde.

**Toda cifra va acompañada de la procedencia de su etiqueta.** Mientras el campo
`procedencia` de `data/etiquetas_p1_p2.json` diga `provisional_regla`, ningún
número derivado de ella puede presentarse como validación.

### 6. La regla del conjunto de prueba

**Apartado y cerrado.** Lo forman:

1. los **cinco casos de estudio** de la guía MIGRA-IA-GUIA-001, presentados en
   ciego en `docs/plantilla_casos_ciegos.md`, con la clave en
   `_plantilla_clave.json`;
2. las **etiquetas del panel de expertos** —clase de obsolescencia y orden de
   prioridad— que se recogen con `docs/formulario_etiquetado.md`.

**Se abre una sola vez**, en la **revisión final previa a la publicación en
Zenodo**, con el protocolo ya cerrado, y **lo que salga es lo que se publica**.
Ese momento es el que fija el punto: no una fecha del calendario, sino el hito
del proyecto —la última revisión antes de liberar la versión con DOI.

No se vuelve a ajustar nada después de abrirlo: si el resultado obliga a cambiar
el modelo, ese cambio empieza un protocolo nuevo y el
conjunto de prueba deja de ser válido para él.

Hasta hoy **no se ha abierto**. Todo lo reportado procede de los dos pliegues de
desarrollo.

---

### Deuda declarada al firmar

Se firma sabiendo que hay tres cosas abiertas, y se firma igual para que lo que
venga después no pueda acomodarse a lo que salga:

1. **La etiqueta de P1 se deriva de las mismas fechas que serían las variables**,
   así que hoy P1 es la re-derivación de una definición y no una predicción. Por
   eso la auditoría de fuga deja fuera todas las columnas de fecha y sobrevive
   una sola variable, la antigüedad. La etiqueta del panel es lo que lo convierte
   en un problema de aprendizaje real.
2. **P2 no tiene orden de referencia experto**, así que su clásico asignado
   —*gradient boosting* en modo ranking— no se ha evaluado.
3. **El conjunto es de nueve filas.** Ninguna diferencia entre modelos de este
   tamaño es estadísticamente sostenible, y el reporte lo dice en vez de
   dejarlo implícito.
