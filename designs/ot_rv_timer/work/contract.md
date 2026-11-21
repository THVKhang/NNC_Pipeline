# Verification contract (Gate 2)

```
interface: 26 ports, 0 parameters, clock clk_i, reset {'name': 'rst_ni', 'active_low': True}
checks: 35 {'assertion': 13, 'test': 22}  rules 228: in checks 151, not verified 77, uncovered 0 (after first pass 0), unknown IDs 0
calls: 1 (0 cached)  cost US$1.7633
```

## Interface

| Port | Dir | Width | Type |
|---|---|---|---|
| clk_i | input | 1 |  |
| rst_ni | input | 1 |  |
| i_a_valid | input | 1 |  |
| o_a_ready | output | 1 |  |
| i_a_opcode | input | 3 |  |
| i_a_param | input | 3 |  |
| i_a_size | input | 2 |  |
| i_a_source | input | 8 |  |
| i_a_address | input | 32 |  |
| i_a_mask | input | 4 |  |
| i_a_data | input | 32 |  |
| i_a_instr | input | 1 |  |
| i_a_intg_flip | input | 1 |  |
| o_d_valid | output | 1 |  |
| i_d_ready | input | 1 |  |
| o_d_opcode | output | 3 |  |
| o_d_param | output | 3 |  |
| o_d_size | output | 2 |  |
| o_d_source | output | 8 |  |
| o_d_sink | output | 1 |  |
| o_d_data | output | 32 |  |
| o_d_error | output | 1 |  |
| o_d_intg_err | output | 1 |  |
| o_alert | output | 1 |  |
| o_alert_integ_fail | output | 1 |  |
| o_intr_timer_expired | output | 1 |  |

## Checks

| ID | Kind | Group | Title | Rules | Behavior / expected |
|---|---|---|---|---|---|
| CHK-001 | assertion | alert | No alert signal-integrity failure | RT-5-04, RT-8-32, RT-3-07 | At every rising edge with rst_ni=1, o_alert_integ_fail=0. This includes the whole time after a request with i_a_intg_flip=1. |
| CHK-002 | assertion | alert | o_alert is a single-cycle pulse per handshake | RT-5-02 | If rst_ni=1 and o_alert=1 at rising edge k, then o_alert=0 at rising edge k+1. |
| CHK-003 | assertion | alert | No spurious alerts, no more pulses than test writes | RT-4.2-01, RT-8-14, RT-5-06, RT-8-12 | Model state:
- flip_seen: set at the acceptance edge of any request with i_a_intg_flip=1; cleared while rst_ni=0.
- regwen: 1 while rst_ni=0; set to 0 at the D beat with o_d_error=0 of a PutFullData (a_size=2, mask 1111) to 0x000 with i_a_data[31]=0.
- Qualifying write: a PutFullData with a_size=2 and mask 1111 to 0x000 with i_a_data[0]=1, accepted while regwen=1.

While flip_seen=0:
(a) Every rising edge with o_alert=1 lies at or after the acceptance edge of some qualifying write. It also lies no later than 16 edges after that write's D beat, and that D beat had o_d_error=0.
(b) The number of edges with o_alert=1 since the last rst_ni release is never larger than the number of qualifying writes accepted since then. |
| CHK-004 | assertion | intr | Interrupt output masked by INTR_ENABLE0.IE_0 | RT-8-07, CP-T1.8.6-04, RT-T5.4.1-01 | Model ie: ie is 0 while rst_ni=0. At the D beat with o_d_error=0 of a request with intg_flip=0 to 0x100 that is either a PutFullData/PutPartialData with a_size=2 and mask 1111 or a PutPartialData with a_size=0 and mask 0001, ie takes that request's i_a_data[0].

Condition: at rising edge k, rst_ni=1, ie=0, no write to 0x100 is outstanding, and no such write had its D beat at edges k-2 to k.

Required: o_intr_timer_expired=0 at edge k.

The check is disabled from the acceptance of a request with i_a_intg_flip=1 until reset. |
| CHK-005 | assertion | intr | Latched interrupt falls only after a clearing write or reset | CP-T1.8.6-06, CP-T1.8.5-02, CP-T1.8.5.1-01, CP-T1.8.1-01 | If rst_ni=1 at rising edges k and k+1, o_intr_timer_expired=1 at edge k and 0 at edge k+1, then a write request (opcode 0 or 1, intg_flip=0) of one of these kinds was accepted at or before edge k+1:
- to 0x100 with i_a_data[0]=0 and mask[0]=1;
- to 0x104 with i_a_data[0]=1 and mask[0]=1;
- to 0x118;
- to 0x11C.
That request is either still outstanding at edge k+1 or had its D beat at an edge at or after k-5.

