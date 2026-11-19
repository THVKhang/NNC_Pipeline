// ============================================================================
// Module  : m_vlsit_sfifo_mem
// Purpose : Storage of the synchronous-clock FIFO: PARA_SFIFO_DEPTH words of
//           PARA_SFIFO_DATA_W bits with one write port (CLK-WR) and one read
//           port (CLK-RD) with a read data register (latency one read-clock
//           cycle). Branch selected at elaboration by PARA_SFIFO_MEM_USE_MACRO:
//           0 = pure RTL array, 1 = SRAM wrapper m_vlsit_sfifo_ram_macro.
//           The memory content is not reset (resetless payload).
// Spec    : SyncFIFO_Design_Specification.md sections 5.1, 10.5, 14.2,
//           14.2.1 (m_vlsit_sfifo_mem), 8 (PARA_SFIFO_MEM_USE_MACRO)
// ============================================================================
`default_nettype none

module m_vlsit_sfifo_mem #(
    // PARA_SFIFO_DEPTH: number of FIFO entries
    // Legal values: any integer of 2 or more, no upper limit
    // Default: 8
    parameter logic [31:0] PARA_SFIFO_DEPTH         = 8,
    // PARA_SFIFO_DATA_W: data word width in bits
    // Legal values: 1 or more, no upper limit
    // Default: 32
    parameter logic [31:0] PARA_SFIFO_DATA_W        = 32,
    // PARA_SFIFO_MEM_USE_MACRO: storage branch, 0 = RTL array, 1 = SRAM wrapper
    // Legal values: 0 or 1
    // Default: 0
    parameter logic [31:0] PARA_SFIFO_MEM_USE_MACRO = 0,
    // Derived: memory address width
    localparam logic [31:0] LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH)
) (
    // Write port (CLK-WR)
    input  wire                          i_clk_wr,
    input  wire                          i_wr_en,
    input  wire  [LPARA_ADDR_W-1:0]      i_wr_addr,
    input  wire  [PARA_SFIFO_DATA_W-1:0] i_wr_data,
    // Read port (CLK-RD)
    input  wire                          i_clk_rd,
    input  wire  [LPARA_ADDR_W-1:0]      i_rd_addr,
    output logic [PARA_SFIFO_DATA_W-1:0] o_rd_data
);

  // REQ: SF-4-06, SF-8-07, SF-14.2-02
  // Storage branch selected at elaboration (present or absent)
  generate
    if (PARA_SFIFO_MEM_USE_MACRO == 32'd0) begin : g_mem_array
      // REQ: SF-3-12, SF-1.1-11, SF-14.1-03
      // Flop array of DEPTH words, resetless payload
      logic [PARA_SFIFO_DATA_W-1:0] reg_mem_array [0:PARA_SFIFO_DEPTH-1];
      // Memory output register (drives o_rd_data of the top), not reset
      logic [PARA_SFIFO_DATA_W-1:0] reg_mem_rd_data;

      // REQ: SF-14.2.1-11, SF-3-01, SF-3-43
      // Write port: store the word at the write address when enabled
      always_ff @(posedge i_clk_wr) begin
        if (i_wr_en) begin
          reg_mem_array[i_wr_addr] <= i_wr_data;
        end
      end

      // REQ: SF-14.2.1-12, SF-14.2.1-13, SF-10.5-01, SF-10.5-02, SF-3-22
      // Read port: read every read-clock cycle, registered output; a word
      // written at the same edge is not seen (old word kept)
      always_ff @(posedge i_clk_rd) begin
        reg_mem_rd_data <= reg_mem_array[i_rd_addr];
      end

      assign o_rd_data = reg_mem_rd_data;
    end else begin : g_mem_macro
      // REQ: SF-1.2-01, SF-3-56, SF-14.2-02, SF-14.2.1-16, SF-8-08
      // SRAM wrapper: active-low write enable, read enable tied to 0
      m_vlsit_sfifo_ram_macro #(
          .PARA_SFIFO_RAM_ADDR_W (LPARA_ADDR_W),
          .PARA_SFIFO_RAM_DATA_W (PARA_SFIFO_DATA_W)
      ) u_ram_macro (
          .i_clk_wr  (i_clk_wr),
          .i_wr_en_n (~i_wr_en),
          .i_wr_addr (i_wr_addr),
          .i_wr_data (i_wr_data),
          .i_clk_rd  (i_clk_rd),
          .i_rd_en_n (1'b0),
          .i_rd_addr (i_rd_addr),
          .o_rd_data (o_rd_data)
      );
    end
  endgenerate

endmodule

`default_nettype wire
