# Verification contract (Gate 2)

```
interface: 10 ports, 0 parameters, clock clk, reset {'name': 'resetn', 'active_low': True}
checks: 9 {'assertion': 3, 'test': 6}  rules 23: in checks 7, not verified 16, uncovered 0 (after first pass 0), unknown IDs 0
calls: 1 (0 cached)  cost US$0.2691
```

## Interface

| Port | Dir | Width | Type |
|---|---|---|---|
| clk | input | 1 | Clock |
| resetn | input | 1 | Reset (synchronous, active low) |
| pcpi_valid | input | 1 | Data |
| pcpi_insn | input | 32 | Data |
| pcpi_rs1 | input | 32 | Data |
| pcpi_rs2 | input | 32 | Data |
| pcpi_wr | output | 1 | Data |
| pcpi_rd | output | 32 | Data |
| pcpi_wait | output | 1 | Data |
| pcpi_ready | output | 1 | Data |

## Checks

| ID | Kind | Group | Title | Rules | Behavior / expected |
|---|---|---|---|---|---|
| CHK-001 | assertion | pcpi | pcpi_wait stays asserted until pcpi_ready | PD-T1.1-06 | If resetn=1, pcpi_valid=1, pcpi_wait=1 and pcpi_ready=0 at a rising edge of clk, then at the next rising edge either pcpi_wait=1 or pcpi_ready=1. pcpi_wait must not drop while an accepted instruction is still running and pcpi_ready has not been asserted. Disabled while resetn=0. |
| CHK-002 | assertion | pcpi | pcpi_wr only together with pcpi_ready | PD-T1.1-03 | If resetn=1 and pcpi_wr=1 at a rising edge of clk, then pcpi_ready=1 at the same rising edge. A result is written only when execution completes. |
| CHK-003 | assertion | pcpi | pcpi_ready only in response to an outstanding pcpi_valid | PD-T1.1-02 | If pcpi_ready=1 at a rising edge of clk, then resetn=1 and pcpi_valid=1 at the same rising edge. Under the legal stimulus, the master holds pcpi_valid until it samples pcpi_ready. So the DUT never signals completion when no instruction is outstanding. |
| CHK-004 | test | divide | Directed DIV/DIVU/REM/REMU results incl. rounding toward zero and remainder sign | RVM-T1.2-01, RVM-T1.2-02, PD-T1.1-03 | pcpi_rd at the completion edge equals the RV32M result. Quotients round toward zero, and a nonzero signed remainder has the dividend's sign. — STIMULUS: Using the CHK-008 handshake, issue these (rs1, rs2) operands: DIV/REM (7,2), (0xFFFFFFF9,2), (7,0xFFFFFFFE), (0xFFFFFFF9,0xFFFFFFFE), (0xFFFFFFFA,3), (0,5), (0x80000000,1), (0x7FFFFFFF,0x7FFFFFFF). DIVU/REMU (0xFFFFFFFF,2), (0x80000000,0xFFFFFFFF), (7,2), (5,7), (0xFFFFFFFF,1). — EXPECTED: At the edge with pcpi_ready=1 and pcpi_wr=1, pcpi_rd equals: DIV 3, 0xFFFFFFFD, 0xFFFFFFFD, 3, 0xFFFFFFFE, 0, 0x80000000, 1. REM 1, 0xFFFFFFFF, 1, 0xFFFFFFFF, 0, 0, 0, 0. DIVU 0x7FFFFFFF, 0, 3, 0, 0xFFFFFFFF. REMU 1, 0x80000000, 1, 5, 0. |
| CHK-005 | test | divide | Constrained-random division against reference model | RVM-T1.2-01, RVM-T1.2-02, PD-T1.1-02, PD-T1.1-03 | Back-to-back random division operations all complete and return results matching a 32-bit reference model. — STIMULUS: After reset, issue 5000 instructions. Pick each from DIV/DIVU/REM/REMU at random. Draw pcpi_rs1 and pcpi_rs2 at random, weighted toward 0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, small magnitudes and powers of two (division by zero included at low weight). Use random rd/rs1/rs2 instruction fields and random 0..3 idle cycles between instructions. Hold inputs stable until pcpi_ready=1, as in CHK-008. — EXPECTED: Every instruction gets exactly one pcpi_ready=1 within 200 edges, with pcpi_wr=1 at the same edge. pcpi_rd equals the reference: trunc(rs1/rs2) for DIV (signed) and DIVU (unsigned), and rs1 - q*rs2 for REM/REMU. Each nonzero REM result has the same sign bit as pcpi_rs1. Divide-by-zero and overflow cases follow CHK-006/CHK-007. |
| CHK-006 | test | divide | Division by zero | RVM-T1.2-08, RVM-T1.2-01 | Division by zero returns a quotient with all bits set and a remainder equal to the dividend (L=32). — STIMULUS: Using the CHK-008 handshake, issue DIV, DIVU, REM and REMU with pcpi_rs2=0 and pcpi_rs1 in {0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x12345678}. — EXPECTED: Each instruction completes with pcpi_ready=1 and pcpi_wr=1 at the same edge, within 200 edges. pcpi_rd = 0xFFFFFFFF for DIV and DIVU. pcpi_rd = pcpi_rs1 (the dividend) for REM and REMU. |
| CHK-007 | test | divide | Signed division overflow | RVM-T1.2-09, RVM-T1.2-01 | Dividing the most-negative integer by -1 returns the dividend as the quotient and 0 as the remainder. — STIMULUS: Using the CHK-008 handshake, issue DIV and REM with pcpi_rs1=0x80000000 and pcpi_rs2=0xFFFFFFFF. As an unsigned contrast, also issue DIVU and REMU with the same operands. — EXPECTED: DIV: pcpi_rd=0x80000000. REM: pcpi_rd=0x00000000. DIVU: pcpi_rd=0x00000000. REMU: pcpi_rd=0x80000000. In each case pcpi_ready=1 and pcpi_wr=1 at the same edge, within 200 edges. |
| CHK-008 | test | pcpi | PCPI handshake: early pcpi_wait, then pcpi_ready with pcpi_wr | PD-T1.1-06, PD-T1.1-02, PD-T1.1-03 | For each supported division instruction, the DUT asserts pcpi_wait soon enough that the core's 16-cycle illegal-instruction timeout cannot fire. It keeps pcpi_wait high until completion, then asserts pcpi_ready together with pcpi_wr. — STIMULUS: After reset, issue each of DIV, DIVU, REM and REMU (opcode 0110011, funct7 0000001, funct3 100/101/110/111, random rd/rs1/rs2 fields) with random nonzero pcpi_rs2 and random pcpi_rs1. Drive pcpi_valid=1 with pcpi_insn, pcpi_rs1 and pcpi_rs2 stable from the issue edge until the edge where pcpi_ready=1 is sampled, then drive pcpi_valid=0 on the next cycle. Leave 0, 1 and 5 idle cycles between instructions. — EXPECTED: For every instruction: (a) pcpi_wait=1 or pcpi_ready=1 is sampled at one of the first 16 rising edges after the edge where pcpi_valid was first sampled high. (b) From the first edge with pcpi_wait=1 until the completion edge, pcpi_wait=1 on every edge. (c) pcpi_ready=1 is sampled exactly once per issued instruction, within 200 rising edges of issue (timeout = failure). (d) At that same edge, pcpi_wr=1. (e) No pcpi_ready or pcpi_wr pulse occurs while pcpi_valid=0. |
| CHK-009 | test | reset | Idle after reset: no completion without an instruction | PD-T1.1-02, PD-T1.1-03 | After a synchronous reset and with no instruction issued, the DUT does not signal completion or write a result. — STIMULUS: Drive resetn=0 for 5 rising edges with pcpi_valid=0, pcpi_insn/pcpi_rs1/pcpi_rs2 at random values. Then drive resetn=1 and keep pcpi_valid=0 for 50 more rising edges while pcpi_insn, pcpi_rs1 and pcpi_rs2 change randomly every cycle (including valid DIV/DIVU/REM/REMU encodings). — EXPECTED: From the first rising edge after resetn is released and on every edge for all 50 idle cycles: pcpi_ready=0 and pcpi_wr=0. pcpi_wait=0 on every idle edge once 2 edges have passed after release. |

