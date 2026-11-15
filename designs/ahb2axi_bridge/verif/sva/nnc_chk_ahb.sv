module nnc_chk_ahb #(
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
  input  logic                        o_ahb_hreadyout,
  input  logic                        o_ahb_hresp,
  input  logic [31:0]                 o_ahb_hrdata,
  input  logic [2:0]                  o_axi_awid,
  input  logic [31:0]                 o_axi_awaddr,
  input  logic [7:0]                  o_axi_awlen,
  input  logic [2:0]                  o_axi_awsize,
  input  logic [1:0]                  o_axi_awburst,
  input  logic                        o_axi_awlock,
  input  logic [3:0]                  o_axi_awcache,
  input  logic [2:0]                  o_axi_awprot,
  input  logic                        o_axi_awvalid,
  input  logic                        i_axi_awready,
  input  logic [31:0]                 o_axi_wdata,
  input  logic [3:0]                  o_axi_wstrb,
  input  logic                        o_axi_wlast,
  input  logic                        o_axi_wvalid,
  input  logic                        i_axi_wready,
  input  logic [2:0]                  i_axi_bid,
  input  logic [1:0]                  i_axi_bresp,
  input  logic                        i_axi_bvalid,
  input  logic                        o_axi_bready,
  input  logic [2:0]                  o_axi_arid,
  input  logic [31:0]                 o_axi_araddr,
  input  logic [7:0]                  o_axi_arlen,
  input  logic [2:0]                  o_axi_arsize,
  input  logic [1:0]                  o_axi_arburst,
  input  logic                        o_axi_arlock,
  input  logic [3:0]                  o_axi_arcache,
  input  logic [2:0]                  o_axi_arprot,
  input  logic                        o_axi_arvalid,
  input  logic                        i_axi_arready,
  input  logic [2:0]                  i_axi_rid,
  input  logic [31:0]                 i_axi_rdata,
  input  logic [1:0]                  i_axi_rresp,
  input  logic                        i_axi_rlast,
  input  logic                        i_axi_rvalid,
  input  logic                        o_axi_rready
);

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;

  // helper: previous cycle was first ERROR cycle (HRESP=1, HREADYOUT=0)
  logic chk001_prev_first;
  always_ff @(posedge i_clk_core) begin
    if (!i_rst_n_core) chk001_prev_first <= 1'b0;
    else chk001_prev_first <= (o_ahb_hresp && !o_ahb_hreadyout);
  end

  // CHK-001: AHB ERROR is a two-cycle response (AA-12-16, AA-15.3-07, AA-T1.7.2.2-07)
  a_CHK_001: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_ahb_hresp || chk001_prev_first) |->
    (chk001_prev_first == (o_ahb_hresp && o_ahb_hreadyout)))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && ((o_ahb_hresp || chk001_prev_first))) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: IDLE and BUSY transfers get zero-wait OKAY (AA-6.1-01, AA-T1.7.3.1-03)
  a_CHK_002: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (i_ahb_hsel && i_ahb_hready && (i_ahb_htrans == 2'b00 || i_ahb_htrans == 2'b01)) |=>
    (o_ahb_hreadyout && !o_ahb_hresp))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && ((i_ahb_hsel && i_ahb_hready && (i_ahb_htrans == 2'b00 || i_ahb_htrans == 2'b01)))) hits_CHK_002 <= hits_CHK_002 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
  end
endmodule
