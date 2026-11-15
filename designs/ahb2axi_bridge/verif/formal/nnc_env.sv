// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Encodings
  // ---------------------------------------------------------------------------
  localparam logic [1:0] LPARA_HTRANS_IDLE   = 2'b00;
  localparam logic [1:0] LPARA_HTRANS_BUSY   = 2'b01;
  localparam logic [1:0] LPARA_HTRANS_NONSEQ = 2'b10;
  localparam logic [1:0] LPARA_HTRANS_SEQ    = 2'b11;
  localparam logic [2:0] LPARA_HBURST_SINGLE = 3'b000;

  // ---------------------------------------------------------------------------
  // AHB helper state (derived from interface pins only)
  // ---------------------------------------------------------------------------
  // ahb_dp_sel  : this Subordinate owns the current AHB data phase
  // ahb_dp_wr   : the current data phase is a NONSEQ/SEQ write to this Subordinate
  // ahb_in_burst: last accepted address phase at this Subordinate was part of a
  //               non-SINGLE burst (NONSEQ/SEQ/BUSY with HBURST != SINGLE)
  logic ahb_dp_sel   = 1'b0;
  logic ahb_dp_wr    = 1'b0;
  logic ahb_in_burst = 1'b0;

  always @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      ahb_dp_sel   <= 1'b0;
      ahb_dp_wr    <= 1'b0;
      ahb_in_burst <= 1'b0;
    end else if (i_ahb_hready) begin
      ahb_dp_sel   <= i_ahb_hsel;
      ahb_dp_wr    <= i_ahb_hsel && i_ahb_htrans[1] && i_ahb_hwrite;
      ahb_in_burst <= i_ahb_hsel && (i_ahb_htrans != LPARA_HTRANS_IDLE)
                      && (i_ahb_hburst != LPARA_HBURST_SINGLE);
    end
  end

  // ---------------------------------------------------------------------------
  // AXI helper state (derived from interface pins only)
  // ---------------------------------------------------------------------------
  wire axi_aw_hs = o_axi_awvalid && i_axi_awready;
  wire axi_wl_hs = o_axi_wvalid  && i_axi_wready && o_axi_wlast;
  wire axi_b_hs  = i_axi_bvalid  && o_axi_bready;
  wire axi_ar_hs = o_axi_arvalid && i_axi_arready;
  wire axi_r_hs  = i_axi_rvalid  && o_axi_rready && i_axi_rlast;

  logic [3:0] axi_aw_pend = 4'd0;  // AW handshakes without B response
  logic [3:0] axi_wl_pend = 4'd0;  // WLAST handshakes without B response
  logic [3:0] axi_ar_pend = 4'd0;  // AR handshakes without final R beat
  logic [2:0] axi_aw_id_q = 3'd0;  // AWID of the single outstanding write
  logic [2:0] axi_ar_id_q = 3'd0;  // ARID of the single outstanding read
  logic       axi_aw_id_v = 1'b0;  // exactly one write outstanding, ID known
  logic       axi_ar_id_v = 1'b0;  // exactly one read outstanding, ID known

  wire [3:0] axi_aw_pend_nxt = axi_aw_pend + {3'd0, axi_aw_hs} - {3'd0, axi_b_hs};
  wire [3:0] axi_wl_pend_nxt = axi_wl_pend + {3'd0, axi_wl_hs} - {3'd0, axi_b_hs};
  wire [3:0] axi_ar_pend_nxt = axi_ar_pend + {3'd0, axi_ar_hs} - {3'd0, axi_r_hs};

  always @(posedge i_clk_core) begin
    if (!i_rst_n_core) begin
      axi_aw_pend <= 4'd0;
      axi_wl_pend <= 4'd0;
      axi_ar_pend <= 4'd0;
      axi_aw_id_q <= 3'd0;
      axi_ar_id_q <= 3'd0;
      axi_aw_id_v <= 1'b0;
      axi_ar_id_v <= 1'b0;
    end else begin
      axi_aw_pend <= axi_aw_pend_nxt;
      axi_wl_pend <= axi_wl_pend_nxt;
      axi_ar_pend <= axi_ar_pend_nxt;
      // write ID tracking
      if (axi_aw_pend_nxt == 4'd0) begin
        axi_aw_id_v <= 1'b0;
      end else if (axi_aw_hs && (axi_aw_pend_nxt == 4'd1)) begin
        axi_aw_id_q <= o_axi_awid;
        axi_aw_id_v <= 1'b1;
      end else if (axi_aw_pend_nxt != 4'd1) begin
        axi_aw_id_v <= 1'b0;
      end
      // read ID tracking
      if (axi_ar_pend_nxt == 4'd0) begin
        axi_ar_id_v <= 1'b0;
      end else if (axi_ar_hs && (axi_ar_pend_nxt == 4'd1)) begin
        axi_ar_id_q <= o_axi_arid;
        axi_ar_id_v <= 1'b1;
      end else if (axi_ar_pend_nxt != 4'd1) begin
        axi_ar_id_v <= 1'b0;
      end
    end
  end

  // ---------------------------------------------------------------------------
  // Reset-time input values
  // ---------------------------------------------------------------------------
  // ENV-01: While i_rst_n_core is low the AHB manager drives HSEL=0, HTRANS=IDLE, HWRITE=0, HBURST=SINGLE, HMASTLOCK=0 (AA-T1.7.2.2-03)
  always @(*) begin
    if (!i_rst_n_core)
      assume (!i_ahb_hsel && (i_ahb_htrans == LPARA_HTRANS_IDLE) && !i_ahb_hwrite
              && (i_ahb_hburst == LPARA_HBURST_SINGLE) && !i_ahb_hmastlock);
  end

  // ENV-02: The AXI Subordinate (reset consistently with the bridge) keeps BVALID and RVALID low during reset (AA-T1.7.2.2-17, AA-T1.7.2.2-24, AA-12-14)
  always @(*) begin
    if (!i_rst_n_core)
      assume (!i_axi_bvalid && !i_axi_rvalid);
  end

  // ---------------------------------------------------------------------------
  // AHB5 manager / interconnect obligations
  // ---------------------------------------------------------------------------
  // ENV-03: During a data phase owned by this Subordinate, the global HREADY equals this Subordinate's HREADYOUT (AHB5 multiplexor) (AA-6.1-01, AA-T1.7.3.1-01, AA-12-16)
  always @(*) begin
    if (i_rst_n_core && ahb_dp_sel)
      assume (i_ahb_hready == o_ahb_hreadyout);
  end

  // ENV-04: HWDATA/HWSTRB of a write data phase to this Subordinate stay stable while the data phase is extended by HREADY=0 (AA-T1.7.3.1-02, AA-6.1-01)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && $past(i_rst_n_core) && ahb_dp_wr && !$past(i_ahb_hready))
      assume ($stable(i_ahb_hwdata) && $stable(i_ahb_hwstrb));
  end

  // ENV-05: SEQ and BUSY are presented to this Subordinate only inside a non-SINGLE burst (first beat of a burst is NONSEQ) (AA-6.1-01, AA-T1.7.3.1-01, AA-3-03)
  always @(*) begin
    if (i_rst_n_core && i_ahb_hsel
        && ((i_ahb_htrans == LPARA_HTRANS_SEQ) || (i_ahb_htrans == LPARA_HTRANS_BUSY)))
      assume (ahb_in_burst);
  end

  // ---------------------------------------------------------------------------
  // AXI4 Subordinate obligations
  // ---------------------------------------------------------------------------
  // ENV-06: BVALID is asserted only after both the AW handshake and the final (WLAST) W handshake of an outstanding write (AA-6.1-02, AA-3-21, AA-T1.7.3.2-02)
  always @(*) begin
    if (i_rst_n_core && i_axi_bvalid)
      assume ((axi_aw_pend != 4'd0) && (axi_wl_pend != 4'd0));
  end

  // ENV-07: Once asserted, BVALID with BID/BRESP is held stable until BREADY (AA-T1.7.2.2-18, AA-6.1-02)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && $past(i_rst_n_core) && $past(i_axi_bvalid && !o_axi_bready))
      assume (i_axi_bvalid && $stable(i_axi_bid) && $stable(i_axi_bresp));
  end

  // ENV-08: BID returns the AWID of the outstanding write transaction (AA-6.1-02, AA-T1.7.3.2-05, AA-9-13)
  always @(*) begin
    if (i_rst_n_core && i_axi_bvalid && axi_aw_id_v)
      assume (i_axi_bid == axi_aw_id_q);
  end

  // ENV-09: RVALID is asserted only after the AR handshake of an outstanding read (AA-6.1-02, AA-5.3-01, AA-T1.7.3.4-01)
  always @(*) begin
    if (i_rst_n_core && i_axi_rvalid)
      assume (axi_ar_pend != 4'd0);
  end

  // ENV-10: Once asserted, RVALID with RID/RDATA/RRESP/RLAST is held stable until RREADY (AA-T1.7.2.2-25, AA-6.1-02)
  always @(posedge i_clk_core) begin
    if (i_rst_n_core && $past(i_rst_n_core) && $past(i_axi_rvalid && !o_axi_rready))
      assume (i_axi_rvalid && $stable(i_axi_rid) && $stable(i_axi_rdata)
              && $stable(i_axi_rresp) && $stable(i_axi_rlast));
  end

  // ENV-11: RID returns the ARID of the outstanding read transaction (AA-6.1-02, AA-T1.7.3.2-05, AA-9-13)
  always @(*) begin
    if (i_rst_n_core && i_axi_rvalid && axi_ar_id_v)
      assume (i_axi_rid == axi_ar_id_q);
  end

  // ENV-12: Every R beat of a single-beat read carries RLAST=1 (AA-T1.7.2.2-23, AA-5.4-07, AA-T1.7.3.2-03, AA-5.3-01)
  always @(*) begin
    if (i_rst_n_core && i_axi_rvalid)
      assume (i_axi_rlast);
  end
endmodule
