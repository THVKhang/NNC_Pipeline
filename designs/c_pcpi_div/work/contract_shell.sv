// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module picorv32_pcpi_div (
  input  logic                        clk,
  input  logic                        resetn,
  input  logic                        pcpi_valid,
  input  logic [31:0]                 pcpi_insn,
  input  logic [31:0]                 pcpi_rs1,
  input  logic [31:0]                 pcpi_rs2,
  output logic                        pcpi_wr,
  output logic [31:0]                 pcpi_rd,
  output logic                        pcpi_wait,
  output logic                        pcpi_ready
);
  assign pcpi_wr = '0;
  assign pcpi_rd = '0;
  assign pcpi_wait = '0;
  assign pcpi_ready = '0;
endmodule
