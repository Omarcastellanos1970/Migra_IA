# Baseline reproducible: riesgo ordinal y prioridad de reemplazo

Generado por `_baseline.py`. Reproducible: misma entrada, misma salida,
sin clave de API y sin dependencias de terceros en el calculo.

```
==========================================================================
BASELINE REPRODUCIBLE: RIESGO ORDINAL Y PRIORIDAD DE REEMPLAZO
==========================================================================
Fecha de referencia fija: 2026-09-04. Semilla declarada: 42.
Subproblema cubierto: P1 (riesgo ordinal). P2 ver seccion 7.

1. CONJUNTO DE DATOS
--------------------------------------------------------------------------
  Archivo   : data/ciclo_vida_plataformas.csv
  Origen    : Tabla 2 de 'tabla de frecuencias' (fila agregada MEDIA excluida)
  Muestras  : 9 plataformas
  Marcas    : 5 fabricantes
  Clases    : 2 presentes de 4 definidas en la escala
     1. Activo, en comercializacion                   n=0   <-- SIN NINGUNA MUESTRA
     2. Anuncio de descontinuacion (phase-out)        n=0   <-- SIN NINGUNA MUESTRA
     3. Descontinuado, aun con soporte y repuestos    n=6
     4. Descontinuado y sin soporte (fin de vida)     n=3

  Balance   : clase 3: 6 / clase 4: 3

  SESGO DE SELECCION, declarado: la tabla se construyo para documentar
  descontinuaciones, asi que solo contiene plataformas ya descontinuadas.
  No hay ni una muestra de las clases 1 y 2. Un clasificador entrenado aqui
  no puede aprender a reconocer una plataforma vigente, y el modelo ordinal
  degenera de hecho en binario: con dos clases solo queda un corte.

  Conversion de fechas (para auditar celda a celda):
     PLC-5 (1785)                       lanz 1986  antig 40  clase 4
        Anuncio_fin_de_vida          dia primero (dia>12, sin ambiguedad)
        Fin_comercializacion         mmm-aa (aa<50 -> 20aa)
        Fin_repuestos_reparacion     dia primero (dia>12, sin ambiguedad)
     SLC 500                            lanz 1991  antig 35  clase 3
        Anuncio_fin_de_vida          vacio o n.d.
        Fin_comercializacion         dia primero (dia>12, sin ambiguedad)
        Fin_repuestos_reparacion     vacio o n.d.
     S7-300 / ET 200M                   lanz 1995  antig 31  clase 3
        Anuncio_fin_de_vida          AMBIGUA dd/mm vs mm/dd; se aplica dia primero, como el resto de la tabla
        Fin_comercializacion         AMBIGUA dd/mm vs mm/dd; se aplica dia primero, como el resto de la tabla
        Fin_repuestos_reparacion     AMBIGUA dd/mm vs mm/dd; se aplica dia primero, como el resto de la tabla
     Modicon Quantum                    lanz 1994  antig 32  clase 3
        Anuncio_fin_de_vida          mmm-aa (aa<50 -> 20aa)
        Fin_comercializacion         dia primero (dia>12, sin ambiguedad)
        Fin_repuestos_reparacion     vacio o n.d.
     Modicon Premium                    lanz 1996  antig 30  clase 3
        Anuncio_fin_de_vida          mmm-aa (aa<50 -> 20aa)
        Fin_comercializacion         solo anio (se asume 1 de enero)
        Fin_repuestos_reparacion     vacio o n.d.
     MELSEC-A/QnA (tipo grande)         lanz 1985  antig 41  clase 4
        Anuncio_fin_de_vida          vacio o n.d.
        Fin_comercializacion         mmm-aa (aa<50 -> 20aa)
        Fin_repuestos_reparacion     mm-aaaa
     MELSEC AnS/QnAS                    lanz 1993  antig 33  clase 4
        Anuncio_fin_de_vida          vacio o n.d.
        Fin_comercializacion         mmm-aa (aa<50 -> 20aa)
        Fin_repuestos_reparacion     mm-aaaa
     SYSMAC CS1                         lanz 1999  antig 27  clase 3
        Anuncio_fin_de_vida          AMBIGUA dd/mm vs mm/dd; se aplica dia primero, como el resto de la tabla
        Fin_comercializacion         mm-aaaa (se toma la primera de dos fechas)
        Fin_repuestos_reparacion     mmm-aa (aa<50 -> 20aa)
     SYSMAC CJ1 (Europa)                lanz 2001  antig 25  clase 3
        Anuncio_fin_de_vida          dia primero (dia>12, sin ambiguedad)
        Fin_comercializacion         mmm-aa (aa<50 -> 20aa)
        Fin_repuestos_reparacion     solo anio (se asume 1 de enero)

  Datos faltantes: 5 plataformas con alguna fecha ausente
     SLC 500: Anuncio_fin_de_vida, Fin_repuestos_reparacion
     Modicon Quantum: Fin_repuestos_reparacion
     Modicon Premium: Fin_repuestos_reparacion
     MELSEC-A/QnA (tipo grande): Anuncio_fin_de_vida
     MELSEC AnS/QnAS: Anuncio_fin_de_vida

2. PARTICION
--------------------------------------------------------------------------
  Esquema   : leave-one-manufacturer-out
  Agrupa por: Fabricante (dos plataformas de una marca comparten politica
              de soporte; repartirlas dejaria que el modelo la reconozca)
  Guardada  : data/particion_ciclo_vida.json
  Pliegues  : 5
     [0] prueba = Mitsubishi   (2 muestra/s)  entrenamiento = 7
     [1] prueba = Omron        (2 muestra/s)  entrenamiento = 7
     [2] prueba = Rockwell     (2 muestra/s)  entrenamiento = 7
     [3] prueba = Schneider    (2 muestra/s)  entrenamiento = 7
     [4] prueba = Siemens      (1 muestra/s)  entrenamiento = 8

3 y 4. BASELINES, MISMA PARTICION Y MISMAS METRICAS
--------------------------------------------------------------------------
  B0 trivial : clase mayoritaria del pliegue de entrenamiento. Sin variables.
  B1 clasico : regresion logistica ordinal (probabilidades proporcionales)
               sobre antiguedad, el modelo asignado al rubro.
               L2=1.0, paso=0.05, iteraciones=4000, inicio en ceros.

                exactitud   F1 macro   err. ordinal
  B0 trivial        0.667      0.400          0.333
  B1 clasico        0.778      0.679          0.222

  Coeficientes por pliegue (esto es lo que un ingeniero puede auditar):
     pliegue de prueba     beta   cortes
     Mitsubishi        0.642   [1.938]
     Omron             0.700   [0.307]
     Rockwell          0.701   [1.002]
     Schneider         0.721   [0.323]
     Siemens           0.771   [0.578]

     beta positivo = mas antiguedad empuja hacia clases mas altas, que es el
     sentido esperado. La pendiente esta en unidades de desviacion tipica de
     la antiguedad del propio pliegue, no en anios.

  Prediccion por plataforma:
     plataforma                         rubro         antig  real   B0   B1
     MELSEC-A/QnA (tipo grande)         Mitsubishi       41     4    3    3
     MELSEC AnS/QnAS                    Mitsubishi       33     4    3    3
     SYSMAC CS1                         Omron            27     3    3    3
     SYSMAC CJ1 (Europa)                Omron            25     3    3    3
     PLC-5 (1785)                       Rockwell         40     4    3    4
     SLC 500                            Rockwell         35     3    3    3
     Modicon Quantum                    Schneider        32     3    3    3
     Modicon Premium                    Schneider        30     3    3    3
     S7-300 / ET 200M                   Siemens          31     3    3    3

  LECTURA: el clasico supera al trivial en las tres metricas o en parte de
  ellas. Con nueve filas la diferencia NO es estadisticamente sostenible:
  cada acierto vale 0.111 de exactitud. Sirve como indicio de que la
  antiguedad lleva senal, no como evidencia de que el modelo funcione.

5. SEMILLA Y VERSIONES
--------------------------------------------------------------------------
  Semilla declarada : 42
  Uso real          : NINGUNO. No hay paso estocastico: el ajuste arranca en
                      ceros, el paso y las iteraciones son fijos y no hay
                      barajado ni muestreo. La reproducibilidad no depende de
                      la semilla, y por eso se dice en vez de sugerir que si.
  Python            : 3.14.6 (Windows)
  Dependencias del calculo: ninguna de terceros (biblioteca estandar)
  Entorno congelado : 25 paquetes
     Flask==3.1.3
     Jinja2==3.1.6
     MarkupSafe==3.0.3
     Werkzeug==3.1.8
     annotated-types==0.7.0
     anthropic==0.117.0
     anyio==4.14.2
     blinker==1.9.0
     certifi==2026.6.17
     click==8.4.2
     colorama==0.4.6
     distro==1.9.0
     docstring_parser==0.18.0
     h11==0.16.0
     httpcore==1.0.9
     httpx==0.28.1
     idna==3.18
     itsdangerous==2.2.0
     jiter==0.16.0
     pydantic==2.13.4
     pydantic_core==2.46.4
     python-dotenv==1.2.2
     sniffio==1.3.1
     typing-inspection==0.4.2
     typing_extensions==4.16.0

6. AUDITORIA DE FUGA DE DATOS
--------------------------------------------------------------------------
  [EXCLUIDA] Vida_comercial_anios
      identidad verificada en 9 de 9 filas: Vida_comercial_anios =
      anio(fin_comercializacion) - Lanzamiento. La fecha de la que se
      deriva es una de las que definen la etiqueta, asi que la columna es
      la etiqueta escrita de otra forma.
  [EXCLUIDA] Soporte_total_anios
      identidad verificada en 6 de 6 filas: Soporte_total_anios =
      anio(fin_repuestos) - Lanzamiento. La fecha de la que se deriva es
      una de las que definen la etiqueta, asi que la columna es la
      etiqueta escrita de otra forma.
  [EXCLUIDAS] Anuncio_fin_de_vida / Fin_comercializacion / Fin_repuestos_reparacion
      son las columnas con las que se deriva la clase. Usarlas como
      variable seria predecir la etiqueta con la etiqueta.
  [EXCLUIDA] Nivel
      mide cuan verificado esta el dato contra la fuente (A/B/C), no una
      propiedad del equipo. Es metadato del proceso de recoleccion: si
      entrara, el modelo aprenderia el habito documental del fabricante.
  [EXCLUIDA como variable] Fabricante
      es la variable de agrupamiento. En leave-one-manufacturer-out la
      marca de prueba nunca aparece en entrenamiento, asi que como
      variable no es utilizable: solo sirve para formar los pliegues.
  [ADMITIDA] Lanzamiento -> antiguedad
      es anterior a cualquier evento de fin de vida y esta disponible en
      la placa del equipo. Unica variable que sobrevive a la auditoria.

  RESULTADO: de las columnas disponibles sobrevive 1.
  El conjunto admite exactamente una variable no contaminada. Ese es el
  hallazgo, y condiciona todo lo anterior: el clasico no tuvo mas remedio
  que ser univariante.

  Fuera de esta tabla, en el banco de casos del artefacto:
     - Los escenarios de desarrollo 'critico' y 'otra_marca' comparten las
       mismas 24 respuestas: son 2 casos independientes, no 3.
     - 'critico' (S7-300 -> S7-1500) reproduce la ruta del caso ciego 26.1,
       y el destino de 'otra_marca' (Omron NX) la del caso ciego 26.5:
       el conjunto de desarrollo pisa el de prueba.
     - En modo agente con API, la herramienta consultar_guia alcanza
       data/base_conocimiento.json, que contiene los cinco casos ciegos con
       su estrategia. En modo determinista no: interactivo.py no importa
       conocimiento. La fuga existe y depende del modo.

7. P2 PRIORIDAD DE REEMPLAZO - NO EVALUABLE TODAVIA
--------------------------------------------------------------------------
  El clasico asignado a P2 es gradient boosting en modo ranking. No se
  ejecuta, y la razon no es tecnica sino de datos: un modelo de ranking
  necesita un orden de referencia -que plataforma debe reemplazarse antes
  que cual- y ese orden no existe en ninguna fuente del proyecto.

  Derivarlo de la puntuacion del propio motor seria circular: el modelo
  aprenderia a reproducir la formula que se pretende evaluar.

  Lo que hace falta para desbloquearlo, en orden de coste:
     1. Un orden de prioridad por juicio experto sobre estas 9 plataformas,
        emitido por los coautores sin ver la salida del motor. Es el mismo
        procedimiento de _plantilla_ciega.py y se puede pedir en una sesion.
     2. Ampliar la tabla de ciclo de vida a las 130 generaciones del
        catalogo, que es lo que daria un conjunto donde el boosting tenga
        sentido. Trabajo de extraccion y verificacion en fuentes oficiales.
```
