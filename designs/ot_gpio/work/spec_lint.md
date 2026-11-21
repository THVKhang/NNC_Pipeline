# Specification gaps: ot_gpio

Agent A18 read only the specification and listed what it leaves open or states inconsistently ({'high': 10, 'medium': 7, 'low': 2}; 0 without a valid line reference). Nothing was changed: answer each question or amend the specification before approving gate G1.

## GAP-001 [high] contradiction

**Scenario.** After reset, DIRECT_OE = 0xff00ff00 (prog guide line 244). Software writes MASKED_OE_LOWER = 0x0f0f0f0f (mask 0x0f0f, data 0x0f0f) and then reads DIRECT_OE and DATA_IN.

**The specification says.** The register description says: "Writing lower 16 bits of the register changes DATA_OE[15:0] value if mask bits are set" (spec/gpio_Design_Specification.md:663-665, also :636-638). Under that rule DATA_OE[15:0] = (0xff00 & ~0x0f0f) | (0x0f0f & 0x0f0f) = 0xff0f. The Programmer's Guide instead shows "*GPIO_MASKED_OE_LOWER = 0x0f0f0f0f; ... // 0x00000f0f; *GPIO_DIRECT_OE // 0xff000f0f; *GPIO_DATA_IN // 0x17fff5f6" (:248-251), and the same for UPPER, giving 0x0f0f0f0f (:253-256). In those results the unmasked OE bits were cleared. The DATA_OUT example just above keeps the unmasked bits (0x3344 -> 0x3546, :232-234).

**Left open.** The DATA_OE example clears the unmasked bits, while the register description and the DATA_OUT example keep them. So the text gives two different masked-write rules for DATA_OE, and with them different expected DATA_OE and DATA_IN values.

**Question.** Is the Programmer's Guide DATA_OE example wrong (should it read 0x0000ff0f / 0xff00ff0f / 0x17ff35f6, and so on), or do masked OE writes really differ from masked OUT writes?

**Readings.**
- Masked OE writes keep DATA_OE bits whose mask is 0, as for DATA_OUT; the example values at lines 249-256 are wrong.
- Masked OE writes behave as the example shows, so bits whose mask is 0 end up 0; the register text is wrong.

References: spec/gpio_Design_Specification.md:88-93, spec/gpio_Design_Specification.md:100, spec/gpio_Design_Specification.md:232-234, spec/gpio_Design_Specification.md:244-256, spec/gpio_Design_Specification.md:636-638, spec/gpio_Design_Specification.md:663-665, spec/gpio_Design_Specification.md:654-655 (7/7 checked)

## GAP-002 [high] contradiction

**Scenario.** Software writes MASKED_OE_LOWER = 0xffff0001, then reads MASKED_OE_LOWER. The same is done with MASKED_OUT_LOWER.

**The specification says.** Theory text: "Reads of masked registers return the lower/upper 16 bits of the DATA_OUT contents. Zeros are returned in the upper 16 bits (mask field)." (:95-96). Register text: "Read-back of this register returns upper 16 bits as zero" (:640, :667). However the field tables give MASKED_OE_* mask as type "rw" (:649, :654, :676, :681), while MASKED_OUT_* mask is "wo" (:578, :583, :604, :609).

**Left open.** The field tables say the mask can be read back, but the prose says it reads as zero. A test generated from the field types would expect the mask written last (0xffff) in bits 31:16.

**Question.** What does a read of MASKED_OE_LOWER/UPPER return in bits 31:16: always 0, or the mask written last? Which access type should the register model use?

**Readings.**
- Reads return 0 in bits 31:16, as for MASKED_OUT_*; the 'rw' type is nominal.
- Bits 31:16 are a real rw field and return the mask written last.

References: spec/gpio_Design_Specification.md:95-96, spec/gpio_Design_Specification.md:640, spec/gpio_Design_Specification.md:649, spec/gpio_Design_Specification.md:654, spec/gpio_Design_Specification.md:667, spec/gpio_Design_Specification.md:681, spec/gpio_Design_Specification.md:583, spec/gpio_Design_Specification.md:1128 (8/8 checked)

