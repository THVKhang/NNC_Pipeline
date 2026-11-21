# Specification gaps: ot_rv_timer

Agent A18 read only the specification and listed what it leaves open or states inconsistently ({'high': 9, 'medium': 8, 'low': 3}; 0 without a valid line reference). Nothing was changed: answer each question or amend the specification before approving gate G1.

## GAP-001 [high] contradiction

**Scenario.** Timer active, mtime >= mtimecmp and stays so. Software writes 1 to INTR_STATE0.IS_0 (0x104) without changing COMPARE_*. Two cycles later the test reads INTR_STATE0 and samples o_intr_timer_expired.

**The specification says.** Programmer's guide: "Clearing the interrupt can be done by writing 1 into the Interrupt Status register INTR_STATE0." The block description says the timer "generates an interrupt if the counter reaches (or is above) a programmed value" and the interrupt is Event type. Comportability: "if the event itself is still active, the INTR_STATE register will return to true." Register tool: "Since d is still 1 the q will return to 1 after one cycle".

**Left open.** The spec does not say whether the 'event' is the level mtime>=mtimecmp, which sets IS again every cycle so a W1C alone never clears it, or only the crossing edge, which a W1C clears for good. It says W1C clears the interrupt, but under the level reading it does not.

**Question.** Is the event that sets INTR_STATE0.IS_0 the level (mtime >= mtimecmp) or the transition into that condition? After a W1C while the condition still holds, does IS_0 read 0 or 1, and does o_intr_timer_expired drop?

**Readings.**
- Level event: IS_0 is set again one cycle after the W1C. W1C alone cannot clear the interrupt while mtime >= mtimecmp; at most there is a one-cycle dip.
- Edge event: IS_0 stays 0 after the W1C until mtime crosses mtimecmp again, which needs a new compare value or an mtime write.

References: spec/rv_timer_Design_Specification.md:31, spec/rv_timer_Design_Specification.md:271, spec/rv_timer_Design_Specification.md:273, spec/rv_timer_Design_Specification.md:497, spec/standards/opentitan_comportability.md:637, spec/standards/opentitan_register_tool.md:909-910 (6/6 checked)

## GAP-002 [high] contradiction

**Scenario.** IS_0 = 1 with mtime >= mtimecmp. Software writes COMPARE_UPPER0_0 (0x11c) with (a) a value that makes mtimecmp > mtime, (b) a value that keeps mtimecmp <= mtime, or (c) the same value it already holds.

**The specification says.** "The RV_TIMER module also follows RISC-V Privileged spec that requires the interrupt to be cleared by updating mtimecmp ... both COMPARE_LOWER0_0 and COMPARE_UPPER0_0 can clear the interrupt source." "mtimecmp shall be written after mtime in order to clear any pending interrupt condition." Scope: "clearing by writing the compare registers". Comportability: "The hardware does not have the ability to clear the latched interrupt state, only software does."

**Left open.** The spec does not say whether a compare write clears the latched INTR_STATE bit itself or only removes the source condition. If the bit is cleared, it does not say whether that happens on any write or only when the new value makes mtime < mtimecmp. It also leaves case (b) open: does IS_0 drop and then set again, or stay 1? Finally, which takes precedence when a tick in the same cycle sets the condition?

**Question.** Exactly what does a write to COMPARE_LOWER0_0 or COMPARE_UPPER0_0 do to INTR_STATE0.IS_0 in cases (a), (b) and (c)? In which cycle does it take effect, and what wins when an expiry occurs in the same cycle?

**Readings.**
- Any write to either compare register clears IS_0 unconditionally. If the condition still holds, IS_0 is set again in the next cycle.
- A compare write only changes the comparator input. IS_0 stays latched until a W1C; 'clear the interrupt source' means only the condition.
- A compare write clears IS_0 only when the new 64-bit compare value is greater than mtime.

