module nnc_chk_tlul (
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

  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  // ---------------- helper state: outstanding request table ----------------
  logic [255:0] out_v;
  logic [2:0]   out_op    [256];
  logic [1:0]   out_size  [256];
  logic [31:0]  out_addr  [256];
  logic [3:0]   out_mask  [256];
  logic         out_instr [256];
  logic         out_flip  [256];
  logic         dis_q;

  wire acc    = i_a_valid && o_a_ready;
  wire dbeat  = o_d_valid && i_d_ready;
  wire dis_now = dis_q || (acc && i_a_intg_flip);

  wire m_tbl  = out_v[o_d_source];
  wire m_now  = acc && (i_a_source == o_d_source) && !m_tbl;
  wire matched = m_tbl || m_now;

  wire [2:0]  r_op    = m_tbl ? out_op[o_d_source]    : i_a_opcode;
  wire [1:0]  r_size  = m_tbl ? out_size[o_d_source]  : i_a_size;
  wire [31:0] r_addr  = m_tbl ? out_addr[o_d_source]  : i_a_address;
  wire [3:0]  r_mask  = m_tbl ? out_mask[o_d_source]  : i_a_mask;
  wire        r_instr = m_tbl ? out_instr[o_d_source] : i_a_instr;
  wire        r_flip  = m_tbl ? out_flip[o_d_source]  : i_a_intg_flip;

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      out_v <= '0;
      dis_q <= 1'b0;
    end else begin
      if (dbeat && m_tbl) out_v[o_d_source] <= 1'b0;
      if (acc) begin
        out_v[i_a_source]     <= 1'b1;
        out_op[i_a_source]    <= i_a_opcode;
        out_size[i_a_source]  <= i_a_size;
        out_addr[i_a_source]  <= i_a_address;
        out_mask[i_a_source]  <= i_a_mask;
        out_instr[i_a_source] <= i_a_instr;
        out_flip[i_a_source]  <= i_a_intg_flip;
      end
      if (acc && i_a_intg_flip) dis_q <= 1'b1;
    end
  end

  // ---------------- classification of the matched request ----------------
  wire [7:0] nb_ones = (8'd1 << (4'd1 << r_size)) - 8'd1;
  wire [3:0] act     = 4'(nb_ones << r_addr[1:0]);
  wire [31:0] r_word = {r_addr[31:2], 2'b00};
  wire op_def   = (r_op == 3'd0) || (r_op == 3'd1) || (r_op == 3'd4);
  wire op_put   = (r_op == 3'd0) || (r_op == 3'd1);
  wire misal    = (r_size == 2'd1) ? r_addr[0] :
                  (r_size == 2'd2) ? (r_addr[1:0] != 2'b00) : 1'b0;
  wire mapped   = (r_word == 32'h000) || (r_word == 32'h004) || (r_word == 32'h100) ||
                  (r_word == 32'h104) || (r_word == 32'h108) || (r_word == 32'h10C) ||
                  (r_word == 32'h110) || (r_word == 32'h114) || (r_word == 32'h118) ||
                  (r_word == 32'h11C);
  wire wr_ok4   = (r_word == 32'h004) || (r_word == 32'h100) || (r_word == 32'h104) ||
                  (r_word == 32'h108);
  wire e_a = !op_def;
  wire e_b = (r_size == 2'd3);
  wire e_c = misal;
  wire e_d = ((r_mask & ~act) != 4'd0);
  wire e_e = (r_op == 3'd0) && ((r_mask & act) != act);
  wire e_f = !mapped;
  wire e_g = op_put && (r_size == 2'd0) && (r_mask == 4'b0001) && mapped && !wr_ok4;
  wire err_req = e_a || e_b || e_c || e_d || e_e || e_f || e_g;
  wire noerr_req = !err_req && (
        (op_def && r_size == 2'd2 && r_mask == 4'hF) ||
        (r_op == 3'd1 && r_size == 2'd0 && r_mask == 4'b0001 && wr_ok4) ||
        (r_op == 3'd4 && r_size <= 2'd1 && r_mask == act));

  wire ante_009 = dbeat && !dis_now;
  wire ante_010 = dbeat && matched && !r_flip && !dis_now;
  wire ante_011 = dbeat && matched && !r_flip && !dis_now && !r_instr && (r_addr < 32'h200);
  wire ante_012 = o_d_valid && !i_d_ready && !dis_now;

  // CHK-009: Every D-channel beat matches exactly one outstanding request (TL-T3.1.3.2.3-01, TL-T2.2-03, RT-4.1-01, TL-T3.1.3.5-08)
  a_CHK_009: assert property (@(posedge clk_i) disable iff (!rst_ni) ante_009 |-> matched)
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (ante_009)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: Response opcode and size echo (RT-8-27, RT-3-04, RT-3-01, TL-T3.1.3.4-07, RT-4.1-01)
  a_CHK_010: assert property (@(posedge clk_i) disable iff (!rst_ni) ante_010 |->
      ((r_op == 3'd4) ? (o_d_opcode == 3'd1 && o_d_size == r_size) :
       op_put         ? (o_d_opcode == 3'd0 && o_d_size == r_size) :
                        o_d_error))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (ante_010)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: d_error value for classified requests (RT-4.1-06, RT-8-19, RT-8-21, RT-8-22, RT-8-23, RT-8-28, TL-T3.1.3.4-06, TL-T3.1.3.5-01, TL-T3.1.3.5-02, TL-T3.1.3.5-03, TL-T3.1.3.5-04, TL-T3.1.3.5-05, RG-T1.4.1-04, RG-T1.4.1-05, RG-T1.4.1-07, RT-1-02)
  a_CHK_011: assert property (@(posedge clk_i) disable iff (!rst_ni) ante_011 |->
      (err_req ? (o_d_error == 1'b1) : (noerr_req ? (o_d_error == 1'b0) : 1'b1)))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (ante_011)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: D channel holds under back-pressure (RT-4.1-01)
  a_CHK_012: assert property (@(posedge clk_i) disable iff (!rst_ni) ante_012 |=>
      (o_d_valid && $stable(o_d_opcode) && $stable(o_d_param) && $stable(o_d_size) &&
       $stable(o_d_source) && $stable(o_d_sink) && $stable(o_d_data) && $stable(o_d_error)))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (ante_012)) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: Response integrity never fails (RT-4.3-01, RT-4.3-02, RT-8-32, RT-3-05, RT-4.2-01)
  a_CHK_013: assert property (@(posedge clk_i) disable iff (!rst_ni) 1'b1 |-> (o_d_intg_err == 1'b0))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge clk_i) if (!(!rst_ni) && (1'b1)) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
