module nnc_cov #(
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

  // ---- helper handshake and decode wires ----
  wire cv_ar_hs   = i_axi_arvalid & o_axi_arready;
  wire cv_aw_hs   = i_axi_awvalid & o_axi_awready;
  wire cv_w_hs    = i_axi_wvalid & o_axi_wready;
  wire cv_b_hs    = o_axi_bvalid & i_axi_bready;
  wire cv_r_hs    = o_axi_rvalid & i_axi_rready;
  wire cv_apb_setup = o_apb_psel & ~o_apb_penable;
  wire cv_apb_acc   = o_apb_psel & o_apb_penable;
  wire cv_apb_done  = cv_apb_acc & i_apb_pready;

  wire        cv_ar_sz_bad   = (i_axi_arsize > 3'd2);
  wire        cv_ar_rsv      = (i_axi_arburst == 2'b11);
  wire        cv_ar_cache_bad = (i_axi_arcache[3:1] != 3'b000);
  wire        cv_ar_len_bad  = ((i_axi_arburst == 2'b00) && (i_axi_arlen > 8'd15)) ||
                               ((i_axi_arburst == 2'b10) && !((i_axi_arlen == 8'd1) || (i_axi_arlen == 8'd3) ||
                                                              (i_axi_arlen == 8'd7) || (i_axi_arlen == 8'd15)));
  wire [31:0] cv_ar_bytes    = ({24'd0, i_axi_arlen} + 32'd1) << i_axi_arsize;
  wire [31:0] cv_ar_off      = {20'd0, i_axi_araddr[11:0]} & ~((32'd1 << i_axi_arsize) - 32'd1);
  wire [31:0] cv_ar_end      = cv_ar_off + cv_ar_bytes;
  wire        cv_ar_cross    = (i_axi_arburst == 2'b01) && (cv_ar_end > 32'd4096);
  wire        cv_ar_unsup    = cv_ar_sz_bad || cv_ar_rsv || cv_ar_cache_bad || cv_ar_len_bad || cv_ar_cross;

  wire        cv_aw_sz_bad   = (i_axi_awsize > 3'd2);
  wire        cv_aw_rsv      = (i_axi_awburst == 2'b11);
  wire        cv_aw_cache_bad = (i_axi_awcache[3:1] != 3'b000);
  wire        cv_aw_len_bad  = ((i_axi_awburst == 2'b00) && (i_axi_awlen > 8'd15)) ||
                               ((i_axi_awburst == 2'b10) && !((i_axi_awlen == 8'd1) || (i_axi_awlen == 8'd3) ||
                                                              (i_axi_awlen == 8'd7) || (i_axi_awlen == 8'd15)));
  wire [31:0] cv_aw_bytes    = ({24'd0, i_axi_awlen} + 32'd1) << i_axi_awsize;
  wire [31:0] cv_aw_off      = {20'd0, i_axi_awaddr[11:0]} & ~((32'd1 << i_axi_awsize) - 32'd1);
  wire [31:0] cv_aw_end      = cv_aw_off + cv_aw_bytes;
  wire        cv_aw_cross    = (i_axi_awburst == 2'b01) && (cv_aw_end > 32'd4096);
  wire        cv_aw_unsup    = cv_aw_sz_bad || cv_aw_rsv || cv_aw_cache_bad || cv_aw_len_bad || cv_aw_cross;

  // ---- tracker and history registers ----
  logic [1:0]  cv_owner     = 2'd0;   // 0 idle, 1 read, 2 write
  logic [7:0]  cv_len       = 8'd0;
  logic [1:0]  cv_burst     = 2'd0;
  logic [2:0]  cv_size      = 3'd0;
  logic [1:0]  cv_addr_lo   = 2'd0;
  logic        cv_unsup     = 1'b0;
  logic [8:0]  cv_acnt      = 9'd0;
  logic [31:0] cv_last_paddr = 32'd0;
  logic [1:0]  cv_rstall    = 2'd0;
  logic [1:0]  cv_bstall    = 2'd0;
  logic [5:0]  cv_await     = 6'd0;
  logic [1:0]  cv_last_done = 2'd0;   // 0 none, 1 read, 2 write
  logic        cv_wr_err    = 1'b0;
  logic        cv_rd_err    = 1'b0;
  logic        cv_rst_flag  = 1'b0;

  always_ff @(posedge i_clk_axi) begin
    if (!i_rst_n_axi) begin
      cv_owner      <= 2'd0;
      cv_len        <= 8'd0;
      cv_burst      <= 2'd0;
      cv_size       <= 3'd0;
      cv_addr_lo    <= 2'd0;
      cv_unsup      <= 1'b0;
      cv_acnt       <= 9'd0;
      cv_last_paddr <= 32'd0;
      cv_rstall     <= 2'd0;
      cv_bstall     <= 2'd0;
      cv_await      <= 6'd0;
      cv_last_done  <= 2'd0;
      cv_wr_err     <= 1'b0;
      cv_rd_err     <= 1'b0;
      if (cv_owner != 2'd0 || o_apb_psel) cv_rst_flag <= 1'b1;
    end else begin
      cv_rst_flag <= 1'b0;
      if (cv_owner == 2'd0) begin
        cv_acnt   <= 9'd0;
        cv_wr_err <= 1'b0;
        cv_rd_err <= 1'b0;
        if (cv_ar_hs) begin
          cv_owner   <= 2'd1;
          cv_len     <= i_axi_arlen;
          cv_burst   <= i_axi_arburst;
          cv_size    <= i_axi_arsize;
          cv_addr_lo <= i_axi_araddr[1:0];
          cv_unsup   <= cv_ar_unsup;
        end else if (cv_aw_hs) begin
          cv_owner   <= 2'd2;
          cv_len     <= i_axi_awlen;
          cv_burst   <= i_axi_awburst;
          cv_size    <= i_axi_awsize;
          cv_addr_lo <= i_axi_awaddr[1:0];
          cv_unsup   <= cv_aw_unsup;
        end
      end else begin
        if (cv_apb_done) begin
          cv_acnt <= cv_acnt + 9'd1;
          if (o_apb_pwrite && i_apb_pslverr)  cv_wr_err <= 1'b1;
          if (!o_apb_pwrite && i_apb_pslverr) cv_rd_err <= 1'b1;
        end
        if (cv_r_hs && cv_owner == 2'd1 && o_axi_rlast) begin
          cv_owner     <= 2'd0;
          cv_last_done <= 2'd1;
        end
        if (cv_b_hs && cv_owner == 2'd2) begin
          cv_owner     <= 2'd0;
          cv_last_done <= 2'd2;
        end
      end
      if (cv_apb_done) cv_last_paddr <= o_apb_paddr;
      if (o_axi_rvalid && !i_axi_rready) cv_rstall <= (cv_rstall == 2'd3) ? 2'd3 : cv_rstall + 2'd1;
      else cv_rstall <= 2'd0;
      if (o_axi_bvalid && !i_axi_bready) cv_bstall <= (cv_bstall == 2'd3) ? 2'd3 : cv_bstall + 2'd1;
      else cv_bstall <= 2'd0;
      if (cv_apb_acc && !i_apb_pready) cv_await <= (cv_await == 6'd63) ? 6'd63 : cv_await + 6'd1;
      else cv_await <= 6'd0;
    end
  end

  wire cv_rd_end = cv_r_hs && (cv_owner == 2'd1) && o_axi_rlast;
  wire cv_wr_end = cv_b_hs && (cv_owner == 2'd2);
  wire cv_any_end = cv_rd_end || cv_wr_end;

  // COVP-001: Supported read beat returned OKAY
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_r_hs && cv_owner == 2'd1 && !cv_unsup && o_axi_rresp == 2'b00)) hits_COVP_001 <= hits_COVP_001 + 1;
  // COVP-002: Supported read beat returned SLVERR from PSLVERR
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_r_hs && cv_owner == 2'd1 && !cv_unsup && o_axi_rresp == 2'b10)) hits_COVP_002 <= hits_COVP_002 + 1;
  // COVP-003: Unsupported read beat returned SLVERR
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_r_hs && cv_owner == 2'd1 && cv_unsup && o_axi_rresp == 2'b10)) hits_COVP_003 <= hits_COVP_003 + 1;
  // COVP-004: Supported write completes with B OKAY
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && !cv_unsup && o_axi_bresp == 2'b00)) hits_COVP_004 <= hits_COVP_004 + 1;
  // COVP-005: Supported write completes with B SLVERR
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && !cv_unsup && o_axi_bresp == 2'b10)) hits_COVP_005 <= hits_COVP_005 + 1;
  // COVP-006: Unsupported write completes with one SLVERR B
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && cv_unsup && o_axi_bresp == 2'b10)) hits_COVP_006 <= hits_COVP_006 + 1;
  // COVP-007: Read FIXED burst of 16 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_rd_end && !cv_unsup && cv_burst == 2'b00 && cv_len == 8'd15)) hits_COVP_007 <= hits_COVP_007 + 1;
  // COVP-008: Write FIXED burst of 16 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && !cv_unsup && cv_burst == 2'b00 && cv_len == 8'd15)) hits_COVP_008 <= hits_COVP_008 + 1;
  // COVP-009: Read INCR burst of 256 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_rd_end && !cv_unsup && cv_burst == 2'b01 && cv_len == 8'd255)) hits_COVP_009 <= hits_COVP_009 + 1;
  // COVP-010: Write INCR burst of 256 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && !cv_unsup && cv_burst == 2'b01 && cv_len == 8'd255)) hits_COVP_010 <= hits_COVP_010 + 1;
  // COVP-011: Read WRAP burst of 16 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_rd_end && !cv_unsup && cv_burst == 2'b10 && cv_len == 8'd15)) hits_COVP_011 <= hits_COVP_011 + 1;
  // COVP-012: Write WRAP burst of 16 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_wr_end && !cv_unsup && cv_burst == 2'b10 && cv_len == 8'd15)) hits_COVP_012 <= hits_COVP_012 + 1;
  // COVP-013: Minimum WRAP burst of 2 beats completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_any_end && !cv_unsup && cv_burst == 2'b10 && cv_len == 8'd1)) hits_COVP_013 <= hits_COVP_013 + 1;
  // COVP-014: Single-beat INCR transaction completes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_any_end && !cv_unsup && cv_burst == 2'b01 && cv_len == 8'd0)) hits_COVP_014 <= hits_COVP_014 + 1;
  // COVP-015: Byte transfer with unaligned start address on APB
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && cv_size == 3'd0 && cv_addr_lo != 2'b00)) hits_COVP_015 <= hits_COVP_015 + 1;
  // COVP-016: Halfword write on upper lanes with PSTRB 1100
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && o_apb_pwrite && cv_size == 3'd1 && cv_addr_lo[1] && o_apb_pstrb == 4'b1100)) hits_COVP_016 <= hits_COVP_016 + 1;
  // COVP-017: Word transfer with unaligned start address
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && cv_size == 3'd2 && cv_addr_lo != 2'b00)) hits_COVP_017 <= hits_COVP_017 + 1;
  // COVP-018: Aligned word write with full strobes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && o_apb_pwrite && cv_size == 3'd2 && o_apb_pstrb == 4'b1111)) hits_COVP_018 <= hits_COVP_018 + 1;
  // COVP-019: Write beat with zero byte strobes
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && o_apb_pwrite && o_apb_pstrb == 4'b0000)) hits_COVP_019 <= hits_COVP_019 + 1;
  // COVP-020: Read request with unsupported size or reserved burst accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_ar_hs && (cv_ar_sz_bad || cv_ar_rsv))) hits_COVP_020 <= hits_COVP_020 + 1;
  // COVP-021: Write request with unsupported size or reserved burst accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_aw_hs && (cv_aw_sz_bad || cv_aw_rsv))) hits_COVP_021 <= hits_COVP_021 + 1;
  // COVP-022: Request with illegal cache value accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((cv_ar_hs && cv_ar_cache_bad) || (cv_aw_hs && cv_aw_cache_bad))) hits_COVP_022 <= hits_COVP_022 + 1;
  // COVP-023: INCR burst crossing a 4-KiB boundary accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((cv_ar_hs && cv_ar_cross) || (cv_aw_hs && cv_aw_cross))) hits_COVP_023 <= hits_COVP_023 + 1;
  // COVP-024: Illegal FIXED or WRAP length accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((cv_ar_hs && cv_ar_len_bad) || (cv_aw_hs && cv_aw_len_bad))) hits_COVP_024 <= hits_COVP_024 + 1;
  // COVP-025: INCR burst ending exactly at 4-KiB boundary is supported
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((cv_ar_hs && !cv_ar_unsup && i_axi_arburst == 2'b01 && cv_ar_end == 32'd4096) ||
                                                          (cv_aw_hs && !cv_aw_unsup && i_axi_awburst == 2'b01 && cv_aw_end == 32'd4096))) hits_COVP_025 <= hits_COVP_025 + 1;
  // COVP-026: RREADY backpressure for 3 or more cycles
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_rvalid && !i_axi_rready && cv_rstall >= 2'd2)) hits_COVP_026 <= hits_COVP_026 + 1;
  // COVP-027: BREADY backpressure for 3 or more cycles
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (o_axi_bvalid && !i_axi_bready && cv_bstall >= 2'd2)) hits_COVP_027 <= hits_COVP_027 + 1;
  // COVP-028: Request held pending while a transaction owns the bridge
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_owner != 2'd0 && ((i_axi_arvalid && !o_axi_arready) || (i_axi_awvalid && !o_axi_awready)))) hits_COVP_028 <= hits_COVP_028 + 1;
  // COVP-029: WVALID presented before AW accepted
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (i_axi_wvalid && cv_owner == 2'd0 && !cv_aw_hs)) hits_COVP_029 <= hits_COVP_029 + 1;
  // COVP-030: APB wait states of 3 or more cycles
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_acc && !i_apb_pready && cv_await >= 6'd2)) hits_COVP_030 <= hits_COVP_030 + 1;
  // COVP-031: Long APB wait of 32 or more cycles
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_acc && !i_apb_pready && cv_await >= 6'd32)) hits_COVP_031 <= hits_COVP_031 + 1;
  // COVP-032: Write continues cleanly after an earlier PSLVERR beat
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && o_apb_pwrite && !i_apb_pslverr && cv_wr_err)) hits_COVP_032 <= hits_COVP_032 + 1;
  // COVP-033: Read burst continues with OKAY beat after an earlier error beat
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_r_hs && cv_owner == 2'd1 && !cv_unsup && o_axi_rresp == 2'b00 && cv_rd_err)) hits_COVP_033 <= hits_COVP_033 + 1;
  // COVP-034: Reset applied during activity then idle after reset
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_rst_flag && cv_owner == 2'd0 && !o_apb_psel && !o_axi_bvalid && !o_axi_rvalid)) hits_COVP_034 <= hits_COVP_034 + 1;
  // COVP-035: First tie after reset won by AR
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_owner == 2'd0 && cv_ar_hs && i_axi_awvalid && cv_last_done == 2'd0)) hits_COVP_035 <= hits_COVP_035 + 1;
  // COVP-036: Tie won by AW after a completed read
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_owner == 2'd0 && cv_aw_hs && i_axi_arvalid && cv_last_done == 2'd1)) hits_COVP_036 <= hits_COVP_036 + 1;
  // COVP-037: Tie won by AR after a completed write
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_owner == 2'd0 && cv_ar_hs && i_axi_awvalid && cv_last_done == 2'd2)) hits_COVP_037 <= hits_COVP_037 + 1;
  // COVP-038: Maximum ID value echoed on R or B
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && ((cv_r_hs && o_axi_rid == {PARA_AXI_ID_W{1'b1}}) || (cv_b_hs && o_axi_bid == {PARA_AXI_ID_W{1'b1}}))) hits_COVP_038 <= hits_COVP_038 + 1;
  // COVP-039: PPROT all ones on completed APB transfer
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_done && o_apb_pprot == 3'b111)) hits_COVP_039 <= hits_COVP_039 + 1;
  // COVP-040: WRAP burst address wraps back to lower boundary
  always_ff @(posedge i_clk_axi) if (!(!i_rst_n_axi) && (cv_apb_setup && cv_owner != 2'd0 && !cv_unsup && cv_burst == 2'b10 && cv_acnt != 9'd0 && o_apb_paddr < cv_last_paddr)) hits_COVP_040 <= hits_COVP_040 + 1;

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
