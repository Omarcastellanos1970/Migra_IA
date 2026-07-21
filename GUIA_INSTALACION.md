# 🚀 Guía rápida — Instalar y probar MIGRA-IA

> **Para:** coautores del proyecto (Julio, Isidoro).
> **Tiempo:** ~15 minutos.
> ✅ **Puedes probarlo GRATIS**, sin clave y sin costo, gracias al **modo demo**.

MIGRA-IA es un agente que guía el **diagnóstico de obsolescencia** y la **migración de hardware industrial** (PLC, HMI, redes, variadores, etc.).

---

## ✅ Paso 1 — Aceptar la invitación de GitHub
Revisa tu correo (**incluida la carpeta de spam**). Te llegó un mensaje de **GitHub** que dice *"…invited you to collaborate on Migra_IA"*. Haz clic en **Accept invitation**.
- Si **no tienes cuenta** de GitHub, créala gratis en https://github.com **con ese mismo correo**.

## ✅ Paso 2 — Instalar Python (una sola vez)
1. Entra a https://www.python.org/downloads/ y descarga **Python 3.10 o superior**.
2. Ejecuta el instalador y **‼️ MUY IMPORTANTE:** marca la casilla **"Add Python to PATH"** antes de dar *Install*.
3. Termina la instalación.

## ✅ Paso 3 — Descargar el proyecto
**Opción fácil (recomendada):**
1. Entra al repositorio: **https://github.com/Omarcastellanos1970/Migra_IA**
2. Botón verde **"Code"** → **"Download ZIP"**.
3. Descomprime el ZIP (clic derecho → *Extraer todo*). Te quedará una carpeta con el proyecto.

## ✅ Paso 4 — Instalar el agente (una sola vez)
1. Abre la carpeta del proyecto.
2. En la **barra de direcciones** del explorador de archivos, escribe `powershell` y presiona **Enter** (abre una terminal ya ubicada en esa carpeta).
3. Copia y pega estos comandos, **uno por uno**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
> Si `Activate.ps1` te da un error de permisos, usa en su lugar: `.venv\Scripts\activate.bat`

## ✅ Paso 5 — Ejecutar y probar GRATIS (modo demo)
- **Lo más fácil (Windows):** doble clic en el archivo **`Iniciar_MIGRA-IA.bat`**. Se abrirá una ventana negra y luego tu navegador en http://127.0.0.1:5000
- **O por terminal:** ejecuta `python -m webapp.app` y abre http://127.0.0.1:5000

En el navegador, pulsa **"Modo demo (sin clave)"** → escribe cualquier texto y pulsa *Enviar*.
👉 **Es gratis y no necesita clave de API.** Verás el diagnóstico, el riesgo de obsolescencia (**75.2 / "Riesgo alto"**), el expediente y el informe generado.

> ⚠️ **No cierres la ventana negra** mientras usas el agente. Para apagarlo, ciérrala o pulsa **Ctrl + C**.

## 🔑 Paso 6 (opcional) — Usar el agente real con IA
El modo demo ya muestra todo el motor. Si quieres el **agente conversacional completo** (razonamiento con Claude):
1. Consigue una clave de API en https://console.anthropic.com/settings/keys *(servicio de pago de Anthropic; cada quien usa la suya)*.
2. En la carpeta del proyecto, **copia** el archivo `.env.example` y **renómbralo** a `.env`.
3. Ábrelo con el **Bloc de notas** y reemplaza `sk-ant-...` por tu clave.
4. Vuelve a ejecutar y elige **"Caso real (API)"**.

---

## 🆘 Problemas comunes
| Problema | Solución |
|---|---|
| `"python" no se reconoce…` | No marcaste *"Add Python to PATH"*. Reinstala Python marcando esa casilla. |
| El `.bat` se abre y se cierra de inmediato | Primero completa el **Paso 4** (crear `.venv` e instalar). El lanzador necesita el entorno ya instalado. |
| `Activate.ps1 … scripts is disabled` | Usa `.venv\Scripts\activate.bat`, o ejecuta antes: `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| La página no abre | Espera unos segundos a que arranque; revisa que la ventana negra siga abierta y abre manualmente http://127.0.0.1:5000 |

---

¿Dudas? Escríbele a **Carlos**. 🙂
