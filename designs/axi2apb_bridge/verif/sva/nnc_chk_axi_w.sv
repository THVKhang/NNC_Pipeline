module nnc_chk_axi_w #(
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

  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  // Helper tracker: write outstanding from AW handshake until B handshake
  logic        chk013_active;
  logic [7:0]  chk013_len;
  logic [9:0]  chk013_cnt;

  wire chk013_aw_hs = i_axi_awvalid && o_axi_awready;
  wire chk013_w_hs  = i_axi_wvalid  && o_axi_wready;
  wire chk013_b_hs  = o_axi_bvalid  && i_axi_bready;
  wire chk013_new_aw = chk013_aw_hs && (!chk013_active || chk013_b_hs);
  wire [9:0] chk013_eff_cnt = chk013_new_aw ? 10'd1 : (chk013_cnt + 10'd1);
  wire [9:0] chk013_eff_max = (chk013_new_aw ? {2'b00, i_axi_awlen} : {2'b00, chk013_len}) + 10'd1;

  always_ff @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      chk013_active <= 1'b0;
      chk013_len    <= 8'd0;
      chk013_cnt    <= 10'd0;
    end else begin
      if (chk013_b_hs && chk013_active) begin
        chk013_active <= 1'b0;
        chk013_cnt    <= 10'd0;
      end
      if (chk013_new_aw) begin
        chk013_active <= 1'b1;
        chk013_len    <= i_axi_awlen;
        chk013_cnt    <= chk013_w_hs ? 10'd1 : 10'd0;
      end else if (chk013_active && chk013_w_hs && !chk013_b_hs && (chk013_cnt != 10'h3FF)) begin
        chk013_cnt    <= chk013_cnt + 10'd1;
      end
    end
  end

  // CHK-013: WREADY gated by AW acceptance; W beats never exceed AWLEN+1 (AB-5.3-04, AB-5.3-02, AB-3-35, AB-3-06)
  a_CHK_013: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    o_axi_wready |-> ((chk013_active || chk013_aw_hs) &&
                      (!i_axi_wvalid || (chk013_eff_cnt <= chk013_eff_max))))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_wready)) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
