<!-- gpio specification for NNC Pipeline: the OpenTitan gpio documents below, concatenated in this order,
     from lowRISC/opentitan commit ee811654ff1a1431781504554a36490c2f77d6b1 (hw/top_earlgrey/ip_autogen/gpio). Text unchanged except that
     (1) the regression-badge block at the top of README.md is removed, and (2) in doc/registers.md the sections
     PER_PIN_OE_1 to PER_PIN_OE_31 and PER_PIN_INTR_CTRL_1 to PER_PIN_INTR_CTRL_31 are replaced by one note: they
     are identical to PER_PIN_OE_0 and PER_PIN_INTR_CTRL_0 with the GPIO index i in place of 0, at the offsets of
     the Summary table. Licence: Apache-2.0 (see ../NOTICE.md).
     The last part, "ot_gpio_nnc: integration of the OpenTitan gpio for verification", is not from
     OpenTitan: it was written for NNC Pipeline and describes the verification wrapper. -->

<!-- Source: hw/top_earlgrey/ip_autogen/gpio/README.md -->

# GPIO HWIP Technical Specification

# Overview

This document specifies GPIO hardware IP functionality. This
module conforms to the [Comportable guideline for peripheral device
functionality](../../../../doc/contributing/hw/comportability/README.md)
See that document for integration overview within the broader top
level system.

## Features

- 32 GPIO ports
- Configurable interrupt per GPIO for detecting rising edge, falling edge,
  or active low/high input
- Two ways to update GPIO output: direct-write and masked (thread-safe) update
- Second, per-pin register view to assign individual GPIOs to different software
  components, e.g., CHERIoT compartments

## Description

The GPIO block allows software to communicate through general purpose I/O
pins in a flexible manner. Each of 32 independent bits can be written
as peripheral outputs in two modes. Each of the 32 bits can be read
by software as peripheral inputs.  How these peripheral inputs and
outputs are connected to the chip IO is not within the scope of this
document. See the Comportability Specification for peripheral IO options
at the top chip level.