## Not verified by simulation

| Rule | Reason | Note |
|---|---|---|
| PD-T1.1-01 | not_applicable_to_dut | This binds the master (PicoRV32 core). The DUT is the PCPI slave. It is used as a stimulus constraint in CHK-004..CHK-009: pcpi_valid is asserted with pcpi_insn/pcpi_rs1/pcpi_rs2 and held stable until pcpi_ready. |
| PD-T1.1-04 | not_applicable_to_dut | The register-file write-back is done by the core, not the DUT. The DUT side (pcpi_rd value when pcpi_wr=1) is checked in CHK-004..CHK-007. |
| PD-T1.1-05 | not_applicable_to_dut | Raising the illegal-instruction exception is core behaviour. Its 16-cycle bound is used as the acknowledge deadline the DUT must meet in CHK-008(a). |
| PD-T1.1-07 | not_applicable_to_dut | How the core reacts to pcpi_wait is master behaviour. The DUT's pcpi_wait timing is covered by CHK-001 and CHK-008. |
| RVM-T1.1-01 | not_applicable_to_dut | MUL is not implemented by picorv32_pcpi_div (a division/remainder coprocessor). |
| RVM-T1.1-02 | not_applicable_to_dut | MULH/MULHU/MULHSU are not implemented by picorv32_pcpi_div. |
| RVM-T1.1-03 | design_guideline | This is a recommended software code sequence. There is nothing to observe at the DUT. |
| RVM-T1.1-04 | design_guideline | This is a register-allocation constraint on software. Multiply is also not implemented by this DUT. |
| RVM-T1.1-05 | not_applicable_to_dut | This is an optional microarchitectural fusion of multiply, which this divider DUT does not implement. |
| RVM-T1.1-06 | not_applicable_to_dut | MULW is RV64-only. The DUT is XLEN=32 (pcpi_rd is 32 bits). |
| RVM-T1.1-07 | not_applicable_to_dut | This is an RV64 software usage note for MUL. It does not apply to a 32-bit divider. |
| RVM-T1.2-03 | design_guideline | This is a recommended software code sequence. Each DIV/REM is still checked on its own in CHK-004/CHK-005. |
| RVM-T1.2-04 | design_guideline | This is a software register-allocation constraint. The DUT does not write registers, and the rd field is ignored at the PCPI interface. |
| RVM-T1.2-05 | not_observable_at_interface | Optional fusion (MAY) of div+rem is an internal microarchitectural choice. Results are still checked per instruction in CHK-005. |
| RVM-T1.2-06 | not_applicable_to_dut | DIVW/DIVUW/REMW/REMUW are RV64-only. The DUT is XLEN=32. |
| RVM-T1.2-07 | not_applicable_to_dut | REMW/REMUW sign extension is RV64-only. The DUT is XLEN=32. |

## Assumptions

- The DUT implements only the RV32M division instructions DIV, DIVU, REM and REMU with XLEN=32 (based on the module name and the 32-bit pcpi_rd). It does not implement the multiply instructions.
- Instruction encodings follow the standard RV32M R-type format: opcode 0110011, funct7 0000001, funct3 100=DIV, 101=DIVU, 110=REM, 111=REMU.
- The result is presented on pcpi_rd with pcpi_wr=1 at the same rising edge where pcpi_ready=1, matching how the PicoRV32 core samples the PCPI response.
- The spec gives no exact division latency, so a 200-cycle completion timeout is used as the failure bound instead of an exact cycle count.
- Legal master stimulus holds pcpi_valid, pcpi_insn, pcpi_rs1 and pcpi_rs2 stable from issue until pcpi_ready=1 is sampled, and deasserts pcpi_valid on the following cycle. pcpi_valid is never withdrawn before pcpi_ready.
- The spec gives no reset values ('See specification'), so only the no-completion-when-idle behaviour after reset is checked (pcpi_ready=0, pcpi_wr=0). pcpi_wait is expected to be 0 after a 2-cycle settling window.
