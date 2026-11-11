// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_vlsit_afifo_top #(
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
  output logic                        o_sw_rst_busy,
  output logic                        o_full,
  output logic                        o_full_thr,
  output logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_PTR_W)-1:0]    i_empty_thr,
  output logic [(PARA_AFIFO_DATA_W)-1:0] o_rd_data,
  output logic                        o_empty,
  output logic                        o_empty_thr,
  output logic                        o_underflow
);
  assign o_sw_rst_busy = '0;
  assign o_full = '0;
  assign o_full_thr = '0;
  assign o_overflow = '0;
  assign o_rd_data = '0;
  assign o_empty = '0;
  assign o_empty_thr = '0;
  assign o_underflow = '0;
endmodule