Writes to CTRL, TIMER_V_LOWER0, TIMER_V_UPPER0 and CFG0 do not explain a fall. The check is disabled from the acceptance of a request with i_a_intg_flip=1 until reset. |
| CHK-006 | assertion | reset | Outputs inactive during reset | RT-8-30, RT-2-04 | At every rising edge (and at any other sample point) where rst_ni=0: o_d_valid=0, o_alert=0, o_alert_integ_fail=0 and o_intr_timer_expired=0. o_a_ready is not checked. |
| CHK-007 | assertion | reset | Outputs change only at rising clock edges | RT-2-02 | The test bench changes inputs only right after a rising edge of clk_i. For every clock period between rising edges k and k+1 where rst_ni=1 at both edges and does not fall in between, each output keeps one value from just after edge k (once the new inputs are applied) until edge k+1. The outputs checked are o_a_ready, o_d_valid, o_d_opcode, o_d_param, o_d_size, o_d_source, o_d_sink, o_d_data, o_d_error, o_d_intg_err, o_alert, o_alert_integ_fail and o_intr_timer_expired. They are sampled just after edge k and at the falling edge of clk_i. |
| CHK-008 | assertion | tbhost | Test-bench host obligations (stimulus self-check) | RT-4.1-04, RT-8-29, RT-8-34, RT-8-20, RT-8-18, RT-8-25, RT-8-03, RT-8-15, TL-T3.1.3.4-02 | Checked at every rising edge:
(1) If i_a_valid=1 and o_a_ready=0, then at the next edge i_a_valid=1 and i_a_opcode, i_a_param, i_a_size, i_a_source, i_a_address, i_a_mask, i_a_data, i_a_instr and i_a_intg_flip are unchanged.
(2) i_a_valid=0 at every edge with rst_ni=0 and at the first edge after rst_ni rises.
(3) Whenever i_a_valid=1:
- i_a_param=0;
- i_a_address<0x200;
- i_a_mask is not one of 0101, 1001, 1010, 1011, 1101;
- not (i_a_instr=1 and i_a_opcode is 0 or 1);
- i_a_source differs from every outstanding request's a_source;
- not a write to 0x000 with i_a_data=0x00000001.
(4) No write to 0x10C, 0x110 or 0x114 is presented while the modeled CTRL.active_0 is 1 or a write to 0x004 is outstanding. The model is the bit 0 of the last error-free write to 0x004, and it is 0 after reset. |
| CHK-009 | assertion | tlul | Every D-channel beat matches exactly one outstanding request | TL-T3.1.3.2.3-01, TL-T2.2-03, RT-4.1-01, TL-T3.1.3.5-08 | The checker keeps a set of outstanding requests. A request is added at each rising edge where rst_ni=1, i_a_valid=1 and o_a_ready=1, keyed by i_a_source, and it records i_a_opcode, i_a_size, i_a_address, i_a_mask, i_a_data, i_a_instr and i_a_intg_flip. At each rising edge where rst_ni=1, o_d_valid=1 and i_d_ready=1 (a D beat), exactly one outstanding request has a_source equal to o_d_source and was accepted at this edge or an earlier one. That request is removed. A D beat with no matching outstanding request (an orphan) is a failure. At most one D beat completes per edge. The set is cleared while rst_ni=0. From the acceptance of a request with i_a_intg_flip=1 until rst_ni=0, the check is disabled (D-010). |
| CHK-010 | assertion | tlul | Response opcode and size echo | RT-8-27, RT-3-04, RT-3-01, TL-T3.1.3.4-07, RT-4.1-01 | For each D beat that CHK-009 matches to a request R with R.i_a_intg_flip=0, checked at the same rising edge:
- If R.opcode=4 (Get), then o_d_opcode=1 (AccessAckData) and o_d_size=R.a_size.
- If R.opcode is 0 (PutFullData) or 1 (PutPartialData), then o_d_opcode=0 (AccessAck) and o_d_size=R.a_size.
- If R.opcode is not 0, 1 or 4, only o_d_error=1 is required.
- In every D beat of a request with defined opcode, o_d_opcode is 0 or 1.
o_d_param and o_d_sink are not checked. The check is disabled from the acceptance of a request with i_a_intg_flip=1 until reset. |
| CHK-011 | assertion | tlul | d_error value for classified requests | RT-4.1-06, RT-8-19, RT-8-21, RT-8-22, RT-8-23, RT-8-28, TL-T3.1.3.4-06, TL-T3.1.3.5-01, TL-T3.1.3.5-02, TL-T3.1.3.5-03, TL-T3.1.3.5-04, TL-T3.1.3.5-05, RG-T1.4.1-04, RG-T1.4.1-05, RG-T1.4.1-07, RT-1-02 | This applies to each D beat matched to a request R with intg_flip=0, instr=0 and address<0x200.

o_d_error must be 1 if any of these holds:
(a) R.opcode is not 0, 1 or 4.
(b) R.a_size=3.
(c) R.address is not a multiple of 2^R.a_size.
(d) R.mask has a 1 on a byte lane outside lanes R.address[1:0] to R.address[1:0]+2^R.a_size-1.
(e) R.opcode=0 and R.mask is not 1 on every lane of that range.
(f) R.address with bits [1:0] cleared is not one of 0x000, 0x004, 0x100, 0x104, 0x108, 0x10C, 0x110, 0x114, 0x118, 0x11C.
(g) R.opcode is 0 or 1, R.a_size=0, R.mask=0001, and R.address is one of 0x000, 0x10C, 0x110, 0x114, 0x118, 0x11C.

o_d_error must be 0 if none of (a) to (g) holds and R is one of:
- a Get, PutFullData or PutPartialData with a_size=2 and mask 1111 to a mapped aligned address;
- a PutPartialData with a_size=0 and mask 0001 to 0x004, 0x100, 0x104 or 0x108;
- a Get with a_size 0 or 1, an address aligned to that size and a mask equal to exactly the active lanes, to a mapped address.

