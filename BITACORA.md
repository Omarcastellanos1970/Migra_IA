# Bitácora de trabajo asistido — MIGRA-IA

Registro de las sesiones en las que el artefacto se construyó con asistencia de
un modelo de lenguaje. Existe para que cualquier número publicado pueda
rastrearse hasta la corrida que lo produjo, y para que el trabajo no dependa de
la memoria de nadie.

**Regla de trabajo** (taller de la maestría):

- Se le pide al agente que **corra el código y muestre la salida real**, nunca
  que describa lo que pasaría.
- Se le pide que **contradiga la formulación propia**; un revisor crítico vale
  más que un asistente complaciente.
- **Cada número se vuelve a correr** antes de entrar a una tabla del paper.
- La **contribución intelectual la definen los autores**, que son quienes conocen la
  planta. El agente no la escribe.
- Ninguna **referencia** se usa sin contrastarla después contra su DOI o arXiv.

Cada entrada anota cuatro cosas: **qué se pidió**, **qué devolvió**, **qué se
verificó** y **qué se corrigió**. Si algo no se pudo verificar, se dice.

Las entradas marcadas *(reconstruida)* se escribieron después, a partir del
mensaje de commit y del estado del repositorio; no se registraron en vivo. Esa
es exactamente la falla que esta bitácora viene a cerrar.

---

## 2026-08-28 · Catálogo de fabricantes *(reconstruida — commit `9c73ee2`)*

**Se pidió.** Que el agente dejara de responder con el caso Siemens de ejemplo
cuando se le preguntaba por otro fabricante.

**Devolvió.** `data/fabricantes_cpu.json` (30 fabricantes, 130 generaciones, 469
modelos, 77 fuentes oficiales con URL), derivado **por parser** del documento de
tesis *Fabricantes de PLC y evolución de modelos de CPU* (25-08-2026), más
`migra_ia/fabricantes.py` con `identificar()` y `anclaje()`.

**Se verificó.** Que el texto del documento se conserva verbatim, incluidas sus
notas de dato no verificado. Que sin coincidencia `identificar()` devuelve
`no_catalogado` en lugar de aproximar a la marca más parecida. Sin fuga de otras
marcas en seis equipos distintos.

**Se corrigió.** Los rangos abreviados de modelos **no se expandieron**:
completar los códigos intermedios habría sido inventar números de parte.

---

## 2026-08-29 · Procedimiento de migración y demo interactiva *(reconstruida — commit `68cee52`)*

**Se pidió.** Cerrar el vacío que quedaba al decidir cambiar de CPU: el agente
diagnosticaba y se detenía, sin procedimiento que ofrecer al técnico.

**Devolvió.** Los 50 pasos del documento en `data/procedimiento_migracion.json`
(título y detalle **literales**, con una capa anotada marcada explícitamente
como propuesta), la extensión P1–P7 para reconstrucción de programa, y
`migra_ia/interactivo.py`: la demo sin clave donde el motor real trabaja con las
respuestas del usuario.

**Se verificó.** Que los prerrequisitos bloquean de verdad (el paso 35 exige
respaldo verificado y plan de retorno antes de tocar la máquina) y que las
variantes por caso desactivan los pasos 21 y 22 en cambio de marca.

**Se corrigió.** En el paso 13 no se afirma equivalencia modelo a modelo entre
marcas: el catálogo no publica atributos comparables, y eso se dice en lugar de
suponerlo.

---

## 2026-09-02 (tarde) · Dos modos en la interfaz *(reconstruida — commit `d60a8b7`)*

**Se pidió.** Sacar la demo guiada de la página: un recorrido que solo lee el
nombre y el equipo y sigue guion para todo lo demás se lee como *Wizard-of-Oz* y
le resta credibilidad a la demo interactiva, que sí es legítimamente
determinista.

**Devolvió.** Interfaz con dos modos —*Demo interactiva (sin clave)* y *Caso
real (API)*— y la Sección 4 de `ARTIFACT.md` reanclada a `_interactivo_run.py`.

**Se verificó.** `compileall` limpio, `node --check` sobre el JS de la página,
los cuatro recorridos con las mismas cifras que antes del cambio: crítico 85.0,
sano 11.8, otra_marca 85.0 con cambio de marca a OMRON Sysmac NX.

**Se corrigió.** Once documentos que seguían pidiendo pulsar un botón retirado,
incluidos los dos `.bat`.

---

## 2026-09-02 (noche) · Baselines, sensibilidad y plantilla ciega *(reconstruida — commit `35cd0fd`)*

**Se pidió.** Responder por adelantado a la pregunta del revisor: *"85.0
comparado con qué?"*. El artefacto tenía datos, características y modelo, pero
ningún baseline y ninguna evidencia de evaluación.

**Devolvió.** `_evaluacion.py` en siete secciones y `_plantilla_ciega.py` para
la validación por juicio experto de los coautores.

| | Qué mira | Resultado (caso crítico) |
|---|---|---|
| B0 trivial | solo M01 | 75.0 → Riesgo alto |
| B1 uniforme | los 8 factores sin ponderar | 83.1 → Riesgo crítico |
| Propuesta | los 8 factores con los pesos de la Sección 6 | 85.0 → Riesgo crítico |

**Se verificó.** Dos corridas seguidas dan salida idéntica. Monte Carlo de 5 000
muestras por escenario: la puntuación se mueve entre 81.3 y 88.6 en el crítico y
entre 9.3 y 13.9 en el sano, y **la clasificación no cambia en ninguna de las
10 000 muestras**. Monotonía sin violaciones en M01, M06 y C10. En la plantilla
ciega, búsqueda de los cinco destinos y las cinco estrategias: **cero
apariciones**.

**Se corrigió — y esto lo destapó el propio análisis, contra la formulación
propia:**

1. **`decidir()` no lee la puntuación.** Forzando el riesgo a 0 con las
   respuestas intactas, la recomendación sigue siendo migrar. Es el diseño, no
   un defecto, pero significa que la estabilidad frente a los pesos es
   *invariancia por construcción* y **no debe presentarse como robustez de la
   decisión**.
2. **F12 se pregunta y ninguna regla la usa.** El mapa de decisión cita F01 y
   F12–F18 como condiciones favorables para reconstrucción; el motor implementa
   F13, N05 y N06. Hueco declarado entre lo documentado y lo implementado.
3. **B0 llega a la misma decisión que la propuesta.** Los 8 factores le ganan a
   la regla trivial en la *clasificación*, no en la *recomendación*. Se declara
   en el informe en lugar de dejar que lo encuentre el revisor.

**Sin resolver.** Esto es **verificación, no validación**: dice que el motor se
comporta como su diseño declara, no que su diseño acierte. La validación de
campo sigue pendiente por falta de casos reales.

---

## 2026-09-02 (19:28) · Tablas de puntuación de los 8 factores

**Se pidió.** Saber de dónde sale el 75.0 del baseline trivial y, en general,
qué convierte cada respuesta en un número.

**Devolvió.** `_reglas_puntuacion.py`, que lee las tablas **del árbol sintáctico
de `migra_ia/interactivo.py`**, y el documento generado
`docs/reglas_de_puntuacion.md`.

**Se verificó.** Que el documento no puede divergir del motor: si alguien cambia
un número en el código, el documento cambia en la siguiente corrida.

**Se corrigió.** Lo que el árbol sintáctico **no** captura —los cruces entre
códigos (repuestos contrasta M06 con C10), los topes (el historial se limita si
hay causa raíz externa) y las condiciones de omisión— no se dedujo: va descrito
a mano en las notas y se verifica ejecutando el motor.

---

## 2026-09-04 · Eliminación completa de la demo guiada

**Se pidió.** Quitar del todo el guion narrado, que ya no era alcanzable desde
la interfaz pero seguía en el repositorio.

**Devolvió.** Borrados `migra_ia/demo.py` y `_demo_run.py`; limpiadas la rama
`es_demo` de `webapp/app.py` y el camino `modo === "demo"` del JS.

**Se verificó.** `compileall` limpio · `node --check` OK en el JS de la app y de
la landing · los tres escenarios siguen dando **85.0 / 11.8 / 85.0** con 24
respuestas y 0 datos faltantes · `_evaluacion.py` pasa su anclaje y
`docs/evaluacion_interna.md` **no cambió ni un carácter** tras la corrida ·
`POST /api/nuevo {"demo":true}` ya no arranca ningún guion · cero referencias
colgantes en todo el árbol.

**Se corrigió.** Dos cosas que el borrado dejaba mintiendo:

1. `docs/informe_ejemplo.md` y `docs/expediente_ejemplo.json` los producía el
   guion borrado (75.2, agente v0.1.0). **Regenerados** desde el escenario
   `critico` de `_interactivo_run.py` (85.0, v0.3.0), y por tanto reproducibles
   otra vez. La ruta del informe en el expediente pasa a ser **relativa**: la
   anterior publicaba el árbol de directorios de la máquina del autor.
