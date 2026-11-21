# Verification fix candidate: ot_gpio

Agent A17 (no RTL) proposed changes for 1 fault(s) judged B by triage. Status: **candidate**. Nothing in verif/ changes until `nnc fix-verif ot_gpio --apply`, and then gate G3 must be approved again.

## Faults (as A17 saw them)

1. **formal counterexample on CHK-003 (a_CHK_003, verif/sva/nnc_chk_alert.sv:97): No alert without an alert cause**
   - specification: spec/gpio_Design_Specification.md:1079-1081 [INT-INTG-002]: "When `i_a_intg_flip` is 1, bit 0 of `a_user.cmd_intg` is inverted. Line 963: "fatal_fault | This fatal alert is triggered when a fatal TL-UL bus integrity fault is detected." Line 1164 D-017: "After a request with `i_a_intg_flip` = 1 is accepted, `o_alert` shall pulse no later than 16 cycles later...". This is an upper bound measured from acceptance; it does not say an alert must not appear before acceptance. Lines 1076-1077 [INT-INTG-001] (GP-4.2-01, the only rule cited by CHK-003): "A request with `i_a_intg_flip` = 0 therefore alwa
   - verification: verif/sva/nnc_chk_alert.sv:48 `a_hs = i_a_valid && o_a_ready`. Line 72 sets intg_seen_q only on `a_hs && i_a_intg_flip`. Line 82 `cause_a = intg_seen_q || (a_hs && i_a_intg_flip)`. So a flipped-integrity request counts as a cause only once it is accepted. Lines 50-51 and 83 give cause_b (ALERT_TEST write with data[0]=1, plus a 16-cycle window after its response). Line 97 asserts `o_alert |-> alert_cause`. Nothing in the checker covers a flipped request that is presented (i_a_valid=1) but still waiting for o_a_ready.

## Changes

- `verif/sva/nnc_chk_alert.sv` (faults [1]): CHK-003 counted a request with i_a_intg_flip=1 as an alert cause only once it was accepted (A handshake). The spec does not say that. INT-INTG-002 says that a request with i_a_intg_flip=1 has a command integrity error, which is a fatal TL-UL bus integrity fault that triggers fatal_fault. In TL-UL, a request exists as soon as a_valid=1. INT-TL-003 says a presented request stays stable until accepted. D-017 gives only an upper bound (16 cycles), measured from acceptance; it does not forbid an earlier alert. So the checker now records cause (a) in any cycle with i_a_valid=1 and i_a_intg_flip=1, both in the sticky intg_seen_q and in the same-cycle term. This makes the checker follow the spec without weakening anything the spec requires. Traffic with i_a_intg_flip=0 (INT-INTG-001) still never counts as a cause. Cause (b), CHK-001/002, the assertion, its counters and the CHK-003 reference are unchanged. — spec/gpio_Design_Specification.md:1079-1081 [INT-INTG-002], spec/gpio_Design_Specification.md:1076-1077 [INT-INTG-001], spec/gpio_Design_Specification.md:1067-1068 [INT-TL-003], spec/gpio_Design_Specification.md:1164 D-017, spec/gpio_Design_Specification.md:963 Security Alerts fatal_fault, spec/opentitan_tlul_bus_specification.md:83 a_valid

## Attempts

- attempt 0: files sva/nnc_chk_alert.sv; after: failing assertions none, failing tests none

## Weakening check (code)

- no weakening found

## Regression of the candidate on the RTL

| | before | candidate |
|---|---|---|
| failing tests | none | none |
| failing assertions | none | none |
| tests / assertions | 26 / 13 | 26 / 13 |

## Diff

```diff
--- a/verif/sva/nnc_chk_alert.sv
+++ b/verif/sva/nnc_chk_alert.sv
@@ -70,5 +70,10 @@
       timer_q     <= 0;
     end else begin
-      if (a_hs && i_a_intg_flip) intg_seen_q <= 1'b1;
+      // NNC verification fix (fix-verif, triage B): a request with i_a_intg_flip=1 has a command
+      // integrity error (fatal bus integrity fault, INT-INTG-002) from the moment it is presented
+      // (a_valid=1 means "Request from host is valid", TL-UL spec); it is committed (INT-TL-003) and
+      // D-017 only gives an upper bound from acceptance, so the cause counts from i_a_valid=1, not
+      // only from the A handshake. Traffic with i_a_intg_flip=0 is still never an alert cause.
+      if (i_a_valid && i_a_intg_flip) intg_seen_q <= 1'b1;
       outs_q <= outs_next;
       if (a_test_wr) b_flag_q <= 1'b1;
@@ -80,5 +85,7 @@
 
   logic cause_a, cause_b, alert_cause;
-  assign cause_a = intg_seen_q || (a_hs && i_a_intg_flip);
+  // NNC verification fix (fix-verif, triage B): cause (a) is a cycle with i_a_valid=1 and
+  // i_a_intg_flip=1 (presented flipped-integrity request), per INT-INTG-002 / D-017 / TL-UL a_valid.
+  assign cause_a = intg_seen_q || (i_a_valid && i_a_intg_flip);
   assign cause_b = a_test_wr || (b_flag_q && (outs_q != 0 || timer_q <= 16));
   assign alert_cause = cause_a || cause_b;
```

Cost: US$0.34
