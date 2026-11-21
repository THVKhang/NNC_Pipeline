# Sign-off scope: what the flow checks, and what it leaves out

NNC Pipeline verifies RTL against its specification. This note covers the checks that an IP sign-off
usually also asks for. For each one it says whether the flow needs it, what the flow does now, and the
plan. The yardstick is OpenTitan's public process, because two designs here are OpenTitan IPs:
- [development stages](https://opentitan.org/book/doc/project_governance/development_stages.html);
- [sign-off checklist](https://opentitan.org/book/doc/project_governance/checklist/index.html);
- the VCS coverage configuration `hw/dv/tools/vcs/cover.cfg` of lowRISC/opentitan.

## What OpenTitan asks of one IP

| Area | OpenTitan item and stage | Required at IP level? |
|---|---|---|
| Lint | LINT_SETUP (D1), LINT_PASS (D2), LINT_COMPLETE (D3) | yes |
| Clock domain crossing | CDC_SYNCMACRO and CDC_SETUP (D2), CDC_COMPLETE (D3) | yes; CDC_SETUP may be waived when no block-level CDC flow exists |
| Reset domain crossing | RDC_SETUP (D2), RDC_COMPLETE (D3) | yes |
| Timing, area | TIMING_CHECK, AREA_CHECK (D2): "done with an FPGA or ASIC synthesis flow" | a synthesis estimate, not sign-off STA |
| Deleted flops | REVIEW_DELETED_FF (D3) | yes, when a block-level synthesis flow exists |
| Place and route | none | no |
| DFT / scan | none | no |
| Code coverage | V2: line, toggle, FSM, branch and assertion at 90 %. V3: 100 %, with reviewed waivers. Pre-verified primitives are left out of the coverage model (cover.cfg) | yes |
| Functional coverage | V2: 90 %. V3: 100 % | yes |
| Formal | FPV: 90 % proven at V2, 100 % at V3, with no undetermined property | for FPV blocks |
| X-propagation | X_PROP_ANALYSIS_COMPLETED (V3) | yes, at V3 |

## Decision per area

### Code coverage: needed, done in phase 19
- **Was:** coverage counted every point Verilator instruments. For the OpenTitan IPs that included
  thousands of points in package functions the design never calls (`prim_secded_pkg` alone held 8 136 of
  21 352 line points of gpio). It also included toggles of bits that cannot change, such as the
  zero-extended upper bits of pointer arithmetic.
- **Now:** the flow measures coverage over the elaborated design. The scope comes from two tool runs on
  the DUT alone, with each run's parameters:
  - `verilator --json-only` gives the package functions the design keeps;
  - Yosys `proc; flatten; opt` gives the bits that constant propagation proves constant.
- **Safeguards:**
  - nothing is left out by hand;
  - a left-out point that was executed is still counted, and reported as a scope conflict;
  - when the simulator records a toggle on a bit the netlist calls constant, none of that signal's bits is
    left out. This happened on gpio's `prim_onehot_check` tree, whose leaves above `OneHotWidth` are tied
    to 0;
  - the 0->1 toggle of a constant-1 bit at time zero (Verilator starts at 0) does not count as a toggle;
  - the report keeps the count over all points next to the scoped one.
- **Second figure:** design config `coverage_preverified` lists modules verified elsewhere, as OpenTitan's
  cover.cfg lists its pre-verified primitives. The report adds the coverage without their subtrees in
  extra rows. This figure is added next to the coverage of the whole design and never replaces it. The
  two OpenTitan designs use OpenTitan's own list.
- **Still open:** points that are unreachable but that constant propagation cannot prove, such as the upper
  bits of a subtraction. A formal unreachability pass (the "UNR" of commercial tools) would settle them;
  it is planned. Until then they count as uncovered.

### Clock and reset domain crossing: needed, done in phase 20 (`nnc cdc`)
- **Why:** OpenTitan requires CDC and RDC at D2/D3. Several designs here cross domains:
  - async_gray_fifo and async_apb_bridge have two asynchronous clocks;
  - sync_fifo and gen_sync_fifo have two synchronous clocks;
  - gpio with `GpioAsyncOn` and uart_lite synchronise asynchronous inputs.
- **Gap:** RTL rule RR-33 ("a signal crosses between clock domains only through the synchronizer the
  specification describes") is checked by review only.
- **Now:** `nnc cdc <ip>` (nnc/cdc.py) runs a structural check on the flattened Yosys netlist of every
  parameter set of the run set, and writes `work/cdc.md`:
  - each flop gets the clock domain of its clock port;
  - every flop whose data cone starts in another domain is a crossing;
  - a crossing is SYNC only into a chain of at least two flops of the destination domain, with no logic
    before the first flop and nothing else reading it;
  - several bits of one register synchronized separately are SYNC_MULTIBIT, for review (gray code or
    handshake needed);
  - data captured under a synchronized control is QUALIFIED, for review;
  - everything else is UNSYNC, an error. So is a first stage read by logic, and so is raw use of a value
    that is also synchronized;
  - asynchronous resets coming from another domain are reported for review (RDC).
- **Inputs:** the contract gives each port its domain. Design config `cdc_async_inputs` declares inputs
  that are asynchronous, optionally per parameter value (gpio: `i_gpio:GpioAsyncOn=1`).
- **Validation:** two synchronizer faults put into a copy of async_gray_fifo are reported:
  - the output taken from the first stage gives FIRST_STAGE_READ;
  - no synchronizer gives UNSYNC.
- **Results on the 13 designs:** 11 clean, and two for review:
  - async_gray_fifo: gray pointers, and read data qualified by them;
  - async_apb_bridge: the request and response payloads, qualified by the synchronized handshake.
- **CI:** the `cdc` job reruns the check and compares it with the recorded result.
- **What it is not:** this is not a commercial CDC tool. It finds missing or misused synchronizers. It does
  not prove gray coding or handshake protocols; formal checks and simulation keep that job.

### Timing and area: an estimate is enough at IP level, exists
- **Requirement:** OpenTitan asks only for a synthesis-based check at D2.
- **What exists:** `nnc rtl-check <ip>` synthesizes with Yosys and maps to GF180MCU in two corners. It
  reports the area in µm² and the longest combinational path in ps (ABC with the Liberty delays, no wires).
  It works on any design, delivered or generated.
- **Not done:** OpenSTA is not in the OSS CAD Suite, so there is no constraint-based STA.
- **Limit:** the number is a sanity check, not timing closure.

### Place and route: not needed
- Not an IP sign-off item. It needs a floorplan, a technology setup and constraints of the chip that
  contains the IP, and it checks implementation rather than the RTL against its specification.
- Out of scope.

### DFT / scan: not needed in this flow
- No OpenTitan IP item. Scan insertion happens at chip level.
- The RTL rules already require the structures that make scan insertion safe:
  - every register on the rising edge of a contract clock, with no derived or gated clock (RR-30);
  - resets only through reset ports (RR-31).
- Out of scope.

### X-propagation: useful, planned (small)
- **Gap:** Verilator is two-state, so a missing reset can hide behind a zero initial value.
- **Plan:** one run-set configuration with `--x-assign unique --x-initial unique` and
  `+verilator+rand+reset+2`, which gives every unreset flop a random value. A test that passes only with
  zeros then fails.