2. La landing le decía al revisor *"pulsa Demo interactiva"* y a renglón seguido
   *"salida esperada: 75.2"*, que era el número del guion. **Reanclada a 85.0**
   en las tres copias: el widget del motor arranca con los ocho valores reales
   del escenario crítico (75/85/90/95/100/75/55/90) y la lectura de diagnóstico
   describe el caso que sí se puede reproducir.

---

## 2026-09-04 (2.ª parte) · Baseline reproducible

**Se pidió.** El entregable del taller: baseline reproducible con seis casillas
marcadas. El rubro asigna el modelo — *regresión logística ordinal y
gradient boosting en modo ranking*, como resultado principal de dos de los tres
subproblemas.

**Devolvió.** `_baseline.py` y su informe `docs/baseline_reproducible.md`, más el
conjunto de datos dentro del repositorio (`data/ciclo_vida_plataformas.csv`), la
partición guardada (`data/particion_ciclo_vida.json`) y el entorno congelado
(`requirements-freeze.txt`).

| | exactitud | F1 macro | error ordinal |
|---|---|---|---|
| B0 trivial (clase mayoritaria) | 0.667 | 0.400 | 0.333 |
| B1 clásico (logística ordinal) | 0.778 | 0.679 | 0.222 |

**Se verificó.** Dos corridas seguidas dan salida **byte a byte idéntica**. La
fecha de referencia se fijó en `2026-09-04` en vez de usar «hoy», porque las
etiquetas se derivan de comparar fechas y con «hoy» el entregable dejaría de ser
reproducible en cuanto pase el calendario. La identidad de las dos columnas
excluidas por fuga se comprobó con aritmética sobre los propios datos, no por
criterio: **9 de 9 filas** y **6 de 6 filas**.

**Se corrigió — cuatro cosas que el propio ejercicio destapó:**

1. **La tabla solo tiene 9 filas y 2 clases de 4.** No hay ni una muestra de
   «activo» ni de «phase-out», porque la tabla se construyó para documentar
   descontinuaciones. El modelo ordinal degenera en binario y no puede aprender
   a reconocer una plataforma vigente. Declarado como sesgo de selección.
2. **Solo una variable sobrevive a la auditoría de fuga.** `Vida_comercial_anios`
   y `Soporte_total_anios` son la etiqueta escrita de otra forma; `Nivel` es
   metadato de verificación, no propiedad del equipo; `Fabricante` es la variable
   de agrupamiento. Queda `antiguedad`. Por eso el clásico es univariante: no
   por elección, por obligación.
3. **P2 no es evaluable todavía.** El gradient boosting en modo ranking necesita
   un orden de referencia que no existe en ninguna fuente del proyecto, y
   derivarlo de la puntuación del motor sería circular. Se declara qué haría
   falta en vez de fabricar el dato.
4. **Se rehízo el clásico.** La primera versión usaba un tocón de decisión;
   al confirmarse que el rubro asigna el modelo se sustituyó por la logística
   ordinal que pide el rubro.

**Sin resolver.** El conjunto es de nueve filas: cada acierto vale 0.111 de
exactitud, así que la ventaja del clásico sobre el trivial es un indicio, no
evidencia. Ampliar la tabla de ciclo de vida a las 130 generaciones del catálogo
es lo que le daría sentido estadístico, y es trabajo de fuentes oficiales.

---

## 2026-09-04 (3.ª parte) · Etiquetas de P1 y P2, y el formulario para el panel

**Se pidió.** El usuario no tiene comunicación con sus coautores y pide que se
resuelva lo que ellos harían: producir las etiquetas de referencia de P1 (clase
de obsolescencia) y P2 (prioridad de reemplazo).

**Devolvió.** `_etiquetado.py` con tres acciones y una separación que no se
mezcla: `provisional` escribe `data/etiquetas_p1_p2.json` con un etiquetado
**derivado de una regla escrita**, `formulario` escribe
`docs/formulario_etiquetado.md` para que lo respondan los coautores, y
`comparar` lee los formularios devueltos y mide el acuerdo entre evaluadores.

**Se verificó.** Que el formulario **no contiene ninguna salida del motor** ni
el etiquetado provisional: la única aparición de la palabra «provisional» es la
frase que advierte que no lo lleva. El criterio de P2 se escribió **antes** de
mirar los datos, para que no pudiera acomodarse al resultado.

**Se corrigió.** La primera versión trataba el fin de repuestos no publicado
como el peor caso y lo imprimía como «sin repuestos ya». Eso es afirmar algo
que ninguna fuente dice, y contradice el principio del propio proyecto de
marcar el dato faltante en vez de suponerlo. Ahora hay **tres bandas**: sin
repuestos confirmado, fin de repuestos **no publicado**, y con repuestos. El
orden resultante no cambió; lo que cambió es lo que se afirma de tres de las
nueve plataformas.

**Sin resolver, y es lo importante.** Un etiquetado por regla **no es juicio
experto**. El taller lo pone en la columna «así no»: la contribución la define
el equipo, que es quien conoce la planta. Mientras `procedencia` diga
`provisional_regla`, ninguna cifra que salga de aquí puede presentarse como
validación. Además, con etiqueta derivada de las fechas, P1 sigue siendo la
re-derivación de una definición y no una predicción — por eso la auditoría de
fuga deja fuera todas las columnas de fecha. La etiqueta del panel es lo que
convierte P1 en un problema de aprendizaje real.

---

## 2026-09-04 (4.ª parte) · De un número solitario a media y desviación

**Se pidió.** Aplicar la pauta de validación: la validación cruzada entrega
**media y desviación** de los k pliegues, no un número solitario que depende de
cómo cayó la partición.

**Devolvió.** `_baseline.py` ya hacía 5 pliegues, pero agrupaba las nueve
predicciones en una bolsa y reportaba una sola cifra. Ahora calcula las métricas
**por pliegue** y reporta media ± desviación muestral (n−1), con la tabla de los
cinco pliegues debajo y la cifra agrupada relegada a contraste.

| | exactitud | F1 macro | error ordinal |
|---|---|---|---|
| B0 trivial | 0.700 ± 0.447 | 0.667 ± 0.471 | 0.300 ± 0.447 |
| B1 clásico | 0.800 ± 0.447 | 0.800 ± 0.447 | 0.200 ± 0.447 |

**Se verificó.** Dos corridas byte a byte idénticas (248 líneas). Cero
caracteres no ASCII en el script, que es la convención del repo para lo que se
genera por código.

**Se corrigió — y esto es lo que el número solitario tapaba.** La tabla por
pliegue enseña que el pliegue **Mitsubishi da 0.000 en los dos modelos**: falla
las dos plataformas. Otros tres pliegues dan 1.000. Esa dispersión no se veía en
el 0.778 agrupado. Además, **la desviación (0.447) es mayor que la diferencia
entre los dos modelos (0.100)**, de modo que la ventaja del clásico deja de
poder presentarse como tal: el intervalo de uno cubre la media del otro. Es un
resultado más honesto y más débil que el anterior, y el informe lo dice así.

**Sin resolver.** El conjunto de prueba apartado —los cinco casos de la guía y
las etiquetas del panel— sigue **sin abrir**, y el informe ahora lo declara
explícitamente para que nadie confunda estos cinco pliegues de desarrollo con
una medida sobre datos apartados.

---

## 2026-09-04 (5.ª parte) · Esquema de partición asignado por el rubro

**Se pidió.** Aplicar el esquema que el rubro asigna: **estratificada por
nivel de obsolescencia, agrupando por caso de migración**, con el
preprocesamiento ajustado dentro de cada pliegue.

**Devolvió.** `particionar_estratificado()` en `_baseline.py`, que busca la *k*
más alta en la que todo pliegue de prueba contiene las dos clases sin partir
ninguna marca. Resultado: **k = 2**.

| Pliegue | Prueba | n | exact. B0 | exact. B1 |
|---|---|---|---|---|
| 0 | Mitsubishi + Schneider + Siemens | 5 | 0.600 | 0.600 |
| 1 | Omron + Rockwell | 4 | 0.750 | 1.000 |

| | exactitud | F1 macro | error ordinal |
|---|---|---|---|
| B0 trivial | 0.675 ± 0.106 | 0.402 ± 0.038 | 0.325 ± 0.106 |
| B1 clásico | 0.800 ± 0.283 | 0.688 ± 0.442 | 0.200 ± 0.283 |

**Se verificó.** Dos corridas byte a byte idénticas (257 líneas). Y una de las
tres exigencias ya se cumplía sin saberlo: **el preprocesamiento se ajusta
dentro del pliegue** — la media y la escala con que se estandariza la antigüedad
salen solo del entrenamiento de cada pliegue, en `b1_logistica_ordinal()`. No
había ningún ajuste hecho una sola vez sobre las nueve filas.

**Se corrigió — dos cosas.**

1. **El reparto de marcas estaba mal.** La primera versión mandaba cada marca al
   pliegue con menos muestras de la clase minoritaria. Eso dejaba a Mitsubishi
   —que aporta 2 de las 3 muestras de clase 4— solo en su pliegue y **sin
   ninguna clase 3**, así que ninguna *k* pasaba la comprobación y todo caía al
   esquema de contraste sin estratificar. Ahora el reparto balancea **todas** las
   clases: cada marca va al pliegue donde menos desvía del ideal.
