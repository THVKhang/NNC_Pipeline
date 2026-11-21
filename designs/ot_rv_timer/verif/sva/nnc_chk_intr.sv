module nnc_chk_intr (
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

  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;

  // Helper model: queue of accepted requests (in order), IE model, flip-disable
  localparam int QW = 3;
  localparam int QD = (1 << QW);

  logic [QD-1:0] q_w100 = '0;  // write to 0x100 (any)
  logic [QD-1:0] q_upd  = '0;  // write that updates ie on its D beat
  logic [QD-1:0] q_unk  = '0;  // write to 0x100 of a kind whose effect on IE_0 is not modelled
  logic [QD-1:0] q_d0   = '0;  // data[0] of request
  logic [QD-1:0] q_clr  = '0;  // clearing write kind
  logic [QW-1:0] wp = '0;
  logic [QW-1:0] rp = '0;
  int unsigned cnt = 0;
  int unsigned c100 = 0;
  int unsigned cclr = 0;
  logic ie = 1'b0;
  // NNC verification fix (fix-verif, triage B): ie_unk=1 means an error-free write to 0x100 that is not
  // one of the modelled kinds has completed, so IE_0 is not known to the model (D-013: "other sub-word
  // cases are not checked").
  logic ie_unk = 1'b0;
  logic seen_flip = 1'b0;
  logic prev_rst_ok = 1'b0;
  logic prev_intr = 1'b0;
  logic dw1 = 1'b0, dw2 = 1'b0;
  logic [6:1] dcs = '0;

  wire acc    = i_a_valid && o_a_ready;
  wire dbeat  = o_d_valid && i_d_ready;
  wire is_wr  = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);
  wire n_flip = !i_a_intg_flip;
  wire dis    = seen_flip || (acc && i_a_intg_flip);

  wire a_w100 = is_wr && (i_a_address == 32'h100);
  // NNC verification fix (fix-verif, triage B): D-013 says "a byte write (a_size 0, mask 0001, offset
  // aligned) to byte 0 of CTRL, INTR_ENABLE0, INTR_STATE0 or INTR_TEST0 completes with d_error = 0 and
  // has the effect of the write" and does not restrict the opcode. So a PutFullData byte write to
  // INTR_ENABLE0 updates IE_0 just as a PutPartialData one does. Before, only opcode 1 was modelled,
  // which left ie=0 after an error-free PutFullData byte write. The CHK-004 assertion is unchanged.
  // The ie model is still updated only when the D beat has d_error=0.
  wire a_upd  = n_flip && (i_a_address == 32'h100) &&
                ( (is_wr && i_a_size == 2'd2 && i_a_mask == 4'b1111) ||
                  (is_wr && i_a_size == 2'd0 && i_a_mask == 4'b0001) );
  // NNC verification fix (fix-verif, triage B): any other write (intg_flip=0) to 0x100, e.g. an aligned
  // half-word or a partial mask, is legal stimulus (INT-TL-003). By the register tool
  // (opentitan_register_tool.md:689-695) it may succeed and change IE_0 (width 1), but D-013 leaves it
  // unchecked. Its error-free D beat makes ie unknown until the next modelled write or reset.
  wire a_unk  = n_flip && a_w100 && !a_upd;
  wire a_clr  = n_flip && is_wr && (
                  ((i_a_address == 32'h100) && !i_a_data[0] && i_a_mask[0]) ||
                  ((i_a_address == 32'h104) &&  i_a_data[0] && i_a_mask[0]) ||
                  (i_a_address == 32'h118) ||
                  (i_a_address == 32'h11C));

  wire pop   = dbeat && (cnt != 0);
  wire push  = acc && (cnt < QD);
  wire dw0   = pop && q_w100[rp];
  wire dc0   = pop && q_clr[rp];

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      q_w100 <= '0; q_upd <= '0; q_unk <= '0; q_d0 <= '0; q_clr <= '0;
      wp <= '0; rp <= '0; cnt <= 0; c100 <= 0; cclr <= 0;
      ie <= 1'b0; ie_unk <= 1'b0; seen_flip <= 1'b0;
      prev_rst_ok <= 1'b0; prev_intr <= 1'b0;
      dw1 <= 1'b0; dw2 <= 1'b0; dcs <= '0;
    end else begin
      prev_rst_ok <= 1'b1;
      prev_intr <= o_intr_timer_expired;
      dw1 <= dw0; dw2 <= dw1;
      dcs <= {dcs[5:1], dc0};
      if (acc && i_a_intg_flip) seen_flip <= 1'b1;
      if (push) begin
        q_w100[wp] <= a_w100;
        q_upd[wp]  <= a_upd;
        q_unk[wp]  <= a_unk;
        q_d0[wp]   <= i_a_data[0];
        q_clr[wp]  <= a_clr;
        wp <= wp + 1'b1;
      end
      if (pop) begin
        rp <= rp + 1'b1;
        // NNC verification fix (fix-verif, triage B): a modelled error-free write sets ie and makes it
        // known again; an unmodelled error-free write to 0x100 makes it unknown.
        if (q_upd[rp] && !o_d_error) begin
          ie     <= q_d0[rp];
          ie_unk <= 1'b0;
        end
        if (q_unk[rp] && !o_d_error) ie_unk <= 1'b1;
      end
      cnt  <= cnt  + (push ? 1 : 0) - (pop ? 1 : 0);
      c100 <= c100 + ((push && a_w100) ? 1 : 0) - ((pop && q_w100[rp]) ? 1 : 0);
      cclr <= cclr + ((push && a_clr) ? 1 : 0) - ((pop && q_clr[rp]) ? 1 : 0);
    end
  end

  // CHK-004: Interrupt output masked by INTR_ENABLE0.IE_0 (RT-8-07, CP-T1.8.6-04, RT-T5.4.1-01)
  // NNC verification fix (fix-verif, triage B): not applied while ie_unk=1 (IE_0 set by an unmodelled,
  // error-free write to 0x100 whose effect D-013 leaves unchecked). Otherwise unchanged.
  a_CHK_004: assert property (@(posedge clk_i) disable iff (!rst_ni)
    (rst_ni && !ie && !ie_unk && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2) |-> (o_intr_timer_expired == 1'b0))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_ni && !ie && !ie_unk && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: Latched interrupt falls only after a clearing write or reset (CP-T1.8.6-06, CP-T1.8.5-02, CP-T1.8.5.1-01, CP-T1.8.1-01)
  a_CHK_005: assert property (@(posedge clk_i) disable iff (!rst_ni)
    (rst_ni && prev_rst_ok && prev_intr && !o_intr_timer_expired && !dis) |->
      ((cclr != 0) || (acc && a_clr) || dc0 || (|dcs)))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_ni && prev_rst_ok && prev_intr && !o_intr_timer_expired && !dis)) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
