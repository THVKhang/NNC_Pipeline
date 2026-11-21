module nnc_chk_tbhost (
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

  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;

  // helper state (driven only from interface signals)
  logic         rst_q;
  logic         stall_q;
  logic [255:0] outst_q;
  logic [255:0] ctrl_pend_q;
  logic [255:0] ctrl_upd_q;
  logic [255:0] ctrl_val_q;
  logic         active_model_q;

  wire a_hs       = i_a_valid && o_a_ready;
  wire d_hs       = o_d_valid && i_d_ready;
  wire a_is_wr    = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);
  wire a_ctrl_wr  = a_is_wr && (i_a_address[31:2] == 30'h1);
  wire d_known    = outst_q[o_d_source];
  wire src_busy   = outst_q[i_a_source] &&
                    !(d_hs && (o_d_source == i_a_source));
  wire cfg_wr     = a_is_wr && ((i_a_address[31:2] == 30'h43) ||
                                (i_a_address[31:2] == 30'h44) ||
                                (i_a_address[31:2] == 30'h45));
  wire bad_mask   = (i_a_mask == 4'b0101) || (i_a_mask == 4'b1001) ||
                    (i_a_mask == 4'b1010) || (i_a_mask == 4'b1011) ||
                    (i_a_mask == 4'b1101);

  always_ff @(posedge clk_i) begin
    rst_q <= rst_ni;
    if (!rst_ni) begin
      stall_q        <= 1'b0;
      outst_q        <= '0;
      ctrl_pend_q    <= '0;
      ctrl_upd_q     <= '0;
      ctrl_val_q     <= '0;
      active_model_q <= 1'b0;
    end else begin
      stall_q <= i_a_valid && !o_a_ready;
      if (d_hs && d_known) begin
        outst_q[o_d_source]     <= 1'b0;
        ctrl_pend_q[o_d_source] <= 1'b0;
        if (ctrl_upd_q[o_d_source] && !o_d_error)
          active_model_q <= ctrl_val_q[o_d_source];
      end
      if (a_hs) begin
        outst_q[i_a_source]     <= 1'b1;
        ctrl_pend_q[i_a_source] <= a_ctrl_wr;
        ctrl_upd_q[i_a_source]  <= a_ctrl_wr && i_a_mask[0];
        ctrl_val_q[i_a_source]  <= i_a_data[0];
      end
    end
  end

  // CHK-008: Test-bench host obligations (stimulus self-check) (RT-4.1-04, RT-8-29, RT-8-34, RT-8-20, RT-8-18, RT-8-25, RT-8-03, RT-8-15, TL-T3.1.3.4-02)
  a_CHK_008: assert property (@(posedge clk_i)
    (!rst_ni || !rst_q || stall_q || i_a_valid) |->
      ( (!rst_ni ? !i_a_valid : 1'b1)
        && ((rst_ni && !rst_q) ? !i_a_valid : 1'b1)
        && (stall_q ? (i_a_valid
                       && i_a_opcode  == $past(i_a_opcode)
                       && i_a_param   == $past(i_a_param)
                       && i_a_size    == $past(i_a_size)
                       && i_a_source  == $past(i_a_source)
                       && i_a_address == $past(i_a_address)
                       && i_a_mask    == $past(i_a_mask)
                       && i_a_data    == $past(i_a_data)
                       && i_a_instr   == $past(i_a_instr)
                       && i_a_intg_flip == $past(i_a_intg_flip)) : 1'b1)
        && (i_a_valid ? (i_a_param == 3'd0
                         && i_a_address < 32'h200
                         && !bad_mask
                         && !(i_a_instr && a_is_wr)
                         && !src_busy
                         && !(a_is_wr && i_a_address[31:2] == 30'h0 && i_a_data == 32'h1)
                         && !(cfg_wr && (active_model_q || (|ctrl_pend_q)))) : 1'b1)
      ))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (!rst_ni || !rst_q || stall_q || i_a_valid)) hits_CHK_008 <= hits_CHK_008 + 1;

  final begin
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
  end
endmodule
