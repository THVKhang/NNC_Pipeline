# Verification fix candidate: x_fixverif_uart

Agent A17 (no RTL) proposed changes for 6 fault(s) judged B by triage. Status: **candidate**. Nothing in verif/ changes until `nnc fix-verif x_fixverif_uart --apply`, and then gate G3 must be approved again.

## Faults (as A17 saw them)

1. **CHK-002 – Output values while reset is asserted (7 fails, one per run, always @0 ps; sim.log:122, sim_runs/*.log)**
   - specification: spec/uart_lite_Design_Specification.md:106 REQ-RST-002 "While i_rst_n is 0, the outputs shall have these values: o_txd = 1, o_tx_ready = 1, o_rx_valid = 0, o_rx_data = 0, o_rx_frame_err = 0, o_rx_overrun = 0." Line 104 REQ-RST-001: "When i_rst_n becomes 0, every flip-flop ... shall take its reset value at once". Line 358 ENV-002: "The environment shall hold i_rst_n at 0 for at least 2 cycles of i_clk at the start of a simulation." contract.json:705 (UL-12.1-02): "Applied as a stimulus constraint: every simulation starts with i_rst_n=0 for at least 2 i_clk cycles." The spec does not say what th
   - verification: Env.start() drives i_rst_n=1 at t=0 (verif/tests/test_uart_lite.py:144) and starts the clock (146). It waits two rising edges (149-152) and a falling edge (158). Only then does it call reset(), which waits another rising edge plus 0.3P and drives i_rst_n=0 (185-189), at about 46 ns. The SVA (verif/sva/nnc_chk_reset.sv:22-24) samples at every posedge with !i_rst_n. At the t=0 posedge the sampled i_rst_n is still the simulator default 0, because cocotb's write of 1 happens in the same time step. The sampled outputs are the un-reset 0 values, so o_txd===1 fails. The expected values come straight 

2. **CHK-003 – Delivery into an empty holding register at V=M+2 (83 fails; first @318400000 ps = 318.4 us in test_chk_021_low_at_release)**
   - specification: spec:172 REQ-RX-003 "While idle, the receiver shall detect a start bit at edge T0 if and only if s(T0-1) = 1 and s(T0) = 0." spec:222 REQ-FE-003 "After a frame with a frame error, the receiver shall not detect a new start bit until s has been 1 at one edge and 0 at the next edge ... so a line held at 0 produces exactly one frame." spec:321 REQ-ERR-001 and spec:326 REQ-ERR-003: a line that stays low gives exactly one 0x00 with o_rx_frame_err=1. D-005 (spec:412): "A 1-to-0 transition is required, so a break gives one byte." spec:200 REQ-RX-020 sets the load at V. The contract RX model (contract.
   - verification: Stimulus: test_chk_021 holds i_rxd=0 through reset release and for 40N cycles (test_uart_lite.py:961-967). test_chk_028(b) holds a 50N-cycle break with i_rx_ready=1 (1109-1112). test_chk_029/regression send frames with stop=0 followed by a gap of at least 1 (rx_random, 368-377). Expected value: the SVA reference model in verif/sva/nnc_chk_rx.sv:64-68 starts a frame whenever the model is idle and `!i_rxd`. It has no previous-sample term, so it does not check s(T0-1)=1. After a frame that ends with the line still low (break, or a stop=0 frame), it restarts at M+1 and produces phantom frames ever

3. **CHK-005 – Overrun drop at V keeps the held byte; one-cycle pulse (24 fails; first @993370000 ps = 993.37 us in test_chk_028_idle_break part (c); 0 fails in wide.s1)**
   - specification: spec:226 REQ-OVR-001 drops the byte "At the delivery edge V of a completed frame, if o_rx_valid = 1 and i_rx_ready = 0". spec:228 REQ-OVR-002 gives a one-cycle o_rx_overrun pulse. spec:232 REQ-OVR-004: "o_rx_overrun shall be 0 in every cycle except the cycle after an edge at which a byte is dropped." Only a completed frame, started at a real T0 with s(T0-1)=1 and s(T0)=0 (spec:172 REQ-RX-003), has a V. spec:222 REQ-FE-003 / spec:321 REQ-ERR-001: "a line held at 0 produces exactly one frame" ("deliver the byte 0x00 ... or drop it with an overrun pulse").
   - verification: test_chk_028(c) (test_uart_lite.py:1122-1133): holds 0x77 with i_rx_ready=0, drives i_rxd=0 for long(50) cycles, then 1. It expects exactly one overrun pulse (1132) and 0x77 held (1133); this Python check passes. The SVA CHK-005 (verif/sva/nnc_chk_rx.sv:109-111) fires on every model V with o_rx_valid=1 && !i_rx_ready. The model (64-68) re-detects a 'start' on the still-low line at M+1 because it has no s(T0-1)=1 term, so it creates phantom V's every H+9N+1 cycles. Fails at 993370, 996430, 999490, 1002550 ns are 3060 ns = 153 cycles apart (N=16). In wide.s1 the low time is capped at 12N (test_u

4. **CHK-006 – o_rx_overrun only after a drop edge (24 fails; first @993370000 ps, same timestamps as CHK-005; 0 fails in wide.s1)**
   - specification: spec:232 REQ-OVR-004: "o_rx_overrun shall be 0 in every cycle except the cycle after an edge at which a byte is dropped." spec:226 REQ-OVR-001: a drop happens only "At the delivery edge V of a completed frame". spec:172 REQ-RX-003 (start needs s(T0-1)=1, s(T0)=0) and spec:222 REQ-FE-003 / D-005 (spec:412): a held-low line gives one frame. spec:236 REQ-OVR-006: glitches and reset-cut frames never pulse.
   - verification: The SVA (verif/sva/nnc_chk_rx.sv:85-94, 115-117) computes `drop_q <= mdl_v && o_rx_valid && !i_rx_ready` and asserts `o_rx_overrun == drop_q`. mdl_v comes from the faulty model at lines 64-68, which starts on any low sample while idle. On a line held low after the first frame it creates phantom drop edges every H+9N+1 cycles (993370, 996430, 999490, 1002550 ns; 153 cycles apart at N=16). Stimulus is test_chk_028(c), test_uart_lite.py:1122-1133. That test's own assertion of exactly one overrun pulse (1132) passes.

5. **CHK-009 – Empty register: data/flag stable unless a byte is loaded (80 fails; first @328460000 ps; fails come in pairs at one timestamp)**
   - specification: spec:210 REQ-RX-025: "o_rx_data and o_rx_frame_err shall change only at an edge where a new byte is loaded, or on reset." spec:212 REQ-RX-026: i_rx_ready has no effect while o_rx_valid=0. spec:200 REQ-RX-020: a load happens at V=M+2 of a completed frame. spec:180 REQ-RX-007 and spec:192 REQ-RX-013: a new start is detected at any edge with s(T0-1)=1, s(T0)=0 once the receiver is idle.
   - verification: The SVA (verif/sva/nnc_chk_rx.sv:133-141) has two properties, a_CHK_009 and a_CHK_009_b. Both increment fails_CHK_009 and print the same message, which explains the paired fails. Both assume no load unless the model has mdl_v/load_q. The faulty model (64-68) is busy with a phantom frame that started on a still-low line (no s(T0-1)=1 check), so it misses the real falling edge of the next frame. Timing confirms this. In chk_021, with R1 ≈ 312240 ns, phantom starts fall at R1+0/153/306/459/612. The phantom at R1+612 spans the real start of 0xA5 at R1+656, and the real V+1 = R1+811 → 328460 ns, th

6. **CHK-010 – Transmit handshake, acceptance condition and idle values (21 fails = 3 per run, always @0, @20000, @40000 ps)**
   - specification: spec:140 REQ-TX-003 "While the transmitter is idle (no frame in progress), o_tx_ready shall be 1." spec:164 REQ-TX-014 "While the transmitter is idle, o_txd shall be 1." spec:358 ENV-002 "The environment shall hold i_rst_n at 0 for at least 2 cycles of i_clk at the start of a simulation." contract.json:705 says this is applied as a stimulus constraint. The idle state is only defined after reset (REQ-RST-009, spec:120); the spec says nothing about outputs before the first reset.
   - verification: Env.start() drives i_rst_n=1 at t=0 (test_uart_lite.py:144) and starts the clock (146). It then waits RisingEdge, RisingEdge, FallingEdge (149-158), and reset() waits another RisingEdge plus 0.3P before driving i_rst_n=0 (185-189). The SVA (verif/sva/nnc_chk_tx.sv:38-52, 62-65) has tx_pos=0 (2-state default) and is not disabled because i_rst_n=1. It expects idle values o_tx_ready=1 && o_txd=1 (part b), gets 0/0, and fails at exactly those three edges. The Python monitor does not see these edges: it is not armed until the first reset (test_uart_lite.py:251-259).

## Changes

- `verif/sva/nnc_chk_rx.sv` (faults [2, 3, 4, 5]): The SVA RX reference model started a frame on any low sample while it was idle. It had no s(T0-1)=1 term. On a line still low after a frame (a break, or a stop=0 frame followed by low), it restarted at M+1 and made phantom frames every H+9N+1 edges. Their phantom V edges then made CHK-003, CHK-005, CHK-006 and CHK-009 expect loads and drops that the spec forbids. This change adds a model register mdl_prev for s(E-1). It resets to 1 (REQ-RST-010) and is updated with i_rxd at every non-reset edge. The idle start condition is now mdl_prev && !i_rxd. This is the same rule the Python model uses. The assertions themselves are unchanged and none is relaxed. The model is now more exact. — spec/uart_lite_Design_Specification.md:172 REQ-RX-003, spec/uart_lite_Design_Specification.md:222 REQ-FE-003, spec/uart_lite_Design_Specification.md:321 REQ-ERR-001, spec/uart_lite_Design_Specification.md:326 REQ-ERR-003, spec/uart_lite_Design_Specification.md:122 REQ-RST-010, spec/uart_lite_Design_Specification.md:112 REQ-RST-005, spec/uart_lite_Design_Specification.md:192 REQ-RX-013, spec/uart_lite_Design_Specification.md:226 REQ-OVR-001, spec/uart_lite_Design_Specification.md:232 REQ-OVR-004, spec/uart_lite_Design_Specification.md:210 REQ-RX-025, spec/uart_lite_Design_Specification.md:412 D-005, contract.json:781 RX reference model (s(T0-1)=1 and s(T0)=0)
- `verif/tests/test_uart_lite.py` (faults [1, 6]): The previous fix only ran its reset-first start sequence when get_sim_time('step') == 0. In most runs the first test (test_chk_014 / test_chk_015) is not verifiable for that run's N and returns right away. cocotb lets simulated time move between tests, so the first test that really calls Env.start() begins after t=0. The time==0 test was therefore False and the old sequence ran instead: i_rst_n=1 written at the same moment as the first rising clock edge. That gave the same CHK-002 fail at the first edge and the same 3 CHK-010 fails at the first 3 edges as before. This also explains why only 5 of 7 runs still failed: in the N=4 runs, test_chk_014 starts at t=0. The fix replaces the time test with a module-level flag that is True only for the first Env.start() of the simulation, whatever the time. That first start then always does this: clock held low; i_rst_n given a real 1->0 assertion before the clock starts (REQ-RST-001), so every rising edge sees i_rst_n=0 and reset outputs (REQ-RST-002); i_rst_n held at 0 for at least 2 rising edges (ENV-002, contract UL-12.1-02); release at a falling edge (ENV-001). No assertion, expected value or check reference is changed. Later tests keep their original sequence. — spec/uart_lite_Design_Specification.md:104 REQ-RST-001, spec/uart_lite_Design_Specification.md:106 REQ-RST-002, spec/uart_lite_Design_Specification.md:120 REQ-RST-009, spec/uart_lite_Design_Specification.md:140 REQ-TX-003, spec/uart_lite_Design_Specification.md:164 REQ-TX-014, spec/uart_lite_Design_Specification.md:356 ENV-001, spec/uart_lite_Design_Specification.md:358 ENV-002, contract.json:705 UL-12.1-02

## Attempts

- attempt 0: files sva/nnc_chk_rx.sv, tests/test_uart_lite.py; after: failing assertions CHK-002, CHK-010, failing tests none
- attempt 1: files tests/test_uart_lite.py; after: failing assertions none, failing tests none

## Weakening check (code)

- no weakening found

## Regression of the candidate on the RTL

| | before | candidate |
|---|---|---|
| failing tests | none | none |
| failing assertions | CHK-002, CHK-003, CHK-005, CHK-006, CHK-009, CHK-010 | none |
| tests / assertions | 20 / 13 | 20 / 13 |

## Diff

```diff
--- a/verif/sva/nnc_chk_rx.sv
+++ b/verif/sva/nnc_chk_rx.sv
@@ -46,4 +46,8 @@
   logic        drop_q;
   logic        load_q;
+  // NNC verification fix (fix-verif, triage B): model register for s(E-1). REQ-RX-003 / contract RX model:
+  // a start bit is detected at T0 only if s(T0-1)=1 and s(T0)=0; REQ-FE-003 / D-005: a line held at 0 gives
+  // exactly one frame. Reset value 1 because s(R1-1) is taken as 1 (REQ-RST-010, REQ-RST-005).
+  logic        mdl_prev;
 
   assign mdl_v = mdl_m1_d2;
@@ -59,9 +63,12 @@
       mdl_m1   <= 1'b0;
       mdl_m1_d2 <= 1'b0;
+      mdl_prev <= 1'b1;  // NNC verification fix (fix-verif, triage B): s(R1-1)=1 after reset (REQ-RST-010)
     end else begin
       mdl_m1    <= 1'b0;
       mdl_m1_d2 <= mdl_m1;
+      mdl_prev  <= i_rxd;  // NNC verification fix (fix-verif, triage B): s(E) becomes s(E-1) at the next edge
       if (!mdl_busy) begin
-        if (!i_rxd) begin
+        // NNC verification fix (fix-verif, triage B): start needs s(T0-1)=1 and s(T0)=0 (REQ-RX-003), not just a low sample
+        if (mdl_prev && !i_rxd) begin
           mdl_busy <= 1'b1;
           mdl_cnt  <= 1;
--- a/verif/tests/test_uart_lite.py
+++ b/verif/tests/test_uart_lite.py
@@ -22,4 +22,10 @@
              "o_rx_frame_err": 0, "o_rx_overrun": 0}
 LOOP_MAX = 10 ** 8
+
+# NNC verification fix (fix-verif, triage B): True until the first Env.start() of this simulation. The
+# test for "start of a simulation" (ENV-002) must not use sim time == 0: tests that return through
+# not_verifiable (test_chk_014/015 when N is another value) let cocotb move time on before the next test,
+# so the first real Env.start() can begin after t=0 and the reset-first sequence was skipped.
+_SIM_FIRST_START = True
 
 
@@ -141,7 +147,28 @@
 
     async def start(self):
+        global _SIM_FIRST_START
         d = self.dut
-        d.i_rst_n.value = 1
-        self.idle()
+        # NNC verification fix (fix-verif, triage B): ENV-002 / contract UL-12.1-02 require i_rst_n=0 for at
+        # least 2 i_clk cycles at the start of a simulation. REQ-RST-002 output values only hold once a reset
+        # has been applied (REQ-RST-001: "when i_rst_n becomes 0"). At simulation start, hold the clock low and
+        # give i_rst_n a real 1->0 assertion before the clock starts. The first rising edge then comes after
+        # the reset, so there is no race at the first edge, and the reset is held for at least 2 cycles before a
+        # synchronous release at a falling edge (ENV-001). Later tests keep the original sequence, so pending SVA
+        # consequents of the previous test still complete with i_rst_n=1 before the reset (FLUSH_CYCLES rule).
+        # NNC verification fix (fix-verif, triage B): "start of a simulation" means the first Env.start() of
+        # this simulation (module flag), not sim time 0: earlier not-verifiable tests let time move on, so the
+        # time test was False and this sequence never ran.
+        sim_start = _SIM_FIRST_START
+        _SIM_FIRST_START = False
+        if sim_start:
+            self.clk.value = 0
+            d.i_rst_n.value = 1
+            self.idle()
+            await Timer(1, "step")
+            d.i_rst_n.value = 0
+            await Timer(1, "step")
+        else:
+            d.i_rst_n.value = 1
+            self.idle()
         res = start_clock(d)
         if inspect.isawaitable(res):
@@ -157,4 +184,9 @@
             cocotb.start_soon(self._chk001(name))
         await FallingEdge(self.clk)
+        if sim_start:
+            # NNC verification fix (fix-verif, triage B): at least 2 rising edges with i_rst_n=0 (ENV-002), then a
+            # synchronous release at a falling edge (ENV-001) before the asynchronous reset assertion below
+            await FallingEdge(self.clk)
+            d.i_rst_n.value = 1
         await self.reset(5)
         await self.fe(2)
```

Cost: US$1.17
