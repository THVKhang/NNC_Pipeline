module nnc_chk_wr #(
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

  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;

  // helper signals
  wire block_w = (!i_rst_n_sw) || o_sw_rst_busy;

  // read-domain accepted-read counter (cleared by read reset)
  int unsigned ra_cnt;
  always_ff @(posedge i_clk_rd or negedge i_rst_n_rd) begin
    if (!i_rst_n_rd) ra_cnt <= 0;
    else if (i_rd_en && !o_empty) ra_cnt <= ra_cnt + 1;
  end

  // write-domain reference model
  int unsigned wa_cnt = 0;
  int unsigned rbase = 0;
  int unsigned occ_q = 0;
  logic r1 = 1'b0;
  wire acc_w = i_wr_en && !o_full;

  always_ff @(posedge i_clk_wr) begin
    if (!i_rst_n_wr || !i_rst_n_rd) begin
      wa_cnt <= 0;
      rbase  <= ra_cnt;
      occ_q  <= 0;
      r1     <= 1'b0;
    end else if (block_w) begin
      wa_cnt <= 0;
      rbase  <= ra_cnt;
      occ_q  <= 0;
      r1     <= 1'b1;
    end else begin
      wa_cnt <= wa_cnt + (acc_w ? 1 : 0);
      occ_q  <= wa_cnt + (acc_w ? 1 : 0) - (ra_cnt - rbase);
      r1     <= 1'b1;
    end
  end

  // CHK-009: Write block term forces o_full and o_full_thr (SF-3-35, SF-3-36, SF-10.6-03, SF-10.7-01, SF-10.1-02, SF-15.3-13)
  a_CHK_009: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    (((!i_rst_n_sw) || o_sw_rst_busy) && i_rst_n_rd) |-> (o_full && (o_full_thr == (i_full_thr == 0))))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((((!i_rst_n_sw) || o_sw_rst_busy) && i_rst_n_rd))) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: Write-view occupancy model for o_full and o_full_thr (SF-1.3-02, SF-1.3-03, SF-3-05, SF-3-14, SF-3-45, SF-3-53, SF-3-54, SF-5.1-01, SF-5.3-05, SF-5.4-03, SF-9-03, SF-9-05, SF-9-06, SF-10.2-01, SF-10.2-04, SF-10.2-07, SF-10.4-07, SF-10.6-02, SF-10.6-03, SF-10.7-07, SF-13-04)
  a_CHK_010: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    ((i_rst_n_sw && !o_sw_rst_busy && i_rst_n_rd) |->
      ((o_full == (occ_q == unsigned'(PARA_SFIFO_DEPTH))) &&
       (!r1 || (o_full_thr == (occ_q >= unsigned'(i_full_thr)))))))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((i_rst_n_sw && !o_sw_rst_busy && i_rst_n_rd))) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: o_overflow exact one-cycle pulse (SF-1.3-04, SF-3-17, SF-3-37, SF-6.2-06, SF-6.3-06, SF-6.3-08, SF-6.3-11, SF-10.2-05, SF-10.6-04, SF-12-01, SF-12-07, SF-12-10, SF-12-11, SF-15.3-10, SF-15.3-13)
  a_CHK_011: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    1'b1 |=> (o_overflow == ($past(i_wr_en) && $past(o_full) && $past(i_rst_n_sw) && !$past(o_sw_rst_busy))))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (1'b1)) hits_CHK_011 <= hits_CHK_011 + 1;

  final begin
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
  end
endmodule