## GAP-003 [high] initial_state

**Scenario.** rst_ni is held at 0 and then released. Before any write, the test reads DIRECT_OUT, DIRECT_OE, INTR_CTRL_EN_*, CTRL_EN_INPUT_FILTER, MASKED_*, PER_PIN_* and DATA_IN, and checks o_gpio and o_gpio_en.

**The specification says.** Every one of these registers has the header "Reset default: `0x0`", but its field table lists Reset "x". Examples: DATA_IN (:531 vs :542), DIRECT_OUT (:547 vs :558), MASKED_OUT_LOWER (:572 vs :583-584), DIRECT_OE (:618 vs :628), INTR_CTRL_EN_RISING (:690 vs :701), CTRL_EN_INPUT_FILTER (:766 vs :777), PER_PIN_IO (:824 vs :874,:876), PER_PIN_OE_0 (:884 vs :896), PER_PIN_INTR_CTRL_0 (:905 vs :917). INT-RST-001: "every register holds its reset value as given in the register tables" (:1018-1019). INT-VER-001 requires checking the "reset values of every register" (:1128).

**Left open.** For about half the registers, it is not clear whether the reset value is 0 or undefined. o_gpio and o_gpio_en are DATA_OUT and DATA_OE (:1107), so their values during and after reset are also unclear. DATA_IN tracks the pins and cannot simply 'hold' 0 while i_gpio is 1.

**Question.** Is the reset value of each of these registers 0x0 (header) or 'x' (field table)? For DATA_IN, what reads back during reset and in the first cycles after reset when i_gpio is not 0?

**Readings.**
- All of them reset to 0; 'x' in the tables only marks hardware-maintained (hwext) storage. o_gpio and o_gpio_en are 0 during reset.
- The value is undefined and must not be checked. DATA_IN shows the synchronised pins as soon as the synchroniser flops fill.
- DATA_IN is 0 for a fixed number of cycles after reset (the synchroniser/filter flops reset to 0), then follows the pins.

References: spec/gpio_Design_Specification.md:531, spec/gpio_Design_Specification.md:542, spec/gpio_Design_Specification.md:547, spec/gpio_Design_Specification.md:558, spec/gpio_Design_Specification.md:618, spec/gpio_Design_Specification.md:628, spec/gpio_Design_Specification.md:690, spec/gpio_Design_Specification.md:701, spec/gpio_Design_Specification.md:766, spec/gpio_Design_Specification.md:777, spec/gpio_Design_Specification.md:824, spec/gpio_Design_Specification.md:874, spec/gpio_Design_Specification.md:884, spec/gpio_Design_Specification.md:896, spec/gpio_Design_Specification.md:1017-1019, spec/gpio_Design_Specification.md:1107, spec/gpio_Design_Specification.md:1128 (17/17 checked)

## GAP-004 [high] contradiction

**Scenario.** After reset, software sets INTR_CTRL_EN_RISING[3] = 1 and leaves INTR_ENABLE[3] = 0. The test bench then drives i_gpio[3] from 0 to 1, and software reads INTR_STATE.

**The specification says.** Theory: "the 32 bits of the INTR_ENABLE register determines whether the associated inputs are configured to detect interrupt events. If enabled via the various INTR_CTRL_EN registers, their current state can be read in the INTR_STATE register" (:165-168). INTR_CTRL_EN_*: "If INTR_ENABLE[i] is true, a value of 1 on INTR_CTRL_EN_RISING[i] enables rising-edge interrupt detection" (:687-688, :706-707, :725-726, :744-745). INTR_ENABLE field: "Enable interrupt when corresponding bit in INTR_STATE.gpio is set" (:492). Comportability: "The contents of the INTR_STATE register are not qualified by INTR_ENABLE, but rather show the raw state of all latched hardware interrupt events" (standards/opentitan_comportability.md:523), and INTR_ENABLE only masks the output (:520, :634).

