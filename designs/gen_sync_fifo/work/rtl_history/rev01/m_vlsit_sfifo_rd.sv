// ============================================================================
// Module  : m_vlsit_sfifo_rd
// Purpose : Read side of the synchronous-clock FIFO (CLK-RD / RST-RD): read
//           pointer (modulo 2 x DEPTH), read acceptance, look-ahead empty and
//           empty-threshold flags, underflow pulse, memory read address (the
//           address of the next read pointer, show-ahead), optional retiming
//           flops of the write pointer and the request, and the read-side
//           software reset FSM with its acknowledge flop.
// Spec    : SyncFIFO_Design_Specification.md sections 5.1, 5.3, 5.4, 6.2,
//           6.3, 7.3, 9, 10.1, 10.2, 10.5, 10.6, 10.7, 12, 14.2, 14.2.1
// ============================================================================
`default_nettype none

module m_vlsit_sfifo_rd #(
    // PARA_SFIFO_DEPTH: number of FIFO entries
    // Legal values: any integer of 2 or more, no upper limit
    // Default: 8
    parameter logic [31:0] PARA_SFIFO_DEPTH      = 8,
    // PARA_SFIFO_DATA_W: data word width in bits
    // Legal values: 1 or more, no upper limit
    // Default: 32
    parameter logic [31:0] PARA_SFIFO_DATA_W     = 32,
    // PARA_SFIFO_PTR_RETIME: 0 = direct write pointer, 1 = one retiming flop
    // Legal values: 0 or 1
    // Default: 0
    parameter logic [31:0] PARA_SFIFO_PTR_RETIME = 0,
    // Derived: memory address width, pointer width, occupancy width
    localparam logic [31:0] LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_PTR_W  = $clog2(2 * PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_OCC_W  = $clog2(PARA_SFIFO_DEPTH + 1)
) (
    // Clock and reset (CLK-RD)
    input  wire                          i_clk_rd,
    input  wire                          i_rst_n_rd,
    // Read interface
    input  wire                          i_rd_en,
    input  wire  [LPARA_OCC_W-1:0]       i_empty_thr,
    output logic [PARA_SFIFO_DATA_W-1:0] o_rd_data,
    output logic                         o_empty,
    output logic                         o_empty_thr,
    output logic                         o_underflow,
    // Pointers and handshake with the write side
    input  wire  [LPARA_PTR_W-1:0]       i_wr_ptr,
    output logic [LPARA_PTR_W-1:0]       o_rd_ptr,
    input  wire                          i_req_wr,
    output logic                         o_ack_rd,
    // Memory read port
    output logic [LPARA_ADDR_W-1:0]      o_mem_rd_addr,
    input  wire  [PARA_SFIFO_DATA_W-1:0] i_mem_rd_data
);

  // --------------------------------------------------------------------------
  // Constants
  // --------------------------------------------------------------------------
  localparam logic [31:0] LPARA_TWO_DEPTH = 2 * PARA_SFIFO_DEPTH;
  localparam logic [31:0] LPARA_PTR_LAST  = (2 * PARA_SFIFO_DEPTH) - 1;
  localparam logic [31:0] LPARA_PTR_ONE   = 1;

  // --------------------------------------------------------------------------
  // Read reset FSM states (2 bits, encoding 3 recovers to RUN)
  // --------------------------------------------------------------------------
  typedef enum logic [1:0] {
    ENUM_ST_RUN = 2'd0,
    ENUM_ST_RST = 2'd1,
    ENUM_ST_ACK = 2'd2
  } t_fsm_srst_rd_e;

  t_fsm_srst_rd_e reg_fsm_srst_current_state;
  t_fsm_srst_rd_e w_fsm_srst_nxt_state;

  // --------------------------------------------------------------------------
  // Signals
  // --------------------------------------------------------------------------
  logic [LPARA_PTR_W-1:0] reg_rd_ptr;
  logic [LPARA_PTR_W-1:0] w_rd_ptr_inc;
  logic [LPARA_PTR_W-1:0] w_rd_ptr_nxt;
  logic [LPARA_PTR_W-1:0] w_wr_ptr_view;
  logic                   w_req_view;
  logic [LPARA_PTR_W:0]   w_occ_nxt;
  logic [LPARA_PTR_W:0]   w_empty_thr_ext;
  logic                   reg_empty;
  logic                   reg_empty_thr;
  logic                   reg_underflow;
  logic                   reg_ack;
  logic                   w_block;
  logic                   w_rd_accept;

  // --------------------------------------------------------------------------
  // View of the write pointer and the request (timed paths, no synchronizer)
  // --------------------------------------------------------------------------
  // REQ: SF-1.1-04, SF-1.1-12, SF-3-24, SF-3-25, SF-3-26, SF-3-27, SF-3-28
  // REQ: SF-3-57, SF-14.2.1-01, SF-4-06, SF-5.3-02
  generate
    if (PARA_SFIFO_PTR_RETIME != 32'd0) begin : g_wr_ptr_retime
      // One plain retiming flop per crossing signal in the destination domain
      logic [LPARA_PTR_W-1:0] reg_wr_ptr_rt;
      logic                   reg_req_rt;

      always_ff @(posedge i_clk_rd or negedge i_rst_n_rd) begin
        if (!i_rst_n_rd) begin
          reg_wr_ptr_rt <= '0;
          reg_req_rt    <= 1'b0;
        end else begin
          reg_wr_ptr_rt <= i_wr_ptr;
          reg_req_rt    <= i_req_wr;
        end
      end

      assign w_wr_ptr_view = reg_wr_ptr_rt;
      assign w_req_view    = reg_req_rt;
    end else begin : g_wr_ptr_direct
      // Direct path into the flag logic
      assign w_wr_ptr_view = i_wr_ptr;
      assign w_req_view    = i_req_wr;
    end
  endgenerate

  // --------------------------------------------------------------------------
  // Software reset block term and read acceptance
  // --------------------------------------------------------------------------
  // REQ: SF-3-38, SF-3-39, SF-10.7-03, SF-6.3-11, SF-12-07
  // Block: request seen on the read side OR read FSM not in RUN
  assign w_block = w_req_view | (reg_fsm_srst_current_state != ENUM_ST_RUN);

  // REQ: SF-3-02, SF-6.3-03, SF-3-11, SF-5.4-02, SF-10.1-01
  // Accepted only if the own empty flag allows it
  assign w_rd_accept = i_rd_en & ~w_block & ~reg_empty;

  // --------------------------------------------------------------------------
  // Read pointer (modulo 2 x DEPTH)
  // --------------------------------------------------------------------------
  // REQ: SF-3-13, SF-9-01, SF-8-10
  assign w_rd_ptr_inc = (reg_rd_ptr == LPARA_PTR_LAST[LPARA_PTR_W-1:0])
                      ? '0
                      : (reg_rd_ptr + LPARA_PTR_ONE[LPARA_PTR_W-1:0]);

  // REQ: SF-5.3-04, SF-3-19, SF-10.1-07, SF-10.7-03
  always_comb begin
    w_rd_ptr_nxt = reg_rd_ptr;
    if (reg_fsm_srst_current_state == ENUM_ST_RST) begin
      w_rd_ptr_nxt = '0;
    end else if (w_rd_accept) begin
      w_rd_ptr_nxt = w_rd_ptr_inc;
    end
  end

  // --------------------------------------------------------------------------
  // Look-ahead occupancy of the read view: occ(wr_ptr_view, next read ptr)
  // --------------------------------------------------------------------------
  // REQ: SF-9-03, SF-5.4-01, SF-5.1-01, SF-5.4-04, SF-6.3-05
  assign w_occ_nxt = (w_wr_ptr_view >= w_rd_ptr_nxt)
                   ? ({1'b0, w_wr_ptr_view} - {1'b0, w_rd_ptr_nxt})
                   : ({1'b0, w_wr_ptr_view} + LPARA_TWO_DEPTH[LPARA_PTR_W:0]
                      - {1'b0, w_rd_ptr_nxt});

  // REQ: SF-9-06, SF-9-05
  // Threshold zero-extended for the comparison
  assign w_empty_thr_ext = {{(LPARA_PTR_W + 1 - LPARA_OCC_W){1'b0}}, i_empty_thr};

  // --------------------------------------------------------------------------
  // Pointer, flag and pulse flops
  // --------------------------------------------------------------------------
  // REQ: SF-3-08, SF-3-15, SF-3-18, SF-3-54, SF-10.6-05, SF-10.6-07, SF-3-29
  // REQ: SF-3-30, SF-7.3-02, SF-7.3-05, SF-6.2-06, SF-12-11, SF-14.2.1-07
  // REQ: SF-10.2-03, SF-10.2-06, SF-6.3-10, SF-12-04, SF-5.3-03, SF-3-52
  always_ff @(posedge i_clk_rd or negedge i_rst_n_rd) begin
    if (!i_rst_n_rd) begin
      reg_rd_ptr    <= '0;
      reg_empty     <= 1'b1;
      reg_empty_thr <= 1'b1;
      reg_underflow <= 1'b0;
    end else begin
      reg_rd_ptr    <= w_rd_ptr_nxt;
      reg_empty     <= (w_occ_nxt == '0);
      reg_empty_thr <= (w_occ_nxt <= w_empty_thr_ext);
      reg_underflow <= i_rd_en & ~w_block & reg_empty;
    end
  end

  // --------------------------------------------------------------------------
  // Read reset FSM (four-phase handshake, read side)
  // --------------------------------------------------------------------------
  // REQ: SF-10.1-06, SF-10.1-07, SF-10.1-08, SF-3-40, SF-3-41, SF-1.1-14
  // REQ: SF-10.7-03, SF-10.7-05
  always_comb begin
    w_fsm_srst_nxt_state = reg_fsm_srst_current_state;
    case (reg_fsm_srst_current_state)
      ENUM_ST_RUN: begin
        if (w_req_view) begin
          w_fsm_srst_nxt_state = ENUM_ST_RST;
        end
      end
      ENUM_ST_RST: begin
        w_fsm_srst_nxt_state = ENUM_ST_ACK;
      end
      ENUM_ST_ACK: begin
        // Flush check: request 0 and write pointer seen as 0
        if (!w_req_view && (w_wr_ptr_view == '0)) begin
          w_fsm_srst_nxt_state = ENUM_ST_RUN;
        end
      end
      default: begin
        w_fsm_srst_nxt_state = ENUM_ST_RUN;
      end
    endcase
  end

  // REQ: SF-14.2.1-10, SF-3-46, SF-7.3-08, SF-10.7-09
  // FSM and acknowledge flops; acknowledge 1 from leaving RST to leaving ACK
  always_ff @(posedge i_clk_rd or negedge i_rst_n_rd) begin
    if (!i_rst_n_rd) begin
      reg_fsm_srst_current_state <= ENUM_ST_RUN;
      reg_ack                    <= 1'b0;
    end else begin
      reg_fsm_srst_current_state <= w_fsm_srst_nxt_state;
      reg_ack                    <= (w_fsm_srst_nxt_state == ENUM_ST_ACK);
    end
  end

  // --------------------------------------------------------------------------
  // Outputs
  // --------------------------------------------------------------------------
  // REQ: SF-3-21, SF-10.6-06, SF-3-38
  // Flag flops combined with the block term by one gate
  assign o_empty     = w_block | reg_empty;
  assign o_empty_thr = w_block | reg_empty_thr;
  assign o_underflow = reg_underflow;

  // REQ: SF-14.2.1-07, SF-14.2.1-10
  assign o_rd_ptr = reg_rd_ptr;
  assign o_ack_rd = reg_ack;

  // REQ: SF-14.2.1-08, SF-10.5-01, SF-3-03, SF-6.3-04, SF-3-13
  // Memory read address: next read pointer modulo DEPTH (show-ahead)
  assign o_mem_rd_addr = (w_rd_ptr_nxt >= PARA_SFIFO_DEPTH[LPARA_PTR_W-1:0])
                       ? (w_rd_ptr_nxt[LPARA_ADDR_W-1:0]
                          - PARA_SFIFO_DEPTH[LPARA_ADDR_W-1:0])
                       : w_rd_ptr_nxt[LPARA_ADDR_W-1:0];

  // REQ: SF-3-22, SF-14.2.1-09, SF-20.2-01, SF-3-10
  // o_rd_data is the memory output register, no logic after it
  assign o_rd_data = i_mem_rd_data;

endmodule

`default_nettype wire
