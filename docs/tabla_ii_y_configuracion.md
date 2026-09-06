# Tabla II y párrafo de configuración experimental

Generado por `_tabla_ii.py`. Ningún número está escrito a mano: salen de correr
`_baseline.py` sobre la partición congelada, y el coste de medir la inferencia
aquí mismo.

**Estado:** fila del trivial con números; el resto vacío, que es el plan de experimentos

---

## 1. El título, en una línea

> Riesgo ordinal de obsolescencia en 9 plataformas de automatización: F1 macro medio ± desviación sobre 2 pliegues agrupados por fabricante

Contiene las cuatro cosas que pide el ejercicio: el conjunto de datos
(9 plataformas de automatización), la métrica principal ($F_1$ macro),
sobre qué se promedia (2 pliegues) y el agrupamiento (por fabricante).

## 2. La tabla

| Modelo | $F_1$ macro (media ± desv.) | Exactitud | Coste (µs/caso) |
|---|---|---|---|
| **Trivial**<br><sub>clase mayoritaria del pliegue de entrenamiento</sub> | 0,402 ± 0,038 | 0,675 | 0,024 |
| **Clásico: logística ordinal**<br><sub>escala ordenada, dato tabular escaso y coeficientes auditables</sub> | --- | --- | --- |
| **Propuesta: agente con RAG y verificación**<br><sub>recupera evidencia citable y no ajusta pesos</sub> | --- | --- | --- |

Las celdas vacías son el plan de experimentos: se llenan cuando cada modelo se ejecute bajo esta misma partición. El coste es el mejor de cinco rondas y se da con dos cifras significativas, que es hasta donde llega la resolución de la medida.

## 3. El párrafo de configuración experimental (siete frases)

### Español

El conjunto de datos procede de la tabla de ciclo de vida de plataformas de automatización del repositorio del proyecto, reúne 9 plataformas de 5 fabricantes etiquetadas en 2 de los cuatro niveles de la escala ordinal de obsolescencia (niveles 3 y 4), y su unidad de observación es la plataforma, no el caso de migración. La partición es una validación cruzada de 2 pliegues, estratificada por nivel y agrupada por fabricante, con semilla 42 y reparto determinista guardado en disco: cada pliegue aparta como prueba un bloque completo de marcas —5 y 4 plataformas de las 9, un 56 % y un 44 %— que no interviene en ningún ajuste, de modo que ninguna marca aparece a la vez en entrenamiento y en prueba. El preprocesamiento calcula una sola característica, la antigüedad de la plataforma como 2026 menos el año de lanzamiento —la única que sobrevivió a la auditoría de fuga—, y la estandariza con la media y la escala del entrenamiento, ajustadas dentro de cada pliegue y nunca sobre el conjunto completo. Se comparan tres modelos: una línea base trivial que responde siempre la clase mayoritaria del pliegue de entrenamiento, una regresión logística ordinal de probabilidades proporcionales y el agente propuesto, todavía no ejecutado; los dos primeros están implementados con la biblioteca estándar de Python 3.14.6, sin dependencias de terceros. No hay búsqueda de hiperparámetros: el espacio explorado es de cero puntos para los tres modelos, el mismo esfuerzo para todos, porque la trivial no tiene ninguno y los de la logística ordinal se fijaron de antemano en regularización L2=1,0, paso 0,05, 4000 iteraciones e inicio en ceros, idénticos en todos los pliegues. La validación es cruzada agrupada con k=2 y una sola repetición —repetirla daría el mismo resultado, porque no hay ningún paso estocástico—, y reporta la media y la desviación típica muestral entre pliegues del F1 macro como métrica principal que decide, con la exactitud y el error ordinal medio como secundarias que explican. Todo se ejecuta en CPU sobre un equipo con procesador 12th Gen Intel Core i5-12500H (12 núcleos, 16 hilos, 3,1 GHz), 31,7 GB de memoria y Windows 11 Pro de 64 bits, compilación 26200: entrenar la validación cruzada completa cuesta 67 ms, la semilla 42 queda declarada aunque no llegue a usarse por ser determinista el ajuste, y el código y los datos están publicados en https://github.com/Omarcastellanos1970/Migra_IA.

### English

The dataset comes from the automation platform life-cycle table of the project repository, gathers 9 platforms from 5 manufacturers labelled in 2 of the four levels of the ordinal obsolescence scale (levels 3 and 4), and its unit of observation is the platform, not the migration case. The partition is a 2-fold cross-validation, stratified by level and grouped by manufacturer, with seed 42 and a deterministic assignment stored on disk: each fold holds out as test a complete block of brands —5 and 4 platforms out of 9, 56 % and 44 %— that takes part in no fitting, so that no brand appears in training and test at the same time. Preprocessing computes a single feature, platform age as 2026 minus the release year —the only one that survived the leakage audit—, and standardizes it with the training mean and scale, fitted inside each fold and never over the complete set. Three models are compared: a trivial baseline that always answers the majority class of the training fold, a proportional-odds ordinal logistic regression and the proposed agent, not yet executed; the first two are implemented with the Python 3.14.6 standard library, with no third-party dependencies. There is no hyperparameter search: the explored space is zero points for all three models, the same effort for everyone, because the trivial one has none and those of the ordinal logistic were fixed in advance at L2=1.0 regularization, step 0.05, 4000 iterations and a zero start, identical across folds. Validation is grouped cross-validation with k=2 and a single repetition —repeating it would give the same result, since there is no stochastic step—, and it reports the mean and sample standard deviation across folds of macro F1 as the deciding primary metric, with accuracy and mean ordinal error as explanatory secondary ones. Everything runs on CPU on a machine with a 12th Gen Intel Core i5-12500H processor (12 cores, 16 threads, 3.1 GHz), 31.7 GB of memory and Windows 11 Pro 64-bit, build 26200: training the complete cross-validation costs 67 ms, seed 42 is declared although it is never actually used because the fit is deterministic, and code and data are published at https://github.com/Omarcastellanos1970/Migra_IA.

