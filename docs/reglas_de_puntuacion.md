# Reglas de puntuacion de los 8 factores

Extraido automaticamente de `migra_ia/interactivo.py` por `_reglas_puntuacion.py`. Si el codigo cambia, este documento cambia.

Cada factor produce un valor 0-100 (mayor = mas riesgo). El riesgo total es la media ponderada de los ocho, con los pesos de la Seccion 6.

## Estado del ciclo de vida

**Peso 0.20** - implementado en `_f_ciclo_vida()` - lee: `M01`

*Sin tabla de consulta: la regla es condicional. Ver notas.*

**Notas:** Tabla directa sobre M01. Si M01 es 'No se conoce' el factor NO se puntua: se omite, los pesos se renormalizan y el hueco se registra como dato faltante. Es la unica forma de que el motor no suponga un estado que nadie declaro.

## Disponibilidad de repuestos

**Peso 0.15** - implementado en `_f_repuestos()` - lee: `M04`, `M06`, `C10`

| Respuesta | Valor |
|---|---|
| Si, sin problema | 10 |
| Si, pero con plazo largo | 45 |
| Solo por pedido especial | 65 |
| No | 95 |
| *(no se conoce)* | sin defecto: ver notas |

**Notas:** M04 fija la base. Despues hay un CRUCE que la tabla no muestra: se compara el plazo de entrega (M06) con la parada que la linea tolera (C10). Si M06 esta en 'De 2 a 8 semanas' o peor, la base se eleva a un minimo de 85, porque un repuesto que llega despues de lo que la planta aguanta no cubre el riesgo por si solo.

## Soporte del fabricante

**Peso 0.15** - implementado en `_f_soporte()` - lee: `M09`, `M07`

Segun `M09`:

| Respuesta | Valor |
|---|---|
| Si, vigente | 10 |
| Vencido | 60 |
| No | 85 |
| *(no se conoce)* | sin defecto: ver notas |

Segun `M07`:

| Respuesta | Valor |
|---|---|
| Si, del fabricante | -15 |
| Si, de tercero certificado | -5 |
| Si, de tercero sin certificar | 5 |
| No | 15 |
| *(cualquier otra / no se conoce)* | 0 |

**Notas:** M09 (contrato vigente) fija la base y M07 (servicio de reparacion) la ajusta hacia arriba o hacia abajo. Si M09 no se conoce, la base queda en 55 salvo que M07 tampoco se conozca, en cuyo caso el factor se omite.

## Disponibilidad del software

**Peso 0.10** - implementado en `_f_software()` - lee: `N02`, `N03`, `N05`, `N06`

Segun `N02`:

| Respuesta | Valor |
|---|---|
| Windows XP | 25 |
| Windows 7 | 20 |
| Windows 10 | 0 |
| Windows 11 | 0 |
| Linux | 0 |
| Maquina virtual sobre un equipo moderno | 0 |
| *(cualquier otra / no se conoce)* | 10 |

Segun `N03`:

| Respuesta | Valor |
|---|---|
| Original con licencia vigente | 0 |
| Original con licencia vencida | 15 |
| Licencia flotante en servidor | 5 |
| Llave fisica (dongle) | 15 |
| Version de demostracion o limitada | 20 |
| No se tiene licencia | 30 |
| *(cualquier otra / no se conoce)* | 10 |

Segun `N05`:

| Respuesta | Valor |
|---|---|
| Si, ya probado con este PLC | 0 |
| Si, pero sin probar | 10 |
| No | 25 |
| *(cualquier otra / no se conoce)* | 10 |

Segun `N06`:

| Respuesta | Valor |
|---|---|
| Si, todas | 0 |
| Parcialmente | 15 |
| No | 30 |
| No hay contrasenas | 0 |
| *(cualquier otra / no se conoce)* | 15 |

**Notas:** ACUMULADOR: **arranca en 20** y suma las cuatro tablas de arriba (N02 + N03 + N05 + N06). Un valor no listado suma el defecto indicado. El resultado se acota a 0-100. El factor solo se omite si los cuatro codigos faltan a la vez.

## Disponibilidad de respaldo

**Peso 0.15** - implementado en `_f_respaldo()` - lee: `F01`, `F06`, `F07`

*Sin tabla de consulta: la regla es condicional. Ver notas.*

**Notas:** CONDICIONAL EN CASCADA, no hay tabla. Se evalua en este orden y se detiene en la primera que se cumpla:

