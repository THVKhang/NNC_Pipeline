module nnc_chk_reset #(
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

  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  // helper: reset was deasserted at the previous rising edge
  logic rst_n_prev = 1'b0;
  always_ff @(posedge i_clk_core) rst_n_prev <= i_rst_n_core;

  // CHK-012: Output values while reset is asserted (BR-3-31, BR-3-21, BR-6.2-03, BR-6.2-04, BR-6.2-06, BR-6.2-15, BR-7.3-03, BR-15.3-06, BR-20-11)
  a_CHK_012: assert property (@(posedge i_clk_core) !i_rst_n_core |->
      (o_tlul_a_valid == 1'b0) && (o_tlul_d_ready == 1'b0) &&
      (o_apb_pready == 1'b0) && (o_apb_pslverr == 1'b0) &&
      (o_apb_prdata == 32'h0) && (o_tlul_a_opcode == 3'b000) &&
      (o_tlul_a_address == '0) && (o_tlul_a_data == 32'h0) &&
      (o_tlul_a_param == 3'b000) && (o_tlul_a_size == 2'b10) &&
      (o_tlul_a_source == PARA_SRC_W'(PARA_SRC_ID)) &&
      (o_tlul_a_mask == 4'b1111) && (o_tlul_a_user == '0))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!i_rst_n_core) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: d_ready constant 1 after the first edge following reset release (BR-3-22, BR-6.2-15, BR-15.3-06, BR-20-11, BR-5.3-04)
  a_CHK_013: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core) rst_n_prev |-> (o_tlul_d_ready == 1'b1))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (rst_n_prev)) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
