# Publishing the MIGRA-IA page as a public URL

**Español:** [PUBLICAR_SITIO.md](PUBLICAR_SITIO.md)

The artifact page is a self-contained HTML file. It is already in place in two locations:

- `MIGRA-IA_sitio.html` (root) — to send the file directly (email/USB).
- `docs/index.html` (+ `docs/.nojekyll`) — ready to be published as a website.

> An honest note: a public URL always needs a host (an account/service).
> It cannot be created "out of nothing"; the two simplest routes are below.

---

## Option 1 — Netlify Drop (the fastest one, NO account)

1. Open **https://app.netlify.com/drop**
2. Drag the **`docs`** folder onto the box on the page.
3. In seconds your public URL appears (e.g. `https://something-random.netlify.app`).
   That URL is already shareable with anyone.
4. (Optional) Create a free account so that the URL is permanent and can be renamed.

Advantage: zero installation. Ideal for showing it right away.

---

## Option 2 — GitHub Pages (permanent and CITABLE for the paper)

It needs a GitHub account (free). It gives a stable URL such as
`https://<your-user>.github.io/migra-ia/`, the most suitable one to cite in the thesis
and to archive later on Zenodo (see `docs/en/ZENODO_GUIDE.md`).

### 2.1. Install/use the GitHub CLI (the comfortable option)
```powershell
winget install --id GitHub.cli -e
gh auth login          # sign in to your GitHub account (once only)
```

### 2.2. Publish (from the project folder)
```powershell
git config --global user.name  "Your Name"
git config --global user.email "your-email@example.com"

git init
git add .
git commit -m "MIGRA-IA v0.1.0 + pagina del artefacto"
git branch -M main

gh repo create migra-ia --public --source=. --push
```

### 2.3. Enable Pages
- On GitHub: repo → **Settings → Pages**
- Source: **Deploy from a branch** · Branch: **main** · Folder: **/docs** · **Save**
- In ~1 minute your site will be at `https://<your-user>.github.io/migra-ia/`

To update the page afterwards: edit `docs/index.html`, then
`git add . && git commit -m "update" && git push`. The site updates by itself.

`docs/.nojekyll` is already included so that GitHub serves the HTML as it is.

---

## Option 3 — GitHub Pages FROM THE BROWSER (nothing to install)

Everything from the browser; you need neither git nor gh. It gives the same permanent URL.

1. A GitHub account (free): https://github.com/signup
2. Create a repository: https://github.com/new
   - Repository name: `migra-ia`
   - Visibility: **Public**
   - Do NOT tick "Add a README"
   - **Create repository**
3. Upload the page:
   - In the empty repo, click on the link **"uploading an existing file"**
     (or **Add file -> Upload files**).
   - Drag the **`index.html`** file that is in the project's `docs\` folder.
   - At the bottom, press **Commit changes**.
4. Enable Pages:
   - **Settings** (of the repo) -> **Pages** (left-hand menu).
   - Source: **Deploy from a branch**.
   - Branch: **main** · Folder: **/ (root)** · **Save**.
5. Wait ~1 minute and reload Settings -> Pages. It will show:
   `https://<your-user>.github.io/migra-ia/`  ← that is your URL to share and to cite.

Note: uploading only `index.html` to the root means `.nojekyll` is not needed.
To update the page later: Add file -> Upload files (replace index.html) -> Commit.

---

## Which one to choose?
- **To show it right away / quickly:** Option 1 (Netlify Drop).
- **Formal reference for the IEEE paper:** Option 2 (GitHub Pages) + a Zenodo DOI.
