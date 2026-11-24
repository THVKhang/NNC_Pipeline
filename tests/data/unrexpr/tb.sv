// Short stimulus for m_ex.sv: writes the coverage.dat of tests/data/unrexpr (b stays 0).
module nnc_tb_top;
  logic clk = 0, rst_n = 0, a = 0, b = 0;
  logic [3:0] v = 0;
  logic y1, y2, y3, y4, q;
  m_ex u_dut (.*);
  always #5 clk = ~clk;
  initial begin
    #12 rst_n = 1;
    repeat (4) begin
      @(negedge clk) a = ~a;
      v = v + 1;
    end
    $finish;
  end
endmodule