**Left open.** The gpio text makes INTR_ENABLE a condition for detection, so INTR_STATE[3] would stay 0. The comportability text makes INTR_ENABLE only mask o_intr_gpio, so INTR_STATE[3] would become 1. Likewise, setting INTR_ENABLE later may or may not raise the interrupt for an edge that is already latched.

**Question.** Does INTR_ENABLE[i] = 0 stop INTR_STATE[i] from being set by a configured edge or level, or does it only mask o_intr_gpio[i]?

**Readings.**
- INTR_ENABLE only masks the output; INTR_STATE latches events whatever INTR_ENABLE says (comportability).
- INTR_ENABLE gates detection; with INTR_ENABLE[i] = 0, INTR_STATE[i] never sets from hardware (gpio theory/register text).

References: spec/gpio_Design_Specification.md:165-168, spec/gpio_Design_Specification.md:492, spec/gpio_Design_Specification.md:687-688, spec/gpio_Design_Specification.md:706-707, spec/standards/opentitan_comportability.md:520, spec/standards/opentitan_comportability.md:523, spec/standards/opentitan_comportability.md:634, spec/gpio_Design_Specification.md:1116-1118 (8/8 checked)

## GAP-007 [high] request_while_busy

**Scenario.** CTRL_EN_INPUT_FILTER[5] = 1. The test bench drives i_gpio[5] from 0 to 1, holds it for exactly 15 or 16 clk_i cycles, then returns it to 0. Separately, software sets or clears CTRL_EN_INPUT_FILTER[5] while i_gpio[5] = 1 has been stable for a long time.

**The specification says.** "This requires the input to be stable for 16 cycles of the module clock before the input register reflects the change and interrupt generation is evaluated" (:55-57); "a value of input bit [i] must be stable for 16 cycles before transitioning" (:763-764); "This 16-cycle filter is applied to both the DATA_IN register and the interrupt detection logic" (:141).

**Left open.** (a) The exact threshold is not given: does a pulse of 16 stable cycles pass and 15 not, or does the change appear on the 16th or the 17th cycle? Is the count taken after the synchroniser? (b) What the filter holds when it is switched on or off is not given. If the filter state was not tracking while disabled (for example it reset to 0), enabling it while the pin is 1 could make DATA_IN drop to 0 and come back, giving false falling/rising interrupt events. Disabling it could make DATA_IN jump at once.

**Question.** What is the exact number of stable cycles (counted at which point) before a filtered change appears in DATA_IN? Does the filter keep tracking the input while disabled, so that switching CTRL_EN_INPUT_FILTER on or off never creates an edge event?

**Readings.**
- A change appears after it has been stable for 16 cycles at the synchroniser output; the filter always tracks, so switching it causes no false edges.
- A change appears on the 17th cycle (16 equal samples plus 1 register stage), and switching the filter can create edges if the filtered and raw values differ.

References: spec/gpio_Design_Specification.md:54-57, spec/gpio_Design_Specification.md:139-141, spec/gpio_Design_Specification.md:181, spec/gpio_Design_Specification.md:763-764 (4/4 checked)

## GAP-008 [high] contradiction

**Scenario.** GpioAsHwStrapsEn = 1. rst_ni is released while i_strap_en is already 1; in another test, i_strap_en rises in cycle N after reset. In both, i_gpio changes between cycle N and N+1, and CTRL_EN_INPUT_FILTER has already been set by software.

**The specification says.** Theory: "on the first cycle when the strap_en_i signal is asserted, the GPIO detects its transition from low to high. One clock cycle later, it samples the GPIO input values" (:152-153), and "The strap_en_i signal transition from low to high is expected only once after the reset process" (:154). Register: "GPIO input data is sampled after reset on the first cycle where the strap_en_i input is high" (:802-803). Parameter: "at initial cold boot" (:1003). Theory also says "After each reset" (:152).

