module nnc_cov (
  input  logic                        clk_i,
  input  logic                        rst_ni,
  input  logic                        i_a_valid,
  input  logic                        o_a_ready,
  input  logic [2:0]                  i_a_opcode,
  input  logic [2:0]                  i_a_param,
  input  logic [1:0]                  i_a_size,
  input  logic [7:0]                  i_a_source,
  input  logic [31:0]                 i_a_address,
  input  logic [3:0]                  i_a_mask,
  input  logic [31:0]                 i_a_data,
  input  logic                        i_a_instr,
  input  logic                        i_a_intg_flip,
  input  logic                        o_d_valid,
  input  logic                        i_d_ready,
  input  logic [2:0]                  o_d_opcode,
  input  logic [2:0]                  o_d_param,
  input  logic [1:0]                  o_d_size,
  input  logic [7:0]                  o_d_source,
  input  logic                        o_d_sink,
  input  logic [31:0]                 o_d_data,
  input  logic                        o_d_error,
  input  logic                        o_d_intg_err,
  input  logic                        o_alert,
  input  logic                        o_alert_integ_fail,
  input  logic                        o_intr_timer_expired
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

  wire a_fire = i_a_valid & o_a_ready;
  wire d_fire = o_d_valid & i_d_ready;
  wire a_wr = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);
  wire a_full = (i_a_size == 2'd2) && (i_a_mask == 4'hF) && (i_a_address[1:0] == 2'b00);
  wire a_mapped = (i_a_address[31:3] == 29'd0) || (i_a_address[31:5] == 27'd8);
  wire a_clean = !i_a_intg_flip && !i_a_instr;

  logic [2:0] q_op   [0:255];
  logic [1:0] q_size [0:255];
  logic [8:0] q_addr [0:255];
  logic       q_flip [0:255];
  logic       q_instr[0:255];

  wire [2:0] m_op    = q_op[o_d_source];
  wire [1:0] m_size  = q_size[o_d_source];
  wire [8:0] m_addr  = q_addr[o_d_source];
  wire       m_flip  = q_flip[o_d_source];
  wire       m_instr = q_instr[o_d_source];
  wire       m_clean = !m_flip && !m_instr;

  int unsigned out_cnt = 0;
  logic [7:0] a_stall_cnt = 8'd0;
  logic [7:0] d_stall_cnt = 8'd0;
  logic flip_seen = 1'b0;
  logic [7:0] alert_cnt = 8'd0;
  logic regwen_cleared = 1'b0;
  logic ctrl_active = 1'b0;
  logic prev_intr = 1'b0;

  logic rst_prev = 1'b0;
  logic act_before = 1'b0;
  logic [7:0] low_len = 8'd0;

  always_ff @(posedge clk_i) begin
    rst_prev <= rst_ni;
    if (!rst_ni) begin
      if (low_len != 8'd255) low_len <= low_len + 8'd1;
    end else begin
      low_len <= 8'd0;
      act_before <= (out_cnt != 0) || o_d_valid || ctrl_active;
    end
  end

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      out_cnt <= 0;
      a_stall_cnt <= 8'd0;
      d_stall_cnt <= 8'd0;
      flip_seen <= 1'b0;
      alert_cnt <= 8'd0;
      regwen_cleared <= 1'b0;
      ctrl_active <= 1'b0;
      prev_intr <= 1'b0;
    end else begin
      out_cnt <= out_cnt + {31'd0, a_fire} - {31'd0, d_fire};
      if (i_a_valid && !o_a_ready) begin
        if (a_stall_cnt != 8'd255) a_stall_cnt <= a_stall_cnt + 8'd1;
      end else a_stall_cnt <= 8'd0;
      if (o_d_valid && !i_d_ready) begin
        if (d_stall_cnt != 8'd255) d_stall_cnt <= d_stall_cnt + 8'd1;
      end else d_stall_cnt <= 8'd0;
      if (a_fire && i_a_intg_flip) flip_seen <= 1'b1;
      if (flip_seen && o_alert && alert_cnt != 8'd255) alert_cnt <= alert_cnt + 8'd1;
      if (a_fire && !i_a_intg_flip && a_wr && i_a_address == 32'h0 && a_full && !i_a_data[31])
        regwen_cleared <= 1'b1;
      if (a_fire && !i_a_intg_flip && a_wr && i_a_address == 32'h4 && i_a_mask[0])
        ctrl_active <= i_a_data[0];
      prev_intr <= o_intr_timer_expired;
    end
  end

  always_ff @(posedge clk_i) begin
    if (a_fire) begin
      q_op[i_a_source]    <= i_a_opcode;
      q_size[i_a_source]  <= i_a_size;
      q_addr[i_a_source]  <= i_a_address[8:0];
      q_flip[i_a_source]  <= i_a_intg_flip;
      q_instr[i_a_source] <= i_a_instr;
    end
  end

  // COVP-001: Get answered with AccessAckData, no error
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_fire && m_op == 3'd4 && m_clean && o_d_opcode == 3'd1 && !o_d_error)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: PutFullData acknowledged with AccessAck
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_fire && m_op == 3'd0 && m_size == 2'd2 && m_clean && o_d_opcode == 3'd0 && !o_d_error)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: PutPartialData full-word write succeeds
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_fire && m_op == 3'd1 && m_size == 2'd2 && m_clean && o_d_opcode == 3'd0 && !o_d_error)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: Byte write to 1-bit register INTR_ENABLE0
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd1 && i_a_size == 2'd0 && i_a_mask == 4'b0001 && i_a_address == 32'h100)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Byte write to wide register returns error
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_fire && m_op == 3'd1 && m_size == 2'd0 && m_clean && m_addr[1:0] == 2'b00 && m_addr[8:2] >= 7'h44 && m_addr[8:2] <= 7'h47 && o_d_error)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Get to unmapped offset accepted
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd2 && i_a_address[1:0] == 2'b00 && i_a_address >= 32'h120 && i_a_address < 32'h200)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Write to unmapped offset accepted
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address >= 32'h120 && i_a_address < 32'h200)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: Unmapped access answered with d_error
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_fire && m_clean && m_size == 2'd2 && m_addr[1:0] == 2'b00 && m_addr >= 9'h120 && o_d_error)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: Illegal opcode request
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && !i_a_intg_flip && i_a_opcode != 3'd0 && i_a_opcode != 3'd1 && i_a_opcode != 3'd4)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: Illegal size 3 request
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && !i_a_intg_flip && i_a_size == 2'd3)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: Misaligned address request
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && !i_a_intg_flip && ((i_a_size == 2'd1 && i_a_address[0]) || (i_a_size == 2'd2 && i_a_address[1:0] != 2'b00)))) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: PutFullData with incomplete mask
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && !i_a_intg_flip && i_a_opcode == 3'd0 && i_a_size == 2'd2 && i_a_mask != 4'hF)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: Byte read at lane 0 of a mapped register
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd0 && i_a_address[1:0] == 2'd0 && a_mapped)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: Byte read at lane 3 of a mapped register
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd0 && i_a_address[1:0] == 2'd3 && a_mapped)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: Half-word read of upper half
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd1 && i_a_address[1:0] == 2'd2 && a_mapped)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Instruction-fetch Get
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && i_a_instr)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Corrupted A-channel integrity request
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_intg_flip)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Alert pulse without integrity fault
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert && !flip_seen)) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Repeated alert after integrity fault
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert && flip_seen && alert_cnt != 8'd0)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: ALERT_TEST fatal_fault write while regwen set
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h0 && i_a_data[0] && i_a_data[31] && !regwen_cleared)) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: Write 0 to regwen
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h0 && !i_a_data[31])) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: Alert test write after regwen cleared
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h0 && i_a_data[0] && regwen_cleared)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: Full-word Get of ALERT_TEST and CTRL
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd2 && i_a_mask == 4'hF && (i_a_address == 32'h0 || i_a_address == 32'h4))) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: Full-word Get of interrupt, config, timer and compare registers
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_opcode == 3'd4 && a_clean && i_a_size == 2'd2 && i_a_mask == 4'hF && i_a_address[1:0] == 2'b00 && i_a_address[31:5] == 27'd8)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: Interrupt output rises
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_intr_timer_expired && !prev_intr)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: Interrupt output falls
  always_ff @(posedge clk_i) if (!(!rst_ni) && (!o_intr_timer_expired && prev_intr)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: INTR_STATE W1C write while interrupt is high
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && !i_a_intg_flip && i_a_address == 32'h104 && i_a_mask[0] && i_a_data[0] && o_intr_timer_expired)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: INTR_TEST write of 1
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h108 && i_a_data[0])) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: Compare write while timer active
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && (i_a_address == 32'h118 || i_a_address == 32'h11C) && ctrl_active)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: Timer activated
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h4 && i_a_data[0] && !ctrl_active)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: Timer deactivated while active
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h4 && !i_a_data[0] && ctrl_active)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: CFG0 written with nonzero prescale
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h10C && i_a_data[11:0] != 12'd0)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: TIMER_V_UPPER written to all ones
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && a_wr && a_clean && a_full && i_a_address == 32'h114 && i_a_data == 32'hFFFFFFFF)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: A-channel stall of 3 or more cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (i_a_valid && !o_a_ready && a_stall_cnt >= 8'd2)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: D-channel back-pressure of 3 or more cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_d_valid && !i_d_ready && d_stall_cnt >= 8'd2)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: Request accepted with another outstanding
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && out_cnt >= 1)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: Reset released after activity
  always_ff @(posedge clk_i) if (!(!rst_ni) && (!rst_prev && act_before)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: Short reset window of at most 2 cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (!rst_prev && low_len != 8'd0 && low_len <= 8'd2)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: Request at highest register-space word 0x1FC
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_fire && i_a_address == 32'h1FC)) hits_COVP_039 <= hits_COVP_039 + 1;

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