| Situacion | Valor |
|---|---|
| F01 no se respondio | *factor omitido* |
| F01 = No (no existe copia) | 100 |
| F01 no se conoce | 90 |
| F06 = No (el respaldo no abre) | 100 |
| F07 = No (no compila) | 90 |
| F06 = Si y F07 = Si (verificado) | 15 |
| verificacion incompleta | 70 |

La logica es la Regla 3 de la guia: un respaldo que no se puede verificar se trata como ausente. Por eso 'no se sabe' (90) puntua casi como 'no existe' (100), y solo el respaldo que abre Y compila baja a 15.

## Compatibilidad con sistemas actuales

**Peso 0.10** - implementado en `_f_compatibilidad()` - lee: `G01`, `O07`, `O08`, `O02`

*Sin tabla de consulta: la regla es condicional. Ver notas.*

**Notas:** ACUMULADOR, no hay tabla. **Arranca en 20** y suma por cada cosa que el cambio arrastra:

| Condicion | Suma |
|---|---|
| G01 incluye una red propietaria | +30 |
| G01 incluye red de generacion anterior* | +15 |
| O07 incluye bloques propietarios | +20 |
| O07 incluye lista de instrucciones (AWL/STL) | +15 |
| O07 incluye GRAFCET / SFC / GRAPH | +10 |
| O08 = Si (librerias propietarias) | +25 |
| O02 = Si (control de movimiento) | +20 |

Las dos de G01 son excluyentes: propietaria tiene prioridad sobre legado. Las de O07 se acumulan entre si. Se acota a 0-100.

*Redes consideradas de generacion anterior: MPI, Profibus DP, Profibus PA, DeviceNet, ControlNet, CC-Link, AS-Interface, RS-232, RS-485.

## Historial de fallas

**Peso 0.05** - implementado en `_f_historial()` - lee: `L01`, `L03`

| Respuesta | Valor |
|---|---|
| En aumento | 20 |
| Estable | 0 |
| En disminucion | -10 |
| Sin fallas registradas | -15 |
| *(cualquier otra / no se conoce)* | 5 |

**Notas:** L01 (numero de paros en 12 meses) fija el escalon, que es un condicional y no una tabla:

| Paros en L01 | Valor |
|---|---|
| 0 | 10 |
| 1 a 2 | 30 |
| 3 a 5 | 50 |
| mas de 5 | 70 |
| sin numero legible | 45 |

Sobre ese escalon se suma la tabla de L03 de arriba. Despues se aplica un TOPE: si hay causa raiz externa sin corregir (tablero caliente, mala puesta a tierra, energia deficiente, bateria agotada), el factor se **limita a 55**, porque esas fallas no son atribuibles al controlador y sustituirlo no las corrige. Es el unico factor cuyo valor puede BAJAR por una regla de diseno.

## Criticidad productiva

**Peso 0.10** - implementado en `_f_criticidad()` - lee: `C08`, `C10`, `Q04`

Segun `C08`:

| Respuesta | Valor |
|---|---|
| Baja: puede detenerse varios dias | 20 |
| Media: afecta parcialmente la produccion | 45 |
| Alta: afecta una linea importante | 70 |
| Critica: detiene la planta o presenta riesgo de seguridad | 95 |
| *(no se conoce)* | sin defecto: ver notas |

Segun `Q04`:

| Respuesta | Valor |
|---|---|
| No hay ventana disponible | 15 |
| En el paro anual de planta o vacaciones | 10 |
| Fines de semana | 5 |
| *(cualquier otra / no se conoce)* | 0 |

Segun `C10`:

| Respuesta | Valor |
|---|---|
| Menos de 1 hora | 20 |
| 1 a 4 horas | 15 |
| 4 a 12 horas | 10 |
| 12 a 24 horas | 5 |
| Mas de 24 horas | 0 |
| *(cualquier otra / no se conoce)* | 0 |

**Notas:** C08 (criticidad de la maquina) fija la base; C10 (parada tolerable) y Q04 (ventana de intervencion) la suben. Si C08 no se conoce, el factor se omite entero.

---

## Lo que estas tablas no dicen

Todas estas constantes estan puestas a mano, igual que los pesos. El analisis de sensibilidad de `_evaluacion.py` perturba **solo los ocho pesos**, no estas constantes: la estabilidad del 100% que reporta vale para la ponderacion, no para las reglas. Es el siguiente hueco de la misma familia.

