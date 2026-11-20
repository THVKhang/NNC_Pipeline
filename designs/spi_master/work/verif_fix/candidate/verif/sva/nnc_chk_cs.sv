module nnc_chk_cs #(
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

  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;
  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;

  localparam int unsigned D_CS   = PARA_SPI_CLK_DIV;
  localparam int unsigned LIM_CS = 17 * PARA_SPI_CLK_DIV;

  // Helper state
  logic        cs_hs_q;
  assign cs_hs_q = i_cmd_valid && o_cmd_ready;

  // CHK-007 helpers: first last-transfer handshake A_L and cycles since it
  logic              lastseen_q;
  int unsigned       lcnt_q;
  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      lastseen_q <= 1'b0;
      lcnt_q     <= 0;
    end else if (lastseen_q) begin
      if (lcnt_q == LIM_CS) begin
        lastseen_q <= 1'b0;
        lcnt_q     <= 0;
      end else begin
        lcnt_q <= lcnt_q + 1;
      end
    end else if (cs_hs_q && i_cmd_last) begin
      lastseen_q <= 1'b1;
      lcnt_q     <= 1;
    end
  end

  // CHK-008 helpers: consecutive high samples of o_cs_n after a burst
  logic        seen_low_q;
  int unsigned hc_q;
  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      seen_low_q <= 1'b0;
      hc_q       <= 0;
    end else if (!o_cs_n) begin
      seen_low_q <= 1'b1;
      hc_q       <= 0;
    end else if (seen_low_q && hc_q < D_CS) begin
      hc_q <= hc_q + 1;
    end
  end

  // CHK-009 helpers: lead counter and captured CPOL
  int unsigned ldc_q;
  logic        cpol_b_q;
  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      ldc_q    <= 0;
      cpol_b_q <= 1'b0;
    end else if (cs_hs_q && o_cs_n) begin
      ldc_q    <= 1;
      cpol_b_q <= i_cpol;
    end else if (ldc_q != 0 && ldc_q <= D_CS) begin
      ldc_q <= ldc_q + 1;
    end else begin
      ldc_q <= 0;
    end
  end

  // CHK-006: o_cs_n falls exactly at a burst-start handshake (SPI-7.2-01, SPI-8-02, SPI-7.1-01)
  a_CHK_006: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    o_cs_n |=> (o_cs_n == !$past(i_cmd_valid && o_cmd_ready)))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_cs_n)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: o_cs_n low for whole burst, rises at A_last+17D only (SPI-7.2-02, SPI-7.2-03, SPI-7.8-06, SPI-3-06, SPI-8-04, SPI-8-07, SPI-1.2-02, SPI-14-01, SPI-7.2-07, SPI-7.1-02, SPI-5-07, SPI-12-22)
  a_CHK_007: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    !o_cs_n |=> (o_cs_n == $past(lastseen_q && (lcnt_q == LIM_CS))))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_cs_n)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: Minimum o_cs_n high gap between bursts (SPI-7.2-05, SPI-8-05, SPI-14-02, SPI-12-22)
  a_CHK_008: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    ($fell(o_cs_n) && seen_low_q) |-> (hc_q >= D_CS))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ($fell(o_cs_n) && seen_low_q)) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: Lead time: first SCLK edge D cycles after o_cs_n falls (SPI-7.2-04, SPI-8-01, SPI-14-01, SPI-12-22)
  a_CHK_009: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (ldc_q != 0) |-> ((ldc_q <= D_CS) ? (!o_cs_n && (o_sclk == cpol_b_q)) : (o_sclk != cpol_b_q)))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (ldc_q != 0)) hits_CHK_009 <= hits_CHK_009 + 1;

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
  end
endmodule
