module nnc_chk_flow #(
  parameter int PARA_SPI_CLK_DIV = 4
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_cmd_valid,
  input  logic                        o_cmd_ready,
  input  logic [7:0]                  i_cmd_data,
  input  logic                        i_cmd_last,
  input  logic                        o_rsp_valid,
  input  logic                        i_rsp_ready,
  input  logic [7:0]                  o_rsp_data,
  input  logic                        o_sclk,
  input  logic                        o_mosi,
  input  logic                        i_miso,
  input  logic                        o_cs_n,
  input  logic                        i_cpol,
  input  logic                        i_cpha
);

  int unsigned fails_CHK_010 = 0;
  int unsigned hits_CHK_010 = 0;

  localparam int unsigned XFER_CYC = 16 * PARA_SPI_CLK_DIV;

  logic        flow_hs;
  logic        flow_busy;
  logic        flow_last_q;
  logic        flow_pause;
  logic        flow_pause_q;
  int unsigned flow_cnt;
  // NNC verification fix (fix-verif, triage B): CPOL_b = i_cpol captured at the first acceptance edge of the
  // burst (REQ-MODE-001, term CPOL_b). REQ-FLOW-003 requires o_sclk = CPOL_b in Pause, not the current i_cpol,
  // which may differ during the ENV-003 error test (REQ-MODE-003, REQ-ERR-001).
  logic        flow_cpol_b;

  assign flow_hs = i_cmd_valid && o_cmd_ready;

  always_ff @(posedge i_clk) begin
    if (!i_rst_n) begin
      flow_busy    <= 1'b0;
      flow_last_q  <= 1'b0;
      flow_pause   <= 1'b0;
      flow_pause_q <= 1'b0;
      flow_cnt     <= 0;
      flow_cpol_b  <= 1'b0;
    end else begin
      flow_pause_q <= flow_pause;
      // NNC verification fix (fix-verif, triage B): burst start = handshake with o_cs_n=1 in the cycle ending at
      // the acceptance edge; capture CPOL_b there (REQ-MODE-001).
      if (flow_hs && o_cs_n) flow_cpol_b <= i_cpol;
      if (flow_hs) begin
        flow_busy   <= 1'b1;
        flow_cnt    <= 0;
        flow_last_q <= i_cmd_last;
        flow_pause  <= 1'b0;
      end else if (flow_busy) begin
        if (flow_cnt == XFER_CYC - 1) begin
          flow_busy <= 1'b0;
          if (!flow_last_q) flow_pause <= 1'b1;
        end else begin
          flow_cnt <= flow_cnt + 1;
        end
      end
    end
  end

  // CHK-010: Pause entry and Pause outputs (SPI-7.8-02, SPI-7.8-03, SPI-3-05, SPI-1.2-08, SPI-14-20, SPI-8-13)
  // NNC verification fix (fix-verif, triage B): o_sclk compared with the captured CPOL_b (REQ-FLOW-003,
  // contract CHK-010 "o_sclk=CPOL_b") instead of the current i_cpol input.
  a_CHK_010: assert property (@(posedge i_clk) disable iff (!i_rst_n)
    flow_pause |-> ((o_cs_n == 1'b0) && (o_sclk == flow_cpol_b) &&
                    (!flow_pause_q || ($stable(o_sclk) && $stable(o_mosi)))))
    else begin fails_CHK_010++; $display("NNC_FAIL CHK-010 @%0t", $time); end
  always_ff @(posedge i_clk) if (!(!i_rst_n) && (flow_pause)) hits_CHK_010 <= hits_CHK_010 + 1;

  final begin
    $display("NNC_CHECK CHK-010 hits=%0d fails=%0d", hits_CHK_010, fails_CHK_010);
  end
endmodule
