# Baseline comparison — async_apb_bridge

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS common_rtl/004_AsyncAPBBridge/verification @ 53407f2), run as its own script runs it (64 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 3/3, NNC 3/3

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|
| AA1 | PPROT not forwarded | caught (64 runs) | caught |
| AA2 | two-phase acknowledge detected on the wrong level | caught (32 runs) | caught |
| AA3 | PSLVERR dropped on the requester side | caught (64 runs) | caught |

## Mutants

The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants that did not compile in NNC are left out). Killed: hand-written **10/12**, NNC **11/12**; killed only by the hand-written testbench 0, only by NNC 1, by neither 1.

| Mutant | Line | Operator | Hand-written | NNC |
|---|---|---|---|---|
| M01 | m_vlsit_apbcdc_slv.sv:159 | negate_if | killed | killed |
| M02 | m_vlsit_apbcdc_slv.sv:202 | zero_to_one | killed | killed |
| M03 | m_vlsit_apbcdc_cell_sync.sv:158 | negate_if | killed | killed |
| M04 | m_vlsit_apbcdc_cell_sync.sv:168 | one_to_zero | killed | killed |
| M05 | m_vlsit_apbcdc_mst.sv:214 | ne_to_eq | survived | killed |
| M06 | m_vlsit_apbcdc_cell_sync.sv:154 | zero_to_one | killed | killed |
| M07 | m_vlsit_apbcdc_cell_sync.sv:171 | eq_to_ne | survived | survived |
| M08 | m_vlsit_apbcdc_mst.sv:208 | negate_if | killed | killed |
| M09 | m_vlsit_apbcdc_slv.sv:207 | ne_to_eq | killed | killed |
| M10 | m_vlsit_apbcdc_slv.sv:179 | eq_to_ne | killed | killed |
| M11 | VLSIT_CELL_SYNC_2FF_RN.sv:37 | zero_to_one | killed | killed |
| M12 | VLSIT_CELL_SYNC_2FF_RN.sv:36 | negate_if | killed | killed |
