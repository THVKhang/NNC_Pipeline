// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
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

  // ---------------------------------------------------------------------------
  // Helper: counts i_clk cycles from time zero (saturates at 2). It is not
  // cleared by i_rst_n because it only tracks the power-on reset from
  // time zero (SPI-12-12).
  // ---------------------------------------------------------------------------
  reg [1:0] env_por_cnt = 2'd0;
  always @(posedge i_clk) begin
    if (env_por_cnt != 2'd2)
      env_por_cnt <= env_por_cnt + 2'd1;
  end

  // ENV-01: i_cmd_valid is 0 whenever i_rst_n is 0 (SPI-5-02, SPI-12-03)
  always @(*) begin
    if (!i_rst_n)
      assume (!i_cmd_valid);
  end

  // ENV-02: i_rst_n is held at 0 from time zero for at least the first 2 i_clk cycles (SPI-12-12)
  always @(*) begin
    if (env_por_cnt != 2'd2)
      assume (!i_rst_n);
  end
endmodule
