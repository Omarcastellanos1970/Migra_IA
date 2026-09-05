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
