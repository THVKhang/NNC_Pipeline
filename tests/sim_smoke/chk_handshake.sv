// Smoke test of the simulation layer: two rules extracted from the AXI specification
// (IHI0022C chapter 3) written as SVA, each with a fail counter (assert action block) and a hit
// counter (principle PR-4: an assertion that never fired proves nothing).
//
//   R-3.1-05  Once VALID is asserted it must remain asserted until the handshake occurs.  (3.1:s12)
//   R-3.1-03  The source must keep the information stable until READY is HIGH.          (3.1:s9)
//
// Facts about the simulator (Verilator 5.055, checked 2026-11-07) that this pattern relies on.
// A comment must not start with the word "verilator": the tool reads it as a pragma.
//   * the else action block of `assert property` runs and the simulation continues;
//   * the action statement of `cover property` is NOT executed, so hits are counted by an
//     always_ff on the same antecedent; the cover property stays for the coverage database.
module chk_handshake #(
  parameter int W = 8
) (
  input logic         clk,
  input logic         rst_n,
  input logic         valid,
  input logic         ready,
  input logic [W-1:0] data
);
  int unsigned fails_valid_hold  = 0;
  int unsigned hits_valid_hold   = 0;
  int unsigned fails_data_stable = 0;
  int unsigned hits_data_stable  = 0;

  wire wait_state = valid && !ready;   // antecedent shared by both rules

  // R-3.1-05 (3.1:s12)
  a_valid_hold: assert property (@(posedge clk) disable iff (!rst_n) wait_state |=> valid)
    else begin
      fails_valid_hold++;
      $display("ASSERT FAIL R-3.1-05 VALID dropped before handshake @%0t", $time);
    end
  c_valid_hold: cover property (@(posedge clk) disable iff (!rst_n) wait_state);

  // R-3.1-03 (3.1:s9)
  a_data_stable: assert property (@(posedge clk) disable iff (!rst_n) wait_state |=> $stable(data))
    else begin
      fails_data_stable++;
      $display("ASSERT FAIL R-3.1-03 data changed before READY @%0t", $time);
    end
  c_data_stable: cover property (@(posedge clk) disable iff (!rst_n) wait_state);

  // Hit counters (antecedent true at a sampled edge).
  always_ff @(posedge clk) begin
    if (rst_n && wait_state) begin
      hits_valid_hold  <= hits_valid_hold + 1;
      hits_data_stable <= hits_data_stable + 1;
    end
  end
endmodule

// Top level driven by cocotb (acts as the source and the destination).
module tb_top (
  input logic       clk,
  input logic       rst_n,
  input logic       valid,
  input logic       ready,
  input logic [7:0] data
);
  chk_handshake #(.W(8)) u_chk (.*);
endmodule