References: spec/rv_timer_Design_Specification.md:236-237, spec/rv_timer_Design_Specification.md:274-275, spec/rv_timer_Design_Specification.md:640, spec/standards/opentitan_comportability.md:638 (4/4 checked)

## GAP-003 [high] other

**Scenario.** CTRL.active_0 = 0. Software writes TIMER_V = 0x10 and COMPARE = 0x5, so mtime >= mtimecmp while the timer is stopped. The test checks INTR_STATE0 and o_intr_timer_expired.

**The specification says.** CTRL.active_0: "If 1, timer operates". "If mtime is greater than or equal to mtimecmp, the timer raises an interrupt."

**Left open.** The spec does not say whether 'operates' covers only the tick/increment or also the comparator and interrupt generation.

**Question.** Is the expiry comparison (and the setting of INTR_STATE0) gated by CTRL.active_0?

**Readings.**
- The comparator is always live, so the interrupt is raised even with active_0 = 0.
- The interrupt is only raised while active_0 = 1; with active_0 = 0 only mtime is frozen and no expiry is reported.

References: spec/rv_timer_Design_Specification.md:334, spec/rv_timer_Design_Specification.md:56-57, spec/rv_timer_Design_Specification.md:271 (3/3 checked)

## GAP-004 [high] reset_during_operation

**Scenario.** prescale = 9, active_0 = 1. Software writes CTRL.active_0 = 0 when the internal prescaler count is 6, waits, then writes active_0 = 1. The test predicts the cycle of the first mtime increment after re-activation, and also after the very first activation following reset.

**The specification says.** "A tick generator creates a tick every time its internal counter hits the CFG0.prescaler value." A prescaler of 47 at 48MHz gives a 1us tick. Software "should de-activate the timer and then proceed" before changing prescaler/step.

**Left open.** The spec does not say whether de-activation resets the prescaler's internal counter or freezes it. It also does not give the latency from the CTRL write to the first tick: prescale+1 cycles after the write, prescale cycles, or an extra register stage.

**Question.** What does the tick counter do while active_0 = 0, and how many clk_i cycles after the CTRL write that sets active_0 = 1 does mtime first change?

**Readings.**
- The counter is cleared while inactive. The first tick comes prescale+1 cycles after activation (counting from the cycle the CTRL value takes effect).
- The counter holds its value while inactive. The first tick comes after the remaining (prescale - count + 1) cycles.
- The tick fires on the first active cycle (counter starts at a terminal value), then every prescale+1 cycles.

References: spec/rv_timer_Design_Specification.md:54-55, spec/rv_timer_Design_Specification.md:70-71, spec/rv_timer_Design_Specification.md:174-177, spec/rv_timer_Design_Specification.md:334 (4/4 checked)

## GAP-008 [high] simultaneous_events

**Scenario.** After reset (ALERT_TEST.regwen = 1), software writes ALERT_TEST = 0x0000_0001: fatal_fault = 1 and, implicitly, regwen bit 31 = 0. It then writes ALERT_TEST = 0x8000_0001.

**The specification says.** ALERT_TEST bit 31 regwen is rw0c, reset 1: "Write 0 to disable alert testing until the next reset." Bit 0 fatal_fault is wo: "Write 1 to trigger one alert event of this kind." Reset default is 0x80000000.

**Left open.** Any full-word write with bit 31 = 0 clears regwen. The spec does not say whether the same write's fatal_fault = 1 is gated by the old regwen value (the alert fires and then locks) or the new one (no alert). It also does not say whether writes ignored because regwen = 0 return d_error.

**Question.** Does a single write of 0x0000_0001 to ALERT_TEST produce an alert and lock testing, or lock without an alert? Is a later write of 1 to fatal_fault with regwen = 0 silently ignored with a normal AccessAck?

**Readings.**
- regwen is sampled before the write: 0x1 triggers one alert, then regwen = 0 and later tests are blocked.
- The write takes effect atomically with the new regwen: 0x1 clears regwen and the alert is suppressed. Software must write 0x8000_0001 to test.
- Writes blocked by regwen = 0 return d_error = 1 rather than being silently ignored.

