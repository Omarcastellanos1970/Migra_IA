# MIGRA-IA — Advisory agent for hardware obsolescence and migration

**Select language:** [Español](README.md) · [English](README.en.md)

A conversational agent that assists technical staff **step by step** in
diagnosing hardware obsolescence and planning the migration of industrial
automation systems (PLCs, I/O modules, HMIs, industrial networks, drives, servos
and associated instrumentation).

**Assisted** mode: it recommends, documents and guides; the final approval and
any intervention on real equipment belong to authorized personnel.

> Prototype v0.4.0 built on the Claude API (`claude-opus-4-8`).
> It implements the specification of the document *MIGRA-IA — Master
> questionnaire and functional design of the agent* and the reference guide
> *MIGRA-IA-GUIA-001*.

**Authors:** Carlos Omar Castellanos · Julio Noé Castillo · Isidoro Medina · Luis Loo
**License:** MIT · **DOI (all versions):** [10.5281/zenodo.21480949](https://doi.org/10.5281/zenodo.21480949) — it always resolves to the latest version published in Zenodo.

> **Try it now, without installing anything:** <https://migra-ia.onrender.com>
> — the interactive demo, in the browser, **with no account and no API key**.
> If the first load takes a while, that is the free plan waking the service up (~50 s).

> **Are you a reviewer?** The project can be assessed **with no API key and at no
> cost** using the *interactive demo*. Follow [`ARTIFACT.en.md`](ARTIFACT.en.md).

---

## What it does

- It conducts the **adaptive questionnaire** (sections A-K): the answers enable,
  hide or modify the questions that follow.
- It records user, plant, machine, controller, modules, networks, HMI, functional
  safety, instrumentation and objectives, with **unique identifiers** and a
  **confidence level** for every item of data.
- It computes the **obsolescence risk score** (0-100) by weighting the eight
  factors of Section 6.
- It applies the **mandatory safety rules** (Section 8): it does not invent
  catalog numbers, does not assume compatibility or backups, separates facts,
  inferences and recommendations, and **asks for human approval** before any
  instruction that involves intervening.
- It consults the **knowledge base** *MIGRA-IA-GUIA-001* (six methodological
  stages, chapters, migration routes per manufacturer, test library, templates
  and management annexes) and **cites the guide** in its recommendations.
- It opens the **migration procedure** *MIGRA-IA-PROC-050* (50 numbered steps
  plus the P1-P7 extension for building the program) when changing the CPU is
  decided, and **specializes** it according to the case: with the manufacturer's
  route if the same brand is kept, and with the **porting route between
  manufacturers** when the target is from another brand and the source program is
  accessible.
- It marks **missing data** and **functional safety flags**.
- It generates a **traceable technical report** in Markdown with the standard
  structure of Section 9.
- It saves the whole **case file** (with its audit trail) in `cases/`.

## Requirements

- Python 3.10 or later.
- An Anthropic API key.

## Installation

**Windows (without using the terminal):** double-click **`INSTALL.bat`** and,
when it finishes, double-click **`Start_MIGRA-IA.bat`**. Step by step in
[`START_HERE.txt`](START_HERE.txt).

**Any system:**

```bash
cd MIGRA_IA_Cuestionario_y_Diseno_del_Agente
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# (or in Git Bash:  source .venv/Scripts/activate)

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your key in it:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Language

The agent exists in Spanish and in English. Choose it with the `MIGRA_IA_LANG`
environment variable (`es` by default), or with the **ES | EN** selector in the
web interface:

```bash
# English
set MIGRA_IA_LANG=en        # Windows
export MIGRA_IA_LANG=en     # Git Bash / Linux / macOS
```

The content of each language lives in `data/<language>/`. A language is only
offered once all its files are complete: one language is never served as a
fallback for the other, because that would produce a screen with the two
languages mixed.

## Use

There are two ways of using the same agent. They share the engine
(questionnaire, rules, risk engine and case file); only the interface changes.

### 1. Web app (recommended)

A chat interface in the browser with a live case file panel (risk, assets,
missing data, flags and pending approvals).

```bash
python -m webapp.app
```

Then open **http://127.0.0.1:5000**. On entering, a new case is opened and the
agent begins the diagnosis. Type the information it asks for; the right-hand
panel updates by itself. The **New case** button resets the case file.

### 2. Console (CLI)

```bash
# Open a new case:
python -m migra_ia.agent

# Continue an existing case:
python -m migra_ia.agent CAS-2026-000123
```

Commands inside the console session:

- `/resumen` — shows the current state of the case file.
- `/salir` — finishes and saves.

In both modes the agent asks a few questions at a time. Answer in natural
language; you can state your level of experience to adjust the technical depth.
When the agent proposes an action on the real equipment:

- in the **console** it asks for explicit approval in the terminal;
- on the **web**, for safety, it records it as a *pending approval*
  (it does not carry out the intervention automatically).

## Structure of the project

```
MIGRA_IA_Cuestionario_y_Diseno_del_Agente/
├── data/
│   ├── es/                   # Content in Spanish
│   ├── en/                   # Content in English
│   │   ├── questionnaire.json     # Catalog of questions A-K with adaptive rules
│   │   ├── knowledge_base.json    # Guide MIGRA-IA-GUIA-001 (stages, routes, tests)
│   │   ├── migration_procedure.json
│   │   ├── cpu_manufacturers.json
│   │   └── system_prompt.md       # The prompt is content, not code
│   └── platform_lifecycle.csv     # Measurements of the paper (language-neutral)
├── migra_ia/                 # Reusable engine
│   ├── config.py             # Model, paths, identity and language of the agent
│   ├── prompt.py             # Builds the system prompt of the active language
│   ├── scoring.py            # Obsolescence scoring engine (Sec. 6)
│   ├── case.py               # Traceable case file + IDs + audit trail (Sec. 2, 5, 13)
│   ├── knowledge.py          # Queries to the knowledge base (guide)
│   ├── tools.py              # Tools for recording, risk, approval and report
│   ├── core.py               # Agent turn (used by the web app)
│   └── agent.py              # Conversational loop with streaming (CLI)
├── webapp/                   # Web app (Flask)
│   ├── app.py                # Server and API
│   └── templates/index.html  # Chat interface + case file panel
├── cases/                    # Case files and reports generated (created on use)
├── requirements.txt
└── .env.example
```

## Scope of the MVP

The initial focus recommended by the design document (Section 12.2):

| Category             | MVP scope                                            |
| -------------------- | ---------------------------------------------------- |
| Source platforms     | Siemens S7-300 and S7-400                            |
| Target platform      | Siemens S7-1500                                      |
| Software             | STEP 7 Classic and TIA Portal                        |
| Networks             | MPI, Profibus DP, Profinet, Industrial Ethernet      |
| Elements             | CPU, I/O modules, HMI and drives                     |

The agent works with any brand, but it is worth **validating its accuracy with
real cases** before widening the scope.

## Notice

MIGRA-IA is a **technical assistance** system. It does not replace functional
safety assessments, lockout and tagout procedures, plant standards or the
authorization of competent personnel. Always verify the recommendations before
intervening on real equipment.

## Next steps (roadmap)

1. Enrich the branching rules of the questionnaire in `questionnaire.json`.
2. Add uploading of nameplate images (vision) for reading nameplate data.
3. A database of verified equivalences (with no invented catalog numbers).
4. Export of the report to Word/PDF.
5. Multi-user web interface and relational schema (Section 13).
