module nnc_chk_rd #(
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

  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;

  // helper counters (write domain)
  int unsigned wa_cnt = 0;
  always_ff @(posedge i_clk_wr) begin
    if (!i_rst_n_wr) wa_cnt <= 0;
    else if (o_sw_rst_busy) wa_cnt <= 0;
    else if (i_wr_en && !o_full) wa_cnt <= wa_cnt + 1;
  end

  // helper registers (read domain)
  int unsigned ra_cnt = 0;
  int unsigned occ_q = 0;
  logic busy_q4 = 1'b1;
  logic uf_exp_q = 1'b0;
  logic busy_q5 = 1'b0;
  logic rd_acc;
  int unsigned ra_next;
  assign rd_acc = i_rd_en && !o_empty;
  assign ra_next = ra_cnt + (rd_acc ? 1 : 0);

  always_ff @(posedge i_clk_rd) begin
    if (!i_rst_n_rd) begin
      ra_cnt   <= 0;
      occ_q    <= 0;
      busy_q4  <= 1'b1;
      uf_exp_q <= 1'b0;
      busy_q5  <= 1'b0;
    end else begin
      busy_q4  <= o_sw_rst_busy;
      busy_q5  <= o_sw_rst_busy;
      uf_exp_q <= i_rd_en && o_empty;
      if (o_sw_rst_busy) begin
        ra_cnt <= 0;
        occ_q  <= 0;
      end else begin
        ra_cnt <= ra_next;
        occ_q  <= wa_cnt - ra_next;
      end
    end
  end

  // CHK-003: Reads blocked while software reset busy (SF-3-38, SF-10.6-06, SF-10.7-03, SF-15.3-13)
  a_CHK_003: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
    (i_rst_n_wr && o_sw_rst_busy) |-> (o_empty && o_empty_thr))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rst_n_wr && o_sw_rst_busy)) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Read-view occupancy model for o_empty and o_empty_thr (SF-1.3-02, SF-1.3-03, SF-3-08, SF-3-15, SF-3-52, SF-3-54, SF-5.1-01, SF-5.3-02, SF-5.4-03, SF-9-03, SF-9-05, SF-9-06, SF-10.2-02, SF-10.2-03, SF-10.2-07, SF-10.3-13, SF-10.4-06, SF-10.6-05, SF-10.6-06, SF-13-03)
  a_CHK_004: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
    (!o_sw_rst_busy && !busy_q4) |->
      ((o_empty == (occ_q == 0)) && (o_empty_thr == (occ_q <= i_empty_thr))))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (!o_sw_rst_busy && !busy_q4)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: o_underflow one-cycle pulse (SF-1.3-04, SF-3-18, SF-3-39, SF-6.2-06, SF-6.3-06, SF-6.3-10, SF-10.2-06, SF-10.3-08, SF-10.6-07, SF-12-04, SF-12-07, SF-12-10, SF-12-11, SF-15.3-11)
  a_CHK_005: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
    (uf_exp_q || o_underflow) |->
      ((!o_underflow || uf_exp_q) && (busy_q5 || (o_underflow == uf_exp_q))))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (uf_exp_q || o_underflow)) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
