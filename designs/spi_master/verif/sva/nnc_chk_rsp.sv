module nnc_chk_rsp #(
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

  int unsigned fails_CHK_019 = 0;
  int unsigned hits_CHK_019 = 0;
  int unsigned fails_CHK_020 = 0;
  int unsigned hits_CHK_020 = 0;
  int unsigned fails_CHK_021 = 0;
  int unsigned hits_CHK_021 = 0;
  int unsigned fails_CHK_022 = 0;
  int unsigned hits_CHK_022 = 0;

  localparam int unsigned END_K = 16 * PARA_SPI_CLK_DIV;

  logic        pr;
  logic        end_q;
  logic        active;
  logic        cpha_r;
  int unsigned k;
  logic [7:0]  sh;
  logic [7:0]  q0;
  logic [7:0]  q1;
  logic [1:0]  qn;

  // Reference model: transfer tracking, MISO capture and response queue
  always_ff @(posedge i_clk) begin : model
    int unsigned kk;
    int unsigned m;
    logic        is_end;
    logic        smp;
    logic [7:0]  r;
    logic [7:0]  h0;
    logic [7:0]  h1;
    logic [1:0]  n;
    pr <= i_rst_n;
    if (!i_rst_n) begin
      end_q  <= 1'b0;
      active <= 1'b0;
      cpha_r <= 1'b0;
      k      <= 0;
      sh     <= 8'h00;
      q0     <= 8'h00;
      q1     <= 8'h00;
      qn     <= 2'd0;
    end else begin
      kk     = k + 1;
      m      = kk / PARA_SPI_CLK_DIV;
      is_end = active && (kk == END_K);
      smp    = active && ((kk % PARA_SPI_CLK_DIV) == 0) &&
               (cpha_r ? (((m % 2) == 0) && (m >= 2) && (m <= 16))
                       : (((m % 2) == 1) && (m <= 15)));
      r  = cpha_r ? {sh[6:0], i_miso} : sh;
      h0 = q0;
      h1 = q1;
      n  = qn;
      if (o_rsp_valid && i_rsp_ready && (n != 2'd0)) begin
        h0 = h1;
        n  = n - 2'd1;
      end
      if (is_end) begin
        if (n == 2'd0)      h0 = r;
        else if (n == 2'd1) h1 = r;
        if (n != 2'd3) n = n + 2'd1;
      end
      q0 <= h0;
      q1 <= h1;
      qn <= n;
      end_q <= is_end;
      if (i_cmd_valid && o_cmd_ready) begin
        active <= 1'b1;
        k      <= 0;
        cpha_r <= i_cpha;
        sh     <= 8'h00;
      end else if (active) begin
        k <= kk;
        if (smp) sh <= {sh[6:0], i_miso};
        if (is_end) active <= 1'b0;
      end
    end
  end

  // CHK-019: Response outputs change only at clock edges or reset (SPI-7.7-09)
  logic chg_ok_clk;
  logic chg_ok_rst;
  logic chg_seen;
  logic [7:0] prev_data;
  logic prev_valid;
  logic prev_rst_n;
  always_ff @(posedge i_clk) begin
    prev_data  <= o_rsp_data;
    prev_valid <= o_rsp_valid;
  end
  // asynchronous-change detector: any change of the outputs between clock edges
  always @(o_rsp_valid or o_rsp_data) begin
    chg_seen = 1'b1;
  end
  initial chg_seen = 1'b0;
  // evaluated just before each clock edge: changes since the last edge are legal only
  // if they happened in the time step of that edge; we compare against the sampled values.
  // Outputs sampled at edge E-1 (prev_*) and at edge E (preponed) can differ only through
  // changes at E-1's time step (legal) ; mid-cycle changes show as a change between a
  // value captured shortly after the edge and the value just before the next edge.
  logic [7:0] post_data;
  logic       post_valid;
  logic       post_ok;
  always @(negedge i_clk) begin
    post_data  <= o_rsp_data;
    post_valid <= o_rsp_valid;
  end
  always_ff @(posedge i_clk) begin
    post_ok <= 1'b1;
  end
  a_CHK_019: assert property (@(posedge i_clk) disable iff (!i_rst_n) 1'b1 |-> (post_ok && (o_rsp_valid == post_valid) && (o_rsp_data == post_data)))
    else begin fails_CHK_019++; $display("NNC_FAIL CHK-019 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (1'b1)) hits_CHK_019 <= hits_CHK_019 + 1;

  // CHK-020: Response reference model: data, order, timing, depth<=2 (SPI-7.7-01..07, SPI-7.7-11, SPI-7.7-12, SPI-8-03, SPI-8-14, SPI-8-16, SPI-14-06, SPI-10-13, SPI-10-06, SPI-1.1-02, SPI-1.2-09, SPI-7.6-01, SPI-7.6-02, SPI-7.6-03, SPI-7.6-05, SPI-5-09)
  a_CHK_020: assert property (@(posedge i_clk) disable iff (!i_rst_n) pr |-> ((o_rsp_valid == (qn != 2'd0)) && ((qn == 2'd0) || (o_rsp_data == q0)) && (qn <= 2'd2)))
    else begin fails_CHK_020++; $display("NNC_FAIL CHK-020 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pr)) hits_CHK_020 <= hits_CHK_020 + 1;

  // CHK-021: o_rsp_data hold and i_rsp_ready ignored while not valid (SPI-7.7-08, SPI-7.7-10, SPI-14-12, SPI-7.7-07)
  a_CHK_021: assert property (@(posedge i_clk) disable iff (!i_rst_n) (pr && !end_q && (!$past(o_rsp_valid) || !$past(i_rsp_ready))) |-> ((o_rsp_valid == $past(o_rsp_valid)) && $stable(o_rsp_data)))
    else begin fails_CHK_021++; $display("NNC_FAIL CHK-021 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pr && !end_q && (!$past(o_rsp_valid) || !$past(i_rsp_ready)))) hits_CHK_021 <= hits_CHK_021 + 1;

  // CHK-022: No transfer starts while a byte is shown or held (SPI-7.8-07, SPI-7.7-13, SPI-8-15, SPI-14-05, SPI-1.1-04, SPI-10-07, SPI-8-12, SPI-14-03)
  a_CHK_022: assert property (@(posedge i_clk) disable iff (!i_rst_n) (i_cmd_valid && o_cmd_ready) |-> (!o_rsp_valid && (qn == 2'd0)))
    else begin fails_CHK_022++; $display("NNC_FAIL CHK-022 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (i_cmd_valid && o_cmd_ready)) hits_CHK_022 <= hits_CHK_022 + 1;

  final begin
    $display("NNC_CHECK CHK-019 hits=%0d fails=%0d", hits_CHK_019, fails_CHK_019);
    $display("NNC_CHECK CHK-020 hits=%0d fails=%0d", hits_CHK_020, fails_CHK_020);
    $display("NNC_CHECK CHK-021 hits=%0d fails=%0d", hits_CHK_021, fails_CHK_021);
    $display("NNC_CHECK CHK-022 hits=%0d fails=%0d", hits_CHK_022, fails_CHK_022);
  end
endmodule
