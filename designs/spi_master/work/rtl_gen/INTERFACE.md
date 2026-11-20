# Interface of the top module `m_spi_master` (contract, gate G2)

The top module must have exactly these parameters and ports (names, directions, widths).

## Parameters

| Name | Default (keep it) | Chosen value | Legal values | Derived from |
|---|---|---|---|---|
| PARA_SPI_CLK_DIV | 4 | 4 | 1 to 255 |  |

Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s computed by the formula. The RTL must work for every legal value, not only the chosen one (the checks run with the chosen values).

## Ports

| Name | Direction | Width | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|
| i_clk | input | 1 | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Not applicable | CLK | Active-low reset |
| i_cmd_valid | input | 1 | 0 | CLK | Command stream valid. The environment keeps it 0 while i_rst_n = 0 |
| o_cmd_ready | output | 1 | 1 | CLK | Command stream ready. Does not depend combinationally on any input |
| i_cmd_data | input | 8 | Not applicable | CLK | Byte to send. Captured at the command handshake |
| i_cmd_last | input | 1 | Not applicable | CLK | 1 = this byte ends the burst, and o_cs_n is released after it. Captured at the command handshake |
| o_rsp_valid | output | 1 | 0 | CLK | Response stream valid |
| i_rsp_ready | input | 1 | Not applicable | CLK | Response stream ready |
| o_rsp_data | output | 8 | 0 | CLK | Byte received during the transfer of the matching command |
| o_sclk | output | 1 | Equal to i_cpol (follows it combinationally) | CLK | SPI serial clock |
| o_mosi | output | 1 | 0 | CLK | SPI master-out slave-in data |
| i_miso | input | 1 | Not applicable | CLK | SPI master-in slave-out data. Sampled by i_clk without a synchroniser |
| o_cs_n | output | 1 | 1 | CLK | SPI slave select, active low |
| i_cpol | input | 1 | Not applicable | CLK | SPI clock polarity (SCLK idle level). May change only while o_cs_n = 1 |
| i_cpha | input | 1 | Not applicable | CLK | SPI clock phase. 0 = sample on leading edges, 1 = sample on trailing edges. May change only while o_cs_n = 1 |

Clocks: i_clk (relation: single or synchronous).
Resets: i_rst_n (active low, clock i_clk)
