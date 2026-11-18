// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Helper: counts the first i_clk cycles from the start of the trace (saturates at 2).
  // It is NOT cleared by i_rst_n on purpose. UL-12.1-02 only applies at the start of
  // simulation. Reset may be asserted again later, at any time and for any length
  // (UL-12.3-04), and that must stay unconstrained.
  // ---------------------------------------------------------------------------
  logic [1:0] env_init_cnt = 2'd0;

  always @(posedge i_clk) begin
    if (env_init_cnt != 2'd2)
      env_init_cnt <= env_init_cnt + 2'd1;
  end

  // ENV-01: i_rst_n is held at 0 for at least the first 2 i_clk cycles of the trace (UL-12.1-02)
  always @(*) begin
    if (env_init_cnt != 2'd2)
      assume (!i_rst_n);
  end

  // Deliberately unconstrained (the specification calls these legal or places no obligation):
  //  - i_tx_valid may fall before a handshake, and i_tx_data may change at any edge
  //    (UL-7.2-02, UL-7.2-07, UL-12.4-07). There is no hold-until-ready rule.
  //  - i_rx_ready is free in every cycle, including when o_rx_valid = 0 (UL-7.6-06, UL-12.4-06).
  //  - i_rxd is any bit sequence: glitches, breaks, low at reset release, frame errors and
  //    back-to-back frames (UL-10.x, UL-12.3-0x).
  //  - i_rst_n may be asserted again at any cycle after the start (UL-12.3-04).
  //  - Synchronous release (UL-12.1-01), absence of X/Z (UL-12.1-03, UL-12.1-05) and moving
  //    i_rxd away from clock edges (UL-12.1-04) hold by construction in the synchronous,
  //    two-valued formal model.
endmodule
