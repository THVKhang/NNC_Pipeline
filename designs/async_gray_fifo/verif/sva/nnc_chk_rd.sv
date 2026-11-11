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

  // helper registers (read domain)
  logic rd_rst_q = 1'b1;
  always_ff @(posedge i_clk_rd) rd_rst_q <= i_rst_n_rd;

  logic       cap_v = 1'b0;
  logic       cap_empty = 1'b0;
  logic       cap_empty_thr = 1'b0;
  logic       cap_underflow = 1'b0;
  logic [(PARA_AFIFO_DATA_W)-1:0] cap_rd_data = '0;
  always_ff @(negedge i_clk_rd) begin
    cap_v         <= 1'b1;
    cap_empty     <= o_empty;
    cap_empty_thr <= o_empty_thr;
    cap_underflow <= o_underflow;
    cap_rd_data   <= o_rd_data;
  end

  // CHK-001: Read-domain hardware reset values (AF-7.3-02, AF-3-35, AF-3-36, AF-12-06)
  a_CHK_001: assert property (@(posedge i_clk_rd) (!i_rst_n_rd) || (i_rst_n_rd && !rd_rst_q) |->
      (o_empty && !o_underflow && (i_rst_n_rd || o_empty_thr)))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if ((!i_rst_n_rd) || (i_rst_n_rd && !rd_rst_q)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_underflow is the registered one-cycle pulse of a non-blocked read while empty (AF-3-41, AF-6.2-08, AF-10.1-01, AF-10.2-04, AF-10.6.2-11, AF-11-02, AF-12-04, AF-12-06, AF-20.2-08, AF-6.3-04)
  a_CHK_002: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
      (i_rd_en && o_empty && i_rst_n_wr && i_rst_n_sw && !o_sw_rst_busy) |=> o_underflow)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty && i_rst_n_wr && i_rst_n_sw && !o_sw_rst_busy)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-002: no spurious or sticky underflow pulses (AF-6.2-08, AF-11-02, AF-12-06)
  a_CHK_002_a: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
      (o_underflow && $past(i_rst_n_rd)) |-> ($past(i_rd_en) && $past(o_empty)))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end

  // CHK-003: o_empty_thr consistency for every 4-bit i_empty_thr (AF-3-15, AF-6.2-21, AF-20.2-06, AF-3-62, AF-10.7.2-04, AF-10.7.6-05, AF-10.7.5-11, AF-20.2-25)
  a_CHK_003: assert property (@(posedge i_clk_rd)
      1'b1 |-> ((!o_empty || o_empty_thr) &&
                (i_empty_thr < PARA_AFIFO_DEPTH || o_empty_thr) &&
                (i_empty_thr != 0 || (o_empty_thr == o_empty))))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (1'b1) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Read-domain outputs change only at i_clk_rd edges (AF-6.2-06, AF-7.2-10, AF-6.2-19)
  a_CHK_004: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
      cap_v |-> (o_empty == cap_empty && o_empty_thr == cap_empty_thr &&
                 o_underflow == cap_underflow && o_rd_data == cap_rd_data))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (cap_v)) hits_CHK_004 <= hits_CHK_004 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
  end
endmodule
