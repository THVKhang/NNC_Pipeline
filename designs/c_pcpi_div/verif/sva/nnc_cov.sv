module nnc_cov (
  input  logic                        clk,
  input  logic                        resetn,
  input  logic                        pcpi_valid,
  input  logic [31:0]                 pcpi_insn,
  input  logic [31:0]                 pcpi_rs1,
  input  logic [31:0]                 pcpi_rs2,
  input  logic                        pcpi_wr,
  input  logic [31:0]                 pcpi_rd,
  input  logic                        pcpi_wait,
  input  logic                        pcpi_ready
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

  logic prev_out = 1'b0;
  logic prev_ready_q = 1'b0;
  logic prev_wait_q = 1'b0;
  logic prev_rstn = 1'b0;
  logic raw_out = 1'b0;
  logic mid_rst = 1'b0;
  logic [7:0] cnt = 8'd0;
  logic [7:0] idle_cnt = 8'd0;

  wire is_div = (pcpi_insn[6:0] == 7'b0110011) && (pcpi_insn[31:25] == 7'b0000001) && pcpi_insn[14];
  wire [2:0] f3 = pcpi_insn[14:12];
  wire done = pcpi_valid && is_div && pcpi_ready && pcpi_wr;
  wire rs2_zero = (pcpi_rs2 == 32'd0);
  wire ovf = (pcpi_rs1 == 32'h80000000) && (pcpi_rs2 == 32'hFFFFFFFF);

  always_ff @(posedge clk) begin
    raw_out <= resetn && pcpi_valid && !pcpi_ready;
    prev_rstn <= resetn;
    if (!resetn) begin
      prev_out <= 1'b0;
      prev_ready_q <= 1'b0;
      prev_wait_q <= 1'b0;
      cnt <= 8'd0;
      idle_cnt <= 8'd0;
      if (raw_out) mid_rst <= 1'b1;
    end else begin
      prev_out <= pcpi_valid && !pcpi_ready;
      prev_ready_q <= pcpi_ready;
      prev_wait_q <= pcpi_wait;
      if (!pcpi_valid || pcpi_ready) cnt <= 8'd0;
      else if (cnt != 8'hFF) cnt <= cnt + 8'd1;
      if (pcpi_valid || pcpi_wait || pcpi_ready || pcpi_wr) idle_cnt <= 8'd0;
      else if (idle_cnt != 8'hFF) idle_cnt <= idle_cnt + 8'd1;
      if (pcpi_ready) mid_rst <= 1'b0;
    end
  end

  // COVP-001: DIV completes with write
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: DIVU completes with write
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b101)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: REM completes with write
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b110)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: REMU completes with write
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b111)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Wait high in first cycle of a division request
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && is_div && !prev_out && pcpi_wait)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Wait held on consecutive cycles
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && is_div && pcpi_wait && !pcpi_ready && prev_wait_q)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Wait still high after 16 cycles
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && is_div && pcpi_wait && !pcpi_ready && cnt >= 8'd16)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: Wait still high after 31 cycles
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && is_div && pcpi_wait && !pcpi_ready && cnt >= 8'd31)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: Completion in mid latency class
  always_ff @(posedge clk) if (!(!resetn) && (done && cnt >= 8'd16 && cnt <= 8'd31)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: Completion in long latency class
  always_ff @(posedge clk) if (!(!resetn) && (done && cnt >= 8'd32)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: DIV by zero
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100 && rs2_zero)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: DIVU by zero
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b101 && rs2_zero)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: REM by zero
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b110 && rs2_zero)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: REMU by zero
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b111 && rs2_zero)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: DIV signed overflow
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100 && ovf)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: REM signed overflow
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b110 && ovf)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: DIV negative dividend positive divisor
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100 && pcpi_rs1[31] && !pcpi_rs2[31] && !rs2_zero)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: DIV positive dividend negative divisor
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100 && !pcpi_rs1[31] && pcpi_rs2[31])) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: DIV both operands negative
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b100 && pcpi_rs1[31] && pcpi_rs2[31] && !ovf)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: REM negative dividend nonzero result
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b110 && pcpi_rs1[31] && pcpi_rd != 32'd0 && !rs2_zero)) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: REM positive dividend negative divisor nonzero result
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b110 && !pcpi_rs1[31] && pcpi_rs2[31] && pcpi_rd != 32'd0)) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: DIVU with high-bit dividend
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b101 && pcpi_rs1[31] && !pcpi_rs2[31] && !rs2_zero)) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: REMU dividend smaller than divisor
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b111 && !rs2_zero && pcpi_rs1 < pcpi_rs2)) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: DIVU dividend smaller than divisor
  always_ff @(posedge clk) if (!(!resetn) && (done && f3 == 3'b101 && !rs2_zero && pcpi_rs1 < pcpi_rs2)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: Equal operands
  always_ff @(posedge clk) if (!(!resetn) && (done && pcpi_rs1 == pcpi_rs2 && !rs2_zero)) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: Divisor one
  always_ff @(posedge clk) if (!(!resetn) && (done && pcpi_rs2 == 32'd1)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: Zero dividend
  always_ff @(posedge clk) if (!(!resetn) && (done && pcpi_rs1 == 32'd0 && !rs2_zero)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: Remainder exactly zero
  always_ff @(posedge clk) if (!(!resetn) && (done && f3[1] && pcpi_rd == 32'd0 && !rs2_zero && pcpi_rs1 != 32'd0)) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: Back-to-back division requests
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && is_div && !prev_out && prev_ready_q)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: Non-division instruction ignored
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && !is_div && !pcpi_wait && !pcpi_ready)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: Idle first cycle after reset
  always_ff @(posedge clk) if (!(!resetn) && (!prev_rstn && !pcpi_valid && !pcpi_wait && !pcpi_ready && !pcpi_wr)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: Long idle after reset
  always_ff @(posedge clk) if (!(!resetn) && (idle_cnt >= 8'd8 && !pcpi_valid && !pcpi_wait && !pcpi_ready && !pcpi_wr)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: Completion after reset during activity
  always_ff @(posedge clk) if (!(!resetn) && (mid_rst && pcpi_ready && pcpi_wr)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: Most negative dividend with other divisor
  always_ff @(posedge clk) if (!(!resetn) && (done && pcpi_rs1 == 32'h80000000 && !rs2_zero && pcpi_rs2 != 32'hFFFFFFFF)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: Signed division by minus one without overflow
  always_ff @(posedge clk) if (!(!resetn) && (done && (f3 == 3'b100 || f3 == 3'b110) && pcpi_rs2 == 32'hFFFFFFFF && pcpi_rs1 != 32'h80000000)) hits_COVP_035 <= hits_COVP_035 + 1;

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
  end
endmodule
