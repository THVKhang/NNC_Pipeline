# Extracted rules - riscv_m_extension.adoc

```
rules: 18  by strength {'MUST': 11, 'SHOULD': 2, 'MAY': 3, 'MUST_NOT': 2}  by check {'scenario': 9, 'none': 9}
normative sentences: 11  cited 11  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (0 from cache)  cost US$0.0418  tokens in 5184 out 2465
```


## T1.1 Multiplication Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RVM-T1.1-01 | MUST | system | scenario | mul multiplies rs1 by rs2 as XLEN-bit values and writes the lower XLEN bits of the product to the destination register. *(when: executing mul)* | T1.1:s1 (p21) |
| RVM-T1.1-02 | MUST | system | scenario | mulh, mulhu and mulhsu return the upper XLEN bits of the 2×XLEN-bit product for signed×signed, unsigned×unsigned and signed rs1×unsigned rs2 respectively. *(when: executing mulh, mulhu or mulhsu)* | T1.1:s1 (p21) |
| RVM-T1.1-03 | SHOULD | any | none | Use mulh (or mulhu/mulhsu if appropriate) rdh,rs1,rs2 followed by mul rdl,rs1,rs2 to obtain both halves. *(when: both high and low bits of the same product are required)* | T1.1:s2 (p23) |
| RVM-T1.1-04 | MUST | any | none | Source specifiers rs1 and rs2 must be in the same order in both instructions, and rdh must not be the same as rs1 or rs2. *(when: using the recommended mulh/mul fusion sequence)* | T1.1:s3 (p23) |
| RVM-T1.1-05 | MAY | system | none | Microarchitectures may fuse the two instructions into a single multiply operation instead of two separate multiplies. *(when: mulh followed by mul of the same operands)* | T1.1:s4 (p23) |
| RVM-T1.1-06 | MUST | system | scenario | mulw multiplies the lower 32 bits of the source registers and writes the sign extension of the lower 32 bits of the result to the destination register. *(when: RV64 mulw)* | T1.1:s6 (p28) |
| RVM-T1.1-07 | MUST | any | none | Signed arguments must be proper 32-bit signed values and unsigned arguments must have their upper 32 bits clear. *(when: RV64 mul used to obtain the upper 32 bits of the 64-bit product)* | T1.1:s7 (p30) |

## T1.2 Division Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RVM-T1.2-01 | MUST | system | scenario | div and divu perform XLEN-bit signed and unsigned division of rs1 by rs2 rounding towards zero; rem and remu return the remainder of the corresponding division. *(when: executing div, divu, rem or remu)* | T1.2:s1 (p46) |
| RVM-T1.2-02 | MUST | system | scenario | The sign of a nonzero rem result equals the sign of the dividend. *(when: rem with a nonzero result)* | T1.2:s2 (p46) |
| RVM-T1.2-03 | SHOULD | any | none | Use div rdq,rs1,rs2 followed by rem rdr,rs1,rs2 (or divu and remu if appropriate). *(when: both quotient and remainder are required from the same division)* | T1.2:s4 (p51) |
| RVM-T1.2-04 | MUST_NOT | any | none | rdq must not be the same register as rs1 or rs2. *(when: using the recommended div/rem sequence)* | T1.2:s5 (p51) |
| RVM-T1.2-05 | MAY | system | none | Microarchitectures may fuse the two instructions into a single divide operation instead of two separate divides. *(when: div followed by rem of the same operands)* | T1.2:s6 (p51) |
| RVM-T1.2-06 | MUST | system | scenario | divw and divuw divide the lower 32 bits of rs1 by those of rs2 as signed and unsigned and write the 32-bit quotient sign-extended to 64 bits in rd; remw and remuw give the corresponding remainders. *(when: RV64 divw, divuw, remw, remuw)* | T1.2:s7 (p53) |
| RVM-T1.2-07 | MUST | system | scenario | remw and remuw always sign-extend the 32-bit result to 64 bits, including on a divide by zero. *(when: remw or remuw, including divide by zero)* | T1.2:s8 (p53) |
| RVM-T1.2-08 | MUST | system | scenario | Division by zero returns all bits set (-1 for div/divw, 2^L-1 for divu/divuw) as quotient, and the remainder equals the dividend for rem/remw/remu/remuw. *(when: division by zero)* | T1.2:s10, T1.2:s15, T1.2:s16 (p53) |
| RVM-T1.2-09 | MUST | system | scenario | On signed overflow the quotient equals the dividend (-2^(L-1)) and the remainder is zero. *(when: signed division overflow: most-negative integer divided by -1)* | T1.2:s11, T1.2:s12, T1.2:s17 (p53) |
| RVM-T1.2-10 | MUST_NOT | system | none | Unsigned division overflow does not occur. *(when: unsigned division)* | T1.2:s13 (p53) |
| RVM-T1.2-11 | MAY | any | none | A single branch instruction may be inserted after each divide to implement the required control flow change. *(when: language standard mandates divide-by-zero exception causing immediate control flow change)* | T1.2:s20 (p63) |
