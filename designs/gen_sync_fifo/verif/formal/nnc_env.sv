// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

// ---------------------------------------------------------------------------
// Helper state: the value of each hardware reset sampled at the last edge of
// its own clock. "Up" means that domain has seen its reset released at an edge.
// It is cleared at the first edge of the domain clock that samples the reset low.
// ---------------------------------------------------------------------------
reg r_env_wr_up = 1'b0;
reg r_env_rd_up = 1'b0;

always @(posedge i_clk_wr) r_env_wr_up <= i_rst_n_wr;
always @(posedge i_clk_rd) r_env_rd_up <= i_rst_n_rd;

// ENV-01: The two hardware resets are asserted together. Once both domains are up,
// neither reset may be asserted without the other. Each reset may still be released
// at its own clock edge, because each domain's flag clears when its reset is sampled
// low. (SF-3-32, SF-7.3-04)
always @(*)
  if (r_env_wr_up && r_env_rd_up)
    assume (i_rst_n_wr == i_rst_n_rd);

// ENV-02: No write request until both hardware resets are released. The write domain
// may leave reset before the read domain does. (SF-3-32, SF-7.3-04)
always @(posedge i_clk_wr)
  if (!i_rst_n_rd)
    assume (!i_wr_en);

// ENV-03: No read request until both hardware resets are released. The read domain
// may leave reset before the write domain does. (SF-3-32, SF-7.3-04)
always @(posedge i_clk_rd)
  if (!i_rst_n_wr)
    assume (!i_rd_en);

// ENV-04: The static thresholds i_full_thr and i_empty_thr do not change while the
// FIFO is in use, meaning both resets are released. These inputs have no clock domain,
// so they are checked at the edges of both clocks. Any value is allowed, including a
// value above DEPTH (SF-9-05), and the values may change during reset.
// (SF-3-16, SF-6.2-08, SF-1.3-03)
always @(posedge i_clk_wr)
  if (i_rst_n_wr && i_rst_n_rd && $past(i_rst_n_wr) && $past(i_rst_n_rd))
    assume ($stable(i_full_thr) && $stable(i_empty_thr));

always @(posedge i_clk_rd)
  if (i_rst_n_wr && i_rst_n_rd && $past(i_rst_n_wr) && $past(i_rst_n_rd))
    assume ($stable(i_full_thr) && $stable(i_empty_thr));
endmodule