2. **`k = 2` es un techo duro, no una elección.** Solo dos fabricantes aportan
   clase 4 (Mitsubishi con 2, Rockwell con 1), así que no hay con qué llenar un
   tercer pliegue estratificado sin partir una marca — y partirlo devolvería la
   fuga por la puerta de atrás.

**Lo que la estratificación arregló.** En leave-one-manufacturer-out el pliegue
de Mitsubishi era puro clase 4 y **los dos modelos sacaban 0.000** en él. Con la
partición estratificada la desviación del trivial baja de **±0.447 a ±0.106**: la
cifra deja de depender de que una marca caiga entera de un lado. El esquema
anterior se conserva declarado como contraste, precisamente para enseñar esa
distorsión.

---

## 2026-09-04 (6.ª parte) · Métricas de ordenamiento de P2

**Se pidió.** Aplicar las métricas que el rubro fija en el
subproblema de ordenamiento: **precisión en los primeros k** y **posición media
del elemento correcto**.

**Devolvió.** `metricas_ranking()` en `_etiquetado.py` y la acción
`python _etiquetado.py p2`, que evalúa el orden trivial —la más antigua
primero— contra el orden de referencia disponible:

```
precision@1 = 1.0     posicion media de los 1 primeros = 1.0  (ideal 1.0)
precision@3 = 0.667   posicion media de los 3 primeros = 2.33 (ideal 2.0)
precision@5 = 1.0     posicion media de los 5 primeros = 3.0  (ideal 3.0)
desplazamiento medio de puesto = 1.11
```

En el paper, el plan de evaluación de los cuatro `.tex` ya tenía la precisión en
los primeros k («acierto en las posiciones 1 y 3») y ahora incorpora la segunda.

**Se verificó.** El comando imprime un **aviso en cabecera** cuando la
procedencia del orden de referencia no es `panel_experto`, que es el caso hoy:
lo que mide es coherencia interna, no acierto.

**Se corrigió.** Nada que estuviera mal; sí una **adaptación que hay que
declarar**. Las dos métricas están pensadas para una recuperación con un
elemento relevante entre muchos, y P2 es una permutación completa de las mismas
nueve plataformas. Así que precision@k se mide como el solapamiento entre las k
primeras de cada orden, y la posición media se mide sobre los elementos que la
**referencia** pone en cabeza. Va escrito en el docstring en vez de disimularse.

**Sin resolver.** El clásico de P2 —gradient boosting en modo ranking— sigue sin
evaluarse, porque sigue sin haber orden de referencia de juicio experto. En
cuanto lleguen los formularios, este mismo comando lo mide sin tocar código.

---

## 2026-09-04 (7.ª parte) · El protocolo de validación, firmado

**Se pidió.** Escribir el protocolo de validación —media página, seis puntos—
que se firma **antes** de correr los experimentos finales y que después se pega
casi literal en la metodología del paper.

**Devolvió.** `PROTOCOLO_VALIDACION.md`, firmado el 2026-09-04:

1. **Partición** — unidad = la plataforma; agrupamiento = fabricante; semilla 42
   declarada y **sin uso**; índices en `data/particion_ciclo_vida.json`; fecha de
   referencia fija.
2. **Esquema** — cruzada estratificada agrupada, **k = 2** (techo duro),
   **1 repetición** porque no hay aleatoriedad; preprocesamiento dentro del
   pliegue.
3. **Métricas congeladas** — P1: principal **F1 macro**, secundarias exactitud y
   error ordinal. P2: principal **precisión en los 3 primeros**, secundarias
   posición media y desplazamiento de puesto.
4. **Búsqueda permitida** — **ninguna**. Hiperparámetros fijos y declarados;
   esfuerzo de búsqueda cero para los dos modelos, que es lo que hace justa la
   comparación.
5. **Reporte** — media ± desviación muestral sobre pliegues, nunca el mejor
   número; la cifra agrupada solo como contraste etiquetado; toda cifra con la
   procedencia de su etiqueta.
6. **Conjunto de prueba** — los cinco casos ciegos más las etiquetas del panel;
   se abre **una sola vez**, con el protocolo cerrado, y lo que salga se publica.

**Se verificó.** Los seis archivos que cita el protocolo existen; la partición
guardada declara `k = 2`, semilla 42 y fecha `2026-09-04`; los hiperparámetros
del documento coinciden con las constantes del código (`ITERACIONES = 4000`,
`PASO = 0.05`, `L2 = 1.0`); y `etiquetas_p1_p2.json` sigue en
`provisional_regla`.

**Se corrigió.** El protocolo declaraba una métrica principal que el informe no
distinguía de las demás. Ahora `_baseline.py` la imprime como tal, citando el
punto 3 del protocolo, para que sea exigible y no solo declarativa.

**Sin resolver, y firmado sabiéndolo.** El protocolo lleva una sección de deuda
declarada con las tres cosas abiertas: la etiqueta de P1 sale de las mismas
fechas que serían las variables; P2 no tiene orden de referencia experto; y con
nueve filas ninguna diferencia entre modelos es estadísticamente sostenible. Se
firma igual, que es el punto: **desde hoy el protocolo manda sobre el
entusiasmo**, y lo que venga después ya no puede acomodarse a lo que salga.

---

## 2026-09-04 (8.ª parte) · Características de dominio y riesgo de datos

**Se pidió.** Revisar el material del taller y hacer las correcciones
necesarias. De ahí salió una de sus listas de comprobación, «Protocolo de
validación y datos confirmados», de la que faltaban dos puntos.

> **Corregido el 2026-09-04.** Esta entrada decía antes que el usuario había
> pedido «el entregable de martes». No lo pidió: la etiqueta *ENTREGABLE ·
> MARTES* está impresa en la diapositiva del taller y yo la convertí en un
> encargo con fecha. El único plazo que el usuario ha fijado es que **el
> complemento del paper se entrega en septiembre**. El trabajo hecho no cambia;
> cambia de quién salió.

**Devolvió.** Las dos que faltaban:

- **Casilla 3, características de dominio** — `_caracteristicas.py` y
  `docs/caracteristicas_dominio.md`, generado leyendo el cuestionario y las
  tablas de puntuación (que a su vez salen del árbol sintáctico del motor), de
  modo que no pueda divergir. Decisión documentada: **no se va con el dato
  crudo**; el proyecto define características de dominio y las pondera.
- **Casilla 5, riesgo de datos** — `docs/riesgo_de_datos.md`, siete puntos
  ordenados por lo que bloquean, con «qué falta / quién / para cuándo». Los
  hechos están verificados; los responsables y las fechas van marcados
  `POR DECIDIR` porque no salen de ningún archivo.

**Se verificó.** Los pesos de los ocho factores suman 1.00 y se extraen del
documento generado, no se copian a mano.

**Se corrigió — el contraste destapó dos huérfanas más de las que yo tenía.**
Además de `C05`, `D07`, `M02` y `M03`, tampoco los usa ningún factor `M05`
(repuestos de mercado secundario) ni `Q01` (coste de una hora de parada).
**Son seis datos que se le piden al técnico, se guardan en el expediente y se
tiran.** Cerrarlo obliga a tocar `scoring.py`, cuyos pesos describe la Sección 6
del paper: decisión editorial, no técnica.

**Sin resolver.** La casilla 6 pide «la tanda de clásicos lanzada con el
prompt 5». No sé qué es el prompt 5 —es material del taller que no he visto— así
que esa casilla queda sin marcar a propósito en vez de darla por buena.

---

## 2026-09-04 (9.ª parte) · Pasada de coherencia contra todas las pautas

**Se pidió.** Revisar todo el material del taller de una vez y corregir lo que
hiciera falta, antes de retomar el paper.

**Devolvió — dos incoherencias reales entre documentos:**

1. **`_evaluacion.py` y `ARTIFACT.md` presentaban tres escenarios como tres
   casos.** La auditoría de fuga estableció que `otra_marca` es `critico` con
   otro destino: **las mismas 24 respuestas**. El propio `_evaluacion.py` ya lo
   sabía en su sección 2, donde lo salta, pero su sección 1 lo listaba en pie de
   igualdad. Ahora ambos avisan: **3 filas, 2 casos independientes**, y que las
   cifras coinciden por construcción y no cuentan como evidencia adicional.
2. **El paper no nombraba la métrica que decide.** Corregido en los cuatro
   `.tex`: para P1 la principal es el F1 macro, no la exactitud.

