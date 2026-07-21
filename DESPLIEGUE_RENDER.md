# 🌐 Publicar MIGRA-IA en internet (Render — gratis)

Guía para poner el agente en una **URL pública** que cualquiera pueda abrir, sin instalar nada.
Usamos **Render** porque tiene plan gratuito y despliega directo desde GitHub.

> El repositorio ya trae el archivo `render.yaml` con toda la configuración lista.

---

## Pasos

1. Entra a **https://render.com** y crea una cuenta gratis.
   👉 Lo más fácil: **"Sign in with GitHub"** (usa tu misma cuenta `Omarcastellanos1970`).

2. Autoriza a Render a ver tus repositorios cuando te lo pida.

3. En el panel de Render, arriba a la derecha: **New +** → **Blueprint**.

4. Elige tu repositorio **`Migra_IA`** y confirma.
   Render detectará el archivo `render.yaml` y mostrará el servicio **migra-ia**.

5. Te pedirá el valor de **`ANTHROPIC_API_KEY`**. Aquí decides:
   - 🆓 **Demo pública gratis (recomendado para empezar):** déjalo **VACÍO**.
     Funcionará el **"Modo demo"** para todos, **sin ningún costo**.
   - 🤖 **Agente IA real:** pega tu clave de Anthropic.
     ⚠️ **Ojo:** así, **cada visitante** que use el modo real gasta API de **tu** cuenta.

6. Clic en **Apply** (o **Create / Deploy**). Espera unos minutos mientras construye.

7. Render te dará una **URL pública** parecida a:
   **`https://migra-ia.onrender.com`**
   👉 ¡Esa es la que compartes con quien quieras!

---

## Cosas que debes saber

- 💤 **Plan gratis:** el servicio "se duerme" tras ~15 min sin visitas. La primera visita
  después tarda ~50 segundos en "despertar". Es normal en el plan gratuito.
- 🔒 **Tu clave está segura:** se guarda **solo** en el panel de Render (variable de
  entorno), **nunca** en el repositorio. El archivo `.env` sigue ignorado por Git.
- 💾 Las conversaciones viven mientras el servicio esté activo (suficiente para demostrar).
- 💳 **Control de costo:** si activaste el modo IA real y quieres limitar el gasto,
  puedes fijar un **límite de uso** en tu cuenta de Anthropic (console.anthropic.com),
  o desplegar sin clave (solo demo) mientras tanto.

---

## Actualizar la página publicada
Cada vez que hagamos cambios y los subamos a GitHub (rama `main`), Render **redepliega
solo**. No hay que hacer nada más.
