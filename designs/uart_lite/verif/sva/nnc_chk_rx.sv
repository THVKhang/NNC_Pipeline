module nnc_chk_rx #(
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

  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;
  int unsigned fails_CHK_004 = 0;
  int unsigned hits_CHK_004 = 0;
  int unsigned fails_CHK_005 = 0;
  int unsigned hits_CHK_005 = 0;
  int unsigned fails_CHK_006 = 0;
  int unsigned hits_CHK_006 = 0;
  int unsigned fails_CHK_007 = 0;
  int unsigned hits_CHK_007 = 0;
  int unsigned fails_CHK_008 = 0;
  int unsigned hits_CHK_008 = 0;
  int unsigned fails_CHK_009 = 0;
  int unsigned hits_CHK_009 = 0;

  // RX reference model (derived only from i_rxd, i_rst_n)
  localparam int unsigned N_BIT = PARA_UART_CLKS_PER_BIT;
  localparam int unsigned H_HALF = N_BIT / 2;
  localparam int unsigned M_CNT = H_HALF + 9 * N_BIT;

  logic        mdl_busy;
  int unsigned mdl_cnt;
  logic [7:0]  mdl_sh;
  logic [7:0]  mdl_byte;
  logic        mdl_stop;
  logic        mdl_m1;
  logic        mdl_v;      // 1 when the sampled edge is the delivery edge V
  logic        rst_d;
  logic        drop_q;
  logic        load_q;

  assign mdl_v = mdl_m1_d2;
  logic mdl_m1_d2;
  logic mdl_prev;   // NNC hand fix (G3, triage B): previous i_rxd sample of the model

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      mdl_busy <= 1'b0;
      mdl_cnt  <= 0;
      mdl_sh   <= 8'h00;
      mdl_byte <= 8'h00;
      mdl_stop <= 1'b1;
      mdl_m1   <= 1'b0;
      mdl_m1_d2 <= 1'b0;
      mdl_prev  <= 1'b1;
    end else begin
      mdl_prev  <= i_rxd;
      mdl_m1    <= 1'b0;
      mdl_m1_d2 <= mdl_m1;
      if (!mdl_busy) begin
        // NNC hand fix (G3, triage B): a frame starts on a falling edge of i_rxd (previous sample 1,
        // REQ-RST-010: taken as 1 at reset release), not on any low sample; the model invented frames on a
        // line held low (CHK-003/005/006/009).
        if (mdl_prev && !i_rxd) begin
          mdl_busy <= 1'b1;
          mdl_cnt  <= 1;
        end
      end else begin
        mdl_cnt <= mdl_cnt + 1;
        if (mdl_cnt == H_HALF && i_rxd) begin
          mdl_busy <= 1'b0;
        end else if (mdl_cnt > H_HALF && mdl_cnt < M_CNT && (((mdl_cnt - H_HALF) % N_BIT) == 0)) begin
          mdl_sh <= {i_rxd, mdl_sh[7:1]};
        end else if (mdl_cnt == M_CNT) begin
          mdl_byte <= mdl_sh;
          mdl_stop <= i_rxd;
          mdl_m1   <= 1'b1;
          mdl_busy <= 1'b0;
        end
      end
    end
  end

  always_ff @(posedge i_clk) begin
    rst_d <= i_rst_n;
    if (!i_rst_n) begin
      drop_q <= 1'b0;
      load_q <= 1'b0;
    end else begin
      drop_q <= mdl_v && o_rx_valid && !i_rx_ready;
      load_q <= mdl_v && (!o_rx_valid || i_rx_ready);
    end
  end

  // CHK-003: Delivery into an empty holding register at V=M+2 (UL-7.6-01, UL-7.5-01, UL-7.5-02, UL-8.2-01, UL-14-03, UL-7.7-01, UL-1.2-09, UL-5-06, UL-5-09, UL-5-11)
  a_CHK_003: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (mdl_v && !o_rx_valid) |=> (o_rx_valid && (o_rx_data == mdl_byte) && (o_rx_frame_err == !mdl_stop) && !o_rx_overrun))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (mdl_v && !o_rx_valid)) hits_CHK_003 <= hits_CHK_003 + 1;

  // CHK-004: Held byte taken at the delivery edge itself loads the new byte, no overrun (UL-7.6-02, UL-10.2-02, UL-14-04)
  a_CHK_004: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (mdl_v && o_rx_valid && i_rx_ready) |=> (o_rx_valid && (o_rx_data == mdl_byte) && (o_rx_frame_err == !mdl_stop) && !o_rx_overrun))
    else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (mdl_v && o_rx_valid && i_rx_ready)) hits_CHK_004 <= hits_CHK_004 + 1;

  // CHK-005: Overrun drop at V keeps the held byte; one-cycle pulse (UL-7.8-01, UL-7.8-02, UL-7.8-03, UL-8.4-01, UL-10.2-01, UL-1.2-10, UL-5-13)
  a_CHK_005: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (mdl_v && o_rx_valid && !i_rx_ready) |=> ((o_rx_overrun && o_rx_valid && (o_rx_data == $past(o_rx_data)) && (o_rx_frame_err == $past(o_rx_frame_err))) ##1 !o_rx_overrun))
    else begin fails_CHK_005++; $display("NNC_FAIL CHK-005 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (mdl_v && o_rx_valid && !i_rx_ready)) hits_CHK_005 <= hits_CHK_005 + 1;

  // CHK-006: o_rx_overrun only after a drop edge, independent of o_rx_valid (UL-7.8-04, UL-7.8-05, UL-7.8-06, UL-7.4-06)
  a_CHK_006: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    rst_d |-> (o_rx_overrun == drop_q))
    else begin fails_CHK_006++; $display("NNC_FAIL CHK-006 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (rst_d)) hits_CHK_006 <= hits_CHK_006 + 1;

  // CHK-007: Consumer take empties the holding register (UL-7.6-03, UL-5-07)
  a_CHK_007: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (!mdl_v && o_rx_valid && i_rx_ready) |=> (!o_rx_valid && $stable(o_rx_data) && $stable(o_rx_frame_err) && !o_rx_overrun))
    else begin fails_CHK_007++; $display("NNC_FAIL CHK-007 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!mdl_v && o_rx_valid && i_rx_ready)) hits_CHK_007 <= hits_CHK_007 + 1;

  // CHK-008: Held byte is stable until taken (UL-7.6-04, UL-1.2-05)
  a_CHK_008: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (!mdl_v && o_rx_valid && !i_rx_ready) |=> (o_rx_valid && $stable(o_rx_data) && $stable(o_rx_frame_err)))
    else begin fails_CHK_008++; $display("NNC_FAIL CHK-008 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!mdl_v && o_rx_valid && !i_rx_ready)) hits_CHK_008 <= hits_CHK_008 + 1;

  // CHK-009: Empty register: i_rx_ready has no effect; data and flag keep the last loaded values (UL-7.6-05, UL-7.6-06, UL-14-07, UL-10.7-02)
  a_CHK_009: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (!mdl_v && !o_rx_valid) |=> (!o_rx_valid && $stable(o_rx_data) && $stable(o_rx_frame_err) && !o_rx_overrun))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (!mdl_v && !o_rx_valid)) hits_CHK_009 <= hits_CHK_009 + 1;

  // CHK-009: data and flag change only after a load edge (UL-7.6-05)
  a_CHK_009_b: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (rst_d && !load_q) |-> ($stable(o_rx_data) && $stable(o_rx_frame_err)))
    else begin fails_CHK_009++; $display("NNC_FAIL CHK-009 @%0t", $time); end

  final begin
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
    $display("NNC_CHECK CHK-004 hits=%0d fails=%0d", hits_CHK_004, fails_CHK_004);
    $display("NNC_CHECK CHK-005 hits=%0d fails=%0d", hits_CHK_005, fails_CHK_005);
    $display("NNC_CHECK CHK-006 hits=%0d fails=%0d", hits_CHK_006, fails_CHK_006);
    $display("NNC_CHECK CHK-007 hits=%0d fails=%0d", hits_CHK_007, fails_CHK_007);
    $display("NNC_CHECK CHK-008 hits=%0d fails=%0d", hits_CHK_008, fails_CHK_008);
    $display("NNC_CHECK CHK-009 hits=%0d fails=%0d", hits_CHK_009, fails_CHK_009);
  end
endmodule
