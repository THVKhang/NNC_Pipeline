module nnc_chk_clk #(
  parameter int PARA_SFIFO_DEPTH = 8,
  parameter int PARA_SFIFO_DATA_W = 32,
  parameter int PARA_SFIFO_PTR_RETIME = 0,
  parameter int PARA_SFIFO_MEM_USE_MACRO = 0,
  localparam int LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH),
  localparam int LPARA_PTR_W = $clog2(2 * PARA_SFIFO_DEPTH),
  localparam int LPARA_OCC_W = $clog2(PARA_SFIFO_DEPTH + 1)
) (
  input  logic                        i_clk_wr,
  input  logic                        i_rst_n_wr,
  input  logic                        i_wr_en,
  input  logic [(PARA_SFIFO_DATA_W)-1:0] i_wr_data,
  input  logic [(LPARA_OCC_W)-1:0]    i_full_thr,
  input  logic                        i_rst_n_sw,
  input  logic                        o_sw_rst_busy,
  input  logic                        o_full,
  input  logic                        o_full_thr,
  input  logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_OCC_W)-1:0]    i_empty_thr,
  input  logic [(PARA_SFIFO_DATA_W)-1:0] o_rd_data,
  input  logic                        o_empty,
  input  logic                        o_empty_thr,
  input  logic                        o_underflow
);

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;

  // Helper time stamps of the events that make an output change legal
  longint t_wr_edge = -1;
  longint t_rd_edge = -1;
  longint t_wr_rstf = -1;
  longint t_rd_rstf = -1;
  longint t_sw_chg  = -1;
  logic   busy_prev = 1'b0;

  always @(posedge i_clk_wr) begin
    t_wr_edge = longint'($time);
    busy_prev = o_sw_rst_busy;
  end
  always @(posedge i_clk_rd) t_rd_edge = longint'($time);
  always @(negedge i_rst_n_wr) t_wr_rstf = longint'($time);
  always @(negedge i_rst_n_rd) t_rd_rstf = longint'($time);
  always @(i_rst_n_sw) t_sw_chg = longint'($time);

  // Violation counters (one per output, changed by a single process each)
  int unsigned v_ovf = 0;
  int unsigned v_busy = 0;
  int unsigned v_full = 0;
  int unsigned v_fthr = 0;
  int unsigned v_und = 0;
  int unsigned v_rdd = 0;
  int unsigned v_emp = 0;
  int unsigned v_ethr = 0;

  always @(o_overflow) begin
    if ($time != 0 && !(longint'($time) == t_wr_edge || longint'($time) == t_wr_rstf)) v_ovf++;
  end
  always @(o_sw_rst_busy) begin
    if ($time != 0 && !(longint'($time) == t_wr_edge || longint'($time) == t_wr_rstf)) v_busy++;
  end
  always @(o_full) begin
    if ($time != 0 && !(longint'($time) == t_wr_edge || longint'($time) == t_wr_rstf ||
                        longint'($time) == t_sw_chg)) v_full++;
  end
  always @(o_full_thr) begin
    if ($time != 0 && !(longint'($time) == t_wr_edge || longint'($time) == t_wr_rstf ||
                        longint'($time) == t_sw_chg)) v_fthr++;
  end
  always @(o_underflow) begin
    if ($time != 0 && !(longint'($time) == t_rd_edge || longint'($time) == t_rd_rstf)) v_und++;
  end
  always @(o_rd_data) begin
    if ($time != 0 && !(longint'($time) == t_rd_edge)) v_rdd++;
  end
  always @(o_empty) begin
    if ($time != 0 && !(longint'($time) == t_rd_edge || longint'($time) == t_rd_rstf ||
                        (o_empty === 1'b1 && longint'($time) == t_wr_edge && busy_prev == 1'b0))) v_emp++;
  end
  always @(o_empty_thr) begin
    if ($time != 0 && !(longint'($time) == t_rd_edge || longint'($time) == t_rd_rstf ||
                        (o_empty_thr === 1'b1 && longint'($time) == t_wr_edge && busy_prev == 1'b0))) v_ethr++;
  end

  // CHK-001: Outputs change only at their own clock edge (SF-5.4-05, SF-10.3-05, SF-6.2-02)
  a_CHK_001: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr) 1'b1 |-> $stable({v_ovf, v_busy, v_full, v_fthr}))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-001 (read domain outputs): o_underflow, o_rd_data, o_empty, o_empty_thr (SF-5.4-05, SF-10.3-05)
  a_CHK_001_rd: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd) 1'b1 |-> $stable({v_und, v_rdd, v_emp, v_ethr}))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
  end
endmodule
