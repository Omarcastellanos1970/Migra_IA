# Diagnostico de obsolescencia y plan de migracion — CPU Siemens S7-300 315-2 DP (DEMO)

- Caso: CAS-2026-904335
- Agente: MIGRA-IA v0.1.0
- Fecha: 2026-07-20T12:29:04-06:00
- Nivel de confianza global: confianza_media
- Aprobacion humana: PENDIENTE (este informe es una asistencia tecnica; debe ser verificado por personal autorizado antes de intervenir).

---

## 1. Identificacion
Caso de demostracion. CPU Siemens S7-300 315-2 DP.

## 2. Resumen ejecutivo
CPU en fin de ciclo de vida, con falla intermitente y sin respaldo verificado del programa. Riesgo de obsolescencia alto. Se recomienda recuperar el respaldo y migrar a S7-1500.

## 3. Informacion confirmada
CPU 315-2 DP; falla intermitente; Profibus DP/MPI; criticidad alta.

## 4. Informacion no confirmada / supuestos
Probable ausencia de respaldo; repuestos escasos.

## 5. Datos faltantes
Respaldo del programa sin verificar; memoria utilizada; lista completa de modulos; version de firmware; funciones especiales.

## 6. Estado y puntuacion de obsolescencia
Riesgo alto (ver puntuacion ponderada en el expediente, motor de la Seccion 6).

## 7. Riesgos
Tecnico: falla de CPU sin respaldo. Productivo: parada de linea critica. Seguridad: revision obligatoria por especialista (bandera activa).

## 8. Alternativas
(1) Operacion temporal controlada; (2) repuesto directo; (3) hardware equivalente; (4) migracion a S7-1500; (5) reconstruccion.

## 9. Recomendacion principal
Prioridad 1: recuperar el respaldo. Luego migrar a S7-1500 conservando Profibus DP.

## 10. Equivalencias preliminares (a verificar con el fabricante)
CPU S7-300 315-2 DP -> familia S7-1500 con Profibus DP (p. ej. CPU 1516-3 PN/DP o CM 1542-5); modulos S7-300 -> ET 200MP/ET 200SP; STEP 7 Classic -> TIA Portal. NO se confirman numeros de catalogo: deben verificarse oficialmente.

## 11. Plan de respaldo, migracion y retorno
Respaldo verificado -> levantamiento -> arquitectura destino -> mapa de senales -> conversion en TIA Portal -> BOM preliminar -> plan de retorno (conservar CPU original).

## 12. Plan de pruebas
FAT en banco con simulacion de E/S; SAT en ventana de parada con pruebas de seguridad por especialista.

## 13. Nivel de confianza y fuentes
Confianza media. Fuentes: declaracion verbal del tecnico (pendiente de evidencias: placa, respaldo, lista de E/S).