References: spec/rv_timer_Design_Specification.md:301-317, spec/rv_timer_Design_Specification.md:625-627, spec/rv_timer_Design_Specification.md:640-641, spec/standards/opentitan_register_tool.md:172 (4/4 checked)

## GAP-010 [high] error_and_recovery

**Scenario.** The test bench issues a PutFullData to CTRL with i_a_intg_flip = 1 (command integrity error), keeps i_d_ready = 1, then sends normal reads and writes.

**The specification says.** "The request then has a command integrity error: a fatal TL-UL bus integrity fault ... which triggers the fatal_fault alert ... These documents do not specify the D-channel response to such a request." Scope: "bus error responses (... integrity errors)".

**Left open.** The spec gives no D-channel response for this request. It also does not say whether the write commits, whether a response arrives at all (the test may hang waiting), or whether later legal requests are served normally or also fail. Yet the verification scope lists integrity errors among bus error responses.

**Question.** For a request with a command integrity error: is a D-channel response returned, and with d_error = 1? Is the write suppressed? Does the device respond normally to later requests before reset?

**Readings.**
- The request is answered with d_error = 1, the write is dropped, and later requests behave normally (only the alert persists).
- The response and register side effects are unspecified. The test only checks o_alert and must not wait for or check the response.
- Every request after the fault is answered with an error until reset.

References: spec/rv_timer_Design_Specification.md:604-607, spec/rv_timer_Design_Specification.md:625-626, spec/rv_timer_Design_Specification.md:641-642 (3/3 checked)

## GAP-011 [high] other

**Scenario.** The host sends Get/PutFullData with i_a_instr = 1 (instruction fetch) to a mapped register such as TIMER_V_LOWER0.

**The specification says.** Scope: "bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors)". TL-UL: instr_type "is used by downstream consumers to provide separate privilege control". INT-CFG-002: RACL disabled, "no access is rejected for an access-control reason".

**Left open.** No normative text says that rv_timer rejects instruction fetches. RACL is disabled, and the TL-UL explicit error list does not mention instr_type. The spec also does not say whether a write with instr_type = True errors, or whether an erroring write still takes effect.

**Question.** Which requests with instr_type = MuBi4True get d_error = 1 (reads, writes, both)? Is register state and read data unaffected?

**Readings.**
- All instruction-type accesses get d_error = 1, writes have no effect, and reads return no register data.
- Only reads (fetches) with instr_type = True error. Writes with instr_type = True are accepted.
- No error: instr_type is ignored because RACL is disabled.

References: spec/rv_timer_Design_Specification.md:535-536, spec/rv_timer_Design_Specification.md:567, spec/rv_timer_Design_Specification.md:641, spec/standards/opentitan_tlul_bus_specification.md:296-299, spec/standards/opentitan_tlul_bus_specification.md:357-367 (5/5 checked)

## GAP-012 [high] parameter_extremes

**Scenario.** The host reads or writes addresses 0x200, 0x204, 0x1000_0004 and 0xFFFF_FF0C, i.e. a mapped offset plus bits above the decoded range.

**The specification says.** i_a_address is a 32-bit "byte address; the register offsets ... are relative to 0". The register tool says "excess address bits are stripped off during address decoding ... If the resulting address is mapped, the request is forwarded to the corresponding register and no error is returned." Scope: "bus error responses (unmapped addresses ...)".

**Left open.** The spec does not give the number of address bits rv_timer decodes. So the test cannot know whether 0x200 aliases ALERT_TEST (no error, side effect) or counts as unmapped (d_error). TL-UL lists "Accesses to non-existent addresses" as an error case.

**Question.** How many address bits does the device decode? Are addresses at or above that range aliases of the registers, or unmapped addresses that return d_error?

**Readings.**
- Only the low address bits (e.g. 9, covering 0x0-0x1FF) are decoded. Higher addresses alias, with no error and the register side effect.
- The full 32-bit address is decoded. Anything other than the ten listed offsets returns d_error = 1.