**Left open.** (a) Which cycle is sampled, N or N+1? (b) Is a level that is already high at reset release a trigger, or is a 0->1 transition required? (c) Which value is sampled: raw i_gpio, the synchronised input, or the filtered DATA_IN? (d) Does a warm rst_ni re-arm sampling, or does it happen only at cold boot? (e) When do o_straps_valid and HW_STRAPS_DATA_IN_VALID become 1 relative to the trigger?

**Question.** In exactly which cycle are the straps sampled, from which signal (raw, synchronised or filtered), and when does VALID rise? Does strap_en_i = 1 at reset release trigger sampling, and does every rst_ni re-arm it?

**Readings.**
- Sampled in the cycle where strap_en_i is first seen high (register text); a level high at reset counts; VALID one cycle later.
- Sampled one cycle after a detected 0->1 transition (theory text); a level already high at reset release never triggers.
- The value sampled is the filtered DATA_IN, versus the unfiltered synchronised input.

References: spec/gpio_Design_Specification.md:151-156, spec/gpio_Design_Specification.md:797-804, spec/gpio_Design_Specification.md:947, spec/gpio_Design_Specification.md:1003, spec/gpio_Design_Specification.md:1122-1123, spec/gpio_Design_Specification.md:1131 (6/6 checked)

## GAP-010 [high] contradiction

**Scenario.** Software writes ALERT_TEST = 0x00000001, meaning to fire one test alert. Bit 31 of that write is 0. Software then writes 0x00000001 again and watches o_alert.

**The specification says.** The ALERT_TEST register has "regwen | rw0c | 0x1 | Write 0 to disable alert testing until the next reset" at bit 31 and fatal_fault (wo) at bit 0, reset 0x80000000 (:513-526). INT-ALERT-003: "A write of 1 to ALERT_TEST.fatal_fault triggers one alert event" (:1101-1102). Comportability: "ALERT_TEST is a write-only (wo) register" with one bit per alert (standards/opentitan_comportability.md:702-703). It also says the fatal sender "latch[es] the alert until the next system reset" (:708).

**Left open.** (a) A write of 0x1 also writes 0 to regwen. Does the alert fire on that write (does regwen gate the same write or only later ones)? Does the second write fire? (b) Does reading ALERT_TEST return 0x80000000 (regwen readable) or 0 (wo register)? (c) For a fatal alert, does the test produce one handshake (INT-ALERT-003) or repeat until reset (latched fatal sender)?

**Question.** How do ALERT_TEST.regwen and fatal_fault interact within one write and across later writes, what does an ALERT_TEST read return, and how many o_alert pulses does one test write give?

**Readings.**
- The first write of 0x1 fires one alert and clears regwen, so later test writes are ignored; reads return bit 31.
- regwen is sampled before the write: both 0x1 writes fire, and regwen only blocks from the following write on.
- The test alert of a fatal alert repeats until reset, as for a real fault.

References: spec/gpio_Design_Specification.md:510-526, spec/gpio_Design_Specification.md:1100-1102, spec/standards/opentitan_comportability.md:702-703, spec/standards/opentitan_comportability.md:708 (4/4 checked)

## GAP-011 [high] error_and_recovery

**Scenario.** The test bench issues a Get to DATA_IN (0x10) with i_a_instr = 1, and a PutFullData to DIRECT_OUT with i_a_instr = 1.

**The specification says.** The wrapper maps i_a_instr to a_user.instr_type = MuBi4True (:1036, :1065). INT-VER-001 lists "instruction fetches" among the "bus error responses" to be verified (:1132). The TL-UL spec only says instr_type "is used by downstream consumers to provide separate privilege control" (standards/opentitan_tlul_bus_specification.md:297-299). No text says the gpio rejects instruction fetches.

**Left open.** No text states which instruction-type requests get d_error = 1 (reads only, or writes too), whether a write with instr_type = True still updates the register, or what d_data an erroring read returns.

**Question.** Is every request with instr_type = MuBi4True answered with d_error = 1 and no side effect? Does this apply to writes as well as reads?

