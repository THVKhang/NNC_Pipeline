// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_axi2apb_bridge #(
  parameter int PARA_AXI_ID_W = 4
) (
  input  logic                        i_clk_axi,
  input  logic                        i_rst_n_axi,
  input  logic [(PARA_AXI_ID_W)-1:0]  i_axi_awid,
  input  logic [31:0]                 i_axi_awaddr,
  input  logic [7:0]                  i_axi_awlen,
  input  logic [2:0]                  i_axi_awsize,
  input  logic [1:0]                  i_axi_awburst,
  input  logic [3:0]                  i_axi_awcache,
  input  logic [2:0]                  i_axi_awprot,
  input  logic                        i_axi_awvalid,
  output logic                        o_axi_awready,
  input  logic [31:0]                 i_axi_wdata,
  input  logic [3:0]                  i_axi_wstrb,
  input  logic                        i_axi_wlast,
  input  logic                        i_axi_wvalid,
  output logic                        o_axi_wready,
  output logic [(PARA_AXI_ID_W)-1:0]  o_axi_bid,
  output logic [1:0]                  o_axi_bresp,
  output logic                        o_axi_bvalid,
  input  logic                        i_axi_bready,
  input  logic [(PARA_AXI_ID_W)-1:0]  i_axi_arid,
  input  logic [31:0]                 i_axi_araddr,
  input  logic [7:0]                  i_axi_arlen,
  input  logic [2:0]                  i_axi_arsize,
  input  logic [1:0]                  i_axi_arburst,
  input  logic [3:0]                  i_axi_arcache,
  input  logic [2:0]                  i_axi_arprot,
  input  logic                        i_axi_arvalid,
  output logic                        o_axi_arready,
  output logic [(PARA_AXI_ID_W)-1:0]  o_axi_rid,
  output logic [31:0]                 o_axi_rdata,
  output logic [1:0]                  o_axi_rresp,
  output logic                        o_axi_rlast,
  output logic                        o_axi_rvalid,
  input  logic                        i_axi_rready,
  output logic [31:0]                 o_apb_paddr,
  output logic                        o_apb_pwrite,
  output logic [31:0]                 o_apb_pwdata,
  output logic [3:0]                  o_apb_pstrb,
  output logic [2:0]                  o_apb_pprot,
  output logic                        o_apb_psel,
  output logic                        o_apb_penable,
  input  logic                        i_apb_pready,
  input  logic [31:0]                 i_apb_prdata,
  input  logic                        i_apb_pslverr
);
  assign o_axi_awready = '0;
  assign o_axi_wready = '0;
  assign o_axi_bid = '0;
  assign o_axi_bresp = '0;
  assign o_axi_bvalid = '0;
  assign o_axi_arready = '0;
  assign o_axi_rid = '0;
  assign o_axi_rdata = '0;
  assign o_axi_rresp = '0;
  assign o_axi_rlast = '0;
  assign o_axi_rvalid = '0;
  assign o_apb_paddr = '0;
  assign o_apb_pwrite = '0;
  assign o_apb_pwdata = '0;
  assign o_apb_pstrb = '0;
  assign o_apb_pprot = '0;
  assign o_apb_psel = '0;
  assign o_apb_penable = '0;
endmodule
