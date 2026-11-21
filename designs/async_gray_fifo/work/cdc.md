# Clock and reset domain crossings: async_gray_fifo

Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or handshakes.

Verdict: **review**

## Configuration base

Domains: i_clk_rd, i_clk_wr; 30 flops. Counts: QUALIFIED 32, SYNC 2, SYNC_MULTIBIT 8

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 4 | i_clk_rd | w_wr_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 4 | i_clk_wr | w_rd_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 32 | i_clk_rd | u_vlsit_afifo_mem.gen_array.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_rd | w_req_wr | 2 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_wr | w_ack_rd | 2 |  |

## Configuration cell1

Domains: i_clk_rd, i_clk_wr; 40 flops. Counts: QUALIFIED 32, SYNC 2, SYNC_MULTIBIT 8

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.gen_dff2.w_mid | 4 | i_clk_rd | w_wr_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.gen_dff2.w_mid | 4 | i_clk_wr | w_rd_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 32 | i_clk_rd | u_vlsit_afifo_mem.gen_array.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.gen_dff2.w_mid | 1 | i_clk_rd | w_req_wr | 2 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.gen_dff2.w_mid | 1 | i_clk_wr | w_ack_rd | 2 |  |

## Configuration cell3

Domains: i_clk_rd, i_clk_wr; 30 flops. Counts: QUALIFIED 32, SYNC 2, SYNC_MULTIBIT 8

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 4 | i_clk_rd | w_wr_gray | 3 | 4 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 4 | i_clk_wr | w_rd_gray | 3 | 4 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 32 | i_clk_rd | u_vlsit_afifo_mem.gen_array.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 1 | i_clk_rd | w_req_wr | 3 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync3.gen_rn.u_dont_touch_sync3ff.reg_chain | 1 | i_clk_wr | w_ack_rd | 3 |  |

## Configuration cell4

Domains: i_clk_rd, i_clk_wr; 30 flops. Counts: QUALIFIED 32, SYNC 2, SYNC_MULTIBIT 8

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 4 | i_clk_rd | w_wr_gray | 4 | 4 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 4 | i_clk_wr | w_rd_gray | 4 | 4 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 32 | i_clk_rd | u_vlsit_afifo_mem.gen_array.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 1 | i_clk_rd | w_req_wr | 4 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.genblk1.gen_sync4.gen_rn.u_dont_touch_sync4ff.reg_chain | 1 | i_clk_wr | w_ack_rd | 4 |  |

## Configuration macro

Domains: i_clk_rd, i_clk_wr; 30 flops. Counts: QUALIFIED 32, SYNC 2, SYNC_MULTIBIT 8

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 4 | i_clk_rd | w_wr_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 4 | i_clk_wr | w_rd_gray | 2 | 4 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 32 | i_clk_rd | u_vlsit_afifo_mem.gen_macro.u_vlsit_afifo_ram_macro.u_dont_touch_sram.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_rd | w_req_wr | 2 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_wr | w_ack_rd | 2 |  |

## Configuration small

Domains: i_clk_rd, i_clk_wr; 20 flops. Counts: QUALIFIED 1, SYNC 2, SYNC_MULTIBIT 4

| Kind | Destination register | Bits | Domain | From | Stages | Note |
|---|---|---|---|---|---|---|
| SYNC_MULTIBIT | u_vlsit_afifo_rd.u_sync_wr_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 2 | i_clk_rd | w_wr_gray | 2 | 2 bits of one register synchronized separately: gray code or handshake needed |
| SYNC_MULTIBIT | u_vlsit_afifo_wr.u_sync_rd_gray.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 2 | i_clk_wr | w_rd_gray | 2 | 2 bits of one register synchronized separately: gray code or handshake needed |
| QUALIFIED | o_rd_data | 1 | i_clk_rd | u_vlsit_afifo_mem.gen_array.reg_mem |  | captured under control of u_vlsit_afifo_rd.w_req_s, u_vlsit_afifo_rd.w_wgray_s[0], u_vlsit_afifo_rd.w_wgray_s[1] |
| SYNC | u_vlsit_afifo_rd.u_sync_req.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_rd | w_req_wr | 2 |  |
| SYNC | u_vlsit_afifo_wr.u_sync_ack.gen_bit_cell[*].u_vlsit_afifo_cell_sync.genblk1.genblk1.gen_sync2.gen_rn.u_dont_touch_sync2ff.reg_chain | 1 | i_clk_wr | w_ack_rd | 2 |  |

