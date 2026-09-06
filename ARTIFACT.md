# Artefacto reproducible — MIGRA-IA

**Autores:** Carlos Omar Castellanos · Julio Noe Castillo · Isidoro Emilio Medina
**Versión:** 0.3.0 · **Licencia:** MIT

Este documento es la **guía de evaluación del artefacto** que acompaña al artículo.
Está pensado para que un revisor pueda ejecutar y verificar el sistema en su
propia máquina, **sin necesidad de una clave de API y sin costo**, en ~10–15 min.

---

## 1. Qué es y qué demuestra

MIGRA-IA es un agente conversacional asistido que guía paso a paso al personal
técnico para (a) **diagnosticar la obsolescencia** de hardware de automatización
industrial y (b) **orientar la solución**: alternativas, sugerencia de
equivalencias y procedimiento de migración.

Afirmaciones respaldadas por el artefacto (verificables con la demo interactiva):

1. **Cuestionario adaptativo** que captura la información del equipo por secciones
   (A–K) con niveles de confianza por dato.
2. **Motor de puntuación de riesgo de obsolescencia** (0–100) que pondera 8
   factores y clasifica el riesgo — resultado **determinista** (mismo caso → misma
   puntuación).
3. **Expediente trazable** con identificadores únicos y registro de auditoría.
4. **Reglas de seguridad**: no inventa números de catálogo, marca datos faltantes,
   activa banderas de seguridad funcional y exige validación humana.
5. **Consultoría**: alternativas comparadas, equivalencias sugeridas (a verificar)
   y procedimiento de migración por etapas.
6. **Informe técnico trazable** generado automáticamente.
7. **Base de conocimiento citable** (*MIGRA-IA-GUIA-001*): el agente estructura el
   diagnóstico por las seis etapas de la metodología y **cita la guía** al
   fundamentar sus recomendaciones, consultándola con la herramienta
   `consultar_guia` (`data/base_conocimiento.json`).

---

## 2. Requisitos

- **Python 3.10 o superior** (probado con 3.14 en Windows 11).
- Sin GPU. Sin conexión a internet para la demo.
- ~150 MB para el entorno virtual con dependencias.

---

## 3. Instalación

### Windows — instalación asistida (recomendada)

Descomprima el paquete y haga **doble clic en `INSTALAR.bat`**. Detecta Python,
crea el entorno virtual, instala las dependencias y verifica la instalación. Una
vez terminado, **doble clic en `Iniciar_MIGRA-IA.bat`** arranca el agente y abre
el navegador. Instrucciones paso a paso en `EMPIEZA_AQUI.txt`.

### Cualquier sistema — instalación manual

```bash
# En la carpeta del proyecto:
python -m venv .venv
# Windows:  .venv\Scripts\activate       (o usar .venv\Scripts\python.exe)
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Evaluación SIN clave de API (demo interactiva)

Es la vía recomendada para revisar el artefacto. Ejercita el **motor real**
—cuestionario, cálculo de riesgo, mapa de decisión, procedimiento de migración,
expediente e informe— **sin modelo de lenguaje**: el resultado es determinista y
reproducible, las mismas respuestas producen siempre la misma puntuación.

```bash
python -m webapp.app
```

Abra **http://127.0.0.1:5000** y pulse **"Demo interactiva (sin clave)"**.
Responda las preguntas con el número de la opción; el equipo que escriba se
identifica contra el catálogo verificado de fabricantes, y si procede migrar el
agente recorre el procedimiento paso a paso con la CPU destino que elija.

### Reproducción exacta por línea de comandos

Para obtener las cifras de referencia sin navegador y sin tener que decidir las
respuestas, el repositorio incluye tres escenarios con respuestas fijas. Son
tres recorridos pero **dos casos independientes**: `otra_marca` es `critico` con
otro destino, con las mismas 24 respuestas, así que su puntuación coincide por
construcción y no cuenta como evidencia adicional.

```bash
python _interactivo_run.py              # caso crítico, misma marca
python _interactivo_run.py sano         # caso sin obsolescencia
python _interactivo_run.py otra_marca   # migración con cambio de marca
```

**Salidas esperadas** (deterministas):

| Escenario | Riesgo | Migración | Destino |
|---|---|---|---|
| `critico` | **85.0 → "Riesgo crítico"** | activa, 57 de 57 pasos | Siemens S7-1500 (misma marca) |
| `sano` | **11.8 → "Riesgo bajo"** | no se abre | — |
| `otra_marca` | **85.0 → "Riesgo crítico"** (mismas respuestas que `critico`) | activa, con `cambio_marca` | OMRON Sysmac NX |

Los tres cierran con **24 respuestas** registradas, **0 datos faltantes** y **1
informe** generado en `casos/`. En la interfaz, el panel derecho debe reflejar
los mismos valores, además de los activos registrados, los datos faltantes, las
banderas de seguridad y las aprobaciones humanas pendientes.

**Salidas de referencia ya incluidas** (para comparar sin ejecutar):
- `docs/informe_ejemplo.md` — informe técnico generado por el motor.
- `docs/expediente_ejemplo.json` — expediente trazable con auditoría.

Ambas proceden del escenario `critico` de `python _interactivo_run.py`, de modo
que el revisor puede regenerarlas y compararlas: el informe cierra en **85.0 →
"Riesgo crítico"** con las 24 respuestas del escenario y el detalle de los ocho
factores, cada uno citando los códigos de pregunta que lo sustentan.

### Verificación directa del motor de riesgo

También puede reproducirse el motor de riesgo de forma aislada:

```bash
python -c "from migra_ia.scoring import calcular_riesgo; r=calcular_riesgo({'estado_ciclo_vida':{'valor':90,'justificacion':'fin de vida'},'disponibilidad_respaldo':{'valor':100,'justificacion':'sin respaldo'}}); print(r.puntuacion, r.clasificacion)"
```

---

## 5. Evaluación CON clave de API (opcional — agente real)

Para probar el agente conversacional completo (razonamiento adaptativo con Claude):

1. Copie `.env.example` a `.env` y coloque una `ANTHROPIC_API_KEY` válida
   (servicio de pago de Anthropic; no requerido para evaluar el artefacto).
2. `python -m webapp.app` → **"Caso real (API)"**, o consola: `python -m migra_ia.agente`.

La demo interactiva es suficiente para verificar todas las afirmaciones
estructurales; la clave solo habilita el razonamiento en lenguaje natural sobre
datos arbitrarios.

---

## 6. Estructura del repositorio

```
migra_ia/        Motor: prompt, scoring (Sec. 6), expediente trazable, tools
                 interactivo.py — demo interactiva, sin modelo de lenguaje
                 conocimiento.py — consultas a la base de conocimiento
