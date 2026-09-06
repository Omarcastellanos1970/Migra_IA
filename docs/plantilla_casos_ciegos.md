# MIGRA-IA - Valoracion ciega de casos

Gracias por ayudar con esto. Son cinco casos y toma alrededor de una hora.

## Que se le pide

Lea la situacion de cada caso y responda el cuestionario **con su propio
criterio profesional**, como lo haria ante ese equipo en planta.

## Tres reglas que hacen valido el ejercicio

1. **No ejecute el agente MIGRA-IA antes de terminar.** El objetivo es
   comparar su criterio contra el del programa; si ve la salida primero,
   el resultado ya no mide nada.
2. **No consulte con los demas coautores hasta entregar.** Lo que se mide
   es cuanto coinciden ustedes de forma independiente.
3. **Si un dato no se puede saber con lo que dice el caso, respondalo como
   'No se conoce'.** No lo adivine. Que falte informacion es un resultado
   valido y el motor lo trata como tal.

## Como responder

Escriba el **numero** de la opcion despues del `=`, dentro de las comillas
invertidas. Por ejemplo: `` `M01 = 4` ``. Tambien puede escribir el texto
completo de la opcion si lo prefiere.

Guarde el archivo como `respuestas_SUNOMBRE.md` y devuelvalo.

---

## Caso 1

**Contexto:** Estacion de bombeo

**Situacion:** Sistema de bombeo con PLC-5, Remote I/O y SCADA antiguo; la planta debe mantener servicio continuo.

### Cuestionario - Caso 1

**C08.** Criticidad de la maquina
  1) Baja: puede detenerse varios dias  2) Media: afecta parcialmente la produccion  3) Alta: afecta una linea importante  4) Critica: detiene la planta o presenta riesgo de seguridad

`C08 = `

**C10.** Tiempo maximo permitido de parada
  1) Menos de 1 hora  2) 1 a 4 horas  3) 4 a 12 horas  4) 12 a 24 horas  5) Mas de 24 horas

`C10 = `

**Q04.** Cuando puede intervenirse la maquina?
  1) Hay un paro programado ya definido  2) En el paro anual de planta o vacaciones  3) Fines de semana  4) En cualquier momento  5) No hay ventana disponible

`Q04 = `

**M01.** Estado del producto declarado por el fabricante
  1) Activo, en comercializacion  2) En madurez, ya existe un sucesor  3) Anuncio de descontinuacion (phase-out)  4) Descontinuado, aun con soporte y repuestos  5) Descontinuado y sin soporte (fin de vida)  6) No se conoce

`M01 = `

**M04.** Se consiguen repuestos NUEVOS del fabricante o de un distribuidor autorizado?
  1) Si, sin problema  2) Si, pero con plazo largo  3) Solo por pedido especial  4) No  5) No se ha consultado

`M04 = `

**M06.** Plazo de entrega tipico de un repuesto critico (CPU o modulo)
  1) En existencia en la planta o local  2) Menos de 2 semanas  3) De 2 a 8 semanas  4) Mas de 8 semanas  5) No se consigue  6) No se conoce

`M06 = `

**M09.** Existe contrato de soporte o mantenimiento vigente con el fabricante o con un integrador?
  1) Si, vigente  2) Vencido  3) No  4) No se conoce

`M09 = `

**M07.** Existe servicio de reparacion para la CPU o los modulos?
  1) Si, del fabricante  2) Si, de tercero certificado  3) Si, de tercero sin certificar  4) No  5) No se conoce

`M07 = `

**F01.** Existe copia del programa del PLC?
  1) Si  2) No  3) No se conoce

`F01 = `

**F06.** El respaldo abre correctamente?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F06 = `

**F07.** Puede compilarse sin errores?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F07 = `

**F12.** La CPU esta operativa?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F12 = `

**F13.** Existe cable de programacion?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F13 = `

**N02.** Sistema operativo de esa PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Maquina virtual sobre un equipo moderno  7) Otro  8) No se conoce

`N02 = `

