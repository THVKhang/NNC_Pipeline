# Extracted rules - gpio_Design_Specification.md

```
rules: 171  by strength {'MUST': 153, 'MAY': 8, 'SHOULD': 2, 'MUST_NOT': 8}  by check {'scenario': 113, 'both': 27, 'none': 9, 'assertion': 22}
normative sentences: 40  cited 39  skipped 1  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 17 (0 from cache)  cost US$0.5544  tokens in 87672 out 27851
```


## T2.2 Description

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T2.2-01 | MUST | system | scenario | Each of the 32 independent GPIO bits can be written as a peripheral output via direct write, giving software simultaneous control of all 32 bits. *(when: writing GPIO outputs in direct-write mode)* | T2.2:s2, T2.2:s6, T2.2:s7 (p33) |
| GP-T2.2-02 | MUST | system | scenario | Masked write modifies only the selected bits of a 16-bit half, using the user-provided mask and new values, without read-modify-write; unmasked bits keep their output value. *(when: writing GPIO outputs in masked-write mode)* | T2.2:s2, T2.2:s8, T2.2:s9 (p33) |
| GP-T2.2-03 | MAY | system | scenario | Software can read each of the 32 GPIO bits as peripheral inputs. | T2.2:s3, T2.2:s11 (p33) |
| GP-T2.2-04 | MAY | system | scenario | Software can configure interrupt event detection for any of the 32 bits as positive edge, negative edge or level detection. *(when: interrupt configured for a GPIO bit)* | T2.2:s12, T2.2:s13 (p50) |
| GP-T2.2-05 | MUST | system | both | The input must be stable for 16 module clock cycles before the input register reflects the change and interrupt generation is evaluated. *(when: noise filter enabled for a GPIO input)* | T2.2:s14, T2.2:s15 (p50) |
| GP-T2.2-06 | MUST | system | scenario | A change in output value is reflected in the input register with a corresponding filter delay. *(when: filter enabled and pin set to output)* | T2.2:s16 (p50) |

## T3.2.1 GPIO Output logic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T3.2.1-01 | MUST | slave | scenario | DIRECT_OUT provides full write and read access to all 32 bits of the DATA_OUT register. *(when: software accesses DATA_OUT via DIRECT_OUT)* | T3.2.1:s1, T3.2.1:s2, T3.2.1:s3 (p82) |
| GP-T3.2.1-02 | MUST | slave | scenario | Upper 16 bits of the write are a mask of bits to modify and lower 16 bits are data; hardware updates only masked DATA_OUT bits without read-modify-write. *(when: a write to MASKED_OUT_UPPER or MASKED_OUT_LOWER)* | T3.2.1:s4, T3.2.1:s5 (p88) |
| GP-T3.2.1-03 | MUST | slave | scenario | Reads return the upper or lower 16 bits of DATA_OUT in the lower 16 bits, with zeros in the upper 16 mask-field bits. *(when: a read of a masked output register)* | T3.2.1:s6, T3.2.1:s7 (p95) |
| GP-T3.2.1-04 | SHOULD | master | none | Software should read the DATA_IN register to read what is on the pins. *(when: software needs to read the value on the pins)* | T3.2.1:s8 (p95) |
| GP-T3.2.1-05 | MUST | slave | scenario | DATA_OE is accessible directly via DIRECT_OE and with masked access via MASKED_OE_UPPER and MASKED_OE_LOWER, with the same semantics as DATA_OUT. | T3.2.1:s10, T3.2.1:s11 (p100) |
| GP-T3.2.1-06 | MUST | system | scenario | The output enable is sent to the pad control block to determine whether the pad drives the DATA_OUT value to the pin. | T3.2.1:s12 (p104) |
| GP-T3.2.1-07 | MUST | system | scenario | Output values of unused GPIOs are disconnected and have no effect on the GPIO input regardless of output enable values. *(when: GPIO output is unused (not wired to a pin or not selected for pin multiplexing))* | T3.2.1:s14 (p111) |

## T3.2.2 Per-Pin Register View

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T3.2.2-01 | MUST | slave | scenario | The per-pin and 32-bit register views alias the same state, and a write to a per-pin register affects only its own GPIO. | T3.2.2:s3 (p117) |
| GP-T3.2.2-02 | MUST | slave | scenario | Per-pin view has separate aligned ranges: PER_PIN_IO holds one register per GPIO for DATA_OUT/DATA_IN bit i; configuration range holds consecutive PER_PIN_OE_n and PER_PIN_INTR_CTRL_n registers per GPIO. | T3.2.2:s4, T3.2.2:s5, T3.2.2:s6 (p121) |
| GP-T3.2.2-03 | MUST | master | scenario | A register write must cover all bytes of the register that hold a field. *(when: writing a per-pin register)* | T3.2.2:s7 (p126) |
| GP-T3.2.2-04 | MUST | slave | scenario | Output enable and interrupt configuration of a GPIO are in separate registers so access to one can be granted without the other. | T3.2.2:s8 (p126) |
| GP-T3.2.2-05 | MUST_NOT | slave | scenario | INTR_STATE, INTR_ENABLE and INTR_TEST have no per-pin view. | T3.2.2:s9 (p129) |

## T3.2.3 GPIO Input

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T3.2.3-01 | MUST | slave | scenario | DATA_IN is always readable and reflects the value at the chip input pad regardless of DATA_OE. | T3.2.3:s1, T3.2.3:s9, T3.2.3:s10 (p134) |
| GP-T3.2.3-02 | MUST | system | scenario | GPIO peripheral inputs not connected to a chip input are tied to constant zero. *(when: pin-multiplexing unit present and the peripheral input is not connected to a chip input)* | T3.2.3:s2 (p134) |
| GP-T3.2.3-03 | MAY | slave | scenario | Each of the 32 inputs can be independently enabled for the 16-cycle noise filter via CTRL_EN_INPUT_FILTER, applied to both DATA_IN and interrupt detection. | T3.2.3:s3, T3.2.3:s4, T3.2.3:s5 (p139) |

