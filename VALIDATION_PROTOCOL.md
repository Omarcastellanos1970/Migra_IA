# Validation protocol — ordinal risk and replacement priority

**Español:** [PROTOCOLO_VALIDACION.md](PROTOCOLO_VALIDACION.md)

**Signed on 2026-09-04.** From that date the protocol rules: if a later result is
not to our liking, it is reported all the same. Changing any of the six points
requires writing down here what was changed, when and why, before running
anything again.

What follows is written to be pasted almost literally into the methodology of
the paper.

---

## The contract — half a page, to paste into the methodology

> This is the version that goes into the paper. Everything after it is a working
> annex: it justifies each decision and gives the files where it can be checked,
> but it is not published.

The **unit of observation** is the control platform. The **grouping constraint**
is the manufacturer, and no brand is split between training and test, because
two platforms of the same brand share a life-cycle policy and splitting them
would let the model recognize it on the other side. The **seed**, 42, is
declared even though it is not used: there is no stochastic step. The indices of
the split are stored in the repository.

The **scheme** is cross-validation stratified by obsolescence level while
keeping the grouping, with **k = 2** and **a single repetition**. The *k* is not
a choice: only two manufacturers contribute samples of the top class, so there
is nothing with which to fill a third stratified fold without splitting a brand.
Repeating would add nothing as long as there is no randomness. The
**preprocessing is fitted inside each fold**, never once over the complete set.

The **metrics are frozen** before the final runs. In the ordinal classification
the main one is the **macro $F_1$** —and not the accuracy, which with unbalanced
classes rewards whoever always answers the majority one—, with the accuracy, the
mean ordinal error and the inter-rater agreement as secondary ones. In the
ranking the main one is the **precision in the first three positions**, with the
mean position of the candidates that the reference places at the top and the
mean rank displacement as secondary ones.

**No hyperparameter search is allowed**: they are fixed and declared, and with a
set of this size searching them over the split itself would fit the search to
the validation. The trivial baseline has none, so the search effort is zero for
both models and the comparison is fair.

Every result is **reported as the mean and standard deviation over the folds**,
never as the best number of a single run, and accompanied by the provenance of
the label with which it was obtained.

The **test set** stays aside and **is opened only once**, in the **final review
prior to publication on Zenodo**, with the protocol already closed. Whatever
comes out is what gets published: if it forced a change to the model, that
change starts a new protocol and the set stops being valid for it.

---

## Working annex

### 1. The split

**Unit of observation:** the control platform (a CPU and its family), not the
component and not the plant. Nine units in `data/platform_lifecycle.csv`,
derived from obsolescence Table 2.

**Grouping constraint:** the **manufacturer**. Two platforms of the same brand
share a life-cycle policy, so splitting them between training and test would let
the model learn the policy and recognize it on the other side. No brand is ever
split.

> The field states the grouping as a "migration case" because it assumes
> components that share a case. Here each row is an independent platform and
> there are no cases, so the unit that groups is the brand. It is declared as a
> deviation from the statement, not as an omission.

**Seed:** `42`, declared. **It is not used**: there is no stochastic step — the
fit starts at zeros, the step and the iterations are fixed, and there is no
shuffling and no sampling. This is said explicitly instead of suggesting that
reproducibility depends on it.

**Stored indices:** `data/lifecycle_partition.json`, with the scheme, the *k*,
the reason for the ceiling on *k*, the scope of the preprocessing and the
labels.

**Reference date:** `2026-09-04`, fixed. The classes are derived by comparing
dates against it; using "today" would make the labels change by themselves with
the calendar.

### 2. The validation scheme

**Cross-validation stratified by obsolescence level, grouped by manufacturer.**
**k = 2**, which is the largest possible one: only two manufacturers contribute
samples of class 4 (Mitsubishi with two, Rockwell with one), so there is nothing
with which to fill a third stratified fold without splitting a brand.

- Fold 0 — test: Mitsubishi + Schneider + Siemens (5 samples)
- Fold 1 — test: Omron + Rockwell (4 samples)