**Se verificó.** Antes de renombrar los duplicados del paper se comprobó **por
hash contra el contenido del ZIP** cuál es la copia canónica: las de
`Resumen_Metodologia\`. Las de la raíz se renombraron a `*.VIEJO-no-usar`, que
es reversible, en vez de borrarlas.

**Sin resolver, y son los tres pendientes para mañana:**

- **El paper no se ha compilado.** La ES pasó de 3.527 a **3.672 palabras** en
  la sesión (+145) y la referencia son ~3.330 para 6 páginas. Es lo primero que
  hay que medir.
- **El sexto punto de esa lista de comprobación** sigue sin cubrir: falta saber
  qué es el prompt 5.
- **Seis códigos del cuestionario se recogen y no se usan** (`C05`, `D07`,
  `M02`, `M03`, `M05`, `Q01`), y **F12** igual. Cerrarlo toca `scoring.py` y
  obliga a actualizar la Sección 6 del paper: decisión editorial pendiente.

---

## 2026-09-04 (10.ª parte) · El protocolo, ahora sí en media página

**Se pidió.** Releer la pauta del protocolo de validación. Dice, literal:
*«media página que se escribe antes de correr los experimentos finales y que
después se pega casi literal en la metodología del paper»*.

**Se corrigió.** El protocolo que escribí incumplía lo primero que la pauta
exige: tenía **1.091 palabras**, útiles como documento de trabajo pero
impegables en un paper de seis páginas. Ahora el archivo abre con **el contrato,
422 palabras** —media página a dos columnas, en prosa corrida, con los seis
puntos y listo para pegar— y todo el detalle pasa a **anexo de trabajo**, que no
se publica. No se perdió nada: se separó lo que va al paper de lo que justifica
cada decisión.

**Se precisó.** El usuario aclaró qué es la «Semana 4» de la pauta: **la
revisión final previa a la publicación en Zenodo**. El punto 6 ya no dice «una
sola vez» a secas, sino que fija ese hito — no una fecha de calendario, sino el
momento del proyecto en que se libera la versión con DOI. Queda escrito en el
contrato y en el anexo.

**Se verificó.** El contrato cubre los seis puntos de la pauta y ninguna cifra
suya contradice al anexo: misma unidad de observación, mismo agrupamiento, misma
semilla, misma *k*, mismas métricas principales y misma regla de apertura.

---

## 2026-09-05 · La figura principal, diseñada antes de tener los números

**Se pidió.** La pauta de *anatomía* del taller: cada proyecto tiene **una**
figura principal, «se diseña esta noche, con los ejes rotulados, y se llena
cuando lleguen los números». La fila que nos toca dice: curva de la proporción de
programas que pasan el verificador frente al número de iteraciones de
corrección; demuestra que el verificador en el lazo sube el acierto y en qué
iteración deja de subir; línea de referencia, la generación sin verificador en
la iteración cero.

**Se devolvió.** La figura, generada por código y sin un solo número tecleado a
mano:

- `data/figura_p3_verificador.csv` — seis filas (iteraciones 0 a 5) con las
  celdas **vacías a propósito**. Una celda vacía significa «todavía no medido»;
  un cero significaría «medido y ninguno pasó».
- `_figura_p3.py` — única fuente de la figura. Con el CSV vacío emite **modo
  diseño**: ejes rotulados, rejilla, las dos referencias externas y un aviso de
  que la curva está pendiente. **No dibuja ninguna curva inventada.** En cuanto
  el CSV tenga filas, traza la parte medida, dibuja la línea de referencia
  propia en el valor de la iteración cero, marca la iteración en la que la
  mejora cae por debajo de 2 puntos porcentuales y lo dice también en el pie.
- `Figura_P3_verificador_ES.tex` y `Figure_P3_verifier_EN.tex` — bloque
  `figure` con pgfplots, escritos a la vez en `docs/figuras\` y en la carpeta
  `Figures\` del paper.
- `docs/figuras/figura_p3_verificador.svg` y `.html` — vista previa para el
  navegador, porque en esta máquina no hay LaTeX y el diseño había que verlo
  esta noche.

Las dos líneas punteadas de 47 % y 72 % son de Fakih *et al.*, la misma línea
base que el plan de evaluación ya citaba; la figura las rotula como ajenas para
que nadie las lea como resultado propio. Al ser una cita que el paper ya usa,
el invariante de 26 referencias citadas no se mueve.

**Se verificó.** `py_compile` limpio. Se ejecutaron los tres caminos con CSV de
prueba en carpeta temporal, sin tocar los datos buenos: con datos completos
detecta la meseta —en el juego de prueba, la iteración 4—; con datos parciales
traza lo medido y mantiene el aviso; con datos imposibles se niega a generar y
explica por qué (`pasan=40 fuera del rango 0..30` y el banco de casos cambiando
de tamaño entre iteraciones). El SVG parsea como XML bien formado. El estado
final de los archivos buenos vuelve a ser `MODO DISENO`.

**Se corrigió.** El script tenía un defecto propio: al probarlo con un CSV
ajeno **sobreescribía igualmente la vista previa oficial** de `docs/figuras`.
Ahora esa carpeta solo se toca cuando los datos son los canónicos; con
`--csv` de prueba la salida va únicamente a donde diga `--salida`.

**Se anotó una discrepancia, sin resolverla.** El rubro asigna los modelos
clásicos de **P1 y P2** (logística ordinal y *gradient boosting* en modo
ranking), mientras que esta figura vive en **P3**. No es contradicción —el
paper formula los tres subproblemas y P3 es justo el que tiene verificación en
el bucle—, pero conviene confirmar con el taller que la figura principal del
artículo sea la de P3 y no una de riesgo ordinal.

**Queda abierto.** (1) El CSV está vacío: la figura se llena cuando se ejecute
el banco de casos. (2) La figura **no está insertada en el paper**: cuesta dos
líneas de preámbulo (`\usepackage{pgfplots}` y `\pgfplotsset{compat=1.18}`),
un `\input` y una frase que la referencie, y el paper va a seis páginas justas
con +145 palabras sin medir desde ayer. Es decisión del usuario y depende de
compilar la ES en Overleaf.

---

## 2026-09-05 (2.ª parte) · Los dos ejercicios del taller: Tabla II y las siete frases

**Se pidió.** Ejercicio 1, la Tabla II con las celdas vacías: título en una
línea, filas trivial + clásicos justificados + propuesta y ni una más, columnas
con la métrica principal ±, una secundaria que explique y un costo, y solo la
fila del trivial con números. Ejercicio 2, la configuración experimental en
siete frases, cada una con lo que no puede faltar, guardada como `PROTOCOLO.md`
y lista para pegar en Overleaf. El usuario añadió que el punto 7 debe declarar
la máquina real: equipo, sistema operativo y características.

**Se devolvió.** `_tabla_ii.py`, que importa `_baseline.py` y no teclea ningún
número:

- **Título en una línea:** «Riesgo ordinal de obsolescencia en 9 plataformas de
  automatización: F1 macro medio ± desviación sobre 2 pliegues agrupados por
  fabricante». Lleva las cuatro cosas: datos, métrica, sobre qué se promedia y
  agrupamiento.
- **Tres filas.** El *gradient boosting* de P2 se dejó fuera a propósito: es
  otro subproblema con otra métrica, y la tabla tiene un solo título.
- **Columnas:** F1 macro media ± desviación, exactitud como secundaria —explica
  por qué decide el F1: el trivial acierta 0,675 y su F1 se hunde a 0,402— y el
  tiempo de inferencia por caso como costo.
- **Celdas:** solo el trivial lleva número. El clásico se deja vacío como pide
  el ejercicio aunque esté medido desde ayer; se llena con `--con-clasico`.
- **`PROTOCOLO.md`** con el párrafo de siete frases en español e inglés, en
  versión legible y en versión con marcas de LaTeX para pegar en Overleaf.
- **`docs/tabla_ii_y_configuracion.md`** con la tabla, el párrafo y la
  verificación dato a dato.

**Se verificó.** 28 datos del párrafo contrastados contra el código y contra la
tabla: misma partición, misma métrica, mismo *k*. Las siete frases se cuentan
por programa en los dos idiomas. La máquina no se escribió a mano: se consulta
a Windows —i5-12500H de 12 núcleos, 31,7 GB, Windows 11 Pro build 26200— y
entrenar la validación cruzada completa cuesta 66 ms.

**Se corrigió.** El coste salía 0,02 en una ejecución y 0,03 en la siguiente:
el valor real está en 0,025 y el redondeo a dos decimales caía justo en la
frontera. Ahora se dan dos cifras significativas, que es hasta donde llega la
resolución. Y la verificación **está marcando una discrepancia de verdad**: el
tiempo del clásico oscila un 36 % entre rondas con la máquina ocupada, así que
ese número no es publicable tal cual. No afecta a lo que se entrega —esa celda
va vacía—, pero el día que se llene hay que medir con el equipo en reposo.

**Se anotó.** `PROTOCOLO.md` y `PROTOCOLO_VALIDACION.md` conviven: aquel es el
contrato de validación de los seis puntos; este es la configuración
experimental que va al artículo. Si alguna cifra difiere, manda la de
`PROTOCOLO.md`, que se regenera desde el código.

**Queda abierto.** El paper sigue **sin tocar**, por instrucción del usuario
hasta terminar de revisar las pautas del máster.

---

## 2026-09-05 (3.ª parte) · El presupuesto de seis páginas y la ronda de datos

**Se pidió.** Dos cosas más del taller. El presupuesto de páginas —cómo debe
repartirse el paper de seis páginas— y una sugerencia para la ronda de cinco
preguntas de sí o no, que decide **con qué dato entra cada equipo a deep
learning** la próxima semana.

**Se midió.** El paper contra el presupuesto, repartiendo su propio texto
—ya validado en seis páginas— según las proporciones exigidas, para que la
escala sea la suya. Está volcado hacia adelante: sobran 319 palabras en la
introducción, 302 en trabajo relacionado y 312 en método, y faltan 257 de
configuración experimental —la sección no existe—, 437 en resultados y
discusión y 239 en conclusiones. **No hay que escribir más: hay que mover.**
Además sobran referencias por poco: **26 únicas contra un techo de 25**.

**Se comprobó, contra lo que decía el registro.** El catálogo tiene 30
fabricantes, **130 generaciones**, 469 modelos y **cero fechas**; lo declara él
mismo: *«se incorporarán en una siguiente capa únicamente cuando exista
evidencia fechada y verificable»*. La tabla de ciclo de vida son 9 filas, 6 de
clase 3 y 3 de clase 4, sobre cinco fabricantes.

**Se sugirió, para la ronda de datos.** Cuatro «sí» demostrables mostrando
pantalla —los datos cargan, el n por clase sale impreso, la partición está
congelada en disco y la métrica está escrita— y el quinto, el plan B, es el
único que faltaba fechar. Y una advertencia: **entrar con la tabla de nueve
sería ganar el punto de control y perder la semana**; nueve filas, dos clases y
una sola variable admisible no sostienen deep learning ni sostienen el clásico.
La propuesta es entrar con **la capa de fechas que le falta al catálogo**, y que
el deep learning entre **por el texto** —extraer el hecho fechado de los
documentos del fabricante—, que es donde hay volumen y es lo que convierte
nueve filas en ciento treinta. Eso además rompe la circularidad actual, en la
que la etiqueta se deriva de las mismas fechas que serían las variables.
**El deep learning va en el extractor, no en el clasificador de riesgo:** ni 35
ni 130 filas justifican una red para predecir el nivel de obsolescencia.

**Plan B propuesto, con fecha.** Los cinco fabricantes que ya están en la tabla
—Siemens, Rockwell, Schneider, Mitsubishi y Omron— suman **35 generaciones**:
pasar de 9 filas a 35 con evidencia fechada, **para el viernes 11 de
septiembre**, con nombre de quien lo hace.

**Se corrigió el registro.** La figura que el usuario mandó eliminar el 06-08
**no era de este paper**: se había quedado por error de un ejemplo anterior. No
hay contradicción con el presupuesto, que pide una Figura 1 de arquitectura en
«Método propuesto»; hay que **crearla nueva**, en la Semana 3.

**Estado al cerrar.** El paper **no se tocó**: los cuatro `.tex` y los tres ZIP
siguen como quedaron el 04-09. Nada de hoy está commiteado. La próxima sesión
es para **completar el paper según estos lineamientos**.

## 2026-09-05 (2.ª parte) · Fuera las siglas, en el paper y en el repo

**Se pidió.** Eliminar las siglas que nos identifican dentro de la maestría:
señalan a los autores y no tienen por qué viajar en el paper. La orden llegó
al final de la sesión anterior y **la ventana se cerró antes de aplicarla**.

**Se hizo, primero en el paper.** En los `.tex` la sigla salía en dos sitios y en
los dos idiomas —la fila de la Tabla II y la etiqueta del eje x de la Fig. 1—;
en el cuerpo de los paper no aparecía ni una vez. Se corrigieron los cuatro
`.tex` de la carpeta del paper, sus cuatro gemelos de `docs/figuras` y los
rótulos de `_tabla_ii.py` y `_figura_comparacion.py`, que es por donde volvería
a colarse en la siguiente regeneración.

**Y después en el repo entero, a petición del usuario.** 16 archivos: los cinco
scripts (`_baseline.py`, `_caracteristicas.py`, `_figura_comparacion.py`,
`_figura_p3.py`, `_tabla_ii.py` — docstrings, comentarios, banners del informe,
títulos de las vistas previas HTML y textos de `--help` y de consola),
`ARTIFACT.md`, `PROTOCOLO_VALIDACION.md`, esta misma bitácora y seis documentos
de `docs/` (incluidas las salidas generadas `baseline_reproducible.md`,
`caracteristicas_dominio.md`, `tabla_ii_y_configuracion.md` y los `.html`/`.svg`
de las figuras). Donde la frase quedaba coja, la sigla se sustituyó por **«el
rubro»**, que es lo que en realidad asignaba el modelo.
Las salidas generadas se editaron a mano **igual que las emiten ahora los
generadores**, así que una regeneración no debería producir diferencia.

**Lo que NO se tocó, a propósito.** `data/fabricantes_cpu.json` contiene números
de parte de Siemens (`314-6CG23`) donde las mismas dos letras aparecen por
casualidad: un reemplazo a ciegas habría corrompido el catálogo. Se verificó que
siguen las dos apariciones intactas.

**Verificado.** Sintaxis correcta en los cinco scripts (`py_compile`) y **cero
apariciones de la sigla en todo el árbol de trabajo**, descontando `.venv`
—terceros— y los números de parte. `__pycache__` se regeneró ya limpio.

⚠️ **Queda en el historial de git.** Los objetos de commits anteriores
(`.git/objects`) conservan la sigla en doce blobs: si el repo se hace público,
quien navegue el historial la ve. Limpiarlo exige reescribir el historial
(`git filter-repo`) y forzar el push; **no se hizo**, es decisión del usuario.

**Estado al cerrar (superado por la 3.ª parte).** La limpieza quedó **commiteada en local** (ocho
archivos ya seguidos por git), pero **no empujada**: el usuario decidió que hoy
no se sube nada y que la rama limpia se empuja en el lanzamiento, la semana del
7 al 13 de septiembre. Descartadas las otras dos salidas que se le plantearon:
ni se borra la rama remota mientras tanto, ni se reescribe el historial.

**Y entra también el trabajo del 05-09, por orden del usuario.** Segundo commit
local con los **18 archivos que nunca habían estado en git**: `PROTOCOLO.md`,
los tres generadores (`_tabla_ii.py`, `_figura_comparacion.py`, `_figura_p3.py`),
los dos CSV de `data/`, `docs/tabla_ii_y_configuracion.md` y las once salidas de
`docs/figuras/` (seis `.tex`, dos `.html`, dos `.svg` y la guía de inserción).
Revisados antes de añadirlos: **sin claves ni `.env`** y **sin la sigla**. Lo
único que hubo que corregir fue `docs/figuras/insercion_en_el_paper.md`, que
traía **la ruta absoluta del escritorio del autor** en dos comandos de ejemplo;
se sustituyó por una marca genérica, que es la misma regla que ya se aplicó el
04-09 al expediente de ejemplo. El repo es público: ahí no viaja el árbol de
directorios de nadie.

⚠️ **Ojo con lo que ya está publicado.** El repo es **público** desde el
21-07 y la rama `catalogo-fabricantes-adaptativo` se empujó el 04-09, así que
la sigla se lee hoy en github.com en los ocho archivos de esa rama. `main`
sigue en `55a8f78` y no contiene ninguno de ellos: por ahí está limpio.

## 2026-09-05 (3.ª parte) · El repositorio deja de estar congelado en julio

**Se pidió.** Dos cosas: que `main` reflejara el trabajo de agosto y septiembre
—llevaba parado desde el 29 de julio y la web pública mostraba ese estado— y que
ni la sigla ni la palabra que nombraba al equipo aparecieran en ningún sitio,
tampoco en el historial.

**Se separó lo que era una misma palabra con dos sentidos.** El texto usaba el
mismo término para el equipo de la maestría y para la unidad de agrupamiento de
la validación cruzada. Lo primero se fue; lo segundo pasa a llamarse **marca** o
**fabricante**, que es exactamente lo que el protocolo declara que es. En código:
la variable local pasa a `agrupaciones` y las claves del reparto y del informe a
`prueba_marcas` y `marca`. `data/particion_ciclo_vida.json` se **regeneró** con
`_baseline.py` para que el archivo siga siendo lo que produce el script.

**Se verificó que no cambia ni un número.** Mismos pliegues y mismas plataformas
a cada lado, misma `k = 2`, mismo esquema; **B0 0,675 ±0,106 y B1 0,800 ±0,283**,
con **F1 macro 0,402 y 0,688**. Es decir: la Tabla II del paper sigue valiendo tal
cual está.

**Se reescribió el historial.** `git filter-branch` sobre los **17 commits** que
`main` no tenía, filtrando a la vez el contenido de los archivos y los mensajes
de commit. Comprobado después, uno por uno: **cero apariciones** en cualquier
archivo de cualquiera de los 17 commits y en cualquier mensaje, y el **árbol
final es idéntico** al de antes de reescribir —`git diff` vacío—, así que la
reescritura no perdió nada. Los números de parte de Siemens (`314-6CG23`), que
llevan las mismas dos letras por casualidad, siguen intactos: las reglas iban con
límite de palabra.

**Se publicó.** `main` avanzó de `55a8f78` a `53ff396` sin fusión ni conflictos, y
la rama de trabajo se reempujó con `--force-with-lease`. Verificado contra el
remoto ya publicado: limpio en archivos y en mensajes.

⚠️ **Dos avisos.** (1) Al reescribir, los 17 commits **cambiaron de hash**: quien
tenga una copia antigua no debe hacer `pull`, sino volver a clonar. (2) GitHub
conserva un tiempo los objetos viejos aunque ya no los apunte ninguna rama; se
borran solos con su recolección de basura, y si hiciera falta antes hay que
pedírselo a su soporte.

**Estado al cerrar.** `main` = `origin/main` = `53ff396`. La página pública se
regenera desde `docs/` de `main`, así que pasa a mostrar el motor anclado en
**85,0 «Riesgo crítico»** en lugar del 75,2 antiguo. Las etiquetas `v0.2.0` y
`v0.3.0` y sus DOI de Zenodo **no se tocaron**: son anteriores a `55a8f78` y
quedaron fuera del rango reescrito, de modo que la cita del paper sigue válida.

## 2026-09-05 (4.ª parte) · La valoración ciega estaba deshecha antes de empezar

**Se encontró al revisar lo que quedaba publicado.** `_plantilla_clave.json`
—el mapa de cada caso ciego a su id en la guía— estaba en el repositorio, que es
público, pese a que su propia nota dice *«NO enviar este archivo a los
coautores»*. Entró el 02-09 y se publicó con la rama el 04-09.

**Y el archivo era lo de menos.** El orden salía de
`random.Random(SEMILLA_ORDEN).shuffle(casos)` con la **semilla escrita en
`_plantilla_ciega.py`**, que también es público. Con el guion y la guía delante,
cualquiera reproducía el barajado y sabía qué caso ciego es cuál. Borrar solo el
JSON habría sido teatro: la fuga era la semilla.

**Se cerró en tres pasos.** (1) La semilla sale del repositorio: se pasa con
`--semilla`, se toma de `MIGRA_SEMILLA_ORDEN` o se lee de la clave local, y si no
hay ninguna el guion se niega a generar. (2) `_plantilla_clave.json` pasa a
`.gitignore` y deja de seguirse, pero **sigue en el disco**: es la clave, hace
falta para medir la concordancia. (3) **Se rebarajó con una semilla nueva** y se
regeneró `docs/plantilla_casos_ciegos.md`, porque quien clonara entre el 4 y hoy
ya tiene la semilla vieja: retirarla sin rebarajar no habría servido de nada. El
orden que van a valorar los coautores **no se puede reproducir** desde nada de lo
publicado.

**Lo que la plantilla NO revelaba, y sigue sin revelar:** el documento que se
envía no lleva los identificadores de la guía. Comprobado.

⏭️ **Queda pendiente purgar del historial** el archivo de la clave y la semilla
vieja: aparecen en 15 commits. La reescritura está preparada y verificada, pero
el permiso para ejecutarla lo tiene que dar el usuario. **No es urgente**: sirve
para el orden viejo, que ya no se usa. Mientras tanto, en el árbol publicado no
están ni el archivo ni la semilla.

---

## 2026-09-07 · La ruta de conversión de Siemens

**Se pidió.** Que el cuestionario dispare los pasos de migración de Siemens en un
caso que hasta ahora el agente no distinguía: el usuario **sí** conoce la
contraseña y **sí** puede acceder al código, pero insiste en migrar porque el
equipo está descontinuado y sin repuestos. El agente acababa empujando a
reconstruir un programa que en realidad se puede convertir.

**Devolvió.** La cadena de conversión que el procedimiento de 57 pasos no tenía
en ningún lado: **STEP 5 → S5 File Converter → SIMATIC Manager (STEP 7) →
MigrateProject → TIA Portal**, sin saltos directos. Cinco archivos (+441/−14):

- Disparador `obsolescencia_con_acceso_al_codigo`, que se activa leyendo
  N06/F16, F01/F06/F07 y M01/M04/M06/M09, y **devuelve la cadena de evidencia**
  que lo sostiene en vez de afirmarlo a secas.
- Bloque `rutas_por_fabricante` con la ruta de Siemens en siete pasos (S1–S7).
  No sustituye a los 57: **los especializa** en el 13, 20, 21, 22 y 23.
- Tema `ruta_fabricante` en `consultar_procedimiento`, su render en Markdown y
  el bloque correspondiente en el prompt del modo guía.
- En el cuestionario, las dos variantes de ejecución de la migración y la regla
  de prioridad 7: convertir un programa y reescribirlo no se presupuestan igual.

**Se verificó.** Corriendo el despachador real `ejecutar_herramienta`, no
describiéndolo: con el expediente de prueba, `tema='disparadores'` devuelve
`obsolescencia_con_acceso_al_codigo` con las **siete** respuestas que lo
sostienen, y `tema='ruta_fabricante'` devuelve los S1–S7 completos ·
`compileall` limpio en `migra_ia` y `webapp` · controles negativos: Rockwell
**declara** que no tiene ruta en vez de improvisarla, un caso con `sin_respaldo`
recibe el aviso de que la ruta no aplica, y un expediente vacío no dispara nada ·
`total_pasos` sigue en **57** y el cuestionario en **17** secciones · `.env` en
la línea 1 de `.gitignore`, sin trackear, y `git status --porcelain` sin archivos
extra antes del push.

**No se pudo verificar.** Las dos guías oficiales de Siemens que la ruta cita
(`105106251` para S5→S7 y `109478811` para S7-300→S7-1500) ya venían en
`data/fabricantes_cpu.json`, pero **no se comprobó que sigan resolviendo**: el
portal responde `403 Forbidden` desde Akamai a cualquier cliente sin navegador.
Es protección anti-bot, no prueba de enlace muerto, pero tampoco prueba de lo
contrario. Queda pendiente abrirlas a mano.

**Se corrigió.** Dos cosas:

1. **Un falso positivo que daba el diagnóstico contrario.**
   `contrasena_desconocida` se disparaba por encontrar la palabra "contrasena"
   en el texto libre de las respuestas. Responder *"No hay contraseñas"* —que es
   la mejor noticia posible— activaba **reconstrucción**, que es justo la ruta
   cara. Ahora queda suprimido cuando el programa es accesible.
2. **Una reescritura que ensuciaba el diff.** El primer parche volcó
   `data/cuestionario.json` con `json.dump(indent=2)` y expandió el formato
   compacto original: **1794 líneas** de diff para dos cambios. Se revirtió con
   `git checkout --` y se aplicó a mano. El diff final del archivo son **9
   líneas**.

**Una decisión de ingeniería queda anotada en el propio dato.** La ruta habla de
**S7-1200** y no de S7-200 porque la restricción de lenguaje es de esa familia:
TIA Portal no admite AWL para S7-1200 y el S7-1500 sí. Por eso el paso S5 solo
exige convertir AWL a KOP o bloques cuando el destino es un S7-1200. Está en el
campo `nota_tecnica` de la ruta, para que nadie lo "corrija" más adelante.

⏭️ **Queda pendiente.** La ruta está **cerrada para Siemens y abierta para las
otras 29 marcas** del catálogo: el hueco se declara en
`ruta_de_conversion_por_marca` en vez de rellenarse improvisando. Y `main`
todavía no tiene nada de esto; el trabajo vive solo en la rama
`catalogo-fabricantes-adaptativo`.

---

## 2026-09-07 (2.ª parte) · El agente tiene dos motores, y solo actualicé uno

**Se pidió.** Ver la ruta de Siemens funcionando en el agente del escritorio. El
recorrido llegó hasta fijar el destino —**SIMATIC S7-1200**, con la pantalla de
*"Misma marca"*— y ahí no aparecía nada nuevo.

**Devolvió.** El diagnóstico, que era el hallazgo de verdad: **la webapp tiene dos
motores y yo solo había tocado uno.** `webapp/app.py:64` bifurca según el modo:

- **Chat con clave de Anthropic** → usa el system prompt y las herramientas. Ahí sí
  estaba la ruta.
- **Demo interactiva, sin clave** → usa `migra_ia/interactivo.py`, un guion
  **determinista** de 991 líneas que no consulta al modelo para nada.

El texto que salía en pantalla estaba escrito literalmente en `interactivo.py:826`.
Y `grep ruta_fabricante migra_ia/interactivo.py` daba **0**: ese motor no pedía la
ruta en ningún momento. Habría recorrido los 57 pasos y en el 21 habría dicho el
texto genérico *"usar las herramientas del fabricante"*, sin nombrar nunca el S5
File Converter ni MigrateProject.

El arreglo, commit `8a29c25` (+98/−1):

- `procedimiento.ruta_para_paso()` y `texto_ruta_para_paso()` devuelven los
  sub-pasos de la marca que especializan **un** paso concreto, o vacío si no
  aplica. `texto_ruta_resumen()` anuncia la ruta al fijar el destino.
- `interactivo.py` los llama en dos sitios: justo después de `fijar_cpu_destino`
  —que es cuando el usuario decide— y en el render de cada paso.
- Paso **5b** en el árbol de decisión del prompt, para que las tres capas digan lo
  mismo. Se numera 5b y no se renumera del 5 al 8 porque `cuestionario.json:221`
  remite al *"paso 2 del arbol de decision"*.

**Se verificó.** Los pasos **13, 20, 21, 22 y 23** salen con su desglose de marca y
los otros **52 quedan idénticos** · con destino S7-1200 aparece el aviso de que hay
que pasar AWL a KOP antes de migrar, y con S7-1500 **no** aparece, que es lo
correcto porque esa familia sí admite AWL · controles negativos: sin respaldo,
marca sin ruta publicada y cambio de marca no muestran nada, en vez de mostrar una
ruta que no aplica · `compileall` limpio · servidor reiniciado a las **22:58:57**,
respondiendo **HTTP 200**, con los tres archivos modificados a las 22:07, 22:48 y
22:49, todos anteriores al arranque.

**Se corrigió.** Dos cosas, y la primera es un error de método:

1. **Di por hecho que un motor hereda del otro.** Cablée la ruta en la capa de
   datos y en el prompt, y asumí que el modo interactivo la recogería. No la
   recoge: es un guion aparte. La comprobación que faltaba era trivial —un `grep`
   del nombre de la función en el otro motor— y no la hice. **Regla para la
   próxima: al añadir una capacidad, comprobar en cuántos motores hay que
   enchufarla, no en cuántos la definen.**
2. **Los pasos 20 y 22 se quedaban mudos.** Figuran en `aplica_a_pasos` pero no
   tienen sub-paso propio, solo una regla que los gobierna. La primera versión
   devolvía vacío si no había sub-pasos, así que se perdía justo el aviso de que
   el hardware no se convierte. Lo destapó la prueba, no la lectura del código.

**Por qué no se veía aunque los archivos estuvieran bien.** `webapp/app.py:30`
construye el system prompt **en el import**, todos los módulos de datos usan
`@lru_cache` y el servidor arranca con `debug=False`, sin recarga automática.
Editar un archivo no cambia nada hasta cerrar y reabrir `Iniciar_MIGRA-IA.bat`.
Conviene recordarlo antes de dar por roto algo que solo está sin recargar.

⏭️ **Queda pendiente.** `main` sigue sin nada de este trabajo: los tres commits
viven en `catalogo-fabricantes-adaptativo`.

## 2026-09-08 · El porte entre marcas, cuando el código sí está

**Se pidió.** Analizar el escenario que faltaba —contraseñas conocidas, programa
accesible y, aun así, migración a un PLC de **otra marca**— y contrastarlo contra
una lista de dieciséis pasos de migración entre fabricantes antes de decidir si se
agregaba algo.

**El mapeo, primero.** De los dieciséis, **doce ya existían** en los 57 pasos, casi
siempre con más detalle: respaldo *verificado* (5), matriz de equivalencia con la
prohibición de equivaler por nombre (14), comunicaciones (24), HMI/SCADA (25),
simulación (30), comparación viejo contra nuevo (32) y FAT/SAT (31, 42). **Dos no
existían**: la tabla de equivalencia de instrucciones entre fabricantes y el triaje
de lógica trasladable frente a reprogramable. **Uno estaba a medias**: nada
inventariaba la memoria interna del programa viejo —marcas, DB, temporizadores,
contadores— ni censaba en qué lenguaje está escrito cada bloque. Y **uno se
descartó**: seleccionar la CPU nueva por memoria, velocidad y E/S choca con el
`limite_duro` del paso 13, porque el catálogo no publica atributos comparables por
modelo entre marcas y esa decisión es lo que separa este agente de uno que inventa.

**El hueco de verdad estaba en el cruce.** `procedimiento.py:122` ya calculaba
`con_codigo_fuente` y **ningún dato lo leía**: ocho `variante_cambio_marca`, ocho
`variante_sin_respaldo` y cero para la combinación de las dos. Con cambio de marca
ganaba el texto genérico del paso 21 —*«se REESCRIBE desde cero… planificar como
desarrollo nuevo»*—, que es el de la vía ciega. El disparador que escribí ayer
declara ese caso *«el escenario MÁS FAVORABLE»*, y en cuanto el usuario elegía otra
marca el agente le hablaba como si no tuviera nada en la mano.

**Se agregó**, commit `0996576` (+413/−61). Un bloque `ruta_cambio_de_marca` con la
misma forma que `rutas_por_fabricante`, para que lo sirva la maquinaria de ayer sin
inventar mecanismo: **C1** inventario de memoria interna y censo de lenguajes (paso
11), **C2** tabla de equivalencia de instrucciones (paso 12), **C3** triaje
trasladable / adaptable / a reprogramar (paso 21), **C4** mapeo de direcciones
desde la tabla de símbolos original (paso 18) y **C5** comparación E/S por E/S y
secuencia por secuencia (paso 32). Seis reglas, incluidas dos que no estaban en
ningún sitio: **la lógica de seguridad no se porta por analogía** aunque exista
instrucción equivalente, y **conocer la contraseña no da derecho** a reimplementar
la lógica de un tercero en otra plataforma. Es una sola ruta para cualquier par de
marcas: describe el método, no las equivalencias, que se construyen caso por caso
contra los manuales de los dos fabricantes.

**Se corrigió el «desde cero» en seis sitios**, porque solo es cierto sin acceso al
código: la variante del paso 21 y el *en contra* del paso 13 en los datos; el aviso
al fijar destino, la justificación que se guarda en el expediente y la
recomendación del informe en `interactivo.py`; la consecuencia de
`fijar_cpu_destino` en `herramientas.py`; y la opción B en `prompt.py`. También
entraron las variantes de cambio de marca que faltaban en los pasos 23, 24 y 25: el
23 hablaba de corregir un reporte de migración que entre marcas no existe.

**Los dos motores, esta vez desde el principio.** La regla de ayer se aplicó antes
de escribir nada, y valió: además de `ruta_para_paso`, el modo interactivo tenía
**tres textos cableados a mano** que afirmaban «reescritura completa» sin mirar el
acceso al código. Con la función sola no habría bastado.

**Se verificó.** Cinco escenarios de contexto: cambio de marca con código (sale la
ruta en 11, 12, 18, 21 y 32), cambio de marca sin código (nada), `sin_respaldo` más
cambio de marca (nada), misma marca con código —**la ruta de Siemens intacta**, con
sus S1-S7 donde siempre— y un par sin ruta publicada, Omron a Mitsubishi, que
funciona porque la ruta es genérica. De punta a punta con el motor determinista:
escenario nuevo `otra_marca_con_codigo` en `_interactivo_run.py`, 57 de 57 pasos y
riesgo 69,2; `critico` sigue dando **85,0** y 57 de 57. `compileall` limpio y el
system prompt construyéndose en 44.569 caracteres con el tema nuevo, el paso 5c y
el índice.

**Se blindó el generador.** `_generar_procedimiento.py` reescribe el JSON entero
desde el `.docx` y no conoce ninguna de las dos rutas: regenerarlo habría borrado en
silencio el trabajo de ayer y el de hoy, sin decir nada. Ahora compara lo que va a
escribir contra lo que hay, se detiene y enumera lo que se perdería. Probado.

⏭️ **Queda pendiente.** El smoke test contra la API no se corrió: la clave devuelve
**401**. Y `main` sigue sin nada de esto: el trabajo está en la rama
`ruta-cambio-de-marca`, en local y **sin empujar**.

## 2026-09-08 (2.ª parte) · El triaje llegaba tarde

**Se pidió.** Correr el escenario `otra_marca_con_codigo` y ver el **paso 21
completo**, no un recorte.

**Lo que se vio.** El paso sale bien —texto original, criterio de salida, el aviso
de que no aplica y debajo el sub-paso C3 con sus dos reglas—, pero el avance lo
delataba: **27 de 57**. La extensión P1-P7 se intercala tras el paso 20, así que
cuando el recorrido llega al 21 el programa nuevo **ya está escrito**. El triaje
que decide qué se traslada, qué se adapta y qué se reprograma —y de donde sale la
estimación de esfuerzo— llegaba después de haber hecho el trabajo.

**Se movió**, commit `aac1d20`. C3 pasa a especializar el **paso 11**, junto al
inventario C1: la clasificación y su estimación quedan cerradas **antes** de
redactar la especificación en P1. Como el triaje ahora precede a la tabla de
equivalencia de instrucciones (C2, paso 12), se declara **provisional**: todo
bloque que dependa de una instrucción sin equivalente pasa a *a reprogramar*
cuando el 12 cierre, y el criterio de salida de C3 obliga a revisarlo entonces.

El paso 21 sigue en la ruta con sus dos reglas —la fuente es especificación, no
plantilla; y la titularidad del programa— y su variante remite al triaje ya hecho
en el 11.

**Se verificó.** Los cinco escenarios de contexto, con el 11 mostrando C1 y C3 y el
21 solo reglas; la ruta de Siemens intacta; `otra_marca_con_codigo` 57 de 57 y
`critico` en **85,0**.

## 2026-09-08 (3.ª parte) · El cierre de la versión: metadatos, nombres y etiqueta

**Se pidió.** Cerrar la versión: fusionar a `main` el trabajo de la rama, poner al
día los metadatos de la release, etiquetar la **v0.4.0** y borrar las ramas que ya
no hacían falta.

**La fusión.** Avance rápido limpio —`main` salía del mismo commit del que nació la
rama—, sin commit de fusión y sin conflictos.

**Los metadatos**, commit `e22ed79`. Versión y descripción de la 0.4.0, y una
corrección de afiliación: los **cuatro** autores quedan en Universidad Tecnológica
de Honduras. El repo le atribuía a Loo una segunda afiliación que no le
corresponde. `CITATION.cff` y `.zenodo.json` eran los dos únicos archivos con
campo de afiliación; las tres landings y el BibTeX listan nombres sin ella.

**La tarjeta del artefacto**, commit `6c4ecd0`. `ARTIFACT.md` y `README.md`
recogen el escenario `otra_marca_con_codigo` y la ruta de porte entre marcas, que
hasta entonces solo existían en el código y en esta bitácora.

**Los nombres**, commit `85b5121`. El bloque de autores del paper dice **«Julio Noé
Castillo»** con tilde e **«Isidoro Medina»** sin el segundo nombre; el repo llevaba
la tilde omitida a propósito en los metadatos —decisión vieja, que se levanta— e
«Isidoro Emilio Medina» en ocho sitios. Ambos quedan como en el paper. En el
BibTeX de `docs/GUIA_ZENODO.md` la tilde va como escape de LaTeX, `No\'e`, igual
que el resto de ese bloque; en la plantilla de subida y en la landing va la tilde
real. Las tres copias de la landing siguen idénticas por hash. Se hizo **antes** de
etiquetar a propósito: estos nombres quedan fijos en el registro de Zenodo.

