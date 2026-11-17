# NNC IP specification template

A specification written in this shape can go through the whole flow without hand work: `nnc ingest` splits it
into numbered sections and sentences, the contract stage reads the port and parameter tables, `nnc params`
reads the legal values, and the rule extractor cites every requirement by section. `nnc spec-draft` writes a
first version in this shape from a short design description, and `nnc spec-check` checks the shape.

Rules for the text:
- Number every section (`## 4 Parameters`, `### 7.2 Write path`). Keep one topic per section.
- Write each requirement as one sentence with **shall** (must hold) or **should** (recommended), with an ID in
  brackets at the start: `[REQ-WR-003] The FIFO shall ...`. One behaviour per sentence; name signals exactly.
- Say what happens in every case, including errors, back-pressure, reset in the middle of an operation, and
  parameter extremes. A gap in the specification becomes an open question at gate G1.
- Do not describe the implementation unless it is a requirement (for example a synchronizer depth). The
  verification is generated from this text only.

---

# `<IP name>` Design Specification

Revision: `<x.y>`, `<date>`. Top module: `<m_top>`.

## 1 Overview

### 1.1 Purpose
What the block does, in two or three sentences.

### 1.2 Features
A list of the features.

### 1.3 Out of scope
What the block does not do (so that nobody tests for it).

## 2 References

| ID | Document | Revision | Used for |
|---|---|---|---|
| REF-001 | `<standard>` | `<issue>` | `<which part>` |

## 3 Terms

| Term | Meaning |
|---|---|

## 4 Parameters

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| PARA_X_DATA_W | 32 | 8, 16 or 32 | Data width in bits |
| PARA_X_DEPTH | 8 | Power of 2, minimum 2 | Number of entries |
| LPARA_X_ADDR_W | Derived | - | $clog2(PARA_X_DEPTH) |

Legal values in one of the forms the flow checks: `0 or 1`, `8, 16 or 32`, `1 to 32`, `Minimum 2`,
`Power of 2, minimum 2, no upper limit`, `0 to PARA_X_DATA_W`. Anything else after a `;` is kept as a note.
A derived parameter has `Derived` as default and its formula in the Description column.

## 5 Interface

**`<m_top>`**: all ports (`<CLK-DOMAIN>`)

| Port | Direction | Width | Signal type | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|---|
| i_clk | input | 1 | Clock | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Reset (asynchronous assertion, synchronous release) | Not applicable | CLK | Active-low reset |
| i_x_valid | input | 1 | Data | 0 | CLK | ... |
| o_x_data | output | PARA_X_DATA_W | Data | 0 | CLK | ... |

Inputs start with `i_`, outputs with `o_`; active-low signals end with `_n`. A width is a number or a
parameter name. The reset value column gives the value of each output while reset is asserted.

## 6 Clocks and resets

### 6.1 Clocks
Each clock, its domain and the relation between clocks (one clock; synchronous; asynchronous).

### 6.2 Resets
Assertion and release of each reset, which state it clears, and what happens to an operation in progress.

## 7 Functional description

### 7.1 `<first function>`
Requirements with IDs, for example `[REQ-FUNC-001] When i_x_valid is 1 and o_x_ready is 1 at a rising edge
of i_clk, the block shall ...`.

### 7.n `<further functions>`

## 8 Timing and protocol

Latency and throughput of each operation, back-pressure, ordering, and a cycle-by-cycle example of the main
transfer (a table of cycles and signal values).

## 9 Registers

Only if the block has software-visible registers.

| Offset | Name | Field | Bits | Access | Reset | Description |
|---|---|---|---|---|---|---|

## 10 Errors and corner cases

Each error condition, how it is detected, and the response. Behaviour at parameter extremes.

## 11 Configurations

| ID | Parameter values | Purpose |
|---|---|---|
| CFG-BASE | defaults | main configuration |
| CFG-MIN | PARA_X_DEPTH=2 | smallest legal |

The verification runs every configuration listed here (`run_set.json`).

## 12 Verification requirements

What the environment of the block guarantees (protocol obligations of the blocks that drive the inputs),
which internal behaviour is observable only through the ports, and any check that needs a special setup.

## 13 Implementation constraints

Target clock frequency, area budget, technology (for example GF180MCU), coding rules (`docs/RTL_RULES.md`).

## 14 Decisions and open questions

| ID | Question | Decision | By | Date |
|---|---|---|---|---|
