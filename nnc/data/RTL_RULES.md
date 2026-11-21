# NNC RTL rules

These rules apply to RTL that the flow generates (`nnc gen-rtl`, agent A15) or rewrites (`nnc restyle`). The
agent receives this file. Rules marked **code** are checked by `nnc/rtlcheck.py` after every attempt, and a
violation goes back to the agent. Rules marked **review** are for the person who approves gate `D2_rtl`.

The rules aim at RTL that the open-source tools of the flow accept in the same way: Verilator (lint and
simulation), Yosys (synthesis and formal) and SymbiYosys. A construct that one tool reads differently from
another makes simulation results say nothing about the synthesized circuit.

## Files and interface

| ID | Rule | Checked by |
|---|---|---|
| RR-01 | One module per file. The file is named `<module>.sv`. `rtl/filelist.f` lists every file in compile order, leaf modules first and the top module last. | code |
| RR-02 | The top module has exactly the ports of the contract: same names, directions and widths for the chosen configuration. It has exactly the contract's overridable parameters, with the contract defaults. Derived parameters are `localparam`s computed by the formula of the contract. | code |
| RR-03 | Every file starts with a header comment that names the module's purpose and the specification sections it implements. | review |

## Synthesizable subset

| ID | Rule | Checked by |
|---|---|---|
| RR-10 | No `initial` blocks, no initial values in declarations (`logic x = 0;`), no delays (`#5`), no `force`/`release`, `fork`/`join`, `wait`, events, classes or programs. The one exception is simulation-only code that the specification asks for (for example a metastability model): it goes inside `` `ifndef SYNTHESIS `` … `` `endif `` (or the `` `else `` of `` `ifdef <X>_SYNTHESIS ``), is not checked, and is listed for the reviewer. | code |
| RR-11 | The only system functions are `$clog2`, `$bits`, `$signed`, `$unsigned`, `$high`, `$low`, `$size`. No `$display`, `$finish`, `$random` or other system tasks. | code |
| RR-12 | No `inout` ports, no tri-state values (`'z`, `1'bz`). | code |
| RR-13 | Write SystemVerilog that Yosys `read_verilog -sv` accepts: `typedef enum logic [...]` and packed arrays are fine; avoid interfaces, classes, unpacked structs and packages. | code (the synthesis step reads the RTL) |

## Sequential and combinational logic

| ID | Rule | Checked by |
|---|---|---|
| RR-20 | Registers are written only in `always_ff`, with nonblocking assignments (`<=`) only. Plain `always` and `always_latch` are not used. | code |
| RR-21 | Combinational logic is written with `assign` or `always_comb`, with blocking assignments (`=`) only. Every variable of an `always_comb` gets a value on every path (give defaults at the top of the block), so no latch is inferred. | code |
| RR-22 | No latches, no combinational loops, no signal with more than one driver, no output or used signal without a driver. | code (Yosys `proc` and `check`) |
| RR-23 | Every `case` in combinational logic has a `default` branch. `casex` is not used. `casez` is used only for real wildcard matches. | code (`default` count: warning; `casex`: error) |
| RR-24 | Finite-state machines use an enumerated type (`typedef enum logic [N-1:0]`), a defined reset state, and a `default` that returns to a safe state. | review |

## Clocks and resets

| ID | Rule | Checked by |
|---|---|---|
| RR-30 | A register is clocked by a clock port of the contract, on its rising edge. No derived, divided or gated clocks. | code (the edge signals of every `always_ff`) |
| RR-31 | The only other signal in an `always_ff` sensitivity list is a reset port of the contract, with the edge that asserts it (an active-low reset: `negedge`). A reset is synchronous or asynchronous as the specification says. | code (names); review (style) |
| RR-32 | Each register the specification gives a reset value is reset to that value. A register may stay without reset only where the specification allows it (for example a data payload qualified by a valid bit). | review |
| RR-33 | A signal crosses between clock domains only through the synchronizer structure the specification describes. | review |

## Quality and traceability

| ID | Rule | Checked by |
|---|---|---|
| RR-40 | `verilator --lint-only -Wall` reports no warning for the chosen configuration. A warning that cannot be fixed (for example an input bit the specification leaves unused) may be waived with a `verilator lint_off` comment pragma, but only with a `// WAIVER: <reason>` comment on the same or the previous line. The reviewer sees every waiver. | code |
| RR-41 | A width or count that depends on a parameter is written with that parameter, not as a number computed for the default configuration. | review |
| RR-42 | The block or statement that implements a requirement carries a comment `// REQ: <rule id>[, <rule id>...]` with the IDs of the approved rules (`rules.md`). An unknown ID is an error; the share of rules that are tagged is reported. | code |
| RR-43 | Yosys synthesizes the top module without error. The report gives cell area and an estimated combinational delay on the GF180 open cell library (typical and slow corners). These numbers are estimates without wires, clock-to-output or setup time; they are not a timing sign-off. | code |
| RR-44 | Names say what a signal is (`*_valid`, `*_ready`, `*_cnt`, `reg_*` or `r_*` for registers); no single-letter names except loop indices. | review |

## What the RTL agent sees

The RTL agent works from the specification, the approved rules (G1), the interface and parameters of the
contract (G2), the chosen configuration (D1) and this file. It never sees the verification: not the check
plan of the contract, the SVA checkers, the tests or their results. When a verification failure is
traced to the RTL, the fix agent receives the specification-level description of the fault (what the
specification says and what the RTL does), never the test code. This keeps the RTL and the verification
independent interpretations of the same specification, so a shared misreading is less likely to hide a bug.