**La etiqueta.** `v0.4.0` **anotada** sobre `85b5121` y empujada a origin, con
notas al estilo de la de v0.3.0: catálogo de 30 fabricantes y 469 modelos,
MIGRA-IA-PROC-050, cuestionario de 17 secciones, modo interactivo sin clave, línea
base del riesgo ordinal y las dos rutas. Conviene saber que `v0.2.0` es ligera y
que `v0.3.0` y `v0.4.0` son anotadas.

**Las ramas.** Borradas en local y en remoto `ruta-cambio-de-marca` (estaba en
`11a4906`) y `catalogo-fabricantes-adaptativo` (en `37da610`). Las dos aparecían en
`git branch --merged main` antes de tocarlas, y sus commits siguen alcanzables
desde el histórico de `main` y desde la etiqueta. En el repositorio queda **solo
`main`**.

⏭️ **Queda pendiente.** El **release de GitHub**: la etiqueta sola no dispara el
webhook de Zenodo, así que la v0.4.0 **todavía no tiene DOI**. El procedimiento
está en `docs/GUIA_ZENODO.md`, incluido qué hacer si el release sale *Failed* en
rojo, como ocurrió con la v0.3.0. Cuando el DOI exista habrá que actualizar la
referencia IEEE y el BibTeX de esa guía, que hoy citan la v0.3.0 con su DOI y
listan tres autores. Y el **smoke test contra la API sigue sin correrse**: la clave
devuelve 401.

