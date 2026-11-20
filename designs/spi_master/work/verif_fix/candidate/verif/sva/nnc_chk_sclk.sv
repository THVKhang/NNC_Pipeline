module nnc_chk_sclk #(
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

  int unsigned fails_CHK_023 = 0;
  int unsigned hits_CHK_023 = 0;
  int unsigned fails_CHK_024 = 0;
  int unsigned hits_CHK_024 = 0;
  int unsigned fails_CHK_025 = 0;
  int unsigned hits_CHK_025 = 0;
  int unsigned fails_CHK_026 = 0;
  int unsigned hits_CHK_026 = 0;
  int unsigned fails_CHK_027 = 0;
  int unsigned hits_CHK_027 = 0;

  localparam int unsigned D_CYC = PARA_SPI_CLK_DIV;
  localparam int unsigned L_CYC = 16 * PARA_SPI_CLK_DIV;

  // Helper state: transfer tracking (cnt = index of the cycle ending at the sampled edge)
  logic        hs_cmd;
  logic        t_act;
  int unsigned t_cnt;
  logic        t_cpol_b;
  logic        t_last_b;
  logic        t_edge_now;
  logic        t_exp_lvl;

  assign hs_cmd     = i_cmd_valid && o_cmd_ready;
  assign t_edge_now = t_act && (((t_cnt + 1) % D_CYC) == 0);
  assign t_exp_lvl  = ((((t_cnt + 1) / D_CYC) % 2) == 1) ? !t_cpol_b : t_cpol_b;

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      t_act    <= 1'b0;
      t_cnt    <= 0;
      t_cpol_b <= 1'b0;
      t_last_b <= 1'b0;
    end else if (hs_cmd) begin
      t_act    <= 1'b1;
      t_cnt    <= 0;
      // NNC verification fix (fix-verif, triage B): CPOL_b is i_cpol captured at the first acceptance edge of the
      // burst only (spec term CPOL_b, REQ-MODE-001); it controls o_sclk for the whole burst including Pause and
      // Trail, and changes of i_cpol while o_cs_n=0 have no effect (REQ-MODE-002/003, REQ-ERR-001). Load t_cpol_b
      // only at a burst-start handshake (o_cs_n=1 in the cycle ending at A, contract assumption) and keep it on
      // continuation and Pause handshakes. Used by CHK-023, CHK-025 and CHK-027.
      if (o_cs_n) t_cpol_b <= i_cpol;
      t_last_b <= i_cmd_last;
    end else if (t_act) begin
      if (t_cnt == L_CYC - 1) t_act <= 1'b0;
      else                    t_cnt <= t_cnt + 1;
    end
  end

  // CHK-023: SCLK edges at A+k*D with correct levels (SPI-3-01, SPI-3-02, SPI-3-03, SPI-7.4-01, SPI-7.4-04, SPI-1.2-05, SPI-4-02, SPI-8-06, SPI-12-21, SPI-7.3-02)
  a_CHK_023: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    t_act |=> ($past(t_edge_now) ? (o_sclk != $past(o_sclk) && o_sclk == $past(t_exp_lvl)) : (o_sclk == $past(o_sclk))))
    else begin fails_CHK_023++; $display("NNC_FAIL CHK-023 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (t_act)) hits_CHK_023 <= hits_CHK_023 + 1;

  // CHK-024: No other o_sclk changes while o_cs_n=0 (SPI-7.4-02, SPI-7.3-03)
  a_CHK_024: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (!o_cs_n && !t_edge_now) |=> (o_cs_n || (o_sclk == $past(o_sclk))))
    else begin fails_CHK_024++; $display("NNC_FAIL CHK-024 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_cs_n && !t_edge_now)) hits_CHK_024 <= hits_CHK_024 + 1;

  // CHK-025: SCLK at CPOL_b in lead, Pause and Trail (SPI-7.4-03, SPI-3-05, SPI-12-22, SPI-7.3-02)
  a_CHK_025: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (!o_cs_n && !(t_act && (t_cnt >= D_CYC))) |-> (o_sclk == t_cpol_b))
    else begin fails_CHK_025++; $display("NNC_FAIL CHK-025 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_cs_n && !(t_act && (t_cnt >= D_CYC)))) hits_CHK_025 <= hits_CHK_025 + 1;

  // CHK-026: o_sclk equals i_cpol while o_cs_n=1 (SPI-7.4-05, SPI-7.4-06, SPI-14-08, SPI-10-03, SPI-6.2-03)
  a_CHK_026: assert property (@(posedge i_clk)
    ((!i_rst_n) || o_cs_n) |-> (o_sclk == i_cpol))
    else begin fails_CHK_026++; $display("NNC_FAIL CHK-026 @%0t", $time); end
  always_ff @(posedge i_clk) if ((!i_rst_n) || o_cs_n) hits_CHK_026 <= hits_CHK_026 + 1;

  // CHK-027: No-gap joint between back-to-back transfers (SPI-7.4-07, SPI-7.8-01, SPI-1.2-07, SPI-8-06)
  a_CHK_027: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (t_act && (t_cnt == L_CYC - 1) && !t_last_b && hs_cmd) |=>
      (!o_cs_n && o_sclk != $past(o_sclk) && o_sclk == t_cpol_b)
      ##D_CYC (!o_cs_n && o_sclk != $past(o_sclk) && o_sclk == !t_cpol_b))
    else begin fails_CHK_027++; $display("NNC_FAIL CHK-027 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (t_act && (t_cnt == L_CYC - 1) && !t_last_b && hs_cmd)) hits_CHK_027 <= hits_CHK_027 + 1;

  final begin
    $display("NNC_CHECK CHK-023 hits=%0d fails=%0d", hits_CHK_023, fails_CHK_023);
    $display("NNC_CHECK CHK-024 hits=%0d fails=%0d", hits_CHK_024, fails_CHK_024);
    $display("NNC_CHECK CHK-025 hits=%0d fails=%0d", hits_CHK_025, fails_CHK_025);
    $display("NNC_CHECK CHK-026 hits=%0d fails=%0d", hits_CHK_026, fails_CHK_026);
    $display("NNC_CHECK CHK-027 hits=%0d fails=%0d", hits_CHK_027, fails_CHK_027);
  end
endmodule
