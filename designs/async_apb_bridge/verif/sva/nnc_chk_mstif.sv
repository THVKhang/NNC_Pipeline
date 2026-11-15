module nnc_chk_mstif #(
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

  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;
  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;

  // helper registers (i_clk_mst domain)
  logic chk6_armed;      // a Setup cycle was seen since the last PREADY
  logic chk6_prev_setup; // previous edge was a Setup cycle
  logic chk8_released = 1'b0;  // first reset release seen
  logic chk8_is_read;    // transfer in progress is a read (sampled at Setup)

  always_ff @(posedge i_clk_mst) begin
    if (!i_rst_n_mst) begin
      chk6_armed <= 1'b0;
      chk6_prev_setup <= 1'b0;
      chk8_is_read <= 1'b0;
    end else begin
      chk6_prev_setup <= (i_apb_psel && !i_apb_penable);
      if (i_apb_psel && !i_apb_penable) begin
        chk6_armed <= 1'b1;
        chk8_is_read <= !i_apb_pwrite;
      end else if (o_apb_pready) begin
        chk6_armed <= 1'b0;
      end
    end
  end

  always_ff @(posedge i_clk_mst) begin
    if (i_rst_n_mst) chk8_released <= 1'b1;
  end

  // CHK-003: Requester-side PREADY only in an Access cycle (AB2-15.3-02, AB2-3-08, AB2-6.3-04, AB2-20.2-06, AB2-2.3-01)
  a_CHK_003: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) (o_apb_pready && i_rst_n_slv) |-> (i_apb_psel && i_apb_penable))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && i_rst_n_slv)) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Requester-side PREADY is a one-cycle pulse (AB2-3-08, AB2-15.3-03, AB2-10.1-04, AB2-5.4-04)
  a_CHK_004: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) (o_apb_pready && i_rst_n_slv) |=> (!o_apb_pready && !o_apb_pslverr))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && i_rst_n_slv)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: PSLVERR only in the PREADY cycle, no sticky error (AB2-3-11, AB2-3-23, AB2-15.3-04, AB2-6.2-01, AB2-6.3-09, AB2-12-08, AB2-10.1-04)
  a_CHK_005: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) (o_apb_pslverr && i_rst_n_slv) |-> o_apb_pready)
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pslverr && i_rst_n_slv)) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: At most one PREADY per accepted Setup phase (AB2-3-07, AB2-15.3-03, AB2-5.4-04, AB2-10.1-02)
  a_CHK_006: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) (o_apb_pready && i_rst_n_slv) |-> (chk6_armed && !chk6_prev_setup && !(i_apb_psel && !i_apb_penable)))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && i_rst_n_slv)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: Response outputs stable outside the PREADY cycle (AB2-3-22)
  a_CHK_007: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) (!o_apb_pready && i_rst_n_slv) |-> ($stable(o_apb_prdata) && $stable(o_apb_pruser) && $stable(o_apb_pbuser)))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (!o_apb_pready && i_rst_n_slv)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: No unknown requester-side outputs after reset (AB2-15.3-18, AB2-6.3-05)
  a_CHK_008: assert property (@(posedge i_clk_mst) disable iff (!i_rst_n_mst) chk8_released |-> (!$isunknown({o_apb_pready, o_apb_pslverr, o_apb_prdata, o_apb_pruser, o_apb_pbuser}) && !(o_apb_pready && chk8_is_read && $isunknown(o_apb_prdata))))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (chk8_released)) hits_CHK_008 <= hits_CHK_008 + 1;

  final begin
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
  end
endmodule