References: spec/rv_timer_Design_Specification.md:288-299, spec/rv_timer_Design_Specification.md:564, spec/rv_timer_Design_Specification.md:641, spec/standards/opentitan_register_tool.md:673-684, spec/standards/opentitan_tlul_bus_specification.md:367 (5/5 checked)

## GAP-013 [high] contradiction

**Scenario.** The host writes CTRL (0x4), INTR_ENABLE0, INTR_STATE0 or INTR_TEST0 with PutPartialData, a_size = 0, a_mask = 0001 (a byte write that covers every field of the register). The same is done for CFG0 with a_mask = 0011 and for ALERT_TEST with mask 0001.

**The specification says.** Scope lists "sub-word writes" among bus error responses. The register tool returns errors for "writes of size smaller than register size" where "The width of the register is determined by the location of its fields", e.g. "an 8b write to a register which is larger than 8 bits". TL-UL: devices "have the right to assert d_error" for subword masks.

**Left open.** CTRL and the INTR_* registers are 1 bit wide, so by the register-tool rule a byte write to byte 0 is legal and not an error. The scope sentence suggests all sub-word writes error. The spec also does not say whether the rule checks a_size or a_mask, e.g. a_size = 2 with a_mask = 0001.

**Question.** For each register, which partial writes (by a_size and a_mask) return d_error? Does a byte write that covers all of a register's fields succeed and update it?

**Readings.**
- Error only if the enabled byte lanes do not cover all bytes that hold fields of the register: byte writes to CTRL and INTR_* succeed, while byte writes to CFG0, TIMER_V and COMPARE error.
- Any write with a_size < 2 or a_mask != 1111 returns d_error, and the register is unchanged.

References: spec/rv_timer_Design_Specification.md:323-334, spec/rv_timer_Design_Specification.md:641, spec/standards/opentitan_register_tool.md:689-695, spec/standards/opentitan_tlul_bus_specification.md:338-340 (4/4 checked)

## GAP-005 [medium] request_while_busy

**Scenario.** active_0 = 1, prescale = 100, and the internal counter has reached 60. Software writes CFG0.prescale = 20 (or changes step) without de-activating first.

**The specification says.** The tick fires when the internal counter "hits the CFG0.prescaler value". "These two fields need to be stable to correctly increment the timer value. If software wants to change these fields, it should de-activate the timer and then proceed."

**Left open.** Changing CFG0 while running is legal bus stimulus, but the result is not defined. 'Hits' can be read as an equality or a >= comparison. With equality, the counter runs past the new value up to 4095 and wraps, so no tick comes for about 4000 cycles.

**Question.** What is the defined behaviour when CFG0.prescale or CFG0.step is written while active_0 = 1? Is the tick condition count == prescale or count >= prescale, and is the new step applied from the next tick?

**Readings.**
- Tick when count >= prescale: a smaller new prescaler causes a tick on the next cycle, then the new period.
- Tick when count == prescale: the counter runs on to 4095, wraps, and only then ticks at the new value.
- Behaviour is undefined (software restriction). The test must not change CFG0 while active, and the scoreboard must not check it.

References: spec/rv_timer_Design_Specification.md:54-55, spec/rv_timer_Design_Specification.md:174-177, spec/rv_timer_Design_Specification.md:404 (3/3 checked)

## GAP-006 [medium] simultaneous_events

**Scenario.** active_0 = 1, prescale = 0 (a tick every cycle), TIMER_V_LOWER0 = 0xFFFF_FFFF. In the cycle where the tick carries into the upper half, software writes TIMER_V_LOWER0 = 0x1234. The test then reads TIMER_V_UPPER0 and TIMER_V_LOWER0.

**The specification says.** The programmer's guide recommends a write sequence for mtime because the timer can increment between the two writes. The timer value registers are hrw. Register tool: "If both software and hardware request an update in the same clock cycle ... the software updated value is used".

