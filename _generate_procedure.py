# -*- coding: utf-8 -*-
"""Genera data/es/migration_procedure.json a partir del .docx de 50 pasos.

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

ROOT = Path(__file__).resolve().parent
DOCX_NAME = "Procedimiento_Migracion_PLC_CPU_50_Pasos.docx"
TARGET = ROOT / "data" / "es" / "migration_procedure.json"


def docx_path() -> Path:
    """Localiza el documento fuente sin depender de rutas de una sola maquina.

    Orden de busqueda: el argumento de la linea de comandos; la carpeta
    `fuentes/` del repositorio, que es lo deseable para que el artefacto sea
    reproducible por cualquiera; y por ultimo la carpeta de descargas.
    """
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    candidatas = [ROOT / "sources" / DOCX_NAME,
                  Path.home() / "Downloads" / DOCX_NAME]
    for c in candidatas:
        if c.exists():
            return c
    return candidatas[0]

TECHNICIAN = "tecnico"
ENGINEERING = "ingenieria"
SPECIALIST = "safety_specialist"
MANAGER = "responsable"


def req(approval=False, detenida=False, loto=False, especialista=False) -> dict:
    return {
        "human_approval": approval,
        "machine_stopped": detenida,
        "loto": loto,
        "safety_specialist": especialista,
    }


# --------------------------------------------------------------------------- #
# Fases: agrupan los 50 pasos y los cruzan con las 6 etapas de la guia
# --------------------------------------------------------------------------- #
PHASES = [
    {
        "id": "levantamiento",
        "name": "Levantamiento y aseguramiento de la evidencia",
        "steps": list(range(1, 13)),
        "guide_stage": "diagnostico",
        "purpose": "Saber que hay, asegurarlo y entenderlo antes de decidir nada.",
    },
    {
        "id": "seleccion_e_ingenieria",
        "name": "Seleccion de la CPU e ingenieria de la solucion",
        "steps": list(range(13, 21)),
        "guide_stage": "ingenieria",
        "purpose": "Elegir la plataforma destino y disenar la solucion completa en papel.",
    },
    {
        "id": "conversion",
        "name": "Conversion o reescritura del programa",
        "steps": list(range(21, 31)),
        "guide_stage": "construccion",
        "purpose": "Llevar la logica a la plataforma nueva y dejarla compilando y simulada.",
    },
    {
        "id": "fat",
        "name": "Pruebas de aceptacion en fabrica y plan de retorno",
        "steps": list(range(31, 34)),
        "guide_stage": "fat",
        "purpose": "Demostrar en banco que funciona, y tener como volver atras si falla.",
    },
    {
        "id": "corte_y_puesta_en_marcha",
        "name": "Corte, instalacion y puesta en marcha",
        "steps": list(range(34, 45)),
        "guide_stage": "corte_sat",
        "purpose": "Intervenir la maquina real, probar en campo y aceptar el sistema.",
    },
    {
        "id": "cierre",
        "name": "Documentacion, capacitacion y cierre",
        "steps": list(range(45, 51)),
        "guide_stage": "cierre",
        "purpose": "Dejar el sistema documentado, respaldado, entendido y formalmente aceptado.",
    },
]


# --------------------------------------------------------------------------- #
# Disparadores: cuando el agente pasa de diagnosticar a guiar
# --------------------------------------------------------------------------- #
DISPARADORES = [
    {
        "id": "cpu_obsoleta",
        "title": "CPU obsoleta o sin soporte",
        "description": "La CPU o su familia estan descontinuadas, sin soporte del "
                       "fabricante, sin repuestos, o con un plazo de entrega mayor que "
                       "la parada tolerable.",
        "decision_map_alternative": "Migracion a plataforma moderna",
        "origin": "usuario, 2026-08-29",
    },
    {
        "id": "contrasena_desconocida",
        "title": "Contrasena de la CPU desconocida",
        "description": "La CPU esta protegida y nadie conoce la contrasena, de modo que "
                       "el programa no se puede leer ni modificar.",
        "decision_map_alternative": "Reconstruccion del programa",
        "activates_variant": "without_backup",
        "origin": "usuario, 2026-08-29",
    },
    {
        "id": "sin_acceso_al_programa",
        "title": "No se puede copiar ni abrir el programa anterior",
        "description": "No hay respaldo, o el que hay no abre; falta el software, la "
                       "licencia o el adaptador de programacion; o el proyecto esta "
                       "corrupto o depende de bloques propietarios inaccesibles.",
        "decision_map_alternative": "Reconstruccion del programa",
        "activates_variant": "without_backup",
        "origin": "usuario, 2026-08-29",
    },
    {
        "id": "decision_del_usuario",
        "title": "El usuario decide cambiar la CPU",
        "description": "Con o sin sugerencia del agente, el usuario resuelve migrar a "
                       "una CPU nueva. La decision es suya y el agente la acata.",
        "origin": "usuario, 2026-08-29",
    },
]


# --------------------------------------------------------------------------- #
# Opciones de CPU destino que el agente ofrece en el paso 13
# --------------------------------------------------------------------------- #
CPU_OPTIONS = {
    "step": 13,
    "rule": "El agente PRESENTA las dos opciones y sus consecuencias. La eleccion "
             "es del usuario: un cambio de marca nunca es un supuesto del agente.",
    "options": [
        {
            "id": "misma_marca",
            "title": "CPU nueva del mismo fabricante",
            "what_it_offers": "La generacion actual del mismo fabricante, con los modelos "
                          "que el catalogo documenta y su fuente oficial. Cuando la guia "
                          "publica una ruta para la familia de origen, se usa esa ruta y "
                          "no una generica.",
            "pros": [
                "Existe herramienta oficial de conversion del programa (pasos 21 y 22)",
                "Se conserva el ecosistema: software, redes, repuestos y personal ya formado",
                "La matriz de equivalencia del paso 14 se hace modelo a modelo",
            ],
            "cons": [
                "Queda atado al mismo fabricante y a su politica de ciclo de vida",
            ],
            "data_support": "Completo: las 30 marcas del catalogo tienen su "
                                "generacion actual documentada con modelos y fuente.",
        },
        {
            "id": "marca_alternativa",
            "title": "Plataforma actual de otra marca",
            "what_it_offers": "Las plataformas actuales de marcas alternativas a nivel de "
                          "FAMILIA, con sus modelos documentados y su fuente oficial.",
            "pros": [
                "Puede mejorar precio, disponibilidad local o soporte tecnico cercano",
                "Rompe la dependencia de un unico fabricante",
            ],
            "cons": [
                "No existe herramienta de conversion: el programa se reescribe completo",
                "Software, licencias y capacitacion nuevos, con su costo y su curva de aprendizaje",
                "Las redes de campo pueden necesitar conversion o pasarela",
                "Cambia el ecosistema de repuestos y el proveedor de servicio",
            ],
            "data_support": "Parcial y declarado: el catalogo documenta que familias "
                                "actuales existen y con que modelos, pero NO publica "
                                "atributos comparables por modelo (memoria, E/S, tiempo de "
                                "ciclo, redes). Por eso el agente ofrece la comparacion a "
                                "nivel de plataforma y remite la seleccion del modelo exacto "
                                "a la herramienta oficial de seleccion del fabricante.",
            "hard_limit": "El agente NO afirma equivalencia modelo a modelo entre marcas "
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
    dict(label="P1", role=ENGINEERING, prereq=[6], origin="Guia MIGRA-IA-GUIA-001, cap. 6",
        title="Redactar la especificacion funcional independiente de la marca.",
        detail="A partir de lo documentado en el paso 6, escribir que debe hacer la "
                "maquina sin referencia a marca ni a codigo: modos de operacion, "
                "secuencias, permisos, enclavamientos, alarmas, condiciones de arranque y "
                "paro, y estados seguros. Es el contrato contra el que se validara el "
                "sistema nuevo aunque cambie todo el codigo.",
        criterion="Documento funcional aprobado por operacion y mantenimiento, que describe "
                 "cada modo y cada secuencia sin nombrar hardware ni instrucciones.",
        evidence=["Especificacion funcional firmada por produccion y por mantenimiento",
                   "Trazabilidad de cada funcion al paso 6 o a la observacion en planta"]),
    dict(label="P2", role=ENGINEERING, prereq=["P1"], origin="Guia MIGRA-IA-GUIA-001, cap. 6",
        title="Modelar formalmente la secuencia de control (GRAFCET/SFC; red de Petri en lo critico).",
        detail="Traducir la especificacion a un modelo de estados y transiciones: etapas, "
                "condiciones de transicion, acciones asociadas, modos automatico y manual, "
                "paro de emergencia y recuperacion. Donde la secuencia sea critica o haya "
                "concurrencia entre subsistemas, levantar ademas la red de Petri y analizar "
                "bloqueos, alcanzabilidad y estados muertos ANTES de escribir una sola linea.",
        criterion="Modelo que cubre todos los modos declarados en P1, sin estados muertos ni "
                 "transiciones ambiguas. En las secuencias criticas, analisis de la red de "
                 "Petri sin bloqueos ni estados inalcanzables.",
        evidence=["Diagrama GRAFCET/SFC por subsistema",
                   "Analisis de la red de Petri de las secuencias criticas, con conclusiones",
                   "Lista de estados seguros y como se alcanzan desde cualquier punto"],
        note="Este modelo es tambien la referencia de aceptacion del paso 32: comparar el "
             "sistema nuevo contra un modelo formal es mas fuerte que compararlo contra una "
             "descripcion en prosa."),
    dict(label="P3", role=ENGINEERING, prereq=[13, "P2"], origin="Guia MIGRA-IA-GUIA-001, cap. 10",
        title="Definir la arquitectura del software.",
        detail="Descomponer el programa por equipos y funciones, y fijar ANTES de codificar: "
                "convenciones de nombres, tipos de datos, variables retentivas, estructura de "
                "tareas, prioridades, tiempo de ciclo objetivo y watchdog.",
        criterion="Arquitectura escrita y revisada, con la lista de bloques y su "
                 "responsabilidad, las convenciones de nombres y la retentividad declarada.",
        evidence=["Documento de arquitectura de software",
                   "Plantilla de nombres y tipos de datos acordada"],
        note="Depende del paso 13: la plataforma destino condiciona tipos de datos, tareas y "
             "retentividad, asi que esta arquitectura no puede cerrarse antes de elegir la CPU."),
    dict(label="P4", role=ENGINEERING, prereq=[18, "P3"], origin="Guia MIGRA-IA-GUIA-001, cap. 10",
        title="Construir la lista de variables y enlazarla con el mapa de E/S.",
        detail="Declarar cada variable con su tipo, rango, unidad, valor inicial y "
                "retentividad, y su correspondencia con la tabla de mapeo del paso 18. "
                "Ninguna E/S del paso 7 puede quedar sin variable, y ninguna variable sin origen.",
        criterion="Lista de variables completa y cuadrada contra el paso 18 en ambos sentidos.",
        evidence=["Lista de variables exportada del proyecto",
                   "Comprobacion cruzada contra la tabla de mapeo del paso 18"]),
    dict(label="P5", role=ENGINEERING, prereq=["P4"], origin="Guia MIGRA-IA-GUIA-001, cap. 10",
        title="Escribir el programa por bloques, siguiendo el modelo.",
        detail="Codificar cada bloque de la arquitectura implementando las etapas y "
                "transiciones del modelo. Cada bloque referencia la etapa o el requisito que "
                "realiza. No se improvisa logica que no este en la especificacion: si hace "
                "falta algo nuevo, se vuelve a P1 y se documenta antes de codificarlo.",
        criterion="Todos los bloques de la arquitectura escritos y compilando, con la "
                 "referencia al requisito o etapa que implementan.",
        evidence=["Proyecto en control de versiones, con un commit por bloque o funcion",
                   "Matriz de trazabilidad requisito -> bloque"]),
    dict(label="P6", role=ENGINEERING, prereq=["P5"], origin="Guia MIGRA-IA-GUIA-001, cap. 18",
        title="Revisar el codigo con una persona distinta a quien lo escribio.",
        detail="Revision dirigida a: logica critica, inicializacion y arranque en frio, "
                "estados seguros, manejo de fallos de comunicacion, y trazabilidad de cada "
                "bloque con su requisito.",
        criterion="Revision registrada, con cada hallazgo cerrado o aceptado de forma explicita.",
        evidence=["Acta de revision de codigo con hallazgos y su resolucion"],
        note="Si el programa toca funciones de seguridad, esta revision NO sustituye la "
             "validacion del especialista del paso 28."),
    dict(label="P7", role=ENGINEERING, prereq=["P6"], origin="Guia MIGRA-IA-GUIA-001, cap. 18",
        title="Probar cada bloque por separado antes de integrar.",
        detail="Pruebas unitarias con entradas normales, valores limite, errores, perdida de "
                "comunicacion, arranque, parada, reset y recuperacion, en simulador o con "
                "senales forzadas en entorno controlado, documentando las limitaciones de la "
                "simulacion.",
        criterion="Cada bloque probado con su juego de casos y su resultado registrado; "
                 "ningun bloque llega a la integracion sin probar.",
        evidence=["Registro de pruebas unitarias por bloque, con casos y resultados",
                   "Limitaciones de la simulacion declaradas"]),
]

# El bloque se recorre SIEMPRE, pero no cuesta lo mismo en las dos rutas.
DEPTH = {
    "conversion": "RUTA DE CONVERSION (misma marca, con respaldo verificado): recorrido "
                  "ligero. P1 y P2 se hacen igualmente, porque son la referencia contra la "
                  "que se valida la conversion en el paso 32; P3 a P7 los cubre en gran parte "
                  "la herramienta oficial y los pasos 21 a 23, y aqui solo se comprueba que el "
                  "resultado cumple la arquitectura y la trazabilidad.",
    "rebuild": "RUTA DE RECONSTRUCCION O CAMBIO DE MARCA: recorrido completo. No hay "
                      "programa que convertir, asi que P1 a P7 son el trabajo principal y los "
                      "pasos 21 y 22 no aplican. Dimensionar el esfuerzo como desarrollo "
                      "nuevo, no como migracion.",
}


def traversal_order() -> list:
    """Claves de los pasos en el orden en que se recorren.

    La extension se intercala tras el paso 20 (configurar el hardware nuevo) y
    antes del 21 (convertir): es donde nace el programa, tanto si se convierte
    como si se escribe de cero.
    """
    return ([str(n) for n in range(1, 21)]
            + [p["label"] for p in EXTENSION_PROGRAMA]
            + [str(n) for n in range(21, 51)])


# --------------------------------------------------------------------------- #
# Huecos detectados en el documento: se declaran, NO se rellenan inventando
# --------------------------------------------------------------------------- #
HUECOS_DECLARADOS = [
    {
        "id": "construccion_del_programa",
        "description": "Los pasos 21 a 23 asumen que existe un programa que convertir "
                       "('migrar con herramientas oficiales', 'revisar el reporte de "
                       "migracion'). Ningun paso cubre ESCRIBIR el programa nuevo. En la "
                       "ruta de reconstruccion -sin respaldo o con contrasena desconocida- "
                       "y en el cambio de marca, los pasos 21 y 22 quedan como 'no aplica' "
                       "y no los sustituia nada: el hueco caia justo donde esta el trabajo.",
        "status": "CERRADO por la extension P1-P7 (construccion del programa), derivada de "
                  "los capitulos 6, 10 y 18 de la guia. Pendiente de validacion del autor.",
    },
    {
        "id": "compra_y_plazos",
        "description": "Entre el paso 20 (configurar el hardware nuevo) y el 21 (migrar "
                       "el programa) no hay ningun paso de cotizacion, compra y recepcion "
                       "del hardware. En la practica el plazo de entrega es lo que fija la "
                       "fecha de la parada del paso 34. El BOM solo aparece en el paso 46, "
                       "como documentacion final.",
        "status": "pendiente de decision del autor",
    },
    {
        "id": "cpu_bloqueada_sin_contrasena",
        "description": "El paso 3 asume que el upload desde el PLC se puede hacer. No hay "
                       "ningun paso que cubra que hacer cuando la CPU esta protegida y la "
                       "contrasena se desconoce, que es justamente uno de los disparadores "
                       "de la migracion. Se cubre provisionalmente con la variante "
                       "'without_backup' de los pasos 3, 5, 11, 21 y 22.",
        "status": "cubierto por variante, pendiente de validacion del autor",
    },
    {
        "id": "roles_no_declarados",
        "description": "El documento no dice quien ejecuta cada paso. El campo 'role' es una "
                       "propuesta para que el agente pueda avisar cuando un paso excede al "
                       "tecnico de mantenimiento.",
        "status": "propuesta, pendiente de validacion del autor",
    },
]


# --------------------------------------------------------------------------- #
# Capa de anotaciones por paso
# --------------------------------------------------------------------------- #
ANNOTATIONS: dict[int, dict] = {
1: dict(role=TECHNICIAN, covers="D, E, H, J",
    criterion="Ficha del sistema completa: marca, familia, modelo exacto, numero de parte y firmware de la CPU, mas el listado de modulos, racks, fuentes, redes, HMI/SCADA, variadores e instrumentos conectados.",
    evidence=["Fotografia legible de la placa de la CPU y de cada modulo",
               "Numeros de parte transcritos tal como aparecen en el equipo, sin completar codigos"]),
2: dict(role=TECHNICIAN, covers="M",
    criterion="Estado de ciclo de vida declarado por el fabricante para la CPU y los modulos (activo, en retirada o descontinuado), con disponibilidad de repuestos y plazo de entrega.",
    evidence=["Cita de la fuente oficial del fabricante que declara el estado",
               "Plazo de entrega cotizado para los repuestos criticos"]),
3: dict(role=TECHNICIAN, covers="F", requires=req(approval=True),
    criterion="Copia del proyecto original y, cuando fue posible, del upload directo desde el PLC, guardada con checksum y en al menos dos ubicaciones distintas.",
    evidence=["Archivo de proyecto guardado con equipo y fecha en el nombre",
               "Checksum o tamano anotado en el expediente",
               "Ubicacion de las dos copias"],
    without_backup="Si la CPU tiene contrasena desconocida, falta el software o el adaptador, o el upload falla: DETENERSE y escalar. No forzar el acceso. Registrar el caso como SIN RESPALDO VERIFICADO y continuar por la via de reconstruccion (pasos 6, 7 y 11), que es la alternativa 'Reconstruccion del programa' del mapa de decision."),
4: dict(role=TECHNICIAN, covers="F, N",
    criterion="Nombre y version exacta del software de ingenieria y del firmware con los que el proyecto abre y compila.",
    evidence=["Version anotada tal como la reporta el propio software",
               "Tipo de licencia y su forma de activacion"]),
5: dict(role=TECHNICIAN, covers="F", prereq=[3],
    criterion="El proyecto abre en un entorno independiente y compila sin errores, y su checksum coincide con el del paso 3. Un respaldo que no se puede verificar se trata como AUSENTE.",
    evidence=["Resultado de la compilacion del respaldo",
               "Checksum verificado contra el del paso 3"],
    without_backup="Si no abre, esta corrupto o no compila, NO se declara respaldo: se marca el caso como sin respaldo y se pasa a la via de reconstruccion."),
6: dict(role=TECHNICIAN, covers="C",
    criterion="Descripcion escrita del funcionamiento real: secuencias automaticas, operacion manual, enclavamientos, permisos, alarmas, tiempos, setpoints, PID, recetas y condiciones de seguridad.",
    evidence=["Documento de operacion validado por el operador de la maquina",
               "Registro del ciclo observado en planta"],
    note="Cuando no hay respaldo, este paso deja de ser documentacion y pasa a ser la FUENTE PRINCIPAL para reconstruir el programa: su calidad determina la del sistema nuevo.",
    without_backup="Es el paso mas importante de todo el procedimiento: sin programa de origen, la especificacion del sistema nuevo sale de aqui, de las entrevistas y de la observacion del ciclo."),
7: dict(role=TECHNICIAN, covers="E",
    criterion="Tabla de E/S completa: direccion actual, tag, descripcion, tipo de senal y dispositivo de campo, sin filas incompletas.",
    evidence=["Tabla de E/S levantada o exportada",
               "Contraste con el cableado real de al menos una muestra por tipo de senal"]),
8: dict(role=TECHNICIAN, covers="G",
    criterion="Lista de todos los protocolos en uso, con el equipo que hay en cada extremo.",
    evidence=["Inventario de interfaces y protocolos",
               "Fotografia de las tarjetas de comunicacion instaladas"]),
9: dict(role=TECHNICIAN, covers="G",
    criterion="Mapa de red documentado: direcciones, mascaras, nombres, nodos, puertos, velocidades y topologia fisica.",
    evidence=["Diagrama de red actualizado", "Tabla de direcciones y de nodos"]),
10: dict(role=TECHNICIAN, covers="G, H",
    criterion="Lista de todos los sistemas que intercambian datos con la CPU, con el sentido del intercambio y su criticidad.",
    evidence=["Matriz de dependencias externas",
               "Confirmacion del responsable de cada sistema conectado"]),
11: dict(role=ENGINEERING, covers="O", prereq=[5],
    criterion="Bloques del programa clasificados por funcion, con los de seguridad y los protegidos o propietarios identificados aparte.",
    evidence=["Inventario de bloques con su funcion",
               "Marcado de los bloques inaccesibles o protegidos"],
    without_backup="Sin respaldo no hay programa que analizar: la clasificacion se sustituye por la logica levantada en los pasos 6 y 7, y el alcance de lo que NO se pudo recuperar se declara explicitamente en el expediente."),
12: dict(role=ENGINEERING, covers="O", prereq=[11],
    criterion="Lista de instrucciones, bloques de sistema, direccionamiento y estructuras que la plataforma destino no soporta igual, cada una con su esfuerzo estimado.",
    evidence=["Lista de incompatibilidades detectadas",
               "Referencia del manual del fabricante que sustenta cada una"],
    note="Este paso se abre aqui pero solo se cierra despues del paso 13: hasta no fijar la CPU destino no se sabe que es lo que no soporta."),
13: dict(role=ENGINEERING, decision_cpu=True, prereq=[2, 7, 12],
    criterion="CPU destino elegida y justificada frente a memoria, velocidad, E/S, comunicaciones, conexiones, funciones tecnologicas y condiciones ambientales del caso, con su fuente oficial citada.",
    evidence=["Comparacion documentada entre los requisitos del caso y las caracteristicas publicadas de la CPU candidata",
               "Verificacion en la herramienta oficial de seleccion del fabricante"],
    note="Es el punto donde el agente ofrece las dos opciones: A) CPU de la generacion actual del MISMO fabricante, y B) plataformas actuales de marcas alternativas. La eleccion la hace el usuario, nunca el agente.",
    brand_change="Si el usuario elige otra marca, el agente presenta la generacion actual de las marcas alternativas a nivel de PLATAFORMA (familia, modelos documentados y fuente oficial). No afirma equivalencia modelo a modelo: el catalogo no publica atributos comparables y esa seleccion se cierra en la herramienta oficial del fabricante."),
14: dict(role=ENGINEERING, prereq=[7, 13],
    criterion="Matriz que relaciona cada CPU, modulo de E/S, modulo especial e interfaz antigua con su reemplazo y la accion necesaria (reemplazo directo, equivalente, adaptador, se conserva, se elimina), sin filas por definir.",
    evidence=["Matriz de equivalencia de hardware completa"],
    brand_change="Entre marcas distintas la matriz deja de ser modelo a modelo: la equivalencia se establece por criterio funcional (tipo y numero de senales, rangos, redes, funciones especiales) y NUNCA por similitud de nombre o de referencia."),
15: dict(role=ENGINEERING, prereq=[7, 14],
    criterion="Cada tipo de senal verificado contra la tarjeta nueva: tension, corriente, PNP/NPN, aislamiento, resolucion, rango, tipo de sensor y tipo de salida.",
    evidence=["Hoja de comparacion electrica por tipo de senal",
               "Identificacion de las senales que necesitan acondicionamiento o rele de interposicion"]),
16: dict(role=ENGINEERING, prereq=[14, 15],
    criterion="Lista de lo que se conserva y de lo que se sustituye, con la interfaz que lo hace posible en cada caso.",
    evidence=["Decision documentada por dispositivo, con su justificacion"],
    note="Los pasos 15 y 16 suelen obligar a revisar la seleccion del paso 13: la seleccion de CPU es iterativa, no un punto unico."),
17: dict(role=ENGINEERING, prereq=[16],
    criterion="Arquitectura destino definida: CPU, racks, E/S locales y remotas, redes, HMI, variadores y dispositivos externos, con su diagrama.",
    evidence=["Diagrama de la arquitectura nueva",
               "Lista de materiales preliminar derivada del diagrama"]),
18: dict(role=ENGINEERING, prereq=[7, 17],
    criterion="Tabla de mapeo que relaciona cada direccion o tag antiguo con el nuevo, completa, sin duplicados y sin ninguna E/S del paso 7 fuera de la tabla.",
    evidence=["Tabla de mapeo de antigua a nueva",
               "Comprobacion de cobertura contra la lista de E/S del paso 7"]),
19: dict(role=ENGINEERING, prereq=[17],
    criterion="Proyecto creado en la version correcta del software de ingenieria, con CPU, firmware, modulos y dispositivos agregados.",
    evidence=["Proyecto nuevo creado y guardado",
               "Version de software y de firmware anotadas"],
    brand_change="Con cambio de marca esto implica software, licencias y capacitacion NUEVOS, no una version mas reciente del que ya se tiene. Presupuestar y planificar la formacion antes de llegar a este punto."),
20: dict(role=ENGINEERING, prereq=[19],
    criterion="Configuracion de hardware completa y compilable: rack, CPU, E/S locales y remotas, redes y dispositivos asociados.",
    evidence=["Configuracion de hardware compilada sin errores"]),
21: dict(role=ENGINEERING, prereq=[5, 20],
    criterion="Programa pasado por la herramienta oficial de migracion del fabricante, con su reporte guardado y la version de la herramienta anotada.",
    evidence=["Reporte de migracion archivado", "Version de la herramienta utilizada"],
    brand_change="NO APLICA. Entre fabricantes distintos no existe herramienta de conversion: el programa se REESCRIBE desde cero a partir de los pasos 6, 7, 11 y 18. Planificar el esfuerzo como desarrollo nuevo, no como conversion.",
    without_backup="NO APLICA: sin programa de origen no hay nada que convertir. Se reescribe a partir de la logica levantada en los pasos 6 y 7."),
22: dict(role=ENGINEERING, prereq=[21],
    criterion="Cada mensaje del reporte clasificado como error, advertencia, funcion no soportada, conversion automatica o modificacion manual pendiente. No queda ningun mensaje sin revisar.",
    evidence=["Reporte clasificado, con responsable y estado por mensaje"],
    brand_change="NO APLICA: no hay reporte de migracion. Su equivalente es la revision de la especificacion funcional reescrita contra lo documentado en el paso 6.",
    without_backup="NO APLICA: no hay reporte. La verificacion se hace contra el paso 6."),
23: dict(role=ENGINEERING, prereq=[22],
    criterion="Todas las incompatibilidades del paso 22 resueltas y probadas; ninguna queda pendiente ni para revisar despues.",
    evidence=["Registro de cada bloque reconstruido o instruccion sustituida",
               "Compilacion limpia tras cada correccion"]),
24: dict(role=ENGINEERING, prereq=[10, 23],
    criterion="Cada intercambio de datos del paso 10 reconstruido y verificado en la plataforma nueva.",
    evidence=["Lista de intercambios probados con su resultado"]),
25: dict(role=ENGINEERING, prereq=[18, 23],
    criterion="Cada tag de pantalla apunta a una variable valida del PLC nuevo; el reporte de tags sin resolver queda en cero.",
    evidence=["Reporte de tags sin resolver en cero", "Pantallas revisadas una por una"]),
26: dict(role=ENGINEERING, prereq=[15, 23],
    criterion="Para cada senal analogica, el valor en unidades de ingenieria coincide con el del sistema anterior dentro de la tolerancia acordada y declarada.",
    evidence=["Tabla de comparacion de escalamiento por senal, con su tolerancia"]),
27: dict(role=ENGINEERING, prereq=[6, 23],
    criterion="Setpoints, limites, unidades y parametros de sintonizacion trasladados, con el comportamiento esperado documentado y las diferencias entre generaciones de bloques anotadas.",
    evidence=["Tabla de parametros PID antes y despues",
               "Nota de las diferencias de comportamiento entre generaciones de bloques"]),
28: dict(role=SPECIALIST, prereq=[23], requires=req(especialista=True),
    criterion="Funciones de seguridad validadas de forma INDEPENDIENTE por un especialista, segun el procedimiento de seguridad funcional aplicable, con su registro firmado.",
    evidence=["Validacion firmada por el especialista de seguridad funcional",
               "Registro de las pruebas de seguridad"],
    note="El agente NO da instrucciones operativas sobre funciones de seguridad: las identifica, advierte y deriva al especialista. Es una barrera dura del proyecto."),
29: dict(role=ENGINEERING, prereq=[23, 24, 25, 26, 27],
    criterion="Compilacion con cero errores; cada advertencia restante analizada y aceptada o resuelta, ninguna ignorada.",
    evidence=["Salida de compilacion archivada", "Lista de advertencias con su decision"]),
30: dict(role=ENGINEERING, prereq=[29],
    criterion="Secuencias y logica probadas offline o en simulacion, con los desvios corregidos y SIN haber intervenido todavia la maquina real.",
    evidence=["Registro de las pruebas de simulacion y su resultado"]),
31: dict(role=ENGINEERING, prereq=[30],
    criterion="Protocolo FAT escrito y aprobado, cubriendo arranque, paro, automatico, manual, alarmas, fallas, enclavamientos, secuencias, comunicaciones, PID y condiciones anormales, con la configuracion congelada.",
    evidence=["Protocolo FAT aprobado", "Configuracion congelada e identificada"]),
32: dict(role=ENGINEERING, prereq=[31],
    criterion="Para cada prueba del protocolo hay un resultado esperado definido y un resultado obtenido registrado. No queda ninguna desviacion critica abierta.",
    evidence=["Matriz de pruebas con esperado contra obtenido",
               "Registro de desviaciones clasificadas en critica, mayor y menor"],
    note="Precision necesaria: la comparacion se hace contra el comportamiento DOCUMENTADO en el paso 6 y contra el programa de origen. No exige energizar las dos CPU a la vez, porque en planta la CPU antigua sigue en produccion hasta el corte."),
33: dict(role=ENGINEERING, prereq=[5, 32], bloqueante=True,
    criterion="Plan de retorno escrito, con la CPU original, su respaldo verificado y el cableado necesarios para revertir, y el tiempo estimado de reversion.",
    evidence=["Plan de retorno aprobado",
               "Confirmacion de que la CPU original y su respaldo quedan disponibles"]),
34: dict(role=MANAGER, prereq=[33], requires=req(approval=True),
    criterion="Ventana de parada autorizada por escrito, con fecha, duracion, personal, herramientas, respaldos, repuestos, responsabilidades y permisos de trabajo emitidos.",
    evidence=["Autorizacion de parada firmada", "Permisos de trabajo emitidos"]),
35: dict(role=TECHNICIAN, prereq=[3, 5, 33, 34], bloqueante=True,
    requires=req(approval=True, detenida=True, loto=True),
    criterion="Hardware instalado segun el diseno del paso 17, con la CPU original conservada e identificada para el plan de retorno.",
    evidence=["Registro fotografico de la instalacion",
               "CPU original etiquetada y resguardada"],
    note="PASO IRREVERSIBLE. No se ejecuta sin respaldo verificado (paso 5) y plan de retorno (paso 33). Si no hay respaldo, la reconstruccion debe estar validada antes de llegar aqui."),
36: dict(role=TECHNICIAN, prereq=[35], requires=req(detenida=True, loto=True),
    criterion="Alimentacion, polaridades, tierra, continuidad y conexiones verificadas con instrumento ANTES de energizar completamente.",
    evidence=["Hoja de verificacion electrica firmada"]),
37: dict(role=TECHNICIAN, prereq=[36],
    criterion="Configuracion de hardware y programa cargados en la CPU nueva, con IP o nombre de dispositivo asignados y comunicacion establecida.",
    evidence=["Confirmacion de descarga sin errores", "Direccion o nombre asignado anotado"]),
38: dict(role=TECHNICIAN, prereq=[18, 37], requires=req(detenida=True),
    criterion="Cada entrada y cada salida accionada y comprobada contra su dispositivo de campo. Ninguna E/S queda sin probar.",
    evidence=["Lista de E/S firmada punto por punto"]),
39: dict(role=TECHNICIAN, prereq=[38],
    criterion="Cada actuador probado individualmente en manual, con su respuesta correcta y sus enclavamientos activos.",
    evidence=["Registro de pruebas en manual por actuador"]),
40: dict(role=TECHNICIAN, prereq=[39],
    criterion="Secuencia completa ejecutada en automatico, con todas las transiciones entre estados correctas.",
    evidence=["Registro del ciclo automatico completo"]),
41: dict(role=ENGINEERING, prereq=[40], requires=req(approval=True, especialista=True),
    criterion="Cada condicion de falla prevista en el diseno provocada de forma controlada, con su respuesta verificada contra lo esperado.",
    evidence=["Registro de las fallas provocadas y de la respuesta obtenida"],
    note="Provocar fallas es una maniobra deliberada de riesgo: se hace en condiciones controladas, con el personal advertido y el area despejada. Para E-Stop y funciones de seguridad, con el especialista presente."),
42: dict(role=MANAGER, prereq=[41],
    criterion="Sistema completo validado en campo bajo condiciones reales, con el protocolo SAT firmado y sin desviaciones criticas abiertas.",
    evidence=["Protocolo SAT firmado por el responsable de la instalacion"]),
43: dict(role=ENGINEERING, prereq=[6, 42],
    criterion="Tiempos de ciclo, produccion, precision, tiempos de respuesta y alarmas comparados contra los del sistema anterior, sin deterioro no justificado.",
    evidence=["Tabla de indicadores antes y despues, con la fuente de los valores anteriores"],
    note="Los valores de antes deben venir del paso 6. Si no se registraron, la comparacion no es posible y hay que declararlo asi en lugar de estimarlos."),
44: dict(role=ENGINEERING, prereq=[43],
    criterion="Cada diferencia detectada corregida, documentada y vuelta a probar.",
    evidence=["Registro de cambios del commissioning, con la prueba que valida cada uno"],
    note="Es un lazo, no un paso lineal: cada correccion obliga a repetir las pruebas de los pasos 38 a 43 que se vean afectadas."),
45: dict(role=ENGINEERING, prereq=[44],
    criterion="Respaldo final que refleja exactamente lo que quedo funcionando, verificado abriendolo y compilandolo, con checksum y dos copias.",
    evidence=["Proyecto as-built guardado y verificado", "Checksum anotado"]),
46: dict(role=ENGINEERING, prereq=[45],
    criterion="Planos electricos, arquitectura de red, lista de E/S, direcciones, BOM, manuales y diagramas actualizados al estado real instalado.",
    evidence=["Documentacion as-built entregada"]),
47: dict(role=ENGINEERING, prereq=[46],
    criterion="Tabla de trazabilidad que relaciona cada elemento antiguo con el nuevo y las modificaciones de software que fueron necesarias.",
    evidence=["Tabla de trazabilidad completa de la migracion"]),
48: dict(role=MANAGER, prereq=[46],
    criterion="Operadores y mantenimiento capacitados en diagnostico, conexion, respaldo, recuperacion y diferencias de operacion, con registro de asistencia.",
    evidence=["Registro de capacitacion firmado", "Material de consulta entregado"],
    brand_change="Con cambio de marca la capacitacion no es un tramite: el personal parte de cero en el software nuevo. Se dimensiona y se presupuesta desde el paso 13."),
49: dict(role=ENGINEERING, prereq=[45],
    criterion="Los tres proyectos conservados e identificados con fecha y version: Proyecto_original, Proyecto_migrado_pruebas y Proyecto_final_as-built.",
    evidence=["Repositorio o carpeta de versiones con los tres proyectos"]),
50: dict(role=MANAGER, prereq=[45, 46, 47, 48, 49], requires=req(approval=True),
    criterion="Cierre formal con documentacion as-built, resultados FAT y SAT, respaldos verificados y aceptacion firmada del responsable de la instalacion.",
    evidence=["Acta de cierre firmada"]),
}


# --------------------------------------------------------------------------- #
# Lectura del .docx
# --------------------------------------------------------------------------- #
def paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    output = []
    for p in root.iter(W + "p"):
        partes = [n.text or "" for n in p.iter() if n.tag == W + "t"]
        text = "".join(partes).strip()
        if text:
            output.append(text)
    return output


STEP_PATTERN = re.compile(r"^(\d{1,2})\.\s+(.*)$")


def read_document(path: Path) -> dict:
    lineas = paragraphs(path)
    doc = {"title": lineas[0], "subtitle": lineas[1], "objective": "", "application_note": ""}
    steps: list[dict] = []
    actual: dict | None = None
    for linea in lineas[2:]:
        m = STEP_PATTERN.match(linea)
        if m:
            actual = {"n": int(m.group(1)), "title": m.group(2).strip(), "detail": ""}
            steps.append(actual)
            continue
        if linea.lower().startswith("objetivo:"):
            doc["objective"] = linea.split(":", 1)[1].strip()
        elif linea.lower().startswith("nota de aplicaci"):
            doc["application_note"] = linea.split(":", 1)[1].strip()
        elif actual is not None:
            actual["detail"] = (actual["detail"] + " " + linea).strip()
    doc["steps"] = steps
    return doc


# --------------------------------------------------------------------------- #
# Construccion y validacion
# --------------------------------------------------------------------------- #
def phase_of(n: int) -> dict:
    for f in PHASES:
        if n in f["steps"]:
            return f
    raise ValueError(f"El paso {n} no pertenece a ninguna fase")


def build(doc: dict) -> dict:
    steps = []
    for p in doc["steps"]:
        n = p["n"]
        a = ANNOTATIONS[n]
        f = phase_of(n)
        step = {
            "key": str(n),
            "n": n,
            "label": str(n),
            "title": p["title"],
            "detail": p["detail"],
            "phase": f["id"],
            "guide_stage": f["guide_stage"],
            "role": a["role"],
            "exit_criterion": a["criterion"],
            "evidence": a["evidence"],
            "prerequisites": [str(x) for x in a.get("prereq", [])],
            "requires": a.get("requires", req()),
        }
        if a.get("covers"):
            step["covered_by_questionnaire"] = a["covers"]
        if a.get("note"):
            step["agent_note"] = a["note"]
        if a.get("brand_change"):
            step["brand_change_variant"] = a["brand_change"]
        if a.get("without_backup"):
            step["no_backup_variant"] = a["without_backup"]
        if a.get("blocking"):
            step["blocking"] = True
        if a.get("decision_cpu"):
            step["cpu_decision_point"] = True
        steps.append(step)

    # Extension: los siete pasos de construccion del programa. Llevan etiqueta
    # propia y quedan marcados como extension para que nunca se confundan con el
    # documento original de 50 pasos ni alteren su numeracion.
    for e in EXTENSION_PROGRAMA:
        steps.append({
            "key": e["label"],
            "n": None,
            "label": e["label"],
            "title": e["title"],
            "detail": e["detail"],
            "phase": "construccion_del_programa",
            "guide_stage": "construccion",
            "role": e["role"],
            "exit_criterion": e["criterion"],
            "evidence": e["evidence"],
            "prerequisites": [str(x) for x in e.get("prereq", [])],
            "requires": e.get("requires", req()),
            "extension": "programa",
            "methodological_origin": e["origin"],
            **({"agent_note": e["note"]} if e.get("note") else {}),
        })
    return {
        "document": {
            "id": "MIGRA-IA-PROC-050",
            "title": doc["title"],
            "subtitle": doc["subtitle"],
            "objective": doc["objective"],
            "application_note": doc["application_note"],
            "source": DOCX_NAME,
            "total_steps": len(steps),
            "annotated_layer": {
                "description": "El titulo y el detalle de cada paso son literales del "
                               "documento fuente. Los campos criterio_salida, evidencia, "
                               "rol, requiere, prerrequisitos, nota_agente, "
                               "variante_cambio_marca y variante_sin_respaldo son una "
                               "PROPUESTA de MIGRA-IA, pendiente de validacion del autor.",
                "proposed_fields": ["phase", "guide_stage", "role", "exit_criterion",
                                      "evidence", "prerequisites", "requires",
                                      "covered_by_questionnaire", "agent_note",
                                      "brand_change_variant", "no_backup_variant",
                                      "blocking", "cpu_decision_point"],
            },
        },
        "triggers": DISPARADORES,
        "target_cpu_options": CPU_OPTIONS,
        "phases": PHASES + [{
            "id": "construccion_del_programa",
            "name": "Construccion del programa nuevo (extension P1-P7)",
            "steps": [e["label"] for e in EXTENSION_PROGRAMA],
            "guide_stage": "construccion",
            "purpose": "Especificar, modelar y escribir el programa. Es lo que el "
                         "documento original no cubria: sus pasos 21 a 23 asumen que ya "
                         "existe un programa que convertir.",
            "extension": True,
            "depth": DEPTH,
        }],
        "order": traversal_order(),
        "steps": steps,
        "declared_gaps": HUECOS_DECLARADOS,
    }


def validate(data: dict) -> list[str]:
    errores = []
    steps = data["steps"]
    base = [p for p in steps if not p.get("extension")]
    ext = [p for p in steps if p.get("extension")]
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

    order = data["order"]
    claves = {p["key"] for p in steps}
    if sorted(order) != sorted(claves):
        errores.append("el orden de recorrido no coincide con los pasos definidos")
    position = {c: i for i, c in enumerate(order)}

    for p in steps:
        etq = p["label"]
        if not p["detail"]:
            errores.append(f"paso {etq} sin detalle")
        if not p["exit_criterion"]:
            errores.append(f"paso {etq} sin criterio de salida")
        if not p["evidence"]:
            errores.append(f"paso {etq} sin evidencia")
        for req_c in p["prerequisites"]:
            if req_c not in claves:
                errores.append(f"paso {etq}: prerrequisito {req_c} no existe")
            # La comparacion es por POSICION en el recorrido, no por numero: la
            # extension se intercala tras el 20, asi que P3 va antes que el 21.
            elif position[req_c] >= position[p["key"]]:
                errores.append(f"paso {etq}: prerrequisito {req_c} no es anterior "
                               "en el orden de recorrido")

    cubiertos = sorted(str(n) for f in data["phases"] for n in f["steps"])
    if cubiertos != sorted(claves):
        errores.append("las fases no cubren exactamente los pasos definidos")
    if not any(p.get("cpu_decision_point") for p in steps):
        errores.append("ningun paso marcado como punto de decision de CPU")
    return errores


def main() -> int:
    docx = docx_path()
    if not docx.exists():
        print(f"No se encuentra el documento: {docx}")
        print("Pasa su ruta como argumento, o dejalo en la carpeta fuentes/ del repo.")
        return 1
    doc = read_document(docx)
    data = build(doc)
    errores = validate(data)
    if errores:
        print("VALIDACION FALLIDA:")
        for e in errores:
            print("  -", e)
        return 1
    # El JSON se sigue manteniendo a mano despues de generarlo: las rutas por
    # fabricante, la ruta de cambio de marca y algunas variantes no salen del .docx y
    # este script no las produce. Regenerar encima las borraria en silencio, asi que
    # aqui se detiene y dice exactamente que se perderia.
    if TARGET.exists():
        actual = json.loads(TARGET.read_text(encoding="utf-8"))
        generados = {p["key"]: p for p in data["steps"]}
        bloques = [k for k in actual if k not in data]
        # Las dos claves de variante que este script NO produce. Antes se
        # detectaban por el prefijo `variante_`; al pasar a ingles el prefijo
        # se volvio sufijo, y un `endswith("_variant")` a secas tambien caza
        # `activates_variant` y `excludes_variant`, que son otra cosa. Se
        # nombran las dos y se acabo la ambiguedad.
        A_MANO = ("brand_change_variant", "no_backup_variant")
        variantes = [
            p["key"] for p in actual.get("steps", [])
            if any(k in A_MANO for k in p)
            and not any(k in A_MANO for k in generados.get(p["key"], {}))
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
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK  {TARGET}")
    print(f"    pasos: {len(data['steps'])}   fases: {len(data['phases'])}"
          f"   disparadores: {len(data['triggers'])}")
    print(f"    con variante de cambio de marca: "
          f"{sum(1 for p in data['steps'] if 'brand_change_variant' in p)}")
    print(f"    con variante sin respaldo: "
          f"{sum(1 for p in data['steps'] if 'no_backup_variant' in p)}")
    print(f"    que exigen aprobacion humana: "
          f"{sum(1 for p in data['steps'] if p['requires']['human_approval'])}")
    print(f"    que exigen maquina detenida: "
          f"{sum(1 for p in data['steps'] if p['requires']['machine_stopped'])}")
    print(f"    que exigen especialista de seguridad: "
          f"{sum(1 for p in data['steps'] if p['requires']['safety_specialist'])}")
    print(f"    bloqueantes: {[p['n'] for p in data['steps'] if p.get('blocking')]}")
    print(f"    tamano: {TARGET.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
