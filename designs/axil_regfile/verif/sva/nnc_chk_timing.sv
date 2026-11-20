module nnc_chk_timing #(
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

  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;

  // helper: concatenation of all monitored outputs
  localparam int LPARA_OUTS_W = 1+1+1+2+1+1+32+2+LPARA_REGS_W;
  logic [LPARA_OUTS_W-1:0] chk017_outs;
  assign chk017_outs = {o_s_axi_awready, o_s_axi_wready, o_s_axi_bvalid, o_s_axi_bresp,
                        o_s_axi_arready, o_s_axi_rvalid, o_s_axi_rdata, o_s_axi_rresp, o_regs};

  time         chk017_t_pos = 0;
  time         chk017_t_rst = 0;
  int unsigned chk017_viol_cnt = 0;

  always @(posedge i_clk) chk017_t_pos = $time;
  always @(negedge i_rst_n) chk017_t_rst = $time;

  // any change of a monitored output while reset is released must coincide with a rising clock edge
  always @(chk017_outs) begin
    if (i_rst_n === 1'b1 && $time > 0) begin
      if (!(i_clk === 1'b1 && $time == chk017_t_pos) && !($time == chk017_t_rst))
        chk017_viol_cnt = chk017_viol_cnt + 1;
    end
  end

  // CHK-017: Outputs change only at a rising edge of i_clk or at reset assertion (RF-5-04, RF-6.1-01, RF-1.2-10)
  a_CHK_017: assert property (@(posedge i_clk) disable iff (!i_rst_n) 1'b1 |-> $stable(chk017_viol_cnt))
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (1'b1)) hits_CHK_017 <= hits_CHK_017 + 1;

  final begin
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
  end
endmodule
