// ============================================================================
// Module  : m_uart_lite_rx
// Purpose : uart_lite receiver. Two-flip-flop synchronizer on i_rxd, falling
//           edge start detection, start-bit check at H = floor(N/2), middle-
//           of-bit sampling of 8 data bits (LSB first) and the stop bit, a
//           one-byte holding register on a valid/ready stream, frame error
//           flag and one-cycle overrun pulse.
// Spec    : uart_lite_Design_Specification.md sections 1.2, 4, 5, 6.2, 7.1,
//           7.4, 7.5, 7.6, 7.7, 7.8, 8.2, 8.4, 10.1-10.5, 10.7, 10.8, 13.
// Timing  : s(E) is captured by r_rxd_meta at edge E and is in r_rxd_sync in
//           the cycle after edge E+1. Every receiver decision about s(E) is
//           therefore registered at edge E+2. For the stop-bit sample M this
//           gives the delivery edge V = M + 2 of the specification.
// ============================================================================
module m_uart_lite_rx #(
  parameter int PARA_UART_CLKS_PER_BIT = 16,
  parameter int PARA_UART_HALF_BIT     = PARA_UART_CLKS_PER_BIT / 2
) (
  input  logic       i_clk,
  input  logic       i_rst_n,
  input  logic       i_rxd,
  input  logic       i_rx_ready,
  output logic       o_rx_valid,
  output logic [7:0] o_rx_data,
  output logic       o_rx_frame_err,
  output logic       o_rx_overrun
);

  // REQ: UL-13-06, UL-10.8-01, UL-4-02, UL-14-02, UL-4-03
  // Bit-period / half-bit counter: just wide enough for N-1 (<= 16 bits).
  localparam int                     LPARA_CNT_W         = $clog2(PARA_UART_CLKS_PER_BIT);
  localparam logic [LPARA_CNT_W-1:0] LPARA_CNT_BIT_LAST  = LPARA_CNT_W'(PARA_UART_CLKS_PER_BIT - 1);
  localparam logic [LPARA_CNT_W-1:0] LPARA_CNT_HALF_LAST = LPARA_CNT_W'(PARA_UART_HALF_BIT - 1);
  localparam logic [LPARA_CNT_W-1:0] LPARA_CNT_ONE       = LPARA_CNT_W'(1);

  // REQ: UL-7.4-02
  // Idle, or receiving (start check, data bits, stop bit).
  typedef enum logic [1:0] {
    RX_IDLE  = 2'd0,  // waiting for s(T0-1) = 1, s(T0) = 0
    RX_START = 2'd1,  // waiting for the start-bit check at T0+H
    RX_DATA  = 2'd2,  // sampling data bits at T0+H+(i+1)N
    RX_STOP  = 2'd3   // waiting for the stop-bit sample at M = T0+H+9N
  } rx_state_e;

  // REQ: UL-7.4-01, UL-5-15, UL-13-05
  // Exactly two synchronizer flip-flops, no logic in between; marked so that
  // synthesis keeps them as they are.
  (* keep = "true", async_reg = "true" *) logic r_rxd_meta;
  (* keep = "true", async_reg = "true" *) logic r_rxd_sync;
  logic                   r_rxd_prev;       // previous synchronised value s(E-1)

  rx_state_e              r_rx_state;
  rx_state_e              w_rx_state_nxt;
  logic [LPARA_CNT_W-1:0] r_rx_cnt;
  logic [LPARA_CNT_W-1:0] w_rx_cnt_nxt;
  logic [2:0]             r_rx_bit_cnt;
  logic [2:0]             w_rx_bit_cnt_nxt;
  logic [7:0]             r_rx_shift;
  logic [7:0]             w_rx_shift_nxt;
  logic                   w_rx_start_fall;
  logic                   w_rx_cnt_zero;
  logic                   w_rx_frame_done;
  logic                   w_rx_take;
  logic                   w_rx_load;
  logic                   w_rx_drop;

  // REQ: UL-7.4-01, UL-6.2-05, UL-14-06, UL-6.2-12, UL-6.1-01, UL-13-04, UL-6.2-01
  // Synchronizer and previous-value flip-flop all reset to 1, so the first
  // sample after reset release sees s(R1-1) = 1.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_rxd_meta <= 1'b1;
      r_rxd_sync <= 1'b1;
      r_rxd_prev <= 1'b1;
    end else begin
      r_rxd_meta <= i_rxd;
      r_rxd_sync <= r_rxd_meta;
      r_rxd_prev <= r_rxd_sync;
    end
  end

  // REQ: UL-7.4-03, UL-7.4-04, UL-1.2-07, UL-7.7-03, UL-14-05, UL-10.4-02, UL-10.4-03
  // Start condition: s(E-1) = 1 and s(E) = 0 (one high sample is enough).
  assign w_rx_start_fall = r_rxd_prev & ~r_rxd_sync;
  assign w_rx_cnt_zero   = (r_rx_cnt == '0);

  // REQ: UL-7.4-02, UL-7.4-05, UL-7.4-07, UL-7.4-08, UL-7.5-01, UL-7.5-02, UL-7.5-03, UL-7.5-04, UL-7.5-05, UL-7.5-06, UL-1.2-08, UL-1.1-01, UL-7.1-01, UL-1.1-02, UL-14-02, UL-10.3-01, UL-10.3-02, UL-8.2-03
  // Receiver sequencer. Only s(T0-1), s(T0), s(T0+H), the 8 data samples
  // and s(M) are used; all other samples while receiving are ignored. It
  // never waits for i_rx_ready.
  always_comb begin
    w_rx_state_nxt   = r_rx_state;
    w_rx_cnt_nxt     = r_rx_cnt;
    w_rx_bit_cnt_nxt = r_rx_bit_cnt;
    w_rx_shift_nxt   = r_rx_shift;
    w_rx_frame_done  = 1'b0;
    case (r_rx_state)
      RX_IDLE: begin
        if (w_rx_start_fall) begin
          // T0 detected: start-bit check H edges later.
          w_rx_state_nxt = RX_START;
          w_rx_cnt_nxt   = LPARA_CNT_HALF_LAST;
        end
      end
      RX_START: begin
        if (!w_rx_cnt_zero) begin
          w_rx_cnt_nxt = r_rx_cnt - LPARA_CNT_ONE;
        end else if (r_rxd_sync) begin
          // s(T0+H) = 1: glitch, back to idle, outputs untouched.
          w_rx_state_nxt = RX_IDLE;
        end else begin
          // Start bit confirmed: first data sample N edges later.
          w_rx_state_nxt   = RX_DATA;
          w_rx_cnt_nxt     = LPARA_CNT_BIT_LAST;
          w_rx_bit_cnt_nxt = 3'd0;
        end
      end
      RX_DATA: begin
        if (!w_rx_cnt_zero) begin
          w_rx_cnt_nxt = r_rx_cnt - LPARA_CNT_ONE;
        end else begin
          // Data bit i = s(T0+H+(i+1)N); LSB received first.
          w_rx_shift_nxt = {r_rxd_sync, r_rx_shift[7:1]};
          w_rx_cnt_nxt   = LPARA_CNT_BIT_LAST;
          if (r_rx_bit_cnt == 3'd7) begin
            w_rx_state_nxt = RX_STOP;
          end else begin
            w_rx_bit_cnt_nxt = r_rx_bit_cnt + 3'd1;
          end
        end
      end
      RX_STOP: begin
        if (!w_rx_cnt_zero) begin
          w_rx_cnt_nxt = r_rx_cnt - LPARA_CNT_ONE;
        end else begin
          // Stop-bit sample s(M): the frame completes whatever its value;
          // the receiver is idle from here on.
          w_rx_state_nxt  = RX_IDLE;
          w_rx_frame_done = 1'b1;
        end
      end
      default: begin
        w_rx_state_nxt = RX_IDLE;
      end
    endcase
  end

  // REQ: UL-6.2-11, UL-6.2-08, UL-6.2-04, UL-6.1-01, UL-13-04, UL-6.2-01
  // Sequencer registers: reset discards a partly received frame.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_rx_state   <= RX_IDLE;
      r_rx_cnt     <= '0;
      r_rx_bit_cnt <= 3'd0;
      r_rx_shift   <= 8'd0;
    end else begin
      r_rx_state   <= w_rx_state_nxt;
      r_rx_cnt     <= w_rx_cnt_nxt;
      r_rx_bit_cnt <= w_rx_bit_cnt_nxt;
      r_rx_shift   <= w_rx_shift_nxt;
    end
  end

  // REQ: UL-5-07, UL-7.6-03, UL-7.6-06, UL-10.7-02
  // Take: o_rx_valid = 1 and i_rx_ready = 1 (i_rst_n = 1 implied by reset).
  assign w_rx_take = o_rx_valid & i_rx_ready;
  // REQ: UL-7.6-01, UL-7.6-02, UL-14-04, UL-10.2-02, UL-8.2-01, UL-14-03
  // Load at V = M+2 when the holding register is empty or is emptied now.
  assign w_rx_load = w_rx_frame_done & (~o_rx_valid | i_rx_ready);
  // REQ: UL-7.8-01, UL-10.2-01, UL-1.2-10, UL-5-13
  // Drop at V when the holding register is full and not being emptied.
  assign w_rx_drop = w_rx_frame_done & o_rx_valid & ~i_rx_ready;

  // REQ: UL-1.2-05, UL-5-05, UL-5-06, UL-5-08, UL-5-09, UL-5-10, UL-5-11, UL-5-12, UL-6.2-02, UL-6.2-08, UL-6.2-09, UL-7.1-04, UL-7.6-04, UL-7.6-05, UL-7.6-07, UL-14-07
  // Holding register and overrun pulse; all outputs are flip-flops.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      o_rx_valid     <= 1'b0;
      o_rx_data      <= 8'd0;
      o_rx_frame_err <= 1'b0;
      o_rx_overrun   <= 1'b0;
    end else begin
      // REQ: UL-7.8-02, UL-7.8-04, UL-7.8-05, UL-7.8-06, UL-7.4-06, UL-8.4-01
      // One-cycle pulse, only for a dropped completed frame; not qualified
      // by o_rx_valid. Glitches and reset-cut frames never complete.
      o_rx_overrun <= w_rx_drop;
      if (w_rx_load) begin
        // REQ: UL-1.2-09, UL-7.7-01, UL-7.7-02, UL-10.1-01, UL-10.4-01, UL-10.5-01
        // Frame error = inverse of the stop-bit sample s(M); the byte is
        // delivered like any other byte.
        o_rx_valid     <= 1'b1;
        o_rx_data      <= r_rx_shift;
        o_rx_frame_err <= ~r_rxd_sync;
      end else if (w_rx_take) begin
        // REQ: UL-7.6-03, UL-7.8-03, UL-10.2-03, UL-14-09
        // Byte taken with nothing new: valid drops, data/flag keep values.
        // On a drop nothing here changes: held byte kept, new flag lost.
        o_rx_valid <= 1'b0;
      end
    end
  end

endmodule
