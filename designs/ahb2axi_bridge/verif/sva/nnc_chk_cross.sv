module nnc_chk_cross #(
  parameter int PARA_RD_ID_COUNT = 1,
  parameter int PARA_WR_ID_COUNT = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_ahb_hsel,
  input  logic                        i_ahb_hready,
  input  logic [31:0]                 i_ahb_haddr,
  input  logic [1:0]                  i_ahb_htrans,
  input  logic                        i_ahb_hwrite,
  input  logic [2:0]                  i_ahb_hsize,
  input  logic [2:0]                  i_ahb_hburst,
  input  logic [6:0]                  i_ahb_hprot,
  input  logic                        i_ahb_hnonsec,
  input  logic                        i_ahb_hmastlock,
  input  logic [31:0]                 i_ahb_hwdata,
  input  logic [3:0]                  i_ahb_hwstrb,
  input  logic                        o_ahb_hreadyout,
  input  logic                        o_ahb_hresp,
  input  logic [31:0]                 o_ahb_hrdata,
  input  logic [2:0]                  o_axi_awid,
  input  logic [31:0]                 o_axi_awaddr,
  input  logic [7:0]                  o_axi_awlen,
  input  logic [2:0]                  o_axi_awsize,
  input  logic [1:0]                  o_axi_awburst,
  input  logic                        o_axi_awlock,
  input  logic [3:0]                  o_axi_awcache,
  input  logic [2:0]                  o_axi_awprot,
  input  logic                        o_axi_awvalid,
  input  logic                        i_axi_awready,
  input  logic [31:0]                 o_axi_wdata,
  input  logic [3:0]                  o_axi_wstrb,
  input  logic                        o_axi_wlast,
  input  logic                        o_axi_wvalid,
  input  logic                        i_axi_wready,
  input  logic [2:0]                  i_axi_bid,
  input  logic [1:0]                  i_axi_bresp,
  input  logic                        i_axi_bvalid,
  input  logic                        o_axi_bready,
  input  logic [2:0]                  o_axi_arid,
  input  logic [31:0]                 o_axi_araddr,
  input  logic [7:0]                  o_axi_arlen,
  input  logic [2:0]                  o_axi_arsize,
  input  logic [1:0]                  o_axi_arburst,
  input  logic                        o_axi_arlock,
  input  logic [3:0]                  o_axi_arcache,
  input  logic [2:0]                  o_axi_arprot,
  input  logic                        o_axi_arvalid,
  input  logic                        i_axi_arready,
  input  logic [2:0]                  i_axi_rid,
  input  logic [31:0]                 i_axi_rdata,
  input  logic [1:0]                  i_axi_rresp,
  input  logic                        i_axi_rlast,
  input  logic                        i_axi_rvalid,
  input  logic                        o_axi_rready
);

  int unsigned fails_CHK_013 = 0;
  int unsigned hits_CHK_013 = 0;
  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;
  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;
  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;

  localparam int unsigned D = 64;

  // ---------------- common helpers ----------------
  wire h_acc = i_ahb_hsel && i_ahb_hready && i_ahb_htrans[1];
  logic h_misal;
  always_comb begin
    case (i_ahb_hsize)
      3'd0:    h_misal = 1'b0;
      3'd1:    h_misal = i_ahb_haddr[0];
      3'd2:    h_misal = (i_ahb_haddr[1:0] != 2'b00);
      default: h_misal = 1'b1;
    endcase
  end
  wire h_rsv = (i_ahb_hprot[5:2] == 4'b0100) || (i_ahb_hprot[5:2] == 4'b0101) ||
               (i_ahb_hprot[5:2] == 4'b1000) || (i_ahb_hprot[5:2] == 4'b1001) ||
               (i_ahb_hprot[5:2] == 4'b1010) || (i_ahb_hprot[5:2] == 4'b1011) ||
               (i_ahb_hprot[5:2] == 4'b1100) || (i_ahb_hprot[5:2] == 4'b1101);
  wire h_rej = i_ahb_hmastlock || i_ahb_hprot[6] || (i_ahb_hsize > 3'd2) || h_misal || h_rsv;
  wire h_acc_ok = h_acc && !h_rej;

  // burst position / size of the current write address phase
  logic [4:0] h_N;
  always_comb begin
    case (i_ahb_hburst)
      3'b010, 3'b011: h_N = 5'd4;
      3'b100, 3'b101: h_N = 5'd8;
      3'b110, 3'b111: h_N = 5'd16;
      default:        h_N = 5'd0;
    endcase
  end
  int unsigned h_prev_cnt;
  int unsigned h_cur_cnt;
  always_comb begin
    h_cur_cnt = (i_ahb_htrans == 2'b10) ? 32'd1 : (h_prev_cnt + 32'd1);
  end
  wire h_term = (h_N != 5'd0) && (h_cur_cnt == {27'd0, h_N});
  wire h_wait_cls = (i_ahb_hburst <= 3'b001) || !i_ahb_hprot[2] ||
                    (i_ahb_hprot[6:2] == 5'b00001) || h_term;

  // counters
  int unsigned ra, arh, wa, wh, bh, wlcnt, pcnt;
  int unsigned bstart_a [D];
  int unsigned bn_a     [D];
  int unsigned xw       [D];
  logic        bad_a    [D];

  // data phase tracker
  logic        dp_active, dp_rd, dp_rej, dp_wait, dp_term, dp_rseen, dp_rok;
  int unsigned dp_j, dp_bs;
  logic [31:0] dp_rdata;

  wire h_rhs  = i_axi_rvalid && o_axi_rready;
  wire h_whs  = o_axi_wvalid && i_axi_wready;
  wire h_bhs  = i_axi_bvalid && o_axi_bready;

  always_ff @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      ra <= 0; arh <= 0; wa <= 0; wh <= 0; bh <= 0; wlcnt <= 0; pcnt <= 0;
      h_prev_cnt <= 0;
      dp_active <= 1'b0; dp_rd <= 1'b0; dp_rej <= 1'b0; dp_wait <= 1'b0;
      dp_term <= 1'b0; dp_rseen <= 1'b0; dp_rok <= 1'b0;
      dp_j <= 0; dp_bs <= 0; dp_rdata <= 32'd0;
    end else begin
      if (h_acc_ok && !i_ahb_hwrite) ra <= ra + 1;
      if (o_axi_arvalid && i_axi_arready) arh <= arh + 1;
      if (o_axi_awvalid && i_axi_awready) pcnt <= pcnt + 32'(o_axi_awlen) + 1;

      if (h_acc_ok && i_ahb_hwrite) begin
        wa <= wa + 1;
        h_prev_cnt <= h_cur_cnt;
        bstart_a[(wa + 1) % D] <= wa + 2 - h_cur_cnt;
        bn_a[(wa + 1) % D]     <= {27'd0, h_N};
      end

      if (h_whs) begin
        wh <= wh + 1;
        xw[(wh + 1) % D] <= wlcnt + 1;
        if (o_axi_wlast) wlcnt <= wlcnt + 1;
      end
      if (h_bhs) begin
        bh <= bh + 1;
        bad_a[bh % D] <= (i_axi_bresp != 2'b00);
      end

      if (h_acc) begin
        dp_active <= 1'b1;
        dp_rd     <= !i_ahb_hwrite;
        dp_rej    <= h_rej;
        dp_j      <= wa + 1;
        dp_wait   <= h_wait_cls;
        dp_term   <= h_term;
        dp_bs     <= wa + 2 - h_cur_cnt;
        dp_rseen  <= 1'b0;
      end else begin
        if (o_ahb_hreadyout) dp_active <= 1'b0;
        if (dp_active && dp_rd && h_rhs && !dp_rseen) begin
          dp_rseen <= 1'b1;
          dp_rdata <= i_axi_rdata;
          dp_rok   <= (i_axi_rresp == 2'b00);
        end
      end
    end
  end

  // ---------------- CHK-013 ----------------
  // CHK-013: No AR before the matching AHB read is accepted (AA-3-06, AA-5.4-02, AA-15.3-02, AA-21-03, AA-1.1-01, AA-3-03)
  a_CHK_013: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    o_axi_arvalid |-> (ra > arh))
    else begin fails_CHK_013++; $display("NNC_FAIL CHK-013 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_axi_arvalid)) hits_CHK_013 <= hits_CHK_013 + 1;

  // ---------------- CHK-014 ----------------
  int unsigned c14_f, c14_l;
  logic c14_ok;
  always_comb begin
    c14_f = pcnt + 1;
    c14_l = pcnt + 32'(o_axi_awlen) + 1;
    c14_ok = (wa >= c14_l) &&
             (bn_a[c14_f % D] != 0) &&
             (bstart_a[c14_f % D] == bstart_a[c14_l % D]) &&
             (bn_a[c14_f % D] == bn_a[c14_l % D]) &&
             (wa + 1 >= bstart_a[c14_f % D] + bn_a[c14_f % D]);
  end
  // CHK-014: No AXI write burst before the full AHB fixed burst is accepted (AA-15.3-05, AA-5.4-05, AA-3-08, AA-T1.7.3.1-08)
  a_CHK_014: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_axi_awvalid && (o_axi_awlen != 8'd0)) |-> c14_ok)
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && ((o_axi_awvalid && (o_axi_awlen != 8'd0)))) hits_CHK_014 <= hits_CHK_014 + 1;

  // ---------------- CHK-015 ----------------
  wire        c15_ant = dp_active && dp_rd && !dp_rej && o_ahb_hreadyout;
  wire        c15_have = dp_rseen || h_rhs;
  wire [31:0] c15_data = dp_rseen ? dp_rdata : i_axi_rdata;
  wire        c15_ok   = dp_rseen ? dp_rok : (i_axi_rresp == 2'b00);
  wire        c15_cons = c15_have &&
                         (c15_ok ? (!o_ahb_hresp && (o_ahb_hrdata == c15_data)) : o_ahb_hresp);
  // CHK-015: AHB read completes only with its R beat and carries RDATA unchanged (AA-5.3-02, AA-10.4-01, AA-3-05, AA-T1.7.3.4-01, AA-9-03, AA-1.1-01, AA-3-32, AA-3-33)
  a_CHK_015: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    c15_ant |-> c15_cons)
    else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (c15_ant)) hits_CHK_015 <= hits_CHK_015 + 1;

  // ---------------- CHK-016 ----------------
  int unsigned c16_xj, c16_lo, c16_k, c16_bnow_i;
  logic c16_wdone, c16_err, c16_bok;
  always_comb begin
    c16_xj   = xw[dp_j % D];
    c16_wdone = (wh >= dp_j);
    c16_bnow_i = h_bhs ? 1 : 0;
    c16_bok  = c16_wdone && ((bh + c16_bnow_i) >= c16_xj);
    c16_lo   = c16_xj;
    if (dp_term && (dp_bs >= 1) && (wh >= dp_bs)) c16_lo = xw[dp_bs % D];
    c16_err  = 1'b0;
    c16_k    = 0;
    for (int unsigned i = 0; i < 64; i++) begin
      if (c16_wdone && (c16_xj >= c16_lo + i) && (c16_xj >= i + 1)) begin
        c16_k = c16_xj - i;
        if (c16_k <= bh) begin
          if (bad_a[(c16_k - 1) % D]) c16_err = 1'b1;
        end else if ((c16_k == bh + 1) && h_bhs && (i_axi_bresp != 2'b00)) begin
          c16_err = 1'b1;
        end
      end
    end
  end
  wire c16_ant = dp_active && !dp_rd && !dp_rej && dp_wait && o_ahb_hreadyout;
  wire c16_cons = c16_bok && (c16_err ? o_ahb_hresp : !o_ahb_hresp);
  // CHK-016: Waiting-class writes complete only after their BRESP (AA-3-17, AA-3-18, AA-10.4-03, AA-20.3-04, AA-21-02, AA-3-40, AA-10.2-02, AA-T1.7.3.4-02, AA-3-21)
  a_CHK_016: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    c16_ant |-> c16_cons)
    else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (c16_ant)) hits_CHK_016 <= hits_CHK_016 + 1;

  // ---------------- CHK-017 ----------------
  wire c17_rejdone = dp_active && dp_rej && o_ahb_hreadyout;
  wire c17_ant = c17_rejdone || h_whs;
  wire c17_cons = (!c17_rejdone || o_ahb_hresp) && (!h_whs || (wh < wa));
  // CHK-017: Locally rejected transfers end in ERROR and produce no W data (AA-3-34, AA-3-35, AA-T1.7.3.3-01, AA-20.3-02, AA-12-01, AA-12-03, AA-12-05, AA-20.2-01)
  a_CHK_017: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    c17_ant |-> c17_cons)
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (c17_ant)) hits_CHK_017 <= hits_CHK_017 + 1;

  final begin
    $display("NNC_CHECK CHK-013 hits=%0d fails=%0d", hits_CHK_013, fails_CHK_013);
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
  end
endmodule