## 2026-09-09 · El agente, por fin, en línea

**Se pidió.** Relanzar el agente evacuando los pendientes uno a uno. El primero de
la lista era el más viejo: el requisito, declarado en julio y reafirmado el 29 de
ese mes, de que *cualquiera* pueda **abrir, descargar e interactuar**. Abrir y
descargar estaban cumplidos desde que el repositorio se hizo público; interactuar
exigía instalar Python, y por eso no lo estaba.

**Se desplegó.** Servicio web en Render creado desde el Blueprint que lee el
`render.yaml` del repositorio, plan gratuito, rama `main`, sincronizando el commit
`40c15a3`. La variable `ANTHROPIC_API_KEY` se dejó **vacía** a propósito: así la
página pública ofrece solo la demo interactiva, que no toca la API, y ningún
visitante puede consumir la cuenta de nadie. Dirección:
**https://migra-ia.onrender.com**

**Se verificó**, contra el servicio en vivo y no contra la copia local:

- La página responde **HTTP 200** y sirve la **0.4.0**, con sus dos entradas.
- `POST /api/nuevo {"interactivo": true}` abre expediente sin credencial alguna.
- Respondiendo **«Siemens S7-300»**, el agente identifica marca Siemens, familia
  **SIMATIC S7-300** —etapa intermedia, posición 4 de 7 en la cronología— y lista
  las seis CPU documentadas de esa generación. El catálogo de 30 fabricantes viaja
  entero al servidor.
