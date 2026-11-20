// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module m_spi_master #(
  parameter int PARA_SPI_CLK_DIV = 4
) (
  input  logic                        i_clk,
  input  logic                        i_rst_n,
  input  logic                        i_cmd_valid,
  output logic                        o_cmd_ready,
  input  logic [7:0]                  i_cmd_data,
  input  logic                        i_cmd_last,
  output logic                        o_rsp_valid,
  input  logic                        i_rsp_ready,
  output logic [7:0]                  o_rsp_data,
  output logic                        o_sclk,
  output logic                        o_mosi,
  input  logic                        i_miso,
  output logic                        o_cs_n,
  input  logic                        i_cpol,
  input  logic                        i_cpha
);
  assign o_cmd_ready = '0;
  assign o_rsp_valid = '0;
  assign o_rsp_data = '0;
  assign o_sclk = '0;
  assign o_mosi = '0;
  assign o_cs_n = '0;
endmodule
