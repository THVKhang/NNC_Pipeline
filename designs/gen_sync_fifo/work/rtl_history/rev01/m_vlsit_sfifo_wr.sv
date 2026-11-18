// ============================================================================
// Module  : m_vlsit_sfifo_wr
// Purpose : Write side of the synchronous-clock FIFO (CLK-WR / RST-WR): write
//           pointer (modulo 2 x DEPTH), write acceptance, look-ahead full and
//           full-threshold flags, overflow pulse, memory write port, optional
//           retiming flops of the read pointer and the acknowledge, and the
//           write-side software reset FSM with its request and busy flops.
// Spec    : SyncFIFO_Design_Specification.md sections 5.1, 5.3, 5.4, 6.2,
//           6.3, 7.3, 9, 10.1, 10.2, 10.6, 10.7, 12, 14.2, 14.2.1
// ============================================================================
`default_nettype none

module m_vlsit_sfifo_wr #(
    // PARA_SFIFO_DEPTH: number of FIFO entries
    // Legal values: any integer of 2 or more, no upper limit
    // Default: 8
    parameter logic [31:0] PARA_SFIFO_DEPTH      = 8,
    // PARA_SFIFO_DATA_W: data word width in bits
    // Legal values: 1 or more, no upper limit
    // Default: 32
    parameter logic [31:0] PARA_SFIFO_DATA_W     = 32,
    // PARA_SFIFO_PTR_RETIME: 0 = direct read pointer, 1 = one retiming flop
    // Legal values: 0 or 1
    // Default: 0
    parameter logic [31:0] PARA_SFIFO_PTR_RETIME = 0,
    // Derived: memory address width, pointer width, occupancy width
    localparam logic [31:0] LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_PTR_W  = $clog2(2 * PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_OCC_W  = $clog2(PARA_SFIFO_DEPTH + 1)
) (
    // Clock and reset (CLK-WR)
    input  wire                          i_clk_wr,
    input  wire                          i_rst_n_wr,
    // Write interface
    input  wire                          i_wr_en,
    input  wire  [PARA_SFIFO_DATA_W-1:0] i_wr_data,
    input  wire  [LPARA_OCC_W-1:0]       i_full_thr,
    output logic                         o_full,
    output logic                         o_full_thr,
    output logic                         o_overflow,
    // Software reset interface
    input  wire                          i_rst_n_sw,
    output logic                         o_sw_rst_busy,
    // Pointers and handshake with the read side
    input  wire  [LPARA_PTR_W-1:0]       i_rd_ptr,
    output logic [LPARA_PTR_W-1:0]       o_wr_ptr,
    output logic                         o_req_wr,
    input  wire                          i_ack_rd,
    // Memory write port
    output logic                         o_mem_wr_en,
    output logic [LPARA_ADDR_W-1:0]      o_mem_wr_addr,
    output logic [PARA_SFIFO_DATA_W-1:0] o_mem_wr_data
);

  // --------------------------------------------------------------------------
  // Constants
  // --------------------------------------------------------------------------
  localparam logic [31:0] LPARA_TWO_DEPTH = 2 * PARA_SFIFO_DEPTH;
  localparam logic [31:0] LPARA_PTR_LAST  = (2 * PARA_SFIFO_DEPTH) - 1;
  localparam logic [31:0] LPARA_PTR_ONE   = 1;

  // --------------------------------------------------------------------------
  // Write reset FSM states (3 bits, encodings 5 to 7 recover to RUN)
  // --------------------------------------------------------------------------
  typedef enum logic [2:0] {
    ENUM_ST_RUN  = 3'd0,
    ENUM_ST_REQ  = 3'd1,
    ENUM_ST_PTR  = 3'd2,
    ENUM_ST_HOLD = 3'd3,
    ENUM_ST_REL  = 3'd4
  } t_fsm_srst_wr_e;

  t_fsm_srst_wr_e reg_fsm_srst_current_state;
  t_fsm_srst_wr_e w_fsm_srst_nxt_state;

  // --------------------------------------------------------------------------
  // Signals
  // --------------------------------------------------------------------------
  logic [LPARA_PTR_W-1:0] reg_wr_ptr;
  logic [LPARA_PTR_W-1:0] w_wr_ptr_inc;
  logic [LPARA_PTR_W-1:0] w_wr_ptr_nxt;
  logic [LPARA_PTR_W-1:0] w_rd_ptr_view;
  logic                   w_ack_view;
  logic [LPARA_PTR_W:0]   w_occ_nxt;
  logic [LPARA_PTR_W:0]   w_full_thr_ext;
  logic                   reg_full;
  logic                   reg_full_thr;
  logic                   reg_overflow;
  logic                   reg_sw_rst_busy;
  logic                   reg_req;
  logic                   reg_sw_rst_pend;
  logic                   reg_sw_rst_req_d;
  logic                   w_sw_rst_pend_nxt;
  logic                   w_sw_rst_fall;
  logic                   w_block;
  logic                   w_wr_accept;
  logic                   w_full_thr_blk;

  // --------------------------------------------------------------------------
  // View of the read pointer and the acknowledge (timed paths, no synchronizer)
  // --------------------------------------------------------------------------
  // REQ: SF-1.1-04, SF-1.1-12, SF-3-24, SF-3-25, SF-3-26, SF-3-27, SF-3-28
  // REQ: SF-3-57, SF-14.2.1-01, SF-4-06
  generate
    if (PARA_SFIFO_PTR_RETIME != 32'd0) begin : g_rd_ptr_retime
      // One plain retiming flop per crossing signal in the destination domain
      logic [LPARA_PTR_W-1:0] reg_rd_ptr_rt;
      logic                   reg_ack_rt;

      always_ff @(posedge i_clk_wr or negedge i_rst_n_wr) begin
        if (!i_rst_n_wr) begin
          reg_rd_ptr_rt <= '0;
          reg_ack_rt    <= 1'b0;
        end else begin
          reg_rd_ptr_rt <= i_rd_ptr;
          reg_ack_rt    <= i_ack_rd;
        end
      end

      assign w_rd_ptr_view = reg_rd_ptr_rt;
      assign w_ack_view    = reg_ack_rt;
    end else begin : g_rd_ptr_direct
      // Direct path into the flag logic
      assign w_rd_ptr_view = i_rd_ptr;
      assign w_ack_view    = i_ack_rd;
    end
  endgenerate

  // --------------------------------------------------------------------------
  // Software reset block term and write acceptance
  // --------------------------------------------------------------------------
  // REQ: SF-3-35, SF-3-36, SF-10.7-01, SF-6.3-11, SF-12-07
  // Block with no clock delay from i_rst_n_sw = 0; held by the busy flop.
  // A pending new request (REQ-SRST-008) also blocks in its RUN cycle.
  assign w_block = reg_sw_rst_busy | ~i_rst_n_sw | reg_sw_rst_pend;

  // REQ: SF-3-01, SF-6.3-01, SF-3-07, SF-5.4-02, SF-20.2-05, SF-10.1-01
  // Accepted only if the own full flag allows it (no bypass)
  assign w_wr_accept = i_wr_en & ~w_block & ~reg_full;

  // --------------------------------------------------------------------------
  // Write pointer (modulo 2 x DEPTH)
  // --------------------------------------------------------------------------
  // REQ: SF-3-13, SF-9-01, SF-8-10
  assign w_wr_ptr_inc = (reg_wr_ptr == LPARA_PTR_LAST[LPARA_PTR_W-1:0])
                      ? '0
                      : (reg_wr_ptr + LPARA_PTR_ONE[LPARA_PTR_W-1:0]);

  // REQ: SF-5.3-01, SF-3-19, SF-10.1-04, SF-10.7-04
  always_comb begin
    w_wr_ptr_nxt = reg_wr_ptr;
    if (reg_fsm_srst_current_state == ENUM_ST_PTR) begin
      w_wr_ptr_nxt = '0;
    end else if (w_wr_accept) begin
      w_wr_ptr_nxt = w_wr_ptr_inc;
    end
  end

  // --------------------------------------------------------------------------
  // Look-ahead occupancy of the write view: occ(next write ptr, rd_ptr_view)
  // --------------------------------------------------------------------------
  // REQ: SF-9-03, SF-5.4-01, SF-5.1-01, SF-5.4-04, SF-6.3-05
  assign w_occ_nxt = (w_wr_ptr_nxt >= w_rd_ptr_view)
                   ? ({1'b0, w_wr_ptr_nxt} - {1'b0, w_rd_ptr_view})
                   : ({1'b0, w_wr_ptr_nxt} + LPARA_TWO_DEPTH[LPARA_PTR_W:0]
                      - {1'b0, w_rd_ptr_view});

  // REQ: SF-9-06, SF-9-05
  // Threshold zero-extended for the comparison
  assign w_full_thr_ext = {{(LPARA_PTR_W + 1 - LPARA_OCC_W){1'b0}}, i_full_thr};

  // --------------------------------------------------------------------------
  // Pointer, flag and pulse flops
  // --------------------------------------------------------------------------
  // REQ: SF-3-05, SF-3-14, SF-3-17, SF-3-54, SF-10.6-02, SF-10.6-04, SF-3-29
  // REQ: SF-3-30, SF-7.3-01, SF-7.3-05, SF-10.6-10, SF-6.2-06, SF-12-11
  // REQ: SF-14.2.1-02, SF-10.2-01, SF-10.2-05, SF-6.3-08, SF-12-01, SF-3-37
  always_ff @(posedge i_clk_wr or negedge i_rst_n_wr) begin
    if (!i_rst_n_wr) begin
      reg_wr_ptr   <= '0;
      reg_full     <= 1'b0;
      reg_full_thr <= 1'b0;
      reg_overflow <= 1'b0;
    end else begin
      reg_wr_ptr   <= w_wr_ptr_nxt;
      reg_full     <= (w_occ_nxt == PARA_SFIFO_DEPTH[LPARA_PTR_W:0]);
      reg_full_thr <= (w_occ_nxt >= w_full_thr_ext);
      reg_overflow <= i_wr_en & ~w_block & reg_full;
    end
  end

  // --------------------------------------------------------------------------
  // Write reset FSM (four-phase handshake, write side)
  // --------------------------------------------------------------------------
  // REQ: SF-10.1-02, SF-10.1-03, SF-10.1-04, SF-10.1-05, SF-3-33, SF-3-34
  // REQ: SF-3-40, SF-3-41, SF-1.1-14, SF-10.7-02, SF-10.7-04, SF-10.7-06
  // REQ: SF-10.7-08, SF-3-47, SF-3-48, SF-10.7-10
  always_comb begin
    w_fsm_srst_nxt_state = reg_fsm_srst_current_state;
    case (reg_fsm_srst_current_state)
      ENUM_ST_RUN: begin
        if (!i_rst_n_sw || reg_sw_rst_pend) begin
          w_fsm_srst_nxt_state = ENUM_ST_REQ;
        end
      end
      ENUM_ST_REQ: begin
        if (w_ack_view) begin
          w_fsm_srst_nxt_state = ENUM_ST_PTR;
        end
      end
      ENUM_ST_PTR: begin
        w_fsm_srst_nxt_state = ENUM_ST_HOLD;
      end
      ENUM_ST_HOLD: begin
        if (i_rst_n_sw) begin
          w_fsm_srst_nxt_state = ENUM_ST_REL;
        end
      end
      ENUM_ST_REL: begin
        // Flush check: acknowledge 0 and read pointer seen as 0
        if (!w_ack_view && (w_rd_ptr_view == '0)) begin
          w_fsm_srst_nxt_state = ENUM_ST_RUN;
        end
      end
      default: begin
        w_fsm_srst_nxt_state = ENUM_ST_RUN;
      end
    endcase
  end

  // REQ: SF-3-47, SF-10.7-10
  // A new request that arrives while a sequence runs (a low level in REL, or
  // a new falling edge in REQ or PTR) is remembered and served from RUN.
  assign w_sw_rst_fall = ~i_rst_n_sw & ~reg_sw_rst_req_d;

  always_comb begin
    w_sw_rst_pend_nxt = reg_sw_rst_pend;
    case (reg_fsm_srst_current_state)
      ENUM_ST_RUN: begin
        w_sw_rst_pend_nxt = 1'b0;
      end
      ENUM_ST_REQ, ENUM_ST_PTR: begin
        w_sw_rst_pend_nxt = reg_sw_rst_pend | w_sw_rst_fall;
      end
      ENUM_ST_HOLD: begin
        w_sw_rst_pend_nxt = reg_sw_rst_pend;
      end
      ENUM_ST_REL: begin
        w_sw_rst_pend_nxt = reg_sw_rst_pend | ~i_rst_n_sw;
      end
      default: begin
        w_sw_rst_pend_nxt = 1'b0;
      end
    endcase
  end

  // REQ: SF-3-44, SF-6.2-02, SF-14.2.1-06, SF-3-46, SF-7.3-08, SF-10.7-09
  // FSM, busy, request and handshake flops; hardware reset has priority
  always_ff @(posedge i_clk_wr or negedge i_rst_n_wr) begin
    if (!i_rst_n_wr) begin
      reg_fsm_srst_current_state <= ENUM_ST_RUN;
      reg_sw_rst_busy            <= 1'b0;
      reg_req                    <= 1'b0;
      reg_sw_rst_pend            <= 1'b0;
      reg_sw_rst_req_d           <= 1'b0;
    end else begin
      reg_fsm_srst_current_state <= w_fsm_srst_nxt_state;
      // Busy: 1 from the cycle after the request is taken until back in RUN
      reg_sw_rst_busy            <= (w_fsm_srst_nxt_state != ENUM_ST_RUN);
      // Request: set with busy, cleared when REL starts
      reg_req                    <= (w_fsm_srst_nxt_state == ENUM_ST_REQ)
                                  | (w_fsm_srst_nxt_state == ENUM_ST_PTR)
                                  | (w_fsm_srst_nxt_state == ENUM_ST_HOLD);
      reg_sw_rst_pend            <= w_sw_rst_pend_nxt;
      reg_sw_rst_req_d           <= ~i_rst_n_sw;
    end
  end

  // --------------------------------------------------------------------------
  // Outputs
  // --------------------------------------------------------------------------
  // REQ: SF-3-21, SF-10.6-03, SF-3-35
  // Flag flops combined with the block term by one gate
  assign w_full_thr_blk = (i_full_thr == '0);
  assign o_full         = w_block | reg_full;
  assign o_full_thr     = w_block ? w_full_thr_blk : reg_full_thr;
  assign o_overflow     = reg_overflow;
  assign o_sw_rst_busy  = reg_sw_rst_busy;

  // REQ: SF-14.2.1-02, SF-14.2.1-06
  assign o_wr_ptr = reg_wr_ptr;
  assign o_req_wr = reg_req;

  // REQ: SF-14.2.1-03, SF-14.2.1-04, SF-14.2.1-05, SF-3-13
  // Memory write port: address = write pointer modulo DEPTH
  assign o_mem_wr_en   = w_wr_accept;
  assign o_mem_wr_addr = (reg_wr_ptr >= PARA_SFIFO_DEPTH[LPARA_PTR_W-1:0])
                       ? (reg_wr_ptr[LPARA_ADDR_W-1:0]
                          - PARA_SFIFO_DEPTH[LPARA_ADDR_W-1:0])
                       : reg_wr_ptr[LPARA_ADDR_W-1:0];
  assign o_mem_wr_data = i_wr_data;

endmodule

`default_nettype wire
