module nnc_chk_timing #(
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

  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;

  // Helper: all outputs sampled at the falling clock edge, with reset state at that edge
  logic [158:0] outs_now;
  logic [158:0] outs_neg = '0;
  logic         rst_neg  = 1'b0;

  assign outs_now = {o_a_ready, o_d_valid, o_d_opcode, o_d_param, o_d_size, o_d_source,
                     o_d_sink, o_d_data, o_d_error, o_d_intg_err, o_alert, o_alert_integ_fail,
                     o_gpio, o_gpio_en, o_intr_gpio, o_straps_valid, o_straps_data};

  always_ff @(negedge clk_i) begin
    outs_neg <= outs_now;
    rst_neg  <= rst_ni;
  end

  logic rst_prev = 1'b0;
  always_ff @(posedge clk_i) rst_prev <= rst_ni;

  // CHK-010: Outputs change only at rising clock edges (GP-2-02)
  a_CHK_010: assert property (@(posedge clk_i) disable iff (!rst_ni) (rst_neg && rst_prev) |-> (outs_now == outs_neg))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_neg && rst_prev)) hits_CHK_010 <= hits_CHK_010 + 1;

  final begin
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
  end
endmodule
