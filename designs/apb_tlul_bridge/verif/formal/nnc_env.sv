// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
  parameter int PARA_ADDR_W = 32,
  parameter int PARA_SRC_W = 8,
  parameter int PARA_SRC_ID = 0,
  parameter int PARA_A_USER_W = 1,
  parameter int PARA_D_SINK_W = 1,
  parameter int PARA_D_USER_W = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_ADDR_W)-1:0]    i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [3:0]                  i_apb_pstrb,
  input  logic [31:0]                 i_apb_pwdata,
  input  logic                        o_apb_pready,
  input  logic [31:0]                 o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic                        o_tlul_a_valid,
  input  logic                        i_tlul_a_ready,
  input  logic [2:0]                  o_tlul_a_opcode,
  input  logic [2:0]                  o_tlul_a_param,
  input  logic [1:0]                  o_tlul_a_size,
  input  logic [(PARA_SRC_W)-1:0]     o_tlul_a_source,
  input  logic [(PARA_ADDR_W)-1:0]    o_tlul_a_address,
  input  logic [3:0]                  o_tlul_a_mask,
  input  logic [31:0]                 o_tlul_a_data,
  input  logic [(PARA_A_USER_W)-1:0]  o_tlul_a_user,
  input  logic                        i_tlul_d_valid,
  input  logic                        o_tlul_d_ready,
  input  logic [2:0]                  i_tlul_d_opcode,
  input  logic [(PARA_SRC_W)-1:0]     i_tlul_d_source,
  input  logic [31:0]                 i_tlul_d_data,
  input  logic                        i_tlul_d_error,
  input  logic [2:0]                  i_tlul_d_param,
  input  logic [1:0]                  i_tlul_d_size,
  input  logic [(PARA_D_SINK_W)-1:0]  i_tlul_d_sink,
  input  logic [(PARA_D_USER_W)-1:0]  i_tlul_d_user
);

  // ---------------------------------------------------------------------------
  // Helper state (built from interface signals only and cleared by the DUT reset)
  // ---------------------------------------------------------------------------
  // r_apb_cont = 1: in the previous cycle the APB Requester was in a Setup phase
  // (PSEL=1, PENABLE=0), or in an Access phase that was not yet completed
  // (PSEL=1, PENABLE=1, PREADY=0). In this cycle the transfer must continue in its Access phase.
  reg r_apb_cont = 1'b0;
  always @(posedge i_clk_core) begin
    if (!i_rst_n_core)
      r_apb_cont <= 1'b0;
    else
      r_apb_cont <= i_apb_psel && (!i_apb_penable || !o_apb_pready);
  end

  // r_d_stall = 1: in the previous cycle the device presented a D-channel beat
  // (d_valid=1) and the bridge did not accept it (d_ready=0).
  reg r_d_stall = 1'b0;
  always @(posedge i_clk_core) begin
    if (!i_rst_n_core)
      r_d_stall <= 1'b0;
    else
      r_d_stall <= i_tlul_d_valid && !o_tlul_d_ready;
  end

  // ---------------------------------------------------------------------------
  // APB Requester obligations
  // ---------------------------------------------------------------------------
  // ENV-01: The APB Requester is reset together with the bridge. While reset is asserted it is idle (PSEL=0, PENABLE=0). (BR-7.3-05, BR-3-32)
  always @(*) begin
    if (!i_rst_n_core)
      assume (!i_apb_psel && !i_apb_penable);
  end

  // ENV-02: A Setup phase is followed by an Access phase in the next cycle, and the Access phase lasts until PREADY. PSEL and PENABLE stay high until PREADY. (BR-6.3-01, BR-20-01)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && r_apb_cont)
      assume (i_apb_psel && i_apb_penable);
  end

  // ENV-03: PENABLE is high only in an Access phase. An Access phase follows a one-cycle Setup phase. After PREADY the next cycle is idle or a new Setup phase (back-to-back with PSEL held high), and it is never an Access phase. (BR-6.3-01, BR-20-01, BR-20-02, BR-3-37)
  always @(*) begin
    if (!r_apb_cont)
      assume (!i_apb_penable);
  end

  // ENV-04: PADDR, PWRITE, PWDATA and PSTRB stay unchanged from the Setup phase until PREADY. (BR-6.3-02, BR-20-01)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && r_apb_cont) begin
      assume ($stable(i_apb_paddr));
      assume ($stable(i_apb_pwrite));
      assume ($stable(i_apb_pwdata));
      assume ($stable(i_apb_pstrb));
    end
  end

  // ---------------------------------------------------------------------------
  // TL-UL device obligations
  // ---------------------------------------------------------------------------
  // ENV-05: TL-UL D-channel handshake. When the device has presented a D-channel beat that was not accepted (d_valid=1, d_ready=0), it keeps d_valid high and the D payload stable. (BR-15.1-02, BR-3-40)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && r_d_stall) begin
      assume (i_tlul_d_valid);
      assume ($stable(i_tlul_d_opcode));
      assume ($stable(i_tlul_d_source));
      assume ($stable(i_tlul_d_data));
      assume ($stable(i_tlul_d_error));
      assume ($stable(i_tlul_d_param));
      assume ($stable(i_tlul_d_size));
      assume ($stable(i_tlul_d_sink));
      assume ($stable(i_tlul_d_user));
    end
  end
endmodule
