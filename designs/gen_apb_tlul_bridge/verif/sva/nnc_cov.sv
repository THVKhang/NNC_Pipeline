module nnc_cov #(
  parameter int PARA_ADDR_W = 32,
  parameter int PARA_SRC_W = 8,
  parameter int PARA_SRC_ID = 0,
  parameter int PARA_A_USER_W = 1,
  parameter int PARA_D_SINK_W = 1,
  parameter int PARA_D_USER_W = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_ADDR_W)-1:0]    i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [3:0]                  i_apb_pstrb,
  input  logic [31:0]                 i_apb_pwdata,
  input  logic                        o_apb_pready,
  input  logic [31:0]                 o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic                        o_tlul_a_valid,
  input  logic                        i_tlul_a_ready,
  input  logic [2:0]                  o_tlul_a_opcode,
  input  logic [2:0]                  o_tlul_a_param,
  input  logic [1:0]                  o_tlul_a_size,
  input  logic [(PARA_SRC_W)-1:0]     o_tlul_a_source,
  input  logic [(PARA_ADDR_W)-1:0]    o_tlul_a_address,
  input  logic [3:0]                  o_tlul_a_mask,
  input  logic [31:0]                 o_tlul_a_data,
  input  logic [(PARA_A_USER_W)-1:0]  o_tlul_a_user,
  input  logic                        i_tlul_d_valid,
  input  logic                        o_tlul_d_ready,
  input  logic [2:0]                  i_tlul_d_opcode,
  input  logic [(PARA_SRC_W)-1:0]     i_tlul_d_source,
  input  logic [31:0]                 i_tlul_d_data,
  input  logic                        i_tlul_d_error,
  input  logic [2:0]                  i_tlul_d_param,
  input  logic [1:0]                  i_tlul_d_size,
  input  logic [(PARA_D_SINK_W)-1:0]  i_tlul_d_sink,
  input  logic [(PARA_D_USER_W)-1:0]  i_tlul_d_user
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

  // Helper decode
  wire w_setup   = i_apb_psel && !i_apb_penable;
  wire w_illegal = (i_apb_paddr[1:0] != 2'b00) || (i_apb_pwrite && (i_apb_pstrb != 4'b1111));
  wire w_legal   = !w_illegal;
  wire w_acc     = o_tlul_a_valid && i_tlul_a_ready;

  logic       r_pending;
  logic       r_exp_get;
  logic [7:0] r_age;
  logic [7:0] r_acc_cnt;
  logic [7:0] r_bp;
  logic [1:0] r_kind;
  logic       r_pready_d;

  wire w_counted = i_tlul_d_valid && o_tlul_d_ready && (w_acc || r_pending);
  wire w_get     = w_acc ? o_tlul_a_opcode[2] : r_exp_get;
  wire w_orphan  = i_tlul_d_valid && !w_counted;
  wire w_n_pend  = (w_acc && !(i_tlul_d_valid && o_tlul_d_ready)) ||
                   (r_pending && !(i_tlul_d_valid && o_tlul_d_ready));

  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin
    if (!i_rst_n_core) begin
      r_pending  <= 1'b0;
      r_exp_get  <= 1'b0;
      r_age      <= 8'd0;
      r_acc_cnt  <= 8'd0;
      r_bp       <= 8'd0;
      r_kind     <= 2'd0;
      r_pready_d <= 1'b0;
    end else begin
      r_pready_d <= o_apb_pready;
      if (w_acc && !(i_tlul_d_valid && o_tlul_d_ready)) begin
        r_pending <= 1'b1;
        r_exp_get <= o_tlul_a_opcode[2];
      end else if (r_pending && i_tlul_d_valid && o_tlul_d_ready) begin
        r_pending <= 1'b0;
      end
      if (r_pending) begin
        if (r_age != 8'hFF) r_age <= r_age + 8'd1;
      end else r_age <= 8'd0;
      if (i_apb_psel && i_apb_penable && !o_apb_pready) begin
        if (r_acc_cnt != 8'hFF) r_acc_cnt <= r_acc_cnt + 8'd1;
      end else r_acc_cnt <= 8'd0;
      if (o_tlul_a_valid && !i_tlul_a_ready) begin
        if (r_bp != 8'hFF) r_bp <= r_bp + 8'd1;
      end else r_bp <= 8'd0;
      if (w_setup) r_kind <= w_illegal ? 2'd3 : (i_apb_pwrite ? 2'd1 : 2'd2);
    end
  end

  // Reset-history helpers (no async reset: they must see state across reset)
  logic p_rstn  = 1'b0;
  logic p_av    = 1'b0;
  logic p_wt    = 1'b0;
  logic r_ab_av = 1'b0;
  logic r_ab_wt = 1'b0;
  logic r_ab_set = 1'b0;

  always_ff @(posedge i_clk_core) begin
    p_rstn <= i_rst_n_core;
    p_av   <= o_tlul_a_valid;
    p_wt   <= i_rst_n_core && w_n_pend;
    if (!i_rst_n_core) begin
      if (p_av) r_ab_av <= 1'b1;
      if (p_wt) r_ab_wt <= 1'b1;
      r_ab_set <= 1'b0;
    end else begin
      if (w_setup && (r_ab_av || r_ab_wt)) r_ab_set <= 1'b1;
      if (o_apb_pready && r_ab_set) begin
        r_ab_av  <= 1'b0;
        r_ab_wt  <= 1'b0;
        r_ab_set <= 1'b0;
      end
    end
  end

  // COVP-001: Legal full-strobe write Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && w_legal && i_apb_pwrite)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: Legal read Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && w_legal && !i_apb_pwrite)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: Misaligned read Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && !i_apb_pwrite && i_apb_paddr[1:0] != 2'b00)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: Misaligned write with full strobe Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && i_apb_pwrite && i_apb_pstrb == 4'b1111 && i_apb_paddr[1:0] != 2'b00)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Aligned write with PSTRB zero Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && i_apb_pwrite && i_apb_paddr[1:0] == 2'b00 && i_apb_pstrb == 4'b0000)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Aligned write with partial PSTRB Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && i_apb_pwrite && i_apb_paddr[1:0] == 2'b00 && i_apb_pstrb != 4'b0000 && i_apb_pstrb != 4'b1111)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Aligned read with PSTRB not full (ignored)
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && !i_apb_pwrite && i_apb_paddr[1:0] == 2'b00 && i_apb_pstrb != 4'b1111)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: Legal Setup at highest word address
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && w_legal && (&i_apb_paddr[PARA_ADDR_W-1:2]))) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: Write completes in 3 Access cycles with PRDATA 0
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && i_apb_pwrite && !o_apb_pslverr && r_acc_cnt == 8'd2 && o_apb_prdata == 32'h0)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: Read completes in 3 Access cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && !i_apb_pwrite && !o_apb_pslverr && r_acc_cnt == 8'd2)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: Write with same-cycle response, 2 Access cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && i_apb_pwrite && !o_apb_pslverr && r_acc_cnt == 8'd1)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: Read with same-cycle response, 2 Access cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && !i_apb_pwrite && !o_apb_pslverr && r_acc_cnt == 8'd1)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: Local error completion in 1 Access cycle
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && o_apb_pslverr && r_acc_cnt == 8'd0 && o_apb_prdata == 32'h0)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: Channel A back-pressure
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_tlul_a_valid && !i_tlul_a_ready)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: Channel A accepted after 3 or more stall cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_acc && r_bp >= 8'd3)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Response in acceptance cycle after back-pressure
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_acc && r_bp >= 8'd1 && i_tlul_d_valid)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Response delayed 1 to 3 cycles after acceptance
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && r_pending && r_age >= 8'd1 && r_age <= 8'd3)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Response delayed 8 or more cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && r_pending && r_age >= 8'd8)) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Write response with d_error
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && !w_get && i_tlul_d_error && i_tlul_d_opcode == 3'b000 && i_tlul_d_source == PARA_SRC_ID)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: Read response with d_error
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && w_get && i_tlul_d_error && i_tlul_d_opcode == 3'b001 && i_tlul_d_source == PARA_SRC_ID)) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: Write answered with AccessAckData
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && !w_get && i_tlul_d_opcode == 3'b001)) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: Read answered with AccessAck
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && w_get && i_tlul_d_opcode == 3'b000)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: Undefined d_opcode on a counted response
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && (|i_tlul_d_opcode[2:1]))) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: Wrong d_source on a counted response
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && i_tlul_d_source != PARA_SRC_ID)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: Orphan response while APB idle
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_orphan && !i_apb_psel)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: Orphan response during Setup or blocked channel A
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_orphan && (w_setup || (o_tlul_a_valid && !i_tlul_a_ready)))) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: Orphan response in the PREADY cycle
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_orphan && o_apb_pready)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: No response for 16 or more Access cycles
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_apb_psel && i_apb_penable && !o_apb_pready && r_acc_cnt >= 8'd16)) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: Ignored response fields non-default
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted && ((|i_tlul_d_param) || (i_tlul_d_size != 2'b10) || (|i_tlul_d_sink) || (|i_tlul_d_user)))) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: Non-zero PPROT on a legal Setup
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && w_legal && (|i_apb_pprot))) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: Back-to-back write then read, PSEL held
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_legal && !i_apb_pwrite && r_kind == 2'd1)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: Back-to-back read then write, PSEL held
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_legal && i_apb_pwrite && r_kind == 2'd2)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: Back-to-back legal then illegal
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_illegal && (r_kind == 2'd1 || r_kind == 2'd2))) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: Back-to-back illegal then legal
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_legal && r_kind == 2'd3)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: Back-to-back illegal then illegal
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_illegal && r_kind == 2'd3)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: Recovery after reset during pending a_valid
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && r_ab_av && r_ab_set)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: Recovery after reset while waiting for response
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && r_ab_wt && r_ab_set)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: Setup at first edge after reset release
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_setup && !p_rstn)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: d_valid at first edge after reset release
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_tlul_d_valid && !p_rstn)) hits_COVP_039 <= hits_COVP_039 + 1;
  // COVP-040: Back-to-back write then write, PSEL held
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_pready_d && w_setup && w_legal && i_apb_pwrite && r_kind == 2'd1)) hits_COVP_040 <= hits_COVP_040 + 1;

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
