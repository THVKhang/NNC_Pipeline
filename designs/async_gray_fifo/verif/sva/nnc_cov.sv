module nnc_cov #(
  parameter int PARA_AFIFO_DEPTH = 8,
  parameter int PARA_AFIFO_DATA_W = 32,
  parameter int PARA_AFIFO_CELL_TYPE = 2,
  parameter int PARA_AFIFO_MEM_USE_MACRO = 0,
  localparam int LPARA_ADDR_W = $clog2(PARA_AFIFO_DEPTH),
  localparam int LPARA_PTR_W = LPARA_ADDR_W + 1
) (
  input  logic                        i_clk_wr,
  input  logic                        i_rst_n_wr,
  input  logic                        i_wr_en,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] i_wr_data,
  input  logic [(LPARA_PTR_W)-1:0]    i_full_thr,
  input  logic                        i_rst_n_sw,
  input  logic                        o_sw_rst_busy,
  input  logic                        o_full,
  input  logic                        o_full_thr,
  input  logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_PTR_W)-1:0]    i_empty_thr,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] o_rd_data,
  input  logic                        o_empty,
  input  logic                        o_empty_thr,
  input  logic                        o_underflow
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

// ---- write-domain helpers ----
logic w_prev_full;
logic w_prev_blk;
logic w_prev_busy;
logic w_prev_sw;
logic w_prev2_sw;
logic w_prev_ovf;
logic w_first;
int unsigned w_full_bp;
int unsigned w_sw_low;
int unsigned w_acc_cnt;
int unsigned w_burst;
wire w_blk = !i_rst_n_sw || o_sw_rst_busy;
wire w_acc = i_wr_en && !o_full && i_rst_n_sw && !o_sw_rst_busy;
wire [31:0] w_thr = {28'd0, i_full_thr};
always_ff @(posedge i_clk_wr) begin
  if (!i_rst_n_wr) begin
    w_prev_full <= 1'b0;
    w_prev_blk <= 1'b0;
    w_prev_busy <= 1'b0;
    w_prev_sw <= 1'b1;
    w_prev2_sw <= 1'b1;
    w_prev_ovf <= 1'b0;
    w_first <= 1'b1;
    w_full_bp <= 0;
    w_sw_low <= 0;
    w_acc_cnt <= 0;
    w_burst <= 0;
  end else begin
    w_prev_full <= o_full;
    w_prev_blk <= w_blk;
    w_prev_busy <= o_sw_rst_busy;
    w_prev_sw <= i_rst_n_sw;
    w_prev2_sw <= w_prev_sw;
    w_prev_ovf <= o_overflow;
    if (w_acc) w_first <= 1'b0;
    if (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy) begin
      if (w_full_bp < 1000) w_full_bp <= w_full_bp + 1;
    end else w_full_bp <= 0;
    if (!i_rst_n_sw) begin
      if (w_sw_low < 1000) w_sw_low <= w_sw_low + 1;
    end else w_sw_low <= 0;
    if (w_blk) w_acc_cnt <= 0;
    else if (w_acc) w_acc_cnt <= (w_acc_cnt == (2*PARA_AFIFO_DEPTH - 1)) ? 0 : w_acc_cnt + 1;
    if (w_acc) begin
      if (w_burst < 1000) w_burst <= w_burst + 1;
    end else w_burst <= 0;
  end
end

// COVP-001: Accepted write
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_acc)) hits_COVP_001 <= hits_COVP_001 + 1;
// COVP-002: Write requested while full (not blocked)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy)) hits_COVP_002 <= hits_COVP_002 + 1;
// COVP-003: o_overflow pulse seen
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_overflow)) hits_COVP_003 <= hits_COVP_003 + 1;
// COVP-004: Consecutive overflow pulses (back-to-back rejects)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_overflow && w_prev_ovf)) hits_COVP_004 <= hits_COVP_004 + 1;
// COVP-005: o_full rises outside software reset
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_full && !w_prev_full && !w_blk && !w_prev_blk)) hits_COVP_005 <= hits_COVP_005 + 1;
// COVP-006: o_full falls outside software reset (late fall after read)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_full && w_prev_full && !w_blk && !w_prev_blk)) hits_COVP_006 <= hits_COVP_006 + 1;
// COVP-007: o_full falls at write release of software reset
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_sw_rst_busy && w_prev_busy && i_rst_n_sw && !o_full)) hits_COVP_007 <= hits_COVP_007 + 1;
// COVP-008: Full back-pressure held with write requests for 3+ cycles
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy && w_full_bp >= 2)) hits_COVP_008 <= hits_COVP_008 + 1;
// COVP-009: i_full_thr = 0 gives o_full_thr = 1
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_thr == 0 && o_full_thr)) hits_COVP_009 <= hits_COVP_009 + 1;
// COVP-010: i_full_thr = DEPTH with FIFO full
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_thr == PARA_AFIFO_DEPTH && o_full && o_full_thr && !w_blk)) hits_COVP_010 <= hits_COVP_010 + 1;
// COVP-011: i_full_thr above DEPTH gives o_full_thr = 0
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_thr > PARA_AFIFO_DEPTH && !o_full_thr)) hits_COVP_011 <= hits_COVP_011 + 1;
// COVP-012: Mid i_full_thr reached (partial FIFO)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_thr >= 1 && w_thr < PARA_AFIFO_DEPTH && o_full_thr && !o_full && !w_blk)) hits_COVP_012 <= hits_COVP_012 + 1;
// COVP-013: Nonzero i_full_thr not reached
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_thr >= 1 && w_thr <= PARA_AFIFO_DEPTH && !o_full_thr && !o_full)) hits_COVP_013 <= hits_COVP_013 + 1;
// COVP-014: Software reset request starts
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!i_rst_n_sw && !o_sw_rst_busy)) hits_COVP_014 <= hits_COVP_014 + 1;
// COVP-015: One-cycle i_rst_n_sw low pulse
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_rst_n_sw && !w_prev_sw && w_prev2_sw)) hits_COVP_015 <= hits_COVP_015 + 1;
// COVP-016: i_rst_n_sw held low 3+ cycles
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!i_rst_n_sw && w_sw_low >= 2)) hits_COVP_016 <= hits_COVP_016 + 1;
// COVP-017: o_sw_rst_busy rises
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_sw_rst_busy && !w_prev_busy)) hits_COVP_017 <= hits_COVP_017 + 1;
// COVP-018: Write attempted while i_rst_n_sw is low
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && !i_rst_n_sw)) hits_COVP_018 <= hits_COVP_018 + 1;
// COVP-019: Write attempted while busy with i_rst_n_sw at 1
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && i_rst_n_sw && o_sw_rst_busy)) hits_COVP_019 <= hits_COVP_019 + 1;
// COVP-020: i_rst_n_sw driven low again while busy
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!i_rst_n_sw && w_prev_sw && o_sw_rst_busy && w_prev_busy)) hits_COVP_020 <= hits_COVP_020 + 1;
// COVP-021: One-cycle busy gap between back-to-back sequences
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_sw_rst_busy && w_prev_busy && !i_rst_n_sw)) hits_COVP_021 <= hits_COVP_021 + 1;
// COVP-022: First accepted write after hardware reset
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_acc && w_first)) hits_COVP_022 <= hits_COVP_022 + 1;
// COVP-023: Write pointer wrap (2*DEPTH accepted writes)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_acc && w_acc_cnt == (2*PARA_AFIFO_DEPTH - 1))) hits_COVP_023 <= hits_COVP_023 + 1;
// COVP-024: Write burst of DEPTH or more consecutive accepted writes
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (w_acc && w_burst >= (PARA_AFIFO_DEPTH - 1))) hits_COVP_024 <= hits_COVP_024 + 1;

