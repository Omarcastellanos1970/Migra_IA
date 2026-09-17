# Reproducible artifact — MIGRA-IA

**Español:** [ARTIFACT.md](ARTIFACT.md)

**Authors:** Carlos Omar Castellanos · Julio Noé Castillo · Isidoro Medina · Luis Loo
**Version:** 0.4.0 · **License:** MIT

This document is the **artifact evaluation guide** that accompanies the article.
It is written so that a reviewer can run and verify the system on their own
machine, **without an API key and at no cost**, in ~10–15 min.

**It can also be evaluated online, with nothing to install:** <https://migra-ia.onrender.com>
It is the same interactive demo, with no account and no API key, and it is
enough to check the claims in section 1. To reproduce the deterministic outputs
and the case file in `cases/`, the local run described below is still needed.

---

## 1. What it is and what it demonstrates

MIGRA-IA is an assisted conversational agent that guides technical staff step by
step in order to (a) **diagnose the obsolescence** of industrial automation
hardware and (b) **steer the solution**: alternatives, suggested equivalences
and migration procedure.

Claims supported by the artifact (verifiable with the interactive demo):

1. **Adaptive questionnaire** that captures the equipment information by
   sections (A–K) with a confidence level for each item.
2. **Obsolescence risk scoring engine** (0–100) that weighs 8 factors and
   classifies the risk — a **deterministic** result (same case → same score).
3. **Traceable case file** with unique identifiers and an audit trail.
4. **Safety rules**: it does not invent catalog numbers, it flags missing data,
   it raises functional-safety flags and it requires human validation.
5. **Consultancy**: compared alternatives, suggested equivalences (to be
   verified) and a staged migration procedure.
6. **Traceable technical report** generated automatically.
7. **Citable knowledge base** (*MIGRA-IA-GUIA-001*): the agent structures the
   diagnosis along the six stages of the methodology and **cites the guide**
   when it supports its recommendations, consulting it with the `query_guide`
   tool (`data/en/knowledge_base.json`).

---

## 2. Requirements

- **Python 3.10 or above** (tested with 3.14 on Windows 11).
- No GPU. No internet connection for the demo.
- ~150 MB for the virtual environment with its dependencies.

---

## 3. Installation

### Windows — assisted installation (recommended)

Unzip the package and **double-click `INSTALL.bat`**. It detects Python,
creates the virtual environment, installs the dependencies and verifies the
installation. Once it finishes, **double-clicking `Start_MIGRA-IA.bat`**
starts the agent and opens the browser. Step-by-step instructions in
`START_HERE.txt`.

### Any system — manual installation

```bash
# In the project folder:
python -m venv .venv
# Windows:  .venv\Scripts\activate       (or use .venv\Scripts\python.exe)
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Evaluation WITHOUT an API key (interactive demo)

This is the recommended way to review the artifact. It exercises the **real
engine** —questionnaire, risk calculation, decision map, migration procedure,
case file and report— **with no language model**: the result is deterministic
and reproducible, and the same answers always produce the same score.

```bash
python -m webapp.app
```

Open **http://127.0.0.1:5000** and press **"Interactive demo (no API key)"**.
Answer the questions with the number of the option; the equipment you type is
identified against the verified manufacturer catalog, and if migration is
warranted the agent walks through the procedure step by step with the target CPU
you choose.

### Exact reproduction from the command line

To obtain the reference figures without a browser and without having to decide
the answers, the repository includes four scenarios with fixed answers. They are
four runs but **three independent cases**: `otra_marca` is `critico` with a
different target, with the same 24 answers, so its score coincides by
construction and does not count as additional evidence.
`otra_marca_con_codigo` does change four answers —those about access to the
program: known passwords and a backup that opens and compiles— and that is why
its score is different.

```bash
python _interactive_run.py              # critical case, same brand
python _interactive_run.py sano         # case with no obsolescence
python _interactive_run.py otra_marca   # change of brand, no access to the program
python _interactive_run.py otra_marca_con_codigo   # change of brand with the program accessible
```

**Expected outputs** (deterministic):

| Scenario | Risk | Migration | Target |
|---|---|---|---|
| `critico` | **85.0 → "Critical risk"** | open, 57 of 57 steps | Siemens S7-1500 (same brand) |
| `sano` | **11.8 → "Low risk"** | not opened | — |
| `otra_marca` | **85.0 → "Critical risk"** (same answers as `critico`) | open, with `cambio_marca` | OMRON Sysmac NX |
| `otra_marca_con_codigo` | **69.2 → "High risk"** | open, with `cambio_marca` **and** the source program accessible: the porting route applies | OMRON Sysmac NX |

All four close with **24 answers** recorded, **0 missing data** and **1 report**
generated in `cases/`. In the interface, the right-hand panel must show the same
values, together with the registered assets, the missing data, the safety flags
and the pending human approvals.

**Reference outputs already included** (to compare without running anything):
- `docs/en/example_report.md` — technical report generated by the engine.
- `docs/en/example_case_file.json` — traceable case file with its audit trail.

Both come from the `critico` scenario of `python _interactive_run.py`, so the
reviewer can regenerate them and compare: the report closes at **85.0 →
"Critical risk"** with the 24 answers of the scenario and the detail of the
eight factors, each one citing the question codes that support it.

### Direct verification of the risk engine

The risk engine can also be reproduced in isolation:

```bash
python -c "from migra_ia.scoring import compute_risk; r=compute_risk({'estado_ciclo_vida':{'value':90,'justificacion':'end of life'},'disponibilidad_respaldo':{'value':100,'justificacion':'no backup'}}); print(r.score, r.classification)"
```

---

## 5. Evaluation WITH an API key (optional — the real agent)

To try the complete conversational agent (adaptive reasoning with Claude):

1. Copy `.env.example` to `.env` and put a valid `ANTHROPIC_API_KEY` in it
   (a paid Anthropic service; not required in order to evaluate the artifact).
2. `python -m webapp.app` → **"Real case (API)"**, or console:
   `python -m migra_ia.agent`.

The interactive demo is enough to verify every structural claim; the key only
enables natural-language reasoning over arbitrary data.

---

## 6. Structure of the repository

```
migra_ia/        Engine: prompt, scoring (Sec. 6), traceable case file, tools
                 interactive.py — interactive demo, with no language model
                 knowledge.py — queries to the knowledge base
