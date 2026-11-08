module nnc_chk_reset #(
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
  input  logic                        o_axi_awready,
  input  logic [31:0]                 i_axi_wdata,
  input  logic [3:0]                  i_axi_wstrb,
  input  logic                        i_axi_wlast,
  input  logic                        i_axi_wvalid,
  input  logic                        o_axi_wready,
  input  logic [(PARA_AXI_ID_W)-1:0]  o_axi_bid,
  input  logic [1:0]                  o_axi_bresp,
  input  logic                        o_axi_bvalid,
  input  logic                        i_axi_bready,
  input  logic [(PARA_AXI_ID_W)-1:0]  i_axi_arid,
  input  logic [31:0]                 i_axi_araddr,
  input  logic [7:0]                  i_axi_arlen,
  input  logic [2:0]                  i_axi_arsize,
  input  logic [1:0]                  i_axi_arburst,
  input  logic [3:0]                  i_axi_arcache,
  input  logic [2:0]                  i_axi_arprot,
  input  logic                        i_axi_arvalid,
  input  logic                        o_axi_arready,
  input  logic [(PARA_AXI_ID_W)-1:0]  o_axi_rid,
  input  logic [31:0]                 o_axi_rdata,
  input  logic [1:0]                  o_axi_rresp,
  input  logic                        o_axi_rlast,
  input  logic                        o_axi_rvalid,
  input  logic                        i_axi_rready,
  input  logic [31:0]                 o_apb_paddr,
  input  logic                        o_apb_pwrite,
  input  logic [31:0]                 o_apb_pwdata,
  input  logic [3:0]                  o_apb_pstrb,
  input  logic [2:0]                  o_apb_pprot,
  input  logic                        o_apb_psel,
  input  logic                        o_apb_penable,
  input  logic                        i_apb_pready,
  input  logic [31:0]                 i_apb_prdata,
  input  logic                        i_apb_pslverr
);

  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;

  logic rst_prev_low_CHK_017 = 1'b0;
  always_ff @(posedge i_clk_axi) rst_prev_low_CHK_017 <= !i_rst_n_axi;

  // CHK-017: Synchronous reset values of all outputs (AB-3-27, AB-7.3-01, AB-6.2-03, AB-6.2-05, AB-10.1-06, AB-12-09)
  a_CHK_017: assert property (@(posedge i_clk_axi) (!i_rst_n_axi) |=>
      (o_axi_bvalid == 1'b0) && (o_axi_rvalid == 1'b0) &&
      (o_axi_bid == '0) && (o_axi_bresp == 2'b00) &&
      (o_axi_rid == '0) && (o_axi_rdata == 32'h0) && (o_axi_rresp == 2'b00) &&
      (o_axi_rlast == 1'b0) && (o_apb_psel == 1'b0) && (o_apb_penable == 1'b0) &&
      (o_apb_paddr == 32'h0) && (o_apb_pwrite == 1'b0) && (o_apb_pwdata == 32'h0) &&
      (o_apb_pstrb == 4'h0) && (o_apb_pprot == 3'b000))
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end

  // CHK-017: ready outputs low when reset is active at two consecutive edges (AB-3-27, AB-7.3-01, AB-10.1-06)
  a_CHK_017_rdy: assert property (@(posedge i_clk_axi) (!i_rst_n_axi && rst_prev_low_CHK_017) |->
      (o_axi_awready == 1'b0) && (o_axi_wready == 1'b0) && (o_axi_arready == 1'b0))
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end

  always_ff @(posedge i_clk_axi) if (!i_rst_n_axi) hits_CHK_017 <= hits_CHK_017 + 1;

  final begin
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
  end
endmodule