## T3.2.3.1 GPIO Inputs as HW Straps

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T3.2.3.1-01 | MUST | slave | both | GPIO detects strap_en_i low-to-high and one clock cycle later samples the GPIO inputs into HW_STRAPS_DATA_IN. *(when: after reset, first cycle strap_en_i is asserted)* | T3.2.3.1:s1, T3.2.3.1:s2, T3.2.3.1:s3 (p151) |
| GP-T3.2.3.1-02 | MUST | slave | scenario | All 32 input bits are sampled regardless of output enable, and later input changes are not captured in HW_STRAPS_DATA_IN. *(when: after the strap sample is taken)* | T3.2.3.1:s5, T3.2.3.1:s6 (p151) |

## T3.2.4 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T3.2.4-01 | MUST | slave | scenario | The GPIO provides 32 interrupt signals, each independently enabled, tested and configured. | T3.2.4:s1, T3.2.4:s2 (p161) |
| GP-T3.2.4-02 | MUST | slave | scenario | Interrupt state is readable in INTR_STATE only when enabled, and can be triggered only by GPIO input. *(when: interrupt enabled via INTR_ENABLE and INTR_CTRL_EN registers)* | T3.2.4:s3, T3.2.4:s4, T3.2.4:s11 (p161) |
| GP-T3.2.4-03 | MUST | slave | scenario | Writing 1 to an INTR_STATE bit clears that interrupt. *(when: writing 1 to an INTR_STATE bit)* | T3.2.4:s5 (p161) |
| GP-T3.2.4-04 | MUST | slave | scenario | Each bit supports rising-edge, falling-edge, level-high and level-low interrupt detection, selected by the corresponding INTR_CTRL_EN register. | T3.2.4:s6, T3.2.4:s7, T3.2.4:s8, T3.2.4:s9 (p171) |
| GP-T3.2.4-05 | MAY | master | scenario | An input may be configured for both rising and falling edge detection, with no hardware indication of which edge caused the interrupt. | T3.2.4:s10 (p171) |
| GP-T3.2.4-06 | MUST | slave | scenario | All inputs pass through the optional noise filter before interrupt detection. | T3.2.4:s12 (p180) |
| GP-T3.2.4-07 | MUST | slave | scenario | Interrupts to the processor are level interrupts; edge detection is converted into a level interrupt. *(when: edge detection configured)* | T3.2.4:s13, T3.2.4:s14 (p180) |

## T4.4 Per-Pin Register View

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T4.4-01 | SHOULD | system | none | Each component should be granted access only to the per-pin registers of its own GPIOs, while software managing all GPIOs keeps using the 32-bit registers. *(when: when individual GPIOs belong to different software components)* | T4.4:s2 (p309) |
| GP-T4.4-02 | MUST | master | scenario | A write to PER_PIN_IO_i must cover both bytes 0 and 1, i.e., be at least 16 bits wide. *(when: when writing PER_PIN_IO_i, which has fields in bytes 0 and 1)* | T4.4:s7 (p317) |
| GP-T4.4-03 | MUST | slave | scenario | A byte write to PER_PIN_IO_i returns an error and has no effect on the register. *(when: when a byte write is made to PER_PIN_IO_i)* | T4.4:s8 (p317) |
| GP-T4.4-04 | MUST | system | none | A capability for PER_PIN_IO_i must cover at least bytes 0 and 1 of the register. *(when: when granting a capability for PER_PIN_IO_i)* | T4.4:s8 (p317) |
| GP-T4.4-05 | MAY | master | scenario | PER_PIN_OE_i and PER_PIN_INTR_CTRL_i accept byte writes. | T4.4:s9 (p317) |

