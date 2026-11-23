module nnc_chk_axis #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;

  // CHK-001: m_axis output stalls (holds valid and data) while m_axis_tready is low (UA-T1.3-05, UA-T1.3-07)
  a_CHK_001: assert property (@(posedge clk) disable iff (rst)
    (m_axis_tvalid && !m_axis_tready) |=> (m_axis_tvalid && $stable(m_axis_tdata)))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && !m_axis_tready)) hits_CHK_001 <= hits_CHK_001 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
  end
endmodule
