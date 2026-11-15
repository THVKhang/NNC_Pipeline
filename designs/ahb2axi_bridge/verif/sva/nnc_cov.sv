module nnc_cov #(
  parameter int PARA_RD_ID_COUNT = 1,
  parameter int PARA_WR_ID_COUNT = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_ahb_hsel,
  input  logic                        i_ahb_hready,
  input  logic [31:0]                 i_ahb_haddr,
  input  logic [1:0]                  i_ahb_htrans,
  input  logic                        i_ahb_hwrite,
  input  logic [2:0]                  i_ahb_hsize,
  input  logic [2:0]                  i_ahb_hburst,
  input  logic [6:0]                  i_ahb_hprot,
  input  logic                        i_ahb_hnonsec,
  input  logic                        i_ahb_hmastlock,
  input  logic [31:0]                 i_ahb_hwdata,
  input  logic [3:0]                  i_ahb_hwstrb,
  input  logic                        o_ahb_hreadyout,
  input  logic                        o_ahb_hresp,
  input  logic [31:0]                 o_ahb_hrdata,
  input  logic [2:0]                  o_axi_awid,
  input  logic [31:0]                 o_axi_awaddr,
  input  logic [7:0]                  o_axi_awlen,
  input  logic [2:0]                  o_axi_awsize,
  input  logic [1:0]                  o_axi_awburst,
  input  logic                        o_axi_awlock,
  input  logic [3:0]                  o_axi_awcache,
  input  logic [2:0]                  o_axi_awprot,
  input  logic                        o_axi_awvalid,
  input  logic                        i_axi_awready,
  input  logic [31:0]                 o_axi_wdata,
  input  logic [3:0]                  o_axi_wstrb,
  input  logic                        o_axi_wlast,
  input  logic                        o_axi_wvalid,
  input  logic                        i_axi_wready,
  input  logic [2:0]                  i_axi_bid,
  input  logic [1:0]                  i_axi_bresp,
  input  logic                        i_axi_bvalid,
  input  logic                        o_axi_bready,
  input  logic [2:0]                  o_axi_arid,
  input  logic [31:0]                 o_axi_araddr,
  input  logic [7:0]                  o_axi_arlen,
  input  logic [2:0]                  o_axi_arsize,
  input  logic [1:0]                  o_axi_arburst,
  input  logic                        o_axi_arlock,
  input  logic [3:0]                  o_axi_arcache,
  input  logic [2:0]                  o_axi_arprot,
  input  logic                        o_axi_arvalid,
  input  logic                        i_axi_arready,
  input  logic [2:0]                  i_axi_rid,
  input  logic [31:0]                 i_axi_rdata,
  input  logic [1:0]                  i_axi_rresp,
  input  logic                        i_axi_rlast,
  input  logic                        i_axi_rvalid,
  input  logic                        o_axi_rready
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

