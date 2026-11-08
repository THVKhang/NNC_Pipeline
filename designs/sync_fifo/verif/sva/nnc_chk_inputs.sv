module nnc_chk_inputs #(
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

  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;

  // CHK-002: No unknown input when a request is sampled (SF-15.3-04)
  a_CHK_002: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr) 1'b1 |->
    (!$isunknown(i_wr_en) && !$isunknown(i_rst_n_sw) && !$isunknown(i_full_thr) &&
     (!(i_wr_en === 1'b1) || !$isunknown(i_wr_data))))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (1'b1)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-002: No unknown input when a request is sampled (SF-15.3-04), read domain
  a_CHK_002_rd: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd) 1'b1 |->
    (!$isunknown(i_rd_en) && !$isunknown(i_empty_thr)))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (1'b1)) hits_CHK_002 <= hits_CHK_002 + 1;

  final begin
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
  end
endmodule
