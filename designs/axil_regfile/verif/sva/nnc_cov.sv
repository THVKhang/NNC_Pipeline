module nnc_cov #(
  parameter int PARA_NUM_REGS = 8,
  parameter int PARA_ADDR_W = 8,
  localparam int LPARA_REGS_W = PARA_NUM_REGS*32
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_s_axi_awvalid,
  input  logic                        o_s_axi_awready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_awaddr,
  input  logic [2:0]                  i_s_axi_awprot,
  input  logic                        i_s_axi_wvalid,
  input  logic                        o_s_axi_wready,
  input  logic [31:0]                 i_s_axi_wdata,
  input  logic [3:0]                  i_s_axi_wstrb,
  input  logic                        o_s_axi_bvalid,
  input  logic                        i_s_axi_bready,
  input  logic [1:0]                  o_s_axi_bresp,
  input  logic                        i_s_axi_arvalid,
  input  logic                        o_s_axi_arready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_araddr,
  input  logic [2:0]                  i_s_axi_arprot,
  input  logic                        o_s_axi_rvalid,
  input  logic                        i_s_axi_rready,
  input  logic [31:0]                 o_s_axi_rdata,
  input  logic [1:0]                  o_s_axi_rresp,
  input  logic [(LPARA_REGS_W)-1:0]   o_regs,
  input  logic [31:0]                 i_status
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

// helpers
wire aw_x = i_s_axi_awvalid & o_s_axi_awready & i_rst_n;
wire w_x  = i_s_axi_wvalid  & o_s_axi_wready  & i_rst_n;
wire ar_x = i_s_axi_arvalid & o_s_axi_arready & i_rst_n;
wire b_x  = o_s_axi_bvalid  & i_s_axi_bready  & i_rst_n;
wire r_x  = o_s_axi_rvalid  & i_s_axi_rready  & i_rst_n;

