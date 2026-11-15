module nnc_chk_reset #(
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

  int unsigned fails_CHK_018 = 0;
  int unsigned hits_CHK_018 = 0;
  int unsigned fails_CHK_019 = 0;
  int unsigned hits_CHK_019 = 0;
  int unsigned fails_CHK_020 = 0;
  int unsigned hits_CHK_020 = 0;

  // CHK-018: AHB outputs hold reset values during reset (AA-T1.7.2.2-05, AA-T1.7.2.2-06, AA-T1.7.2.2-08, AA-7.3-01, AA-10.2-06)
  a_CHK_018: assert property (@(posedge i_clk_core) (!i_rst_n_core) |-> (o_ahb_hreadyout == 1'b1 && o_ahb_hresp == 1'b0 && o_ahb_hrdata == 32'h0000_0000))
    else begin fails_CHK_018++; $display("NNC_FAIL CHK-018 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!i_rst_n_core) hits_CHK_018 <= hits_CHK_018 + 1;

  // CHK-019: AXI VALID/READY outputs suppressed during reset (AA-T1.7.2.2-13, AA-15.3-08, AA-7.3-01, AA-10.2-06, AA-5.1-02, AA-3-30)
  a_CHK_019: assert property (@(posedge i_clk_core) (!i_rst_n_core) |-> (o_axi_awvalid == 1'b0 && o_axi_wvalid == 1'b0 && o_axi_arvalid == 1'b0 && o_axi_bready == 1'b0 && o_axi_rready == 1'b0))
    else begin fails_CHK_019++; $display("NNC_FAIL CHK-019 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!i_rst_n_core) hits_CHK_019 <= hits_CHK_019 + 1;

  // CHK-020: AXI payload outputs hold reset values during reset (AA-T1.7.2.2-09, AA-T1.7.2.2-15, AA-T1.7.2.2-19, AA-T1.7.2.2-21)
  a_CHK_020: assert property (@(posedge i_clk_core) (!i_rst_n_core) |-> (o_axi_awid == 3'd0 && o_axi_awaddr == 32'd0 && o_axi_awlen == 8'd0 && o_axi_awsize == 3'd0 && o_axi_awburst == 2'b01 && o_axi_awcache == 4'd0 && o_axi_awprot == 3'd0 && o_axi_wdata == 32'd0 && o_axi_wstrb == 4'd0 && o_axi_wlast == 1'b0 && o_axi_arid == 3'd0 && o_axi_araddr == 32'd0 && o_axi_arlen == 8'd0 && o_axi_arsize == 3'd0 && o_axi_arburst == 2'b01 && o_axi_arcache == 4'd0 && o_axi_arprot == 3'd0))
    else begin fails_CHK_020++; $display("NNC_FAIL CHK-020 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!i_rst_n_core) hits_CHK_020 <= hits_CHK_020 + 1;

  final begin
    $display("NNC_CHECK CHK-018 hits=%0d fails=%0d", hits_CHK_018, fails_CHK_018);
    $display("NNC_CHECK CHK-019 hits=%0d fails=%0d", hits_CHK_019, fails_CHK_019);
    $display("NNC_CHECK CHK-020 hits=%0d fails=%0d", hits_CHK_020, fails_CHK_020);
  end
endmodule
