# Interface of the top module `m_uart_lite` (contract, gate G2)

The top module must have exactly these parameters and ports (names, directions, widths).

## Parameters

| Name | Default (keep it) | Chosen value | Legal values | Derived from |
|---|---|---|---|---|
| PARA_UART_CLKS_PER_BIT | 16 | 16 | 4 to 65535 |  |

Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s computed by the formula. The RTL must work for every legal value, not only the chosen one (the checks run with the chosen values).

## Ports

| Name | Direction | Width | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|
| i_clk | input | 1 | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Not applicable | CLK | Active-low reset |
| i_tx_valid | input | 1 | Not applicable | CLK | Transmit stream: i_tx_data holds a byte to send |
| o_tx_ready | output | 1 | 1 | CLK | Transmit stream: the transmitter can accept a byte at the next edge |
| i_tx_data | input | 8 | Not applicable | CLK | Transmit stream: byte to send; bit 0 is sent first |
| o_rx_valid | output | 1 | 0 | CLK | Receive stream: the holding register holds a byte |
| i_rx_ready | input | 1 | Not applicable | CLK | Receive stream: the consumer takes the held byte at this edge |
| o_rx_data | output | 8 | 0 | CLK | Receive stream: received byte; bit 0 was received first; qualified by o_rx_valid |
| o_rx_frame_err | output | 1 | 0 | CLK | Receive stream: 1 when the stop bit of the held byte was sampled as 0; qualified by o_rx_valid |
| o_rx_overrun | output | 1 | 0 | CLK | One-cycle pulse: a received byte was dropped because the holding register was full |
| o_txd | output | 1 | 1 | CLK | Serial transmit line, idle high |
| i_rxd | input | 1 | Not applicable | ASYNC | Serial receive line, idle high, asynchronous to i_clk, synchronised inside the block |

Clocks: i_clk (relation: single or synchronous).
Resets: i_rst_n (active low, clock i_clk)