## T5.1 Summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.1-01 | MUST | slave | scenario | gpio core registers INTR_STATE through HW_STRAPS_DATA_IN must be accessible at offsets 0x0 to 0x44 in 4-byte steps, each 4 bytes long, with the listed functions. *(when: Register access to the gpio core registers)* | T5.1:s1, T5.1:s2, T5.1:s3, T5.1:s4, T5.1:s5, T5.1:s6, T5.1:s7, T5.1:s8, T5.1:s9, T5.1:s10, T5.1:s11, T5.1:s12, T5.1:s13, T5.1:s14, T5.1:s15, T5.1:s16, T5.1:s17, T5.1:s18 (p347) |
| GP-T5.1-02 | MUST | slave | scenario | PER_PIN_IO_0 to PER_PIN_IO_31 must be at offsets 0x100 to 0x17c in 4-byte steps, each 4 bytes long, giving a per-pin view of output and input data of one GPIO. *(when: Register access to PER_PIN_IO registers)* | T5.1:s19, T5.1:s20, T5.1:s21, T5.1:s22, T5.1:s23, T5.1:s24, T5.1:s25, T5.1:s26, T5.1:s27, T5.1:s28, T5.1:s29, T5.1:s30, T5.1:s31, T5.1:s32, T5.1:s33, T5.1:s34, T5.1:s35, T5.1:s36, T5.1:s37, T5.1:s38, T5.1:s39, T5.1:s40, T5.1:s41, T5.1:s42, T5.1:s43, T5.1:s44, T5.1:s45, T5.1:s46, T5.1:s47, T5.1:s48, T5.1:s49, T5.1:s50 (p365) |
| GP-T5.1-03 | MUST | slave | scenario | PER_PIN_OE_n and PER_PIN_INTR_CTRL_n for GPIO[n], n=0..31, must alternate at offsets 0x200 to 0x2fc in 4-byte steps, each 4 bytes long. *(when: Register access to PER_PIN_OE and PER_PIN_INTR_CTRL registers)* | T5.1:s51, T5.1:s52, T5.1:s53, T5.1:s54, T5.1:s55, T5.1:s56, T5.1:s57, T5.1:s58, T5.1:s59, T5.1:s60, T5.1:s61, T5.1:s62, T5.1:s63, T5.1:s64, T5.1:s65, T5.1:s66, T5.1:s67, T5.1:s68, T5.1:s69, T5.1:s70, T5.1:s71, T5.1:s72, T5.1:s73, T5.1:s74, T5.1:s75, T5.1:s76, T5.1:s77, T5.1:s78, T5.1:s79, T5.1:s80, T5.1:s81, T5.1:s82, T5.1:s83, T5.1:s84, T5.1:s85, T5.1:s86, T5.1:s87, T5.1:s88, T5.1:s89, T5.1:s90, T5.1:s91, T5.1:s92, T5.1:s93, T5.1:s94, T5.1:s95, T5.1:s96, T5.1:s97, T5.1:s98, T5.1:s99, T5.1:s100, T5.1:s101, T5.1:s102, T5.1:s103, T5.1:s104, T5.1:s105, T5.1:s106, T5.1:s107, T5.1:s108, T5.1:s109, T5.1:s110, T5.1:s111, T5.1:s112, T5.1:s113, T5.1:s114 (p397) |

## T5.2.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.2.1-01 | MUST | system | both | INTR_STATE.gpio bit is raised when the corresponding GPIO pin detects its configured interrupt mode; the field is rw1c (write 1 clears). *(when: any GPIO pin detects its configured interrupt mode)* | T5.2.1:s1 (p476) |

## T5.3.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.3.1-01 | MUST | system | both | An interrupt is enabled by INTR_ENABLE.gpio[i] only when INTR_STATE.gpio[i] is set. *(when: corresponding bit in INTR_STATE.gpio is set)* | T5.3.1:s1 (p492) |

## T5.4.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.4.1-01 | MUST | system | both | Writing 1 to INTR_TEST.gpio[i] forces INTR_STATE.gpio[i] to 1. *(when: 1 is written to INTR_TEST.gpio[i])* | T5.4.1:s1 (p508) |

## T5.5.1 Fields

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.5.1-01 | MUST | system | scenario | Writing 0 to ALERT_TEST.regwen disables alert testing until the next reset. *(when: 0 is written to ALERT_TEST.regwen)* | T5.5.1:s1 (p524) |
| GP-T5.5.1-02 | MUST | system | scenario | Writing 1 to ALERT_TEST.fatal_fault triggers one alert event of the fatal_fault kind. *(when: 1 is written to ALERT_TEST.fatal_fault)* | T5.5.1:s3 (p526) |

## T5.8 MASKED_OUT_LOWER

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.8-01 | MUST | system | scenario | Upper 16 bits of MASKED_OUT_LOWER are a mask; DATA_OUT[i] for i in 0..15 is updated with data[i] only if mask[i] is 1. *(when: MASKED_OUT_LOWER is written)* | T5.8:s2, T5.8:s3, T5.8:s4, T5.8.1:s1, T5.8.1:s2 (p563) |
| GP-T5.8-02 | MUST | system | scenario | Reading MASKED_OUT_LOWER returns upper 16 bits as zero and lower 16 bits as DATA_OUT[15:0]. *(when: MASKED_OUT_LOWER is read)* | T5.8:s5 (p569) |

## T5.9 MASKED_OUT_UPPER

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.9-01 | MUST | system | scenario | Upper 16 bits of MASKED_OUT_UPPER are a mask; DATA_OUT[i] for i in 16..31 is updated from the lower 16 bits only if mask[i] is 1. *(when: MASKED_OUT_UPPER is written)* | T5.9:s2, T5.9:s3, T5.9:s4, T5.9.1:s1, T5.9.1:s2 (p589) |
| GP-T5.9-02 | MUST | system | scenario | Reading MASKED_OUT_UPPER returns upper 16 bits as zero and lower 16 bits as DATA_OUT[31:16]. *(when: MASKED_OUT_UPPER is read)* | T5.9:s5 (p595) |

## T5.10 DIRECT_OE

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.10-01 | MUST | system | scenario | Setting direct_oe[i] to 1 enables output mode for GPIO[i]. *(when: direct_oe[i] is set to 1)* | T5.10:s2 (p615) |

## T5.11 MASKED_OE_LOWER

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.11-01 | MUST | system | scenario | Upper 16 bits of MASKED_OE_LOWER are a mask; DATA_OE[i] for i in 0..15 is updated from the lower 16 bits only if mask[i] is 1. *(when: MASKED_OE_LOWER is written)* | T5.11:s2, T5.11:s3, T5.11:s4, T5.11.1:s1, T5.11.1:s2 (p633) |
| GP-T5.11-02 | MUST | system | scenario | Reading MASKED_OE_LOWER returns upper 16 bits as zero and lower 16 bits as DATA_OE[15:0]. *(when: MASKED_OE_LOWER is read)* | T5.11:s5 (p640) |

