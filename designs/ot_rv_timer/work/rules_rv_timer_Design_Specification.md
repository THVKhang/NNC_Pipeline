# Extracted rules - rv_timer_Design_Specification.md

```
rules: 132  by strength {'MUST': 110, 'SHOULD': 4, 'MAY': 10, 'MUST_NOT': 8}  by check {'scenario': 83, 'both': 11, 'none': 20, 'assertion': 18}
normative sentences: 36  cited 36  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 14 (12 from cache)  cost US$0.0775  tokens in 9803 out 4554
```


## T2.2 Description

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T2.2-01 | MUST | system | scenario | Each 64-bit counter increments by the step value whenever the prescaler times out. *(when: whenever the prescaler times out)* | T2.2:s1 (p29) |
| RT-T2.2-02 | MUST | system | both | Each timer generates an interrupt if its counter reaches or exceeds the programmed value. *(when: when the counter reaches or is above the programmed compare value)* | T2.2:s2 (p29) |

## T2.3 Compatibility

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T2.3-01 | MUST | system | scenario | The timer IP provides memory-mapped registers equivalent to mtime and mtimecmp usable as the RISC-V machine-mode timer registers. | T2.3:s1 (p40) |

## T3.1 Block Diagram

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T3.1-01 | MUST | system | both | The tick generator creates a tick every time its internal counter hits the CFG0.prescaler value. *(when: when the tick generator's internal counter hits the CFG0.prescaler value)* | T3.1:s2 (p53) |
| RT-T3.1-02 | MUST | system | both | Each tick increments mtime by the CFG0.step value. *(when: on each tick)* | T3.1:s3 (p53) |
| RT-T3.1-03 | MUST | system | both | The timer compares 64-bit mtime with 64-bit mtimecmp and raises an interrupt when mtime is greater than or equal to mtimecmp. *(when: when the 64-bit mtime is greater than or equal to the 64-bit mtimecmp)* | T3.1:s4, T3.1:s5 (p53) |

## T3.2.1 Tick Generator

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T3.2.1-01 | MUST | system | scenario | The tick generator produces a fixed-period pulse signal, enabling a timer tick such as 1us or 10us regardless of the system clock period. | T3.2.1:s1, T3.2.1:s2 (p63) |
| RT-T3.2.1-02 | SHOULD | master | none | Firmware should change CFG0.prescaler appropriately for the single fixed clock frequency to obtain the desired tick period. *(when: because the timer supports only a single fixed clock in this version)* | T3.2.1:s6 (p70) |

## T3.2.2 Configurable number of timers and harts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T3.2.2-01 | MUST | system | scenario | Each hart has its own tick generator and counter, so the number of prescaler, step, and mtime registers equals the number of harts. | T3.2.2:s2, T3.2.2:s3 (p77) |
| RT-T3.2.2-02 | MAY | system | scenario | Each hart can have multiple sets of mtimecmp, comparator logic, and expire interrupt signals. | T3.2.2:s4 (p81) |
| RT-T3.2.2-03 | MUST | system | scenario | The IP is fixed to one hart and one timer per hart. *(when: in this version of the IP)* | T3.2.2:s5 (p81) |
| RT-T3.2.2-04 | MUST | system | scenario | There are separate interrupts per timer and a set of interrupt enable and state registers per hart. | T3.2.2:s7 (p85) |

## T4.1 Initialization

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T4.1-01 | MUST | system | scenario | The prescaler and step fields must be stable for the timer value to increment correctly. *(when: while the timer is active and incrementing)* | T4.1:s2 (p174) |
| RT-T4.1-02 | SHOULD | master | scenario | Software should de-activate the timer before changing the prescaler or step fields, then proceed with the change. *(when: when software wants to change prescaler or step)* | T4.1:s3 (p174) |

## T4.2 Register Access

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T4.2-01 | MUST_NOT | master | scenario | The CPU cannot access a 64-bit value in a single request over the 32-bit register interface; two 32-bit accesses are required. | T4.2:s3 (p181) |
| RT-T4.2-02 | MAY | slave | scenario | The timer value may increment between the two 32-bit reads of mtime and mtimeh. *(when: when a 64-bit timer value is read as two separate 32-bit reads)* | T4.2:s4 (p181) |
| RT-T4.2-03 | MAY | master | none | A rollover between the two reads can be detected in a standard way using a third read. *(when: when reading the 64-bit timer value in two reads)* | T4.2:s9 (p195) |
| RT-T4.2-04 | SHOULD | master | scenario | Software should use the prescribed safe write sequence to set mtime so timer operation does not yield an indeterminate result. *(when: when mtime must be set to an arbitrary, dynamically-determined value)* | T4.2:s13 (p219) |
| RT-T4.2-05 | SHOULD | master | scenario | The safe write sequence should be used so the timer does not assume an incorrect time between the two 32-bit writes. *(when: when the target lower half of mtime is close to 0xFFFF_FFFF)* | T4.2:s14 (p232) |
| RT-T4.2-06 | MUST | master | scenario | mtimecmp shall be written after mtime in order to clear any pending interrupt condition. *(when: when mtime is modified)* | T4.2:s15 (p236) |

## T4.3 Timer behaviour close to 2^64

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T4.3-01 | MAY | slave | scenario | One tick can carry mtime from below mtimecmp past the end of the range, so mtime skips mtimecmp and the interrupt is not raised. *(when: when CFG0.step is above 1 and mtimecmp is close to 0xFFFF_FFFF_FFFF_FFFF)* | T4.3:s7 (p245) |
| RT-T4.3-02 | MAY | master | none | Software may set mtimecmp to 0xFFFF_FFFF_FFFF_FFFF to get an intermediate interrupt. *(when: when the computed mtime + timeout comparison value overflows)* | T4.3:s10 (p255) |
| RT-T4.3-03 | MUST | master | none | The service routine needs to poll mtime until it wraps before scheduling the required interrupt with the originally computed mtimecmp value. *(when: in the service routine for the intermediate all-ones interrupt)* | T4.3:s11 (p255) |
| RT-T4.3-04 | MAY | slave | scenario | mtime can step over the all-ones value so the intermediate interrupt is never raised. *(when: when step is above 1)* | T4.3:s12 (p255) |
| RT-T4.3-05 | MAY | master | scenario | Setting mtimecmp to 0xFFFF_FFFF_FFFF_FFFF - step + 1 works for the intermediate interrupt, since the last mtime before wrap is at least that large. *(when: for any nonzero step)* | T4.3:s13 (p255) |

## T4.4 Interrupt Handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T4.4-01 | MUST | slave | both | The RV_TIMER module generates the interrupt when mtime is greater than or equal to mtimecmp. *(when: when mtime is greater than or equal to mtimecmp)* | T4.4:s1 (p271) |
| RT-T4.4-02 | MAY | master | scenario | The interrupt can be cleared by writing 1 to the Interrupt Status register INTR_STATE0. | T4.4:s3 (p271) |
| RT-T4.4-03 | MAY | master | scenario | The interrupt can be cleared by updating mtimecmp; a write to either COMPARE_LOWER0_0 or COMPARE_UPPER0_0 clears the interrupt source. | T4.4:s4, T4.4:s5 (p271) |

## T5.1 Summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.1-01 | MUST | slave | scenario | ALERT_TEST register must be located at offset 0x0 with length 4 bytes. | T5.1:s1, T5.2:s2 (p290) |
| RT-T5.1-02 | MUST | slave | scenario | CTRL must be at offset 0x4, length 4, reset to 0x0 with reset mask 0x1. | T5.1:s2, T5.3:s2, T5.3:s3, T5.3:s4 (p291) |
| RT-T5.1-03 | MUST | slave | scenario | INTR_ENABLE0 must be at offset 0x100, length 4, reset to 0x0 with reset mask 0x1. | T5.1:s3, T5.4:s2, T5.4:s3, T5.4:s4 (p292) |
| RT-T5.1-04 | MUST | slave | scenario | INTR_STATE0 must be at offset 0x104, length 4, reset to 0x0 with reset mask 0x1. | T5.1:s4, T5.5:s2, T5.5:s3, T5.5:s4 (p293) |
| RT-T5.1-05 | MUST | slave | scenario | INTR_TEST0 must be at offset 0x108, length 4, reset value 0x0 with reset mask 0x1. | T5.1:s5, T5.6:s2, T5.6:s3, T5.6:s4 (p294) |
| RT-T5.1-06 | MUST | slave | scenario | CFG0 must be at offset 0x10c, length 4, reset to 0x10000 with reset mask 0xff0fff. | T5.1:s6, T5.7:s2, T5.7:s3, T5.7:s4 (p295) |
| RT-T5.1-07 | MUST | slave | scenario | TIMER_V_LOWER0 at offset 0x110 holds timer value [31:0] as rw field v, reset 0x0, mask 0xffffffff. | T5.1:s7, T5.8:s2, T5.8:s3, T5.8:s4, T5.8.1:s1 (p296) |
| RT-T5.1-08 | MUST | slave | scenario | TIMER_V_UPPER0 at offset 0x114 holds timer value [63:32] as rw field v, reset 0x0, mask 0xffffffff. | T5.1:s8, T5.9:s2, T5.9:s3, T5.9:s4, T5.9.1:s1 (p297) |
| RT-T5.1-09 | MUST | slave | scenario | COMPARE_LOWER0_0 at offset 0x118 holds compare value [31:0] as rw field v, reset 0xffffffff, mask 0xffffffff. | T5.1:s9, T5.10:s2, T5.10:s3, T5.10:s4, T5.10.1:s1 (p298) |
| RT-T5.1-10 | MUST | slave | scenario | COMPARE_UPPER0_0 at offset 0x11c holds compare value [63:32] as rw field v, reset 0xffffffff, mask 0xffffffff. | T5.1:s10, T5.11:s2, T5.11:s3, T5.11:s4, T5.11.1:s1 (p299) |

## T5.2 ALERT_TEST

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.2-01 | MUST | slave | scenario | ALERT_TEST must reset to 0x80000000 with reset mask 0x80000001. *(when: After reset)* | T5.2:s3, T5.2:s4 (p304) |

## T5.2.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.2.1-01 | MUST | slave | scenario | Writing 0 to regwen disables alert testing until the next reset; regwen can only be cleared, not set, by writes. *(when: Software writes 0 to ALERT_TEST regwen bit 31 (rw0c, reset 0x1))* | T5.2.1:s1 (p315) |
| RT-T5.2.1-02 | MUST | slave | scenario | ALERT_TEST bits 30:1 are reserved. | T5.2.1:s2 (p316) |
| RT-T5.2.1-03 | MUST | slave | scenario | Writing 1 to fatal_fault triggers one alert event of the fatal kind. *(when: Write 1 to ALERT_TEST bit 0 (wo, reset 0x0) while alert testing is enabled)* | T5.2.1:s3 (p317) |

## T5.3.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.3.1-01 | MUST | system | scenario | When active_0 is 1 the timer operates; bits 31:1 of CTRL are reserved. *(when: CTRL.active_0 (rw, reset 0x0) is 1)* | T5.3.1:s1, T5.3.1:s2 (p333) |

## T5.4.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.4.1-01 | MUST | slave | scenario | IE_0 (bit 0, rw, reset 0x0) is the interrupt enable for the timer; bits 31:1 are reserved. | T5.4.1:s1, T5.4.1:s2 (p350) |

## T5.5.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.5.1-01 | MUST | slave | scenario | IS_0 (bit 0, rw1c, reset 0x0) holds the timer interrupt status and is cleared by writing 1; bits 31:1 are reserved. | T5.5.1:s1, T5.5.1:s2 (p367) |

## T5.6.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.6.1-01 | MUST | slave | scenario | T_0 (bit 0, wo, reset x) is the interrupt test for timer; bits 31:1 are reserved. | T5.6.1:s1, T5.6.1:s2 (p384) |

## T5.7.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T5.7.1-01 | MUST | slave | scenario | CFG0 step (bits 23:16, rw, reset 0x1) is the increment per tick; prescale (bits 11:0, rw, reset 0x0) generates the tick; other bits reserved. | T5.7.1:s1, T5.7.1:s2, T5.7.1:s3, T5.7.1:s4 (p401) |

## T6.1 Inter-Module Signals

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T6.1-01 | MUST | system | scenario | The racl_policies input must carry the incoming RACL policy vector from a racl_ctrl instance, with the policy selection vector parameter selecting the policy for each register. | T6.1:s1 (p489) |
| RT-T6.1-02 | MUST | slave | scenario | The module must output RACL error log information of this module on racl_error. | T6.1:s2 (p490) |

## T6.2 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T6.2-01 | MUST | slave | both | The module must raise interrupt timer_expired_hart0_timer0 when hart0's timer0 has expired (mtime >= mtimecmp). *(when: hart0's timer0 expired (mtime >= mtimecmp))* | T6.2:s1 (p497) |

## T6.3 Security Alerts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T6.3-01 | MUST | slave | scenario | The fatal_fault alert must be triggered when a fatal TL-UL bus integrity fault is detected inside RV_TIMER. *(when: a fatal TL-UL bus integrity fault is detected inside the RV_TIMER unit)* | T6.3:s1 (p503) |

## T6.4 Security Countermeasures

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T6.4-01 | MUST | slave | scenario | The module must implement the RV_TIMER.BUS.INTEGRITY countermeasure, an end-to-end bus integrity scheme on the TL-UL interface. | T6.4:s1 (p509) |

## T7 ot_rv_timer_nnc: integration of the OpenTitan rv_timer for verification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-T7-01 | MUST | system | none | The verification top ot_rv_timer_nnc must consist of the OpenTitan rv_timer plus a thin wrapper that flattens its struct ports and closes two protocols. | T7:s2 (p518) |
| RT-T7-02 | MUST | system | none | The behaviour of rv_timer itself must follow only the OpenTitan documents; the wrapper adds only port mapping, fixed configuration and wrapper behaviour. | T7:s3 (p518) |

## 1 Configuration

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-1-01 | MUST | system | none | The design under verification has exactly one hart and one timer (N_HARTS = 1, N_TIMERS = 1). | 1:s1 (p532) |
| RT-1-02 | MUST | system | scenario | Every register access is permitted when RACL is disabled. *(when: RACL is disabled)* | 1:s2 (p535) |
| RT-1-03 | MUST_NOT | system | both | No register access is rejected for an access-control reason. *(when: RACL is disabled)* | 1:s2 (p535) |
| RT-1-04 | MUST | system | none | The alert sender of rv_timer and the alert receiver of the wrapper both use the synchronous clocking scheme, with no synchronizer flops on the differential pairs. | 1:s3 (p538) |
| RT-1-05 | MUST_NOT | system | assertion | Alert ping requests are never issued. | 1:s4 (p538) |
| RT-1-06 | MUST | system | none | Every run uses the single fixed configuration; there is no design parameter to vary. | 1:s5 (p541) |

## 2 Clock and reset

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-2-01 | MUST | system | none | clk_i is the only clock in the design. | 2:s1 (p545) |
| RT-2-02 | MUST | system | assertion | All inputs are sampled and all outputs change at the rising edge of clk_i, except for the effect of rst_ni. | 2:s2 (p545) |
| RT-2-03 | MUST | system | both | rst_ni is active-low and may be asserted asynchronously, but its release must be synchronous to clk_i. | 2:s3 (p548) |
| RT-2-04 | MUST | system | both | Every register holds its reset value as given in the rv_timer specification register tables. *(when: While rst_ni is 0)* | 2:s4 (p548) |

## 3 Ports

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-3-01 | MUST | master | assertion | i_a_opcode must encode TL-UL request types as Get = 4, PutFullData = 0 and PutPartialData = 1. | 3:s5 (p560) |
| RT-3-02 | MUST | system | scenario | i_a_instr = 1 marks the request as an instruction fetch (a_user.instr_type = MuBi4True); i_a_instr = 0 marks a data access (MuBi4False). | 3:s12 (p567) |
| RT-3-03 | MUST | system | scenario | When i_a_intg_flip is 1, the A-channel integrity sent with the request is corrupted. *(when: i_a_intg_flip is 1)* | 3:s13 (p568) |
| RT-3-04 | MUST | slave | assertion | o_d_opcode must encode TL-UL response types as AccessAck = 0 and AccessAckData = 1. | 3:s16 (p571) |
| RT-3-05 | MUST | system | scenario | o_d_intg_err indicates that the response integrity of the D-channel beat is wrong. *(when: the response integrity of the D-channel beat is wrong)* | 3:s23 (p578) |
| RT-3-06 | MUST | system | scenario | o_alert indicates that the alert fatal_fault was received. *(when: alert fatal_fault is received)* | 3:s24 (p579) |
| RT-3-07 | MUST | system | scenario | o_alert_integ_fail indicates a signal integrity failure on the alert differential pairs. *(when: a signal integrity failure occurs on the alert differential pairs)* | 3:s25 (p580) |

## 4.1 Mapping

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-4.1-01 | MUST | system | scenario | The i_a_*, o_a_ready, o_d_* (except o_d_intg_err) and i_d_ready ports must be the same-named fields of the rv_timer TL-UL device interface tl, with TL-UL meaning. | 4.1:s1 (p587) |
| RT-4.1-02 | MUST | system | assertion | a_user.rsvd is 0. | 4.1:s2 (p590) |
| RT-4.1-03 | MUST | system | assertion | a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. | 4.1:s2 (p590) |
| RT-4.1-04 | MUST | master | assertion | The test bench must follow the TL-UL host rules, including keeping A-channel signals stable while a_valid is 1 and a_ready is 0. *(when: test bench acting as TL-UL host)* | 4.1:s3, 4.1:s4 (p592) |
| RT-4.1-05 | MAY | master | scenario | The test bench may send requests listed as TL-UL error cases (unsupported opcode, bad size or mask, misaligned address) as legal stimulus. | 4.1:s5 (p592) |
| RT-4.1-06 | MUST | slave | both | The device must answer such error-case requests with d_error = 1. *(when: request is a TL-UL error case (unsupported opcode, bad size or mask, misaligned address))* | 4.1:s5 (p592) |

## 4.2 Request integrity

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-4.2-01 | MUST | system | assertion | The wrapper must compute a_user.cmd_intg and a_user.data_intg with the OpenTitan TL-UL host integrity generator, so the request carries correct integrity. *(when: i_a_intg_flip = 0)* | 4.2:s1, 4.2:s2 (p599) |
| RT-4.2-02 | MUST | system | assertion | Bit 0 of a_user.cmd_intg must be inverted. *(when: i_a_intg_flip is 1)* | 4.2:s3 (p604) |
| RT-4.2-03 | MUST | slave | scenario | Such a request is a fatal TL-UL bus integrity fault that triggers the fatal_fault alert. *(when: request has command integrity error (i_a_intg_flip is 1))* | 4.2:s4 (p604) |

## 4.3 Response integrity

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-4.3-01 | MUST | system | assertion | o_d_intg_err must be 1 in a cycle where o_d_valid is 1 and the d_user.rsp_intg check fails, and 0 otherwise. | 4.3:s1 (p611) |
| RT-4.3-02 | MUST_NOT | slave | assertion | A correct device must never make o_d_intg_err 1. | 4.3:s2 (p611) |

## 5 Alert

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-5-01 | MUST | system | none | rv_timer has one alert, fatal_fault, sent through an alert sender. | 5:s1 (p617) |
| RT-5-02 | MUST | system | both | o_alert is the receiver's alert_o output and is 1 for one clock cycle for each alert handshake the receiver detects. *(when: When the alert receiver detects an alert handshake)* | 5:s2 (p617) |
| RT-5-03 | MUST | system | assertion | o_alert_integ_fail is the integ_fail_o output of the alert receiver. | 5:s3 (p622) |
| RT-5-04 | MUST_NOT | slave | assertion | A correct sender never makes o_alert_integ_fail 1. *(when: With a correct alert sender)* | 5:s4 (p622) |
| RT-5-05 | MUST | system | scenario | o_alert pulses repeatedly after a bus integrity fault until rst_ni is asserted, as a fatal alert is repeated until reset. *(when: After a bus integrity fault, until rst_ni is asserted)* | 5:s5 (p625) |
| RT-5-06 | MUST | system | scenario | A write of 1 to ALERT_TEST.fatal_fault triggers exactly one alert event. *(when: A write of 1 to ALERT_TEST.fatal_fault)* | 5:s6 (p625) |

## 6 Interrupt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-6-01 | MUST | system | assertion | o_intr_timer_expired must be the interrupt output intr_timer_expired_hart0_timer0_o of rv_timer. | 6:s1 (p631) |
| RT-6-02 | MUST | system | scenario | o_intr_timer_expired must behave as an event-type interrupt per the comportability specification, with registers INTR_ENABLE0, INTR_STATE0 and INTR_TEST0. | 6:s1 (p631) |

## 7 Verification scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-7-01 | MUST | system | scenario | Verification shall cover reset values of every register through the ports. | 7:s1 (p637) |
| RT-7-02 | MUST | system | scenario | Verification shall cover the access type of every register field as given in the register tables (rw, rw1c, wo, rw0c). | 7:s1 (p637) |
| RT-7-03 | MUST | system | scenario | Verification shall cover the tick generator (prescaler) and the step. | 7:s1 (p637) |
| RT-7-04 | MUST | system | scenario | Verification shall cover counting of the 64-bit timer value, including writes to it and the carry from the lower to the upper half. | 7:s1 (p637) |
| RT-7-05 | MUST | system | scenario | Verification shall cover the compare and the interrupt: state, enable, test, and clearing by writing the compare registers. | 7:s1 (p637) |
| RT-7-06 | MUST | system | scenario | Verification shall cover ALERT_TEST with its regwen field. | 7:s1 (p637) |
| RT-7-07 | MUST | system | scenario | Verification shall cover bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the fatal_fault alert. | 7:s1 (p637) |
| RT-7-08 | MUST | system | scenario | Behaviour close to 2^64 shall be reached by writing the timer value registers. *(when: Because the 64-bit timer value cannot be run through its whole range in simulation)* | 7:s2, 7:s3 (p644) |

## 8 Decisions for verification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RT-8-01 | MUST | system | scenario | Timer value increases by CFG0.step (modulo 2^64) once every CFG0.prescale + 1 cycles; prescale 0 gives a tick every cycle. *(when: CTRL.active_0 = 1 and CFG0 unchanged)* | 8:s5 (p659) |
| RT-8-02 | MUST | system | scenario | The first tick shall come no later than CFG0.prescale + 1 + 4 cycles after the write response. *(when: after CTRL.active_0 becomes 1)* | 8:s5 (p659) |
| RT-8-03 | MUST | master | none | Tests write CFG0 and TIMER_V_* only while CTRL.active_0 = 0; behaviour after such a write while active is not checked. *(when: writing CFG0 or TIMER_V_*)* | 8:s6 (p660) |
| RT-8-04 | MUST | system | scenario | INTR_STATE0.IS_0 shall read 1 within 4 cycles after a write of 1 to it. *(when: mtime >= mtimecmp holds and timer is active, after a write of 1 to INTR_STATE0.IS_0)* | 8:s7 (p661) |
| RT-8-05 | MUST | system | scenario | IS_0 shall be 1 no later than 4 cycles after that tick. *(when: condition mtime >= mtimecmp becomes true by a tick)* | 8:s9 (p663) |
| RT-8-06 | MUST | system | scenario | IS_0 shall be 1 no later than CFG0.prescale + 1 + 4 cycles after the write response. *(when: condition becomes true by a register write while active)* | 8:s9 (p663) |
| RT-8-07 | MUST | system | assertion | o_intr_timer_expired shall equal IS_0 AND IE_0. *(when: except in the 2 cycles after IS_0 or IE_0 changes)* | 8:s9 (p663) |
| RT-8-08 | MUST | system | scenario | IS_0 shall be 0 and the interrupt deasserted within 4 cycles. *(when: after a write to COMPARE_LOWER0_0 or COMPARE_UPPER0_0 leaves mtimecmp > mtime and it stays so)* | 8:s10 (p664) |
| RT-8-09 | MUST | system | scenario | IS_0 shall be 1 again within 4 cycles; an intermediate dip is not checked. *(when: after a compare write mtime >= mtimecmp still holds)* | 8:s10 (p664) |
| RT-8-10 | MUST | slave | scenario | Write-only fields read 0, reserved bits read 0 and writes to them have no effect. | 8:s12 (p666) |
| RT-8-11 | MUST | slave | scenario | INTR_TEST0 reads 0x0 and ALERT_TEST reads 0x8000_0000. *(when: after reset)* | 8:s12 (p666) |
| RT-8-12 | MUST | slave | scenario | Regwen reads 0 until reset; a later write of 0x8000_0001 completes with d_error = 0, triggers no alert. *(when: after a write to ALERT_TEST with bit 31 = 0 (regwen cleared until reset))* | 8:s13 (p667) |
| RT-8-13 | MUST | slave | scenario | Exactly one o_alert pulse shall occur, no later than 16 cycles after the write response. *(when: one write of 1 to fatal_fault, no other alert cause, no other such write within 32 cycles)* | 8:s13 (p667) |
| RT-8-14 | MUST | slave | scenario | At least one o_alert pulse and no more pulses than writes shall occur. *(when: fatal_fault writes closer than 32 cycles apart)* | 8:s13 (p667) |
| RT-8-15 | MUST_NOT | master | none | Tests do not use the combined write 0x0000_0001; they write 0x8000_0001. *(when: triggering an alert)* | 8:s13 (p667) |
| RT-8-16 | MUST | slave | scenario | o_alert shall pulse no later than 16 cycles after acceptance, then at least once every 32 cycles until rst_ni is asserted. *(when: request with i_a_intg_flip = 1 accepted)* | 8:s14 (p668) |
| RT-8-17 | MUST | master | none | The test resets the design. *(when: after a test with i_a_intg_flip = 1)* | 8:s14 (p668) |
| RT-8-18 | MUST_NOT | master | none | A write with i_a_instr = 1 is not used. | 8:s15 (p669) |
| RT-8-19 | MUST | slave | scenario | The slave returns d_error = 1 and changes no register. *(when: request to an unmapped offset in 0x000..0x1FF)* | 8:s16 (p670) |
| RT-8-20 | MUST_NOT | master | none | Requests at offset 0x200 and above are not used. | 8:s16 (p670) |
| RT-8-21 | MUST | slave | scenario | Returns d_error = 1 and changes nothing. *(when: byte write (a_size 0, mask 0001, aligned) to CFG0, TIMER_V_*, COMPARE_* or ALERT_TEST)* | 8:s17 (p671) |
| RT-8-22 | MUST | slave | scenario | Completes with d_error = 0 and has the effect of the write. *(when: byte write to byte 0 of CTRL, INTR_ENABLE0, INTR_STATE0 or INTR_TEST0)* | 8:s17 (p671) |
| RT-8-23 | MUST | slave | scenario | The write succeeds with d_error = 0. *(when: full-word write with mask 1111)* | 8:s17 (p671) |
| RT-8-24 | MUST | slave | scenario | Returns the full register. *(when: read of any size)* | 8:s17 (p671) |
| RT-8-25 | MUST | master | none | Match responses by d_source, use distinct a_source per outstanding request, and do not assume o_a_ready = 1. *(when: outstanding requests)* | 8:s18 (p672) |
| RT-8-26 | MUST | slave | scenario | Returned value lies between values before the request and after the response. *(when: read of TIMER_V_* while active)* | 8:s18 (p672) |
| RT-8-27 | MUST | slave | assertion | d_error is correct, d_source echoes a_source, d_size echoes a_size, d_opcode is AccessAckData for Get and AccessAck for PutFullData and PutPartialData. *(when: response)* | 8:s19 (p673) |
| RT-8-28 | MUST | slave | scenario | d_error = 1 is returned. *(when: undefined opcode)* | 8:s19 (p673) |
| RT-8-29 | MUST | master | none | The test bench keeps i_a_valid = 0. *(when: rst_ni = 0 and first cycle after release)* | 8:s20 (p674) |
| RT-8-30 | MUST | slave | assertion | o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired shall be 0. *(when: rst_ni = 0)* | 8:s20 (p674) |
| RT-8-31 | MUST | slave | scenario | The pending response is discarded. *(when: response pending at reset)* | 8:s20 (p674) |
| RT-8-32 | MUST | slave | assertion | o_d_intg_err and o_alert_integ_fail shall be 0 in every cycle. *(when: rst_ni = 1, including during i_a_intg_flip = 1)* | 8:s21 (p675) |
| RT-8-33 | MUST | master | none | Reached only by writing the timer value registers while inactive to values near the carry, then counting. *(when: testing carry at 2^32 and near 2^64)* | 8:s22 (p676) |
| RT-8-34 | MUST | master | none | Tests drive i_a_param = 0. | 8:s23 (p677) |
