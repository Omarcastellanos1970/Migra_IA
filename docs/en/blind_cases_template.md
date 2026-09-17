# MIGRA-IA - Blind assessment of cases

Thank you for helping with this. There are five cases and it takes about an hour.

## What you are asked to do

Read the situation of each case and answer the questionnaire **with your own
professional judgement**, as you would in front of that equipment in the plant.

## Three rules that make the exercise valid

1. **Do not run the MIGRA-IA agent before you finish.** The aim is to
   compare your judgement against the program's; if you see the output first,
   the result no longer measures anything.
2. **Do not consult the other co-authors until you hand it in.** What is
   measured is how much you agree independently.
3. **If something cannot be known from what the case says, answer it as
   'Not known'.** Do not guess. Missing information is a valid result
   and the engine treats it as such.

## How to answer

Write the **number** of the option after the `=`, inside the back
quotes. For example: `` `M01 = 4` ``. You can also write the full text
of the option if you prefer.

Save the file as `answers_YOURNAME.md` and return it.

---

## Case 1

**Context:** Pumping station

**Situation:** Pumping system with a PLC-5, Remote I/O and an old SCADA; the plant has to keep the service continuous.

### Questionnaire - Case 1

**C08.** Machine criticality
  1) Low: can be stopped for several days  2) Medium: partially affects production  3) High: affects a major line  4) Critical: stops the plant or presents a safety risk

`C08 = `

**C10.** Maximum allowable downtime
  1) Less than 1 hour  2) 1 to 4 hours  3) 4 to 12 hours  4) 12 to 24 hours  5) More than 24 hours

`C10 = `

**Q04.** When can the machine be worked on?
  1) There is an already scheduled shutdown  2) During the annual plant shutdown or the holidays  3) Weekends  4) At any time  5) There is no window available

`Q04 = `

**M01.** Product status declared by the manufacturer
  1) Active, on sale  2) Mature, a successor already exists  3) Discontinuation announced (phase-out)  4) Discontinued, still with support and spare parts  5) Discontinued and without support (end of life)  6) Not known

`M01 = `

**M04.** Are NEW spare parts available from the manufacturer or an authorized distributor?
  1) Yes, without difficulty  2) Yes, but with a long lead time  3) Only by special order  4) No  5) It has not been checked

`M04 = `

**M06.** Typical lead time for a critical spare part (CPU or module)
  1) In stock at the plant or locally  2) Less than 2 weeks  3) From 2 to 8 weeks  4) More than 8 weeks  5) Not available  6) Not known

`M06 = `

**M09.** Is there a current support or maintenance contract with the manufacturer or with an integrator?
  1) Yes, current  2) Expired  3) No  4) Not known

`M09 = `

**M07.** Is there a repair service for the CPU or the modules?
  1) Yes, from the manufacturer  2) Yes, from a certified third party  3) Yes, from an uncertified third party  4) No  5) Not known

`M07 = `

**F01.** Is there a copy of the PLC program?
  1) Yes  2) No  3) Not known

`F01 = `

**F06.** Does the backup open correctly?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F06 = `

**F07.** Can it be compiled without errors?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F07 = `

**F12.** Is the CPU operational?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F12 = `

**F13.** Is a programming cable available?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F13 = `

**N02.** Operating system of that PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Virtual machine on a modern computer  7) Other  8) Not known

`N02 = `

**N03.** Type of license of the programming software
  1) Original with a current license  2) Original with an expired license  3) Floating license on a server  4) Physical key (dongle)  5) Demonstration or limited version  6) No license is held  7) Not known

`N03 = `

**N05.** Is the correct programming cable or adapter available, with its driver installed?
  1) Yes, already tested with this PLC  2) Yes, but untested  3) No  4) Not known

`N05 = `

**N06.** Are the passwords for the project and for the protected blocks known?
  1) Yes, all of them  2) Partially  3) No  4) There are no passwords  5) Not known

`N06 = `

**G01.** Which networks does the machine use?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Proprietary network  18) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`G01 = `

