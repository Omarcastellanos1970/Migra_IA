# Cómo publicar el artefacto en Zenodo y obtener un DOI

Zenodo (del CERN) es un repositorio gratuito que asigna un **DOI citable** a tu
código. Es aceptado por IEEE/ACM como artefacto. Hay dos vías; la **A** es la
recomendada porque versiona automáticamente.

Antes de publicar, revisa que `CITATION.cff` y `.zenodo.json` tengan los datos
correctos (autores, afiliación, ORCID si tienen).

---

## Vía A — GitHub + Zenodo (recomendada)

1. **Crea un repositorio en GitHub** (por ejemplo `migra-ia`) y sube el proyecto:
   ```bash
   cd MIGRA_IA_Cuestionario_y_Diseno_del_Agente
   git init
   git add .
   git commit -m "MIGRA-IA v0.1.0 — artefacto reproducible"
   git branch -M main
   git remote add origin https://github.com/<tu-usuario>/migra-ia.git
   git push -u origin main
   ```
   > El `.gitignore` ya excluye `.env`, `.venv/` y los casos generados. **Verifica
   > que tu `.env` con la clave NO se suba** (no debe aparecer en `git status`).

2. **Conecta Zenodo con GitHub:**
   - Entra a https://zenodo.org e inicia sesión con tu cuenta de GitHub.
   - Ve a **Settings → GitHub** (https://zenodo.org/account/settings/github/).
   - Busca el repositorio `migra-ia` y **activa el interruptor (ON)**.

3. **Crea un *release* en GitHub:**
   - En el repo → **Releases → Create a new release**.
   - Tag: `vX.Y.Z`. Título: `MIGRA-IA vX.Y.Z`. Publica.
   - Zenodo detecta el release y **genera el DOI automáticamente** (tarda 1–2 min).

4. **Obtén el DOI:**
   - Vuelve a Zenodo → **Upload** → verás el depósito con su DOI
     (formato `10.5281/zenodo.NNNNNNNN`).
   - Zenodo da dos DOI: uno **de la versión** y uno **"concept"** que siempre
     apunta a la última versión. Para el paper suele citarse el de la versión
     concreta.

5. **Coloca el DOI en el proyecto y en el paper:**
   - El `README.md` cita el **concept DOI**, así que no hay que tocarlo en cada
     versión: resuelve solo a la más reciente.
   - Actualiza el DOI de la versión y el número de versión en `docs/index.html`
     (y sus copias `docs/proyecto.html` y `MIGRA-IA_sitio.html`, que deben quedar
     idénticas), en `CITATION.cff` y en `.zenodo.json`.
   - Cita el artefacto en el artículo (ver más abajo).

---

## Si el release aparece como *Failed* (rojo) en Zenodo

Ocurrió el 2026-07-29 con la v0.3.0: el release se publicó justo durante una
**caída de Zenodo** y el webhook devolvió `504 timed out`, así que el DOI nunca
se generó. Zenodo **no ofrece botón de reintento**. Qué hacer:

1. Comprueba la causa en GitHub → **Settings → Webhooks** → el hook de Zenodo →
   pestaña **Recent Deliveries**. Un `504` o `502` es un fallo de Zenodo, no tuyo.
2. **Borra el release en GitHub conservando el tag** y vuelve a crearlo desde ese
   mismo tag. Eso emite un evento nuevo y Zenodo lo archiva:
   ```bash
   gh release delete vX.Y.Z --yes          # NO uses --cleanup-tag: el tag se conserva
   gh release create vX.Y.Z --verify-tag --latest \
     --title "MIGRA-IA vX.Y.Z" --notes-file NOTAS.md
   ```
   > Guarda antes el texto de las notas: borrar el release lo elimina.
3. Al reintentar verás entregas con `409 conflicto` en `release.published`. **No
   significan fallo**: basta con que la entrega de `release.created` responda
   `202`. Verifica el resultado real contra la API, no por el color del panel:
   ```bash
   curl -s "https://zenodo.org/api/records?q=conceptrecid:21480949&all_versions=true"
   ```
4. La fila roja del intento fallido **se queda para siempre** en el panel de
   Zenodo. Es solo histórico; ignórala si el DOI ya salió.

---

## Vía B — Subida directa del ZIP (sin GitHub)

1. Comprime la carpeta del proyecto **sin** `.venv/`, `.env`, `casos/*` ni
   `__pycache__/` (deja `docs/`, el código y los archivos de metadatos).
2. Entra a https://zenodo.org → **Upload → New upload**.
3. Sube el ZIP y completa: *Upload type* = **Software**, título, autores
   (Castellanos, Carlos Omar; Castillo, Julio Noe; Medina, Isidoro Emilio),
   descripción, *License* = **MIT**, palabras clave.
4. **Publish** → Zenodo asigna el DOI.

---

## Cómo citar el artefacto en el paper (IEEE)

DOI ya asignados (verificados en la API de Zenodo):

| Alcance | DOI |
| --- | --- |
| Version v0.3.0 (la que se cita en el paper) | `10.5281/zenodo.21659730` |
| Version v0.2.0 | `10.5281/zenodo.21480950` |
| Concept (resuelve siempre a la ultima) | `10.5281/zenodo.21480949` |

Referencia IEEE:

```
C. O. Castellanos, J. N. Castillo, e I. E. Medina, "MIGRA-IA: Agente inteligente
para diagnóstico de obsolescencia y migración de sistemas de automatización
industrial (v0.3.0)," Zenodo, 2026. doi: 10.5281/zenodo.21659730.
```

En LaTeX (IEEEtran), en tu `.bib`. Usa `@misc` y **no** `@software`: `IEEEtran.bst`
no reconoce ese tipo de entrada y la referencia no se renderiza.

```bibtex
@misc{migra_ia_2026,
  author       = {Castellanos, Carlos Omar and Castillo, Julio Noe and Medina, Isidoro Emilio},
  title        = {{MIGRA-IA: Agente inteligente para diagn\'ostico de obsolescencia y migraci\'on de sistemas de automatizaci\'on industrial (v0.3.0)}},
  howpublished = {Zenodo},
  year         = {2026},
  doi          = {10.5281/zenodo.21659730},
  url          = {https://doi.org/10.5281/zenodo.21659730}
}
```

> Cita el DOI de la **version**, no el concept: fija el codigo exacto que describe
> el articulo aunque despues se publique una version nueva.

> Coherente con la práctica del proyecto: **el DOI debe existir y verificarse**
> antes de citarlo en `ref.bib`.

---

## Antes de enviar (checklist)

- [ ] `CITATION.cff` y `.zenodo.json` con autores/afiliación correctos.
- [ ] El `.env` con la clave **no** está en el repositorio ni en el ZIP.
- [ ] El artefacto arranca y el modo demo da el resultado esperado (ver `ARTIFACT.md`).
- [ ] DOI generado y colocado en `README.md` y en el `.bib` del paper.
