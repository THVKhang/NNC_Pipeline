// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_apb_tlul_bridge #(
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
  output logic                        o_apb_pready,
  output logic [31:0]                 o_apb_prdata,
  output logic                        o_apb_pslverr,
  output logic                        o_tlul_a_valid,
  input  logic                        i_tlul_a_ready,
  output logic [2:0]                  o_tlul_a_opcode,
  output logic [2:0]                  o_tlul_a_param,
  output logic [1:0]                  o_tlul_a_size,
  output logic [(PARA_SRC_W)-1:0]     o_tlul_a_source,
  output logic [(PARA_ADDR_W)-1:0]    o_tlul_a_address,
  output logic [3:0]                  o_tlul_a_mask,
  output logic [31:0]                 o_tlul_a_data,
  output logic [(PARA_A_USER_W)-1:0]  o_tlul_a_user,
  input  logic                        i_tlul_d_valid,
  output logic                        o_tlul_d_ready,
  input  logic [2:0]                  i_tlul_d_opcode,
  input  logic [(PARA_SRC_W)-1:0]     i_tlul_d_source,
  input  logic [31:0]                 i_tlul_d_data,
  input  logic                        i_tlul_d_error,
  input  logic [2:0]                  i_tlul_d_param,
  input  logic [1:0]                  i_tlul_d_size,
  input  logic [(PARA_D_SINK_W)-1:0]  i_tlul_d_sink,
  input  logic [(PARA_D_USER_W)-1:0]  i_tlul_d_user
);
  assign o_apb_pready = '0;
  assign o_apb_prdata = '0;
  assign o_apb_pslverr = '0;
  assign o_tlul_a_valid = '0;
  assign o_tlul_a_opcode = '0;
  assign o_tlul_a_param = '0;
  assign o_tlul_a_size = '0;
  assign o_tlul_a_source = '0;
  assign o_tlul_a_address = '0;
  assign o_tlul_a_mask = '0;
  assign o_tlul_a_data = '0;
  assign o_tlul_a_user = '0;
  assign o_tlul_d_ready = '0;
endmodule