**O07.** In which languages is the program written?
  1) Ladder (KOP / LD)  2) Function blocks (FUP / FBD)  3) Instruction list (AWL / STL / IL)  4) Structured text (SCL / ST)  5) GRAFCET, GRAPH or SFC  6) Proprietary blocks from the machine manufacturer  7) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`O07 = `

**O08.** Does the program use blocks, libraries or functions proprietary to the machine manufacturer?
  1) Yes  2) No  3) Not known

`O08 = `

**O02.** Is there motion control, positioning or synchronized axes (servos, electronic cams, interpolation)?
  1) Yes  2) No  3) Not known

`O02 = `

**L01.** How many unplanned stoppages attributable to the control system has the machine had in the last 12 months?
  _write a number_

`L01 = `

**L03.** How has the frequency of faults evolved over the last 24 months?
  1) Increasing  2) Stable  3) Decreasing  4) No faults recorded  5) No record is kept

`L03 = `

**L07.** Does the machine lose the program, the data or the time when power is removed?
  1) Yes  2) No  3) It has not been tested  4) Not known

`L07 = `

**P01.** Temperature inside the control panel
  1) Below 30 C  2) Between 30 and 40 C  3) Between 40 and 50 C  4) Above 50 C  5) It has not been measured

`P01 = `

**P04.** Quality of the electrical supply
  1) Frequent voltage variations  2) Frequent outages  3) Presence of harmonics  4) Without UPS  5) With UPS  6) Grounding verified  7) Grounding doubtful or non-existent  8) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`P04 = `

---

## Case 2

**Context:** Bottling line

**Situation:** Line with an S7-300 CPU, ET 200M I/O, an HMI panel and PROFIBUS drives, with module failures and difficulty in obtaining spare parts.

### Questionnaire - Case 2

**C08.** Machine criticality
  1) Low: can be stopped for several days  2) Medium: partially affects production  3) High: affects a major line  4) Critical: stops the plant or presents a safety risk

`C08 = `

**C10.** Maximum allowable downtime
  1) Less than 1 hour  2) 1 to 4 hours  3) 4 to 12 hours  4) 12 to 24 hours  5) More than 24 hours

`C10 = `

**Q04.** When can the machine be worked on?
  1) There is an already scheduled shutdown  2) During the annual plant shutdown or the holidays  3) Weekends  4) At any time  5) There is no window available

`Q04 = `

**M01.** Product status declared by the manufacturer
  1) Active, on sale  2) Mature, a successor already exists  3) Discontinuation announced (phase-out)  4) Discontinued, still with support and spare parts  5) Discontinued and without support (end of life)  6) Not known

`M01 = `

**M04.** Are NEW spare parts available from the manufacturer or an authorized distributor?
  1) Yes, without difficulty  2) Yes, but with a long lead time  3) Only by special order  4) No  5) It has not been checked

`M04 = `

**M06.** Typical lead time for a critical spare part (CPU or module)
  1) In stock at the plant or locally  2) Less than 2 weeks  3) From 2 to 8 weeks  4) More than 8 weeks  5) Not available  6) Not known

`M06 = `

**M09.** Is there a current support or maintenance contract with the manufacturer or with an integrator?
  1) Yes, current  2) Expired  3) No  4) Not known

`M09 = `

**M07.** Is there a repair service for the CPU or the modules?
  1) Yes, from the manufacturer  2) Yes, from a certified third party  3) Yes, from an uncertified third party  4) No  5) Not known

`M07 = `

**F01.** Is there a copy of the PLC program?
  1) Yes  2) No  3) Not known

`F01 = `

**F06.** Does the backup open correctly?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F06 = `

**F07.** Can it be compiled without errors?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F07 = `

**F12.** Is the CPU operational?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F12 = `

**F13.** Is a programming cable available?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F13 = `

**N02.** Operating system of that PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Virtual machine on a modern computer  7) Other  8) Not known

`N02 = `

**N03.** Type of license of the programming software
  1) Original with a current license  2) Original with an expired license  3) Floating license on a server  4) Physical key (dongle)  5) Demonstration or limited version  6) No license is held  7) Not known

