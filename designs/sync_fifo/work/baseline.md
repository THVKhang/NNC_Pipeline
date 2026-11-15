# Baseline comparison — sync_fifo

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS common_rtl/002_SyncFIFO/verification @ 53407f2), run as its own script runs it (8 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 3/3, NNC 3/3

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|
| SF1 | full flag one entry early | caught (8 runs) | caught |
| SF2 | overflow pulse also for a blocked write | caught (8 runs) | caught |
| SF3 | empty threshold compare off by one | caught (8 runs) | caught |

## Mutants

The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants that did not compile in NNC are left out). Killed: hand-written **29/36**, NNC **36/36**; killed only by the hand-written testbench 0, only by NNC 7, by neither 0.

| Mutant | Line | Operator | Hand-written | NNC |
|---|---|---|---|---|
| M01 | m_vlsit_sfifo_rd.sv:180 | and_to_or | killed | killed |
| M02 | m_vlsit_sfifo_wr.sv:153 | zero_to_one | survived | killed |
| M03 | m_vlsit_sfifo_wr.sv:131 | one_to_zero | killed | killed |
| M04 | m_vlsit_sfifo_rd.sv:136 | negate_if | killed | killed |
| M05 | m_vlsit_sfifo_rd.sv:104 | ne_to_eq | killed | killed |
| M06 | m_vlsit_sfifo_rd.sv:126 | one_to_zero | killed | killed |
| M07 | m_vlsit_sfifo_rd.sv:123 | eq_to_ne | killed | killed |
| M08 | m_vlsit_sfifo_wr.sv:219 | eq_to_ne | killed | killed |
| M09 | m_vlsit_sfifo_mem.sv:52 | negate_if | killed | killed |
| M10 | m_vlsit_sfifo_wr.sv:141 | negate_if | killed | killed |
| M11 | m_vlsit_sfifo_wr.sv:216 | ne_to_eq | killed | killed |
| M12 | m_vlsit_sfifo_rd.sv:149 | zero_to_one | survived | killed |
| M13 | m_vlsit_sfifo_wr.sv:192 | and_to_or | survived | killed |
| M14 | m_vlsit_sfifo_wr.sv:213 | zero_to_one | killed | killed |
| M15 | m_vlsit_sfifo_wr.sv:128 | one_to_zero | killed | killed |
| M16 | m_vlsit_sfifo_rd.sv:175 | negate_if | killed | killed |
| M17 | m_vlsit_sfifo_rd.sv:109 | ne_to_eq | killed | killed |
| M18 | m_vlsit_sfifo_rd.sv:123 | one_to_zero | killed | killed |
| M19 | m_vlsit_sfifo_rd.sv:180 | eq_to_ne | killed | killed |
| M20 | m_vlsit_sfifo_wr.sv:128 | eq_to_ne | killed | killed |
| M21 | m_vlsit_sfifo_wr.sv:212 | negate_if | killed | killed |
| M22 | m_vlsit_sfifo_wr.sv:110 | ne_to_eq | survived | killed |
| M23 | m_vlsit_sfifo_rd.sv:147 | zero_to_one | killed | killed |
| M24 | m_vlsit_sfifo_wr.sv:150 | zero_to_one | survived | killed |
| M25 | m_vlsit_sfifo_rd.sv:211 | negate_if | killed | killed |
| M26 | m_vlsit_sfifo_rd.sv:105 | ne_to_eq | survived | killed |
| M27 | m_vlsit_sfifo_rd.sv:145 | one_to_zero | killed | killed |
| M28 | m_vlsit_sfifo_rd.sv:151 | eq_to_ne | killed | killed |
| M29 | m_vlsit_sfifo_wr.sv:192 | eq_to_ne | killed | killed |
| M30 | m_vlsit_sfifo_wr.sv:188 | negate_if | killed | killed |
| M31 | m_vlsit_sfifo_wr.sv:109 | ne_to_eq | killed | killed |
| M32 | m_vlsit_sfifo_rd.sv:201 | zero_to_one | survived | killed |
| M33 | m_vlsit_sfifo_wr.sv:151 | zero_to_one | killed | killed |
| M34 | m_vlsit_sfifo_rd.sv:190 | negate_if | killed | killed |
| M35 | m_vlsit_sfifo_rd.sv:146 | one_to_zero | killed | killed |
| M36 | m_vlsit_sfifo_rd.sv:203 | eq_to_ne | killed | killed |
