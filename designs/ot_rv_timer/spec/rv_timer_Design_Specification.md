<!-- rv_timer specification for NNC Pipeline: the OpenTitan rv_timer documents below, concatenated in this order,
     from lowRISC/opentitan commit ee811654ff1a1431781504554a36490c2f77d6b1. Text unchanged except that the regression-badge table at the top
     of README.md is removed. Licence: Apache-2.0 (see ../NOTICE.md).
     The last part, "ot_rv_timer_nnc: integration of the OpenTitan rv_timer for verification", is not from
     OpenTitan: it was written for NNC Pipeline and describes the verification wrapper. -->

<!-- Source: hw/ip/rv_timer/README.md -->

# Timer HWIP Technical Specification

# Overview

This document specifies RISC-V Timer hardware IP functionality. This module
conforms to the
[Comportable guideline for peripheral functionality.](../../../doc/contributing/hw/comportability/README.md)
See that document for integration overview within the broader top level
system.


## Features

- 64-bit timer with 12-bit prescaler and 8-bit step register
- Compliant with RISC-V privileged specification v1.11
- Configurable number of timers per hart and number of harts

Note: Although the number of timers is indeed configurable, the implementation currently only connects up one timer for one hart.
## Description

The timer module provides a configurable number of 64-bit counters where each
counter increments by a step value whenever the prescaler times out. Each timer
generates an interrupt if the counter reaches (or is above) a programmed
value. The timer is intended to be used by the processors to check the current
time relative to the reset or the system power-on.

In this version, the timer doesn't consider low-power modes and
assumes the clock is neither turned off nor changed during runtime.

## Compatibility

The timer IP provides memory-mapped registers equivalent to `mtime` and `mtimecmp` which can
be used as the machine-mode timer registers defined in the RISC-V privileged
spec. Additional features such as prescaler, step, and a configurable number of
timers and harts have been added.

<!-- Source: hw/ip/rv_timer/doc/theory_of_operation.md -->

# Theory of Operation

## Block Diagram

![Timer Block Diagram](../doc/timer_block_diagram.svg)

