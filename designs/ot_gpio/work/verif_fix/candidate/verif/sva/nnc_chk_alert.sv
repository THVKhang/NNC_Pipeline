module nnc_chk_alert #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;

  // helper registers
  logic a_hs, d_hs, a_test_wr;
  assign a_hs = i_a_valid && o_a_ready;
  assign d_hs = o_d_valid && i_d_ready;
  assign a_test_wr = a_hs && (i_a_opcode == 3'd0 || i_a_opcode == 3'd1) &&
                     (i_a_address == 32'hC) && i_a_data[0];

  logic        intg_seen_q;
  logic        b_flag_q;
  int unsigned outs_q;
  int unsigned timer_q;
  int unsigned outs_next;

  always_comb begin
    outs_next = outs_q;
    if (a_hs) outs_next = outs_next + 1;
    if (d_hs && outs_q != 0) outs_next = outs_next - 1;
  end

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      intg_seen_q <= 1'b0;
      b_flag_q    <= 1'b0;
      outs_q      <= 0;
      timer_q     <= 0;
    end else begin
      // NNC verification fix (fix-verif, triage B): a request with i_a_intg_flip=1 has a command
      // integrity error (fatal bus integrity fault, INT-INTG-002) from the moment it is presented
      // (a_valid=1 means "Request from host is valid", TL-UL spec); it is committed (INT-TL-003) and
      // D-017 only gives an upper bound from acceptance, so the cause counts from i_a_valid=1, not
      // only from the A handshake. Traffic with i_a_intg_flip=0 is still never an alert cause.
      if (i_a_valid && i_a_intg_flip) intg_seen_q <= 1'b1;
      outs_q <= outs_next;
      if (a_test_wr) b_flag_q <= 1'b1;
      if (outs_next != 0 || a_test_wr) timer_q <= 0;
      else if (d_hs) timer_q <= 1;
      else if (timer_q < 31) timer_q <= timer_q + 1;
    end
  end

  logic cause_a, cause_b, alert_cause;
  // NNC verification fix (fix-verif, triage B): cause (a) is a cycle with i_a_valid=1 and
  // i_a_intg_flip=1 (presented flipped-integrity request), per INT-INTG-002 / D-017 / TL-UL a_valid.
  assign cause_a = intg_seen_q || (i_a_valid && i_a_intg_flip);
  assign cause_b = a_test_wr || (b_flag_q && (outs_q != 0 || timer_q <= 16));
  assign alert_cause = cause_a || cause_b;

  // CHK-001: Alert signal integrity never fails (GP-5-03, GP-5-04, GP-3-05, GP-10-33, AH-T1.3.4-01)
  a_CHK_001: assert property (@(posedge clk_i) disable iff (!rst_ni) 1'b1 |-> (o_alert_integ_fail == 1'b0))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_alert is a single-cycle pulse (GP-5-02)
  a_CHK_002: assert property (@(posedge clk_i) disable iff (!rst_ni) o_alert |=> !o_alert)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: No alert without an alert cause (GP-4.2-01)
  a_CHK_003: assert property (@(posedge clk_i) disable iff (!rst_ni) o_alert |-> alert_cause)
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert)) hits_CHK_003 <= hits_CHK_003 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
  end
endmodule
