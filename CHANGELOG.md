# Changelog

Measurements for every phase are in [docs/EVALUATION.md](docs/EVALUATION.md). The design notes are in Vietnamese, in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Planned work is in [docs/ROADMAP.md](docs/ROADMAP.md).

No release contains a G4 sign-off. G1–G3 were approved by an AI assistant on the owner's delegation, and each
approval is recorded as delegated. See [docs/G4_REVIEW_REQUEST.md](docs/G4_REVIEW_REQUEST.md).

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
