// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env (
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

  // ---------------------------------------------------------------------------
  // Helper state (driven from interface signals only, reset with the DUT reset)
  // ---------------------------------------------------------------------------
  reg f_past_valid = 1'b0;
  always @(posedge clk_i) f_past_valid <= 1'b1;

  // Registered copy of rst_ni: rst_ni && !f_rst_q marks the first cycle after reset release.
  reg f_rst_q = 1'b0;
  always @(posedge clk_i) f_rst_q <= rst_ni;

  wire f_a_hs  = i_a_valid && o_a_ready;
  wire f_d_hs  = o_d_valid && i_d_ready;
  wire f_a_put = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);

  // A legal write to CTRL that includes byte lane 0 (full word or a sub-word write to byte 0),
  // which therefore updates CTRL.active_0 (RT-8-22, RT-8-23).
  wire f_a_ctrl_wr = f_a_put && (i_a_address == 32'h0000_0004) && i_a_mask[0] &&
                     !i_a_intg_flip && !i_a_instr &&
                     ( ((i_a_size == 2'd2) && ((i_a_opcode == 3'd1) || (i_a_mask == 4'hF))) ||
                       ((i_a_size == 2'd1) && (i_a_mask[3:2] == 2'b00) &&
                        ((i_a_opcode == 3'd1) || (i_a_mask == 4'b0011))) ||
                       ((i_a_size == 2'd0) && (i_a_mask == 4'b0001)) );

  // Any write request to the CTRL word (conservative, used only for the "write in flight" tracking).
  wire f_a_ctrl_any = f_a_put && (i_a_address[31:2] == 30'd1);

  // Any write request to the CFG0 / TIMER_V_LOWER0 / TIMER_V_UPPER0 words (0x10C, 0x110, 0x114).
  // RT-8-03 states that tests write these registers only while CTRL.active_0 = 0; the spec does not
  // state that every sub-word / partial-mask shape is without effect (RT-8-21 covers byte writes
  // only), so every write request to these words is treated as a write to them.
  wire f_a_cfg_wr = f_a_put && ((i_a_address[31:2] == 30'h43) ||
                                (i_a_address[31:2] == 30'h44) ||
                                (i_a_address[31:2] == 30'h45));

  // A write to ALERT_TEST (offset 0x0, aligned, word size, good integrity, data access) that
  // reaches both byte lane 0 (fatal_fault) and byte lane 3 (regwen): PutFullData with full mask,
  // or PutPartialData whose mask includes lanes 0 and 3.
  wire f_a_at_both = f_a_put && (i_a_address == 32'h0000_0000) && (i_a_size == 2'd2) &&
                     !i_a_intg_flip && !i_a_instr &&
                     ( ((i_a_opcode == 3'd0) && (i_a_mask == 4'hF)) ||
                       ((i_a_opcode == 3'd1) && i_a_mask[0] && i_a_mask[3]) );

  // Outstanding a_source identifiers (request accepted, response not yet taken).
  // Pending responses are discarded by reset (RT-8-31).
  reg [255:0] f_outst = 256'd0;
  // Outstanding writes to CTRL (accepted, response not yet taken).
  reg [255:0] f_ctrl_pend = 256'd0;
  // Outstanding writes to CFG0 / TIMER_V_* (accepted, response not yet taken).
  reg [255:0] f_cfg_pend = 256'd0;
  always @(posedge clk_i) begin
    if (!rst_ni) begin
      f_outst     <= 256'd0;
      f_ctrl_pend <= 256'd0;
      f_cfg_pend  <= 256'd0;
    end else begin
      if (f_d_hs) begin
        f_outst[o_d_source]     <= 1'b0;
        f_ctrl_pend[o_d_source] <= 1'b0;
        f_cfg_pend[o_d_source]  <= 1'b0;
      end
      if (f_a_hs) begin
        f_outst[i_a_source] <= 1'b1;
        if (f_a_ctrl_any) f_ctrl_pend[i_a_source] <= 1'b1;
        if (f_a_cfg_wr)   f_cfg_pend[i_a_source]  <= 1'b1;
      end
    end
  end

  // Shadow of CTRL.active_0 as programmed by the test bench (reset value 0).
  // Updated on every accepted legal write to CTRL that covers byte lane 0 (full word or byte 0).
  reg f_active = 1'b0;
  always @(posedge clk_i) begin
    if (!rst_ni)
      f_active <= 1'b0;
    else if (f_a_hs && f_a_ctrl_wr)
      f_active <= i_a_data[0];
  end

  // CTRL.active_0 may be 1: programmed active, or a CTRL write has not completed yet.
  wire f_maybe_active = f_active || (|f_ctrl_pend);

  // ENV-01: no request is issued while reset is asserted (RT-8-29, RT-2-03, CP-T1.5.2-04)
  always @(*) if (!rst_ni) assume (!i_a_valid);

  // ENV-09: no request in the first cycle after reset release (RT-8-29)
  always @(*) if (rst_ni && !f_rst_q) assume (!i_a_valid);

  // ENV-02: TL-UL host rule - once a_valid is raised it stays raised and all A-channel
  //         signals (including a_user: instr type and integrity) stay stable until a_ready (RT-4.1-04, RT-4.1-01)
  always @(posedge clk_i)
    if (f_past_valid && rst_ni && $past(rst_ni) && $past(i_a_valid) && !$past(o_a_ready)) begin
      assume (i_a_valid);
      assume ($stable(i_a_opcode));
      assume ($stable(i_a_param));
      assume ($stable(i_a_size));
      assume ($stable(i_a_source));
      assume ($stable(i_a_address));
      assume ($stable(i_a_mask));
      assume ($stable(i_a_data));
      assume ($stable(i_a_instr));
      assume ($stable(i_a_intg_flip));
    end

  // ENV-03: a_param is driven to 0 (RT-8-34)
  always @(*) if (i_a_valid) assume (i_a_param == 3'd0);

  // ENV-04: requests at offset 0x200 and above are not used (RT-8-20)
  always @(*) if (i_a_valid) assume (i_a_address < 32'h0000_0200);

  // ENV-05: a write (PutFullData / PutPartialData) with i_a_instr = 1 is not used (RT-8-18)
  always @(*) if (i_a_valid && i_a_instr) assume (!f_a_put);

  // ENV-06: distinct a_source per outstanding request (RT-8-25, TL-T3.1.3.2-01)
  always @(*)
    if (rst_ni && i_a_valid)
      assume (!f_outst[i_a_source] || (f_d_hs && (o_d_source == i_a_source)));

  // ENV-07: the combined ALERT_TEST write (fatal_fault = 1 together with regwen = 0) is not used;
  //         tests write 0x8000_0001 instead (RT-8-15). Restricted only for writes that reach both
  //         byte lane 0 and byte lane 3 (full-mask PutFullData or PutPartialData with mask[0] and
  //         mask[3]); byte / misaligned / malformed / integrity-flipped writes stay legal error
  //         stimulus (RT-8-21, RT-4.1-05)
  always @(*)
    if (i_a_valid && f_a_at_both)
      assume (!(i_a_data[0] && !i_a_data[31]));

  // ENV-08: CFG0 and TIMER_V_LOWER0/UPPER0 are written (any write request to these words) only
  //         while CTRL.active_0 = 0, i.e. not while the timer is (or may still be) active,
  //         including a CTRL write still in flight (RT-8-03, RT-T4.1-01, RT-T4.1-02, RT-8-33)
  always @(*)
    if (i_a_valid && f_a_cfg_wr)
      assume (!f_maybe_active);

  // ENV-10: the timer is not activated while a CFG0 / TIMER_V_* write is still in flight, so those
  //         writes complete while CTRL.active_0 = 0 (RT-8-03, RT-T4.1-02)
  always @(*)
    if (i_a_valid && f_a_ctrl_wr && i_a_data[0])
      assume (!(|f_cfg_pend));
endmodule
