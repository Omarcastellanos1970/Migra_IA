# Publicar la página de MIGRA-IA como URL pública

La página del artefacto es un HTML autocontenido. Ya está lista en dos lugares:

- `MIGRA-IA_sitio.html` (raíz) — para enviar el archivo directamente (correo/USB).
- `docs/index.html` (+ `docs/.nojekyll`) — preparada para publicar como sitio web.

> Nota honesta: una URL pública siempre necesita un anfitrión (una cuenta/servicio).
> No se puede crear "de la nada"; abajo van las dos vías más simples.

---

## Opción 1 — Netlify Drop (la más rápida, SIN cuenta)

1. Abre **https://app.netlify.com/drop**
2. Arrastra la carpeta **`docs`** al recuadro de la página.
3. En segundos aparece tu URL pública (p. ej. `https://algo-azar.netlify.app`).
   Esa URL ya es compartible con cualquiera.
4. (Opcional) Crea una cuenta gratis para que la URL sea permanente y renombrable.

Ventaja: cero instalación. Ideal para mostrarlo ya.

---

## Opción 2 — GitHub Pages (permanente y CITABLE para el paper)

Requiere una cuenta de GitHub (gratis). Da una URL estable como
`https://<tu-usuario>.github.io/migra-ia/`, la más adecuada para citar en la tesis
y para archivar luego en Zenodo (ver `docs/GUIA_ZENODO.md`).

### 2.1. Instalar/usar GitHub CLI (opción cómoda)
```powershell
winget install --id GitHub.cli -e
gh auth login          # inicia sesión en tu cuenta de GitHub (una sola vez)
```

### 2.2. Publicar (desde la carpeta del proyecto)
```powershell
git config --global user.name  "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"

git init
git add .
git commit -m "MIGRA-IA v0.1.0 + pagina del artefacto"
git branch -M main

gh repo create migra-ia --public --source=. --push
```

### 2.3. Activar Pages
- En GitHub: repo → **Settings → Pages**
- Source: **Deploy from a branch** · Branch: **main** · Folder: **/docs** · **Save**
- En ~1 minuto tu sitio estará en `https://<tu-usuario>.github.io/migra-ia/`

Para actualizar la página después: edita `docs/index.html`, luego
`git add . && git commit -m "update" && git push`. El sitio se actualiza solo.

`docs/.nojekyll` ya está incluido para que GitHub sirva el HTML tal cual.

---

## Opción 3 — GitHub Pages POR EL NAVEGADOR (sin instalar nada)

Todo con el navegador; no necesitas git ni gh. Da la misma URL permanente.

1. Cuenta de GitHub (gratis): https://github.com/signup
2. Crea un repositorio: https://github.com/new
   - Repository name: `migra-ia`
   - Visibilidad: **Public**
   - NO marques "Add a README"
   - **Create repository**
3. Sube la página:
   - En el repo vacío, pulsa el enlace **"uploading an existing file"**
     (o **Add file -> Upload files**).
   - Arrastra el archivo **`index.html`** que está en la carpeta `docs\` del proyecto.
   - Abajo, pulsa **Commit changes**.
4. Activa Pages:
   - **Settings** (del repo) -> **Pages** (menú izquierdo).
   - Source: **Deploy from a branch**.
   - Branch: **main** · Folder: **/ (root)** · **Save**.
5. Espera ~1 minuto y recarga Settings -> Pages. Aparecerá:
   `https://<tu-usuario>.github.io/migra-ia/`  ← esa es tu URL para compartir y citar.

Nota: subiendo solo `index.html` a la raíz no hace falta `.nojekyll`.
Para actualizar la página luego: Add file -> Upload files (reemplaza index.html) -> Commit.

---

## ¿Cuál elegir?
- **Mostrarlo ya / rápido:** Opción 1 (Netlify Drop).
- **Referencia formal del paper IEEE:** Opción 2 (GitHub Pages) + DOI de Zenodo.