## T5.12 MASKED_OE_UPPER

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.12-01 | MUST | system | scenario | Upper 16 bits of MASKED_OE_UPPER are a mask; DATA_OE[i] for i in 16..31 is updated from the lower 16 bits only if mask[i] is 1. *(when: MASKED_OE_UPPER is written)* | T5.12:s2, T5.12:s3, T5.12:s4, T5.12.1:s1, T5.12.1:s2 (p660) |
| GP-T5.12-02 | MUST | system | scenario | Reading MASKED_OE_UPPER returns upper 16 bits as zero and lower 16 bits as DATA_OE[31:16]. *(when: MASKED_OE_UPPER is read)* | T5.12:s5 (p667) |

## T5.13 INTR_CTRL_EN_RISING

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.13-01 | MUST | system | scenario | Rising-edge interrupt detection on GPIO[i] is enabled. *(when: INTR_ENABLE[i] is true and INTR_CTRL_EN_RISING[i] is 1)* | T5.13:s2 (p687) |

## T5.14 INTR_CTRL_EN_FALLING

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.14-01 | MUST | system | scenario | Falling-edge interrupt detection on GPIO[i] is enabled. *(when: INTR_ENABLE[i] is true and INTR_CTRL_EN_FALLING[i] is 1)* | T5.14:s2 (p706) |

## T5.15 INTR_CTRL_EN_LVLHIGH

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.15-01 | MUST | system | scenario | Level-high interrupt detection on GPIO[i] is enabled. *(when: INTR_ENABLE[i] is true and INTR_CTRL_EN_LVLHIGH[i] is 1)* | T5.15:s2 (p725) |

## T5.16 INTR_CTRL_EN_LVLLOW

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.16-01 | MUST | system | scenario | Level-low interrupt detection on GPIO[i] is enabled. *(when: INTR_ENABLE[i] is true and INTR_CTRL_EN_LVLLOW[i] is 1)* | T5.16:s2 (p744) |

## T5.17 CTRL_EN_INPUT_FILTER

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.17-01 | MUST | system | both | A value of input bit [i] must be stable for 16 cycles before transitioning. *(when: CTRL_EN_INPUT_FILTER[i] is true)* | T5.17:s2 (p763) |

## T5.18 HW_STRAPS_DATA_IN_VALID

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.18-01 | MUST | system | scenario | HW_STRAPS_DATA_IN_VALID indicates whether the data in HW_STRAPS_DATA_IN is valid. | T5.18:s1 (p780) |

## T5.19 HW_STRAPS_DATA_IN

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.19-01 | MUST | system | both | GPIO input data is sampled at most once after reset on the first cycle where strap_en_i is high, and stored in HW_STRAPS_DATA_IN. *(when: GpioAsHwStrapsEn is true)* | T5.19:s1, T5.19:s4, T5.19:s5 (p797) |
| GP-T5.19-02 | MUST | system | both | HW_STRAPS_DATA_IN reads as zero. *(when: GpioAsHwStrapsEn is false)* | T5.19:s3 (p801) |

## T5.20 PER_PIN_IO

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.20-01 | MUST | system | scenario | PER_PIN_IO bit 8 (data_in) aliases DATA_IN[i] and bit 0 (data_out) aliases DATA_OUT[i] for GPIO[i]. | T5.20:s2, T5.20.2:s2, T5.20.2:s4 (p822) |
| GP-T5.20-02 | MUST | system | scenario | Writing PER_PIN_IO updates only DATA_OUT[i], without affecting other GPIOs. *(when: PER_PIN_IO is written)* | T5.20:s3 (p822) |

## T5.21 PER_PIN_OE_0

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.21-01 | MUST | system | scenario | PER_PIN_OE_0 bit 0 aliases bit 0 of DIRECT_OE (DATA_OE[0]). | T5.21:s2, T5.21.1:s2 (p881) |
| GP-T5.21-02 | MUST | system | scenario | Writing PER_PIN_OE_0 updates only DATA_OE[0], without affecting other GPIOs. *(when: PER_PIN_OE_0 is written)* | T5.21:s3 (p881) |

## T5.22 PER_PIN_INTR_CTRL_0

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.22-01 | MUST | system | scenario | PER_PIN_INTR_CTRL_0 bits 0..4 alias bit 0 of INTR_CTRL_EN_RISING, FALLING, LVLHIGH, LVLLOW and CTRL_EN_INPUT_FILTER respectively. | T5.22:s2, T5.22.1:s2, T5.22.1:s3, T5.22.1:s4, T5.22.1:s5, T5.22.1:s6 (p901) |
| GP-T5.22-02 | MUST | system | scenario | Writing PER_PIN_INTR_CTRL_0 updates only the configuration of GPIO[0], without affecting other GPIOs. *(when: PER_PIN_INTR_CTRL_0 is written)* | T5.22:s3 (p901) |
| GP-T5.22-03 | MUST | system | scenario | PER_PIN_INTR_CTRL_0 is separate from PER_PIN_OE_0 so access to output enable and interrupt configuration can be controlled independently. | T5.22:s4 (p901) |

## T5.23 PER_PIN_OE_1 to PER_PIN_OE_31, PER_PIN_INTR_CTRL_1 to PER_PIN_INTR_CTRL_31

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T5.23-01 | MUST | system | scenario | PER_PIN_OE_i at 0x200+8*i and PER_PIN_INTR_CTRL_i at 0x204+8*i behave like the index-0 registers for GPIO[i], with reset default 0x0. *(when: GPIO index i is 1 to 31)* | T5.23:s1, T5.23:s2 (p924) |

## T6.2 Inter-Module Signals

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T6.2-01 | MUST | system | scenario | On strap_en, gpio must take a snapshot of the input pins and provide the sampled values on sampled_straps. *(when: when strap_en is asserted)* | T6.2:s1 (p947) |
| GP-T6.2-02 | MUST_NOT | system | scenario | The behaviour of strap_en after the snapshot event must have no effect on the sampled strap values. *(when: after the strap snapshot event has occurred)* | T6.2:s1 (p947) |
| GP-T6.2-03 | MUST | system | scenario | sampled_straps must carry the sampled strap values. | T6.2:s2 (p948) |

