# Interface of the top module `m_vlsit_sfifo_top` (contract, gate G2)

The top module must have exactly these parameters and ports (names, directions, widths).

## Parameters

| Name | Default (keep it) | Chosen value | Legal values | Derived from |
|---|---|---|---|---|
| PARA_SFIFO_DEPTH | 8 | 8 | Any integer of 2 or more, no upper limit (DEC-009) |  |
| PARA_SFIFO_DATA_W | 32 | 32 | 1 or more, no upper limit |  |
| PARA_SFIFO_PTR_RETIME | 0 | 0 | 0 or 1 |  |
| PARA_SFIFO_MEM_USE_MACRO | 0 | 0 | 0 or 1 |  |
| LPARA_ADDR_W | Derived | 3 | At least 1 | $clog2(PARA_SFIFO_DEPTH) |
| LPARA_PTR_W | Derived | 4 | At least 2 | $clog2(2 * PARA_SFIFO_DEPTH) |
| LPARA_OCC_W | Derived | 4 | At least 2 | $clog2(PARA_SFIFO_DEPTH + 1) |

Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s computed by the formula. The RTL must work for every legal value, not only the chosen one (the checks run with the chosen values).

## Ports

| Name | Direction | Width | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|
| i_clk_wr | input | 1 | Not applicable | CLK-WR | Write-domain clock |
| i_rst_n_wr | input | 1 | Not applicable | CLK-WR | Hardware reset of all write-domain state |
| i_wr_en | input | 1 | 0 | CLK-WR | Write request: accepted when i_wr_en = 1 and o_full = 0 |
| i_wr_data | input | PARA_SFIFO_DATA_W | Not applicable | CLK-WR | Word to store |
| i_full_thr | input | LPARA_OCC_W | Not applicable | static, no clock | Threshold of o_full_thr, an occupancy value |
| i_rst_n_sw | input | 1 | 1 | CLK-WR | Software reset request, active-low |
| o_sw_rst_busy | output | 1 | 0 | CLK-WR | Software reset busy: writes are possible again when it is 0 |
| o_full | output | 1 | 0 | CLK-WR | FIFO has no free place in the write view; also 1 while writes are blocked by the software reset |
| o_full_thr | output | 1 | 0 | CLK-WR | Occupancy in the write view is at or above i_full_thr; while writes are blocked it shows the value of an empty FIFO |
| o_overflow | output | 1 | 0 | CLK-WR | A write was requested while the FIFO was full and was dropped |
| i_clk_rd | input | 1 | Not applicable | CLK-RD | Read-domain clock |
| i_rst_n_rd | input | 1 | Not applicable | CLK-RD | Hardware reset of all read-domain state |
| i_rd_en | input | 1 | 0 | CLK-RD | Read request: accepted when i_rd_en = 1 and o_empty = 0 |
| i_empty_thr | input | LPARA_OCC_W | Not applicable | static, no clock | Threshold of o_empty_thr, an occupancy value |
| o_rd_data | output | PARA_SFIFO_DATA_W | Not defined until the first word is stored (not reset) | CLK-RD | Word at the read pointer (show-ahead); the memory output register |
| o_empty | output | 1 | 1 | CLK-RD | FIFO has no word visible to the read side; also 1 while reads are blocked by the software reset |
| o_empty_thr | output | 1 | 1 | CLK-RD | Occupancy in the read view is at or below i_empty_thr; while reads are blocked it is 1 |
| o_underflow | output | 1 | 0 | CLK-RD | A read was requested while the FIFO was empty and was dropped |

Clocks: i_clk_wr, i_clk_rd (relation: single or synchronous).
Resets: i_rst_n_wr (active low, clock i_clk_wr), i_rst_n_rd (active low, clock i_clk_rd)