The timer module is composed of tick generators, counters, and comparators.
A tick generator creates a tick every time its internal counter hits the
[`CFG0.prescaler`](registers.md#cfg0) value. The tick is used to increment `mtime` by the [`CFG0.step`](registers.md#cfg0)
value. The 64-bit `mtime` value is compared with the 64-bit `mtimecmp`. If
`mtime` is greater than or equal to `mtimecmp`, the timer raises an interrupt.

## Design Details

### Tick Generator

The tick module inside the timer IP is used to generate a fixed period of pulse
signal. This allows creation of a call-clock timer tick such as 1us or 10us
regardless of the system clock period. It is useful if the system has more than
one clock as a clock source. The firmware just needs to adjust the
[`CFG0.prescaler`](registers.md#cfg0) value and the actual timer interrupt handling routine does not
need a variable clock period to update `mtimecmp`.

For instance, if a system switches between 48MHz and 200MHz clocks, a prescaler
value of **47** for 48MHz and **199** for 200MHz will generate a 1us tick.
In this version, the timer only supports a single fixed clock, so the firmware
should change [`CFG0.prescaler`](registers.md#cfg0) appropriately.

### Configurable number of timers and harts

The timer IP supports more than one HART and/or more than one timer per hart.
Each hart has a set of tick generator and counter. It means the timer IP has the
same number of prescalers, steps, and `mtime` registers as the number of harts.

Each hart can have multiple sets of `mtimecmp`, comparator logic, and expire
interrupt signals. This version of the IP is fixed to have one Hart and one
Timer per Hart.

Below is an example configuration file for `N_TIMER` 2 and `N_HARTS` 2.
It has separate interrupts per timer and a set of interrupt enable and state
registers per Hart.

```hjson
{
  // ...
  interrupt_list: [
    { name: "timer_expired_hart0_timer0",
      desc: "raised if hart0's timer0 expired (mtime >= mtimecmp)"
    },
    { name: "timer_expired_hart0_timer1",
      desc: "raised if hart0's timer1 expired (mtime >= mtimecmp)"
    },
    { name: "timer_expired_hart1_timer0",
      desc: "raised if hart1's timer0 expired (mtime >= mtimecmp)"
    },
    { name: "timer_expired_hart1_timer1",
      desc: "raised if hart1's timer1 expired (mtime >= mtimecmp)"
    },
  ],
  //...
  registers: {
    // ...
    { skipto: "0x100" },
    { name: "CFG0",
      desc: "Configuration for Hart 0",
      swaccess: "rw",
      hwaccess: "hro",
      fields: [
        { bits: "11:0", name: "prescale", desc: "Prescaler to generate tick" },
        { bits: "23:16", name: "step", resval: "0x1", desc: "Incremental value for each tick" },
      ],
    },
    // ...
    { multireg: {
        name: "INTR_ENABLE0",
        desc: "Interrupt Enable",
        count: 2,
        cname: "TIMER",
        swaccess: "rw",
        hwaccess: "hro",
        fields: [
          { bits: "0", name: "IE", desc: "Interrupt Enable for timer" }
        ]
      }
    },
    { multireg: {
        name: "INTR_STATE0",
        desc: "Interrupt Status",
        count: 2,
        cname: "TIMER",
        swaccess: "ro",
        hwaccess: "hrw",
        fields: [
          { bits: "0", name: "IS", desc: "Interrupt status for timer" }
        ],
      }
    },
    // ...
    { skipto: "0x200" },
    { name: "CFG1",
      desc: "Configuration for Hart 1",
      swaccess: "rw",
      hwaccess: "hro",
      fields: [
        { bits: "11:0", name: "prescale", desc: "Prescaler to generate tick" },
        { bits: "23:16", name: "step", resval: "0x1", desc: "Incremental value for each tick" },
      ],
    },
    // ...
    { name: "TIMER_V_UPPER1",
      desc: "Timer value Upper",
      swaccess: "rw",
      hwaccess: "hrw",
      fields: [
        { bits: "31:0", name: "v", desc: "Timer value [63:32]" },
      ],
    },
    // ...
}
```

<!-- Source: hw/ip/rv_timer/doc/programmers_guide.md -->

# Programmer's Guide

## Initialization

Software is expected to configure `prescaler` and `step` before activating the
timer. These two fields need to be stable to correctly increment the timer
value. If software wants to change these fields, it should de-activate the
timer and then proceed.

## Register Access

The timer IP has 64-bit timer value registers and 64-bit compare registers. The
register interface, however, is set to 32-bit data width. The CPU cannot access
64-bit data in a single request. However, when split into two reads, it is
possible the timer value can increment between the two requests.

The IP doesn't have a latching or blocking mechanism to avoid this issue. It is
the programmer's responsibility to ensure the correct value is read. For
instance, if the CPU reads `0xFFFF_FFFF` from lower 32-bit timer value (`mtime`)
and `0x0000_0001` from upper 32-bit timer value (`mtimeh`), there is a chance
that rather than having the value `0x1_FFFF_FFFF` the timer value has changed
from `0x0_FFFF_FFFF` to `0x1_0000_0000` between the two reads. If there is the
possibility of an interrupt between the two reads then the counter could have
advanced even more.

This condition can be detected in a standard way using a third read. Figure 10.1
in the RISC-V unprivileged specification explains how to avoid this.

```asm
again:
    rdcycleh  x3
    rdcycle   x2
    rdcycleh  x4
    bne       x3, x4, again
```

Updating `mtimecmp` register also follows a similar approach to avoid a spurious
interrupt during the register update. Please refer to the `mtimecmp` section in
the RISC-V privileged specification.

```asm
# New comparand is in a1:a0.
li t0, -1
li t1, TOP_EARLGREY_RV_TIMER_BASE_ADDR
sw t0, RV_TIMER_COMPARE_LOWER0_0_REG_OFFSET(t1)   # No smaller than old value.
sw a1, RV_TIMER_COMPARE_UPPER0_0_REG_OFFSET(t1)   # No smaller than new value.
sw a0, RV_TIMER_COMPARE_LOWER0_0_REG_OFFSET(t1)   # New value.
```

In typical usage the `mtime` register would not be written, but if there is a need
to set it to an arbitrary, dynamically-determined value, the following sequence
should be used to prevent the operation of the timer yielding an indeterminate
result:

```asm
# Desired time is in a1:a0
li t1, TOP_EARLGREY_RV_TIMER_BASE_ADDR
sw x0, RV_TIMER_TIMER_V_LOWER0_0_REG_OFFSET(t1)
sw a1, RV_TIMER_TIMER_V_UPPER0_0_REG_OFFSET(t1)  # Upper half of target value.
sw a0, RV_TIMER_TIMER_V_LOWER0_0_REG_OFFSET(t1)  # Lower half of target value.
```

In the event that the target value of the lower half is close to 0xFFFF_FFFF,
this sequence prevents the timer from assuming an incorrect time between the
two 32-bit writes required to set the 64-bit timer value.

If the value of `mtime` is modified in this manner then `mtimecmp` shall be
written after `mtime` in order to clear any pending interrupt condition.

## Timer behaviour close to 2^64

There are some peculiarities when `mtime` and `mtimecmp` get close to the end of
the 64-bit integer range. In particular, because an unsigned comparison is done
between `mtime` and `mtimecmp` care is needed. A couple of cases are:

1. `mtimecmp` close to 0xFFFF_FFFF_FFFF_FFFF. In this case the time-out event
   will be signaled when `mtime` passes the comparison value, the interrupt will
   be raised and the source indicated in the corresponding bit of the interrupt
   status register. However, if there is a delay in servicing the interrupt the
   `mtime` value could wrap to zero (and continue to increment) so the value
   read by the interrupt service routine will be less than the comparison value.
   With a [`CFG0.step`](registers.md#cfg0) above 1, one tick can also carry
   `mtime` from below `mtimecmp` past the end of the range, so `mtime` skips
   the comparison value and the interrupt is not raised.

2. When the timer is setup to trigger a `timeout` some number of timer ticks
   into the future, the computation of the comparison value `mtime + timeout`
   may overflow. If this value is set in `mtimecmp` it would make `mtime`
   greater than `mtimecmp` and immediately signal an interrupt.
   A possible solution is to have an intermediate interrupt by setting the
   `mtimecmp` to 64-bit all-ones, `0xFFFF_FFFF_FFFF_FFFF`. Then the service
   routine for that interrupt will need to poll `mtime` until it wraps (which
   could take up to a timer clock tick) before scheduling the required interrupt
   using the originally computed `mtimecmp` value.
   With a `step` above 1, `mtime` can step over the all-ones value and this
   intermediate interrupt is never raised. Setting `mtimecmp` to
   `0xFFFF_FFFF_FFFF_FFFF - step + 1` works for any nonzero `step`, since the
   last value of `mtime` before it wraps is always at least that large.

## Interrupt Handling

If `mtime` is greater than or equal to the value of `mtimecmp`, the interrupt is generated from the RV_TIMER module.
If the core enables the timer interrupt in `MIE` CSR, it jumps into the timer interrupt service routine.
Clearing the interrupt can be done by writing 1 into the Interrupt Status register [`INTR_STATE0`](../../spi_device/data/spi_device.hjson#intr_state0).
The RV_TIMER module also follows RISC-V Privileged spec that requires the interrupt to be cleared by updating `mtimecmp` memory-mapped CSRs.
In this case both [`COMPARE_LOWER0_0`](../../spi_device/data/spi_device.hjson#compare_lower0_0) and [`COMPARE_UPPER0_0`](../../spi_device/data/spi_device.hjson#compare_upper0_0) can clear the interrupt source.

## Device Interface Functions (DIFs)

- [Device Interface Functions](../../../../sw/device/lib/dif/dif_rv_timer.h)

<!-- Source: hw/ip/rv_timer/doc/registers.md -->

# Registers

<!-- BEGIN CMDGEN util/regtool.py -d ./hw/ip/rv_timer/data/rv_timer.hjson -->
## Summary

| Name                                             | Offset   |   Length | Description              |
|:-------------------------------------------------|:---------|---------:|:-------------------------|
| rv_timer.[`ALERT_TEST`](#alert_test)             | 0x0      |        4 | Alert Test Register      |
| rv_timer.[`CTRL`](#ctrl)                         | 0x4      |        4 | Control register         |
| rv_timer.[`INTR_ENABLE0`](#intr_enable0)         | 0x100    |        4 | Interrupt Enable         |
| rv_timer.[`INTR_STATE0`](#intr_state0)           | 0x104    |        4 | Interrupt Status         |
| rv_timer.[`INTR_TEST0`](#intr_test0)             | 0x108    |        4 | Interrupt test register  |
| rv_timer.[`CFG0`](#cfg0)                         | 0x10c    |        4 | Configuration for Hart 0 |
| rv_timer.[`TIMER_V_LOWER0`](#timer_v_lower0)     | 0x110    |        4 | Timer value Lower        |
| rv_timer.[`TIMER_V_UPPER0`](#timer_v_upper0)     | 0x114    |        4 | Timer value Upper        |
| rv_timer.[`COMPARE_LOWER0_0`](#compare_lower0_0) | 0x118    |        4 | Timer value Lower        |
| rv_timer.[`COMPARE_UPPER0_0`](#compare_upper0_0) | 0x11c    |        4 | Timer value Upper        |

## ALERT_TEST
Alert Test Register
- Offset: `0x0`
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

## CTRL
Control register
- Offset: `0x4`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "active_0", "bits": 1, "attr": ["rw"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 100}}
```

|  Bits  |  Type  |  Reset  | Name     | Description          |
|:------:|:------:|:-------:|:---------|:---------------------|
|  31:1  |        |         |          | Reserved             |
|   0    |   rw   |   0x0   | active_0 | If 1, timer operates |

## INTR_ENABLE0
Interrupt Enable
- Offset: `0x100`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "IE_0", "bits": 1, "attr": ["rw"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                |
|:------:|:------:|:-------:|:-------|:---------------------------|
|  31:1  |        |         |        | Reserved                   |
|   0    |   rw   |   0x0   | IE_0   | Interrupt Enable for timer |

## INTR_STATE0
Interrupt Status
- Offset: `0x104`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "IS_0", "bits": 1, "attr": ["rw1c"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description                |
|:------:|:------:|:-------:|:-------|:---------------------------|
|  31:1  |        |         |        | Reserved                   |
|   0    |  rw1c  |   0x0   | IS_0   | Interrupt status for timer |

## INTR_TEST0
Interrupt test register
- Offset: `0x108`
- Reset default: `0x0`
- Reset mask: `0x1`

### Fields

```wavejson
{"reg": [{"name": "T_0", "bits": 1, "attr": ["wo"], "rotate": -90}, {"bits": 31}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description              |
|:------:|:------:|:-------:|:-------|:-------------------------|
|  31:1  |        |         |        | Reserved                 |
|   0    |   wo   |    x    | T_0    | Interrupt test for timer |

## CFG0
Configuration for Hart 0
- Offset: `0x10c`
- Reset default: `0x10000`
- Reset mask: `0xff0fff`

### Fields

```wavejson
{"reg": [{"name": "prescale", "bits": 12, "attr": ["rw"], "rotate": 0}, {"bits": 4}, {"name": "step", "bits": 8, "attr": ["rw"], "rotate": 0}, {"bits": 8}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name     | Description                     |
|:------:|:------:|:-------:|:---------|:--------------------------------|
| 31:24  |        |         |          | Reserved                        |
| 23:16  |   rw   |   0x1   | step     | Incremental value for each tick |
| 15:12  |        |         |          | Reserved                        |
|  11:0  |   rw   |   0x0   | prescale | Prescaler to generate tick      |

## TIMER_V_LOWER0
Timer value Lower
- Offset: `0x110`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "v", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description        |
|:------:|:------:|:-------:|:-------|:-------------------|
|  31:0  |   rw   |   0x0   | v      | Timer value [31:0] |

## TIMER_V_UPPER0
Timer value Upper
- Offset: `0x114`
- Reset default: `0x0`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "v", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |  Reset  | Name   | Description         |
|:------:|:------:|:-------:|:-------|:--------------------|
|  31:0  |   rw   |   0x0   | v      | Timer value [63:32] |

## COMPARE_LOWER0_0
Timer value Lower
- Offset: `0x118`
- Reset default: `0xffffffff`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "v", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |   Reset    | Name   | Description                |
|:------:|:------:|:----------:|:-------|:---------------------------|
|  31:0  |   rw   | 0xffffffff | v      | Timer compare value [31:0] |

## COMPARE_UPPER0_0
Timer value Upper
- Offset: `0x11c`
- Reset default: `0xffffffff`
- Reset mask: `0xffffffff`

### Fields

```wavejson
{"reg": [{"name": "v", "bits": 32, "attr": ["rw"], "rotate": 0}], "config": {"lanes": 1, "fontsize": 10, "vspace": 80}}
```

|  Bits  |  Type  |   Reset    | Name   | Description                 |
|:------:|:------:|:----------:|:-------|:----------------------------|
|  31:0  |   rw   | 0xffffffff | v      | Timer compare value [63:32] |


<!-- END CMDGEN -->

<!-- Source: hw/ip/rv_timer/doc/interfaces.md -->

# Hardware Interfaces

<!-- BEGIN CMDGEN util/regtool.py --interfaces ./hw/ip/rv_timer/data/rv_timer.hjson -->
Referring to the [Comportable guideline for peripheral device functionality](https://opentitan.org/book/doc/contributing/hw/comportability), the module **`rv_timer`** has the following hardware interfaces defined
- Primary Clock: **`clk_i`**
- Other Clocks: *none*
- Bus Device Interfaces (TL-UL): **`tl`**
- Bus Host Interfaces (TL-UL): *none*
- Peripheral Pins for Chip IO: *none*

## [Inter-Module Signals](https://opentitan.org/book/doc/contributing/hw/comportability/index.html#inter-signal-handling)

| Port Name     | Package::Struct               | Type    | Act   |   Width | Description                                                                                                                          |
|:--------------|:------------------------------|:--------|:------|--------:|:-------------------------------------------------------------------------------------------------------------------------------------|
| racl_policies | top_racl_pkg::racl_policy_vec | uni     | rcv   |       1 | Incoming RACL policy vector from a racl_ctrl instance. The policy selection vector (parameter) selects the policy for each register. |
| racl_error    | top_racl_pkg::racl_error_log  | uni     | req   |       1 | RACL error log information of this module.                                                                                           |
| tl            | tlul_pkg::tl                  | req_rsp | rsp   |       1 |                                                                                                                                      |

## Interrupts

| Interrupt Name             | Type   | Description                                          |
|:---------------------------|:-------|:-----------------------------------------------------|
| timer_expired_hart0_timer0 | Event  | raised if hart0's timer0 expired (mtime >= mtimecmp) |

## Security Alerts

| Alert Name   | Description                                                                                                |
|:-------------|:-----------------------------------------------------------------------------------------------------------|
| fatal_fault  | This fatal alert is triggered when a fatal TL-UL bus integrity fault is detected inside the RV_TIMER unit. |

## Security Countermeasures

| Countermeasure ID      | Description                      |
|:-----------------------|:---------------------------------|
| RV_TIMER.BUS.INTEGRITY | End-to-end bus integrity scheme. |


<!-- END CMDGEN -->

<!-- Source: written for NNC Pipeline (not OpenTitan) -->

# ot_rv_timer_nnc: integration of the OpenTitan rv_timer for verification

Written for NNC Pipeline. This document describes the verification top `ot_rv_timer_nnc`: the OpenTitan
`rv_timer` (specified by the OpenTitan parts of this document, above) plus a thin wrapper that flattens its struct
ports and closes two protocols. The behaviour of `rv_timer` itself is specified only by the OpenTitan
documents; this document adds the port mapping, the fixed configuration and what the wrapper does.

Normative references:
- the OpenTitan parts of this document (above): the timer, its registers, interrupt and alert.
- `standards/opentitan_tlul_bus_specification.md`: the TL-UL bus, including the bus integrity scheme.
- `standards/opentitan_comportability.md`: interrupt and alert conventions of OpenTitan peripherals.
- `standards/opentitan_register_tool.md`: register access types and bus error responses of generated register blocks.
- `standards/opentitan_alert_handler_theory_of_operation.md`: the differential alert handshake and the alert receiver.

## 1. Configuration

[INT-CFG-001] The design under verification has one hart and one timer (`N_HARTS` = 1, `N_TIMERS` = 1), as
stated in the rv_timer Features and Theory of Operation sections.

[INT-CFG-002] RACL (register access control) is disabled: every register access is permitted, and no access is
rejected for an access-control reason.

[INT-CFG-003] The alert sender of `rv_timer` and the alert receiver of the wrapper both use the synchronous
clocking scheme (no synchronizer flops on the differential pairs). Ping requests are never issued.

[INT-CFG-004] There is no design parameter to vary: every run uses this one configuration.

## 2. Clock and reset

[INT-CLK-001] `clk_i` is the only clock. All inputs are sampled and all outputs change at its rising edge,
except for the effect of `rst_ni`.

[INT-RST-001] `rst_ni` is the active-low reset, asserted asynchronously and released synchronously to `clk_i`
(the reset strategy of the comportability specification). While `rst_ni` is 0, every register holds its reset
value as given in the register tables of the rv_timer specification.

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
| `i_a_address` | input | 32 | TL-UL `a_address` (byte address; the register offsets of the rv_timer specification are relative to 0) |
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
| `o_intr_timer_expired` | output | 1 | Interrupt `timer_expired_hart0_timer0` |

## 4. TL-UL device interface

### 4.1 Mapping

[INT-TL-001] The `i_a_*`, `o_a_ready`, `o_d_*` (except `o_d_intg_err`) and `i_d_ready` ports are the fields of the
same name of the TL-UL device interface `tl` of `rv_timer`, with the meaning given by the TL-UL bus specification.

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
command integrity error: a fatal TL-UL bus integrity fault in the sense of the rv_timer Security Alerts table,
which triggers the `fatal_fault` alert (section 5). These documents do not specify the D-channel response to
such a request.

### 4.3 Response integrity

[INT-INTG-003] The wrapper checks `d_user.rsp_intg` of every D-channel beat against the response fields with
OpenTitan's response integrity checker for TL-UL hosts. `o_d_intg_err` is 1 in a cycle where
`o_d_valid` is 1 and this check fails, and 0 otherwise. A correct device never makes it 1.

## 5. Alert

[INT-ALERT-001] `rv_timer` has one alert, `fatal_fault`, sent through an alert sender. The wrapper connects it
to an alert receiver as described in the alert handler theory of operation (Differential Alert Signaling).
`o_alert` is the `alert_o` output of that receiver: it is 1 for one clock cycle for each alert handshake that
the receiver detects.

[INT-ALERT-002] `o_alert_integ_fail` is the `integ_fail_o` output of the receiver. A correct sender never makes
it 1.

[INT-ALERT-003] A fatal alert is repeated until reset (comportability specification, Alerts per Module), so
after a bus integrity fault `o_alert` pulses repeatedly until `rst_ni` is asserted. A write of 1 to
`ALERT_TEST.fatal_fault` triggers one alert event, as the register description says.

## 6. Interrupt

[INT-INTR-001] `o_intr_timer_expired` is the interrupt output `intr_timer_expired_hart0_timer0_o` of
`rv_timer`, an event-type interrupt as defined in the comportability specification, with the registers
`INTR_ENABLE0`, `INTR_STATE0` and `INTR_TEST0`.

## 7. Verification scope

[INT-VER-001] The verification shall cover, through the ports above: reset values of every register; the
access type of every register field as given in the register tables (rw, rw1c, wo, rw0c); the tick generator (prescaler) and the step; counting
of the 64-bit timer value, including writes to it and the carry from the lower to the upper half; the compare
and the interrupt (state, enable, test, clearing by writing the compare registers); `ALERT_TEST` with its
`regwen` field; bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity
errors) and the `fatal_fault` alert.

[INT-VER-002] The 64-bit timer value cannot be run through its whole range in simulation. Behaviour close to
2^64 shall be reached by writing the timer value registers.

## 8. Decisions for verification

These decisions answer questions that the documents above leave open (gaps found by `nnc spec-lint` before
gate G1, and the open questions of the rule review). They were made by Claude on the delegation of the
project owner (GabrielHCMUT), on 2026-11-20, from the documents only; they are **not** OpenTitan requirements
and not a hardware designer's review. Where the documents do not decide a behaviour, the decision is that the
verification does not demand one reading: it checks only what every reading has in common, or a bound.
The numeric bounds in this section are verification bounds chosen to be generous, not timing requirements of
rv_timer.

| ID | Question | Decision |
|---|---|---|
| D-001 | Tick period (gaps 004, 005; question 1) | With `CTRL.active_0` = 1 and `CFG0` unchanged, the timer value increases by `CFG0.step` (modulo 2^64) once every `CFG0.prescale` + 1 cycles (the 48 MHz example: prescale 47 gives a tick every 48 cycles), so prescale 0 gives a tick every cycle. The cycle of the first tick after `active_0` becomes 1 is not specified; it shall come no later than `CFG0.prescale` + 1 + 4 cycles after the write response. |
| D-002 | Changing `CFG0` or writing the timer value while active (gaps 005, 006; question 4) | A software obligation (Programmer's Guide). Tests write `CFG0` and `TIMER_V_*` only while `CTRL.active_0` = 0. Behaviour after such a write while active is not checked. |
| D-003 | Interrupt event (gap 001; question 2) | The event is the condition mtime >= mtimecmp (the interrupt description, and Event type in the comportability specification: "if the event itself is still active, the INTR_STATE register will return to true"). While the condition holds and the timer is active, `INTR_STATE0.IS_0` shall read 1 within 4 cycles after a write of 1 to it. |
| D-004 | Expiry while inactive (gap 003) | Not specified. `INTR_STATE0` and the interrupt are not checked while `CTRL.active_0` = 0 with mtime >= mtimecmp. |
| D-005 | Latencies (gap 007; question 2) | When the condition becomes true by a tick, `IS_0` shall be 1 no later than 4 cycles after that tick; when it becomes true by a register write while active, no later than `CFG0.prescale` + 1 + 4 cycles after the write response. `o_intr_timer_expired` shall equal `IS_0` AND `IE_0` except in the 2 cycles after either changes. |
| D-006 | Clearing by a compare write (gap 002; question 3) | A write to `COMPARE_LOWER0_0` or `COMPARE_UPPER0_0` after which mtimecmp > mtime (and stays so) shall leave `IS_0` = 0 and the interrupt 0 within 4 cycles. If mtime >= mtimecmp still holds after the write, `IS_0` shall be 1 again within 4 cycles; a dip in between is not checked. |
| D-007 | Software write to `INTR_STATE0` at the same time as an expiry (question 17) | Software has precedence for that cycle; if the condition still holds, `IS_0` returns to 1 (register tool, simultaneous access). Only the result after 4 cycles is checked. |
| D-008 | Reads of write-only fields and reserved bits (gap 019; questions 5, 6, 7) | A wo field has no read path (register tool, Type WO): it reads 0. Reserved bits read 0 and writes to them have no effect. After reset `INTR_TEST0` reads 0x0 and `ALERT_TEST` reads 0x8000_0000. |
| D-009 | `ALERT_TEST` (gaps 008, 009; questions 10, 18) | Tests that trigger an alert write 0x8000_0001 (regwen kept at 1); the combined write 0x0000_0001 is not used. A write with bit 31 = 0 sets `regwen` to 0 until reset; afterwards a write of 0x8000_0001 completes with `d_error` = 0, triggers no alert, and `regwen` still reads 0. One write of 1 to `fatal_fault`, with no other alert cause and no other such write within 32 cycles, gives exactly one `o_alert` pulse, no later than 16 cycles after the write response. For writes closer together, at least one pulse and no more pulses than writes. |
| D-010 | Fatal alert after a command integrity error (gap 010; questions 9, 11) | `o_alert` shall pulse no later than 16 cycles after the request with `i_a_intg_flip` = 1 is accepted, and then at least once in every 32 cycles until `rst_ni` is asserted. The D-channel response to that request and the behaviour of later requests are not checked; the test bench does not wait more than 32 cycles for that response. After such a test, the test resets the design. |
| D-011 | Instruction fetches (gap 011) | Not stated for registers in these documents. A request with `i_a_instr` = 1 is not checked for `d_error`; a write with `i_a_instr` = 1 is not used. |
| D-012 | Address decoding (gap 012; question 16) | Following the register tool example (registers up to 0x84 use 8 address bits), the registers 0x0..0x11c use the offsets 0x000..0x1FF. A request to an unmapped offset in 0x000..0x1FF returns `d_error` = 1 and changes no register. Requests at 0x200 and above are not used. |
| D-013 | Sub-word and partial writes (gap 013; question 14) | Per the register tool: a write is an error when it is smaller than the register, where the register width is set by its highest field bit, or when its size is below 32 bits and the address is not 4-byte aligned. Checked cases: full-word writes with mask 1111 succeed; a byte write (a_size 0, mask 0001, offset aligned) to CFG0, TIMER_V_*, COMPARE_* or ALERT_TEST returns `d_error` = 1 and changes nothing; a byte write to byte 0 of CTRL, INTR_ENABLE0, INTR_STATE0 or INTR_TEST0 completes with `d_error` = 0 and has the effect of the write. Non-contiguous masks and other sub-word cases are not checked. Reads of any size return the full register (register tool). |
| D-014 | Outstanding requests and back-pressure (gap 015) | TL-UL allows several outstanding requests and does not guarantee order. The test bench matches responses by `d_source`, uses a distinct `a_source` per outstanding request, and does not assume `o_a_ready` = 1. A read of `TIMER_V_*` while active is checked only to lie between the values before the request and after the response. |
| D-015 | Fields of a response (gap 016) | Checked: `d_error`, `d_source` (echo of `a_source`), `d_size` (echo of `a_size`), `d_opcode` (AccessAckData for Get, AccessAck for PutFullData and PutPartialData). `d_data` is checked only for a Get without error. For an undefined opcode only `d_error` = 1 is checked. `d_param` and `d_sink` are not checked. |
| D-016 | Reset (gap 018; question 8) | The test bench keeps `i_a_valid` = 0 while `rst_ni` = 0 and in the first cycle after release. While `rst_ni` = 0, `o_d_valid`, `o_alert`, `o_alert_integ_fail` and `o_intr_timer_expired` shall be 0; `o_a_ready` is not checked. A response pending at reset is discarded. The rule that outputs change only at rising clock edges is not applied in cycles where `rst_ni` is 0 or falls. |
| D-017 | Integrity outputs | `o_d_intg_err` and `o_alert_integ_fail` shall be 0 in every cycle with `rst_ni` = 1 (a correct device and sender never set them), including during a test with `i_a_intg_flip` = 1. |
| D-018 | Natural carry at 2^32 and behaviour near 2^64 (question 12) | Reached only by writing the timer value registers (while inactive) to values close to the carry, then counting. |
| D-019 | Out of scope (questions 13, 15; gaps 017, 020) | User-bit default values, Status-type interrupts (rv_timer has none), requests with a non-zero `a_param`, and the bit layout of `a_user`/`d_user` (the wrapper produces them) are not checked; tests drive `i_a_param` = 0. |
| D-020 | Access type of `INTR_STATE0.IS_0` (gap 014) | The register tables bind: `IS_0` is rw1c. The hjson text in the Theory of Operation is an example for two harts and two timers, not this configuration. |