**Left open.** The spec does not say how one 64-bit hardware increment interacts with a software write to a single 32-bit half in the same cycle. Possible outcomes: lower takes the software value and upper still gets the carry; the whole tick is dropped; or the increment is applied on top of the written value. It also does not say whether a tick in that cycle is lost or delayed.

**Question.** When a tick and a software write to TIMER_V_LOWER0 or TIMER_V_UPPER0 occur in the same cycle, what are the two halves afterwards?

**Readings.**
- Per field, software wins: lower = written value and upper = old upper + carry; the tick's lower result is lost.
- Software wins for the whole 64-bit value: upper keeps its old value, lower = written value, and the tick is lost.
- The tick is applied after the write: lower = written value + step.

References: spec/rv_timer_Design_Specification.md:156-162, spec/rv_timer_Design_Specification.md:219-234, spec/rv_timer_Design_Specification.md:638-639, spec/standards/opentitan_register_tool.md:817 (4/4 checked)

## GAP-007 [medium] other

**Scenario.** An expiry occurs (mtime becomes >= mtimecmp) in cycle N, or software writes INTR_TEST0.T_0 = 1 or INTR_ENABLE0 = 1 in cycle N. The test checks in which cycle INTR_STATE0 reads 1 and in which cycle o_intr_timer_expired rises.

**The specification says.** o_intr_timer_expired is "the interrupt output intr_timer_expired_hart0_timer0_o of rv_timer, an event-type interrupt". Comportability waveform: "Event-Type Interrupt Latching and Clearing (output flop enabled)", with INTR_STATE one cycle after hw_i and intr_o one cycle after INTR_STATE.

**Left open.** The output flop is shown as an option. The spec does not say whether rv_timer has it, nor the latency from the tick to the mtime update to the state bit.

**Question.** What are the cycle latencies from an mtime/compare update (or a write to INTR_TEST0 or INTR_ENABLE0) to INTR_STATE0.IS_0, and from there to o_intr_timer_expired? Is the output flop present?

**Readings.**
- Output flop present: o_intr_timer_expired rises one cycle after IS_0 is set.
- No output flop: o_intr_timer_expired = IS_0 & IE_0 combinationally, in the same cycle as the state bit.

References: spec/rv_timer_Design_Specification.md:631-633, spec/standards/opentitan_comportability.md:563-577, spec/standards/opentitan_comportability.md:634 (3/3 checked)

## GAP-009 [medium] request_while_busy

**Scenario.** Software writes ALERT_TEST.fatal_fault = 1 twice back to back (two bus writes a few cycles apart), while the first differential handshake (4 phases plus 2 pause cycles) is still in progress. In a second case, a test write arrives after a bus integrity fault has already started the repeated fatal alert.

**The specification says.** "A write of 1 to ALERT_TEST.fatal_fault triggers one alert event". o_alert "is 1 for one clock cycle for each alert handshake that the receiver detects". "The sender will wait for 2 cycles between handshakes."

**Left open.** The spec does not say whether a test request that arrives while a handshake is in progress is queued (two o_alert pulses), merged into the ongoing one (one pulse), or dropped. With a fatal alert already active, it does not say whether a test write adds anything.

**Question.** How many o_alert pulses must the test expect for N ALERT_TEST writes issued closer together than one handshake period?

**Readings.**
- Requests merge: one pulse per handshake, however many test writes arrived during it.
- Each write is remembered: N pulses.

References: spec/rv_timer_Design_Specification.md:617-620, spec/rv_timer_Design_Specification.md:625-627, spec/standards/opentitan_alert_handler_theory_of_operation.md:170-171 (3/3 checked)

## GAP-014 [medium] contradiction

**Scenario.** A register-access test enumerates the access types to check and builds its expected access-type map from the spec.

