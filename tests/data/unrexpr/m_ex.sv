// Test design for nnc/unrexpr.py (ROADMAP 24): expression points in each context the module reads.
module m_ex #(
  parameter bit Gen = 1'b1
) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       a,
  input  logic       b,
  input  logic [3:0] v,
  output logic       y1,
  output logic       y2,
  output logic       y3,
  output logic       y4,
  output logic       q
);
  logic t;
  function automatic logic f(input logic x);
    return x & a;
  endfunction
  assign y1 = a & b;
  if (Gen) begin : gen_y
    logic g;
    assign g = a | b;
    assign y2 = g & b;
  end else begin : gen_n
    assign y2 = 1'b0;
  end
  always_comb begin
    t = a ^ b;
    y3 = t & b;
  end
  always_comb begin
    y4 = 1'b0;
    for (int i = 0; i < 4; i++) y4 = y4 | (v[i] & b);
  end
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else if (a && f(b)) q <= ~q;
  end
  typedef struct packed { logic x; logic [2:0] y; } s_t;
  s_t s; logic [8:1] w; logic [3:0][1:0] pa;
  assign s = {a, v[2:0]}; assign w = {v, v}; assign pa = {v, v};
  logic y5, y6, y7, y8;
  assign y5 = s[3] & b;
  assign y6 = w[1] & b;
  assign y7 = pa[3][0] & b;
  assign y8 = v[2] & b;
endmodule
