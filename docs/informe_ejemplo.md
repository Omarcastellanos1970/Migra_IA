# Diagnostico interactivo — Siemens SIMATIC S7-300

- Caso: CAS-2026-506650
- Agente: MIGRA-IA v0.3.0
- Fecha: 2026-09-04T20:05:06-06:00
- Nivel de confianza global: confianza_media
- Aprobacion humana: PENDIENTE (este informe es una asistencia tecnica; debe ser verificado por personal autorizado antes de intervenir).

---

## 1. Identificacion
Caso interactivo. Siemens SIMATIC S7-300 (CPU 315-2 DP).

## 2. Resumen ejecutivo
Diagnostico construido sobre las respuestas dadas por el usuario en la demo interactiva, con el motor de riesgo y el mapa de decision reales.

## 3. Informacion confirmada
24 respuestas registradas: C08, C10, F01, F12, F13, G01, L01, L03, L07, M01, M04, M06, M07, M09, N02, N03, N05, N06, O02, O07, O08, P01, P04, Q04.

## 4. Informacion no confirmada
Todas las respuestas provienen de la declaracion del usuario; ninguna esta verificada contra placa, manual ni fuente oficial.

## 5. Datos faltantes
Ninguno registrado.

## 6. Estado y puntuacion de obsolescencia
85.0 / 100 — **Riesgo critico**.

- Estado del ciclo de vida (peso 0.20): 75 — M01: estado declarado por el fabricante = 'Descontinuado, aun con soporte y repuestos'.
- Disponibilidad de repuestos (peso 0.15): 85 — M04: 'Solo por pedido especial'. M06 'De 2 a 8 semanas' frente a C10 '4 a 12 horas': el repuesto llega despues de lo que la linea tolera, asi que la estrategia de repuesto no cubre el riesgo por si sola.
- Soporte del fabricante (peso 0.15): 90 — M09 contrato de soporte: 'No'; M07 servicio de reparacion: 'Si, de tercero sin certificar'.
- Disponibilidad del software (peso 0.10): 95 — Barrera de acceso al programa: N02 sistema operativo 'Windows 7'; N03 licencia 'Llave fisica (dongle)'; N05 adaptador 'Si, pero sin probar'; N06 contrasenas 'No'.
- Disponibilidad de respaldo (peso 0.15): 100 — F01: no existe copia del programa. Prioridad 1: recuperarlo antes de cualquier decision.
- Compatibilidad con sistemas actuales (peso 0.10): 75 — Cuanto arrastra el cambio: G01 redes de generacion anterior (MPI, Profibus DP); O07 incluye lista de instrucciones (AWL/STL), sin conversion automatica garantizada; O08 usa librerias propietarias.
- Historial de fallas (peso 0.05): 55 — L01 6 paros no programados en 12 meses; L03 tendencia 'En aumento'; CAUSA RAIZ EXTERNA no corregida (P01 temperatura del tablero 'Entre 40 y 50 C'; P04 puesta a tierra dudosa o inexistente; P04 calidad de energia deficiente; L07 la maquina pierde el programa, los datos o la hora sin energia (bateria o respaldo de memoria agotado)): estas fallas no son atribuibles al controlador, asi que el factor se limita. Corregirla es previo a cualquier sustitucion.
- Criticidad productiva (peso 0.10): 90 — C08 criticidad 'Alta: afecta una linea importante'; C10 parada tolerable '4 a 12 horas'; Q04 ventana de intervencion 'En el paro anual de planta o vacaciones'.

## 7. Riesgos
Los que se desprenden de los factores anteriores.

## 8. Alternativas
1. **Correccion de causa raiz (sin cambiar el controlador)** — Se evalua PRIMERO porque hay causa raiz externa sin corregir: P01 temperatura del tablero 'Entre 40 y 50 C'; P04 puesta a tierra dudosa o inexistente; P04 calidad de energia deficiente; L07 la maquina pierde el programa, los datos o la hora sin energia (bateria o respaldo de memoria agotado). Sustituir el controlador sin corregirla reproduce la falla en el equipo nuevo.
2. **Reconstruccion del programa** — No hay respaldo verificado (F01/F06/F07) y no hay via para leer el programa del PLC (N05/N06/F13): el programa debe reconstruirse a partir del levantamiento funcional.
3. **Migracion a plataforma moderna** — M01 'Descontinuado, aun con soporte y repuestos' y M06 con plazo mayor que la parada tolerable: el repuesto no cubre el riesgo, y la obsolescencia no se revierte reparando.

## 9. Recomendacion principal
Migrar a **Siemens S7-1500 / S7-1500R/H segun necesidad** (misma marca: conversion con herramienta oficial)

## 10. Hardware preliminar
Sin numeros de catalogo confirmados: deben verificarse con el fabricante y su herramienta oficial de seleccion.

## 11. Plan de respaldo, migracion y retorno
Procedimiento MIGRA-IA-PROC-050, avance 57 de 57 pasos (50 del documento mas la extension P1-P7 de construccion del programa).

## 12. Plan de pruebas
FAT (pasos 31-33) y SAT (pasos 42-44) del procedimiento.

## 13. Nivel de confianza y fuentes
Confianza media. Fuentes: respuestas del usuario y catalogo verificado de fabricantes. Este informe procede de una demostracion interactiva determinista, sin intervencion de un modelo de lenguaje.