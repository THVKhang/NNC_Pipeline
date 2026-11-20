// ============================================================================
// Module  : m_axil_regfile
// Purpose : AXI4-Lite subordinate register file: PARA_NUM_REGS 32-bit
//           read/write control registers (driven on o_regs) and one 32-bit
//           read-only status register at 0x40 that returns i_status.
// Spec    : axil_regfile_Design_Specification.md
//           section 4  (parameters), 5 (interface), 6 (clock and reset),
//           7.1 (decode), 7.2 (AW/W acceptance), 7.3 (register update),
//           7.4 (write response), 7.5 (read), 7.6 (concurrent read/write),
//           8 (timing and back-pressure), 9 (register map),
//           10 (errors, parameter extremes), 13 (implementation).
// Structure:
//   - Write path: AW and W are taken independently (either order or same
//     edge). The decoded address and the data/strobes are held until the B
//     transfer. At Ec (later of the two transfers) the register is written
//     and bvalid rises. awready / wready are registered and are the inverse
//     of the held state of the next cycle.
//   - Read path: at the AR transfer the selected value (register, i_status
//     or 0) and the response are captured in rdata / rresp and rvalid rises.
//     arready is registered and is 0 while the read data is pending.
//   - Every output is a flip-flop output, reset asynchronously by i_rst_n.
// ============================================================================
module m_axil_regfile #(
  parameter int PARA_NUM_REGS = 8,  // number of read/write registers (1 to 16)
  parameter int PARA_ADDR_W   = 8   // AXI address width (7 to 16)
) (
  input  logic                         i_clk,
  input  logic                         i_rst_n,
  // write address channel
  input  logic                         i_s_axi_awvalid,
  output logic                         o_s_axi_awready,
  input  logic [PARA_ADDR_W-1:0]       i_s_axi_awaddr,
  input  logic [2:0]                   i_s_axi_awprot,
  // write data channel
  input  logic                         i_s_axi_wvalid,
  output logic                         o_s_axi_wready,
  input  logic [31:0]                  i_s_axi_wdata,
  input  logic [3:0]                   i_s_axi_wstrb,
  // write response channel
  output logic                         o_s_axi_bvalid,
  input  logic                         i_s_axi_bready,
  output logic [1:0]                   o_s_axi_bresp,
  // read address channel
  input  logic                         i_s_axi_arvalid,
  output logic                         o_s_axi_arready,
  input  logic [PARA_ADDR_W-1:0]       i_s_axi_araddr,
  input  logic [2:0]                   i_s_axi_arprot,
  // read data channel
  output logic                         o_s_axi_rvalid,
  input  logic                         i_s_axi_rready,
  output logic [31:0]                  o_s_axi_rdata,
  output logic [1:0]                   o_s_axi_rresp,
  // SoC side
  output logic [PARA_NUM_REGS*32-1:0]  o_regs,
  input  logic [31:0]                  i_status
);

  // --------------------------------------------------------------------------
  // Local parameters
  // --------------------------------------------------------------------------
  // REQ: RF-4-05
  localparam int LPARA_REGS_W = PARA_NUM_REGS * 32;  // width of o_regs
  localparam int LPARA_WIDX_W = PARA_ADDR_W - 2;     // width of the word index

  // REQ: RF-1.3-01, RF-7.4-08, RF-7.5-14
  // Only OKAY and SLVERR are ever produced.
  localparam logic [1:0] LPARA_RESP_OKAY   = 2'b00;
  localparam logic [1:0] LPARA_RESP_SLVERR = 2'b10;

  // --------------------------------------------------------------------------
  // Parameter range check (elaboration only, simulation/lint tools)
  // --------------------------------------------------------------------------
  // REQ: RF-4-06, RF-14-11
