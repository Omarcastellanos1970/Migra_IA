# Verificacion interna del motor MIGRA-IA

Generado por `_evaluacion.py`. Reproducible: mismas respuestas, mismos numeros, sin clave de API.

Semilla Monte Carlo: `42` - muestras: `5000`.

```
==========================================================================
VERIFICACION INTERNA DEL MOTOR - MIGRA-IA
==========================================================================
Sin clave de API, sin datos de campo. Determinista y reproducible.

0. ANCLAJE CONTRA ARTIFACT.md
--------------------------------------------------------------------------
  OK       critico        85.0  esperado 85.0  (Riesgo critico)
  OK       sano           11.8  esperado 11.8  (Riesgo bajo)

1. BASELINE vs PROPUESTA
--------------------------------------------------------------------------
  caso           B0 trivial   B1 uniforme   propuesta   decision
  critico              75.0          83.1        85.0   migrar
  sano                 10.0          11.9        11.8   no migrar
  otra_marca           75.0          83.1        85.0   migrar

  Los pesos de la Seccion 6 SI cambian el resultado frente a pesos
  uniformes en: critico (83.1 vs 85.0), sano (11.9 vs 11.8), otra_marca (83.1 vs 85.0)

2. SENSIBILIDAD DE LOS PESOS
--------------------------------------------------------------------------
  [critico]  base = 85.0 (Riesgo critico)
    estado_ciclo_vida          peso 0.20  -50%:  86.1  -20%:  85.4  +20%:  84.6  +50%:  84.1
    disponibilidad_repuestos   peso 0.15  -50%:  85.0  -20%:  85.0  +20%:  85.0  +50%:  85.0
    soporte_fabricante         peso 0.15  -50%:  84.6  -20%:  84.8  +20%:  85.1  +50%:  85.3
    disponibilidad_software    peso 0.10  -50%:  84.5  -20%:  84.8  +20%:  85.2  +50%:  85.5
    disponibilidad_respaldo    peso 0.15  -50%:  83.8  -20%:  84.5  +20%:  85.4  +50%:  86.0
    compatibilidad_sistemas    peso 0.10  -50%:  85.5  -20%:  85.2  +20%:  84.8  +50%:  84.5
    historial_fallas           peso 0.05  -50%:  85.8  -20%:  85.3  +20%:  84.7  +50%:  84.3
    criticidad_productiva      peso 0.10  -50%:  84.7  -20%:  84.9  +20%:  85.1  +50%:  85.2
    Monte Carlo (5000 muestras, pesos x U(0.5,1.5) renormalizados):
      puntuacion 81.3 .. 88.6   media 85.0   sd 1.1
      la clasificacion se mantiene en 100.0% de las muestras

  [sano]  base = 11.8 (Riesgo bajo)
    estado_ciclo_vida          peso 0.20  -50%:  11.9  -20%:  11.8  +20%:  11.7  +50%:  11.6
    disponibilidad_repuestos   peso 0.15  -50%:  11.9  -20%:  11.8  +20%:  11.7  +50%:  11.6
    soporte_fabricante         peso 0.15  -50%:  12.7  -20%:  12.1  +20%:  11.4  +50%:  10.9
    disponibilidad_software    peso 0.10  -50%:  11.3  -20%:  11.6  +20%:  11.9  +50%:  12.1
    disponibilidad_respaldo    peso 0.15  -50%:  11.5  -20%:  11.6  +20%:  11.8  +50%:  12.0
    compatibilidad_sistemas    peso 0.10  -50%:  11.3  -20%:  11.6  +20%:  11.9  +50%:  12.1
    historial_fallas           peso 0.05  -50%:  12.1  -20%:  11.9  +20%:  11.6  +50%:  11.5
    criticidad_productiva      peso 0.10  -50%:  11.3  -20%:  11.6  +20%:  11.9  +50%:  12.1
    Monte Carlo (5000 muestras, pesos x U(0.5,1.5) renormalizados):
      puntuacion 9.3 .. 13.9   media 11.8   sd 0.71
      la clasificacion se mantiene en 100.0% de las muestras

3. INFLUENCIA DE CADA PREGUNTA (escenario 'critico')
--------------------------------------------------------------------------
  cod     rango     min     max  pregunta
  M01      17.0    72.0    89.0  Estado del producto declarado por el fabri
  M09      11.2    73.8    85.0  Existe contrato de soporte o mantenimiento
  C08       6.0    80.0    86.0  Criticidad de la maquina
  M07       4.5    82.0    86.5  Existe servicio de reparacion para la CPU 
  F01       4.5    80.5    85.0  Existe copia del programa del PLC?
  M06       3.0    82.0    85.0  Plazo de entrega tipico de un repuesto cri
  N06       3.0    82.0    85.0  Se conocen las contrasenas del proyecto y 
  G01       3.0    83.5    86.5  Que redes utiliza la maquina?
  N02       2.5    83.0    85.5  Sistema operativo de esa PC
  O08       2.5    82.5    85.0  El programa usa bloques, librerias o funci
  C10       2.0    84.0    86.0  Tiempo maximo permitido de parada
  N03       2.0    83.5    85.5  Tipo de licencia del software de programac

  Sin efecto sobre la puntuacion: F12, F13, L03, L07, P01, P04
  (no implica que sean inutiles: ver seccion 4, pueden mover la ruta)

4. INFLUENCIA SOBRE LA RUTA DE DECISION
--------------------------------------------------------------------------
  Una pregunta puede no mover el numero y aun asi cambiar la recomendacion.
  [critico] ruta base: Correccion de causa raiz (sin cambiar el controlador) > Reconstruccion del programa > Migracion a plataforma moderna
    cambian la ruta: Q04 (2 rutas), M01 (4 rutas), M06 (2 rutas), F01 (2 rutas)
    no mueven ni puntuacion ni ruta: F12, F13, L03, L07, P01, P04
  [sano] ruta base: Reparacion del equipo existente
    cambian la ruta: Q04 (2 rutas), M01 (4 rutas), F01 (2 rutas), F06 (2 rutas), F07 (2 rutas), L07 (2 rutas), P01 (2 rutas), P04 (2 rutas)
    no mueven ni puntuacion ni ruta: ninguna

5. MONOTONIA SOBRE ESCALAS ORDINALES (escenario 'critico')
--------------------------------------------------------------------------
  [M01] riesgo debe subir
    72.0 -> 76.0 -> 81.0 -> 85.0 -> 89.0
    sin violaciones
  [M06] riesgo debe subir
    82.0 -> 82.0 -> 85.0 -> 85.0 -> 85.0
    sin violaciones
  [C10] riesgo debe bajar
    86.0 -> 85.5 -> 85.0 -> 84.5 -> 84.0
    sin violaciones

6. MARGEN HASTA EL UMBRAL MAS CERCANO (20/40/60/80)
--------------------------------------------------------------------------
  critico        85.0 (Riesgo critico) a 5.0 puntos del umbral 80
  sano           11.8 (Riesgo bajo) a 8.2 puntos del umbral 20
  otra_marca     85.0 (Riesgo critico) a 5.0 puntos del umbral 80

7. RELACION ENTRE LA PUNTUACION Y LA DECISION
--------------------------------------------------------------------------
  Se fuerza la puntuacion a los extremos dejando las respuestas intactas.
    puntuacion real    (Riesgo critico) -> migrar = True
    forzada a 0        (Riesgo bajo) -> migrar = True
    forzada a 100      (Riesgo critico) -> migrar = True

```
