# Inputs the flow accepts

This page answers one question: *does the flow work with any specification and any RTL?*

No tool can promise that for every input. The flow is built so that **no input gives a silently wrong
result**:
- every input gets a verdict before any agent runs (`nnc intake`);
- the inputs that need it are adapted by generated, recorded code (`nnc adapt`);
- how far this reaches is measured on open-source RTL the flow was not written for (`nnc corpus`).

## Verdicts

| Verdict | Meaning | What happens next |
|---|---|---|
| ready | The flow runs on the input as it is. | The usual flow (GUIDE.md). |
| adapt | The flow runs after a generated adaptation. | `nnc adapt` copies the library files, writes a wiring-only wrapper and the interface document. All of it is shown at Gate 1. |
| needs_input | The inputs leave something open. | The report names it: a library folder (`--lib`), a parameter value, the top among several candidates, a specification the flow cannot read. |
| unsupported | The flow cannot run on the input. | The report says why: VHDL, encrypted source, a port type with no adapter. |

## RTL

| Input | Handling | Evidence |
|---|---|---|
| Verilog-2001, SystemVerilog (packages, typedefs, generate, type parameters, assertions) | Verilator reads it. Formal and CDC read it with the Yosys Verilog frontend, or with yosys-slang when that frontend fails. The intake picks the frontend. | corpus; ot_gpio, ot_rv_timer |
| Files spread over folders | Closure of the top over library folders (`--lib`), packages first in dependency order, include folders. `nnc adapt` copies the files unchanged and records their SHA-256. | tests/test_intake.py; corpus (common_cells + tech_cells_generic) |
| Top not given | The one module that no other module instantiates. If there are several, the verdict is needs_input with the list. | tests/test_intake.py |
| Plain vector and enum ports | Driven directly. | |
| Packed struct or union ports, packed arrays of structs, unpacked arrays | Wrapper `<top>_nnc`, wiring only: one port per field or element. At time 0 the simulation stops if a DUT port has another width than the one the wrapper was made for. | gpio raw top (7 struct ports); corpus |
| Ports under `` `ifdef ``, Verilog-1995 port lists | The port reader of the simulation evaluates `` `ifdef ``/`` `ifndef ``/`` `else `` with the run's macros, and reads directions from the body. | picorv32 (`RISCV_FORMAL` ports); tests |
| Ports of a user type (`input data_t x`) | The port name is the last identifier of the declaration, whatever the type. | common_cells |
| Package imports in the module header | Skipped by the port reader; Verilator, Yosys and slang read them. | common_cells (`cc_lzc`) |
| A vector of clocks (`input [1:0] clks_i`) | The wrapper splits it into one clock port per bit; the bits that clock flops are clocks in the interface document. | common_cells (`cc_clk_mux_glitch_free`) |
| Parameters wider than 32 bits, enum or type parameters | The contract and the test bench declare parameters as `parameter int`. These parameters keep the default of the RTL; the interface document lists them and says why. To verify another value, the specification must give it as a 32-bit integer, or a configuration of the RTL must set it. | verilog-axi (`M_ADDR_WIDTH`, 128 bits), common_cells (`Mode`, an enum) |
| Combinational design (no clock) | Test-bench clock `nnc_clk`, connected to nothing in the DUT. Tests drive inputs and checkers sample on it. | corpus (priority_encoder, lzc, popcount, ...) |
| Several clocks | The specification must say whether they are synchronous. The CDC check (`nnc cdc`) classifies the crossings. | async_gray_fifo, async_apb_bridge |
| Latches, tri-state, falling-edge flops, gated or derived clocks | Listed as notes: simulation and formal run; tri-state behaviour is not checked; derived clocks are listed by the CDC check. | |
| Module of another library missing | needs_input, naming the module. | corpus (`tc_sync`) |
| Top parameter without default | needs_input, naming the parameter. | corpus |
| Code Verilator rejects | needs_input, with Verilator's first error. | corpus (wb2axip `axi2axi3`) |
| Code Verilator reads but cannot simulate (`Unsupported:` errors such as BLKANDNBLK) | The first simulation build stops with Verilator's error. The flow does not change the RTL; another simulator would be needed. | corpus (verilog-axi `axi_vfifo_dec`) |
| Interface port on the top, unpacked struct port, real or string port | unsupported: no adapter yet. | tests |
| VHDL, mixed VHDL and Verilog, encrypted (`` `pragma protect ``) | unsupported. VHDL files next to Verilog ones are ignored, with a note. | neorv32 |

## Specification

| Input | Handling |
|---|---|
| Markdown, plain text | Read directly; tables are read. Headings may be `#` lines or underlined with `===`/`---` (setext, as in picorv32's README). |
| PDF with a text layer | Read with pdftotext, without tables. The port table then comes from the interface document of `nnc adapt`, or from a Markdown file. |
| Scanned PDF | Error from `nnc spec-check` and the intake: OCR it first. |
| Word `.docx`, HTML | Converted to Markdown by `nnc/specconv.py` (headings, paragraphs, lists, tables, code). The converted text is what the agents read; the index keeps the hash of the original. |
| AsciiDoc (`.adoc`), as the RISC-V specifications | Converted the same way: section and block titles, role spans and instruction macros of the RISC-V manual, tables with column and row spans, admonitions, listing and diagram source blocks, included fragments found next to the document. A missing include is named in the text. |
| No port table, or one in another form | Given RTL: `nnc adapt` writes the interface document from the port declarations and the netlist. Only names, widths, fields, clocks and resets come from it, never behaviour. No RTL: `nnc spec-draft` (agent A0) drafts the template form. |
| No requirement IDs, not in the template's shape | Accepted (OpenTitan gpio has 0 IDs). Rules cite sentence IDs of the index. |
| English | Normative sentences (must, shall, only, ...) are flagged for the extraction to decide. |
| Vietnamese | The same, with *phải, không được, bắt buộc, chỉ khi, được phép, cấm, luôn, nên*. |
| Other languages | The agents read them, but no sentence is flagged as normative. That is a limit: the extraction then has no list of candidates to account for. |

## Measured on open-source RTL

`nnc corpus` takes every module of six open-source repositories, at fixed commits, as the top of a design. For
each it runs the intake. Then it runs the adaptation in a scratch workspace and the intake of the verified top
again. It reads the interface document back through the contract. It compares the result with the port list
the simulation parses. With `--smoke`, it also builds and runs the flow's test bench with a generic test (clock,
reset, random inputs for 200 cycles) and measures coverage with the design scope.