**The specification says.** The register table gives INTR_STATE0.IS_0 as "rw1c". The example configuration shows INTR_STATE0 with "swaccess: \"ro\"". Scope: "the access type of every register field (rw, ro, wo, rw0c)". Comportability: INTR_STATE "may be RO or W1C depending on IntrT".

**Left open.** The scope list names 'ro', which no field in the register table has, and leaves out 'rw1c', which IS_0 has. The example hjson gives a different access type for the same register.

**Question.** Is INTR_STATE0.IS_0 rw1c (as in the register table) or ro (as in the example hjson)? Should the verification scope list read (rw, rw1c, wo, rw0c)?

**Readings.**
- IS_0 is rw1c. 'ro' in the scope is a typo for 'rw1c'.
- IS_0 is ro (Status-like) and is cleared only by compare writes. The register table is wrong.

References: spec/rv_timer_Design_Specification.md:132-143, spec/rv_timer_Design_Specification.md:362-368, spec/rv_timer_Design_Specification.md:637-638, spec/standards/opentitan_comportability.md:519 (4/4 checked)

## GAP-015 [medium] back_pressure

**Scenario.** The host sends a read, holds i_d_ready = 0 for 20 cycles while keeping i_a_valid = 1 with a second request, then releases i_d_ready.

**The specification says.** TL-UL lists "Support for multiple outstanding requests". INT-TL-003: the test bench follows the host rules. No statement on device acceptance while a response is pending.

**Left open.** The spec does not say how many requests the device can have outstanding, whether o_a_ready drops while o_d_valid is stalled, or whether the timer state seen by a read is sampled at acceptance or at response time.

**Question.** While a D-channel response is held by i_d_ready = 0, does the device deassert o_a_ready? How many requests can be outstanding? Is the TIMER_V read value taken in the cycle the request is accepted?

**Readings.**
- Only one outstanding request: o_a_ready = 0 until the pending response is accepted, and read data is captured at acceptance.
- The device keeps accepting requests (buffered), so o_a_ready can stay 1 during D-channel back-pressure.

References: spec/standards/opentitan_tlul_bus_specification.md:15, spec/rv_timer_Design_Specification.md:592-595 (2/2 checked)

## GAP-016 [medium] error_and_recovery

