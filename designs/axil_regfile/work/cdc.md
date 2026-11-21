# Clock and reset domain crossings: axil_regfile

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **clean**

## Configuration base

Domains: SYNC; 23 flops. Counts: 

## Configuration min

Domains: SYNC; 16 flops. Counts: 

## Configuration max

Domains: SYNC; 31 flops. Counts: 

## Configuration full_a7

Domains: SYNC; 31 flops. Counts: 