**N03.** Tipo de licencia del software de programacion
  1) Original con licencia vigente  2) Original con licencia vencida  3) Licencia flotante en servidor  4) Llave fisica (dongle)  5) Version de demostracion o limitada  6) No se tiene licencia  7) No se conoce

`N03 = `

**N05.** Se dispone del cable o adaptador de programacion correcto, con su driver instalado?
  1) Si, ya probado con este PLC  2) Si, pero sin probar  3) No  4) No se conoce

`N05 = `

**N06.** Se conocen las contrasenas del proyecto y de los bloques protegidos?
  1) Si, todas  2) Parcialmente  3) No  4) No hay contrasenas  5) No se conoce

`N06 = `

**G01.** Que redes utiliza la maquina?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Red propietaria  18) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`G01 = `

**O07.** En que lenguajes esta escrito el programa?
  1) Ladder (KOP / LD)  2) Bloques de funciones (FUP / FBD)  3) Lista de instrucciones (AWL / STL / IL)  4) Texto estructurado (SCL / ST)  5) GRAFCET, GRAPH o SFC  6) Bloques propietarios del fabricante de la maquina  7) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`O07 = `

**O08.** El programa usa bloques, librerias o funciones propietarias del fabricante de la maquina?
  1) Si  2) No  3) No se conoce

`O08 = `

**O02.** Existe control de movimiento, posicionamiento o ejes sincronizados (servos, levas electronicas, interpolacion)?
  1) Si  2) No  3) No se conoce

`O02 = `

**L01.** Cuantos paros no programados atribuibles al sistema de control ha tenido la maquina en los ultimos 12 meses?
  _escriba un numero_

`L01 = `

**L03.** Como ha evolucionado la frecuencia de fallas en los ultimos 24 meses?
  1) En aumento  2) Estable  3) En disminucion  4) Sin fallas registradas  5) No se lleva registro

`L03 = `

**L07.** La maquina pierde el programa, los datos o la hora al quitar la energia?
  1) Si  2) No  3) No se ha probado  4) No se conoce

`L07 = `

**P01.** Temperatura dentro del tablero de control
  1) Menor a 30 C  2) Entre 30 y 40 C  3) Entre 40 y 50 C  4) Mayor a 50 C  5) No se ha medido

`P01 = `

**P04.** Calidad de la energia electrica
  1) Variaciones frecuentes de tension  2) Cortes frecuentes  3) Presencia de armonicos  4) Sin UPS  5) Con UPS  6) Puesta a tierra verificada  7) Puesta a tierra dudosa o inexistente  8) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`P04 = `

---

## Caso 2

**Contexto:** Linea de embotellado

**Situacion:** Linea con CPU S7-300, E/S ET 200M, panel HMI y variadores PROFIBUS con fallas de modulos y dificultad para conseguir repuestos.

### Cuestionario - Caso 2

**C08.** Criticidad de la maquina
  1) Baja: puede detenerse varios dias  2) Media: afecta parcialmente la produccion  3) Alta: afecta una linea importante  4) Critica: detiene la planta o presenta riesgo de seguridad

`C08 = `

**C10.** Tiempo maximo permitido de parada
  1) Menos de 1 hora  2) 1 a 4 horas  3) 4 a 12 horas  4) 12 a 24 horas  5) Mas de 24 horas

`C10 = `

**Q04.** Cuando puede intervenirse la maquina?
  1) Hay un paro programado ya definido  2) En el paro anual de planta o vacaciones  3) Fines de semana  4) En cualquier momento  5) No hay ventana disponible

`Q04 = `

**M01.** Estado del producto declarado por el fabricante
  1) Activo, en comercializacion  2) En madurez, ya existe un sucesor  3) Anuncio de descontinuacion (phase-out)  4) Descontinuado, aun con soporte y repuestos  5) Descontinuado y sin soporte (fin de vida)  6) No se conoce

`M01 = `

