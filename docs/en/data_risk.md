# Data risk

**Español:** [../riesgo_de_datos.md](../riesgo_de_datos.md)

**Updated on 2026-09-04.** What is missing, who gets it and by when. The facts
are verified against the repository; the **who** and **by when** columns marked
`TO BE DECIDED` have to be set by the team, they do not come from any file.

It is ordered by what blocks, not by what costs.

---

## 1. Labels from the panel of experts — BLOCKS P1 and P2

**What is missing.** The obsolescence class of the nine platforms and their
replacement priority order, issued by engineers without seeing the output of the
engine.

**Why it blocks.** With no external label, the one for P1 is derived from the
same dates that would be the variables: today P1 re-derives a definition instead
of predicting, and that is why the leakage audit leaves **a single admissible
variable**. P2 is simply not evaluated, because its assigned classic model
—*gradient boosting* in ranking mode— needs a reference ordering that does not
exist.

**Status.** The instrument is ready and costs no new work:
`docs/en/labelling_form.md`, with no output of the engine inside it, 20-30
minutes per evaluator. `python _labeling.py comparar` reads what comes back and
measures the agreement between evaluators. In the meantime there is a
provisional rule-based labelling, stamped `provisional_regla`, which **cannot be
published as validation**.

**Who.** Julio Noé Castillo and Isidoro Medina.
**By when.** `TO BE DECIDED` — as of today, 2026-09-04, there is no
communication with them. A single session unblocks both subproblems at once.

## 2. Size of the set — BLOCKS any statistical claim

**What is missing.** The life-cycle table has **9 platforms**. The catalog of
the agent has **130 generations and 469 models**, but only nomenclature: its
fields are family, models, remark and sources. **It carries neither a release
year nor a support horizon.**

**Why it blocks.** With nine rows, each hit is worth 0.111 of accuracy and no
difference between models is sustainable. It is also the reason why `k = 2` is a
ceiling: only two manufacturers contribute class 4.

**What would have to be done.** Put a release date and a declared status on the
130 generations, with an official source per row. It is extraction and
verification work, not programming.

**Who.** `TO BE DECIDED`.
**By when.** `TO BE DECIDED`. Cost reference: the level-C items of eight
platforms have been open since July and closed slowly.

## 3. Level-C items still open — BLOCKS their entry into the paper

**What is missing.** `FUENTES_TABLAS.md` classifies each datum as A/B/C and
carries the rule in writing: *"no level-C datum may pass into the paper without
being closed first"*. Still open: Siemens S5 (1979) and S7-300 (1995 vs. 1994) ·
Rockwell ControlLogix 5550 (**1997 vs. 1999**, unresolved) · Schneider Quantum
(1994), Premium (1996) and M262 (2019) · Mitsubishi QnA (1994) and L (2011) ·
Omron CJ2 (2008) and NX102 (2019).

**Status.** The rule is being respected: **none of those figures is in the
`.tex` files today**, checked. The risk is that they get in without being
closed.

**Who.** `TO BE DECIDED`.
**By when.** Before any of those figures enters the paper.

## 4. End of spare parts not published — 3 of 9 platforms

**What is missing.** `SLC 500`, `Modicon Quantum` and `Modicon Premium` carry
`n.d.` for the end of spare parts and repair. `SLC 500` has no end-of-life
announcement either, and neither do `MELSEC-A/QnA` and `MELSEC AnS/QnAS`: **five
of the nine have some date missing**.

**How it is being handled.** It is not replaced by the worst case. In the
replacement priority there is a band of its own, *end of spare parts NOT
published*, distinct from *no spare parts, confirmed*. Saying "there are no
spare parts any more" about a datum that nobody published would be inventing it.

**Who.** `TO BE DECIDED` — it is obtained by asking the manufacturer or by
locating the official discontinuation notice.
**By when.** `TO BE DECIDED`.

## 5. Four ambiguous dates — resolved by convention, not confirmed

**What is missing.** Four cells admit a `dd/mm` or `mm/dd` reading: the three
dates of `S7-300 / ET 200M` and the announcement of `SYSMAC CS1`. They are
resolved by applying **day first**, like the rest of the table, and the report
marks them `AMBIGUA` cell by cell.

**Impact today: none.** Both readings fall on the same side of the reference
date, so **the class does not change** with either of them. It stops being
harmless if the reference date comes close to those months.

**Who.** `TO BE DECIDED`.
**By when.** Before moving `FECHA_REF`.

## 6. Plant data — declared absent in the paper

**What is missing.** Access to PLC projects in production. The paper already
declares it in Section III-C and defines a four-level data strategy; it is not a
new discovery, it is the constraint we start from.

**Consequence accepted.** The declared objective is evidence equivalent to
**TRL 4-5**, not an industrial demonstration. Field validation is left as future
work and it is written that way.

**Who / by when.** Not applicable: it is a constraint, not a task.

## 7. API key — the real mode has never been tested

**What is missing.** The `ANTHROPIC_API_KEY` of the local `.env` is a
21-character **placeholder**; a real one is more than 100 long. The API returns
`401`. The code gets as far as sending the request.

**Impact.** The interactive demo mode and the whole baseline work with no key,
and they are what gets evaluated. But the agent mode with the API **has never
been exercised end to end**, so it cannot be claimed to work.

**Who.** Carlos Omar Castellanos.
**By when.** `TO BE DECIDED`. It needs a key with credit.

---

## What changes if nothing arrives

If none of the seven is resolved, the work is still publishable but **only as
verification**: it says that the engine behaves as its design declares, not that
its design is right. What cannot be done is to present the current figures as
validation, and that is why each one travels with the provenance of its label.

The one with the most return per effort is **point 1**: 20-30 minutes per
co-author, and it turns P1 into a real learning problem and P2 into something
evaluable.
