# Rules for review (Gate 1)

```
rules in 285: kept 228 (fixed 30), merged 3, rejected 54, unreviewed 0; open questions 3 (raised 42, answered from the documents 39, duplicates 0)
calls: 21 (18 from cache)  cost US$0.5792
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.

## Open questions (the designer decides: `nnc answer <design> <n> "<decision>" --by <name>`)

1. Are Status interrupts' INTR_STATE bits ro mirroring the input, and does INTR_TEST apply to Status type? The quote only says INTR_STATE is ro for Status. (CP-T1.8.5.2-03, CP-T1.8.4-03, CP-T1.8.6-03) — *The documents say INTR_STATE is ro for Status type and that the wired interrupt comes directly from the input signal. They do not say whether INTR_STATE mirrors the input exactly, or whether INTR_TEST applies to Status type. rv_timer has no Status interrupts and they are out of scope, so a designer decision is needed if this is to be checked.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-20T11:04:29+00:00): Out of scope: rv_timer has only an Event-type interrupt (spec D-019). Status-type behaviour is not checked. Delegated decision, not a hardware designer's review.
2. Can fatal cause registers be reset by system reset? 'Not clearable in any way' needs an exception for reset. (CP-T1.9.4-07, CP-T1.9.4-02) — *The documents say fatal cause registers must not be clearable in any way and must be read-only. They do not say whether system reset resets such a register, so the missing reset exception must be decided by the designer.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-20T11:04:29+00:00): rv_timer has no cause register for its fatal alert, so this is not checked. A reset ends the repeated fatal alert (comportability: fatal alerts repeat until reset; spec D-010). Delegated decision, not a hardware designer's review.
3. Is 'wait 2 cycles between handshakes' measured from ack deassertion to next alert assertion, and is it exact or a minimum? (AH-T1.3.2-03) — *The documents say the sender waits 2 cycles (2 sender cycles) between handshakes. They do not say from which event it is measured (for example ack deassertion to the next alert assertion), nor whether it is exact or a minimum. The designer must define this.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-20T11:04:29+00:00): Neither the start point nor exactness is checked. Only the bounds of spec D-009 and D-010 are checked: first pulse within 16 cycles, then at least one pulse every 32 cycles while the fatal alert lasts. Delegated decision, not a hardware designer's review.

## Questions answered by the documents

- Is the interrupt level-sensitive (stays asserted while counter >= compare) or a one-shot event? The quote says 'reaches (or is above)'. How is it cleared, and is the comparison 64-bit unsigned? → Event-type, latched in INTR_STATE0 (not a one-shot pulse). The condition is mtime >= mtimecmp, compared as 64-bit unsigned. Software clears it by writing 1 to INTR_STATE0, or by updating COMPARE_LOWER0_0 or COMPARE_UPPER0_0. If the condition still holds after a clear, IS_0 returns to 1. [T3.1:s4, T4.3:s2, T4.4:s1, T4.4:s3, T4.4:s5, T1.8.5.1:s5, T1.8.5.1:s6, T1.8.6:s11, 8:s7]
- Is the step value applied on every prescaler timeout even when the timer is disabled or stopped? The quote does not say whether the counter is gated by an enable. → The counter is gated by CTRL.active_0 ("if 1, timer operates"). Software must configure the timer before activating it, and de-activate it to change prescaler or step. Ticks and increments apply with active_0 = 1. [T5.3.1:s2, T4.1:s1, T4.1:s3, 8:s5]
- Section 3.2.2 says each hart can have multiple mtimecmp/comparators, but this version is fixed to one timer per hart. Which applies for verification? Does the per-hart interrupt enable/state set conflict with the multi-timer text? → This version is fixed to one hart and one timer, so N_HARTS = 1 and N_TIMERS = 1 apply for verification. The multi-timer text and the per-hart enable/state registers belong to the two-hart, two-timer example configuration, not this one. The register tables bind. [T3.2.2:s5, T3.2.2:s6, T2.1:s4, 1:s1, 8:s24]
- When exactly does the tick occur relative to the counter (counter == prescaler, then reset to 0?), and what happens if CFG0.prescaler is 0 or CFG0.prescaler/step are changed while running? → A tick occurs every CFG0.prescale + 1 cycles, so prescale 0 gives a tick every cycle. Each tick adds step to mtime. Changing CFG0 while active is a software obligation and the behaviour is not checked. [T3.1:s2, T3.1:s3, 8:s5, 8:s6, T4.1:s2, T4.1:s3]
- Is the interrupt level-sensitive (stays asserted while mtime >= mtimecmp) or latched until cleared, and is the comparison done on every cycle or only on ticks? → The interrupt is latched in INTR_STATE0 (event type), so it is not simply level-follow. The event is the condition mtime >= mtimecmp. IS_0 becomes 1 within 4 cycles after the tick that makes the condition true, or within prescale + 1 + 4 cycles after a register write that makes it true. It returns to 1 after a clear if the condition still holds. [T3.1:s5, T1.8.5.1:s5, T1.8.6:s11, 8:s7, 8:s9]
- Does a write to either COMPARE_LOWER0_0 or COMPARE_UPPER0_0 clear the interrupt only when the new mtimecmp exceeds mtime, or does it clear the interrupt source unconditionally (so it re-asserts if mtime >= mtimecmp still holds)? → A write to either compare register can clear the interrupt source. If mtimecmp > mtime afterwards, IS_0 and the interrupt stay 0. If mtime >= mtimecmp still holds, IS_0 returns to 1 within 4 cycles, and the dip in between is not checked. [T4.4:s4, T4.4:s5, 8:s10]
- Is the prescaler/step stability requirement enforced by hardware (e.g. ignoring writes while active) or only a software obligation? What does the DUT do if they change while active? → It is only a software obligation. Prescaler and step must be stable while active, and software de-activates the timer before changing them. The documents do not describe hardware enforcement. Tests change CFG0 only while inactive, and behaviour after a change while active is not checked. [T4.1:s1, T4.1:s2, T4.1:s3, 8:s6]
- When mtime skips mtimecmp because of a step above 1 at wraparound, is the interrupt missed by design, or is it expected to be raised? → The interrupt is missed by design. With step above 1, mtime can skip over mtimecmp at wraparound, or step over the all-ones value, and the interrupt is not raised. [T4.3:s7, T4.3:s12, T4.3:s13]
- INTR_TEST0 has reset default 0x0 but its field T_0 (wo) has reset x. Which is correct for reads after reset? → INTR_TEST0 reads 0x0 after reset. A wo field has no read path and reads 0. The "x" is only the field's nominal reset value. [8:s12, T5.6:s3]
- ALERT_TEST reset is 0x80000000 and the mask is 0x80000001, yet wo fatal_fault has reset 0x0. What do reads of bit 0 return, and is the mask meant to include it? → ALERT_TEST reads 0x8000_0000 after reset. Bit 0 (wo fatal_fault) reads 0 and bit 31 (regwen) reads 1. The reset mask is simply as given in the register table. [8:s12, T5.2:s3, T5.2:s4, T5.2.1:s1, T5.2.1:s3]
- Does regwen=0 block fatal_fault alert triggering? The quote states only 'disable alert testing'. → Yes. After regwen is cleared to 0, a write of 0x8000_0001 completes with d_error = 0, triggers no alert, and regwen still reads 0. The state lasts until reset. [8:s13, T5.2.1:s1]
- Do reserved bits read as 0 and are writes to them ignored? → Yes. Reserved bits read 0 and writes to them have no effect. [8:s12]
- RT-T6.1-01: Which policy-selection parameter values map each register to a RACL policy, and what is the expected access result when a policy denies access? → RACL is disabled in this configuration. Every register access is permitted and none is rejected for an access-control reason, so no policy mapping or denial behaviour is needed. [1:s2, 1:s5]
- RT-T6.2-01: Is the timer_expired_hart0_timer0 interrupt level-held while mtime >= mtimecmp and the interrupt enabled, or a pulse? Is the comparison signed/unsigned over 64 bits? → The interrupt is not a pulse. IS_0 is latched and the output equals IS_0 AND IE_0, except in the 2 cycles after either changes. The comparison is 64-bit unsigned. [8:s9, T4.3:s2, T6.2:s1, 6:s1, T1.8.6:s9]
- Is 'Ping requests are never issued' a property of the design or a testbench/environment constraint? Which alert channel does it cover, and what is its source section? → It is stated as part of the fixed verification configuration (INT-CFG-003): ping requests are never issued. It covers the single alert channel, fatal_fault, whose sender and receiver both use the synchronous scheme. The documents do not say whether this is a design property or a testbench constraint. [1:s3, 1:s4, 5:s1]
- The reset values are only referenced from the register tables, which are not quoted. Should the checker take them from those tables, and are they checked on the registers or on the outputs? → Yes. Reset values are taken from the rv_timer register tables, and while rst_ni is 0 every register holds that value. The outputs o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired must be 0 during reset. [2:s4, 8:s20]
- The 'except for the effect of rst_ni' clause allows outputs to change asynchronously when reset asserts. Should the edge-only output check be exempt for every cycle in which rst_ni is low, or only at the falling edge of rst_ni? → The edge-only output rule is not applied in any cycle where rst_ni is 0, nor in the cycle where it falls. [8:s20, 2:s2]
- Are Get=4, PutFullData=0, PutPartialData=1 the only legal a_opcode values, and what is the expected behavior for other opcodes? → Get = 4, PutFullData = 0 and PutPartialData = 1 are the defined request opcodes. 3'b01x, 3'b101 and 3'b11x are undefined, and devices should return an error. For an undefined opcode only d_error = 1 is checked. [3:s5, T3.1.3.4:s12, T3.1.3.4:s13, T3.1.3.4:s14, T3.1.3.4:s15, 8:s19]
- Is o_alert (and o_d_intg_err) a level or a one-cycle pulse, and how long does it remain asserted? → o_alert is a one-clock-cycle pulse for each handshake the receiver detects. o_d_intg_err is a per-cycle flag: it is 1 in a cycle where o_d_valid is 1 and the response integrity check fails, otherwise 0. For a correct device it is always 0. [5:s2, 4.3:s1, 4.3:s2, 8:s21]
- Is the fatal_fault alert timing/latency after a command integrity error defined (section 5)? Also is o_d_intg_err expected to flag integrity errors on error-response beats? → The documents themselves do not specify the D-channel response. The verification decision is that o_alert pulses no later than 16 cycles after the request with i_a_intg_flip = 1 is accepted. o_d_intg_err and o_alert_integ_fail must stay 0 in every cycle with rst_ni = 1, including during such a test, so error-response beats are not expected to flag. [4.2:s5, 8:s14, 8:s21, 4.3:s2]
- Does 'one alert event' in ALERT_TEST mean exactly one o_alert pulse, given the alert sender/receiver handshake and differential signaling latency? What is the expected latency? → Yes, under the stated conditions. One write of 1 to fatal_fault, with no other alert cause and no other such write within 32 cycles, gives exactly one o_alert pulse. It arrives no later than 16 cycles after the write response. For writes closer together, at least one pulse and no more pulses than writes. [8:s13, 5:s6]
- What is the repeat interval of o_alert pulses after a fatal bus integrity fault, and is it bounded? → A fatal alert repeats until reset. After the first pulse (within 16 cycles of the request), o_alert pulses at least once in every 32 cycles until rst_ni is asserted. This bound is a verification bound. [5:s5, 8:s14, 8:s4]
- The event-type interrupt behaviour is defined only by reference to the comportability specification. Which exact semantics should be verified: INTR_STATE set on the event, output equal to STATE AND ENABLE, INTR_TEST setting STATE, and write-1-to-clear? → INTR_STATE0 is set by the event, or by writing 1 to INTR_TEST0. The output interrupt is INTR_STATE0 ANDed with INTR_ENABLE0. Writing 1 to INTR_STATE0 clears it (rw1c), but it returns to 1 if the event is still active. Software has precedence over hardware for that cycle. [T1.8.5.1:s5, T1.8.5.1:s6, T1.8.6:s7, T1.8.6:s8, T1.8.6:s9, T1.8.6:s11, 8:s11, 8:s24]
- INT-VER-001 says 'through the ports above', but the ports are not part of the quote. Which ports (bus interface, interrupt, alert) are allowed for observing each item? → Items are observed through the section 3 ports: the TL-UL A and D channel ports for registers and bus errors, o_intr_timer_expired for the interrupt, and o_alert and o_alert_integ_fail for alerts. Section 7 gives no finer per-item port assignment. [7:s1, 3:s3, 3:s24, 3:s25, 3:s26]
- What is the expected response for each bus error case (unmapped address, sub-word write, instruction fetch, integrity error), and when does fatal_fault assert? The quote does not say. → Unmapped offsets in 0x000..0x1FF return d_error = 1 and change no register. Sub-word writes: a byte write to CFG0, TIMER_V_*, COMPARE_* or ALERT_TEST returns d_error = 1 and changes nothing, while a byte write to byte 0 of CTRL, INTR_ENABLE0, INTR_STATE0 or INTR_TEST0 succeeds. Instruction fetches are not checked for d_error. For an integrity error, o_alert pulses within 16 cycles and the D response is not checked. [8:s14, 8:s15, 8:s16, 8:s17]
- Which registers does 'timer value registers' cover (lower and upper halves)? Is a write to one half atomic with respect to counting? → The timer value registers are TIMER_V_LOWER0 (bits [31:0]) and TIMER_V_UPPER0 (bits [63:32]). The two 32-bit writes are not atomic with respect to counting, so tests write them only while CTRL.active_0 = 0. [T5.8.1:s1, T5.9.1:s1, T4.2:s2, T4.2:s3, 8:s6, 8:s22]
- D-001 says the first-tick cycle is unspecified but bounded by prescale+1+4 cycles after the write response. Is the 4-cycle margin a register-write-to-timer-enable latency or a general tolerance? It matters for the 'once every prescale+1 cycles' check right after active_0 is set. → The 4-cycle margin is a generous verification bound, not an rv_timer timing requirement. The first-tick cycle after active_0 becomes 1 is unspecified and must come within prescale + 1 + 4 cycles after the write response. The period check of one tick per prescale + 1 cycles applies from the first tick onward. [8:s4, 8:s5]
- o_intr_timer_expired is allowed to differ from IS_0 AND IE_0 for 2 cycles after a change, but IS_0 itself has a 4-cycle latency. Is the 2-cycle window counted from the IS_0/IE_0 register change or from the triggering event? Is it measured at the interface? → The 2-cycle window counts from a change of IS_0 or IE_0 (either of them), and is observed at the o_intr_timer_expired port. The 4-cycle IS_0 latency is a separate bound measured from the tick or write. [8:s9, 3:s26]
- The D-009 quote is cut off at 'no more pulses than'. Please confirm the limit is the number of fatal_fault writes. → Confirmed. The full text reads "no more pulses than writes", so the limit is the number of fatal_fault writes. [8:s13]
- What is the project-specific default value for user signals generated by a baseline source, and does it need to be a constant across the project? Is it checkable? → The documents give no concrete value. A baseline source generates a project-specific default and receivers ignore user signals. User-bit default values are out of scope and not checked, so this is not checkable. [T2.3:s3, 8:s23]
- Does 'no burst transactions' mean a request size is limited to the bus width, or are multi-beat operations simply unsupported? Define the exact checkable condition. → Transaction size is limited to the bus width, and there are no bursts, so each request is a single beat. The checkable condition on this 32-bit bus is a_size <= 2; a larger a_size is an error case (d_error). [T2.1:s8, T2.2:s11, T3.1.3.5:s5, T3.1:s40, 4.1:s5]
- Does a_size greater than 2 apply for a 64-bit bus given PutFullData mentions 'h3 for 64b? The 'a_size must not be greater than 2' rule conflicts with that. → There is no conflict for this design. The bus is 32 bits wide (DW = 32, SZW = 2 for 4B), so a_size must not exceed 2. The 'h3 case applies only if or when a 64-bit bus is supported. [T3.1:s38, T3.1:s40, T3.1.3.5:s5, T3.1.3.4:s12, 3:s7, 3:s11]
- Is a non-contiguous mask an error or permitted for devices? The spec says hosts do not use them but devices may or may not return d_error. → A non-contiguous mask is permitted by TL-UL, and hosts in this project do not use them. Devices may or may not support them and have the right to assert d_error. For this verification, non-contiguous masks are not checked. [T3.1.3.4:s9, T3.1.3.4:s11, T3.1.3.5:s8, 8:s17]
- CP-T1.8.6-03 says INTR_TEST 'can' set INTR_STATE, while CP-T1.8.4-03 says INTR_TEST asserts the interrupt; should this be mandatory? → INTR_TEST is defined as a write-only register that asserts the interrupt for testing, and a write of 1 sets the corresponding INTR_STATE bit. The "can" in the hardware example only describes that implementation. For rv_timer, INTR_TEST0 is a required register of the event-type interrupt. [T1.8.4:s7, T1.8.6:s8, 6:s1, T5.6:s1]
- Is a cause register mandatory for IPs with multiple bundled alerts? CP-T1.9.4-05 only recommends it, but CP-T1.9.4-06 and CP-T1.9.4-07 make mandatory demands of cause registers. → A cause register is not mandatory; it is only recommended for IPs with multiple bundled alerts. The "must" statements apply to cause registers that exist: recoverable ones must be SW-clearable or auto-cleared by HW, and fatal ones must be read-only. [T1.9.4:s6, T1.9.4:s7, T1.9.4:s8]
- Does 'typically return an error' for unmapped addresses allow implementations that return no error, and how should the testbench treat that? → For the general register tool, "typically" leaves room for implementations that do not return an error. For this design the verification decision is that a request to an unmapped offset in 0x000..0x1FF returns d_error = 1 and changes no register. Requests at 0x200 and above are not used. [T1.4.1:s3, T1.4.1:s5, T1.4.1:s9, 8:s16]
- When software and hardware write simultaneously to RW1C/RW1S registers, what exactly is the resulting value? The quote only says it is 'more tricky'. → For this design the decision is that software has precedence for that cycle. A write of 1 to IS_0 clears it, and if the condition still holds IS_0 returns to 1. Only the result after 4 cycles is checked. The generic subreg equation is in a figure that is not quoted. [T1.5.6.1:s2, T1.5.6.1:s16, T1.5.6.1:s17, 8:s11]
- Is the window error rule mandatory or optional ('might be relaxed')? → It is a recommendation, not a mandatory rule: following the error rules for windows is recommended, and it may be relaxed, for example for memory-backed windows that handle byte masks. [T1.4.1:s26, T1.4.1:s27]
- Does 'eventually' for pingfail have a bounded latency that can be asserted? → Yes, the latency is bounded by the programmable ping timeout. After that timeout the LFSR timer automatically raises a pingfail alert. The timeout value depends on clock ratios and is set via PING_TIMEOUT_CYC_SHADOWED. In rv_timer no pings are issued. [T1.3.3:s6, T1.3.6:s10, T1.3.6:s11, T1.3.6:s13, T1.3.4:s10, 1:s4]


## rv_timer_Design_Specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| RT-T2.2-01 |  | MUST | system | scenario | Each 64-bit counter increments by the step value whenever the prescaler times out. *(when: whenever the prescaler times out)* | keep |
| RT-T2.2-02 |  | MUST | system | scenario | Each timer generates an interrupt if its counter reaches or exceeds the programmed value. *(when: when the counter reaches or is above the programmed compare value)* | fix: check both->scenario |
| RT-T3.1-01 |  | MUST | system | both | The tick generator creates a tick every time its internal counter hits the CFG0.prescaler value. *(when: when the tick generator's internal counter hits the CFG0.prescaler value)* | keep |
| RT-T3.1-02 |  | MUST | system | both | Each tick increments mtime by the CFG0.step value. *(when: on each tick)* | keep |
| RT-T3.1-03 |  | MUST | system | both | The timer compares 64-bit mtime with 64-bit mtimecmp and raises an interrupt when mtime is greater than or equal to mtimecmp. *(when: when the 64-bit mtime is greater than or equal to the 64-bit mtimecmp)* | keep |
| RT-T3.2.2-01 |  | MUST | system | scenario | Each hart has its own tick generator and counter, so the number of prescaler, step, and mtime registers equals the number of harts. | keep |
| RT-T3.2.2-03 |  | MUST | system | scenario | The IP is fixed to one hart and one timer per hart. *(when: in this version of the IP)* | keep |
| RT-T3.2.2-04 |  | MUST | system | scenario | There are separate interrupts per timer and a set of interrupt enable and state registers per hart. | keep |
| RT-T4.1-01 |  | MUST | system | scenario | The prescaler and step fields must be stable for the timer value to increment correctly. *(when: while the timer is active and incrementing)* | keep |
| RT-T4.1-02 |  | SHOULD | master | scenario | Software should de-activate the timer before changing the prescaler or step fields, then proceed with the change. *(when: when software wants to change prescaler or step)* | keep |
| RT-T4.2-06 |  | MUST | master | scenario | mtimecmp shall be written after mtime in order to clear any pending interrupt condition. *(when: when mtime is modified)* | keep |
| RT-T4.3-02 |  | MAY | master | none | Software may set mtimecmp to 0xFFFF_FFFF_FFFF_FFFF to get an intermediate interrupt. *(when: when the computed mtime + timeout comparison value overflows)* | keep |
| RT-T4.3-05 |  | MAY | master | none | Setting mtimecmp to 0xFFFF_FFFF_FFFF_FFFF - step + 1 works for the intermediate interrupt, since the last mtime before wrap is at least that large. *(when: for any nonzero step)* | fix: check scenario->none |
| RT-T4.4-01 |  | MUST | slave | both | The RV_TIMER module generates the interrupt when mtime is greater than or equal to mtimecmp. *(when: when mtime is greater than or equal to mtimecmp)* | keep |
| RT-T4.4-02 |  | MAY | master | scenario | The interrupt can be cleared by writing 1 to the Interrupt Status register INTR_STATE0. | keep |
| RT-T4.4-03 |  | MUST | slave | both | The interrupt can be cleared by updating mtimecmp; a write to either COMPARE_LOWER0_0 or COMPARE_UPPER0_0 clears the interrupt source. | fix: strength MAY->MUST, actor master->slave, check scenario->both |
| RT-T5.1-01 |  | MUST | slave | scenario | ALERT_TEST register must be located at offset 0x0 with length 4 bytes. | keep |
| RT-T5.1-02 |  | MUST | slave | scenario | CTRL must be at offset 0x4, length 4, reset to 0x0 with reset mask 0x1. | keep |
| RT-T5.1-03 |  | MUST | slave | scenario | INTR_ENABLE0 must be at offset 0x100, length 4, reset to 0x0 with reset mask 0x1. | keep |
| RT-T5.1-04 |  | MUST | slave | scenario | INTR_STATE0 must be at offset 0x104, length 4, reset to 0x0 with reset mask 0x1. | keep |
| RT-T5.1-05 |  | MUST | slave | scenario | INTR_TEST0 must be at offset 0x108, length 4, reset value 0x0 with reset mask 0x1. | keep |
| RT-T5.1-06 |  | MUST | slave | scenario | CFG0 must be at offset 0x10c, length 4, reset to 0x10000 with reset mask 0xff0fff. | keep |
| RT-T5.1-07 |  | MUST | slave | scenario | TIMER_V_LOWER0 at offset 0x110 holds timer value [31:0] as rw field v, reset 0x0, mask 0xffffffff. | keep |
| RT-T5.1-08 |  | MUST | slave | scenario | TIMER_V_UPPER0 at offset 0x114 holds timer value [63:32] as rw field v, reset 0x0, mask 0xffffffff. | keep |
| RT-T5.1-09 |  | MUST | slave | scenario | COMPARE_LOWER0_0 at offset 0x118 holds compare value [31:0] as rw field v, reset 0xffffffff, mask 0xffffffff. | keep |
| RT-T5.1-10 |  | MUST | slave | scenario | COMPARE_UPPER0_0 at offset 0x11c holds compare value [63:32] as rw field v, reset 0xffffffff, mask 0xffffffff. | keep |
| RT-T5.2-01 |  | MUST | slave | scenario | ALERT_TEST must reset to 0x80000000 with reset mask 0x80000001. *(when: After reset)* | keep |
| RT-T5.2.1-01 |  | MUST | slave | scenario | Writing 0 to regwen disables alert testing until the next reset; regwen can only be cleared, not set, by writes. *(when: Software writes 0 to ALERT_TEST regwen bit 31 (rw0c, reset 0x1))* | keep |
| RT-T5.2.1-03 |  | MUST | slave | scenario | Writing 1 to fatal_fault triggers one alert event of the fatal kind. *(when: Write 1 to ALERT_TEST bit 0 (wo, reset 0x0) while alert testing is enabled)* | keep |
| RT-T5.3.1-01 |  | MUST | system | scenario | When active_0 is 1 the timer operates; bits 31:1 of CTRL are reserved. *(when: CTRL.active_0 (rw, reset 0x0) is 1)* | keep |
| RT-T5.4.1-01 |  | MUST | slave | scenario | IE_0 (bit 0, rw, reset 0x0) is the interrupt enable for the timer; bits 31:1 are reserved. | keep |
| RT-T5.5.1-01 |  | MUST | slave | scenario | IS_0 (bit 0, rw1c, reset 0x0) holds the timer interrupt status and is cleared by writing 1; bits 31:1 are reserved. | keep |
| RT-T5.6.1-01 |  | MUST | slave | scenario | T_0 (bit 0, wo, reset x) is the interrupt test for timer; bits 31:1 are reserved. | keep |
| RT-T5.7.1-01 |  | MUST | slave | scenario | CFG0 step (bits 23:16, rw, reset 0x1) is the increment per tick; prescale (bits 11:0, rw, reset 0x0) generates the tick; other bits reserved. | keep |
| RT-T6.1-01 |  | MUST | master | scenario | The racl_policies input must carry the incoming RACL policy vector from a racl_ctrl instance, with the policy selection vector parameter selecting the policy for each register. | fix: actor system->master |
| RT-T6.2-01 |  | MUST | slave | both | The module must raise interrupt timer_expired_hart0_timer0 when hart0's timer0 has expired (mtime >= mtimecmp). *(when: hart0's timer0 expired (mtime >= mtimecmp))* | keep |
| RT-T6.3-01 |  | MUST | slave | scenario | The fatal_fault alert must be triggered when a fatal TL-UL bus integrity fault is detected inside RV_TIMER. *(when: a fatal TL-UL bus integrity fault is detected inside the RV_TIMER unit)* | keep |
| RT-1-01 |  | MUST | system | none | The design under verification has exactly one hart and one timer (N_HARTS = 1, N_TIMERS = 1). | keep |
| RT-1-02 |  | MUST | system | scenario | Every register access is permitted when RACL is disabled. *(when: RACL is disabled)* | keep; merged RT-1-03 |
| RT-1-04 |  | MUST | system | none | The alert sender of rv_timer and the alert receiver of the wrapper both use the synchronous clocking scheme, with no synchronizer flops on the differential pairs. | keep |
| RT-1-06 |  | MUST | system | none | Every run uses the single fixed configuration; there is no design parameter to vary. | keep |
| RT-2-02 |  | MUST | system | assertion | All inputs are sampled and all outputs change at the rising edge of clk_i, except for the effect of rst_ni. | keep |
| RT-2-03 |  | MUST | system | both | rst_ni is active-low and may be asserted asynchronously, but its release must be synchronous to clk_i. | keep |
| RT-2-04 |  | MUST | system | both | Every register holds its reset value as given in the rv_timer specification register tables. *(when: While rst_ni is 0)* | keep |
| RT-3-01 |  | MUST | master | assertion | i_a_opcode must encode TL-UL request types as Get = 4, PutFullData = 0 and PutPartialData = 1. | keep |
| RT-3-02 |  | MUST | system | scenario | i_a_instr = 1 marks the request as an instruction fetch (a_user.instr_type = MuBi4True); i_a_instr = 0 marks a data access (MuBi4False). | keep |
| RT-3-03 |  | MUST | system | scenario | When i_a_intg_flip is 1, the A-channel integrity sent with the request is corrupted. *(when: i_a_intg_flip is 1)* | keep |
| RT-3-04 |  | MUST | slave | assertion | o_d_opcode must encode TL-UL response types as AccessAck = 0 and AccessAckData = 1. | keep |
| RT-3-05 |  | MUST | system | scenario | o_d_intg_err indicates that the response integrity of the D-channel beat is wrong. *(when: the response integrity of the D-channel beat is wrong)* | keep |
| RT-3-06 |  | MUST | system | scenario | o_alert indicates that the alert fatal_fault was received. *(when: alert fatal_fault is received)* | keep |
| RT-3-07 |  | MUST | system | scenario | o_alert_integ_fail indicates a signal integrity failure on the alert differential pairs. *(when: a signal integrity failure occurs on the alert differential pairs)* | keep |
| RT-4.1-01 |  | MUST | system | both | The i_a_*, o_a_ready, o_d_* (except o_d_intg_err) and i_d_ready ports must be the same-named fields of the rv_timer TL-UL device interface tl, with TL-UL meaning. | fix: check scenario->both |
| RT-4.1-03 |  | MUST | system | assertion | a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. | keep; merged RT-4.1-02 |
| RT-4.1-04 |  | MUST | master | assertion | The test bench must follow the TL-UL host rules, including keeping A-channel signals stable while a_valid is 1 and a_ready is 0. *(when: test bench acting as TL-UL host)* | keep |
| RT-4.1-05 |  | MAY | master | scenario | The test bench may send requests listed as TL-UL error cases (unsupported opcode, bad size or mask, misaligned address) as legal stimulus. | keep |
| RT-4.1-06 |  | MUST | slave | both | The device must answer such error-case requests with d_error = 1. *(when: request is a TL-UL error case (unsupported opcode, bad size or mask, misaligned address))* | keep |
| RT-4.2-01 |  | MUST | system | both | The wrapper must compute a_user.cmd_intg and a_user.data_intg with the OpenTitan TL-UL host integrity generator, so the request carries correct integrity. *(when: i_a_intg_flip = 0)* | fix: check assertion->both |
| RT-4.2-02 |  | MUST | system | assertion | Bit 0 of a_user.cmd_intg must be inverted. *(when: i_a_intg_flip is 1)* | keep |
| RT-4.2-03 |  | MUST | slave | scenario | Such a request is a fatal TL-UL bus integrity fault that triggers the fatal_fault alert. *(when: request has command integrity error (i_a_intg_flip is 1))* | keep |
| RT-4.3-01 |  | MUST | system | assertion | o_d_intg_err must be 1 in a cycle where o_d_valid is 1 and the d_user.rsp_intg check fails, and 0 otherwise. | keep |
| RT-4.3-02 |  | MUST_NOT | slave | assertion | A correct device must never make o_d_intg_err 1. | keep |
| RT-5-01 |  | MUST | system | none | rv_timer has one alert, fatal_fault, sent through an alert sender. | keep |
| RT-5-02 |  | MUST | system | both | o_alert is the receiver's alert_o output and is 1 for one clock cycle for each alert handshake the receiver detects. *(when: When the alert receiver detects an alert handshake)* | keep |
| RT-5-04 |  | MUST_NOT | system | assertion | A correct sender never makes o_alert_integ_fail 1. *(when: With a correct alert sender)* | fix: actor slave->system |
| RT-5-05 |  | MUST | system | scenario | o_alert pulses repeatedly after a bus integrity fault until rst_ni is asserted, as a fatal alert is repeated until reset. *(when: After a bus integrity fault, until rst_ni is asserted)* | keep |
| RT-5-06 |  | MUST | system | scenario | A write of 1 to ALERT_TEST.fatal_fault triggers exactly one alert event. *(when: A write of 1 to ALERT_TEST.fatal_fault)* | keep |
| RT-6-02 |  | MUST | system | scenario | o_intr_timer_expired must behave as an event-type interrupt per the comportability specification, with registers INTR_ENABLE0, INTR_STATE0 and INTR_TEST0. | keep |
| RT-7-01 |  | MUST | system | scenario | Verification shall cover reset values of every register through the ports. | keep |
| RT-7-02 |  | MUST | system | scenario | Verification shall cover the access type of every register field as given in the register tables (rw, rw1c, wo, rw0c). | keep |
| RT-7-03 |  | MUST | system | scenario | Verification shall cover the tick generator (prescaler) and the step. | keep |
| RT-7-04 |  | MUST | system | scenario | Verification shall cover counting of the 64-bit timer value, including writes to it and the carry from the lower to the upper half. | keep |
| RT-7-05 |  | MUST | system | scenario | Verification shall cover the compare and the interrupt: state, enable, test, and clearing by writing the compare registers. | keep |
| RT-7-06 |  | MUST | system | scenario | Verification shall cover ALERT_TEST with its regwen field. | keep |
| RT-7-07 |  | MUST | system | scenario | Verification shall cover bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the fatal_fault alert. | keep |
| RT-7-08 |  | MUST | system | scenario | Behaviour close to 2^64 shall be reached by writing the timer value registers. *(when: Because the 64-bit timer value cannot be run through its whole range in simulation)* | keep |
| RT-8-01 |  | MUST | system | scenario | Timer value increases by CFG0.step (modulo 2^64) once every CFG0.prescale + 1 cycles; prescale 0 gives a tick every cycle. *(when: CTRL.active_0 = 1 and CFG0 unchanged)* | keep |
| RT-8-02 |  | MUST | system | scenario | The first tick shall come no later than CFG0.prescale + 1 + 4 cycles after the write response. *(when: after CTRL.active_0 becomes 1)* | keep |
| RT-8-03 |  | MUST | master | none | Tests write CFG0 and TIMER_V_* only while CTRL.active_0 = 0; behaviour after such a write while active is not checked. *(when: writing CFG0 or TIMER_V_*)* | keep |
| RT-8-04 |  | MUST | system | scenario | INTR_STATE0.IS_0 shall read 1 within 4 cycles after a write of 1 to it. *(when: mtime >= mtimecmp holds and timer is active, after a write of 1 to INTR_STATE0.IS_0)* | keep |
| RT-8-05 |  | MUST | system | scenario | IS_0 shall be 1 no later than 4 cycles after that tick. *(when: condition mtime >= mtimecmp becomes true by a tick)* | keep |
| RT-8-06 |  | MUST | system | scenario | IS_0 shall be 1 no later than CFG0.prescale + 1 + 4 cycles after the write response. *(when: condition becomes true by a register write while active)* | keep |
| RT-8-07 |  | MUST | system | assertion | o_intr_timer_expired shall equal IS_0 AND IE_0. *(when: except in the 2 cycles after IS_0 or IE_0 changes)* | keep |
| RT-8-08 |  | MUST | system | scenario | IS_0 shall be 0 and the interrupt deasserted within 4 cycles. *(when: after a write to COMPARE_LOWER0_0 or COMPARE_UPPER0_0 leaves mtimecmp > mtime and it stays so)* | keep |
| RT-8-09 |  | MUST | system | scenario | IS_0 shall be 1 again within 4 cycles; an intermediate dip is not checked. *(when: after a compare write mtime >= mtimecmp still holds)* | keep |
| RT-8-10 |  | MUST | slave | scenario | Write-only fields read 0, reserved bits read 0 and writes to them have no effect. | keep |
| RT-8-11 |  | MUST | slave | scenario | INTR_TEST0 reads 0x0 and ALERT_TEST reads 0x8000_0000. *(when: after reset)* | keep |
| RT-8-12 |  | MUST | slave | scenario | Regwen reads 0 until reset; a later write of 0x8000_0001 completes with d_error = 0, triggers no alert. *(when: after a write to ALERT_TEST with bit 31 = 0 (regwen cleared until reset))* | keep |
| RT-8-13 |  | MUST | slave | scenario | Exactly one o_alert pulse shall occur, no later than 16 cycles after the write response. *(when: one write of 1 to fatal_fault, no other alert cause, no other such write within 32 cycles)* | keep |
| RT-8-14 |  | MUST | slave | scenario | At least one o_alert pulse and no more pulses than writes shall occur. *(when: fatal_fault writes closer than 32 cycles apart)* | keep |
| RT-8-15 |  | MUST_NOT | master | none | Tests do not use the combined write 0x0000_0001; they write 0x8000_0001. *(when: triggering an alert)* | keep |
| RT-8-16 |  | MUST | slave | scenario | o_alert shall pulse no later than 16 cycles after acceptance, then at least once every 32 cycles until rst_ni is asserted. *(when: request with i_a_intg_flip = 1 accepted)* | keep |
| RT-8-17 |  | MUST | master | none | The test resets the design. *(when: after a test with i_a_intg_flip = 1)* | keep |
| RT-8-18 |  | MUST_NOT | master | none | A write with i_a_instr = 1 is not used. | keep |
| RT-8-19 |  | MUST | slave | scenario | The slave returns d_error = 1 and changes no register. *(when: request to an unmapped offset in 0x000..0x1FF)* | keep |
| RT-8-20 |  | MUST_NOT | master | none | Requests at offset 0x200 and above are not used. | keep |
| RT-8-21 |  | MUST | slave | scenario | Returns d_error = 1 and changes nothing. *(when: byte write (a_size 0, mask 0001, aligned) to CFG0, TIMER_V_*, COMPARE_* or ALERT_TEST)* | keep |
| RT-8-22 |  | MUST | slave | scenario | Completes with d_error = 0 and has the effect of the write. *(when: byte write to byte 0 of CTRL, INTR_ENABLE0, INTR_STATE0 or INTR_TEST0)* | keep |
| RT-8-23 |  | MUST | slave | scenario | The write succeeds with d_error = 0. *(when: full-word write with mask 1111)* | keep |
| RT-8-25 |  | MUST | master | none | Match responses by d_source, use distinct a_source per outstanding request, and do not assume o_a_ready = 1. *(when: outstanding requests)* | keep |
| RT-8-26 |  | MUST | slave | scenario | Returned value lies between values before the request and after the response. *(when: read of TIMER_V_* while active)* | keep |
| RT-8-27 |  | MUST | slave | assertion | d_error is correct, d_source echoes a_source, d_size echoes a_size, d_opcode is AccessAckData for Get and AccessAck for PutFullData and PutPartialData. *(when: response)* | keep |
| RT-8-28 |  | MUST | slave | scenario | d_error = 1 is returned. *(when: undefined opcode)* | keep |
| RT-8-29 |  | MUST | master | none | The test bench keeps i_a_valid = 0. *(when: rst_ni = 0 and first cycle after release)* | keep |
| RT-8-30 |  | MUST | slave | assertion | o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired shall be 0. *(when: rst_ni = 0)* | keep |
| RT-8-31 |  | MUST | slave | scenario | The pending response is discarded. *(when: response pending at reset)* | keep |
| RT-8-32 |  | MUST | slave | assertion | o_d_intg_err and o_alert_integ_fail shall be 0 in every cycle. *(when: rst_ni = 1, including during i_a_intg_flip = 1)* | keep |
| RT-8-33 |  | MUST | master | none | Reached only by writing the timer value registers while inactive to values near the carry, then counting. *(when: testing carry at 2^32 and near 2^64)* | keep |
| RT-8-34 |  | MUST | master | none | Tests drive i_a_param = 0. | keep |

## opentitan_tlul_bus_specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| TL-T2.2-01 |  | MAY | system | scenario | Existing TL-UL IP blocks may be used directly in devices that do not need the additional sideband signals. *(when: Devices that do not need the additional sideband (user extension) signals)* | keep |
| TL-T2.2-03 |  | MUST | any | scenario | The bus carries only one request and one response per cycle, and no burst transactions. | fix: check assertion->scenario |
| TL-T2.3-01 |  | MAY | system | scenario | Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. | keep |
| TL-T2.3-02 |  | MUST | any | scenario | As a receiver, a baseline block ignores the user signals. *(when: Block built to the base specification acts as a receiver)* | fix: actor destination->any |
| TL-T2.3-03 |  | MUST | any | scenario | As a source, a baseline block generates a project-specific default value for the user signals. *(when: Baseline block acts as a source)* | fix: actor source->any |
| TL-T3.1.1-02 |  | MUST | slave | scenario | TL-UL devices tolerate reset windows shorter than 100 cycles. *(when: reset window shorter than 100 cycles)* | fix: strength MAY->MUST |
| TL-T3.1.3.1-01 |  | MUST | interconnect | scenario | Request steering must be a function of the address only; a_source and a_user must not enter into the address calculation. *(when: routing a request)* | keep |
| TL-T3.1.3.2-01 |  | MAY | master | scenario | A host may use a_source/d_source to ascribe request identifiers, since TL-UL does not guarantee in-order responses. *(when: response reordering is required)* | keep |
| TL-T3.1.3.2-02 |  | MUST | system | none | The fabric architect must ensure AIW covers the host outstanding requests and the maximum source ID growth added by bus primitives. | keep |
| TL-T3.1.3.2-03 |  | MUST | system | none | The fabric must provide enough host ID bits to maintain those ID values. *(when: converting from a host such as AXI using RID or WID)* | keep |
| TL-T3.1.3.2.1-01 |  | MUST | interconnect | both | The primitive shifts a_source left and post-pends sub-source bits; on the response it shifts them off, shifting zeros into the top, and returns the result on d_source. *(when: a primitive adds source ID bits)* | keep |
| TL-T3.1.3.2.1-02 |  | SHOULD | interconnect | none | Assertions should ensure no significant bits of a_source are lost in M:1 sockets. *(when: M:1 sockets)* | fix: check assertion->none |
| TL-T3.1.3.2.2-01 |  | MUST_NOT | master | none | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | keep |
| TL-T3.1.3.2.3-01 |  | MUST | slave | both | Devices must return the associated a_source on the response d_source. | fix: check assertion->both |
| TL-T3.1.3.3-01 |  | MUST | any | none | Bus hosts and devices must understand the usage of user bits and apply them appropriately. | keep |
| TL-T3.1.3.3-03 |  | SHOULD | interconnect | both | The bus fabric must not rely on user bits for transport and must pass them on blindly; usage must be assigned project-wide. | fix: strength MUST->SHOULD |
| TL-T3.1.3.4-01 |  | MAY | master | scenario | a_opcode may designate a write (Put) or read (Get); writes may be full (PutFullData) or partial (PutPartialData). | keep |
| TL-T3.1.3.4-02 |  | SHOULD_NOT | master | assertion | TL-UL hosts in this project should not use non-contiguous a_mask values such as 0b1001. | keep |
| TL-T3.1.3.4-03 |  | MAY | slave | scenario | Devices may assert d_error if they do not support a particular subword a_mask. *(when: device does not support a subword mask)* | keep; merged TL-T3.1.3.5-06 |
| TL-T3.1.3.4-04 |  | SHOULD | master | assertion | For PutFullData, a_size should be 'h2 for a 32b write ('h3 for 64b bus). *(when: a_opcode is PutFullData)* | keep |
| TL-T3.1.3.4-05 |  | SHOULD | master | assertion | For PutPartialData, a_size should encode 2^a_size bytes and the a_mask bits should indicate the valid byte lanes. *(when: a_opcode is PutPartialData)* | keep |
| TL-T3.1.3.4-06 |  | SHOULD | slave | both | Devices should return an error for undefined request opcodes. *(when: a_opcode is 3'b01x, 3'b101 or 3'b11x)* | keep |
| TL-T3.1.3.4-07 |  | SHOULD | master | scenario | Undefined response opcodes d_opcode 3'b01x and 3'b1xx should return an error. *(when: d_opcode is 3'b01x or 3'b1xx)* | fix: actor any->master |
| TL-T3.1.3.5-01 |  | MUST | slave | both | TL-UL devices must raise a runtime error via d_error when a request carries a wrong opcode. *(when: request has a wrong opcode)* | keep |
| TL-T3.1.3.5-02 |  | MUST_NOT | master | both | a_size must not be greater than 2; a request violating this is flagged by the device with d_error. *(when: request issued)* | keep |
| TL-T3.1.3.5-03 |  | MUST | master | both | Inactive lanes must be marked with 'b0 in a_mask; violation is flagged by the device with d_error. *(when: request has inactive lanes)* | keep |
| TL-T3.1.3.5-04 |  | MUST | master | both | PutFullData must mark all active lanes with a 'b1 in a_mask; violation is flagged by the device with d_error. *(when: a_opcode is PutFullData)* | keep |
| TL-T3.1.3.5-05 |  | MUST | slave | scenario | TL-UL devices must raise a runtime error via d_error for accesses to non-existent addresses. *(when: request accesses a non-existent address)* | fix: check both->scenario |
| TL-T3.1.3.5-07 |  | MUST | master | both | Register files always assume aligned 32-bit accesses, so accesses to them must be aligned 32-bit. *(when: accessing register files)* | keep |
| TL-T3.1.3.5-08 |  | MUST | master | both | A host must discard orphaned responses (no valid request counterpart) and responses with the wrong opcode. *(when: response is orphaned or has the wrong opcode)* | fix: check scenario->both |
| TL-T3.1.3.5-10 |  | MAY | any | none | Devices and hosts may implement additional, more restrictive checks if needed. | keep |

## opentitan_comportability.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| CP-T1.5.2-01 |  | MUST | system | none | Each peripheral must specify clocking via a nonempty list of clocking items, each defining clock and reset in fields named clock and reset. | keep |
| CP-T1.5.2-02 |  | SHOULD | system | none | Exactly one clocking item dictionary should have boolean field primary set to true. *(when: When there are several clocking items)* | keep |
| CP-T1.5.2-03 |  | MUST | system | none | The primary clock is used to clock any device interfaces. | keep |
| CP-T1.5.2-04 |  | MUST | system | scenario | Resets within the design are asynchronous active low: assertion is asynchronous to any clock, deassertion is synchronized to the clock of the associated storage element. | fix: check both->scenario |
| CP-T1.5.2-05 |  | SHOULD | system | none | Security sensitive storage elements need special care, e.g. synchronous reset after chip-wide reset to a randomized value. *(when: For security sensitive storage elements)* | keep |
| CP-T1.5.2-06 |  | MAY | system | none | The clock and reset fields of a clocking item are optional. *(when: For blocks that generate clocks or resets)* | keep |
| CP-T1.5.2-07 |  | MUST | system | none | The primary clock item must have both clock and reset fields. | keep |
| CP-T1.5.3-02 |  | MUST | system | none | Every peripheral must expose at least one device interface on the chip bus. | keep |
| CP-T1.5.3-03 |  | MAY | system | none | Peripherals can act as bus host on some occasions, though the processor being primary host is preferred. | keep |
| CP-T1.5.3-04 |  | SHOULD | system | none | The bus_interfaces attribute should contain a list of dictionaries describing the interfaces the peripheral exposes. | keep |
| CP-T1.5.3-05 |  | MUST | system | none | The peripheral must have protocol of tlul since all peripherals use TL-UL. | keep |
| CP-T1.5.3-06 |  | MUST | system | none | Each bus interface entry must contain a direction of either host or device. | keep |
| CP-T1.5.3-07 |  | MUST | master | scenario | All bus hosts must use the same clock as the defined primary host clock. | keep |
| CP-T1.5.3-08 |  | MAY | system | none | An entry may include a name, which is added as a prefix to the module's top-level port names. | keep |
| CP-T1.5.3-09 |  | MUST | system | none | The name field must be provided to avoid port name collisions. *(when: When another entry in the list has the same direction)* | keep |
| CP-T1.5.5-01 |  | MUST | system | none | The module must have an output named intr_name_o for each interrupt name. *(when: For each name in the interrupt list)* | keep |
| CP-T1.6-01 |  | MUST | system | none | All lowRISC peripheral designs must conform to the register specification. | keep |
| CP-T1.8-01 |  | SHOULD | system | none | All interrupts shall have common naming, hardware interfaces, and software interfaces. *(when: Where possible)* | keep |
| CP-T1.8.1-01 |  | MUST | source | assertion | Wired CIP interrupts use active-high level-triggering. | keep |
| CP-T1.8.2-01 |  | MUST | system | none | Each interrupt_list entry must have a required name key of type string. | keep |
| CP-T1.8.2-02 |  | MAY | system | none | Each interrupt_list entry may have an optional desc string. | keep |
| CP-T1.8.2-03 |  | MAY | system | none | Each entry may have an optional type, Event or Status, defaulting to Event if unspecified. | keep |
| CP-T1.8.3-01 |  | MUST | system | scenario | A peripheral generates a separate wired interrupt for each interrupt source. | keep |
| CP-T1.8.3-02 |  | MUST_NOT | system | none | Peripherals do not send a single combined interrupt for the processor to disambiguate by querying the peripheral. | keep |
| CP-T1.8.4-01 |  | MUST | system | scenario | INTR_STATE, INTR_ENABLE and INTR_TEST registers are created at the top of the address map in that order, one bitfield per interrupt. | keep |
| CP-T1.8.4-02 |  | MUST_NOT | system | none | The .hjson must not define more than 32 interrupts per peripheral. | keep |
| CP-T1.8.4-03 |  | MUST | slave | scenario | INTR_STATE at offset 0x0 holds interrupt state, INTR_ENABLE at 0x4 masks it to intr_o, INTR_TEST at 0x8 is write-only and asserts the interrupt. | keep |
| CP-T1.8.4-04 |  | MUST | slave | scenario | INTR_STATE shows raw latched interrupt events and is not qualified by INTR_ENABLE. | keep |
| CP-T1.8.5-02 |  | MUST | slave | scenario | The interrupt is cleared only by a software W1C write of the INTR_STATE bitfield. *(when: Event type interrupt)* | keep |
| CP-T1.8.5-03 |  | MUST | source | scenario | Interrupt requests are triggered while input is true, including immediately after the previous request is acknowledged. *(when: Status type interrupt, input persistently true)* | keep |
| CP-T1.8.5.1-01 |  | MUST | source | both | When the event occurs it is latched into the INTR_STATE bitfield and intr_o is latched high until acknowledged, then low. *(when: Event type interrupt)* | keep |
| CP-T1.8.5.2-01 |  | MUST | system | assertion | A status type interrupt must drive a wired level-triggered interrupt directly from the hardware input signal, qualified only by INTR_ENABLE, staying asserted while the input is asserted. *(when: Status type interrupt)* | keep |
| CP-T1.8.5.2-02 |  | MUST | system | scenario | The wired status interrupt must not deassert until the root cause of the hardware input signal is addressed by software intervention. *(when: Status type interrupt)* | keep |
| CP-T1.8.5.2-03 |  | MUST_NOT | slave | scenario | Software cannot acknowledge a status type interrupt through INTR_STATE, which is read-only (ro) in this context. *(when: Status type interrupt)* | keep |
| CP-T1.8.5.2-05 |  | SHOULD | master | none | Software should mask the interrupt, at the peripheral or further up the tree such as the PLIC. *(when: SW cannot address the root cause or wishes to defer handling)* | keep |
| CP-T1.8.5.2-06 |  | MAY | master | scenario | Masking at the peripheral can be achieved by clearing the corresponding bit in INTR_ENABLE. *(when: Masking at the peripheral)* | keep |
| CP-T1.8.6-02 |  | MUST | slave | assertion | The event must set the associated bit in INTR_STATE to 1. *(when: Event foo is detected)* | keep |
| CP-T1.8.6-03 |  | MAY | master | scenario | A write of 1 to the associated foo bit of INTR_TEST can set the corresponding INTR_STATE bit. *(when: Write of 1 to the foo bit of INTR_TEST)* | keep |
| CP-T1.8.6-04 |  | MUST | slave | assertion | The outgoing interrupt intr_foo_o must be the INTR_STATE output ANDed with INTR_ENABLE. | keep |
| CP-T1.8.6-05 |  | MUST | slave | both | A write of 1 to an INTR_STATE bit clears the latched value, but INTR_STATE returns to true if the event is still active. *(when: Software writes 1 to the INTR_STATE bit)* | keep |
| CP-T1.8.6-06 |  | MUST_NOT | slave | assertion | Hardware must not clear the latched interrupt state; only software can clear it. | keep |
| CP-T1.9.1-03 |  | MUST | slave | scenario | A recoverable alert must be one-time triggered: the alert sender transmits a single alert event when the error condition is asserted. *(when: Recoverable alert)* | keep |
| CP-T1.9.1-04 |  | MUST | slave | scenario | A fatal alert must be continuously transmitted by the alert sender until the system is reset. *(when: Fatal alert)* | keep |
| CP-T1.9.1-05 |  | SHOULD | slave | none | Fatal alerts should also trigger local security countermeasures. *(when: Fatal alert and local countermeasures exist)* | keep |
| CP-T1.9.1-07 |  | MAY | slave | none | A peripheral may optionally send a regular IRQ for any alert event, if needed by the programming model. *(when: Alert event occurs)* | keep |
| CP-T1.9.2-02 |  | MUST | any | none | Recoverable alerts must be prefixed with recov_ and fatal alerts must be prefixed with fatal_. *(when: Alert naming)* | keep |
| CP-T1.9.2-03 |  | MAY | any | none | Alert names may default to just recov and/or fatal, implying no more than one alert of that type is exposed. *(when: Many diverse sources bundled into one alert event)* | keep |
| CP-T1.9.3-01 |  | MUST | slave | scenario | Every peripheral has a write-only (wo) ALERT_TEST register for software to test alert reporting in the alert handler. | keep |
| CP-T1.9.3-02 |  | MUST | slave | both | Every alert has one field bit in ALERT_TEST, connected to the test input of the corresponding prim_alert_sender. | fix: check scenario->both |
| CP-T1.9.4-01 |  | MUST | slave | scenario | Internal events are sent active-high to the prim_alert_sender within the peripheral. | fix: check assertion->scenario |
| CP-T1.9.4-02 |  | MUST | slave | both | One prim_alert_sender must be instantiated per distinct alert event, with IsFatal set to 1 for fatal alerts so the alert is latched until reset. | keep |
| CP-T1.9.4-03 |  | MAY | any | none | The peripheral maintainer determines distinct alert events; multiple sources can be bundled depending on the required distinction. | keep |
| CP-T1.9.4-04 |  | SHOULD | any | none | Each peripheral should bundle alert sources into one or two distinct alerts, for example one fatal and one recoverable. | keep |
| CP-T1.9.4-05 |  | SHOULD | slave | scenario | The IP should expose a cause register for disambiguation. *(when: Comportable IP with multiple bundled alerts)* | keep |
| CP-T1.9.4-06 |  | MUST | slave | scenario | Cause registers for recoverable alerts must be clearable by SW or automatically cleared by HW. *(when: Cause register for recoverable alerts)* | keep |
| CP-T1.9.4-07 |  | MUST | slave | scenario | Cause registers for fatal alerts must not be clearable in any way and must be read-only. *(when: Cause register for fatal alerts)* | fix: strength MUST_NOT->MUST |
| CP-T1.9.4-08 |  | MUST | slave | both | The prim_alert_sender converts the event into a differentially encoded signal pair routed to the hardware alert handler. | keep |

## opentitan_register_tool.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| RG-T1.3-03 |  | MUST | system | none | The name_reg2hw_t structure contains the signals driven from the register module to the rest of the hardware, including required .q, .qe and .re signals. | fix: actor master->system, check scenario->none |
| RG-T1.3-04 |  | MUST | system | none | The name_hw2reg_t structure contains the signals driven from the rest of the hardware to the register module, including required .d and .de signals. | fix: check scenario->none |
| RG-T1.4.1-01 |  | SHOULD | slave | scenario | Accesses to unmapped target addresses fully representable with internal address bits typically return an error. *(when: access to an unmapped address representable with the internally used address bits)* | keep |
| RG-T1.4.1-02 |  | MUST | slave | scenario | If the stripped address is mapped, the request is forwarded to the register and no error is returned. *(when: excess address bits map the request to a mapped address, e.g. 0x184 to 0x84)* | keep |
| RG-T1.4.1-03 |  | SHOULD | slave | scenario | A request to unmapped address 0x88 typically returns an error. *(when: module registers span 0x0 to 0x84 with 8 internal address bits; request to unmapped address 0x88)* | keep |
| RG-T1.4.1-04 |  | MUST | slave | both | An error response is returned when TL-UL a_opcode has an illegal value. *(when: a_opcode has an illegal value)* | keep |
| RG-T1.4.1-05 |  | MUST | slave | both | A write smaller than the register size must return an error. *(when: TL-UL write of size smaller than the register size, e.g. 8b write to a register wider than 8 bits)* | keep |
| RG-T1.4.1-06 |  | MUST | slave | both | Writes smaller than 32b that are not word-aligned must return an error. *(when: 8b or 16b write to an address not 4B aligned)* | keep |
| RG-T1.4.1-07 |  | MUST | slave | both | Reads smaller than a full word return the full register content and do not signal an error. *(when: read smaller than full word)* | keep |
| RG-T1.4.1-08 |  | MUST | slave | both | Read response data is always in its byte channel, e.g. a one-byte read to 0x3 returns the full word with the correct byte in bits [31:24]. *(when: sub-word read)* | keep |
| RG-T1.4.1-09 |  | SHOULD | slave | scenario | Windows should follow the error rules based on the declared validbits, though this may be relaxed in some cases. *(when: windowed TL-UL bus)* | fix: actor system->slave, check none->scenario |
| RG-T1.5.1-01 |  | MUST | slave | both | The software-written value takes priority over the hardware update. *(when: software and hardware request an update in the same clock cycle (de and we both true))* | keep |
| RG-T1.5.1-02 |  | MAY | slave | scenario | The hardware can present updated values through de and d. *(when: hwaccess allows hardware writes)* | keep |
| RG-T1.5.1-03 |  | MUST | slave | both | The register content is updated with d. *(when: de is true and no software write)* | fix: check assertion->both |
| RG-T1.5.1-05 |  | MUST | slave | assertion | qe is a registered version of the bus write enable we, aligned with the change in q. *(when: hwqe is true)* | keep |
| RG-T1.5.3-02 |  | MUST | slave | scenario | A software read returns a hardwired value equal to the register default value. *(when: swaccess is ro, hwaccess is none or hro, and hwext is true)* | keep |
| RG-T1.5.4-01 |  | MUST | slave | scenario | When re indicates the register is being read, the register contents are set to zero. *(when: RC register is read)* | keep |
| RG-T1.5.6.1-01 |  | MUST | slave | scenario | The subreg for R0W1C/RW1S/RW1C/RW0C types must handle simultaneous hardware and software write attempts. *(when: hardware and software attempt to write the register at the same time)* | keep |
| RG-T1.5.6.1-02 |  | MUST | slave | scenario | Software has precedence over hardware, as for the RW type. *(when: hardware and software write simultaneously)* | keep |
| RG-T1.5.6.1-04 |  | SHOULD | master | none | Hardware should feed the q value back into d, only setting bits with new events, to avoid collisions with software clearing. *(when: hardware writes a RW1C-type register)* | keep |
| RG-T1.5.6.1-05 |  | MUST | slave | both | The software clear must still take effect for one cycle to create a new interrupt edge, then q returns to 1 since d is still 1. *(when: software clears a RW1C bit while the hardware d input is still 1)* | keep |
| RG-T1.5.6.2-01 |  | MAY | any | scenario | RW1C, RW1S and similar register types may be created with hwext true. | keep |
| RG-T1.5.6.2-02 |  | MUST | system | scenario | The auto-generated hardware is the same as the hwext RW register, with the implementation done outside the generated register block. *(when: RW1C, RW1S or similar register has hwext true)* | keep |
| RG-T1.5.6.2-03 |  | MAY | any | scenario | hwqe may be set true for these register types. *(when: clearing is to be monitored by external hardware)* | keep |

## opentitan_alert_handler_theory_of_operation.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| AH-T1.3.1-02 |  | SHOULD | source | none | Peripherals defining alerts should instantiate one prim_alert_sender module to convert the alert event into a signal to the alert handler. *(when: A peripheral defines one or more alert signals)* | fix: strength MUST->SHOULD, actor slave->source |
| AH-T1.3.2-01 |  | MUST | any | scenario | Alerts are encoded differentially and signaled using a full handshake on the alert_p/n and ack_p/n wires. | fix: check both->scenario |
| AH-T1.3.2-02 |  | MUST | slave | scenario | The alert sender must keep repeating the native alert message and handshake pattern on its output wires while the alert is true. *(when: The alert event is still true within the peripheral)* | keep |
| AH-T1.3.2-03 |  | MUST | slave | both | The sender waits 2 cycles between handshakes. *(when: Between repeated handshakes)* | fix: check assertion->both |
| AH-T1.3.2-04 |  | MUST | slave | both | The receiver must immediately propagate the first occurrence of an alert to alert_o. *(when: Initial level change on alert_tx_i.alert_p/n is received and synchronized, even if handshake lines are manipulated to emulate backpressure)* | fix: actor master->slave |
| AH-T1.3.4-01 |  | MUST | master | both | The receiver must assert integ_fail_o when alert_tx_i.alert_p/n is incorrectly encoded. *(when: The alert_tx_i.alert_p/n pair is not correctly encoded at the receiver)* | keep |
| AH-T1.3.4-02 |  | MUST | slave | both | The sender must set alert_tx_o.alert_p/n to the same continuously toggling value, which triggers integ_fail_o on the receiver. *(when: The ping_p/n or ack_p/n pair is incorrectly encoded on the sender side)* | keep |
| AH-T1.3.4-03 |  | MUST | system | both | Such lock-up must always trigger either a signal integrity alert or eventually a pingfail alert. *(when: Signal integrity failures occur during ping or alert handshaking and the protocol state machines lock up)* | fix: check scenario->both |

## Rejected

| ID | Statement | Reason |
|---|---|---|
| RT-T2.3-01 | The timer IP provides memory-mapped registers equivalent to mtime and mtimecmp usable as the RISC-V machine-mode timer registers. | The quote is a descriptive statement of capability ('can be used as'), with nothing concrete to verify beyond the register behaviour that is specified elsewhere. It does not state a testable requirement. |
| RT-T3.2.1-01 | The tick generator produces a fixed-period pulse signal, enabling a timer tick such as 1us or 10us regardless of the system clock period. | Descriptive statement of purpose; no concrete verifiable behavior beyond what T3.1-01 already covers. |
| RT-T3.2.1-02 | Firmware should change CFG0.prescaler appropriately for the single fixed clock frequency to obtain the desired tick period. | Firmware guidance/software programming advice; not a hardware behavior to verify. |
| RT-T3.2.2-02 | Each hart can have multiple sets of mtimecmp, comparator logic, and expire interrupt signals. | Optional capability that is overridden by the fixed one-timer-per-hart limitation in this version; nothing to verify. |
| RT-T4.2-01 | The CPU cannot access a 64-bit value in a single request over the 32-bit register interface; two 32-bit accesses are required. | Describes a CPU limitation (a bus width fact); nothing to verify on the DUT, and the rule restates it as a prohibition the quote does not impose. |
| RT-T4.2-02 | The timer value may increment between the two 32-bit reads of mtime and mtimeh. | Descriptive observation of a hazard, not a testable requirement on the DUT. |
| RT-T4.2-03 | A rollover between the two reads can be detected in a standard way using a third read. | Describes a software technique with no concrete verifiable behaviour; the third-read sequence is not specified in the quote. |
| RT-T4.2-04 | Software should use the prescribed safe write sequence to set mtime so timer operation does not yield an indeterminate result. | The quote refers to a sequence that is not given in it; the rule is not verifiable from the quote itself and is software guidance. |
| RT-T4.2-05 | The safe write sequence should be used so the timer does not assume an incorrect time between the two 32-bit writes. | Describes the rationale of an unspecified sequence; the sequence is not in the quote, so nothing concrete to check. |
| RT-T4.3-01 | One tick can carry mtime from below mtimecmp past the end of the range, so mtime skips mtimecmp and the interrupt is not raised. | Descriptive of a hazard/behaviour consequence with an uncertain actor; it is an explanation, not a requirement to check. |
| RT-T4.3-03 | The service routine needs to poll mtime until it wraps before scheduling the required interrupt with the originally computed mtimecmp value. | Software service routine behaviour described as a consequence of a suggested solution; the quote does not state a verifiable DUT requirement and it is part of a possible solution. |
| RT-T4.3-04 | mtime can step over the all-ones value so the intermediate interrupt is never raised. | Descriptive observation of a limitation of the solution, not a requirement. |
| RT-T5.2.1-02 | ALERT_TEST bits 30:1 are reserved. | Reserved bits are only a description; the quote gives no behaviour to verify. |
| RT-T6.1-02 | The module must output RACL error log information of this module on racl_error. | Quote is only a port description (name, type, direction); it states no verifiable behaviour of when or how racl_error is output. |
| RT-T6.4-01 | The module must implement the RV_TIMER.BUS.INTEGRITY countermeasure, an end-to-end bus integrity scheme on the TL-UL interface. | Quote is a countermeasure table entry with only a name and a vague description; no concrete verifiable behaviour beyond what the fatal_fault alert rule covers. |
| RT-T7-01 | The verification top ot_rv_timer_nnc must consist of the OpenTitan rv_timer plus a thin wrapper that flattens its struct ports and closes two protocols. | Descriptive statement of the verification top's composition; nothing to verify or exercise as behaviour. |
| RT-T7-02 | The behaviour of rv_timer itself must follow only the OpenTitan documents; the wrapper adds only port mapping, fixed configuration and wrapper behaviour. | Document-scope statement about where behaviour is specified; not a testable behaviour of the design. |
| RT-1-05 | Alert ping requests are never issued. | The quote 'Ping requests are never issued.' has no context. It does not name the alert channel or the condition, and the rule's wording is a restatement without a verifiable scope. Also, as a bare fragment it is ambiguous about whether it is a design property or a testbench constraint. |
| RT-2-01 | clk_i is the only clock in the design. | The quote only describes the design structure, that clk_i is the only clock. There is no behaviour to verify and no stimulus to exercise, so it is a description and not a testable requirement. |
| RT-5-03 | o_alert_integ_fail is the integ_fail_o output of the alert receiver. | Only a connection description (o_alert_integ_fail equals integ_fail_o of an internal receiver); nothing checkable from interface signals beyond the receiver's internals. |
| RT-6-01 | o_intr_timer_expired must be the interrupt output intr_timer_expired_hart0_timer0_o of rv_timer. | The quote only names the port as the rv_timer interrupt output. It is a description of the connection, with nothing to verify and nothing checkable every cycle from interface signals. |
| RT-8-24 | Returns the full register. | The quote does not say that a read of any size returns the full register. It only covers write errors, and the visible text says nothing about reads. |
| TL-T2.2-02 | Existing TL-UL IP blocks can be adapted to use the added user extension features. | Vague 'straightforwardly adapted' statement about design effort; nothing to verify or exercise. Also merely restates the second half of the same sentence as 01. |
| TL-T2.2-04 | Bus primitives can be combined to form a flexible crossbar connecting any M hosts to any N devices. | Descriptive statement about composability of primitives into a crossbar; no checkable behaviour. |
| TL-T2.3-04 | Blocks can be modified to make use of the user extensions. | Statement that blocks can be easily modified; a design-effort remark with nothing to verify. |
| TL-T3.1.1-01 | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles during reset, unlike TileLink 1.7.1. | Describes a relaxation relative to TileLink; nothing to verify or exercise (not a stimulus the DUT must handle). |
| TL-T3.1.3.3-02 | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | Quote says user bits follow the same timing as source bits; this is descriptive and not a precise checkable rule, and the actor 'any' is unclear. |
| TL-T3.1.3.5-09 | Raising a critical hardware error on protocol-check violations is planned but not yet implemented. | Describes an unimplemented planned feature; nothing to verify. |
| CP-T1.5.2.1-01 | Tradeoff notes on asynchronous active low versus synchronous active high reset are informative only. | Informative tradeoff commentary; nothing to verify. |
| CP-T1.5.3-01 | Peripherals can connect to the chip bus. | Descriptive statement; nothing to verify or exercise. |
| CP-T1.8.5-01 | A designer may choose between Event and Status interrupt behaviors. | Descriptive design choice; nothing to verify. |
| CP-T1.8.5-04 | Designers may generate interrupts from instantaneous events or persistent status, making software handlers simpler and race-free. | Design rationale; no verifiable behaviour. |
| CP-T1.8.5.1-02 | prim_intr_hw parameterized with .IntrT("Event") can generate Event interrupt hardware. | Implementation note about a primitive; no checkable behaviour. |
| CP-T1.8.5.2-04 | The generic component prim_intr_hw can generate the correct status interrupt hardware when parameterized with .IntrT("Status"). | Implementation note about a primitive; no checkable behaviour. |
| CP-T1.8.6-01 | The block diagram shows one possible hardware implementation of interrupt foo; other implementations are permitted. | Descriptive of one possible implementation. |
| CP-T1.9.1-01 | Each peripheral can send zero or more alerts, each a distinguishable security threat. | Descriptive; nothing to verify. |
| CP-T1.9.1-02 | Each alert originates in an internal event and must be specially handled within the peripheral and then within the alert handler module. | 'Specially handled' is vague with no verifiable behaviour. |
| CP-T1.9.1-06 | Error conditions should use the recommended alert type listed in the table; the regular IRQ column entries marked (x) are optional. | The table content is not in the quote; the rule cannot be derived from it. |
| CP-T1.9.2-01 | Alerts shall be given a meaningful name indicative of their cause. | 'Meaningful' is subjective and not verifiable. |
| CP-T1.9.4-09 | The alert handler is generated with enough alert ports for each alert declared in the included peripheral configuration files. | This describes automatic generation of the alert handler, a tool-flow description. It is not testable behaviour of the peripheral. |
| RG-T1.3-01 | The tool output is two Verilog files that can be instantiated by a peripheral following the Comportability Guidelines. | Description of tool output; nothing to verify in RTL. |
| RG-T1.3-02 | The tool can be invoked from the top project directory to generate the uart registers. | Usage example of tool invocation; not a verifiable hardware requirement. |
| RG-T1.5-01 | The qs output is typically the same as q except for hwext registers. | Quote is a garbled port table description; the rule about qs vs q is a description, not a verifiable requirement. |
| RG-T1.5.1-04 | A hwaccess of none requests no hardware interface, usable for scratch, DV test or read-only version registers. | Descriptive usage guidance; nothing to verify. |
| RG-T1.5.2-01 | No de input is required from hardware; only d is added to the struct bundle. | Descriptive note about generated struct; not verifiable behaviour. |
| RG-T1.5.3-01 | RO registers behave as RW registers with no wd and we inputs. | Conceptual statement ('can be thought of'), not a requirement. |
| RG-T1.5.4-02 | RC registers are not recommended, except for backwards compatibility with other IP. | Design advice with nothing to verify. |
| RG-T1.5.4-03 | hwext must not be true for RC registers since re is not exported. | Tool restriction on configuration, not verifiable hardware behaviour. |
| RG-T1.5.5-01 | hwext should be set to true so outside hardware handles the write event. | Design guidance for configuration; nothing to verify. |
| RG-T1.5.6-01 | These register types must be implemented with special prim_subreg configuration because writing sets values in unique ways. | Implementation description of prim_subreg configuration; not a behaviour to check. |
| RG-T1.5.6.1-03 | The hardware value is sent to the logic that potentially clears that value or the stored value. | Internal description of data flow, vague and not observable. |
| AH-T1.3.1-01 | Alerts must be handled by the main processor or escalated to other hardware modules to take action. | Definition/description of alerts; no testable requirement on a specific interface behavior. |
| AH-T1.3.2-05 | The alert sender and receiver modules may be used either synchronously or asynchronously. | Describes configurability/usage options; nothing to verify as a requirement. |
| AH-T1.3.2-06 | The signaling protocol remains the same; the additional synchronizer flops at the diff pair inputs may be omitted, giving lower latency. | Descriptive statement about optional synchronizer removal and latency; nothing to check. |
