# How to publish the artifact on Zenodo and obtain a DOI

**Select language:** [Español](../GUIA_ZENODO.md) · [English](ZENODO_GUIDE.md)
Zenodo (from CERN) is a free repository that assigns a **citable DOI** to your
code. It is accepted by IEEE/ACM as an artifact. There are two routes; **A** is
the recommended one because it versions automatically.

Before publishing, check that `CITATION.cff` and `.zenodo.json` have the right
data (authors, affiliation, ORCID if they have one).

---

## Route A — GitHub + Zenodo (recommended)

1. **Create a repository on GitHub** (for example `migra-ia`) and upload the project:
   ```bash
   cd MIGRA_IA_Cuestionario_y_Diseno_del_Agente
   git init
   git add .
   git commit -m "MIGRA-IA v0.1.0 — artefacto reproducible"
   git branch -M main
   git remote add origin https://github.com/<your-user>/migra-ia.git
   git push -u origin main
   ```
   > The `.gitignore` already excludes `.env`, `.venv/` and the generated cases. **Check
   > that your `.env` with the key does NOT get uploaded** (it must not appear in `git status`).

2. **Connect Zenodo with GitHub:**
   - Go to https://zenodo.org and sign in with your GitHub account.
   - Go to **Settings → GitHub** (https://zenodo.org/account/settings/github/).
   - Find the `migra-ia` repository and **turn the switch ON**.

3. **Create a *release* on GitHub:**
   - In the repo → **Releases → Create a new release**.
   - Tag: `vX.Y.Z`. Title: `MIGRA-IA vX.Y.Z`. Publish.
   - Zenodo detects the release and **generates the DOI automatically** (it takes 1–2 min).

4. **Get the DOI:**
   - Go back to Zenodo → **Upload** → you will see the deposit with its DOI
     (in the form `10.5281/zenodo.NNNNNNNN`).
   - Zenodo gives two DOIs: one **for the version** and a **"concept"** one that always
     points to the latest version. For the paper it is usually the one for the
     specific version that gets cited.

5. **Put the DOI in the project and in the paper:**
   - The `README.md` cites the **concept DOI**, so there is no need to touch it on
     every version: it resolves to the most recent one by itself. The same goes
     for `README.en.md`.
   - Update the version DOI and the version number in the five copies of the
     page —`docs/index.html`, `docs/en/index.html`, `docs/proyecto.html`,
     `MIGRA-IA_sitio.html` and `MIGRA-IA_site.html`—, in `CITATION.cff` and in
     `.zenodo.json`. All five carry the same DOI and the same version; the only
     thing they differ in is the language selector, which in the two standalone
     ones links by file name and in the site ones by folder.
   - Cite the artifact in the article (see below).

---

## If the release shows up as *Failed* (red) on Zenodo

It happened on 2026-07-29 with v0.3.0: the release was published right during a
**Zenodo outage** and the webhook returned `504 timed out`, so the DOI was never
generated. Zenodo **offers no retry button**. What to do:

1. Check the cause on GitHub → **Settings → Webhooks** → the Zenodo hook →
   the **Recent Deliveries** tab. A `504` or `502` is a failure on Zenodo's side, not yours.
2. **Delete the release on GitHub keeping the tag** and create it again from that
   same tag. That emits a new event and Zenodo archives it:
   ```bash
   gh release delete vX.Y.Z --yes          # do NOT use --cleanup-tag: the tag is kept
   gh release create vX.Y.Z --verify-tag --latest \
     --title "MIGRA-IA vX.Y.Z" --notes-file NOTAS.md
   ```
   > Save the text of the notes first: deleting the release removes it.
3. On the retry you will see deliveries with `409 conflict` on `release.published`. **They
   do not mean failure**: it is enough that the `release.created` delivery answers
   `202`. Check the real result against the API, not by the color of the dashboard:
   ```bash
   curl -s "https://zenodo.org/api/records?q=conceptrecid:21480949&all_versions=true"
   ```
4. The red row of the failed attempt **stays forever** on the Zenodo dashboard.
   It is only history; ignore it if the DOI did come out.

---

## Route B — Direct upload of the ZIP (without GitHub)

1. Compress the project folder **without** `.venv/`, `.env`, `cases/*` or
   `__pycache__/` (keep `docs/`, the code and the metadata files).
2. Go to https://zenodo.org → **Upload → New upload**.
3. Upload the ZIP and fill in: *Upload type* = **Software**, title, authors
   (Castellanos, Carlos Omar; Castillo, Julio Noé; Medina, Isidoro;
   Loo, Luis),
   description, *License* = **MIT**, keywords.
4. **Publish** → Zenodo assigns the DOI.

---

## How to cite the artifact in the paper (IEEE)

DOIs already assigned (verified against the Zenodo API):

| Scope | DOI |
| --- | --- |
| Version v0.4.0 (the latest published one) | `10.5281/zenodo.22683608` |
| Version v0.3.0 | `10.5281/zenodo.21659730` |
| Version v0.2.0 | `10.5281/zenodo.21480950` |
| Concept (always resolves to the latest one) | `10.5281/zenodo.21480949` |

IEEE reference —the title is the one of the published record, which is in
Spanish, and a citation quotes the record as it stands:

```
C. O. Castellanos, J. N. Castillo, I. Medina y L. Loo, "MIGRA-IA: Agente
inteligente para diagnóstico de obsolescencia y migración de sistemas de
automatización industrial (v0.4.0)," Zenodo, 2026. doi: 10.5281/zenodo.22683608.
```

In LaTeX (IEEEtran), in your `.bib`. Use `@misc` and **not** `@software`: `IEEEtran.bst`
does not recognize that entry type and the reference does not render.

```bibtex
@misc{migra_ia_2026,
  author       = {Castellanos, Carlos Omar and Castillo, Julio No\'e and Medina, Isidoro and Loo, Luis},
  title        = {{MIGRA-IA: Agente inteligente para diagn\'ostico de obsolescencia y migraci\'on de sistemas de automatizaci\'on industrial (v0.4.0)}},
  howpublished = {Zenodo},
  year         = {2026},
  doi          = {10.5281/zenodo.22683608},
  url          = {https://doi.org/10.5281/zenodo.22683608}
}
```

> Cite the DOI of the **version**, not the concept one: it fixes the exact code
> that the article describes even if a new version is published afterwards.

> **An exception decided in this project:** the paper and the landing page cite the
> **concept DOI** `10.5281/zenodo.21480949`, which always resolves to the latest
> version. It was chosen that way so that no future release forces an edit to the
> article or to the page; that is why the paper does NOT have to be touched when a
> new version is published.

> Consistent with the practice of the project: **the DOI must exist and be verified**
> before citing it in `ref.bib`.

---

## Before submitting (checklist)

- [ ] `CITATION.cff` and `.zenodo.json` with the right authors/affiliation.
- [ ] The `.env` with the key is **not** in the repository nor in the ZIP.
- [ ] The artifact starts and the interactive demo gives the expected result (see `ARTIFACT.en.md`).
- [ ] The DOI generated and placed in `README.md`, in `README.en.md` and in the paper's `.bib`.