The sources are fetched into `corpus/.cache` and never committed. `corpus/results.md` lists every design.

| Source | Commit | Licence | Language | Designs | ready | adapted | needs_input | unsupported | chain_failed | smoke pass |
|---|---|---|---|---|---|---|---|---|---|---|
| common_cells | `e73baaec2c` | SHL-0.51 | SystemVerilog (packages, type parameters, interfaces, assertion macros) | 108 | 100 | 7 | 1 | 0 | 0 | 94/107 |
| verilog-axi | `516bd5dadc` | MIT | Verilog-2001 (AXI4 and AXI4-Lite, many parameters) | 55 | 55 | 0 | 0 | 0 | 0 | 53/55 |
| verilog-uart | `1b867e53af` | MIT | Verilog-2001 | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 |
| wb2axip | `2e8d3bc2d2` | Apache-2.0 | Verilog with formal properties (Wishbone, AXI, APB bridges) | 63 | 61 | 0 | 2 | 0 | 0 | 61/61 |
| picorv32 | `ef203c2b0a` | ISC | Verilog (a RISC-V CPU in one file) | 8 | 8 | 0 | 0 | 0 | 0 | 8/8 |
| neorv32 | `61c1428dae` | BSD-3-Clause | VHDL (the flow must refuse it) | 1 | 0 | 0 | 0 | 1 | 0 | 0/0 |
| **all** | | | | **238** | **227** | **7** | **3** | **1** | **0** | **219/234** |

