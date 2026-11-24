module m_br (
  input  logic       clk,
  input  logic       rst_n,
  input  logic [1:0] s,
  output logic       q,
  output logic       q2
);
  logic [1:0] st;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      q  <= 1'b0;
      st <= 2'd0;
    end else begin
      if (s == 2'd3) q <= 1'b1;
      else if (st == 2'd2) q <= 1'b0;
      case (st)
        2'd0: st <= 2'd1;
        2'd1: begin st <= 2'd0; end
        default: st <= 2'd0;
      endcase
    end
  end
  always_comb begin
    q2 = 1'b0;
    case (s)
      2'd0, 2'd1: q2 = 1'b1;
      default: ;
    endcase
    if (st == 2'd3) q2 = 1'b1; // a comment ; with a semicolon
  end
endmodule
