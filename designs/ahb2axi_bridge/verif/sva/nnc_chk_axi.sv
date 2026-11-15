module nnc_chk_axi #(
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

  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;
  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;
  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;

  // ---------------- helpers ----------------
  wire aw_hs = o_axi_awvalid && i_axi_awready;
  wire b_hs  = i_axi_bvalid  && o_axi_bready;
  wire ar_hs = o_axi_arvalid && i_axi_arready;
  wire r_hs  = i_axi_rvalid  && o_axi_rready && i_axi_rlast;
  wire w_hs  = o_axi_wvalid  && i_axi_wready;

  // outstanding counters (CHK-008)
  int nw_q;
  int nr_q;
  always_ff @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      nw_q <= 0;
      nr_q <= 0;
    end else begin
      nw_q <= nw_q + (aw_hs ? 1 : 0) - (b_hs ? 1 : 0);
      nr_q <= nr_q + (ar_hs ? 1 : 0) - (r_hs ? 1 : 0);
    end
  end

  // W burst tracking (CHK-010)
  int unsigned aw_cnt_q;
  int unsigned wb_cnt_q;
  int unsigned wbeat_q;
  logic [7:0]  awlen_q;
  always_ff @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      aw_cnt_q <= 0;
      wb_cnt_q <= 0;
      wbeat_q  <= 0;
      awlen_q  <= 8'h00;
    end else begin
      if (aw_hs) begin
        aw_cnt_q <= aw_cnt_q + 1;
        awlen_q  <= o_axi_awlen;
      end
      if (w_hs) begin
        if (o_axi_wlast) begin
          wb_cnt_q <= wb_cnt_q + 1;
          wbeat_q  <= 0;
        end else if (wbeat_q != 32'hFFFF_FFFF) begin
          wbeat_q <= wbeat_q + 1;
        end
      end
    end
  end
  wire        w_aw_prev  = (aw_cnt_q > wb_cnt_q);
  wire        w_avail    = w_aw_prev || aw_hs;
  wire [7:0]  w_len      = w_aw_prev ? awlen_q : o_axi_awlen;
  wire        w_beat_last = (wbeat_q == {24'b0, w_len});

  // AW shape helpers (CHK-011/012)
  wire [31:0] aw_mask  = (32'd1 << o_axi_awsize) - 32'd1;
  wire [31:0] ar_mask  = (32'd1 << o_axi_arsize) - 32'd1;
  wire [31:0] aw_bytes = (32'({24'b0, o_axi_awlen}) + 32'd1) << o_axi_awsize;
  wire [31:0] aw_end   = {20'b0, o_axi_awaddr[11:0]} + aw_bytes;

  // CHK-003: AXI lock outputs tied low (AA-T1.7.2.2-11, AA-18-05, AA-T1.7.3.1-15)
  a_CHK_003: assert property (@(posedge i_clk_core) 1'b1 |-> (o_axi_awlock == 1'b0 && o_axi_arlock == 1'b0))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (1'b1) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Reads are always single-beat INCR (AA-T1.7.2.2-20, AA-T1.7.2.2-21, AA-15.3-03, AA-1.1-04, AA-T1.7.3.2-03, AA-5.4-07)
  a_CHK_004: assert property (@(posedge i_clk_core) 1'b1 |-> (o_axi_arlen == 8'h00 && o_axi_arburst == 2'b01))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (1'b1) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: AW VALID and payload stable until AWREADY (AA-T1.7.2.2-12, AA-5.4-04, AA-15.3-01, AA-12-10, AA-T1.7.3.2-01, AA-15.2-01)
  a_CHK_005: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_awvalid && !i_axi_awready) |=> (o_axi_awvalid && $stable(o_axi_awid) && $stable(o_axi_awaddr) && $stable(o_axi_awlen) &&
       $stable(o_axi_awsize) && $stable(o_axi_awburst) && $stable(o_axi_awcache) && $stable(o_axi_awprot)))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_awvalid && !i_axi_awready)) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: W VALID and payload stable until WREADY (AA-T1.7.2.2-14, AA-5.4-04, AA-15.3-01, AA-12-10, AA-T1.7.3.2-01)
  a_CHK_006: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_wvalid && !i_axi_wready) |=> (o_axi_wvalid && $stable(o_axi_wdata) && $stable(o_axi_wstrb) && $stable(o_axi_wlast)))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_wvalid && !i_axi_wready)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: AR VALID and payload stable until ARREADY (AA-T1.7.2.2-22, AA-5.4-04, AA-15.3-01, AA-12-10, AA-T1.7.3.2-01)
  a_CHK_007: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_arvalid && !i_axi_arready) |=> (o_axi_arvalid && $stable(o_axi_arid) && $stable(o_axi_araddr) && $stable(o_axi_arlen) &&
       $stable(o_axi_arsize) && $stable(o_axi_arburst) && $stable(o_axi_arcache) && $stable(o_axi_arprot)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_arvalid && !i_axi_arready)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: At most one outstanding read and one outstanding write (AA-5.4-06, AA-T1.7.3.2-02, AA-T1.7.3.2-06, AA-1.1-01)
  a_CHK_008: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    ((nw_q == 1 && !b_hs) || (nr_q == 1 && !(i_axi_rvalid && o_axi_rready))) |->
      ((!(nw_q == 1 && !b_hs) || !o_axi_awvalid) && (!(nr_q == 1 && !(i_axi_rvalid && o_axi_rready)) || !o_axi_arvalid)))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && ((nw_q == 1 && !b_hs) || (nr_q == 1 && !(i_axi_rvalid && o_axi_rready)))) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: AXI IDs stay below the configured ID count (AA-15.3-09, AA-3-37)
  a_CHK_009: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_arvalid || o_axi_awvalid) |->
      ((!o_axi_arvalid || (int'(o_axi_arid) < PARA_RD_ID_COUNT)) && (!o_axi_awvalid || (int'(o_axi_awid) < PARA_WR_ID_COUNT))))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_arvalid || o_axi_awvalid)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: W beat count and WLAST match AWLEN (AA-3-12, AA-5.4-07, AA-T1.7.2.2-16, AA-15.3-04, AA-9-09)
  a_CHK_010: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (w_hs && w_avail) |-> (o_axi_wlast == w_beat_last))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (w_hs && w_avail)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: AW burst shape is legal and never crosses 4 KiB (AA-T1.7.3.2-04, AA-3-22, AA-T1.7.3.1-12, AA-9-09)
  a_CHK_011: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    o_axi_awvalid |-> ((o_axi_awlen <= 8'd15) &&
      (o_axi_awburst == 2'b01 || o_axi_awburst == 2'b10) &&
      (o_axi_awburst != 2'b10 || ((o_axi_awlen == 8'd3 || o_axi_awlen == 8'd7 || o_axi_awlen == 8'd15) && ((o_axi_awaddr & aw_mask) == 32'd0))) &&
      (o_axi_awburst != 2'b01 || (aw_end <= 32'd4096))))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_awvalid)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: Issued AXI requests use supported sizes and are aligned (AA-T1.7.3.1-04, AA-9-04)
  a_CHK_012: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_arvalid || o_axi_awvalid) |->
      ((!o_axi_arvalid || (o_axi_arsize <= 3'd2 && ((o_axi_araddr & ar_mask) == 32'd0))) &&
       (!o_axi_awvalid || (o_axi_awsize <= 3'd2 && ((o_axi_awaddr & aw_mask) == 32'd0)))))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_arvalid || o_axi_awvalid)) hits_CHK_012 <= hits_CHK_012 + 1;

  final begin
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
  end
endmodule
