// ============================================================================
// Module  : m_vlsit_sfifo_top
// Purpose : Structural top of the synchronous-clock FIFO: ports, parameters,
//           interconnect and the three instances u_wr (write side, CLK-WR),
//           u_rd (read side, CLK-RD) and u_mem (storage). The two clocks are
//           synchronous (one source, fixed phase); the pointers and the
//           software reset handshake cross as timed paths, no synchronizer.
// Spec    : SyncFIFO_Design_Specification.md sections 1.1, 4, 5.1, 5.2, 6.2,
//           7.1, 7.2, 8, 14.2
// ============================================================================
`default_nettype none

module m_vlsit_sfifo_top #(
    // PARA_SFIFO_DEPTH: number of FIFO entries (not only a power of two)
    // Legal values: any integer of 2 or more, no upper limit
    // Default: 8
    parameter logic [31:0] PARA_SFIFO_DEPTH         = 8,
    // PARA_SFIFO_DATA_W: data word width in bits
    // Legal values: 1 or more, no upper limit
    // Default: 32
    parameter logic [31:0] PARA_SFIFO_DATA_W        = 32,
    // PARA_SFIFO_PTR_RETIME: pointer path, 0 = direct, 1 = one retiming flop
    // Legal values: 0 or 1
    // Default: 0
    parameter logic [31:0] PARA_SFIFO_PTR_RETIME    = 0,
    // PARA_SFIFO_MEM_USE_MACRO: storage, 0 = RTL array, 1 = SRAM wrapper
    // Legal values: 0 or 1
    // Default: 0
    parameter logic [31:0] PARA_SFIFO_MEM_USE_MACRO = 0,
    // REQ: SF-8-09, SF-8-10, SF-8-11
    // Derived: memory address width, pointer width, occupancy width
    localparam logic [31:0] LPARA_ADDR_W = $clog2(PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_PTR_W  = $clog2(2 * PARA_SFIFO_DEPTH),
    localparam logic [31:0] LPARA_OCC_W  = $clog2(PARA_SFIFO_DEPTH + 1)
) (
    // REQ: SF-3-20, SF-4-07, SF-6.2-01, SF-6.1-01, SF-6.1-02, SF-6.1-03
    // REQ: SF-6.1-04
    // Write domain (CLK-WR)
    input  wire                          i_clk_wr,
    input  wire                          i_rst_n_wr,
    input  wire                          i_wr_en,
    input  wire  [PARA_SFIFO_DATA_W-1:0] i_wr_data,
    input  wire  [LPARA_OCC_W-1:0]       i_full_thr,
    input  wire                          i_rst_n_sw,
    output logic                         o_sw_rst_busy,
    output logic                         o_full,
    output logic                         o_full_thr,
    output logic                         o_overflow,
    // Read domain (CLK-RD)
    input  wire                          i_clk_rd,
    input  wire                          i_rst_n_rd,
    input  wire                          i_rd_en,
    input  wire  [LPARA_OCC_W-1:0]       i_empty_thr,
    output logic [PARA_SFIFO_DATA_W-1:0] o_rd_data,
    output logic                         o_empty,
    output logic                         o_empty_thr,
    output logic                         o_underflow
);

  // --------------------------------------------------------------------------
  // Interconnect
  // --------------------------------------------------------------------------
  logic [LPARA_PTR_W-1:0]       w_wr_ptr;
  logic [LPARA_PTR_W-1:0]       w_rd_ptr;
  logic                         w_req_wr;
  logic                         w_ack_rd;
  logic                         w_mem_wr_en;
  logic [LPARA_ADDR_W-1:0]      w_mem_wr_addr;
  logic [PARA_SFIFO_DATA_W-1:0] w_mem_wr_data;
  logic [LPARA_ADDR_W-1:0]      w_mem_rd_addr;
  logic [PARA_SFIFO_DATA_W-1:0] w_mem_rd_data;

  // --------------------------------------------------------------------------
  // Write side (CLK-WR)
  // --------------------------------------------------------------------------
  // REQ: SF-14.2-01, SF-14.2-03, SF-3-55, SF-1.1-01, SF-1.1-06, SF-1.3-01
  m_vlsit_sfifo_wr #(
      .PARA_SFIFO_DEPTH      (PARA_SFIFO_DEPTH),
      .PARA_SFIFO_DATA_W     (PARA_SFIFO_DATA_W),
      .PARA_SFIFO_PTR_RETIME (PARA_SFIFO_PTR_RETIME)
  ) u_wr (
      .i_clk_wr      (i_clk_wr),
      .i_rst_n_wr    (i_rst_n_wr),
      .i_wr_en       (i_wr_en),
      .i_wr_data     (i_wr_data),
      .i_full_thr    (i_full_thr),
      .o_full        (o_full),
      .o_full_thr    (o_full_thr),
      .o_overflow    (o_overflow),
      .i_rst_n_sw    (i_rst_n_sw),
      .o_sw_rst_busy (o_sw_rst_busy),
      .i_rd_ptr      (w_rd_ptr),
      .o_wr_ptr      (w_wr_ptr),
      .o_req_wr      (w_req_wr),
      .i_ack_rd      (w_ack_rd),
      .o_mem_wr_en   (w_mem_wr_en),
      .o_mem_wr_addr (w_mem_wr_addr),
      .o_mem_wr_data (w_mem_wr_data)
  );

  // --------------------------------------------------------------------------
  // Read side (CLK-RD)
  // --------------------------------------------------------------------------
  // REQ: SF-14.2-01, SF-14.2-03, SF-1.1-02, SF-1.3-05
  m_vlsit_sfifo_rd #(
      .PARA_SFIFO_DEPTH      (PARA_SFIFO_DEPTH),
      .PARA_SFIFO_DATA_W     (PARA_SFIFO_DATA_W),
      .PARA_SFIFO_PTR_RETIME (PARA_SFIFO_PTR_RETIME)
  ) u_rd (
      .i_clk_rd      (i_clk_rd),
      .i_rst_n_rd    (i_rst_n_rd),
      .i_rd_en       (i_rd_en),
      .i_empty_thr   (i_empty_thr),
      .o_rd_data     (o_rd_data),
      .o_empty       (o_empty),
      .o_empty_thr   (o_empty_thr),
      .o_underflow   (o_underflow),
      .i_wr_ptr      (w_wr_ptr),
      .o_rd_ptr      (w_rd_ptr),
      .i_req_wr      (w_req_wr),
      .o_ack_rd      (w_ack_rd),
      .o_mem_rd_addr (w_mem_rd_addr),
      .i_mem_rd_data (w_mem_rd_data)
  );

  // --------------------------------------------------------------------------
  // Storage (write port CLK-WR, read port CLK-RD)
  // --------------------------------------------------------------------------
  // REQ: SF-14.2-01, SF-3-04, SF-1.2-01
  m_vlsit_sfifo_mem #(
      .PARA_SFIFO_DEPTH         (PARA_SFIFO_DEPTH),
      .PARA_SFIFO_DATA_W        (PARA_SFIFO_DATA_W),
      .PARA_SFIFO_MEM_USE_MACRO (PARA_SFIFO_MEM_USE_MACRO)
  ) u_mem (
      .i_clk_wr  (i_clk_wr),
      .i_wr_en   (w_mem_wr_en),
      .i_wr_addr (w_mem_wr_addr),
      .i_wr_data (w_mem_wr_data),
      .i_clk_rd  (i_clk_rd),
      .i_rd_addr (w_mem_rd_addr),
      .o_rd_data (w_mem_rd_data)
  );

endmodule

`default_nettype wire
