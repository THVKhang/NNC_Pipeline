module nnc_chk_reset #(
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

  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;
  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;
  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;

  // helper: previous-cycle reset level (starts at 1 so R1 needs a prior observed reset)
  logic rst_q = 1'b1;
  always_ff @(posedge i_clk) rst_q <= i_rst_n;
  wire r1_edge = i_rst_n && !rst_q;

  // CHK-013: Handshake outputs are 0 while reset is asserted; no transfer while i_rst_n=0 (RF-6.2-02, RF-14-01, RF-6.2-05, RF-3-01, RF-10.1-10)
  a_CHK_013: assert property (@(posedge i_clk) (!i_rst_n) |-> (o_s_axi_awready == 1'b0 && o_s_axi_wready == 1'b0 && o_s_axi_arready == 1'b0 && o_s_axi_bvalid == 1'b0 && o_s_axi_rvalid == 1'b0))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  a_CHK_013_n: assert property (@(negedge i_clk) (!i_rst_n) |-> (o_s_axi_awready == 1'b0 && o_s_axi_wready == 1'b0 && o_s_axi_arready == 1'b0 && o_s_axi_bvalid == 1'b0 && o_s_axi_rvalid == 1'b0))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk) if (!i_rst_n) hits_CHK_013 <= hits_CHK_013 + 1;

  // CHK-014: Data outputs and o_regs are 0 while reset is asserted (RF-6.2-03, RF-6.2-04, RF-14-09, RF-1.2-02, RF-9-01, RF-12.2-04)
  a_CHK_014: assert property (@(posedge i_clk) (!i_rst_n) |-> (o_s_axi_bresp == 2'b00 && o_s_axi_rresp == 2'b00 && o_s_axi_rdata == 32'h0000_0000 && o_regs == '0))
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  a_CHK_014_n: assert property (@(negedge i_clk) (!i_rst_n) |-> (o_s_axi_bresp == 2'b00 && o_s_axi_rresp == 2'b00 && o_s_axi_rdata == 32'h0000_0000 && o_regs == '0))
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk) if (!i_rst_n) hits_CHK_014 <= hits_CHK_014 + 1;

  // CHK-015: No transfer at R1 (RF-6.2-06, RF-14-01)
  a_CHK_015: assert property (@(posedge i_clk) disable iff (!i_rst_n) r1_edge |-> (o_s_axi_awready == 1'b0 && o_s_axi_wready == 1'b0 && o_s_axi_arready == 1'b0 && o_s_axi_bvalid == 1'b0 && o_s_axi_rvalid == 1'b0))
    else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1_edge)) hits_CHK_015 <= hits_CHK_015 + 1;

  // CHK-016: Readies are 1 from R1 (RF-6.2-07, RF-14-01)
  a_CHK_016: assert property (@(posedge i_clk) disable iff (!i_rst_n) r1_edge |=> (o_s_axi_awready == 1'b1 && o_s_axi_wready == 1'b1 && o_s_axi_arready == 1'b1))
    else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (r1_edge)) hits_CHK_016 <= hits_CHK_016 + 1;

  final begin
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
  end
endmodule