**M04.** Se consiguen repuestos NUEVOS del fabricante o de un distribuidor autorizado?
  1) Si, sin problema  2) Si, pero con plazo largo  3) Solo por pedido especial  4) No  5) No se ha consultado

`M04 = `

**M06.** Plazo de entrega tipico de un repuesto critico (CPU o modulo)
  1) En existencia en la planta o local  2) Menos de 2 semanas  3) De 2 a 8 semanas  4) Mas de 8 semanas  5) No se consigue  6) No se conoce

`M06 = `

**M09.** Existe contrato de soporte o mantenimiento vigente con el fabricante o con un integrador?
  1) Si, vigente  2) Vencido  3) No  4) No se conoce

`M09 = `

**M07.** Existe servicio de reparacion para la CPU o los modulos?
  1) Si, del fabricante  2) Si, de tercero certificado  3) Si, de tercero sin certificar  4) No  5) No se conoce

`M07 = `

**F01.** Existe copia del programa del PLC?
  1) Si  2) No  3) No se conoce

`F01 = `

**F06.** El respaldo abre correctamente?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F06 = `

**F07.** Puede compilarse sin errores?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F07 = `

**F12.** La CPU esta operativa?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F12 = `

**F13.** Existe cable de programacion?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F13 = `

**N02.** Sistema operativo de esa PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Maquina virtual sobre un equipo moderno  7) Otro  8) No se conoce

`N02 = `

**N03.** Tipo de licencia del software de programacion
  1) Original con licencia vigente  2) Original con licencia vencida  3) Licencia flotante en servidor  4) Llave fisica (dongle)  5) Version de demostracion o limitada  6) No se tiene licencia  7) No se conoce

`N03 = `

**N05.** Se dispone del cable o adaptador de programacion correcto, con su driver instalado?
  1) Si, ya probado con este PLC  2) Si, pero sin probar  3) No  4) No se conoce

`N05 = `

**N06.** Se conocen las contrasenas del proyecto y de los bloques protegidos?
  1) Si, todas  2) Parcialmente  3) No  4) No hay contrasenas  5) No se conoce

`N06 = `

**G01.** Que redes utiliza la maquina?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Red propietaria  18) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`G01 = `

**O07.** En que lenguajes esta escrito el programa?
  1) Ladder (KOP / LD)  2) Bloques de funciones (FUP / FBD)  3) Lista de instrucciones (AWL / STL / IL)  4) Texto estructurado (SCL / ST)  5) GRAFCET, GRAPH o SFC  6) Bloques propietarios del fabricante de la maquina  7) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`O07 = `

**O08.** El programa usa bloques, librerias o funciones propietarias del fabricante de la maquina?
  1) Si  2) No  3) No se conoce

`O08 = `

**O02.** Existe control de movimiento, posicionamiento o ejes sincronizados (servos, levas electronicas, interpolacion)?
  1) Si  2) No  3) No se conoce

`O02 = `

**L01.** Cuantos paros no programados atribuibles al sistema de control ha tenido la maquina en los ultimos 12 meses?
  _escriba un numero_

`L01 = `

**L03.** Como ha evolucionado la frecuencia de fallas en los ultimos 24 meses?
  1) En aumento  2) Estable  3) En disminucion  4) Sin fallas registradas  5) No se lleva registro

`L03 = `

**L07.** La maquina pierde el programa, los datos o la hora al quitar la energia?
  1) Si  2) No  3) No se ha probado  4) No se conoce

`L07 = `

**P01.** Temperatura dentro del tablero de control
  1) Menor a 30 C  2) Entre 30 y 40 C  3) Entre 40 y 50 C  4) Mayor a 50 C  5) No se ha medido

`P01 = `

**P04.** Calidad de la energia electrica
  1) Variaciones frecuentes de tension  2) Cortes frecuentes  3) Presencia de armonicos  4) Sin UPS  5) Con UPS  6) Puesta a tierra verificada  7) Puesta a tierra dudosa o inexistente  8) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`P04 = `

---

## Caso 3

**Contexto:** Maquina de motion

