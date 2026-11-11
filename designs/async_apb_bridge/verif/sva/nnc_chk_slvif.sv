module nnc_chk_slvif #(
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

  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;
  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;
  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;
  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;

  // CHK-011: No unknown completer-side outputs after reset (AB2-15.3-18)
  a_CHK_011: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) 1'b1 |-> !$isunknown({o_apb_psel, o_apb_penable, o_apb_pwrite, o_apb_paddr, o_apb_pprot, o_apb_pstrb, o_apb_pwdata, o_apb_pwakeup, o_apb_pauser, o_apb_pwuser}))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (1'b1)) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: Completer-side PENABLE implies PSEL; PSEL rises in a Setup cycle (AB2-15.3-06, AB2-3-14, AB2-3-15, AB2-5.4-05, AB2-6.3-01)
  a_CHK_012: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && (o_apb_penable || o_apb_psel)) |-> ((!o_apb_penable || o_apb_psel) && !(o_apb_psel && !$past(o_apb_psel) && o_apb_penable)))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && (o_apb_penable || o_apb_psel))) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: Completer-side Setup phase lasts exactly one cycle (AB2-3-15, AB2-5.3-05, AB2-10.1-06, AB2-15.3-06, AB2-6.3-01)
  a_CHK_013: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && o_apb_psel && !o_apb_penable) |=> (o_apb_psel && o_apb_penable))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && o_apb_psel && !o_apb_penable)) hits_CHK_013 <= hits_CHK_013 + 1;

  // CHK-014: Access phase held while the completer is not ready (AB2-3-14, AB2-3-10, AB2-5.3-06)
  a_CHK_014: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && o_apb_psel && o_apb_penable && !i_apb_pready) |=> (o_apb_psel && o_apb_penable))
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && o_apb_psel && o_apb_penable && !i_apb_pready)) hits_CHK_014 <= hits_CHK_014 + 1;

  // CHK-015: Completer-side transfer ends at the PREADY edge (AB2-3-17, AB2-10.3-03, AB2-10.1-07, AB2-5.3-07, AB2-15.3-08)
  a_CHK_015: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && o_apb_psel && o_apb_penable && i_apb_pready) |=> (!o_apb_psel && !o_apb_penable))
    else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && o_apb_psel && o_apb_penable && i_apb_pready)) hits_CHK_015 <= hits_CHK_015 + 1;

  // CHK-016: Completer-side request fields stable during a transfer (AB2-3-16, AB2-15.3-07, AB2-6.2-02..08, AB2-6.3-06, AB2-6.3-17)
  a_CHK_016: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && o_apb_psel && !(o_apb_penable && i_apb_pready)) |=> $stable({o_apb_pwrite, o_apb_paddr, o_apb_pprot, o_apb_pstrb, o_apb_pwdata, o_apb_pauser, o_apb_pwuser}))
    else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && o_apb_psel && !(o_apb_penable && i_apb_pready))) hits_CHK_016 <= hits_CHK_016 + 1;

  // CHK-017: Completer-side request fields loaded only at Setup entry (AB2-3-22, AB2-6.3-07, AB2-10.1-05, AB2-7.2-03)
  a_CHK_017: assert property (@(posedge i_clk_slv) disable iff (!i_rst_n_slv) (i_rst_n_mst && !$stable({o_apb_pwrite, o_apb_paddr, o_apb_pprot, o_apb_pstrb, o_apb_pwdata, o_apb_pauser, o_apb_pwuser})) |-> (o_apb_psel && !o_apb_penable && !$past(o_apb_psel)))
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (i_rst_n_mst && !$stable({o_apb_pwrite, o_apb_paddr, o_apb_pprot, o_apb_pstrb, o_apb_pwdata, o_apb_pauser, o_apb_pwuser}))) hits_CHK_017 <= hits_CHK_017 + 1;

  final begin
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
  end
endmodule
