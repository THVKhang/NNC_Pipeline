module nnc_chk_gpio #(
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

  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;

  // helper decode of the current A request
  logic a_hs, d_hs, a_wr, a_rel;
  assign a_hs = i_a_valid && o_a_ready;
  assign d_hs = o_d_valid && i_d_ready;
  assign a_wr = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);
  assign a_rel = a_wr && (
      (i_a_address == 32'h14) || (i_a_address == 32'h18) || (i_a_address == 32'h1C) ||
      (i_a_address == 32'h20) || (i_a_address == 32'h24) || (i_a_address == 32'h28) ||
      ((i_a_address >= 32'h100) && (i_a_address <= 32'h17C) && (i_a_address[1:0] == 2'b00)) ||
      ((i_a_address >= 32'h200) && (i_a_address <= 32'h2F8) && (i_a_address[2:0] == 3'b000)));

  logic        pend_v, pend_wr;
  logic [31:0] pend_addr, pend_data;
  logic [31:0] shadow_out, shadow_oe;
  logic        chk_active, chk_dis, ok_d1;
  logic        d_wr_ok;
  assign d_wr_ok = d_hs && pend_v && pend_wr && !o_d_error;

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      pend_v     <= 1'b0;
      pend_wr    <= 1'b0;
      pend_addr  <= 32'h0;
      pend_data  <= 32'h0;
      shadow_out <= 32'h0;
      shadow_oe  <= 32'h0;
      chk_active <= 1'b1;
      chk_dis    <= 1'b0;
      ok_d1      <= 1'b0;
    end else begin
      ok_d1 <= d_hs && pend_v && pend_wr;
      if (ok_d1) chk_active <= 1'b1;
      if (d_hs) pend_v <= 1'b0;
      if (d_wr_ok) begin
        case (pend_addr)
          32'h14: shadow_out <= pend_data;
          32'h18: for (int i = 0; i < 16; i++) if (pend_data[16+i]) shadow_out[i] <= pend_data[i];
          32'h1C: for (int i = 0; i < 16; i++) if (pend_data[16+i]) shadow_out[16+i] <= pend_data[i];
          32'h20: shadow_oe <= pend_data;
          32'h24: for (int i = 0; i < 16; i++) if (pend_data[16+i]) shadow_oe[i] <= pend_data[i];
          32'h28: for (int i = 0; i < 16; i++) if (pend_data[16+i]) shadow_oe[16+i] <= pend_data[i];
          default: begin
            if ((pend_addr >= 32'h100) && (pend_addr <= 32'h17C) && (pend_addr[1:0] == 2'b00))
              shadow_out[(pend_addr - 32'h100) >> 2] <= pend_data[0];
            if ((pend_addr >= 32'h200) && (pend_addr <= 32'h2F8) && (pend_addr[2:0] == 3'b000))
              shadow_oe[(pend_addr - 32'h200) >> 3] <= pend_data[0];
          end
        endcase
      end
      if (a_hs) begin
        pend_v    <= 1'b1;
        pend_wr   <= a_rel;
        pend_addr <= i_a_address;
        pend_data <= i_a_data;
        if (a_rel) chk_active <= 1'b0;
        if (i_a_intg_flip) chk_dis <= 1'b1;
      end
    end
  end

  logic chk004_ante;
  assign chk004_ante = chk_active && !chk_dis && !(a_hs && (a_rel || i_a_intg_flip));

  // CHK-004: o_gpio / o_gpio_en follow the DATA_OUT / DATA_OE shadow model (GP-3-06, GP-3-07, GP-10-38, GP-6-01, GP-10-03, GP-T3.2.1-06)
  a_CHK_004: assert property (@(posedge clk_i) disable iff (!rst_ni) chk004_ante |-> (o_gpio == shadow_out && o_gpio_en == shadow_oe))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (chk004_ante)) hits_CHK_004 <= hits_CHK_004 + 1;

  final begin
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
  end
endmodule