webapp/          App web (Flask): servidor + interfaz de chat
data/            cuestionario.json (catálogo A–K con reglas adaptativas)
                 base_conocimiento.json (guía MIGRA-IA-GUIA-001)
docs/            informe_ejemplo.md, expediente_ejemplo.json, guía Zenodo
casos/           Expedientes e informes generados en ejecución
INSTALAR.bat     Instalación asistida en Windows (doble clic)
Iniciar_MIGRA-IA.bat  Arranque del agente en Windows (doble clic)
EMPIEZA_AQUI.txt Instrucciones paso a paso para usuarios no técnicos
ARTIFACT.md      Este documento
BITACORA.md      Registro de las sesiones asistidas: que se pidio, que devolvio,
                 que se verifico y que se corrigio
_baseline.py     Baseline reproducible (P1 riesgo ordinal): dataset,
                 particion agrupada, trivial vs clasico y auditoria de fuga
requirements-freeze.txt  Entorno exacto con el que se produjo ese informe
_etiquetado.py   Etiquetas de P1/P2 (provisionales, por regla) y formulario
                 de etiquetado ciego para el panel de expertos
PROTOCOLO_VALIDACION.md  Los seis puntos del protocolo, firmados y congelados
_caracteristicas.py  Contrasta las caracteristicas de dominio del rubro con
                 las que el motor realmente usa (genera docs/)
CITATION.cff     Metadatos de cita
.zenodo.json     Metadatos para el DOI de Zenodo
LICENSE          MIT
```

---

## 7. Lista de verificación para el revisor

- [ ] La instalación finaliza sin errores (`INSTALAR.bat` en Windows, o
      `pip install -r requirements.txt`).
- [ ] La app arranca en http://127.0.0.1:5000.
- [ ] `python _interactivo_run.py` produce riesgo **85.0 / "Riesgo crítico"** y
      abre la migración; `... sano` produce **11.8 / "Riesgo bajo"** y no la abre.
- [ ] `python _interactivo_run.py otra_marca` marca el cambio de marca y propone
      un destino de otro fabricante (OMRON Sysmac NX).
- [ ] El panel muestra activo, dato faltante, bandera y aprobación pendiente.
- [ ] Se genera un informe en `casos/` con la misma estructura que
      `docs/informe_ejemplo.md`.
- [ ] La demo muestra alternativas, equivalencias y procedimiento de migración.

Tiempo estimado de evaluación: **10–15 minutos**.

---

## 8. Cómo citar

Ver `CITATION.cff`. Tras publicar en Zenodo, reemplace el DOI en el `README`
y cite el artefacto en el artículo (ver `docs/GUIA_ZENODO.md`).
