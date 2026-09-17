# 🚀 Quick guide — Install and try MIGRA-IA

**Español:** [GUIA_INSTALACION.md](GUIA_INSTALACION.md)

> **For:** the co-authors of the project (Julio, Isidoro).
> **Time:** ~15 minutes.
> ✅ **You can try it FREE**, with no key and at no cost, thanks to the **interactive demo**.

MIGRA-IA is an agent that guides the **obsolescence diagnosis** and the **migration of industrial hardware** (PLC, HMI, networks, drives, etc.).

---

## ✅ Step 1 — Accept the GitHub invitation
Check your email (**including the spam folder**). A message from **GitHub** arrived saying *"…invited you to collaborate on Migra_IA"*. Click on **Accept invitation**.
- If you **do not have a GitHub account**, create one for free at https://github.com **with that same email address**.

## ✅ Step 2 — Install Python (once only)
1. Go to https://www.python.org/downloads/ and download **Python 3.10 or above**.
2. Run the installer and **‼️ VERY IMPORTANT:** tick the box **"Add Python to PATH"** before pressing *Install*.
3. Finish the installation.

## ✅ Step 3 — Download the project
**The easy option (recommended):**
1. Go to the repository: **https://github.com/Omarcastellanos1970/Migra_IA**
2. Green **"Code"** button → **"Download ZIP"**.
3. Unzip the ZIP (right-click → *Extract all*). You will end up with a folder containing the project.

## ✅ Step 4 — Install the agent (once only)
1. Open the project folder.
2. In the **address bar** of the file explorer, type `powershell` and press **Enter** (it opens a terminal already located in that folder).
3. Copy and paste these commands, **one by one**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
> If `Activate.ps1` gives you a permissions error, use this instead: `.venv\Scripts\activate.bat`

## ✅ Step 5 — Run it and try it FREE (interactive demo)
- **The easiest way (Windows):** double-click on the file **`Start_MIGRA-IA.bat`**. A black window will open and then your browser at http://127.0.0.1:5000
- **Or from the terminal:** run `python -m webapp.app` and open http://127.0.0.1:5000

In the browser, press **"Interactive demo (no API key)"** → answer each question with the number of the option and press *Send*.
👉 **It is free and needs no API key.** You will see the diagnosis, the obsolescence risk computed on **your** answers, the case file and the generated report.

> ⚠️ **Do not close the black window** while you are using the agent. To shut it down, close it or press **Ctrl + C**.

## 🔑 Step 6 (optional) — Use the real agent with AI
The interactive demo already shows the whole engine. If you want the **complete conversational agent** (reasoning with Claude):
1. Get an API key at https://console.anthropic.com/settings/keys *(a paid Anthropic service; everyone uses their own)*.
2. In the project folder, **copy** the file `.env.example` and **rename it** to `.env`.
3. Open it with **Notepad** and replace `sk-ant-...` with your key.
4. Run it again and choose **"Real case (API)"**.

---

## 🆘 Common problems
| Problem | Solution |
|---|---|
| `"python" is not recognized…` | You did not tick *"Add Python to PATH"*. Reinstall Python ticking that box. |
| The `.bat` opens and closes immediately | Complete **Step 4** first (create `.venv` and install). The launcher needs the environment already installed. |
| `Activate.ps1 … scripts is disabled` | Use `.venv\Scripts\activate.bat`, or run beforehand: `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| The page does not open | Wait a few seconds for it to start; check that the black window is still open and open http://127.0.0.1:5000 manually |

---

Any questions? Write to **Carlos**. 🙂
