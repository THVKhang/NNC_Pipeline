module nnc_cov #(
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

  int unsigned hits_COVP_001 = 0;
  int unsigned hits_COVP_002 = 0;
  int unsigned hits_COVP_003 = 0;
  int unsigned hits_COVP_004 = 0;
  int unsigned hits_COVP_005 = 0;
  int unsigned hits_COVP_006 = 0;
  int unsigned hits_COVP_007 = 0;
  int unsigned hits_COVP_008 = 0;
  int unsigned hits_COVP_009 = 0;
  int unsigned hits_COVP_010 = 0;
  int unsigned hits_COVP_011 = 0;
  int unsigned hits_COVP_012 = 0;
  int unsigned hits_COVP_013 = 0;
  int unsigned hits_COVP_014 = 0;
  int unsigned hits_COVP_015 = 0;
  int unsigned hits_COVP_016 = 0;
  int unsigned hits_COVP_017 = 0;
  int unsigned hits_COVP_018 = 0;
  int unsigned hits_COVP_019 = 0;
  int unsigned hits_COVP_020 = 0;
  int unsigned hits_COVP_021 = 0;
  int unsigned hits_COVP_022 = 0;
  int unsigned hits_COVP_023 = 0;
  int unsigned hits_COVP_024 = 0;
  int unsigned hits_COVP_025 = 0;
  int unsigned hits_COVP_026 = 0;
  int unsigned hits_COVP_027 = 0;
  int unsigned hits_COVP_028 = 0;
  int unsigned hits_COVP_029 = 0;
  int unsigned hits_COVP_030 = 0;
  int unsigned hits_COVP_031 = 0;
  int unsigned hits_COVP_032 = 0;
  int unsigned hits_COVP_033 = 0;
  int unsigned hits_COVP_034 = 0;
  int unsigned hits_COVP_035 = 0;
  int unsigned hits_COVP_036 = 0;
  int unsigned hits_COVP_037 = 0;
  int unsigned hits_COVP_038 = 0;
  int unsigned hits_COVP_039 = 0;

  // helper state
  logic [7:0] bcnt = '0;
  logic [9:0] pcnt = '0;
  logic [7:0] stall = '0;
  logic [5:0] hi_cnt = '0;
  logic cs_q = 1'b1;
  logic rdy_q = 1'b1;
  logic valid_q = 1'b0;
  logic pop_q = 1'b0;
  logic cpol_q = 1'b0;
  logic cpha_q = 1'b0;
  logic cpol_b = 1'b0;
  logic cpha_b = 1'b0;
  logic s_xfer = 1'b0, s_pause = 1'b0, s_gap = 1'b0, s_rsp = 1'b0;
  logic r_xfer = 1'b0, r_pause = 1'b0, r_gap = 1'b0, r_rsp = 1'b0;
  logic rst_seen = 1'b0;

  wire hs = i_cmd_valid && o_cmd_ready;
  wire cs_rise = o_cs_n && !cs_q;
  wire pause_c = !o_cs_n && (o_sclk == cpol_b) && o_cmd_ready;
  wire joint_c = !o_cs_n && (o_sclk != cpol_b);

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      bcnt <= '0; pcnt <= '0; stall <= '0; hi_cnt <= '0;
      cs_q <= 1'b1; rdy_q <= 1'b1; valid_q <= 1'b0; pop_q <= 1'b0;
      cpol_q <= i_cpol; cpha_q <= i_cpha;
      cpol_b <= i_cpol; cpha_b <= i_cpha;
      if (!rst_seen) begin
        r_xfer <= s_xfer; r_pause <= s_pause; r_gap <= s_gap; r_rsp <= s_rsp;
      end
      rst_seen <= 1'b1;
    end else begin
      rst_seen <= 1'b0;
      r_xfer <= 1'b0; r_pause <= 1'b0; r_gap <= 1'b0; r_rsp <= 1'b0;
      cs_q <= o_cs_n; rdy_q <= o_cmd_ready; valid_q <= o_rsp_valid;
      pop_q <= o_rsp_valid && i_rsp_ready;
      cpol_q <= i_cpol; cpha_q <= i_cpha;
      if (hs) begin
        if (o_cs_n) begin
          cpol_b <= i_cpol; cpha_b <= i_cpha; bcnt <= 8'd1;
        end else if (bcnt != 8'd255) bcnt <= bcnt + 8'd1;
      end
      if (pause_c && !hs) begin
        if (pcnt != 10'd1023) pcnt <= pcnt + 10'd1;
      end else pcnt <= '0;
      if (o_cs_n) begin
        if (hi_cnt != 6'd63) hi_cnt <= hi_cnt + 6'd1;
      end else hi_cnt <= '0;
      if (o_rsp_valid && !i_rsp_ready) begin
        if (stall != 8'd255) stall <= stall + 8'd1;
      end else stall <= '0;
      s_xfer  <= !o_cs_n && !o_cmd_ready;
      s_pause <= pause_c;
      s_gap   <= o_cs_n && !o_cmd_ready && !o_rsp_valid;
      s_rsp   <= o_rsp_valid;
    end
  end

  // COVP-001: Burst start in mode 0 (CPOL=0,CPHA=0)
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && !i_cpol && !i_cpha)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: Burst start in mode 1 (CPOL=0,CPHA=1)
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && !i_cpol && i_cpha)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: Burst start in mode 2 (CPOL=1,CPHA=0)
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && i_cpol && !i_cpha)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: Burst start in mode 3 (CPOL=1,CPHA=1)
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && i_cpol && i_cpha)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Mode inputs changed in the cycle before burst-start acceptance
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && (i_cpol != cpol_q || i_cpha != cpha_q))) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Mode inputs differ from captured mode during a burst (error test)
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_cs_n && (i_cpol != cpol_b || i_cpha != cpha_b))) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: i_cpol toggled in Idle with o_sclk following
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_cs_n && (i_cpol != cpol_q) && (o_sclk == i_cpol))) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: i_cmd_last=1 on the first byte of a burst
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && i_cmd_last)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: Burst of length 1 completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt == 8'd1)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: Burst of length 2 completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt == 8'd2)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: Burst of length 3 to 15 completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt >= 8'd3 && bcnt <= 8'd15)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: Burst of length 16 completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt == 8'd16)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: Burst of length 17 to 31 completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt >= 8'd17 && bcnt <= 8'd31)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: Long burst of 32 or more bytes completed
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && bcnt >= 8'd32)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: No-gap joint into a continuing transfer
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && joint_c && !i_cmd_last)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Joint handshake carrying i_cmd_last=1
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && joint_c && i_cmd_last)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Pause entered
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pause_c && pcnt == 10'd0)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Pause lasting 16 or more cycles
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pause_c && pcnt >= 10'd16)) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Long Pause of 64 or more cycles
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pause_c && pcnt >= 10'd64)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: Pause exit by a command handshake
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && pause_c)) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: Pause exit with i_cmd_last=1
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && pause_c && i_cmd_last)) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: Idle blocked cycle after o_cs_n rise
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_cs_n && !o_cmd_ready && !o_rsp_valid)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: Burst start at first ready cycle of Idle
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && !rdy_q)) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: o_cs_n rises while a response byte is shown
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (cs_rise && o_rsp_valid)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: Response byte becomes valid
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rsp_valid && !valid_q)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: Response taken in its first valid cycle
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rsp_valid && i_rsp_ready && !valid_q)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: Back-pressure on response for 3 or more cycles
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rsp_valid && !i_rsp_ready && stall >= 8'd3)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: Long response back-pressure of 32 or more cycles
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rsp_valid && !i_rsp_ready && stall >= 8'd32)) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: Command blocked by response back-pressure
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (i_cmd_valid && !o_cmd_ready && o_rsp_valid && stall >= 8'd8)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: Response popped and another byte still valid
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pop_q && o_rsp_valid)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: Command handshake right after response taken
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (pop_q && hs)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: Response shown during Pause or Trail
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_cs_n && (o_sclk == cpol_b) && !o_cmd_ready && o_rsp_valid)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: First edge after reset release ready
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && o_cmd_ready && o_cs_n && !o_rsp_valid)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: Command handshake at first edge after reset
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && hs)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: Reset during Transfer or Trail
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && r_xfer)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: Reset during Pause
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && r_pause)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: Reset during Idle gap
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && r_gap)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: Reset with a response byte shown or held
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_seen && r_rsp)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: Burst start after long Idle
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (hs && o_cs_n && hi_cnt >= 6'd32)) hits_COVP_039 <= hits_COVP_039 + 1;

  final begin
    $display("NNC_COVER COVP-001 hits=%0d", hits_COVP_001);
    $display("NNC_COVER COVP-002 hits=%0d", hits_COVP_002);
    $display("NNC_COVER COVP-003 hits=%0d", hits_COVP_003);
    $display("NNC_COVER COVP-004 hits=%0d", hits_COVP_004);
    $display("NNC_COVER COVP-005 hits=%0d", hits_COVP_005);
    $display("NNC_COVER COVP-006 hits=%0d", hits_COVP_006);
    $display("NNC_COVER COVP-007 hits=%0d", hits_COVP_007);
    $display("NNC_COVER COVP-008 hits=%0d", hits_COVP_008);
    $display("NNC_COVER COVP-009 hits=%0d", hits_COVP_009);
    $display("NNC_COVER COVP-010 hits=%0d", hits_COVP_010);
    $display("NNC_COVER COVP-011 hits=%0d", hits_COVP_011);
    $display("NNC_COVER COVP-012 hits=%0d", hits_COVP_012);
    $display("NNC_COVER COVP-013 hits=%0d", hits_COVP_013);
    $display("NNC_COVER COVP-014 hits=%0d", hits_COVP_014);
    $display("NNC_COVER COVP-015 hits=%0d", hits_COVP_015);
    $display("NNC_COVER COVP-016 hits=%0d", hits_COVP_016);
    $display("NNC_COVER COVP-017 hits=%0d", hits_COVP_017);
    $display("NNC_COVER COVP-018 hits=%0d", hits_COVP_018);
    $display("NNC_COVER COVP-019 hits=%0d", hits_COVP_019);
    $display("NNC_COVER COVP-020 hits=%0d", hits_COVP_020);
    $display("NNC_COVER COVP-021 hits=%0d", hits_COVP_021);
    $display("NNC_COVER COVP-022 hits=%0d", hits_COVP_022);
    $display("NNC_COVER COVP-023 hits=%0d", hits_COVP_023);
    $display("NNC_COVER COVP-024 hits=%0d", hits_COVP_024);
    $display("NNC_COVER COVP-025 hits=%0d", hits_COVP_025);
    $display("NNC_COVER COVP-026 hits=%0d", hits_COVP_026);
    $display("NNC_COVER COVP-027 hits=%0d", hits_COVP_027);
    $display("NNC_COVER COVP-028 hits=%0d", hits_COVP_028);
    $display("NNC_COVER COVP-029 hits=%0d", hits_COVP_029);
    $display("NNC_COVER COVP-030 hits=%0d", hits_COVP_030);
    $display("NNC_COVER COVP-031 hits=%0d", hits_COVP_031);
    $display("NNC_COVER COVP-032 hits=%0d", hits_COVP_032);
    $display("NNC_COVER COVP-033 hits=%0d", hits_COVP_033);
    $display("NNC_COVER COVP-034 hits=%0d", hits_COVP_034);
    $display("NNC_COVER COVP-035 hits=%0d", hits_COVP_035);
    $display("NNC_COVER COVP-036 hits=%0d", hits_COVP_036);
    $display("NNC_COVER COVP-037 hits=%0d", hits_COVP_037);
    $display("NNC_COVER COVP-038 hits=%0d", hits_COVP_038);
    $display("NNC_COVER COVP-039 hits=%0d", hits_COVP_039);
  end
endmodule
