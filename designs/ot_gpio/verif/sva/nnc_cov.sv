module nnc_cov #(
  parameter int GpioAsyncOn = 1,
  parameter int GpioAsHwStrapsEn = 1
) (
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
  input  logic [31:0]                 i_gpio,
  input  logic [31:0]                 o_gpio,
  input  logic [31:0]                 o_gpio_en,
  input  logic [31:0]                 o_intr_gpio,
  input  logic                        i_strap_en,
  input  logic                        o_straps_valid,
  input  logic [31:0]                 o_straps_data
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

  // helper signals
  wire a_hs = i_a_valid && o_a_ready;
  wire d_hs = o_d_valid && i_d_ready;
  wire a_wr = a_hs && (i_a_opcode[2:1] == 2'b00);
  wire a_rd = a_hs && (i_a_opcode == 3'd4);
  wire [29:0] wa = i_a_address[31:2];
  wire full_ok = (i_a_size == 2'd2) && (i_a_mask == 4'hF) && (i_a_address[1:0] == 2'b00) && !i_a_intg_flip;
  wire sel_io  = (i_a_address[6:2] == 5'd0) || (i_a_address[6:2] == 5'd15) || (i_a_address[6:2] == 5'd16) || (i_a_address[6:2] == 5'd31);
  wire sel_cfg = (i_a_address[7:3] == 5'd0) || (i_a_address[7:3] == 5'd15) || (i_a_address[7:3] == 5'd16) || (i_a_address[7:3] == 5'd31);
  wire unmapped = (wa >= 30'd18 && wa < 30'd64) || (wa >= 30'd96 && wa < 30'd128) || (wa >= 30'd192 && wa < 30'd256);

  int outstanding = 0;
  int unsigned a_stall = 0;
  int unsigned d_stall = 0;
  int unsigned alert_cnt = 0;
  int unsigned rst_len = 0;
  logic flip_seen = 1'b0;
  logic prev_a_hs = 1'b0;
  logic pre_busy = 1'b0;
  logic rst_was_low = 1'b0;
  logic prev_strap_en = 1'b0;
  logic [31:0] prev_intr = 32'h0;

  always_ff @(posedge clk_i) begin
    rst_was_low <= !rst_ni;
    prev_strap_en <= i_strap_en;
    prev_intr <= o_intr_gpio;
    if (!rst_ni) begin
      outstanding <= 0;
      a_stall <= 0;
      d_stall <= 0;
      alert_cnt <= 0;
      flip_seen <= 1'b0;
      prev_a_hs <= 1'b0;
      if (rst_len < 255) rst_len <= rst_len + 1;
    end else begin
      rst_len <= 0;
      pre_busy <= (outstanding > 0) || o_d_valid;
      outstanding <= outstanding + (a_hs ? 1 : 0) - (d_hs ? 1 : 0);
      prev_a_hs <= a_hs;
      if (i_a_valid && !o_a_ready) begin
        if (a_stall < 255) a_stall <= a_stall + 1;
      end else a_stall <= 0;
      if (o_d_valid && !i_d_ready) begin
        if (d_stall < 255) d_stall <= d_stall + 1;
      end else d_stall <= 0;
      if (a_hs && i_a_intg_flip) flip_seen <= 1'b1;
      if (flip_seen && o_alert && alert_cnt < 255) alert_cnt <= alert_cnt + 1;
    end
  end

  // COVP-001: Legal full-word Get handshake
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_rd && full_ok)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: Legal PutFullData handshake
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && i_a_opcode == 3'd0 && full_ok)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: Legal PutPartialData handshake
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && i_a_opcode == 3'd1 && full_ok)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: Read response without error
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_hs && o_d_opcode == 3'd1 && !o_d_error)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Write response without error
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_hs && o_d_opcode == 3'd0 && !o_d_error)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Error response to a read
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_hs && o_d_opcode == 3'd1 && o_d_error)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Error response to a write
  always_ff @(posedge clk_i) if (!(!rst_ni) && (d_hs && o_d_opcode == 3'd0 && o_d_error)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: A-channel back-pressure
  always_ff @(posedge clk_i) if (!(!rst_ni) && (i_a_valid && !o_a_ready)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: A-channel back-pressure for 3 or more cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (i_a_valid && !o_a_ready && a_stall >= 2)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: D-channel back-pressure
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_d_valid && !i_d_ready)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: D-channel back-pressure for 3 or more cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_d_valid && !i_d_ready && d_stall >= 2)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: Back-to-back A handshakes
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && prev_a_hs)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: Two or more outstanding requests
  always_ff @(posedge clk_i) if (!(!rst_ni) && (outstanding >= 2)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: Unmapped offset below 0x400
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && i_a_address[31:10] == 22'h0 && unmapped)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: Misaligned address
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && !i_a_intg_flip && i_a_address[1:0] != 2'b00 && i_a_address[31:10] == 22'h0)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Oversize request
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && !i_a_intg_flip && i_a_size == 2'd3)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Undefined opcode
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && !i_a_intg_flip && i_a_opcode != 3'd0 && i_a_opcode != 3'd1 && i_a_opcode != 3'd4)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Mask covering inactive lanes
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && !i_a_intg_flip && ((i_a_size == 2'd2 && i_a_mask != 4'hF) || (i_a_size == 2'd0 && i_a_mask == 4'hF)))) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Byte write to PER_PIN_OE/INTR_CTRL range
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && !i_a_intg_flip && i_a_size == 2'd0 && i_a_address[31:8] == 24'h000002)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: Byte write to wide register
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && !i_a_intg_flip && i_a_size == 2'd0 && (wa < 30'd18 || i_a_address[31:7] == 25'h2))) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: Byte read (sub-word, size 0)
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_rd && !i_a_intg_flip && i_a_size == 2'd0)) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: Half-word read (sub-word, size 1)
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_rd && !i_a_intg_flip && i_a_size == 2'd1)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: Instruction-fetch read
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_rd && i_a_instr)) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: Request with corrupted integrity accepted
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_hs && i_a_intg_flip)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: Alert pulse observed
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: Repeated alert after integrity fault
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert && flip_seen && alert_cnt >= 1)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: ALERT_TEST fatal_fault write
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa == 30'd3 && i_a_data[0] && i_a_data[31])) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: ALERT_TEST regwen clear write
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa == 30'd3 && !i_a_data[31])) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: DATA_OUT direct and masked writes
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa >= 30'd5 && wa <= 30'd7)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: DATA_OE direct and masked writes
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa >= 30'd8 && wa <= 30'd10)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: PER_PIN_IO write on GPIO 0/15/16/31
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && i_a_address[31:7] == 25'h2 && sel_io)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: PER_PIN_OE write on GPIO 0/15/16/31
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && !i_a_intg_flip && i_a_address[31:8] == 24'h000002 && !i_a_address[2] && sel_cfg)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: PER_PIN_INTR_CTRL write on GPIO 0/15/16/31
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && !i_a_intg_flip && i_a_address[31:8] == 24'h000002 && i_a_address[2] && sel_cfg)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: Interrupt control and filter register write
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa >= 30'd11 && wa <= 30'd15)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: INTR_STATE/INTR_ENABLE/INTR_TEST write
  always_ff @(posedge clk_i) if (!(!rst_ni) && (a_wr && full_ok && wa <= 30'd2)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: Interrupt output change
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_intr_gpio != prev_intr)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: Reset released after activity pending
  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_was_low && pre_busy)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: Short reset of at most 2 cycles
  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_was_low && rst_len >= 1 && rst_len <= 2)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: i_strap_en rising edge
  always_ff @(posedge clk_i) if (!(!rst_ni) && (i_strap_en && !prev_strap_en)) hits_COVP_039 <= hits_COVP_039 + 1;
  // COVP-040: Strap valid output high
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_straps_valid)) hits_COVP_040 <= hits_COVP_040 + 1;

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
