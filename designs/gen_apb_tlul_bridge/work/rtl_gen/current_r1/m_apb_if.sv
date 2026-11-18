// ============================================================================
// Module  : m_apb_if
// Purpose : APB4 Completer side of the APB4 to TL-UL bridge. Detects the Setup
//           phase by level, checks PSTRB and PADDR[1:0], launches a legal
//           request towards m_tlul_if, sequences the APB FSM
//           (IDLE, BUSY, DONE) and drives PREADY, PRDATA and PSLVERR from flops.
// Spec    : m_apb_tlul_bridge_Design_Specification.md sections 5.1, 5.3, 5.4,
//           6.2, 6.3, 7.3, 10.1, 10.2, 10.3, 10.4, 12, 13, 14.1, 14.2
// ============================================================================
`default_nettype none

// REQ: BR-3-23, BR-14.2-02, BR-14.2-04
module m_apb_if #(
  // Parameter Description: Width of the byte address on both buses.
  // Parameter values: 16 to 32, default 32.
  // Parameter unit: bits
  parameter logic [31:0] PARA_ADDR_W = 32'd32
) (
  // Clock and reset
  input  wire                     i_clk_core,
  input  wire                     i_rst_n_core,
  // APB4 Completer request
  input  wire                     i_apb_psel,
  input  wire                     i_apb_penable,
  input  wire                     i_apb_pwrite,
  input  wire [PARA_ADDR_W-1:0]   i_apb_paddr,
  input  wire [3:0]               i_apb_pstrb,
  input  wire [31:0]              i_apb_pwdata,
  // APB4 Completer completion (all from flops)
  output logic                    o_apb_pready,
  output logic [31:0]             o_apb_prdata,
  output logic                    o_apb_pslverr,
  // Internal request bundle to m_tlul_if (section 5.1)
  output logic                    o_req_launch,
  output logic                    o_req_wr,
  output logic [PARA_ADDR_W-3:0]  o_req_addr,
  output logic [31:0]             o_req_wdata,
  // Internal response bundle from m_tlul_if (section 5.1)
  input  wire                     i_resp_valid,
  input  wire                     i_resp_err,
  input  wire [31:0]              i_resp_rdata
);

  // --------------------------------------------------------------------------
  // APB FSM encoding (section 10.1)
  // --------------------------------------------------------------------------
  // REQ: BR-14.1-04
  typedef enum logic [1:0] {
    ENUM_ST_IDLE = 2'b00,
    ENUM_ST_BUSY = 2'b01,
    ENUM_ST_DONE = 2'b10
  } e_fsm_apb_state;

  e_fsm_apb_state reg_fsm_apb_current_state;
  e_fsm_apb_state w_fsm_apb_nxt_state;

  logic        w_setup;
  logic        w_legal;
  logic        w_req_launch;
  logic        w_local_err;
  logic        w_resp_done;

  logic        reg_pready;
  logic        reg_pslverr;
  logic [31:0] reg_prdata;

  // --------------------------------------------------------------------------
  // Setup detect and legality check (section 10.2)
  // --------------------------------------------------------------------------
  // Setup phase recognised by the levels PSEL = 1 and PENABLE = 0 while the
  // APB FSM is idle, never by an edge of PSEL.
  // REQ: BR-3-01, BR-3-12, BR-5.3-10, BR-20-12, BR-6.3-01, BR-1.3-05, BR-20-02
  assign w_setup = (reg_fsm_apb_current_state == ENUM_ST_IDLE)
                 && i_apb_psel && !i_apb_penable;

  // Legal: word-aligned address, and full strobe for a write. PSTRB is
  // ignored on reads.
  // REQ: BR-6.2-01, BR-6.2-02, BR-9-02, BR-3-05, BR-6.3-04, BR-20-04, BR-9-01
  assign w_legal = (i_apb_paddr[1:0] == 2'b00)
                 && (!i_apb_pwrite || (i_apb_pstrb == 4'b1111));

  // REQ: BR-5.1-02, BR-10.1-01, BR-1.1-01
  assign w_req_launch = w_setup && w_legal;

  // Illegal request: local error, no TL-UL request is launched.
  // REQ: BR-T1-03, BR-T1-04, BR-T1-05, BR-1.3-03, BR-2.3-01, BR-2.3-02, BR-5.4-05
  // REQ: BR-1.1-04, BR-20-05, BR-20-06, BR-9-04, BR-12-02
  assign w_local_err = w_setup && !w_legal;

  // Response for the outstanding request accepted while BUSY.
  // REQ: BR-10.1-03
  assign w_resp_done = (reg_fsm_apb_current_state == ENUM_ST_BUSY) && i_resp_valid;

  // --------------------------------------------------------------------------
  // Request bundle towards m_tlul_if (section 5.1): captured there at the
  // edge that ends the Setup cycle (early launch).
  // --------------------------------------------------------------------------
  // REQ: BR-5.3-01, BR-6.3-02, BR-9-03
  assign o_req_launch = w_req_launch;
  assign o_req_wr     = i_apb_pwrite;
  assign o_req_addr   = i_apb_paddr[PARA_ADDR_W-1:2];
  assign o_req_wdata  = i_apb_pwdata;

  // --------------------------------------------------------------------------
  // APB FSM next-state logic (section 10.1)
  // --------------------------------------------------------------------------
  // REQ: BR-10.1-01, BR-10.1-02, BR-10.1-03, BR-5.3-11, BR-3-06, BR-3-07, BR-12-09
  // REQ: BR-20-07
  always_comb begin : p_com_apb_fsm
    w_fsm_apb_nxt_state = ENUM_ST_IDLE;
    case (reg_fsm_apb_current_state)
      ENUM_ST_IDLE: begin
        if (w_req_launch) begin
          w_fsm_apb_nxt_state = ENUM_ST_BUSY;
        end else if (w_local_err) begin
          w_fsm_apb_nxt_state = ENUM_ST_DONE;
        end else begin
          w_fsm_apb_nxt_state = ENUM_ST_IDLE;
        end
      end
      ENUM_ST_BUSY: begin
        // No timeout: waits for the response indefinitely (DEC-003).
        if (i_resp_valid) begin
          w_fsm_apb_nxt_state = ENUM_ST_DONE;
        end else begin
          w_fsm_apb_nxt_state = ENUM_ST_BUSY;
        end
      end
      ENUM_ST_DONE: begin
        // PREADY cycle; idle again in the next cycle (next Setup accepted).
        // REQ: BR-3-37, BR-3-38, BR-13-04, BR-5.3-12, BR-6.3-05, BR-3-14
        w_fsm_apb_nxt_state = ENUM_ST_IDLE;
      end
      default: begin
        w_fsm_apb_nxt_state = ENUM_ST_IDLE;
      end
    endcase
  end

  // REQ: BR-3-30, BR-7.3-01, BR-7.3-02, BR-14.1-03, BR-3-32, BR-7.3-05, BR-3-29
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_apb_fsm
    if (!i_rst_n_core) begin
      reg_fsm_apb_current_state <= ENUM_ST_IDLE;
    end else begin
      reg_fsm_apb_current_state <= w_fsm_apb_nxt_state;
    end
  end

  // --------------------------------------------------------------------------
  // Response flops (sections 5.3, 10.1, 12)
  // Local error: loaded at the Setup edge, PREADY and PSLVERR in the first
  // Access cycle, PRDATA = 0.
  // TL-UL response: loaded at the edge of the response cycle, PREADY in the
  // next cycle. PREADY and PSLVERR are cleared at the edge leaving DONE.
  // PRDATA holds its last value outside a completion (DEC-009).
  // --------------------------------------------------------------------------
  // REQ: BR-10.1-02, BR-10.3-01, BR-3-24, BR-3-25, BR-6.3-11, BR-6.3-13, BR-12-01
  // REQ: BR-12-04, BR-3-36, BR-13-03, BR-10.1-03, BR-5.3-06, BR-5.3-08, BR-3-34
  // REQ: BR-3-35, BR-13-01, BR-13-02, BR-3-26, BR-3-27, BR-3-28, BR-1.3-04
  // REQ: BR-6.3-14, BR-6.3-15, BR-12-05, BR-12-07, BR-20-10, BR-3-09, BR-3-10
  // REQ: BR-6.2-04, BR-11-02, BR-3-30, BR-3-31, BR-7.3-02, BR-14.1-03
  always_ff @(posedge i_clk_core or negedge i_rst_n_core) begin : p_ff_apb_resp
    if (!i_rst_n_core) begin
      reg_pready  <= 1'b0;
      reg_pslverr <= 1'b0;
      reg_prdata  <= 32'h0000_0000;
    end else if (w_local_err) begin
      reg_pready  <= 1'b1;
      reg_pslverr <= 1'b1;
      reg_prdata  <= 32'h0000_0000;
    end else if (w_resp_done) begin
      reg_pready  <= 1'b1;
      reg_pslverr <= i_resp_err;
      reg_prdata  <= i_resp_rdata;
    end else begin
      reg_pready  <= 1'b0;
      reg_pslverr <= 1'b0;
    end
  end

  // --------------------------------------------------------------------------
  // Outputs: directly from flop Q pins.
  // PREADY is high only in DONE, for one cycle; PSLVERR only with PREADY.
  // --------------------------------------------------------------------------
  // REQ: BR-3-17, BR-3-18, BR-3-19, BR-5.4-04, BR-6.2-03, BR-6.2-05, BR-5.3-07
  // REQ: BR-20-08, BR-17.1.2-01
  assign o_apb_pready  = reg_pready;
  assign o_apb_pslverr = reg_pslverr;
  assign o_apb_prdata  = reg_prdata;

endmodule : m_apb_if

`default_nettype wire
