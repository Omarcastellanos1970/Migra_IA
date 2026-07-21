# Artefacto reproducible — MIGRA-IA

**Autores:** Carlos Omar Castellanos · Julio Noe Castillo · Isidoro Emilio Medina
**Versión:** 0.1.0 · **Licencia:** MIT

Este documento es la **guía de evaluación del artefacto** que acompaña al artículo.
Está pensado para que un revisor pueda ejecutar y verificar el sistema en su
propia máquina, **sin necesidad de una clave de API y sin costo**, en ~10–15 min.

---

## 1. Qué es y qué demuestra

MIGRA-IA es un agente conversacional asistido que guía paso a paso al personal
técnico para (a) **diagnosticar la obsolescencia** de hardware de automatización
industrial y (b) **orientar la solución**: alternativas, sugerencia de
equivalencias y procedimiento de migración.

Afirmaciones respaldadas por el artefacto (verificables con el modo demo):

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

---

## 2. Requisitos

- **Python 3.10 o superior** (probado con 3.14 en Windows 11).
- Sin GPU. Sin conexión a internet para el modo demo.
- ~150 MB para el entorno virtual con dependencias.

---

## 3. Instalación

```bash
# En la carpeta del proyecto:
python -m venv .venv
# Windows:  .venv\Scripts\activate       (o usar .venv\Scripts\python.exe)
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Evaluación SIN clave de API (modo demostración)

Es la vía recomendada para revisar el artefacto. Ejercita el **motor real**
(cuestionario, cálculo de riesgo, expediente e informe) con un caso de ejemplo.

```bash
python -m webapp.app
```

Abre **http://127.0.0.1:5000** y pulsa **"Modo demo (sin clave)"**. Escribe
cualquier texto y pulsa *Enviar* para avanzar por el diagnóstico.

**Salidas esperadas** (deterministas):

| Elemento | Valor esperado |
|---|---|
| Riesgo de obsolescencia | **75.2 / 100 → "Riesgo alto"** |
| Activos registrados | 1 (CPU S7-300 315-2 DP) |
| Datos faltantes | 1 (respaldo sin verificar) |
| Bandera de seguridad | "REVISIÓN OBLIGATORIA POR ESPECIALISTA…" |
| Aprobación pendiente | 1 (lectura de programa desde el PLC) |
| Informe generado | 1 archivo Markdown en `casos/` |

El panel derecho debe reflejar estos valores. La demo muestra explícitamente
**alternativas**, **equivalencias sugeridas** y el **procedimiento de migración**
S7-300 → S7-1500.

**Referencia de salida ya incluida** (para comparar sin ejecutar):
- `docs/informe_ejemplo.md` — informe técnico generado por la demo.
- `docs/expediente_ejemplo.json` — expediente trazable con auditoría.

### Verificación por línea de comandos (sin navegador)

También puede reproducirse el motor de riesgo de forma directa:

```bash
python -c "from migra_ia.scoring import calcular_riesgo; r=calcular_riesgo({'estado_ciclo_vida':{'valor':90,'justificacion':'fin de vida'},'disponibilidad_respaldo':{'valor':100,'justificacion':'sin respaldo'}}); print(r.puntuacion, r.clasificacion)"
```

---

## 5. Evaluación CON clave de API (opcional — agente real)

Para probar el agente conversacional completo (razonamiento adaptativo con Claude):

1. Copie `.env.example` a `.env` y coloque una `ANTHROPIC_API_KEY` válida
   (servicio de pago de Anthropic; no requerido para evaluar el artefacto).
2. `python -m webapp.app` → **"Caso real (API)"**, o consola: `python -m migra_ia.agente`.

El modo demo es suficiente para verificar todas las afirmaciones estructurales;
la clave solo habilita el razonamiento en lenguaje natural sobre datos arbitrarios.

---

## 6. Estructura del repositorio

```
migra_ia/        Motor: prompt, scoring (Sec. 6), expediente trazable, tools, demo
webapp/          App web (Flask): servidor + interfaz de chat
data/            cuestionario.json (catálogo A–K con reglas adaptativas)
docs/            informe_ejemplo.md, expediente_ejemplo.json, guía Zenodo
casos/           Expedientes e informes generados en ejecución
ARTIFACT.md      Este documento
CITATION.cff     Metadatos de cita
.zenodo.json     Metadatos para el DOI de Zenodo
LICENSE          MIT
```

---

## 7. Lista de verificación para el revisor

- [ ] `pip install -r requirements.txt` finaliza sin errores.
- [ ] La app arranca en http://127.0.0.1:5000.
- [ ] El modo demo produce riesgo **75.2 / "Riesgo alto"**.
- [ ] El panel muestra activo, dato faltante, bandera y aprobación pendiente.
- [ ] Se genera un informe en `casos/` equivalente a `docs/informe_ejemplo.md`.
- [ ] La demo muestra alternativas, equivalencias y procedimiento de migración.

Tiempo estimado de evaluación: **10–15 minutos**.

---

## 8. Cómo citar

Ver `CITATION.cff`. Tras publicar en Zenodo, reemplace el DOI en el `README`
y cite el artefacto en el artículo (ver `docs/GUIA_ZENODO.md`).
