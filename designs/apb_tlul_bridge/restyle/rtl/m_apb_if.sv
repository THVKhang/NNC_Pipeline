/*
 * Project      : VLSI Technology - AI RTL generator
 * Author       : Nguyen Quan and Claude (user)
 * AI Flow      : VLSIT RTL Generator AI Automation Flow
 * AI Flow Page : https://github.com/nguyenquanicd/VLSIT_RTL_Generator_AI_Model
 * Date         : 2026-10-18
 * Module       : m_apb_if
 * Purpose      : APB4 completer side of the APB to TL-UL bridge. It detects the Setup phase,
 *                checks the request, launches it to the TL-UL side and returns the completion.
 * Spec sections: 5.1 (internal interface), 5.3 (early launch and back-to-back transfers),
 *                5.4 (invariants), 6.3 (APB transfer cases), 7.3 (reset), 10.1 (APB FSM),
 *                12 (local errors), 14.2 (hierarchy: APB-facing logic).
 */
`timescale 1ns/1ps

module m_apb_if #(
  // Parameter Description: width of the APB byte address; bits [1:0] are checked for alignment.
  // Parameter values: legal range is 16 to 32; default is 32.
  // Parameter unit: bit
  parameter logic [31:0] PARA_ADDR_W = 32
) (
  input wire i_clk_core,
  input wire i_rst_n_core,
  input wire i_apb_psel,
  input wire i_apb_penable,
  input wire i_apb_pwrite,
  input wire i_resp_valid,
  input wire i_resp_err,
  input wire [PARA_ADDR_W-1:0] i_apb_paddr,
  input wire [3:0] i_apb_pstrb,
  input wire [31:0] i_apb_pwdata,
  input wire [31:0] i_resp_rdata,
  output logic o_req_launch,
  output logic o_req_wr,
  output logic o_apb_pready,
  output logic o_apb_pslverr,
  output logic [PARA_ADDR_W-3:0] o_req_addr,
  output logic [31:0] o_req_wdata,
  output logic [31:0] o_apb_prdata
);

  // APB FSM states: IDLE waits for a Setup phase, BUSY waits for the TL-UL response, and DONE
  // holds PREADY for one cycle. Unused encoding 2'b11 recovers to ENUM_ST_IDLE.
  typedef enum logic [1:0] {
    ENUM_ST_IDLE = 2'b00,
    ENUM_ST_BUSY = 2'b01,
    ENUM_ST_DONE = 2'b10
  } apb_state_type_def;

  // Internal signal declarations
  apb_state_type_def reg_fsm_apb_current_state;
  apb_state_type_def w_fsm_apb_nxt_state;
  logic w_setup;
  logic w_legal;
  logic w_req_launch;
  logic w_local_err;
  logic w_pready_nxt;
  logic w_pslverr_nxt;
  logic [31:0] w_prdata_nxt;
  logic reg_pready;
  logic reg_pslverr;
  logic [31:0] reg_prdata;

  // Setup phase: the level PSEL = 1 with PENABLE = 0 while the FSM is idle, not an edge of PSEL, so
  // back-to-back transfers with PSEL held high start exactly like the first transfer.
  // REQ: BR-3-01, BR-3-12, BR-5.3-10, BR-1.3-05, BR-20-12
  assign w_setup = (reg_fsm_apb_current_state == ENUM_ST_IDLE) & i_apb_psel & ~i_apb_penable;

  // Legal request: word-aligned address, and a full strobe when the access is a write.
  // PSTRB is ignored on reads, where the APB requester drives it LOW.
  // REQ: BR-T1-03, BR-T1-04, BR-2.3-01, BR-2.3-02, BR-3-05, BR-6.3-04, BR-9-04
  assign w_legal = (i_apb_paddr[1:0] == 2'b00) & (~i_apb_pwrite | (i_apb_pstrb == 4'b1111));

  // A legal Setup phase launches the TL-UL request; an illegal one gets a local error answer.
  // REQ: BR-5.1-02, BR-T1-05, BR-5.4-05, BR-1.3-03
  assign w_req_launch = w_setup & w_legal;
  assign w_local_err  = w_setup & ~w_legal;

  // Request bundle for the TL-UL side: forwarded straight from the APB inputs of the Setup cycle.
  // REQ: BR-5.1-02, BR-5.3-01
  assign o_req_launch = w_req_launch;
  assign o_req_wr     = i_apb_pwrite;
  assign o_req_addr   = i_apb_paddr[PARA_ADDR_W-1:2];
  assign o_req_wdata  = i_apb_pwdata;

  // Completion outputs come straight from flip-flops.
  // REQ: BR-3-17, BR-5.3-07, BR-20-08
  assign o_apb_pready  = reg_pready;
  assign o_apb_pslverr = reg_pslverr;
  assign o_apb_prdata  = reg_prdata;

  // Next-state logic: IDLE moves to BUSY on a launch or to DONE on a local error, BUSY moves to
  // DONE when the response arrives, and DONE always returns to IDLE. The next state gets its
  // default first and the case has a default branch, so no latch is inferred.
  // REQ: BR-10.1-01, BR-10.1-02, BR-10.1-03, BR-5.3-11, BR-5.4-04
  always_comb begin : p_com_fsm_nxt
    w_fsm_apb_nxt_state = reg_fsm_apb_current_state;
    case (reg_fsm_apb_current_state)
      ENUM_ST_IDLE: begin
        if (w_req_launch) begin
          w_fsm_apb_nxt_state = ENUM_ST_BUSY;
        end else if (w_local_err) begin
          w_fsm_apb_nxt_state = ENUM_ST_DONE;
        end
      end
      ENUM_ST_BUSY: begin
        if (i_resp_valid) begin
          w_fsm_apb_nxt_state = ENUM_ST_DONE;
        end
      end
      ENUM_ST_DONE: w_fsm_apb_nxt_state = ENUM_ST_IDLE;
      default:      w_fsm_apb_nxt_state = ENUM_ST_IDLE;
    endcase
  end

  // Completion values: PREADY and PSLVERR last one cycle. A local error clears PRDATA, a response
  // loads PRDATA (already zero for writes and errors), otherwise PRDATA holds its last value.
  // Every next value gets its default first, so no latch is inferred.
  // REQ: BR-3-24, BR-3-25, BR-12-01, BR-12-04, BR-3-09, BR-3-10, BR-3-18, BR-3-19, BR-6.2-04
  always_comb begin : p_com_resp
    w_pready_nxt  = 1'b0;
    w_pslverr_nxt = 1'b0;
    w_prdata_nxt  = reg_prdata;
    if (w_local_err) begin
      w_pready_nxt  = 1'b1;
      w_pslverr_nxt = 1'b1;
      w_prdata_nxt  = '0;
    end else if ((reg_fsm_apb_current_state == ENUM_ST_BUSY) & i_resp_valid) begin
      w_pready_nxt  = 1'b1;
      w_pslverr_nxt = i_resp_err;
      w_prdata_nxt  = i_resp_rdata;
    end
  end

  // Current-state register: the control state is reset asynchronously to IDLE and otherwise takes
  // the next state every clock cycle.
  // REQ: BR-3-30, BR-7.3-02, BR-3-32
  always_ff @(posedge i_clk_core, negedge i_rst_n_core) begin : p_ff_fsm_apb
    if (!i_rst_n_core) begin
      reg_fsm_apb_current_state <= ENUM_ST_IDLE;
    end else begin
      reg_fsm_apb_current_state <= w_fsm_apb_nxt_state;
    end
  end

  // Completion flip-flops: all are reset asynchronously to zero, so every output is defined
  // after reset.
  // REQ: BR-3-31, BR-7.3-02, BR-6.2-03, BR-5.3-06
  always_ff @(posedge i_clk_core, negedge i_rst_n_core) begin : p_ff_resp
    if (!i_rst_n_core) begin
      reg_pready  <= 1'b0;
      reg_pslverr <= 1'b0;
      reg_prdata  <= '0;
    end else begin
      reg_pready  <= w_pready_nxt;
      reg_pslverr <= w_pslverr_nxt;
      reg_prdata  <= w_prdata_nxt;
    end
  end

endmodule
