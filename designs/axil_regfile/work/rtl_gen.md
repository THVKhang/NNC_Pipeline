# RTL generation report: axil_regfile

Status: **clean** after 1 attempt(s) (agent A15, opus, rtl-v1); cost US$1.06.
Remaining findings: 0 errors, 0 warnings, 1 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 47804.8704 | 16884.13 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 47389.9776 | 31490.02 |

Generic cells: 1075. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 141 of 193 (73.1 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

RF-1.2-04, RF-10.2-05, RF-11-01, RF-11-02, RF-11-03, RF-11-04, RF-11-05, RF-12.1-01, RF-12.1-02, RF-12.1-03, RF-12.1-05, RF-12.1-06, RF-12.1-07, RF-12.1-08, RF-12.1-09, RF-12.1-10, RF-12.1-11, RF-12.2-02, RF-12.2-03, RF-12.2-04, RF-12.2-05, RF-12.3-01, RF-12.3-02, RF-12.4-01, RF-12.4-02, RF-12.4-03, RF-12.4-04, RF-12.4-05, RF-12.4-06, RF-12.4-07, RF-12.4-08, RF-12.4-09, RF-12.4-10, RF-12.4-11, RF-12.4-12, RF-13-01, RF-13-02, RF-13-03, RF-13-04, RF-13-05, RF-13-08, RF-13-09, RF-14-06, RF-14-13, RF-14-14, RF-3-02, RF-4-01, RF-4-02, RF-4-04, RF-4-07, RF-7.4-09, RF-7.5-15

</details>

## Lint waivers (RR-40)

- m_axil_regfile.sv:91 // WAIVER: awprot, arprot and address bits [1:0] are ignored by the specification (sections 1.3, 7.1) // verilator lint_off UNUSEDSIGNAL

## Open points stated by the agent

- Section 4 / REQ-PAR-003 (RF-4-06, SHOULD): RR-11 does not allow system tasks, so the parameter range check uses an elaboration-time $error inside `ifndef SYNTHESIS`. I read REQ-PAR-003 as the specification asking for this behaviour. Yosys defines SYNTHESIS, so synthesis skips the check. Verilator lint and simulation still run it.
- Section 5 / REQ-PAR-002: LPARA_REGS_W is a localparam in the module body, equal to PARA_NUM_REGS*32. The o_regs port width is written as PARA_NUM_REGS*32 rather than LPARA_REGS_W, because tools differ on accepting a localparam in the ANSI parameter port list. The width is the same; o_regs is driven from an internal vector declared with LPARA_REGS_W.
- Sections 7.4 / 7.5 (REQ-WR-027, REQ-RD-014): outside reset, o_s_axi_bresp, o_s_axi_rdata and o_s_axi_rresp keep the value of the last response while their valid is 0. They are reset to 0 (OKAY / 0x0) as REQ-RST-002 requires.
- Section 13 (REQ-IMP-004): I chose to reset the held write-transaction payload (decoded address, wdata, wstrb) asynchronously to 0, because it counts as 'transaction state'. This is the cautious choice, although a valid bit already qualifies these values.
- Section 1.3 / 7.1: i_s_axi_awprot, i_s_axi_arprot and address bits [1:0] are unused, as the spec requires. The Verilator UNUSEDSIGNAL warning is waived with a `// WAIVER:` comment on a single XOR-reduced sink signal named `unused_inputs`.
- Section 7.1 (decode): a write's decoded result (register hit, mapped flag, 4-bit register number) is stored at the AW transfer instead of the full address. This keeps storage small (section 13 storage guidance), and the behaviour is the same as decoding the stored address at Ec.
- Section 7.3 (REQ-WR-017 / REQ-ERR-004): a write with wstrb = 4'b0000 is handled like any other write. It completes at Ec with the normal bvalid timing and the normal response, and no byte lane is enabled, so no register bit changes.

## Findings

| Severity | Rule | Where | Message |
|---|---|---|---|
| info | RR-10 | m_axil_regfile.sv:74 | simulation-only code (not under SYNTHESIS): not synthesized; reviewer: check it models only what the specification asks for |

## Attempts

- 0: {'error': 0, 'warning': 0, 'info': 1} (changed m_axil_regfile_dec.sv, m_axil_regfile.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve axil_regfile D2_rtl --by "<name>" --note "..."`.
