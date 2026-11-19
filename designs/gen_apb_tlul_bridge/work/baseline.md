# Baseline comparison — gen_apb_tlul_bridge

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS example/apb_tlul_bridge/verification @ 53407f2), run as its own script runs it (2 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 0/0, NNC 0/0

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|

## Mutants

The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants that did not compile in NNC are left out). Killed: hand-written **36/36**, NNC **36/36**; killed only by the hand-written testbench 0, only by NNC 0, by neither 0.

| Mutant | Line | Operator | Hand-written | NNC |
|---|---|---|---|---|
| M01 | m_apb_if.sv:80 | or_to_and | killed | killed |
| M02 | m_tlul_if.sv:196 | zero_to_one | killed | killed |
| M03 | m_apb_if.sv:168 | one_to_zero | killed | killed |
| M04 | m_tlul_if.sv:117 | eq_to_ne | killed | killed |
| M05 | m_apb_if.sv:177 | zero_to_one | killed | killed |
| M06 | m_apb_if.sv:167 | negate_if | killed | killed |
| M07 | m_apb_if.sv:92 | and_to_or | killed | killed |
| M08 | m_tlul_if.sv:127 | ne_to_eq | killed | killed |
| M09 | m_apb_if.sv:92 | eq_to_ne | killed | killed |
| M10 | m_tlul_if.sv:117 | and_to_or | killed | killed |
| M11 | m_tlul_if.sv:127 | or_to_and | killed | killed |
| M12 | m_tlul_if.sv:194 | one_to_zero | killed | killed |
| M13 | m_tlul_if.sv:163 | negate_if | killed | killed |
| M14 | m_tlul_if.sv:209 | zero_to_one | killed | killed |
| M15 | m_apb_if.sv:169 | one_to_zero | killed | killed |
| M16 | m_tlul_if.sv:106 | eq_to_ne | killed | killed |
| M17 | m_apb_if.sv:164 | zero_to_one | killed | killed |
| M18 | m_apb_if.sv:163 | negate_if | killed | killed |
| M19 | m_apb_if.sv:88 | and_to_or | killed | killed |
| M20 | m_apb_if.sv:80 | eq_to_ne | killed | killed |
| M21 | m_tlul_if.sv:106 | and_to_or | killed | killed |
| M22 | m_tlul_if.sv:117 | or_to_and | killed | killed |
| M23 | m_tlul_if.sv:227 | one_to_zero | killed | killed |
| M24 | m_tlul_if.sv:208 | negate_if | killed | killed |
| M25 | m_tlul_if.sv:192 | zero_to_one | killed | killed |
| M26 | m_apb_if.sv:172 | one_to_zero | killed | killed |
| M27 | m_tlul_if.sv:108 | eq_to_ne | killed | killed |
| M28 | m_apb_if.sv:176 | zero_to_one | killed | killed |
| M29 | m_apb_if.sv:115 | negate_if | killed | killed |
| M30 | m_apb_if.sv:74 | and_to_or | killed | killed |
| M31 | m_tlul_if.sv:108 | and_to_or | killed | killed |
| M32 | m_tlul_if.sv:193 | negate_if | killed | killed |
| M33 | m_tlul_if.sv:225 | zero_to_one | killed | killed |
| M34 | m_apb_if.sv:165 | zero_to_one | killed | killed |
| M35 | m_apb_if.sv:142 | negate_if | killed | killed |
| M36 | m_apb_if.sv:74 | and_to_or | killed | killed |
