module nnc_chk_apb #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;
  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;

  // helper registers: previous-edge samples of APB control
  logic h_p_psel   = 1'b0;
  logic h_p_pen    = 1'b0;
  logic h_p_pready = 1'b0;
  logic h_p_ok     = 1'b0;
  always_ff @(posedge i_clk_axi) begin
    h_p_psel   <= o_apb_psel;
    h_p_pen    <= o_apb_penable;
    h_p_pready <= i_apb_pready;
    h_p_ok     <= i_rst_n_axi;
  end

  // CHK-001: APB SETUP/ACCESS phase sequencing (AB-6.2-01, AB-10.3-04, AB-6.1-02)
  a_CHK_001: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_apb_psel || o_apb_penable || h_p_psel) |->
      ((!o_apb_penable || o_apb_psel) &&
       (!(h_p_ok && h_p_psel && !h_p_pen) || (o_apb_psel && o_apb_penable)) &&
       (!(h_p_ok && h_p_psel && h_p_pen && h_p_pready) || !o_apb_penable) &&
       (!(h_p_ok && o_apb_penable) || (h_p_psel && !(h_p_pen && h_p_pready)))))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((o_apb_psel || o_apb_penable || h_p_psel))) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: APB wait-state hold of control and payload (AB-3-22, AB-5.4-03, AB-6.2-10, AB-6.2-11, AB-6.2-07, AB-3-40, AB-15.2-02)
  a_CHK_002: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_apb_psel && o_apb_penable && !i_apb_pready) |=>
      (o_apb_psel && o_apb_penable && $stable(o_apb_paddr) && $stable(o_apb_pwrite) &&
       $stable(o_apb_pwdata) && $stable(o_apb_pstrb) && $stable(o_apb_pprot)))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((o_apb_psel && o_apb_penable && !i_apb_pready))) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: APB payload stable from SETUP into ACCESS (AB-6.2-07, AB-6.2-11)
  a_CHK_003: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_apb_psel && !o_apb_penable) |=>
      ($stable(o_apb_paddr) && $stable(o_apb_pwrite) && $stable(o_apb_pwdata) &&
       $stable(o_apb_pstrb) && $stable(o_apb_pprot)))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((o_apb_psel && !o_apb_penable))) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: PADDR word aligned (AB-3-10, AB-6.2-09, AB-9-13)
  a_CHK_004: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    1'b1 |-> (o_apb_paddr[1:0] == 2'b00))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (1'b1)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: PSTRB zero on APB reads (AB-3-12, AB-6.2-12)
  a_CHK_005: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (o_apb_psel && !o_apb_pwrite) |-> (o_apb_pstrb == 4'b0000))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((o_apb_psel && !o_apb_pwrite))) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: APB outputs zero when idle (AB-6.2-08)
  a_CHK_006: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi)
    (!o_apb_psel) |-> (!o_apb_penable && o_apb_paddr == 32'h0 && !o_apb_pwrite &&
                       o_apb_pwdata == 32'h0 && o_apb_pstrb == 4'h0 && o_apb_pprot == 3'b000))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((!o_apb_psel))) hits_CHK_006 <= hits_CHK_006 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
  end
endmodule
