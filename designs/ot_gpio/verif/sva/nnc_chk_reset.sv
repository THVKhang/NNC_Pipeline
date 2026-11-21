module nnc_chk_reset #(
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

  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;

  // NNC verification fix (fix-verif, triage B): D-016 binds the outputs 'while rst_ni = 0', i.e. once reset has been
  // asserted; no document defines a power-on state before the first assertion (time 0). rst_seen_q is set at the
  // first falling edge of rst_ni or at the first rising clock edge processed with rst_ni=0 and is never cleared, so
  // every later edge with rst_ni=0 is checked, including the first clock edge after an asynchronous assertion.
  logic rst_seen_q = 1'b0;
  always_ff @(posedge clk_i or negedge rst_ni) if (!rst_ni) rst_seen_q <= 1'b1;
  wire chk008_ante = rst_seen_q && !rst_ni;

  // CHK-008: Outputs held at zero during reset (GP-10-31, GP-10-03, GP-2-06)
  a_CHK_008: assert property (@(posedge clk_i) chk008_ante |-> (o_d_valid == 1'b0 && o_alert == 1'b0 && o_alert_integ_fail == 1'b0 && o_intr_gpio == 32'h0 && o_gpio == 32'h0 && o_gpio_en == 32'h0))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t o_d_valid=%0b o_alert=%0b o_alert_integ_fail=%0b o_intr_gpio=%h o_gpio=%h o_gpio_en=%h", $time, o_d_valid, o_alert, o_alert_integ_fail, o_intr_gpio, o_gpio, o_gpio_en); end
  // NNC verification fix (fix-verif, triage B): the hit condition was '!(!rst_ni) && (!rst_ni)' (never true); count the edges where the check is active.
  always_ff @(posedge clk_i) if (chk008_ante) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-008: same check on the falling clock edge (GP-10-31, GP-10-03, GP-2-06)
  a_CHK_008_neg: assert property (@(negedge clk_i) chk008_ante |-> (o_d_valid == 1'b0 && o_alert == 1'b0 && o_alert_integ_fail == 1'b0 && o_intr_gpio == 32'h0 && o_gpio == 32'h0 && o_gpio_en == 32'h0))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t o_d_valid=%0b o_alert=%0b o_alert_integ_fail=%0b o_intr_gpio=%h o_gpio=%h o_gpio_en=%h", $time, o_d_valid, o_alert, o_alert_integ_fail, o_intr_gpio, o_gpio, o_gpio_en); end

  final begin
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
  end
endmodule
