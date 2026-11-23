# Blind run: c_axil_ram (ROADMAP 21.6, 2026-11-23)

The flow on a module it was not written for: `axil_ram` of [verilog-axi](https://github.com/alexforencich/verilog-axi)
(commit `516bd5dadc`, MIT). The specification is what the repository documents about it: the `axil_ram`
section, the common signals and parameters, and the AXI4-Lite interface example of the README.

## Every intervention

| Step | Intervention | By |
|---|---|---|
| Inputs | README excerpt (sections named in `NOTICE.md`). The AXI4-Lite protocol itself is specified by Arm's AMBA specification, which is licensed and cannot be redistributed, so it is not given. | Claude (delegated) |
| Intake | Verdict *adapt*: no port table. `nnc adapt` wrote `spec/axil_ram_interface.md`. | code, no choice |
| G1 | **Not approved.** The extraction found 0 normative sentences and produced 1 rule; the review rejected it. | — |

## Outcome

The documentation describes the module in one sentence ("AXI lite RAM with parametrizable data and address
interface widths") and lists signal names. It states no behaviour, so the flow has nothing to verify. It reports
that and stops, and it invents no behaviour. Verifying `axil_ram` needs the AXI4-Lite specification as a
`standard` document.

Agent cost: US$0.04.
