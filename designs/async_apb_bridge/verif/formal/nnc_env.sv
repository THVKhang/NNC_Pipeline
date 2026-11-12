// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Helper registers (driven only from interface signals; initial value 0)
  // ---------------------------------------------------------------------------
  // Requester-side transfer in progress: set after the Setup cycle, cleared after the PREADY cycle
  reg r_env_mst_busy = 1'b0;

  always @(posedge i_clk_mst) begin
    if (!i_rst_n_mst || !i_rst_n_slv)
      r_env_mst_busy <= 1'b0;
    else if (r_env_mst_busy) begin
      if (o_apb_pready)
        r_env_mst_busy <= 1'b0;
    end
    else if (i_apb_psel && !i_apb_penable)
      r_env_mst_busy <= 1'b1;
  end

  // APB5: PWAKEUP was high together with PSEL -> must stay high until PREADY
  reg r_env_wk_hold = 1'b0;

  always @(posedge i_clk_mst) begin
    if (!i_rst_n_mst || !i_rst_n_slv || (PARA_APBCDC_APB5 == 0))
      r_env_wk_hold <= 1'b0;
    else if (o_apb_pready || !i_apb_psel)
      r_env_wk_hold <= 1'b0;
    else if (i_apb_pwakeup)
      r_env_wk_hold <= 1'b1;
  end

  // ---------------------------------------------------------------------------
  // Reset sequencing (evaluated on the formal global clock: resets are
  // asynchronous inputs and may change between DUT clock edges)
  // ---------------------------------------------------------------------------
  // ENV-01: Resets are asserted together: when i_rst_n_mst falls, i_rst_n_slv is low in the same step (never mst alone) (AB2-3-39, AB2-3-41, AB2-6.3-27)
  always @($global_clock)
    if ($fell(i_rst_n_mst))
      assume (!i_rst_n_slv);

  // ENV-02: Resets are asserted together: when i_rst_n_slv falls, i_rst_n_mst is low in the same step (never slv alone) (AB2-3-39, AB2-3-41, AB2-6.3-27)
  always @($global_clock)
    if ($fell(i_rst_n_slv))
      assume (!i_rst_n_mst);

  // ENV-06: i_rst_n_mst is released synchronously to its domain clock: it rises only together with a rising edge of i_clk_mst (AB2-3-39)
  always @($global_clock)
    if ($rose(i_rst_n_mst))
      assume ($rose(i_clk_mst));

  // ENV-07: i_rst_n_slv is released synchronously to its domain clock: it rises only together with a rising edge of i_clk_slv (AB2-3-39)
  always @($global_clock)
    if ($rose(i_rst_n_slv))
      assume ($rose(i_clk_slv));

  // ENV-03: The requester keeps i_apb_psel low while either reset is asserted; no transfer starts before both resets are released (AB2-7.3-04)
  always @(*)
    if (!i_rst_n_mst || !i_rst_n_slv)
      assume (!i_apb_psel);

  // ---------------------------------------------------------------------------
  // Requester-side APB sequencing (non-pipelined APB)
  // ---------------------------------------------------------------------------
  // ENV-04: After the one-cycle Setup phase the requester stays in Access (PSEL and PENABLE high) until the PREADY cycle; no new Setup before PREADY (AB2-6.3-01, AB2-10.4-02, AB2-20.2-01, AB2-15.3-02)
  always @(posedge i_clk_mst)
    if (i_rst_n_mst && i_rst_n_slv && r_env_mst_busy)
      assume (i_apb_psel && i_apb_penable);

  // ---------------------------------------------------------------------------
  // APB5 wake-up
  // ---------------------------------------------------------------------------
  // ENV-05: APB5 only: once i_apb_pwakeup is high in a cycle with i_apb_psel, it stays high until o_apb_pready (AB2-6.3-13, AB2-8-04)
  always @(posedge i_clk_mst)
    if ((PARA_APBCDC_APB5 != 0) && i_rst_n_mst && i_rst_n_slv && r_env_wk_hold && !o_apb_pready)
      assume (i_apb_pwakeup);
endmodule
