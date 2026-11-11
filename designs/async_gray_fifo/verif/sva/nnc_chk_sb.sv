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

  // Reference model: one process sees both clocks, so the queues have a single driver.
  logic [PARA_AFIFO_DATA_W-1:0] q_ref[$];
  logic [PARA_AFIFO_DATA_W-1:0] p_ref[$];
  logic        clk_wr_prev = 1'b0;
  logic        clk_rd_prev = 1'b0;
  logic        busy_prev   = 1'b0;
  logic        sw_pend     = 1'b0;
  int unsigned sw_cnt      = 0;
  int unsigned hits_CHK_006_r = 0;

  // Snapshots (non-blocking, so assertions see the state before the current edge)
  logic                          s_active = 1'b0;
  logic                          s_have   = 1'b0;
  logic                          s_pempty = 1'b1;
  int                            s_n      = 0;
  logic [PARA_AFIFO_DATA_W-1:0]  s_head   = '0;

  always @(i_clk_wr or i_clk_rd or i_rst_n_wr or i_rst_n_rd) begin
    logic wr_edge;
    logic rd_edge;
    wr_edge = (i_clk_wr === 1'b1) && (clk_wr_prev !== 1'b1);
    rd_edge = (i_clk_rd === 1'b1) && (clk_rd_prev !== 1'b1);
    clk_wr_prev = (i_clk_wr === 1'b1);
    clk_rd_prev = (i_clk_rd === 1'b1);
    if ((i_rst_n_wr !== 1'b1) || (i_rst_n_rd !== 1'b1)) begin
      q_ref.delete();
      p_ref.delete();
      busy_prev = 1'b0;
      sw_pend   = 1'b0;
      sw_cnt    = 0;
    end else begin
      // read edge first: simultaneous edges see the state before the write
      if (rd_edge) begin
        if ((i_rd_en === 1'b1) && (o_empty === 1'b0)) begin
          if (p_ref.size() > 0) void'(p_ref.pop_front());
          else if (q_ref.size() > 0) void'(q_ref.pop_front());
        end
        if (sw_pend) begin
          sw_cnt = sw_cnt + 1;
          if (sw_cnt >= 5) begin
            p_ref.delete();
            sw_pend = 1'b0;
          end
        end
      end
      if (wr_edge) begin
        if ((i_wr_en === 1'b1) && (o_full === 1'b0)) q_ref.push_back(i_wr_data);
        if ((o_sw_rst_busy === 1'b1) && !busy_prev) begin
          while (q_ref.size() > 0) p_ref.push_back(q_ref.pop_front());
          sw_pend = 1'b1;
          sw_cnt  = 0;
        end
        busy_prev = (o_sw_rst_busy === 1'b1);
      end
    end
    s_active <= (i_rst_n_wr === 1'b1) && (i_rst_n_rd === 1'b1);
    s_n      <= q_ref.size();
    s_pempty <= (p_ref.size() == 0);
    s_have   <= (p_ref.size() > 0) || (q_ref.size() > 0);
    s_head   <= (p_ref.size() > 0) ? p_ref[0] : ((q_ref.size() > 0) ? q_ref[0] : '0);
  end

  // CHK-005: Scoreboard: show-ahead data, write order, exactly-once, software-reset discard (AF-1.1-01, AF-1.1-02, AF-3-04, AF-3-05, AF-3-06, AF-3-26, AF-3-32, AF-3-57, AF-5.3-01, AF-5.3-04, AF-5.3-05, AF-6.2-04, AF-6.2-05, AF-6.2-19, AF-6.2-29, AF-6.3-09, AF-7.2-03, AF-10.2-02, AF-10.4-01, AF-10.5-01, AF-10.5-02, AF-10.6.3-03, AF-10.7.2-01, AF-10.7.6-06, AF-15.3-05, AF-20.2-04, AF-5.4-04, AF-10.7.4-08, AF-10.7.5-04, AF-7.3-06)
  a_CHK_005: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd) (s_active && (o_empty === 1'b0)) |-> (s_have && ((^o_rd_data) !== 1'bx) && (o_rd_data === s_head)))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (s_active && (o_empty === 1'b0))) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: Flags are never optimistic; occupancy is within 0..PARA_AFIFO_DEPTH (AF-3-10, AF-3-12, AF-5.1-01, AF-5.4-01, AF-5.4-04, AF-10.3-03, AF-10.6.2-10, AF-15.3-06, AF-15.3-19, AF-6.2-17, AF-6.2-20, AF-10.5-04)
  a_CHK_006: assert property (@(posedge i_clk_wr) disable iff (!i_rst_n_wr) s_active |-> ((s_n <= PARA_AFIFO_DEPTH) && ((s_n != PARA_AFIFO_DEPTH) || (o_full === 1'b1))))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_wr) if (!(!i_rst_n_wr) && (s_active)) hits_CHK_006 <= hits_CHK_006 + 1;

  a_CHK_006_r: assert property (@(posedge i_clk_rd) disable iff (!i_rst_n_rd) (s_active && (s_n == 0) && s_pempty) |-> (o_empty === 1'b1))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk_rd) if (!(!i_rst_n_rd) && (s_active && (s_n == 0) && s_pempty)) hits_CHK_006_r <= hits_CHK_006_r + 1;

  final begin
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
  end
endmodule