**Situacion:** Equipo con CJ, modulos de motion y HMI NS; se requiere mejorar diagnostico y disponibilidad.

### Cuestionario - Caso 3

**C08.** Criticidad de la maquina
  1) Baja: puede detenerse varios dias  2) Media: afecta parcialmente la produccion  3) Alta: afecta una linea importante  4) Critica: detiene la planta o presenta riesgo de seguridad

`C08 = `

**C10.** Tiempo maximo permitido de parada
  1) Menos de 1 hora  2) 1 a 4 horas  3) 4 a 12 horas  4) 12 a 24 horas  5) Mas de 24 horas

`C10 = `

**Q04.** Cuando puede intervenirse la maquina?
  1) Hay un paro programado ya definido  2) En el paro anual de planta o vacaciones  3) Fines de semana  4) En cualquier momento  5) No hay ventana disponible

`Q04 = `

**M01.** Estado del producto declarado por el fabricante
  1) Activo, en comercializacion  2) En madurez, ya existe un sucesor  3) Anuncio de descontinuacion (phase-out)  4) Descontinuado, aun con soporte y repuestos  5) Descontinuado y sin soporte (fin de vida)  6) No se conoce

`M01 = `

**M04.** Se consiguen repuestos NUEVOS del fabricante o de un distribuidor autorizado?
  1) Si, sin problema  2) Si, pero con plazo largo  3) Solo por pedido especial  4) No  5) No se ha consultado

`M04 = `

**M06.** Plazo de entrega tipico de un repuesto critico (CPU o modulo)
  1) En existencia en la planta o local  2) Menos de 2 semanas  3) De 2 a 8 semanas  4) Mas de 8 semanas  5) No se consigue  6) No se conoce

`M06 = `

**M09.** Existe contrato de soporte o mantenimiento vigente con el fabricante o con un integrador?
  1) Si, vigente  2) Vencido  3) No  4) No se conoce

`M09 = `

**M07.** Existe servicio de reparacion para la CPU o los modulos?
  1) Si, del fabricante  2) Si, de tercero certificado  3) Si, de tercero sin certificar  4) No  5) No se conoce

`M07 = `

**F01.** Existe copia del programa del PLC?
  1) Si  2) No  3) No se conoce

`F01 = `

**F06.** El respaldo abre correctamente?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F06 = `

**F07.** Puede compilarse sin errores?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F07 = `

**F12.** La CPU esta operativa?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F12 = `

**F13.** Existe cable de programacion?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F13 = `

**N02.** Sistema operativo de esa PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Maquina virtual sobre un equipo moderno  7) Otro  8) No se conoce

`N02 = `

**N03.** Tipo de licencia del software de programacion
  1) Original con licencia vigente  2) Original con licencia vencida  3) Licencia flotante en servidor  4) Llave fisica (dongle)  5) Version de demostracion o limitada  6) No se tiene licencia  7) No se conoce

`N03 = `

**N05.** Se dispone del cable o adaptador de programacion correcto, con su driver instalado?
  1) Si, ya probado con este PLC  2) Si, pero sin probar  3) No  4) No se conoce

`N05 = `

**N06.** Se conocen las contrasenas del proyecto y de los bloques protegidos?
  1) Si, todas  2) Parcialmente  3) No  4) No hay contrasenas  5) No se conoce

`N06 = `

**G01.** Que redes utiliza la maquina?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Red propietaria  18) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`G01 = `

**O07.** En que lenguajes esta escrito el programa?
  1) Ladder (KOP / LD)  2) Bloques de funciones (FUP / FBD)  3) Lista de instrucciones (AWL / STL / IL)  4) Texto estructurado (SCL / ST)  5) GRAFCET, GRAPH o SFC  6) Bloques propietarios del fabricante de la maquina  7) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`O07 = `

**O08.** El programa usa bloques, librerias o funciones propietarias del fabricante de la maquina?
  1) Si  2) No  3) No se conoce

`O08 = `

