# Verification fix candidate: ot_rv_timer

Agent A17 (no RTL) proposed changes for 2 fault(s) judged B by triage. Status: **candidate**. Nothing in verif/ changes until `nnc fix-verif ot_rv_timer --apply`, and then gate G3 must be approved again.

## Faults (as A17 saw them)

1. **formal counterexample on CHK-003**
   - specification: rv_timer_Design_Specification.md:604-606 (INT-INTG-002): "When i_a_intg_flip is 1, bit 0 of a_user.cmd_intg is inverted. The request then has a command integrity error: a fatal TL-UL bus integrity fault ..., which triggers the fatal_fault alert (section 5)." This does not say the request must first be accepted. D-010, line 668 (RT-8-16): "o_alert shall pulse no later than 16 cycles after the request with i_a_intg_flip = 1 is accepted". That is an upper bound measured from acceptance. It does not forbid an earlier alert. D-009, line 667 (RT-8-14) bounds alert pulses caused by ALERT_TEST writes 
   - verification: nnc_chk_alert.sv:66 defines `flip_now_w = flip_seen || (acc_w && i_a_intg_flip)`, and line 81 sets flip_seen only `if (acc_w && i_a_intg_flip)`. A flip request that is presented (i_a_valid=1) but not yet accepted, or never accepted, does not stop the check. Lines 112-115 then require q_cnt+qual_w-qerr >= a_cnt+1 and a recent qualifying write for every o_alert pulse.