**Readings.**
- All instruction-type requests error, and writes have no effect.
- Only instruction-type reads (Get) error; writes are handled normally.
- No error at all, since only RACL (disabled) would apply privilege control.

References: spec/gpio_Design_Specification.md:1036, spec/gpio_Design_Specification.md:1065, spec/gpio_Design_Specification.md:1132, spec/standards/opentitan_tlul_bus_specification.md:105, spec/standards/opentitan_tlul_bus_specification.md:297-299 (5/5 checked)

## GAP-012 [high] error_and_recovery

**Scenario.** The test bench issues Get requests to 0x300, 0x400 and 0x1100. 0x1100 differs from PER_PIN_IO_0 (0x100) only above bit 9.

**The specification says.** The register map ends at 0x2fc (:460). i_a_address is a 32-bit byte address relative to 0 (:1033). Register tool: "Since excess address bits are stripped off during address decoding ... If the resulting address is mapped, the request is forwarded to the corresponding register and no error is returned" (standards/opentitan_register_tool.md:676-678). INT-VER-001 requires checking errors for "unmapped addresses" (:1132).

**Left open.** The number of address bits the gpio decodes is not stated. So it is unclear whether 0x400 or 0x1100 alias mapped registers (no error, real access) or return d_error = 1.

**Question.** How many low address bits does ot_gpio_nnc decode? Which addresses above 0x2fc alias registers, and which return d_error?

**Readings.**
- 10 address bits are decoded: 0x300-0x3ff error, and 0x1100 aliases PER_PIN_IO_0 without error.
- All 32 bits are decoded: any address outside the map returns d_error = 1.

References: spec/gpio_Design_Specification.md:345-460, spec/gpio_Design_Specification.md:1033, spec/gpio_Design_Specification.md:1132, spec/standards/opentitan_register_tool.md:673-684 (4/4 checked)

## GAP-013 [high] other

**Scenario.** PutPartialData with a_size = 2, a_address = 0x14 (DIRECT_OUT) and a_mask = 0b0011. Also with a_mask = 0b0001 to PER_PIN_IO_5 (0x114).

**The specification says.** Register tool: errors for "TL-UL writes of size smaller than register size ... The width of the register is determined by the location of its fields" (standards/opentitan_register_tool.md:689-693). The gpio text: "A register write must cover all bytes of the register that hold a field" (:126), and "a write to it must cover both bytes, i.e., be at least 16 bits wide" (:317). The TL-UL spec allows PutPartialData with active lanes given by a_mask (standards/opentitan_tlul_bus_specification.md:345).

**Left open.** It is unclear whether the error check uses a_size or the active a_mask bytes. A full-size (a_size = 2) write with only some mask bits set could either error, or be accepted and update only the enabled bytes (or the whole register).

**Question.** For writes, is 'size smaller than register' judged from a_size or from a_mask? What happens to a 4-byte PutPartialData whose mask does not cover every byte holding a field?

**Readings.**
- Judged by a_mask: d_error = 1 and no update.
- Judged by a_size: accepted, and only the bytes enabled in the mask are written.
- Judged by a_size: accepted, and the whole register is written from a_data.

References: spec/gpio_Design_Specification.md:126, spec/gpio_Design_Specification.md:317-319, spec/standards/opentitan_register_tool.md:689-695, spec/standards/opentitan_tlul_bus_specification.md:345, spec/standards/opentitan_tlul_bus_specification.md:361-364 (5/5 checked)

## GAP-005 [medium] simultaneous_events

**Scenario.** INTR_CTRL_EN_LVLLOW[2] = 1, INTR_ENABLE[2] = 1 and i_gpio[2] is held at 0. In cycle N, software's write of 1 to INTR_STATE[2] takes effect. The test watches o_intr_gpio[2] in cycles N+1 and N+2.

