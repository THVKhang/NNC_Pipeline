module nnc_chk_strap #(
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

  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;

  // helper state for CHK-009
  logic        c009_seen_en;   // i_strap_en was 1 at some rising edge since reset release (before current edge)
  logic        c009_prev_valid; // o_straps_valid was 1 at previous edge with rst_ni=1
  logic [31:0] c009_prev_data;

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      c009_seen_en    <= 1'b0;
      c009_prev_valid <= 1'b0;
      c009_prev_data  <= '0;
    end else begin
      if (i_strap_en) c009_seen_en <= 1'b1;
      c009_prev_valid <= o_straps_valid;
      c009_prev_data  <= o_straps_data;
    end
  end

  wire c009_quiet = !c009_seen_en && !i_strap_en;
  wire c009_ante  = (GpioAsHwStrapsEn == 1) && (c009_quiet || c009_prev_valid);

  // CHK-009: Strap outputs: invalid before the trigger, frozen after sampling (GP-10-12, GP-10-13, GP-T6.2-02, GP-T3.2.3.1-02)
  a_CHK_009: assert property (@(posedge clk_i) disable iff (!rst_ni)
    c009_ante |->
      ((!c009_quiet || !o_straps_valid) &&
       (!c009_prev_valid || (o_straps_valid && (o_straps_data == c009_prev_data)))))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (c009_ante)) hits_CHK_009 <= hits_CHK_009 + 1;

  final begin
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
  end
endmodule
