# Interactive diagnosis — Siemens SIMATIC S7-300

- Case: CAS-2026-046177
- Agent: MIGRA-IA v0.4.0
- Date: 2026-09-16T21:20:46-06:00
- Overall confidence level: medium_confidence
- Human approval: PENDING (this report is technical assistance; it must be verified by authorized staff before any intervention).

---

## 1. Identification
Interactive case. Siemens SIMATIC S7-300 (CPU 315-2 DP).

## 2. Executive summary
Diagnosis built on the answers given by the user in the interactive demo, with the real risk engine and decision map.

## 3. Confirmed information
24 answers recorded: C08, C10, F01, F12, F13, G01, L01, L03, L07, M01, M04, M06, M07, M09, N02, N03, N05, N06, O02, O07, O08, P01, P04, Q04.

## 4. Unconfirmed information
All the answers come from the user's declaration; none is verified against a nameplate, a manual or an official source.

## 5. Missing data
None recorded.

## 6. Obsolescence status and score
85.0 / 100 — **Critical risk**.

- Life cycle status (weight 0.20): 75 — M01: status declared by the manufacturer = 'Discontinued, still with support and spare parts'.
- Spare parts availability (weight 0.15): 85 — M04: 'Only by special order'. M06 'From 2 to 8 weeks' against C10 '4 to 12 hours': the spare part arrives later than the line can tolerate, so the spare parts strategy does not cover the risk on its own.
- Manufacturer support (weight 0.15): 90 — M09 support contract: 'No'; M07 repair service: 'Yes, from an uncertified third party'.
- Software availability (weight 0.10): 95 — Barrier to accessing the program: N02 operating system 'Windows 7'; N03 license 'Physical key (dongle)'; N05 adapter 'Yes, but untested'; N06 passwords 'No'.
- Backup availability (weight 0.15): 100 — F01: there is no copy of the program. Priority 1: recover it before any decision.
- Compatibility with current systems (weight 0.10): 75 — How much the change drags along: G01 networks from an earlier generation (MPI, Profibus DP); O07 includes instruction list (AWL/STL), with no guaranteed automatic conversion; O08 usa librerias propietarias.
- Fault history (weight 0.05): 55 — L01 6 unplanned stoppages in 12 months; L03 trend 'Increasing'; EXTERNAL ROOT CAUSE not corrected (P01 panel temperature 'Between 40 and 50 C'; P04 puesta a tierra dudosa o inexistente; P04 poor quality of the electrical supply; L07 the machine loses the program, the data or the time without power (flat battery or degraded backup memory)): these faults are not attributable to the controller, so the factor is limited. Correcting it comes before any replacement.
- Production criticality (weight 0.10): 90 — C08 criticality 'High: affects a major line'; C10 tolerable downtime '4 to 12 hours'; Q04 intervention window 'During the annual plant shutdown or the holidays'.

## 7. Risks
Those that follow from the factors above.

## 8. Alternatives
1. **Correction of the root cause (without changing the controller)** — It is assessed FIRST because there is an uncorrected external root cause: P01 panel temperature 'Between 40 and 50 C'; P04 puesta a tierra dudosa o inexistente; P04 poor quality of the electrical supply; L07 the machine loses the program, the data or the time without power (flat battery or degraded backup memory). Replacing the controller without correcting it reproduces the fault on the new equipment.
2. **Rebuilding the program** — There is no verified backup (F01/F06/F07) and there is no way to read the program from the PLC (N05/N06/F13): the program must be rebuilt from the functional survey.
3. **Migration to a modern platform** — M01 'Discontinued, still with support and spare parts' and M06 with a lead time longer than the tolerable downtime: the spare part does not cover the risk, and obsolescence is not reversed by repairing.

## 9. Main recommendation
Migrar a **Siemens S7-1500 or S7-1500R/H as needed** (same brand: conversion with the official tool)

## 10. Preliminary hardware
With no confirmed catalog numbers: they must be verified with the manufacturer and its official selection tool.

## 11. Backup, migration and rollback plan
Procedure MIGRA-IA-PROC-050, progress 57 of 57 steps (50 from the document plus the P1-P7 extension for building the program).

## 12. Test plan
FAT (steps 31-33) and SAT (steps 42-44) of the procedure.

## 13. Confidence level and sources
Medium confidence. Sources: the user's answers and the verified manufacturer catalog. This report comes from a deterministic interactive demonstration, with no language model involved.