# Baseline comparison — async_apb_bridge

The upstream hand-written testbench (VLSIT_ASIC_SOC_AI_SKILLS common_rtl/004_AsyncAPBBridge/verification @ 53407f2), run as its own script runs it (64 runs per RTL), against the same faults as the bug benchmark of the generated verification. A fault is caught when any run fails.

Unmodified RTL: **all runs pass**

**Caught:** hand-written 3/3, NNC 3/3

| Bug | Fault | Hand-written testbench | NNC (generated) |
|---|---|---|---|
| AA1 | PPROT not forwarded | caught (64 runs) | caught |
| AA2 | two-phase acknowledge detected on the wrong level | caught (32 runs) | caught |
| AA3 | PSLVERR dropped on the requester side | caught (64 runs) | caught |