webapp/          Web app (Flask): server + chat interface
data/            questionnaire.json (A–K catalog with adaptive rules)
                 knowledge_base.json (MIGRA-IA-GUIA-001 guide)
docs/            example_report.md, example_case_file.json, Zenodo guide
cases/           Case files and reports generated at run time
INSTALL.bat      Assisted installation on Windows (double click)
Start_MIGRA-IA.bat    Start-up of the agent on Windows (double click)
START_HERE.txt   Step-by-step instructions for non-technical users
ARTIFACT.en.md   This document
BITACORA.md      Log of the assisted sessions: what was asked, what came back,
                 what was verified and what was corrected
_baseline.py     Reproducible baseline (P1, ordinal risk): dataset, grouped
                 split, trivial vs classic, and leakage audit
requirements-freeze.txt  Exact environment in which that report was produced
_labeling.py     Labels for P1/P2 (provisional, rule-based) and the blind
                 labelling form for the panel of experts
VALIDATION_PROTOCOL.md  The six points of the protocol, signed and frozen
_features.py     Contrasts the domain features of the sector with the ones the
                 engine actually uses (generates docs/)
CITATION.cff     Citation metadata
.zenodo.json     Metadata for the Zenodo DOI
LICENSE          MIT
```

---

## 7. Checklist for the reviewer

- [ ] The installation finishes without errors (`INSTALL.bat` on Windows, or
      `pip install -r requirements.txt`).
- [ ] The app starts at http://127.0.0.1:5000.
- [ ] `python _interactive_run.py` produces a risk of **85.0 / "Critical risk"**
      and opens the migration; `... sano` produces **11.8 / "Low risk"** and
      does not open it.
- [ ] `python _interactive_run.py otra_marca` flags the change of brand and
      proposes a target from another manufacturer (OMRON Sysmac NX).
- [ ] `python _interactive_run.py otra_marca_con_codigo` produces **69.2 / "High
      risk"** and, once that same target is set, announces the **porting route
      between manufacturers**: steps 11, 12, 18 and 32 come out with their
      sub-steps C1–C5, and 21 is left as *not applicable* with its rules.
- [ ] The panel shows an asset, a missing datum, a flag and a pending approval.
- [ ] A report is generated in `cases/` with the same structure as
      `docs/en/example_report.md`.
- [ ] The demo shows alternatives, equivalences and a migration procedure.

Estimated evaluation time: **10–15 minutes**.

---

## 8. How to cite

See `CITATION.cff`. Once published on Zenodo, replace the DOI in the `README`
and cite the artifact in the article (see `docs/en/ZENODO_GUIDE.md`).
