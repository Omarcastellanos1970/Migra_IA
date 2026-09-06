# PROTOCOLO — configuración experimental

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

## Español (7 frases)

El conjunto de datos procede de la tabla de ciclo de vida de plataformas de automatización del repositorio del proyecto, reúne 9 plataformas de 5 fabricantes etiquetadas en 2 de los cuatro niveles de la escala ordinal de obsolescencia (niveles 3 y 4), y su unidad de observación es la plataforma, no el caso de migración. La partición es una validación cruzada de 2 pliegues, estratificada por nivel y agrupada por fabricante, con semilla 42 y reparto determinista guardado en disco: cada pliegue aparta como prueba un bloque completo de marcas —5 y 4 plataformas de las 9, un 56 % y un 44 %— que no interviene en ningún ajuste, de modo que ninguna marca aparece a la vez en entrenamiento y en prueba. El preprocesamiento calcula una sola característica, la antigüedad de la plataforma como 2026 menos el año de lanzamiento —la única que sobrevivió a la auditoría de fuga—, y la estandariza con la media y la escala del entrenamiento, ajustadas dentro de cada pliegue y nunca sobre el conjunto completo. Se comparan tres modelos: una línea base trivial que responde siempre la clase mayoritaria del pliegue de entrenamiento, una regresión logística ordinal de probabilidades proporcionales y el agente propuesto, todavía no ejecutado; los dos primeros están implementados con la biblioteca estándar de Python 3.14.6, sin dependencias de terceros. No hay búsqueda de hiperparámetros: el espacio explorado es de cero puntos para los tres modelos, el mismo esfuerzo para todos, porque la trivial no tiene ninguno y los de la logística ordinal se fijaron de antemano en regularización L2=1,0, paso 0,05, 4000 iteraciones e inicio en ceros, idénticos en todos los pliegues. La validación es cruzada agrupada con k=2 y una sola repetición —repetirla daría el mismo resultado, porque no hay ningún paso estocástico—, y reporta la media y la desviación típica muestral entre pliegues del F1 macro como métrica principal que decide, con la exactitud y el error ordinal medio como secundarias que explican. Todo se ejecuta en CPU sobre un equipo con procesador 12th Gen Intel Core i5-12500H (12 núcleos, 16 hilos, 3,1 GHz), 31,7 GB de memoria y Windows 11 Pro de 64 bits, compilación 26200: entrenar la validación cruzada completa cuesta 67 ms, la semilla 42 queda declarada aunque no llegue a usarse por ser determinista el ajuste, y el código y los datos están publicados en https://github.com/Omarcastellanos1970/Migra_IA.

<details><summary>El mismo párrafo con las marcas de LaTeX, para pegar en Overleaf</summary>

```latex
El conjunto de datos procede de la tabla de ciclo de vida de plataformas de automatización del repositorio del proyecto, reúne 9 plataformas de 5 fabricantes etiquetadas en 2 de los cuatro niveles de la escala ordinal de obsolescencia (niveles 3 y 4), y su unidad de observación es la plataforma, no el caso de migración. La partición es una validación cruzada de 2 pliegues, estratificada por nivel y agrupada por fabricante, con semilla 42 y reparto determinista guardado en disco: cada pliegue aparta como prueba un bloque completo de marcas —5 y 4 plataformas de las 9, un 56\,\% y un 44\,\%— que no interviene en ningún ajuste, de modo que ninguna marca aparece a la vez en entrenamiento y en prueba. El preprocesamiento calcula una sola característica, la antigüedad de la plataforma como 2026 menos el año de lanzamiento —la única que sobrevivió a la auditoría de fuga—, y la estandariza con la media y la escala del entrenamiento, ajustadas dentro de cada pliegue y nunca sobre el conjunto completo. Se comparan tres modelos: una línea base trivial que responde siempre la clase mayoritaria del pliegue de entrenamiento, una regresión logística ordinal de probabilidades proporcionales y el agente propuesto, todavía no ejecutado; los dos primeros están implementados con la biblioteca estándar de Python 3.14.6, sin dependencias de terceros. No hay búsqueda de hiperparámetros: el espacio explorado es de cero puntos para los tres modelos, el mismo esfuerzo para todos, porque la trivial no tiene ninguno y los de la logística ordinal se fijaron de antemano en regularización $L_2=1{,}0$, paso 0{,}05, 4000 iteraciones e inicio en ceros, idénticos en todos los pliegues. La validación es cruzada agrupada con $k=2$ y una sola repetición —repetirla daría el mismo resultado, porque no hay ningún paso estocástico—, y reporta la media y la desviación típica muestral entre pliegues del $F_1$ macro como métrica principal que decide, con la exactitud y el error ordinal medio como secundarias que explican. Todo se ejecuta en CPU sobre un equipo con procesador 12th Gen Intel Core i5-12500H (12 núcleos, 16 hilos, 3,1 GHz), 31,7 GB de memoria y Windows 11 Pro de 64 bits, compilación 26200: entrenar la validación cruzada completa cuesta 67 ms, la semilla 42 queda declarada aunque no llegue a usarse por ser determinista el ajuste, y el código y los datos están publicados en https://github.com/Omarcastellanos1970/Migra_IA.
```

