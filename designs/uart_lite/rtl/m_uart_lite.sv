// ============================================================================
// Module  : m_uart_lite
// Purpose : Top of uart_lite, a small full-duplex 8N1 UART for a single-clock
//           SoC. Bit period = PARA_UART_CLKS_PER_BIT cycles of i_clk.
//           Transmit valid/ready byte stream in, serial o_txd out; serial
//           i_rxd in (asynchronous, synchronised inside), receive valid/ready
//           byte stream out with frame error flag and overrun pulse.
// Spec    : uart_lite_Design_Specification.md sections 1, 4, 5, 6, 7, 8, 10,
//           13 (transmitter in m_uart_lite_tx, receiver in m_uart_lite_rx).
// ============================================================================
module m_uart_lite #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic       i_clk,
  input  logic       i_rst_n,
  input  logic       i_tx_valid,
  output logic       o_tx_ready,
  input  logic [7:0] i_tx_data,
  output logic       o_rx_valid,
  input  logic       i_rx_ready,
  output logic [7:0] o_rx_data,
  output logic       o_rx_frame_err,
  output logic       o_rx_overrun,
  output logic       o_txd,
  input  logic       i_rxd
);

  // REQ: UL-4-02
  // Middle-of-bit sampling offset H = floor(N / 2) (integer division).
  localparam int LPARA_UART_HALF_BIT = PARA_UART_CLKS_PER_BIT / 2;

`ifndef SYNTHESIS
  // REQ: UL-4-04, UL-14-10, UL-1.2-02, UL-10.8-02
  // Elaboration error for an illegal bit period (legal: 4 to 65535).
  // Kept out of synthesis because RR-11 allows no other system task.
  if ((PARA_UART_CLKS_PER_BIT < 4) || (PARA_UART_CLKS_PER_BIT > 65535)) begin : g_param_illegal
    $error("m_uart_lite: PARA_UART_CLKS_PER_BIT must be 4 to 65535");
  end
`endif

  // REQ: UL-1.2-11, UL-7.1-02, UL-7.1-03, UL-10.7-03, UL-4-01, UL-5-01, UL-7.1-04
  // Transmitter and receiver share only i_clk and i_rst_n; every output port
  // is driven directly by a flip-flop inside the submodules.
  m_uart_lite_tx #(
    .PARA_UART_CLKS_PER_BIT (PARA_UART_CLKS_PER_BIT)
  ) u_tx (
    .i_clk      (i_clk),
    .i_rst_n    (i_rst_n),
    .i_tx_valid (i_tx_valid),
    .i_tx_data  (i_tx_data),
    .o_tx_ready (o_tx_ready),
    .o_txd      (o_txd)
  );

  m_uart_lite_rx #(
    .PARA_UART_CLKS_PER_BIT (PARA_UART_CLKS_PER_BIT),
    .PARA_UART_HALF_BIT     (LPARA_UART_HALF_BIT)
  ) u_rx (
    .i_clk          (i_clk),
    .i_rst_n        (i_rst_n),
    .i_rxd          (i_rxd),
    .i_rx_ready     (i_rx_ready),
    .o_rx_valid     (o_rx_valid),
    .o_rx_data      (o_rx_data),
    .o_rx_frame_err (o_rx_frame_err),
    .o_rx_overrun   (o_rx_overrun)
  );

endmodule
