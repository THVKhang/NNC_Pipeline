module nnc_chk_tx #(
  parameter int PARA_UART_CLKS_PER_BIT = 16
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_tx_valid,
  input  logic                        o_tx_ready,
  input  logic [7:0]                  i_tx_data,
  input  logic                        o_rx_valid,
  input  logic                        i_rx_ready,
  input  logic [7:0]                  o_rx_data,
  input  logic                        o_rx_frame_err,
  input  logic                        o_rx_overrun,
  input  logic                        o_txd,
  input  logic                        i_rxd
);

  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;
  int unsigned fails_CHK_011 = 0;
  int unsigned hits_CHK_011 = 0;
  int unsigned fails_CHK_012 = 0;
  int unsigned hits_CHK_012 = 0;
  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;

  localparam int unsigned FRAME_CLKS = 10 * PARA_UART_CLKS_PER_BIT;

  // TX reference model: tx_pos = m means the current edge is E0+m (1..FRAME_CLKS), 0 = no frame active
  logic        tx_accept;
  int unsigned tx_pos;
  logic [7:0]  tx_dat;
  int unsigned tx_bitidx;
  logic        tx_exp_bit;

  assign tx_accept = i_tx_valid && o_tx_ready && i_rst_n;

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      tx_pos <= 0;
      tx_dat <= 8'h00;
    end else begin
      if (tx_accept) begin
        tx_pos <= 1;
        tx_dat <= i_tx_data;
      end else if (tx_pos != 0 && tx_pos < FRAME_CLKS) begin
        tx_pos <= tx_pos + 1;
      end else begin
        tx_pos <= 0;
      end
    end
  end

  always_comb begin
    tx_bitidx = (tx_pos == 0) ? 0 : ((tx_pos - 1) / PARA_UART_CLKS_PER_BIT);
    if (tx_bitidx == 0)      tx_exp_bit = 1'b0;
    else if (tx_bitidx >= 9) tx_exp_bit = 1'b1;
    else                     tx_exp_bit = tx_dat[tx_bitidx - 1];
  end

  // CHK-010: Transmit handshake, acceptance condition and idle values (UL-7.2-01, UL-5-02, UL-7.2-03, UL-7.2-06, UL-7.3-05, UL-1.2-01, UL-5-14, UL-8.1-01)
  a_CHK_010: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (tx_pos == 0 || tx_pos == 1) |->
      ((tx_pos != 0 || (o_tx_ready && o_txd)) && (tx_pos != 1 || (!o_tx_ready && !o_txd))))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ((tx_pos == 0 || tx_pos == 1))) hits_CHK_010 <= hits_CHK_010 + 1;

  // CHK-011: Cycle-exact transmit frame content (UL-7.3-01, UL-1.1-01, UL-1.1-02, UL-7.1-01, UL-5-04, UL-8.1-01, UL-8.1-02, UL-7.2-02, UL-12.2-06, UL-4-01)
  a_CHK_011: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (tx_pos != 0) |-> (o_txd == tx_exp_bit))
    else begin fails_CHK_011++; $display("NNC_FAIL CHK-011 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ((tx_pos != 0))) hits_CHK_011 <= hits_CHK_011 + 1;

  // CHK-012: o_tx_ready timing during a frame (UL-7.2-04, UL-7.2-05, UL-8.1-03, UL-12.2-06)
  a_CHK_012: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (tx_pos != 0) |-> ((tx_pos < FRAME_CLKS) ? !o_tx_ready : o_tx_ready))
    else begin fails_CHK_012++; $display("NNC_FAIL CHK-012 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ((tx_pos != 0))) hits_CHK_012 <= hits_CHK_012 + 1;

  // CHK-013: No idle cycle between back-to-back frames; idle high after a frame (UL-7.3-03, UL-7.3-04, UL-1.2-04, UL-1.2-01)
  // At the first sample of any frame the start bit is 0 and the previous sample (stop bit or idle) was 1.
  a_CHK_013: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (tx_pos == 1) |-> (!o_txd && $past(o_txd)))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && ((tx_pos == 1))) hits_CHK_013 <= hits_CHK_013 + 1;

  final begin
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
    $display("NNC_CHECK CHK-011 hits=%0d fails=%0d", hits_CHK_011, fails_CHK_011);
    $display("NNC_CHECK CHK-012 hits=%0d fails=%0d", hits_CHK_012, fails_CHK_012);
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
  end
endmodule
