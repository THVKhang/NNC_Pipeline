module nnc_chk_integ #(
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

  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;

  // CHK-005: D-channel response integrity never fails (GP-4.3-01, GP-4.3-02, GP-3-03, GP-10-33, TL-T3.1.3.3-02)
  a_CHK_005: assert property (@(posedge clk_i) disable iff (!rst_ni) 1'b1 |-> (o_d_intg_err == 1'b0))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (1'b1)) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