- Respondiendo un dato basura (**«1»**), se niega: *«no voy a asimilarlo a la marca
  más parecida»*. La regla de no inventar equivalencias se comporta igual en la
  nube que en la máquina del autor.

**Se corrigió.** El enlace no aparecía en ninguna parte: se añadió al `README.md`,
a `ARTIFACT.md` y a las **tres copias de la landing**, que siguen idénticas por
hash. En `ARTIFACT.md` queda acotado qué permite y qué no: la vía en línea basta
para comprobar las afirmaciones de la sección 1, pero **no** reproduce las salidas
deterministas ni el expediente en `casos/`, que siguen exigiendo la ejecución
local. Y `render.yaml` aún describía la clave vacía como «Modo demo», el guion
narrado que se retiró el 4 de septiembre; ahora dice «Demo interactiva».

⏭ **Queda pendiente.** El plan gratuito **duerme el servicio** tras un rato sin
visitas: la primera carga puede tardar cerca de un minuto en despertar, y conviene
decirlo a quien reciba el enlace. Siguen abiertos el **release de GitHub** —que es
lo que acuña el DOI de la versión— y el **smoke test contra la API**, cuya clave
devuelve 401.

## 2026-09-09 (2.ª parte) · El release, el DOI y la etiqueta que hubo que mover

