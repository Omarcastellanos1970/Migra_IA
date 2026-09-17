# Scoring rules of the 8 factors

Extracted automatically from `migra_ia/interactive.py` by `_scoring_rules.py`. If the code changes, this document changes.

Each factor produces a value of 0-100 (higher = more risk). The total risk is the weighted mean of the eight, with the weights of Section 6.

## Life cycle status

**Weight 0.20** - implemented in `_f_lifecycle()` - reads: `M01`

*No lookup table: the rule is conditional. See the notes.*

**Notes:** A direct table on M01. If M01 is 'Not known' the factor is NOT scored: it is omitted, the weights are renormalized and the gap is recorded as missing data. It is the only way for the engine not to assume a status that nobody declared.

## Spare parts availability

**Weight 0.15** - implemented in `_f_spare_parts()` - reads: `M04`, `M06`, `C10`

| Answer | Value |
|---|---|
| Yes, without difficulty | 10 |
| Yes, but with a long lead time | 45 |
| Only by special order | 65 |
| No | 95 |
| *(not known)* | no default: see the notes |

**Notes:** M04 sets the base. After that there is a CROSS-CHECK that the table does not show: the lead time (M06) is compared with the downtime the line tolerates (C10). If M06 is at 'From 2 to 8 weeks' or worse, the base is raised to a minimum of 85, because a spare part that arrives later than the plant can bear does not cover the risk on its own.

## Manufacturer support

**Weight 0.15** - implemented in `_f_support()` - reads: `M09`, `M07`

According to `M09`:

| Answer | Value |
|---|---|
| Yes, current | 10 |
| Expired | 60 |
| No | 85 |
| *(not known)* | no default: see the notes |

According to `M07`:

| Answer | Value |
|---|---|
| Yes, from the manufacturer | -15 |
| Yes, from a certified third party | -5 |
| Yes, from an uncertified third party | 5 |
| No | 15 |
| *(any other / not known)* | 0 |

**Notes:** M09 (a current contract) sets the base and M07 (repair service) adjusts it up or down. If M09 is not known, the base stays at 55 unless M07 is not known either, in which case the factor is omitted.

## Software availability

**Weight 0.10** - implemented in `_f_software()` - reads: `N02`, `N03`, `N05`, `N06`

According to `N02`:

| Answer | Value |
|---|---|
| Windows XP | 25 |
| Windows 7 | 20 |
| Windows 10 | 0 |
| Windows 11 | 0 |
| Linux | 0 |
| Virtual machine on a modern computer | 0 |
| *(any other / not known)* | 10 |

According to `N03`:

| Answer | Value |
|---|---|
| Original with a current license | 0 |
| Original with an expired license | 15 |
| Floating license on a server | 5 |
| Physical key (dongle) | 15 |
| Demonstration or limited version | 20 |
| No license is held | 30 |
| *(any other / not known)* | 10 |

According to `N05`:

| Answer | Value |
|---|---|
| Yes, already tested with this PLC | 0 |
| Yes, but untested | 10 |
| No | 25 |
| *(any other / not known)* | 10 |

According to `N06`:

| Answer | Value |
|---|---|
| Yes, all of them | 0 |
| Partially | 15 |
| No | 30 |
| There are no passwords | 0 |
| *(any other / not known)* | 15 |

**Notes:** ACCUMULATOR: it **starts at 20** and adds up the four tables above (N02 + N03 + N05 + N06). A value that is not listed adds the default indicated. The result is clamped to 0-100. The factor is only omitted if all four codes are missing at once.

## Backup availability

**Weight 0.15** - implemented in `_f_backup()` - reads: `F01`, `F06`, `F07`

*No lookup table: the rule is conditional. See the notes.*

**Notes:** A CASCADING CONDITIONAL, there is no table. It is evaluated in this order and stops at the first one that holds:

| Situation | Value |
|---|---|
| F01 was not answered | *factor omitted* |
| F01 = No (no copy exists) | 100 |
| F01 is not known | 90 |
| F06 = No (the backup does not open) | 100 |
| F07 = No (it does not compile) | 90 |
| F06 = Yes and F07 = Yes (verified) | 15 |
| incomplete verification | 70 |

The logic is Rule 3 of the guide: a backup that cannot be verified is treated as absent. That is why 'not known' (90) scores almost like 'does not exist' (100), and only a backup that opens AND compiles drops to 15.

## Compatibility with current systems

**Weight 0.10** - implemented in `_f_compatibility()` - reads: `G01`, `O07`, `O08`, `O02`

*No lookup table: the rule is conditional. See the notes.*

**Notes:** ACCUMULATOR, there is no table. It **starts at 20** and adds for each thing the change drags along:

| Condition | Adds |
|---|---|
| G01 includes a proprietary network | +30 |
| G01 includes a network from an earlier generation* | +15 |
| O07 includes proprietary blocks | +20 |
| O07 includes an instruction list (AWL/STL) | +15 |
| O07 includes GRAFCET / SFC / GRAPH | +10 |
| O08 = Yes (proprietary libraries) | +25 |
| O02 = Yes (motion control) | +20 |

The two for G01 are mutually exclusive: proprietary takes precedence over legacy. Those for O07 accumulate with each other. It is clamped to 0-100.

*Networks considered to be from an earlier generation: MPI, Profibus DP, Profibus PA, DeviceNet, ControlNet, CC-Link, AS-Interface, RS-232, RS-485.

## Fault history

**Weight 0.05** - implemented in `_f_history()` - reads: `L01`, `L03`

| Answer | Value |
|---|---|
| Increasing | 20 |
| Stable | 0 |
| Decreasing | -10 |
| No faults recorded | -15 |
| *(any other / not known)* | 5 |

**Notes:** L01 (the number of stoppages in 12 months) sets the step, which is a conditional and not a table:

| Stoppages in L01 | Value |
|---|---|
| 0 | 10 |
| 1 to 2 | 30 |
| 3 to 5 | 50 |
| more than 5 | 70 |
| no readable number | 45 |

On top of that step the L03 table above is added. Then a CAP is applied: if there is an uncorrected external root cause (a hot cabinet, poor grounding, a deficient power supply, a flat battery), the factor is **limited to 55**, because those faults are not attributable to the controller and replacing it does not correct them. It is the only factor whose value can GO DOWN because of a design rule.

## Production criticality

**Weight 0.10** - implemented in `_f_criticality()` - reads: `C08`, `C10`, `Q04`

According to `C08`:

| Answer | Value |
|---|---|
| Low: can be stopped for several days | 20 |
| Medium: partially affects production | 45 |
| High: affects a major line | 70 |
| Critical: stops the plant or presents a safety risk | 95 |
| *(not known)* | no default: see the notes |

According to `Q04`:

| Answer | Value |
|---|---|
| There is no window available | 15 |
| During the annual plant shutdown or the holidays | 10 |
| Weekends | 5 |
| *(any other / not known)* | 0 |

According to `C10`:

| Answer | Value |
|---|---|
| Less than 1 hour | 20 |
| 1 to 4 hours | 15 |
| 4 to 12 hours | 10 |
| 12 to 24 hours | 5 |
| More than 24 hours | 0 |
| *(any other / not known)* | 0 |

**Notes:** C08 (criticality of the machine) sets the base; C10 (tolerable downtime) and Q04 (intervention window) raise it. If C08 is not known, the whole factor is omitted.

---

## What these tables do not say

All these constants are set by hand, just like the weights. The sensitivity analysis of `_evaluation.py` perturbs **only the eight weights**, not these constants: the 100% stability it reports holds for the weighting, not for the rules. It is the next gap of the same family.

