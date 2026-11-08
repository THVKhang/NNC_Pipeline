module nnc_chk_cross #(
  parameter int PARA_ADDR_W = 32,
  parameter int PARA_SRC_W = 8,
  parameter int PARA_SRC_ID = 0,
  parameter int PARA_A_USER_W = 1,
  parameter int PARA_D_SINK_W = 1,
  parameter int PARA_D_USER_W = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_ADDR_W)-1:0]    i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [3:0]                  i_apb_pstrb,
  input  logic [31:0]                 i_apb_pwdata,
  input  logic                        o_apb_pready,
  input  logic [31:0]                 o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic                        o_tlul_a_valid,
  input  logic                        i_tlul_a_ready,
  input  logic [2:0]                  o_tlul_a_opcode,
  input  logic [2:0]                  o_tlul_a_param,
  input  logic [1:0]                  o_tlul_a_size,
  input  logic [(PARA_SRC_W)-1:0]     o_tlul_a_source,
  input  logic [(PARA_ADDR_W)-1:0]    o_tlul_a_address,
  input  logic [3:0]                  o_tlul_a_mask,
  input  logic [31:0]                 o_tlul_a_data,
  input  logic [(PARA_A_USER_W)-1:0]  o_tlul_a_user,
  input  logic                        i_tlul_d_valid,
  input  logic                        o_tlul_d_ready,
  input  logic [2:0]                  i_tlul_d_opcode,
  input  logic [(PARA_SRC_W)-1:0]     i_tlul_d_source,
  input  logic [31:0]                 i_tlul_d_data,
  input  logic                        i_tlul_d_error,
  input  logic [2:0]                  i_tlul_d_param,
  input  logic [1:0]                  i_tlul_d_size,
  input  logic [(PARA_D_SINK_W)-1:0]  i_tlul_d_sink,
  input  logic [(PARA_D_USER_W)-1:0]  i_tlul_d_user
);

  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;
  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;

  // ---------------- helper signals (ports only) ----------------
  logic w_legal, w_illegal, w_fire, w_resp, w_counted, w_exp_get, w_err, w_illegal_setup;
  logic [2:0] w_exp_op;
  logic req_open;
  logic pending;
  logic exp_get_r;
  logic prev_rst;
  logic prev_ok;

  assign w_legal   = (i_apb_paddr[1:0] == 2'b00) && (!i_apb_pwrite || (i_apb_pstrb == 4'b1111));
  assign w_illegal = (i_apb_paddr[1:0] != 2'b00) || (i_apb_pwrite && (i_apb_pstrb != 4'b1111));
  assign w_fire    = o_tlul_a_valid && i_tlul_a_ready;
  assign w_resp    = i_tlul_d_valid && o_tlul_d_ready;
  assign w_counted = w_resp && (pending || w_fire);
  assign w_exp_get = pending ? exp_get_r : o_tlul_a_opcode[2];
  assign w_exp_op  = w_exp_get ? 3'b001 : 3'b000;
  assign w_err     = i_tlul_d_error || (i_tlul_d_opcode != w_exp_op) ||
                     (i_tlul_d_source != PARA_SRC_W'(PARA_SRC_ID));
  assign w_illegal_setup = i_apb_psel && !i_apb_penable && w_illegal;

  always_ff @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      req_open  <= 1'b0;
      pending   <= 1'b0;
      exp_get_r <= 1'b0;
    end else begin
      if (w_fire) req_open <= 1'b1;
      else if (o_apb_pready) req_open <= 1'b0;

      if (w_fire && !w_resp) begin
        pending   <= 1'b1;
        exp_get_r <= o_tlul_a_opcode[2];
      end else if (pending && w_resp) begin
        pending <= 1'b0;
      end
    end
  end

  always_ff @(posedge i_clk_core) begin
    prev_rst <= i_rst_n_core;
    prev_ok  <= (w_counted || w_illegal_setup);
  end

  // CHK-006: Legal Setup launches the request from flops in the first Access cycle (BR-3-01, BR-3-02, BR-1.1-02, BR-5.3-01, BR-5.3-02, BR-5.3-04, BR-5.1-02, BR-10.1-01, BR-10.3-03, BR-15.3-08, BR-15.3-10, BR-3-12, BR-20-12, BR-3-03, BR-3-04, BR-3-05, BR-9-03, BR-6.2-13, BR-6.2-06)
  a_CHK_006: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (i_apb_psel && !i_apb_penable && w_legal && !o_apb_pready && !o_tlul_a_valid) |=>
    (o_tlul_a_valid && !o_apb_pready && o_tlul_d_ready &&
     (o_tlul_a_opcode == ($past(i_apb_pwrite) ? 3'b000 : 3'b100)) &&
     (o_tlul_a_address == $past(i_apb_paddr)) &&
     (!$past(i_apb_pwrite) || (o_tlul_a_data == $past(i_apb_pwdata)))))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_apb_psel && !i_apb_penable && w_legal && !o_apb_pready && !o_tlul_a_valid)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: Illegal Setup completes locally in the first Access cycle with no request (BR-T1-03, BR-T1-04, BR-T1-05, BR-2.3-01, BR-2.3-02, BR-3-24, BR-3-25, BR-3-36, BR-10.1-02, BR-10.3-01, BR-12-01, BR-12-02, BR-12-04, BR-15.3-07, BR-5.4-05, BR-9-04, BR-15.3-10)
  a_CHK_007: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (i_apb_psel && !i_apb_penable && w_illegal) |=>
    ((o_apb_pready && o_apb_pslverr && (o_apb_prdata == 32'h0) && !o_tlul_a_valid) ##1 !o_tlul_a_valid))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (i_apb_psel && !i_apb_penable && w_illegal)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: One request at a time, none before the APB completion (BR-3-06, BR-3-07, BR-5.4-01, BR-6.3-06, BR-15.3-03, BR-1.1-04, TL-T3.2-03)
  a_CHK_008: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    o_tlul_a_valid |-> !req_open)
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_tlul_a_valid)) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: a_valid only inside an APB Access phase before PREADY (BR-5.4-02, BR-5.4-06)
  a_CHK_009: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    o_tlul_a_valid |-> (i_apb_psel && i_apb_penable && !o_apb_pready))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_tlul_a_valid)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: Accepted TL-UL response is checked and mapped to the APB completion one cycle later (BR-1.3-04, BR-3-09, BR-3-26, BR-3-27, BR-3-28, BR-5.3-06, BR-5.3-07, BR-5.3-08, BR-10.1-03, BR-10.1-05, BR-9-09, BR-20-10, BR-6.3-14, BR-6.3-15, BR-12-05, BR-12-07, BR-8-04, BR-8-08, BR-1.1-01, BR-11-02)
  a_CHK_010: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    w_counted |=>
    (o_apb_pready &&
     (o_apb_pslverr == $past(w_err)) &&
     (o_apb_prdata == (($past(w_exp_get) && !$past(w_err)) ? $past(i_tlul_d_data) : 32'h0))))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_counted)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: PREADY only caused by an illegal Setup or a counted response (BR-3-11, BR-6.3-08, BR-10.1-06, BR-15.3-09, BR-12-09, BR-3-32, BR-1.1-01)
  a_CHK_011: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_apb_pready && prev_rst) |-> prev_ok)
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && prev_rst)) hits_CHK_011 <= hits_CHK_011 + 1;

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
  end
endmodule
