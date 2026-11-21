module nnc_chk_alert (
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;

  // Helper model
  logic        acc_w;
  logic        wr0_w;
  logic        qual_w;
  logic        d_beat_w;
  logic        flip_pres_w;
  logic        flip_now_w;
  logic        flip_seen;
  logic        regwen;
  logic        p_valid;
  logic        p_qual;
  logic        p_clr;
  int unsigned q_cnt;
  int unsigned q_err;
  int unsigned a_cnt;
  int unsigned age;
  int unsigned qerr_now_w;

  assign acc_w      = i_a_valid && o_a_ready;
  // NNC verification fix (fix-verif, triage B): a full-word write (a_size=2, mask 1111) to ALERT_TEST
  // is a write to fatal_fault / regwen whether it is PutFullData or PutPartialData. Spec INT-ALERT-003 /
  // RT-T5.2.1-03 ("Write 1 to trigger one alert event") and D-009 do not limit the opcode, D-013 /
  // CHK-029 say full-word writes with mask 1111 succeed for both PutFullData and PutPartialData, and
  // TL-T3.1.3.4-05 defines PutPartialData with a_size=2 as a 4-byte write. Before, only opcode 0 was
  // counted, so a legal PutPartialData alert-test write was not counted as qualifying (and did not
  // clear the regwen model). The count bound and the 16-cycle bound are unchanged.
  assign wr0_w      = acc_w && ((i_a_opcode == 3'd0) || (i_a_opcode == 3'd1)) && (i_a_size == 2'd2) &&
                      (i_a_mask == 4'hF) && (i_a_address == 32'h0);
  assign qual_w     = wr0_w && i_a_data[0] && regwen;
  assign d_beat_w   = p_valid && o_d_valid && i_d_ready;
  // NNC verification fix (fix-verif, triage B): INT-INTG-002 says a request with i_a_intg_flip=1 "has a
  // command integrity error ... which triggers the fatal_fault alert" and does not require the request to
  // be accepted first. D-010 gives only an upper bound from acceptance and does not forbid an earlier
  // alert, and D-014 lets the bench present requests while o_a_ready=0. So the flip exemption starts at
  // the first edge (rst_ni=1) where such a request is presented (i_a_valid=1), not only at acceptance.
  // Every acceptance is also a presentation, so the old trigger is still included. The assertion and
  // its bounds are unchanged.
  assign flip_pres_w = rst_ni && i_a_valid && i_a_intg_flip;
  assign flip_now_w = flip_seen || flip_pres_w;
  assign qerr_now_w = q_err + ((d_beat_w && p_qual && o_d_error) ? 1 : 0);

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      flip_seen <= 1'b0;
      regwen    <= 1'b1;
      p_valid   <= 1'b0;
      p_qual    <= 1'b0;
      p_clr     <= 1'b0;
      q_cnt     <= 0;
      q_err     <= 0;
      a_cnt     <= 0;
      age       <= 31;
    end else begin
      // NNC verification fix (fix-verif, triage B): set on presentation of a flip request (INT-INTG-002),
      // not only on its acceptance edge.
      if (flip_pres_w) flip_seen <= 1'b1;
      if (d_beat_w) begin
        p_valid <= 1'b0;
        if (p_clr && !o_d_error) regwen <= 1'b0;
        if (p_qual && !o_d_error) age <= 1;
        else if (age < 31) age <= age + 1;
        if (p_qual && o_d_error) q_err <= q_err + 1;
      end else begin
        if (age < 31) age <= age + 1;
      end
      if (acc_w) begin
        p_valid <= 1'b1;
        p_qual  <= qual_w;
        p_clr   <= wr0_w && !i_a_data[31];
      end
      if (qual_w) q_cnt <= q_cnt + 1;
      if (o_alert) a_cnt <= a_cnt + 1;
    end
  end

  // CHK-001: No alert signal-integrity failure (RT-5-04, RT-8-32, RT-3-07)
  a_CHK_001: assert property (@(posedge clk_i) disable iff (!rst_ni) 1'b1 |-> !o_alert_integ_fail)
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_alert is a single-cycle pulse per handshake (RT-5-02)
  a_CHK_002: assert property (@(posedge clk_i) disable iff (!rst_ni) o_alert |=> !o_alert)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: No spurious alerts, no more pulses than test writes (RT-4.2-01, RT-8-14, RT-5-06, RT-8-12)
  a_CHK_003: assert property (@(posedge clk_i) disable iff (!rst_ni)
      (o_alert && !flip_now_w) |->
        ((q_cnt + (qual_w ? 1 : 0) - qerr_now_w) >= (a_cnt + 1)) &&
        ((p_valid && p_qual) || qual_w || (age <= 16)))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_alert && !flip_now_w)) hits_CHK_003 <= hits_CHK_003 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
  end
endmodule
