module nnc_chk_regs #(
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

  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;

  // Reference model helpers for CHK-012
  logic                       seen_rst_012 = 1'b0;
  logic                       aw_pend_012;
  logic                       w_pend_012;
  logic [(PARA_ADDR_W)-1:0]   aw_q_012;
  logic [31:0]                wd_q_012;
  logic [3:0]                 ws_q_012;
  logic [(LPARA_REGS_W)-1:0]  m_012;

  wire                        aw_x_012    = i_s_axi_awvalid && o_s_axi_awready;
  wire                        w_x_012     = i_s_axi_wvalid && o_s_axi_wready;
  wire                        aw_have_012 = aw_pend_012 || aw_x_012;
  wire                        w_have_012  = w_pend_012 || w_x_012;
  wire [(PARA_ADDR_W)-1:0]    aw_cur_012  = aw_pend_012 ? aw_q_012 : i_s_axi_awaddr;
  wire [31:0]                 wd_cur_012  = w_pend_012 ? wd_q_012 : i_s_axi_wdata;
  wire [3:0]                  ws_cur_012  = w_pend_012 ? ws_q_012 : i_s_axi_wstrb;
  wire [(PARA_ADDR_W)-3:0]    widx_012    = aw_cur_012[(PARA_ADDR_W)-1:2];

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      seen_rst_012 <= 1'b1;
      aw_pend_012  <= 1'b0;
      w_pend_012   <= 1'b0;
      aw_q_012     <= '0;
      wd_q_012     <= '0;
      ws_q_012     <= '0;
      m_012        <= '0;
    end else begin
      if (aw_x_012 && !aw_pend_012) begin
        aw_pend_012 <= 1'b1;
        aw_q_012    <= i_s_axi_awaddr;
      end
      if (w_x_012 && !w_pend_012) begin
        w_pend_012 <= 1'b1;
        wd_q_012   <= i_s_axi_wdata;
        ws_q_012   <= i_s_axi_wstrb;
      end
      if (aw_have_012 && w_have_012) begin
        aw_pend_012 <= 1'b0;
        w_pend_012  <= 1'b0;
        for (int k = 0; k < PARA_NUM_REGS; k++) begin
          if (int'(widx_012) == k) begin
            for (int i = 0; i < 4; i++) begin
              if (ws_cur_012[i])
                m_012[32*k + 8*i +: 8] <= wd_cur_012[8*i +: 8]; // nnc-literal-ok (byte lane width, not a parameter)
            end
          end
        end
      end
    end
  end

  // CHK-012: o_regs equals the reference register model every cycle (RF-1.1-03, RF-1.2-03, RF-5-01, RF-5-02, RF-5-03, RF-7.2-09, RF-7.3-01, RF-7.3-02, RF-7.3-03, RF-7.3-04, RF-7.3-05, RF-7.3-06, RF-7.3-07, RF-7.3-08, RF-7.3-09, RF-7.5-16, RF-7.6-02, RF-7.1-06, RF-9-02, RF-9-03, RF-9-06, RF-9-08, RF-9-11, RF-10.1-01, RF-10.1-03, RF-10.1-04, RF-12.2-02, RF-12.2-03, RF-14-05)
  a_CHK_012: assert property (@(posedge i_clk) disable iff (!i_rst_n) seen_rst_012 |-> (o_regs == m_012))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (seen_rst_012)) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-012: falling-edge comparison of o_regs with the model updated at the preceding rising edge
  a_CHK_012_neg: assert property (@(negedge i_clk) disable iff (!i_rst_n) seen_rst_012 |-> (o_regs == m_012))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
  end
endmodule