## 4. Verificación dato a dato

Cada dato del párrafo, contra el código y contra la tabla.

| Dato | Valor | De dónde sale | ¿Coincide? |
|---|---|---|---|
| Plataformas | 9 | len(cargar()) sobre data/ciclo_vida_plataformas.csv | sí |
| Fabricantes | 5 | Mitsubishi, Omron, Rockwell, Schneider, Siemens | sí |
| Unidad de observacion | la plataforma | particion_ciclo_vida.json: agrupamiento = Fabricante | sí |
| k | 2 | particionar_estratificado(); json k=2 | sí |
| Agrupamiento | Fabricante | ningun fabricante en train y test a la vez | sí |
| Semilla | 42 | _baseline.SEMILLA; json semilla=42 | sí |
| Preprocesamiento | dentro del pliegue | ajustado dentro de cada pliegue (media y escala del entrenamiento) | sí |
| Caracteristica admitida | antiguedad = 2026 - Lanzamiento | auditoria de fuga: unica superviviente | sí |
| Metrica principal | F1 macro | PROTOCOLO_VALIDACION.md punto 3, congelada | sí |
| Secundarias | exactitud, error ordinal medio | metricas() de _baseline.py | sí |
| Promedio | media +- desv. tipica muestral entre pliegues | _media_sd(), n-1 | sí |
| Python | 3.14.6 | platform.python_version() | sí |
| Tabla, fila trivial | 0.402 +- 0.038 | cv['b0']['f1_macro'], la misma llamada que pinta la tabla | sí |
| Tabla, fila clasico | vacia por el ejercicio | medida y disponible: 0.688 +- 0.442, se llena con --con-clasico | sí |
| Tabla, fila propuesta | vacia | NO EXISTE TODAVIA: el agente no se ha ejecutado bajo esta particion | sí |
| Coste, trivial | 0.024 us/caso | mejor de 9 rondas x 2000 repeticiones; dispersion 0.031 us (131 % del valor), por eso la tabla lleva dos cifras significativas | **NO** |
| Coste, clasico | 0.542 us/caso | mejor de 9 rondas x 2000 repeticiones; dispersion 0.049 us (9 % del valor), por eso la tabla lleva dos cifras significativas | sí |
| Clases | 2 de 4 (3, 4) | etiquetas del CSV; los niveles 1 y 2 no aparecen en la muestra | sí |
| Proporciones | prueba de 5 y 4 de 9 | tamano real de cada pliegue de prueba | sí |
| Prueba apartada | si | el pliegue de prueba no entra en ningun ajuste: el preprocesamiento se ajusta en entrenamiento | sí |
| Repeticiones | 1 | una sola pasada; el ajuste es determinista y repetirla da lo mismo | sí |
| Tiempo de entrenamiento | 67 ms | medido aqui: entrenar la validacion cruzada completa, mejor de 5 rondas | sí |
| Maquina | 12th Gen Intel(R) Core(TM) i5-12500H | Win32_Processor, consultado al sistema | sí |
| Memoria | 31.7 GB | Win32_ComputerSystem | sí |
| Sistema operativo | Microsoft Windows 11 Pro 64 bits build 26200 | Win32_OperatingSystem | sí |
| Aceleracion | ninguna, todo en CPU | no hay GPU en el calculo: es biblioteca estandar | sí |
| Repositorio | https://github.com/Omarcastellanos1970/Migra_IA | publico, con DOI de Zenodo | sí |
| Frases del parrafo | ES 7, EN 7 | el ejercicio exige exactamente siete | sí |


## 5. Lo que no coincide o no existe todavía

- El tiempo de inferencia depende de lo que este haciendo la maquina: se mide en microsegundos y una ventana abierta lo mueve. El numero que entre al paper hay que tomarlo con el equipo en reposo, y el script avisa si la dispersion entre rondas pasa del 25 % del valor.
- La fila de la propuesta entera: el agente no se ha ejecutado bajo esta particion. Ninguna celda suya puede llenarse hoy.
- El coste de la propuesta no es comparable en microsegundos: llevara llamada de red y recuperacion, y habra que reportarlo en segundos por caso, no en la misma unidad.
- kappa entre evaluadores: el paper lo declara como secundaria de P1, pero no hay panel todavia, asi que no aparece en la tabla.

