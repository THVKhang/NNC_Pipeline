module nnc_chk_tx #(
  parameter int DATA_WIDTH = 8
) (
  input  logic                        clk,
  input  logic                        rst,
  input  logic [7:0]                  s_axis_tdata,
  input  logic                        s_axis_tvalid,
  input  logic                        s_axis_tready,
  input  logic [7:0]                  m_axis_tdata,
  input  logic                        m_axis_tvalid,
  input  logic                        m_axis_tready,
  input  logic                        rxd,
  input  logic                        txd,
  input  logic                        tx_busy,
  input  logic                        rx_busy,
  input  logic                        rx_overrun_error,
  input  logic                        rx_frame_error,
  input  logic [15:0]                 prescale
);

  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;

  // CHK-004: tx_busy is high whenever txd is driving a low (frame) level (UA-T1.3-06)
  a_CHK_004: assert property (@(posedge clk) disable iff (rst) (txd == 1'b0) |-> (tx_busy == 1'b1))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge clk) if (!(rst) && (txd == 1'b0)) hits_CHK_004 <= hits_CHK_004 + 1;

  final begin
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
  end
endmodule
