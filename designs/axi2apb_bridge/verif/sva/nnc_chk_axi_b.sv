module nnc_chk_axi_b #(
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

  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;

  // CHK-007: B channel hold under BREADY backpressure (AB-6.2-02, AB-3-21, AB-5.4-06, AB-15.2-02)
  a_CHK_007: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_axi_bvalid && !i_axi_bready) |=> (o_axi_bvalid && $stable(o_axi_bid) && $stable(o_axi_bresp)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_bvalid && !i_axi_bready)) hits_CHK_007 <= hits_CHK_007 + 1;

  // Write transaction tracker (owner=WR), built from interface signals only
  logic                       wr_active;
  logic [(PARA_AXI_ID_W)-1:0] wr_id;
  logic [7:0]                 wr_len;
  logic [9:0]                 wr_wcnt;
  logic [9:0]                 wr_apbcnt;
  logic                       wr_err;

  wire wr_w_hs   = i_axi_wvalid && o_axi_wready;
  wire wr_apb_cp = o_apb_psel && o_apb_penable && o_apb_pwrite && i_apb_pready;
  wire [9:0] wr_exp = {2'b00, wr_len} + 10'd1;

  always_ff @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      wr_active <= 1'b0;
      wr_id     <= '0;
      wr_len    <= 8'd0;
      wr_wcnt   <= 10'd0;
      wr_apbcnt <= 10'd0;
      wr_err    <= 1'b0;
    end else begin
      if (wr_active && o_axi_bvalid && i_axi_bready) begin
        wr_active <= 1'b0;
        wr_wcnt   <= 10'd0;
        wr_apbcnt <= 10'd0;
        wr_err    <= 1'b0;
      end else if (!wr_active && i_axi_awvalid && o_axi_awready) begin
        wr_active <= 1'b1;
        wr_id     <= i_axi_awid;
        wr_len    <= i_axi_awlen;
        wr_wcnt   <= wr_w_hs ? 10'd1 : 10'd0;
        wr_apbcnt <= 10'd0;
        wr_err    <= 1'b0;
      end else if (wr_active) begin
        if (wr_w_hs) wr_wcnt <= wr_wcnt + 10'd1;
        if (wr_apb_cp) begin
          wr_apbcnt <= wr_apbcnt + 10'd1;
          if (i_apb_pslverr) wr_err <= 1'b1;
        end
      end
    end
  end

  // CHK-008: Single B after all W beats and APB writes, with correct BID/BRESP (AB-3-14, AB-5.4-04, AB-9-05, AB-5.3-05, AB-3-34, AB-3-37, AB-6.3-11, AB-10.2-02, AB-10.2-04, AB-10.2-06, AB-12-04, AB-12-07, AB-12-11, AB-3-41, AB-5.4-05)
  a_CHK_008: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_axi_bvalid && wr_active) |->
      ((o_axi_bid == wr_id) && (wr_wcnt == wr_exp) &&
       ((wr_apbcnt == 10'd0) ? (o_axi_bresp == 2'b10) :
        ((wr_apbcnt == wr_exp) && (o_axi_bresp == (wr_err ? 2'b10 : 2'b00))))))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_bvalid && wr_active)) hits_CHK_008 <= hits_CHK_008 + 1;

  final begin
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
  end
endmodule
