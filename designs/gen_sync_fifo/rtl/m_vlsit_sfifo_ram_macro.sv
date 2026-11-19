// ============================================================================
// Module  : m_vlsit_sfifo_ram_macro
// Purpose : SRAM wrapper of the synchronous-clock FIFO storage: one write port
//           (i_clk_wr, active-low write enable) and one read port (i_clk_rd,
//           active-low read enable) with a registered read data output (read
//           latency of one read-clock cycle). 2^PARA_SFIFO_RAM_ADDR_W rows.
//           A word written at the same edge as it is read is not seen: the
//           read register keeps the old word.
// Spec    : SyncFIFO_Design_Specification.md sections 1.2, 10.5 (MEM-002),
//           14.2, 14.2.1 (m_vlsit_sfifo_ram_macro), 20.1 (OI-003)
// Note    : This wrapper belongs to 000_Common/rtl_lib. The library cell
//           VLSIT_CELL_SRAM_1W1R (and its model) is not available in this
//           work folder, so the body is a behavioural stand-in with the same
//           port contract. When the cell is mapped, the body is replaced by
//           one instance of VLSIT_CELL_SRAM_1W1R named u_dont_touch_sram.
// ============================================================================
`default_nettype none

module m_vlsit_sfifo_ram_macro #(
    // PARA_SFIFO_RAM_ADDR_W: address width of the SRAM (rows = 2^ADDR_W)
    // Legal values: 1 or more
    // Default: 3
    parameter logic [31:0] PARA_SFIFO_RAM_ADDR_W = 3,
    // PARA_SFIFO_RAM_DATA_W: word width of the SRAM in bits
    // Legal values: 1 or more
    // Default: 32
    parameter logic [31:0] PARA_SFIFO_RAM_DATA_W = 32
) (
    // Write port (CLK-WR)
    input  wire                              i_clk_wr,
    input  wire                              i_wr_en_n,
    input  wire  [PARA_SFIFO_RAM_ADDR_W-1:0] i_wr_addr,
    input  wire  [PARA_SFIFO_RAM_DATA_W-1:0] i_wr_data,
    // Read port (CLK-RD)
    input  wire                              i_clk_rd,
    input  wire                              i_rd_en_n,
    input  wire  [PARA_SFIFO_RAM_ADDR_W-1:0] i_rd_addr,
    output logic [PARA_SFIFO_RAM_DATA_W-1:0] o_rd_data
);

  // Number of rows of the macro: 2^ADDR_W (rows above DEPTH-1 are unused)
  localparam logic [31:0] LPARA_RAM_ROWS = 32'd1 << PARA_SFIFO_RAM_ADDR_W;

  // Storage rows: resetless payload
  logic [PARA_SFIFO_RAM_DATA_W-1:0] reg_ram_array [0:LPARA_RAM_ROWS-1];
  // Registered read data (macro output register), not reset
  logic [PARA_SFIFO_RAM_DATA_W-1:0] reg_ram_rd_data;

  // REQ: SF-14.2.1-15, SF-1.2-01
  // Write port: the word is stored at the write clock when i_wr_en_n = 0
  always_ff @(posedge i_clk_wr) begin
    if (!i_wr_en_n) begin
      reg_ram_array[i_wr_addr] <= i_wr_data;
    end
  end

  // REQ: SF-14.2.1-17, SF-10.5-02
  // Read port: address sampled every read cycle, data registered (latency 1)
  always_ff @(posedge i_clk_rd) begin
    if (!i_rd_en_n) begin
      reg_ram_rd_data <= reg_ram_array[i_rd_addr];
    end
  end

  assign o_rd_data = reg_ram_rd_data;

endmodule

`default_nettype wire