**O02.** Existe control de movimiento, posicionamiento o ejes sincronizados (servos, levas electronicas, interpolacion)?
  1) Si  2) No  3) No se conoce

`O02 = `

**L01.** Cuantos paros no programados atribuibles al sistema de control ha tenido la maquina en los ultimos 12 meses?
  _escriba un numero_

`L01 = `

**L03.** Como ha evolucionado la frecuencia de fallas en los ultimos 24 meses?
  1) En aumento  2) Estable  3) En disminucion  4) Sin fallas registradas  5) No se lleva registro

`L03 = `

**L07.** La maquina pierde el programa, los datos o la hora al quitar la energia?
  1) Si  2) No  3) No se ha probado  4) No se conoce

`L07 = `

**P01.** Temperatura dentro del tablero de control
  1) Menor a 30 C  2) Entre 30 y 40 C  3) Entre 40 y 50 C  4) Mayor a 50 C  5) No se ha medido

`P01 = `

**P04.** Calidad de la energia electrica
  1) Variaciones frecuentes de tension  2) Cortes frecuentes  3) Presencia de armonicos  4) Sin UPS  5) Con UPS  6) Puesta a tierra verificada  7) Puesta a tierra dudosa o inexistente  8) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`P04 = `

---

## Caso 4

**Contexto:** Maquina de empaque

**Situacion:** Maquina con PLC MELSEC-A, modulos de posicionamiento y GOT antiguo.

### Cuestionario - Caso 4

**C08.** Criticidad de la maquina
  1) Baja: puede detenerse varios dias  2) Media: afecta parcialmente la produccion  3) Alta: afecta una linea importante  4) Critica: detiene la planta o presenta riesgo de seguridad

`C08 = `

**C10.** Tiempo maximo permitido de parada
  1) Menos de 1 hora  2) 1 a 4 horas  3) 4 a 12 horas  4) 12 a 24 horas  5) Mas de 24 horas

`C10 = `

**Q04.** Cuando puede intervenirse la maquina?
  1) Hay un paro programado ya definido  2) En el paro anual de planta o vacaciones  3) Fines de semana  4) En cualquier momento  5) No hay ventana disponible

`Q04 = `

**M01.** Estado del producto declarado por el fabricante
  1) Activo, en comercializacion  2) En madurez, ya existe un sucesor  3) Anuncio de descontinuacion (phase-out)  4) Descontinuado, aun con soporte y repuestos  5) Descontinuado y sin soporte (fin de vida)  6) No se conoce

`M01 = `

**M04.** Se consiguen repuestos NUEVOS del fabricante o de un distribuidor autorizado?
  1) Si, sin problema  2) Si, pero con plazo largo  3) Solo por pedido especial  4) No  5) No se ha consultado

`M04 = `

**M06.** Plazo de entrega tipico de un repuesto critico (CPU o modulo)
  1) En existencia en la planta o local  2) Menos de 2 semanas  3) De 2 a 8 semanas  4) Mas de 8 semanas  5) No se consigue  6) No se conoce

`M06 = `

**M09.** Existe contrato de soporte o mantenimiento vigente con el fabricante o con un integrador?
  1) Si, vigente  2) Vencido  3) No  4) No se conoce

`M09 = `

**M07.** Existe servicio de reparacion para la CPU o los modulos?
  1) Si, del fabricante  2) Si, de tercero certificado  3) Si, de tercero sin certificar  4) No  5) No se conoce

`M07 = `

**F01.** Existe copia del programa del PLC?
  1) Si  2) No  3) No se conoce

`F01 = `

**F06.** El respaldo abre correctamente?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F06 = `

**F07.** Puede compilarse sin errores?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F07 = `

**F12.** La CPU esta operativa?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F12 = `

**F13.** Existe cable de programacion?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F13 = `

**N02.** Sistema operativo de esa PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Maquina virtual sobre un equipo moderno  7) Otro  8) No se conoce

`N02 = `