</details>

## English (7 sentences)

The dataset comes from the automation platform life-cycle table of the project repository, gathers 9 platforms from 5 manufacturers labelled in 2 of the four levels of the ordinal obsolescence scale (levels 3 and 4), and its unit of observation is the platform, not the migration case. The partition is a 2-fold cross-validation, stratified by level and grouped by manufacturer, with seed 42 and a deterministic assignment stored on disk: each fold holds out as test a complete block of brands —5 and 4 platforms out of 9, 56 % and 44 %— that takes part in no fitting, so that no brand appears in training and test at the same time. Preprocessing computes a single feature, platform age as 2026 minus the release year —the only one that survived the leakage audit—, and standardizes it with the training mean and scale, fitted inside each fold and never over the complete set. Three models are compared: a trivial baseline that always answers the majority class of the training fold, a proportional-odds ordinal logistic regression and the proposed agent, not yet executed; the first two are implemented with the Python 3.14.6 standard library, with no third-party dependencies. There is no hyperparameter search: the explored space is zero points for all three models, the same effort for everyone, because the trivial one has none and those of the ordinal logistic were fixed in advance at L2=1.0 regularization, step 0.05, 4000 iterations and a zero start, identical across folds. Validation is grouped cross-validation with k=2 and a single repetition —repeating it would give the same result, since there is no stochastic step—, and it reports the mean and sample standard deviation across folds of macro F1 as the deciding primary metric, with accuracy and mean ordinal error as explanatory secondary ones. Everything runs on CPU on a machine with a 12th Gen Intel Core i5-12500H processor (12 cores, 16 threads, 3.1 GHz), 31.7 GB of memory and Windows 11 Pro 64-bit, build 26200: training the complete cross-validation costs 67 ms, seed 42 is declared although it is never actually used because the fit is deterministic, and code and data are published at https://github.com/Omarcastellanos1970/Migra_IA.

<details><summary>Same paragraph with LaTeX markup, to paste into Overleaf</summary>

```latex
The dataset comes from the automation platform life-cycle table of the project repository, gathers 9 platforms from 5 manufacturers labelled in 2 of the four levels of the ordinal obsolescence scale (levels 3 and 4), and its unit of observation is the platform, not the migration case. The partition is a 2-fold cross-validation, stratified by level and grouped by manufacturer, with seed 42 and a deterministic assignment stored on disk: each fold holds out as test a complete block of brands —5 and 4 platforms out of 9, 56\,\% and 44\,\%— that takes part in no fitting, so that no brand appears in training and test at the same time. Preprocessing computes a single feature, platform age as 2026 minus the release year —the only one that survived the leakage audit—, and standardizes it with the training mean and scale, fitted inside each fold and never over the complete set. Three models are compared: a trivial baseline that always answers the majority class of the training fold, a proportional-odds ordinal logistic regression and the proposed agent, not yet executed; the first two are implemented with the Python 3.14.6 standard library, with no third-party dependencies. There is no hyperparameter search: the explored space is zero points for all three models, the same effort for everyone, because the trivial one has none and those of the ordinal logistic were fixed in advance at $L_2=1.0$ regularization, step 0.05, 4000 iterations and a zero start, identical across folds. Validation is grouped cross-validation with $k=2$ and a single repetition —repeating it would give the same result, since there is no stochastic step—, and it reports the mean and sample standard deviation across folds of macro $F_1$ as the deciding primary metric, with accuracy and mean ordinal error as explanatory secondary ones. Everything runs on CPU on a machine with a 12th Gen Intel Core i5-12500H processor (12 cores, 16 threads, 3.1 GHz), 31.7 GB of memory and Windows 11 Pro 64-bit, build 26200: training the complete cross-validation costs 67 ms, seed 42 is declared although it is never actually used because the fit is deterministic, and code and data are published at https://github.com/Omarcastellanos1970/Migra_IA.
```

</details>

---

## La máquina, declarada

un equipo con procesador 12th Gen Intel Core i5-12500H (12 núcleos, 16 hilos, 3,1 GHz), 31,7 GB de memoria y Windows 11 Pro de 64 bits, compilación 26200

## Relación con `PROTOCOLO_VALIDACION.md`

Aquel documento es el contrato de validación de los seis puntos, firmado el
2026-09-04: qué se congela, qué métrica decide y cuándo se abre la prueba. Este
es la configuración experimental que va al artículo. No se contradicen, pero si
alguna cifra difiere, **manda la de aquí**, porque esta se regenera desde el
código en cada ejecución.