**The specification says.** The interrupt is "an event-type interrupt" (:1116-1117). Example: "try and clear [3:2], fails since still active low" (:277-279). Register tool: "if the event is still true ... the clear should still have effect for one cycle in order to create a new interrupt edge. Since d is still 1 the q will return to 1 after one cycle" (standards/opentitan_register_tool.md:909-910). Comportability: "if the event itself is still active, the INTR_STATE register will return to true" (standards/opentitan_comportability.md:637).

**Left open.** While a level condition is active, it is not stated whether INTR_STATE[2] and o_intr_gpio[2] drop for one cycle after the W1C (a glitch the test could see) or stay high throughout.

**Question.** While the level condition is active, does a W1C to INTR_STATE produce a one-cycle low on INTR_STATE[i] and o_intr_gpio[i], or must both stay high?

**Readings.**
- One-cycle drop and then set again (register tool rule, which produces a new interrupt edge).
- No visible drop: the level condition has priority over the clear in the same cycle.

References: spec/gpio_Design_Specification.md:182-183, spec/gpio_Design_Specification.md:274-279, spec/gpio_Design_Specification.md:1116-1118, spec/standards/opentitan_register_tool.md:906-910, spec/standards/opentitan_comportability.md:637 (5/5 checked)

## GAP-006 [medium] simultaneous_events

**Scenario.** INTR_CTRL_EN_RISING[0] = 1. The filtered or synchronised i_gpio[0] rises in the same clock cycle in which software's W1C of INTR_STATE[0] (clearing an earlier edge) takes effect.

**The specification says.** Register tool RW1C logic: "q <= (de ? d : q) & (we ? ~wd : '1)" and "the software has precedence" (standards/opentitan_register_tool.md:889, :896). Comportability: "The hardware does not have the ability to clear the latched interrupt state, only software does" (standards/opentitan_comportability.md:638). The gpio documents say nothing about this collision.

**Left open.** If software has precedence, the new edge is lost and INTR_STATE[0] stays 0 after the clear. A scoreboard that counts events would instead expect INTR_STATE[0] = 1.

**Question.** When an edge event and a W1C of the same INTR_STATE bit fall in the same cycle, is the new event kept (INTR_STATE = 1) or lost (INTR_STATE = 0)?

**Readings.**
- The clear wins and the event is lost (generic subreg formula).
- The event wins: the hardware set has priority, so no edge is lost.

References: spec/standards/opentitan_register_tool.md:886-904, spec/standards/opentitan_comportability.md:636-638, spec/gpio_Design_Specification.md:168-169 (3/3 checked)

## GAP-009 [medium] parameter_extremes

**Scenario.** GpioAsHwStrapsEn = 0 (a legal value, INT-CFG-004). The test bench pulses i_strap_en after reset, then reads HW_STRAPS_DATA_IN_VALID and checks o_straps_valid and o_straps_data.

**The specification says.** Only HW_STRAPS_DATA_IN is covered: "If the parameter is false then the register reads as zero" (:801). HW_STRAPS_DATA_IN_VALID has no description (:791-794), and the ports are described only as sampled_straps_o fields (:1055-1056, :1122-1123).

**Left open.** When the feature is disabled, it is not stated whether HW_STRAPS_DATA_IN_VALID and o_straps_valid stay 0 or still go to 1 after strap_en, or what o_straps_data carries.

**Question.** With GpioAsHwStrapsEn = 0, what do HW_STRAPS_DATA_IN_VALID, o_straps_valid and o_straps_data show before and after an i_strap_en pulse?

**Readings.**
- All stay 0 permanently.
- VALID still rises after strap_en and only the data reads 0.
- The outputs are unspecified and not checked.

References: spec/gpio_Design_Specification.md:800-801, spec/gpio_Design_Specification.md:791-794, spec/gpio_Design_Specification.md:1003, spec/gpio_Design_Specification.md:1055-1056, spec/gpio_Design_Specification.md:1122-1123 (5/5 checked)

## GAP-014 [medium] error_and_recovery

**Scenario.** In cycle N the test bench sends a PutFullData to DIRECT_OUT = 0xffffffff with i_a_intg_flip = 1. It then sends a correct Get to DIRECT_OUT and a correct write.