**Scenario.** The host reads an unmapped address (e.g. 0x8) or sends an undefined opcode (e.g. 3'b010), and the scoreboard checks o_d_opcode, o_d_data, o_d_size, o_d_param and o_d_sink of the error response.

**The specification says.** Errors are signalled "with the d_error bit" on "either" response opcode. Devices "must simply return the associated a_source". d_param is "unused". Nothing on d_data or d_opcode for error/undefined-opcode responses.

**Left open.** For error responses the spec does not give d_data (0, all ones, or don't care), the d_opcode for an undefined a_opcode, or whether d_size echoes a_size. For write responses it does not give the value of d_data.

**Question.** What are d_opcode, d_data, d_size, d_param and d_sink in an error response (read error, write error, undefined opcode)? Is d_data defined for AccessAck?

**Readings.**
- Error reads return AccessAckData with d_data = all ones. Undefined opcodes get AccessAck. d_size echoes a_size and d_param = d_sink = 0.
- Only d_error, d_source and d_opcode are checked; the other fields are don't care.

References: spec/standards/opentitan_tlul_bus_specification.md:319-353, spec/standards/opentitan_tlul_bus_specification.md:261-264, spec/rv_timer_Design_Specification.md:571-576 (3/3 checked)

## GAP-018 [medium] reset_during_operation

**Scenario.** rst_ni is asserted asynchronously (a) while a TL-UL request is accepted but its response is not yet sent or not yet accepted, and (b) in the middle of an alert handshake. The host also drives i_a_valid = 1 during reset or in the first cycle after release.

**The specification says.** "While rst_ni is 0, every register holds its reset value". TL-UL: devices "can tolerate shorter reset windows" (the 100-cycle valid-low rule is waived). INT-ALERT-003: o_alert pulses "until rst_ni is asserted".

**Left open.** The spec defines register values during reset but not the output ports. It does not give o_a_ready, o_d_valid, o_alert or o_intr_timer_expired during and right after reset. It does not say whether an in-flight response is dropped, or whether a request presented during reset may be accepted. It also leaves the output values before the first reset undefined.

**Question.** What values must o_a_ready, o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired have while rst_ni = 0 and in the first cycle after release? Is a pending response discarded? May the host assert a_valid during reset?

**Readings.**
- All outputs are 0 during reset, pending responses are discarded, and the host must keep a_valid = 0 until reset is released.
- o_a_ready may be 1 during reset; only register values are guaranteed. The host may present a request in the release cycle and expect it to be accepted.

References: spec/rv_timer_Design_Specification.md:545-550, spec/rv_timer_Design_Specification.md:625-626, spec/standards/opentitan_tlul_bus_specification.md:131-139 (3/3 checked)

## GAP-017 [low] other

**Scenario.** The host sends a valid Get or PutFullData with i_a_param = 3'b101.

**The specification says.** TL-UL: a_param is "unused". The explicit error list covers opcode, addr/size/mask, alignment and non-existent addresses. Further, "devices ... may implement additional more restrictive checks".

**Left open.** The spec does not say whether a non-zero a_param is ignored or returns d_error.

**Question.** Is a request with a non-zero a_param processed normally or answered with d_error?

**Readings.**
- a_param is ignored, so the access completes normally.
- A non-zero a_param is a protocol violation and gets d_error = 1 with no side effect.

References: spec/rv_timer_Design_Specification.md:561, spec/standards/opentitan_tlul_bus_specification.md:86, spec/standards/opentitan_tlul_bus_specification.md:357-373 (3/3 checked)

## GAP-019 [low] initial_state

**Scenario.** A reset-value test reads INTR_TEST0 (0x108) and the wo bit 0 of ALERT_TEST after reset and compares them with the register table.

**The specification says.** The INTR_TEST0.T_0 reset value is "x". The register reset default is 0x0 with mask 0x1. The register tool: WO registers have "no output back to the software read response mux". Scope: "reset values of every register".

**Left open.** An 'x' reset next to a 0x0 register reset default leaves the read value of wo fields unclear: always 0, or don't care.

**Question.** Does a read of INTR_TEST0 and of ALERT_TEST bit 0 always return 0, and should the reset test check it?

**Readings.**
- wo fields always read 0, so INTR_TEST0 reads 0x0 and ALERT_TEST reads 0x8000_0000 after reset.
- wo read data is unspecified ('x') and excluded from the check.

References: spec/rv_timer_Design_Specification.md:370-385, spec/rv_timer_Design_Specification.md:313-317, spec/rv_timer_Design_Specification.md:637, spec/standards/opentitan_register_tool.md:869 (4/4 checked)

## GAP-020 [low] contradiction

**Scenario.** An engineer builds the a_user field layout from the standards to check what the wrapper drives.

**The specification says.** The TL-UL struct defines tl_a_user_t as {rsvd1[6:0], parity_en, parity[7:0]}. The text names instr_type, cmd_intg and data_intg. INT-TL-002 says "a_user.rsvd is 0. a_user.instr_type is MuBi4True ...". "Bus Integrity Scheme: To be filled in."

**Left open.** The quoted struct does not contain the fields the wrapper text refers to. The integrity encoding is left to code outside the spec.

**Question.** Which a_user/d_user layout applies: the struct in the TL-UL document or the instr_type/cmd_intg/data_intg layout used by the wrapper?

**Readings.**
- The wrapper's layout applies and the struct in the standard is out of date.
- The struct in the standard is normative, so the wrapper text is inconsistent with it.

References: spec/standards/opentitan_tlul_bus_specification.md:170-174, spec/standards/opentitan_tlul_bus_specification.md:382-383, spec/rv_timer_Design_Specification.md:590, spec/rv_timer_Design_Specification.md:599-602 (4/4 checked)

Cost: US$1.03
