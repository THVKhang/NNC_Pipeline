module nnc_chk_rd #(
  parameter int PARA_AFIFO_DEPTH = 8,
  parameter int PARA_AFIFO_DATA_W = 32,
  parameter int PARA_AFIFO_CELL_TYPE = 2,
  parameter int PARA_AFIFO_MEM_USE_MACRO = 0,
  localparam int LPARA_ADDR_W = $clog2(PARA_AFIFO_DEPTH),
  localparam int LPARA_PTR_W = LPARA_ADDR_W + 1
) (
  input  logic                        i_clk_wr,
  input  logic                        i_rst_n_wr,
  input  logic                        i_wr_en,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] i_wr_data,
  input  logic [(LPARA_PTR_W)-1:0]    i_full_thr,
  input  logic                        i_rst_n_sw,
  input  logic                        o_sw_rst_busy,
  input  logic                        o_full,
  input  logic                        o_full_thr,
  input  logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_PTR_W)-1:0]    i_empty_thr,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] o_rd_data,
  input  logic                        o_empty,
  input  logic                        o_empty_thr,
  input  logic                        o_underflow
);

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;

  // helper: previous-edge reset level (read domain), used for the "first edge after release" window
  logic rst_rd_q = 1'b0;
  always_ff @(posedge i_clk_rd) rst_rd_q <= i_rst_n_rd;

  // CHK-001: Read-domain hardware reset values (AF-7.3-02, AF-3-35, AF-3-36, AF-12-06)
  a_CHK_001: assert property (@(posedge i_clk_rd)
    (!i_rst_n_rd || (i_rst_n_rd && !rst_rd_q)) |->
    (o_empty === 1'b1 && !o_underflow && (i_rst_n_rd || o_empty_thr === 1'b1)))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!i_rst_n_rd || (i_rst_n_rd && !rst_rd_q)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_underflow is the registered one-cycle pulse of a non-blocked read while empty (AF-3-41, AF-6.2-08, AF-10.1-01, AF-10.2-04, AF-10.6.2-11, AF-11-02, AF-12-04, AF-12-06, AF-20.2-08, AF-6.3-04)
  a_CHK_002: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
    ($past(i_rst_n_rd) && (o_underflow || ($past(i_rd_en) && $past(o_empty) && $past(i_rst_n_wr) && $past(i_rst_n_sw) && !$past(o_sw_rst_busy)))) |->
    ((!o_underflow || ($past(i_rd_en) && $past(o_empty))) &&
     (o_underflow || !($past(i_rd_en) && $past(o_empty) && $past(i_rst_n_wr) && $past(i_rst_n_sw) && !$past(o_sw_rst_busy)))))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && ($past(i_rst_n_rd) && (o_underflow || ($past(i_rd_en) && $past(o_empty) && $past(i_rst_n_wr) && $past(i_rst_n_sw) && !$past(o_sw_rst_busy))))) hits_CHK_002 <= hits_CHK_002 + 1;

  // NNC hand fix (G3, formal triage B): after a hardware reset of one domain only, the pointer state of the two
  // domains is inconsistent (ASM-005, ERR-003) and the occupancy-dependent flag relations are not checked until a
  // reset of both domains with overlapping windows (contract CHK-023). Async-reset form (as rd_only_rst in nnc_chk_wr.sv).
  logic wr_only_rst = 1'b0;
  always @(negedge i_rst_n_wr or negedge i_rst_n_rd)
    if (!i_rst_n_rd) wr_only_rst <= 1'b0;
    else             wr_only_rst <= 1'b1;
  logic rd_only_rst = 1'b0;
  always @(negedge i_rst_n_rd or negedge i_rst_n_wr)
    if (!i_rst_n_wr) rd_only_rst <= 1'b0;
    else             rd_only_rst <= 1'b1;
  wire one_dom = rd_only_rst || wr_only_rst;

  // CHK-003: o_empty_thr consistency for every i_empty_thr (AF-3-15, AF-6.2-21, AF-20.2-06, AF-3-62, AF-10.7.2-04, AF-10.7.6-05, AF-10.7.5-11, AF-20.2-25)
  a_CHK_003: assert property (@(posedge i_clk_rd)
    1'b1 |->
    ((!o_empty || o_empty_thr) &&
     (one_dom || !(int'(unsigned'(i_empty_thr)) >= PARA_AFIFO_DEPTH) || o_empty_thr) &&  // NNC hand fix (G3, formal triage B), see one_dom
     ((i_empty_thr != '0) || (o_empty_thr == o_empty))))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (1'b1) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Read-domain outputs change only at i_clk_rd edges (AF-6.2-06, AF-7.2-10, AF-6.2-19)
  time t_clk_rd_edge = 0;
  time t_rst_rd_chg = 0;
  time t_thr_chg = 0;
  int unsigned chg_cnt = 0;
  int unsigned chg_prev = 0;
  always @(posedge i_clk_rd) t_clk_rd_edge = $time;
  always @(i_rst_n_rd) t_rst_rd_chg = $time;
  always @(i_empty_thr) t_thr_chg = $time;
  always @(o_empty or o_empty_thr or o_underflow or o_rd_data) begin
    if ($time != 0 && $time != t_clk_rd_edge && $time != t_rst_rd_chg && $time != t_thr_chg)
      chg_cnt = chg_cnt + 1;
  end
  always_ff @(posedge i_clk_rd) chg_prev <= chg_cnt;
  a_CHK_004: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
    1'b1 |-> (chg_cnt == chg_prev))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (1'b1)) hits_CHK_004 <= hits_CHK_004 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
  end
endmodule
