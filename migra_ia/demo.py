"""Modo demostracion (sin API key).

Recorre un caso de ejemplo (Siemens S7-300) con respuestas del agente
guionizadas, pero usando el MOTOR REAL: cada paso invoca las herramientas
verdaderas sobre el expediente, de modo que el riesgo se calcula con
scoring.py y el informe se genera de verdad.

La demo muestra el ciclo completo de consultoria: diagnostico -> riesgo ->
alternativas -> sugerencia de equivalencias -> procedimiento de migracion ->
aprobacion humana -> informe. Sirve para presentar el agente sin gastar tokens.
"""

from __future__ import annotations

from .caso import Caso
from .herramientas import ejecutar_herramienta
from .nucleo import aprobador_pendiente

# Cada paso: texto del agente + herramientas reales que se ejecutan al mostrarlo.
DEMO_PASOS: list[dict] = [
    {
        "texto": (
            "**[MODO DEMOSTRACION — sin clave de API]**\n\n"
            "Hola, soy MIGRA-IA. Asisto paso a paso al personal tecnico para "
            "diagnosticar la obsolescencia de un equipo y orientarlo hacia la "
            "solucion: reparacion, repuesto, **hardware equivalente** o "
            "**migracion** a una plataforma moderna.\n\n"
            "Esta es una demostracion guiada con un caso real de ejemplo (Siemens "
            "S7-300). Veras: diagnostico -> riesgo -> alternativas -> equivalencias "
            "sugeridas -> procedimiento de migracion -> informe. Escribe cualquier "
            "cosa y pulsa Enviar para avanzar; observa el panel de la derecha.\n\n"
            "Para empezar: cual es tu nombre y estas autorizado para acceder o "
            "modificar el sistema, o solo para diagnostico?"
        ),
        "tools": [],
    },
    {
        "texto": (
            "Gracias, Luis. Trabajaremos en **modo diagnostico**: no dare "
            "instrucciones de intervencion sin aprobacion de personal autorizado.\n\n"
            "Hablemos del controlador. Cual es el fabricante, la familia y el modelo "
            "de la CPU? Si no lo sabes, una foto de la placa me sirve."
        ),
        "tools": [
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "A", "codigo": "A01", "pregunta": "Nombre del responsable",
                 "valor": "Luis", "nivel_confianza": "confirmado", "fuente": "verbal"},
                {"seccion": "A", "codigo": "A02", "pregunta": "Cargo o funcion",
                 "valor": "Ingeniero de mantenimiento", "nivel_confianza": "confirmado", "fuente": "verbal"},
                {"seccion": "A", "codigo": "A07", "pregunta": "Autorizacion",
                 "valor": "Solo autorizado para diagnostico", "nivel_confianza": "confirmado", "fuente": "verbal"},
            ]}),
        ],
    },
    {
        "texto": (
            "Registrado: **Siemens S7-300, CPU 315-2 DP**, operando con fallas "
            "intermitentes. Lo mas critico ahora es que **no hay respaldo verificado "
            "del programa** — lo marco como dato faltante prioritario.\n\n"
            "Existe copia del programa del PLC? Se conoce la contrasena, y estan "
            "disponibles STEP 7 y el cable MPI para intentar leerlo?"
        ),
        "tools": [
            ("registrar_activo", {"tipo": "cpu", "descripcion": "CPU S7-300 315-2 DP",
                                   "fabricante": "Siemens", "modelo": "S7-300 / CPU 315-2 DP",
                                   "estado": "Operando con fallas", "nivel_confianza": "confianza_media",
                                   "notas": "Falla intermitente reportada por el usuario."}),
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "D", "codigo": "D01", "pregunta": "Fabricante del PLC",
                 "valor": "Siemens", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                {"seccion": "D", "codigo": "D02", "pregunta": "Familia del PLC",
                 "valor": "S7-300", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                {"seccion": "C", "codigo": "C07", "pregunta": "Estado actual",
                 "valor": "Operando con fallas", "nivel_confianza": "confianza_media", "fuente": "verbal"},
            ]}),
            ("registrar_dato_faltante", {"descripcion": "Respaldo del programa del PLC sin verificar",
                                          "impacto": "Bloquea cualquier descarga o migracion segura hasta recuperarlo."}),
        ],
    },
    {
        "texto": (
            "Entendido: no se conoce si hay respaldo. La **prioridad 1** pasa a ser "
            "recuperar el programa antes de cualquier otra accion.\n\n"
            "Sigamos con las comunicaciones y la criticidad. La maquina usa Profibus "
            "DP y MPI? Que tan critica es para la produccion?"
        ),
        "tools": [
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "F", "codigo": "F01", "pregunta": "Existe copia del programa?",
                 "valor": "No se conoce", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                {"seccion": "G", "codigo": "G01", "pregunta": "Redes utilizadas",
                 "valor": "Profibus DP, MPI", "nivel_confianza": "confianza_media", "fuente": "verbal"},
            ]}),
        ],
    },
    {
        "texto": (
            "Anotado: **criticidad alta** y red **Profibus DP** (relevante para elegir "
            "una plataforma destino compatible).\n\n"
            "Ultima parte antes de evaluar: la migracion afectaria funciones de "
            "seguridad (paros de emergencia, cortinas, PLC de seguridad)? Y cual es "
            "tu objetivo principal?"
        ),
        "tools": [
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "C", "codigo": "C08", "pregunta": "Criticidad de la maquina",
                 "valor": "Alta: afecta una linea importante", "nivel_confianza": "confianza_media", "fuente": "verbal"},
                {"seccion": "K", "codigo": "K01", "pregunta": "Que desea realizar?",
                 "valor": "Reducir riesgo de parada; evaluar migracion", "nivel_confianza": "confirmado", "fuente": "verbal"},
            ]}),
        ],
    },
    {
        "texto": (
            "Como no se conoce si la migracion afecta la seguridad, activo una "
            "**bandera de seguridad funcional**: cualquier cambio que la toque "
            "requiere revision de un especialista.\n\n"
            "Con la informacion confirmada, calculo el riesgo de obsolescencia…"
        ),
        "tools": [
            ("guardar_respuestas", {"respuestas": [
                {"seccion": "I", "codigo": "I07", "pregunta": "La migracion afectara funciones de seguridad?",
                 "valor": "No se conoce", "nivel_confianza": "confianza_media", "fuente": "verbal"},
            ]}),
            ("registrar_bandera_seguridad", {"texto": "REVISION OBLIGATORIA POR ESPECIALISTA EN SEGURIDAD FUNCIONAL"}),
        ],
    },
    {
        "texto": (
            "**Riesgo calculado.** Mira el panel: la puntuacion y su clasificacion "
            "salen del motor real (ponderacion de los 8 factores de la Seccion 6).\n\n"
            "El peso mayor lo aportan el fin de ciclo de vida de la S7-300, la "
            "ausencia de respaldo verificado y la alta criticidad productiva. "
            "Ahora paso a la **consultoria**: alternativas de solucion."
        ),
        "tools": [
            ("calcular_riesgo_obsolescencia", {"factores": {
                "estado_ciclo_vida": {"valor": 90, "justificacion": "S7-300 en fin de ciclo de vida; descontinuacion progresiva."},
                "disponibilidad_repuestos": {"valor": 70, "justificacion": "Repuestos limitados; mercado de segunda mano."},
                "soporte_fabricante": {"valor": 75, "justificacion": "Soporte reducido; el fabricante recomienda migrar."},
                "disponibilidad_software": {"valor": 40, "justificacion": "STEP 7 Classic disponible pero requiere SO antiguo."},
                "disponibilidad_respaldo": {"valor": 100, "justificacion": "Sin respaldo verificado del programa."},
                "compatibilidad_sistemas": {"valor": 50, "justificacion": "Profibus DP compatible con la plataforma destino."},
                "historial_fallas": {"valor": 70, "justificacion": "Falla intermitente reportada."},
                "criticidad_productiva": {"valor": 80, "justificacion": "Maquina de alta criticidad para la linea."},
            }}),
        ],
    },
    {
        "texto": (
            "**Alternativas de solucion** (de menor a mayor alcance):\n\n"
            "1. **Operacion temporal controlada** — mantener el equipo con respaldo "
            "recuperado y repuesto puente. *Rapido y barato, no resuelve la "
            "obsolescencia.*\n"
            "2. **Repuesto directo** — reemplazar la CPU por la misma referencia "
            "(nueva o usada). *Minima intervencion; depende de disponibilidad, que "
            "aqui es limitada.*\n"
            "3. **Hardware equivalente** — CPU compatible que conserve E/S, redes y "
            "logica con cambios menores. *Equilibrio costo/vida util.*\n"
            "4. **Migracion a plataforma moderna** — S7-1500 con TIA Portal. *Mayor "
            "inversion, pero resuelve la obsolescencia y habilita mejoras.*\n"
            "5. **Reconstruccion** — reingenieria si no hay respaldo ni documentacion. "
            "*Ultimo recurso.*\n\n"
            "Dado el riesgo alto y la falta de repuestos, te sugiero **equivalencia "
            "hacia S7-1500**. Te muestro las equivalencias."
        ),
        "tools": [],
    },
    {
        "texto": (
            "**Sugerencia de equivalencias (preliminar — a verificar).**\n\n"
            "| Elemento actual | Candidato equivalente | Criterio |\n"
            "|---|---|---|\n"
            "| CPU S7-300 315-2 DP | Familia **S7-1500** con interfaz Profibus DP "
            "(p. ej. CPU 1516-3 PN/DP) o S7-1500 + modulo CM 1542-5 | Conserva "
            "Profibus DP; mayor memoria y rendimiento |\n"
            "| Modulos E/S S7-300 (SM) | Modulos **ET 200MP / ET 200SP** | Mismos "
            "tipos de senal (DI/DO/AI/AO), reutiliza cableado por canal |\n"
            "| STEP 7 Classic | **TIA Portal** (herramienta de migracion S7-300→S7-1500) | "
            "Conversion asistida del programa |\n"
            "| MPI | **Profinet / Industrial Ethernet** | Puesta en marcha y HMI |\n\n"
            "⚠️ **Importante (regla del agente):** estas son familias candidatas por "
            "criterio tecnico; **no confirmo numeros de catalogo exactos**. Deben "
            "verificarse con el fabricante y su herramienta oficial de seleccion/"
            "migracion, y validarse contra E/S, memoria, tiempo de ciclo y funciones "
            "especiales reales."
        ),
        "tools": [],
    },
    {
        "texto": (
            "**Procedimiento de migracion por etapas** (S7-300 → S7-1500):\n\n"
            "1. **Respaldo y aseguramiento** — recuperar y verificar el programa, HMI "
            "y parametros de drives; guardar copia con checksum.\n"
            "2. **Levantamiento** — inventario completo de E/S, redes, direcciones y "
            "funciones especiales (PID, conteo, posicionamiento).\n"
            "3. **Arquitectura destino** — seleccionar CPU y periferia S7-1500/ET 200, "
            "definir redes (Profinet + Profibus DP donde aplique).\n"
            "4. **Mapa de senales** — tabla de conversion de direccionamiento "
            "S7-300 → S7-1500 (entradas, salidas, marcas, DB).\n"
            "5. **Conversion del programa** — migrar con TIA Portal, revisar bloques, "
            "resolver instrucciones no equivalentes, conservar simbolos y comentarios.\n"
            "6. **Lista de materiales (BOM) preliminar** — hardware, licencias, "
            "accesorios (a cotizar con referencias verificadas).\n"
            "7. **Pruebas FAT** — en banco, con simulacion de E/S, antes de tocar la "
            "planta.\n"
            "8. **Puesta en marcha (SAT)** — ventana de parada planificada, pruebas de "
            "seguridad con especialista, verificacion de la secuencia.\n"
            "9. **Plan de retorno** — dejar la CPU original y respaldo listos para "
            "revertir si el arranque falla.\n\n"
            "Cada etapa que toque seguridad requiere validacion del especialista "
            "(bandera activa)."
        ),
        "tools": [],
    },
    {
        "texto": (
            "**Guia paso a paso (nivel principiante) — adaptada a tu equipo Siemens.**\n\n"
            "Como la Prioridad 1 es recuperar el respaldo, te dejo el procedimiento "
            "detallado, como si fuera la primera vez que lo haces. En un caso real, "
            "antes del detalle operativo pediria **aprobacion humana**.\n\n"
            "**A) Crear el respaldo del programa (S7-300 con STEP 7 / TIA Portal):**\n"
            "1. Reune: PC con STEP 7 (o TIA Portal) de la version correcta, cable "
            "**MPI/Profibus** (o adaptador PC-Adapter/USB) con su driver, y averigua si "
            "la CPU tiene contrasena.\n"
            "2. Conecta el cable entre la PC y el puerto de programacion de la CPU "
            "315-2 DP.\n"
            "3. Abre el software y crea un **proyecto nuevo vacio** para recibir el "
            "programa.\n"
            "4. Ponte **EN LINEA** (online): elige la interfaz PG/PC, ajusta la "
            "direccion MPI del PLC y comprueba que responda (nodos accesibles).\n"
            "5. **Sube TODO** del PLC a la PC (Cargar estacion / Upload): bloques "
            "(OB/FB/FC/DB), configuracion de hardware y simbolos/comentarios si estan.\n"
            "6. **Guarda** el proyecto con un nombre claro (ej. "
            "`S7300_Maquina_2026-07-21`) y anota la version del software.\n"
            "7. **Verifica**: que abra y compile sin errores; anota el tamano.\n"
            "8. Guarda **dos copias** en lugares distintos (PC + USB o carpeta de red).\n\n"
            "**B) Cargar el programa en la CPU nueva (migracion a S7-1500, TIA Portal):**\n"
            "*Solo con el respaldo verificado, aprobacion y la maquina detenida y "
            "bloqueada (LOTO).*\n"
            "1. Confirma maquina **detenida y bloqueada** y que hay aprobacion.\n"
            "2. Monta y cablea la CPU S7-1500; revisa alimentacion y tierra **antes** "
            "de energizar.\n"
            "3. Ajusta el **firmware** de la CPU nueva a la version requerida.\n"
            "4. Abre en TIA Portal el **proyecto migrado** (convertido desde STEP 7 con "
            "la herramienta de migracion).\n"
            "5. Revisa la **configuracion de hardware** (CPU, modulos ET 200, "
            "direcciones) para que coincida con lo instalado.\n"
            "6. Pon la CPU en **STOP**.\n"
            "7. **Descarga TODO** (Download): hardware + programa.\n"
            "8. Ponte en linea y revisa el **buffer de diagnostico** (sin errores; LED "
            "de estado en verde).\n"
            "9. Pasa a **RUN** de forma controlada y prueba las E/S en modo seguro; "
            "luego valida la secuencia paso a paso.\n"
            "10. Si algo falla, aplica el **PLAN DE RETORNO**: vuelve a la CPU/respaldo "
            "original.\n\n"
            "⚠️ Todo lo que toque **seguridad** (paros, cortinas, PL/SIL) lo revisa un "
            "especialista."
        ),
        "tools": [],
    },
    {
        "texto": (
            "**Recomendacion principal (confianza media).** Separo lo que se de lo "
            "que infiero:\n\n"
            "- **Hechos confirmados:** CPU S7-300 315-2 DP; falla intermitente; red "
            "Profibus DP/MPI; criticidad alta.\n"
            "- **Inferencias (no confirmadas):** probable ausencia de respaldo; "
            "repuestos escasos.\n"
            "- **Recomendacion:** *Prioridad 1 — recuperar el respaldo del programa.* "
            "Luego, **migrar a S7-1500** conservando Profibus DP segun las "
            "equivalencias y el procedimiento anteriores.\n\n"
            "Para darte el procedimiento operativo de lectura del programa desde el "
            "PLC (podria requerir detener la maquina), necesito **aprobacion "
            "humana**. La dejo registrada como PENDIENTE en el panel."
        ),
        "tools": [
            ("solicitar_aprobacion_humana", {
                "accion_propuesta": "Leer/recuperar el programa desde el PLC S7-300",
                "riesgos": "Puede requerir detener la maquina; sin respaldo previo hay riesgo de perdida.",
                "puede_detener_produccion": True,
            }),
        ],
    },
    {
        "texto": (
            "Genero el **informe tecnico trazable** con la estructura estandar "
            "(Seccion 9) — incluye diagnostico, alternativas, equivalencias, "
            "procedimiento de migracion y datos faltantes — y lo guardo en `casos/`.\n\n"
            "Con esto termina la demostracion. Viste el ciclo completo de consultoria: "
            "diagnostico guiado, calculo de riesgo, **alternativas**, **equivalencias "
            "sugeridas**, **procedimiento de migracion** y validacion humana.\n\n"
            "Para un diagnostico **real con los datos de tu equipo**, configura tu "
            "`ANTHROPIC_API_KEY` en el archivo `.env` y abre un **Caso real (API)**."
        ),
        "tools": [
            ("generar_informe", {
                "titulo": "Diagnostico de obsolescencia y plan de migracion — CPU Siemens S7-300 315-2 DP (DEMO)",
                "nivel_confianza_global": "confianza_media",
                "resumen": "Riesgo alto; recuperar respaldo y migrar a S7-1500 conservando Profibus DP.",
                "cuerpo_markdown": (
                    "## 1. Identificacion\nCaso de demostracion. CPU Siemens S7-300 315-2 DP.\n\n"
                    "## 2. Resumen ejecutivo\nCPU en fin de ciclo de vida, con falla intermitente y "
                    "sin respaldo verificado del programa. Riesgo de obsolescencia alto. Se recomienda "
                    "recuperar el respaldo y migrar a S7-1500.\n\n"
                    "## 3. Informacion confirmada\nCPU 315-2 DP; falla intermitente; Profibus DP/MPI; "
                    "criticidad alta.\n\n"
                    "## 4. Informacion no confirmada / supuestos\nProbable ausencia de respaldo; "
                    "repuestos escasos.\n\n"
                    "## 5. Datos faltantes\nRespaldo del programa sin verificar; memoria utilizada; "
                    "lista completa de modulos; version de firmware; funciones especiales.\n\n"
                    "## 6. Estado y puntuacion de obsolescencia\nRiesgo alto (ver puntuacion ponderada "
                    "en el expediente, motor de la Seccion 6).\n\n"
                    "## 7. Riesgos\nTecnico: falla de CPU sin respaldo. Productivo: parada de linea "
                    "critica. Seguridad: revision obligatoria por especialista (bandera activa).\n\n"
                    "## 8. Alternativas\n(1) Operacion temporal controlada; (2) repuesto directo; "
                    "(3) hardware equivalente; (4) migracion a S7-1500; (5) reconstruccion.\n\n"
                    "## 9. Recomendacion principal\nPrioridad 1: recuperar el respaldo. Luego migrar a "
                    "S7-1500 conservando Profibus DP.\n\n"
                    "## 10. Equivalencias preliminares (a verificar con el fabricante)\n"
                    "CPU S7-300 315-2 DP -> familia S7-1500 con Profibus DP (p. ej. CPU 1516-3 PN/DP o "
                    "CM 1542-5); modulos S7-300 -> ET 200MP/ET 200SP; STEP 7 Classic -> TIA Portal. "
                    "NO se confirman numeros de catalogo: deben verificarse oficialmente.\n\n"
                    "## 11. Plan de respaldo, migracion y retorno\nRespaldo verificado -> levantamiento "
                    "-> arquitectura destino -> mapa de senales -> conversion en TIA Portal -> BOM "
                    "preliminar -> plan de retorno (conservar CPU original).\n\n"
                    "## 12. Plan de pruebas\nFAT en banco con simulacion de E/S; SAT en ventana de "
                    "parada con pruebas de seguridad por especialista.\n\n"
                    "## 13. Nivel de confianza y fuentes\nConfianza media. Fuentes: declaracion verbal "
                    "del tecnico (pendiente de evidencias: placa, respaldo, lista de E/S).\n"
                ),
            }),
        ],
    },
]

_TEXTO_FIN = (
    "La demostracion ya termino. Pulsa **Modo demo** para reiniciarla, o "
    "configura tu `ANTHROPIC_API_KEY` y abre un **Caso real (API)** para diagnosticar "
    "tu propio equipo."
)


def ejecutar_paso(caso: Caso, indice: int) -> dict:
    """Ejecuta el paso `indice` del guion sobre el expediente real.

    Devuelve {"texto", "acciones", "resumen", "fin", "demo": True}.
    """
    if indice >= len(DEMO_PASOS):
        return {"texto": _TEXTO_FIN, "acciones": [], "resumen": caso.resumen(),
                "fin": True, "demo": True}

    paso = DEMO_PASOS[indice]
    acciones: list[str] = []
    for nombre, entrada in paso["tools"]:
        ejecutar_herramienta(caso, nombre, entrada, aprobador_pendiente)
        acciones.append(nombre)

    caso.guardar()
    return {
        "texto": paso["texto"],
        "acciones": acciones,
        "resumen": caso.resumen(),
        "fin": indice >= len(DEMO_PASOS) - 1,
        "demo": True,
    }