**Se pidió.** Cerrar el relanzamiento: publicar el release de GitHub, que es lo que
dispara el webhook de Zenodo, y comprobar el DOI resultante.

**Primero hubo que mover la etiqueta.** `v0.4.0` apuntaba a `85b5121` y `main` ya iba
dos commits por delante, con el enlace del agente y la entrada anterior de esta
bitácora. Publicar desde ahí habría archivado bajo un DOI **permanente** una copia
que no menciona que el agente está en línea —y eso no se corrige después—. Se dejó
la etiqueta de respaldo `respaldo-etiqueta-v0.4.0-en-85b5121` y se reetiquetó sobre
`736d436`. Ningún commit quedó huérfano: `main` avanzó en línea recta, así que
`85b5121` sigue en su historial. La ventana para hacerlo era esta: con el DOI ya
acuñado, mover la etiqueta habría dejado la cita apuntando a un contenido distinto
del archivado.

**Se publicó el release.** Las tres entregas del webhook repiten el patrón de la
v0.3.0: `release/created` **202 OK** —esa es la que archiva— y `published` y
`released` **409**, que significa *ya atendido*, no fallo. Conviene no volver a
alarmarse con eso.

**El DOI de la versión es `10.5281/zenodo.22683608`.** Verificado en la API: estado
*done*, tipo Software, licencia MIT, versión 0.4.0, los cuatro autores con
afiliación UTH y el ZIP de 366,1 KB. Resuelve en doi.org con **302**, que es la
única prueba de que quedó registrado en DataCite. El **concept DOI**
`10.5281/zenodo.21480949` ya apunta a este registro, de modo que el paper y la
landing citan la 0.4.0 **sin tocar una sola línea**.

**Se verificó el contenido archivado**, descargando el ZIP del propio depósito: el
enlace `migra-ia.onrender.com` aparece en `README.md`, `ARTIFACT.md`,
`DESPLIEGUE_RENDER.md` y las tres copias de la landing, y la entrada de hoy está en
la bitácora. Era exactamente lo que motivó mover la etiqueta.

**El smoke test sí se corrió, y sigue en 401.** `API key is invalid`. Importa lo que
funcionó antes de fallar: se leyó el `.env`, se creó el cliente, se abrió el
expediente `CAS-2026-043736`, se construyó el prompt con sus herramientas y se envió
la petición. **El fallo es de credencial, no de código**; la clave del `.env` sigue
siendo un marcador de posición. Queda pendiente de una clave real.

**Se corrigió.** `docs/GUIA_ZENODO.md` citaba la v0.3.0 con tres autores: ahora la
tabla lista los cuatro DOI, y la referencia IEEE y el BibTeX van con la 0.4.0 y sus
cuatro autores. Se añadió la excepción del proyecto —paper y landing citan el
concept DOI a propósito— porque la propia guía recomendaba lo contrario y esa
contradicción había que dejarla escrita.
