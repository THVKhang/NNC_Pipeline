# SPI master: design description

Written as the input of `nnc spec-draft` (the designer's short description; the specification is drafted from it).

A small SPI master for a single-clock SoC. It shifts one byte out on MOSI and one byte in from MISO per
transfer, with one slave select. Software gives it bytes through a stream and gets the received bytes back
through another stream.

Interfaces (one clock `i_clk`, one active-low asynchronous reset `i_rst_n`):
- Command stream in: `i_cmd_valid`, `o_cmd_ready`, `i_cmd_data[7:0]` (the byte to send) and `i_cmd_last`
  (1 when this byte ends the burst: slave select is released after it). A command is accepted at a rising
  clock edge when valid and ready are both 1.
- Response stream out: `o_rsp_valid`, `i_rsp_ready`, `o_rsp_data[7:0]` (the byte received during the transfer
  of the matching command). The master must not lose a received byte: if the response is not taken, it does
  not start the next transfer.
- SPI pins: `o_sclk`, `o_mosi`, `i_miso` (from the slave, sampled with the internal clock; no synchroniser is
  needed because the slave drives it from SCLK), `o_cs_n` (active low).
- Mode: `i_cpol` and `i_cpha` select the SPI mode 0 to 3 (standard meaning). They may change only while
  `o_cs_n` = 1; the master uses the values present when a burst starts.

Timing: SCLK runs at `i_clk` divided by 2 x `PARA_SPI_CLK_DIV` (parameter, legal 1 to 255, default 4), so each
SCLK half period is `PARA_SPI_CLK_DIV` clock cycles. Data are sent MSB first. Slave select goes low at least one
SCLK half period before the first SCLK edge and goes high at least one half period after the last edge of a
burst; between two bursts it stays high for at least one half period. Bytes of one burst follow each other
without a gap when the next command is already valid; otherwise SCLK pauses in its idle level with slave select
still low until the next command arrives.

Reset: `o_cs_n` = 1, `o_sclk` at the idle level of the current `i_cpol`, `o_mosi` = 0, no response valid,
`o_cmd_ready` = 1.

Target: GF180MCU, 50 MHz. Verify the four modes, the default divider and the minimum divider.
