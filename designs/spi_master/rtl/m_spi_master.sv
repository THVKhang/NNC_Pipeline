// =============================================================================
// Module  : m_spi_master
// Purpose : Single-clock SPI master with one slave select. One 8-bit full-duplex
//           transfer (MSB first) per command of a valid/ready command stream,
//           one received byte per transfer on a valid/ready response stream.
//           Bursts framed by i_cmd_last, SPI modes 0..3 captured per burst,
//           SCLK = f(i_clk) / (2 * PARA_SPI_CLK_DIV), lead/trail/gap of one
//           SCLK half period, one shown + one held response byte under
//           back-pressure, asynchronous active-low reset.
// Spec    : spi_master_Design_Specification.md rev 0.1
//           sections 1.1, 1.2, 3 (terms), 4 (parameters), 5 (interface),
//           6.1 (clocks), 6.2 (resets), 7 (phases), 7.1 (command stream),
//           7.2 (burst framing / slave select), 7.3 (SPI modes),
//           7.4 (SCLK generation), 7.5 (MOSI), 7.6 (MISO), 7.7 (response
//           stream), 7.8 (continuation, pause, end of burst), 8 (timing),
//           10 (corner cases), 13 (implementation constraints), 14 (decisions).
// =============================================================================
module m_spi_master #(
  // D: number of i_clk cycles in one SCLK half period, legal 1 to 255
  parameter int PARA_SPI_CLK_DIV = 4
) (
  input  logic       i_clk,
  input  logic       i_rst_n,
  // Command stream
  input  logic       i_cmd_valid,
  output logic       o_cmd_ready,
  input  logic [7:0] i_cmd_data,
  input  logic       i_cmd_last,
  // Response stream
  output logic       o_rsp_valid,
  input  logic       i_rsp_ready,
  output logic [7:0] o_rsp_data,
  // SPI
  output logic       o_sclk,
  output logic       o_mosi,
  input  logic       i_miso,
  output logic       o_cs_n,
  // Mode configuration (quasi-static)
  input  logic       i_cpol,
  input  logic       i_cpha
);

  // ---------------------------------------------------------------------------
  // Parameter legality check (elaboration time)
  // ---------------------------------------------------------------------------
  // REQ: SPI-4-03, SPI-14-11
