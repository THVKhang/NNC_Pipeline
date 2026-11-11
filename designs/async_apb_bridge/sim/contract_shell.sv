// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_vlsit_apbcdc_top #(
  parameter int PARA_APBCDC_ADDR_W = 32,
  parameter int PARA_APBCDC_DATA_W = 32,
  parameter int PARA_APBCDC_APB5 = 0,
  parameter int PARA_APBCDC_USER_REQ_W = 0,
  parameter int PARA_APBCDC_USER_DATA_W = 0,
  parameter int PARA_APBCDC_USER_RESP_W = 0,
  parameter int PARA_APBCDC_HS_TYPE = 0,
  parameter int PARA_APBCDC_CELL_TYPE = 2,
  localparam int LPARA_STRB_W = PARA_APBCDC_DATA_W / 8
) (
  input  logic                        i_clk_mst,
  input  logic                        i_rst_n_mst,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_APBCDC_ADDR_W)-1:0] i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [(LPARA_STRB_W)-1:0]   i_apb_pstrb,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_pwdata,
  input  logic                        i_apb_pwakeup,
  input  logic [(PARA_APBCDC_USER_REQ_W)-1:0] i_apb_pauser,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pwuser,
  output logic                        o_apb_pready,
  output logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_prdata,
  output logic                        o_apb_pslverr,
  output logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pruser,
  output logic [(PARA_APBCDC_USER_RESP_W)-1:0] o_apb_pbuser,
  input  logic                        i_clk_slv,
  input  logic                        i_rst_n_slv,
  output logic                        o_apb_psel,
  output logic                        o_apb_penable,
  output logic                        o_apb_pwrite,
  output logic [(PARA_APBCDC_ADDR_W)-1:0] o_apb_paddr,
  output logic [2:0]                  o_apb_pprot,
  output logic [(LPARA_STRB_W)-1:0]   o_apb_pstrb,
  output logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_pwdata,
  output logic                        o_apb_pwakeup,
  output logic [(PARA_APBCDC_USER_REQ_W)-1:0] o_apb_pauser,
  output logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pwuser,
  input  logic                        i_apb_pready,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_prdata,
  input  logic                        i_apb_pslverr,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pruser,
  input  logic [(PARA_APBCDC_USER_RESP_W)-1:0] i_apb_pbuser
);
  assign o_apb_pready = '0;
  assign o_apb_prdata = '0;
  assign o_apb_pslverr = '0;
  assign o_apb_pruser = '0;
  assign o_apb_pbuser = '0;
  assign o_apb_psel = '0;
  assign o_apb_penable = '0;
  assign o_apb_pwrite = '0;
  assign o_apb_paddr = '0;
  assign o_apb_pprot = '0;
  assign o_apb_pstrb = '0;
  assign o_apb_pwdata = '0;
  assign o_apb_pwakeup = '0;
  assign o_apb_pauser = '0;
  assign o_apb_pwuser = '0;
endmodule
