module nnc_chk_intr #(
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

  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;

  // ---- common helpers: handshakes, pending request tracking, integrity disable
  wire a_hs = i_a_valid && o_a_ready;
  wire d_hs = o_d_valid && i_d_ready;
  wire cur_is_wr = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);
  wire cur_w4 = cur_is_wr && (i_a_address == 32'h4);
  wire cur_w0 = cur_is_wr && (i_a_address == 32'h0);
  wire [31:0] cur_q = cur_w0 ? i_a_data : (cur_w4 ? ~i_a_data : 32'h0);

  logic        pend_valid;
  logic        pend_w4;
  logic [31:0] pend_data;
  logic [31:0] pend_q;
  logic        dis_intg;
  logic [31:0] shadow_en;
  logic        settled;
  logic [31:0] done1_q;
  logic [31:0] done2_q;

  wire        eff_w4   = pend_valid ? pend_w4   : cur_w4;
  wire [31:0] eff_data = pend_valid ? pend_data : i_a_data;
  wire [31:0] eff_q    = pend_valid ? pend_q    : cur_q;
  wire        eff_ok   = pend_valid || a_hs;
  wire        wr_ev    = d_hs && eff_ok && eff_w4 && !o_d_error;
  wire        dis_now  = dis_intg || (a_hs && i_a_intg_flip);
  wire [31:0] dmask    = (d_hs && eff_ok) ? eff_q : 32'h0;

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      pend_valid <= 1'b0;
      pend_w4    <= 1'b0;
      pend_data  <= 32'h0;
      pend_q     <= 32'h0;
      dis_intg   <= 1'b0;
      shadow_en  <= 32'h0;
      settled    <= 1'b1;
      done1_q    <= 32'h0;
      done2_q    <= 32'h0;
    end else begin
      dis_intg <= dis_now;
      if (a_hs && !(d_hs && !pend_valid)) begin
        pend_valid <= 1'b1;
        pend_w4    <= cur_w4;
        pend_data  <= i_a_data;
        pend_q     <= cur_q;
      end else if (d_hs) begin
        pend_valid <= 1'b0;
      end
      if (wr_ev) begin
        shadow_en <= eff_data;
        settled   <= 1'b0;
      end else begin
        settled   <= 1'b1;
      end
      done1_q <= dmask;
      done2_q <= done1_q;
    end
  end

  wire [31:0] qmask_now = (pend_valid ? pend_q : 32'h0) | (a_hs ? cur_q : 32'h0) | done1_q | done2_q;

  // NNC verification fix (fix-verif, triage B): no document says whether a register write takes effect at its
  // A handshake or at its D handshake (D-018 only binds o_intr_gpio outside the 2 cycles after INTR_ENABLE changes).
  // Bits that an outstanding INTR_ENABLE write sets from 0 to 1 are therefore 'in transition' from its A handshake
  // until its D handshake (Ed and Ed+1 stay masked by wr_ev/settled as before). Bits that are 0 in both the old and
  // the new value are still checked on every edge.
  wire [31:0] en_rise_pend = (((a_hs && cur_w4) ? i_a_data : 32'h0) |
                              ((pend_valid && pend_w4) ? pend_data : 32'h0)) & ~shadow_en;
  wire [31:0] chk006_bits  = ~shadow_en & ~en_rise_pend;

  wire chk006_ante = rst_ni && !dis_now && !wr_ev && settled && (chk006_bits != 32'h0);

  // CHK-006: Disabled interrupts never assert o_intr_gpio (GP-10-05, CP-T1.8.4-03, CP-T1.8.6-04)
  a_CHK_006: assert property (@(posedge clk_i) disable iff (!rst_ni) chk006_ante |-> ((o_intr_gpio & chk006_bits) == 32'h0))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (chk006_ante)) hits_CHK_006 <= hits_CHK_006 + 1;

  wire chk007_ante = rst_ni && !dis_now && (o_intr_gpio != 32'h0);

  // CHK-007: Interrupt level is held until software acknowledges it (CP-T1.8.6-06, CP-T1.8.5-01, CP-T1.8.1-01)
  a_CHK_007: assert property (@(posedge clk_i) disable iff (!rst_ni) chk007_ante |=> (dis_now || ((($past(o_intr_gpio) & ~o_intr_gpio) & ~qmask_now) == 32'h0)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (chk007_ante)) hits_CHK_007 <= hits_CHK_007 + 1;

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
  end
endmodule
