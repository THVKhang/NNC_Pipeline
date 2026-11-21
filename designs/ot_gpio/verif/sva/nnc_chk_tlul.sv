module nnc_chk_tlul #(
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

  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  // helper signals for CHK-013
  logic a_hs, d_hs, chk13_dis_q, chk13_dis;
  int unsigned pend_cnt [256];
  logic [2:0] pend_op [256];
  logic [1:0] pend_sz [256];

  assign a_hs = rst_ni && i_a_valid && o_a_ready;
  assign d_hs = rst_ni && o_d_valid && i_d_ready;
  assign chk13_dis = chk13_dis_q || (a_hs && i_a_intg_flip);

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      chk13_dis_q <= 1'b0;
      for (int k = 0; k < 256; k++) begin
        pend_cnt[k] = 0;
        pend_op[k]  = 3'd0;
        pend_sz[k]  = 2'd0;
      end
    end else begin
      if (a_hs && i_a_intg_flip) chk13_dis_q <= 1'b1;
      if (d_hs && (pend_cnt[o_d_source] != 0))
        pend_cnt[o_d_source] = pend_cnt[o_d_source] - 1;
      if (a_hs) begin
        if (pend_cnt[i_a_source] == 0) begin
          pend_op[i_a_source] = i_a_opcode;
          pend_sz[i_a_source] = i_a_size;
        end
        pend_cnt[i_a_source] = pend_cnt[i_a_source] + 1;
      end
    end
  end

  wire        chk13_match = (pend_cnt[o_d_source] != 0);
  wire [2:0]  chk13_op    = pend_op[o_d_source];
  wire [1:0]  chk13_sz    = pend_sz[o_d_source];
  wire        chk13_ok    = chk13_match &&
                            ((chk13_op == 3'd4) ? (o_d_opcode == 3'd1 && o_d_size == chk13_sz) :
                             (chk13_op == 3'd0 || chk13_op == 3'd1) ? (o_d_opcode == 3'd0 && o_d_size == chk13_sz) :
                             (o_d_error == 1'b1));

  // CHK-012: D channel held stable under back-pressure (GP-4.1-01)
  a_CHK_012: assert property (@(posedge clk_i) disable iff (!rst_ni)
    (o_d_valid && !i_d_ready) |=>
      (o_d_valid && $stable(o_d_opcode) && $stable(o_d_param) && $stable(o_d_size) &&
       $stable(o_d_source) && $stable(o_d_sink) && $stable(o_d_data) && $stable(o_d_error)))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_d_valid && !i_d_ready)) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: Response matches an outstanding request (TL-T3.1.3.2.3-01, GP-10-27, TL-T2.2-03, TL-T3.1.3.5-08, GP-10-28, GP-10-32, GP-4.1-01)
  a_CHK_013: assert property (@(posedge clk_i) disable iff (!rst_ni)
    (o_d_valid && i_d_ready && !chk13_dis) |-> chk13_ok)
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (o_d_valid && i_d_ready && !chk13_dis)) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