`ifndef SYNTHESIS
  generate
    if ((PARA_NUM_REGS < 1) || (PARA_NUM_REGS > 16)) begin : g_err_num_regs
      $error("m_axil_regfile: PARA_NUM_REGS must be 1 to 16");
    end
    if ((PARA_ADDR_W < 7) || (PARA_ADDR_W > 16)) begin : g_err_addr_w
      $error("m_axil_regfile: PARA_ADDR_W must be 7 to 16");
    end
  endgenerate
`endif

  // --------------------------------------------------------------------------
  // Ignored inputs
  // --------------------------------------------------------------------------
  // REQ: RF-1.3-02, RF-1.3-03, RF-5-06, RF-7.1-01, RF-10.1-05, RF-10.1-07, RF-9-12
  // awprot / arprot and address bits [1:0] have no effect on any output.
  // WAIVER: awprot, arprot and address bits [1:0] are ignored by the specification (sections 1.3, 7.1)
  // verilator lint_off UNUSEDSIGNAL
  logic unused_inputs;
  assign unused_inputs = ^{i_s_axi_awprot, i_s_axi_arprot,
                           i_s_axi_awaddr[1:0], i_s_axi_araddr[1:0]};
  // verilator lint_on UNUSEDSIGNAL

  // --------------------------------------------------------------------------
  // Registers (flip-flops)
  // --------------------------------------------------------------------------
  // write channel handshake state
  logic        r_awready;      // drives o_s_axi_awready
  logic        r_wready;       // drives o_s_axi_wready
  logic        r_aw_held;      // a write address is held
  logic        r_w_held;       // write data is held
  logic        r_bvalid;       // drives o_s_axi_bvalid
  logic [1:0]  r_bresp;        // drives o_s_axi_bresp
  // held write address (decoded at the AW transfer)
  logic        r_aw_reg_hit;   // held address selects a read/write register
  logic        r_aw_okay;      // held address is mapped (register or status)
  logic [3:0]  r_aw_reg_idx;   // register number of the held address
  // held write data
  logic [31:0] r_wdata;
  logic [3:0]  r_wstrb;
  // read channel
  logic        r_arready;      // drives o_s_axi_arready
  logic        r_rvalid;       // drives o_s_axi_rvalid
  logic [31:0] r_rdata;        // drives o_s_axi_rdata
  logic [1:0]  r_rresp;        // drives o_s_axi_rresp

  // --------------------------------------------------------------------------
  // Handshakes
  // --------------------------------------------------------------------------
  logic aw_hs;  // AW transfer at this edge
  logic w_hs;   // W transfer at this edge
  logic b_hs;   // B transfer at this edge
  logic ar_hs;  // AR transfer at this edge
  logic rd_hs;  // R transfer at this edge

  // REQ: RF-3-01, RF-6.2-05, RF-6.2-06, RF-10.1-10
  // A transfer needs valid and ready at 1. All readies and valids of the block
  // are 0 during reset and in the cycle that ends at R1, and the flip-flops
  // are held in reset while i_rst_n is 0, so no transfer happens then.
  assign aw_hs = i_s_axi_awvalid & r_awready;
  assign w_hs  = i_s_axi_wvalid  & r_wready;
  assign b_hs  = r_bvalid        & i_s_axi_bready;
  assign ar_hs = i_s_axi_arvalid & r_arready;
  assign rd_hs = r_rvalid        & i_s_axi_rready;

  // --------------------------------------------------------------------------
  // Address decode
  // --------------------------------------------------------------------------
  logic [LPARA_WIDX_W-1:0] aw_widx;
  logic                    aw_reg_hit;
  logic                    aw_status_hit;
  logic [3:0]              aw_reg_idx;
  logic [LPARA_WIDX_W-1:0] ar_widx;
  logic                    ar_reg_hit;
  logic                    ar_status_hit;
  logic [3:0]              ar_reg_idx;

  // REQ: RF-7.1-01, RF-7.1-05, RF-10.1-06
  // Only the word index (bits [PARA_ADDR_W-1:2]) is decoded.
  assign aw_widx = i_s_axi_awaddr[PARA_ADDR_W-1:2];
  assign ar_widx = i_s_axi_araddr[PARA_ADDR_W-1:2];

  // REQ: RF-7.1-06, RF-10.1-01
  // The write is decoded from the address taken at its AW transfer.
  m_axil_regfile_dec #(
    .PARA_NUM_REGS (PARA_NUM_REGS),
    .PARA_WIDX_W   (LPARA_WIDX_W)
  ) u_aw_dec (
    .i_widx       (aw_widx),
    .o_reg_hit    (aw_reg_hit),
    .o_status_hit (aw_status_hit),
    .o_reg_idx    (aw_reg_idx)
  );

  // REQ: RF-7.1-07, RF-10.1-02
  // The read is decoded from the address taken at its AR transfer.
  m_axil_regfile_dec #(
    .PARA_NUM_REGS (PARA_NUM_REGS),
    .PARA_WIDX_W   (LPARA_WIDX_W)
  ) u_ar_dec (
    .i_widx       (ar_widx),
    .o_reg_hit    (ar_reg_hit),
    .o_status_hit (ar_status_hit),
    .o_reg_idx    (ar_reg_idx)
  );

  // --------------------------------------------------------------------------
  // Write path: acceptance and completion
  // --------------------------------------------------------------------------
  logic        aw_held_d;   // write address held in the next cycle
  logic        w_held_d;    // write data held in the next cycle
  logic        wr_commit;   // this edge is Ec of a write transaction
  logic        wr_reg_hit;  // the completing write selects a read/write register
  logic        wr_okay;     // the completing write is to a mapped address
  logic [3:0]  wr_reg_idx;  // register number of the completing write
  logic [31:0] wr_data;     // write data of the completing write
  logic [3:0]  wr_strb;     // write strobes of the completing write

  // REQ: RF-3-03, RF-7.2-07, RF-7.2-08, RF-8.2-02
  // Address / data are held from their transfer until the B transfer.
  assign aw_held_d = (r_aw_held | aw_hs) & ~b_hs;
  assign w_held_d  = (r_w_held  | w_hs)  & ~b_hs;

  // REQ: RF-1.2-07, RF-7.2-05, RF-7.2-06, RF-14-05
  // Ec: both AW and W have been taken, and at least one of them at this edge.
  assign wr_commit = (aw_hs | r_aw_held) & (w_hs | r_w_held) & (aw_hs | w_hs);

  // REQ: RF-7.1-06, RF-7.2-09
  // Address info from the AW transfer, data and strobes from the W transfer
  // (taken now, or held from an earlier edge).
  assign wr_reg_hit = aw_hs ? aw_reg_hit                     : r_aw_reg_hit;
  assign wr_okay    = aw_hs ? (aw_reg_hit | aw_status_hit)   : r_aw_okay;
  assign wr_reg_idx = aw_hs ? aw_reg_idx                     : r_aw_reg_idx;
  assign wr_data    = w_hs  ? i_s_axi_wdata                  : r_wdata;
  assign wr_strb    = w_hs  ? i_s_axi_wstrb                  : r_wstrb;

  // REQ: RF-7.2-01, RF-7.2-02, RF-7.2-03, RF-7.2-04, RF-6.2-02, RF-6.2-07, RF-6.2-08, RF-6.2-09, RF-6.2-10, RF-6.2-11, RF-14-01, RF-14-02, RF-14-10, RF-14-12, RF-8.1-03, RF-8.1-01
  // Readies are registered and depend only on the held state of the next
  // cycle: 0 during reset and in the cycle that ends at R1, 1 from R1 while
  // nothing is held, 0 while held, 1 again in the cycle that starts at Eb.
  // Reset discards every held state and any pending response.
  // REQ: RF-7.4-01, RF-7.4-02, RF-7.4-03, RF-7.4-04, RF-7.4-05, RF-7.4-06, RF-7.4-07, RF-1.2-09, RF-14-03, RF-8.2-01, RF-1.2-05, RF-9-06, RF-9-08, RF-9-11, RF-10.1-03, RF-10.1-04
  // bvalid is 1 from Ec until Eb; bresp is set at Ec and stable until Eb:
  // OKAY for a register or the status register, SLVERR for unmapped.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_aw_held <= 1'b0;
      r_w_held  <= 1'b0;
      r_awready <= 1'b0;
      r_wready  <= 1'b0;
      r_bvalid  <= 1'b0;
      r_bresp   <= LPARA_RESP_OKAY;
    end else begin
      r_aw_held <= aw_held_d;
      r_w_held  <= w_held_d;
      r_awready <= ~aw_held_d;
      r_wready  <= ~w_held_d;
      if (wr_commit) begin
        r_bvalid <= 1'b1;
        r_bresp  <= wr_okay ? LPARA_RESP_OKAY : LPARA_RESP_SLVERR;
      end else if (b_hs) begin
        r_bvalid <= 1'b0;
      end
    end
  end

  // REQ: RF-7.1-06, RF-7.2-09, RF-13-06
  // Held write address (decoded) and held write data / strobes.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_aw_reg_hit <= 1'b0;
      r_aw_okay    <= 1'b0;
      r_aw_reg_idx <= 4'd0;
      r_wdata      <= 32'd0;
      r_wstrb      <= 4'd0;
    end else begin
      if (aw_hs) begin
        r_aw_reg_hit <= aw_reg_hit;
        r_aw_okay    <= aw_reg_hit | aw_status_hit;
        r_aw_reg_idx <= aw_reg_idx;
      end
      if (w_hs) begin
        r_wdata <= i_s_axi_wdata;
        r_wstrb <= i_s_axi_wstrb;
      end
    end
  end

  // --------------------------------------------------------------------------
  // Read/write registers and read-data selection
  // --------------------------------------------------------------------------
  logic [LPARA_REGS_W-1:0]        regs_flat;  // all register values
  logic [32*(PARA_NUM_REGS+1)-1:0] rd_chain;  // OR chain of the read mux

  assign rd_chain[31:0] = 32'd0;

  genvar k;
  generate
    for (k = 0; k < PARA_NUM_REGS; k = k + 1) begin : g_reg
      logic [31:0] r_reg;   // read/write register k
      logic        wr_en;   // register k is written at this edge
      logic        rd_sel;  // register k is selected by the read address

      // REQ: RF-7.3-04, RF-7.3-05, RF-7.3-06, RF-7.3-07, RF-7.3-09, RF-7.5-16, RF-7.6-02
      // Only Ec of a write that selects register k changes register k.
      assign wr_en  = wr_commit & wr_reg_hit & ({28'd0, wr_reg_idx} == k);
      assign rd_sel = ({28'd0, ar_reg_idx} == k);

      // REQ: RF-1.1-01, RF-1.2-02, RF-1.2-03, RF-5-01, RF-5-02, RF-7.3-01, RF-7.3-02, RF-7.3-03, RF-7.3-08, RF-9-01, RF-9-03, RF-6.2-04, RF-6.2-01, RF-6.1-01
      // Byte lane i is written from wdata lane i when wstrb[i] is 1 at Ec;
      // other lanes keep their value. Reset to 0 asynchronously.
      always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
          r_reg <= 32'd0;
        end else if (wr_en) begin
          if (wr_strb[0]) r_reg[7:0]   <= wr_data[7:0];
          if (wr_strb[1]) r_reg[15:8]  <= wr_data[15:8];
          if (wr_strb[2]) r_reg[23:16] <= wr_data[23:16];
          if (wr_strb[3]) r_reg[31:24] <= wr_data[31:24];
        end
      end

      // REQ: RF-1.1-03, RF-5-03, RF-9-02
      assign regs_flat[32*k +: 32] = r_reg;

      // REQ: RF-7.5-09, RF-9-04
      assign rd_chain[32*(k+1) +: 32] = rd_chain[32*k +: 32] | (rd_sel ? r_reg : 32'd0);
    end
  endgenerate

  // REQ: RF-1.1-03, RF-5-03, RF-13-07, RF-1.2-10
  // o_regs comes directly from the register flip-flops.
  assign o_regs = regs_flat;

  // --------------------------------------------------------------------------
  // Read path
  // --------------------------------------------------------------------------
  logic [31:0] rd_data_d;  // read data captured at the AR transfer
  logic [1:0]  rd_resp_d;  // read response captured at the AR transfer
  logic        rd_valid_d; // rvalid in the next cycle

  // REQ: RF-7.5-09, RF-7.5-10, RF-7.5-12, RF-7.5-13, RF-1.2-06, RF-9-05, RF-9-07, RF-9-10, RF-14-07, RF-7.6-03, RF-7.6-04, RF-7.6-06, RF-10.1-02
  // Register value (as in the cycle that ends at Ear: old value if a write
  // completes at the same edge), i_status for 0x40, 0 with SLVERR otherwise.
  assign rd_data_d = ar_reg_hit    ? rd_chain[32*PARA_NUM_REGS +: 32] :
                     ar_status_hit ? i_status                         :
                                     32'd0;
  assign rd_resp_d = (ar_reg_hit | ar_status_hit) ? LPARA_RESP_OKAY : LPARA_RESP_SLVERR;

  // REQ: RF-7.5-04, RF-7.5-06, RF-7.5-07, RF-7.5-08, RF-14-04
  assign rd_valid_d = ar_hs | (r_rvalid & ~rd_hs);

  // REQ: RF-7.5-01, RF-7.5-02, RF-7.5-03, RF-7.5-05, RF-7.5-11, RF-7.6-01, RF-7.6-05, RF-8.1-02, RF-8.2-03, RF-8.2-04, RF-8.2-05, RF-8.2-06, RF-8.2-07, RF-1.2-08, RF-10.1-08, RF-10.1-09, RF-6.2-02, RF-6.2-03, RF-14-09, RF-13-06
  // The read path only depends on the AR/R channels (and the register
  // values). rdata/rresp are captured at Ear and held until Er, so later
  // writes or i_status changes do not affect them. arready is 0 while the
  // read data is pending and 1 again in the cycle that starts at Er.
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
      r_arready <= 1'b0;
      r_rvalid  <= 1'b0;
      r_rdata   <= 32'd0;
      r_rresp   <= LPARA_RESP_OKAY;
    end else begin
      r_arready <= ~rd_valid_d;
      r_rvalid  <= rd_valid_d;
      if (ar_hs) begin
        r_rdata <= rd_data_d;
        r_rresp <= rd_resp_d;
      end
    end
  end

  // --------------------------------------------------------------------------
  // Outputs: every output is a flip-flop output
  // --------------------------------------------------------------------------
  // REQ: RF-5-04, RF-13-07, RF-1.2-10, RF-1.2-11
  assign o_s_axi_awready = r_awready;
  assign o_s_axi_wready  = r_wready;
  assign o_s_axi_bvalid  = r_bvalid;
  assign o_s_axi_bresp   = r_bresp;
  assign o_s_axi_arready = r_arready;
  assign o_s_axi_rvalid  = r_rvalid;
  assign o_s_axi_rdata   = r_rdata;
  assign o_s_axi_rresp   = r_rresp;

endmodule