2. **formal counterexample on CHK-004**
   - specification: D-005, rv_timer_Design_Specification.md:663 (RT-8-07): "o_intr_timer_expired shall equal IS_0 AND IE_0 except in the 2 cycles after either changes." The comportability rule CP-T1.8.6-04 says the same: "The output of the INTR_STATE register becomes the outgoing interrupt to the processor after masking (ANDing) with the value of INTR_ENABLE." IE_0 is the rw field at bit 0, and bits 31:1 are reserved (RT-T5.4.1-01). Register tool, opentitan_register_tool.md:689-695: errors only for "writes of size smaller than register size" ("The width of the register is determined by the location of its fields"
   - verification: nnc_chk_intr.sv:68-70 updates ie only for writes to 0x100 with (a_size=2, mask 1111) or (a_size=0, mask 0001). The update happens at the D beat with d_error=0 (line 104). Line 61 tracks any write to 0x100 in c100/dw0..dw2 only until its D beat plus 2 edges. After that, ie is assumed to still hold its old value (0) even though an unmodelled, error-free write to 0x100 may have changed IE_0. The assertion at lines 113-114 then requires o_intr_timer_expired=0. The contract text (contract.json:316) defines ie the same way, restricted to these two write kinds.

## Changes

- `verif/sva/nnc_chk_alert.sv` (faults [1]): CHK-003 only stopped checking once a request with i_a_intg_flip=1 was accepted (acc_w). INT-INTG-002 says such a request has a command integrity error that triggers the fatal_fault alert, and it does not say the request must be accepted first. D-010 only gives an upper bound measured from acceptance ('no later than 16 cycles after ... is accepted'), so it does not forbid an earlier alert. D-014 lets the bench present requests while o_a_ready=0. So an alert caused by a flip request that is presented but not yet (or never) accepted is legal, and the old checker reported it as spurious. The fix sets flip_seen, and the same-edge term flip_now_w, at any edge with rst_ni=1, i_a_valid=1 and i_a_intg_flip=1. Every acceptance is also a presentation, so the old trigger is still included. The assertion itself, the count bound, the 16-cycle bound and the cover counter are unchanged, and no assumption was added. — rv_timer_Design_Specification.md:604-606 INT-INTG-002, rv_timer_Design_Specification.md:625-627 INT-ALERT-003, rv_timer_Design_Specification.md:667 D-009 (RT-8-14), rv_timer_Design_Specification.md:668 D-010 (RT-8-16), rv_timer_Design_Specification.md:672 D-014, rv_timer_Design_Specification.md:592-595 INT-TL-003
- `verif/sva/nnc_chk_intr.sv` (faults [2]): The CHK-004 ie model was updated only by full-word writes (mask 1111) and aligned byte writes (mask 0001) to 0x100. After an error-free write to 0x100 of any other kind (for example an aligned half-word, or a PutPartialData with a different mask) finished its 2-edge window, the checker still assumed the old ie (0) and required o_intr_timer_expired=0. Per the register-tool rules such a write may be legal and may change IE_0. INT-TL-003 makes it legal stimulus. D-013 says these cases are 'not checked', so the specification does not fix the resulting IE_0. Following the conservative option (2) from the triage, a new flag ie_unk is set at the error-free D beat of a write (intg_flip=0) to 0x100 that is not one of the modelled kinds. It is cleared by reset or by the error-free D beat of the next modelled write, which sets ie again. CHK-004 does not fire while ie_unk=1. All other CHK-004 terms (ie, flip disable, outstanding-write and 2-edge D-beat windows), CHK-005 and the cover counters are unchanged, and no assumption was added. The flip disable here was reviewed and left as it is: a flip request that is not accepted cannot write INTR_ENABLE0/INTR_STATE0, so presentation alone does not affect CHK-004/CHK-005. — rv_timer_Design_Specification.md:663 D-005 (RT-8-07), rv_timer_Design_Specification.md:671 D-013, rv_timer_Design_Specification.md:592-595 INT-TL-003, opentitan_register_tool.md:689-695, CP-T1.8.6-04, RT-T5.4.1-01

## Attempts

- attempt 0: files sva/nnc_chk_alert.sv, sva/nnc_chk_intr.sv; after: failing assertions none, failing tests none

## Weakening check (code)

- no weakening found

## Regression of the candidate on the RTL

| | before | candidate |
|---|---|---|
| failing tests | none | none |
| failing assertions | none | none |
| tests / assertions | 23 / 13 | 23 / 13 |

## Diff

```diff
--- a/verif/sva/nnc_chk_alert.sv
+++ b/verif/sva/nnc_chk_alert.sv
@@ -40,4 +40,5 @@
   logic        qual_w;
   logic        d_beat_w;
+  logic        flip_pres_w;
   logic        flip_now_w;
   logic        flip_seen;
@@ -64,5 +65,13 @@
   assign qual_w     = wr0_w && i_a_data[0] && regwen;
   assign d_beat_w   = p_valid && o_d_valid && i_d_ready;
-  assign flip_now_w = flip_seen || (acc_w && i_a_intg_flip);
+  // NNC verification fix (fix-verif, triage B): INT-INTG-002 says a request with i_a_intg_flip=1 "has a
+  // command integrity error ... which triggers the fatal_fault alert" and does not require the request to
+  // be accepted first. D-010 gives only an upper bound from acceptance and does not forbid an earlier
+  // alert, and D-014 lets the bench present requests while o_a_ready=0. So the flip exemption starts at
+  // the first edge (rst_ni=1) where such a request is presented (i_a_valid=1), not only at acceptance.
+  // Every acceptance is also a presentation, so the old trigger is still included. The assertion and
+  // its bounds are unchanged.
+  assign flip_pres_w = rst_ni && i_a_valid && i_a_intg_flip;
+  assign flip_now_w = flip_seen || flip_pres_w;
   assign qerr_now_w = q_err + ((d_beat_w && p_qual && o_d_error) ? 1 : 0);
 
@@ -79,5 +88,7 @@
       age       <= 31;
     end else begin
-      if (acc_w && i_a_intg_flip) flip_seen <= 1'b1;
+      // NNC verification fix (fix-verif, triage B): set on presentation of a flip request (INT-INTG-002),
+      // not only on its acceptance edge.
+      if (flip_pres_w) flip_seen <= 1'b1;
       if (d_beat_w) begin
         p_valid <= 1'b0;
--- a/verif/sva/nnc_chk_intr.sv
+++ b/verif/sva/nnc_chk_intr.sv
@@ -39,4 +39,5 @@
   logic [QD-1:0] q_w100 = '0;  // write to 0x100 (any)
   logic [QD-1:0] q_upd  = '0;  // write that updates ie on its D beat
+  logic [QD-1:0] q_unk  = '0;  // write to 0x100 of a kind whose effect on IE_0 is not modelled
   logic [QD-1:0] q_d0   = '0;  // data[0] of request
   logic [QD-1:0] q_clr  = '0;  // clearing write kind
@@ -47,4 +48,8 @@
   int unsigned cclr = 0;
   logic ie = 1'b0;
+  // NNC verification fix (fix-verif, triage B): ie_unk=1 means an error-free write to 0x100 that is not
+  // one of the modelled kinds has completed, so IE_0 is not known to the model (D-013: "other sub-word
+  // cases are not checked").
+  logic ie_unk = 1'b0;
   logic seen_flip = 1'b0;
   logic prev_rst_ok = 1'b0;
@@ -69,4 +74,9 @@
                 ( (is_wr && i_a_size == 2'd2 && i_a_mask == 4'b1111) ||
                   (is_wr && i_a_size == 2'd0 && i_a_mask == 4'b0001) );
+  // NNC verification fix (fix-verif, triage B): any other write (intg_flip=0) to 0x100, e.g. an aligned
+  // half-word or a partial mask, is legal stimulus (INT-TL-003). By the register tool
+  // (opentitan_register_tool.md:689-695) it may succeed and change IE_0 (width 1), but D-013 leaves it
+  // unchecked. Its error-free D beat makes ie unknown until the next modelled write or reset.
+  wire a_unk  = n_flip && a_w100 && !a_upd;
   wire a_clr  = n_flip && is_wr && (
                   ((i_a_address == 32'h100) && !i_a_data[0] && i_a_mask[0]) ||
@@ -82,7 +92,7 @@
   always_ff @(posedge clk_i) begin
     if (!rst_ni) begin
-      q_w100 <= '0; q_upd <= '0; q_d0 <= '0; q_clr <= '0;
+      q_w100 <= '0; q_upd <= '0; q_unk <= '0; q_d0 <= '0; q_clr <= '0;
       wp <= '0; rp <= '0; cnt <= 0; c100 <= 0; cclr <= 0;
-      ie <= 1'b0; seen_flip <= 1'b0;
+      ie <= 1'b0; ie_unk <= 1'b0; seen_flip <= 1'b0;
       prev_rst_ok <= 1'b0; prev_intr <= 1'b0;
       dw1 <= 1'b0; dw2 <= 1'b0; dcs <= '0;
@@ -96,4 +106,5 @@
         q_w100[wp] <= a_w100;
         q_upd[wp]  <= a_upd;
+        q_unk[wp]  <= a_unk;
         q_d0[wp]   <= i_a_data[0];
         q_clr[wp]  <= a_clr;
@@ -102,5 +113,11 @@
       if (pop) begin
         rp <= rp + 1'b1;
-        if (q_upd[rp] && !o_d_error) ie <= q_d0[rp];
+        // NNC verification fix (fix-verif, triage B): a modelled error-free write sets ie and makes it
+        // known again; an unmodelled error-free write to 0x100 makes it unknown.
+        if (q_upd[rp] && !o_d_error) begin
+          ie     <= q_d0[rp];
+          ie_unk <= 1'b0;
+        end
+        if (q_unk[rp] && !o_d_error) ie_unk <= 1'b1;
       end
       cnt  <= cnt  + (push ? 1 : 0) - (pop ? 1 : 0);
@@ -111,8 +128,10 @@
 
   // CHK-004: Interrupt output masked by INTR_ENABLE0.IE_0 (RT-8-07, CP-T1.8.6-04, RT-T5.4.1-01)
+  // NNC verification fix (fix-verif, triage B): not applied while ie_unk=1 (IE_0 set by an unmodelled,
+  // error-free write to 0x100 whose effect D-013 leaves unchecked). Otherwise unchanged.
   a_CHK_004: assert property (@(posedge clk_i) disable iff (!rst_ni)
-    (rst_ni && !ie && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2) |-> (o_intr_timer_expired == 1'b0))
+    (rst_ni && !ie && !ie_unk && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2) |-> (o_intr_timer_expired == 1'b0))
     else begin fails_CHK_004++; $display("NNC_FAIL CHK-004 @%0t", $time); end
-  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_ni && !ie && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2)) hits_CHK_004 <= hits_CHK_004 + 1;
+  always_ff @(posedge clk_i) if (!(!rst_ni) && (rst_ni && !ie && !ie_unk && !dis && (c100 == 0) && !dw0 && !dw1 && !dw2)) hits_CHK_004 <= hits_CHK_004 + 1;
 
   // CHK-005: Latched interrupt falls only after a clearing write or reset (CP-T1.8.6-06, CP-T1.8.5-02, CP-T1.8.5.1-01, CP-T1.8.1-01)
```

Cost: US$0.67
