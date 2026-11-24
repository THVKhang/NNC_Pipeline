# Changelog

Measurements for every phase are in [docs/EVALUATION.md](docs/EVALUATION.md). The design notes are in Vietnamese, in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Planned work is in [docs/ROADMAP.md](docs/ROADMAP.md).

No release contains a G4 sign-off. G1–G3 were approved by an AI assistant on the owner's delegation, and each
approval is recorded as delegated. See [docs/G4_REVIEW_REQUEST.md](docs/G4_REVIEW_REQUEST.md).

## Unreleased

### Waveforms are no longer committed
- The 50 `.vcd` traces (formal counterexamples, non-equivalent mutants) left git: 1.34 million of the repository's
  lines, 16 of them gpio mutant traces of about 150 000 lines each. Other hardware projects (OpenTitan, cocotb, CVA6,
  VeeR) ignore waveforms too. `nnc formal` and `nnc mutate-equiv` write them again, and `nnc review-kit` copies
  those present on the machine. They stay in the history of earlier commits.

### Parallel tool jobs
- `NNC_JOBS` (default: the CPU count) sets the parallel tool jobs: run-set configurations, SymbiYosys tasks
  (formal, UNR), mutants, and the compiler jobs of each build. `--jobs` on the stage commands; `formal-check` and
  `demo` take `--jobs` (`--workers` stays as an alias). Agent calls keep `--workers` (default 4).

### Phase 23.1: names that differ between Verilator and Yosys
- Packed struct fields: Verilator names a toggle point per field (`tl_i.a_address[3]`), Yosys has one packed net
  (`tl_i`). `coverage.struct_fields` reads the layout of every struct variable from `verilator --json-only` (nested
  structs, enums), and each field point is matched to its bit of the net, for constant bits and for UNR.
- Instances that Verilator merges over a generate loop (`gen_filter[*].u_filter`): a merged point is constant, or
  PROVEN, only if it is in every instance of the netlist.
- Checked on gpio: 2 280 more constant toggle points are matched, and no simulated toggle contradicts any of them
  (no new signal kept whole, no scope conflict).
- UNR records: signals that were not in the netlist are tried again, and names that are no longer candidates
  leave the record.

### Phase 23.2: UNR for designs with a simulation-only model
- Config `unr_cut` (modules): the proofs read the RTL with `formal_defines` and make every output of these
  modules free (Yosys `blackbox` + `cutpoint -blackbox`). This allows more behaviours than any model of those
  modules, the simulated one included, so a PROVEN bit holds in simulation. `unr.cut_check` refuses the cut
  when a file that tests one of those macros defines a module that is not cut.

### Phase 23.3: branches never executed (EVALUATION §15)
- `nnc sim --unr` also proves branches (nnc/unrbranch.py). Each IF branch or case item with no hit gets a
  marker in an instrumented copy of the RTL. In a clocked block the marker is a flop that toggles when the branch
  runs. In a combinational block it is a signal set to 1 there. The copy is used only when Verilator shows every
  marker as the first statement of its branch.
- A branch PROVEN constant after the first reset in every configuration leaves the block metric, and its lines
  leave the line metric when no other point covers them. `branches_executed` counts any PROVEN branch that a
  simulation runs; it is 0 on all 13 designs. Block coverage: ahb2axi_bridge 77.1 → 97.1 %, ot_rv_timer
  87.8 → 99.3 %, ot_gpio 93.6 → 99.5 %. Tests and checks unchanged.
- A PROVEN branch is dead in the RTL as delivered, not necessarily by design. ahb2axi_bridge's AXI burst path
  (WR_BURST, WR_BBURST, `o_axi_awlen`) is proven dead. The cause is its recorded fault 2:
  `reg_burst_fallback` is always set. The G4 reviewer judges each exclusion against the specification
  (`work/unr.md`, review packet checklist).
- UNR tasks have up to 4 control assertions on flops of different signals, and conclude when the guard and one
  control fail. spi_master's `min` configuration had a constant control, so all its tasks were vacuous.
- Instances merged by Verilator over a generate loop are written `u_top_*` in `work/unr.md`. Records of
  configurations that are not in the run set are kept in `unr.json` but not shown.