## T6.3 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T6.3-01 | MUST | system | scenario | The corresponding gpio interrupt event must be raised when a GPIO pin detects the configured interrupt mode. *(when: when any GPIO pin detects its configured interrupt mode)* | T6.3:s1 (p957) |

## T6.4 Security Alerts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T6.4-01 | MUST | system | scenario | The fatal_fault alert must be triggered when a fatal TL-UL bus integrity fault is detected. *(when: when a fatal TL-UL bus integrity fault is detected)* | T6.4:s1 (p963) |

## T7 ot_gpio_nnc: integration of the OpenTitan gpio for verification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-T7-01 | MUST | system | scenario | The behaviour of the gpio block itself must conform only to the OpenTitan documents; the wrapper must not alter gpio behaviour beyond port mapping, configurations and wrapper functions. | T7:s3 (p976) |

## 1 Configuration

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-1-01 | MUST | system | scenario | Every register access must be permitted and no access may be rejected for an access-control reason. *(when: RACL is disabled in the configuration)* | 1:s2 (p992) |
| GP-1-02 | MUST | system | none | The alert sender of gpio and the alert receiver of the wrapper must both use the synchronous clocking scheme, with no synchronizer flops on the differential pairs. | 1:s3 (p995) |
| GP-1-03 | MUST_NOT | system | assertion | Ping requests must never be issued. | 1:s4 (p995) |
| GP-1-04 | MUST | system | scenario | GpioAsyncOn is passed through unchanged from ot_gpio_nnc to gpio (legal values 0 or 1, default 1); when 1, 2-flop synchronizers are instantiated on all GPIO inputs. *(when: GpioAsyncOn is 1)* | 1:s5, 1:s6 (p998) |
| GP-1-05 | MUST | system | scenario | GpioAsHwStrapsEn is passed through unchanged to gpio (legal values 0 or 1, default 1); when 1, HW straps sampling logic for GPIO inputs is enabled at initial cold boot, and HW_STRAPS_DATA_IN behaves per its register description. *(when: GpioAsHwStrapsEn is 1)* | 1:s5, 1:s7 (p998) |
| GP-1-06 | MUST | system | none | The verification must be run in every combination of GpioAsyncOn and GpioAsHwStrapsEn that the run set selects; the default (1, 1) is the Earl Grey top-level configuration. | 1:s8 (p1005) |

## 2 Clock and reset

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-2-01 | MUST | system | none | clk_i is the only clock in the design. | 2:s1 (p1010) |
| GP-2-02 | MUST | system | assertion | TL-UL and strap inputs are sampled and all outputs change only at the rising edge of clk_i, except for the effect of rst_ni. | 2:s2 (p1010) |
| GP-2-03 | MAY | any | scenario | i_gpio may change at any time relative to clk_i. *(when: GpioAsyncOn = 1)* | 2:s3 (p1013) |
| GP-2-04 | MUST | master | assertion | The test bench must change i_gpio only synchronously to clk_i, like the other inputs. *(when: GpioAsyncOn = 0 (no synchronizer))* | 2:s4 (p1013) |
| GP-2-05 | MUST | system | assertion | rst_ni is active-low reset, asserted asynchronously and released synchronously to clk_i. | 2:s5 (p1017) |
| GP-2-06 | MUST | system | both | While rst_ni is 0, every register holds its reset value given in the gpio specification register tables. *(when: rst_ni is 0)* | 2:s6 (p1017) |

## 3 Ports

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-3-01 | MUST | system | scenario | i_a_instr=1 must make the request an instruction fetch (a_user.instr_type = MuBi4True); i_a_instr=0 must make it a data access (MuBi4False). *(when: A request is presented on the TL-UL A channel)* | 3:s12 (p1036) |
| GP-3-02 | MUST | system | scenario | When i_a_intg_flip is 1, the A-channel integrity sent with the request must be corrupted. *(when: i_a_intg_flip is 1)* | 3:s13 (p1037) |
| GP-3-03 | MUST | system | scenario | o_d_intg_err must indicate when the response integrity of the D-channel beat is wrong. *(when: The response integrity of the D-channel beat is wrong)* | 3:s23 (p1047) |
| GP-3-04 | MUST | system | scenario | o_alert must indicate that alert fatal_fault has been received. *(when: Alert fatal_fault is received)* | 3:s24 (p1048) |
| GP-3-05 | MUST | system | scenario | o_alert_integ_fail must indicate a signal integrity failure on the alert differential pairs. *(when: Signal integrity failure occurs on the alert differential pairs)* | 3:s25 (p1049) |
| GP-3-06 | MUST | system | both | o_gpio (cio_gpio_o) must carry the value of DATA_OUT. | 3:s27 (p1051) |
| GP-3-07 | MUST | system | both | o_gpio_en (cio_gpio_en_o) must carry the value of DATA_OE. | 3:s28 (p1052) |

