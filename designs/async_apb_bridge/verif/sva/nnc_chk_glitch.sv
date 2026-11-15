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

  // helpers for CHK-002: event monitors, one per output domain
  int unsigned gl_cnt_m = 0;
  int unsigned gl_cnt_s = 0;
  time         edge_t_m = 0;
  time         edge_t_s = 0;
  logic        seen_m = 1'b0;
  logic        seen_s = 1'b0;
  logic        pclk_m = 1'b0;
  logic        prst_m = 1'b1;
  logic        pclk_s = 1'b0;
  logic        prst_s = 1'b1;
  logic        e_m, e_s, c_m, c_s;

  logic                                p_pready;
  logic [(PARA_APBCDC_DATA_W)-1:0]     p_prdata;
  logic                                p_pslverr;
  logic [(PARA_APBCDC_USER_DATA_W)-1:0] p_pruser;
  logic [(PARA_APBCDC_USER_RESP_W)-1:0] p_pbuser;

  logic                                q_psel, q_penable, q_pwrite, q_pwakeup;
  logic [(PARA_APBCDC_ADDR_W)-1:0]     q_paddr;
  logic [2:0]                          q_pprot;
  logic [(LPARA_STRB_W)-1:0]           q_pstrb;
  logic [(PARA_APBCDC_DATA_W)-1:0]     q_pwdata;
  logic [(PARA_APBCDC_USER_REQ_W)-1:0] q_pauser;
  logic [(PARA_APBCDC_USER_DATA_W)-1:0] q_pwuser;

  // master-domain outputs: any change outside a clk_mst rise / rst_n_mst fall time step is counted
  always @(i_clk_mst or i_rst_n_mst or o_apb_pready or o_apb_prdata or o_apb_pslverr or
           o_apb_pruser or o_apb_pbuser) begin
    e_m = (i_clk_mst === 1'b1 && pclk_m !== 1'b1) || (i_rst_n_mst === 1'b0 && prst_m !== 1'b0);
    c_m = (o_apb_pready !== p_pready) || (o_apb_prdata !== p_prdata) ||
          (o_apb_pslverr !== p_pslverr) || (o_apb_pruser !== p_pruser) ||
          (o_apb_pbuser !== p_pbuser);
    if (e_m) begin
      seen_m = 1'b1;
      edge_t_m = $time;
    end
    if (c_m && seen_m && (edge_t_m != $time)) gl_cnt_m = gl_cnt_m + 1;
    pclk_m = i_clk_mst;
    prst_m = i_rst_n_mst;
    p_pready = o_apb_pready;
    p_prdata = o_apb_prdata;
    p_pslverr = o_apb_pslverr;
    p_pruser = o_apb_pruser;
    p_pbuser = o_apb_pbuser;
  end

  // slave-domain outputs: any change outside a clk_slv rise / rst_n_slv fall time step is counted
  always @(i_clk_slv or i_rst_n_slv or o_apb_psel or o_apb_penable or o_apb_pwrite or
          o_apb_paddr or o_apb_pprot or o_apb_pstrb or o_apb_pwdata or o_apb_pwakeup or
          o_apb_pauser or o_apb_pwuser) begin
    e_s = (i_clk_slv === 1'b1 && pclk_s !== 1'b1) || (i_rst_n_slv === 1'b0 && prst_s !== 1'b0);
    c_s = (o_apb_psel !== q_psel) || (o_apb_penable !== q_penable) ||
          (o_apb_pwrite !== q_pwrite) || (o_apb_paddr !== q_paddr) ||
          (o_apb_pprot !== q_pprot) || (o_apb_pstrb !== q_pstrb) ||
          (o_apb_pwdata !== q_pwdata) || (o_apb_pwakeup !== q_pwakeup) ||
          (o_apb_pauser !== q_pauser) || (o_apb_pwuser !== q_pwuser);
    if (e_s) begin
      seen_s = 1'b1;
      edge_t_s = $time;
    end
    if (c_s && seen_s && (edge_t_s != $time)) gl_cnt_s = gl_cnt_s + 1;
    pclk_s = i_clk_slv;
    prst_s = i_rst_n_slv;
    q_psel = o_apb_psel;
    q_penable = o_apb_penable;
    q_pwrite = o_apb_pwrite;
    q_paddr = o_apb_paddr;
    q_pprot = o_apb_pprot;
    q_pstrb = o_apb_pstrb;
    q_pwdata = o_apb_pwdata;
    q_pwakeup = o_apb_pwakeup;
    q_pauser = o_apb_pauser;
    q_pwuser = o_apb_pwuser;
  end

  // CHK-002: Outputs change only at their own clock edge or on reset assertion (AB2-3-21, AB2-20.2-06)
  a_CHK_002: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) 1'b1 |-> $stable(gl_cnt_m))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (1'b1)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-002: slave-domain outputs, same check on the completer clock (AB2-3-21, AB2-20.2-06)
  a_CHK_002_slv: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) 1'b1 |-> $stable(gl_cnt_s))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
  end
endmodule