### Phase 23.4: x_init in every run set
- 14 more run sets have a configuration `xrand` (`"x_init": "random"`, seed 1): all 15 designs now have one. Designs
  that had no run set get one (`base` + `xrand`). The old configurations give the
  same results. The only new failure is ahb2axi_bridge CHK-012, already reported in 0.8.0 (step 23.6).
- A configuration with `"x_init": "random"` is tested as before, but its coverage is not merged: its toggles
  before the first reset are not activity of the design, and they would cover points and undo the constant-bit
  and UNR exclusions.

### Phase 23.5: expression closure of ot_rv_timer
- `nnc cover --metric expression --target 90`, without the pre-verified `prim_*` modules (US$3.44). One closure
  module with 4 tests; 27/27 tests pass. Expression 83.7 → 87.4 %; the target is not met. The analyst claims
  10 point groups are unreachable through the ports (tie-offs, integrity faults the ports cannot inject). They
  are listed in `work/coverage.md` and still counted. G3 approved again (delegated).

### Phase 23.6: CHK-012 of ahb2axi_bridge under x_init
- Triage of this one failure (`work/triage_xrand_chk012.md`, US$1.19) concluded A_rtl_wrong. It is the recorded
  fault 2, not a new fault. A single write also gets `reg_burst_fallback = 1`, so its AWADDR and AWSIZE come from
  the burst table, which has no reset. The table reads as 0 (a wrong but aligned address) when flops start at 0,
  and as a random value under x_init. The RTL was not changed.

### Closure without pre-verified modules
- When a design declares `coverage_preverified`, `nnc cover` (code metrics) takes its target and the uncovered
  points given to the analyst from the coverage without those modules. This matches OpenTitan's `cover.cfg`.
  `nnc sim` now stores those uncovered points (`coverage.without_preverified.uncovered`).

### Phase 24: expression points never hit (EVALUATION §16)
- `nnc sim --unr` also proves expression points (`nnc/unrexpr.py`). Each term combination that no run hit becomes
  a marker wire at module level in an instrumented copy of the RTL. The wire is 1 exactly when the combination
  holds, and is inserted before `endmodule` on the same line, so no line moves. Verilator checks the copy, and
  SymbiYosys proves the marker 0 after the first reset (guard and control as for toggle bits). A point PROVEN in
  every configuration leaves the expression metric. A simulation that hits a PROVEN point is counted
  (`expressions_executed`); it is 0 on every design.
- A combination is tried only when its terms read at module level mean the same as in the expression: no
  function, loop variable, local name, struct member or blocking write by the same block. A bit select is
  allowed only on a packed vector `[H:0]`, because Verilator prints selects of other types in another numbering.
- Chained constant selects that Verilator prints for struct members (`reg2hw[321:312][3:2][0]`) become one
  select (`reg2hw[314]`), which Yosys reads.
- Markers go in batches of at most 20 000 tokens per `endmodule` line (Verilator stops above 40 000; gpio has 616
  markers in one module).
- Results: ot_rv_timer 27 points PROVEN, expression without `prim_*` 87.4 → 91.3 %, so `nnc cover` reports
  `target_met` with no new test. ahb2axi_bridge 71.9 → 82.9 %, sync_fifo 92.8 → 98.5 %, axil_regfile
  95.7 → 100.0 %, ot_gpio 64.9 → 85.0 %. Tests and assertions unchanged.
- The closure report has a `final` row when formal changed the result after the last round, and says for each
  point claimed unreachable whether it is still counted. The G3 reminder is printed only when closure added rounds.
- Limit: only points that no run of any configuration hit are tried; a point hit in one configuration and missed
  in another stays counted.

## 0.8.0 (2026-11-24)

### Phase 19.4: random initial values in run sets (EVALUATION §12)
- Harness fixes for `"x_init": "random"`. At time 0 every input is 0. The concurrent checkers are off until the
  first rising edge of every clock (`NNC_X_INIT` block of `nnc_tb_top`, left out of formal). Resets are inactive
  at time 0 and asserted at 1 ps, so that every copy of a reset net sees one real edge (plusarg `+NNC_X_INIT`,
  `nnc_cocotb.X_INIT`). Runs without x_init are unchanged: all 67 recorded runs of the 15 designs give the same
  results.
