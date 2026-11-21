// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module ot_rv_timer_nnc (
  input  logic                        clk_i,
  input  logic                        rst_ni,
  input  logic                        i_a_valid,
  output logic                        o_a_ready,
  input  logic [2:0]                  i_a_opcode,
  input  logic [2:0]                  i_a_param,
  input  logic [1:0]                  i_a_size,
  input  logic [7:0]                  i_a_source,
  input  logic [31:0]                 i_a_address,
  input  logic [3:0]                  i_a_mask,
  input  logic [31:0]                 i_a_data,
  input  logic                        i_a_instr,
  input  logic                        i_a_intg_flip,
  output logic                        o_d_valid,
  input  logic                        i_d_ready,
  output logic [2:0]                  o_d_opcode,
  output logic [2:0]                  o_d_param,
  output logic [1:0]                  o_d_size,
  output logic [7:0]                  o_d_source,
  output logic                        o_d_sink,
  output logic [31:0]                 o_d_data,
  output logic                        o_d_error,
  output logic                        o_d_intg_err,
  output logic                        o_alert,
  output logic                        o_alert_integ_fail,
  output logic                        o_intr_timer_expired
);
  assign o_a_ready = '0;
  assign o_d_valid = '0;
  assign o_d_opcode = '0;
  assign o_d_param = '0;
  assign o_d_size = '0;
  assign o_d_source = '0;
  assign o_d_sink = '0;
  assign o_d_data = '0;
  assign o_d_error = '0;
  assign o_d_intg_err = '0;
  assign o_alert = '0;
  assign o_alert_integ_fail = '0;
  assign o_intr_timer_expired = '0;
endmodule
