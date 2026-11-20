module nnc_chk_axi_wr #(
  parameter int PARA_NUM_REGS = 8,
  parameter int PARA_ADDR_W = 8,
  localparam int LPARA_REGS_W = PARA_NUM_REGS*32
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_s_axi_awvalid,
  input  logic                        o_s_axi_awready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_awaddr,
  input  logic [2:0]                  i_s_axi_awprot,
  input  logic                        i_s_axi_wvalid,
  input  logic                        o_s_axi_wready,
  input  logic [31:0]                 i_s_axi_wdata,
  input  logic [3:0]                  i_s_axi_wstrb,
  input  logic                        o_s_axi_bvalid,
  input  logic                        i_s_axi_bready,
  input  logic [1:0]                  o_s_axi_bresp,
  input  logic                        i_s_axi_arvalid,
  input  logic                        o_s_axi_arready,
  input  logic [(PARA_ADDR_W)-1:0]    i_s_axi_araddr,
  input  logic [2:0]                  i_s_axi_arprot,
  input  logic                        o_s_axi_rvalid,
  input  logic                        i_s_axi_rready,
  input  logic [31:0]                 o_s_axi_rdata,
  input  logic [1:0]                  o_s_axi_rresp,
  input  logic [(LPARA_REGS_W)-1:0]   o_regs,
  input  logic [31:0]                 i_status
);

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

  // Helper state
  localparam int LP_WW = PARA_ADDR_W-2;
  logic aw_held = 1'b0;
  logic w_held = 1'b0;
  logic b_pending = 1'b0;
  logic aw_mapped_q = 1'b0;

  wire aw_x = i_s_axi_awvalid && o_s_axi_awready;
  wire w_x  = i_s_axi_wvalid && o_s_axi_wready;
  wire b_x  = o_s_axi_bvalid && i_s_axi_bready;
  wire [LP_WW-1:0] aw_w = i_s_axi_awaddr[PARA_ADDR_W-1:2];
  wire aw_mapped = (32'(aw_w) < 32'(PARA_NUM_REGS)) || (32'(aw_w) == 32'd16);
  wire ec_now = (aw_x && (w_held || w_x)) || (w_x && aw_held);

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      aw_held <= 1'b0;
      w_held <= 1'b0;
      b_pending <= 1'b0;
    end else begin
      if (b_x) aw_held <= 1'b0;
      else if (aw_x) aw_held <= 1'b1;
      if (b_x) w_held <= 1'b0;
      else if (w_x) w_held <= 1'b1;
      if (b_x) b_pending <= 1'b0;
      else if (ec_now) b_pending <= 1'b1;
    end
  end

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) aw_mapped_q <= 1'b0;
    else if (aw_x && !aw_held) aw_mapped_q <= aw_mapped;
  end

  // CHK-006: o_s_axi_awready follows the held-write-address state (RF-7.2-01, RF-7.2-02, RF-7.2-07, RF-8.1-03, RF-8.2-02, RF-14-10, RF-14-12, RF-3-03)
  a_CHK_006: assert property (@(posedge i_clk) disable iff (!i_rst_n) $past(i_rst_n) |-> (o_s_axi_awready == !aw_held))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ($past(i_rst_n))) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: o_s_axi_wready follows the held-write-data state (RF-7.2-03, RF-7.2-04, RF-7.2-08, RF-8.1-03, RF-8.2-02, RF-14-10, RF-3-03)
  a_CHK_007: assert property (@(posedge i_clk) disable iff (!i_rst_n) $past(i_rst_n) |-> (o_s_axi_wready == !w_held))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ($past(i_rst_n))) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: o_s_axi_bvalid is exactly predicted: 1 from Ec until Eb, otherwise 0 (RF-7.4-01, RF-7.4-03, RF-7.4-04, RF-7.4-05, RF-7.2-06, RF-6.2-08, RF-6.2-10, RF-14-03, RF-1.2-09)
  a_CHK_008: assert property (@(posedge i_clk) disable iff (!i_rst_n) $past(i_rst_n) |-> (o_s_axi_bvalid == b_pending))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ($past(i_rst_n))) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: B response held stable under back-pressure (RF-7.4-02, RF-8.2-01, RF-12.2-05)
  a_CHK_009: assert property (@(posedge i_clk) disable iff (!i_rst_n) (o_s_axi_bvalid && !i_s_axi_bready) |=> (o_s_axi_bvalid && $stable(o_s_axi_bresp)))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_bvalid && !i_s_axi_bready)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-010: o_s_axi_bresp never EXOKAY or DECERR (RF-7.4-08, RF-1.3-01, RF-12.2-05)
  a_CHK_010: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_s_axi_bvalid |-> (o_s_axi_bresp == 2'b00 || o_s_axi_bresp == 2'b10))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_bvalid)) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: o_s_axi_bresp matches the decode of the address taken at Ea (RF-7.4-06, RF-7.4-07, RF-7.4-09, RF-10.1-01, RF-10.1-04, RF-7.3-08, RF-1.2-05, RF-7.1-02, RF-7.1-03, RF-7.1-04, RF-7.1-05, RF-7.1-06, RF-9-06, RF-9-08, RF-9-11, RF-9-12, RF-14-08, RF-12.2-04)
  a_CHK_011: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_s_axi_bvalid |-> (o_s_axi_bresp == (aw_mapped_q ? 2'b00 : 2'b10)))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_bvalid)) hits_CHK_011 <= hits_CHK_011 + 1;

  final begin
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
  end
endmodule