- Trial on 15 designs: 14 fail exactly as their record. ahb2axi_bridge fails CHK-012 in addition, most likely a
  new symptom of its recorded A_rtl_wrong fault (a burst table without reset read during the desync).
- uart_lite: run-set configuration `xrand` (9 runs, 20/20 tests, 0 assertion failures).
- `nnc demo --all-runs`: the kit step runs every recorded run of the run set.

### Phase 19.5: formal unreachability of toggle points (EVALUATION §12)
- `nnc sim --unr` (nnc/unr.py): the uncovered toggle bits (no recorded 1->0) are proved constant after the first
  reset with SymbiYosys (`abc --keep-going pdr`; inputs free, the first reset held for two rising edges of every
  clock). Bits PROVEN in every configuration of the run set leave the toggle coverage; counterexamples and time
  limits stay counted. Results in `work/unr.json` (keyed by the RTL hash, the parameters and the macros) and
  `work/unr.md`; every later `nnc sim` applies them. A recorded 1->0 on a proven bit puts its signal back whole.
- Every task carries two assertions that must FAIL, else it concludes nothing: a guard (the checked phase is
  reachable) and a control (a flop output the simulation toggled can change in the model). They caught a bug of
  the first version: with one clock the edge counter never counted, and every proof was vacuous.
- Toggle coverage: sync_fifo 87.7 → 100 %, axi2apb_bridge 86.4 → 100 %, ahb2axi_bridge 75.9 → 84.1 %, ot_gpio
  87.5 → 89.6 %, ot_rv_timer 83.1 → 83.9 %. Tests and checks of the 13 designs are unchanged.
- Not done (ROADMAP phase 23): struct fields, the two asynchronous designs, line and block points.

## 0.7.0 (2026-11-23)

### Phase 21.6: blind runs on the corpus (EVALUATION §14), and the project page
- Three modules of the corpus run end to end by the agents, with only their documentation and no hand edit:
  `c_pcpi_div` (9/9 checks, mutation 100 %), `c_uart` (6/11: the README leaves the overrun behaviour open, kept
  open for G4), `c_axil_ram` (no behaviour documented: 0 rules, the flow stops). Every intervention is in
  `work/blind_run.md`. Agent cost US$5.40.
- AsciiDoc specifications (`.adoc`, the RISC-V manual): `specconv.adoc_to_markdown`.
- Setext headings in Markdown specifications.
- Fix: the intake now finds synchronous resets (`opt_dff` in its netlist). Before, an interface document typed a
  synchronous reset as data. The corpus gives the same results after the change.
- Fix: `nnc intake` and `nnc demo` read an adapted design as the flow does (verified top, interface document).
- `nnc site`: the project page from the committed results; CI job `pages` publishes it on GitHub Pages.

## 0.6.0 (2026-11-23)

### Phase 22: run it in one command (docs/GUIDE.md, Docker and Codespaces)
- `Dockerfile`: Ubuntu 24.04, the OSS CAD Suite release of CI (SHA-256 checked, FPGA place-and-route tools
  removed), cocotb 2.1.0, `nnc` from a wheel, a non-root user. `docker run --rm ghcr.io/thvkhang/nnc_pipeline`
  runs the demo. CI job `docker` builds it, runs the demo inside it and pushes it to GHCR on main.
- `nnc demo <ip>`: the steps of a finished design that need no agent (intake, the reproduction kit of the
  primary run, CDC, formal with `--formal`), each compared with the recorded outcome.
- `nnc demo --replay` and backend `replay`: the stages that read the specification (extract, review, contract)
  replayed from the committed answer cache; a task with no cached answer stops instead of calling a model.
  The answer cache of the 13 designs is now committed (788 answers, scanned for keys and personal data;
  axi_std stays out). Result: extract and review SAME on the 11 designs that ran them, contract SAME on 9; the
  other 4 contracts are NOT_CACHED because the contract prompt changed after their run.
- `.devcontainer/` for GitHub Codespaces and VS Code Dev Containers (CI job `devcontainer`).

## 0.5.0 (2026-11-23)