**Repetitions: 1.** Repeating adds nothing because there is no randomness: the
same input gives the same output, checked with two runs that are identical byte
by byte. If at some point a stochastic component comes in, this point becomes a
requirement for **5 repetitions with seeds 42, 43, 44, 45 and 46**, and the
report then averages over folds *and* seeds.

**Preprocessing inside the fold.** The mean and the scale with which the age is
standardized are computed **only with the training part of each fold**
(`b1_ordinal_logistic()`). There is no fit made once over the nine rows.

### 3. The metrics — frozen from today

| Subproblem | Main one (decides) | Secondary ones (explain) |
|---|---|---|
| **P1** ordinal risk | **macro F1** | accuracy · mean ordinal error |
| **P2** replacement priority | **precision in the first 3** | mean position of the ones the reference puts at the top · mean rank displacement |

**Why the main one for P1 is the macro F1 and not the accuracy:** the classes
are unbalanced (6 of class 3, 3 of class 4) and there is no sample at all of
classes 1 and 2, so the accuracy rewards whoever always says "class 3".

**Why the one for P2 is precision in the first 3:** the decision the agent
supports is what to start with when the budget does not stretch to everything;
getting the tail right does not change any decision.

The two metrics of P2 are adapted from their usual form, because P2 is a
complete permutation and not a retrieval with a single relevant item. The
adaptation is written in the docstring of `ranking_metrics()`.

### 4. The search that is allowed

**None.** The hyperparameters of the classic model are fixed and declared —
`L2 = 1.0`, step `0.05`, `4000` iterations, start at zeros — and they are not
searched. With nine rows, searching them over the split itself would be fitting
the search to the validation, which is the most common way of inflating a result
without noticing.

The trivial baseline has no hyperparameters, so **the search effort is zero for
both models**, which is what makes the comparison fair.

If the set later grows enough to allow a search, this point requires: the same
grid, the same budget of evaluations for every model, and the search **nested**
inside the training fold.

### 5. The form of the report

**Mean ± sample standard deviation (n−1) over the folds.** Never the best number
of a single run. The pooled figure (micro, the nine predictions in one bag) may
come along as a contrast, always labelled as such and never in place of the
mean.

The per-fold table is published together with the summary: it is what shows the
dispersion that a mean alone hides.

**Every figure comes with the provenance of its label.** As long as the
`procedencia` field of `data/labels_p1_p2.json` says `provisional_regla`, no
number derived from it can be presented as validation.

### 6. The rule of the test set

**Set aside and closed.** It is made up of:

1. the **five case studies** of the MIGRA-IA-GUIA-001 guide, presented blind in
   `docs/en/blind_cases_template.md`, with the key in `_plantilla_clave.json`;
2. the **labels from the panel of experts** —obsolescence class and priority
   order— that are collected with `docs/en/labelling_form.md`.

**It is opened only once**, in the **final review prior to publication on
Zenodo**, with the protocol already closed, and **whatever comes out is what
gets published**. That moment is what fixes the point: not a date on the
calendar, but the milestone of the project —the last review before releasing the
version with a DOI.

Nothing is tuned again after opening it: if the result forces a change to the
model, that change starts a new protocol and the test set stops being valid
for it.

To this day **it has not been opened**. Everything reported comes from the two
development folds.

---

### Debt declared at signing

It is signed in the knowledge that three things are open, and it is signed all
the same so that what comes later cannot accommodate itself to what comes out:

1. **The label of P1 is derived from the same dates that would be the
   variables**, so today P1 is the re-derivation of a definition and not a
   prediction. That is why the leakage audit leaves out every date column and a
   single variable survives, the age. The label from the panel is what turns it
   into a real learning problem.
2. **P2 has no expert reference ordering**, so its assigned classic model
   —*gradient boosting* in ranking mode— has not been evaluated.
3. **The set has nine rows.** No difference between models at this size is
   statistically sustainable, and the report says so instead of leaving it
   implicit.