wire [PARA_ADDR_W-3:0] aw_w = i_s_axi_awaddr[PARA_ADDR_W-1:2];
wire [PARA_ADDR_W-3:0] ar_w = i_s_axi_araddr[PARA_ADDR_W-1:2];
wire aw_reg = (int'(aw_w) < int'(PARA_NUM_REGS));
wire aw_st  = (int'(aw_w) == 16);
wire aw_blw = !aw_reg && (int'(aw_w) < 16);
wire aw_hi  = (int'(aw_w) >= 32);
wire aw_abv = (int'(aw_w) > 16) && !aw_hi;
wire ar_reg = (int'(ar_w) < int'(PARA_NUM_REGS));
wire ar_st  = (int'(ar_w) == 16);
wire ar_blw = !ar_reg && (int'(ar_w) < 16);
wire ar_hi  = (int'(ar_w) >= 32);
wire ar_abv = (int'(ar_w) > 16) && !ar_hi;

logic aw_h = 1'b0, w_h = 1'b0, b_pend = 1'b0, r_pend = 1'b0;
logic q_wreg = 1'b0, q_wst = 1'b0, q_wblw = 1'b0, q_wabv = 1'b0, q_whi = 1'b0;
logic q_rreg = 1'b0, q_rst = 1'b0, q_rblw = 1'b0, q_rabv = 1'b0, q_rhi = 1'b0;
logic [PARA_ADDR_W-3:0] q_ww = '0;
logic [PARA_ADDR_W-3:0] q_rw = '0;
logic [3:0] q_strb = 4'h0;
logic [2:0] bp_b = 3'd0, bp_r = 3'd0, gap_aw = 3'd0;
logic b_x_q = 1'b0, r_x_q = 1'b0, ar_x_q = 1'b0;
logic ec_q = 1'b0;
logic [PARA_ADDR_W-3:0] ec_wq = '0;

wire ec = (aw_x & (w_x | w_h)) | (w_x & aw_h);
wire ec_reg = ec & (aw_x ? aw_reg : q_wreg);
wire [PARA_ADDR_W-3:0] ec_w = aw_x ? aw_w : q_ww;
wire [3:0] ec_strb = w_x ? i_s_axi_wstrb : q_strb;

wire aw_h_n = aw_x | (aw_h & ~b_x);
wire w_h_n  = w_x  | (w_h & ~b_x);
wire b_pend_n = ec | (b_pend & ~b_x);
wire r_pend_n = ar_x | (r_pend & ~r_x);

always_ff @(posedge i_clk or negedge i_rst_n) begin
  if (!i_rst_n) begin
    aw_h <= 1'b0; w_h <= 1'b0; b_pend <= 1'b0; r_pend <= 1'b0;
    q_wreg <= 1'b0; q_wst <= 1'b0; q_wblw <= 1'b0; q_wabv <= 1'b0; q_whi <= 1'b0;
    q_rreg <= 1'b0; q_rst <= 1'b0; q_rblw <= 1'b0; q_rabv <= 1'b0; q_rhi <= 1'b0;
    q_ww <= '0; q_rw <= '0; q_strb <= 4'h0;
    bp_b <= 3'd0; bp_r <= 3'd0; gap_aw <= 3'd0;
    b_x_q <= 1'b0; r_x_q <= 1'b0; ar_x_q <= 1'b0;
    ec_q <= 1'b0; ec_wq <= '0;
  end else begin
    aw_h <= aw_h_n; w_h <= w_h_n; b_pend <= b_pend_n; r_pend <= r_pend_n;
    if (aw_x) begin
      q_wreg <= aw_reg; q_wst <= aw_st; q_wblw <= aw_blw; q_wabv <= aw_abv; q_whi <= aw_hi;
      q_ww <= aw_w;
    end
    if (ar_x) begin
      q_rreg <= ar_reg; q_rst <= ar_st; q_rblw <= ar_blw; q_rabv <= ar_abv; q_rhi <= ar_hi;
      q_rw <= ar_w;
    end
    if (w_x) q_strb <= i_s_axi_wstrb;
    if (o_s_axi_bvalid && !i_s_axi_bready) bp_b <= (bp_b == 3'd7) ? bp_b : bp_b + 3'd1; else bp_b <= 3'd0;
    if (o_s_axi_rvalid && !i_s_axi_rready) bp_r <= (bp_r == 3'd7) ? bp_r : bp_r + 3'd1; else bp_r <= 3'd0;
    if (aw_h && !w_h) gap_aw <= (gap_aw == 3'd7) ? gap_aw : gap_aw + 3'd1; else gap_aw <= 3'd0;
    b_x_q <= b_x; r_x_q <= r_x; ar_x_q <= ar_x;
    ec_q <= ec_reg; ec_wq <= ec_w;
  end
end

// reset history helpers (not cleared by reset)
logic rst_was = 1'b0;
always_ff @(posedge i_clk or negedge i_rst_n) begin
  if (!i_rst_n) rst_was <= 1'b1; else rst_was <= 1'b0;
end
wire r1 = rst_was & i_rst_n;
logic snap_aw = 1'b0, snap_w = 1'b0, snap_b = 1'b0, snap_r = 1'b0;
logic r1_q = 1'b0, v_aw_r1 = 1'b0, v_w_r1 = 1'b0, v_ar_r1 = 1'b0;
logic [31:0] st_prev = 32'h0;
always_ff @(posedge i_clk) begin
  if (i_rst_n && !rst_was) begin
    snap_aw <= aw_h_n; snap_w <= w_h_n; snap_b <= b_pend_n; snap_r <= r_pend_n;
  end
  r1_q <= r1;
  v_aw_r1 <= r1 & i_s_axi_awvalid;
  v_w_r1  <= r1 & i_s_axi_wvalid;
  v_ar_r1 <= r1 & i_s_axi_arvalid;
  st_prev <= i_status;
end

// COVP-001: Write to read/write register answers OKAY
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && o_s_axi_bresp == 2'b00 && q_wreg)) hits_COVP_001 <= hits_COVP_001 + 1;
// COVP-002: Write to status register answers OKAY
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && o_s_axi_bresp == 2'b00 && q_wst)) hits_COVP_002 <= hits_COVP_002 + 1;
// COVP-003: Write to unmapped gap below status answers SLVERR
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && o_s_axi_bresp == 2'b10 && q_wblw)) hits_COVP_003 <= hits_COVP_003 + 1;
// COVP-004: Write to unmapped region above status answers SLVERR
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && o_s_axi_bresp == 2'b10 && q_wabv)) hits_COVP_004 <= hits_COVP_004 + 1;
// COVP-005: Write with high address bit set answers SLVERR
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && o_s_axi_bresp == 2'b10 && q_whi)) hits_COVP_005 <= hits_COVP_005 + 1;
// COVP-006: Read of read/write register answers OKAY
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && o_s_axi_rresp == 2'b00 && q_rreg)) hits_COVP_006 <= hits_COVP_006 + 1;
// COVP-007: Read of status register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && o_s_axi_rresp == 2'b00 && q_rst)) hits_COVP_007 <= hits_COVP_007 + 1;
// COVP-008: Read of unmapped gap below status
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && o_s_axi_rresp == 2'b10 && o_s_axi_rdata == 32'h0 && q_rblw)) hits_COVP_008 <= hits_COVP_008 + 1;
// COVP-009: Read of unmapped region above status
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && o_s_axi_rresp == 2'b10 && o_s_axi_rdata == 32'h0 && q_rabv)) hits_COVP_009 <= hits_COVP_009 + 1;
// COVP-010: Read with high address bit set
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && o_s_axi_rresp == 2'b10 && o_s_axi_rdata == 32'h0 && q_rhi)) hits_COVP_010 <= hits_COVP_010 + 1;
// COVP-011: Write with all strobes set to a register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ec_reg && ec_strb == 4'b1111)) hits_COVP_011 <= hits_COVP_011 + 1;
// COVP-012: Write with partial strobes to a register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ec_reg && ec_strb != 4'b0000 && ec_strb != 4'b1111)) hits_COVP_012 <= hits_COVP_012 + 1;
// COVP-013: Write with zero strobes to a register
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ec_reg && ec_strb == 4'b0000)) hits_COVP_013 <= hits_COVP_013 + 1;
// COVP-014: Write address before write data
always_ff @(posedge i_clk) if (!(!i_rst_n) && (w_x && aw_h)) hits_COVP_014 <= hits_COVP_014 + 1;
// COVP-015: Write data before write address
always_ff @(posedge i_clk) if (!(!i_rst_n) && (aw_x && w_h)) hits_COVP_015 <= hits_COVP_015 + 1;
// COVP-016: AW and W at the same edge
always_ff @(posedge i_clk) if (!(!i_rst_n) && (aw_x && w_x && !aw_h && !w_h)) hits_COVP_016 <= hits_COVP_016 + 1;
// COVP-017: Long gap: write address held 4 or more edges before data
always_ff @(posedge i_clk) if (!(!i_rst_n) && (w_x && aw_h && gap_aw >= 3'd3)) hits_COVP_017 <= hits_COVP_017 + 1;
// COVP-018: B transfer without back-pressure
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && bp_b == 3'd0)) hits_COVP_018 <= hits_COVP_018 + 1;
// COVP-019: B back-pressure of at least 1 cycle
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && bp_b >= 3'd1)) hits_COVP_019 <= hits_COVP_019 + 1;
// COVP-020: B back-pressure of 4 or more cycles
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x && bp_b >= 3'd4)) hits_COVP_020 <= hits_COVP_020 + 1;
// COVP-021: R transfer without back-pressure
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && bp_r == 3'd0)) hits_COVP_021 <= hits_COVP_021 + 1;
// COVP-022: R back-pressure of at least 1 cycle
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && bp_r >= 3'd1)) hits_COVP_022 <= hits_COVP_022 + 1;
// COVP-023: R back-pressure of 4 or more cycles
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x && bp_r >= 3'd4)) hits_COVP_023 <= hits_COVP_023 + 1;
// COVP-024: New AW or W valid presented during stalled B
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_bvalid && !i_s_axi_bready && (i_s_axi_awvalid || i_s_axi_wvalid))) hits_COVP_024 <= hits_COVP_024 + 1;
// COVP-025: New AR valid presented during stalled R
always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_rvalid && !i_s_axi_rready && i_s_axi_arvalid)) hits_COVP_025 <= hits_COVP_025 + 1;
// COVP-026: Back-to-back writes every 2 cycles
always_ff @(posedge i_clk) if (!(!i_rst_n) && (b_x_q && aw_x && w_x)) hits_COVP_026 <= hits_COVP_026 + 1;
// COVP-027: Back-to-back reads every 2 cycles
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r_x_q && ar_x)) hits_COVP_027 <= hits_COVP_027 + 1;
// COVP-028: Read and write of same register with Ear = Ec
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ar_x && ec_reg && ar_reg && ec_w == ar_w)) hits_COVP_028 <= hits_COVP_028 + 1;
// COVP-029: Read and write of same register with Ear = Ec-1
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ar_x_q && q_rreg && ec_reg && ec_w == q_rw)) hits_COVP_029 <= hits_COVP_029 + 1;
// COVP-030: Read and write of same register with Ear = Ec+1
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ec_q && ar_x && ar_reg && ec_wq == ar_w)) hits_COVP_030 <= hits_COVP_030 + 1;
// COVP-031: Status read while i_status changes
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ar_x && ar_st && i_status != st_prev)) hits_COVP_031 <= hits_COVP_031 + 1;
// COVP-032: Reset with only write address held
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1 && snap_aw && !snap_w)) hits_COVP_032 <= hits_COVP_032 + 1;
// COVP-033: Reset with only write data held
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1 && snap_w && !snap_aw)) hits_COVP_033 <= hits_COVP_033 + 1;
// COVP-034: Reset with B response pending
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1 && snap_b)) hits_COVP_034 <= hits_COVP_034 + 1;
// COVP-035: Reset with R response pending
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1 && snap_r)) hits_COVP_035 <= hits_COVP_035 + 1;
// COVP-036: Write valid held through reset taken as new request
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1_q && ((v_aw_r1 && aw_x) || (v_w_r1 && w_x)))) hits_COVP_036 <= hits_COVP_036 + 1;
// COVP-037: Read valid held through reset taken as new request
always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1_q && v_ar_r1 && ar_x)) hits_COVP_037 <= hits_COVP_037 + 1;
// COVP-038: Unaligned address bits [1:0] on AW or AR
always_ff @(posedge i_clk) if (!(!i_rst_n) && ((aw_x && i_s_axi_awaddr[1:0] != 2'b00) || (ar_x && i_s_axi_araddr[1:0] != 2'b00))) hits_COVP_038 <= hits_COVP_038 + 1;
// COVP-039: Non-zero AxPROT on AW or AR
always_ff @(posedge i_clk) if (!(!i_rst_n) && ((aw_x && i_s_axi_awprot != 3'b000) || (ar_x && i_s_axi_arprot != 3'b000))) hits_COVP_039 <= hits_COVP_039 + 1;
// COVP-040: Register write completes while R is stalled
always_ff @(posedge i_clk) if (!(!i_rst_n) && (ec_reg && o_s_axi_rvalid && !i_s_axi_rready)) hits_COVP_040 <= hits_COVP_040 + 1;

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
