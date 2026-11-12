// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Helper: registered reset, so $past()/$stable() are only used once a
  // defined previous cycle outside reset exists.
  // ---------------------------------------------------------------------------
  reg r_past_rst_n = 1'b0;
  always @(posedge i_clk_axi) r_past_rst_n <= i_rst_n_axi;

  // ENV-01: The AXI Manager drives AWVALID, WVALID and ARVALID low while reset is sampled active (AB-6.1-01, AB-2.2-01, AB-7.3-03)
  always @(*) begin
    if (!i_rst_n_axi) begin
      assume (!i_axi_awvalid);
      assume (!i_axi_wvalid);
      assume (!i_axi_arvalid);
    end
  end

  // ENV-02: Once AWVALID is asserted it stays asserted, with AW payload stable, until AWREADY handshake (AB-6.1-01, AB-2.2-01, AB-3-06)
  always @(posedge i_clk_axi) begin
    if (r_past_rst_n && i_rst_n_axi && $past(i_axi_awvalid) && !$past(o_axi_awready)) begin
      assume (i_axi_awvalid);
      assume ($stable(i_axi_awid));
      assume ($stable(i_axi_awaddr));
      assume ($stable(i_axi_awlen));
      assume ($stable(i_axi_awsize));
      assume ($stable(i_axi_awburst));
      assume ($stable(i_axi_awcache));
      assume ($stable(i_axi_awprot));
    end
  end

  // ENV-03: Once WVALID is asserted it stays asserted, with W payload stable, until WREADY handshake (AB-6.1-01, AB-2.2-01, AB-3-06, AB-5.3-03)
  always @(posedge i_clk_axi) begin
    if (r_past_rst_n && i_rst_n_axi && $past(i_axi_wvalid) && !$past(o_axi_wready)) begin
      assume (i_axi_wvalid);
      assume ($stable(i_axi_wdata));
      assume ($stable(i_axi_wstrb));
      assume ($stable(i_axi_wlast));
    end
  end

  // ENV-04: Once ARVALID is asserted it stays asserted, with AR payload stable, until ARREADY handshake (AB-6.1-01, AB-2.2-01, AB-3-06)
  always @(posedge i_clk_axi) begin
    if (r_past_rst_n && i_rst_n_axi && $past(i_axi_arvalid) && !$past(o_axi_arready)) begin
      assume (i_axi_arvalid);
      assume ($stable(i_axi_arid));
      assume ($stable(i_axi_araddr));
      assume ($stable(i_axi_arlen));
      assume ($stable(i_axi_arsize));
      assume ($stable(i_axi_arburst));
      assume ($stable(i_axi_arcache));
      assume ($stable(i_axi_arprot));
    end
  end

  // ---------------------------------------------------------------------------
  // Helper for ENV-05: tracks the accepted AW whose W data is outstanding and
  // counts W beats since the last WLAST handshake (W may precede AW).
  // ---------------------------------------------------------------------------
  reg       r_aw_pend = 1'b0;
  reg [7:0] r_aw_len  = 8'd0;
  reg [8:0] r_w_cnt   = 9'd0;

  wire       w_aw_hs    = i_axi_awvalid && o_axi_awready;
  wire       w_w_hs     = i_axi_wvalid  && o_axi_wready;
  wire       w_pend_eff = r_aw_pend || w_aw_hs;
  wire [7:0] w_len_eff  = r_aw_pend ? r_aw_len : i_axi_awlen;

  always @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      r_aw_pend <= 1'b0;
      r_aw_len  <= 8'd0;
      r_w_cnt   <= 9'd0;
    end else begin
      if (w_w_hs) begin
        if (i_axi_wlast)
          r_w_cnt <= 9'd0;
        else if (r_w_cnt != 9'h1FF)
          r_w_cnt <= r_w_cnt + 9'd1;
      end
      if (w_w_hs && i_axi_wlast && w_pend_eff) begin
        r_aw_pend <= 1'b0;
      end else if (w_aw_hs && !r_aw_pend) begin
        r_aw_pend <= 1'b1;
        r_aw_len  <= i_axi_awlen;
      end
    end
  end

  // ENV-05: The AXI Manager asserts WLAST exactly on W beat AWLEN+1 of the write burst (AB-20-05, AB-5.4-05, AB-6.3-03)
  always @(*) begin
    if (i_rst_n_axi && w_w_hs && w_pend_eff && (r_w_cnt <= {1'b0, w_len_eff}))
      assume (i_axi_wlast == (r_w_cnt == {1'b0, w_len_eff}));
  end
endmodule
