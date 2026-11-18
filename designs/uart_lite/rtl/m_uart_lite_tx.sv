// ============================================================================
// Module  : m_uart_lite_tx
// Purpose : uart_lite transmitter. Takes one byte over a valid/ready stream
//           (i_tx_valid / o_tx_ready / i_tx_data) and sends it on o_txd as an
//           8N1 frame: start bit 0, data bits LSB first, stop bit 1. Each bit
//           lasts PARA_UART_CLKS_PER_BIT cycles of i_clk. o_tx_ready goes back
//           to 1 in the last cycle of the stop bit, so frames can follow each
//           other with no idle bit in between.
// Spec    : uart_lite_Design_Specification.md sections 1.2, 4, 5, 6.2, 7.1,
//           7.2, 7.3, 8.1, 10.7, 10.8, 13.
// Notes   : The only transmit storage is the shift register r_tx_shift
//           (the byte being sent). The transmitter is idle whenever
//           o_tx_ready = 1; while it is idle the bit counters are not used.
// ============================================================================
module m_uart_lite_tx #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic       i_clk,
  input  logic       i_rst_n,
  input  logic       i_tx_valid,
  input  logic [7:0] i_tx_data,
  output logic       o_tx_ready,
  output logic       o_txd
);

  // REQ: UL-13-06, UL-10.8-01, UL-4-03
  // Bit-period counter: just wide enough to hold N-1 (at most 16 bits for
  // N <= 65535), so it never wraps early at N = 65535.
  localparam int                     LPARA_CNT_W        = $clog2(PARA_UART_CLKS_PER_BIT);
  localparam logic [LPARA_CNT_W-1:0] LPARA_CNT_BIT_LAST = LPARA_CNT_W'(PARA_UART_CLKS_PER_BIT - 1);
  localparam logic [LPARA_CNT_W-1:0] LPARA_CNT_ONE      = LPARA_CNT_W'(1);
  localparam logic [3:0]             LPARA_IDX_STOP     = 4'd9;  // frame bit 9 = stop bit

  logic [LPARA_CNT_W-1:0] r_tx_cnt;      // cycles left in the current bit, minus 1
  logic [3:0]             r_tx_bit_idx;  // current frame bit 0..9
  logic [7:0]             r_tx_shift;    // data bits not yet sent, LSB next
  logic                   w_tx_accept;
  logic                   w_tx_cnt_zero;

  // REQ: UL-7.2-01, UL-5-02, UL-6.2-03, UL-10.7-01, UL-7.2-06, UL-7.2-07
  // Handshake: i_tx_valid = 1 and o_tx_ready = 1 at the edge. i_rst_n = 1 is
  // implied because every register below is held in reset while i_rst_n = 0.
  assign w_tx_accept   = i_tx_valid & o_tx_ready;
  assign w_tx_cnt_zero = (r_tx_cnt == '0);

  // REQ: UL-6.1-01, UL-13-04, UL-6.2-01, UL-6.2-02, UL-6.2-06, UL-14-08, UL-6.2-10, UL-5-03, UL-5-14, UL-14-01
  // All flip-flops: rising edge of i_clk, asynchronous active-low reset.
  // Reset abandons any frame: o_txd = 1 and o_tx_ready = 1 at once.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      o_txd        <= 1'b1;
      o_tx_ready   <= 1'b1;
      r_tx_cnt     <= '0;
      r_tx_bit_idx <= 4'd0;
      r_tx_shift   <= 8'd0;
    end else if (w_tx_accept) begin
      // REQ: UL-7.2-02, UL-7.2-08, UL-8.1-01, UL-7.3-03, UL-1.2-04, UL-8.1-05, UL-8.1-06
      // Capture i_tx_data only at the accepting edge E0; the start bit is on
      // o_txd in the cycle after E0 (also when E0 is the last edge of the
      // previous stop bit, so back-to-back frames have no idle cycle).
      o_txd        <= 1'b0;
      o_tx_ready   <= 1'b0;
      r_tx_cnt     <= LPARA_CNT_BIT_LAST;
      r_tx_bit_idx <= 4'd0;
      r_tx_shift   <= i_tx_data;
    end else if (o_tx_ready) begin
      // REQ: UL-7.2-03, UL-7.3-04, UL-7.3-05, UL-1.2-01
      // Idle (or end of a stop bit with no new byte): line stays high.
      o_txd <= 1'b1;
    end else if (!w_tx_cnt_zero) begin
      // REQ: UL-1.1-02, UL-4-01, UL-7.2-04, UL-7.2-05, UL-8.1-02, UL-8.1-03
      // Inside a bit. In the stop bit, o_tx_ready becomes 1 at edge
      // E0+10N-1 (last stop-bit cycle); the stop bit still ends at E0+10N.
      r_tx_cnt <= r_tx_cnt - LPARA_CNT_ONE;
      if ((r_tx_bit_idx == LPARA_IDX_STOP) && (r_tx_cnt == LPARA_CNT_ONE)) begin
        o_tx_ready <= 1'b1;
      end
    end else begin
      // REQ: UL-1.1-01, UL-7.1-01, UL-5-04, UL-7.3-01
      // Bit boundary: next frame bit. Data bits leave LSB first; the shift
      // register fills with 1, so after the 8 data bits it supplies the stop
      // bit (frame bit 9 = 1).
      r_tx_cnt     <= LPARA_CNT_BIT_LAST;
      r_tx_bit_idx <= r_tx_bit_idx + 4'd1;
      o_txd        <= r_tx_shift[0];
      r_tx_shift   <= {1'b1, r_tx_shift[7:1]};
    end
  end

endmodule
