# Baseline comparison — apb_tlul_bridge

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS example/apb_tlul_bridge/verification @ 53407f2), run as its own script runs it (2 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 3/3, NNC 3/3

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|
| TL1 | response source ID not checked | caught (2 runs) | caught |
| TL2 | partial-strobe write accepted | caught (2 runs) | caught |
| TL3 | read data returned with an error response | caught (2 runs) | caught |

## Mutants

The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants that did not compile in NNC are left out). Killed: hand-written **33/33**, NNC **33/33**; killed only by the hand-written testbench 0, only by NNC 0, by neither 0.

| Mutant | Line | Operator | Hand-written | NNC |
|---|---|---|---|---|
| M01 | m_apb_if.sv:116 | one_to_zero | killed | killed |
| M02 | m_apb_if.sv:108 | zero_to_one | killed | killed |
| M03 | m_tlul_if.sv:100 | ne_to_eq | killed | killed |
| M04 | m_tlul_if.sv:189 | zero_to_one | killed | killed |
| M05 | m_apb_if.sv:111 | negate_if | killed | killed |
| M06 | m_tlul_if.sv:153 | eq_to_ne | killed | killed |
| M07 | m_tlul_if.sv:130 | negate_if | killed | killed |
| M08 | m_apb_if.sv:62 | eq_to_ne | killed | killed |
| M09 | m_tlul_if.sv:181 | one_to_zero | killed | killed |
| M10 | m_apb_if.sv:112 | one_to_zero | killed | killed |
| M11 | m_apb_if.sv:135 | zero_to_one | killed | killed |
| M12 | m_tlul_if.sv:177 | zero_to_one | killed | killed |
| M13 | m_apb_if.sv:92 | negate_if | killed | killed |
| M14 | m_tlul_if.sv:89 | eq_to_ne | killed | killed |
| M15 | m_tlul_if.sv:157 | negate_if | killed | killed |
| M16 | m_apb_if.sv:115 | eq_to_ne | killed | killed |
| M17 | m_apb_if.sv:113 | one_to_zero | killed | killed |
| M18 | m_apb_if.sv:109 | zero_to_one | killed | killed |
| M19 | m_tlul_if.sv:178 | zero_to_one | killed | killed |
| M20 | m_apb_if.sv:90 | negate_if | killed | killed |
| M21 | m_tlul_if.sv:142 | negate_if | killed | killed |
| M22 | m_apb_if.sv:66 | eq_to_ne | killed | killed |
| M23 | m_apb_if.sv:136 | zero_to_one | killed | killed |
| M24 | m_apb_if.sv:134 | negate_if | killed | killed |
| M25 | m_tlul_if.sv:167 | negate_if | killed | killed |
| M26 | m_apb_if.sv:66 | eq_to_ne | killed | killed |
| M27 | m_apb_if.sv:125 | negate_if | killed | killed |
| M28 | m_tlul_if.sv:188 | negate_if | killed | killed |
| M29 | m_apb_if.sv:115 | negate_if | killed | killed |
| M30 | m_tlul_if.sv:134 | negate_if | killed | killed |
| M31 | m_apb_if.sv:96 | negate_if | killed | killed |
| M32 | m_tlul_if.sv:135 | negate_if | killed | killed |
| M33 | m_tlul_if.sv:176 | negate_if | killed | killed |
