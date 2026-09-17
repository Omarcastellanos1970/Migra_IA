# 🌐 Publishing MIGRA-IA on the internet (Render — free)

**Select language:** [Español](DESPLIEGUE_RENDER.md) · [English](RENDER_DEPLOYMENT.md)
A guide for putting the agent on a **public URL** that anyone can open, with nothing to install.
We use **Render** because it has a free plan and deploys straight from GitHub.

> The repository already carries the `render.yaml` file with all the configuration ready.

---

## Steps

1. Go to **https://render.com** and create a free account.
   👉 The easiest way: **"Sign in with GitHub"** (use your own `Omarcastellanos1970` account).

2. Authorize Render to see your repositories when it asks you to.

3. In the Render dashboard, at the top right: **New +** → **Blueprint**.

4. Choose your **`Migra_IA`** repository and confirm.
   Render will detect the `render.yaml` file and show the **migra-ia** service.

5. It will ask you for the value of **`ANTHROPIC_API_KEY`**. Here you decide:
   - 🆓 **Free public demo (recommended to start with):** leave it **EMPTY**.
     The **"Interactive demo"** will work for everyone, **at no cost at all**.
   - 🤖 **Real AI agent:** paste your Anthropic key.
     ⚠️ **Careful:** that way, **every visitor** who uses the real mode spends API credit from **your** account.

6. Click on **Apply** (or **Create / Deploy**). Wait a few minutes while it builds.

7. Render will give you a **public URL** similar to:
   **`https://migra-ia.onrender.com`**
   👉 That is the one you share with whoever you want!

---

## Things you should know

- 💤 **Free plan:** the service "goes to sleep" after ~15 min with no visits. The first visit
  after that takes ~50 seconds to "wake it up". It is normal on the free plan.
- 🔒 **Your key is safe:** it is stored **only** in the Render dashboard (as an environment
  variable), **never** in the repository. The `.env` file is still ignored by Git.
- 💾 The conversations live for as long as the service is active (enough for a demonstration).
- 💳 **Cost control:** if you enabled the real AI mode and want to limit the spend,
  you can set a **usage limit** in your Anthropic account (console.anthropic.com),
  or deploy with no key (demo only) in the meantime.

---

## Updating the published page
Every time we make changes and push them to GitHub (`main` branch), Render **redeploys
by itself**. There is nothing else to do.