### Phase 21: any specification, any RTL (docs/INPUT_SUPPORT.md)
- `nnc intake`: a verdict on the inputs before any agent runs: ready, adapt, needs_input or unsupported, each
  with its reason. It finds the top, the closure of the top over library folders (`--lib`), packages in
  dependency order, include folders. It runs Verilator, Yosys and yosys-slang, reads the port types from the
  elaborated tree and the structure (clocks, resets, latches, tri-state, memories) from the netlist. CI checks
  that the 13 designs stay ready.
- `nnc adapt`: copies the library files (SHA-256 recorded), writes a wiring-only wrapper `<top>_nnc` for
  packed struct, packed array and unpacked array ports (the simulation stops at time 0 if a port width changed)
  and the interface document `spec/<top>_interface.md` from the port declarations. That document is the port
  table of the contract only; the extraction agents never read it.
- Combinational designs: the test bench clock `nnc_clk`, connected to nothing in the DUT.
- Specifications in `.docx` and HTML are converted to Markdown (`nnc/specconv.py`). Vietnamese normative words
  are flagged like the English ones. A scanned PDF is an error.
- `nnc corpus`: every module of six open-source repositories at fixed commits (common_cells, verilog-axi,
  verilog-uart, wb2axip, picorv32, neorv32) through intake, adaptation, contract, port check and a smoke
  simulation. 238 modules, 232 reach a running test bench. CI job `corpus`.
- Faults of the flow found by the corpus and fixed: ports under `` `ifdef `` were counted as DUT ports; a port
  of a user type was read as a port named after the type; a package import in the module header hid every
  port; a parameter wider than 32 bits was cut to 32 bits and an enum parameter was passed as an integer
  (such parameters now keep the RTL default); a clock vector was taken as one clock (the wrapper now splits
  it); an asynchronous reset in yosys-slang netlists (`$aldff`) was not found; negative bit indices
  (`[-1:0]`) crashed the coverage scope; a missing include in an inactive `` `ifdef `` branch blocked the
  intake.

## 0.4.0 (2026-11-21)

### Phase 19: coverage of the elaborated design (EVALUATION §12, docs/SIGNOFF_SCOPE.md)
- Every simulation run elaborates the DUT alone with `verilator --json-only` and Yosys. Never-executed points
  of package functions the design never calls, and toggles of bits that constant propagation proves constant,
  are left out of every denominator. The report gives the count over all points next to each figure. Nothing
  is left out by hand; an executed point is always counted; a signal on which the simulator saw a "constant"
  bit toggle counts whole. gpio line 52.5 % -> 96.5 %, rv_timer 24.2 % -> 92.3 %, sync_fifo toggle
  70.6 % -> 87.7 %; the outcomes of all 13 designs are unchanged.
