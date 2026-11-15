// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_ahb2axi_top #(
  parameter int PARA_RD_ID_COUNT = 1,
  parameter int PARA_WR_ID_COUNT = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_ahb_hsel,
  input  logic                        i_ahb_hready,
  input  logic [31:0]                 i_ahb_haddr,
  input  logic [1:0]                  i_ahb_htrans,
  input  logic                        i_ahb_hwrite,
  input  logic [2:0]                  i_ahb_hsize,
  input  logic [2:0]                  i_ahb_hburst,
  input  logic [6:0]                  i_ahb_hprot,
  input  logic                        i_ahb_hnonsec,
  input  logic                        i_ahb_hmastlock,
  input  logic [31:0]                 i_ahb_hwdata,
  input  logic [3:0]                  i_ahb_hwstrb,
  output logic                        o_ahb_hreadyout,
  output logic                        o_ahb_hresp,
  output logic [31:0]                 o_ahb_hrdata,
  output logic [2:0]                  o_axi_awid,
  output logic [31:0]                 o_axi_awaddr,
  output logic [7:0]                  o_axi_awlen,
  output logic [2:0]                  o_axi_awsize,
  output logic [1:0]                  o_axi_awburst,
  output logic                        o_axi_awlock,
  output logic [3:0]                  o_axi_awcache,
  output logic [2:0]                  o_axi_awprot,
  output logic                        o_axi_awvalid,
  input  logic                        i_axi_awready,
  output logic [31:0]                 o_axi_wdata,
  output logic [3:0]                  o_axi_wstrb,
  output logic                        o_axi_wlast,
  output logic                        o_axi_wvalid,
  input  logic                        i_axi_wready,
  input  logic [2:0]                  i_axi_bid,
  input  logic [1:0]                  i_axi_bresp,
  input  logic                        i_axi_bvalid,
  output logic                        o_axi_bready,
  output logic [2:0]                  o_axi_arid,
  output logic [31:0]                 o_axi_araddr,
  output logic [7:0]                  o_axi_arlen,
  output logic [2:0]                  o_axi_arsize,
  output logic [1:0]                  o_axi_arburst,
  output logic                        o_axi_arlock,
  output logic [3:0]                  o_axi_arcache,
  output logic [2:0]                  o_axi_arprot,
  output logic                        o_axi_arvalid,
  input  logic                        i_axi_arready,
  input  logic [2:0]                  i_axi_rid,
  input  logic [31:0]                 i_axi_rdata,
  input  logic [1:0]                  i_axi_rresp,
  input  logic                        i_axi_rlast,
  input  logic                        i_axi_rvalid,
  output logic                        o_axi_rready
);
  assign o_ahb_hreadyout = '0;
  assign o_ahb_hresp = '0;
  assign o_ahb_hrdata = '0;
  assign o_axi_awid = '0;
  assign o_axi_awaddr = '0;
  assign o_axi_awlen = '0;
  assign o_axi_awsize = '0;
  assign o_axi_awburst = '0;
  assign o_axi_awlock = '0;
  assign o_axi_awcache = '0;
  assign o_axi_awprot = '0;
  assign o_axi_awvalid = '0;
  assign o_axi_wdata = '0;
  assign o_axi_wstrb = '0;
  assign o_axi_wlast = '0;
  assign o_axi_wvalid = '0;
  assign o_axi_bready = '0;
  assign o_axi_arid = '0;
  assign o_axi_araddr = '0;
  assign o_axi_arlen = '0;
  assign o_axi_arsize = '0;
  assign o_axi_arburst = '0;
  assign o_axi_arlock = '0;
  assign o_axi_arcache = '0;
  assign o_axi_arprot = '0;
  assign o_axi_arvalid = '0;
  assign o_axi_rready = '0;
endmodule
