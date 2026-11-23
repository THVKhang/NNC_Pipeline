module nnc_cov #(
  parameter int DATA_WIDTH = 8
) (
  input  logic                        clk,
  input  logic                        rst,
  input  logic [7:0]                  s_axis_tdata,
  input  logic                        s_axis_tvalid,
  input  logic                        s_axis_tready,
  input  logic [7:0]                  m_axis_tdata,
  input  logic                        m_axis_tvalid,
  input  logic                        m_axis_tready,
  input  logic                        rxd,
  input  logic                        txd,
  input  logic                        tx_busy,
  input  logic                        rx_busy,
  input  logic                        rx_overrun_error,
  input  logic                        rx_frame_error,
  input  logic [15:0]                 prescale
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

  // helper state
  logic p_mvalid = 1'b0;
  logic p_mready = 1'b0;
  logic [7:0] p_mdata = 8'd0;
  logic p_ovr = 1'b0;
  logic p_fe = 1'b0;
  logic p_txd = 1'b1;
  logic p_txb = 1'b0;
  logic p_rxb = 1'b0;
  logic p_rxd = 1'b1;
  logic p_rst = 1'b1;
  logic ov_seen = 1'b0;
  logic fe_seen = 1'b0;
  logic last_tx = 1'b0;
  logic last_rx = 1'b0;
  logic last_mv = 1'b0;
  int unsigned mstall = 0;
  int unsigned sstall = 0;

  always_ff @(posedge clk) begin
    p_rst <= rst;
    if (rst) begin
      p_mvalid <= 1'b0;
      p_mready <= 1'b0;
      p_mdata <= 8'd0;
      p_ovr <= 1'b0;
      p_fe <= 1'b0;
      p_txd <= 1'b1;
      p_txb <= 1'b0;
      p_rxb <= 1'b0;
      p_rxd <= 1'b1;
      ov_seen <= 1'b0;
      fe_seen <= 1'b0;
      mstall <= 0;
      sstall <= 0;
    end else begin
      p_mvalid <= m_axis_tvalid;
      p_mready <= m_axis_tready;
      p_mdata <= m_axis_tdata[7:0];
      p_ovr <= rx_overrun_error;
      p_fe <= rx_frame_error;
      p_txd <= txd;
      p_txb <= tx_busy;
      p_rxb <= rx_busy;
      p_rxd <= rxd;
      last_tx <= tx_busy;
      last_rx <= rx_busy;
      last_mv <= m_axis_tvalid;
      if (rx_overrun_error) ov_seen <= 1'b1;
      else if (m_axis_tvalid && m_axis_tready) ov_seen <= 1'b0;
      if (rx_frame_error) fe_seen <= 1'b1;
      else if (m_axis_tvalid && !p_mvalid) fe_seen <= 1'b0;
      if (m_axis_tvalid && !m_axis_tready) begin
        if (mstall < 1000) mstall <= mstall + 1;
      end else mstall <= 0;
      if (s_axis_tvalid && !s_axis_tready) begin
        if (sstall < 1000) sstall <= sstall + 1;
      end else sstall <= 0;
    end
  end

  // COVP-001: s_axis handshake
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && s_axis_tready)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: s_axis stall: tvalid high, tready low
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && !s_axis_tready)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: s_axis stall lasting 4+ cycles
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && !s_axis_tready && sstall >= 3)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: s_axis tvalid offered while transmitter busy
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && tx_busy)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: s_axis handshake data all zeros
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && s_axis_tready && s_axis_tdata == '0)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: s_axis handshake data all ones
  always_ff @(posedge clk) if (!(rst) && (s_axis_tvalid && s_axis_tready && s_axis_tdata == '1)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: m_axis handshake
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && m_axis_tready)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: m_axis back-pressure: valid high, ready low
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && !m_axis_tready)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: m_axis stall lasting 4+ cycles
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && !m_axis_tready && mstall >= 3)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: m_axis held stable across a stall cycle
  always_ff @(posedge clk) if (!(rst) && (p_mvalid && !p_mready && m_axis_tvalid && m_axis_tdata[7:0] == p_mdata)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: m_axis transfer after stall released
  always_ff @(posedge clk) if (!(rst) && (p_mvalid && !p_mready && m_axis_tvalid && m_axis_tready)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: m_axis ready high while no valid
  always_ff @(posedge clk) if (!(rst) && (m_axis_tready && !m_axis_tvalid)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: m_axis handshake data all zeros
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && m_axis_tready && m_axis_tdata == '0)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: m_axis handshake data all ones
  always_ff @(posedge clk) if (!(rst) && (m_axis_tvalid && m_axis_tready && m_axis_tdata == '1)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: rx overrun pulse
  always_ff @(posedge clk) if (!(rst) && (rx_overrun_error)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: overrun pulse while pending word held
  always_ff @(posedge clk) if (!(rst) && (rx_overrun_error && m_axis_tvalid && !m_axis_tready)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: overrun pulse ends after one cycle
  always_ff @(posedge clk) if (!(rst) && (p_ovr && !rx_overrun_error)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: rx frame error pulse
  always_ff @(posedge clk) if (!(rst) && (rx_frame_error)) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: frame error pulse ends after one cycle
  always_ff @(posedge clk) if (!(rst) && (p_fe && !rx_frame_error)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: frame error while m_axis idle
  always_ff @(posedge clk) if (!(rst) && (rx_frame_error && !m_axis_tvalid)) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: good reception after an overrun (recovery)
  always_ff @(posedge clk) if (!(rst) && (ov_seen && m_axis_tvalid && m_axis_tready)) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: good reception after a frame error (recovery)
  always_ff @(posedge clk) if (!(rst) && (fe_seen && m_axis_tvalid && !p_mvalid)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: tx_busy rises
  always_ff @(posedge clk) if (!(rst) && (tx_busy && !p_txb)) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: tx_busy falls
  always_ff @(posedge clk) if (!(rst) && (!tx_busy && p_txb)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: txd low while tx_busy
  always_ff @(posedge clk) if (!(rst) && (!txd && tx_busy)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: txd high while tx_busy
  always_ff @(posedge clk) if (!(rst) && (txd && tx_busy)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: idle: tx_busy low with txd high
  always_ff @(posedge clk) if (!(rst) && (!tx_busy && txd)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: rx_busy rises
  always_ff @(posedge clk) if (!(rst) && (rx_busy && !p_rxb)) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: rx_busy falls
  always_ff @(posedge clk) if (!(rst) && (!rx_busy && p_rxb)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: start bit seen on rxd while idle
  always_ff @(posedge clk) if (!(rst) && (p_rxd && !rxd && !rx_busy)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: full duplex: tx_busy and rx_busy together
  always_ff @(posedge clk) if (!(rst) && (tx_busy && rx_busy)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: tx start with minimum prescale (1)
  always_ff @(posedge clk) if (!(rst) && (p_txd && !txd && prescale == 16'd1)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: tx start with small prescale (2..7)
  always_ff @(posedge clk) if (!(rst) && (p_txd && !txd && prescale >= 16'd2 && prescale <= 16'd7)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: tx start with typical prescale (8..255)
  always_ff @(posedge clk) if (!(rst) && (p_txd && !txd && prescale >= 16'd8 && prescale <= 16'd255)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: tx start with large prescale (256+)
  always_ff @(posedge clk) if (!(rst) && (p_txd && !txd && prescale >= 16'd256)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: rx start with small prescale (<8)
  always_ff @(posedge clk) if (!(rst) && (p_rxd && !rxd && !rx_busy && prescale >= 16'd1 && prescale <= 16'd7)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: rx start with larger prescale (>=8)
  always_ff @(posedge clk) if (!(rst) && (p_rxd && !rxd && !rx_busy && prescale >= 16'd8)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: reset released after tx activity
  always_ff @(posedge clk) if (!(rst) && (p_rst && last_tx)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: reset released after rx activity
  always_ff @(posedge clk) if (!(rst) && (p_rst && last_rx)) hits_COVP_039 <= hits_COVP_039 + 1;
  // COVP-040: reset released after pending m_axis word
  always_ff @(posedge clk) if (!(rst) && (p_rst && last_mv)) hits_COVP_040 <= hits_COVP_040 + 1;

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
