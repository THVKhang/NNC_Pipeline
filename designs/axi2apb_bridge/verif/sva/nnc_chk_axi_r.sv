module nnc_chk_axi_r #(
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

  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;

  // Read transaction tracker (derived only from interface signals)
  logic [12:0] ar_bytes;
  logic [12:0] ar_end;
  logic        ar_sup;
  logic        ar_acc;
  assign ar_bytes = ({5'b0, i_axi_arlen} + 13'd1) << i_axi_arsize;
  assign ar_end   = {1'b0, i_axi_araddr[11:0]} + ar_bytes;
  assign ar_sup   = (i_axi_arburst != 2'b11) &&
                    (i_axi_arsize <= 3'd2) &&
                    (i_axi_arcache == 4'b0000 || i_axi_arcache == 4'b0001) &&
                    !((i_axi_arburst == 2'b01) && (ar_end > 13'd4096)) &&
                    !((i_axi_arburst == 2'b10) &&
                      !(i_axi_arlen == 8'd1 || i_axi_arlen == 8'd3 ||
                        i_axi_arlen == 8'd7 || i_axi_arlen == 8'd15));

  logic                         rd_busy;
  logic [PARA_AXI_ID_W-1:0]     cap_id;
  logic [7:0]                   cap_len;
  logic                         cap_sup;
  logic [8:0]                   rbeat_k;
  logic [9:0]                   comp_cnt;
  logic [31:0]                  comp_data [0:255];
  logic                         comp_err  [0:255];

  logic apb_comp;
  assign ar_acc   = i_axi_arvalid && o_axi_arready;
  assign apb_comp = rd_busy && cap_sup && o_apb_psel && o_apb_penable &&
                    i_apb_pready && !o_apb_pwrite;

  always_ff @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      rd_busy  <= 1'b0;
      cap_id   <= '0;
      cap_len  <= '0;
      cap_sup  <= 1'b0;
      rbeat_k  <= '0;
      comp_cnt <= '0;
    end else if (!rd_busy) begin
      if (ar_acc) begin
        rd_busy  <= 1'b1;
        cap_id   <= i_axi_arid;
        cap_len  <= i_axi_arlen;
        cap_sup  <= ar_sup;
        rbeat_k  <= '0;
        comp_cnt <= '0;
      end
    end else begin
      if (apb_comp) begin
        comp_data[comp_cnt[7:0]] <= i_apb_prdata;
        comp_err[comp_cnt[7:0]]  <= i_apb_pslverr;
        comp_cnt <= comp_cnt + 10'd1;
      end
      if (o_axi_rvalid && i_axi_rready) begin
        rbeat_k <= rbeat_k + 9'd1;
        if (o_axi_rlast) rd_busy <= 1'b0;
      end
    end
  end

  logic [9:0]  comp_eff;
  logic        cur_is_k;
  logic [31:0] k_data;
  logic        k_err;
  assign comp_eff = comp_cnt + (apb_comp ? 10'd1 : 10'd0);
  assign cur_is_k = apb_comp && (comp_cnt == {1'b0, rbeat_k});
  assign k_data   = cur_is_k ? i_apb_prdata : comp_data[rbeat_k[7:0]];
  assign k_err    = cur_is_k ? i_apb_pslverr : comp_err[rbeat_k[7:0]];

  // CHK-009: R channel hold under RREADY backpressure (AB-3-21, AB-5.4-06, AB-6.2-04, AB-5.3-01, AB-15.2-02)
  a_CHK_009: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_axi_rvalid && !i_axi_rready) |=>
    (o_axi_rvalid && $stable(o_axi_rid) && $stable(o_axi_rdata) &&
     $stable(o_axi_rresp) && $stable(o_axi_rlast)))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_rvalid && !i_axi_rready)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: RID echo, RLAST position and R beat count (AB-3-13, AB-5.4-04, AB-9-05, AB-6.2-06, AB-3-31, AB-5.4-05)
  a_CHK_010: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (rd_busy && o_axi_rvalid) |->
    ((o_axi_rid == cap_id) && (o_axi_rlast == (rbeat_k == {1'b0, cap_len}))))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (rd_busy && o_axi_rvalid)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: Legal read beat data and response from the APB completion (AB-3-33, AB-3-41, AB-6.3-09, AB-6.3-10, AB-10.2-05, AB-12-06, AB-12-11, AB-9-03, AB-5.3-01)
  a_CHK_011: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (rd_busy && cap_sup && o_axi_rvalid) |->
    ((comp_eff > {1'b0, rbeat_k}) &&
     (k_err ? (o_axi_rresp == 2'b10 && o_axi_rdata == 32'h0)
            : (o_axi_rresp == 2'b00 && o_axi_rdata == k_data))))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (rd_busy && cap_sup && o_axi_rvalid)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: Unsupported read beats are SLVERR with zero data (AB-3-30, AB-10.2-03, AB-12-01, AB-6.3-02)
  a_CHK_012: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (rd_busy && !cap_sup && o_axi_rvalid) |->
    (o_axi_rresp == 2'b10 && o_axi_rdata == 32'h0))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (rd_busy && !cap_sup && o_axi_rvalid)) hits_CHK_012 <= hits_CHK_012 + 1;

  final begin
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
  end
endmodule
