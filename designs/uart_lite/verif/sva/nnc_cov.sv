module nnc_cov #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_tx_valid,
  input  logic                        o_tx_ready,
  input  logic [7:0]                  i_tx_data,
  input  logic                        o_rx_valid,
  input  logic                        i_rx_ready,
  input  logic [7:0]                  o_rx_data,
  input  logic                        o_rx_frame_err,
  input  logic                        o_rx_overrun,
  input  logic                        o_txd,
  input  logic                        i_rxd
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
  int unsigned hits_COVP_040 = 0;

localparam int unsigned CV_N = PARA_UART_CLKS_PER_BIT;
localparam int unsigned CV_H = PARA_UART_CLKS_PER_BIT / 2;

logic cv_s1 = 1'b1;
logic cv_s2 = 1'b1;
logic cv_sp = 1'b1;
logic cv_busy = 1'b0;
logic cv_lowok = 1'b0;
logic cv_hi1 = 1'b0;
logic cv_glq = 1'b0;
logic cv_m1 = 1'b0;
logic cv_load_q = 1'b0;
logic [31:0] cv_rc = 32'd0;
logic [31:0] cv_lowc = 32'd0;
logic [31:0] cv_idle = 32'd0;
logic [7:0] cv_chain = 8'd0;
logic [7:0] cv_drops = 8'd0;
logic cv_rdy_q = 1'b1;
logic cv_rxv_q = 1'b0;
logic cv_rst_q = 1'b1;
logic cv_vq = 1'b0;
logic cv_rq = 1'b0;
logic [7:0] cv_dq = 8'd0;
logic cv_mid_tx = 1'b0;
logic cv_mid_rx = 1'b0;
logic cv_mid_hold = 1'b0;

wire cv_acc = i_tx_valid && o_tx_ready;
wire cv_start = !cv_busy && cv_sp && !cv_s2;
wire cv_glitch = cv_busy && (cv_rc == CV_H) && cv_s2;
wire cv_deliv = cv_busy && (cv_rc == (CV_H + 9 * CV_N));
wire cv_drop = cv_deliv && o_rx_valid && !i_rx_ready;
wire cv_rel = i_rst_n && !cv_rst_q;

