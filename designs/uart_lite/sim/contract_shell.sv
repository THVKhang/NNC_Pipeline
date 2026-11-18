// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_uart_lite #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_tx_valid,
  output logic                        o_tx_ready,
  input  logic [7:0]                  i_tx_data,
  output logic                        o_rx_valid,
  input  logic                        i_rx_ready,
  output logic [7:0]                  o_rx_data,
  output logic                        o_rx_frame_err,
  output logic                        o_rx_overrun,
  output logic                        o_txd,
  input  logic                        i_rxd
);
  assign o_tx_ready = '0;
  assign o_rx_valid = '0;
  assign o_rx_data = '0;
  assign o_rx_frame_err = '0;
  assign o_rx_overrun = '0;
  assign o_txd = '0;
endmodule
