# Verification fix candidate: c_pcpi_div

Agent A17 (no RTL) proposed changes for 1 fault(s) judged B by triage. Status: **candidate**. Nothing in verif/ changes until `nnc fix-verif c_pcpi_div --apply`, and then gate G3 must be approved again.

## Faults (as A17 saw them)

1. **CHK-001 (assertion) 'pcpi_wait stays asserted until pcpi_ready' — 2809 fails / 278073 hits, first fail at 480000 ps (sim.log:39). Fails also occur in groups exactly 370000 ps apart (sim.log:49-51: 19035000, 19405000, 19775000).**
   - specification: spec/c_pcpi_div_Design_Specification.md:62-66 (rule PD-T1.1-06, SHOULD, rules.json:164-186): "A PCPI core that needs more than a couple of cycles to execute an instruction, should assert `pcpi_wait` as soon as the instruction has been decoded successfully and keep it asserted until it asserts `pcpi_ready`." Master side (PD-T1.1-01, spec :48-52) only says pcpi_valid is asserted with the instruction. The spec never says whether the master must drop pcpi_valid between two instructions. contract.json:327 (assumption) says: "Legal master stimulus holds pcpi_valid ... stable from issue until pcpi_re
   - verification: verif/tests/test_c_pcpi_div.py:214-217: after the ready edge, execute() does `await next_cycle; self.drive(0); self.sample(chk)` and returns without waiting for another cycle. idle(gap) (160-167) does `next_cycle` then drive for each of gap iterations, so with gap=0 it does nothing. The next execute() then calls `self.drive(1, insn, rs1, rs2)` at line 181 in the same mid-cycle, which overwrites the pcpi_valid=0 just written. gap=0 is common: CHK-004 randint(0,2) (273), CHK-005 randint(0,3) (295), CHK-008 gap in (0,1,5) (329), regression 50% gap=0 (395-396). The Python model still records self.

## Changes

- `verif/tests/test_c_pcpi_div.py` (faults [1]): execute() drove pcpi_valid=1 in the same mid-cycle where the previous deassert (or the last idle cycle) had just driven pcpi_valid=0. That overwrote the 0, so with gap=0 no rising edge ever saw pcpi_valid=0 between two instructions. The test's own model still recorded valid=0, so it missed this. The contract says the master deasserts pcpi_valid on the cycle after pcpi_ready, so this stimulus was illegal and set off the CHK-001 failures. The fix waits one clock cycle (await next_cycle) at the start of execute() before driving the issue. Now the pcpi_valid=0 that was already driven and checked is really sampled at a rising edge, so every instruction is preceded by at least one pcpi_valid=0 edge. CHK-001 in the SVA, the cover points and all expected values are unchanged. — contract.json:223 (CHK-008 stimulus: 'then drive pcpi_valid=0 on the next cycle'), contract.json:327 ('Legal master stimulus ... deasserts pcpi_valid on the following cycle'), spec/c_pcpi_div_Design_Specification.md:62-66 (PD-T1.1-06: keep pcpi_wait asserted until pcpi_ready), spec/c_pcpi_div_Design_Specification.md:48-52 (PD-T1.1-01)

## Attempts

- attempt 0: files tests/test_c_pcpi_div.py; after: failing assertions none, failing tests none

## Weakening check (code)

- no weakening found

## Regression of the candidate on the RTL

| | before | candidate |
|---|---|---|
| failing tests | none | none |
| failing assertions | CHK-001 | none |
| tests / assertions | 7 / 3 | 7 / 3 |

## Diff

```diff
--- a/verif/tests/test_c_pcpi_div.py
+++ b/verif/tests/test_c_pcpi_div.py
@@ -168,5 +168,5 @@
 
     async def execute(self, op, rs1, rs2, chk="CHK-008", fields=None):
-        """Issue one instruction at the current mid-cycle; return (pcpi_rd, latency in edges).
+        """Issue one instruction at the next mid-cycle; return (pcpi_rd, latency in edges).
 
         Ends mid-cycle right after the pcpi_valid=0 deassert cycle has been driven/checked.
@@ -177,4 +177,14 @@
         insn = encode(op, *fields)
         tag = f"{op} rs1=0x{rs1 & MASK:08X} rs2=0x{rs2 & MASK:08X}"
+
+        # NNC verification fix (fix-verif, triage B): every caller (previous execute() deassert,
+        # idle(), setup, CHK-009 idle loop) ends mid-cycle right after driving pcpi_valid=0 for the
+        # coming rising edge. Driving pcpi_valid=1 in that same mid-cycle overwrote it, so with
+        # gap=0 no rising edge ever sampled pcpi_valid=0 between two instructions (back-to-back
+        # spacing 37 edges instead of 38), which contradicts the contract master rule
+        # (contract.json:223 "then drive pcpi_valid=0 on the next cycle"; contract.json:327
+        # "deasserts pcpi_valid on the following cycle"). Advance one cycle first so the
+        # pcpi_valid=0 already driven and checked is really sampled at a rising edge.
+        await next_cycle(self.dut)
 
         # Issue: these inputs are sampled at the issue edge R_1.
```

Cost: US$0.41
