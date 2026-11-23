module nnc_chk_pcpi (
  input  logic                        clk,
  input  logic                        resetn,
  input  logic                        pcpi_valid,
  input  logic [31:0]                 pcpi_insn,
  input  logic [31:0]                 pcpi_rs1,
  input  logic [31:0]                 pcpi_rs2,
  input  logic                        pcpi_wr,
  input  logic [31:0]                 pcpi_rd,
  input  logic                        pcpi_wait,
  input  logic                        pcpi_ready
);

  int unsigned fails_CHK_001 = 0;
  int unsigned hits_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned hits_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  int unsigned hits_CHK_003 = 0;

  // CHK-001: pcpi_wait stays asserted until pcpi_ready (PD-T1.1-06)
  a_CHK_001: assert property (@(posedge clk) disable iff (!resetn)
    (pcpi_valid && pcpi_wait && !pcpi_ready) |=> (pcpi_wait || pcpi_ready))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_valid && pcpi_wait && !pcpi_ready)) hits_CHK_001 <= hits_CHK_001 + 1;

  // CHK-002: pcpi_wr only together with pcpi_ready (PD-T1.1-03)
  a_CHK_002: assert property (@(posedge clk) disable iff (!resetn)
    pcpi_wr |-> pcpi_ready)
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge clk) if (!(!resetn) && (pcpi_wr)) hits_CHK_002 <= hits_CHK_002 + 1;

  // CHK-003: pcpi_ready only in response to an outstanding pcpi_valid (PD-T1.1-02)
  // Note: no disable iff, since the check also requires resetn=1 when ready=1.
  a_CHK_003: assert property (@(posedge clk)
    pcpi_ready |-> (resetn && pcpi_valid))
    else begin fails_CHK_003++; $display("NNC_FAIL CHK-003 @%0t", $time); end
  always_ff @(posedge clk) if (pcpi_ready) hits_CHK_003 <= hits_CHK_003 + 1;

  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", hits_CHK_001, fails_CHK_001);
    $display("NNC_CHECK CHK-002 hits=%0d fails=%0d", hits_CHK_002, fails_CHK_002);
    $display("NNC_CHECK CHK-003 hits=%0d fails=%0d", hits_CHK_003, fails_CHK_003);
  end
endmodule
