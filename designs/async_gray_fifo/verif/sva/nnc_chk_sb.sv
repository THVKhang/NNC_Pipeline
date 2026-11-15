module nnc_chk_sb #(
  parameter int PARA_AFIFO_DEPTH = 8,
  parameter int PARA_AFIFO_DATA_W = 32,
  parameter int PARA_AFIFO_CELL_TYPE = 2,
  parameter int PARA_AFIFO_MEM_USE_MACRO = 0,
  localparam int LPARA_ADDR_W = $clog2(PARA_AFIFO_DEPTH),
  localparam int LPARA_PTR_W = LPARA_ADDR_W + 1
) (
  input  logic                        i_clk_wr,
  input  logic                        i_rst_n_wr,
  input  logic                        i_wr_en,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] i_wr_data,
  input  logic [(LPARA_PTR_W)-1:0]    i_full_thr,
  input  logic                        i_rst_n_sw,
  input  logic                        o_sw_rst_busy,
  input  logic                        o_full,
  input  logic                        o_full_thr,
  input  logic                        o_overflow,
  input  logic                        i_clk_rd,
  input  logic                        i_rst_n_rd,
  input  logic                        i_rd_en,
  input  logic [(LPARA_PTR_W)-1:0]    i_empty_thr,
  input  logic [(PARA_AFIFO_DATA_W)-1:0] o_rd_data,
  input  logic                        o_empty,
  input  logic                        o_empty_thr,
  input  logic                        o_underflow
);

  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;
  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;

  // ---- reference model shared by CHK-005 / CHK-006 (Q = written words, P = pre-reset words) ----
  localparam int LP_SYNC_S   = (PARA_AFIFO_CELL_TYPE >= 3) ? PARA_AFIFO_CELL_TYPE : 2;
  localparam int LP_CLR_EDGE = LP_SYNC_S + 3;

  logic [PARA_AFIFO_DATA_W-1:0] ref_q [$];
  logic [PARA_AFIFO_DATA_W-1:0] ref_p [$];
  logic        m_wr_clk_q = 1'b0;
  logic        m_rd_clk_q = 1'b0;
  logic        m_busy_q   = 1'b0;
  logic        m_pend     = 1'b0;
  int unsigned m_rd_cnt   = 0;
  logic        m_wr_edge;
  logic        m_rd_edge;
  logic        m_busy_rise;

  // helper registers visible to the assertions (updated with non-blocking assignments)
  logic                          chk_act  = 1'b0;
  // NNC hand fix (G3, triage B): after a reset of one domain only, the model is not re-armed until a reset that
  // covers both domains (contract CHK-023: the handshake after a one-domain reset is not checked)
  logic        m_rw_q   = 1'b1;
  logic        m_rr_q   = 1'b1;
  logic        m_one_dom = 1'b0;
  int unsigned                   q_n      = 0;
  int unsigned                   p_n      = 0;
  logic [PARA_AFIFO_DATA_W-1:0]  head_val = '0;

  // NNC hand fix (G3, triage B): wake on both clock edges so m_*_clk_q follows each clock (posedge only missed edges)
  always @(posedge i_clk_wr or negedge i_clk_wr or posedge i_clk_rd or negedge i_clk_rd or
           negedge i_rst_n_wr or negedge i_rst_n_rd) begin
    m_wr_edge = i_clk_wr && !m_wr_clk_q;
    m_rd_edge = i_clk_rd && !m_rd_clk_q;
    m_wr_clk_q = i_clk_wr;
    m_rd_clk_q = i_clk_rd;
    m_busy_rise = 1'b0;
    if (!i_rst_n_wr && !i_rst_n_rd) m_one_dom = 1'b0;
    else if ((!i_rst_n_wr && m_rw_q && i_rst_n_rd) || (!i_rst_n_rd && m_rr_q && i_rst_n_wr)) m_one_dom = 1'b1;
    m_rw_q = i_rst_n_wr;
    m_rr_q = i_rst_n_rd;
    if (m_wr_edge) begin
      m_busy_rise = (o_sw_rst_busy === 1'b1) && !m_busy_q;
      m_busy_q = (o_sw_rst_busy === 1'b1);
    end
    if (!i_rst_n_wr || !i_rst_n_rd) begin
      ref_q.delete();
      ref_p.delete();
      m_pend = 1'b0;
      m_rd_cnt = 0;
      chk_act <= 1'b0;
    end else begin
      // read side first: a write at the same instant is not visible to the read
      if (m_rd_edge) begin
        if (!o_empty && i_rd_en) begin
          if (ref_p.size() > 0) void'(ref_p.pop_front());
          else if (ref_q.size() > 0) void'(ref_q.pop_front());
        end
        if (m_pend) begin
          m_rd_cnt = m_rd_cnt + 1;
          if (m_rd_cnt >= LP_CLR_EDGE) begin
            ref_p.delete();
            m_pend = 1'b0;
          end
        end
      end
      if (m_wr_edge) begin
        if (i_wr_en && !o_full) ref_q.push_back(i_wr_data);
        if (m_busy_rise) begin
          while (ref_q.size() > 0) ref_p.push_back(ref_q.pop_front());
          m_pend = 1'b1;
          m_rd_cnt = 0;
        end
      end
      chk_act <= !m_one_dom;
    end
    q_n <= ref_q.size();
    p_n <= ref_p.size();
    head_val <= (ref_p.size() > 0) ? ref_p[0] : ((ref_q.size() > 0) ? ref_q[0] : '0);
  end

  // CHK-005: Scoreboard: show-ahead data, write order, exactly-once, software-reset discard (AF-1.1-01, AF-1.1-02, AF-3-04, AF-3-05, AF-3-06, AF-3-26, AF-3-32, AF-3-57, AF-5.3-04, AF-6.2-19, AF-15.3-05, AF-10.6.3-03, AF-10.7.5-04)
  a_CHK_005: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
      (chk_act && i_rst_n_wr && (o_empty === 1'b0)) |->
      (((p_n > 0) || (q_n > 0)) && !$isunknown(o_rd_data) && (o_rd_data == head_val)))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (chk_act && i_rst_n_wr && (o_empty === 1'b0))) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: Flags are never optimistic; occupancy within 0..DEPTH (AF-3-10, AF-3-12, AF-5.1-01, AF-5.4-01, AF-5.4-04, AF-10.3-03, AF-10.6.2-10, AF-15.3-06) - (a) write side: no overfill, full when N == DEPTH
  a_CHK_006: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr)
      (chk_act && i_rst_n_rd) |->
      ((q_n <= PARA_AFIFO_DEPTH) && ((q_n != PARA_AFIFO_DEPTH) || (o_full === 1'b1))))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (chk_act && i_rst_n_rd)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-006: (b) read side: nothing written and no pre-reset word means o_empty = 1 (AF-3-12, AF-5.4-04, AF-10.6.2-10, AF-15.3-06, AF-10.5-04)
  a_CHK_006_rd: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd)
      (chk_act && i_rst_n_wr && (q_n == 0) && (p_n == 0)) |-> (o_empty === 1'b1))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (chk_act && i_rst_n_wr && (q_n == 0) && (p_n == 0))) hits_CHK_006 <= hits_CHK_006 + 1;

  final begin
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
  end
endmodule
