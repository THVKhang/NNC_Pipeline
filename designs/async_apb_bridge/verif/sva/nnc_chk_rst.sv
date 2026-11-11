module nnc_chk_rst #(
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

  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;
  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;

  // CHK-009: Requester-side outputs at reset value while i_rst_n_mst is low (AB2-15.3-17, AB2-3-37, AB2-3-38, AB2-7.3-01, AB2-5.4-06)
  a_CHK_009: assert property (@(posedge i_clk_mst) !i_rst_n_mst |-> (o_apb_pready == 1'b0 && o_apb_pslverr == 1'b0 && o_apb_prdata == '0 && o_apb_pruser == '0 && o_apb_pbuser == '0))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!i_rst_n_mst) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-009 (async part): one time step after falling edge of i_rst_n_mst
  always @(negedge i_rst_n_mst) begin
    #1;
    if (!i_rst_n_mst) begin
      hits_CHK_009++;
      if (!(o_apb_pready == 1'b0 && o_apb_pslverr == 1'b0 && o_apb_prdata == '0 && o_apb_pruser == '0 && o_apb_pbuser == '0)) begin
        fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time);
      end
    end
  end

  // CHK-010: Completer-side outputs at reset value while i_rst_n_slv is low (AB2-15.3-17, AB2-3-38, AB2-7.3-02, AB2-15.3-08, AB2-5.4-06)
  a_CHK_010: assert property (@(posedge i_clk_slv) !i_rst_n_slv |-> (o_apb_psel == 1'b0 && o_apb_penable == 1'b0 && o_apb_pwrite == 1'b0 && o_apb_paddr == '0 && o_apb_pprot == '0 && o_apb_pstrb == '0 && o_apb_pwdata == '0 && o_apb_pwakeup == 1'b0 && o_apb_pauser == '0 && o_apb_pwuser == '0))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!i_rst_n_slv) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-010 (async part): one time step after falling edge of i_rst_n_slv
  always @(negedge i_rst_n_slv) begin
    #1;
    if (!i_rst_n_slv) begin
      hits_CHK_010++;
      if (!(o_apb_psel == 1'b0 && o_apb_penable == 1'b0 && o_apb_pwrite == 1'b0 && o_apb_paddr == '0 && o_apb_pprot == '0 && o_apb_pstrb == '0 && o_apb_pwdata == '0 && o_apb_pwakeup == 1'b0 && o_apb_pauser == '0 && o_apb_pwuser == '0)) begin
        fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time);
      end
    end
  end

  final begin
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
  end
endmodule
