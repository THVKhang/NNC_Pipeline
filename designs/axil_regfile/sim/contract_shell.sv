// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_axil_regfile #(
  parameter int PARA_NUM_REGS = 8,
  parameter int PARA_ADDR_W = 8,
  localparam int LPARA_REGS_W = PARA_NUM_REGS*32
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_s_axi_awvalid,
  output logic                        o_s_axi_awready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_awaddr,
  input  logic [2:0]                  i_s_axi_awprot,
  input  logic                        i_s_axi_wvalid,
  output logic                        o_s_axi_wready,
  input  logic [31:0]                 i_s_axi_wdata,
  input  logic [3:0]                  i_s_axi_wstrb,
  output logic                        o_s_axi_bvalid,
  input  logic                        i_s_axi_bready,
  output logic [1:0]                  o_s_axi_bresp,
  input  logic                        i_s_axi_arvalid,
  output logic                        o_s_axi_arready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_araddr,
  input  logic [2:0]                  i_s_axi_arprot,
  output logic                        o_s_axi_rvalid,
  input  logic                        i_s_axi_rready,
  output logic [31:0]                 o_s_axi_rdata,
  output logic [1:0]                  o_s_axi_rresp,
  output logic [(LPARA_REGS_W)-1:0]   o_regs,
  input  logic [31:0]                 i_status
);
  assign o_s_axi_awready = '0;
  assign o_s_axi_wready = '0;
  assign o_s_axi_bvalid = '0;
  assign o_s_axi_bresp = '0;
  assign o_s_axi_arready = '0;
  assign o_s_axi_rvalid = '0;
  assign o_s_axi_rdata = '0;
  assign o_s_axi_rresp = '0;
  assign o_regs = '0;
endmodule
