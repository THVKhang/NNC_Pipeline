# Clock and reset domain crossings: spi_master

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **clean**

## Configuration base

Domains: SYNC; 15 flops. Counts: 

## Configuration min

Domains: SYNC; 15 flops. Counts: 

## Configuration max

Domains: SYNC; 15 flops. Counts: 

