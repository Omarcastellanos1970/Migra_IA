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
- La **contribución intelectual la definen los autores**, que es quien conoce la
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

## 2026-09-04 (2.ª parte) · Baseline reproducible del rubro

**Se pidió.** El entregable del taller: baseline reproducible con seis casillas
marcadas. El rubro tiene modelo asignado — *regresión logística ordinal y
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
   al confirmarse que el rubro tiene modelo asignado se sustituyó por la logística
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

## 2026-09-04 (5.ª parte) · Esquema de partición asignado al rubro

**Se pidió.** Aplicar el esquema que el rubro asigna al rubro: **estratificada por
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

**Se pidió.** Aplicar las métricas que el rubro fija para **el rubro** en el
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
