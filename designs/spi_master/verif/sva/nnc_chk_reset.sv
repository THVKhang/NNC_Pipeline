module nnc_chk_reset #(
  parameter int PARA_SPI_CLK_DIV = 4
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_cmd_valid,
  input  logic                        o_cmd_ready,
  input  logic [7:0]                  i_cmd_data,
  input  logic                        i_cmd_last,
  input  logic                        o_rsp_valid,
  input  logic                        i_rsp_ready,
  input  logic [7:0]                  o_rsp_data,
  input  logic                        o_sclk,
  input  logic                        o_mosi,
  input  logic                        i_miso,
  input  logic                        o_cs_n,
  input  logic                        i_cpol,
  input  logic                        i_cpha
);

  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;
  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;
  int unsigned fails_CHK_018 = 0;
  int unsigned hits_CHK_018 = 0;

  // helper state
  logic rst_q       = 1'b0;
  logic wait_hs     = 1'b0;

  always_ff @(posedge i_clk) begin
    rst_q <= !i_rst_n;
    if (!i_rst_n) wait_hs <= 1'b1;
    else if (i_cmd_valid && o_cmd_ready) wait_hs <= 1'b0;
  end

  // ---------------- CHK-015 helper: settled snapshot of the 1->0 time step of i_rst_n ----------------
  // NNC verification fix (fix-verif, triage B): the previous 'assert final' had no effect in this simulator
  // (the fail count stayed exactly the same, 287), so it was evaluated like a plain immediate assertion on the
  // first, unsettled evaluation of the time step. The contract (CHK-015) checks the outputs "in the same time
  // step (after combinational settling) and before any further rising edge of i_clk". This no longer depends
  // on the simulator's deferred-assertion support: on a 1->0 transition of i_rst_n a snapshot of all
  // outputs (and i_cpol) is taken and re-taken on every further change inside that same time step, so it holds
  // the settled values of that step. The snapshot is judged at the first event of any later time step
  // (at the latest at the next i_clk edge, so before any further rising edge, whose own updates are not in
  // the snapshot). Same output list, same exact values, every 1->0 transition is checked.
  logic       rst15_prev = 1'b0;
  logic       chk15_pend = 1'b0;
  realtime    chk15_t    = -1.0;
  logic       s15_cs   = 1'b0;
  logic       s15_mosi = 1'b0;
  logic       s15_rv   = 1'b0;
  logic [7:0] s15_rd   = 8'h00;
  logic       s15_rdy  = 1'b0;
  logic       s15_sclk = 1'b0;
  logic       s15_cpol = 1'b0;

  // CHK-015: Outputs take reset values at once on i_rst_n assertion (SPI-6.2-01, SPI-10-09, SPI-10-11)
  always @(posedge i_clk or negedge i_clk or i_rst_n or o_cs_n or o_mosi or o_rsp_valid or o_rsp_data or
           o_cmd_ready or o_sclk or i_cpol) begin
    // NNC verification fix (fix-verif, triage B): judge the settled snapshot of the assertion time step at the
    // first event of a later time step.
    if (chk15_pend && $realtime != chk15_t) begin
      a_CHK_015: assert (s15_cs === 1'b1 && s15_mosi === 1'b0 && s15_rv === 1'b0 &&
                         s15_rd === 8'h00 && s15_rdy === 1'b1 && s15_sclk === s15_cpol)
        else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
      chk15_pend = 1'b0;
    end
    // NNC verification fix (fix-verif, triage B): arm on every 1->0 transition of i_rst_n (contract CHK-015).
    if (rst15_prev === 1'b1 && i_rst_n === 1'b0) begin
      chk15_pend = 1'b1;
      chk15_t    = $realtime;
    end
    rst15_prev = i_rst_n;
    // NNC verification fix (fix-verif, triage B): (re)take the snapshot on every change inside the assertion
    // time step, so the last one holds the values after combinational settling.
    if (chk15_pend) begin
      s15_cs   = o_cs_n;
      s15_mosi = o_mosi;
      s15_rv   = o_rsp_valid;
      s15_rd   = o_rsp_data;
      s15_rdy  = o_cmd_ready;
      s15_sclk = o_sclk;
      s15_cpol = i_cpol;
    end
  end
  always_ff @(posedge i_clk) if (!i_rst_n) hits_CHK_015 <= hits_CHK_015 + 1;

  // ---------------- CHK-016 helper: reset in effect ----------------
  // NNC verification fix (fix-verif, triage B): ENV-008 says "Before the first assertion of i_rst_n the outputs
  // are undefined and no check applies", and ENV-007/GAP-001 says an edge that coincides with the assertion is
  // not covered by any check. The remaining fail (one per run, at 5000 ps = the first i_clk edge of the
  // simulation) is at the first rising edge while i_rst_n = 0 from time zero: no 1->0 transition of i_rst_n
  // exists there, so the edge itself is the first event at which the reset can act on the flip-flops that
  // drive o_cs_n/o_mosi (REQ-IMP-003/004), and the check sampled before that edge settled. The check is now
  // armed by a 1->0 transition of i_rst_n, or (reset held from time zero) after the first rising edge in
  // reset has passed; edges in the very time step of a 1->0 transition are left to CHK-015, which checks
  // the same outputs after settling. All later rising and falling edges in reset are checked with the same
  // outputs and exact values.
  logic    chk16_seen_fall = 1'b0;
  logic    chk16_seen_edge = 1'b0;
  realtime chk16_t_fall    = -1.0;
  always @(negedge i_rst_n) begin
    chk16_seen_fall = 1'b1;
    chk16_t_fall    = $realtime;
  end
  always @(posedge i_clk) if (!i_rst_n) chk16_seen_edge <= 1'b1;
  wire chk16_armed_w = chk16_seen_fall || chk16_seen_edge;

  // CHK-016: Output values held while in reset (SPI-6.2-02, SPI-6.2-04, SPI-6.2-05, SPI-6.2-06, SPI-5-04, SPI-5-08, SPI-5-10, SPI-5-12, SPI-5-13, SPI-6.2-07, SPI-14-12)
  always @(posedge i_clk or negedge i_clk) begin
    // NNC verification fix (fix-verif, triage B): only once the reset is in effect (ENV-008) and not at an edge
    // in the time step of the 1->0 transition (ENV-007/GAP-001; covered after settling by CHK-015).
    if (!i_rst_n && chk16_armed_w && $realtime != chk16_t_fall) begin
      a_CHK_016: assert (o_cs_n === 1'b1 && o_mosi === 1'b0 && o_rsp_valid === 1'b0 &&
                         o_rsp_data === 8'h00 && o_cmd_ready === 1'b1)
        else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
    end
  end
  // NNC verification fix (fix-verif, triage B): count a hit only where the check is evaluated.
  always_ff @(posedge i_clk) if (!i_rst_n && chk16_armed_w && $realtime != chk16_t_fall) hits_CHK_016 <= hits_CHK_016 + 1;

  // CHK-017: o_sclk follows i_cpol combinationally during reset (SPI-6.2-03, SPI-5-11)
  always @(posedge i_clk or negedge i_clk or i_cpol or o_sclk) begin
    if (!i_rst_n) begin
      a_CHK_017: assert (o_sclk === i_cpol)
        else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end
    end
  end
  always_ff @(posedge i_clk) if (!i_rst_n) hits_CHK_017 <= hits_CHK_017 + 1;

  // CHK-018: Ready to accept at first edge after reset release (SPI-6.2-11, SPI-7.1-08, SPI-14-21, SPI-6.2-12)
  a_CHK_018: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    wait_hs |-> (o_cmd_ready && (!rst_q || (o_cs_n && !o_rsp_valid))))
    else begin fails_CHK_018++; $display("NNC_FAIL CHK-018 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (wait_hs)) hits_CHK_018 <= hits_CHK_018 + 1;

  final begin
    // NNC verification fix (fix-verif, triage B): a CHK-015 snapshot still pending at the end of simulation
    // (no later event happened) is judged here, so no 1->0 transition goes unchecked.
    if (chk15_pend && !(s15_cs === 1'b1 && s15_mosi === 1'b0 && s15_rv === 1'b0 &&
                        s15_rd === 8'h00 && s15_rdy === 1'b1 && s15_sclk === s15_cpol)) begin
      fails_CHK_015++;
      $display("NNC_FAIL CHK-015 @%0t", $time);
    end
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
    $display("NNC_CHECK CHK-018 hits=%0d fails=%0d", hits_CHK_018, fails_CHK_018);
  end
endmodule
