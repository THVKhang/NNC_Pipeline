// ============================================================================
// Module  : m_apb_tlul_bridge
// Purpose : Structural top of the APB4 to TL-UL bridge. Holds the ports, the
//           parameters, the internal interface wires of section 5.1 and the
//           two instances u_apb_if (APB-facing) and u_tlul_if (TL-UL-facing).
//           No logic of its own.
// Spec    : m_apb_tlul_bridge_Design_Specification.md sections 5.1, 6.2, 7,
//           8, 14.2, 14.3
// ============================================================================
`default_nettype none

// REQ: BR-14.2-01, BR-3-15, BR-3-16, BR-3-39, BR-14.1-01, BR-14.1-02, BR-14.1-05
// REQ: BR-3-29, BR-7.2-01, BR-7.4-01, BR-3-41, BR-16-01
module m_apb_tlul_bridge #(
  // Parameter Description: Width of the byte address on both buses.
  // Parameter values: 16 to 32, default 32.
  // Parameter unit: bits
  parameter logic [31:0] PARA_ADDR_W   = 32'd32,
  // Parameter Description: Width of the TL-UL source identifier.
  // Parameter values: 1 to 8, default 8.
  // Parameter unit: bits
  parameter logic [31:0] PARA_SRC_W    = 32'd8,
  // Parameter Description: Constant source identifier of every request.
  // Parameter values: 0 to 2^PARA_SRC_W - 1, default 0.
  // Parameter unit: none (identifier value)
  parameter logic [31:0] PARA_SRC_ID   = 32'd0,
  // Parameter Description: Width of the a_user bits, always driven to zero.
  // Parameter values: 1 to 32, default 1.
  // Parameter unit: bits
  parameter logic [31:0] PARA_A_USER_W = 32'd1,
  // Parameter Description: Width of the unused d_sink input (width only).
  // Parameter values: 1 to 4, default 1.
  // Parameter unit: bits
  parameter logic [31:0] PARA_D_SINK_W = 32'd1,
  // Parameter Description: Width of the unused d_user input (width only).
  // Parameter values: 1 to 32, default 1.
  // Parameter unit: bits
  parameter logic [31:0] PARA_D_USER_W = 32'd1
) (
  // Clock and reset (single domain)
  input  wire                      i_clk_core,
  input  wire                      i_rst_n_core,
  // APB4 Completer
  input  wire                      i_apb_psel,
  input  wire                      i_apb_penable,
  input  wire                      i_apb_pwrite,
  input  wire [PARA_ADDR_W-1:0]    i_apb_paddr,
  // WAIVER: PPROT is accepted and ignored (DEC-007, section 14.3)
  // verilator lint_off UNUSED
  input  wire [2:0]                i_apb_pprot,
  // verilator lint_on UNUSED
  input  wire [3:0]                i_apb_pstrb,
  input  wire [31:0]               i_apb_pwdata,
  output logic                     o_apb_pready,
  output logic [31:0]              o_apb_prdata,
  output logic                     o_apb_pslverr,
  // TL-UL host, channel A
  output logic                     o_tlul_a_valid,
  input  wire                      i_tlul_a_ready,
  output logic [2:0]               o_tlul_a_opcode,
  output logic [2:0]               o_tlul_a_param,
  output logic [1:0]               o_tlul_a_size,
  output logic [PARA_SRC_W-1:0]    o_tlul_a_source,
  output logic [PARA_ADDR_W-1:0]   o_tlul_a_address,
  output logic [3:0]               o_tlul_a_mask,
  output logic [31:0]              o_tlul_a_data,
  output logic [PARA_A_USER_W-1:0] o_tlul_a_user,
  // TL-UL host, channel D
  input  wire                      i_tlul_d_valid,
  output logic                     o_tlul_d_ready,
  input  wire [2:0]                i_tlul_d_opcode,
  input  wire [PARA_SRC_W-1:0]     i_tlul_d_source,
  input  wire [31:0]               i_tlul_d_data,
  input  wire                      i_tlul_d_error,
  // WAIVER: d_param, d_size, d_sink, d_user present but unused (DEC-006, 14.3)
  // verilator lint_off UNUSED
  input  wire [2:0]                i_tlul_d_param,
  input  wire [1:0]                i_tlul_d_size,
  input  wire [PARA_D_SINK_W-1:0]  i_tlul_d_sink,
  input  wire [PARA_D_USER_W-1:0]  i_tlul_d_user
  // verilator lint_on UNUSED
);

  // --------------------------------------------------------------------------
  // Internal interface (section 5.1): wires only, no register crosses it.
  // --------------------------------------------------------------------------
  // REQ: BR-3-23, BR-14.2-04, BR-5.1-02, BR-5.1-03
  logic                   w_req_launch;
  logic                   w_req_wr;
  logic [PARA_ADDR_W-3:0] w_req_addr;
  logic [31:0]            w_req_wdata;
  logic                   w_resp_valid;
  logic                   w_resp_err;
  logic [31:0]            w_resp_rdata;

  // --------------------------------------------------------------------------
  // APB-facing module
  // --------------------------------------------------------------------------
  // REQ: BR-14.2-02
  m_apb_if #(
    .PARA_ADDR_W   (PARA_ADDR_W)
  ) u_apb_if (
    .i_clk_core    (i_clk_core),
    .i_rst_n_core  (i_rst_n_core),
    .i_apb_psel    (i_apb_psel),
    .i_apb_penable (i_apb_penable),
    .i_apb_pwrite  (i_apb_pwrite),
    .i_apb_paddr   (i_apb_paddr),
    .i_apb_pstrb   (i_apb_pstrb),
    .i_apb_pwdata  (i_apb_pwdata),
    .o_apb_pready  (o_apb_pready),
    .o_apb_prdata  (o_apb_prdata),
    .o_apb_pslverr (o_apb_pslverr),
    .o_req_launch  (w_req_launch),
    .o_req_wr      (w_req_wr),
    .o_req_addr    (w_req_addr),
    .o_req_wdata   (w_req_wdata),
    .i_resp_valid  (w_resp_valid),
    .i_resp_err    (w_resp_err),
    .i_resp_rdata  (w_resp_rdata)
  );

  // --------------------------------------------------------------------------
  // TL-UL-facing module
  // --------------------------------------------------------------------------
  // REQ: BR-14.2-03, BR-8-01, BR-8-02, BR-8-03, BR-8-05, BR-8-06, BR-8-07
  m_tlul_if #(
    .PARA_ADDR_W      (PARA_ADDR_W),
    .PARA_SRC_W       (PARA_SRC_W),
    .PARA_SRC_ID      (PARA_SRC_ID),
    .PARA_A_USER_W    (PARA_A_USER_W)
  ) u_tlul_if (
    .i_clk_core       (i_clk_core),
    .i_rst_n_core     (i_rst_n_core),
    .i_req_launch     (w_req_launch),
    .i_req_wr         (w_req_wr),
    .i_req_addr       (w_req_addr),
    .i_req_wdata      (w_req_wdata),
    .o_resp_valid     (w_resp_valid),
    .o_resp_err       (w_resp_err),
    .o_resp_rdata     (w_resp_rdata),
    .o_tlul_a_valid   (o_tlul_a_valid),
    .i_tlul_a_ready   (i_tlul_a_ready),
    .o_tlul_a_opcode  (o_tlul_a_opcode),
    .o_tlul_a_param   (o_tlul_a_param),
    .o_tlul_a_size    (o_tlul_a_size),
    .o_tlul_a_source  (o_tlul_a_source),
    .o_tlul_a_address (o_tlul_a_address),
    .o_tlul_a_mask    (o_tlul_a_mask),
    .o_tlul_a_data    (o_tlul_a_data),
    .o_tlul_a_user    (o_tlul_a_user),
    .i_tlul_d_valid   (i_tlul_d_valid),
    .o_tlul_d_ready   (o_tlul_d_ready),
    .i_tlul_d_opcode  (i_tlul_d_opcode),
    .i_tlul_d_source  (i_tlul_d_source),
    .i_tlul_d_data    (i_tlul_d_data),
    .i_tlul_d_error   (i_tlul_d_error)
  );

endmodule : m_apb_tlul_bridge

`default_nettype wire