## 4.1 Mapping

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-4.1-01 | MUST | system | scenario | The i_a_*, o_a_ready, o_d_* (except o_d_intg_err) and i_d_ready ports carry the same-named fields of the gpio TL-UL device interface tl, with TL-UL specification meaning. | 4.1:s1 (p1062) |
| GP-4.1-02 | MUST | system | assertion | a_user.rsvd is 0. | 4.1:s2 (p1065) |
| GP-4.1-03 | MUST | system | assertion | a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. | 4.1:s2 (p1065) |
| GP-4.1-04 | MUST | master | assertion | The test bench must follow the TL-UL host rules, for example keeping A-channel signals stable while a_valid is 1 and a_ready is 0. *(when: test bench acting as TL-UL host)* | 4.1:s3, 4.1:s4 (p1067) |
| GP-4.1-05 | MAY | master | scenario | The test bench may send requests listed as TL-UL error cases (unsupported opcode, bad size or mask, misaligned address) as legal stimulus. | 4.1:s5 (p1067) |
| GP-4.1-06 | MUST | slave | both | The device answers such error-case requests with d_error = 1. *(when: request is a TL-UL error case (unsupported opcode, bad size or mask, misaligned address))* | 4.1:s5 (p1067) |

## 4.2 Request integrity

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-4.2-01 | MUST | system | assertion | The wrapper computes correct a_user.cmd_intg and a_user.data_intg for every request, so a request with i_a_intg_flip = 0 carries correct integrity. *(when: i_a_intg_flip = 0)* | 4.2:s1, 4.2:s2 (p1074) |
| GP-4.2-02 | MUST | system | assertion | Bit 0 of a_user.cmd_intg is inverted. *(when: i_a_intg_flip is 1)* | 4.2:s3 (p1079) |
| GP-4.2-03 | MUST | slave | scenario | The command integrity error is treated as a fatal TL-UL bus integrity fault and triggers the fatal_fault alert. *(when: request has a command integrity error (i_a_intg_flip is 1))* | 4.2:s4 (p1079) |

## 4.3 Response integrity

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-4.3-01 | MUST | system | assertion | o_d_intg_err is 1 in a cycle where o_d_valid is 1 and the d_user.rsp_intg check fails, and 0 otherwise. | 4.3:s1 (p1086) |
| GP-4.3-02 | MUST_NOT | slave | assertion | A correct device never makes o_d_intg_err 1. | 4.3:s2 (p1086) |

## 5 Alert

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-5-01 | MUST | system | scenario | gpio has a single alert, fatal_fault, which is sent through an alert sender. | 5:s1 (p1092) |
| GP-5-02 | MUST | system | both | o_alert is the alert_o output of the alert receiver and is 1 for exactly one clock cycle for each detected alert handshake. *(when: For each alert handshake detected by the receiver)* | 5:s2 (p1092) |
| GP-5-03 | MUST | system | assertion | o_alert_integ_fail is the integ_fail_o output of the alert receiver. | 5:s3 (p1097) |
| GP-5-04 | MUST_NOT | source | assertion | A correct alert sender never makes o_alert_integ_fail 1. *(when: A correct alert sender)* | 5:s4 (p1097) |
| GP-5-05 | MUST | system | scenario | After a bus integrity fault, the fatal alert is repeated so o_alert pulses repeatedly until rst_ni is asserted. *(when: After a bus integrity fault)* | 5:s5 (p1100) |
| GP-5-06 | MUST | system | scenario | A write of 1 to ALERT_TEST.fatal_fault triggers exactly one alert event. *(when: A write of 1 to ALERT_TEST.fatal_fault)* | 5:s6 (p1100) |