**The specification says.** "The request then has a command integrity error: a fatal TL-UL bus integrity fault ... which triggers the fatal_fault alert ... These documents do not specify the D-channel response to such a request." (:1079-1082). "after a bus integrity fault o_alert pulses repeatedly until rst_ni is asserted" (:1100-1101).

**Left open.** The text does not say whether the corrupted write reaches DIRECT_OUT or o_gpio, whether any D-channel response is sent (and with which d_error), or whether later correct requests are served normally while the alert repeats. INT-VER-001 nevertheless requires verifying "integrity errors" as bus error responses (:1132).

**Question.** For a request with a command integrity error, must it have no effect on registers, must it be answered (with d_error = 1), and does the device keep serving later requests normally?

**Readings.**
- Answered with d_error = 1, no register effect, later requests normal; only the alert repeats.
- The response is unspecified and the test checks only the alert and that registers are unchanged.
- The register may be updated; only the alert is guaranteed.

References: spec/gpio_Design_Specification.md:1079-1082, spec/gpio_Design_Specification.md:1100-1101, spec/gpio_Design_Specification.md:1132, spec/gpio_Design_Specification.md:963 (4/4 checked)

## GAP-015 [medium] other

**Scenario.** With GpioAsyncOn = 1 and then 0, the test bench changes i_gpio[0] at a clock edge with INTR_CTRL_EN_RISING[0] = 1 and INTR_ENABLE[0] = 1. It measures the cycles until DATA_IN[0], INTR_STATE[0] and o_intr_gpio[0] change, and the cycles from a DIRECT_OUT write handshake until o_gpio changes.

**The specification says.** "The input synchronizer adds two flops ... though the added delay may vary by up to one GPIO clock cycle" (:144). "With GpioAsyncOn = 0 there is no synchronizer" (:1013-1015). "all outputs change at its rising edge" (:1010-1011). Comportability waveform: INTR_STATE one cycle after the event and intr_o one cycle later ("output flop enabled", standards/opentitan_comportability.md:563-580).

**Left open.** No fixed latencies are given: pin to DATA_IN with GpioAsyncOn = 0 (0 or 1 cycle, combinational or registered), pin to INTR_STATE and o_intr_gpio, write to o_gpio and o_gpio_en, and W1C or INTR_TEST to o_intr_gpio. A cycle-accurate checker and the RTL may disagree.

**Question.** What are the exact latencies, in clk_i cycles, from i_gpio to DATA_IN and INTR_STATE and o_intr_gpio for each GpioAsyncOn value, and from a register write to o_gpio, o_gpio_en and o_intr_gpio? Or must tests allow a stated tolerance?

**Readings.**
- Fixed latencies: 2 sync cycles plus 1 detection cycle plus 1 output flop with GpioAsyncOn = 1; without the 2 with GpioAsyncOn = 0.
- Only ordering and eventual values are specified; tests must allow a window.

References: spec/gpio_Design_Specification.md:142-144, spec/gpio_Design_Specification.md:1010-1015, spec/standards/opentitan_comportability.md:563-580 (3/3 checked)

## GAP-016 [medium] back_pressure

**Scenario.** The test bench holds i_d_ready = 0 while a read response is pending, and keeps i_a_valid = 1 with further requests, including a write to DIRECT_OUT.

**The specification says.** TL-UL lists "Support for multiple outstanding requests" (standards/opentitan_tlul_bus_specification.md:15). INT-TL-003 only requires the host to keep A signals stable (:1067-1068). The gpio spec gives no device outstanding depth or a_ready rule.

**Left open.** Not stated: how many requests the device accepts (a_ready = 1) while its D response is stalled, and whether an accepted write takes effect on o_gpio before its AccessAck is accepted.

**Question.** What is the device's maximum number of outstanding requests? Does a_ready depend on d_ready, and does a write take effect when accepted or when its response is accepted?

**Readings.**
- One outstanding: a_ready = 0 until the pending response is accepted; the write takes effect at A acceptance.
- Several outstanding (a response FIFO); a_ready stays 1 for a few more requests.

