// ============================================================================
// Module  : m_tlul_if
// Purpose : TL-UL host side of the APB4 to TL-UL bridge. Holds the channel A
//           flops loaded at the APB Setup edge (early launch), the TL-UL FSM
//           (IDLE, REQ, WAIT) tracking the single outstanding request,
//           reg_d_ready, and the D-channel response check (d_error, d_opcode,
//           d_source) with read-data forming. Constant fields are tie-offs.
// Spec    : m_apb_tlul_bridge_Design_Specification.md sections 5.1, 5.3, 5.4,
//           6.2, 6.3, 7.3, 8, 9, 10.1, 10.2, 12, 14.1, 14.2, 20 (DEC-004,
//           DEC-005, DEC-008, DEC-010, DEC-013)
// ============================================================================
`default_nettype none

// REQ: BR-3-23, BR-14.2-03, BR-14.2-04
module m_tlul_if #(
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
  parameter logic [31:0] PARA_A_USER_W = 32'd1
) (
  // Clock and reset
  input  wire                      i_clk_core,
  input  wire                      i_rst_n_core,
  // Internal request bundle from m_apb_if (section 5.1)
  input  wire                      i_req_launch,
  input  wire                      i_req_wr,
  input  wire [PARA_ADDR_W-3:0]    i_req_addr,
  input  wire [31:0]               i_req_wdata,
  // Internal response bundle to m_apb_if (section 5.1)
  output logic                     o_resp_valid,
  output logic                     o_resp_err,
  output logic [31:0]              o_resp_rdata,
  // TL-UL channel A (host to device)
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
  // TL-UL channel D (device to host), used fields only
  input  wire                      i_tlul_d_valid,
  output logic                     o_tlul_d_ready,
  input  wire [2:0]                i_tlul_d_opcode,
  input  wire [PARA_SRC_W-1:0]     i_tlul_d_source,
  input  wire [31:0]               i_tlul_d_data,
  input  wire                      i_tlul_d_error
);

  // --------------------------------------------------------------------------
  // Fixed constants (section 8): not parameters, cannot be overridden.
  // --------------------------------------------------------------------------
  // REQ: BR-8-08, BR-8-04, BR-8-02
  localparam logic [1:0]            LPARA_A_SIZE     = 2'd2;
  localparam logic [3:0]            LPARA_A_MASK     = 4'b1111;
  localparam logic [2:0]            LPARA_D_ACK_DATA = 3'd1;
  localparam logic [2:0]            LPARA_D_ACK      = 3'd0;
  localparam logic [PARA_SRC_W-1:0] LPARA_SRC_ID     = PARA_SRC_ID[PARA_SRC_W-1:0];

  // --------------------------------------------------------------------------
  // TL-UL FSM encoding (section 10.1)
  // --------------------------------------------------------------------------
  // REQ: BR-14.1-04
  typedef enum logic [1:0] {
    ENUM_ST_IDLE = 2'b00,
    ENUM_ST_REQ  = 2'b01,
    ENUM_ST_WAIT = 2'b10
  } e_fsm_tlul_state;

  e_fsm_tlul_state reg_fsm_tlul_current_state;
  e_fsm_tlul_state w_fsm_tlul_nxt_state;

  logic                   reg_a_valid;
  logic                   reg_a_rd;
  logic [PARA_ADDR_W-3:0] reg_a_addr;
  logic [31:0]            reg_a_data;
  logic                   reg_d_ready;

  logic                   w_a_load;
  logic                   w_a_accept;
  logic                   w_resp_hit;
  logic                   w_resp_err;
  logic [2:0]             w_exp_d_opcode;
  logic [31:0]            w_resp_rdata;

  // --------------------------------------------------------------------------
  // Channel A load and acceptance
  // --------------------------------------------------------------------------
  // Load only while no request is outstanding (one request at a time).
  // REQ: BR-3-06, BR-5.4-01, BR-6.3-06, BR-5.4-06, BR-1.1-04, BR-1.1-01
  assign w_a_load   = i_req_launch && (reg_fsm_tlul_current_state == ENUM_ST_IDLE);
  // REQ: BR-10.1-04
  assign w_a_accept = (reg_fsm_tlul_current_state == ENUM_ST_REQ) && i_tlul_a_ready;

  // --------------------------------------------------------------------------
  // D-channel checker (section 10.2)
  // A response counts only in WAIT, or in REQ together with a_ready; any other
  // d_valid is an orphan and is discarded.
  // --------------------------------------------------------------------------
  // REQ: BR-10.1-05, BR-10.1-06, BR-3-11, BR-6.3-08, BR-6.3-09, TL-T4.1.3.5-08
  assign w_resp_hit = i_tlul_d_valid && reg_d_ready
                    && (w_a_accept || (reg_fsm_tlul_current_state == ENUM_ST_WAIT));

  // Expected opcode: AccessAckData for a Get, AccessAck for a PutFullData.
  // REQ: BR-9-09, BR-3-27
  assign w_exp_d_opcode = reg_a_rd ? LPARA_D_ACK_DATA : LPARA_D_ACK;

  // REQ: BR-1.3-04, BR-3-26, BR-3-27, BR-3-28, BR-20-10, BR-6.3-14, BR-6.3-15
  // REQ: TL-T4.1.3.2.3-01, BR-12-05, BR-12-07
  assign w_resp_err = i_tlul_d_error
                    || (i_tlul_d_opcode != w_exp_d_opcode)
                    || (i_tlul_d_source != LPARA_SRC_ID);

  // Read data forced to 0 for writes and for every error.
  // REQ: BR-5.1-03, BR-3-09, BR-3-10, BR-9-10
  assign w_resp_rdata = (reg_a_rd && !w_resp_err) ? i_tlul_d_data : 32'h0000_0000;

  assign o_resp_valid = w_resp_hit;
  assign o_resp_err   = w_resp_err;
  assign o_resp_rdata = w_resp_rdata;

  // --------------------------------------------------------------------------
  // TL-UL FSM next-state logic (section 10.1)
  // --------------------------------------------------------------------------
  // REQ: BR-10.1-04, BR-10.1-05, BR-3-06, BR-3-07, BR-6.3-09, BR-10.3-03
  always_comb begin : p_com_tlul_fsm
    w_fsm_tlul_nxt_state = ENUM_ST_IDLE;
    case (reg_fsm_tlul_current_state)
      ENUM_ST_IDLE: begin
        if (i_req_launch) begin
          w_fsm_tlul_nxt_state = ENUM_ST_REQ;
        end else begin
          w_fsm_tlul_nxt_state = ENUM_ST_IDLE;
        end
      end
      ENUM_ST_REQ: begin
        if (i_tlul_a_ready) begin
          if (w_resp_hit) begin
            w_fsm_tlul_nxt_state = ENUM_ST_IDLE;
          end else begin
            w_fsm_tlul_nxt_state = ENUM_ST_WAIT;
          end
        end else begin
          w_fsm_tlul_nxt_state = ENUM_ST_REQ;
        end
      end
      ENUM_ST_WAIT: begin
        if (w_resp_hit) begin
          w_fsm_tlul_nxt_state = ENUM_ST_IDLE;
        end else begin
          w_fsm_tlul_nxt_state = ENUM_ST_WAIT;
        end
      end
      default: begin
        w_fsm_tlul_nxt_state = ENUM_ST_IDLE;
      end
    endcase
  end

  // REQ: BR-3-30, BR-7.3-01, BR-7.3-02, BR-14.1-03, BR-3-32, BR-7.3-05, BR-3-29
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_tlul_fsm
    if (!i_rst_n_core) begin
      reg_fsm_tlul_current_state <= ENUM_ST_IDLE;
    end else begin
      reg_fsm_tlul_current_state <= w_fsm_tlul_nxt_state;
    end
  end

  // --------------------------------------------------------------------------
  // Channel A valid flop: set at the Setup edge, held until a_ready is sampled
  // high; high only in ENUM_ST_REQ.
  // --------------------------------------------------------------------------
  // REQ: BR-5.3-02, BR-3-02, BR-3-08, BR-5.4-02, BR-6.2-06, BR-5.3-04, BR-1.1-02
  // REQ: BR-10.1-04, BR-10.3-02, BR-6.3-07, BR-3-31, BR-7.3-03
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_a_valid
    if (!i_rst_n_core) begin
      reg_a_valid <= 1'b0;
    end else if (w_a_load) begin
      reg_a_valid <= 1'b1;
    end else if (w_a_accept) begin
      reg_a_valid <= 1'b0;
    end
  end

  // --------------------------------------------------------------------------
  // Channel A payload flops: loaded at the Setup edge, stable otherwise.
  // All reset to 0 (DEC-013).
  // --------------------------------------------------------------------------
  // REQ: BR-5.3-01, BR-5.3-02, BR-3-03, BR-3-04, BR-1.3-01, BR-1.3-02, BR-5.4-03
  // REQ: BR-6.2-13, BR-9-03, BR-9-05, BR-7.3-02, BR-7.3-03, BR-14.1-03, BR-3-31
  // REQ: BR-6.3-10, BR-6.3-12
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_a_payload
    if (!i_rst_n_core) begin
      reg_a_rd   <= 1'b0;
      reg_a_addr <= '0;
      reg_a_data <= 32'h0000_0000;
    end else if (w_a_load) begin
      reg_a_rd   <= !i_req_wr;
      reg_a_addr <= i_req_addr;
      reg_a_data <= i_req_wdata;
    end
  end

  // --------------------------------------------------------------------------
  // d_ready: flop reset to 0 with D = 1 (DEC-010).
  // --------------------------------------------------------------------------
  // REQ: BR-3-21, BR-3-22, BR-6.2-15, BR-20-11, BR-5.3-04, BR-3-31
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_d_ready
    if (!i_rst_n_core) begin
      reg_d_ready <= 1'b0;
    end else begin
      reg_d_ready <= 1'b1;
    end
  end

  // --------------------------------------------------------------------------
  // Outputs. Changing outputs come directly from flop Q pins; constant fields
  // are tie-offs (DEC-005).
  // --------------------------------------------------------------------------
  // REQ: BR-3-17, BR-20-08, BR-17.1.2-01, BR-6.2-06
  assign o_tlul_a_valid   = reg_a_valid;
  // Opcode bit 2 from flop (1 = Get), bits [1:0] constant 0.
  // REQ: BR-6.2-07, BR-9-05, BR-3-03, BR-3-04, BR-20-06, BR-20-09
  assign o_tlul_a_opcode  = {reg_a_rd, 2'b00};
  // Address bits [PARA_ADDR_W-1:2] from flops, bits [1:0] constant 0.
  // REQ: BR-6.2-11, BR-9-03, BR-8-01, BR-20-09
  assign o_tlul_a_address = {reg_a_addr, 2'b00};
  // REQ: BR-6.2-13
  assign o_tlul_a_data    = reg_a_data;
  // REQ: BR-3-20, BR-6.2-08, BR-20-09
  assign o_tlul_a_param   = 3'b000;
  // REQ: BR-3-20, BR-6.2-09, BR-9-07, BR-2.3-04, BR-20-09, TL-T4.1.3.4-04, TL-T3.1-01
  assign o_tlul_a_size    = LPARA_A_SIZE;
  // REQ: BR-3-20, BR-6.2-10, BR-5.4-01, BR-8-04, BR-20-09
  assign o_tlul_a_source  = LPARA_SRC_ID;
  // REQ: BR-3-20, BR-6.2-12, BR-9-08, BR-20-09, TL-T4.1.3.4-02
  assign o_tlul_a_mask    = LPARA_A_MASK;
  // REQ: BR-3-20, BR-6.2-14, BR-2.3-05, BR-8-05, BR-20-09, TL-T3.3-03, TL-T4.1.3.3-02
  assign o_tlul_a_user    = '0;
  // REQ: BR-3-21, BR-3-22, BR-6.2-15
  assign o_tlul_d_ready   = reg_d_ready;

endmodule : m_tlul_if

`default_nettype wire
