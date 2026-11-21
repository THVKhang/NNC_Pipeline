module nnc_chk_reset (
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

  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;

  // CHK-006: Outputs inactive during reset (RT-8-30, RT-2-04)
  // NNC verification fix (fix-verif, triage B): diagnostic only - report the sampled rst_ni and the four
  // checked outputs on failure (D-016 / CHK-006); the property itself is unchanged.
  a_CHK_006: assert property (@(posedge clk_i) !rst_ni |-> (o_d_valid == 1'b0 && o_alert == 1'b0 && o_alert_integ_fail == 1'b0 && o_intr_timer_expired == 1'b0))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t rst_ni=%b o_d_valid=%b o_alert=%b o_alert_integ_fail=%b o_intr_timer_expired=%b", $time, $sampled(rst_ni), $sampled(o_d_valid), $sampled(o_alert), $sampled(o_alert_integ_fail), $sampled(o_intr_timer_expired)); end
  always_ff @(posedge clk_i) if (!rst_ni) hits_CHK_006 <= hits_CHK_006 + 1;

  // helpers for CHK-007
  logic [55:0] chk007_outs;
  assign chk007_outs = {o_a_ready, o_d_valid, o_d_opcode, o_d_param, o_d_size, o_d_source,
                        o_d_sink, o_d_data, o_d_error, o_d_intg_err, o_alert,
                        o_alert_integ_fail, o_intr_timer_expired};
  logic        chk007_rst_prev = 1'b0;
  logic        chk007_snap_ok  = 1'b0;
  logic [55:0] chk007_snap     = '0;

  always_ff @(posedge clk_i) chk007_rst_prev <= rst_ni;

  // snapshot at the falling edge; valid only if reset was high at the preceding rising edge and still is
  always_ff @(negedge clk_i) begin
    chk007_snap    <= chk007_outs;
    chk007_snap_ok <= chk007_rst_prev && rst_ni;
  end

  // CHK-007: Outputs change only at rising clock edges (RT-2-02)
  a_CHK_007: assert property (@(posedge clk_i) disable iff (!rst_ni) chk007_snap_ok |-> (chk007_outs == chk007_snap))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (chk007_snap_ok)) hits_CHK_007 <= hits_CHK_007 + 1;

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
  end
endmodule