`ifndef SYNTHESIS
  generate
    if ((PARA_SPI_CLK_DIV < 1) || (PARA_SPI_CLK_DIV > 255)) begin : g_illegal_para_spi_clk_div
      $error("m_spi_master: PARA_SPI_CLK_DIV = %0d is illegal, legal values are 1 to 255",
             PARA_SPI_CLK_DIV);
    end
  endgenerate
`endif

  // ---------------------------------------------------------------------------
  // Local parameters
  // ---------------------------------------------------------------------------
  // REQ: SPI-13-13, SPI-10-16, SPI-4-04
  // Half-period counter: 8 bits, enough for D = 255 (counts 0 .. D-1).
  localparam int unsigned          LP_CNT_W     = 8;
  localparam logic [LP_CNT_W-1:0]  LP_DIV_LAST  = 8'(PARA_SPI_CLK_DIV - 1);
  // SCLK edge counter: number of SCLK edges already made in the transfer (0..15)
  localparam logic [3:0]           LP_EDGE_LAST = 4'd15;

  // ---------------------------------------------------------------------------
  // Phase state machine (spec section 7, phase table)
  // ---------------------------------------------------------------------------
  typedef enum logic [1:0] {
    ST_IDLE  = 2'd0,  // o_cs_n = 1
    ST_XFER  = 2'd1,  // transfer of one byte (16*D cycles)
    ST_PAUSE = 2'd2,  // inside a burst, waiting for the next command
    ST_TRAIL = 2'd3   // D cycles after SCLK edge 16 of the last byte
  } state_e;

  // ---------------------------------------------------------------------------
  // Registers
  // ---------------------------------------------------------------------------
  state_e               r_state;
  logic                 r_cs_n;        // drives o_cs_n directly
  logic                 r_sclk;        // internal SCLK, used while o_cs_n = 0
  logic                 r_cpol_b;      // CPOL_b
  logic                 r_cpha_b;      // CPHA_b
  logic [LP_CNT_W-1:0]  r_div_cnt;     // half-period counter / Idle gap counter
  logic [3:0]           r_edge_cnt;    // SCLK edges done in current transfer
  logic                 r_last;        // captured i_cmd_last of current transfer
  logic                 r_mosi;        // drives o_mosi directly
  logic [7:0]           r_tx_shift;    // bits still to be sent, MSB first
  logic [7:0]           r_rx_shift;    // bits received, shifted in at LSB
  logic                 r_rsp_valid;   // shown byte present
  logic [7:0]           r_rsp_data;    // shown byte
  logic                 r_held_valid;  // held byte present
  logic [7:0]           r_held_data;   // held byte

  // ---------------------------------------------------------------------------
  // Combinational strobes (from flip-flops, plus handshake inputs)
  // ---------------------------------------------------------------------------
  logic       cmd_ready;
  logic       cmd_hs;
  logic       rsp_hs;
  logic       div_tick;
  logic       sclk_edge;
  logic       xfer_last_cycle;
  logic       sample_edge;
  logic       shift_edge;
  logic       cpha_load;
  logic       sclk_next;
  logic [7:0] rx_byte;

  // End of a half period: the next edge is an SCLK edge (in Transfer), the
  // end of Trail, or the end of the blocked Idle cycles.
  // REQ: SPI-1.2-05, SPI-4-02
  assign div_tick        = (r_div_cnt == LP_DIV_LAST);

  // SCLK edge k = r_edge_cnt + 1 happens at the end of this cycle (edge A + k*D)
  // REQ: SPI-3-02, SPI-7.4-01
  assign sclk_edge       = (r_state == ST_XFER) && div_tick;

  // Last cycle of a transfer: ends at SCLK edge 16 (edge A + 16*D)
  // REQ: SPI-3-01
  assign xfer_last_cycle = sclk_edge && (r_edge_cnt == LP_EDGE_LAST);

  // Sampling edges: odd k (r_edge_cnt even) for CPHA_b = 0, even k for CPHA_b = 1
  // REQ: SPI-7.3-04, SPI-7.3-05, SPI-5-15, SPI-7.6-01, SPI-7.6-02
  assign sample_edge     = sclk_edge && (r_edge_cnt[0] == r_cpha_b);

  // Shift edges: even k = 2..14 for CPHA_b = 0, odd k = 1..15 for CPHA_b = 1
  // REQ: SPI-7.3-04, SPI-7.3-05, SPI-7.5-03, SPI-7.5-04, SPI-7.5-07
  assign shift_edge      = sclk_edge && (r_edge_cnt[0] != r_cpha_b)
                           && (r_edge_cnt != LP_EDGE_LAST);

  // Level of SCLK after edge k = r_edge_cnt + 1: odd k leaves the idle level
  // (NOT CPOL_b), even k returns to it (CPOL_b).
  // REQ: SPI-7.4-04, SPI-3-03, SPI-7.3-02
  assign sclk_next       = r_edge_cnt[0] ? r_cpol_b : ~r_cpol_b;

  // CPHA used to launch d[7] at the acceptance edge: i_cpha when the burst
  // starts at this edge (captured at the same edge), CPHA_b otherwise.
  // REQ: SPI-7.3-01, SPI-7.3-03, SPI-7.8-05
  assign cpha_load       = (r_state == ST_IDLE) ? i_cpha : r_cpha_b;

  // Received byte at SCLK edge 16. With CPHA_b = 1 bit r[0] is sampled at that
  // same edge, so it is taken from i_miso (value of the cycle ending there).
  // REQ: SPI-7.6-03, SPI-7.6-05, SPI-14-06
  assign rx_byte         = r_cpha_b ? {r_rx_shift[6:0], i_miso} : r_rx_shift;

  // Handshakes. i_rst_n = 0 holds every register in reset, so no command is
  // accepted and no response is taken during reset.
  // REQ: SPI-7.1-01, SPI-6.2-07, SPI-10-05, SPI-7.7-10
  assign cmd_hs          = i_cmd_valid && cmd_ready;
  assign rsp_hs          = r_rsp_valid && i_rsp_ready;

  // ---------------------------------------------------------------------------
  // o_cmd_ready: logic of flip-flops only, no combinational path from inputs.
  // Reset value 1: r_state = ST_IDLE, r_div_cnt = LP_DIV_LAST, r_rsp_valid = 0.
  // ---------------------------------------------------------------------------
  // REQ: SPI-5-04, SPI-5-05, SPI-6.2-06, SPI-7.1-05, SPI-7.1-06, SPI-7.1-07, SPI-7.1-08, SPI-7.1-09, SPI-7.1-10, SPI-7.1-11, SPI-7.1-12, SPI-13-10, SPI-14-03, SPI-14-04, SPI-14-05, SPI-14-16, SPI-1.1-04, SPI-7.8-07, SPI-8-12, SPI-8-15, SPI-10-07, SPI-7.7-13
  always_comb begin
    cmd_ready = 1'b0;
    case (r_state)
      // Blocked during the first D-1 cycles after o_cs_n rose
      ST_IDLE:  cmd_ready = div_tick && !r_rsp_valid;
      // Only in the last cycle of a non-last transfer
      ST_XFER:  cmd_ready = xfer_last_cycle && !r_last && !r_rsp_valid;
      ST_PAUSE: cmd_ready = !r_rsp_valid;
      ST_TRAIL: cmd_ready = 1'b0;
      default:  cmd_ready = 1'b0;
    endcase
  end

  assign o_cmd_ready = cmd_ready;

  // ---------------------------------------------------------------------------
  // Phase FSM, slave select, SCLK, mode capture, counters
  // ---------------------------------------------------------------------------
  // REQ: SPI-6.1-01, SPI-6.1-02, SPI-6.1-03, SPI-13-03, SPI-13-04, SPI-1.2-10, SPI-5-01, SPI-6.2-01, SPI-6.2-02, SPI-6.2-08, SPI-6.2-11, SPI-6.2-12, SPI-14-10, SPI-14-21, SPI-10-09, SPI-10-11, SPI-5-13
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_state    <= ST_IDLE;
      r_cs_n     <= 1'b1;
      r_sclk     <= 1'b0;
      r_cpol_b   <= 1'b0;
      r_cpha_b   <= 1'b0;
      // Idle with the gap requirement met: accept at the first edge after reset
      r_div_cnt  <= LP_DIV_LAST;
      r_edge_cnt <= 4'd0;
      r_last     <= 1'b0;
    end else begin
      case (r_state)
        // ---------------------------------------------------------------------
        ST_IDLE: begin
          if (cmd_hs) begin
            // REQ: SPI-7.2-01, SPI-8-02, SPI-7.3-01, SPI-1.2-04, SPI-3-04, SPI-1.2-03, SPI-7.1-02, SPI-5-07, SPI-1.2-02, SPI-5-14, SPI-5-16
            r_state    <= ST_XFER;
            r_cs_n     <= 1'b0;
            r_cpol_b   <= i_cpol;
            r_cpha_b   <= i_cpha;
            r_sclk     <= i_cpol;   // equal to o_sclk before the edge: no glitch
            r_div_cnt  <= '0;       // REQ: SPI-7.2-04, SPI-8-01, SPI-14-01
            r_edge_cnt <= 4'd0;
            r_last     <= i_cmd_last;
          end else if (!div_tick) begin
            // Count the blocked Idle cycles R .. R+D-2, then saturate
            // REQ: SPI-7.1-07, SPI-7.2-05, SPI-8-05, SPI-14-02, SPI-8-08, SPI-8-09
            r_div_cnt  <= r_div_cnt + 1'b1;
          end
        end
        // ---------------------------------------------------------------------
        ST_XFER: begin
          if (div_tick) begin
            // SCLK edge k: odd k leaves, even k returns to CPOL_b
            // REQ: SPI-7.4-01, SPI-7.4-02, SPI-7.4-04, SPI-3-03, SPI-7.4-07, SPI-1.2-05
            r_sclk    <= sclk_next;
            r_div_cnt <= '0;
            if (r_edge_cnt == LP_EDGE_LAST) begin
              // SCLK edge 16 (edge A + 16*D): end of the transfer
              r_edge_cnt <= 4'd0;
              if (cmd_hs) begin
                // Next byte joins without gap; this edge is its acceptance edge
                // REQ: SPI-7.8-01, SPI-1.2-07, SPI-8-06, SPI-7.1-02, SPI-10-15
                r_last  <= i_cmd_last;
              end else if (r_last) begin
                // REQ: SPI-7.8-06, SPI-3-06, SPI-8-13
                r_state <= ST_TRAIL;
              end else begin
                // REQ: SPI-7.8-02, SPI-1.2-08, SPI-3-05, SPI-8-13
                r_state <= ST_PAUSE;
              end
            end else begin
              r_edge_cnt <= r_edge_cnt + 4'd1;
            end
          end else begin
            r_div_cnt <= r_div_cnt + 1'b1;
          end
        end
        // ---------------------------------------------------------------------
        ST_PAUSE: begin
          // o_cs_n stays 0, SCLK stays at CPOL_b, no time limit
          // REQ: SPI-7.8-03, SPI-7.8-04, SPI-10-08, SPI-14-20, SPI-7.4-03
          if (cmd_hs) begin
            // REQ: SPI-7.8-05, SPI-7.1-02
            r_state    <= ST_XFER;
            r_div_cnt  <= '0;
            r_edge_cnt <= 4'd0;
            r_last     <= i_cmd_last;
          end
        end
        // ---------------------------------------------------------------------
        ST_TRAIL: begin
          // o_cs_n rises D cycles after SCLK edge 16 (edge A + 17*D), whatever
          // the response stream state
          // REQ: SPI-7.2-02, SPI-7.2-03, SPI-7.2-07, SPI-3-06, SPI-8-04, SPI-8-07, SPI-14-01, SPI-7.4-03
          if (div_tick) begin
            r_state   <= ST_IDLE;
            r_cs_n    <= 1'b1;
            r_div_cnt <= '0;   // start of the D-1 blocked Idle cycles
          end else begin
            r_div_cnt <= r_div_cnt + 1'b1;
          end
        end
        // ---------------------------------------------------------------------
        default: begin
          // Safe state: Idle, slave deselected
          r_state    <= ST_IDLE;
          r_cs_n     <= 1'b1;
          r_div_cnt  <= LP_DIV_LAST;
          r_edge_cnt <= 4'd0;
        end
      endcase
    end
  end

  // ---------------------------------------------------------------------------
  // MOSI transmission (MSB first)
  // ---------------------------------------------------------------------------
  // REQ: SPI-1.1-01, SPI-1.2-01, SPI-7.5-01, SPI-7.5-02, SPI-7.5-03, SPI-7.5-04, SPI-7.5-05, SPI-7.5-06, SPI-7.5-07, SPI-7.5-08, SPI-7.5-09, SPI-14-07, SPI-13-05, SPI-5-06, SPI-5-12, SPI-6.2-04, SPI-7.1-03, SPI-7.1-04, SPI-10-04, SPI-7.3-02
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_mosi     <= 1'b0;
      r_tx_shift <= 8'h00;
    end else if (cmd_hs) begin
      if (cpha_load) begin
        // CPHA = 1: o_mosi keeps its value until SCLK edge 1
        r_tx_shift <= i_cmd_data;
      end else begin
        // CPHA = 0: d[7] launched at the acceptance edge
        r_mosi     <= i_cmd_data[7];
        r_tx_shift <= {i_cmd_data[6:0], 1'b0};
      end
    end else if (shift_edge) begin
      r_mosi     <= r_tx_shift[7];
      r_tx_shift <= {r_tx_shift[6:0], 1'b0};
    end
  end

  assign o_mosi = r_mosi;

  // ---------------------------------------------------------------------------
  // MISO reception: i_miso captured directly into a flip-flop, no synchroniser
  // ---------------------------------------------------------------------------
  // REQ: SPI-1.1-01, SPI-6.1-04, SPI-13-11, SPI-7.6-01, SPI-7.6-02, SPI-7.6-03, SPI-7.6-04, SPI-7.6-05, SPI-7.3-02, SPI-10-02, SPI-14-09
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_rx_shift <= 8'h00;
    end else if (sample_edge) begin
      r_rx_shift <= {r_rx_shift[6:0], i_miso};
    end
  end

  // ---------------------------------------------------------------------------
  // Response stream: one shown byte (o_rsp_data) and at most one held byte
  // ---------------------------------------------------------------------------
  // REQ: SPI-1.1-02, SPI-1.2-09, SPI-5-08, SPI-5-09, SPI-5-10, SPI-6.2-05, SPI-6.2-10, SPI-10-10, SPI-10-12, SPI-7.7-01, SPI-7.7-02, SPI-7.7-03, SPI-7.7-04, SPI-7.7-05, SPI-7.7-06, SPI-7.7-07, SPI-7.7-08, SPI-7.7-09, SPI-7.7-10, SPI-7.7-11, SPI-7.7-12, SPI-8-03, SPI-8-14, SPI-8-16, SPI-10-06, SPI-10-13, SPI-14-06, SPI-14-12, SPI-13-10
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_rsp_valid  <= 1'b0;
      r_rsp_data   <= 8'h00;
      r_held_valid <= 1'b0;
      r_held_data  <= 8'h00;
    end else if (xfer_last_cycle) begin
      // SCLK edge 16 (edge A + 16*D). No byte is held here: a transfer only
      // starts while o_rsp_valid = 0, and a held byte implies o_rsp_valid = 1.
      if (!r_rsp_valid || i_rsp_ready) begin
        // Response register free, or the shown byte is taken at this edge
        r_rsp_valid <= 1'b1;
        r_rsp_data  <= rx_byte;
      end else begin
        // Shown byte not taken: this byte becomes the held byte
        r_held_valid <= 1'b1;
        r_held_data  <= rx_byte;
      end
    end else if (rsp_hs) begin
      if (r_held_valid) begin
        // Held byte replaces the taken shown byte, o_rsp_valid stays 1
        r_rsp_data   <= r_held_data;
        r_held_valid <= 1'b0;
      end else begin
        r_rsp_valid  <= 1'b0;
      end
    end
  end

  assign o_rsp_valid = r_rsp_valid;
  assign o_rsp_data  = r_rsp_data;

  // ---------------------------------------------------------------------------
  // Outputs: slave select and SCLK
  // ---------------------------------------------------------------------------
  // REQ: SPI-13-05, SPI-5-13, SPI-6.2-02
  assign o_cs_n = r_cs_n;

  // o_sclk = o_cs_n ? i_cpol : r_sclk, written as a hazard-free mux (the
  // consensus term i_cpol & r_sclk keeps the output stable when both inputs
  // are equal while o_cs_n changes). While o_cs_n = 0 it comes from the
  // r_sclk flip-flop only; the only input path is i_cpol while o_cs_n = 1
  // (Idle and reset).
  // REQ: SPI-5-11, SPI-6.2-03, SPI-7.4-03, SPI-7.4-05, SPI-7.4-06, SPI-10-03, SPI-10-09, SPI-13-06, SPI-13-07, SPI-13-08, SPI-13-09, SPI-14-08, SPI-7.3-02, SPI-7.3-03
  assign o_sclk = (r_cs_n & i_cpol) | (~r_cs_n & r_sclk) | (i_cpol & r_sclk);

endmodule
