# Extracted rules - opentitan_register_tool.md

```
rules: 35  by strength {'MUST': 21, 'MAY': 5, 'SHOULD': 6, 'MUST_NOT': 2, 'SHOULD_NOT': 1}  by check {'none': 9, 'scenario': 16, 'both': 7, 'assertion': 3}
normative sentences: 25  cited 25  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 2 (2 from cache)  cost US$0.0  tokens in 0 out 0
```


## T1.3 Register Tool Hardware Generation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.3-01 | MUST | system | none | The tool output is two Verilog files that can be instantiated by a peripheral following the Comportability Guidelines. *(when: register generation tool output)* | T1.3:s3 (p598) |
| RG-T1.3-02 | MAY | system | none | The tool can be invoked from the top project directory to generate the uart registers. *(when: generating uart registers)* | T1.3:s6 (p602) |
| RG-T1.3-03 | MUST | master | scenario | The name_reg2hw_t structure contains the signals driven from the register module to the rest of the hardware, including required .q, .qe and .re signals. | T1.3:s8 (p610) |
| RG-T1.3-04 | MUST | system | scenario | The name_hw2reg_t structure contains the signals driven from the rest of the hardware to the register module, including required .d and .de signals. | T1.3:s9 (p610) |

## T1.4.1 Error responses

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.4.1-01 | SHOULD | slave | scenario | Accesses to unmapped target addresses fully representable with internal address bits typically return an error. *(when: access to an unmapped address representable with the internally used address bits)* | T1.4.1:s3 (p675) |
| RG-T1.4.1-02 | MUST | slave | scenario | If the stripped address is mapped, the request is forwarded to the register and no error is returned. *(when: excess address bits map the request to a mapped address, e.g. 0x184 to 0x84)* | T1.4.1:s6, T1.4.1:s11 (p676) |
| RG-T1.4.1-03 | SHOULD | slave | scenario | A request to unmapped address 0x88 typically returns an error. *(when: module registers span 0x0 to 0x84 with 8 internal address bits; request to unmapped address 0x88)* | T1.4.1:s8, T1.4.1:s9 (p681) |
| RG-T1.4.1-04 | MUST | slave | both | An error response is returned when TL-UL a_opcode has an illegal value. *(when: a_opcode has an illegal value)* | T1.4.1:s13 (p688) |
| RG-T1.4.1-05 | MUST | slave | both | A write smaller than the register size must return an error. *(when: TL-UL write of size smaller than the register size, e.g. 8b write to a register wider than 8 bits)* | T1.4.1:s14, T1.4.1:s17 (p689) |
| RG-T1.4.1-06 | MUST | slave | both | Writes smaller than 32b that are not word-aligned must return an error. *(when: 8b or 16b write to an address not 4B aligned)* | T1.4.1:s19, T1.4.1:s20 (p694) |
| RG-T1.4.1-07 | MUST | slave | both | Reads smaller than a full word return the full register content and do not signal an error. *(when: read smaller than full word)* | T1.4.1:s21 (p697) |
| RG-T1.4.1-08 | MUST | slave | both | Read response data is always in its byte channel, e.g. a one-byte read to 0x3 returns the full word with the correct byte in bits [31:24]. *(when: sub-word read)* | T1.4.1:s22 (p697) |
| RG-T1.4.1-09 | SHOULD | system | none | Windows should follow the error rules based on the declared validbits, though this may be relaxed in some cases. *(when: windowed TL-UL bus)* | T1.4.1:s26 (p700) |

## T1.5 Register definitions per type

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5-01 | SHOULD | slave | assertion | The qs output is typically the same as q except for hwext registers. *(when: non-hwext registers)* | T1.5:s9 (p716) |

## T1.5.1 Type RW

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.1-01 | MUST | slave | both | The software-written value takes priority over the hardware update. *(when: software and hardware request an update in the same clock cycle (de and we both true))* | T1.5.1:s6, T1.5.1:s11 (p811) |
| RG-T1.5.1-02 | MAY | slave | scenario | The hardware can present updated values through de and d. *(when: hwaccess allows hardware writes)* | T1.5.1:s9 (p811) |
| RG-T1.5.1-03 | MUST | slave | assertion | The register content is updated with d. *(when: de is true and no software write)* | T1.5.1:s10 (p811) |
| RG-T1.5.1-04 | MAY | system | none | A hwaccess of none requests no hardware interface, usable for scratch, DV test or read-only version registers. *(when: hwaccess is none)* | T1.5.1:s17 (p819) |
| RG-T1.5.1-05 | MUST | slave | assertion | qe is a registered version of the bus write enable we, aligned with the change in q. *(when: hwqe is true)* | T1.5.1:s18, T1.5.1:s19 (p828) |

