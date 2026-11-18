# Interface of the top module `m_apb_tlul_bridge` (contract, gate G2)

The top module must have exactly these parameters and ports (names, directions, widths).

## Parameters

| Name | Default (keep it) | Chosen value | Legal values | Derived from |
|---|---|---|---|---|
| PARA_ADDR_W | 32 | 32 | 16 to 32 |  |
| PARA_SRC_W | 8 | 8 | 1 to 8 |  |
| PARA_SRC_ID | 0 | 0 | 0 to 2^PARA_SRC_W - 1 |  |
| PARA_A_USER_W | 1 | 1 | 1 to 32 |  |
| PARA_D_SINK_W | 1 | 1 | 1 to 4 |  |
| PARA_D_USER_W | 1 | 1 | 1 to 32 |  |

Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s computed by the formula. The RTL must work for every legal value, not only the chosen one (the checks run with the chosen values).

## Ports

| Name | Direction | Width | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|
| i_clk_core | input | 1 | Not applicable (clock) | CLK-CORE | Clock for both interfaces |
| i_rst_n_core | input | 1 | Not applicable (reset) | RST-CORE | Active-low reset |
| i_apb_psel | input | 1 | Not used in reset | CLK-CORE | APB select |
| i_apb_penable | input | 1 | Not used in reset | CLK-CORE | APB enable (Access phase) |
| i_apb_pwrite | input | 1 | Not used in reset | CLK-CORE | 1 = write |
| i_apb_paddr | input | PARA_ADDR_W | Not used in reset | CLK-CORE | Byte address |
| i_apb_pprot | input | 3 | Not used | CLK-CORE | Protection type |
| i_apb_pstrb | input | 4 | Not used in reset | CLK-CORE | Write strobes |
| i_apb_pwdata | input | 32 | Not used in reset | CLK-CORE | Write data |
| o_apb_pready | output | 1 | 0 | CLK-CORE | Transfer ready |
| o_apb_prdata | output | 32 | 0 | CLK-CORE | Read data |
| o_apb_pslverr | output | 1 | 0 | CLK-CORE | Transfer error |
| o_tlul_a_valid | output | 1 | 0 | CLK-CORE | Request valid |
| i_tlul_a_ready | input | 1 | Not used in reset | CLK-CORE | Request accepted |
| o_tlul_a_opcode | output | 3 | 0 | CLK-CORE | Request opcode: bit 2 from a flop (1 = Get); bits [1:0] constant 0 (PutFullData 3'b000, Get 3'b100) |
| o_tlul_a_param | output | 3 | 3'b000 | CLK-CORE | Reserved, always 3'b000 |
| o_tlul_a_size | output | 2 | 2'b10 | CLK-CORE | Request size, always 2'b10 (4 bytes) |
| o_tlul_a_source | output | PARA_SRC_W | PARA_SRC_ID | CLK-CORE | Request identifier, always PARA_SRC_ID |
| o_tlul_a_address | output | PARA_ADDR_W | 0 | CLK-CORE | Request address: bits [PARA_ADDR_W-1:2] from flops, bits [1:0] constant 0 |
| o_tlul_a_mask | output | 4 | 4'b1111 | CLK-CORE | Byte lanes, always 4'b1111 |
| o_tlul_a_data | output | 32 | 0 | CLK-CORE | Write data (copy of PWDATA; unused by the device on Get) |
| o_tlul_a_user | output | PARA_A_USER_W | '0 | CLK-CORE | A-channel user bits, always '0 (DEC-004) |
| i_tlul_d_valid | input | 1 | Not used in reset | CLK-CORE | Response valid |
| o_tlul_d_ready | output | 1 | 0 in reset, then 1 (DEC-010) | CLK-CORE | Response accepted |
| i_tlul_d_opcode | input | 3 | Not used in reset | CLK-CORE | Response opcode (3'b000 AccessAck, 3'b001 AccessAckData) |
| i_tlul_d_source | input | PARA_SRC_W | Not used in reset | CLK-CORE | Response identifier, expected PARA_SRC_ID |
| i_tlul_d_data | input | 32 | Not used in reset | CLK-CORE | Read data |
| i_tlul_d_error | input | 1 | Not used in reset | CLK-CORE | Response error |
| i_tlul_d_param | input | 3 | Not used in reset | CLK-CORE | Response parameter (reserved) |
| i_tlul_d_size | input | 2 | Not used in reset | CLK-CORE | Response size |
| i_tlul_d_sink | input | PARA_D_SINK_W | Not used in reset | CLK-CORE | Response sink identifier |
| i_tlul_d_user | input | PARA_D_USER_W | Not used in reset | CLK-CORE | Response user bits |

Clocks: i_clk_core (relation: single or synchronous).
Resets: i_rst_n_core (active low, clock i_clk_core)
