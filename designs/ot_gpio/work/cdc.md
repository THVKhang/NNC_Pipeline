# Clock and reset domain crossings: ot_gpio

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **clean**

## Configuration base

Domains: SYNC; 195 flops. Counts: SYNC 32

Asynchronous inputs: i_gpio

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_gpio.gen_filter[*].u_filter.gen_async.prim_flop_2sync.intq | 32 | SYNC | i_gpio | 2 |  |

## Configuration sync_off

Domains: SYNC; 131 flops. Counts: 

## Configuration straps_off

Domains: SYNC; 195 flops. Counts: SYNC 32

Asynchronous inputs: i_gpio

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_gpio.gen_filter[*].u_filter.gen_async.prim_flop_2sync.intq | 32 | SYNC | i_gpio | 2 |  |

## Configuration min

Domains: SYNC; 131 flops. Counts: 

