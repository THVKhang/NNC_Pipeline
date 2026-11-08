module nnc_chk_cross #(
  parameter int PARA_AXI_ID_W = 4
) (
  input  logic                        i_clk_axi,
  input  logic                        i_rst_n_axi,
  input  logic [(PARA_AXI_ID_W)-1:0]  i_axi_awid,
  input  logic [31:0]                 i_axi_awaddr,
  input  logic [7:0]                  i_axi_awlen,
  input  logic [2:0]                  i_axi_awsize,
  input  logic [1:0]                  i_axi_awburst,
  input  logic [3:0]                  i_axi_awcache,
  input  logic [2:0]                  i_axi_awprot,
  input  logic                        i_axi_awvalid,
  input  logic                        o_axi_awready,
  input  logic [31:0]                 i_axi_wdata,
  input  logic [3:0]                  i_axi_wstrb,
  input  logic                        i_axi_wlast,
  input  logic                        i_axi_wvalid,
  input  logic                        o_axi_wready,
  input  logic [(PARA_AXI_ID_W)-1:0]  o_axi_bid,
  input  logic [1:0]                  o_axi_bresp,
  input  logic                        o_axi_bvalid,
  input  logic                        i_axi_bready,
  input  logic [(PARA_AXI_ID_W)-1:0]  i_axi_arid,
  input  logic [31:0]                 i_axi_araddr,
  input  logic [7:0]                  i_axi_arlen,
  input  logic [2:0]                  i_axi_arsize,
  input  logic [1:0]                  i_axi_arburst,
  input  logic [3:0]                  i_axi_arcache,
  input  logic [2:0]                  i_axi_arprot,
  input  logic                        i_axi_arvalid,
  input  logic                        o_axi_arready,
  input  logic [(PARA_AXI_ID_W)-1:0]  o_axi_rid,
  input  logic [31:0]                 o_axi_rdata,
  input  logic [1:0]                  o_axi_rresp,
  input  logic                        o_axi_rlast,
  input  logic                        o_axi_rvalid,
  input  logic                        i_axi_rready,
  input  logic [31:0]                 o_apb_paddr,
  input  logic                        o_apb_pwrite,
  input  logic [31:0]                 o_apb_pwdata,
  input  logic [3:0]                  o_apb_pstrb,
  input  logic [2:0]                  o_apb_pprot,
  input  logic                        o_apb_psel,
  input  logic                        o_apb_penable,
  input  logic                        i_apb_pready,
  input  logic [31:0]                 i_apb_prdata,
  input  logic                        i_apb_pslverr
);

  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;
  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;

  // ---------------- Tracker (shared by CHK-014/015/016) ----------------
  localparam logic [1:0] OWN_IDLE = 2'd0;
  localparam logic [1:0] OWN_RD   = 2'd1;
  localparam logic [1:0] OWN_WR   = 2'd2;

  logic [1:0]  owner;
  logic        cap_unsup;
  logic        cap_write;
  logic [31:0] cap_addr;
  logic [7:0]  cap_len;
  logic [2:0]  cap_size;
  logic [1:0]  cap_burst;
  logic [2:0]  cap_prot;
  logic [8:0]  comp_cnt;
  logic [8:0]  setup_cnt;
  logic [8:0]  w_cnt;
  logic [31:0] wd_mem [0:255];
  logic [3:0]  ws_mem [0:255];
  logic [31:0] pd_mem [0:255];
  logic [3:0]  ps_mem [0:255];

  logic ar_hs, aw_hs, rd_done, wr_done, completing, hs_accept;
  assign ar_hs      = i_axi_arvalid && o_axi_arready;
  assign aw_hs      = i_axi_awvalid && o_axi_awready;
  assign rd_done    = o_axi_rvalid && i_axi_rready && o_axi_rlast;
  assign wr_done    = o_axi_bvalid && i_axi_bready;
  assign completing = ((owner == OWN_RD) && rd_done) || ((owner == OWN_WR) && wr_done);
  assign hs_accept  = (ar_hs || aw_hs) && ((owner == OWN_IDLE) || completing);

  // fields of the request being presented (AR has priority)
  logic [31:0] n_addr;
  logic [7:0]  n_len;
  logic [2:0]  n_size;
  logic [1:0]  n_burst;
  logic [3:0]  n_cache;
  logic [2:0]  n_prot;
  assign n_addr  = ar_hs ? i_axi_araddr  : i_axi_awaddr;
  assign n_len   = ar_hs ? i_axi_arlen   : i_axi_awlen;
  assign n_size  = ar_hs ? i_axi_arsize  : i_axi_awsize;
  assign n_burst = ar_hs ? i_axi_arburst : i_axi_awburst;
  assign n_cache = ar_hs ? i_axi_arcache : i_axi_awcache;
  assign n_prot  = ar_hs ? i_axi_arprot  : i_axi_awprot;

  logic [39:0] n_s40, n_end40;
  logic        n_unsup;
  assign n_s40   = 40'd1 << n_size;
  assign n_end40 = {8'd0, (n_addr & ~(n_s40[31:0] - 32'd1))} +
                   ((40'(n_len) + 40'd1) * n_s40) - 40'd1;
  assign n_unsup = (n_size > 3'd2) || (n_burst == 2'b11) ||
                   !((n_cache == 4'b0000) || (n_cache == 4'b0001)) ||
                   ((n_burst == 2'b01) && (n_addr[31:12] != n_end40[31:12]));

  logic apb_comp, apb_setup, w_hs;
  assign apb_comp  = (owner != OWN_IDLE) && !cap_unsup && o_apb_psel && o_apb_penable && i_apb_pready;
  assign apb_setup = (owner != OWN_IDLE) && !cap_unsup && o_apb_psel && !o_apb_penable;
  assign w_hs      = (owner == OWN_WR) && i_axi_wvalid && o_axi_wready;

  always_ff @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      owner     <= OWN_IDLE;
      cap_unsup <= 1'b0;
      cap_write <= 1'b0;
      cap_addr  <= 32'd0;
      cap_len   <= 8'd0;
      cap_size  <= 3'd0;
      cap_burst <= 2'd0;
      cap_prot  <= 3'd0;
      comp_cnt  <= 9'd0;
      setup_cnt <= 9'd0;
      w_cnt     <= 9'd0;
    end else begin
      if (hs_accept) begin
        owner     <= ar_hs ? OWN_RD : OWN_WR;
        cap_unsup <= n_unsup;
        cap_write <= !ar_hs;
        cap_addr  <= n_addr;
        cap_len   <= n_len;
        cap_size  <= n_size;
        cap_burst <= n_burst;
        cap_prot  <= n_prot;
        comp_cnt  <= 9'd0;
        setup_cnt <= 9'd0;
        w_cnt     <= 9'd0;
      end else begin
        if (completing) owner <= OWN_IDLE;
        if (apb_comp)  comp_cnt  <= comp_cnt + 9'd1;
        if (apb_setup) setup_cnt <= setup_cnt + 9'd1;
        if (w_hs)      w_cnt     <= w_cnt + 9'd1;
      end
    end
  end

  always_ff @(posedge i_clk_axi) begin
    if (apb_comp) begin
      pd_mem[comp_cnt[7:0]] <= o_apb_pwdata;
      ps_mem[comp_cnt[7:0]] <= o_apb_pstrb;
    end
    if (w_hs) begin
      wd_mem[w_cnt[7:0]] <= i_axi_wdata;
      ws_mem[w_cnt[7:0]] <= i_axi_wstrb;
    end
  end

  // expected beat address for APB transfer number comp_cnt
  logic [31:0] s_b, t_b, lower_b, k_b, exp_addr, exp_fixed, exp_incr, exp_wrap;
  assign s_b       = 32'd1 << cap_size;
  assign k_b       = {23'd0, comp_cnt};
  assign t_b       = s_b * ({24'd0, cap_len} + 32'd1);
  assign lower_b   = (cap_addr / t_b) * t_b;
  assign exp_fixed = cap_addr;
  assign exp_incr  = (comp_cnt == 9'd0) ? cap_addr : ((cap_addr & ~(s_b - 32'd1)) + k_b * s_b);
  assign exp_wrap  = lower_b + ((cap_addr - lower_b + k_b * s_b) % t_b);
  assign exp_addr  = (cap_burst == 2'b00) ? exp_fixed :
                     (cap_burst == 2'b01) ? exp_incr  : exp_wrap;

  // ---------------- CHK-014 ----------------
  logic ant_014, cons_014;
  assign ant_014 = ar_hs || aw_hs || o_axi_rvalid || o_axi_bvalid || o_apb_psel;
  assign cons_014 = !(ar_hs && aw_hs) &&
                    (!(ar_hs || aw_hs) || (owner == OWN_IDLE) || completing) &&
                    (!o_axi_rvalid || (owner == OWN_RD)) &&
                    (!o_axi_bvalid || (owner == OWN_WR)) &&
                    (!o_apb_psel || (owner != OWN_IDLE) || ar_hs || aw_hs);

  // CHK-014: Transaction tracker: one global owner, actions only after the handshake (AB-1.1-02, AB-3-02, AB-3-06, AB-5.1-04, AB-10.4-02)
  a_CHK_014: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi) ant_014 |-> cons_014)
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (ant_014)) hits_CHK_014 <= hits_CHK_014 + 1;

  // ---------------- CHK-015 ----------------
  logic ant_015;
  assign ant_015 = (hs_accept && n_unsup) || ((owner != OWN_IDLE) && cap_unsup);

  // CHK-015: No APB activity for unsupported requests (AB-3-09, AB-3-18, AB-3-32, AB-3-36, AB-6.3-14, AB-12-02, AB-12-05, AB-6.3-02, AB-6.3-05)
  a_CHK_015: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi) ant_015 |-> !o_apb_psel)
    else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (ant_015)) hits_CHK_015 <= hits_CHK_015 + 1;

  // ---------------- CHK-016 ----------------
  logic        w_chk;
  logic        wc_a_ok, wc_b_ok, apb_ok, setup_ok, cons_016, ant_016;
  logic [7:0]  ck, wk;
  assign ck    = comp_cnt[7:0];
  assign wk    = w_cnt[7:0];
  assign w_chk = w_hs && cap_write && !cap_unsup;

  assign wc_a_ok = !apb_comp || !cap_write ||
                   ((w_cnt > comp_cnt) ? ((o_apb_pwdata == wd_mem[ck]) && (o_apb_pstrb == ws_mem[ck])) :
                    (w_hs && (w_cnt == comp_cnt)) ? ((o_apb_pwdata == i_axi_wdata) && (o_apb_pstrb == i_axi_wstrb)) :
                    1'b1);
  assign wc_b_ok = !w_chk || !(comp_cnt > w_cnt) ||
                   ((i_axi_wdata == pd_mem[wk]) && (i_axi_wstrb == ps_mem[wk]));
  assign apb_ok  = !apb_comp ||
                   ((o_apb_pwrite == cap_write) &&
                    (o_apb_paddr == (exp_addr & 32'hFFFF_FFFC)) &&
                    (o_apb_pprot == cap_prot));
  assign setup_ok = !apb_setup || (setup_cnt <= {1'b0, cap_len});
  assign ant_016  = apb_comp || apb_setup || w_chk;
  assign cons_016 = apb_ok && wc_a_ok && wc_b_ok && setup_ok;

  // CHK-016: APB transfer sequence matches AXI beats (AB-1.1-01, AB-1.2-02, AB-3-11, AB-3-15, AB-6.2-13, AB-9-10, AB-9-11, AB-9-03, AB-18-01, AB-6.3-07, AB-10.2-01, AB-10.2-02, AB-5.3-02, AB-5.3-05)
  a_CHK_016: assert property (@(posedge i_clk_axi) disable iff (!i_rst_n_axi) ant_016 |-> cons_016)
    else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (ant_016)) hits_CHK_016 <= hits_CHK_016 + 1;

  final begin
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
  end
endmodule