`N03 = `

**N05.** Is the correct programming cable or adapter available, with its driver installed?
  1) Yes, already tested with this PLC  2) Yes, but untested  3) No  4) Not known

`N05 = `

**N06.** Are the passwords for the project and for the protected blocks known?
  1) Yes, all of them  2) Partially  3) No  4) There are no passwords  5) Not known

`N06 = `

**G01.** Which networks does the machine use?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Proprietary network  18) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`G01 = `

**O07.** In which languages is the program written?
  1) Ladder (KOP / LD)  2) Function blocks (FUP / FBD)  3) Instruction list (AWL / STL / IL)  4) Structured text (SCL / ST)  5) GRAFCET, GRAPH or SFC  6) Proprietary blocks from the machine manufacturer  7) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`O07 = `

**O08.** Does the program use blocks, libraries or functions proprietary to the machine manufacturer?
  1) Yes  2) No  3) Not known

`O08 = `

**O02.** Is there motion control, positioning or synchronized axes (servos, electronic cams, interpolation)?
  1) Yes  2) No  3) Not known

`O02 = `

**L01.** How many unplanned stoppages attributable to the control system has the machine had in the last 12 months?
  _write a number_

`L01 = `

**L03.** How has the frequency of faults evolved over the last 24 months?
  1) Increasing  2) Stable  3) Decreasing  4) No faults recorded  5) No record is kept

`L03 = `

**L07.** Does the machine lose the program, the data or the time when power is removed?
  1) Yes  2) No  3) It has not been tested  4) Not known

`L07 = `

**P01.** Temperature inside the control panel
  1) Below 30 C  2) Between 30 and 40 C  3) Between 40 and 50 C  4) Above 50 C  5) It has not been measured

`P01 = `

**P04.** Quality of the electrical supply
  1) Frequent voltage variations  2) Frequent outages  3) Presence of harmonics  4) Without UPS  5) With UPS  6) Grounding verified  7) Grounding doubtful or non-existent  8) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`P04 = `

---

## Case 3

**Context:** Motion machine

**Situation:** Equipment with a CJ, motion modules and an NS HMI; better diagnostics and availability are required.

### Questionnaire - Case 3

**C08.** Machine criticality
  1) Low: can be stopped for several days  2) Medium: partially affects production  3) High: affects a major line  4) Critical: stops the plant or presents a safety risk

`C08 = `

**C10.** Maximum allowable downtime
  1) Less than 1 hour  2) 1 to 4 hours  3) 4 to 12 hours  4) 12 to 24 hours  5) More than 24 hours

`C10 = `

**Q04.** When can the machine be worked on?
  1) There is an already scheduled shutdown  2) During the annual plant shutdown or the holidays  3) Weekends  4) At any time  5) There is no window available

`Q04 = `

**M01.** Product status declared by the manufacturer
  1) Active, on sale  2) Mature, a successor already exists  3) Discontinuation announced (phase-out)  4) Discontinued, still with support and spare parts  5) Discontinued and without support (end of life)  6) Not known

`M01 = `

**M04.** Are NEW spare parts available from the manufacturer or an authorized distributor?
  1) Yes, without difficulty  2) Yes, but with a long lead time  3) Only by special order  4) No  5) It has not been checked

`M04 = `

**M06.** Typical lead time for a critical spare part (CPU or module)
  1) In stock at the plant or locally  2) Less than 2 weeks  3) From 2 to 8 weeks  4) More than 8 weeks  5) Not available  6) Not known

`M06 = `

**M09.** Is there a current support or maintenance contract with the manufacturer or with an integrator?
  1) Yes, current  2) Expired  3) No  4) Not known

`M09 = `

**M07.** Is there a repair service for the CPU or the modules?
  1) Yes, from the manufacturer  2) Yes, from a certified third party  3) Yes, from an uncertified third party  4) No  5) Not known

`M07 = `

**F01.** Is there a copy of the PLC program?
  1) Yes  2) No  3) Not known

`F01 = `

**F06.** Does the backup open correctly?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F06 = `

**F07.** Can it be compiled without errors?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F07 = `