## T1.5.2 Type RW HWExt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.2-01 | MUST_NOT | system | none | No de input is required from hardware; only d is added to the struct bundle. *(when: hwext RW register)* | T1.5.2:s10 (p834) |

## T1.5.3 Type RO, with hwext and zero-gate options

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.3-01 | MUST | slave | scenario | RO registers behave as RW registers with no wd and we inputs. *(when: RO registers)* | T1.5.3:s1 (p852) |
| RG-T1.5.3-02 | MUST | slave | scenario | A software read returns a hardwired value equal to the register default value. *(when: swaccess is ro, hwaccess is none or hro, and hwext is true)* | T1.5.3:s5 (p856) |

## T1.5.4 Type RC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.4-01 | MUST | slave | scenario | When re indicates the register is being read, the register contents are set to zero. *(when: RC register is read)* | T1.5.4:s2 (p861) |
| RG-T1.5.4-02 | SHOULD_NOT | system | none | RC registers are not recommended, except for backwards compatibility with other IP. *(when: RC registers)* | T1.5.4:s3 (p861) |
| RG-T1.5.4-03 | MUST_NOT | system | none | hwext must not be true for RC registers since re is not exported. *(when: RC register)* | T1.5.4:s4, T1.5.4:s5 (p861) |

## T1.5.5 Type WO

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.5-01 | SHOULD | system | none | hwext should be set to true so outside hardware handles the write event. *(when: WO register needing no storage, only write indication)* | T1.5.5:s2 (p869) |

## T1.5.6 Type R0W1C, RW1S, RW1C and RW0C

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6-01 | MUST | slave | scenario | These register types must be implemented with special prim_subreg configuration because writing sets values in unique ways. *(when: R0W1C, RW1S, RW1C, RW0C types)* | T1.5.6:s1 (p874) |

## T1.5.6.1 Simultaneous SW and HW access

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6.1-01 | MUST | slave | scenario | The subreg for R0W1C/RW1S/RW1C/RW0C types must handle simultaneous hardware and software write attempts. *(when: hardware and software attempt to write the register at the same time)* | T1.5.6.1:s1 (p888) |
| RG-T1.5.6.1-02 | MUST | slave | scenario | Software has precedence over hardware, as for the RW type. *(when: hardware and software write simultaneously)* | T1.5.6.1:s2 (p888) |
| RG-T1.5.6.1-03 | MUST | slave | scenario | The hardware value is sent to the logic that potentially clears that value or the stored value. *(when: hardware is writing a RW1C register)* | T1.5.6.1:s7 (p899) |
| RG-T1.5.6.1-04 | SHOULD | master | none | Hardware should feed the q value back into d, only setting bits with new events, to avoid collisions with software clearing. *(when: hardware writes a RW1C-type register)* | T1.5.6.1:s9, T1.5.6.1:s10 (p899) |
| RG-T1.5.6.1-05 | MUST | slave | both | The software clear must still take effect for one cycle to create a new interrupt edge, then q returns to 1 since d is still 1. *(when: software clears a RW1C bit while the hardware d input is still 1)* | T1.5.6.1:s16, T1.5.6.1:s17 (p906) |

## T1.5.6.2 HWExt RW1C etc.

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6.2-01 | MAY | any | scenario | RW1C, RW1S and similar register types may be created with hwext true. | T1.5.6.2:s1 (p914) |
| RG-T1.5.6.2-02 | MUST | system | scenario | The auto-generated hardware is the same as the hwext RW register, with the implementation done outside the generated register block. *(when: RW1C, RW1S or similar register has hwext true)* | T1.5.6.2:s2, T1.5.6.2:s3 (p914) |
| RG-T1.5.6.2-03 | MAY | any | scenario | hwqe may be set true for these register types. *(when: clearing is to be monitored by external hardware)* | T1.5.6.2:s5 (p919) |