// ---- read-domain helpers ----
logic r_prev_empty;
logic r_prev_uf;
logic r_prev_acc;
logic r_first;
int unsigned r_empty_bp;
int unsigned r_acc_cnt;
int unsigned r_burst;
wire r_acc = i_rd_en && !o_empty;
wire [31:0] r_thr = {28'd0, i_empty_thr};
always_ff @(posedge i_clk_rd) begin
  if (!i_rst_n_rd) begin
    r_prev_empty <= 1'b1;
    r_prev_uf <= 1'b0;
    r_prev_acc <= 1'b0;
    r_first <= 1'b1;
    r_empty_bp <= 0;
    r_acc_cnt <= 0;
    r_burst <= 0;
  end else begin
    r_prev_empty <= o_empty;
    r_prev_uf <= o_underflow;
    r_prev_acc <= r_acc;
    if (r_acc) r_first <= 1'b0;
    if (i_rd_en && o_empty) begin
      if (r_empty_bp < 1000) r_empty_bp <= r_empty_bp + 1;
    end else r_empty_bp <= 0;
    if (r_acc) r_acc_cnt <= (r_acc_cnt == (2*PARA_AFIFO_DEPTH - 1)) ? 0 : r_acc_cnt + 1;
    if (r_acc) begin
      if (r_burst < 1000) r_burst <= r_burst + 1;
    end else r_burst <= 0;
  end
end

// COVP-025: Accepted read
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_acc)) hits_COVP_025 <= hits_COVP_025 + 1;
// COVP-026: Read requested while empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty)) hits_COVP_026 <= hits_COVP_026 + 1;
// COVP-027: o_underflow pulse seen
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_underflow)) hits_COVP_027 <= hits_COVP_027 + 1;
// COVP-028: Consecutive underflow pulses
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_underflow && r_prev_uf)) hits_COVP_028 <= hits_COVP_028 + 1;
// COVP-029: o_empty falls
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (!o_empty && r_prev_empty)) hits_COVP_029 <= hits_COVP_029 + 1;
// COVP-030: o_empty rises
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_empty && !r_prev_empty)) hits_COVP_030 <= hits_COVP_030 + 1;
// COVP-031: Empty back-pressure with read requests for 3+ cycles
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty && r_empty_bp >= 2)) hits_COVP_031 <= hits_COVP_031 + 1;
// COVP-032: Read burst of DEPTH or more consecutive accepted reads
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_acc && r_burst >= (PARA_AFIFO_DEPTH - 1))) hits_COVP_032 <= hits_COVP_032 + 1;
// COVP-033: i_empty_thr = 0 while empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_thr == 0 && o_empty && o_empty_thr)) hits_COVP_033 <= hits_COVP_033 + 1;
// COVP-034: i_empty_thr = 0 while not empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_thr == 0 && !o_empty && !o_empty_thr)) hits_COVP_034 <= hits_COVP_034 + 1;
// COVP-035: i_empty_thr >= DEPTH while not empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_thr >= PARA_AFIFO_DEPTH && !o_empty && o_empty_thr)) hits_COVP_035 <= hits_COVP_035 + 1;
// COVP-036: Mid i_empty_thr reached while not empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_thr >= 1 && r_thr < PARA_AFIFO_DEPTH && !o_empty && o_empty_thr)) hits_COVP_036 <= hits_COVP_036 + 1;
// COVP-037: Mid i_empty_thr exceeded by occupancy
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_thr >= 1 && r_thr < PARA_AFIFO_DEPTH && !o_empty && !o_empty_thr)) hits_COVP_037 <= hits_COVP_037 + 1;
// COVP-038: First accepted read after hardware reset
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_acc && r_first)) hits_COVP_038 <= hits_COVP_038 + 1;
// COVP-039: Read pointer wrap (2*DEPTH accepted reads)
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (r_acc && r_acc_cnt == (2*PARA_AFIFO_DEPTH - 1))) hits_COVP_039 <= hits_COVP_039 + 1;
// COVP-040: Read request on empty right after a draining read
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty && r_prev_acc)) hits_COVP_040 <= hits_COVP_040 + 1;

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