always_ff @(posedge i_clk) begin
  cv_rst_q <= i_rst_n;
  cv_rdy_q <= o_tx_ready;
  cv_rxv_q <= o_rx_valid;
  cv_vq <= i_tx_valid;
  cv_rq <= i_rx_ready;
  cv_dq <= i_tx_data;
  if (!i_rst_n) begin
    if (!cv_rdy_q) cv_mid_tx <= 1'b1;
    if (cv_busy) cv_mid_rx <= 1'b1;
    if (cv_rxv_q) cv_mid_hold <= 1'b1;
    cv_s1 <= 1'b1; cv_s2 <= 1'b1; cv_sp <= 1'b1;
    cv_busy <= 1'b0; cv_rc <= 32'd0; cv_lowok <= 1'b0; cv_hi1 <= 1'b0;
    cv_glq <= 1'b0; cv_m1 <= 1'b0; cv_load_q <= 1'b0;
    cv_lowc <= 32'd0; cv_idle <= 32'd0; cv_chain <= 8'd0; cv_drops <= 8'd0;
  end else begin
    if (cv_rst_q) begin
      cv_mid_tx <= 1'b0; cv_mid_rx <= 1'b0; cv_mid_hold <= 1'b0;
    end
    cv_s1 <= i_rxd;
    cv_s2 <= cv_s1;
    cv_sp <= cv_s2;
    cv_m1 <= cv_deliv;
    cv_glq <= cv_glitch;
    cv_load_q <= cv_deliv && (!o_rx_valid || i_rx_ready);
    if (cv_start) begin
      cv_busy <= 1'b1; cv_rc <= 32'd1; cv_lowok <= 1'b1; cv_hi1 <= 1'b0;
    end else if (cv_busy) begin
      cv_rc <= cv_rc + 32'd1;
      if (cv_rc <= CV_H && cv_s2) cv_lowok <= 1'b0;
      if (cv_rc == 32'd1 && cv_s2) cv_hi1 <= 1'b1;
      if (cv_glitch || cv_deliv) cv_busy <= 1'b0;
    end
    if (!cv_s2) begin
      if (cv_lowc != 32'hFFFFFFFF) cv_lowc <= cv_lowc + 32'd1;
    end else cv_lowc <= 32'd0;
    if (cv_acc) cv_idle <= 32'd0;
    else if (o_tx_ready && !i_tx_valid && cv_idle != 32'hFFFFFFFF) cv_idle <= cv_idle + 32'd1;
    if (cv_acc) begin
      if (!cv_rdy_q) begin
        if (cv_chain != 8'hFF) cv_chain <= cv_chain + 8'd1;
      end else cv_chain <= 8'd0;
    end
    if (cv_deliv) begin
      if (cv_drop) begin
        if (cv_drops != 8'hFF) cv_drops <= cv_drops + 8'd1;
      end else cv_drops <= 8'd0;
    end
  end
end

// COVP-001: TX byte accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc)) hits_COVP_001 <= hits_COVP_001 + 1;
// COVP-002: TX data 0x00 accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && i_tx_data == 8'h00)) hits_COVP_002 <= hits_COVP_002 + 1;
// COVP-003: TX data 0xFF accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && i_tx_data == 8'hFF)) hits_COVP_003 <= hits_COVP_003 + 1;
// COVP-004: TX data 0x55 or 0xAA accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && (i_tx_data == 8'h55 || i_tx_data == 8'hAA))) hits_COVP_004 <= hits_COVP_004 + 1;
// COVP-005: TX back-to-back acceptance at E0+10N
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && !cv_rdy_q)) hits_COVP_005 <= hits_COVP_005 + 1;
// COVP-006: TX back-to-back chain of 3 or more frames
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && !cv_rdy_q && cv_chain >= 8'd2)) hits_COVP_006 <= hits_COVP_006 + 1;
// COVP-007: TX acceptance after a short idle gap
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && cv_rdy_q && cv_idle >= 32'd1 && cv_idle <= 32'd3)) hits_COVP_007 <= hits_COVP_007 + 1;
// COVP-008: TX acceptance after a long idle gap
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && cv_rdy_q && cv_idle >= 32'd20)) hits_COVP_008 <= hits_COVP_008 + 1;
// COVP-009: TX offer withdrawn while busy
always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_tx_ready && cv_vq && !i_tx_valid)) hits_COVP_009 <= hits_COVP_009 + 1;
// COVP-010: TX offer held through back-pressure then accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && !cv_rdy_q && cv_vq)) hits_COVP_010 <= hits_COVP_010 + 1;
// COVP-011: TX i_tx_data changes during a frame
always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_tx_ready && i_tx_data != cv_dq)) hits_COVP_011 <= hits_COVP_011 + 1;
// COVP-012: TX frame finished, transmitter idle
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_tx_ready && !cv_rdy_q && !i_tx_valid)) hits_COVP_012 <= hits_COVP_012 + 1;
// COVP-013: Reset during a transmit frame
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_rel && cv_mid_tx)) hits_COVP_013 <= hits_COVP_013 + 1;
// COVP-014: Reset during a receive frame
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_rel && cv_mid_rx)) hits_COVP_014 <= hits_COVP_014 + 1;
// COVP-015: Reset while a byte is held
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_rel && cv_mid_hold)) hits_COVP_015 <= hits_COVP_015 + 1;
// COVP-016: TX byte accepted at first edge after release
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_rel && cv_acc)) hits_COVP_016 <= hits_COVP_016 + 1;
// COVP-017: i_rxd low at reset release
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_rel && !i_rxd)) hits_COVP_017 <= hits_COVP_017 + 1;
// COVP-018: RX start bit detected
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_start)) hits_COVP_018 <= hits_COVP_018 + 1;
// COVP-019: Start-bit glitch rejected
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_glitch)) hits_COVP_019 <= hits_COVP_019 + 1;
// COVP-020: Glitch of one low sample
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_glitch && cv_hi1)) hits_COVP_020 <= hits_COVP_020 + 1;
// COVP-021: Glitch of maximum length H low samples
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_glitch && cv_lowok)) hits_COVP_021 <= hits_COVP_021 + 1;
// COVP-022: Start pulse of H+1 low samples accepted
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_busy && cv_rc == (CV_H + 1) && cv_s2 && cv_lowok)) hits_COVP_022 <= hits_COVP_022 + 1;
// COVP-023: New start right after glitch
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_start && cv_glq)) hits_COVP_023 <= hits_COVP_023 + 1;
// COVP-024: Delivery into empty holding register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_deliv && !o_rx_valid)) hits_COVP_024 <= hits_COVP_024 + 1;
// COVP-025: Delivery edge with take at V (no overrun)
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_deliv && o_rx_valid && i_rx_ready)) hits_COVP_025 <= hits_COVP_025 + 1;
// COVP-026: Overrun drop at delivery edge
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_drop)) hits_COVP_026 <= hits_COVP_026 + 1;
// COVP-027: Frame error delivered into empty register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_deliv && !o_rx_valid && !cv_s2)) hits_COVP_027 <= hits_COVP_027 + 1;
// COVP-028: Frame error byte dropped by overrun
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_drop && !cv_s2)) hits_COVP_028 <= hits_COVP_028 + 1;
// COVP-029: Frame error with take at V
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_deliv && o_rx_valid && i_rx_ready && !cv_s2)) hits_COVP_029 <= hits_COVP_029 + 1;
// COVP-030: Back-to-back RX start at M+1
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_start && cv_m1)) hits_COVP_030 <= hits_COVP_030 + 1;
// COVP-031: Loaded byte 0x00 or 0xFF without frame error
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_load_q && o_rx_valid && !o_rx_frame_err && (o_rx_data == 8'h00 || o_rx_data == 8'hFF))) hits_COVP_031 <= hits_COVP_031 + 1;
// COVP-032: Loaded byte 0x55 or 0xAA
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_load_q && o_rx_valid && (o_rx_data == 8'h55 || o_rx_data == 8'hAA))) hits_COVP_032 <= hits_COVP_032 + 1;
// COVP-033: Consumer take outside a delivery edge
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rx_valid && i_rx_ready && !cv_deliv)) hits_COVP_033 <= hits_COVP_033 + 1;
// COVP-034: Held byte stable with i_rx_ready low
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rx_valid && !i_rx_ready && !cv_deliv)) hits_COVP_034 <= hits_COVP_034 + 1;
// COVP-035: i_rx_ready high with empty register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (!o_rx_valid && i_rx_ready && !cv_deliv)) hits_COVP_035 <= hits_COVP_035 + 1;
// COVP-036: Three or more consecutive overrun drops
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_drop && cv_drops >= 8'd2)) hits_COVP_036 <= hits_COVP_036 + 1;
// COVP-037: i_rx_ready toggles while a byte is held
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_rx_valid && (i_rx_ready != cv_rq))) hits_COVP_037 <= hits_COVP_037 + 1;
// COVP-038: Break: line low for 12 bit periods
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_lowc == 12 * CV_N)) hits_COVP_038 <= hits_COVP_038 + 1;
// COVP-039: Delivery while transmitter is busy (full duplex)
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_deliv && !o_tx_ready)) hits_COVP_039 <= hits_COVP_039 + 1;
// COVP-040: TX acceptance while receiver is mid frame (full duplex)
always_ff @(posedge i_clk) if (!(!i_rst_n) && (cv_acc && cv_busy)) hits_COVP_040 <= hits_COVP_040 + 1;

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
    $display("NNC_COVER COVP-040 hits=%0d", hits_COVP_040);
  end
endmodule
