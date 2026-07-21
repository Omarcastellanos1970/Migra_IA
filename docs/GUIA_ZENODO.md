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
   - Tag: `v0.1.0`. Título: `MIGRA-IA v0.1.0`. Publica.
   - Zenodo detecta el release y **genera el DOI automáticamente** (tarda 1–2 min).

4. **Obtén el DOI:**
   - Vuelve a Zenodo → **Upload** → verás el depósito con su DOI
     (formato `10.5281/zenodo.XXXXXXX`).
   - Zenodo da dos DOI: uno **de la versión** (v0.1.0) y uno **"concept"** que
     siempre apunta a la última versión. Para el paper suele citarse el de la
     versión concreta.

5. **Coloca el DOI en el proyecto y en el paper:**
   - Edita el `README.md` y reemplaza `TODO-DOI` por el DOI real.
   - Cita el artefacto en el artículo (ver más abajo).

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

Ejemplo de referencia (reemplaza el DOI y el año):

```
C. O. Castellanos, J. N. Castillo, e I. E. Medina, "MIGRA-IA: Agente inteligente
para diagnóstico de obsolescencia y migración de sistemas de automatización
industrial (v0.1.0)," Zenodo, 2026. doi: 10.5281/zenodo.XXXXXXX.
```

En LaTeX (IEEEtran), en tu `.bib`:

```bibtex
@software{migra_ia_2026,
  author    = {Castellanos, Carlos Omar and Castillo, Julio Noe and Medina, Isidoro Emilio},
  title      = {{MIGRA-IA: Agente inteligente para diagn\'ostico de obsolescencia y migraci\'on de sistemas de automatizaci\'on industrial}},
  version    = {0.1.0},
  year       = {2026},
  publisher  = {Zenodo},
  doi        = {10.5281/zenodo.XXXXXXX},
  url        = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

> Coherente con la práctica del proyecto: **el DOI debe existir y verificarse**
> antes de citarlo en `ref.bib`.

---

## Antes de enviar (checklist)

- [ ] `CITATION.cff` y `.zenodo.json` con autores/afiliación correctos.
- [ ] El `.env` con la clave **no** está en el repositorio ni en el ZIP.
- [ ] El artefacto arranca y el modo demo da el resultado esperado (ver `ARTIFACT.md`).
- [ ] DOI generado y colocado en `README.md` y en el `.bib` del paper.