**F12.** Is the CPU operational?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F12 = `

**F13.** Is a programming cable available?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F13 = `

**N02.** Operating system of that PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Virtual machine on a modern computer  7) Other  8) Not known

`N02 = `

**N03.** Type of license of the programming software
  1) Original with a current license  2) Original with an expired license  3) Floating license on a server  4) Physical key (dongle)  5) Demonstration or limited version  6) No license is held  7) Not known

`N03 = `

**N05.** Is the correct programming cable or adapter available, with its driver installed?
  1) Yes, already tested with this PLC  2) Yes, but untested  3) No  4) Not known

`N05 = `

**N06.** Are the passwords for the project and for the protected blocks known?
  1) Yes, all of them  2) Partially  3) No  4) There are no passwords  5) Not known

`N06 = `

**G01.** Which networks does the machine use?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Proprietary network  18) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`G01 = `

**O07.** In which languages is the program written?
  1) Ladder (KOP / LD)  2) Function blocks (FUP / FBD)  3) Instruction list (AWL / STL / IL)  4) Structured text (SCL / ST)  5) GRAFCET, GRAPH or SFC  6) Proprietary blocks from the machine manufacturer  7) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`O07 = `

**O08.** Does the program use blocks, libraries or functions proprietary to the machine manufacturer?
  1) Yes  2) No  3) Not known

`O08 = `

**O02.** Is there motion control, positioning or synchronized axes (servos, electronic cams, interpolation)?
  1) Yes  2) No  3) Not known

`O02 = `

**L01.** How many unplanned stoppages attributable to the control system has the machine had in the last 12 months?
  _write a number_

`L01 = `

**L03.** How has the frequency of faults evolved over the last 24 months?
  1) Increasing  2) Stable  3) Decreasing  4) No faults recorded  5) No record is kept

`L03 = `

**L07.** Does the machine lose the program, the data or the time when power is removed?
  1) Yes  2) No  3) It has not been tested  4) Not known

`L07 = `

**P01.** Temperature inside the control panel
  1) Below 30 C  2) Between 30 and 40 C  3) Between 40 and 50 C  4) Above 50 C  5) It has not been measured

`P01 = `

**P04.** Quality of the electrical supply
  1) Frequent voltage variations  2) Frequent outages  3) Presence of harmonics  4) Without UPS  5) With UPS  6) Grounding verified  7) Grounding doubtful or non-existent  8) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`P04 = `

---

## Case 4

**Context:** Packaging machine

**Situation:** Machine with a MELSEC-A PLC, positioning modules and an old GOT.

### Questionnaire - Case 4

**C08.** Machine criticality
  1) Low: can be stopped for several days  2) Medium: partially affects production  3) High: affects a major line  4) Critical: stops the plant or presents a safety risk

`C08 = `

**C10.** Maximum allowable downtime
  1) Less than 1 hour  2) 1 to 4 hours  3) 4 to 12 hours  4) 12 to 24 hours  5) More than 24 hours

`C10 = `

**Q04.** When can the machine be worked on?
  1) There is an already scheduled shutdown  2) During the annual plant shutdown or the holidays  3) Weekends  4) At any time  5) There is no window available

`Q04 = `

**M01.** Product status declared by the manufacturer
  1) Active, on sale  2) Mature, a successor already exists  3) Discontinuation announced (phase-out)  4) Discontinued, still with support and spare parts  5) Discontinued and without support (end of life)  6) Not known

`M01 = `

**M04.** Are NEW spare parts available from the manufacturer or an authorized distributor?
  1) Yes, without difficulty  2) Yes, but with a long lead time  3) Only by special order  4) No  5) It has not been checked

`M04 = `

**M06.** Typical lead time for a critical spare part (CPU or module)
  1) In stock at the plant or locally  2) Less than 2 weeks  3) From 2 to 8 weeks  4) More than 8 weeks  5) Not available  6) Not known

`M06 = `

**M09.** Is there a current support or maintenance contract with the manufacturer or with an integrator?
  1) Yes, current  2) Expired  3) No  4) Not known

