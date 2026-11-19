module nnc_chk_gen #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;

  // helper: time of the latest i_clk rising edge or i_rst_n falling edge
  time         edge_t_chk = 0;
  int unsigned bad_cnt_chk = 0;
  int unsigned prev_bad_cnt_chk = 0;

  always @(posedge i_clk or negedge i_rst_n) edge_t_chk = $time;

  always @(o_txd or o_tx_ready or o_rx_valid or o_rx_data or o_rx_frame_err or o_rx_overrun) begin
    if ($time != edge_t_chk) bad_cnt_chk = bad_cnt_chk + 1;
  end

  always_ff @(posedge i_clk) prev_bad_cnt_chk <= bad_cnt_chk;

  // CHK-001: Outputs change only at i_clk rising edges or reset assertion (UL-7.1-04)
  a_CHK_001: assert property (@(posedge i_clk) disable iff (!i_rst_n) 1'b1 |-> (bad_cnt_chk == prev_bad_cnt_chk))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
  end
endmodule
