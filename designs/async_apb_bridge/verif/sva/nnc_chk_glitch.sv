module nnc_chk_glitch #(
  parameter int PARA_APBCDC_ADDR_W = 32,
  parameter int PARA_APBCDC_DATA_W = 32,
  parameter int PARA_APBCDC_APB5 = 0,
  parameter int PARA_APBCDC_USER_REQ_W = 0,
  parameter int PARA_APBCDC_USER_DATA_W = 0,
  parameter int PARA_APBCDC_USER_RESP_W = 0,
  parameter int PARA_APBCDC_HS_TYPE = 0,
  parameter int PARA_APBCDC_CELL_TYPE = 2,
  localparam int LPARA_STRB_W = PARA_APBCDC_DATA_W / 8
) (
  input  logic                        i_clk_mst,
  input  logic                        i_rst_n_mst,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_APBCDC_ADDR_W)-1:0] i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [(LPARA_STRB_W)-1:0]   i_apb_pstrb,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_pwdata,
  input  logic                        i_apb_pwakeup,
  input  logic [(PARA_APBCDC_USER_REQ_W)-1:0] i_apb_pauser,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pwuser,
  input  logic                        o_apb_pready,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pruser,
  input  logic [(PARA_APBCDC_USER_RESP_W)-1:0] o_apb_pbuser,
  input  logic                        i_clk_slv,
  input  logic                        i_rst_n_slv,
  input  logic                        o_apb_psel,
  input  logic                        o_apb_penable,
  input  logic                        o_apb_pwrite,
  input  logic [(PARA_APBCDC_ADDR_W)-1:0] o_apb_paddr,
  input  logic [2:0]                  o_apb_pprot,
  input  logic [(LPARA_STRB_W)-1:0]   o_apb_pstrb,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_pwdata,
  input  logic                        o_apb_pwakeup,
  input  logic [(PARA_APBCDC_USER_REQ_W)-1:0] o_apb_pauser,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pwuser,
  input  logic                        i_apb_pready,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_prdata,
  input  logic                        i_apb_pslverr,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pruser,
  input  logic [(PARA_APBCDC_USER_RESP_W)-1:0] i_apb_pbuser
);

  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;

  // Helper event monitors: record the time of the last allowed edge per domain and count illegal output changes
  time         t_edge_m = 0;
  time         t_chg_m  = 0;
  bit          have_edge_m = 1'b0;
  bit          have_chg_m  = 1'b0;
  int unsigned glitch_cnt_m = 0;

  time         t_edge_s = 0;
  time         t_chg_s  = 0;
  bit          have_edge_s = 1'b0;
  bit          have_chg_s  = 1'b0;
  int unsigned glitch_cnt_s = 0;

  always @(posedge i_clk_mst or negedge i_rst_n_mst) begin
    t_edge_m = $time;
    have_edge_m = 1'b1;
  end

  always @(posedge i_clk_slv or negedge i_rst_n_slv) begin
    t_edge_s = $time;
    have_edge_s = 1'b1;
  end

  always @(o_apb_pready or o_apb_pslverr or o_apb_prdata or o_apb_pruser or o_apb_pbuser) begin
    if ($time != 0) begin
      if (!(have_edge_m && (t_edge_m == $time)) || (have_chg_m && (t_chg_m == $time)))
        glitch_cnt_m = glitch_cnt_m + 1;
      t_chg_m = $time;
      have_chg_m = 1'b1;
    end
  end

  always @(o_apb_psel or o_apb_penable or o_apb_pwrite or o_apb_paddr or o_apb_pprot or
           o_apb_pstrb or o_apb_pwdata or o_apb_pwakeup or o_apb_pauser or o_apb_pwuser) begin
    if ($time != 0) begin
      if (!(have_edge_s && (t_edge_s == $time)) || (have_chg_s && (t_chg_s == $time)))
        glitch_cnt_s = glitch_cnt_s + 1;
      t_chg_s = $time;
      have_chg_s = 1'b1;
    end
  end

  // CHK-002: Outputs change only at their own clock edge or on reset assertion (AB2-3-21, AB2-20.2-06)
  a_CHK_002: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) 1'b1 |-> $stable(glitch_cnt_m))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (1'b1)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-002: Outputs change only at their own clock edge or on reset assertion, slv domain (AB2-3-21, AB2-20.2-06)
  a_CHK_002_slv: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) 1'b1 |-> $stable(glitch_cnt_s))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (1'b1)) hits_CHK_002 <= hits_CHK_002 + 1;

  final begin
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
  end
endmodule
