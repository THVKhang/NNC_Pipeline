# Verification contract (Gate 2)

```
interface: 32 ports, 2 parameters, clock clk_i, reset {'name': 'rst_ni', 'active_low': True}
checks: 38 {'assertion': 13, 'test': 25}  rules 268: in checks 188, not verified 80, uncovered 0 (after first pass 0), unknown IDs 0
calls: 1 (0 cached)  cost US$1.7198
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
| i_gpio | input | 32 |  |
| o_gpio | output | 32 |  |
| o_gpio_en | output | 32 |  |
| o_intr_gpio | output | 32 |  |
| i_strap_en | input | 1 |  |
| o_straps_valid | output | 1 |  |
| o_straps_data | output | 32 |  |

## Checks

| ID | Kind | Group | Title | Rules | Behavior / expected |
|---|---|---|---|---|---|
| CHK-001 | assertion | alert | Alert signal integrity never fails | GP-5-03, GP-5-04, GP-3-05, GP-10-33, AH-T1.3.4-01 | At every rising edge of clk_i with rst_ni=1, o_alert_integ_fail=0. This includes the time while the alert is firing after a write to ALERT_TEST or after an integrity error. |
| CHK-002 | assertion | alert | o_alert is a single-cycle pulse | GP-5-02 | If o_alert=1 at rising edge N with rst_ni=1, then o_alert=0 at rising edge N+1. |
| CHK-003 | assertion | alert | No alert without an alert cause | GP-4.2-01 | o_alert may be 1 at rising edge N (rst_ni=1) only if one of these holds since the last reset release:
(a) an A handshake with i_a_intg_flip=1 took place at an edge at or before N, or
(b) an A handshake of a write (a_opcode 0 or 1) to 0xC (ALERT_TEST) with i_a_data[0]=1 took place, and its D handshake is still pending or happened at edge N-16 or later.
So traffic with i_a_intg_flip=0 (correct integrity added by the wrapper) never raises an alert. |
| CHK-004 | assertion | gpio | o_gpio / o_gpio_en follow the DATA_OUT / DATA_OE shadow model | GP-3-06, GP-3-07, GP-10-38, GP-6-01, GP-10-03, GP-T3.2.1-06 | Shadow model: shadow_out and shadow_oe start at 32'h0 while rst_ni=0. At the D handshake of a write (a_opcode 0 or 1) with o_d_error=0, the shadow is updated from the stored address and data:
- 0x14 DIRECT_OUT: shadow_out=data.
- 0x18 MASKED_OUT_LOWER: for i in 0..15, if data[16+i]=1 then shadow_out[i]=data[i].
- 0x1C MASKED_OUT_UPPER: for i in 0..15, if data[16+i]=1 then shadow_out[16+i]=data[i].
- 0x100+4*i PER_PIN_IO_i: shadow_out[i]=data[0].
- 0x20 DIRECT_OE: shadow_oe=data.
- 0x24 MASKED_OE_LOWER and 0x28 MASKED_OE_UPPER: same rule as MASKED_OUT_* applied to shadow_oe.
- 0x200+8*i PER_PIN_OE_i: shadow_oe[i]=data[0].
Let Ed be the D handshake edge of the last such write. At every rising edge from Ed+2 until the next A handshake of a write to one of these addresses: o_gpio==shadow_out and o_gpio_en==shadow_oe. Also from reset release until the first write: o_gpio=0 and o_gpio_en=0. The check is disabled from an A handshake with i_a_intg_flip=1 until rst_ni=0. |
| CHK-005 | assertion | integ | D-channel response integrity never fails | GP-4.3-01, GP-4.3-02, GP-3-03, GP-10-33, TL-T3.1.3.3-02 | At every rising edge of clk_i with rst_ni=1, o_d_intg_err=0, whether o_d_valid is 0 or 1. The check stays on after a request with i_a_intg_flip=1, because D-017 requires it in every cycle with rst_ni=1. Runs in all four configurations. |
| CHK-006 | assertion | intr | Disabled interrupts never assert o_intr_gpio | GP-10-05, CP-T1.8.4-03, CP-T1.8.6-04 | Shadow model: shadow_en=0 while rst_ni=0. At the D handshake (edge Ed) of a write to 0x4 (INTR_ENABLE) with o_d_error=0, shadow_en=data. For each i: if shadow_en[i]=0 and the edge is at least Ed+2 after the last INTR_ENABLE write (or no write since reset), then o_intr_gpio[i]=0. The check is disabled from an A handshake with i_a_intg_flip=1 until rst_ni=0. |
| CHK-007 | assertion | intr | Interrupt level is held until software acknowledges it | CP-T1.8.6-06, CP-T1.8.5-01, CP-T1.8.1-01 | For each i: if o_intr_gpio[i]=1 at rising edge N and o_intr_gpio[i]=0 at N+1 with rst_ni=1 at both edges, then a qualifying write must be in progress around N+1. A qualifying write is either a write to 0x0 (INTR_STATE) with i_a_data[i]=1 or a write to 0x4 (INTR_ENABLE) with i_a_data[i]=0. Its A handshake must be at or before N+1, and its D handshake must be at or after N-1 or not yet done. In other words, only a software W1C or a software mask can lower an asserted interrupt; hardware never clears it. The check is disabled from an A handshake with i_a_intg_flip=1 until rst_ni=0. |
| CHK-008 | assertion | reset | Outputs held at zero during reset | GP-10-31, GP-10-03, GP-2-06 | At every rising edge and every falling edge of clk_i at which rst_ni=0, all of these must be 0: o_d_valid, o_alert, o_alert_integ_fail, o_intr_gpio (32'h0), o_gpio (32'h0) and o_gpio_en (32'h0). This includes the first clock edge after rst_ni falls asynchronously. o_a_ready, o_straps_valid and o_straps_data are not checked. |
| CHK-009 | assertion | strap | Strap outputs: invalid before the trigger, frozen after sampling | GP-10-12, GP-10-13, GP-T6.2-02, GP-T3.2.3.1-02 | Only when GpioAsHwStrapsEn=1.
(a) At every rising edge with rst_ni=1 where i_strap_en has been 0 at every rising edge since reset release: o_straps_valid=0.
(b) If o_straps_valid=1 at rising edge N with rst_ni=1, and rst_ni=1 at N+1, then at N+1 o_straps_valid=1 and o_straps_data equals its value at N, whatever i_gpio and i_strap_en do. |
| CHK-010 | assertion | timing | Outputs change only at rising clock edges | GP-2-02 | Every change of any output (o_a_ready, o_d_*, o_d_intg_err, o_alert, o_alert_integ_fail, o_gpio, o_gpio_en, o_intr_gpio, o_straps_valid, o_straps_data) happens in the simulation time step of a rising edge of clk_i. Equivalently, each output sampled at a falling edge of clk_i equals its value sampled just before the next rising edge. Not applied in clock cycles where rst_ni is 0 or falls. |
| CHK-011 | assertion | tlhost | Test-bench stimulus legality monitor (host rules and plan constraints) | GP-4.1-04, GP-10-30, GP-10-26, GP-10-21, GP-10-19, GP-10-10, GP-2-04, TL-T3.1.3.4-02, TL-T3.1.3.4-04 | This monitor checks the stimulus and flags test-bench errors, not DUT errors.
(a) If at rising edge N rst_ni=1, i_a_valid=1 and o_a_ready=0, then at N+1: i_a_valid=1, and i_a_opcode, i_a_param, i_a_size, i_a_source, i_a_address, i_a_mask, i_a_data, i_a_instr and i_a_intg_flip are unchanged.
(b) i_a_valid=0 at every edge with rst_ni=0 and at the first rising edge after rst_ni rises.
(c) No A handshake uses an i_a_source equal to that of a request still outstanding.
(d) Whenever i_a_valid=1: i_a_address<32'h400; not (i_a_instr=1 and i_a_opcode in {0,1}); i_a_mask is in {0001,0010,0100,1000,0011,1100,1111}; and i_a_opcode=0 implies i_a_size=2.
(e) If GpioAsHwStrapsEn=1: i_strap_en=0 while rst_ni=0 and at the first 4 rising edges after release. Let Es be the first rising edge after release at which i_strap_en=1. i_gpio has the same value at every rising edge from Es-24 to Es+8.
(f) If GpioAsyncOn=0: every input, i_gpio included, has the same value at each falling edge of clk_i as at the following rising edge, i.e. it changes only just after rising edges. |
| CHK-012 | assertion | tlul | D channel held stable under back-pressure | GP-4.1-01 | If at rising edge N rst_ni=1, o_d_valid=1 and i_d_ready=0, and rst_ni is still 1 at rising edge N+1, then at N+1: o_d_valid=1, and o_d_opcode, o_d_param, o_d_size, o_d_source, o_d_sink, o_d_data and o_d_error equal their values at N. |
| CHK-013 | assertion | tlul | Response matches an outstanding request (source/size/opcode echo, no orphans) | TL-T3.1.3.2.3-01, GP-10-27, TL-T2.2-03, TL-T3.1.3.5-08, GP-10-28, GP-10-32, GP-4.1-01 | The checker records each A handshake: a rising edge with rst_ni=1, i_a_valid=1 and o_a_ready=1. It stores i_a_source, i_a_size and i_a_opcode. At each D handshake (a rising edge with rst_ni=1, o_d_valid=1 and i_d_ready=1):
- Exactly one recorded entry accepted at an earlier edge and not yet answered must have a_source equal to o_d_source. That entry is removed, so every request gets exactly one response beat.
- If the stored opcode is 4 (Get): o_d_opcode=1 (AccessAckData) and o_d_size equals the stored a_size.
- If the stored opcode is 0 or 1: o_d_opcode=0 (AccessAck) and o_d_size equals the stored a_size.
- If the stored opcode is 2, 3, 5, 6 or 7: only o_d_error=1 is checked.
- A D handshake with no matching entry is a failure (orphan response).
All entries are cleared at any edge where rst_ni=0, so a D beat after reset for a request accepted before reset is an orphan (the pending response must be discarded). The checker is disabled from an A handshake with i_a_intg_flip=1 until the next rst_ni=0. o_d_param and o_d_sink are not checked. |
| CHK-014 | test | alert | ALERT_TEST.fatal_fault triggers exactly one o_alert pulse | GP-T5.5.1-02, GP-5-01, GP-5-02, GP-5-06, GP-10-15, GP-10-17, GP-3-04, CP-T1.9.3-01, CP-T1.9.3-02, AH-T1.3.2-01, AH-T1.3.2-05, GP-9-06 | Each write of 1 to ALERT_TEST.fatal_fault, with regwen kept at 1, causes exactly one o_alert pulse within 16 cycles of the write response. — STIMULUS: Three times, separated by at least 64 idle cycles: write ALERT_TEST=32'h8000_0001 (never 32'h0000_0001) with no other alert cause, then observe 64 cycles. Finally read ALERT_TEST. — EXPECTED: - Each write completes with d_error=0.
- After each write, exactly one o_alert pulse (1 for one cycle) occurs no later than 16 cycles after the D handshake, and no other pulse occurs in the 64-cycle window.
- ALERT_TEST reads 32'h8000_0000. o_alert_integ_fail stays 0. |
| CHK-015 | test | alert | ALERT_TEST.regwen rw0c locks alert testing until reset | GP-T5.5.1-01, GP-10-16, GP-10-18 | Writing 0 to regwen disables alert testing until the next reset. — STIMULUS: 1. After reset, read ALERT_TEST.
2. Write ALERT_TEST=32'h0000_0000 and read it.
3. Write ALERT_TEST=32'h8000_0001, observe 64 cycles, and read it.
4. Assert rst_ni for 10 cycles and release it. Read ALERT_TEST, write 32'h8000_0001, and observe 64 cycles. — EXPECTED: - Step 1 reads 32'h8000_0000.
- Step 2 reads 32'h0000_0000.
- Step 3: the write gives d_error=0, no o_alert pulse occurs in the 64 cycles, and ALERT_TEST still reads 32'h0000_0000.
- Step 4: ALERT_TEST reads 32'h8000_0000, and the write gives exactly one o_alert pulse within 16 cycles of its response. |
| CHK-016 | test | alert | Command integrity error raises the fatal alert, repeated until reset | GP-3-02, GP-4.2-02, GP-4.2-03, GP-5-05, GP-T6.4-01, GP-10-34, CP-T1.9.1-04, AH-T1.3.2-01, AH-T1.3.2-03, GP-9-06 | A request with corrupted command integrity starts the fatal alert, which repeats until reset and stops after reset. — STIMULUS: 1. Run normal traffic (i_a_intg_flip=0) for 100 cycles.
2. Send one Get to 0x10 with i_a_intg_flip=1 and a unique a_source (in a second run, a PutFullData to 0x14). Wait at most 32 cycles for its response.
3. Observe 512 cycles.
4. Assert rst_ni for 10 cycles and release it.
5. Run 256 cycles of normal traffic with i_a_intg_flip=0. — EXPECTED: - No o_alert pulse during step 1.
- After the flipped request is accepted at edge Ea, the first o_alert pulse occurs at or before Ea+16. Then there are never 32 consecutive rising edges without an o_alert pulse until rst_ni falls.
- The response, its effect on registers and later requests are not checked.
- o_alert=0 while rst_ni=0.
- After release, there is no o_alert pulse in the 256 cycles, normal accesses give d_error=0, and registers read their reset values.
- o_alert_integ_fail and o_d_intg_err stay 0. |
| CHK-017 | test | filter | Input noise filter on DATA_IN and interrupt detection | GP-T2.2-05, GP-T3.2.3-03, GP-T5.17-01, GP-10-07, GP-10-08, GP-10-09, GP-T3.2.4-06, GP-9-03 | With the filter on, a pulse of at most 12 cycles is filtered out of DATA_IN and interrupt detection, and a change held for at least 24 cycles gets through. The filter is set per bit. — STIMULUS: Bits under test: i in {0,15,16,31}; j=i^1 is the companion bit with the filter off.
1. Hold i_gpio=0. Write CTRL_EN_INPUT_FILTER = (1<<i), INTR_CTRL_EN_RISING = INTR_CTRL_EN_FALLING = (1<<i)\|(1<<j), INTR_ENABLE = (1<<i)\|(1<<j). Wait 24 cycles with i_gpio constant. Clear INTR_STATE by writing 32'hFFFF_FFFF.
2. Short pulse: drive i_gpio[i] and i_gpio[j] to 1 for exactly 12 cycles (E0..E0+11), then back to 0. Poll DATA_IN back-to-back from E0 to E0+50.
3. Long change: drive i_gpio[i] to 1 and hold it for 40 cycles from edge E1. Read DATA_IN accepted at E1+24 or later, and INTR_STATE accepted at E1+28 or later. — EXPECTED: - Step 2:
  - DATA_IN[i] reads 0 in every poll, INTR_STATE[i] reads 0, and o_intr_gpio[i]=0 throughout.
  - Bit j (filter off) reads 1 in DATA_IN for polls accepted between E0+4 and E0+11, and INTR_STATE[j]=1 for reads accepted at E0+8 or later.
- Step 3:
  - DATA_IN[i] reads 1 for reads accepted at E1+24 or later.
  - INTR_STATE[i] reads 1 for reads accepted at E1+28 or later.
  - o_intr_gpio[i]=1 from E1+30.
- All responses have d_error=0. |
| CHK-018 | test | gpio | Direct write of DATA_OUT through DIRECT_OUT | GP-T2.2-01, GP-T3.2.1-01, GP-3-06, GP-10-38, GP-9-02, GP-6-01 | DIRECT_OUT writes and reads all 32 bits of DATA_OUT at once, and o_gpio follows. — STIMULUS: Write DIRECT_OUT with: 32'h0000_0001 shifted left by k for k=0..31 (walking ones), 32'hFFFF_FFFF, 32'h0, and 50 random 32-bit values. After each write, read DIRECT_OUT (0x14), MASKED_OUT_LOWER (0x18) and MASKED_OUT_UPPER (0x1C). — EXPECTED: Let V be the value written.
- DIRECT_OUT reads V.
- MASKED_OUT_LOWER reads {16'h0, V[15:0]}.
- MASKED_OUT_UPPER reads {16'h0, V[31:16]}.
- o_gpio==V at every rising edge from 2 cycles after the write's D handshake until the next write.
- All responses have d_error=0. |
| CHK-019 | test | gpio | Masked writes of DATA_OUT through MASKED_OUT_LOWER / MASKED_OUT_UPPER | GP-T2.2-02, GP-T3.2.1-02, GP-T3.2.1-03, GP-T5.8-01, GP-T5.8-02, GP-T5.9-01, GP-T5.9-02, GP-10-02, GP-9-02 | A masked write changes only the bits whose mask bit is 1. Reads return the selected half of DATA_OUT in bits 15:0 and zero in the mask field. — STIMULUS: 1. Write DIRECT_OUT=32'h1234_5678.
2. Write MASKED_OUT_LOWER=32'h00FF_ABCD.
3. Write MASKED_OUT_UPPER=32'hF0F0_FFFF.
4. Write MASKED_OUT_LOWER=32'h0000_FFFF (mask 0).
5. Write MASKED_OUT_UPPER=32'h0000_0000 (mask 0).
6. Run 100 random masked writes to either register with random mask and data.
Read DIRECT_OUT, MASKED_OUT_LOWER and MASKED_OUT_UPPER after each write. — EXPECTED: - After step 2: DIRECT_OUT=32'h1234_56CD.
- After step 3: DIRECT_OUT=32'hF2F4_56CD.
- After steps 4 and 5: DIRECT_OUT unchanged at 32'hF2F4_56CD; MASKED_OUT_LOWER reads 32'h0000_56CD and MASKED_OUT_UPPER reads 32'h0000_F2F4.
- Random writes: DATA_OUT[h*16+i]=data[i] where mask[i]=1 and is unchanged where mask[i]=0 (h=0 for LOWER, 1 for UPPER). MASKED_OUT_* bits 31:16 always read 0.
- o_gpio equals the expected DATA_OUT from 2 cycles after each write response.
- All responses have d_error=0. |
| CHK-020 | test | gpio | DATA_OE: direct and masked writes, reads and o_gpio_en | GP-T3.2.1-05, GP-T5.10-01, GP-T5.11-01, GP-T5.11-02, GP-T5.12-01, GP-T5.12-02, GP-10-01, GP-10-02, GP-3-07, GP-10-38, GP-9-02, GP-T3.2.1-06 | DATA_OE has the same direct and masked write semantics as DATA_OUT, and o_gpio_en follows DATA_OE. — STIMULUS: 1. Write DIRECT_OE (0x20) with walking ones, 32'hFFFF_FFFF, 32'h0 and random values.
2. Write DIRECT_OE=32'h1234_5678, then MASKED_OE_LOWER (0x24)=32'h00FF_ABCD, then MASKED_OE_UPPER (0x28)=32'hF0F0_FFFF, then mask-0 writes to both.
3. Run 100 random masked writes.
Read DIRECT_OE, MASKED_OE_LOWER and MASKED_OE_UPPER after each write. — EXPECTED: - After each DIRECT_OE write of V: DIRECT_OE reads V, and o_gpio_en==V from 2 cycles after the response. Each bit i set to 1 gives o_gpio_en[i]=1.
- The step 2 sequence gives DATA_OE=32'h1234_56CD, then 32'hF2F4_56CD, then unchanged after the mask-0 writes.
- Random masked writes update only bits whose mask is 1.
- Bits 15:0 of MASKED_OE_LOWER equal DATA_OE[15:0], and bits 15:0 of MASKED_OE_UPPER equal DATA_OE[31:16]. Bits 31:16 of MASKED_OE_* reads are not checked.
- o_gpio_en equals the expected DATA_OE from 2 cycles after each write response. o_gpio is not affected.
- d_error=0 on every response. |
| CHK-021 | test | gpio | DATA_IN with filter off follows i_gpio only (both GpioAsyncOn values) | GP-T2.2-03, GP-T3.2.3-01, GP-10-35, GP-10-43, GP-6-03, GP-T3.2.1-07, GP-2-03, GP-2-04, GP-9-03, GP-6-01 | With the filter off, a held change of i_gpio shows in DATA_IN within 4 cycles, whatever DATA_OUT and DATA_OE are. — STIMULUS: 1. CTRL_EN_INPUT_FILTER=0. Write DIRECT_OE=32'hFFFF_FFFF.
2. Drive i_gpio with walking ones, walking zeros and 100 random values, each held for at least 8 cycles. Before each new value V, write DIRECT_OUT=~V.
3. With GpioAsyncOn=1, change i_gpio at random times within the clock period. With GpioAsyncOn=0, change it only just after rising edges.
4. Let E0 be the first rising edge at which i_gpio has the new value. Send a Get of DATA_IN accepted at E0+4 or later (before the next change), and a Get of PER_PIN_IO_i for i in {0,15,16,31}.
5. Repeat with DIRECT_OE=0. — EXPECTED: - DATA_IN reads V, not o_gpio and not DATA_OUT.
- PER_PIN_IO_i bit 8 equals V[i].
- d_error=0. Identical results with DIRECT_OE=32'hFFFF_FFFF and with DIRECT_OE=0. |
| CHK-022 | test | intr | Edge interrupts: rising, falling, both; latching, W1C, raw INTR_STATE | GP-T5.13-01, GP-T5.14-01, GP-T3.2.4-04, GP-T3.2.4-03, GP-T3.2.4-05, GP-T3.2.4-07, GP-T3.2.4-02, GP-T5.2.1-01, GP-T6.3-01, GP-T2.2-04, GP-7-01, GP-10-04, GP-10-36, GP-10-37, GP-9-04, CP-T1.8.4-05, CP-T1.8.5-01, CP-T1.8.5.1-01, CP-T1.8.6-02, CP-T1.8.6-06, RG-T1.5.1-02 | A configured edge on GPIO i sets INTR_STATE[i] within the D-018 bound and raises o_intr_gpio[i]. The interrupt stays latched until a W1C write, and INTR_STATE is not masked by INTR_ENABLE. — STIMULUS: Filter off. For i in {0,15,16,31} and 4 random bits:
1. Rising: i_gpio=0. Write INTR_CTRL_EN_RISING=(1<<i), others 0, and INTR_ENABLE=(1<<i). Drive i_gpio[i] 0->1 at E0 and hold for 20 cycles. Read INTR_STATE at E0+8 or later. Drive i_gpio[i] 1->0, hold 20 cycles, read INTR_STATE. Write INTR_STATE=~(1<<i), read it. Write INTR_STATE=(1<<i), read it.
2. Falling: the same with INTR_CTRL_EN_FALLING and the opposite edges.
3. Both: RISING and FALLING both set on bit i. Rise, then W1C, then fall.
4. Raw state: after an event with INTR_ENABLE[i]=1, write INTR_ENABLE=0 and read INTR_STATE. — EXPECTED: - Rising, step 1:
  - INTR_STATE reads exactly (1<<i) for reads accepted at E0+8 or later.
  - o_intr_gpio=(1<<i) from E0+10.
  - After the falling input, INTR_STATE[i] still reads 1 and o_intr_gpio[i] stays 1 (not cleared by hardware).
  - The W1C write of ~(1<<i) leaves INTR_STATE=(1<<i).
  - The W1C write of (1<<i) makes INTR_STATE read 0 and o_intr_gpio[i]=0 from 2 cycles after the response.
  - The opposite (falling) edge alone never sets INTR_STATE[i].
- Falling, step 2: the mirror image of step 1.
- Both edges, step 3: each edge sets INTR_STATE[i]=1. INTR_STATE is identical for both edges.
- Raw state, step 4: INTR_STATE[i] still reads 1, and o_intr_gpio[i]=0 from 2 cycles after the INTR_ENABLE write response.
- At all times outside the 2 cycles after a change of INTR_STATE or INTR_ENABLE, o_intr_gpio equals INTR_STATE & INTR_ENABLE. |
| CHK-023 | test | intr | Level interrupts: high, low, and W1C while the level holds | GP-T5.15-01, GP-T5.16-01, GP-T3.2.4-04, GP-10-06, CP-T1.8.6-05, RG-T1.5.6.1-05, GP-T2.2-04, GP-9-04 | A configured level sets INTR_STATE[i]. A W1C write while the level still holds does not clear the interrupt for good. — STIMULUS: Filter off. For i in {0,15,16,31}:
1. LVLHIGH: i_gpio[i]=0. Write INTR_CTRL_EN_LVLHIGH=(1<<i), others 0, and INTR_ENABLE=(1<<i). Drive i_gpio[i]=1 at E0 and keep it. Read INTR_STATE at E0+8 or later. Write INTR_STATE=(1<<i) while i_gpio[i] is still 1, then read INTR_STATE. Drive i_gpio[i]=0, wait 8 cycles, write INTR_STATE=(1<<i), read INTR_STATE, observe 64 cycles.
2. LVLLOW: the mirror image (start at 1, configure LVLLOW, drive 0). — EXPECTED: - INTR_STATE[i] reads 1 for reads accepted at E0+8 or later, and o_intr_gpio[i]=1 from E0+10.
- After the W1C while the level holds, INTR_STATE[i] reads 1 and o_intr_gpio[i]=1 from 4 cycles after that write's response onward. A dip in between is not checked.
- After the level is removed and W1C is written, INTR_STATE[i] reads 0, and o_intr_gpio[i]=0 from 2 cycles after the response and for the next 64 cycles.
- LVLLOW behaves the same way. |
| CHK-024 | test | intr | INTR_TEST forcing and INTR_ENABLE masking per bit | GP-T5.4.1-01, CP-T1.8.4-04, CP-T1.8.6-03, CP-T1.8.4-03, CP-T1.8.6-04, GP-10-05, GP-10-37, GP-7-01, GP-9-04, CP-T1.8.3-01, GP-T3.2.4-02 | INTR_TEST forces INTR_STATE bits, INTR_ENABLE masks o_intr_gpio bit by bit, and each GPIO has its own interrupt line. — STIMULUS: All INTR_CTRL_EN_* =0, i_gpio constant.
1. Write INTR_ENABLE=32'hFFFF_FFFF, then INTR_TEST=32'h8001_0001. Read INTR_STATE and INTR_TEST.
2. Write INTR_ENABLE=32'h0000_0001. Read INTR_STATE.
3. Write INTR_STATE=32'hFFFF_FFFF and read it.
4. Write INTR_ENABLE=0. Set INTR_CTRL_EN_RISING and INTR_CTRL_EN_FALLING to 32'hFFFF_FFFF and toggle i_gpio with random values held for 8 or more cycles, for 200 cycles.
5. Return the CTRL registers to 0. Write INTR_STATE=32'hFFFF_FFFF, then INTR_ENABLE=32'hFFFF_FFFF, and wait 4 cycles. — EXPECTED: - Step 1: INTR_STATE reads 32'h8001_0001, INTR_TEST reads 0, and o_intr_gpio=32'h8001_0001 from 2 cycles after the INTR_TEST write response.
- Step 2: o_intr_gpio=32'h0000_0001 from 2 cycles after the response. INTR_STATE still reads 32'h8001_0001.
- Step 3: INTR_STATE reads 0 and o_intr_gpio=0 from 2 cycles after the response.
- Step 4: o_intr_gpio=0 at every edge. INTR_STATE is not checked.
- Step 5: o_intr_gpio=0 from 4 cycles after the INTR_ENABLE write response. |
| CHK-025 | test | perpin | PER_PIN_IO_i aliases DATA_OUT[i] / DATA_IN[i] and affects only GPIO i | GP-T3.2.2-01, GP-T3.2.2-02, GP-T5.20-01, GP-T5.20-02, GP-T5.1-02, GP-9-07, GP-9-09, GP-9-02, GP-T4.4-02 | Each PER_PIN_IO_i register shows and writes only GPIO i, and aliases the same state as the 32-bit registers. — STIMULUS: i_gpio=G=32'h6B2D_94C1, held constant. For every i in 0..31 (this includes 0, 15, 16 and 31):
1. Write DIRECT_OUT=P (P is random, and also 32'h0 and 32'hFFFF_FFFF).
2. Write PER_PIN_IO_i (0x100+4*i) with full-word data 32'h1 if P[i]=0, else 32'h0.
3. Read DIRECT_OUT, DIRECT_OE, INTR_ENABLE and PER_PIN_IO_j for j in {i, (i+1)%32}.
4. Write DIRECT_OUT with bit i inverted and read PER_PIN_IO_i.
PER_PIN_IO writes are always full-word (PutFullData, mask 1111). — EXPECTED: - After step 2, DIRECT_OUT = P with only bit i inverted, and o_gpio equals that value from 2 cycles after the response.
- DIRECT_OE and INTR_ENABLE are unchanged.
- PER_PIN_IO_i reads (G[i]<<8)\|DATA_OUT[i], with all other bits 0.
- PER_PIN_IO_(i+1) shows its own DATA_OUT and G bits.
- After step 4, PER_PIN_IO_i bit 0 equals the new DATA_OUT[i].
- d_error=0 on every response. |
| CHK-026 | test | perpin | PER_PIN_OE_i / PER_PIN_INTR_CTRL_i alias their bit and affect only GPIO i | GP-T5.21-01, GP-T5.21-02, GP-T5.22-01, GP-T5.22-02, GP-T5.23-01, GP-T5.1-03, GP-T3.2.2-01, GP-T3.2.2-02, GP-9-07, GP-9-09 | Each per-pin configuration register aliases bit i of DATA_OE or of the interrupt-control and filter registers, and a write to it changes only GPIO i. — STIMULUS: INTR_ENABLE=0 and i_gpio constant. For every i in 0..31:
1. Write DIRECT_OE=random R. Write PER_PIN_OE_i (0x200+8*i) full-word with ~R[i]. Read DIRECT_OE and PER_PIN_OE_i.
2. Preload INTR_CTRL_EN_RISING/FALLING/LVLHIGH/LVLLOW and CTRL_EN_INPUT_FILTER with random values. Write PER_PIN_INTR_CTRL_i (0x204+8*i) with 32'h01, 32'h02, 32'h04, 32'h08, 32'h10, 32'h1F and 32'h00 in turn. After each write, wait 24 cycles and read 0x2C, 0x30, 0x34, 0x38 and 0x3C.
3. Write the five 32-bit registers with random values and read PER_PIN_INTR_CTRL_i and PER_PIN_OE_i. — EXPECTED: - After step 1, DIRECT_OE = R with bit i inverted, PER_PIN_OE_i reads that bit in bit 0 with other bits 0, and o_gpio_en follows within 2 cycles after the response.
- In step 2, bit i of INTR_CTRL_EN_RISING, FALLING, LVLHIGH, LVLLOW and CTRL_EN_INPUT_FILTER equals bits 0, 1, 2, 3 and 4 of the written value. All other bits of these registers keep their preloaded value.
- In step 3, PER_PIN_INTR_CTRL_i reads {27'h0, FILTER[i], LVLLOW[i], LVLHIGH[i], FALLING[i], RISING[i]} and PER_PIN_OE_i reads {31'h0, DATA_OE[i]}.
- d_error=0 on every response. |
| CHK-027 | test | perpin | Interrupt registers have no per-pin view | GP-T3.2.2-05 | Writes to the per-pin ranges never change INTR_STATE, INTR_ENABLE or INTR_TEST. — STIMULUS: 1. Write INTR_ENABLE=32'hFFFF_FFFF. Keep INTR_CTRL_EN_LVLHIGH and INTR_CTRL_EN_LVLLOW at 0, and i_gpio=0 constant.
2. For i in {0,15,16,31}: write PER_PIN_IO_i=32'hFFFF_FFFF, PER_PIN_OE_i=32'hFFFF_FFFF and PER_PIN_INTR_CTRL_i=32'h0000_0001 (rising only; the input does not change).
3. Read INTR_STATE, INTR_ENABLE and INTR_TEST. — EXPECTED: - INTR_STATE reads 0, INTR_ENABLE reads 32'hFFFF_FFFF and INTR_TEST reads 0.
- o_intr_gpio=0 throughout.
- All writes complete with d_error=0. |
| CHK-028 | test | regs | Reset values of every register | GP-9-01, GP-2-06, GP-10-03, GP-10-18, GP-T5.1-01, GP-T5.1-02, GP-T5.1-03, GP-T5.23-01, GP-T5.2.1-01, CP-T1.8.4-01 | Right after reset, every register at its specified offset returns its reset value. — STIMULUS: In each configuration of the run set:
1. Hold rst_ni=0 for 10 cycles with i_a_valid=0, i_strap_en=0 and i_gpio=32'hA5A5_5A5A constant. Release rst_ni synchronously.
2. Wait 20 cycles.
3. Issue a Get (a_opcode=4, a_size=2, a_mask=1111) to every offset 0x00..0x44 in steps of 4, to 0x100..0x17C (PER_PIN_IO_0..31) and to 0x200..0x2FC (PER_PIN_OE_i at 0x200+8*i, PER_PIN_INTR_CTRL_i at 0x204+8*i). Use no writes before these reads. — EXPECTED: Every response has d_error=0.
- ALERT_TEST (0xC) reads 32'h8000_0000.
- DATA_IN (0x10) reads 32'hA5A5_5A5A.
- PER_PIN_IO_i reads ({i_gpio[i]}<<8), i.e. bit 8 = bit i of 32'hA5A5_5A5A and all other bits 0.
- HW_STRAPS_DATA_IN_VALID (0x40) reads 0 when GpioAsHwStrapsEn=1 (not checked when it is 0).
- HW_STRAPS_DATA_IN (0x44) reads 0.
- Every other register reads 32'h0: INTR_STATE, INTR_ENABLE, INTR_TEST, DIRECT_OUT, MASKED_OUT_LOWER/UPPER, DIRECT_OE, MASKED_OE_LOWER/UPPER (bits 15:0 checked), INTR_CTRL_EN_RISING/FALLING/LVLHIGH/LVLLOW, CTRL_EN_INPUT_FILTER, all PER_PIN_OE_i and all PER_PIN_INTR_CTRL_i.
- o_gpio=0, o_gpio_en=0 and o_intr_gpio=0 throughout. o_alert never pulses. |
| CHK-029 | test | regs | Field access types: rw, wo, ro, rw0c, reserved bits; RACL off | GP-9-01, GP-10-39, GP-10-40, GP-10-41, GP-10-24, GP-1-01, RG-T1.5.3-01, RG-T1.5.6-01, CP-T1.9.3-01, GP-T5.1-01 | Each register field behaves as its access type says, and every legal full-word access is accepted. — STIMULUS: i_gpio=32'h3C3C_C3C3 constant. INTR_ENABLE=0 and all INTR_CTRL_EN_* =0 unless written below. All writes are PutFullData with a_size=2, a_mask=1111.
1. For each rw register (INTR_ENABLE 0x4, DIRECT_OUT 0x14, DIRECT_OE 0x20, INTR_CTRL_EN_RISING 0x2C, FALLING 0x30, LVLHIGH 0x34, LVLLOW 0x38, CTRL_EN_INPUT_FILTER 0x3C), write and read back 32'hFFFF_FFFF, 32'h0, 32'hA5A5_5A5A and 32'h5A5A_A5A5. Restore 0 at the end; wait 24 cycles after each CTRL_EN_INPUT_FILTER write before reading DATA_IN.
2. Write INTR_TEST=32'h0 and read it.
3. Write ALERT_TEST=32'hFFFF_FFFE (bit 31=1, bit 0=0) and read it.
4. Write DATA_IN=32'hFFFF_FFFF, then 32'h0, reading after each.
5. Write HW_STRAPS_DATA_IN_VALID=32'hFFFF_FFFF and HW_STRAPS_DATA_IN=32'hFFFF_FFFF, reading before and after.
6. For i in {0,15,16,31}, write PER_PIN_IO_i=32'hFFFF_FFFF, PER_PIN_OE_i=32'hFFFF_FFFF and PER_PIN_INTR_CTRL_i=32'hFFFF_FFFF, then read them.
7. Write MASKED_OUT_LOWER=32'hFFFF_FFFF and read it. — EXPECTED: - All accesses complete with d_error=0 (no access-control rejection).
- rw registers read back exactly the value written.
- INTR_TEST reads 0.
- ALERT_TEST reads 32'h8000_0000: wo bit 0 and reserved bits 30:1 read 0, regwen is still 1. No o_alert pulse occurs.
- DATA_IN still reads 32'h3C3C_C3C3.
- HW_STRAPS_DATA_IN_VALID and HW_STRAPS_DATA_IN read the same as before the writes.
- PER_PIN_IO_i reads ((bit i of 32'h3C3C_C3C3)<<8)\|1. PER_PIN_OE_i reads 32'h1. PER_PIN_INTR_CTRL_i reads 32'h1F.
- MASKED_OUT_LOWER reads 32'h0000_FFFF (the wo mask field reads 0). |
| CHK-030 | test | reset | Asynchronous reset assertion, short reset and discarding of a pending response | GP-2-05, GP-10-32, TL-T3.1.1-02, GP-2-06, GP-10-31 | Reset is asserted asynchronously and released synchronously. It clears the outputs and the registers, drops any pending response, and works even when it lasts only 2 cycles. — STIMULUS: 1. Write DIRECT_OUT=32'hFFFF_FFFF and DIRECT_OE=32'hFFFF_FFFF. Write INTR_ENABLE=32'hFFFF_FFFF and INTR_TEST=32'hFFFF_FFFF.
2. Set i_d_ready=0 and send a Get to 0x14, holding it until o_d_valid=1.
3. Assert rst_ni=0 a quarter clock period after a rising edge and keep it low for only 2 rising edges. Release it synchronously.
4. Keep i_a_valid=0 during reset and for the first cycle after release, with i_d_ready=1, and observe 20 cycles without new requests.
5. Read DIRECT_OUT, DIRECT_OE, INTR_ENABLE and INTR_STATE. — EXPECTED: - At the first falling edge of clk_i after rst_ni falls (before the next rising edge), and while rst_ni=0: o_gpio=0, o_gpio_en=0, o_intr_gpio=0, o_d_valid=0, o_alert=0 and o_alert_integ_fail=0.
- After release, no o_d_valid occurs in the 20 idle cycles: the pending response is discarded.
- Then the reads all return 0 with d_error=0, and normal accesses work after the short reset. |
| CHK-031 | test | strap | Strap sampling with GpioAsHwStrapsEn=1 (once per reset, regardless of OE) | GP-T3.2.3.1-01, GP-T3.2.3.1-02, GP-T5.19-01, GP-T6.2-01, GP-T6.2-02, GP-8-01, GP-8-02, GP-8-03, GP-9-05, GP-10-10, GP-10-11, GP-10-12, GP-10-13 | Runs only in the configurations with GpioAsHwStrapsEn=1. The first rising edge of i_strap_en after reset samples i_gpio into HW_STRAPS_DATA_IN, and later changes have no effect until the next reset. — STIMULUS: 1. Hold i_strap_en=0 while rst_ni=0 and for 10 cycles after release.
2. Write DIRECT_OE=32'hFFFF_FFFF and DIRECT_OUT=32'h0F0F_0F0F.
3. Drive i_gpio=S=32'h3C5A_A5C3 from at least 24 cycles before raising i_strap_en.
4. Read HW_STRAPS_DATA_IN_VALID (0x40) before raising i_strap_en.
5. Raise i_strap_en. Es is the first rising edge with i_strap_en=1. Keep i_gpio=S until Es+8.
6. Read 0x40 and 0x44 accepted at Es+4 or later.
7. Drive random i_gpio values and toggle i_strap_en 5 times over 200 cycles, reading 0x40 and 0x44 again.
8. Reset, then repeat steps 1 to 7 with S2=32'hC3A5_5A3C. — EXPECTED: - Before Es: 0x40 reads 0 and o_straps_valid=0.
- From Es+4 on: o_straps_valid=1 and o_straps_data=S. 0x40 reads 32'h1 and 0x44 reads S. The value does not depend on DATA_OE or DATA_OUT.
- In step 7, o_straps_valid, o_straps_data, 0x40 and 0x44 stay unchanged at 1 and S.
- After the reset in step 8, the new sample is S2 with the same timing.
- All responses have d_error=0. |
| CHK-032 | test | strap | HW_STRAPS_DATA_IN reads zero when GpioAsHwStrapsEn=0 | GP-T5.19-02, GP-10-14, GP-9-05 | Runs only in the configurations with GpioAsHwStrapsEn=0. HW_STRAPS_DATA_IN reads 0 at all times. — STIMULUS: Use the same stimulus as CHK-031 steps 1 to 7 with S=32'h3C5A_A5C3. Read HW_STRAPS_DATA_IN (0x44) before the i_strap_en rise, at Es+4 or later, and after the random i_gpio and i_strap_en changes. — EXPECTED: - 0x44 reads 32'h0 in every read, with d_error=0.
- HW_STRAPS_DATA_IN_VALID, o_straps_valid and o_straps_data are not checked. |
| CHK-033 | test | tlul | Aligned byte writes: rejected on wide registers, accepted on PER_PIN_OE / PER_PIN_INTR_CTRL | GP-T4.4-02, GP-T4.4-03, GP-T4.4-05, GP-10-22, GP-10-23, GP-T3.2.2-03, RG-T1.4.1-05, TL-T3.1.3.4-03, TL-T3.1.3.5-07, GP-9-06 | A byte write to a register with fields above bit 7 is an error with no effect. A byte write to PER_PIN_OE_i or PER_PIN_INTR_CTRL_i succeeds. — STIMULUS: 1. Preload: DIRECT_OUT=32'h5555_AAAA, DIRECT_OE=32'hAAAA_5555, INTR_ENABLE=32'hFFFF_FFFF, all INTR_CTRL_EN_* =32'h0F0F_0F0F with i_gpio constant (no events), CTRL_EN_INPUT_FILTER=32'h0. Write INTR_TEST=32'h0000_0100 so INTR_STATE=32'h0000_0100.
2. Send PutPartialData (a_opcode=1, a_size=0, a_mask=0001, address = register offset, data 32'h0000_00FF) to INTR_STATE, INTR_ENABLE, INTR_TEST, DIRECT_OUT, MASKED_OUT_LOWER, MASKED_OUT_UPPER, DIRECT_OE, MASKED_OE_LOWER, MASKED_OE_UPPER, the four INTR_CTRL_EN_* registers, CTRL_EN_INPUT_FILTER and PER_PIN_IO_i for i in {0,15,16,31}. Read every register after each write.
3. Send byte writes with the same encoding to PER_PIN_OE_i (data 8'h01, then 8'h00) and PER_PIN_INTR_CTRL_i (data 8'h1F, then 8'h00) for i in {0,15,16,31}. — EXPECTED: - Every step-2 write gives d_error=1. All register reads are unchanged: INTR_STATE stays 32'h0000_0100, and DIRECT_OUT, DIRECT_OE, INTR_ENABLE and the INTR_CTRL_EN_* registers keep their preloaded values.
- o_gpio, o_gpio_en and o_intr_gpio (=32'h0000_0100) are unchanged.
- Every step-3 write gives d_error=0 and takes effect: DIRECT_OE[i] becomes 1 then 0, and bit i of all five control registers becomes 1 then 0, with readback and o_gpio_en as in CHK-026. |
| CHK-034 | test | tlul | Sub-word reads return the full register | RG-T1.4.1-07, RG-T1.4.1-08 | Reads smaller than a word are accepted and return the whole register, with each byte in its own lane. — STIMULUS: 1. Write DIRECT_OUT=32'hF2F4_56CD.
2. Send Gets to DIRECT_OUT with (a_size=0, address 0x14, mask 0001), (a_size=0, address 0x17, mask 1000), (a_size=1, address 0x16, mask 1100) and (a_size=1, address 0x14, mask 0011). — EXPECTED: Every response has d_error=0, o_d_data=32'hF2F4_56CD, and o_d_size equal to the request's a_size. |
| CHK-035 | test | tlul | TL-UL protocol error cases answered with d_error=1 | GP-4.1-06, TL-T3.1.3.4-05, TL-T3.1.3.5-01, TL-T3.1.3.5-02, TL-T3.1.3.5-04, RG-T1.4.1-04, GP-10-28, GP-9-06 | Requests with an undefined opcode, too large a size, a misaligned address or a mask covering inactive lanes are answered with d_error=1 and change nothing. — STIMULUS: First write DIRECT_OUT=32'h0000_0000. Then send:
(a) a_opcode in {2,3,5,6,7}, address 0x14, a_size=2, mask 1111, data 32'hFFFF_FFFF;
(b) Get with a_size=3 at 0x10;
(c) PutFullData with a_size=2 at address 0x16, mask 1111, data 32'hFFFF_FFFF;
(d) Get with a_size=2 at 0x15, mask 1111;
(e) PutPartialData with a_size=0 at 0x14, mask 0011, data 32'hFFFF_FFFF.
Read DIRECT_OUT after each request. — EXPECTED: - (a) to (e) all give d_error=1. For (a), only d_error is checked.
- For (b) to (e), d_source and d_size echo the request (CHK-013).
- DIRECT_OUT reads 0 and o_gpio stays 0 throughout. No o_alert pulse. |
| CHK-036 | test | tlul | Unmapped offsets return d_error=1 and change nothing | GP-10-20, TL-T3.1.3.5-03, RG-T1.4.1-01, GP-9-06, GP-10-21 | Accesses to unmapped offsets below 0x400 are errors and have no effect. — STIMULUS: 1. Preload every rw register with distinct non-zero patterns (INTR_ENABLE=32'h0, i_gpio constant).
2. Send a Get, then a PutFullData with data 32'hFFFF_FFFF, to each of 0x048, 0x04C, 0x080, 0x0FC, 0x180, 0x1FC, 0x300 and 0x3FC. All addresses are below 0x400.
3. Read all mapped registers. — EXPECTED: - Every request to these offsets gives d_error=1.
- All mapped registers read their preloaded values, and o_gpio and o_gpio_en are unchanged. |
| CHK-037 | test | tlul | Instruction-fetch reads complete without side effects | GP-3-01, GP-4.1-03, GP-10-19, GP-9-06 | Reads marked as instruction fetches get a response and change nothing. — STIMULUS: 1. Write DIRECT_OUT=32'hCAFE_0001.
2. Send Gets with i_a_instr=1 to 0x14 and 0x10. No write is sent with i_a_instr=1.
3. Read DIRECT_OUT with i_a_instr=0. — EXPECTED: - Each instruction-fetch Get gets exactly one response with d_source, d_size and d_opcode=1 as in CHK-013. d_error and d_data are not checked.
- DIRECT_OUT then reads 32'hCAFE_0001, o_gpio is unchanged, and o_alert does not pulse. |
| CHK-038 | test | tlul | Outstanding requests and back-pressure | GP-10-26, TL-T3.1.3.2-01, GP-4.1-01, TL-T2.2-03, GP-4.1-04 | The device handles back-to-back requests and D-channel back-pressure, and every response carries the right source and data. — STIMULUS: Run 500 random legal full-word reads and writes to mapped rw registers.
- Each request uses a distinct a_source among outstanding requests; values include 8'h00, 8'h01, 8'h7F, 8'hFF and random values.
- i_a_valid is asserted back-to-back whenever possible and held until o_a_ready=1, with no assumption that o_a_ready is 1.
- i_d_ready is randomly deasserted for 0 to 10 cycles. — EXPECTED: - Every request gets exactly one response, matched by d_source.
- Read data equals a reference model of the register values (writes applied in acceptance order).
- d_error=0 on all responses. CHK-012 and CHK-013 hold throughout. |

## Not verified by simulation

| Rule | Reason | Note |
|---|---|---|
| GP-T2.2-06 | not_applicable_to_dut | There is no pad model (INT-IO-002, D-021). i_gpio comes only from the test bench, so output-to-input delay does not occur. Designer decision for GP-T2.2-05/06. |
| GP-T3.2.3-02 | not_applicable_to_dut | ot_gpio_nnc has no pin multiplexer (INT-IO-002). |
| GP-T4.4-01 | design_guideline | Software capability-assignment advice; nothing to observe. |
| GP-1-03 | not_observable_at_interface | Ping requests belong to the wrapper's internal alert receiver. No port shows them. |
| GP-4.1-02 | not_observable_at_interface | a_user.rsvd is set inside the wrapper and is not a port. |
| RG-T1.4.1-02 | not_applicable_to_dut | D-012: requests at 0x400 and above are not used, so stripping of excess address bits is not exercised. |
| RG-T1.4.1-06 | covered_by_other_check | D-013 limits sub-word write checks to aligned byte writes (CHK-033). Unaligned sub-word writes are explicitly not checked. |
| RG-T1.4.1-09 | not_applicable_to_dut | gpio has no memory windows. |
| RG-T1.4.1-10 | not_applicable_to_dut | gpio has no memory windows. |
| RG-T1.5.1-01 | not_observable_at_interface | Software/hardware priority in the same internal cycle cannot be lined up from the ports without knowing internal latency. |
| RG-T1.5.1-03 | not_observable_at_interface | Same-cycle de/we collision is internal timing. |
| RG-T1.5.1-05 | not_observable_at_interface | hwqe/qe are internal signals. |
| RG-T1.5.2-01 | static_or_structural | Structure of the hwext register bundle. |
| RG-T1.5.2-02 | not_observable_at_interface | qe timing is internal. |
| RG-T1.5.3-02 | not_observable_at_interface | Whether a ro register is hwext/hardwired is an implementation attribute. The read value of HW_STRAPS_DATA_IN with straps disabled is checked in CHK-032. |
| RG-T1.5.4-01 | not_applicable_to_dut | gpio has no rc (read-clear) registers. |
| RG-T1.5.4-02 | design_guideline | Advice against rc registers. |
| RG-T1.5.4-03 | static_or_structural | Register tool configuration restriction. |
| RG-T1.5.5-01 | design_guideline | Implementation advice for wo registers. |
| RG-T1.5.6.1-01 | not_observable_at_interface | Simultaneous hardware/software write to a rw1c subreg needs internal cycle alignment. The visible W1C behaviour is covered by CHK-022/CHK-023. |
| RG-T1.5.6.1-03 | design_guideline | Recommendation for hardware d feedback. |
| RG-T1.5.6.1-04 | design_guideline | MAY: implementation freedom. |
| RG-T1.5.6.2-01 | static_or_structural | Register attribute legality. |
| RG-T1.5.6.2-02 | static_or_structural | Register attribute legality. |
| TL-T2.2-01 | design_guideline | MAY about reuse of IP blocks. |
| TL-T2.3-01 | static_or_structural | Compatibility statement about block integration. |
| TL-T2.3-02 | not_applicable_to_dut | gpio is not a baseline block; it uses the a_user integrity fields. |
| TL-T2.3-03 | not_applicable_to_dut | gpio is not a baseline block. |
| TL-T3.1.1-01 | not_applicable_to_dut | Relaxation for host drivers. The test bench follows D-016 (CHK-011). |
| TL-T3.1.3.1-01 | not_applicable_to_dut | Interconnect routing rule. There is no fabric in ot_gpio_nnc. |
| TL-T3.1.3.2-02 | not_applicable_to_dut | Fabric architect sizing rule. |
| TL-T3.1.3.2-03 | not_applicable_to_dut | Fabric host-ID conversion rule. |
| TL-T3.1.3.2.1-01 | not_applicable_to_dut | Bus primitive source-ID growth. There is no primitive between the test bench and the DUT. |
| TL-T3.1.3.2.1-02 | not_applicable_to_dut | Bus primitive response source shifting. |
| TL-T3.1.3.2.1-03 | not_applicable_to_dut | M:1 socket assertion recommendation. |
| TL-T3.1.3.2.2-01 | not_applicable_to_dut | Host rule about source contraction through a fabric. The DUT is connected directly; CHK-013 checks the full 8-bit d_source echo. |
| TL-T3.1.3.3-03 | not_applicable_to_dut | Interconnect user-bit pass-through. |
| TL-T3.1.3.5-06 | design_guideline | MAY. Non-contiguous masks are not driven (TL-T3.1.3.4-02, CHK-011), and D-013 leaves partial masks unchecked. |
| CP-T1.5.2-01 | static_or_structural | Configuration file content. |
| CP-T1.5.2-03 | static_or_structural | Configuration file content. |
| CP-T1.5.2-04 | static_or_structural | Configuration file content. |
| CP-T1.5.2.1-01 | design_guideline | Advice on security storage elements. |
| CP-T1.5.3-02 | static_or_structural | Presence of a device interface (the TL-UL ports exist). |
| CP-T1.5.3-03 | not_applicable_to_dut | gpio is not a bus host. |
| CP-T1.5.3-04 | static_or_structural | Configuration file content. |
| CP-T1.5.3-05 | static_or_structural | Configuration file content. |
| CP-T1.5.3-06 | static_or_structural | Configuration file content. |
| CP-T1.5.3-07 | static_or_structural | Clocking structure. The single test-bench host runs on clk_i. |
| CP-T1.5.3-08 | static_or_structural | Configuration file content. |
| CP-T1.5.5-01 | static_or_structural | Port naming of the inner module. |
| CP-T1.6-01 | static_or_structural | Conformance of the register description. |
| CP-T1.8-01 | static_or_structural | Interrupt naming conventions. |
| CP-T1.8.2-01 | static_or_structural | hjson key requirement. |
| CP-T1.8.2-02 | static_or_structural | hjson key option. |
| CP-T1.8.2-03 | static_or_structural | hjson key option. All gpio interrupts are event type. |
| CP-T1.8.4-02 | static_or_structural | hjson interrupt-count limit. |
| CP-T1.8.5.2-01 | not_applicable_to_dut | Status-type interrupts. All gpio interrupts are event type (designer decision). |
| CP-T1.8.5.2-03 | not_applicable_to_dut | Status-type interrupts are out of scope (designer decision). |
| CP-T1.8.5.2-05 | not_applicable_to_dut | Status-type interrupt software handling. |
| CP-T1.8.5.2-06 | not_applicable_to_dut | Status-type interrupt masking. Masking for event interrupts is checked in CHK-006/CHK-024. |
| CP-T1.9.1-03 | not_applicable_to_dut | gpio has no recoverable alert, only fatal_fault. |
| CP-T1.9.1-05 | design_guideline | Recommendation on local countermeasures. |
| CP-T1.9.1-07 | design_guideline | MAY: optional IRQ for alerts. |
| CP-T1.9.2-02 | static_or_structural | Alert naming (fatal_fault). |
| CP-T1.9.2-03 | static_or_structural | Alert naming option. |
| CP-T1.9.4-01 | static_or_structural | Internal connection to prim_alert_sender. |
| CP-T1.9.4-02 | static_or_structural | Instantiation and IsFatal parameter. The fatal repeat behaviour is checked in CHK-016. |
| CP-T1.9.4-03 | design_guideline | Maintainer freedom in bundling. |
| CP-T1.9.4-04 | design_guideline | Bundling recommendation. |
| CP-T1.9.4-05 | design_guideline | Cause register recommendation. |
| CP-T1.9.4-06 | not_applicable_to_dut | gpio has no recoverable alerts or cause registers. |
| CP-T1.9.4-07 | not_applicable_to_dut | gpio has no fatal alert cause register. |
| CP-T1.9.4-08 | covered_by_other_check | The differential pair is internal. Correct encoding is seen through o_alert pulses and o_alert_integ_fail=0 (CHK-001, CHK-014, CHK-016). |
| AH-T1.3.1-02 | static_or_structural | Instantiation of prim_alert_sender. |
| AH-T1.3.2-02 | not_applicable_to_dut | Sender and receiver share clk_i in the wrapper; there is no asynchronous boundary. |
| AH-T1.3.2-04 | not_observable_at_interface | The handshake pause is inside the diff-pair protocol. Only the bounds on o_alert pulse spacing are checked (CHK-016). |
| AH-T1.3.2-06 | static_or_structural | MAY: synchronous or asynchronous instantiation. |
| AH-T1.3.2-07 | static_or_structural | MAY: synchronizer flops omitted. |
| AH-T1.3.4-02 | not_observable_at_interface | Designer decision: sender-side encoding error signalling is not observable except via o_alert_integ_fail, which must stay 0 (CHK-001). |
| AH-T1.3.4-03 | not_applicable_to_dut | Designer decision: no ping requests (INT-CFG-003), so pingfail and lock-up are not checked. |

## Assumptions

- The T5.1 register-table quote is cut off after MASKED_OUT_UPPER (0x1C). The remaining offsets are assumed to follow the gpio register order: DIRECT_OE 0x20, MASKED_OE_LOWER 0x24, MASKED_OE_UPPER 0x28, INTR_CTRL_EN_RISING 0x2C, INTR_CTRL_EN_FALLING 0x30, INTR_CTRL_EN_LVLHIGH 0x34, INTR_CTRL_EN_LVLLOW 0x38, CTRL_EN_INPUT_FILTER 0x3C, HW_STRAPS_DATA_IN_VALID 0x40, HW_STRAPS_DATA_IN 0x44. This is consistent with GP-T5.1-01: 18 registers from 0x0 to 0x44.
- HW_STRAPS_DATA_IN_VALID has its single field at bit 0, with all other bits reserved (read 0). HW_STRAPS_DATA_IN resets to 0x0 before any strap sample. Its field tables are not in the rules.
- Cycle counts are rising edges of clk_i. E0 is the first rising edge at which a changed input is already present, as in the designer decision for D-018. A read 'accepted at Ex' means its A handshake (i_a_valid=1 and o_a_ready=1) happens at edge Ex.
- Byte writes use PutPartialData (a_opcode=1). Full-word writes use PutFullData with a_size=2 and a_mask=1111.
- INTR_TEST is only exercised with INTR_ENABLE=1 on the forced bits. This avoids the INTR_STATE-while-disabled case that D-004 leaves open.
- 'While rst_ni = 0' (D-016) is read as including the first clock edge after an asynchronous assertion, before the next rising edge (CHK-008, CHK-030).
- From an accepted request with i_a_intg_flip=1 until reset, the shadow-model assertions (CHK-013, CHK-004, CHK-006, CHK-007) are disabled, as D-017 requires.
- Every test except CHK-031 and CHK-032 runs in all four run-set configurations (GpioAsyncOn, GpioAsHwStrapsEn) = (1,1), (0,1), (1,0) and (0,0). CHK-031 runs only where GpioAsHwStrapsEn=1, and CHK-032 only where GpioAsHwStrapsEn=0.