**N03.** Tipo de licencia del software de programacion
  1) Original con licencia vigente  2) Original con licencia vencida  3) Licencia flotante en servidor  4) Llave fisica (dongle)  5) Version de demostracion o limitada  6) No se tiene licencia  7) No se conoce

`N03 = `

**N05.** Se dispone del cable o adaptador de programacion correcto, con su driver instalado?
  1) Si, ya probado con este PLC  2) Si, pero sin probar  3) No  4) No se conoce

`N05 = `

**N06.** Se conocen las contrasenas del proyecto y de los bloques protegidos?
  1) Si, todas  2) Parcialmente  3) No  4) No hay contrasenas  5) No se conoce

`N06 = `

**G01.** Que redes utiliza la maquina?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Red propietaria  18) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`G01 = `

**O07.** En que lenguajes esta escrito el programa?
  1) Ladder (KOP / LD)  2) Bloques de funciones (FUP / FBD)  3) Lista de instrucciones (AWL / STL / IL)  4) Texto estructurado (SCL / ST)  5) GRAFCET, GRAPH o SFC  6) Bloques propietarios del fabricante de la maquina  7) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`O07 = `

**O08.** El programa usa bloques, librerias o funciones propietarias del fabricante de la maquina?
  1) Si  2) No  3) No se conoce

`O08 = `

**O02.** Existe control de movimiento, posicionamiento o ejes sincronizados (servos, levas electronicas, interpolacion)?
  1) Si  2) No  3) No se conoce

`O02 = `

**L01.** Cuantos paros no programados atribuibles al sistema de control ha tenido la maquina en los ultimos 12 meses?
  _escriba un numero_

`L01 = `

**L03.** Como ha evolucionado la frecuencia de fallas en los ultimos 24 meses?
  1) En aumento  2) Estable  3) En disminucion  4) Sin fallas registradas  5) No se lleva registro

`L03 = `

**L07.** La maquina pierde el programa, los datos o la hora al quitar la energia?
  1) Si  2) No  3) No se ha probado  4) No se conoce

`L07 = `

**P01.** Temperatura dentro del tablero de control
  1) Menor a 30 C  2) Entre 30 y 40 C  3) Entre 40 y 50 C  4) Mayor a 50 C  5) No se ha medido

`P01 = `

**P04.** Calidad de la energia electrica
  1) Variaciones frecuentes de tension  2) Cortes frecuentes  3) Presencia de armonicos  4) Sin UPS  5) Con UPS  6) Puesta a tierra verificada  7) Puesta a tierra dudosa o inexistente  8) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`P04 = `

---

## Caso 5

**Contexto:** Skid de proceso

**Situacion:** Skid con Quantum, E/S remota, lazos PID y comunicacion Modbus Plus.

### Cuestionario - Caso 5

**C08.** Criticidad de la maquina
  1) Baja: puede detenerse varios dias  2) Media: afecta parcialmente la produccion  3) Alta: afecta una linea importante  4) Critica: detiene la planta o presenta riesgo de seguridad

`C08 = `

**C10.** Tiempo maximo permitido de parada
  1) Menos de 1 hora  2) 1 a 4 horas  3) 4 a 12 horas  4) 12 a 24 horas  5) Mas de 24 horas

`C10 = `

**Q04.** Cuando puede intervenirse la maquina?
  1) Hay un paro programado ya definido  2) En el paro anual de planta o vacaciones  3) Fines de semana  4) En cualquier momento  5) No hay ventana disponible

`Q04 = `

**M01.** Estado del producto declarado por el fabricante
  1) Activo, en comercializacion  2) En madurez, ya existe un sucesor  3) Anuncio de descontinuacion (phase-out)  4) Descontinuado, aun con soporte y repuestos  5) Descontinuado y sin soporte (fin de vida)  6) No se conoce

`M01 = `

**M04.** Se consiguen repuestos NUEVOS del fabricante o de un distribuidor autorizado?
  1) Si, sin problema  2) Si, pero con plazo largo  3) Solo por pedido especial  4) No  5) No se ha consultado

`M04 = `

