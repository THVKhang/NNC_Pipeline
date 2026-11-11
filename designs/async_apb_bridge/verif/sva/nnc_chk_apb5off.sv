module nnc_chk_apb5off #(
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

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;

  localparam bit LP_ZERO_WAKEUP = (PARA_APBCDC_APB5 == 0);
  localparam bit LP_ZERO_PAUSER = (PARA_APBCDC_APB5 == 0) || (PARA_APBCDC_USER_REQ_W == 0);
  localparam bit LP_ZERO_DUSER  = (PARA_APBCDC_APB5 == 0) || (PARA_APBCDC_USER_DATA_W == 0);
  localparam bit LP_ZERO_BUSER  = (PARA_APBCDC_APB5 == 0) || (PARA_APBCDC_USER_RESP_W == 0);

  // CHK-001: Absent APB5 signals drive zero, mst domain (AB2-3-45, AB2-20.2-08, AB2-3-44, AB2-8-04, AB2-8-05, AB2-8-06, AB2-8-08)
  a_CHK_001: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) 1'b1 |-> ((!LP_ZERO_DUSER || (o_apb_pruser == '0)) && (!LP_ZERO_BUSER || (o_apb_pbuser == '0))))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-001: Absent APB5 signals drive zero, slv domain (AB2-3-45, AB2-20.2-08, AB2-3-44, AB2-8-04, AB2-8-05, AB2-8-06, AB2-8-08)
  a_CHK_001_slv: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) 1'b1 |-> ((!LP_ZERO_WAKEUP || (o_apb_pwakeup == 1'b0)) && (!LP_ZERO_PAUSER || (o_apb_pauser == '0)) && (!LP_ZERO_DUSER || (o_apb_pwuser == '0))))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (1'b1)) hits_CHK_001 <= hits_CHK_001 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
  end
endmodule
