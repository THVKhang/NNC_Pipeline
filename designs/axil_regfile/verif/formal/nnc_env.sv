// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

// ---------------------------------------------------------------------------
// Helper: counts the first cycles after time zero. It also tells when $past is
// valid (r_init_cnt != 0).
// ---------------------------------------------------------------------------
reg [1:0] r_init_cnt = 2'd0;
always @(posedge i_clk) begin
  if (r_init_cnt != 2'd2)
    r_init_cnt <= r_init_cnt + 2'd1;
end

// ENV-01: i_rst_n is held at 0 from time zero for at least 2 cycles. Cycle 0 is
//         already assumed in reset, so only the second cycle is added here (RF-12.1-08, RF-14-13)
always @(*) begin
  if (r_init_cnt == 2'd1)
    assume (!i_rst_n);
end

// ENV-02: Write address channel. When AWVALID is 1 and no AW transfer happens at
//         that edge (AWREADY is 0), the manager keeps AWVALID at 1 and keeps
//         AWADDR/AWPROT stable in the next cycle. This obligation ends if reset is
//         asserted in either cycle. A valid that appears after reset release is
//         a new request (RF-12.1-01, RF-12.1-07, RF-12.1-10, RF-12.1-11, RF-14-14)
always @(posedge i_clk) begin
  if ((r_init_cnt != 2'd0) && $past(i_rst_n) && i_rst_n &&
      $past(i_s_axi_awvalid) && !$past(o_s_axi_awready)) begin
    assume (i_s_axi_awvalid);
    assume ($stable(i_s_axi_awaddr));
    assume ($stable(i_s_axi_awprot));
  end
end

// ENV-03: Write data channel. When WVALID is 1 and no W transfer happens at that
//         edge, the manager keeps WVALID at 1 and keeps WDATA/WSTRB stable until
//         the transfer. Reset ends this obligation
//         (RF-12.1-01, RF-12.1-07, RF-12.1-10, RF-12.1-11, RF-14-14)
always @(posedge i_clk) begin
  if ((r_init_cnt != 2'd0) && $past(i_rst_n) && i_rst_n &&
      $past(i_s_axi_wvalid) && !$past(o_s_axi_wready)) begin
    assume (i_s_axi_wvalid);
    assume ($stable(i_s_axi_wdata));
    assume ($stable(i_s_axi_wstrb));
  end
end

// ENV-04: Read address channel. When ARVALID is 1 and no AR transfer happens at
//         that edge, the manager keeps ARVALID at 1 and keeps ARADDR/ARPROT
//         stable until the transfer. Reset ends this obligation
//         (RF-12.1-01, RF-12.1-07, RF-12.1-10, RF-12.1-11, RF-14-14)
always @(posedge i_clk) begin
  if ((r_init_cnt != 2'd0) && $past(i_rst_n) && i_rst_n &&
      $past(i_s_axi_arvalid) && !$past(o_s_axi_arready)) begin
    assume (i_s_axi_arvalid);
    assume ($stable(i_s_axi_araddr));
    assume ($stable(i_s_axi_arprot));
  end
end

// Not constrained on purpose:
//  - i_s_axi_bready and i_s_axi_rready can take any value: they may be held at 0
//    for any time, set before the valid, or depend on it (RF-12.1-02).
//  - i_status can take any value in any cycle. In this sampled formal model it
//    can only change between edges (RF-12.1-05).
//  - The valids are free while reset is active (RF-12.1-07). Reset can be
//    re-asserted at any time (RF-12.3-02, RF-12.4-11).
//  - Address values are free, including unmapped, unaligned and high-bit
//    addresses. Every wstrb value, including 4'b0000, and every prot value are
//    also allowed (RF-10.1-*).
endmodule
