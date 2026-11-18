# UART lite: design description

Written as the input of `nnc spec-draft` (the designer's short description; the specification is drafted from it).

A small UART for a single-clock SoC. It sends and receives bytes on a serial line in 8N1 format: one start bit (0),
eight data bits with the least significant bit first, no parity, one stop bit (1). The line is high when idle.

Interfaces (one clock `i_clk`, one active-low asynchronous reset `i_rst_n`):
- Transmit byte stream in: `i_tx_valid`, `o_tx_ready`, `i_tx_data[7:0]` (valid/ready handshake: a byte is
  accepted at a rising clock edge when both valid and ready are 1).
- Receive byte stream out: `o_rx_valid`, `i_rx_ready`, `o_rx_data[7:0]`, with `o_rx_frame_err` qualified by
  `o_rx_valid` (the stop bit was 0). The receiver holds a byte until it is taken.
- Serial line: `o_txd` (idle high), `i_rxd` (asynchronous to `i_clk`: synchronise it with two flip-flops).
- `o_rx_overrun`: one-cycle pulse when a received byte is lost because the previous one was not taken yet.

Bit timing: the bit period is `PARA_UART_CLKS_PER_BIT` clock cycles (parameter, legal range 4 to 65535,
default 16). The transmitter drives each bit for exactly that many cycles. The receiver detects the falling edge
of the start bit, checks the start bit again in its middle, and samples each data bit and the stop bit in the
middle of the bit. A start bit that is high again in its middle is a glitch: no byte is received.

Transmitter: a byte accepted from the stream is sent immediately when the transmitter is idle; `o_tx_ready` is 1
only when the transmitter can accept a byte (no transmit buffer beyond the shift register is required). Back-to-
back bytes follow each other without an idle bit between the stop bit and the next start bit.

Receiver: a received byte appears on `o_rx_data` with `o_rx_valid` = 1 in the cycle after the middle of the stop
bit, and stays until `i_rx_ready` is 1. A byte with a stop bit of 0 is still delivered, with `o_rx_frame_err` = 1.
If a new byte completes while the previous one is still waiting, the new byte is dropped and `o_rx_overrun`
pulses.

Reset: all outputs to their idle values (`o_txd` = 1, valid flags 0, `o_tx_ready` = 1 after reset).

Target: GF180MCU, 50 MHz. Verify at least the default and the minimum bit period.
