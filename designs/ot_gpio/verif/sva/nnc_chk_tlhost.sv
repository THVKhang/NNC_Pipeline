module nnc_chk_tlhost #(
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

  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;

  // ---------------- helper state ----------------
  localparam int unsigned STRAP_QUIET = 4;
  localparam int unsigned STRAP_BEFORE = 24;
  localparam int unsigned STRAP_AFTER = 8;

  logic [2:0]   rel_cnt_q = '0;      // number of previous edges with rst_ni=1 (saturating at 7)
  logic         pend_q = 1'b0;       // previous edge: valid && !ready (request must be held)
  logic [85:0]  a_fields_q = '0;
  logic [255:0] out_q = '0;          // outstanding sources
  logic [31:0]  prev_gpio_q = '0;
  logic [5:0]   run_q = '0;          // consecutive edges with unchanged i_gpio
  logic         es_seen_q = 1'b0;
  logic [3:0]   after_cnt_q = '0;
  // NNC verification fix (fix-verif, triage B): rule (f) covers every input; the old [48:0] vector truncated the
  // concatenation and dropped i_a_valid, opcode, param, size, source, address, mask and a_data[31:13].
  logic [120:0] neg_in_q = '0;
  logic         neg_seen_q = 1'b0;

  wire [85:0] a_fields = {i_a_opcode, i_a_param, i_a_size, i_a_source, i_a_address,
                          i_a_mask, i_a_data, i_a_instr, i_a_intg_flip};
  wire        a_hs = i_a_valid && o_a_ready;
  wire        d_hs = o_d_valid && i_d_ready;
  wire [5:0]  cur_run = (i_gpio == prev_gpio_q) ? ((run_q == 6'd63) ? run_q : run_q + 6'd1) : 6'd0;
  wire        es_now = (GpioAsHwStrapsEn != 0) && rst_ni && i_strap_en && !es_seen_q;
  // NNC verification fix (fix-verif, triage B): full-width input vector (121 bits). rst_ni is excluded deliberately:
  // its assertion is asynchronous by specification (INT-RST-001), so it is not bound by rule (f).
  wire [120:0] cur_in = {i_a_valid, i_a_opcode, i_a_param, i_a_size, i_a_source,
                         i_a_address, i_a_mask, i_a_data, i_a_instr, i_a_intg_flip,
                         i_d_ready, i_gpio, i_strap_en};

  always_ff @(posedge clk_i) begin
    prev_gpio_q <= i_gpio;
    run_q       <= cur_run;
    a_fields_q  <= a_fields;
    if (!rst_ni) begin
      rel_cnt_q   <= '0;
      pend_q      <= 1'b0;
      out_q       <= '0;
      es_seen_q   <= 1'b0;
      after_cnt_q <= '0;
    end else begin
      if (rel_cnt_q != 3'd7) rel_cnt_q <= rel_cnt_q + 3'd1;
      pend_q <= i_a_valid && !o_a_ready;
      if (d_hs) out_q[o_d_source] <= 1'b0;
      if (a_hs) out_q[i_a_source] <= 1'b1;
      if (es_now) begin
        es_seen_q   <= 1'b1;
        after_cnt_q <= STRAP_AFTER[3:0];
      end else if (after_cnt_q != 4'd0) begin
        after_cnt_q <= after_cnt_q - 4'd1;
      end
    end
  end

  always_ff @(negedge clk_i) begin
    neg_in_q   <= cur_in;
    neg_seen_q <= 1'b1;
  end

  // (a) hold rules
  wire viol_a = pend_q && (!i_a_valid || (a_fields != a_fields_q));
  // (c) distinct source per outstanding request
  wire viol_c = a_hs && out_q[i_a_source] && !(d_hs && (o_d_source == i_a_source));
  // (d) legal requests
  wire mask_ok = (i_a_mask == 4'b0001) || (i_a_mask == 4'b0010) || (i_a_mask == 4'b0100) ||
                 (i_a_mask == 4'b1000) || (i_a_mask == 4'b0011) || (i_a_mask == 4'b1100) ||
                 (i_a_mask == 4'b1111);
  wire viol_d = i_a_valid && !((i_a_address < 32'h400) &&
                               !(i_a_instr && (i_a_opcode == 3'd0 || i_a_opcode == 3'd1)) &&
                               mask_ok &&
                               (i_a_opcode != 3'd0 || i_a_size == 2'd2));
  // (e) strap sampling gpio stability
  wire viol_e = (es_now && (cur_run < STRAP_BEFORE[5:0])) ||
                ((after_cnt_q != 4'd0) && (i_gpio != prev_gpio_q));
  wire viol_any = viol_a || viol_c || viol_d || viol_e;

  // CHK-011: Test-bench stimulus legality monitor (GP-4.1-04, GP-10-30, GP-10-26, GP-10-21, GP-10-19, GP-10-10, GP-2-04, TL-T3.1.3.4-02, TL-T3.1.3.4-04)
  a_CHK_011: assert property (@(posedge clk_i) disable iff (!rst_ni) 1'b1 |-> !viol_any)
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (1'b1)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-011: reset-time rules (b), strap quiet period (e) and sync-input rule (f) (GP-10-30, GP-10-10, GP-2-04)
  wire viol_b   = (!rst_ni || rel_cnt_q == 3'd0) && i_a_valid;
  wire viol_e0  = (GpioAsHwStrapsEn != 0) && (!rst_ni || rel_cnt_q < STRAP_QUIET[2:0]) && i_strap_en;
  wire viol_f   = (GpioAsyncOn == 0) && neg_seen_q && (cur_in != neg_in_q);
  a_CHK_011_rst: assert property (@(posedge clk_i) 1'b1 |-> !(viol_b || viol_e0 || viol_f))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
  end
endmodule