- Config `coverage_preverified`: extra report rows with the coverage without the subtrees of modules verified
  elsewhere (the OpenTitan designs use the list of OpenTitan's cover.cfg).
- Closure: gpio functional 90 % -> 95 % (two tests added; the two points left are claimed unreachable, still
  counted). A closure on another metric no longer overwrites the record of the previous one
  (`work/coverage_<metric>.md`, an "Earlier closure" row in the report).
- Run-set option `"x_init": "random"` (random initial values of unreset variables). Tried, not used in any run
  set yet: see EVALUATION §12.

### Phase 20: clock and reset domain crossings (EVALUATION §13)
- `nnc cdc <ip>`: structural RR-33 check on the flattened Yosys netlist of every parameter set (SYNC,
  SYNC_MULTIBIT, QUALIFIED, UNSYNC, FIRST_STAGE_READ, resets from another domain) -> `work/cdc.md`; `--check`
  compares with the recorded result. Config `cdc_async_inputs` (`port` or `port:PARAM=value`). Report row and
  sign-off condition; flow stage `cdc`; CI job `cdc`. 11 designs clean, 2 for review, 0 violations.

## 0.3.0 (2026-11-21)

### Phase 18: a second OpenTitan IP, stability of the agents
- OpenTitan gpio (EVALUATION §11): four configurations of `GpioAsyncOn` and `GpioAsHwStrapsEn`, the RTL
  unchanged (Apache-2.0, see its NOTICE). 26/26 tests and 13/13 assertions in 5 runs, formal 10 proven and no
  counterexample, 4 verification faults corrected by A17, no hand fix. §11.1 compares with rv_timer, §11.2 with
  the public numbers of OpenTitan's own test benches.
- Fix: with the slang frontend, formal now gives a configuration's parameters to `read_slang -G`; before, every
  check of a parameterised design was ERROR.
- Fix: gate hashes leave out Python caches (`__pycache__/`, `*.pyc`). A cache file in `verif/tests/` made G3 of
  async_apb_bridge and async_gray_fifo look changed on a clean checkout, so CI failed the README table check
  after 0.2.0.
- `nnc stability <run> <run> ...` compares repeated agent runs through the specification sentences their rules
  cite. Measured on uart_lite (EVALUATION §10, `designs/uart_lite/stability/`).
- CI: ot_gpio in the kit and kit-configs jobs, and in formal with one job per configuration.

## 0.2.0 (2026-11-21)

### Phase 17: packaging
- The data files are inside the package (`nnc/data/RTL_RULES.md`, `nnc/data/SPEC_TEMPLATE.md`,
  `nnc/simlib/nnc_cocotb.py`), so `pip install` (not editable) gives a working `nnc`. The `docs/` copies stay the
  source, and a unit test keeps the two equal.
- The version comes from `nnc.__version__`. `nnc --version` prints it.
- The CI job `install` builds the wheel, installs it in a clean virtual environment and runs `nnc doctor` and
  `nnc kit-check` from outside the repository.
- `nnc review-kit <ip>` collects what a G4 reviewer needs for one design into a folder or `.zip`. It does not
  copy licensed standards.
- The README has a table of every design, checked against each design's `work/report.json` by a unit test.

### OpenTitan rv_timer (EVALUATION §9)
- An industrial design: the OpenTitan RTL is unchanged (Apache-2.0, see its NOTICE), with a wrapper written here.
- Formal reads RTL with the yosys-slang plugin (`formal_frontend=slang`, `formal_defines`). Simulation passes
  include directories.
- A checker that samples at the falling clock edge is simulation-only in a one-clock formal model.
- The prompts of the formal-environment agent (A13) and the cover-point agent (A6) show each rule's condition.
- `mutate-equiv`:
  - uses the formal frontend;
  - saves after each mutant and resumes (`--redo` to check all again);
  - runs PDR before BMC.
- The report shows the summary of the mutant equivalence check.

### Phase 16: two designs from a short description (EVALUATION §8)
- spi_master and axil_regfile, made from a description of 31 and 51 lines.
- Mutation counts an `assign` line as executed when the declaration of its target is.

### Phase 15: deeper formal, specification lint (EVALUATION §7.4, §7.5)
- Formal deepens a vacuous check per configuration.
- `nnc spec-lint` (agent A18) lists specification gaps before any code is written.

### Phase 14: verification fixes by an agent (EVALUATION §7.3)
- `nnc fix-verif` (agent A17, which never sees the RTL) corrects verification faults judged B. It works from
  simulation or formal results, with a weakening check, a candidate run and `--apply`. Gate G3 goes stale after
  `--apply`.

### Phases 12 and 13: hardening (EVALUATION §7.1, §7.2)
- The tool host is hardened.
- CI reproduces every recorded run (kit-configs) and reruns formal (`nnc formal-check`).
- `nnc mutate-equiv` proves surviving mutants equivalent, or finds the input that tells them apart.

### Phases 5 to 10: the design half (EVALUATION §6)
- Parameter legality checks, the final configuration and the design gates D1/D2.
- RTL generation (A15) and a repair loop (`fix-rtl`, `close-loop`).
- `restyle` with formal equivalence.
- `spec-draft` and `spec-check`.
- `export` and `derive`.

### Phases 1 to 4 (EVALUATION §1 to §4)
- Generation that follows the configuration, and formal per run-set configuration.
- ahb2axi_bridge.
- A comparison with the hand-written testbenches of the upstream designs.

## 0.1.0

The first flow:
- rules from specifications;
- contract;
- SVA and cocotb generation;
- Verilator runs;
- coverage closure;
- mutation per rule;
- multi-clock designs;
- run sets;
- CI kit check;
- bug benchmark;
- G4 reviewer packet;
- formal with SymbiYosys;
- triage of failures;
- split test generation.