References: spec/standards/opentitan_tlul_bus_specification.md:15, spec/gpio_Design_Specification.md:1067-1070 (2/2 checked)

## GAP-017 [medium] reset_during_operation

**Scenario.** rst_ni is asserted asynchronously (a) while a read response is pending with d_ready = 0, (b) while the input filter is counting, and (c) while the fatal alert repeats after an integrity fault. It is then released.

**The specification says.** "rst_ni is the active-low reset, asserted asynchronously and released synchronously ... While rst_ni is 0, every register holds its reset value" (:1017-1019). "o_alert pulses repeatedly until rst_ni is asserted" (:1100-1101).

**Left open.** The behaviour of non-register outputs during and right after reset is not stated: whether o_d_valid drops immediately and the pending response is lost, whether o_alert or o_alert_integ_fail may pulse during or right after reset (the sender and receiver reset together), and whether straps and filter counters restart.

**Question.** What do o_d_valid, o_a_ready, o_alert and o_alert_integ_fail show during reset and in the first cycles after release? Is a response pending at reset discarded?

**Readings.**
- All outputs are 0 during reset, the pending response is lost, and no alert or integrity pulse may appear after release.
- Outputs are unspecified during reset and a few cycles after; checking starts after a settling time.

References: spec/gpio_Design_Specification.md:1017-1019, spec/gpio_Design_Specification.md:1100-1101, spec/gpio_Design_Specification.md:1093-1098 (3/3 checked)

## GAP-018 [low] error_and_recovery

**Scenario.** The test bench writes 0xffffffff to DATA_IN (ro), HW_STRAPS_DATA_IN (ro) and INTR_TEST. It reads INTR_TEST, and reads with a request that gets d_error = 1.

**The specification says.** DATA_IN, HW_STRAPS_DATA_IN and HW_STRAPS_DATA_IN_VALID are "ro" (:542, :794, :817), and INTR_TEST is "wo" (:508). The register-tool error list ("including the following", standards/opentitan_register_tool.md:686-695) does not mention writes to read-only registers, reads of write-only registers, or d_data on errors.

**Left open.** Not stated: whether a write to a ro register returns d_error, what a read of a wo register returns (0 expected but not stated in the gpio text), and what d_data, d_size, d_param and d_sink carry in error and write responses.

**Question.** Are writes to ro registers silently ignored (no d_error)? Do reads of wo fields return 0? What are d_data and the other D fields on error responses and AccessAck?

**Readings.**
- Ro writes are ignored without error, wo reads return 0, and d_data is don't-care on errors and writes.
- Ro writes return d_error = 1; d_data must be 0 on errors.

References: spec/gpio_Design_Specification.md:508, spec/gpio_Design_Specification.md:542, spec/gpio_Design_Specification.md:817, spec/standards/opentitan_register_tool.md:686-697, spec/standards/opentitan_register_tool.md:867-869 (5/5 checked)

## GAP-019 [low] other

**Scenario.** A test writer copies the comments of the Programmer's Guide interrupt examples into test configurations.

**The specification says.** "*INTR_CTRL_EN_LVLLOW = 0b00001100; // falling detect on GPIO[2], GPIO[3]" and "*INTR_CTRL_EN_LVLHIGH = 0b11000000; // falling detect on GPIO[6], GPIO[7]" (:271-272). "input 4 for both rising edge detection" (:199), while INTR_ENABLE = 0b11011111 also enables bit 5, which has no configuration (:201).

**Left open.** The comments contradict the register names (the registers are level-low and level-high detection, not falling-edge detection).

**Question.** Can the comments be corrected to 'level-low' and 'level-high', and is the enable of bit 5 deliberate?

**Readings.**
- Comments are wrong; the register names decide.
- The comments describe an intended edge behaviour.

References: spec/gpio_Design_Specification.md:197-206, spec/gpio_Design_Specification.md:271-272 (2/2 checked)

Cost: US$1.17
