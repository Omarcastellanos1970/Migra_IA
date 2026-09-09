# -*- coding: utf-8 -*-
"""Genera data/procedimiento_migracion.json a partir del .docx de 50 pasos.

El titulo y el detalle de cada paso se toman LITERALES del documento: no se
reescriben aqui. Encima se anade una capa de anotaciones (fase, criterio de
salida, evidencia, rol, exigencias de seguridad, prerrequisitos y variantes)
que el documento no trae y que el agente necesita para poder guiar paso a paso.
Esa capa es PROPUESTA y esta marcada como tal en el JSON.

Ademas de los 50 pasos del documento se anaden los siete de la extension P1-P7
(construccion del programa), que el documento no cubre. La extension NO renumera
el original: lleva clave propia y queda marcada como tal.

El script valida antes de escribir: los 50 pasos del documento con su numeracion
1..50 intacta y sin duplicados, los 7 de la extension, que el orden de recorrido
cubra exactamente los pasos definidos, y que todo prerrequisito sea anterior EN
EL ORDEN DE RECORRIDO (no por numero: la extension se intercala tras el paso 20).

Uso:
    python _generar_procedimiento.py [ruta al .docx]
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

RAIZ = Path(__file__).resolve().parent
NOMBRE_DOCX = "Procedimiento_Migracion_PLC_CPU_50_Pasos.docx"
DESTINO = RAIZ / "data" / "procedimiento_migracion.json"


def ruta_docx() -> Path:
    """Localiza el documento fuente sin depender de rutas de una sola maquina.

    Orden de busqueda: el argumento de la linea de comandos; la carpeta
    `fuentes/` del repositorio, que es lo deseable para que el artefacto sea
    reproducible por cualquiera; y por ultimo la carpeta de descargas.
    """
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    candidatas = [RAIZ / "fuentes" / NOMBRE_DOCX,
                  Path.home() / "Downloads" / NOMBRE_DOCX]
    for c in candidatas:
        if c.exists():
            return c
    return candidatas[0]

TECNICO = "tecnico"
INGENIERIA = "ingenieria"
ESPECIALISTA = "especialista_seguridad"
RESPONSABLE = "responsable"


def req(aprobacion=False, detenida=False, loto=False, especialista=False) -> dict:
    return {
        "aprobacion_humana": aprobacion,
        "maquina_detenida": detenida,
        "loto": loto,
        "especialista_seguridad": especialista,
    }


# --------------------------------------------------------------------------- #
# Fases: agrupan los 50 pasos y los cruzan con las 6 etapas de la guia
# --------------------------------------------------------------------------- #
FASES = [
    {
        "id": "levantamiento",
        "nombre": "Levantamiento y aseguramiento de la evidencia",
        "pasos": list(range(1, 13)),
        "etapa_guia": "diagnostico",
        "proposito": "Saber que hay, asegurarlo y entenderlo antes de decidir nada.",
    },
    {
        "id": "seleccion_e_ingenieria",
        "nombre": "Seleccion de la CPU e ingenieria de la solucion",
        "pasos": list(range(13, 21)),
        "etapa_guia": "ingenieria",
        "proposito": "Elegir la plataforma destino y disenar la solucion completa en papel.",
    },
    {
        "id": "conversion",
        "nombre": "Conversion o reescritura del programa",
        "pasos": list(range(21, 31)),
        "etapa_guia": "construccion",
        "proposito": "Llevar la logica a la plataforma nueva y dejarla compilando y simulada.",
    },
    {
        "id": "fat",
        "nombre": "Pruebas de aceptacion en fabrica y plan de retorno",
        "pasos": list(range(31, 34)),
        "etapa_guia": "fat",
        "proposito": "Demostrar en banco que funciona, y tener como volver atras si falla.",
    },
    {
        "id": "corte_y_puesta_en_marcha",
        "nombre": "Corte, instalacion y puesta en marcha",
        "pasos": list(range(34, 45)),
        "etapa_guia": "corte_sat",
        "proposito": "Intervenir la maquina real, probar en campo y aceptar el sistema.",
    },
    {
        "id": "cierre",
        "nombre": "Documentacion, capacitacion y cierre",
        "pasos": list(range(45, 51)),
        "etapa_guia": "cierre",
        "proposito": "Dejar el sistema documentado, respaldado, entendido y formalmente aceptado.",
    },
]


# --------------------------------------------------------------------------- #
# Disparadores: cuando el agente pasa de diagnosticar a guiar
# --------------------------------------------------------------------------- #
DISPARADORES = [
    {
        "id": "cpu_obsoleta",
        "titulo": "CPU obsoleta o sin soporte",
        "descripcion": "La CPU o su familia estan descontinuadas, sin soporte del "
                       "fabricante, sin repuestos, o con un plazo de entrega mayor que "
                       "la parada tolerable.",
        "alternativa_mapa_decision": "Migracion a plataforma moderna",
        "origen": "usuario, 2026-08-29",
    },
    {
        "id": "contrasena_desconocida",
        "titulo": "Contrasena de la CPU desconocida",
        "descripcion": "La CPU esta protegida y nadie conoce la contrasena, de modo que "
                       "el programa no se puede leer ni modificar.",
        "alternativa_mapa_decision": "Reconstruccion del programa",
        "activa_variante": "sin_respaldo",
        "origen": "usuario, 2026-08-29",
    },
    {
        "id": "sin_acceso_al_programa",
        "titulo": "No se puede copiar ni abrir el programa anterior",
        "descripcion": "No hay respaldo, o el que hay no abre; falta el software, la "
                       "licencia o el adaptador de programacion; o el proyecto esta "
                       "corrupto o depende de bloques propietarios inaccesibles.",
        "alternativa_mapa_decision": "Reconstruccion del programa",
        "activa_variante": "sin_respaldo",
        "origen": "usuario, 2026-08-29",
    },
    {
        "id": "decision_del_usuario",
        "titulo": "El usuario decide cambiar la CPU",
        "descripcion": "Con o sin sugerencia del agente, el usuario resuelve migrar a "
                       "una CPU nueva. La decision es suya y el agente la acata.",
        "origen": "usuario, 2026-08-29",
    },
]


# --------------------------------------------------------------------------- #
# Opciones de CPU destino que el agente ofrece en el paso 13
# --------------------------------------------------------------------------- #
OPCIONES_CPU = {
    "paso": 13,
    "regla": "El agente PRESENTA las dos opciones y sus consecuencias. La eleccion "
             "es del usuario: un cambio de marca nunca es un supuesto del agente.",
    "opciones": [
        {
            "id": "misma_marca",
            "titulo": "CPU nueva del mismo fabricante",
            "que_ofrece": "La generacion actual del mismo fabricante, con los modelos "
                          "que el catalogo documenta y su fuente oficial. Cuando la guia "
                          "publica una ruta para la familia de origen, se usa esa ruta y "
                          "no una generica.",
            "a_favor": [
                "Existe herramienta oficial de conversion del programa (pasos 21 y 22)",
                "Se conserva el ecosistema: software, redes, repuestos y personal ya formado",
                "La matriz de equivalencia del paso 14 se hace modelo a modelo",
            ],
            "en_contra": [
                "Queda atado al mismo fabricante y a su politica de ciclo de vida",
            ],
            "soporte_de_datos": "Completo: las 30 marcas del catalogo tienen su "
                                "generacion actual documentada con modelos y fuente.",
        },
        {
            "id": "marca_alternativa",
            "titulo": "Plataforma actual de otra marca",
            "que_ofrece": "Las plataformas actuales de marcas alternativas a nivel de "
                          "FAMILIA, con sus modelos documentados y su fuente oficial.",
            "a_favor": [
                "Puede mejorar precio, disponibilidad local o soporte tecnico cercano",
                "Rompe la dependencia de un unico fabricante",
            ],
            "en_contra": [
                "No existe herramienta de conversion: el programa se reescribe completo",
                "Software, licencias y capacitacion nuevos, con su costo y su curva de aprendizaje",
                "Las redes de campo pueden necesitar conversion o pasarela",
                "Cambia el ecosistema de repuestos y el proveedor de servicio",
            ],
            "soporte_de_datos": "Parcial y declarado: el catalogo documenta que familias "
                                "actuales existen y con que modelos, pero NO publica "
                                "atributos comparables por modelo (memoria, E/S, tiempo de "
                                "ciclo, redes). Por eso el agente ofrece la comparacion a "
                                "nivel de plataforma y remite la seleccion del modelo exacto "
                                "a la herramienta oficial de seleccion del fabricante.",
            "limite_duro": "El agente NO afirma equivalencia modelo a modelo entre marcas "
                           "distintas, ni completa numeros de catalogo que el catalogo no "
                           "liste.",
        },
    ],
}


# --------------------------------------------------------------------------- #
# Extension: construccion del programa nuevo (pasos P1-P7)
# --------------------------------------------------------------------------- #
# El documento de 50 pasos cubre CONVERTIR un programa existente (pasos 21-23),
# pero no cubre ESCRIBIRLO. En la ruta de reconstruccion -sin respaldo, o con
# contrasena desconocida- y en el cambio de marca, los pasos 21 y 22 quedan como
# 'no aplica' y nada los sustituye: justo donde esta el trabajo, habia un hueco.
#
# Esta extension lo cierra. No renumera el documento original: los 50 pasos
# conservan su numero y su cita, y estos siete llevan etiqueta propia (P1-P7) y
# se declaran como extension posterior. Su contenido no se inventa: sale de los
# capitulos 6, 10 y 18 de la guia MIGRA-IA-GUIA-001, que ya lo tratan pero que el
# procedimiento no habia operacionalizado.
EXTENSION_PROGRAMA = [
    dict(etiqueta="P1", rol=INGENIERIA, prerreq=[6], origen="Guia MIGRA-IA-GUIA-001, cap. 6",
        titulo="Redactar la especificacion funcional independiente de la marca.",
        detalle="A partir de lo documentado en el paso 6, escribir que debe hacer la "
                "maquina sin referencia a marca ni a codigo: modos de operacion, "
                "secuencias, permisos, enclavamientos, alarmas, condiciones de arranque y "
                "paro, y estados seguros. Es el contrato contra el que se validara el "
                "sistema nuevo aunque cambie todo el codigo.",
        criterio="Documento funcional aprobado por operacion y mantenimiento, que describe "
                 "cada modo y cada secuencia sin nombrar hardware ni instrucciones.",
        evidencia=["Especificacion funcional firmada por produccion y por mantenimiento",
                   "Trazabilidad de cada funcion al paso 6 o a la observacion en planta"]),
    dict(etiqueta="P2", rol=INGENIERIA, prerreq=["P1"], origen="Guia MIGRA-IA-GUIA-001, cap. 6",
        titulo="Modelar formalmente la secuencia de control (GRAFCET/SFC; red de Petri en lo critico).",
        detalle="Traducir la especificacion a un modelo de estados y transiciones: etapas, "
                "condiciones de transicion, acciones asociadas, modos automatico y manual, "
                "paro de emergencia y recuperacion. Donde la secuencia sea critica o haya "
                "concurrencia entre subsistemas, levantar ademas la red de Petri y analizar "
                "bloqueos, alcanzabilidad y estados muertos ANTES de escribir una sola linea.",
        criterio="Modelo que cubre todos los modos declarados en P1, sin estados muertos ni "
                 "transiciones ambiguas. En las secuencias criticas, analisis de la red de "
                 "Petri sin bloqueos ni estados inalcanzables.",
        evidencia=["Diagrama GRAFCET/SFC por subsistema",
                   "Analisis de la red de Petri de las secuencias criticas, con conclusiones",
                   "Lista de estados seguros y como se alcanzan desde cualquier punto"],
        nota="Este modelo es tambien la referencia de aceptacion del paso 32: comparar el "
             "sistema nuevo contra un modelo formal es mas fuerte que compararlo contra una "
             "descripcion en prosa."),
    dict(etiqueta="P3", rol=INGENIERIA, prerreq=[13, "P2"], origen="Guia MIGRA-IA-GUIA-001, cap. 10",
        titulo="Definir la arquitectura del software.",
        detalle="Descomponer el programa por equipos y funciones, y fijar ANTES de codificar: "
                "convenciones de nombres, tipos de datos, variables retentivas, estructura de "
                "tareas, prioridades, tiempo de ciclo objetivo y watchdog.",
        criterio="Arquitectura escrita y revisada, con la lista de bloques y su "
                 "responsabilidad, las convenciones de nombres y la retentividad declarada.",
        evidencia=["Documento de arquitectura de software",
                   "Plantilla de nombres y tipos de datos acordada"],
        nota="Depende del paso 13: la plataforma destino condiciona tipos de datos, tareas y "
             "retentividad, asi que esta arquitectura no puede cerrarse antes de elegir la CPU."),
    dict(etiqueta="P4", rol=INGENIERIA, prerreq=[18, "P3"], origen="Guia MIGRA-IA-GUIA-001, cap. 10",
        titulo="Construir la lista de variables y enlazarla con el mapa de E/S.",
        detalle="Declarar cada variable con su tipo, rango, unidad, valor inicial y "
                "retentividad, y su correspondencia con la tabla de mapeo del paso 18. "
                "Ninguna E/S del paso 7 puede quedar sin variable, y ninguna variable sin origen.",
        criterio="Lista de variables completa y cuadrada contra el paso 18 en ambos sentidos.",
        evidencia=["Lista de variables exportada del proyecto",
                   "Comprobacion cruzada contra la tabla de mapeo del paso 18"]),
    dict(etiqueta="P5", rol=INGENIERIA, prerreq=["P4"], origen="Guia MIGRA-IA-GUIA-001, cap. 10",
        titulo="Escribir el programa por bloques, siguiendo el modelo.",
        detalle="Codificar cada bloque de la arquitectura implementando las etapas y "
                "transiciones del modelo. Cada bloque referencia la etapa o el requisito que "
                "realiza. No se improvisa logica que no este en la especificacion: si hace "
                "falta algo nuevo, se vuelve a P1 y se documenta antes de codificarlo.",
        criterio="Todos los bloques de la arquitectura escritos y compilando, con la "
                 "referencia al requisito o etapa que implementan.",
        evidencia=["Proyecto en control de versiones, con un commit por bloque o funcion",
                   "Matriz de trazabilidad requisito -> bloque"]),
    dict(etiqueta="P6", rol=INGENIERIA, prerreq=["P5"], origen="Guia MIGRA-IA-GUIA-001, cap. 18",
        titulo="Revisar el codigo con una persona distinta a quien lo escribio.",
        detalle="Revision dirigida a: logica critica, inicializacion y arranque en frio, "
                "estados seguros, manejo de fallos de comunicacion, y trazabilidad de cada "
                "bloque con su requisito.",
        criterio="Revision registrada, con cada hallazgo cerrado o aceptado de forma explicita.",
        evidencia=["Acta de revision de codigo con hallazgos y su resolucion"],
        nota="Si el programa toca funciones de seguridad, esta revision NO sustituye la "
             "validacion del especialista del paso 28."),
    dict(etiqueta="P7", rol=INGENIERIA, prerreq=["P6"], origen="Guia MIGRA-IA-GUIA-001, cap. 18",
        titulo="Probar cada bloque por separado antes de integrar.",
        detalle="Pruebas unitarias con entradas normales, valores limite, errores, perdida de "
                "comunicacion, arranque, parada, reset y recuperacion, en simulador o con "
                "senales forzadas en entorno controlado, documentando las limitaciones de la "
                "simulacion.",
        criterio="Cada bloque probado con su juego de casos y su resultado registrado; "
                 "ningun bloque llega a la integracion sin probar.",
        evidencia=["Registro de pruebas unitarias por bloque, con casos y resultados",
                   "Limitaciones de la simulacion declaradas"]),
]

# El bloque se recorre SIEMPRE, pero no cuesta lo mismo en las dos rutas.
PROFUNDIDAD = {
    "conversion": "RUTA DE CONVERSION (misma marca, con respaldo verificado): recorrido "
                  "ligero. P1 y P2 se hacen igualmente, porque son la referencia contra la "
                  "que se valida la conversion en el paso 32; P3 a P7 los cubre en gran parte "
                  "la herramienta oficial y los pasos 21 a 23, y aqui solo se comprueba que el "
                  "resultado cumple la arquitectura y la trazabilidad.",
    "reconstruccion": "RUTA DE RECONSTRUCCION O CAMBIO DE MARCA: recorrido completo. No hay "
                      "programa que convertir, asi que P1 a P7 son el trabajo principal y los "
                      "pasos 21 y 22 no aplican. Dimensionar el esfuerzo como desarrollo "
                      "nuevo, no como migracion.",
}


def orden_de_recorrido() -> list:
    """Claves de los pasos en el orden en que se recorren.

    La extension se intercala tras el paso 20 (configurar el hardware nuevo) y
    antes del 21 (convertir): es donde nace el programa, tanto si se convierte
    como si se escribe de cero.
    """
    return ([str(n) for n in range(1, 21)]
            + [p["etiqueta"] for p in EXTENSION_PROGRAMA]
            + [str(n) for n in range(21, 51)])


# --------------------------------------------------------------------------- #
# Huecos detectados en el documento: se declaran, NO se rellenan inventando
# --------------------------------------------------------------------------- #
HUECOS_DECLARADOS = [
    {
        "id": "construccion_del_programa",
        "descripcion": "Los pasos 21 a 23 asumen que existe un programa que convertir "
                       "('migrar con herramientas oficiales', 'revisar el reporte de "
                       "migracion'). Ningun paso cubre ESCRIBIR el programa nuevo. En la "
                       "ruta de reconstruccion -sin respaldo o con contrasena desconocida- "
                       "y en el cambio de marca, los pasos 21 y 22 quedan como 'no aplica' "
                       "y no los sustituia nada: el hueco caia justo donde esta el trabajo.",
        "estado": "CERRADO por la extension P1-P7 (construccion del programa), derivada de "
                  "los capitulos 6, 10 y 18 de la guia. Pendiente de validacion del autor.",
    },
    {
        "id": "compra_y_plazos",
        "descripcion": "Entre el paso 20 (configurar el hardware nuevo) y el 21 (migrar "
                       "el programa) no hay ningun paso de cotizacion, compra y recepcion "
                       "del hardware. En la practica el plazo de entrega es lo que fija la "
                       "fecha de la parada del paso 34. El BOM solo aparece en el paso 46, "
                       "como documentacion final.",
        "estado": "pendiente de decision del autor",
    },
    {
        "id": "cpu_bloqueada_sin_contrasena",
        "descripcion": "El paso 3 asume que el upload desde el PLC se puede hacer. No hay "
                       "ningun paso que cubra que hacer cuando la CPU esta protegida y la "
                       "contrasena se desconoce, que es justamente uno de los disparadores "
                       "de la migracion. Se cubre provisionalmente con la variante "
                       "'sin_respaldo' de los pasos 3, 5, 11, 21 y 22.",
        "estado": "cubierto por variante, pendiente de validacion del autor",
    },
    {
        "id": "roles_no_declarados",
        "descripcion": "El documento no dice quien ejecuta cada paso. El campo 'rol' es una "
                       "propuesta para que el agente pueda avisar cuando un paso excede al "
                       "tecnico de mantenimiento.",
        "estado": "propuesta, pendiente de validacion del autor",
    },
]


# --------------------------------------------------------------------------- #
# Capa de anotaciones por paso
# --------------------------------------------------------------------------- #
ANOTACIONES: dict[int, dict] = {
1: dict(rol=TECNICO, cubre="D, E, H, J",
    criterio="Ficha del sistema completa: marca, familia, modelo exacto, numero de parte y firmware de la CPU, mas el listado de modulos, racks, fuentes, redes, HMI/SCADA, variadores e instrumentos conectados.",
    evidencia=["Fotografia legible de la placa de la CPU y de cada modulo",
               "Numeros de parte transcritos tal como aparecen en el equipo, sin completar codigos"]),
2: dict(rol=TECNICO, cubre="M",
    criterio="Estado de ciclo de vida declarado por el fabricante para la CPU y los modulos (activo, en retirada o descontinuado), con disponibilidad de repuestos y plazo de entrega.",
    evidencia=["Cita de la fuente oficial del fabricante que declara el estado",
               "Plazo de entrega cotizado para los repuestos criticos"]),
3: dict(rol=TECNICO, cubre="F", requiere=req(aprobacion=True),
    criterio="Copia del proyecto original y, cuando fue posible, del upload directo desde el PLC, guardada con checksum y en al menos dos ubicaciones distintas.",
    evidencia=["Archivo de proyecto guardado con equipo y fecha en el nombre",
               "Checksum o tamano anotado en el expediente",
               "Ubicacion de las dos copias"],
    sin_respaldo="Si la CPU tiene contrasena desconocida, falta el software o el adaptador, o el upload falla: DETENERSE y escalar. No forzar el acceso. Registrar el caso como SIN RESPALDO VERIFICADO y continuar por la via de reconstruccion (pasos 6, 7 y 11), que es la alternativa 'Reconstruccion del programa' del mapa de decision."),
4: dict(rol=TECNICO, cubre="F, N",
    criterio="Nombre y version exacta del software de ingenieria y del firmware con los que el proyecto abre y compila.",
    evidencia=["Version anotada tal como la reporta el propio software",
               "Tipo de licencia y su forma de activacion"]),
5: dict(rol=TECNICO, cubre="F", prerreq=[3],
    criterio="El proyecto abre en un entorno independiente y compila sin errores, y su checksum coincide con el del paso 3. Un respaldo que no se puede verificar se trata como AUSENTE.",
    evidencia=["Resultado de la compilacion del respaldo",
               "Checksum verificado contra el del paso 3"],
    sin_respaldo="Si no abre, esta corrupto o no compila, NO se declara respaldo: se marca el caso como sin respaldo y se pasa a la via de reconstruccion."),
6: dict(rol=TECNICO, cubre="C",
    criterio="Descripcion escrita del funcionamiento real: secuencias automaticas, operacion manual, enclavamientos, permisos, alarmas, tiempos, setpoints, PID, recetas y condiciones de seguridad.",
    evidencia=["Documento de operacion validado por el operador de la maquina",
               "Registro del ciclo observado en planta"],
    nota="Cuando no hay respaldo, este paso deja de ser documentacion y pasa a ser la FUENTE PRINCIPAL para reconstruir el programa: su calidad determina la del sistema nuevo.",
    sin_respaldo="Es el paso mas importante de todo el procedimiento: sin programa de origen, la especificacion del sistema nuevo sale de aqui, de las entrevistas y de la observacion del ciclo."),
7: dict(rol=TECNICO, cubre="E",
    criterio="Tabla de E/S completa: direccion actual, tag, descripcion, tipo de senal y dispositivo de campo, sin filas incompletas.",
    evidencia=["Tabla de E/S levantada o exportada",
               "Contraste con el cableado real de al menos una muestra por tipo de senal"]),
8: dict(rol=TECNICO, cubre="G",
    criterio="Lista de todos los protocolos en uso, con el equipo que hay en cada extremo.",
    evidencia=["Inventario de interfaces y protocolos",
               "Fotografia de las tarjetas de comunicacion instaladas"]),
9: dict(rol=TECNICO, cubre="G",
    criterio="Mapa de red documentado: direcciones, mascaras, nombres, nodos, puertos, velocidades y topologia fisica.",
    evidencia=["Diagrama de red actualizado", "Tabla de direcciones y de nodos"]),
10: dict(rol=TECNICO, cubre="G, H",
    criterio="Lista de todos los sistemas que intercambian datos con la CPU, con el sentido del intercambio y su criticidad.",
    evidencia=["Matriz de dependencias externas",
               "Confirmacion del responsable de cada sistema conectado"]),
11: dict(rol=INGENIERIA, cubre="O", prerreq=[5],
    criterio="Bloques del programa clasificados por funcion, con los de seguridad y los protegidos o propietarios identificados aparte.",
    evidencia=["Inventario de bloques con su funcion",
               "Marcado de los bloques inaccesibles o protegidos"],
    sin_respaldo="Sin respaldo no hay programa que analizar: la clasificacion se sustituye por la logica levantada en los pasos 6 y 7, y el alcance de lo que NO se pudo recuperar se declara explicitamente en el expediente."),
12: dict(rol=INGENIERIA, cubre="O", prerreq=[11],
    criterio="Lista de instrucciones, bloques de sistema, direccionamiento y estructuras que la plataforma destino no soporta igual, cada una con su esfuerzo estimado.",
    evidencia=["Lista de incompatibilidades detectadas",
               "Referencia del manual del fabricante que sustenta cada una"],
    nota="Este paso se abre aqui pero solo se cierra despues del paso 13: hasta no fijar la CPU destino no se sabe que es lo que no soporta."),
13: dict(rol=INGENIERIA, decision_cpu=True, prerreq=[2, 7, 12],
    criterio="CPU destino elegida y justificada frente a memoria, velocidad, E/S, comunicaciones, conexiones, funciones tecnologicas y condiciones ambientales del caso, con su fuente oficial citada.",
    evidencia=["Comparacion documentada entre los requisitos del caso y las caracteristicas publicadas de la CPU candidata",
               "Verificacion en la herramienta oficial de seleccion del fabricante"],
    nota="Es el punto donde el agente ofrece las dos opciones: A) CPU de la generacion actual del MISMO fabricante, y B) plataformas actuales de marcas alternativas. La eleccion la hace el usuario, nunca el agente.",
    cambio_marca="Si el usuario elige otra marca, el agente presenta la generacion actual de las marcas alternativas a nivel de PLATAFORMA (familia, modelos documentados y fuente oficial). No afirma equivalencia modelo a modelo: el catalogo no publica atributos comparables y esa seleccion se cierra en la herramienta oficial del fabricante."),
14: dict(rol=INGENIERIA, prerreq=[7, 13],
    criterio="Matriz que relaciona cada CPU, modulo de E/S, modulo especial e interfaz antigua con su reemplazo y la accion necesaria (reemplazo directo, equivalente, adaptador, se conserva, se elimina), sin filas por definir.",
    evidencia=["Matriz de equivalencia de hardware completa"],
    cambio_marca="Entre marcas distintas la matriz deja de ser modelo a modelo: la equivalencia se establece por criterio funcional (tipo y numero de senales, rangos, redes, funciones especiales) y NUNCA por similitud de nombre o de referencia."),
15: dict(rol=INGENIERIA, prerreq=[7, 14],
    criterio="Cada tipo de senal verificado contra la tarjeta nueva: tension, corriente, PNP/NPN, aislamiento, resolucion, rango, tipo de sensor y tipo de salida.",
    evidencia=["Hoja de comparacion electrica por tipo de senal",
               "Identificacion de las senales que necesitan acondicionamiento o rele de interposicion"]),
16: dict(rol=INGENIERIA, prerreq=[14, 15],
    criterio="Lista de lo que se conserva y de lo que se sustituye, con la interfaz que lo hace posible en cada caso.",
    evidencia=["Decision documentada por dispositivo, con su justificacion"],
    nota="Los pasos 15 y 16 suelen obligar a revisar la seleccion del paso 13: la seleccion de CPU es iterativa, no un punto unico."),
17: dict(rol=INGENIERIA, prerreq=[16],
    criterio="Arquitectura destino definida: CPU, racks, E/S locales y remotas, redes, HMI, variadores y dispositivos externos, con su diagrama.",
    evidencia=["Diagrama de la arquitectura nueva",
               "Lista de materiales preliminar derivada del diagrama"]),
18: dict(rol=INGENIERIA, prerreq=[7, 17],
    criterio="Tabla de mapeo que relaciona cada direccion o tag antiguo con el nuevo, completa, sin duplicados y sin ninguna E/S del paso 7 fuera de la tabla.",
    evidencia=["Tabla de mapeo de antigua a nueva",
               "Comprobacion de cobertura contra la lista de E/S del paso 7"]),
19: dict(rol=INGENIERIA, prerreq=[17],
    criterio="Proyecto creado en la version correcta del software de ingenieria, con CPU, firmware, modulos y dispositivos agregados.",
    evidencia=["Proyecto nuevo creado y guardado",
               "Version de software y de firmware anotadas"],
    cambio_marca="Con cambio de marca esto implica software, licencias y capacitacion NUEVOS, no una version mas reciente del que ya se tiene. Presupuestar y planificar la formacion antes de llegar a este punto."),
20: dict(rol=INGENIERIA, prerreq=[19],
    criterio="Configuracion de hardware completa y compilable: rack, CPU, E/S locales y remotas, redes y dispositivos asociados.",
    evidencia=["Configuracion de hardware compilada sin errores"]),
21: dict(rol=INGENIERIA, prerreq=[5, 20],
    criterio="Programa pasado por la herramienta oficial de migracion del fabricante, con su reporte guardado y la version de la herramienta anotada.",
    evidencia=["Reporte de migracion archivado", "Version de la herramienta utilizada"],
    cambio_marca="NO APLICA. Entre fabricantes distintos no existe herramienta de conversion: el programa se REESCRIBE desde cero a partir de los pasos 6, 7, 11 y 18. Planificar el esfuerzo como desarrollo nuevo, no como conversion.",
    sin_respaldo="NO APLICA: sin programa de origen no hay nada que convertir. Se reescribe a partir de la logica levantada en los pasos 6 y 7."),
22: dict(rol=INGENIERIA, prerreq=[21],
    criterio="Cada mensaje del reporte clasificado como error, advertencia, funcion no soportada, conversion automatica o modificacion manual pendiente. No queda ningun mensaje sin revisar.",
    evidencia=["Reporte clasificado, con responsable y estado por mensaje"],
    cambio_marca="NO APLICA: no hay reporte de migracion. Su equivalente es la revision de la especificacion funcional reescrita contra lo documentado en el paso 6.",
    sin_respaldo="NO APLICA: no hay reporte. La verificacion se hace contra el paso 6."),
23: dict(rol=INGENIERIA, prerreq=[22],
    criterio="Todas las incompatibilidades del paso 22 resueltas y probadas; ninguna queda pendiente ni para revisar despues.",
    evidencia=["Registro de cada bloque reconstruido o instruccion sustituida",
               "Compilacion limpia tras cada correccion"]),
24: dict(rol=INGENIERIA, prerreq=[10, 23],
    criterio="Cada intercambio de datos del paso 10 reconstruido y verificado en la plataforma nueva.",
    evidencia=["Lista de intercambios probados con su resultado"]),
25: dict(rol=INGENIERIA, prerreq=[18, 23],
    criterio="Cada tag de pantalla apunta a una variable valida del PLC nuevo; el reporte de tags sin resolver queda en cero.",
    evidencia=["Reporte de tags sin resolver en cero", "Pantallas revisadas una por una"]),
26: dict(rol=INGENIERIA, prerreq=[15, 23],
    criterio="Para cada senal analogica, el valor en unidades de ingenieria coincide con el del sistema anterior dentro de la tolerancia acordada y declarada.",
    evidencia=["Tabla de comparacion de escalamiento por senal, con su tolerancia"]),
27: dict(rol=INGENIERIA, prerreq=[6, 23],
    criterio="Setpoints, limites, unidades y parametros de sintonizacion trasladados, con el comportamiento esperado documentado y las diferencias entre generaciones de bloques anotadas.",
    evidencia=["Tabla de parametros PID antes y despues",
               "Nota de las diferencias de comportamiento entre generaciones de bloques"]),
28: dict(rol=ESPECIALISTA, prerreq=[23], requiere=req(especialista=True),
    criterio="Funciones de seguridad validadas de forma INDEPENDIENTE por un especialista, segun el procedimiento de seguridad funcional aplicable, con su registro firmado.",
    evidencia=["Validacion firmada por el especialista de seguridad funcional",
               "Registro de las pruebas de seguridad"],
    nota="El agente NO da instrucciones operativas sobre funciones de seguridad: las identifica, advierte y deriva al especialista. Es una barrera dura del proyecto."),
29: dict(rol=INGENIERIA, prerreq=[23, 24, 25, 26, 27],
    criterio="Compilacion con cero errores; cada advertencia restante analizada y aceptada o resuelta, ninguna ignorada.",
    evidencia=["Salida de compilacion archivada", "Lista de advertencias con su decision"]),
30: dict(rol=INGENIERIA, prerreq=[29],
    criterio="Secuencias y logica probadas offline o en simulacion, con los desvios corregidos y SIN haber intervenido todavia la maquina real.",
    evidencia=["Registro de las pruebas de simulacion y su resultado"]),
31: dict(rol=INGENIERIA, prerreq=[30],
    criterio="Protocolo FAT escrito y aprobado, cubriendo arranque, paro, automatico, manual, alarmas, fallas, enclavamientos, secuencias, comunicaciones, PID y condiciones anormales, con la configuracion congelada.",
    evidencia=["Protocolo FAT aprobado", "Configuracion congelada e identificada"]),
32: dict(rol=INGENIERIA, prerreq=[31],
    criterio="Para cada prueba del protocolo hay un resultado esperado definido y un resultado obtenido registrado. No queda ninguna desviacion critica abierta.",
    evidencia=["Matriz de pruebas con esperado contra obtenido",
               "Registro de desviaciones clasificadas en critica, mayor y menor"],
    nota="Precision necesaria: la comparacion se hace contra el comportamiento DOCUMENTADO en el paso 6 y contra el programa de origen. No exige energizar las dos CPU a la vez, porque en planta la CPU antigua sigue en produccion hasta el corte."),
33: dict(rol=INGENIERIA, prerreq=[5, 32], bloqueante=True,
    criterio="Plan de retorno escrito, con la CPU original, su respaldo verificado y el cableado necesarios para revertir, y el tiempo estimado de reversion.",
    evidencia=["Plan de retorno aprobado",
               "Confirmacion de que la CPU original y su respaldo quedan disponibles"]),
34: dict(rol=RESPONSABLE, prerreq=[33], requiere=req(aprobacion=True),
    criterio="Ventana de parada autorizada por escrito, con fecha, duracion, personal, herramientas, respaldos, repuestos, responsabilidades y permisos de trabajo emitidos.",
    evidencia=["Autorizacion de parada firmada", "Permisos de trabajo emitidos"]),
35: dict(rol=TECNICO, prerreq=[3, 5, 33, 34], bloqueante=True,
    requiere=req(aprobacion=True, detenida=True, loto=True),
    criterio="Hardware instalado segun el diseno del paso 17, con la CPU original conservada e identificada para el plan de retorno.",
    evidencia=["Registro fotografico de la instalacion",
               "CPU original etiquetada y resguardada"],
    nota="PASO IRREVERSIBLE. No se ejecuta sin respaldo verificado (paso 5) y plan de retorno (paso 33). Si no hay respaldo, la reconstruccion debe estar validada antes de llegar aqui."),
36: dict(rol=TECNICO, prerreq=[35], requiere=req(detenida=True, loto=True),
    criterio="Alimentacion, polaridades, tierra, continuidad y conexiones verificadas con instrumento ANTES de energizar completamente.",
    evidencia=["Hoja de verificacion electrica firmada"]),
37: dict(rol=TECNICO, prerreq=[36],
    criterio="Configuracion de hardware y programa cargados en la CPU nueva, con IP o nombre de dispositivo asignados y comunicacion establecida.",
    evidencia=["Confirmacion de descarga sin errores", "Direccion o nombre asignado anotado"]),
38: dict(rol=TECNICO, prerreq=[18, 37], requiere=req(detenida=True),
    criterio="Cada entrada y cada salida accionada y comprobada contra su dispositivo de campo. Ninguna E/S queda sin probar.",
    evidencia=["Lista de E/S firmada punto por punto"]),
39: dict(rol=TECNICO, prerreq=[38],
    criterio="Cada actuador probado individualmente en manual, con su respuesta correcta y sus enclavamientos activos.",
    evidencia=["Registro de pruebas en manual por actuador"]),
40: dict(rol=TECNICO, prerreq=[39],
    criterio="Secuencia completa ejecutada en automatico, con todas las transiciones entre estados correctas.",
    evidencia=["Registro del ciclo automatico completo"]),
41: dict(rol=INGENIERIA, prerreq=[40], requiere=req(aprobacion=True, especialista=True),
    criterio="Cada condicion de falla prevista en el diseno provocada de forma controlada, con su respuesta verificada contra lo esperado.",
    evidencia=["Registro de las fallas provocadas y de la respuesta obtenida"],
    nota="Provocar fallas es una maniobra deliberada de riesgo: se hace en condiciones controladas, con el personal advertido y el area despejada. Para E-Stop y funciones de seguridad, con el especialista presente."),
42: dict(rol=RESPONSABLE, prerreq=[41],
    criterio="Sistema completo validado en campo bajo condiciones reales, con el protocolo SAT firmado y sin desviaciones criticas abiertas.",
    evidencia=["Protocolo SAT firmado por el responsable de la instalacion"]),
43: dict(rol=INGENIERIA, prerreq=[6, 42],
    criterio="Tiempos de ciclo, produccion, precision, tiempos de respuesta y alarmas comparados contra los del sistema anterior, sin deterioro no justificado.",
    evidencia=["Tabla de indicadores antes y despues, con la fuente de los valores anteriores"],
    nota="Los valores de antes deben venir del paso 6. Si no se registraron, la comparacion no es posible y hay que declararlo asi en lugar de estimarlos."),
44: dict(rol=INGENIERIA, prerreq=[43],
    criterio="Cada diferencia detectada corregida, documentada y vuelta a probar.",
    evidencia=["Registro de cambios del commissioning, con la prueba que valida cada uno"],
    nota="Es un lazo, no un paso lineal: cada correccion obliga a repetir las pruebas de los pasos 38 a 43 que se vean afectadas."),
45: dict(rol=INGENIERIA, prerreq=[44],
    criterio="Respaldo final que refleja exactamente lo que quedo funcionando, verificado abriendolo y compilandolo, con checksum y dos copias.",
    evidencia=["Proyecto as-built guardado y verificado", "Checksum anotado"]),
46: dict(rol=INGENIERIA, prerreq=[45],
    criterio="Planos electricos, arquitectura de red, lista de E/S, direcciones, BOM, manuales y diagramas actualizados al estado real instalado.",
    evidencia=["Documentacion as-built entregada"]),
47: dict(rol=INGENIERIA, prerreq=[46],
    criterio="Tabla de trazabilidad que relaciona cada elemento antiguo con el nuevo y las modificaciones de software que fueron necesarias.",
    evidencia=["Tabla de trazabilidad completa de la migracion"]),
48: dict(rol=RESPONSABLE, prerreq=[46],
    criterio="Operadores y mantenimiento capacitados en diagnostico, conexion, respaldo, recuperacion y diferencias de operacion, con registro de asistencia.",
    evidencia=["Registro de capacitacion firmado", "Material de consulta entregado"],
    cambio_marca="Con cambio de marca la capacitacion no es un tramite: el personal parte de cero en el software nuevo. Se dimensiona y se presupuesta desde el paso 13."),
49: dict(rol=INGENIERIA, prerreq=[45],
    criterio="Los tres proyectos conservados e identificados con fecha y version: Proyecto_original, Proyecto_migrado_pruebas y Proyecto_final_as-built.",
    evidencia=["Repositorio o carpeta de versiones con los tres proyectos"]),
50: dict(rol=RESPONSABLE, prerreq=[45, 46, 47, 48, 49], requiere=req(aprobacion=True),
    criterio="Cierre formal con documentacion as-built, resultados FAT y SAT, respaldos verificados y aceptacion firmada del responsable de la instalacion.",
    evidencia=["Acta de cierre firmada"]),
}


# --------------------------------------------------------------------------- #
# Lectura del .docx
# --------------------------------------------------------------------------- #
def parrafos(ruta: Path) -> list[str]:
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    salida = []
    for p in raiz.iter(W + "p"):
        partes = [n.text or "" for n in p.iter() if n.tag == W + "t"]
        texto = "".join(partes).strip()
        if texto:
            salida.append(texto)
    return salida


PATRON_PASO = re.compile(r"^(\d{1,2})\.\s+(.*)$")


def leer_documento(ruta: Path) -> dict:
    lineas = parrafos(ruta)
    doc = {"titulo": lineas[0], "subtitulo": lineas[1], "objetivo": "", "nota_aplicacion": ""}
    pasos: list[dict] = []
    actual: dict | None = None
    for linea in lineas[2:]:
        m = PATRON_PASO.match(linea)
        if m:
            actual = {"n": int(m.group(1)), "titulo": m.group(2).strip(), "detalle": ""}
            pasos.append(actual)
            continue
        if linea.lower().startswith("objetivo:"):
            doc["objetivo"] = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("nota de aplicaci"):
            doc["nota_aplicacion"] = linea.split(":", 1)[1].strip()
        elif actual is not None:
            actual["detalle"] = (actual["detalle"] + " " + linea).strip()
    doc["pasos"] = pasos
    return doc


# --------------------------------------------------------------------------- #
# Construccion y validacion
# --------------------------------------------------------------------------- #
def fase_de(n: int) -> dict:
    for f in FASES:
        if n in f["pasos"]:
            return f
    raise ValueError(f"El paso {n} no pertenece a ninguna fase")


def construir(doc: dict) -> dict:
    pasos = []
    for p in doc["pasos"]:
        n = p["n"]
        a = ANOTACIONES[n]
        f = fase_de(n)
        paso = {
            "clave": str(n),
            "n": n,
            "etiqueta": str(n),
            "titulo": p["titulo"],
            "detalle": p["detalle"],
            "fase": f["id"],
            "etapa_guia": f["etapa_guia"],
            "rol": a["rol"],
            "criterio_salida": a["criterio"],
            "evidencia": a["evidencia"],
            "prerrequisitos": [str(x) for x in a.get("prerreq", [])],
            "requiere": a.get("requiere", req()),
        }
        if a.get("cubre"):
            paso["cubierto_por_cuestionario"] = a["cubre"]
        if a.get("nota"):
            paso["nota_agente"] = a["nota"]
        if a.get("cambio_marca"):
            paso["variante_cambio_marca"] = a["cambio_marca"]
        if a.get("sin_respaldo"):
            paso["variante_sin_respaldo"] = a["sin_respaldo"]
        if a.get("bloqueante"):
            paso["bloqueante"] = True
        if a.get("decision_cpu"):
            paso["punto_de_decision_cpu"] = True
        pasos.append(paso)

    # Extension: los siete pasos de construccion del programa. Llevan etiqueta
    # propia y quedan marcados como extension para que nunca se confundan con el
    # documento original de 50 pasos ni alteren su numeracion.
    for e in EXTENSION_PROGRAMA:
        pasos.append({
            "clave": e["etiqueta"],
            "n": None,
            "etiqueta": e["etiqueta"],
            "titulo": e["titulo"],
            "detalle": e["detalle"],
            "fase": "construccion_del_programa",
            "etapa_guia": "construccion",
            "rol": e["rol"],
            "criterio_salida": e["criterio"],
            "evidencia": e["evidencia"],
            "prerrequisitos": [str(x) for x in e.get("prerreq", [])],
            "requiere": e.get("requiere", req()),
            "extension": "programa",
            "origen_metodologico": e["origen"],
            **({"nota_agente": e["nota"]} if e.get("nota") else {}),
        })
    return {
        "documento": {
            "id": "MIGRA-IA-PROC-050",
            "titulo": doc["titulo"],
            "subtitulo": doc["subtitulo"],
            "objetivo": doc["objetivo"],
            "nota_aplicacion": doc["nota_aplicacion"],
            "fuente": NOMBRE_DOCX,
            "total_pasos": len(pasos),
            "capa_anotada": {
                "descripcion": "El titulo y el detalle de cada paso son literales del "
                               "documento fuente. Los campos criterio_salida, evidencia, "
                               "rol, requiere, prerrequisitos, nota_agente, "
                               "variante_cambio_marca y variante_sin_respaldo son una "
                               "PROPUESTA de MIGRA-IA, pendiente de validacion del autor.",
                "campos_propuestos": ["fase", "etapa_guia", "rol", "criterio_salida",
                                      "evidencia", "prerrequisitos", "requiere",
                                      "cubierto_por_cuestionario", "nota_agente",
                                      "variante_cambio_marca", "variante_sin_respaldo",
                                      "bloqueante", "punto_de_decision_cpu"],
            },
        },
        "disparadores": DISPARADORES,
        "opciones_cpu_destino": OPCIONES_CPU,
        "fases": FASES + [{
            "id": "construccion_del_programa",
            "nombre": "Construccion del programa nuevo (extension P1-P7)",
            "pasos": [e["etiqueta"] for e in EXTENSION_PROGRAMA],
            "etapa_guia": "construccion",
            "proposito": "Especificar, modelar y escribir el programa. Es lo que el "
                         "documento original no cubria: sus pasos 21 a 23 asumen que ya "
                         "existe un programa que convertir.",
            "extension": True,
            "profundidad": PROFUNDIDAD,
        }],
        "orden": orden_de_recorrido(),
        "pasos": pasos,
        "huecos_declarados": HUECOS_DECLARADOS,
    }


def validar(datos: dict) -> list[str]:
    errores = []
    pasos = datos["pasos"]
    base = [p for p in pasos if not p.get("extension")]
    ext = [p for p in pasos if p.get("extension")]
    numeros = [p["n"] for p in base]

    # El documento original debe seguir intacto: 50 pasos, 1..50, sin renumerar.
    if len(base) != 50:
        errores.append(f"se esperaban 50 pasos del documento y hay {len(base)}")
    if sorted(numeros) != list(range(1, 51)):
        faltan = [i for i in range(1, 51) if i not in numeros]
        dup = sorted({i for i in numeros if numeros.count(i) > 1})
        errores.append(f"numeracion incorrecta; faltan {faltan}, duplicados {dup}")
    if len(ext) != len(EXTENSION_PROGRAMA):
        errores.append(f"se esperaban {len(EXTENSION_PROGRAMA)} pasos de extension "
                       f"y hay {len(ext)}")

    orden = datos["orden"]
    claves = {p["clave"] for p in pasos}
    if sorted(orden) != sorted(claves):
        errores.append("el orden de recorrido no coincide con los pasos definidos")
    posicion = {c: i for i, c in enumerate(orden)}

    for p in pasos:
        etq = p["etiqueta"]
        if not p["detalle"]:
            errores.append(f"paso {etq} sin detalle")
        if not p["criterio_salida"]:
            errores.append(f"paso {etq} sin criterio de salida")
        if not p["evidencia"]:
            errores.append(f"paso {etq} sin evidencia")
        for req_c in p["prerrequisitos"]:
            if req_c not in claves:
                errores.append(f"paso {etq}: prerrequisito {req_c} no existe")
            # La comparacion es por POSICION en el recorrido, no por numero: la
            # extension se intercala tras el 20, asi que P3 va antes que el 21.
            elif posicion[req_c] >= posicion[p["clave"]]:
                errores.append(f"paso {etq}: prerrequisito {req_c} no es anterior "
                               "en el orden de recorrido")

    cubiertos = sorted(str(n) for f in datos["fases"] for n in f["pasos"])
    if cubiertos != sorted(claves):
        errores.append("las fases no cubren exactamente los pasos definidos")
    if not any(p.get("punto_de_decision_cpu") for p in pasos):
        errores.append("ningun paso marcado como punto de decision de CPU")
    return errores


def main() -> int:
    docx = ruta_docx()
    if not docx.exists():
        print(f"No se encuentra el documento: {docx}")
        print("Pasa su ruta como argumento, o dejalo en la carpeta fuentes/ del repo.")
        return 1
    doc = leer_documento(docx)
    datos = construir(doc)
    errores = validar(datos)
    if errores:
        print("VALIDACION FALLIDA:")
        for e in errores:
            print("  -", e)
        return 1
    # El JSON se sigue manteniendo a mano despues de generarlo: las rutas por
    # fabricante, la ruta de cambio de marca y algunas variantes no salen del .docx y
    # este script no las produce. Regenerar encima las borraria en silencio, asi que
    # aqui se detiene y dice exactamente que se perderia.
    if DESTINO.exists():
        actual = json.loads(DESTINO.read_text(encoding="utf-8"))
        generados = {p["clave"]: p for p in datos["pasos"]}
        bloques = [k for k in actual if k not in datos]
        variantes = [
            p["clave"] for p in actual.get("pasos", [])
            if any(k.startswith("variante_") for k in p)
            and not any(k.startswith("variante_")
                        for k in generados.get(p["clave"], {}))
        ]
        if bloques or variantes:
            print("NO SE ESCRIBE NADA. El archivo actual tiene contenido que este script")
            print("no genera y que se perderia al regenerarlo:")
            if bloques:
                print("  bloques que solo existen en el archivo:", ", ".join(bloques))
            if variantes:
                print("  pasos con variantes anadidas a mano:", ", ".join(variantes))
            print("Llevalos a este script antes de regenerar, o escribe a otro archivo.")
            return 1
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK  {DESTINO}")
    print(f"    pasos: {len(datos['pasos'])}   fases: {len(datos['fases'])}"
          f"   disparadores: {len(datos['disparadores'])}")
    print(f"    con variante de cambio de marca: "
          f"{sum(1 for p in datos['pasos'] if 'variante_cambio_marca' in p)}")
    print(f"    con variante sin respaldo: "
          f"{sum(1 for p in datos['pasos'] if 'variante_sin_respaldo' in p)}")
    print(f"    que exigen aprobacion humana: "
          f"{sum(1 for p in datos['pasos'] if p['requiere']['aprobacion_humana'])}")
    print(f"    que exigen maquina detenida: "
          f"{sum(1 for p in datos['pasos'] if p['requiere']['maquina_detenida'])}")
    print(f"    que exigen especialista de seguridad: "
          f"{sum(1 for p in datos['pasos'] if p['requiere']['especialista_seguridad'])}")
    print(f"    bloqueantes: {[p['n'] for p in datos['pasos'] if p.get('bloqueante')]}")
    print(f"    tamano: {DESTINO.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
