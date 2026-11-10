module nnc_chk_sb #(
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

  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;

  // Reference queue modelled as absolute counters (no cross-domain multi-driven state):
  //  wr domain owns wcnt, wbase, mem; rd domain owns rcnt.
  int unsigned wcnt  = 0;
  int unsigned wbase = 0;
  int unsigned rcnt  = 0;
  logic [(PARA_SFIFO_DATA_W)-1:0] sb_mem [PARA_SFIFO_DEPTH];
  logic sb_busy_q = 1'b0;

  // Q is cleared at the i_clk_wr edge after which o_sw_rst_busy goes from 1 to 0 (CHK-006, CHK-010).
  // That fall is seen only after the edge, so until the next i_clk_wr edge (sb_busy_q=1, o_sw_rst_busy=0)
  // the clear is applied combinationally; the next edge registers it in wbase.
  logic        sb_clr;
  int unsigned sb_base;
  int unsigned sb_head;
  int unsigned sb_size;
  always_comb begin
    sb_clr  = sb_busy_q && !o_sw_rst_busy;
    sb_base = sb_clr ? wcnt : wbase;
    sb_head = (rcnt < sb_base) ? sb_base : rcnt;
    sb_size = wcnt - sb_head;
  end

  always_ff @(posedge i_clk_wr) begin
    sb_busy_q <= o_sw_rst_busy;
    if (!i_rst_n_wr || !i_rst_n_rd) begin
      wbase <= wcnt;
    end else begin
      if (sb_busy_q && !o_sw_rst_busy) wbase <= wcnt;
      if (i_wr_en && !o_full) begin
        sb_mem[wcnt % PARA_SFIFO_DEPTH] <= i_wr_data;
        wcnt <= wcnt + 1;
      end
    end
  end

  always_ff @(posedge i_clk_rd) begin
    if (!i_rst_n_rd || !i_rst_n_wr) rcnt <= sb_head;
    else if (!o_empty && i_rd_en && (sb_size > 0)) rcnt <= sb_head + 1;
    else rcnt <= sb_head;
  end

  // CHK-006: Scoreboard: order, no loss, no duplication, show-ahead data (SF-1.1-01, SF-1.1-02, SF-3-02, SF-3-03, SF-6.3-03, SF-10.5-03, SF-15.3-12)
  a_CHK_006: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd || !i_rst_n_wr)
    (!o_empty) |-> ((sb_size > 0) && (o_rd_data == sb_mem[sb_head % PARA_SFIFO_DEPTH])))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd || !i_rst_n_wr) && (!o_empty)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: Occupancy bounds and safe-direction flag lag, write side (SF-3-05, SF-5.4-01, SF-15.3-09, SF-15.3-15)
  a_CHK_007: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr || !i_rst_n_rd)
    1'b1 |-> ((sb_size <= PARA_SFIFO_DEPTH) && ((sb_size != PARA_SFIFO_DEPTH) || o_full)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr || !i_rst_n_rd) && (1'b1)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-007: Occupancy bounds and safe-direction flag lag, read side (SF-5.4-01, SF-5.4-04, SF-15.3-08, SF-15.3-15)
  a_CHK_007_rd: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd || !i_rst_n_wr)
    1'b1 |-> ((sb_size <= PARA_SFIFO_DEPTH) && ((sb_size != 0) || o_empty)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
  end
endmodule
