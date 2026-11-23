# Extracted rules - riscv_rv32m_listing.adoc

```
rules: 2  by strength {'SHOULD_NOT': 1, 'SHOULD': 1}  by check {'none': 2}
normative sentences: 4  cited 2  skipped 2  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (0 from cache)  cost US$0.018  tokens in 4522 out 355
```


## T1 RV32/64G Instruction Set Listings

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RVL-T1-01 | SHOULD_NOT | any | none | Opcodes marked as reserved should be avoided for custom instruction-set extensions, as future standard extensions might use them. *(when: When defining custom instruction-set extensions)* | T1:s11 (p15) |
| RVL-T1-02 | SHOULD | any | none | Major opcodes custom-0 through custom-3 are recommended for custom instruction-set extensions; future standard extensions will avoid them. *(when: When adding custom instruction-set extensions within the base 32-bit instruction format)* | T1:s12 (p15) |
