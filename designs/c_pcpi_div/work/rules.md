# Rules for review (Gate 1)

```
rules in 28: kept 23 (fixed 0), merged 0, rejected 5, unreviewed 0; open questions 4 (raised 4, answered from the documents 0, duplicates 0)
calls: 4 (0 from cache)  cost US$0.1298
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.

## Open questions (the designer decides: `nnc answer <design> <n> "<decision>" --by <name>`)

1. Is the 16-cycle timeout counted from pcpi_valid assertion? Does asserting pcpi_wait suspend the timeout indefinitely, or only until pcpi_ready? What happens if pcpi_wait is asserted after cycle 16? (PD-T1.1-05, PD-T1.1-07) — *Not settled. The documents say the exception is raised when no PCPI core acknowledges within 16 clock cycles, and that pcpi_wait, kept asserted until pcpi_ready, prevents the illegal instruction exception. They do not say which event starts the 16-cycle count (pcpi_valid assertion is not stated), whether pcpi_wait suspends the timeout indefinitely, or what happens if pcpi_wait is first asserted after cycle 16.*
   - **Decision:** none yet
2. What does 'more than a couple of cycles' mean in cycles? When must pcpi_wait be asserted so that it counts as being asserted 'as soon as' the instruction is decoded? (PD-T1.1-06) — *Not settled. 'More than a couple of cycles' is not quantified, and 'as soon as the instruction has been decoded successfully' has no cycle bound. The only hard limit given is the 16-cycle acknowledgement window. The designer must define the thresholds.*
   - **Decision:** none yet
3. Must pcpi_wr be asserted in the same cycle as pcpi_ready, or can it be asserted earlier? Is pcpi_rd sampled only when pcpi_ready is high? (PD-T1.1-03, PD-T1.1-04) — *Not settled. The documents say pcpi_ready is asserted when execution finishes and that optionally a result is written to pcpi_rd with pcpi_wr asserted. They do not give the timing of pcpi_wr relative to pcpi_ready, and do not say whether pcpi_rd is sampled only when pcpi_ready is high. The designer must specify this.*
   - **Decision:** none yet
4. The quote for T1.1-04 says rdh cannot equal rs1 or rs2, but the mulh/mul pair is only safe if the first instruction does not overwrite a source of the second. T1.2-04 gives the same constraint for rdq. Should the testbench treat these as software-only constraints, or must it check hardware behaviour when they are violated? (RVM-T1.1-04, RVM-T1.2-04) — *Not settled. The RISC-V text gives the rdh/rdq register restrictions as part of the recommended code sequence, so that microarchitectures can fuse the pair. It does not say what hardware must do when they are violated, and it does not say whether a testbench should check that case. The designer must decide whether these are software-only constraints.*
   - **Decision:** none yet


## c_pcpi_div_Design_Specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| PD-T1.1-01 |  | MUST | master | both | The core asserts pcpi_valid, outputs the instruction word on pcpi_insn, and outputs the rs1 and rs2 register values on pcpi_rs1 and pcpi_rs2. *(when: an unsupported instruction is encountered and PCPI is activated (ENABLE_PCPI))* | keep |
| PD-T1.1-02 |  | MAY | slave | scenario | An external PCPI core can decode and execute the instruction and assert pcpi_ready when execution is finished. *(when: pcpi_valid asserted with an instruction)* | keep |
| PD-T1.1-03 |  | MAY | slave | scenario | The PCPI core can optionally write a result value to pcpi_rd and assert pcpi_wr. *(when: instruction execution finished)* | keep |
| PD-T1.1-04 |  | MUST | master | scenario | The PicoRV32 core decodes the rd field of the instruction and writes the pcpi_rd value to the respective register. *(when: PCPI core returns a result with pcpi_wr asserted)* | keep |
| PD-T1.1-05 |  | MUST | master | scenario | An illegal instruction exception is raised and the respective interrupt handler is called. *(when: no external PCPI core acknowledges the instruction within 16 clock cycles)* | keep |
| PD-T1.1-06 |  | SHOULD | slave | both | The PCPI core should assert pcpi_wait as soon as the instruction is decoded successfully and keep it asserted until it asserts pcpi_ready. *(when: the PCPI core needs more than a couple of cycles to execute an instruction)* | keep |
| PD-T1.1-07 |  | MUST | master | scenario | Asserting pcpi_wait prevents the PicoRV32 core from raising an illegal instruction exception. *(when: pcpi_wait is asserted by the PCPI core)* | keep |

## riscv_m_extension.adoc

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| RVM-T1.1-01 |  | MUST | system | scenario | mul multiplies rs1 by rs2 as XLEN-bit values and writes the lower XLEN bits of the product to the destination register. *(when: executing mul)* | keep |
| RVM-T1.1-02 |  | MUST | system | scenario | mulh, mulhu and mulhsu return the upper XLEN bits of the 2×XLEN-bit product for signed×signed, unsigned×unsigned and signed rs1×unsigned rs2 respectively. *(when: executing mulh, mulhu or mulhsu)* | keep |
| RVM-T1.1-03 |  | SHOULD | any | none | Use mulh (or mulhu/mulhsu if appropriate) rdh,rs1,rs2 followed by mul rdl,rs1,rs2 to obtain both halves. *(when: both high and low bits of the same product are required)* | keep |
| RVM-T1.1-04 |  | MUST | any | none | Source specifiers rs1 and rs2 must be in the same order in both instructions, and rdh must not be the same as rs1 or rs2. *(when: using the recommended mulh/mul fusion sequence)* | keep |
| RVM-T1.1-05 |  | MAY | system | none | Microarchitectures may fuse the two instructions into a single multiply operation instead of two separate multiplies. *(when: mulh followed by mul of the same operands)* | keep |
| RVM-T1.1-06 |  | MUST | system | scenario | mulw multiplies the lower 32 bits of the source registers and writes the sign extension of the lower 32 bits of the result to the destination register. *(when: RV64 mulw)* | keep |
| RVM-T1.1-07 |  | MUST | any | none | Signed arguments must be proper 32-bit signed values and unsigned arguments must have their upper 32 bits clear. *(when: RV64 mul used to obtain the upper 32 bits of the 64-bit product)* | keep |
| RVM-T1.2-01 |  | MUST | system | scenario | div and divu perform XLEN-bit signed and unsigned division of rs1 by rs2 rounding towards zero; rem and remu return the remainder of the corresponding division. *(when: executing div, divu, rem or remu)* | keep |
| RVM-T1.2-02 |  | MUST | system | scenario | The sign of a nonzero rem result equals the sign of the dividend. *(when: rem with a nonzero result)* | keep |
| RVM-T1.2-03 |  | SHOULD | any | none | Use div rdq,rs1,rs2 followed by rem rdr,rs1,rs2 (or divu and remu if appropriate). *(when: both quotient and remainder are required from the same division)* | keep |
| RVM-T1.2-04 |  | MUST_NOT | any | none | rdq must not be the same register as rs1 or rs2. *(when: using the recommended div/rem sequence)* | keep |
| RVM-T1.2-05 |  | MAY | system | none | Microarchitectures may fuse the two instructions into a single divide operation instead of two separate divides. *(when: div followed by rem of the same operands)* | keep |
| RVM-T1.2-06 |  | MUST | system | scenario | divw and divuw divide the lower 32 bits of rs1 by those of rs2 as signed and unsigned and write the 32-bit quotient sign-extended to 64 bits in rd; remw and remuw give the corresponding remainders. *(when: RV64 divw, divuw, remw, remuw)* | keep |
| RVM-T1.2-07 |  | MUST | system | scenario | remw and remuw always sign-extend the 32-bit result to 64 bits, including on a divide by zero. *(when: remw or remuw, including divide by zero)* | keep |
| RVM-T1.2-08 |  | MUST | system | scenario | Division by zero returns all bits set (-1 for div/divw, 2^L-1 for divu/divuw) as quotient, and the remainder equals the dividend for rem/remw/remu/remuw. *(when: division by zero)* | keep |
| RVM-T1.2-09 |  | MUST | system | scenario | On signed overflow the quotient equals the dividend (-2^(L-1)) and the remainder is zero. *(when: signed division overflow: most-negative integer divided by -1)* | keep |

## Rejected

| ID | Statement | Reason |
|---|---|---|
| PD-T1-01 | The PCPI can be used to implement non-branching instructions in an external coprocessor core. | Descriptive overview of PCPI purpose; nothing to verify or exercise. |
| RVM-T1.2-10 | Unsigned division overflow does not occur. | A statement of fact ('cannot occur'). It gives no behaviour to verify or exercise. |
| RVM-T1.2-11 | A single branch instruction may be inserted after each divide to implement the required control flow change. | It describes software overhead for language-mandated divide-by-zero handling. No hardware behaviour to verify or exercise. |
| RVL-T1-01 | Opcodes marked as reserved should be avoided for custom instruction-set extensions, as future standard extensions might use them. | This is design guidance for custom-extension authors, not DUT behavior. It cannot be checked by an assertion or exercised in a scenario, so there is nothing to verify. |
| RVL-T1-02 | Major opcodes custom-0 through custom-3 are recommended for custom instruction-set extensions; future standard extensions will avoid them. | This is a recommendation to ISA extension designers, plus a statement about future standard extensions. It describes no DUT behavior to verify or exercise. |
