module nnc_chk_apb #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;

  // CHK-001: PREADY only in an APB Access cycle (BR-3-18, BR-15.3-01, BR-6.2-03)
  a_CHK_001: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core) o_apb_pready |-> (i_apb_psel && i_apb_penable))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: PREADY is a one-cycle pulse (BR-3-18, BR-6.2-03, BR-5.4-04, BR-15.3-01)
  a_CHK_002: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core) o_apb_pready |=> !o_apb_pready)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: PSLVERR only with PREADY (BR-3-19, BR-6.2-05, BR-15.3-01)
  a_CHK_003: assert property (@(posedge i_clk_core) o_apb_pslverr |-> o_apb_pready)
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (o_apb_pslverr) hits_CHK_003 <= hits_CHK_003 + 1;

  // helper: previous-cycle reset state and previous PRDATA
  logic        r_prev_rst_ok;
  logic [31:0] r_prev_prdata;
  always_ff @(posedge i_clk_core) begin
    r_prev_rst_ok <= i_rst_n_core;
    r_prev_prdata <= o_apb_prdata;
  end

  // CHK-004: PRDATA holds its value outside PREADY (BR-6.2-04)
  a_CHK_004: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core) (r_prev_rst_ok && !o_apb_pready) |-> (o_apb_prdata == r_prev_prdata))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (r_prev_rst_ok && !o_apb_pready)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: PRDATA is zero on write and error completions (BR-3-10, BR-9-10, BR-5.1-03)
  a_CHK_005: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core) (o_apb_pready && (i_apb_pwrite || o_apb_pslverr)) |-> (o_apb_prdata == 32'h0))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_apb_pready && (i_apb_pwrite || o_apb_pslverr))) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
