module nnc_chk_axi_rd #(
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

  // helper state
  logic started;
  logic ar_held;
  logic r_pending;
  logic [31:0] exp_rdata;
  logic [1:0]  exp_rresp;

  wire ar_xfer = i_s_axi_arvalid && o_s_axi_arready;
  wire r_xfer  = o_s_axi_rvalid && i_s_axi_rready;
  wire [PARA_ADDR_W-3:0] ar_w = i_s_axi_araddr[PARA_ADDR_W-1:2];
  wire [31:0] ar_wi = 32'(ar_w);

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      started   <= 1'b0;
      ar_held   <= 1'b0;
      r_pending <= 1'b0;
      exp_rdata <= 32'h0;
      exp_rresp <= 2'b00;
    end else begin
      started <= 1'b1;
      if (r_xfer) begin
        ar_held   <= 1'b0;
        r_pending <= 1'b0;
      end else if (ar_xfer) begin
        ar_held   <= 1'b1;
        r_pending <= 1'b1;
      end
      if (ar_xfer) begin
        if (ar_wi < PARA_NUM_REGS) begin
          exp_rdata <= o_regs[32*ar_wi[7:0] +: 32];
          exp_rresp <= 2'b00;
        end else if (ar_wi == 32'd16) begin
          exp_rdata <= i_status;
          exp_rresp <= 2'b00;
        end else begin
          exp_rdata <= 32'h0000_0000;
          exp_rresp <= 2'b10;
        end
      end
    end
  end

  // CHK-001: o_s_axi_arready follows the held-read-address state (RF-7.5-01, RF-7.5-02, RF-7.5-03, RF-8.2-04, RF-8.1-03, RF-14-10, RF-3-03)
  a_CHK_001: assert property (@(posedge i_clk) disable iff (!i_rst_n) started |-> (o_s_axi_arready == !ar_held))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (started)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: o_s_axi_rvalid is exactly predicted (RF-7.5-04, RF-7.5-06, RF-7.5-07, RF-7.5-08, RF-6.2-08, RF-6.2-10, RF-14-04, RF-1.2-09)
  a_CHK_002: assert property (@(posedge i_clk) disable iff (!i_rst_n) started |-> (o_s_axi_rvalid == r_pending))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (started)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: R response held stable under back-pressure (RF-7.5-05, RF-8.2-03, RF-12.2-05, RF-7.5-11, RF-7.6-05)
  a_CHK_003: assert property (@(posedge i_clk) disable iff (!i_rst_n) (o_s_axi_rvalid && !i_s_axi_rready) |=> (o_s_axi_rvalid && $stable(o_s_axi_rdata) && $stable(o_s_axi_rresp)))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_rvalid && !i_s_axi_rready)) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: o_s_axi_rresp never EXOKAY or DECERR (RF-7.5-14, RF-1.3-01, RF-12.2-05)
  a_CHK_004: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_s_axi_rvalid |-> (o_s_axi_rresp == 2'b00 || o_s_axi_rresp == 2'b10))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_rvalid)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: Read data and response match the value sampled at Ear (RF-7.5-09, RF-7.5-10, RF-7.5-12, RF-7.5-13, RF-7.5-15, RF-12.2-04, RF-7.1-02, RF-7.1-03, RF-7.1-04, RF-7.1-05, RF-7.1-07, RF-7.6-03, RF-7.6-04, RF-7.6-06)
  a_CHK_005: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_s_axi_rvalid |-> (o_s_axi_rdata == exp_rdata && o_s_axi_rresp == exp_rresp))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (o_s_axi_rvalid)) hits_CHK_005 <= hits_CHK_005 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
  end
endmodule
