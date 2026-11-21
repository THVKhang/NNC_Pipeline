# Clock and reset domain crossings: async_apb_bridge

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **review**

## Configuration apb4

Domains: i_clk_mst, i_clk_slv; 14 flops. Counts: QUALIFIED 105, SYNC 2

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_mst | w_ack | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_req | 2 |  |

## Configuration 4ph

Domains: i_clk_mst, i_clk_slv; 14 flops. Counts: QUALIFIED 105, SYNC 2

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_mst | w_ack | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_req | 2 |  |

## Configuration apb5

Domains: i_clk_mst, i_clk_slv; 16 flops. Counts: QUALIFIED 105, SYNC 3

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_mst | w_ack | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_req | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_wk.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_wakeup | 2 |  |

## Configuration user

Domains: i_clk_mst, i_clk_slv; 16 flops. Counts: QUALIFIED 129, SYNC 3

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pauser | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pbuser | 4 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pruser | 8 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwuser | 8 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_mst | w_ack | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_req | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_wk.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_wakeup | 2 |  |

## Configuration sync3

Domains: i_clk_mst, i_clk_slv; 14 flops. Counts: QUALIFIED 105, SYNC 2

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 1 | i_clk_mst | w_ack | 3 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 1 | i_clk_slv | w_req | 3 |  |

## Configuration sync4

Domains: i_clk_mst, i_clk_slv; 14 flops. Counts: QUALIFIED 105, SYNC 2

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 32 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 4 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 32 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 1 | i_clk_mst | w_ack | 4 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 1 | i_clk_slv | w_req | 4 |  |

## Configuration min

Domains: i_clk_mst, i_clk_slv; 14 flops. Counts: QUALIFIED 23, SYNC 2

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| QUALIFIED | o_apb_paddr | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pprot | 3 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_prdata | 8 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pslverr | 1 | i_clk_mst | w_resp_payload |  | captured under control of u_vlsit_apbcdc_mst.w_ack_s |
| QUALIFIED | o_apb_pstrb | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwdata | 8 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| QUALIFIED | o_apb_pwrite | 1 | i_clk_slv | w_req_payload |  | captured under control of u_vlsit_apbcdc_slv.w_req_s |
| SYNC | u_vlsit_apbcdc_mst.u_sync_ack.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_mst | w_ack | 2 |  |
| SYNC | u_vlsit_apbcdc_slv.u_sync_req.gen_bit_cell[*].u_vlsit_apbcdc_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_slv | w_req | 2 |  |