`M09 = `

**M07.** Is there a repair service for the CPU or the modules?
  1) Yes, from the manufacturer  2) Yes, from a certified third party  3) Yes, from an uncertified third party  4) No  5) Not known

`M07 = `

**F01.** Is there a copy of the PLC program?
  1) Yes  2) No  3) Not known

`F01 = `

**F06.** Does the backup open correctly?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F06 = `

**F07.** Can it be compiled without errors?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F07 = `

**F12.** Is the CPU operational?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F12 = `

**F13.** Is a programming cable available?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F13 = `

**N02.** Operating system of that PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Virtual machine on a modern computer  7) Other  8) Not known

`N02 = `

**N03.** Type of license of the programming software
  1) Original with a current license  2) Original with an expired license  3) Floating license on a server  4) Physical key (dongle)  5) Demonstration or limited version  6) No license is held  7) Not known

`N03 = `

**N05.** Is the correct programming cable or adapter available, with its driver installed?
  1) Yes, already tested with this PLC  2) Yes, but untested  3) No  4) Not known

`N05 = `

**N06.** Are the passwords for the project and for the protected blocks known?
  1) Yes, all of them  2) Partially  3) No  4) There are no passwords  5) Not known

`N06 = `

**G01.** Which networks does the machine use?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Proprietary network  18) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`G01 = `

**O07.** In which languages is the program written?
  1) Ladder (KOP / LD)  2) Function blocks (FUP / FBD)  3) Instruction list (AWL / STL / IL)  4) Structured text (SCL / ST)  5) GRAFCET, GRAPH or SFC  6) Proprietary blocks from the machine manufacturer  7) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`O07 = `

**O08.** Does the program use blocks, libraries or functions proprietary to the machine manufacturer?
  1) Yes  2) No  3) Not known

`O08 = `

**O02.** Is there motion control, positioning or synchronized axes (servos, electronic cams, interpolation)?
  1) Yes  2) No  3) Not known

`O02 = `

**L01.** How many unplanned stoppages attributable to the control system has the machine had in the last 12 months?
  _write a number_

`L01 = `

**L03.** How has the frequency of faults evolved over the last 24 months?
  1) Increasing  2) Stable  3) Decreasing  4) No faults recorded  5) No record is kept

`L03 = `

**L07.** Does the machine lose the program, the data or the time when power is removed?
  1) Yes  2) No  3) It has not been tested  4) Not known

`L07 = `

**P01.** Temperature inside the control panel
  1) Below 30 C  2) Between 30 and 40 C  3) Between 40 and 50 C  4) Above 50 C  5) It has not been measured

`P01 = `

**P04.** Quality of the electrical supply
  1) Frequent voltage variations  2) Frequent outages  3) Presence of harmonics  4) Without UPS  5) With UPS  6) Grounding verified  7) Grounding doubtful or non-existent  8) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`P04 = `

---

## Case 5

**Context:** Process skid

**Situation:** Skid with a Quantum, remote I/O, PID loops and Modbus Plus communication.

### Questionnaire - Case 5

**C08.** Machine criticality
  1) Low: can be stopped for several days  2) Medium: partially affects production  3) High: affects a major line  4) Critical: stops the plant or presents a safety risk

`C08 = `

**C10.** Maximum allowable downtime
  1) Less than 1 hour  2) 1 to 4 hours  3) 4 to 12 hours  4) 12 to 24 hours  5) More than 24 hours

`C10 = `

**Q04.** When can the machine be worked on?
  1) There is an already scheduled shutdown  2) During the annual plant shutdown or the holidays  3) Weekends  4) At any time  5) There is no window available

`Q04 = `

**M01.** Product status declared by the manufacturer
  1) Active, on sale  2) Mature, a successor already exists  3) Discontinuation announced (phase-out)  4) Discontinued, still with support and spare parts  5) Discontinued and without support (end of life)  6) Not known

`M01 = `

**M04.** Are NEW spare parts available from the manufacturer or an authorized distributor?
  1) Yes, without difficulty  2) Yes, but with a long lead time  3) Only by special order  4) No  5) It has not been checked

