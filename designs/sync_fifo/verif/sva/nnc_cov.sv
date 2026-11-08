module nnc_cov #(
  parameter int PARA_SFIFO_DEPTH = 8,
  parameter int PARA_SFIFO_DATA_W = 32,
  parameter int PARA_SFIFO_PTR_RETIME = 0,
  parameter int PARA_SFIFO_MEM_USE_MACRO = 0,
  localparam int LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH),
  localparam int LPARA_PTR_W = $clog2(2 * PARA_SFIFO_DEPTH),
  localparam int LPARA_OCC_W = $clog2(PARA_SFIFO_DEPTH + 1)
) (
  input  logic                        i_clk_wr,
  input  logic                        i_rst_n_wr,
  input  logic                        i_wr_en,
  input  logic [(PARA_SFIFO_DATA_W)-1:0] i_wr_data,
  input  logic [(LPARA_OCC_W)-1:0]    i_full_thr,
  input  logic                        i_rst_n_sw,
  input  logic                        o_sw_rst_busy,
  input  logic                        o_full,
  input  logic                        o_full_thr,
  input  logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_OCC_W)-1:0]    i_empty_thr,
  input  logic [(PARA_SFIFO_DATA_W)-1:0] o_rd_data,
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

// ---------------- helpers: write domain ----------------
logic full_q = 1'b0;
logic prev_busy = 1'b0;
logic act_q = 1'b0;
logic ovf_q = 1'b0;
logic sw_q = 1'b0;
logic rst_act = 1'b0;
logic rst_ovf = 1'b0;
logic rst_sw = 1'b0;
int unsigned wr_rej_run = 0;
int unsigned busy_run = 0;
int unsigned sw_low_len = 0;
int unsigned wr_cnt = 0;
int unsigned wr_wraps = 0;

always_ff @(posedge i_clk_wr) begin
  if (!i_rst_n_wr) begin
    full_q <= 1'b0;
    prev_busy <= 1'b0;
    wr_rej_run <= 0;
    busy_run <= 0;
    sw_low_len <= 0;
    wr_cnt <= 0;
    wr_wraps <= 0;
  end else begin
    full_q <= o_full && i_rst_n_sw && !o_sw_rst_busy;
    prev_busy <= o_sw_rst_busy;
    if (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy) wr_rej_run <= wr_rej_run + 1;
    else wr_rej_run <= 0;
    if (o_sw_rst_busy) busy_run <= busy_run + 1;
    else busy_run <= 0;
    if (i_rst_n_sw) sw_low_len <= 0;
    else if (sw_low_len < 1000) sw_low_len <= sw_low_len + 1;
    if (i_wr_en && !o_full) begin
      if (wr_cnt == (2*PARA_SFIFO_DEPTH-1)) begin
        wr_cnt <= 0;
        wr_wraps <= wr_wraps + 1;
      end else begin
        wr_cnt <= wr_cnt + 1;
      end
    end
  end
end

// history flops that hold their value while reset is low
always_ff @(posedge i_clk_wr) begin
  if (i_rst_n_wr) begin
    act_q <= (i_wr_en && !o_full) || o_full || o_sw_rst_busy || o_overflow;
    ovf_q <= i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy;
    sw_q  <= o_sw_rst_busy || !i_rst_n_sw;
  end
end

always_ff @(posedge i_clk_wr or negedge i_rst_n_wr) begin
  if (!i_rst_n_wr) begin
    rst_act <= act_q;
    rst_ovf <= ovf_q;
    rst_sw  <= sw_q;
  end else begin
    rst_act <= 1'b0;
    rst_ovf <= 1'b0;
    rst_sw  <= 1'b0;
  end
end

// ---------------- helpers: read domain ----------------
logic emp_q = 1'b1;
logic rd_act_q = 1'b0;
logic rst_rd_act = 1'b0;
int unsigned rd_rej_run = 0;
int unsigned rd_run = 0;
int unsigned rd_cnt = 0;