In the output direction, this module provides direct 32b access to each
GPIO value using direct write. This mode allows software to control all
GPIO bits simultaneously. Alternately, this module provides masked writes
to half of the bits at a time, allowing software to affect the output
value of a subset of the bits without requiring a read-modify-write.
In this mode the user provides a mask of which of the 16 bits are to be
modified, along with their new value. The details of this mode are given
in the [Programmers Guide](#programmers-guide) below.

In the input direction, software can read the contents of any of the GPIO
peripheral inputs.  In addition, software can request the detection of an
interrupt event for any of the 32 bits in a configurable manner.  The choices
are positive edge, negative edge or level detection events. A noise
filter is available through configuration for any of the 32 GPIO inputs.
This requires the input to be stable for 16 cycles of the
module clock before the input register reflects the change and interrupt
generation is evaluated. Note that if the filter is enabled and the pin
is set to output then there will be a corresponding delay in a change
in output value being reflected in the input register.

See the Design Details section for more details on the features.

<!-- Source: hw/top_earlgrey/ip_autogen/gpio/doc/theory_of_operation.md -->

# Theory of Operation

## Block Diagram

![GPIO Block Diagram](../doc/gpio_blockdiagram.svg)

The block diagram above shows the `DATA_OUT` and `DATA_OE` registers
managed by hardware outside of the auto-generated register file.
For reference, it also shows the assumed connections to pads in
the top level netlist.

## Design Details

### GPIO Output logic

![GPIO Output Diagram](../doc/gpio_output.svg)

The GPIO module maintains one 32-bit output register `DATA_OUT` with two
ways to write to it. Direct write access uses [`DIRECT_OUT`](registers.md#direct_out), and
masked access uses [`MASKED_OUT_UPPER`](registers.md#masked_out_upper) and
[`MASKED_OUT_LOWER`](registers.md#masked_out_lower). Direct access provides full write and read
access for all 32 bits in one register.

For masked access the bits to modify are given as a mask in the upper
16 bits of the [`MASKED_OUT_UPPER`](registers.md#masked_out_upper) and
[`MASKED_OUT_LOWER`](registers.md#masked_out_lower) register write, while the data to write is
provided in the lower 16 bits of the register write.  The hardware updates
`DATA_OUT` with the mask so that the modification is done without software
requiring a Read-Modify-Write.

Reads of masked registers return the lower/upper 16 bits of the `DATA_OUT`
contents. Zeros are returned in the upper 16 bits (mask field). To read
what is on the pins, software should read the [`DATA_IN`](registers.md#data_in) register.
(See [GPIO Input](#gpio-input) section below).

The same concept is duplicated for the output enable register `DATA_OE`.
Direct access uses [`DIRECT_OE`](registers.md#direct_oe), and masked access is available
using [`MASKED_OE_UPPER`](registers.md#masked_oe_upper) and [`MASKED_OE_LOWER`](registers.md#masked_oe_lower).

The output enable is sent to the pad control block to determine if the
pad should drive the `DATA_OUT` value to the associated pin or not.

A typical use pattern is for initialization and suspend/resume code to
use the full access registers to set the output enables and current output
values, then switch to masked access for both `DATA_OUT` and `DATA_OE`.

For GPIO outputs that are not used (either not wired to a pin output or
not selected for pin multiplexing), the output values are disconnected
and have no effect on the GPIO input, regardless of output enable values.

### Per-Pin Register View

In addition to the 32-bit registers, which group the GPIOs by function, the GPIO module provides a second register view that groups them by pin.
This view allows assigning individual GPIOs to different software components, for example to CHERIoT compartments, by granting each component access to only the registers of its GPIOs.
Both views alias the same state, and a write to a per-pin register only affects the GPIO it belongs to.

The per-pin view consists of two separate, aligned address ranges, so access to the data of a GPIO can be granted without access to its configuration:

- [`PER_PIN_IO`](registers.md#per_pin_io) holds one register per GPIO with bit i of `DATA_OUT` and of [`DATA_IN`](registers.md#data_in).
- The configuration range holds two registers per GPIO, which directly follow one another: [`PER_PIN_OE_0`](registers.md#per_pin_oe_0) with bit 0 of `DATA_OE`, [`PER_PIN_INTR_CTRL_0`](registers.md#per_pin_intr_ctrl_0) with bit 0 of the interrupt control and input filter registers, then `PER_PIN_OE_1`, `PER_PIN_INTR_CTRL_1`, and so on.

A register write must cover all bytes of the register that hold a field, so access cannot be granted to only some fields of a register.
The output enable and the interrupt configuration of a GPIO are therefore in separate registers, so access to one can be granted without the other.

The interrupt registers [`INTR_STATE`](registers.md#intr_state), [`INTR_ENABLE`](registers.md#intr_enable) and [`INTR_TEST`](registers.md#intr_test) have no per-pin view.
Like the interrupt controller, they are expected to be managed by a trusted software component, for example a trusted CHERIoT compartment, which handles the GPIO interrupts on behalf of the components owning the GPIOs.

### GPIO Input

The [`DATA_IN`](registers.md#data_in) register returns the contents as seen on the
peripheral input, typically from the pads connected to those inputs.  In the
presence of a pin-multiplexing unit, GPIO peripheral inputs that are
not connected to a chip input will be tied to a constant zero input.

The GPIO module provides optional independent noise filter control for each of the 32 input signals.
Each input can be independently enabled with the [`CTRL_EN_INPUT_FILTER`](registers.md#ctrl_en_input_filter) (one bit per input).
This 16-cycle filter is applied to both the [`DATA_IN`](registers.md#data_in) register and the interrupt detection logic.
The timing for [`DATA_IN`](registers.md#data_in) is still not instantaneous if [`CTRL_EN_INPUT_FILTER`](registers.md#ctrl_en_input_filter) is false as there is still both top-level routing delay and input CDC synchronizer delay involved.
The top-level routing delay depends on the physical layout of the chip.
The input synchronizer adds two flops between the chip input and the [`DATA_IN`](registers.md#data_in) register, though the added delay may vary by up to one GPIO clock cycle depending on when cycle each external input transition arrives relative to the GPIO clock.

The contents of [`DATA_IN`](registers.md#data_in) are always readable and reflect the value seen at the chip input pad regardless of the output enable setting from DATA_OE.
If the output enable is true (and the GPIO is connected to a chip-level pad), the value read from [`DATA_IN`](registers.md#data_in) includes the effect of the peripheral's driven output and will only differ from DATA_OUT if the output driver is unable to switch the pin or during the delay imposed by the input synchronizer and noise filter (if enabled).

#### GPIO Inputs as HW Straps

The GPIO controller provides an optional feature to sample GPIO input values as hardware configuration straps.
After each reset, on the first cycle when the `strap_en_i` signal is asserted, the GPIO detects its transition from low to high.
One clock cycle later, it samples the GPIO input values and stores them in the `HW_STRAPS_DATA_IN` register.
The `strap_en_i` signal transition from low to high is expected only once after the reset process.
Sampling occurs exclusively at this time, and any subsequent changes to the GPIO input configuration will not be captured.
This mechanism samples all 32 bits of the GPIO input data, regardless of the GPIO output enable status, providing a reliable snapshot of the input values for firmware access.


### Interrupts

The GPIO module provides 32 interrupt signals to the main processor.
Each interrupt can be independently enabled, tested, and configured.
Following the standard interrupt guidelines in the [Comportability
Specification](../../../../../doc/contributing/hw/comportability/README.md),
the 32 bits of the [`INTR_ENABLE`](registers.md#intr_enable) register determines whether the
associated inputs are configured to detect interrupt events. If enabled
via the various `INTR_CTRL_EN` registers, their current state can be
read in the [`INTR_STATE`](registers.md#intr_state) register. Clearing is done by writing a
`1` into the associated [`INTR_STATE`](registers.md#intr_state) bit field.

For configuration, there are 4 types of interrupts available per bit,
controlled with four control registers. [`INTR_CTRL_EN_RISING`](registers.md#intr_ctrl_en_rising)
configures the associated input for rising-edge detection.
Similarly, [`INTR_CTRL_EN_FALLING`](registers.md#intr_ctrl_en_falling) detects falling edge inputs.
[`INTR_CTRL_EN_LVLHIGH`](registers.md#intr_ctrl_en_lvlhigh) and [`INTR_CTRL_EN_LVLLOW`](registers.md#intr_ctrl_en_lvllow)
allow the input to be level sensitive interrupts. In theory an input can be
configured to detect both a rising and falling edge, but there is no hardware
assistance to indicate which edge caused the output interrupt.

**Note #1:** The interrupt can only be triggered by GPIO input.
**Note #2:** All inputs are sent through optional noise filtering before being sent into interrupt detection.
**Note #3:** All interrupts to the processor are level interrupts as per the Comportability Specification guidelines.
The GPIO module, if configured, converts an edge detection into a level interrupt to the processor core.

<!-- Source: hw/top_earlgrey/ip_autogen/gpio/doc/programmers_guide.md -->

# Programmer's Guide

## Initialization

Initialization of the GPIO module includes the setting up of the interrupt
configuration for each GPIO input, as well as the configuration of
the required noise filtering. These do not provide masked access since
they are not expected to be done frequently.

```cpp
// enable inputs 0 and 1 for rising edge detection with filtering,
// inputs 2 and 3 for falling edge detection with filtering,
// input 4 for both rising edge detection (no filtering)
// and inputs 6 and 7 for active low interrupt detection
*GPIO_INTR_ENABLE =          0b11011111;
*GPIO_INTR_CTRL_EN_RISING =  0b00010011;
*GPIO_INTR_CTRL_EN_FALLING = 0b00011100;
*GPIO_INTR_CTRL_EN_LVLLOW  = 0b11000000;
*GPIO_INTR_CTRL_EN_LVLHIGH = 0b00000000;
*GPIO_CTRL_EN_INPUT_FILTER = 0b00001111;
```

## Common Examples

This section below shows the interaction between the direct access
and mask access for data output and data enable.

```cpp
// assume all GPIO are connected to chip pads.
// assume a weak pullup on all pads, returning 1 if undriven.
printf("0x%x", *GPIO_DATA_IN);          // 0xffffffff

*DIRECT_OUT = 0x11223344;
printf("0x%x", *GPIO_DIRECT_OUT);       // 0x11223344

*DIRECT_OE  = 0x00ff00ff;
printf("0x%x", *GPIO_DIRECT_OE);        // 0x00ff00ff

// weak pullup still applies to undriven signals
printf("0x%x", *GPIO_DATA_IN);          // 0xff22ff44

// read of direct_out still returns DATA_OUT contents
printf("0x%x", *GPIO_DIRECT_OUT);       // 0x11223344

// try masked accesses to DATA_OUT
*GPIO_MASKED_OUT_LOWER = 0x0f0f5566
printf("0x%x", *GPIO_MASKED_OUT_LOWER); // 0x00003546
printf("0x%x", *GPIO_DIRECT_OUT);       // 0x11223546

*GPIO_MASKED_OUT_UPPER = 0x0f0f7788
printf("0x%x", *GPIO_MASKED_OUT_UPPER); // 0x00001728
printf("0x%x", *GPIO_DIRECT_OUT);       // 0x17283546

// OE still applies
printf("0x%x", *GPIO_DATA_IN);          // 0xff28ff46

// manipulate OE
*GPIO_DIRECT_OE = 0xff00ff00;
printf("0x%x", *GPIO_DIRECT_OE);        // 0xff00ff00
printf("0x%x", *GPIO_DATA_IN);          // 0x17ff35ff

*GPIO_MASKED_OE_LOWER = 0x0f0f0f0f;
printf("0x%x", *GPIO_MASKED_OE_LOWER);  // 0x00000f0f
printf("0x%x", *GPIO_DIRECT_OE);        // 0xff000f0f
printf("0x%x", *GPIO_DATA_IN);          // 0x17fff5f6

*GPIO_MASKED_OE_UPPER = 0x0f0f0f0f;
printf("0x%x", *GPIO_MASKED_OE_UPPER);  // 0x00000f0f
printf("0x%x", *GPIO_DIRECT_OE);        // 0x0f0f0f0f
printf("0x%x", *GPIO_DATA_IN);          // 0xf7f8f5f6
```

## Interrupt Handling

This section below gives an example of how interrupt clearing works,
assuming some events have occurred as shown in comments.

```cpp
*INTR_ENABLE = 0x000000ff;              // interrupts enabled GPIO[7:0] inputs
printf("0b%x", *GPIO_DATA_IN);          // assume 0b00000000
printf("0b%x", *GPIO_INTR_STATE);       // 0b00000000

*INTR_CTRL_EN_RISING  = 0b00010001;     // rising detect on GPIO[0], GPIO[4]
*INTR_CTRL_EN_FALLING = 0b00010010;     // falling detect on GPIO[1], GPIO[4]
*INTR_CTRL_EN_LVLLOW  = 0b00001100;     // falling detect on GPIO[2], GPIO[3]
*INTR_CTRL_EN_LVLHIGH = 0b11000000;     // falling detect on GPIO[6], GPIO[7]

// already detected intr[3,2] (level low)
printf("0b%b", *GPIO_INTR_STATE);       // 0b00001100

// try and clear [3:2], fails since still active low
*GPIO_INTR_STATE = 0b00001100;
printf("0b%b", *GPIO_INTR_STATE);       // 0b00001100

// EVENT: all bits [7:0] rising, triggers [7,6,4,0], [3,2] still latched
printf("0b%b", *GPIO_DATA_IN);          // 0b11111111
printf("0b%b", *GPIO_INTR_STATE);       // 0b11011101

// try and clear all bits, [7,6] still detecting level high
*GPIO_INTR_STATE = 0b11111111;
printf("0b%b", *GPIO_INTR_STATE);       // 0b11000000

// EVENT: all bits [7:0] falling, triggers [4,3,2,1], [7,6] still latched
printf("0b%b", *GPIO_DATA_IN);          // 0b00000000
printf("0b%b", *GPIO_INTR_STATE);       // 0b11011110

// try and clear all bits, [3,2] still detecting level low
*GPIO_INTR_STATE = 0b11111111;
printf("0b%b", *GPIO_INTR_STATE);       // 0b00001100

// write test register for all 8 events, trigger regardless of external events
*GPIO_INTR_TEST = 0b11111111;
printf("0b%b", *GPIO_INTR_STATE);       // 0b11111111

// try and clear all bits, [3,2] still detecting level low
*GPIO_INTR_STATE = 0b11111111;
printf("0b%b", *GPIO_INTR_STATE);       // 0b00001100

```

## Per-Pin Register View

Use the per-pin register view when individual GPIOs belong to different software components, for example CHERIoT compartments.
Grant each component access to only the per-pin registers of its GPIOs, and keep using the 32-bit registers in software that manages all GPIOs, for example during initialization.
The per-pin registers of GPIO i are:

- `PER_PIN_IO_i` at offset `0x100 + 4 * i`: `data_out` in bit 0 and the read-only `data_in` in bit 8.
- `PER_PIN_OE_i` at offset `0x200 + 8 * i`: `oe` in bit 0.
- `PER_PIN_INTR_CTRL_i` at offset `0x204 + 8 * i`: the rising-edge, falling-edge, level-high and level-low interrupt enables in bits 0 to 3, and the input filter enable in bit 4.

`PER_PIN_IO_i` has fields in bytes 0 and 1, so a write to it must cover both bytes, i.e., be at least 16 bits wide.
A byte write returns an error and has no effect, so a capability for `PER_PIN_IO_i` must cover at least these two bytes.
`PER_PIN_OE_i` and `PER_PIN_INTR_CTRL_i` also accept byte writes.

The interrupt registers `INTR_STATE`, `INTR_ENABLE` and `INTR_TEST` have no per-pin view.
They are expected to be managed by a trusted component, which handles the GPIO interrupts on behalf of the components owning the GPIOs.

```cpp
// GPIO 5: drive a 1
*GPIO_PER_PIN_OE_5 = 0x1;
*GPIO_PER_PIN_IO_5 = 0x1;                     // 16- or 32-bit write, a byte write errors

// GPIO 9: filtered input with a rising-edge interrupt
*GPIO_PER_PIN_INTR_CTRL_9 = 0x11;             // bit 4: filter, bit 0: rising edge
printf("%d", (*GPIO_PER_PIN_IO_9 >> 8) & 0x1); // data_in of GPIO 9
```

## Device Interface Functions (DIFs)

- [Device Interface Functions](../../../../../sw/device/lib/dif/dif_gpio.h)

<!-- Source: hw/top_earlgrey/ip_autogen/gpio/doc/registers.md -->

# Registers

<!-- BEGIN CMDGEN util/regtool.py -d ./hw/top_earlgrey/ip_autogen/gpio/data/gpio.hjson -->
## Summary

| Name                                                       | Offset   |   Length | Description                                                                       |
|:-----------------------------------------------------------|:---------|---------:|:----------------------------------------------------------------------------------|
| gpio.[`INTR_STATE`](#intr_state)                           | 0x0      |        4 | Interrupt State Register                                                          |
| gpio.[`INTR_ENABLE`](#intr_enable)                         | 0x4      |        4 | Interrupt Enable Register                                                         |
| gpio.[`INTR_TEST`](#intr_test)                             | 0x8      |        4 | Interrupt Test Register                                                           |
| gpio.[`ALERT_TEST`](#alert_test)                           | 0xc      |        4 | Alert Test Register                                                               |
| gpio.[`DATA_IN`](#data_in)                                 | 0x10     |        4 | GPIO Input data read value                                                        |
| gpio.[`DIRECT_OUT`](#direct_out)                           | 0x14     |        4 | GPIO direct output data write value                                               |
| gpio.[`MASKED_OUT_LOWER`](#masked_out_lower)               | 0x18     |        4 | GPIO write data lower with mask.                                                  |
| gpio.[`MASKED_OUT_UPPER`](#masked_out_upper)               | 0x1c     |        4 | GPIO write data upper with mask.                                                  |
| gpio.[`DIRECT_OE`](#direct_oe)                             | 0x20     |        4 | GPIO Output Enable.                                                               |
| gpio.[`MASKED_OE_LOWER`](#masked_oe_lower)                 | 0x24     |        4 | GPIO write Output Enable lower with mask.                                         |
| gpio.[`MASKED_OE_UPPER`](#masked_oe_upper)                 | 0x28     |        4 | GPIO write Output Enable upper with mask.                                         |
| gpio.[`INTR_CTRL_EN_RISING`](#intr_ctrl_en_rising)         | 0x2c     |        4 | GPIO interrupt enable for GPIO, rising edge.                                      |
| gpio.[`INTR_CTRL_EN_FALLING`](#intr_ctrl_en_falling)       | 0x30     |        4 | GPIO interrupt enable for GPIO, falling edge.                                     |
| gpio.[`INTR_CTRL_EN_LVLHIGH`](#intr_ctrl_en_lvlhigh)       | 0x34     |        4 | GPIO interrupt enable for GPIO, level high.                                       |
| gpio.[`INTR_CTRL_EN_LVLLOW`](#intr_ctrl_en_lvllow)         | 0x38     |        4 | GPIO interrupt enable for GPIO, level low.                                        |
| gpio.[`CTRL_EN_INPUT_FILTER`](#ctrl_en_input_filter)       | 0x3c     |        4 | filter enable for GPIO input bits.                                                |
| gpio.[`HW_STRAPS_DATA_IN_VALID`](#hw_straps_data_in_valid) | 0x40     |        4 | Indicates whether the data in [`HW_STRAPS_DATA_IN`](#hw_straps_data_in) is valid. |
| gpio.[`HW_STRAPS_DATA_IN`](#hw_straps_data_in)             | 0x44     |        4 | GPIO input data that was sampled as straps at most once after the block           |
| gpio.[`PER_PIN_IO_0`](#per_pin_io)                         | 0x100    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_1`](#per_pin_io)                         | 0x104    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_2`](#per_pin_io)                         | 0x108    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_3`](#per_pin_io)                         | 0x10c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_4`](#per_pin_io)                         | 0x110    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_5`](#per_pin_io)                         | 0x114    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_6`](#per_pin_io)                         | 0x118    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_7`](#per_pin_io)                         | 0x11c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_8`](#per_pin_io)                         | 0x120    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_9`](#per_pin_io)                         | 0x124    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_10`](#per_pin_io)                        | 0x128    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_11`](#per_pin_io)                        | 0x12c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_12`](#per_pin_io)                        | 0x130    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_13`](#per_pin_io)                        | 0x134    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_14`](#per_pin_io)                        | 0x138    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_15`](#per_pin_io)                        | 0x13c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_16`](#per_pin_io)                        | 0x140    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_17`](#per_pin_io)                        | 0x144    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_18`](#per_pin_io)                        | 0x148    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_19`](#per_pin_io)                        | 0x14c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_20`](#per_pin_io)                        | 0x150    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_21`](#per_pin_io)                        | 0x154    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_22`](#per_pin_io)                        | 0x158    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_23`](#per_pin_io)                        | 0x15c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_24`](#per_pin_io)                        | 0x160    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_25`](#per_pin_io)                        | 0x164    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_26`](#per_pin_io)                        | 0x168    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_27`](#per_pin_io)                        | 0x16c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_28`](#per_pin_io)                        | 0x170    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_29`](#per_pin_io)                        | 0x174    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_30`](#per_pin_io)                        | 0x178    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_IO_31`](#per_pin_io)                        | 0x17c    |        4 | Per-pin view of the output and input data of one GPIO.                            |
| gpio.[`PER_PIN_OE_0`](#per_pin_oe_0)                       | 0x200    |        4 | Per-pin view of the output enable of GPIO[0].                                     |
| gpio.[`PER_PIN_INTR_CTRL_0`](#per_pin_intr_ctrl_0)         | 0x204    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[0].  |
| gpio.[`PER_PIN_OE_1`](#per_pin_oe_1)                       | 0x208    |        4 | Per-pin view of the output enable of GPIO[1].                                     |
| gpio.[`PER_PIN_INTR_CTRL_1`](#per_pin_intr_ctrl_1)         | 0x20c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[1].  |
| gpio.[`PER_PIN_OE_2`](#per_pin_oe_2)                       | 0x210    |        4 | Per-pin view of the output enable of GPIO[2].                                     |
| gpio.[`PER_PIN_INTR_CTRL_2`](#per_pin_intr_ctrl_2)         | 0x214    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[2].  |
| gpio.[`PER_PIN_OE_3`](#per_pin_oe_3)                       | 0x218    |        4 | Per-pin view of the output enable of GPIO[3].                                     |
| gpio.[`PER_PIN_INTR_CTRL_3`](#per_pin_intr_ctrl_3)         | 0x21c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[3].  |
| gpio.[`PER_PIN_OE_4`](#per_pin_oe_4)                       | 0x220    |        4 | Per-pin view of the output enable of GPIO[4].                                     |
| gpio.[`PER_PIN_INTR_CTRL_4`](#per_pin_intr_ctrl_4)         | 0x224    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[4].  |
| gpio.[`PER_PIN_OE_5`](#per_pin_oe_5)                       | 0x228    |        4 | Per-pin view of the output enable of GPIO[5].                                     |
| gpio.[`PER_PIN_INTR_CTRL_5`](#per_pin_intr_ctrl_5)         | 0x22c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[5].  |
| gpio.[`PER_PIN_OE_6`](#per_pin_oe_6)                       | 0x230    |        4 | Per-pin view of the output enable of GPIO[6].                                     |
| gpio.[`PER_PIN_INTR_CTRL_6`](#per_pin_intr_ctrl_6)         | 0x234    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[6].  |
| gpio.[`PER_PIN_OE_7`](#per_pin_oe_7)                       | 0x238    |        4 | Per-pin view of the output enable of GPIO[7].                                     |
| gpio.[`PER_PIN_INTR_CTRL_7`](#per_pin_intr_ctrl_7)         | 0x23c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[7].  |
| gpio.[`PER_PIN_OE_8`](#per_pin_oe_8)                       | 0x240    |        4 | Per-pin view of the output enable of GPIO[8].                                     |
| gpio.[`PER_PIN_INTR_CTRL_8`](#per_pin_intr_ctrl_8)         | 0x244    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[8].  |
| gpio.[`PER_PIN_OE_9`](#per_pin_oe_9)                       | 0x248    |        4 | Per-pin view of the output enable of GPIO[9].                                     |
| gpio.[`PER_PIN_INTR_CTRL_9`](#per_pin_intr_ctrl_9)         | 0x24c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[9].  |
| gpio.[`PER_PIN_OE_10`](#per_pin_oe_10)                     | 0x250    |        4 | Per-pin view of the output enable of GPIO[10].                                    |
| gpio.[`PER_PIN_INTR_CTRL_10`](#per_pin_intr_ctrl_10)       | 0x254    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[10]. |
| gpio.[`PER_PIN_OE_11`](#per_pin_oe_11)                     | 0x258    |        4 | Per-pin view of the output enable of GPIO[11].                                    |
| gpio.[`PER_PIN_INTR_CTRL_11`](#per_pin_intr_ctrl_11)       | 0x25c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[11]. |
| gpio.[`PER_PIN_OE_12`](#per_pin_oe_12)                     | 0x260    |        4 | Per-pin view of the output enable of GPIO[12].                                    |
| gpio.[`PER_PIN_INTR_CTRL_12`](#per_pin_intr_ctrl_12)       | 0x264    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[12]. |
| gpio.[`PER_PIN_OE_13`](#per_pin_oe_13)                     | 0x268    |        4 | Per-pin view of the output enable of GPIO[13].                                    |
| gpio.[`PER_PIN_INTR_CTRL_13`](#per_pin_intr_ctrl_13)       | 0x26c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[13]. |
| gpio.[`PER_PIN_OE_14`](#per_pin_oe_14)                     | 0x270    |        4 | Per-pin view of the output enable of GPIO[14].                                    |
| gpio.[`PER_PIN_INTR_CTRL_14`](#per_pin_intr_ctrl_14)       | 0x274    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[14]. |
| gpio.[`PER_PIN_OE_15`](#per_pin_oe_15)                     | 0x278    |        4 | Per-pin view of the output enable of GPIO[15].                                    |
| gpio.[`PER_PIN_INTR_CTRL_15`](#per_pin_intr_ctrl_15)       | 0x27c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[15]. |
| gpio.[`PER_PIN_OE_16`](#per_pin_oe_16)                     | 0x280    |        4 | Per-pin view of the output enable of GPIO[16].                                    |
| gpio.[`PER_PIN_INTR_CTRL_16`](#per_pin_intr_ctrl_16)       | 0x284    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[16]. |
| gpio.[`PER_PIN_OE_17`](#per_pin_oe_17)                     | 0x288    |        4 | Per-pin view of the output enable of GPIO[17].                                    |
| gpio.[`PER_PIN_INTR_CTRL_17`](#per_pin_intr_ctrl_17)       | 0x28c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[17]. |
| gpio.[`PER_PIN_OE_18`](#per_pin_oe_18)                     | 0x290    |        4 | Per-pin view of the output enable of GPIO[18].                                    |
| gpio.[`PER_PIN_INTR_CTRL_18`](#per_pin_intr_ctrl_18)       | 0x294    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[18]. |
| gpio.[`PER_PIN_OE_19`](#per_pin_oe_19)                     | 0x298    |        4 | Per-pin view of the output enable of GPIO[19].                                    |
| gpio.[`PER_PIN_INTR_CTRL_19`](#per_pin_intr_ctrl_19)       | 0x29c    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[19]. |
| gpio.[`PER_PIN_OE_20`](#per_pin_oe_20)                     | 0x2a0    |        4 | Per-pin view of the output enable of GPIO[20].                                    |
| gpio.[`PER_PIN_INTR_CTRL_20`](#per_pin_intr_ctrl_20)       | 0x2a4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[20]. |
| gpio.[`PER_PIN_OE_21`](#per_pin_oe_21)                     | 0x2a8    |        4 | Per-pin view of the output enable of GPIO[21].                                    |
| gpio.[`PER_PIN_INTR_CTRL_21`](#per_pin_intr_ctrl_21)       | 0x2ac    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[21]. |
| gpio.[`PER_PIN_OE_22`](#per_pin_oe_22)                     | 0x2b0    |        4 | Per-pin view of the output enable of GPIO[22].                                    |
| gpio.[`PER_PIN_INTR_CTRL_22`](#per_pin_intr_ctrl_22)       | 0x2b4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[22]. |
| gpio.[`PER_PIN_OE_23`](#per_pin_oe_23)                     | 0x2b8    |        4 | Per-pin view of the output enable of GPIO[23].                                    |
| gpio.[`PER_PIN_INTR_CTRL_23`](#per_pin_intr_ctrl_23)       | 0x2bc    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[23]. |
| gpio.[`PER_PIN_OE_24`](#per_pin_oe_24)                     | 0x2c0    |        4 | Per-pin view of the output enable of GPIO[24].                                    |
| gpio.[`PER_PIN_INTR_CTRL_24`](#per_pin_intr_ctrl_24)       | 0x2c4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[24]. |
| gpio.[`PER_PIN_OE_25`](#per_pin_oe_25)                     | 0x2c8    |        4 | Per-pin view of the output enable of GPIO[25].                                    |
| gpio.[`PER_PIN_INTR_CTRL_25`](#per_pin_intr_ctrl_25)       | 0x2cc    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[25]. |
| gpio.[`PER_PIN_OE_26`](#per_pin_oe_26)                     | 0x2d0    |        4 | Per-pin view of the output enable of GPIO[26].                                    |
| gpio.[`PER_PIN_INTR_CTRL_26`](#per_pin_intr_ctrl_26)       | 0x2d4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[26]. |
| gpio.[`PER_PIN_OE_27`](#per_pin_oe_27)                     | 0x2d8    |        4 | Per-pin view of the output enable of GPIO[27].                                    |
| gpio.[`PER_PIN_INTR_CTRL_27`](#per_pin_intr_ctrl_27)       | 0x2dc    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[27]. |
| gpio.[`PER_PIN_OE_28`](#per_pin_oe_28)                     | 0x2e0    |        4 | Per-pin view of the output enable of GPIO[28].                                    |
| gpio.[`PER_PIN_INTR_CTRL_28`](#per_pin_intr_ctrl_28)       | 0x2e4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[28]. |
| gpio.[`PER_PIN_OE_29`](#per_pin_oe_29)                     | 0x2e8    |        4 | Per-pin view of the output enable of GPIO[29].                                    |
| gpio.[`PER_PIN_INTR_CTRL_29`](#per_pin_intr_ctrl_29)       | 0x2ec    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[29]. |
| gpio.[`PER_PIN_OE_30`](#per_pin_oe_30)                     | 0x2f0    |        4 | Per-pin view of the output enable of GPIO[30].                                    |
| gpio.[`PER_PIN_INTR_CTRL_30`](#per_pin_intr_ctrl_30)       | 0x2f4    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[30]. |
| gpio.[`PER_PIN_OE_31`](#per_pin_oe_31)                     | 0x2f8    |        4 | Per-pin view of the output enable of GPIO[31].                                    |
| gpio.[`PER_PIN_INTR_CTRL_31`](#per_pin_intr_ctrl_31)       | 0x2fc    |        4 | Per-pin view of the interrupt control and input filter configuration of GPIO[31]. |

## INTR_STATE
Interrupt State Register
- Offset: `0x0`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "gpio", "bits": 32, "attr": ["rw1c"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                 |
|:------:|:------:|:-------:|:-------|:------------------------------------------------------------|
|  31:0  |  rw1c  |   0x0   | gpio   | raised if any of GPIO pin detects configured interrupt mode |

## INTR_ENABLE
Interrupt Enable Register
- Offset: `0x4`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "gpio", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                         |
|:------:|:------:|:-------:|:-------|:------------------------------------------------------------------------------------|
|  31:0  |   rw   |   0x0   | gpio   | Enable interrupt when corresponding bit in [`INTR_STATE.gpio`](#intr_state) is set. |

## INTR_TEST
Interrupt Test Register
- Offset: `0x8`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "gpio", "bits": 32, "attr": ["wo"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                  |
|:------:|:------:|:-------:|:-------|:-----------------------------------------------------------------------------|
|  31:0  |   wo   |   0x0   | gpio   | Write 1 to force corresponding bit in [`INTR_STATE.gpio`](#intr_state) to 1. |

## ALERT_TEST
Alert Test Register
- Offset: `0xc`
- Reset default: `0x80000000`
- Reset mask: `0x80000001`

### Fields

```wavejson
{"reg": [{"name": "fatal_fault", "bits": 1, "attr": ["wo"], "rotate": -90}, {"bits": 30}, {"name": "regwen", "bits": 1, "attr": ["rw0c"], "rotate": -90}], "config": {"lanes": 1, "fontsize": 10, "vspace": 130}}
```

|  Bits  |  Type  |  Reset  | Name        | Description                                            |
|:------:|:------:|:-------:|:------------|:-------------------------------------------------------|
|   31   |  rw0c  |   0x1   | regwen      | Write 0 to disable alert testing until the next reset. |
|  30:1  |        |         |             | Reserved                                               |
|   0    |   wo   |   0x0   | fatal_fault | Write 1 to trigger one alert event of this kind.       |

## DATA_IN
GPIO Input data read value
- Offset: `0x10`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "DATA_IN", "bits": 32, "attr": ["ro"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name    | Description   |
|:------:|:------:|:-------:|:--------|:--------------|
|  31:0  |   ro   |    x    | DATA_IN |               |

## DIRECT_OUT
GPIO direct output data write value
- Offset: `0x14`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "DIRECT_OUT", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name       | Description   |
|:------:|:------:|:-------:|:-----------|:--------------|
|  31:0  |   rw   |    x    | DIRECT_OUT |               |

## MASKED_OUT_LOWER
GPIO write data lower with mask.

Masked write for DATA_OUT[15:0].

Upper 16 bits of this register are used as mask. Writing
lower 16 bits of the register changes DATA_OUT[15:0] value
if mask bits are set.

Read-back of this register returns upper 16 bits as zero
and lower 16 bits as DATA_OUT[15:0].
- Offset: `0x18`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "data", "bits": 16, "attr": ["rw"], "rotate": 0}, {"name": "mask", "bits": 16, "attr": ["wo"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                                     |
|:------:|:------:|:-------:|:-------|:------------------------------------------------------------------------------------------------|
| 31:16  |   wo   |    x    | mask   | Write data mask[15:0]. A value of 1 in mask[i] allows the updating of DATA_OUT[i], 0 <= i <= 15 |
|  15:0  |   rw   |    x    | data   | Write data value[15:0]. Value to write into DATA_OUT[i], valid in the presence of mask[i]==1    |

## MASKED_OUT_UPPER
GPIO write data upper with mask.

Masked write for DATA_OUT[31:16].

Upper 16 bits of this register are used as mask. Writing
lower 16 bits of the register changes DATA_OUT[31:16] value
if mask bits are set.

Read-back of this register returns upper 16 bits as zero
and lower 16 bits as DATA_OUT[31:16].
- Offset: `0x1c`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "data", "bits": 16, "attr": ["rw"], "rotate": 0}, {"name": "mask", "bits": 16, "attr": ["wo"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                                       |
|:------:|:------:|:-------:|:-------|:--------------------------------------------------------------------------------------------------|
| 31:16  |   wo   |    x    | mask   | Write data mask[31:16]. A value of 1 in mask[i] allows the updating of DATA_OUT[i], 16 <= i <= 31 |
|  15:0  |   rw   |    x    | data   | Write data value[31:16]. Value to write into DATA_OUT[i], valid in the presence of mask[i]==1     |

## DIRECT_OE
GPIO Output Enable.

Setting direct_oe[i] to 1 enables output mode for GPIO[i]
- Offset: `0x20`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "DIRECT_OE", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name      | Description   |
|:------:|:------:|:-------:|:----------|:--------------|
|  31:0  |   rw   |    x    | DIRECT_OE |               |

## MASKED_OE_LOWER
GPIO write Output Enable lower with mask.

Masked write for DATA_OE[15:0], the register that controls
output mode for GPIO pins [15:0].

Upper 16 bits of this register are used as mask. Writing
lower 16 bits of the register changes DATA_OE[15:0] value
if mask bits are set.

Read-back of this register returns upper 16 bits as zero
and lower 16 bits as DATA_OE[15:0].
- Offset: `0x24`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "data", "bits": 16, "attr": ["rw"], "rotate": 0}, {"name": "mask", "bits": 16, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                                  |
|:------:|:------:|:-------:|:-------|:---------------------------------------------------------------------------------------------|
| 31:16  |   rw   |    x    | mask   | Write OE mask[15:0]. A value of 1 in mask[i] allows the updating of DATA_OE[i], 0 <= i <= 15 |
|  15:0  |   rw   |    x    | data   | Write OE value[15:0]. Value to write into DATA_OE[i], valid in the presence of mask[i]==1    |

## MASKED_OE_UPPER
GPIO write Output Enable upper with mask.

Masked write for DATA_OE[31:16], the register that controls
output mode for GPIO pins [31:16].

Upper 16 bits of this register are used as mask. Writing
lower 16 bits of the register changes DATA_OE[31:16] value
if mask bits are set.

Read-back of this register returns upper 16 bits as zero
and lower 16 bits as DATA_OE[31:16].
- Offset: `0x28`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "data", "bits": 16, "attr": ["rw"], "rotate": 0}, {"name": "mask", "bits": 16, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                                                                    |
|:------:|:------:|:-------:|:-------|:-----------------------------------------------------------------------------------------------|
| 31:16  |   rw   |    x    | mask   | Write OE mask[31:16]. A value of 1 in mask[i] allows the updating of DATA_OE[i], 16 <= i <= 31 |
|  15:0  |   rw   |    x    | data   | Write OE value[31:16]. Value to write into DATA_OE[i], valid in the presence of mask[i]==1     |

## INTR_CTRL_EN_RISING
GPIO interrupt enable for GPIO, rising edge.

If [`INTR_ENABLE`](#intr_enable)[i] is true, a value of 1 on [`INTR_CTRL_EN_RISING`](#intr_ctrl_en_rising)[i]
enables rising-edge interrupt detection on GPIO[i].
- Offset: `0x2c`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "INTR_CTRL_EN_RISING", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name                | Description   |
|:------:|:------:|:-------:|:--------------------|:--------------|
|  31:0  |   rw   |    x    | INTR_CTRL_EN_RISING |               |

## INTR_CTRL_EN_FALLING
GPIO interrupt enable for GPIO, falling edge.

If [`INTR_ENABLE`](#intr_enable)[i] is true, a value of 1 on [`INTR_CTRL_EN_FALLING`](#intr_ctrl_en_falling)[i]
enables falling-edge interrupt detection on GPIO[i].
- Offset: `0x30`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "INTR_CTRL_EN_FALLING", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name                 | Description   |
|:------:|:------:|:-------:|:---------------------|:--------------|
|  31:0  |   rw   |    x    | INTR_CTRL_EN_FALLING |               |

## INTR_CTRL_EN_LVLHIGH
GPIO interrupt enable for GPIO, level high.

If [`INTR_ENABLE`](#intr_enable)[i] is true, a value of 1 on [`INTR_CTRL_EN_LVLHIGH`](#intr_ctrl_en_lvlhigh)[i]
enables level high interrupt detection on GPIO[i].
- Offset: `0x34`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "INTR_CTRL_EN_LVLHIGH", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name                 | Description   |
|:------:|:------:|:-------:|:---------------------|:--------------|
|  31:0  |   rw   |    x    | INTR_CTRL_EN_LVLHIGH |               |

## INTR_CTRL_EN_LVLLOW
GPIO interrupt enable for GPIO, level low.

If [`INTR_ENABLE`](#intr_enable)[i] is true, a value of 1 on [`INTR_CTRL_EN_LVLLOW`](#intr_ctrl_en_lvllow)[i]
enables level low interrupt detection on GPIO[i].
- Offset: `0x38`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "INTR_CTRL_EN_LVLLOW", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name                | Description   |
|:------:|:------:|:-------:|:--------------------|:--------------|
|  31:0  |   rw   |    x    | INTR_CTRL_EN_LVLLOW |               |

## CTRL_EN_INPUT_FILTER
filter enable for GPIO input bits.

If [`CTRL_EN_INPUT_FILTER`](#ctrl_en_input_filter)[i] is true, a value of input bit [i]
must be stable for 16 cycles before transitioning.
- Offset: `0x3c`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "CTRL_EN_INPUT_FILTER", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name                 | Description   |
|:------:|:------:|:-------:|:---------------------|:--------------|
|  31:0  |   rw   |    x    | CTRL_EN_INPUT_FILTER |               |

## HW_STRAPS_DATA_IN_VALID
Indicates whether the data in [`HW_STRAPS_DATA_IN`](#hw_straps_data_in) is valid.
- Offset: `0x40`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "HW_STRAPS_DATA_IN_VALID", "bits": 1, "attr": ["ro"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 250}}
```

|  Bits  |  Type  |  Reset  | Name                    | Description   |
|:------:|:------:|:-------:|:------------------------|:--------------|
|  31:1  |        |         |                         | Reserved      |
|   0    |   ro   |   0x0   | HW_STRAPS_DATA_IN_VALID |               |

## HW_STRAPS_DATA_IN
GPIO input data that was sampled as straps at most once after the block
came out of reset.

The behavior of this register depends on the GpioAsHwStrapsEn parameter.
- If the parameter is false then the register reads as zero.
- If the parameter is true then GPIO input data is sampled after reset
on the first cycle where the strap_en_i input is high. The
sampled data is then stored in this register.
- Offset: `0x44`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "HW_STRAPS_DATA_IN", "bits": 32, "attr": ["ro"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name              | Description   |
|:------:|:------:|:-------:|:------------------|:--------------|
|  31:0  |   ro   |   0x0   | HW_STRAPS_DATA_IN |               |

## PER_PIN_IO
Per-pin view of the output and input data of one GPIO.

This register aliases bit i of [`DIRECT_OUT`](#direct_out) and [`DATA_IN`](#data_in) for GPIO[i].
Writing it updates only DATA_OUT[i], without affecting the other GPIOs.
- Reset default: `0x0`
- Reset mask: `0x101`

### Instances

| Name          | Offset   |
|:--------------|:---------|
| PER_PIN_IO_0  | 0x100    |
| PER_PIN_IO_1  | 0x104    |
| PER_PIN_IO_2  | 0x108    |
| PER_PIN_IO_3  | 0x10c    |
| PER_PIN_IO_4  | 0x110    |
| PER_PIN_IO_5  | 0x114    |
| PER_PIN_IO_6  | 0x118    |
| PER_PIN_IO_7  | 0x11c    |
| PER_PIN_IO_8  | 0x120    |
| PER_PIN_IO_9  | 0x124    |
| PER_PIN_IO_10 | 0x128    |
| PER_PIN_IO_11 | 0x12c    |
| PER_PIN_IO_12 | 0x130    |
| PER_PIN_IO_13 | 0x134    |
| PER_PIN_IO_14 | 0x138    |
| PER_PIN_IO_15 | 0x13c    |
| PER_PIN_IO_16 | 0x140    |
| PER_PIN_IO_17 | 0x144    |
| PER_PIN_IO_18 | 0x148    |
| PER_PIN_IO_19 | 0x14c    |
| PER_PIN_IO_20 | 0x150    |
| PER_PIN_IO_21 | 0x154    |
| PER_PIN_IO_22 | 0x158    |
| PER_PIN_IO_23 | 0x15c    |
| PER_PIN_IO_24 | 0x160    |
| PER_PIN_IO_25 | 0x164    |
| PER_PIN_IO_26 | 0x168    |
| PER_PIN_IO_27 | 0x16c    |
| PER_PIN_IO_28 | 0x170    |
| PER_PIN_IO_29 | 0x174    |
| PER_PIN_IO_30 | 0x178    |
| PER_PIN_IO_31 | 0x17c    |


### Fields

```wavejson
{"reg": [{"name": "data_out", "bits": 1, "attr": ["rw"], "rotate": -90}, {"bits": 7}, {"name": "data_in", "bits": 1, "attr": ["ro"], "rotate": -90}, {"bits": 23}], "config": {"lanes": 1, "fontsize": 10, "vspace": 100}}
```

|  Bits  |  Type  |  Reset  | Name     | Description                                                     |
|:------:|:------:|:-------:|:---------|:----------------------------------------------------------------|
|  31:9  |        |         |          | Reserved                                                        |
|   8    |   ro   |    x    | data_in  | Input data value of GPIO[i], alias of [`DATA_IN`](#data_in)[i]. |
|  7:1   |        |         |          | Reserved                                                        |
|   0    |   rw   |    x    | data_out | Output data value of GPIO[i], alias of DATA_OUT[i].             |

## PER_PIN_OE_0
Per-pin view of the output enable of GPIO[0].

This register aliases bit 0 of [`DIRECT_OE.`](#direct_oe)
Writing it updates only DATA_OE[0], without affecting the other GPIOs.
- Offset: `0x200`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "oe", "bits": 1, "attr": ["rw"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                                    |
|:------:|:------:|:-------:|:-------|:-----------------------------------------------|
|  31:1  |        |         |        | Reserved                                       |
|   0    |   rw   |    x    | oe     | Output enable of GPIO[0], alias of DATA_OE[0]. |

## PER_PIN_INTR_CTRL_0
Per-pin view of the interrupt control and input filter configuration of GPIO[0].

This register aliases bit 0 of [`INTR_CTRL_EN_RISING`](#intr_ctrl_en_rising), [`INTR_CTRL_EN_FALLING`](#intr_ctrl_en_falling), [`INTR_CTRL_EN_LVLHIGH`](#intr_ctrl_en_lvlhigh), [`INTR_CTRL_EN_LVLLOW`](#intr_ctrl_en_lvllow) and [`CTRL_EN_INPUT_FILTER.`](#ctrl_en_input_filter)
Writing it updates only the configuration of GPIO[0], without affecting the other GPIOs.
It is separate from [`PER_PIN_OE_0`](#per_pin_oe_0), so access to the output enable and to the interrupt configuration of a GPIO can be controlled independently.
- Offset: `0x204`
- Reset default: `0x0`
- Reset mask: `0x1f`

### Fields

```wavejson
{"reg": [{"name": "intr_ctrl_en_rising", "bits": 1, "attr": ["rw"], "rotate": -90}, {"name": "intr_ctrl_en_falling", "bits": 1, "attr": ["rw"], "rotate": -90}, {"name": "intr_ctrl_en_lvlhigh", "bits": 1, "attr": ["rw"], "rotate": -90}, {"name": "intr_ctrl_en_lvllow", "bits": 1, "attr": ["rw"], "rotate": -90}, {"name": "ctrl_en_input_filter", "bits": 1, "attr": ["rw"], "rotate": -90}, {"bits": 27}], "config": {"lanes": 1, "fontsize": 10, "vspace": 220}}
```

|  Bits  |  Type  |  Reset  | Name                 | Description                                                                                            |
|:------:|:------:|:-------:|:---------------------|:-------------------------------------------------------------------------------------------------------|
|  31:5  |        |         |                      | Reserved                                                                                               |
|   4    |   rw   |    x    | ctrl_en_input_filter | Input filter enable of GPIO[0], alias of [`CTRL_EN_INPUT_FILTER`](#ctrl_en_input_filter)[0].           |
|   3    |   rw   |    x    | intr_ctrl_en_lvllow  | Level-low interrupt enable of GPIO[0], alias of [`INTR_CTRL_EN_LVLLOW`](#intr_ctrl_en_lvllow)[0].      |
|   2    |   rw   |    x    | intr_ctrl_en_lvlhigh | Level-high interrupt enable of GPIO[0], alias of [`INTR_CTRL_EN_LVLHIGH`](#intr_ctrl_en_lvlhigh)[0].   |
|   1    |   rw   |    x    | intr_ctrl_en_falling | Falling-edge interrupt enable of GPIO[0], alias of [`INTR_CTRL_EN_FALLING`](#intr_ctrl_en_falling)[0]. |
|   0    |   rw   |    x    | intr_ctrl_en_rising  | Rising-edge interrupt enable of GPIO[0], alias of [`INTR_CTRL_EN_RISING`](#intr_ctrl_en_rising)[0].    |

## PER_PIN_OE_1 to PER_PIN_OE_31, PER_PIN_INTR_CTRL_1 to PER_PIN_INTR_CTRL_31
[Note added for NNC Pipeline] These 62 sections of the original document are identical to PER_PIN_OE_0 and PER_PIN_INTR_CTRL_0 above, with the GPIO index i (1 to 31) in place of 0: PER_PIN_OE_i aliases bit i of DIRECT_OE at offset 0x200 + 8 * i, and PER_PIN_INTR_CTRL_i aliases bit i of the interrupt control and input filter registers at offset 0x204 + 8 * i (see the Summary table and the Programmer's Guide). Reset default 0x0 and fields as for GPIO[0].

<!-- Source: hw/top_earlgrey/ip_autogen/gpio/doc/interfaces.md -->

# Hardware Interfaces

<!-- BEGIN CMDGEN util/regtool.py --interfaces ./hw/top_earlgrey/ip_autogen/gpio/data/gpio.hjson -->
Referring to the [Comportable guideline for peripheral device functionality](https://opentitan.org/book/doc/contributing/hw/comportability), the module **`gpio`** has the following hardware interfaces defined
- Primary Clock: **`clk_i`**
- Other Clocks: *none*
- Bus Device Interfaces (TL-UL): **`tl`**
- Bus Host Interfaces (TL-UL): *none*

## Peripheral Pins for Chip IO

| Pin name   | Direction   | Description            |
|:-----------|:------------|:-----------------------|
| gpio[31:0] | inout       | GPIO inout to/from PAD |

## [Inter-Module Signals](https://opentitan.org/book/doc/contributing/hw/comportability/index.html#inter-signal-handling)

| Port Name      | Package::Struct               | Type    | Act   |   Width | Description                                                                                                                                 |
|:---------------|:------------------------------|:--------|:------|--------:|:--------------------------------------------------------------------------------------------------------------------------------------------|
| strap_en       | logic                         | uni     | rcv   |       1 | The strap enable signal tells gpio to take a snapshot of the input pins. The behaviour of this signal after that event will have no effect. |
| sampled_straps | gpio_pkg::gpio_straps         | uni     | req   |       1 | This vector contains the sampled strap values.                                                                                              |
| racl_policies  | top_racl_pkg::racl_policy_vec | uni     | rcv   |       1 | Incoming RACL policy vector from a racl_ctrl instance. The policy selection vector (parameter) selects the policy for each register.        |
| racl_error     | top_racl_pkg::racl_error_log  | uni     | req   |       1 | RACL error log information of this module.                                                                                                  |
| tl             | tlul_pkg::tl                  | req_rsp | rsp   |       1 |                                                                                                                                             |

## Interrupts

| Interrupt Name   | Type   | Description                                                 |
|:-----------------|:-------|:------------------------------------------------------------|
| gpio[31:0]       | Event  | raised if any of GPIO pin detects configured interrupt mode |

## Security Alerts

| Alert Name   | Description                                                                       |
|:-------------|:----------------------------------------------------------------------------------|
| fatal_fault  | This fatal alert is triggered when a fatal TL-UL bus integrity fault is detected. |

## Security Countermeasures

| Countermeasure ID   | Description                      |
|:--------------------|:---------------------------------|
| GPIO.BUS.INTEGRITY  | End-to-end bus integrity scheme. |


<!-- END CMDGEN -->

# ot_gpio_nnc: integration of the OpenTitan gpio for verification

Written for NNC Pipeline. This document describes the verification top `ot_gpio_nnc`: the OpenTitan `gpio`
(specified by the OpenTitan parts of this document, above) plus a thin wrapper that flattens its struct ports and
closes two protocols. The behaviour of `gpio` itself is specified only by the OpenTitan documents; this document
adds the port mapping, the configurations and what the wrapper does.

Normative references:
- the OpenTitan parts of this document (above): the GPIO block, its registers, interrupts, straps and alert.
- `standards/opentitan_tlul_bus_specification.md`: the TL-UL bus, including the bus integrity scheme.
- `standards/opentitan_comportability.md`: interrupt and alert conventions of OpenTitan peripherals.
- `standards/opentitan_register_tool.md`: register access types and bus error responses of generated register blocks.
- `standards/opentitan_alert_handler_theory_of_operation.md`: the differential alert handshake and the alert receiver.

## 1. Configuration

[INT-CFG-001] The design under verification has 32 GPIOs, as stated in the Features section.

[INT-CFG-002] RACL (register access control) is disabled: every register access is permitted, and no access is
rejected for an access-control reason.

[INT-CFG-003] The alert sender of `gpio` and the alert receiver of the wrapper both use the synchronous clocking
scheme (no synchronizer flops on the differential pairs). Ping requests are never issued.

[INT-CFG-004] Two design parameters of `gpio` are parameters of `ot_gpio_nnc` and are passed through unchanged:

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| GpioAsyncOn | 1 | 0 or 1 | "Instantiates 2-flop synchronizers on all GPIO inputs if set to 1." (gpio parameter list) |
| GpioAsHwStrapsEn | 1 | 0 or 1 | "Enable HW straps sampling logic for GPIO inputs at initial cold boot" (gpio parameter list); the behaviour of `HW_STRAPS_DATA_IN` for each value is given in its register description |

[INT-CFG-005] The verification shall be run in every combination of the two parameters that the run set selects;
the default combination (1, 1) is the configuration of the Earl Grey top level.

## 2. Clock and reset

[INT-CLK-001] `clk_i` is the only clock. All TL-UL and strap inputs are sampled and all outputs change at its
rising edge, except for the effect of `rst_ni`.

[INT-CLK-002] With `GpioAsyncOn` = 1, `i_gpio` may change at any time relative to `clk_i` (an input from a pad). With
`GpioAsyncOn` = 0 there is no synchronizer, and the test bench shall change `i_gpio` only synchronously to `clk_i`,
like the other inputs.

[INT-RST-001] `rst_ni` is the active-low reset, asserted asynchronously and released synchronously to `clk_i`
(the reset strategy of the comportability specification). While `rst_ni` is 0, every register holds its reset
value as given in the register tables of the gpio specification.

## 3. Ports

| Port | Direction | Width | Meaning |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Active-low reset |
| `i_a_valid` | input | 1 | TL-UL `a_valid` |
| `o_a_ready` | output | 1 | TL-UL `a_ready` |
| `i_a_opcode` | input | 3 | TL-UL `a_opcode` (Get = 4, PutFullData = 0, PutPartialData = 1) |
| `i_a_param` | input | 3 | TL-UL `a_param` |
| `i_a_size` | input | 2 | TL-UL `a_size` (log2 of the number of bytes) |
| `i_a_source` | input | 8 | TL-UL `a_source` |
| `i_a_address` | input | 32 | TL-UL `a_address` (byte address; the register offsets of the gpio specification are relative to 0) |
| `i_a_mask` | input | 4 | TL-UL `a_mask` |
| `i_a_data` | input | 32 | TL-UL `a_data` |
| `i_a_instr` | input | 1 | 1: the request is an instruction fetch (`a_user.instr_type` = MuBi4True); 0: a data access (MuBi4False) |
| `i_a_intg_flip` | input | 1 | 1: the A-channel integrity sent with the request is corrupted (see 4.2) |
| `o_d_valid` | output | 1 | TL-UL `d_valid` |
| `i_d_ready` | input | 1 | TL-UL `d_ready` |
| `o_d_opcode` | output | 3 | TL-UL `d_opcode` (AccessAck = 0, AccessAckData = 1) |
| `o_d_param` | output | 3 | TL-UL `d_param` |
| `o_d_size` | output | 2 | TL-UL `d_size` |
| `o_d_source` | output | 8 | TL-UL `d_source` |
| `o_d_sink` | output | 1 | TL-UL `d_sink` |
| `o_d_data` | output | 32 | TL-UL `d_data` |
| `o_d_error` | output | 1 | TL-UL `d_error` |
| `o_d_intg_err` | output | 1 | Response integrity of the D-channel beat is wrong (see 4.3) |
| `o_alert` | output | 1 | Alert `fatal_fault` received (see 5) |
| `o_alert_integ_fail` | output | 1 | Signal integrity failure on the alert differential pairs (see 5) |
| `i_gpio` | input | 32 | GPIO inputs `cio_gpio_i` (see 6) |
| `o_gpio` | output | 32 | GPIO outputs `cio_gpio_o`: the value of `DATA_OUT` (see 6) |
| `o_gpio_en` | output | 32 | GPIO output enables `cio_gpio_en_o`: the value of `DATA_OE` (see 6) |
| `o_intr_gpio` | output | 32 | Interrupts `intr_gpio_o`, one per GPIO (see 7) |
| `i_strap_en` | input | 1 | Strap sampling trigger `strap_en_i` (see 8) |
| `o_straps_valid` | output | 1 | `sampled_straps_o.valid` (see 8) |
| `o_straps_data` | output | 32 | `sampled_straps_o.data` (see 8) |

## 4. TL-UL device interface

### 4.1 Mapping

[INT-TL-001] The `i_a_*`, `o_a_ready`, `o_d_*` (except `o_d_intg_err`) and `i_d_ready` ports are the fields of the
same name of the TL-UL device interface `tl` of `gpio`, with the meaning given by the TL-UL bus specification.

[INT-TL-002] `a_user.rsvd` is 0. `a_user.instr_type` is MuBi4True when `i_a_instr` is 1 and MuBi4False when it is 0.

[INT-TL-003] The test bench acts as the TL-UL host. It shall follow the host rules of the TL-UL bus
specification (for example, the A-channel signals stay stable while `a_valid` is 1 and `a_ready` is 0).
Requests that the TL-UL specification lists as error cases (unsupported opcode, bad size or mask, misaligned
address) are legal stimulus: the device answers them with `d_error` = 1 as the specifications require.

### 4.2 Request integrity

[INT-INTG-001] The wrapper computes `a_user.cmd_intg` and `a_user.data_intg` of every request with OpenTitan's
integrity generator for TL-UL hosts (the section Bus Integrity Scheme of the TL-UL bus specification is not
written yet; the code is not part of this specification). A request with `i_a_intg_flip` = 0 therefore always
carries correct integrity, and the test bench does not compute integrity itself.

[INT-INTG-002] When `i_a_intg_flip` is 1, bit 0 of `a_user.cmd_intg` is inverted. The request then has a
command integrity error: a fatal TL-UL bus integrity fault in the sense of the gpio Security Alerts table,
which triggers the `fatal_fault` alert (section 5). These documents do not specify the D-channel response to
such a request.

### 4.3 Response integrity

[INT-INTG-003] The wrapper checks `d_user.rsp_intg` of every D-channel beat against the response fields with
OpenTitan's response integrity checker for TL-UL hosts. `o_d_intg_err` is 1 in a cycle where `o_d_valid` is 1
and this check fails, and 0 otherwise. A correct device never makes it 1.

## 5. Alert

[INT-ALERT-001] `gpio` has one alert, `fatal_fault`, sent through an alert sender. The wrapper connects it to an
alert receiver as described in the alert handler theory of operation (Differential Alert Signaling). `o_alert`
is the `alert_o` output of that receiver: it is 1 for one clock cycle for each alert handshake that the receiver
detects.

[INT-ALERT-002] `o_alert_integ_fail` is the `integ_fail_o` output of the receiver. A correct sender never makes
it 1.

[INT-ALERT-003] A fatal alert is repeated until reset (comportability specification, Alerts per Module), so after
a bus integrity fault `o_alert` pulses repeatedly until `rst_ni` is asserted. A write of 1 to
`ALERT_TEST.fatal_fault` triggers one alert event, as the register description says.

## 6. GPIO pins

[INT-IO-001] `i_gpio`, `o_gpio` and `o_gpio_en` are the peripheral pins `cio_gpio_i`, `cio_gpio_o` and
`cio_gpio_en_o` of `gpio`: bit i belongs to GPIO[i]. `o_gpio` is `DATA_OUT` and `o_gpio_en` is `DATA_OE`.

[INT-IO-002] There is no pad model and no pin multiplexer in `ot_gpio_nnc`: `i_gpio` is driven only by the test
bench and does not depend on `o_gpio` or `o_gpio_en`. The Programmer's Guide examples assume pads with weak
pull-ups connected to the outputs; a test that follows such an example models the pad itself (for example by
driving `i_gpio[i]` = `o_gpio[i]` where `o_gpio_en[i]` = 1 and 1 elsewhere).

## 7. Interrupts

[INT-INTR-001] `o_intr_gpio[i]` is the interrupt output `intr_gpio_o[i]` of `gpio`, an event-type interrupt as
defined in the comportability specification, with bit i of the registers `INTR_ENABLE`, `INTR_STATE` and
`INTR_TEST`.

## 8. Straps

[INT-STRAP-001] `i_strap_en` is the input `strap_en_i` of `gpio`, and `o_straps_valid` and `o_straps_data` are the
fields `valid` and `data` of its output `sampled_straps_o` (Inter-Module Signals table, GPIO Inputs as HW Straps).

## 9. Verification scope

[INT-VER-001] The verification shall cover, through the ports above and in each configuration of the run set:
reset values of every register; the access type of every register field as given in the register tables; direct
and masked writes of `DATA_OUT` and `DATA_OE` and their reads; the per-pin register view; `DATA_IN` with and without
the input filter; interrupt detection on rising edge, falling edge, high level and low level, with
`INTR_STATE`, `INTR_ENABLE` and `INTR_TEST`; strap sampling with `HW_STRAPS_DATA_IN_VALID` and `HW_STRAPS_DATA_IN`;
bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the
`fatal_fault` alert.

[INT-VER-002] The per-pin registers of 32 GPIOs behave alike. The verification may check every GPIO for the
32-bit registers and a selection of GPIOs for the per-pin registers, provided that the selection includes
GPIO[0], GPIO[15], GPIO[16] and GPIO[31].

## 10. Decisions for verification

The gaps that `nnc spec-lint` found in this specification (work/spec_lint.md, GAP-001..019) are answered here,
from the documents only. Where the documents are silent or disagree, the verification checks only what every
reading has in common, or a bound instead of an exact cycle. These decisions were taken on the project owner's
delegation by an AI assistant, not by a hardware designer; the G4 reviewer is asked to confirm them.

| ID | Subject | Decision |
|---|---|---|
| D-001 | Masked writes of `DATA_OE` (GAP-001) | The register descriptions bind, and the Theory of Operation says the masked-write concept "is duplicated for the output enable register": a write to `MASKED_OE_LOWER` (`MASKED_OE_UPPER`) sets `DATA_OE[i]` to data bit i where mask bit i is 1 and leaves every other bit of `DATA_OE` unchanged, exactly as for `DATA_OUT`. The `DATA_OE` values in the Programmer's Guide example are not used as expected values. |
| D-002 | Read of `MASKED_OE_*` bits 31:16 (GAP-002) | Bits 15:0 of a read of `MASKED_OUT_*` and `MASKED_OE_*` are the corresponding half of `DATA_OUT` / `DATA_OE`. Bits 31:16 of a read of `MASKED_OUT_*` are 0. For `MASKED_OE_*` the text says 0 and the field table says rw: bits 31:16 of a read are not checked. |
| D-003 | Reset values (GAP-003) | The "Reset default" line of each register binds where the field table says "x": `DIRECT_OUT`, `DIRECT_OE`, `MASKED_*`, `INTR_CTRL_EN_*`, `CTRL_EN_INPUT_FILTER`, `PER_PIN_OE_i`, `PER_PIN_INTR_CTRL_i` and `PER_PIN_IO_i.data_out` read 0 after reset, and `o_gpio` and `o_gpio_en` are 0 while `rst_ni` = 0 and until written. `DATA_IN` and `PER_PIN_IO_i.data_in` are not checked while `rst_ni` = 0 and in the first 20 cycles after release. |
| D-004 | `INTR_ENABLE` and detection (GAP-004) | The gpio text makes `INTR_ENABLE` a condition for detection; the comportability specification makes it only mask the output. Checked, as both readings agree: with `INTR_ENABLE[i]` = 1 a configured event sets `INTR_STATE[i]`; with `INTR_ENABLE[i]` = 0, `o_intr_gpio[i]` stays 0. `INTR_STATE[i]` after an event that occurs while `INTR_ENABLE[i]` = 0 is not checked, and neither is `o_intr_gpio[i]` in the 4 cycles after `INTR_ENABLE[i]` is set to 1 when such an event may have been latched. |
| D-005 | W1C while a level condition holds (GAP-005) | If the level condition still holds after a write of 1 to `INTR_STATE[i]`, `INTR_STATE[i]` reads 1 and `o_intr_gpio[i]` (with `INTR_ENABLE[i]` = 1) is 1 again within 4 cycles after the write response; a dip in between is not checked. |
| D-006 | Event in the same cycle as a W1C (GAP-006) | Not checked: tests do not create an edge on GPIO[i] within 8 cycles of a write of 1 to `INTR_STATE[i]`, or do not check `INTR_STATE[i]` after it. |
| D-007 | Input filter threshold and switching (GAP-007) | With `CTRL_EN_INPUT_FILTER[i]` = 1: a new value of `i_gpio[i]` held for at most 12 cycles never appears in `DATA_IN[i]` and creates no interrupt event; a new value held for at least 24 cycles appears in `DATA_IN[i]` no later than 24 cycles after the change. The exact threshold is not checked. After a write that changes `CTRL_EN_INPUT_FILTER[i]`, `DATA_IN[i]` and interrupt events of GPIO[i] are not checked for 24 cycles; tests keep `i_gpio[i]` constant in that window. |
| D-008 | Strap sampling (GAP-008) | With `GpioAsHwStrapsEn` = 1, tests keep `i_strap_en` = 0 while `rst_ni` = 0 and for at least 4 cycles after release, then raise it once and keep `i_gpio` constant from 24 cycles before to 8 cycles after that rising edge. Within 4 cycles after the edge, `HW_STRAPS_DATA_IN_VALID` reads 1, `o_straps_valid` = 1, and `HW_STRAPS_DATA_IN` and `o_straps_data` equal that `i_gpio` value. Before the edge both valid indications are 0. Later changes of `i_gpio` or `i_strap_en` change neither until reset; after a reset ("After each reset", Theory of Operation) the sequence can happen again. A level already high at reset release is not used. |
| D-009 | Straps disabled (GAP-009) | With `GpioAsHwStrapsEn` = 0, `HW_STRAPS_DATA_IN` reads 0 at all times (register description). `HW_STRAPS_DATA_IN_VALID`, `o_straps_valid` and `o_straps_data` are not checked. |
| D-010 | `ALERT_TEST` (GAP-010) | Tests that trigger an alert write 0x8000_0001 (regwen kept at 1); the combined write 0x0000_0001 is not used. A write with bit 31 = 0 sets `regwen` to 0 until reset; afterwards a write of 0x8000_0001 completes with `d_error` = 0, triggers no alert, and `regwen` still reads 0. One write of 1 to `fatal_fault`, with no other alert cause and no other such write within 32 cycles, gives exactly one `o_alert` pulse, no later than 16 cycles after the write response. After reset `ALERT_TEST` reads 0x8000_0000. |
| D-011 | Instruction fetches (GAP-011) | Not stated for registers in these documents. A request with `i_a_instr` = 1 is not checked for `d_error`; a write with `i_a_instr` = 1 is not used. |
| D-012 | Address decoding (GAP-012) | Following the register tool (excess address bits are stripped), the registers 0x000..0x2fc use the offsets 0x000..0x3FF. A request to an unmapped offset in 0x000..0x3FF returns `d_error` = 1 and changes no register. Requests at 0x400 and above are not used. |
| D-013 | Sub-word and partial writes (GAP-013) | Per the register tool and the Per-Pin Register View text: full-word writes with mask 1111 succeed. An aligned byte write (a_size 0 at offset 0 of the register, mask 0001) to a register with fields above bit 7 (`INTR_*`, `DIRECT_*`, `MASKED_*`, `INTR_CTRL_EN_*`, `CTRL_EN_INPUT_FILTER`, `PER_PIN_IO_i`) returns `d_error` = 1 and changes nothing; such a byte write to `PER_PIN_OE_i` or `PER_PIN_INTR_CTRL_i` completes with `d_error` = 0 and has the effect of the write. Other sub-word cases, including a_size 2 with a partial mask, are not checked. Reads of any size return the full register. |
| D-014 | Outstanding requests and back-pressure (GAP-016) | TL-UL allows several outstanding requests and does not guarantee order. The test bench matches responses by `d_source`, uses a distinct `a_source` per outstanding request, and does not assume `o_a_ready` = 1. |
| D-015 | Fields of a response (GAP-018) | Checked: `d_error`, `d_source` (echo of `a_source`), `d_size` (echo of `a_size`), `d_opcode` (AccessAckData for Get, AccessAck for PutFullData and PutPartialData). `d_data` is checked only for a Get without error. For an undefined opcode only `d_error` = 1 is checked. `d_param` and `d_sink` are not checked. |
| D-016 | Reset (GAP-017) | The test bench keeps `i_a_valid` = 0 while `rst_ni` = 0 and in the first cycle after release. While `rst_ni` = 0, `o_d_valid`, `o_alert`, `o_alert_integ_fail`, `o_intr_gpio`, `o_gpio` and `o_gpio_en` shall be 0; `o_a_ready`, `o_straps_valid` and `o_straps_data` are not checked. A response pending at reset is discarded. The rule that outputs change only at rising clock edges is not applied in cycles where `rst_ni` is 0 or falls. |
| D-017 | Integrity outputs and integrity errors (GAP-014) | `o_d_intg_err` and `o_alert_integ_fail` shall be 0 in every cycle with `rst_ni` = 1. After a request with `i_a_intg_flip` = 1 is accepted, `o_alert` shall pulse no later than 16 cycles later and then at least once in every 32 cycles until `rst_ni` is asserted. The D-channel response to that request, its effect on registers and the behaviour of later requests are not checked; the test bench does not wait more than 32 cycles for that response, and the test resets the design afterwards. |
| D-018 | Latencies (GAP-015) | With the filter off, a change of `i_gpio[i]` held for at least 8 cycles appears in `DATA_IN[i]` no later than 4 cycles after the first rising edge after the change (both values of `GpioAsyncOn`). A configured event sets `INTR_STATE[i]` no later than 4 cycles after it appears in `DATA_IN[i]`. `o_intr_gpio[i]` equals `INTR_STATE[i]` AND `INTR_ENABLE[i]` except in the 2 cycles after either changes. `o_gpio` and `o_gpio_en` equal `DATA_OUT` and `DATA_OE` no later than 2 cycles after the response of the write that changed them. Lower bounds are not checked. |
| D-019 | Writes to read-only registers, reads of write-only fields (GAP-018) | A write to a ro register or field (`DATA_IN`, `HW_STRAPS_*`, `PER_PIN_IO_i.data_in`) leaves it unchanged; its `d_error` is not checked. A wo field (`INTR_TEST`, `MASKED_OUT_*` mask, `ALERT_TEST.fatal_fault`) has no read path and reads 0 (register tool, Type WO). Reserved bits read 0 and writes to them have no effect. |
| D-020 | Programmer's Guide comments (GAP-019) | The register names and descriptions decide: `INTR_CTRL_EN_LVLLOW` and `INTR_CTRL_EN_LVLHIGH` enable level detection, not edge detection. The comments of the examples are not used as expected behaviour. |
| D-021 | Pins and the pad model | `DATA_IN` reflects `i_gpio` only (INT-IO-002): with `o_gpio_en[i]` = 1 the test bench may drive `i_gpio[i]` to any value, and `DATA_IN[i]` follows `i_gpio[i]`, not `o_gpio[i]`. |
| D-022 | Out of scope | User-bit default values, requests with a non-zero `a_param`, and the bit layout of `a_user`/`d_user` (the wrapper produces them) are not checked; tests drive `i_a_param` = 0. |