`M04 = `

**M06.** Typical lead time for a critical spare part (CPU or module)
  1) In stock at the plant or locally  2) Less than 2 weeks  3) From 2 to 8 weeks  4) More than 8 weeks  5) Not available  6) Not known

`M06 = `

**M09.** Is there a current support or maintenance contract with the manufacturer or with an integrator?
  1) Yes, current  2) Expired  3) No  4) Not known

`M09 = `

**M07.** Is there a repair service for the CPU or the modules?
  1) Yes, from the manufacturer  2) Yes, from a certified third party  3) Yes, from an uncertified third party  4) No  5) Not known

`M07 = `

**F01.** Is there a copy of the PLC program?
  1) Yes  2) No  3) Not known

`F01 = `

**F06.** Does the backup open correctly?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F06 = `

**F07.** Can it be compiled without errors?   *(answer only if F01 = Yes)*
  1) Yes  2) No  3) Not known

`F07 = `

**F12.** Is the CPU operational?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F12 = `

**F13.** Is a programming cable available?   *(answer only if F01 = No or Not known)*
  1) Yes  2) No  3) Not known

`F13 = `

**N02.** Operating system of that PC
  1) Windows XP  2) Windows 7  3) Windows 10  4) Windows 11  5) Linux  6) Virtual machine on a modern computer  7) Other  8) Not known

`N02 = `

**N03.** Type of license of the programming software
  1) Original with a current license  2) Original with an expired license  3) Floating license on a server  4) Physical key (dongle)  5) Demonstration or limited version  6) No license is held  7) Not known

`N03 = `

**N05.** Is the correct programming cable or adapter available, with its driver installed?
  1) Yes, already tested with this PLC  2) Yes, but untested  3) No  4) Not known

`N05 = `

**N06.** Are the passwords for the project and for the protected blocks known?
  1) Yes, all of them  2) Partially  3) No  4) There are no passwords  5) Not known

`N06 = `

**G01.** Which networks does the machine use?
  1) MPI  2) Profibus DP  3) Profibus PA  4) Profinet  5) Industrial Ethernet  6) Modbus RTU  7) Modbus TCP  8) DeviceNet  9) ControlNet  10) EtherNet/IP  11) CANopen  12) AS-Interface  13) CC-Link  14) EtherCAT  15) RS-232  16) RS-485  17) Proprietary network  18) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`G01 = `

**O07.** In which languages is the program written?
  1) Ladder (KOP / LD)  2) Function blocks (FUP / FBD)  3) Instruction list (AWL / STL / IL)  4) Structured text (SCL / ST)  5) GRAFCET, GRAPH or SFC  6) Proprietary blocks from the machine manufacturer  7) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`O07 = `

**O08.** Does the program use blocks, libraries or functions proprietary to the machine manufacturer?
  1) Yes  2) No  3) Not known

`O08 = `

**O02.** Is there motion control, positioning or synchronized axes (servos, electronic cams, interpolation)?
  1) Yes  2) No  3) Not known

`O02 = `

**L01.** How many unplanned stoppages attributable to the control system has the machine had in the last 12 months?
  _write a number_

`L01 = `

**L03.** How has the frequency of faults evolved over the last 24 months?
  1) Increasing  2) Stable  3) Decreasing  4) No faults recorded  5) No record is kept

`L03 = `

**L07.** Does the machine lose the program, the data or the time when power is removed?
  1) Yes  2) No  3) It has not been tested  4) Not known

`L07 = `

**P01.** Temperature inside the control panel
  1) Below 30 C  2) Between 30 and 40 C  3) Between 40 and 50 C  4) Above 50 C  5) It has not been measured

`P01 = `

**P04.** Quality of the electrical supply
  1) Frequent voltage variations  2) Frequent outages  3) Presence of harmonics  4) Without UPS  5) With UPS  6) Grounding verified  7) Grounding doubtful or non-existent  8) Not known
  _you can mark several, separated by a comma (e.g. 1,3)_

`P04 = `

---
