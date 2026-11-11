module nnc_chk_wr #(
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

  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;
  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  // helper registers
  logic rst_q = 1'b0;
  always_ff @(posedge i_clk_wr) rst_q <= i_rst_n_wr;

  logic       cap_ov, cap_busy, cap_full, cap_thr, cap_sw;
  logic [(LPARA_PTR_W)-1:0] cap_fthr;
  always_ff @(negedge i_clk_wr) begin
    cap_ov   <= o_overflow;
    cap_busy <= o_sw_rst_busy;
    cap_full <= o_full;
    cap_thr  <= o_full_thr;
    cap_sw   <= i_rst_n_sw;     // o_full / o_full_thr may follow a change of i_rst_n_sw (CHK-012)
    cap_fthr <= i_full_thr;     // or of the static threshold (AF-6.2-06)
  end

  logic       rel_flag;
  logic [2:0] rel_age;
  always_ff @(posedge i_clk_wr) begin
    if (!i_rst_n_wr) begin
      rel_flag <= 1'b0;
      rel_age  <= 3'd0;
    end else if (!o_sw_rst_busy) begin
      rel_flag <= 1'b0;
      rel_age  <= 3'd0;
    end else if (!rel_flag) begin
      if (i_rst_n_sw) begin
        rel_flag <= 1'b1;
        rel_age  <= 3'd0;
      end
    end else if (rel_age != 3'd7) begin
      rel_age <= rel_age + 3'd1;
    end
  end
  wire hist_ok = rel_flag && (rel_age >= 3'd2);

  // CHK-007: Write-domain hardware reset values (AF-7.3-01, AF-3-35, AF-3-36, AF-12-03, AF-10.7.7-09, AF-3-64, AF-15.3-16)
  a_CHK_007: assert property (@(posedge i_clk_wr)
    (!i_rst_n_wr || !rst_q) |->
      ((o_overflow == 1'b0) && (o_sw_rst_busy == 1'b0) &&
       (!i_rst_n_sw || (o_full == 1'b0)) &&
       (i_rst_n_wr || !i_rst_n_sw || (o_full_thr == (i_full_thr == '0)))))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!i_rst_n_wr || !rst_q) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: o_overflow is the registered one-cycle pulse of a non-blocked write while full (AF-3-40, AF-6.2-08, AF-10.1-03, AF-10.2-03, AF-10.6.2-11, AF-11-02, AF-12-01, AF-12-03, AF-20.2-08, AF-3-61, AF-10.7.2-05, AF-20.2-24, AF-10.7.4-16, AF-10.7.4-18, AF-6.3-02, AF-6.3-07, AF-12-09)
  a_CHK_008: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    1'b1 |=> (o_overflow == $past(i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy)))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (1'b1)) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: Write block forces o_full=1 and the empty-FIFO o_full_thr with zero latency (AF-3-49, AF-3-60, AF-3-62, AF-10.7.1-01, AF-10.7.2-03, AF-10.7.2-04, AF-10.7.7-08, AF-15.3-17, AF-20.2-23, AF-20.2-25, AF-20.2-26)
  a_CHK_009: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    (!i_rst_n_sw || o_sw_rst_busy) |-> (o_full && (o_full_thr == (i_full_thr == '0))))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!i_rst_n_sw || o_sw_rst_busy)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: o_sw_rst_busy rises exactly at the first edge sampling i_rst_n_sw=0 (AF-3-42, AF-3-63, AF-3-64, AF-6.2-16, AF-10.7.1-02, AF-10.7.2-06, AF-10.7.6-01, AF-10.7.7-02, AF-10.7.7-03, AF-10.7.7-10, AF-15.3-16, AF-15.3-17, AF-20.2-20)
  a_CHK_010: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    (!o_sw_rst_busy) |=> (o_sw_rst_busy == !$past(i_rst_n_sw)))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_sw_rst_busy)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: o_sw_rst_busy falls only after i_rst_n_sw=1 plus a crossing round trip (AF-3-51, AF-3-53, AF-3-55, AF-3-63, AF-6.2-16, AF-7.2-06, AF-10.7.2-06, AF-10.7.4-14, AF-10.7.7-05, AF-10.7.7-07, AF-15.3-12, AF-15.3-17, AF-20.2-23)
  a_CHK_011: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    o_sw_rst_busy |=> (o_sw_rst_busy ||
      ($past(hist_ok) && (o_full_thr == (i_full_thr == '0)) &&
       (i_rst_n_sw ? !o_full : o_full))))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_sw_rst_busy)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: Write-domain outputs change only at i_clk_wr edges (AF-6.2-06, AF-6.2-07, AF-10.7.7-01, AF-3-63, AF-3-28, AF-7.2-10)
  a_CHK_012: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    rst_q |-> ((o_overflow == cap_ov) && (o_sw_rst_busy == cap_busy) &&
               ((i_rst_n_sw != cap_sw) || (i_full_thr != cap_fthr) ||
                ((o_full == cap_full) && (o_full_thr == cap_thr)))))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (rst_q)) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: o_full_thr consistency for every 4-bit i_full_thr (AF-3-14, AF-6.2-18, AF-20.2-05, AF-3-28)
  a_CHK_013: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
    1'b1 |-> (((int'(i_full_thr) != 0) || o_full_thr) &&
              ((int'(i_full_thr) <= PARA_AFIFO_DEPTH) || !o_full_thr) &&
              ((int'(i_full_thr) != PARA_AFIFO_DEPTH) ||
                 (o_full_thr == (o_full && i_rst_n_sw && !o_sw_rst_busy))) &&
              (!(o_full && i_rst_n_sw && !o_sw_rst_busy) ||
                 (o_full_thr == (int'(i_full_thr) <= PARA_AFIFO_DEPTH)))))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (1'b1)) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