All other requests are not checked. |
| CHK-012 | assertion | tlul | D channel holds under back-pressure | RT-4.1-01 | If rst_ni=1, o_d_valid=1 and i_d_ready=0 at rising edge k, and rst_ni=1 at edge k+1, then at edge k+1 o_d_valid=1. Also o_d_opcode, o_d_param, o_d_size, o_d_source, o_d_sink, o_d_data and o_d_error equal their values at edge k. The check is disabled from the acceptance of a request with i_a_intg_flip=1 until reset. |
| CHK-013 | assertion | tlul | Response integrity never fails | RT-4.3-01, RT-4.3-02, RT-8-32, RT-3-05, RT-4.2-01 | At every rising edge with rst_ni=1, o_d_intg_err=0. This includes edges with o_d_valid=1 and the whole time after a request with i_a_intg_flip=1. |
| CHK-014 | test | alert | ALERT_TEST.fatal_fault triggers one alert per write | RT-T5.2.1-03, RT-5-06, RT-8-13, RT-8-14, RT-5-02, RT-3-06, CP-T1.9.3-01, CP-T1.9.3-02, AH-T1.3.2-01, AH-T1.3.2-04, RT-7-06, RT-T5.1-01, RT-8-10 | A write of 1 to fatal_fault gives exactly one o_alert pulse within 16 cycles of the D beat. The wo bit and the reserved bits read 0. — STIMULUS: After reset, idle 50 cycles. Write 0x80000001 to 0x000 (PutFullData, a_size=2, mask 1111; acceptance edge a, D beat r), watch until r+100, then read ALERT_TEST. Repeat 3 times, 100 cycles apart. Next, send 3 writes of 0x80000001, each accepted within 10 cycles of the previous one, and watch until the last D beat + 100. Finally write 0x80000000 and 0xFFFFFFFE, watching 100 cycles after each, and read ALERT_TEST. — EXPECTED: - No o_alert pulse during the idle cycles.
- For each isolated write: o_d_error=0, exactly one o_alert pulse at an edge in [a, r+16], no other pulse up to r+100, and ALERT_TEST reads 0x80000000.
- For the closely spaced burst: between 1 and 3 pulses in total.
- For the 0x80000000 and 0xFFFFFFFE writes: no pulse, and ALERT_TEST reads 0x80000000.
- o_alert_integ_fail=0 throughout. |
| CHK-015 | test | alert | ALERT_TEST.regwen rw0c locks alert testing until reset | RT-T5.2.1-01, RT-8-12, RT-7-06, RT-7-02, RT-T5.2-01 | Writing 0 to regwen disables alert testing until reset. Writing 1 cannot set regwen again. — STIMULUS: 1. After reset, write 0x80000000 to 0x000 and read ALERT_TEST.
2. Write 0x00000000 and read ALERT_TEST.
3. Write 0x80000001, watch 100 cycles, then read ALERT_TEST.
4. Write 0x80000000 and read ALERT_TEST.
5. Assert rst_ni=0 for 5 cycles and release it.
6. Read ALERT_TEST, write 0x80000001 (D beat r), and watch until r+100. — EXPECTED: - Step 1: reads 0x80000000.
- Step 2: o_d_error=0 and reads 0x00000000, with no o_alert pulse.
- Step 3: o_d_error=0, no o_alert pulse within 100 cycles, and reads 0x00000000.
- Step 4: reads 0x00000000.
- Step 6: ALERT_TEST reads 0x80000000, and exactly one o_alert pulse occurs at an edge <= r+16. |
| CHK-016 | test | alert | Command integrity error raises a repeating fatal alert until reset | RT-T6.3-01, RT-4.2-03, RT-3-03, RT-5-05, RT-8-16, RT-8-17, CP-T1.9.1-04, CP-T1.9.4-02, AH-T1.3.2-02, AH-T1.3.2-03, RT-7-07, RT-3-06 | A request with corrupted A-channel integrity causes o_alert pulses that start within 16 cycles of acceptance and repeat at least every 32 cycles until rst_ni is asserted. — STIMULUS: Run 1:
1. After reset, with i_d_ready=1, send one Get (a_size=2, mask 1111) to 0x104 with i_a_intg_flip=1 (acceptance edge a). Do not wait more than 32 cycles for a response.
2. Keep i_a_valid=0 for 1000 cycles.
3. Assert rst_ni=0 for 5 cycles and release it synchronously.
4. Idle 200 cycles, then read CFG0.
Run 2: the same, with a PutFullData of 0x1 to 0x100 with i_a_intg_flip=1. — EXPECTED: - The first o_alert pulse is at an edge in [a, a+16].
- Every window of 32 consecutive edges after it, up to reset assertion, contains at least one pulse.
- o_alert_integ_fail=0 and o_d_intg_err=0 throughout.
- o_alert=0 while rst_ni=0 and during the 200 cycles after release.
- The CFG0 read returns o_d_error=0 and 0x00010000.
- The response to the corrupted request is not checked. |
| CHK-017 | test | err | Unmapped offsets return error and change nothing | RT-8-19, TL-T3.1.3.5-05, RG-T1.4.1-01, RG-T1.4.1-03, RT-7-07, RT-T3.2.2-03, RT-1-01 | Requests to word offsets in 0x000 to 0x1FC that are not mapped get d_error=1 and leave every register unchanged. This includes offsets 0x120 and above, so there are no registers for a second hart or timer. — STIMULUS: After reset, with i_d_ready=1, go through every 4-byte-aligned offset in 0x000 to 0x1FC other than 0x000, 0x004 and 0x100 to 0x11C. Send each one a Get (a_size=2, mask 1111) and a PutFullData (a_size=2, mask 1111, data 0xFFFFFFFF). Then read all 10 mapped registers. — EXPECTED: Every request to an unmapped offset has o_d_error=1, with o_d_opcode=1 for Get and 0 for PutFullData. Afterwards all 10 registers still read the CHK-028 reset values. No o_alert pulse occurs and o_intr_timer_expired stays 0. |
| CHK-018 | test | err | Byte writes per register width | RT-8-21, RT-8-22, RG-T1.4.1-05, TL-T3.1.3.4-03, RT-7-07 | Aligned byte writes to registers wider than 8 bits fail and change nothing. Aligned byte writes to byte 0 of the 1-bit registers succeed and take effect. — STIMULUS: After reset, send PutPartialData (a_size=0, mask 0001, aligned address):
- 0x10C with data 0x05; 0x110, 0x114, 0x118 and 0x11C with data 0x00; 0x000 with data 0x00000000 and then 0x00000001. Read all of them back.
- 0x100 with data 0x01, then read INTR_ENABLE0.
- 0x108 with data 0x01, then read INTR_STATE0.
- 0x104 with data 0x01, then read INTR_STATE0.
- 0x004 with data 0x01, then read CTRL; then 0x004 with data 0x00, then read CTRL. — EXPECTED: - The byte writes to 0x10C, 0x110, 0x114, 0x118, 0x11C and 0x000 return o_d_error=1. Afterwards CFG0=0x00010000, TIMER_V_LOWER0=TIMER_V_UPPER0=0x0, COMPARE_LOWER0_0=COMPARE_UPPER0_0=0xFFFFFFFF and ALERT_TEST=0x80000000. No o_alert pulse occurs within 100 cycles.
- The byte writes to 0x100, 0x108, 0x104 and 0x004 return o_d_error=0.
- INTR_ENABLE0 reads 0x1.
- INTR_STATE0 reads 0x1 after the INTR_TEST0 byte write (read issued 4 or more cycles after its D beat) and 0x0 after the INTR_STATE0 byte write.
- CTRL reads 0x1 and then 0x0. |
| CHK-019 | test | err | TL-UL protocol error cases | RT-4.1-05, RT-4.1-06, RT-8-28, TL-T3.1.3.4-06, TL-T3.1.3.5-01, TL-T3.1.3.5-02, TL-T3.1.3.5-03, TL-T3.1.3.5-04, TL-T3.1.3.5-07, RG-T1.4.1-04, RT-7-07 | Requests with an illegal opcode, size, alignment or mask are answered with d_error=1. — STIMULUS: After reset, with i_d_ready=1, send one request at a time:
- opcodes 2, 3, 5, 6 and 7 with a_size=2 and mask 1111 to 0x10C;
- Get with a_size=3 to 0x110;
- PutFullData with a_size=3 and mask 1111 to 0x110;
- Get with a_size=2 and mask 1111 to 0x112;
- Get with a_size=1 and mask 0011 to 0x111;
- Get with a_size=0 and mask 0010 to 0x110;
- PutFullData with a_size=2 and mask 0111 to 0x118.
Then read CFG0 with a full-word Get. — EXPECTED: Every listed request gets exactly one response with o_d_error=1. For opcodes 0 and 4, CHK-010 also holds (d_opcode, d_size echo). The final CFG0 read returns o_d_error=0 and 0x00010000. |
| CHK-020 | test | err | Sub-word reads return the full word | RG-T1.4.1-07, RG-T1.4.1-08 | Aligned sub-word reads return the full register word in byte-lane positions, without error. — STIMULUS: With CTRL=0, write CFG0=0x00AB0123 and COMPARE_LOWER0_0=0x89ABCDEF. Send Get a_size=0 to 0x10C+k with mask (1<<k) for k=0..3. Send Get a_size=1 to 0x118 with mask 0011 and to 0x11A with mask 1100. — EXPECTED: Every response has o_d_error=0, o_d_opcode=1 and o_d_size equal to a_size. o_d_data is 0x00AB0123 for the four CFG0 reads and 0x89ABCDEF for the two COMPARE_LOWER0_0 reads. |
| CHK-021 | test | err | Instruction-fetch reads | RT-3-02, RT-7-07 | Gets with i_a_instr=1 are answered and have no side effects. o_d_error is not checked for them (D-011). — STIMULUS: After reset, with CFG0=0x00030005 and COMPARE_LOWER0_0=0x12345678, send a Get (a_size=2, mask 1111, i_a_instr=1) to each mapped register. Then read every register with i_a_instr=0. — EXPECTED: Each instruction fetch gets exactly one response with o_d_source equal to a_source, o_d_size=2 and o_d_opcode=1. o_d_intg_err=0, and there is no o_alert pulse within 50 cycles. The later data reads return the values that were programmed (all other registers at their reset values). |
| CHK-022 | test | intr | Interrupt raised by tick when mtime >= mtimecmp | RT-T2.2-02, RT-T3.1-03, RT-T4.4-01, RT-T6.2-01, RT-8-05, CP-T1.8.6-02, CP-T1.8.5.1-01, CP-T1.8.1-01, RT-7-05 | IS_0 and o_intr_timer_expired are set when a tick makes mtime reach or pass mtimecmp. They stay set (level, latched) afterwards. — STIMULUS: For (P, S, C) in (0,1,20), (3,3,10) and (47,1,2), with m=ceil(C/S):
1. With CTRL=0, write CFG0=(S<<16)\|P, TIMER_V_LOWER0=0, TIMER_V_UPPER0=0, COMPARE_UPPER0_0=0, COMPARE_LOWER0_0=C and INTR_ENABLE0=1. Clear INTR_STATE0 by writing 0x1.
2. Write CTRL=1 (acceptance edge a0, D beat t0).
3. Watch for m*(P+1)+50 cycles.
4. Write CTRL=0, then read INTR_STATE0 and TIMER_V_LOWER0.
5. Clear the interrupt by writing COMPARE_UPPER0_0=0xFFFFFFFF before the next case. — EXPECTED: - o_intr_timer_expired=0 at every edge before a0+(m-1)*(P+1).
- o_intr_timer_expired=1 at some edge no later than t0+(P+5)+(m-1)*(P+1)+6, and it stays 1 until deactivation.
- INTR_STATE0 reads 0x1.
- TIMER_V_LOWER0 >= C and is a multiple of S. For (3,3,10) it is >= 12. |
| CHK-023 | test | intr | Interrupt raised by a compare write while active | RT-8-06, RT-T3.1-03, RT-7-05 | When a register write while active makes the condition true, IS_0 is 1 no later than CFG0.prescale+1+4 cycles after the write's D beat. — STIMULUS: 1. With CTRL=0, write CFG0=0x00010007 (P=7, S=1), TIMER_V_LOWER0=0, TIMER_V_UPPER0=0, INTR_ENABLE0=1, and leave COMPARE_* at reset.
2. Activate and wait 100 cycles.
3. Write COMPARE_UPPER0_0=0, then COMPARE_LOWER0_0=0x5 (D beat r).
4. Read INTR_STATE0 with acceptance at an edge >= r+12. — EXPECTED: - o_intr_timer_expired=0 until the COMPARE_LOWER0_0 write is accepted.
- o_intr_timer_expired=1 at some edge no later than r+14.
- INTR_STATE0 reads 0x1. |
| CHK-024 | test | intr | Clearing by compare writes; mtime write does not clear | RT-T4.4-03, RT-8-08, RT-8-09, RT-T4.2-06, RT-7-05 | A write to COMPARE_LOWER0_0 or COMPARE_UPPER0_0 that leaves mtimecmp > mtime clears IS_0 and the interrupt within 4 cycles. If mtime >= mtimecmp still holds after the write, IS_0 is 1 again within 4 cycles. Writing TIMER_V alone does not clear the latched state. — STIMULUS: Start from the end state of CHK-023 (active, P=7, IS_0=1, IE_0=1). For each step, r is the D beat of that step's write.
(a) Write COMPARE_UPPER0_0=0x1.
(b) Write COMPARE_UPPER0_0=0x0.
(c) Write COMPARE_LOWER0_0=0xFFFFFFF0.
(d) Write COMPARE_LOWER0_0=0x0.
(e) Write COMPARE_LOWER0_0=0x80 after mtime > 0x100. Write CTRL=0 and wait 20 cycles. Write TIMER_V_LOWER0=0 and TIMER_V_UPPER0=0, read INTR_STATE0, then write COMPARE_LOWER0_0=0x80.
Read INTR_STATE0 at an edge >= r+4 after each compare write. — EXPECTED: (a) and (c): INTR_STATE0 reads 0x0 and o_intr_timer_expired=0 at every edge from r+4 until the next step.
(b) and (d): INTR_STATE0 reads 0x1 and o_intr_timer_expired=1 at every edge >= r+6 (a dip in between is not checked).
(e) After the TIMER_V writes, INTR_STATE0 still reads 0x1 and o_intr_timer_expired stays 1. After the COMPARE_LOWER0_0 write, INTR_STATE0 reads 0x0 and o_intr_timer_expired=0 at every edge >= r+4. |
| CHK-025 | test | intr | INTR_STATE0 rw1c and event re-assertion | RT-T4.4-02, RT-T5.5.1-01, RT-8-04, CP-T1.8.5-02, CP-T1.8.6-05, RG-T1.5.6.1-01, RG-T1.5.6.1-02, RG-T1.5.6.1-05, RT-7-02 | Writing 1 to IS_0 clears it. If the event condition still holds while active, IS_0 returns to 1 within 4 cycles. Writing 0 to IS_0 has no effect. — STIMULUS: (a) Set up active, P=0, S=1, COMPARE=0x0_00000010, IE_0=1, and wait until o_intr_timer_expired=1. Write INTR_STATE0=0x0 and read it. Write INTR_STATE0=0x1 (D beat r) five times, reading INTR_STATE0 at an edge >= r+4 each time.
(b) Write COMPARE_UPPER0_0=0xFFFFFFFF so the condition is false, then write INTR_TEST0=0x1 so IS_0=1. Write INTR_STATE0=0x1 (D beat r) and read it at an edge >= r+4. — EXPECTED: (a) After the write of 0, INTR_STATE0 reads 0x1 and o_intr_timer_expired stays 1 at every edge. After each write of 1, INTR_STATE0 reads 0x1 and o_intr_timer_expired=1 at every edge >= r+6.
(b) INTR_STATE0 reads 0x0 and o_intr_timer_expired=0 at every edge >= r+6, for at least 100 cycles. |
| CHK-026 | test | intr | Interrupt enable masking and raw INTR_STATE0 | CP-T1.8.4-04, CP-T1.8.6-04, CP-T1.8.5.2-06, RT-8-07, RT-T5.4.1-01, RT-6-02, CP-T1.8.4-03, RT-7-05 | o_intr_timer_expired equals IS_0 AND IE_0, except in the 2 cycles after either one changes. INTR_STATE0 is not qualified by IE_0. — STIMULUS: Run the CHK-022 case (0,1,20) with INTR_ENABLE0=0. Then write INTR_ENABLE0=1 (D beat r1), INTR_ENABLE0=0 (D beat r2) and INTR_ENABLE0=1 (D beat r3), reading INTR_STATE0 after each write. — EXPECTED: - o_intr_timer_expired=0 throughout the IE_0=0 run.
- INTR_STATE0 reads 0x1 at any read accepted after t0+(P+5)+19+4.
- o_intr_timer_expired=1 at every edge >= r1+2 until the r2 write is accepted, 0 at every edge >= r2+2 until the r3 write is accepted, and 1 at every edge >= r3+2.
- INTR_STATE0 reads 0x1 after every write. |
| CHK-027 | test | intr | INTR_TEST0 sets the latched state (wo field) | CP-T1.8.6-03, RT-T5.6.1-01, CP-T1.8.4-03, RT-8-10, RT-8-11, RT-7-02, RT-7-05 | Writing 1 to INTR_TEST0.T_0 sets IS_0 even when the condition is false. INTR_TEST0 reads 0. Writing 0 has no effect. — STIMULUS: After reset (inactive, mtime=0, compare at reset value):
1. Write INTR_ENABLE0=1.
2. Write INTR_TEST0=0x1 (D beat r). Read INTR_STATE0 at an edge >= r+4 and read INTR_TEST0.
3. Write INTR_STATE0=0x1 (D beat r').
4. Write INTR_TEST0=0x0 and read INTR_STATE0.
5. Write INTR_TEST0=0xFFFFFFFF and read INTR_TEST0 and INTR_STATE0.
6. Clear IS_0. Write INTR_ENABLE0=0, write INTR_TEST0=0x1, then read INTR_STATE0. — EXPECTED: After step 2: INTR_STATE0 reads 0x1, INTR_TEST0 reads 0x0, and o_intr_timer_expired=1 at every edge from r+6 for 100 cycles (latched).
After step 3: o_intr_timer_expired=0 at every edge >= r'+6.
After step 4: INTR_STATE0 reads 0x0.
After step 5: INTR_TEST0 reads 0x0 and INTR_STATE0 reads 0x1.
After step 6: INTR_STATE0 reads 0x1 and o_intr_timer_expired stays 0. |
| CHK-028 | test | regs | Reset values and register map | RT-T5.1-01, RT-T5.1-02, RT-T5.1-03, RT-T5.1-04, RT-T5.1-05, RT-T5.1-06, RT-T5.1-07, RT-T5.1-08, RT-T5.1-09, RT-T5.1-10, RT-T5.2-01, RT-8-11, RT-7-01, RT-2-04, RT-T3.2.2-01, RT-T3.2.2-04 | After reset, every register reads its documented reset value through a full-word Get at its documented offset. — STIMULUS: Hold rst_ni=0 for 10 cycles and release it synchronously, keeping i_a_valid=0 in the first cycle after release. Then issue one Get (opcode 4, a_size=2, mask 1111, i_a_instr=0, i_a_intg_flip=0, i_d_ready=1) to each of 0x000, 0x004, 0x100, 0x104, 0x108, 0x10C, 0x110, 0x114, 0x118 and 0x11C, one request at a time. — EXPECTED: Every response has o_d_error=0 and o_d_opcode=1. o_d_data is:
- 0x000: 0x80000000
- 0x004: 0x00000000
- 0x100: 0x00000000
- 0x104: 0x00000000
- 0x108: 0x00000000
- 0x10C: 0x00010000
- 0x110: 0x00000000
- 0x114: 0x00000000
- 0x118: 0xFFFFFFFF
- 0x11C: 0xFFFFFFFF

o_intr_timer_expired=0 and o_alert=0 throughout. |
| CHK-029 | test | regs | rw field access types and reserved bits | RT-T5.3.1-01, RT-T5.4.1-01, RT-T5.7.1-01, RT-T5.1-02, RT-T5.1-03, RT-T5.1-06, RT-T5.1-07, RT-T5.1-08, RT-T5.1-09, RT-T5.1-10, RT-8-10, RT-8-23, RT-7-02, RT-1-02, TL-T3.1.3.4-01, TL-T3.1.3.4-04, TL-T3.1.3.4-05 | Each rw field stores the written value. Reserved bits read 0 and ignore writes. Full-word writes with mask 1111 succeed for both PutFullData and PutPartialData. — STIMULUS: With CTRL=0, write CFG0, TIMER_V_LOWER0 (0x110), TIMER_V_UPPER0 (0x114), COMPARE_LOWER0_0 (0x118), COMPARE_UPPER0_0 (0x11C) and INTR_ENABLE0 (0x100). Each register gets the patterns 0xFFFFFFFF, 0x00000000, 0xA5A5A5A5, 0x5A5A5A5A and 8 random values. Use PutFullData (a_size=2, mask 1111) for half the writes and PutPartialData (a_size=2, mask 1111) for the other half, and read the register back with a full-word Get after each write. Then write CTRL with 0xFFFFFFFE, 0xFFFFFFFF and 0x00000000 and read it back after each write. Finish with CTRL=0. — EXPECTED: Every write and read has o_d_error=0. The value read back is:
- CTRL: data & 0x00000001
- INTR_ENABLE0: data & 0x00000001
- CFG0: data & 0x00FF0FFF
- TIMER_V_LOWER0, TIMER_V_UPPER0, COMPARE_LOWER0_0 and COMPARE_UPPER0_0: exactly the data written |
| CHK-030 | test | reset | Asynchronous reset, short reset window, pending response discarded | RT-2-03, RT-2-04, RT-8-29, RT-8-31, TL-T3.1.1-02, CP-T1.5.2-04 | Reset is asserted asynchronously and released synchronously. It brings every register back to its reset value even with a 2-cycle window, and it discards a pending response. — STIMULUS: (a)
1. Program non-reset values into every rw register, set IE_0=1 and IS_0=1 (o_intr_timer_expired=1), and leave the timer active.
2. Drive rst_ni=0 in the middle of a clock period (between rising edges), hold it for 2 cycles, and release it right after a rising edge, with i_a_valid=0 during reset and the first cycle after.
3. Read all registers. Read TIMER_V_LOWER0 again 50 cycles later.
(b)
1. Send a Get to 0x10C with i_d_ready=0 and wait until o_d_valid=1.
2. Assert rst_ni=0 for 3 cycles and release it.
3. Set i_d_ready=1 and idle 20 cycles.
4. Send a new Get to 0x10C with the same a_source. — EXPECTED: (a) o_intr_timer_expired, o_d_valid and o_alert are 0 before the next rising edge after rst_ni falls and while it stays 0. After release, all registers read the CHK-028 reset values, and TIMER_V_LOWER0 still reads 0 after 50 cycles.
(b) o_d_valid=0 while rst_ni=0, and no D beat occurs in the 20 idle cycles. The new Get gets exactly one response with o_d_error=0 and o_d_data=0x00010000. |
| CHK-031 | test | timer | Tick period, step and counting while active | RT-T2.2-01, RT-T3.1-01, RT-T3.1-02, RT-8-01, RT-8-26, RT-T4.1-01, RT-T4.1-02, RT-T5.7.1-01, RT-T5.3.1-01, RT-7-03, RT-7-04, RG-T1.5.1-02, RG-T1.5.1-03 | While active, mtime increases by CFG0.step once every CFG0.prescale+1 cycles, and stops changing when CTRL.active_0 is cleared. — STIMULUS: For each (P, S) in (0,1), (0,0xFF), (1,1), (3,5), (47,1), (0xFFF,0x80) and (10,0):
1. With CTRL=0, write CFG0=(S<<16)\|P, TIMER_V_UPPER0=0 and TIMER_V_LOWER0=V0=0x1000.
2. Write CTRL=1.
3. Read TIMER_V_LOWER0 about every 20*(P+1) cycles, at least 10 times (3 times for P=0xFFF), with i_d_ready=1. The values never come near a carry.
4. Write CTRL=0. Wait P+5 cycles after its D beat, then read TIMER_V_LOWER0 twice, 2*(P+1)+10 cycles apart.
5. Reprogram CFG0 for the next pair only after CTRL=0. — EXPECTED: Each read value v satisfies (v-V0) mod S = 0, and v=V0 when S=0. The values do not decrease.

For any two reads i<j with acceptance edges a_i, a_j and D-beat edges r_i, r_j, and S>0, n=(v_j-v_i)/S is an integer with floor((a_j-r_i)/(P+1)) <= n <= floor((r_j-a_i)/(P+1))+1.

The two reads after deactivation return the same value. |
| CHK-032 | test | timer | Inactive after reset and first-tick latency | RT-8-02, RT-T5.3.1-01, RT-T3.1-02 | The timer does not count while CTRL.active_0=0. The first tick comes no later than CFG0.prescale+1+4 cycles after the D beat of the activating write. — STIMULUS: After reset, read TIMER_V_LOWER0 at 10, 50 and 100 cycles. Then, for P in {0, 5, 47} with S=1:
1. With CTRL=0, write TIMER_V_LOWER0=0 and TIMER_V_UPPER0=0.
2. Write CTRL=1 (acceptance edge a0, D beat t0).
3. Issue a Get of TIMER_V_LOWER0 that is accepted at edge a with t0+P+6 <= a <= t0+P+10, and record its D-beat edge r.
4. Write CTRL=0. — EXPECTED: The three reads after reset return 0. For each P, the read returns v >= 1 and v <= floor((r-a0)/(P+1))+1. |
| CHK-033 | test | timer | Carry from lower to upper half and 64-bit compare | RT-7-04, RT-8-33, RT-7-08, RT-T3.1-03, RT-7-05 | Counting carries from TIMER_V_LOWER0 into TIMER_V_UPPER0. The compare uses all 64 bits, so a larger lower half with a smaller upper half does not raise the interrupt. — STIMULUS: Case A:
1. With CTRL=0, write CFG0=0x00010000 (P=0, S=1), TIMER_V_LOWER0=0xFFFFFFF0, TIMER_V_UPPER0=0x5, COMPARE_UPPER0_0=0x6, COMPARE_LOWER0_0=0x10 and INTR_ENABLE0=1.
2. Write CTRL=1 (acceptance edge a0, D beat t0).
3. Write CTRL=0 so that it is accepted between t0+40 and t0+100.
4. Wait 10 cycles and read TIMER_V_UPPER0 and TIMER_V_LOWER0.

Case B:
1. With CTRL=0, write CFG0=0x00300001 (P=1, S=0x30), TIMER_V_UPPER0=0 and TIMER_V_LOWER0=0xFFFFFFF0.
2. Activate for 50 cycles, deactivate, wait 10 cycles and read both halves. — EXPECTED: Case A:
- o_intr_timer_expired=0 at every edge before a0+31.
- o_intr_timer_expired=1 at some edge no later than t0+42 and stays 1.
- After deactivation, TIMER_V_UPPER0 reads 0x00000006 and 0x10 <= TIMER_V_LOWER0 <= 0x100.

Case B: with V=(UPPER<<32)\|LOWER, V > 0xFFFFFFF0, (V-0xFFFFFFF0) mod 0x30 = 0 and TIMER_V_UPPER0=0x00000001. |
| CHK-034 | test | timer | Behaviour near 2^64: wrap and intermediate interrupt | RT-7-08, RT-8-33, RT-T4.3-02, RT-T4.3-05, RT-7-04 | mtime wraps modulo 2^64. With mtimecmp set to 2^64-step, the interrupt fires before the wrap and stays latched after it. — STIMULUS: Case A:
1. With CTRL=0, write CFG0=0x00030000 (P=0, S=3), TIMER_V_UPPER0=0xFFFFFFFF, TIMER_V_LOWER0=0xFFFFFFE0, COMPARE_UPPER0_0=0xFFFFFFFF, COMPARE_LOWER0_0=0xFFFFFFFD and INTR_ENABLE0=1.
2. Write CTRL=1 (acceptance edge a0, D beat t0).
3. Deactivate about 60 cycles later, wait 10 cycles, then read TIMER_V_UPPER0, TIMER_V_LOWER0 and INTR_STATE0.
4. Write INTR_STATE0=0x1 (D beat r), then read INTR_STATE0 at an edge >= r+4.

Case B:
1. With CTRL=0 and CFG0=0x00010000, write TIMER_V_UPPER0=0xFFFFFFFF and TIMER_V_LOWER0=0xFFFFFFFF.
2. Activate for 30 cycles, deactivate, wait 10 cycles and read both halves. — EXPECTED: Case A:
- o_intr_timer_expired=0 at every edge before a0+9.
- o_intr_timer_expired=1 at some edge no later than t0+20 and still 1 after the wrap.
- TIMER_V_UPPER0 reads 0x0, TIMER_V_LOWER0 < 0x100 and (TIMER_V_LOWER0+0x20) mod 3 = 0.
- INTR_STATE0 reads 0x1.
- After the W1C, INTR_STATE0 reads 0x0 and o_intr_timer_expired=0 at every edge >= r+6.

Case B: TIMER_V_UPPER0 reads 0x0 and TIMER_V_LOWER0 < 0x100. |
| CHK-035 | test | tlul | Outstanding requests and back-pressure | RT-8-25, TL-T3.1.3.2-01, RT-4.1-04, RT-1-02, TL-T3.1.3.4-01 | Correct responses under pipelined requests, random o_a_ready stalls and random i_d_ready back-pressure. Responses are matched by d_source. — STIMULUS: With CTRL=0, send 2000 random legal requests: full-word Get, PutFullData and PutPartialData (mask 1111) to CFG0, TIMER_V_LOWER0, TIMER_V_UPPER0, COMPARE_LOWER0_0, COMPARE_UPPER0_0 and INTR_ENABLE0, plus Gets to every mapped register. Allow up to 4 outstanding requests with distinct a_source values from 0 to 255. Assert i_a_valid without waiting for o_a_ready and hold the request until it is accepted. Drive i_d_ready randomly at 50%. Never have a write and another access to the same register outstanding at the same time. — EXPECTED: Each accepted request gets exactly one response, matched by o_d_source, with o_d_error=0. Each read returns the reference model value, which is the last written data masked by the field mask (CFG0 0x00FF0FFF, INTR_ENABLE0 0x1, other registers 0xFFFFFFFF). Registers not written hold their reset values. |

## Not verified by simulation

| Rule | Reason | Note |
|---|---|---|
| RT-1-04 | static_or_structural | The alert sender/receiver clocking scheme is a structural choice inside the wrapper. |
| RT-1-06 | static_or_structural | There is a single fixed configuration and no parameter to sweep. |
| RT-T6.1-01 | not_applicable_to_dut | The DUT interface has no racl_policies port, and RACL is disabled (RT-1-02). |
| RT-4.1-03 | not_observable_at_interface | a_user.instr_type is generated inside the wrapper. Its effect is exercised by CHK-021. |
| RT-4.2-02 | not_observable_at_interface | The inverted cmd_intg bit is internal. Its consequence (the fatal alert) is checked by CHK-016. |
| RT-5-01 | static_or_structural | The single alert and its sender are structural. Alert behaviour is checked by CHK-014 and CHK-016. |
| TL-T2.2-01 | not_applicable_to_dut | This is about reusing base TL-UL IP. The wrapper produces the sideband (user) signals. |
| TL-T2.3-01 | not_applicable_to_dut | This is about compatibility between base and extended blocks. User bits are out of scope (D-019). |
| TL-T2.3-02 | not_applicable_to_dut | This binds baseline blocks. The DUT is an extended (OpenTitan) device, and user bits are out of scope (D-019). |
| TL-T2.3-03 | not_applicable_to_dut | User-bit default values are not checked (D-019). |
| TL-T3.1.3.1-01 | not_applicable_to_dut | This binds the interconnect's request steering. There is no fabric between the test bench and the DUT. |
| TL-T3.1.3.2-02 | not_applicable_to_dut | This is a fabric architect obligation (AIW sizing). |
| TL-T3.1.3.2-03 | not_applicable_to_dut | This is a fabric obligation for host ID bits. |
| TL-T3.1.3.2.1-01 | not_applicable_to_dut | This binds bus primitives that grow source IDs. There are none in this environment. |
| TL-T3.1.3.2.1-02 | not_applicable_to_dut | This is a recommendation for M:1 sockets. |
| TL-T3.1.3.2.2-01 | not_applicable_to_dut | This binds hosts behind a fabric. The DUT is a device, and its full d_source echo is checked by CHK-009. |
| TL-T3.1.3.3-01 | design_guideline | This is general advice on user-bit usage. User-bit layout is out of scope (D-019). |
| TL-T3.1.3.3-03 | not_applicable_to_dut | This binds the bus fabric. |
| TL-T3.1.3.5-10 | design_guideline | This only permits additional checks. There is nothing specific to observe. |
| CP-T1.5.2-01 | static_or_structural | This is clocking metadata in the hjson description. |
| CP-T1.5.2-02 | static_or_structural | This is clocking metadata. |
| CP-T1.5.2-03 | static_or_structural | This is a clock assignment. The DUT has the single clock clk_i. |
| CP-T1.5.2-05 | design_guideline | This is advice for security-sensitive storage. There is nothing specified to observe. |
| CP-T1.5.2-06 | static_or_structural | This is clocking metadata. |
| CP-T1.5.2-07 | static_or_structural | This is clocking metadata. |
| CP-T1.5.3-02 | static_or_structural | The presence of a device interface is structural. |
| CP-T1.5.3-03 | static_or_structural | This concerns the bus host role. The DUT is a device only. |
| CP-T1.5.3-04 | static_or_structural | This is hjson metadata. |
| CP-T1.5.3-05 | static_or_structural | This is hjson metadata. |
| CP-T1.5.3-06 | static_or_structural | This is hjson metadata. |
| CP-T1.5.3-07 | static_or_structural | The single clk_i drives both the test bench host and the DUT. |
| CP-T1.5.3-08 | static_or_structural | This concerns port naming. |
| CP-T1.5.3-09 | static_or_structural | This concerns port naming. |
| CP-T1.5.5-01 | static_or_structural | This concerns the interrupt port name inside rv_timer. |
| CP-T1.6-01 | static_or_structural | This is a general conformance statement. The register behaviour itself is checked by CHK-017, CHK-018, CHK-019, CHK-020, CHK-028, CHK-029. |
| CP-T1.8-01 | static_or_structural | This concerns interrupt naming and interface conventions. |
| CP-T1.8.2-01 | static_or_structural | This is hjson schema. |
| CP-T1.8.2-02 | static_or_structural | This is hjson schema. |
| CP-T1.8.2-03 | static_or_structural | This is hjson schema. rv_timer's interrupt is of Event type. |
| CP-T1.8.3-01 | static_or_structural | There is one interrupt source and one wired output port, o_intr_timer_expired. |
| CP-T1.8.3-02 | static_or_structural | This is an interrupt architecture statement. |
| CP-T1.8.4-01 | not_applicable_to_dut | The rv_timer register table puts INTR_ENABLE0, INTR_STATE0 and INTR_TEST0 at 0x100, 0x104 and 0x108, which overrides the generic placement. These offsets are checked in CHK-028, CHK-026 and CHK-027. |
| CP-T1.8.4-02 | static_or_structural | This is an hjson limit. |
| CP-T1.8.5-03 | not_applicable_to_dut | This is Status-type behaviour. rv_timer has only an Event-type interrupt (designer decision, D-019). |
| CP-T1.8.5.2-01 | not_applicable_to_dut | This is a Status-type interrupt rule, out of scope by designer decision. |
| CP-T1.8.5.2-02 | not_applicable_to_dut | This is a Status-type interrupt rule, out of scope by designer decision. |
| CP-T1.8.5.2-03 | not_applicable_to_dut | This is a Status-type interrupt rule, out of scope by designer decision. |
| CP-T1.8.5.2-05 | not_applicable_to_dut | This is software advice for Status-type interrupts. |
| CP-T1.9.1-03 | not_applicable_to_dut | rv_timer has no recoverable alert. |
| CP-T1.9.1-05 | design_guideline | This is a recommendation about local countermeasures. None are specified for rv_timer. |
| CP-T1.9.1-07 | design_guideline | This is an optional IRQ per alert. rv_timer specifies none. |
| CP-T1.9.2-02 | static_or_structural | This concerns alert naming (fatal_fault). |
| CP-T1.9.2-03 | static_or_structural | This concerns alert naming. |
| CP-T1.9.4-01 | covered_by_other_check | The internal event polarity is not visible. Its effect is checked by CHK-014 and CHK-016. |
| CP-T1.9.4-03 | design_guideline | This is maintainer's choice of alert bundling. |
| CP-T1.9.4-04 | design_guideline | This is a bundling recommendation. |
| CP-T1.9.4-05 | not_applicable_to_dut | rv_timer has a single alert and no cause register. |
| CP-T1.9.4-06 | not_applicable_to_dut | rv_timer has no recoverable alert or cause register. |
| CP-T1.9.4-07 | not_applicable_to_dut | rv_timer has no fatal cause register (designer decision). |
| CP-T1.9.4-08 | covered_by_other_check | The differential pair is internal. Correct signalling is shown by the o_alert pulses in CHK-014 and CHK-016 and by o_alert_integ_fail=0 in CHK-001. |
| RG-T1.3-03 | static_or_structural | This concerns internal reg2hw struct contents. |
| RG-T1.3-04 | static_or_structural | This concerns internal hw2reg struct contents. |
| RG-T1.4.1-02 | not_applicable_to_dut | Requests at 0x200 and above are not used (D-012, RT-8-20), so address aliasing is not exercised. |
| RG-T1.4.1-06 | covered_by_other_check | This is only partly covered. CHK-018 checks the aligned sub-word write cases that D-013 selects. D-013 excludes unaligned sub-word writes from checking. |
| RG-T1.4.1-09 | not_applicable_to_dut | rv_timer has no register windows. |
| RG-T1.5.1-01 | not_observable_at_interface | A software write in the same cycle as a hardware update cannot be aligned through the bus. Writes to TIMER_V and CFG0 while active are excluded (D-002). |
| RG-T1.5.1-05 | not_observable_at_interface | qe is an internal register-to-hardware signal. |
| RG-T1.5.3-02 | not_applicable_to_dut | rv_timer has no ro hwext hardwired registers. |
| RG-T1.5.4-01 | not_applicable_to_dut | rv_timer has no read-clear (RC) registers. |
| RG-T1.5.6.1-04 | design_guideline | This is an implementation recommendation for the hardware feeding RW1C registers. |
| RG-T1.5.6.2-01 | not_observable_at_interface | Whether a field is hwext is an implementation choice that cannot be seen through the ports. |
| RG-T1.5.6.2-02 | not_observable_at_interface | This concerns the internal implementation of hwext registers. |
| RG-T1.5.6.2-03 | not_observable_at_interface | hwqe is internal. |
| AH-T1.3.1-02 | static_or_structural | This concerns instantiation of prim_alert_sender. |
| AH-T1.3.4-01 | not_observable_at_interface | The alert differential pairs are internal to the wrapper, so encoding faults cannot be injected through the ports. The correct case (o_alert_integ_fail=0) is checked by CHK-001. |
| AH-T1.3.4-02 | not_observable_at_interface | ping/ack encoding faults cannot be injected through the ports. CHK-001 covers the fault-free case. |
| AH-T1.3.4-03 | not_observable_at_interface | Lock-up through signal-integrity faults cannot be provoked from the ports. |

## Assumptions

- Timing notation: 'edge' means a rising edge of clk_i. The acceptance edge of a request is the edge with i_a_valid=1 and o_a_ready=1. Its D beat (response edge) is the edge with o_d_valid=1, i_d_ready=1 and the matching o_d_source. 'N cycles after the write response' means N rising edges after that D beat.
- The test bench changes inputs only immediately after rising edges of clk_i. Reset is released right after a rising edge.
- The specification gives no latency for these events: IS_0 setting after an INTR_TEST0 write, IS_0 clearing by W1C when the condition is false, and the timer stopping after CTRL.active_0 is written 0. The plan uses the 4-cycle IS_0 bound of D-005/D-006 (plus 2 cycles for o_intr_timer_expired), and P+1+4 cycles for the timer to stop.
- The D-013 text is cut off after 'Reads of any size'. Per RG-T1.4.1-07/08, aligned sub-word Gets whose mask is exactly the active lanes are taken to return the full register word with d_error=0.
- A Get whose mask has bits outside its active lanes, and a PutFullData with a_size=2 and an incomplete mask, are taken to be d_error=1 cases (TL-T3.1.3.5-03/04, RT-4.1-06). For these and for undefined opcodes, only the response is checked, not register side effects.
- IS_0 is a latched event (CP-T1.8.6-06). Only W1C to INTR_STATE0, writes to COMPARE_LOWER0_0 or COMPARE_UPPER0_0 (RT-T4.4-03/D-006), or reset clear it. Writing TIMER_V_* or CTRL does not clear it, and it stays 1 after mtime wraps below mtimecmp.
- The generic comportability offsets and order for INTR_STATE, INTR_ENABLE and INTR_TEST (0x0, 0x4, 0x8) are overridden by the rv_timer register table (0x100 ENABLE, 0x104 STATE, 0x108 TEST).
- The byte writes of D-013 are issued as PutPartialData with a_size=0 and mask 0001.
- A tick cannot occur before the edge at which the activating CTRL write is accepted. This gives the lower bounds on interrupt timing and on tick counts.
