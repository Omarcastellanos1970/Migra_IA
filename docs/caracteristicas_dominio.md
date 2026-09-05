# Caracteristicas de dominio - el rubro

Generado por `_caracteristicas.py` leyendo `data/cuestionario.json` y
`docs/reglas_de_puntuacion.md`, que a su vez se extrae del arbol sintactico
del motor. Si un factor deja de leer un codigo, este documento cambia solo.

Casilla 3 del entregable. La decision esta tomada y es esta: **no se va con
el dato crudo**. El proyecto define caracteristicas de dominio -conocimiento
de ingenieria convertido en numero- y las pondera; lo que sigue dice cuales,
con que peso, y cuales se recogen y no se usan.

## Las candidatas del rubro, contra lo que el motor hace

| Caracteristica | Codigos | Estado |
|---|---|---|
| Anos desde lanzamiento | C05, D07 | **Se pregunta y NO se usa** (C05, D07) |
| Fin de soporte | M03, M02 | **Se pregunta y NO se usa** (M03, M02) |
| Estado en el catalogo del fabricante | M01 | **Usada** por el motor (M01) |
| Repuestos | M04, M05, M06 | **Usada** por el motor (M04, M06); M05 se preguntan y no se usan |
| Protocolo | G01 | **Usada** por el motor (G01) |
| Criticidad | C08, C10, Q01 | **Usada** por el motor (C08, C10); Q01 se preguntan y no se usan |

**Anos desde lanzamiento.** Ano de fabricacion y de instalacion. Esta en la placa del equipo y es anterior a cualquier evento de fin de vida, asi que no puede contaminarse con la etiqueta.

**Fin de soporte.** Ano de fin de soporte y de fin de venta declarados por el fabricante. Ambos opcionales en el cuestionario: se piden 'si se conoce'.

**Estado en el catalogo del fabricante.** La que el dominio manda: es la variable que un gerente de planta ya usa para decidir.

**Repuestos.** Disponibilidad de repuesto nuevo, de mercado secundario y plazo de entrega.

**Protocolo.** Redes que utiliza la maquina. Determina cuanto arrastra el cambio.

**Criticidad.** Criticidad de la maquina, parada tolerable y coste de hora parada.

## Los ocho factores del motor y lo que leen

Estos son los que estan implementados y ponderados. Los pesos son los de la
Seccion 6 del paper y no se tocan sin actualizarlo.

| Factor | Peso | Codigos que lee |
|---|---|---|
| Estado del ciclo de vida | 0.20 | M01 |
| Disponibilidad de repuestos | 0.15 | M04, M06, C10 |
| Soporte del fabricante | 0.15 | M09, M07 |
| Disponibilidad del software | 0.10 | N02, N03, N05, N06 |
| Disponibilidad de respaldo | 0.15 | F01, F06, F07 |
| Compatibilidad con sistemas actuales | 0.10 | G01, O07, O08, O02 |
| Historial de fallas | 0.05 | L01, L03 |
| Criticidad productiva | 0.10 | C08, C10, Q04 |

## Huecos: lo que se recoge y se tira

El cuestionario pide estos datos al tecnico, los guarda en el expediente
y **ningun factor los lee**. Es la misma clase de defecto que F12, pero
sobre las dos caracteristicas que el rubro nombra primero:

- `C05` — Ano aproximado de fabricacion  \[Anos desde lanzamiento\]
- `D07` — Ano aproximado de instalacion  \[Anos desde lanzamiento\]
- `M03` — Ano de fin de soporte tecnico y de suministro de repuestos, si se conoce  \[Fin de soporte\]
- `M02` — Ano en que el fabricante dejo (o dejara) de vender el producto, si se conoce  \[Fin de soporte\]
- `M05` — Se consiguen repuestos usados o reacondicionados en el mercado secundario?  \[Repuestos\]
- `Q01` — Costo aproximado de una hora de parada de esta maquina, indicando la moneda  \[Criticidad\]

Cerrarlo obliga a tocar `scoring.py`, cuyos ocho factores y pesos son los
que describe el paper. Es decision editorial, no tecnica, y esta anotada
como tal.

## En la tabla de ciclo de vida solo sobrevive una

Lo anterior es el cuestionario, que es donde vive el conocimiento de dominio
del proyecto. El conjunto tabular con el que se entrena el baseline de P1 es
otro -`data/ciclo_vida_plataformas.csv`, nueve plataformas- y ahi la
auditoria de fuga deja **una sola variable admisible: la antiguedad**. No es
una eleccion de modelado: las demas columnas o definen la etiqueta o son
metadato del proceso de recoleccion. Ver la seccion 6 de
`docs/baseline_reproducible.md`.

De ahi que la ampliacion del conjunto sea la tarea que desbloquea el resto:
mientras la tabla tenga nueve filas y una variable, las caracteristicas de
dominio estan definidas pero no se pueden ejercitar.
