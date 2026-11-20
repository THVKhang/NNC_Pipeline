module nnc_chk_cmd #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;

  localparam int unsigned D_P   = PARA_SPI_CLK_DIV;
  localparam int unsigned XLEN  = 16 * PARA_SPI_CLK_DIV;

  // ---------------- helper: command handshake and transfer phase tracking ----------------
  wire hs_w = i_cmd_valid && o_cmd_ready;

  logic        xfer_q, pause_q, trail_q, last_q;
  logic [15:0] k_q;

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      xfer_q  <= 1'b0;
      pause_q <= 1'b0;
      trail_q <= 1'b0;
      last_q  <= 1'b0;
      k_q     <= 16'd0;
    end else if (hs_w) begin
      xfer_q  <= 1'b1;
      pause_q <= 1'b0;
      trail_q <= 1'b0;
      last_q  <= i_cmd_last;
      k_q     <= 16'd0;
    end else if (xfer_q) begin
      if (32'(k_q) == XLEN - 1) begin
        xfer_q <= 1'b0;
        k_q    <= 16'd0;
        if (last_q) trail_q <= 1'b1;
        else        pause_q <= 1'b1;
      end else begin
        k_q <= k_q + 16'd1;
      end
    end else if (trail_q) begin
      if (32'(k_q) == D_P - 1) begin
        trail_q <= 1'b0;
        k_q     <= 16'd0;
      end else begin
        k_q <= k_q + 16'd1;
      end
    end
  end

  // ---------------- helper: idle window after o_cs_n rise ----------------
  logic        cs_q;
  logic        idle_act_q;
  logic [15:0] idle_ic_q;

  wire        rose_cs_w  = o_cs_n && !cs_q;
  wire        cur_act_w  = rose_cs_w || idle_act_q;
  wire [15:0] cur_i_w    = rose_cs_w ? 16'd0 :
                           ((32'(idle_ic_q) >= D_P) ? idle_ic_q : idle_ic_q + 16'd1);

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      cs_q       <= 1'b1;
      idle_act_q <= 1'b0;
      idle_ic_q  <= 16'd0;
    end else begin
      cs_q       <= o_cs_n;
      idle_act_q <= cur_act_w && !hs_w && o_cs_n;
      idle_ic_q  <= cur_i_w;
    end
  end

  // ---------------- helper: o_cmd_ready change timing ----------------
  longint signed t_clk = -1;
  longint signed t_rst = -1;
  int unsigned chg_cnt  = 0;
  int unsigned bad_cnt  = 0;
  int unsigned chg_seen = 0;
  int unsigned bad_seen = 0;

  always @(posedge i_clk) t_clk = longint'($time);
  always @(negedge i_rst_n) t_rst = longint'($time);
  always @(o_cmd_ready) begin
    if ($time != 0) begin
      chg_cnt = chg_cnt + 1;
      if (!(longint'($time) == t_clk || longint'($time) == t_rst))
        bad_cnt = bad_cnt + 1;
    end
  end

  always_ff @(posedge i_clk) begin
    chg_seen <= chg_cnt;
    bad_seen <= bad_cnt;
  end

  // CHK-001: o_cmd_ready changes only at clock edges or reset assertion (SPI-7.1-05, SPI-5-05, SPI-14-04, SPI-12-23)
  a_CHK_001: assert property (@(posedge i_clk) disable iff (!i_rst_n) (chg_cnt != chg_seen) |-> (bad_cnt == bad_seen))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (chg_cnt != chg_seen)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_cmd_ready low while a response is shown (SPI-7.1-06, SPI-12-23)
  a_CHK_002: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_rsp_valid |-> !o_cmd_ready)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rsp_valid)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: o_cmd_ready in Idle after o_cs_n rise (SPI-7.1-07, SPI-7.1-08, SPI-14-16, SPI-14-03, SPI-12-23)
  a_CHK_003: assert property (@(posedge i_clk) disable iff (!i_rst_n) cur_act_w |->
      ((32'(cur_i_w) + 32'd1 < D_P) ? !o_cmd_ready : (o_cmd_ready == !o_rsp_valid)))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cur_act_w)) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: o_cmd_ready during a transfer and in its last cycle (SPI-7.1-09, SPI-7.1-10, SPI-8-12, SPI-14-03, SPI-3-01, SPI-12-23)
  a_CHK_004: assert property (@(posedge i_clk) disable iff (!i_rst_n) xfer_q |->
      ((32'(k_q) == XLEN - 1) ? (o_cmd_ready == (!last_q && !o_rsp_valid)) : !o_cmd_ready))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (xfer_q)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: o_cmd_ready in Pause and Trail (SPI-7.1-11, SPI-7.1-12, SPI-14-03, SPI-12-23)
  a_CHK_005: assert property (@(posedge i_clk) disable iff (!i_rst_n) (pause_q || trail_q) |->
      (pause_q ? (o_cmd_ready == !o_rsp_valid) : !o_cmd_ready))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pause_q || trail_q)) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