**M06.** Plazo de entrega tipico de un repuesto critico (CPU o modulo)
  1) En existencia en la planta o local  2) Menos de 2 semanas  3) De 2 a 8 semanas  4) Mas de 8 semanas  5) No se consigue  6) No se conoce

`M06 = `

**M09.** Existe contrato de soporte o mantenimiento vigente con el fabricante o con un integrador?
  1) Si, vigente  2) Vencido  3) No  4) No se conoce

`M09 = `

**M07.** Existe servicio de reparacion para la CPU o los modulos?
  1) Si, del fabricante  2) Si, de tercero certificado  3) Si, de tercero sin certificar  4) No  5) No se conoce

`M07 = `

**F01.** Existe copia del programa del PLC?
  1) Si  2) No  3) No se conoce

`F01 = `

**F06.** El respaldo abre correctamente?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F06 = `

**F07.** Puede compilarse sin errores?   *(responda solo si F01 = Si)*
  1) Si  2) No  3) No se conoce

`F07 = `

**F12.** La CPU esta operativa?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F12 = `

**F13.** Existe cable de programacion?   *(responda solo si F01 = No o No se conoce)*
  1) Si  2) No  3) No se conoce

`F13 = `

**N02.** Sistema operativo de esa PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Maquina virtual sobre un equipo moderno  7) Otro  8) No se conoce

`N02 = `

**N03.** Tipo de licencia del software de programacion
  1) Original con licencia vigente  2) Original con licencia vencida  3) Licencia flotante en servidor  4) Llave fisica (dongle)  5) Version de demostracion o limitada  6) No se tiene licencia  7) No se conoce

`N03 = `

**N05.** Se dispone del cable o adaptador de programacion correcto, con su driver instalado?
  1) Si, ya probado con este PLC  2) Si, pero sin probar  3) No  4) No se conoce

`N05 = `

**N06.** Se conocen las contrasenas del proyecto y de los bloques protegidos?
  1) Si, todas  2) Parcialmente  3) No  4) No hay contrasenas  5) No se conoce

`N06 = `

**G01.** Que redes utiliza la maquina?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Red propietaria  18) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`G01 = `

**O07.** En que lenguajes esta escrito el programa?
  1) Ladder (KOP / LD)  2) Bloques de funciones (FUP / FBD)  3) Lista de instrucciones (AWL / STL / IL)  4) Texto estructurado (SCL / ST)  5) GRAFCET, GRAPH o SFC  6) Bloques propietarios del fabricante de la maquina  7) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`O07 = `

**O08.** El programa usa bloques, librerias o funciones propietarias del fabricante de la maquina?
  1) Si  2) No  3) No se conoce

`O08 = `

**O02.** Existe control de movimiento, posicionamiento o ejes sincronizados (servos, levas electronicas, interpolacion)?
  1) Si  2) No  3) No se conoce

`O02 = `

**L01.** Cuantos paros no programados atribuibles al sistema de control ha tenido la maquina en los ultimos 12 meses?
  _escriba un numero_

`L01 = `

**L03.** Como ha evolucionado la frecuencia de fallas en los ultimos 24 meses?
  1) En aumento  2) Estable  3) En disminucion  4) Sin fallas registradas  5) No se lleva registro

`L03 = `

**L07.** La maquina pierde el programa, los datos o la hora al quitar la energia?
  1) Si  2) No  3) No se ha probado  4) No se conoce

`L07 = `

**P01.** Temperatura dentro del tablero de control
  1) Menor a 30 C  2) Entre 30 y 40 C  3) Entre 40 y 50 C  4) Mayor a 50 C  5) No se ha medido

`P01 = `

**P04.** Calidad de la energia electrica
  1) Variaciones frecuentes de tension  2) Cortes frecuentes  3) Presencia de armonicos  4) Sin UPS  5) Con UPS  6) Puesta a tierra verificada  7) Puesta a tierra dudosa o inexistente  8) No se conoce
  _puede marcar varias, separadas por coma (ej. 1,3)_

`P04 = `

---
