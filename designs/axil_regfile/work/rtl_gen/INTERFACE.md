# Interface of the top module `m_axil_regfile` (contract, gate G2)

The top module must have exactly these parameters and ports (names, directions, widths).

## Parameters

| Name | Default (keep it) | Chosen value | Legal values | Derived from |
|---|---|---|---|---|
| PARA_NUM_REGS | 8 | 8 | 1 to 16 |  |
| PARA_ADDR_W | 8 | 8 | 7 to 16 |  |
| LPARA_REGS_W | Derived | 256 | - | PARA_NUM_REGS*32 |

Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s computed by the formula. The RTL must work for every legal value, not only the chosen one (the checks run with the chosen values).

## Ports

| Name | Direction | Width | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|
| i_clk | input | 1 | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Not applicable | CLK | Active-low reset |
| i_s_axi_awvalid | input | 1 | Not applicable | CLK | Write address valid |
| o_s_axi_awready | output | 1 | 0 | CLK | Write address ready |
| i_s_axi_awaddr | input | PARA_ADDR_W | Not applicable | CLK | Write byte address; bits [1:0] ignored |
| i_s_axi_awprot | input | 3 | Not applicable | CLK | Write protection type; ignored |
| i_s_axi_wvalid | input | 1 | Not applicable | CLK | Write data valid |
| o_s_axi_wready | output | 1 | 0 | CLK | Write data ready |
| i_s_axi_wdata | input | 32 | Not applicable | CLK | Write data; byte lane i is bits 8i+7..8i |
| i_s_axi_wstrb | input | 4 | Not applicable | CLK | Write strobes; bit i enables byte lane i |
| o_s_axi_bvalid | output | 1 | 0 | CLK | Write response valid |
| i_s_axi_bready | input | 1 | Not applicable | CLK | Write response ready |
| o_s_axi_bresp | output | 2 | 0 | CLK | Write response: 2'b00 OKAY or 2'b10 SLVERR |
| i_s_axi_arvalid | input | 1 | Not applicable | CLK | Read address valid |
| o_s_axi_arready | output | 1 | 0 | CLK | Read address ready |
| i_s_axi_araddr | input | PARA_ADDR_W | Not applicable | CLK | Read byte address; bits [1:0] ignored |
| i_s_axi_arprot | input | 3 | Not applicable | CLK | Read protection type; ignored |
| o_s_axi_rvalid | output | 1 | 0 | CLK | Read data valid |
| i_s_axi_rready | input | 1 | Not applicable | CLK | Read data ready |
| o_s_axi_rdata | output | 32 | 0 | CLK | Read data |
| o_s_axi_rresp | output | 2 | 0 | CLK | Read response: 2'b00 OKAY or 2'b10 SLVERR |
| o_regs | output | LPARA_REGS_W | 0 | CLK | Current values of the read/write registers; register k is bits 32k+31..32k |
| i_status | input | 32 | Not applicable | CLK | SoC status word; returned by a read of address 0x40 |

Clocks: i_clk (relation: single or synchronous).
Resets: i_rst_n (active low, clock i_clk)
