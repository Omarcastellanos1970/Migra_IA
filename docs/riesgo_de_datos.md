# Riesgo de datos

**Actualizado el 2026-09-04.** Qué falta, quién lo consigue y para qué fecha.
Los hechos están verificados contra el repositorio; las columnas **quién** y
**para cuándo** marcadas con `POR DECIDIR` las tiene que fijar el equipo, no
salen de ningún archivo.

Se ordena por lo que bloquea, no por lo que cuesta.

---

## 1. Etiquetas del panel de expertos — BLOQUEA P1 y P2

**Qué falta.** La clase de obsolescencia de las nueve plataformas y su orden de
prioridad de reemplazo, emitidos por ingenieros sin ver la salida del motor.

**Por qué bloquea.** Sin etiqueta externa, la de P1 se deriva de las mismas
fechas que serían las variables: hoy P1 re-deriva una definición en vez de
predecir, y por eso la auditoría de fuga deja **una sola variable admisible**.
P2 directamente no se evalúa, porque su clásico asignado —*gradient boosting* en
modo ranking— necesita un orden de referencia que no existe.

**Estado.** El instrumento está listo y no cuesta trabajo nuevo:
`docs/formulario_etiquetado.md`, sin ninguna salida del motor dentro, 20-30
minutos por evaluador. `python _etiquetado.py comparar` lee lo devuelto y mide
el acuerdo entre evaluadores. Mientras tanto hay un etiquetado provisional por
regla, estampado `provisional_regla`, que **no puede publicarse como validación**.

**Quién.** Julio Noé Castillo e Isidoro Medina.
**Para cuándo.** `POR DECIDIR` — hoy 2026-09-04 no hay comunicación con ellos.
Una sola sesión desbloquea los dos subproblemas a la vez.

## 2. Tamaño del conjunto — BLOQUEA cualquier afirmación estadística

**Qué falta.** La tabla de ciclo de vida tiene **9 plataformas**. El catálogo
del agente tiene **130 generaciones y 469 modelos**, pero solo nomenclatura: sus
campos son familia, modelos, observación y fuentes. **No trae ni un año de
lanzamiento ni un horizonte de soporte.**

**Por qué bloquea.** Con nueve filas, cada acierto vale 0.111 de exactitud y
ninguna diferencia entre modelos es sostenible. Es también la razón por la que
`k = 2` es un techo: solo dos fabricantes aportan clase 4.

**Qué habría que hacer.** Poner fecha de lanzamiento y estado declarado a las
130 generaciones, con fuente oficial por fila. Es trabajo de extracción y
verificación, no de programación.

**Quién.** `POR DECIDIR`.
**Para cuándo.** `POR DECIDIR`. Referencia de coste: los niveles C de ocho
plataformas llevan abiertos desde julio y cerraron despacio.

## 3. Niveles C sin cerrar — BLOQUEA su entrada al paper

**Qué falta.** `FUENTES_TABLAS.md` clasifica cada dato en A/B/C y lleva escrita
la regla: *«ningún dato de nivel C debe pasar al paper sin cerrarse antes»*.
Siguen abiertos: Siemens S5 (1979) y S7-300 (1995 vs. 1994) · Rockwell
ControlLogix 5550 (**1997 vs. 1999**, sin resolver) · Schneider Quantum (1994),
Premium (1996) y M262 (2019) · Mitsubishi QnA (1994) y L (2011) · Omron CJ2
(2008) y NX102 (2019).

**Estado.** La regla se está respetando: **ninguna de esas cifras está hoy en
los `.tex`**, comprobado. El riesgo es que entren sin cerrarse.

**Quién.** `POR DECIDIR`.
**Para cuándo.** Antes de que cualquiera de esas cifras entre al paper.

## 4. Fin de repuestos no publicado — 3 de 9 plataformas

**Qué falta.** `SLC 500`, `Modicon Quantum` y `Modicon Premium` traen `n.d.` en
el fin de repuestos y reparación. `SLC 500` tampoco tiene anuncio de fin de
vida, y `MELSEC-A/QnA` y `MELSEC AnS/QnAS` tampoco: **cinco de las nueve tienen
alguna fecha ausente**.

**Cómo se está tratando.** No se sustituye por el peor caso. En la prioridad de
reemplazo hay una banda propia, *fin de repuestos NO publicado*, distinta de
*sin repuestos confirmado*. Decir «ya no hay repuestos» de un dato que nadie
publicó sería inventarlo.

**Quién.** `POR DECIDIR` — se consigue pidiéndolo al fabricante o localizando la
nota oficial de descontinuación.
**Para cuándo.** `POR DECIDIR`.

## 5. Cuatro fechas ambiguas — resueltas por convención, sin confirmar

**Qué falta.** Cuatro celdas admiten lectura `dd/mm` o `mm/dd`: las tres fechas
de `S7-300 / ET 200M` y el anuncio de `SYSMAC CS1`. Se resuelven aplicando
**día primero**, como el resto de la tabla, y el informe las marca `AMBIGUA`
celda a celda.

**Impacto hoy: ninguno.** Las dos lecturas caen del mismo lado de la fecha de
referencia, así que **la clase no cambia** con ninguna de las dos. Deja de ser
inocuo si la fecha de referencia se acerca a esos meses.

**Quién.** `POR DECIDIR`.
**Para cuándo.** Antes de mover `FECHA_REF`.

## 6. Datos de planta — declarado ausente en el paper

**Qué falta.** Acceso a proyectos de PLC en producción. El paper ya lo declara
en la Sección III-C y define una estrategia de datos en cuatro niveles; no es un
descubrimiento nuevo, es la restricción de partida.

**Consecuencia asumida.** El objetivo declarado es evidencia equivalente a
**TRL 4-5**, no una demostración industrial. La validación de campo queda como
trabajo futuro y así está escrito.

**Quién / para cuándo.** No aplica: es una restricción, no una tarea.

## 7. Clave de API — el modo real nunca se ha probado

**Qué falta.** La `ANTHROPIC_API_KEY` del `.env` local es un **placeholder** de
21 caracteres; una real mide más de 100. La API devuelve `401`. El código llega
hasta el envío de la petición.

**Impacto.** El modo demo interactiva y todo el baseline funcionan sin clave, y
son lo que se evalúa. Pero el modo agente con API **nunca se ha ejercitado de
punta a punta**, así que no se puede afirmar que funcione.

**Quién.** Carlos Omar Castellanos.
**Para cuándo.** `POR DECIDIR`. Requiere una clave con saldo.

---

## Lo que cambia si no llega nada

Si ninguno de los siete se resuelve, el trabajo sigue siendo publicable pero
**solo como verificación**: dice que el motor se comporta como su diseño
declara, no que su diseño acierte. Lo que no se puede hacer es presentar las
cifras actuales como validación, y por eso cada una viaja con la procedencia de
su etiqueta.

El de más rendimiento por esfuerzo es el **punto 1**: 20-30 minutos por
coautor, y convierte P1 en un problema de aprendizaje real y P2 en evaluable.