Why a design stops (first reason per design):

| Reason (first one per design) | Designs |
|---|---|
| top parameter without default | 1 |
| Verilator rejects the RTL | 1 |
| unit of another library missing | 1 |
| VHDL source | 1 |

Of the 238 modules, **232** reach a running test bench with the generic smoke test: 219 pass it (median line coverage 92.8 % from 200 cycles of random inputs; that figure only shows the bench drives the design), and in 13 an assertion of the design stops the run because random inputs break a rule of its inputs (no push into a full FIFO, no clear while valid). Tests written from the specification drive legal inputs. 2 use a construct Verilator does not support (BLKANDNBLK), 3 need an input the repository does not give, and 1 is VHDL. chain_failed (a fault of the flow after the intake): 0.

What the corpus shows: on code the flow was not written for, the steps up to a running test bench work for
these shares. Every stop is named, so none is silent.

What it does not show:
- **The quality of the verification of these designs.** The smoke test checks that the machinery builds and
  runs, not that the design is right. The quality of agent-generated verification is measured on the 13 designs
  of [EVALUATION.md](EVALUATION.md): mutation score, bug benchmark, formal, stability.
- **The agent steps on these designs.** Running them end to end with agents costs about US$3-15 per design,
  so that is a separate step.
- **Large designs.** The largest top of the corpus is a small RISC-V CPU (picorv32). SoC-level tops with
  hundreds of files are not in it.

## Faults of the flow found by the corpus, and fixed

| Fault | Where | Fix |
|---|---|---|
| Synchronous resets were never found: the intake netlist kept them as a flop behind a multiplexer, so the interface document typed `rst` as data and the contract had no reset | verilog-uart, verilog-axi, picorv32 (found while preparing the blind run, 21.6) | `opt_dff` in the intake netlist |
| AsciiDoc specifications could not be read | the RISC-V M extension (21.6) | `specconv.adoc_to_markdown` |
| Setext headings (`Title` over `-----`) were read as paragraph text, so a section merged into the one before | picorv32 README (21.6) | the Markdown reader turns them into headings |
| Ports under `` `ifdef `` counted as DUT ports | picorv32 (`rvfi_*` under `RISCV_FORMAL`) | `sim.preprocess`: the port reader evaluates conditional compilation |
| Port of a user type read as a port named after the type | common_cells (`parameter type data_t`) | `sim.dut_ports`: the name is the last identifier |
| A package import in the module header (`module m import p::*; #(...)`) hid every port | common_cells (`cc_lzc`, `cc_cdc_reset_ctrlr`) | `sim.dut_ports` skips header imports and the lifetime keyword |
| Negative bit indices (`[W-1:0]` with W = 0 is `[-1:0]`) crashed the coverage scope | wb2axip (`axissafety`, `C_AXIS_USER_WIDTH = 0`) | `coverage._expand` reads signed ranges |
| A parameter wider than 32 bits was passed as a decimal literal and cut to 32 bits, so the DUT's own parameter checks stopped the simulation | verilog-axi (`axil_crossbar`, `M_ADDR_WIDTH`) | `intake.contract_param`: only 32-bit integer parameters are passed; the others keep the RTL default |
| An enum parameter was passed as an integer (Verilator ENUMVALUE error) | common_cells (`cc_lzc`, `cc_stream_arbiter`) | same |
| A clock vector was taken as one clock (cocotb cannot clock a vector) | common_cells (`cc_clk_mux_glitch_free`) | kind `clock_vector`: one clock port per bit in the wrapper |
| Designs without a clock not supported | common_cells, verilog-axi, wb2axip | virtual clock `nnc_clk` (contract, test bench top, conformance, equivalence, RTL generation) |
| Asynchronous reset not found in yosys-slang netlists | ot_gpio | `$aldff` with a constant load value is an asynchronous reset |
| A missing include in an `` `ifdef `` branch not compiled made the verdict needs_input | ot_gpio (`prim_assert`) | a note when the tools read the RTL |
