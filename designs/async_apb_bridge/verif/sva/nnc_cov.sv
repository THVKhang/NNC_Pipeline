module nnc_cov #(
  parameter int PARA_APBCDC_ADDR_W = 32,
  parameter int PARA_APBCDC_DATA_W = 32,
  parameter int PARA_APBCDC_APB5 = 0,
  parameter int PARA_APBCDC_USER_REQ_W = 0,
  parameter int PARA_APBCDC_USER_DATA_W = 0,
  parameter int PARA_APBCDC_USER_RESP_W = 0,
  parameter int PARA_APBCDC_HS_TYPE = 0,
  parameter int PARA_APBCDC_CELL_TYPE = 2,
  localparam int LPARA_STRB_W = PARA_APBCDC_DATA_W / 8
) (
  input  logic                        i_clk_mst,
  input  logic                        i_rst_n_mst,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_APBCDC_ADDR_W)-1:0] i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [(LPARA_STRB_W)-1:0]   i_apb_pstrb,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_pwdata,
  input  logic                        i_apb_pwakeup,
  input  logic [(PARA_APBCDC_USER_REQ_W)-1:0] i_apb_pauser,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pwuser,
  input  logic                        o_apb_pready,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pruser,
  input  logic [(PARA_APBCDC_USER_RESP_W)-1:0] o_apb_pbuser,
  input  logic                        i_clk_slv,
  input  logic                        i_rst_n_slv,
  input  logic                        o_apb_psel,
  input  logic                        o_apb_penable,
  input  logic                        o_apb_pwrite,
  input  logic [(PARA_APBCDC_ADDR_W)-1:0] o_apb_paddr,
  input  logic [2:0]                  o_apb_pprot,
  input  logic [(LPARA_STRB_W)-1:0]   o_apb_pstrb,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] o_apb_pwdata,
  input  logic                        o_apb_pwakeup,
  input  logic [(PARA_APBCDC_USER_REQ_W)-1:0] o_apb_pauser,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] o_apb_pwuser,
  input  logic                        i_apb_pready,
  input  logic [(PARA_APBCDC_DATA_W)-1:0] i_apb_prdata,
  input  logic                        i_apb_pslverr,
  input  logic [(PARA_APBCDC_USER_DATA_W)-1:0] i_apb_pruser,
  input  logic [(PARA_APBCDC_USER_RESP_W)-1:0] i_apb_pbuser
);

  int unsigned hits_COVP_001 = 0;
  int unsigned hits_COVP_002 = 0;
  int unsigned hits_COVP_003 = 0;
  int unsigned hits_COVP_004 = 0;
  int unsigned hits_COVP_005 = 0;
  int unsigned hits_COVP_006 = 0;
  int unsigned hits_COVP_007 = 0;
  int unsigned hits_COVP_008 = 0;
  int unsigned hits_COVP_009 = 0;
  int unsigned hits_COVP_010 = 0;
  int unsigned hits_COVP_011 = 0;
  int unsigned hits_COVP_012 = 0;
  int unsigned hits_COVP_013 = 0;
  int unsigned hits_COVP_014 = 0;
  int unsigned hits_COVP_015 = 0;
  int unsigned hits_COVP_016 = 0;
  int unsigned hits_COVP_017 = 0;
  int unsigned hits_COVP_018 = 0;
  int unsigned hits_COVP_019 = 0;
  int unsigned hits_COVP_020 = 0;
  int unsigned hits_COVP_021 = 0;
  int unsigned hits_COVP_022 = 0;
  int unsigned hits_COVP_023 = 0;
  int unsigned hits_COVP_024 = 0;
  int unsigned hits_COVP_025 = 0;
  int unsigned hits_COVP_026 = 0;
  int unsigned hits_COVP_027 = 0;
  int unsigned hits_COVP_028 = 0;
  int unsigned hits_COVP_029 = 0;
  int unsigned hits_COVP_030 = 0;
  int unsigned hits_COVP_031 = 0;
  int unsigned hits_COVP_032 = 0;
  int unsigned hits_COVP_033 = 0;
  int unsigned hits_COVP_034 = 0;
  int unsigned hits_COVP_035 = 0;
  int unsigned hits_COVP_036 = 0;
  int unsigned hits_COVP_037 = 0;
  int unsigned hits_COVP_038 = 0;
  int unsigned hits_COVP_039 = 0;
  int unsigned hits_COVP_040 = 0;

  // helper state, mst domain
  logic m_busy = 1'b0;
  logic m_wr = 1'b0;
  logic m_prev_pready = 1'b0;
  logic m_prev_err = 1'b0;
  logic m_prev_psel = 1'b0;
  logic m_prev_wk = 1'b0;
  logic m_rst_lost = 1'b0;
  logic m_after_rst = 1'b1;
  int unsigned m_wait = 0;
  int unsigned m_idle = 0;
  logic [PARA_APBCDC_ADDR_W-1:0] m_prev_addr = '0;
  logic [PARA_APBCDC_DATA_W-1:0] m_prev_wdata = '0;

  always_ff @(posedge i_clk_mst) begin
    if (!i_rst_n_mst) begin
      if (m_busy) m_rst_lost <= 1'b1;
      m_busy <= 1'b0;
      m_wr <= 1'b0;
      m_prev_pready <= 1'b0;
      m_prev_err <= 1'b0;
      m_prev_psel <= 1'b0;
      m_prev_wk <= 1'b0;
      m_after_rst <= 1'b1;
      m_wait <= 0;
      m_idle <= 0;
      m_prev_addr <= '0;
      m_prev_wdata <= '0;
    end else begin
      m_rst_lost <= 1'b0;
      m_prev_pready <= o_apb_pready;
      m_prev_psel <= i_apb_psel;
      m_prev_wk <= i_apb_pwakeup;
      m_prev_addr <= i_apb_paddr;
      m_prev_wdata <= i_apb_pwdata;
      if (i_apb_psel && !i_apb_penable) begin
        m_busy <= 1'b1;
        m_wr <= i_apb_pwrite;
        m_after_rst <= 1'b0;
      end else if (o_apb_pready) begin
        m_busy <= 1'b0;
        m_prev_err <= o_apb_pslverr;
      end
      if (o_apb_pready) m_wait <= 0;
      else if (i_apb_psel && i_apb_penable && (m_wait < 1000)) m_wait <= m_wait + 1;
      if (!i_apb_psel && !m_busy) begin
        if (m_idle < 1000) m_idle <= m_idle + 1;
      end else m_idle <= 0;
    end
  end

  // helper state, slv domain
  int unsigned s_wait = 0;
  logic s_rst_lost = 1'b0;

  always_ff @(posedge i_clk_slv) begin
    if (!i_rst_n_slv) begin
      if (o_apb_psel) s_rst_lost <= 1'b1;
      s_wait <= 0;
    end else begin
      s_rst_lost <= 1'b0;
      if (o_apb_psel && o_apb_penable) begin
        if (i_apb_pready) s_wait <= 0;
        else if (s_wait < 1000) s_wait <= s_wait + 1;
      end
    end
  end

  // COVP-001: write transfer completed without error
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && m_wr && !o_apb_pslverr)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: read transfer completed without error
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && !m_wr && !o_apb_pslverr)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: write transfer completed with error
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && m_wr && o_apb_pslverr)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: read transfer completed with error
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && !m_wr && o_apb_pslverr)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: back-to-back Setup in the cycle after PREADY
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (m_prev_pready && i_apb_psel && !i_apb_penable)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: back-to-back Setup with different operation type
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (m_prev_pready && i_apb_psel && !i_apb_penable && (i_apb_pwrite != m_wr))) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Setup after an idle gap of at least 4 cycles
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && !m_busy && m_idle >= 4)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: first Setup after reset release
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (m_after_rst && i_apb_psel && !i_apb_penable)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: requester Access with at least 8 wait cycles
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && m_wait >= 8)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: requester Access with at least 32 wait cycles
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && m_wait >= 32)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: write Setup with all strobes set
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && i_apb_pwrite && (&i_apb_pstrb))) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: write Setup with partial strobes
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && i_apb_pwrite && (|i_apb_pstrb) && !(&i_apb_pstrb))) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: write Setup with all strobes zero
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && i_apb_pwrite && !(|i_apb_pstrb))) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: read Setup with nonzero PSTRB forwarded
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && !i_apb_pwrite && (|i_apb_pstrb))) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: Setup with PPROT 0
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && (i_apb_pprot == 3'd0))) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Setup with PPROT 7
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && (i_apb_pprot == 3'd7))) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Setup with mixed PPROT
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && (i_apb_pprot != 3'd0) && (i_apb_pprot != 3'd7))) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Setup with address zero
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && !(|i_apb_paddr))) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Setup with address all ones
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && (&i_apb_paddr))) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: Setup with non word-aligned address
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && ((32'(i_apb_paddr) & 32'd3) != 32'd0))) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: write Setup with all-ones write data
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && !i_apb_penable && i_apb_pwrite && (&i_apb_pwdata))) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: read completed with all-ones read data
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && !m_wr && (&o_apb_prdata))) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: read with error and nonzero data forwarded
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && !m_wr && o_apb_pslverr && (|o_apb_prdata))) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: successful transfer right after an errored transfer
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (o_apb_pready && !o_apb_pslverr && m_prev_err)) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: requester changes fields during Access
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (i_apb_psel && i_apb_penable && !o_apb_pready && m_busy && ((i_apb_paddr != m_prev_addr) || (i_apb_pwdata != m_prev_wdata)))) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: mst restart after reset during a transfer
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (m_rst_lost)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: mst domain running while slv reset still held low
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && (!i_rst_n_slv)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: APB5 Setup with wake-up raised before PSEL
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && i_apb_psel && !i_apb_penable && !m_prev_psel && i_apb_pwakeup && m_prev_wk)) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: APB5 Setup with wake-up low
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && i_apb_psel && !i_apb_penable && !i_apb_pwakeup)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: APB5 Setup with nonzero PAUSER
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && i_apb_psel && !i_apb_penable && (|i_apb_pauser))) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: APB5 write Setup with nonzero PWUSER
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && i_apb_psel && !i_apb_penable && i_apb_pwrite && (|i_apb_pwuser))) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: APB5 read completed with nonzero PRUSER
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && o_apb_pready && !m_wr && (|o_apb_pruser))) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: APB5 completion with nonzero PBUSER
  always_ff @(posedge i_clk_mst) if (!(!i_rst_n_mst) && ((PARA_APBCDC_APB5 != 0) && o_apb_pready && (|o_apb_pbuser))) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: completer-side write Setup
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && !o_apb_penable && o_apb_pwrite)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: completer-side read Setup
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && !o_apb_penable && !o_apb_pwrite)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: completer transfer with zero wait states
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && o_apb_penable && i_apb_pready && s_wait == 0)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: completer back-pressure of at least 4 wait cycles
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && o_apb_penable && !i_apb_pready && s_wait >= 3)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: completer transfer completed after at least 16 wait cycles
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && o_apb_penable && i_apb_pready && s_wait >= 16)) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: completer-side completion with PSLVERR
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (o_apb_psel && o_apb_penable && i_apb_pready && i_apb_pslverr)) hits_COVP_039 <= hits_COVP_039 + 1;
  // COVP-040: slv restart after reset during a transfer
  always_ff @(posedge i_clk_slv) if (!(!i_rst_n_slv) && (s_rst_lost)) hits_COVP_040 <= hits_COVP_040 + 1;

  final begin
    $display("NNC_COVER COVP-001 hits=%0d", hits_COVP_001);
    $display("NNC_COVER COVP-002 hits=%0d", hits_COVP_002);
    $display("NNC_COVER COVP-003 hits=%0d", hits_COVP_003);
    $display("NNC_COVER COVP-004 hits=%0d", hits_COVP_004);
    $display("NNC_COVER COVP-005 hits=%0d", hits_COVP_005);
    $display("NNC_COVER COVP-006 hits=%0d", hits_COVP_006);
    $display("NNC_COVER COVP-007 hits=%0d", hits_COVP_007);
    $display("NNC_COVER COVP-008 hits=%0d", hits_COVP_008);
    $display("NNC_COVER COVP-009 hits=%0d", hits_COVP_009);
    $display("NNC_COVER COVP-010 hits=%0d", hits_COVP_010);
    $display("NNC_COVER COVP-011 hits=%0d", hits_COVP_011);
    $display("NNC_COVER COVP-012 hits=%0d", hits_COVP_012);
    $display("NNC_COVER COVP-013 hits=%0d", hits_COVP_013);
    $display("NNC_COVER COVP-014 hits=%0d", hits_COVP_014);
    $display("NNC_COVER COVP-015 hits=%0d", hits_COVP_015);
    $display("NNC_COVER COVP-016 hits=%0d", hits_COVP_016);
    $display("NNC_COVER COVP-017 hits=%0d", hits_COVP_017);
    $display("NNC_COVER COVP-018 hits=%0d", hits_COVP_018);
    $display("NNC_COVER COVP-019 hits=%0d", hits_COVP_019);
    $display("NNC_COVER COVP-020 hits=%0d", hits_COVP_020);
    $display("NNC_COVER COVP-021 hits=%0d", hits_COVP_021);
    $display("NNC_COVER COVP-022 hits=%0d", hits_COVP_022);
    $display("NNC_COVER COVP-023 hits=%0d", hits_COVP_023);
    $display("NNC_COVER COVP-024 hits=%0d", hits_COVP_024);
    $display("NNC_COVER COVP-025 hits=%0d", hits_COVP_025);
    $display("NNC_COVER COVP-026 hits=%0d", hits_COVP_026);
    $display("NNC_COVER COVP-027 hits=%0d", hits_COVP_027);
    $display("NNC_COVER COVP-028 hits=%0d", hits_COVP_028);
    $display("NNC_COVER COVP-029 hits=%0d", hits_COVP_029);
    $display("NNC_COVER COVP-030 hits=%0d", hits_COVP_030);
    $display("NNC_COVER COVP-031 hits=%0d", hits_COVP_031);
    $display("NNC_COVER COVP-032 hits=%0d", hits_COVP_032);
    $display("NNC_COVER COVP-033 hits=%0d", hits_COVP_033);
    $display("NNC_COVER COVP-034 hits=%0d", hits_COVP_034);
    $display("NNC_COVER COVP-035 hits=%0d", hits_COVP_035);
    $display("NNC_COVER COVP-036 hits=%0d", hits_COVP_036);
    $display("NNC_COVER COVP-037 hits=%0d", hits_COVP_037);
    $display("NNC_COVER COVP-038 hits=%0d", hits_COVP_038);
    $display("NNC_COVER COVP-039 hits=%0d", hits_COVP_039);
    $display("NNC_COVER COVP-040 hits=%0d", hits_COVP_040);
  end
endmodule
