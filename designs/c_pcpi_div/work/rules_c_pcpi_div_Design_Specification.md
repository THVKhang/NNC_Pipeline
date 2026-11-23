# Extracted rules - c_pcpi_div_Design_Specification.md

```
rules: 8  by strength {'MAY': 3, 'MUST': 4, 'SHOULD': 1}  by check {'none': 1, 'both': 2, 'scenario': 5}
normative sentences: 7  cited 7  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (0 from cache)  cost US$0.0294  tokens in 4401 out 1144
```


## T1 PicoRV32 PCPI division core

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| PD-T1-01 | MAY | system | none | The PCPI can be used to implement non-branching instructions in an external coprocessor core. *(when: implementing non-branching instructions in an external coprocessor)* | T1:s1, T1.1:s1 (p5) |

## T1.1 Pico Co-Processor Interface (PCPI)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| PD-T1.1-01 | MUST | master | both | The core asserts pcpi_valid, outputs the instruction word on pcpi_insn, and outputs the rs1 and rs2 register values on pcpi_rs1 and pcpi_rs2. *(when: an unsupported instruction is encountered and PCPI is activated (ENABLE_PCPI))* | T1.1:s3 (p48) |
| PD-T1.1-02 | MAY | slave | scenario | An external PCPI core can decode and execute the instruction and assert pcpi_ready when execution is finished. *(when: pcpi_valid asserted with an instruction)* | T1.1:s4 (p54) |
| PD-T1.1-03 | MAY | slave | scenario | The PCPI core can optionally write a result value to pcpi_rd and assert pcpi_wr. *(when: instruction execution finished)* | T1.1:s5 (p54) |
| PD-T1.1-04 | MUST | master | scenario | The PicoRV32 core decodes the rd field of the instruction and writes the pcpi_rd value to the respective register. *(when: PCPI core returns a result with pcpi_wr asserted)* | T1.1:s6 (p54) |
| PD-T1.1-05 | MUST | master | scenario | An illegal instruction exception is raised and the respective interrupt handler is called. *(when: no external PCPI core acknowledges the instruction within 16 clock cycles)* | T1.1:s7 (p60) |
| PD-T1.1-06 | SHOULD | slave | both | The PCPI core should assert pcpi_wait as soon as the instruction is decoded successfully and keep it asserted until it asserts pcpi_ready. *(when: the PCPI core needs more than a couple of cycles to execute an instruction)* | T1.1:s8 (p60) |
| PD-T1.1-07 | MUST | master | scenario | Asserting pcpi_wait prevents the PicoRV32 core from raising an illegal instruction exception. *(when: pcpi_wait is asserted by the PCPI core)* | T1.1:s9 (p60) |
