# Clock and reset domain crossings: uart_lite

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **clean**

## Configuration base

Domains: SYNC; 16 flops. Counts: SYNC 1

Asynchronous inputs: i_rxd

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_rx.r_rxd_meta | 1 | SYNC | i_rxd | 2 |  |

## Configuration min

Domains: SYNC; 16 flops. Counts: SYNC 1

Asynchronous inputs: i_rxd

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_rx.r_rxd_meta | 1 | SYNC | i_rxd | 2 |  |

## Configuration odd

Domains: SYNC; 16 flops. Counts: SYNC 1

Asynchronous inputs: i_rxd

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_rx.r_rxd_meta | 1 | SYNC | i_rxd | 2 |  |

## Configuration wide

Domains: SYNC; 16 flops. Counts: SYNC 1

Asynchronous inputs: i_rxd

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC | u_rx.r_rxd_meta | 1 | SYNC | i_rxd | 2 |  |