// helper decode
wire h_acc = i_ahb_hsel && i_ahb_hready && i_ahb_htrans[1];
wire h_misal = ((i_ahb_hsize == 3'd1) && i_ahb_haddr[0]) || ((i_ahb_hsize == 3'd2) && (i_ahb_haddr[1:0] != 2'b00));
wire h_resv = (i_ahb_hprot[5:2] == 4'b0100) || (i_ahb_hprot[5:2] == 4'b0101) || ((i_ahb_hprot[5:2] >= 4'b1000) && (i_ahb_hprot[5:2] <= 4'b1101));
wire h_big = (i_ahb_hsize > 3'd2);
wire h_rej = i_ahb_hmastlock || i_ahb_hprot[6] || h_big || h_misal || h_resv;
wire h_fixed = (i_ahb_hburst >= 3'd2);
wire [4:0] h_beats = ((i_ahb_hburst == 3'd2) || (i_ahb_hburst == 3'd3)) ? 5'd4 :
                     ((i_ahb_hburst == 3'd4) || (i_ahb_hburst == 3'd5)) ? 5'd8 :
                     ((i_ahb_hburst == 3'd6) || (i_ahb_hburst == 3'd7)) ? 5'd16 : 5'd1;
wire h_aw_hs = o_axi_awvalid && i_axi_awready;
wire h_w_hs  = o_axi_wvalid && i_axi_wready;
wire h_ar_hs = o_axi_arvalid && i_axi_arready;
wire [15:0] h_aw_bytes = ({8'b0, o_axi_awlen} + 16'd1) << o_axi_awsize;
wire [15:0] h_aw_end = {4'b0, o_axi_awaddr[11:0]} + h_aw_bytes;

reg h_dp_rd = 1'b0;
reg h_dp_wr = 1'b0;
reg h_dp_rej = 1'b0;
reg [4:0] h_rem = 5'd0;
reg h_last_wr_pfx = 1'b0;
reg h_lk_v = 1'b0;
reg h_lk_w = 1'b0;
reg [6:0] h_prev_hprot = 7'd0;
reg h_prev_nonsec = 1'b0;
reg h_prev_acc = 1'b0;
reg [3:0] h_aw_st = 4'd0;
reg [3:0] h_w_st = 4'd0;
reg [3:0] h_ar_st = 4'd0;
reg h_act_rd_d = 1'b0;
reg h_act_wr_d = 1'b0;
reg h_rst_rd = 1'b0;
reg h_rst_wr = 1'b0;
reg h_rst_prev = 1'b0;

wire h_act_rd = o_axi_arvalid || h_dp_rd;
wire h_act_wr = o_axi_awvalid || o_axi_wvalid || h_dp_wr;

always_ff @(posedge i_clk_core) begin
  h_rst_prev <= i_rst_n_core;
  h_act_rd_d <= h_act_rd;
  h_act_wr_d <= h_act_wr;
  if (!i_rst_n_core) begin
    if (h_rst_prev) begin
      h_rst_rd <= h_act_rd_d;
      h_rst_wr <= h_act_wr_d;
    end
  end else if (h_rst_prev) begin
    h_rst_rd <= 1'b0;
    h_rst_wr <= 1'b0;
  end
end

always_ff @(posedge i_clk_core) begin
  if (!i_rst_n_core) begin
    h_dp_rd <= 1'b0;
    h_dp_wr <= 1'b0;
    h_dp_rej <= 1'b0;
    h_rem <= 5'd0;
    h_last_wr_pfx <= 1'b0;
    h_lk_v <= 1'b0;
    h_lk_w <= 1'b0;
    h_prev_hprot <= 7'd0;
    h_prev_nonsec <= 1'b0;
    h_prev_acc <= 1'b0;
    h_aw_st <= 4'd0;
    h_w_st <= 4'd0;
    h_ar_st <= 4'd0;
  end else begin
    if (i_ahb_hready) begin
      h_dp_rd <= h_acc && !i_ahb_hwrite && !h_rej;
      h_dp_wr <= h_acc && i_ahb_hwrite && !h_rej;
      h_dp_rej <= h_acc && h_rej;
    end
    h_prev_acc <= h_acc;
    if (h_acc) begin
      if (i_ahb_htrans == 2'b10) h_rem <= h_fixed ? (h_beats - 5'd1) : 5'd0;
      else if (h_rem != 5'd0) h_rem <= h_rem - 5'd1;
      h_last_wr_pfx <= i_ahb_hwrite && h_fixed && !h_rej;
      h_prev_hprot <= i_ahb_hprot;
      h_prev_nonsec <= i_ahb_hnonsec;
      if (!h_rej) begin
        h_lk_v <= 1'b1;
        h_lk_w <= i_ahb_hwrite;
      end
    end
    if (o_axi_awvalid && !i_axi_awready) begin
      if (h_aw_st != 4'hF) h_aw_st <= h_aw_st + 4'd1;
    end else h_aw_st <= 4'd0;
    if (o_axi_wvalid && !i_axi_wready) begin
      if (h_w_st != 4'hF) h_w_st <= h_w_st + 4'd1;
    end else h_w_st <= 4'd0;
    if (o_axi_arvalid && !i_axi_arready) begin
      if (h_ar_st != 4'hF) h_ar_st <= h_ar_st + 4'd1;
    end else h_ar_st <= 4'd0;
  end
end

// COVP-001: AHB read completes OKAY with data
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_rd && o_ahb_hreadyout && !o_ahb_hresp && (o_ahb_hrdata != 32'h0))) hits_COVP_001 <= hits_COVP_001 + 1;
// COVP-002: AHB read completes with two-cycle ERROR from RRESP
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_rd && o_ahb_hreadyout && o_ahb_hresp)) hits_COVP_002 <= hits_COVP_002 + 1;
// COVP-003: AHB write completes OKAY
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_wr && o_ahb_hreadyout && !o_ahb_hresp)) hits_COVP_003 <= hits_COVP_003 + 1;
// COVP-004: AHB write completes with ERROR from BRESP
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_wr && o_ahb_hreadyout && o_ahb_hresp)) hits_COVP_004 <= hits_COVP_004 + 1;
// COVP-005: Rejected transfer ERROR second cycle
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_rej && o_ahb_hreadyout && o_ahb_hresp)) hits_COVP_005 <= hits_COVP_005 + 1;
// COVP-006: Rejected transfer ERROR first cycle
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_dp_rej && !o_ahb_hreadyout && o_ahb_hresp)) hits_COVP_006 <= hits_COVP_006 + 1;
// COVP-007: Accepted transfer with HMASTLOCK=1
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && i_ahb_hmastlock)) hits_COVP_007 <= hits_COVP_007 + 1;
// COVP-008: Accepted transfer with HPROT[6]=1
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && i_ahb_hprot[6])) hits_COVP_008 <= hits_COVP_008 + 1;
// COVP-009: Accepted transfer with HSIZE>2 only
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && h_big && !i_ahb_hmastlock && !i_ahb_hprot[6] && !h_resv)) hits_COVP_009 <= hits_COVP_009 + 1;
// COVP-010: Accepted misaligned transfer only
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && h_misal && !i_ahb_hmastlock && !i_ahb_hprot[6] && !h_resv)) hits_COVP_010 <= hits_COVP_010 + 1;
// COVP-011: Accepted reserved HPROT code only
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && h_resv && !i_ahb_hmastlock && !i_ahb_hprot[6] && !h_big && !h_misal)) hits_COVP_011 <= hits_COVP_011 + 1;
// COVP-012: Rejected SEQ beat after captured fixed write prefix
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && h_rej && (i_ahb_htrans == 2'b11) && h_last_wr_pfx)) hits_COVP_012 <= hits_COVP_012 + 1;
// COVP-013: New legal transfer accepted during ERROR second cycle
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && o_ahb_hresp && o_ahb_hreadyout)) hits_COVP_013 <= hits_COVP_013 + 1;
// COVP-014: IDLE transfer selected and ready
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_ahb_hsel && i_ahb_hready && (i_ahb_htrans == 2'b00))) hits_COVP_014 <= hits_COVP_014 + 1;
// COVP-015: BUSY inside a fixed burst
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_ahb_hsel && i_ahb_hready && (i_ahb_htrans == 2'b01) && (h_rem != 5'd0))) hits_COVP_015 <= hits_COVP_015 + 1;
// COVP-016: Fixed burst cut short by a new NONSEQ
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && (i_ahb_htrans == 2'b10) && (h_rem != 5'd0))) hits_COVP_016 <= hits_COVP_016 + 1;
// COVP-017: Fixed burst cut short by IDLE
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_ahb_hsel && i_ahb_hready && (i_ahb_htrans == 2'b00) && (h_rem != 5'd0))) hits_COVP_017 <= hits_COVP_017 + 1;
// COVP-018: Legal byte access at nonzero byte offset
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && (i_ahb_hsize == 3'd0) && (i_ahb_haddr[1:0] != 2'b00))) hits_COVP_018 <= hits_COVP_018 + 1;
// COVP-019: AHB master wait (HREADY low) with active transfer
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_ahb_hsel && !i_ahb_hready && i_ahb_htrans[1])) hits_COVP_019 <= hits_COVP_019 + 1;
// COVP-020: Fixed 4-beat write burst fully accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && (i_ahb_htrans == 2'b11) && (h_rem == 5'd1) && ((i_ahb_hburst == 3'd2) || (i_ahb_hburst == 3'd3)))) hits_COVP_020 <= hits_COVP_020 + 1;
// COVP-021: Fixed 8-beat write burst fully accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && (i_ahb_htrans == 2'b11) && (h_rem == 5'd1) && ((i_ahb_hburst == 3'd4) || (i_ahb_hburst == 3'd5)))) hits_COVP_021 <= hits_COVP_021 + 1;
// COVP-022: Fixed 16-beat write burst fully accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && (i_ahb_htrans == 2'b11) && (h_rem == 5'd1) && ((i_ahb_hburst == 3'd6) || (i_ahb_hburst == 3'd7)))) hits_COVP_022 <= hits_COVP_022 + 1;
// COVP-023: Read/write direction switch in acceptance order
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && h_lk_v && (h_lk_w != i_ahb_hwrite))) hits_COVP_023 <= hits_COVP_023 + 1;
// COVP-024: WRAP burst beat at wrap address boundary
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && (i_ahb_htrans == 2'b11) && (i_ahb_hsize == 3'd2) && (((i_ahb_hburst == 3'd2) && (i_ahb_haddr[3:0] == 4'h0)) || ((i_ahb_hburst == 3'd4) && (i_ahb_haddr[4:0] == 5'h00)) || ((i_ahb_hburst == 3'd6) && (i_ahb_haddr[5:0] == 6'h00))))) hits_COVP_024 <= hits_COVP_024 + 1;
// COVP-025: SINGLE or undefined INCR write accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && (i_ahb_hburst <= 3'd1))) hits_COVP_025 <= hits_COVP_025 + 1;
// COVP-026: Device-E write accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && (i_ahb_hprot[6:2] == 5'b00001))) hits_COVP_026 <= hits_COVP_026 + 1;
// COVP-027: Non-bufferable fixed write burst beat accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && h_fixed && !i_ahb_hprot[2])) hits_COVP_027 <= hits_COVP_027 + 1;
// COVP-028: Bufferable Normal fixed write burst beat accepted
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && h_fixed && (i_ahb_htrans == 2'b11) && i_ahb_hprot[2] && i_ahb_hprot[3])) hits_COVP_028 <= hits_COVP_028 + 1;
// COVP-029: Burst-scoped attributes change mid burst
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && i_ahb_hwrite && h_fixed && (i_ahb_htrans == 2'b11) && ((i_ahb_hprot != h_prev_hprot) || (i_ahb_hnonsec != h_prev_nonsec)))) hits_COVP_029 <= hits_COVP_029 + 1;
// COVP-030: Back-to-back accepted beats
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && h_prev_acc)) hits_COVP_030 <= hits_COVP_030 + 1;
// COVP-031: Legal halfword access at upper half
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_acc && !h_rej && (i_ahb_hsize == 3'd1) && i_ahb_haddr[1])) hits_COVP_031 <= hits_COVP_031 + 1;
// COVP-032: AW stalled 3+ cycles then handshake
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_aw_hs && (h_aw_st >= 4'd3))) hits_COVP_032 <= hits_COVP_032 + 1;
// COVP-033: W stalled 3+ cycles then handshake
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_w_hs && (h_w_st >= 4'd3))) hits_COVP_033 <= hits_COVP_033 + 1;
// COVP-034: AR stalled 3+ cycles then handshake
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_ar_hs && (h_ar_st >= 4'd3))) hits_COVP_034 <= hits_COVP_034 + 1;
// COVP-035: Reset released after reset during write activity
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (!h_rst_prev && h_rst_wr)) hits_COVP_035 <= hits_COVP_035 + 1;
// COVP-036: Reset released after reset during read activity
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (!h_rst_prev && h_rst_rd)) hits_COVP_036 <= hits_COVP_036 + 1;
// COVP-037: AW handshake single-beat (AWLEN=0)
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_aw_hs && (o_axi_awlen == 8'd0))) hits_COVP_037 <= hits_COVP_037 + 1;
// COVP-038: AW handshake maximum burst (AWLEN=15)
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_aw_hs && (o_axi_awlen == 8'd15))) hits_COVP_038 <= hits_COVP_038 + 1;
// COVP-039: AW WRAP burst handshake
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_aw_hs && (o_axi_awburst == 2'b10) && (o_axi_awlen != 8'd0))) hits_COVP_039 <= hits_COVP_039 + 1;
// COVP-040: AW INCR burst ending exactly at 4 KiB boundary
always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_aw_hs && (o_axi_awburst == 2'b01) && (o_axi_awlen != 8'd0) && (h_aw_end == 16'd4096))) hits_COVP_040 <= hits_COVP_040 + 1;

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
