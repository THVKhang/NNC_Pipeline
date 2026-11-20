// ============================================================================
// Module  : m_axil_regfile_dec
// Purpose : Address decoder of the axil_regfile AXI4-Lite register file.
//           Takes the word index (address bits [PARA_ADDR_W-1:2]) and tells
//           whether it selects a read/write register (word index k with
//           0 <= k < PARA_NUM_REGS), the read-only status register (word
//           index 16), or nothing (unmapped). All word-index bits are
//           compared, so there is no aliasing.
// Spec    : axil_regfile_Design_Specification.md sections 7.1 (address
//           decode), 9 (register map), 10.2 (parameter extremes).
// Purely combinational; used once for the write address and once for the
// read address by m_axil_regfile.
// ============================================================================
module m_axil_regfile_dec #(
  parameter int PARA_NUM_REGS = 8,  // number of read/write registers (1 to 16)
  parameter int PARA_WIDX_W   = 6   // width of the word index = PARA_ADDR_W-2 (5 to 14)
) (
  input  logic [PARA_WIDX_W-1:0] i_widx,        // word index, address bits [PARA_ADDR_W-1:2]
  output logic                   o_reg_hit,     // selects read/write register o_reg_idx
  output logic                   o_status_hit,  // selects the status register (0x40)
  output logic [3:0]             o_reg_idx      // register number, valid when o_reg_hit is 1
);

  // Compare in a 32-bit domain so that every parameter value gives the same
  // width on both sides of each comparison.
  localparam logic [31:0] LPARA_NUM_REGS_U  = PARA_NUM_REGS;
  localparam logic [31:0] LPARA_STATUS_WIDX = 32'd16;

  logic [31:0] widx_ext;

  // REQ: RF-7.1-05, RF-14-08
  // Full decode: every bit of the word index takes part in the comparisons.
  assign widx_ext = {{(32-PARA_WIDX_W){1'b0}}, i_widx};

  // REQ: RF-7.1-02, RF-1.2-01, RF-10.2-01, RF-10.2-02, RF-9-13
  // Word index k < PARA_NUM_REGS selects read/write register k.
  assign o_reg_hit = (widx_ext < LPARA_NUM_REGS_U);

  // REQ: RF-7.1-03, RF-1.1-04
  // Word index 16 (byte address 0x40 to 0x43) selects the status register.
  assign o_status_hit = (widx_ext == LPARA_STATUS_WIDX);

  // REQ: RF-7.1-04, RF-10.2-03, RF-10.2-04, RF-9-09
  // Every other word index is unmapped (o_reg_hit = o_status_hit = 0).
  // The register number is only used when o_reg_hit is 1, in which case the
  // word index is below 16 and fits in its 4 low bits.
  assign o_reg_idx = i_widx[3:0];

endmodule
