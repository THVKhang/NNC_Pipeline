module nnc_chk_mosi #(
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

  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;
  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;

  localparam int unsigned DD = PARA_SPI_CLK_DIV;
  localparam int unsigned TOT = 16 * PARA_SPI_CLK_DIV;

  // helper state: cnt = cycles since handshake edge A; the cycle starting at A+m has cnt == m
  logic              busy;
  int unsigned       cnt;
  logic [7:0]        d_r;
  logic              ph_r;
  logic              mp_r;
  logic              mosi_q;
  wire               hs = i_cmd_valid && o_cmd_ready;

  always_ff @(posedge i_clk) begin
    mosi_q <= o_mosi;
    if (!i_rst_n) begin
      busy <= 1'b0;
      cnt  <= 0;
      d_r  <= 8'h00;
      ph_r <= 1'b0;
      mp_r <= 1'b0;
    end else if (hs) begin
      busy <= 1'b1;
      cnt  <= 0;
      d_r  <= i_cmd_data;
      // NNC verification fix (fix-verif, triage B): CPHA_b is i_cpha captured at the first acceptance edge of the
      // burst only (spec term CPHA_b, REQ-MODE-001); it controls o_mosi for the whole burst and changes of i_cpha
      // while o_cs_n=0 have no effect (REQ-MODE-002/003, REQ-ERR-001). Load ph_r only at a burst-start handshake
      // (o_cs_n=1 in the cycle ending at A, contract assumption) and keep it on continuation and Pause handshakes.
      if (o_cs_n) ph_r <= i_cpha;
      mp_r <= o_mosi;
    end else if (busy && (cnt < TOT + 1)) begin
      cnt  <= cnt + 1;
    end
  end

  function automatic logic [2:0] clampj(input int unsigned q);
    if (q > 7) clampj = 3'd7;
    else       clampj = q[2:0];
  endfunction

  // expected bits
  wire [2:0] j0   = clampj(cnt / (2 * DD));
  wire [2:0] j1   = clampj(((cnt >= DD) ? (cnt - DD) : 0) / (2 * DD));
  wire       exp0 = d_r[3'd7 - j0];
  wire       exp1 = (cnt < DD) ? mp_r : d_r[3'd7 - j1];

  // allowed change edges (CHK-013)
  wire a0 = !ph_r && ((cnt == 0) || (((cnt % (2 * DD)) == 0) && (cnt <= 14 * DD)));
  wire a1 = ph_r && (cnt >= DD) && (cnt <= 15 * DD) && (((cnt - DD) % (2 * DD)) == 0);
  wire changed = (o_mosi != mosi_q);

  // sampling edge detection (CHK-014), evaluated at the edge that ends the cycle before S
  wire [31:0] cn1 = cnt + 32'd1;
  wire       smp0 = busy && !ph_r && ((cn1 % (2 * DD)) == DD) && (cn1 < TOT);
  wire       smp1 = busy && ph_r && ((cn1 % (2 * DD)) == 0) && (cn1 >= 2 * DD) && (cn1 <= TOT);
  wire [2:0] js0  = clampj(cn1 / (2 * DD));
  wire [2:0] js1  = clampj((cn1 / (2 * DD) > 0) ? (cn1 / (2 * DD) - 1) : 0);
  wire       exp_s = ph_r ? d_r[3'd7 - js1] : d_r[3'd7 - js0];
  wire       smp   = smp0 || smp1;

  // CHK-011: MOSI shift timing, CPHA_b=0 (SPI-7.5-01, SPI-7.5-02, SPI-7.5-03, SPI-7.5-08, SPI-7.3-04, SPI-1.2-01, SPI-1.1-01, SPI-7.1-02, SPI-5-06, SPI-12-21)
  a_CHK_011: assert property (@(posedge i_clk) disable iff (!i_rst_n) (busy && !ph_r) |-> (o_mosi == exp0))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (busy && !ph_r)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: MOSI shift timing, CPHA_b=1 (SPI-7.5-04, SPI-7.5-09, SPI-7.3-05, SPI-14-07, SPI-12-21, SPI-5-06, SPI-1.1-01)
  a_CHK_012: assert property (@(posedge i_clk) disable iff (!i_rst_n) (busy && ph_r) |-> (o_mosi == exp1))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (busy && ph_r)) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: o_mosi changes only at shift edges; holds in Idle/Pause/Trail (SPI-7.5-05, SPI-7.5-06, SPI-14-07, SPI-7.8-03)
  a_CHK_013: assert property (@(posedge i_clk) disable iff (!i_rst_n) (!busy || changed) |->
      ((!changed && (busy || !o_mosi)) || (busy && (a0 || a1))))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!busy || changed)) hits_CHK_013 <= hits_CHK_013 + 1;

  // CHK-014: o_mosi stable at every sampling edge (SPI-7.5-07, SPI-12-22, SPI-12-21, SPI-5-15)
  a_CHK_014: assert property (@(posedge i_clk) disable iff (!i_rst_n) smp |=>
      ((o_mosi == $past(o_mosi)) && ($past(o_mosi) == $past(exp_s))))
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (smp)) hits_CHK_014 <= hits_CHK_014 + 1;

  final begin
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
  end
endmodule