always_ff @(posedge i_clk_rd) begin
  if (!i_rst_n_rd) begin
    emp_q <= 1'b1;
    rd_rej_run <= 0;
    rd_run <= 0;
    rd_cnt <= 0;
  end else begin
    emp_q <= o_empty;
    if (i_rd_en && o_empty && !o_sw_rst_busy) rd_rej_run <= rd_rej_run + 1;
    else rd_rej_run <= 0;
    if (i_rd_en && !o_empty) rd_run <= rd_run + 1;
    else rd_run <= 0;
    if (i_rd_en && !o_empty) begin
      if (rd_cnt == (2*PARA_SFIFO_DEPTH-1)) rd_cnt <= 0;
      else rd_cnt <= rd_cnt + 1;
    end
  end
end

always_ff @(posedge i_clk_rd) begin
  if (i_rst_n_rd) rd_act_q <= !o_empty || o_sw_rst_busy;
end

always_ff @(posedge i_clk_rd or negedge i_rst_n_rd) begin
  if (!i_rst_n_rd) rst_rd_act <= rd_act_q;
  else rst_rd_act <= 1'b0;
end

// COVP-001: Write accepted
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && !o_full)) hits_COVP_001 <= hits_COVP_001 + 1;
// COVP-002: Rejected unblocked write (full)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy)) hits_COVP_002 <= hits_COVP_002 + 1;
// COVP-003: o_overflow pulse observed
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_overflow)) hits_COVP_003 <= hits_COVP_003 + 1;
// COVP-004: Three or more consecutive rejected writes
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy && wr_rej_run >= 2)) hits_COVP_004 <= hits_COVP_004 + 1;
// COVP-005: Write request during software reset block
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && (!i_rst_n_sw || o_sw_rst_busy))) hits_COVP_005 <= hits_COVP_005 + 1;
// COVP-006: Software reset sequence starts
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_sw_rst_busy && !i_rst_n_sw)) hits_COVP_006 <= hits_COVP_006 + 1;
// COVP-007: Software reset low level of exactly 1 cycle
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_rst_n_sw && sw_low_len == 1)) hits_COVP_007 <= hits_COVP_007 + 1;
// COVP-008: Software reset low level of 3 to 9 cycles
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_rst_n_sw && sw_low_len >= 3 && sw_low_len < 10)) hits_COVP_008 <= hits_COVP_008 + 1;
// COVP-009: Software reset low level of 10 or more cycles
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_rst_n_sw && sw_low_len >= 10)) hits_COVP_009 <= hits_COVP_009 + 1;
// COVP-010: o_sw_rst_busy falls (sequence completion)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (prev_busy && !o_sw_rst_busy)) hits_COVP_010 <= hits_COVP_010 + 1;
// COVP-011: Busy held for 3 or more cycles
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_sw_rst_busy && busy_run >= 3)) hits_COVP_011 <= hits_COVP_011 + 1;
// COVP-012: New software reset request while busy
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_sw_rst_busy && !i_rst_n_sw)) hits_COVP_012 <= hits_COVP_012 + 1;
// COVP-013: Software reset started while FIFO full
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_sw_rst_busy && !i_rst_n_sw && full_q)) hits_COVP_013 <= hits_COVP_013 + 1;
// COVP-014: o_full rises
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_full && i_rst_n_sw && !o_sw_rst_busy && !full_q)) hits_COVP_014 <= hits_COVP_014 + 1;
// COVP-015: o_full falls
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (!o_full && full_q)) hits_COVP_015 <= hits_COVP_015 + 1;
// COVP-016: Simultaneous accepted write and read
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && !o_full && i_rd_en && !o_empty)) hits_COVP_016 <= hits_COVP_016 + 1;
// COVP-017: Write to full FIFO with read request accepted (no bypass)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && o_full && i_rst_n_sw && !o_sw_rst_busy && i_rd_en && !o_empty)) hits_COVP_017 <= hits_COVP_017 + 1;
// COVP-018: o_full_thr active while not full
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (o_full_thr && !o_full)) hits_COVP_018 <= hits_COVP_018 + 1;
// COVP-019: Blocked write: o_full_thr shows empty value 1 (threshold 0)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((!i_rst_n_sw || o_sw_rst_busy) && (i_full_thr == 0) && o_full_thr)) hits_COVP_019 <= hits_COVP_019 + 1;
// COVP-020: Blocked write: o_full_thr 0 (threshold not 0)
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((!i_rst_n_sw || o_sw_rst_busy) && (i_full_thr != 0) && !o_full_thr)) hits_COVP_020 <= hits_COVP_020 + 1;
// COVP-021: Full threshold above DEPTH while FIFO full
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((i_full_thr > PARA_SFIFO_DEPTH) && o_full && i_rst_n_sw && !o_sw_rst_busy && !o_full_thr)) hits_COVP_021 <= hits_COVP_021 + 1;
// COVP-022: Full threshold equal DEPTH at full
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && ((i_full_thr == PARA_SFIFO_DEPTH) && o_full && i_rst_n_sw && !o_sw_rst_busy && o_full_thr)) hits_COVP_022 <= hits_COVP_022 + 1;
// COVP-023: Write pointer wrap
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && !o_full && wr_cnt == (2*PARA_SFIFO_DEPTH-1))) hits_COVP_023 <= hits_COVP_023 + 1;
// COVP-024: Second write pointer wrap
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (i_wr_en && !o_full && wr_cnt == (2*PARA_SFIFO_DEPTH-1) && wr_wraps >= 1)) hits_COVP_024 <= hits_COVP_024 + 1;
// COVP-025: Write-domain hardware reset during activity, release observed
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (rst_act)) hits_COVP_025 <= hits_COVP_025 + 1;
// COVP-026: Write-domain hardware reset while overflow pulse active
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (rst_ovf)) hits_COVP_026 <= hits_COVP_026 + 1;
// COVP-027: Hardware reset during software reset sequence
always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (rst_sw)) hits_COVP_027 <= hits_COVP_027 + 1;
// COVP-028: Read accepted
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && !o_empty)) hits_COVP_028 <= hits_COVP_028 + 1;
// COVP-029: Rejected unblocked read (empty)
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty && !o_sw_rst_busy)) hits_COVP_029 <= hits_COVP_029 + 1;
// COVP-030: o_underflow pulse observed
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_underflow)) hits_COVP_030 <= hits_COVP_030 + 1;
// COVP-031: Three or more consecutive rejected reads
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_empty && !o_sw_rst_busy && rd_rej_run >= 2)) hits_COVP_031 <= hits_COVP_031 + 1;
// COVP-032: Read request during software reset block
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && o_sw_rst_busy && o_empty)) hits_COVP_032 <= hits_COVP_032 + 1;
// COVP-033: o_empty rises
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_empty && !emp_q && !o_sw_rst_busy)) hits_COVP_033 <= hits_COVP_033 + 1;
// COVP-034: o_empty falls
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (!o_empty && emp_q)) hits_COVP_034 <= hits_COVP_034 + 1;
// COVP-035: Four or more back-to-back accepted reads
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && !o_empty && rd_run >= 4)) hits_COVP_035 <= hits_COVP_035 + 1;
// COVP-036: o_empty_thr active while not empty
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (o_empty_thr && !o_empty && !o_sw_rst_busy)) hits_COVP_036 <= hits_COVP_036 + 1;
// COVP-037: o_empty_thr inactive (occupancy above threshold)
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (!o_empty_thr && !o_empty)) hits_COVP_037 <= hits_COVP_037 + 1;
// COVP-038: Empty threshold above DEPTH with data present
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && ((i_empty_thr > PARA_SFIFO_DEPTH) && !o_empty && !o_sw_rst_busy && o_empty_thr)) hits_COVP_038 <= hits_COVP_038 + 1;
// COVP-039: Read pointer wrap
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (i_rd_en && !o_empty && rd_cnt == (2*PARA_SFIFO_DEPTH-1))) hits_COVP_039 <= hits_COVP_039 + 1;
// COVP-040: Read-domain hardware reset during activity, release observed
always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (rst_rd_act)) hits_COVP_040 <= hits_COVP_040 + 1;

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
