module nnc_chk_reset #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_tx_valid,
  input  logic                        o_tx_ready,
  input  logic [7:0]                  i_tx_data,
  input  logic                        o_rx_valid,
  input  logic                        i_rx_ready,
  input  logic [7:0]                  o_rx_data,
  input  logic                        o_rx_frame_err,
  input  logic                        o_rx_overrun,
  input  logic                        o_txd,
  input  logic                        i_rxd
);

  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;

  // CHK-002: Output values while reset is asserted (UL-6.2-02, UL-6.2-01, UL-5-03, UL-5-05, UL-5-08, UL-5-10, UL-5-12, UL-5-14, UL-14-01)
  a_CHK_002: assert property (@(posedge i_clk) (!i_rst_n) |->
      (o_txd === 1'b1 && o_tx_ready === 1'b1 && o_rx_valid === 1'b0 &&
       o_rx_data === 8'h00 && o_rx_frame_err === 1'b0 && o_rx_overrun === 1'b0))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end

  always_ff @(posedge i_clk) if (!i_rst_n) hits_CHK_002 <= hits_CHK_002 + 1;

  final begin
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
  end
endmodule
