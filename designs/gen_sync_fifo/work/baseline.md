# Baseline comparison — gen_sync_fifo

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS common_rtl/002_SyncFIFO/verification @ 53407f2), run as its own script runs it (8 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 0/0, NNC 0/0

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|

## Mutants

The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants that did not compile in NNC are left out). Killed: hand-written **31/35**, NNC **35/35**; killed only by the hand-written testbench 0, only by NNC 4, by neither 0; 1 did not compile under Icarus Verilog.

| Mutant | Line | Operator | Hand-written | NNC |
|---|---|---|---|---|
| M01 | m_vlsit_sfifo_mem.sv:54 | negate_if | killed | killed |
| M02 | m_vlsit_sfifo_wr.sv:222 | and_to_or | survived | killed |
| M03 | m_vlsit_sfifo_rd.sv:123 | ne_to_eq | killed | killed |
| M04 | m_vlsit_sfifo_wr.sv:203 | or_to_and | killed | killed |
| M05 | m_vlsit_sfifo_wr.sv:184 | zero_to_one | killed | killed |
| M06 | m_vlsit_sfifo_rd.sv:198 | and_to_or | killed | killed |
| M07 | m_vlsit_sfifo_rd.sv:174 | eq_to_ne | killed | killed |
| M08 | m_vlsit_sfifo_rd.sv:142 | negate_if | killed | killed |
| M09 | m_vlsit_sfifo_rd.sv:170 | one_to_zero | killed | killed |
| M10 | m_vlsit_sfifo_rd.sv:171 | zero_to_one | killed | killed |
| M11 | m_vlsit_sfifo_wr.sv:270 | ne_to_eq | killed | killed |
| M12 | m_vlsit_sfifo_wr.sv:272 | eq_to_ne | killed | killed |
| M13 | m_vlsit_sfifo_wr.sv:155 | negate_if | killed | killed |
| M14 | m_vlsit_sfifo_wr.sv:183 | zero_to_one | survived | killed |
| M15 | m_vlsit_sfifo_rd.sv:133 | eq_to_ne | killed | killed |
| M16 | m_vlsit_sfifo_rd.sv:140 | negate_if | killed | killed |
| M17 | m_vlsit_sfifo_rd.sv:169 | one_to_zero | killed | killed |
| M18 | m_vlsit_sfifo_rd.sv:213 | zero_to_one | survived | killed |
| M19 | m_vlsit_sfifo_wr.sv:146 | eq_to_ne | killed | killed |
| M20 | m_vlsit_sfifo_wr.sv:222 | negate_if | killed | killed |
| M21 | m_vlsit_sfifo_wr.sv:182 | zero_to_one | killed | killed |
| M22 | m_vlsit_sfifo_rd.sv:198 | eq_to_ne | killed | killed |
| M23 | m_vlsit_sfifo_rd.sv:189 | negate_if | killed | killed |
| M24 | m_vlsit_sfifo_wr.sv:274 | eq_to_ne | killed | killed |
| M25 | m_vlsit_sfifo_wr.sv:216 | negate_if | killed | killed |
| M26 | m_vlsit_sfifo_wr.sv:263 | zero_to_one | killed | killed |
| M27 | m_vlsit_sfifo_rd.sv:216 | eq_to_ne | killed | killed |
| M28 | m_vlsit_sfifo_rd.sv:198 | negate_if | killed | killed |
| M29 | m_vlsit_sfifo_wr.sv:273 | eq_to_ne | killed | killed |
| M30 | m_vlsit_sfifo_wr.sv:208 | negate_if | killed | killed |
| M31 | m_vlsit_sfifo_wr.sv:266 | zero_to_one | survived | killed |
| M32 | m_vlsit_sfifo_rd.sv:140 | eq_to_ne | killed | killed |
| M33 | m_vlsit_sfifo_rd.sv:211 | negate_if | killed | killed |
| M34 | m_vlsit_sfifo_wr.sv:222 | eq_to_ne | not_compiled | killed |
| M35 | m_vlsit_sfifo_wr.sv:261 | negate_if | killed | killed |
| M36 | m_vlsit_sfifo_wr.sv:265 | zero_to_one | killed | killed |