## 6 GPIO pins

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-6-01 | MUST | system | assertion | i_gpio, o_gpio and o_gpio_en must map to cio_gpio_i, cio_gpio_o and cio_gpio_en_o respectively, with bit i belonging to GPIO[i]. | 6:s1 (p1106) |
| GP-6-02 | MUST | system | both | o_gpio carries DATA_OUT and o_gpio_en carries DATA_OE. | 6:s1 (p1106) |
| GP-6-03 | MUST_NOT | system | assertion | ot_gpio_nnc must not contain a pad model or pin multiplexer; i_gpio is driven only by the test bench and does not depend on o_gpio or o_gpio_en. | 6:s2 (p1109) |
| GP-6-04 | MUST | any | scenario | The test must model the pad itself, for example driving i_gpio[i] = o_gpio[i] where o_gpio_en[i] = 1 and 1 elsewhere. *(when: a test follows a Programmer's Guide example assuming pads with weak pull-ups)* | 6:s3 (p1109) |

## 7 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-7-01 | MUST | system | both | o_intr_gpio[i] must be the interrupt output intr_gpio_o[i] of gpio, an event-type interrupt per the comportability specification, associated with bit i of INTR_ENABLE, INTR_STATE and INTR_TEST. | 7:s1 (p1116) |

## 8 Straps

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-8-01 | MUST | system | assertion | The wrapper input i_strap_en must be connected to the gpio input strap_en_i. | 8:s1 (p1122) |
| GP-8-02 | MUST | system | assertion | The wrapper output o_straps_valid must be driven by the valid field of the gpio output sampled_straps_o. | 8:s1 (p1122) |
| GP-8-03 | MUST | system | assertion | The wrapper output o_straps_data must be driven by the data field of the gpio output sampled_straps_o. | 8:s1 (p1122) |

## 9 Verification scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-9-01 | MUST | system | scenario | Verification must cover reset values of every register and the access type of every register field as given in the register tables. *(when: in each configuration of the run set, through the ports)* | 9:s1 (p1127) |
| GP-9-02 | MUST | system | scenario | Verification must cover direct and masked writes of DATA_OUT and DATA_OE and their reads, and the per-pin register view. *(when: in each configuration of the run set)* | 9:s1 (p1127) |
| GP-9-03 | MUST | system | scenario | Verification must cover DATA_IN with and without the input filter. *(when: in each configuration of the run set)* | 9:s1 (p1127) |
| GP-9-04 | MUST | system | scenario | Verification must cover interrupt detection on rising edge, falling edge, high level and low level, with INTR_STATE, INTR_ENABLE and INTR_TEST. *(when: in each configuration of the run set)* | 9:s1 (p1127) |
| GP-9-05 | MUST | system | scenario | Verification must cover strap sampling with HW_STRAPS_DATA_IN_VALID and HW_STRAPS_DATA_IN. *(when: in each configuration of the run set)* | 9:s1 (p1127) |
| GP-9-06 | MUST | system | scenario | Verification must cover bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the fatal_fault alert. *(when: in each configuration of the run set)* | 9:s1 (p1127) |
| GP-9-07 | MUST | slave | scenario | The per-pin registers of all 32 GPIOs must behave alike. *(when: per-pin registers of the 32 GPIOs)* | 9:s2 (p1135) |
| GP-9-08 | MAY | system | none | Verification may check every GPIO for the 32-bit registers and only a selection of GPIOs for per-pin registers. *(when: verifying 32-bit registers versus per-pin registers)* | 9:s3 (p1135) |
| GP-9-09 | MUST | system | none | The selection of GPIOs must include GPIO[0], GPIO[15], GPIO[16] and GPIO[31]. *(when: when only a selection of GPIOs is checked for per-pin registers)* | 9:s3 (p1135) |

## 10 Decisions for verification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| GP-10-01 | MUST | slave | scenario | DATA_OE[i] is set to data bit i where mask bit i is 1 and every other DATA_OE bit is left unchanged, as for DATA_OUT. *(when: write to MASKED_OE_LOWER or MASKED_OE_UPPER)* | 10:s4 (p1148) |
| GP-10-02 | MUST | slave | scenario | Bits 15:0 of the read return the corresponding half of DATA_OUT or DATA_OE; bits 31:16 of MASKED_OUT_* read 0. *(when: read of MASKED_OUT_* or MASKED_OE_*)* | 10:s5 (p1149) |
| GP-10-03 | MUST | slave | both | DIRECT_OUT, DIRECT_OE, MASKED_*, INTR_CTRL_EN_*, CTRL_EN_INPUT_FILTER, PER_PIN_OE_i, PER_PIN_INTR_CTRL_i and PER_PIN_IO_i.data_out read 0; o_gpio and o_gpio_en are 0. *(when: after reset and until written; o_gpio and o_gpio_en also while rst_ni = 0)* | 10:s6 (p1150) |
| GP-10-04 | MUST | slave | scenario | A configured event sets INTR_STATE[i]. *(when: INTR_ENABLE[i] = 1 and a configured event occurs)* | 10:s7 (p1151) |
| GP-10-05 | MUST | slave | both | o_intr_gpio[i] stays 0. *(when: INTR_ENABLE[i] = 0)* | 10:s7 (p1151) |
| GP-10-06 | MUST | slave | scenario | INTR_STATE[i] reads 1 and o_intr_gpio[i] with INTR_ENABLE[i] = 1 is 1 again within 4 cycles after the write response. *(when: level condition still holds after write of 1 to INTR_STATE[i])* | 10:s8 (p1152) |
| GP-10-07 | MUST | slave | scenario | The new value never appears in DATA_IN[i] and creates no interrupt event. *(when: CTRL_EN_INPUT_FILTER[i] = 1 and new i_gpio[i] value held at most 12 cycles)* | 10:s10 (p1154) |
| GP-10-08 | MUST | slave | scenario | The new value appears in DATA_IN[i] no later than 24 cycles after the change. *(when: CTRL_EN_INPUT_FILTER[i] = 1 and new i_gpio[i] value held at least 24 cycles)* | 10:s10 (p1154) |
| GP-10-09 | MUST | master | scenario | Tests keep i_gpio[i] constant; DATA_IN[i] and interrupt events are not checked in this window. *(when: after a write that changes CTRL_EN_INPUT_FILTER[i], for 24 cycles)* | 10:s10 (p1154) |
| GP-10-10 | MUST | master | scenario | Tests keep i_strap_en = 0 while rst_ni = 0 and at least 4 cycles after release, raise it once, and keep i_gpio constant from 24 cycles before to 8 cycles after the rising edge. *(when: GpioAsHwStrapsEn = 1)* | 10:s11 (p1155) |
| GP-10-11 | MUST | slave | both | HW_STRAPS_DATA_IN_VALID reads 1, o_straps_valid = 1, and HW_STRAPS_DATA_IN and o_straps_data equal the sampled i_gpio value. *(when: GpioAsHwStrapsEn = 1, within 4 cycles after the i_strap_en rising edge)* | 10:s11 (p1155) |
| GP-10-12 | MUST | slave | both | Both valid indications are 0. *(when: GpioAsHwStrapsEn = 1, before the i_strap_en rising edge)* | 10:s11 (p1155) |
| GP-10-13 | MUST | slave | both | Later changes of i_gpio or i_strap_en change neither the valid indications nor the strap data. *(when: GpioAsHwStrapsEn = 1, after strap sampling until reset)* | 10:s11 (p1155) |
| GP-10-14 | MUST | slave | both | HW_STRAPS_DATA_IN reads 0 at all times. *(when: GpioAsHwStrapsEn = 0)* | 10:s12 (p1156) |
| GP-10-15 | MUST | master | scenario | Tests write 0x8000_0001 to keep regwen at 1 and do not use the combined write 0x0000_0001. *(when: tests that trigger an alert)* | 10:s13 (p1157) |
| GP-10-16 | MUST | slave | scenario | A write of 0x8000_0001 completes with d_error = 0, triggers no alert, and regwen still reads 0. *(when: after a write with bit 31 = 0 sets regwen to 0, until reset)* | 10:s13 (p1157) |
| GP-10-17 | MUST | slave | both | Exactly one o_alert pulse occurs, no later than 16 cycles after the write response. *(when: one write of 1 to fatal_fault, no other alert cause and no other such write within 32 cycles)* | 10:s13 (p1157) |
| GP-10-18 | MUST | slave | scenario | ALERT_TEST reads 0x8000_0000. *(when: after reset)* | 10:s13 (p1157) |
| GP-10-19 | MUST_NOT | master | scenario | Tests do not use a write with i_a_instr = 1; d_error of a request with i_a_instr = 1 is not checked. | 10:s14 (p1158) |
| GP-10-20 | MUST | slave | scenario | The response has d_error = 1 and no register changes. *(when: request to an unmapped offset in 0x000..0x3FF)* | 10:s15 (p1159) |
| GP-10-21 | MUST_NOT | master | none | Requests at offset 0x400 and above are not used. | 10:s15 (p1159) |
| GP-10-22 | MUST | slave | scenario | The write returns d_error = 1 and changes nothing. *(when: aligned byte write (a_size 0, mask 0001) to INTR_*, DIRECT_*, MASKED_*, INTR_CTRL_EN_*, CTRL_EN_INPUT_FILTER or PER_PIN_IO_i)* | 10:s16 (p1160) |
| GP-10-23 | MUST | slave | scenario | The write completes with d_error = 0 and has the effect of the write. *(when: aligned byte write (a_size 0, mask 0001) to PER_PIN_OE_i or PER_PIN_INTR_CTRL_i)* | 10:s16 (p1160) |
| GP-10-24 | MUST | slave | scenario | The write succeeds. *(when: full-word write with mask 1111)* | 10:s16 (p1160) |
| GP-10-25 | MUST | slave | scenario | The read returns the full register. *(when: read of any size)* | 10:s16 (p1160) |
| GP-10-26 | MUST | master | scenario | The test bench matches responses by d_source, uses a distinct a_source per outstanding request, and does not assume o_a_ready = 1. *(when: multiple outstanding requests)* | 10:s17 (p1161) |
| GP-10-27 | MUST | slave | both | d_source echoes a_source, d_size echoes a_size, and d_opcode is AccessAckData for Get and AccessAck for PutFullData and PutPartialData. *(when: response)* | 10:s18 (p1162) |
| GP-10-28 | MUST | slave | scenario | d_error = 1. *(when: undefined opcode)* | 10:s18 (p1162) |
| GP-10-29 | MUST | slave | scenario | d_data is checked. *(when: Get without error)* | 10:s18 (p1162) |
| GP-10-30 | MUST | master | assertion | The test bench keeps i_a_valid = 0 while rst_ni = 0 and in the first cycle after release. | 10:s19 (p1163) |
| GP-10-31 | MUST | slave | assertion | o_d_valid, o_alert, o_alert_integ_fail, o_intr_gpio, o_gpio and o_gpio_en are 0. *(when: rst_ni = 0)* | 10:s19 (p1163) |
| GP-10-32 | MUST | slave | scenario | The pending response is discarded. *(when: response pending at reset)* | 10:s19 (p1163) |
| GP-10-33 | MUST | slave | assertion | o_d_intg_err and o_alert_integ_fail are 0 in every cycle. *(when: rst_ni = 1)* | 10:s20 (p1164) |
| GP-10-34 | MUST | slave | both | o_alert pulses no later than 16 cycles later and then at least once in every 32 cycles until rst_ni is asserted. *(when: request with i_a_intg_flip = 1 accepted)* | 10:s20 (p1164) |
| GP-10-35 | MUST | slave | both | DATA_IN[i] shows the change no later than 4 cycles after the first rising edge after the change, for both values of GpioAsyncOn. *(when: filter off, i_gpio[i] change held at least 8 cycles)* | 10:s21 (p1165) |
| GP-10-36 | MUST | slave | both | INTR_STATE[i] is set no later than 4 cycles after it. *(when: configured event appears in DATA_IN[i])* | 10:s21 (p1165) |
| GP-10-37 | MUST | slave | assertion | o_intr_gpio[i] equals INTR_STATE[i] AND INTR_ENABLE[i]. *(when: except in the 2 cycles after INTR_STATE or INTR_ENABLE changes)* | 10:s21 (p1165) |
| GP-10-38 | MUST | slave | both | o_gpio and o_gpio_en equal DATA_OUT and DATA_OE no later than 2 cycles after the write response. *(when: after a write that changed DATA_OUT or DATA_OE)* | 10:s21 (p1165) |
| GP-10-39 | MUST | slave | scenario | The register or field is left unchanged. *(when: write to a ro register or field (DATA_IN, HW_STRAPS_*, PER_PIN_IO_i.data_in))* | 10:s22 (p1166) |
| GP-10-40 | MUST | slave | scenario | The read returns 0. *(when: read of a wo field (INTR_TEST, MASKED_OUT_* mask, ALERT_TEST.fatal_fault))* | 10:s22 (p1166) |
| GP-10-41 | MUST | slave | scenario | Reserved bits read 0 and writes to them have no effect. *(when: reserved bits)* | 10:s22 (p1166) |
| GP-10-42 | MUST | slave | scenario | INTR_CTRL_EN_LVLLOW and INTR_CTRL_EN_LVLHIGH enable level detection, not edge detection. | 10:s23 (p1167) |
| GP-10-43 | MUST | slave | scenario | DATA_IN[i] follows i_gpio[i], not o_gpio[i]. *(when: o_gpio_en[i] = 1)* | 10:s24 (p1168) |
| GP-10-44 | MUST | master | scenario | Tests drive i_a_param = 0. | 10:s25 (p1169) |
