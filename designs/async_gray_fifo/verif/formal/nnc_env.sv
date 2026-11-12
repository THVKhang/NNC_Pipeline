// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Environment obligations taken from the specification only.
  // Everything else is left free, because the specification calls it legal:
  // writes while full (overflow), reads while empty (underflow), accesses
  // during a software reset (blocked, no error pulse), i_rst_n_sw low for one
  // or more cycles at any time (also while busy), any i_wr_data, any threshold
  // value (written once), hardware resets asserted at different times and
  // asynchronously at any moment (also during a software-reset sequence).
  // ---------------------------------------------------------------------------

  // Helper: r_inuse is set once both hardware resets have been released for
  // the first time. From then on the FIFO is in use and the static thresholds
  // have already been written ("written once before use").
  reg  r_inuse = 1'b0;
  wire w_inuse = r_inuse | (i_rst_n_wr & i_rst_n_rd);

  always @($global_clock)
    r_inuse <= w_inuse;

  // ENV-01: i_full_thr is a static configuration input with a false path and no synchronizer. It is written once before use and does not change after the FIFO has first entered use (both resets released), whatever reset activity follows. (AF-3-17, AF-6.2-10, AF-7.2-04, AF-17.1.3-04, AF-20.2-07)
  always @($global_clock)
    if (w_inuse)
      assume ($stable(i_full_thr));

  // ENV-02: i_empty_thr is a static configuration input with a false path and no synchronizer. It is written once before use and does not change after the FIFO has first entered use (both resets released), whatever reset activity follows. (AF-3-17, AF-6.2-10, AF-7.2-04, AF-17.1.3-04, AF-20.2-07)
  always @($global_clock)
    if (w_inuse)
      assume ($stable(i_empty_thr));

  // ENV-03: No write starts until both domains are out of hardware reset. The producer keeps the write interface idle while either reset is asserted. (AF-20.1-05, AF-10.7.4-23, AF-12-07)
  always @(posedge i_clk_wr)
    if (!i_rst_n_wr || !i_rst_n_rd)
      assume (!i_wr_en);

  // ENV-04: No read starts until both domains are out of hardware reset. The consumer keeps the read interface idle while either reset is asserted. (AF-20.1-05, AF-10.7.4-23, AF-12-07)
  always @(posedge i_clk_rd)
    if (!i_rst_n_rd || !i_rst_n_wr)
      assume (!i_rd_en);

  // ENV-05: i_rst_n_wr is already synchronized to i_clk_wr. It is released (0->1) only at a rising edge of i_clk_wr, so the releasing edge still samples it low: low for at least one write-clock edge. Assertion stays asynchronous and unconstrained. (AF-6.2-03, AF-3-34, AF-7.3-01, AF-20.1-01)
  always @($global_clock)
    if ($rose(i_rst_n_wr))
      assume ($rose(i_clk_wr));

  // ENV-06: i_rst_n_rd is already synchronized to i_clk_rd. It is released (0->1) only at a rising edge of i_clk_rd, so the releasing edge still samples it low: low for at least one read-clock edge. Assertion stays asynchronous and unconstrained. (AF-6.2-03, AF-3-34, AF-7.3-02, AF-20.1-01)
  always @($global_clock)
    if ($rose(i_rst_n_rd))
      assume ($rose(i_clk_rd));

  // Helper: reset pairing.
  // r_dirty : a hardware reset was asserted in the current reset window.
  // r_ovl   : in this window the two resets were low at the same time
  //           (overlapping windows). The two resets can still be asserted
  //           and released at different times.
  // The window closes only when the two resets overlapped and both are now
  // released. A reset of one domain that ends while the other domain is
  // running is a "reset of one domain only" (inconsistent state, not repaired
  // by the IP). The window then stays pending until the whole FIFO gets a real
  // reset (overlapping resets of both domains).
  reg  r_dirty = 1'b0;
  reg  r_ovl   = 1'b0;
  wire w_dirty    = r_dirty | !i_rst_n_wr | !i_rst_n_rd;
  wire w_ovl      = r_ovl   | (!i_rst_n_wr & !i_rst_n_rd);
  wire w_rst_pend = w_dirty & !w_ovl;  // one domain reset alone, no overlap yet

  always @($global_clock) begin
    if (w_dirty && w_ovl && i_rst_n_wr && i_rst_n_rd) begin
      r_dirty <= 1'b0;
      r_ovl   <= 1'b0;
    end else begin
      r_dirty <= w_dirty;
      r_ovl   <= w_ovl;
    end
  end

  // ENV-07: The integrator resets both domains (the whole FIFO, with the two reset windows overlapping). After a hardware reset of only one domain, the producer issues no write until both domains have been reset together and both are out of reset. The assertion and release times of the resets can differ. (AF-12-07, AF-7.2-12, AF-10.7.4-24, AF-20.1-05, AF-20.2-27, AF-3-36, AF-7.2-11)
  always @(posedge i_clk_wr)
    if (w_rst_pend)
      assume (!i_wr_en);

  // ENV-08: The integrator resets both domains (the whole FIFO, with the two reset windows overlapping). After a hardware reset of only one domain, the consumer issues no read until both domains have been reset together and both are out of reset. The assertion and release times of the resets can differ. (AF-12-07, AF-7.2-12, AF-10.7.4-24, AF-20.1-05, AF-20.2-27, AF-3-36, AF-7.2-11)
  always @(posedge i_clk_rd)
    if (w_rst_pend)
      assume (!i_rd_en);
endmodule
