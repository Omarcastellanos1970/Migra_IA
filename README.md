# MIGRA-IA — Agente de asesoría en obsolescencia y migración de hardware

Agente conversacional que asiste **paso a paso** al personal técnico para
diagnosticar la obsolescencia de hardware y planificar la migración de sistemas
de automatización industrial (PLC, módulos de E/S, HMI, redes industriales,
variadores, servos e instrumentación asociada).

Modalidad **asistida**: recomienda, documenta y guía; la aprobación final y toda
intervención sobre equipos reales corresponde a personal autorizado.

> Prototipo v0.2.0 construido sobre la API de Claude (`claude-opus-4-8`).
> Implementa la especificación del documento *MIGRA-IA — Cuestionario maestro y
> diseño funcional del agente*.

**Autores:** Carlos Omar Castellanos · Julio Noe Castillo · Isidoro Emilio Medina
**Licencia:** MIT · **DOI (v0.2.0):** [10.5281/zenodo.21480950](https://doi.org/10.5281/zenodo.21480950) · **DOI (todas las versiones):** [10.5281/zenodo.21480949](https://doi.org/10.5281/zenodo.21480949)

> **¿Eres revisor?** El proyecto se puede evaluar **sin clave de API y sin costo**
> con el *modo demo*. Sigue [`ARTIFACT.md`](ARTIFACT.md).

---

## Qué hace

- Conduce el **cuestionario adaptativo** (secciones A–K): las respuestas activan,
  ocultan o modifican las preguntas siguientes.
- Registra usuario, planta, máquina, controlador, módulos, redes, HMI,
  seguridad funcional, instrumentación y objetivos, con **identificadores únicos**
  y **niveles de confianza** por cada dato.
- Calcula la **puntuación de riesgo de obsolescencia** (0–100) ponderando los
  ocho factores de la Sección 6.
- Aplica las **reglas obligatorias** de seguridad (Sección 8): no inventa números
  de catálogo, no asume compatibilidad ni respaldos, separa hechos/inferencias/
  recomendaciones, y **solicita aprobación humana** antes de instrucciones de
  intervención.
- Marca **datos faltantes** y **banderas de seguridad funcional**.
- Genera un **informe técnico trazable** en Markdown con la estructura estándar
  de la Sección 9.
- Guarda todo el **expediente** (con registro de auditoría) en `casos/`.

## Requisitos

- Python 3.10 o superior.
- Una clave de API de Anthropic.

## Instalación

```bash
cd MIGRA_IA_Cuestionario_y_Diseno_del_Agente
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# (o en Git Bash:  source .venv/Scripts/activate)

pip install -r requirements.txt
```

Copia `.env.example` a `.env` y coloca tu clave:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Uso

Hay dos formas de usar el mismo agente. Comparten el motor (cuestionario, reglas,
motor de riesgo y expediente); solo cambia la interfaz.

### 1. App web (recomendada)

Interfaz de chat en el navegador con un panel del expediente en vivo (riesgo,
activos, datos faltantes, banderas y aprobaciones pendientes).

```bash
python -m webapp.app
```

Luego abre **http://127.0.0.1:5000**. Al entrar se abre un caso nuevo y el agente
comienza el diagnóstico. Escribe la información que te pide; el panel derecho se
actualiza solo. El botón **Nuevo caso** reinicia el expediente.

### 2. Consola (CLI)

```bash
# Abrir un caso nuevo:
python -m migra_ia.agente

# Continuar un caso existente:
python -m migra_ia.agente CAS-2026-000123
```

Comandos dentro de la sesión de consola:

- `/resumen` — muestra el estado actual del expediente.
- `/salir` — termina y guarda.

En ambos modos, el agente hace preguntas de a poco. Responde en lenguaje natural;
puedes indicar tu nivel de experiencia para ajustar la profundidad técnica.
Cuando el agente proponga una acción sobre el equipo real:

- en **consola** te pide aprobación explícita en la terminal;
- en la **web**, por seguridad, la deja registrada como *aprobación pendiente*
  (no ejecuta la intervención automáticamente).

## Estructura del proyecto

```
MIGRA_IA_Cuestionario_y_Diseno_del_Agente/
├── data/
│   └── cuestionario.json     # Catálogo de preguntas A–K con reglas adaptativas
├── migra_ia/                 # Motor reutilizable
│   ├── config.py             # Modelo, rutas e identidad del agente
│   ├── prompt.py             # Prompt del sistema (reglas, confianza, estructura)
│   ├── scoring.py            # Motor de puntuación de obsolescencia (Sec. 6)
│   ├── caso.py               # Expediente trazable + IDs + auditoría (Sec. 2, 5, 13)
│   ├── herramientas.py       # Tools de registro, riesgo, aprobación e informe
│   ├── nucleo.py             # Turno del agente (usado por la web)
│   └── agente.py             # Bucle conversacional con streaming (CLI)
├── webapp/                   # App web (Flask)
│   ├── app.py                # Servidor y API
│   └── templates/index.html  # Interfaz de chat + panel del expediente
├── casos/                    # Expedientes e informes generados (se crean al usar)
├── requirements.txt
└── .env.example
```

## Alcance del MVP

Foco inicial recomendado por el documento de diseño (Sección 12.2):

| Categoría            | Alcance MVP                                          |
| -------------------- | --------------------------------------------------- |
| Plataformas origen   | Siemens S7-300 y S7-400                             |
| Plataforma destino   | Siemens S7-1500                                      |
| Software             | STEP 7 Classic y TIA Portal                          |
| Redes                | MPI, Profibus DP, Profinet, Industrial Ethernet      |
| Elementos            | CPU, módulos de E/S, HMI y variadores               |

El agente funciona con cualquier marca, pero conviene **validar la precisión con
casos reales** antes de ampliar el alcance.

## Aviso

MIGRA-IA es un sistema de **asistencia técnica**. No sustituye las evaluaciones de
seguridad funcional, los procedimientos de bloqueo y etiquetado, las normas de la
planta ni la autorización de personal competente. Verifica siempre las
recomendaciones antes de intervenir equipos reales.

## Próximos pasos (roadmap)

1. Enriquecer las reglas de ramificación del cuestionario en `cuestionario.json`.
2. Añadir carga de imágenes de placas (visión) para lectura de datos de placa.
3. Base de datos de equivalencias verificadas (sin números de catálogo inventados).
4. Exportación del informe a Word/PDF.
5. Interfaz web multiusuario y esquema relacional (Sección 13).
