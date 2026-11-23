module nnc_chk_rx #(
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

  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;

  // CHK-002: rx_overrun_error is a single-cycle pulse (UA-T1.3-07)
  a_CHK_002: assert property (@(posedge clk) disable iff (rst) rx_overrun_error |=> !rx_overrun_error)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge clk) if (!(rst) && (rx_overrun_error)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: rx_frame_error is a single-cycle pulse (UA-T1.3-08)
  a_CHK_003: assert property (@(posedge clk) disable iff (rst) rx_frame_error |=> !rx_frame_error)
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge clk) if (!(rst) && (rx_frame_error)) hits_CHK_003 <= hits_CHK_003 + 1;

  final begin
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
  end
endmodule
