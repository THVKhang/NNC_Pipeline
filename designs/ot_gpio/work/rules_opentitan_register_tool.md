# Extracted rules - opentitan_register_tool.md

```
rules: 35  by strength {'MUST': 20, 'MAY': 7, 'SHOULD': 5, 'MUST_NOT': 2, 'SHOULD_NOT': 1}  by check {'none': 9, 'scenario': 15, 'both': 11}
normative sentences: 25  cited 24  skipped 2  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 2 (0 from cache)  cost US$0.0847  tokens in 12428 out 4199
```


## T1.3 Register Tool Hardware Generation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.3-01 | MUST | system | none | The tool output is two Verilog files that can be instantiated by a peripheral following the Comportability Guidelines. *(when: register generation tool produces hardware output)* | T1.3:s3 (p598) |
| RG-T1.3-02 | MAY | system | none | The tool can be invoked from the top project directory to generate registers, e.g. for uart. *(when: invoking the tool from the top project directory)* | T1.3:s6 (p602) |
| RG-T1.3-03 | MUST | system | scenario | The name_reg2hw_t structure contains the signals driven from the register module to the rest of the hardware, including any required .q, .qe and .re signals. | T1.3:s8 (p610) |
| RG-T1.3-04 | MUST | system | scenario | The name_hw2reg_t structure contains the signals driven from the rest of the hardware to the register module, including any required .d and .de signals. | T1.3:s9 (p610) |

## T1.4.1 Error responses

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.4.1-01 | SHOULD | slave | scenario | Accesses to unmapped addresses representable with the internal address bits typically return an error. *(when: access targets an unmapped address fully representable with the internally used address bits)* | T1.4.1:s3 (p675) |
| RG-T1.4.1-02 | MUST | slave | scenario | If the stripped address maps to a register, the request is forwarded to that register and no error is returned. *(when: excess address bits stripped and resulting address is mapped)* | T1.4.1:s5, T1.4.1:s6 (p676) |
| RG-T1.4.1-03 | SHOULD | slave | scenario | A request to an address representable by the internal address bits but with no register mapped should return an error. *(when: request to an unmapped address such as 0x88 with 8 internal address bits)* | T1.4.1:s8, T1.4.1:s9 (p681) |
| RG-T1.4.1-04 | MUST | slave | both | An error response is returned when TL-UL a_opcode has an illegal value. *(when: a_opcode has an illegal value)* | T1.4.1:s13 (p688) |
| RG-T1.4.1-05 | MUST | slave | both | A write smaller than the register size returns an error. *(when: TL-UL write of size smaller than the register size, e.g. 8b write to register wider than 8 bits)* | T1.4.1:s14, T1.4.1:s17 (p689) |
| RG-T1.4.1-06 | MUST | slave | both | Sub-word writes that are not word-aligned return an error. *(when: write of size 8b or 16b to an address not 4B aligned)* | T1.4.1:s19, T1.4.1:s20 (p694) |
| RG-T1.4.1-07 | MUST | slave | both | Reads smaller than a full word return the full register content and do not signal error. *(when: read smaller than full word (32b))* | T1.4.1:s21 (p697) |
| RG-T1.4.1-08 | MUST | slave | both | Read response data is always in its byte channel, e.g. a byte read at 0x3 returns the full word with the correct byte in bits [31:24]. *(when: sub-word read, e.g. one-byte read to address 0x3)* | T1.4.1:s22 (p697) |
| RG-T1.4.1-09 | SHOULD | system | none | The error rules above should be followed for windows based on the declared number of validbits, though this may be relaxed in some cases. *(when: window access, based on declared validbits)* | T1.4.1:s26 (p700) |
| RG-T1.4.1-10 | MAY | slave | scenario | Errors need not be returned for unaligned sub-word writes. *(when: window terminates in a memory handling byte and halfword writes via masking)* | T1.4.1:s27 (p700) |

## T1.5.1 Type RW

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.1-01 | MUST | system | scenario | Software write enable and write data have the highest priority in modifying register contents. | T1.5.1:s6 (p811) |
| RG-T1.5.1-02 | MAY | system | both | Hardware can present updated values via de and d; when de is true the register content is updated with d. *(when: hwaccess allows hardware writes)* | T1.5.1:s9, T1.5.1:s10 (p811) |
| RG-T1.5.1-03 | MUST | system | both | The software-written value is used. *(when: software and hardware both request an update in the same cycle (de and we true))* | T1.5.1:s11 (p811) |
| RG-T1.5.1-04 | MAY | system | none | A hwaccess of none provides no hardware interface and may be used for registers only software can modify. *(when: hwaccess is none)* | T1.5.1:s17 (p819) |
| RG-T1.5.1-05 | MUST | system | both | qe is a registered version of the bus-side we, aligned with the change in q. *(when: hwqe is true)* | T1.5.1:s18, T1.5.1:s19 (p828) |

## T1.5.2 Type RW HWExt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.2-01 | MUST_NOT | system | none | No de input is required from peripheral hardware; only d is added to the struct bundle. *(when: hwext register)* | T1.5.2:s10 (p834) |
| RG-T1.5.2-02 | MUST | system | both | qe timing is one cycle earlier than in the non-hwext model. *(when: hwext register)* | T1.5.2:s11 (p847) |

## T1.5.3 Type RO, with hwext and zero-gate options

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.3-01 | MUST | system | scenario | RO registers behave as RW registers with no wd and we inputs. *(when: read-only registers)* | T1.5.3:s1, T1.5.3:s2 (p852) |
| RG-T1.5.3-02 | MUST | system | scenario | A software read returns a hardwired value equal to the register default value. *(when: swaccess is ro, hwaccess is none or hro, and hwext is true)* | T1.5.3:s5 (p856) |

## T1.5.4 Type RC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.4-01 | MUST | system | both | When re indicates the register is being read, the contents are set to zero. *(when: register type rc is read)* | T1.5.4:s2 (p861) |
| RG-T1.5.4-02 | SHOULD_NOT | system | none | RC registers are not recommended, except for backwards compatibility. | T1.5.4:s3 (p861) |
| RG-T1.5.4-03 | MUST_NOT | system | none | hwext must not be true for RC registers since re is not exported. *(when: register type RC)* | T1.5.4:s4, T1.5.4:s5 (p861) |

## T1.5.5 Type WO

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.5-01 | SHOULD | system | none | hwext should be set to true so outside hardware handles the write event. *(when: WO register with no storage needed, only write indication)* | T1.5.5:s2 (p869) |

## T1.5.6 Type R0W1C, RW1S, RW1C and RW0C

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6-01 | MUST | system | scenario | These types are implemented with special prim_subreg configuration so writing sets values in type-specific ways. *(when: R0W1C, RW1S, RW1C, RW0C types)* | T1.5.6:s1 (p874) |

## T1.5.6.1 Simultaneous SW and HW access

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6.1-01 | MUST | slave | scenario | The subreg must handle simultaneous hardware and software writes, with software taking precedence as for the RW type. *(when: when hardware and software write a RW1C/RW1S/RW0C/R0W1C subreg at the same time)* | T1.5.6.1:s1, T1.5.6.1:s2 (p888) |
| RG-T1.5.6.1-02 | MUST | slave | scenario | The hardware write value is sent to the logic that potentially clears that value or the stored value. *(when: RW1C subreg when hardware is writing)* | T1.5.6.1:s7 (p899) |
| RG-T1.5.6.1-03 | SHOULD | master | none | Hardware should feed the q value back into d, only setting bits with new events, to avoid collisions with software clearing. *(when: hardware writing a RW1C-type register)* | T1.5.6.1:s8, T1.5.6.1:s9, T1.5.6.1:s10 (p899) |
| RG-T1.5.6.1-04 | MAY | master | scenario | Hardware may drive d and de to clear or set bits as it sees fit, including clearing all events, rather than set-only. *(when: RW1C-type subreg hardware writes)* | T1.5.6.1:s11, T1.5.6.1:s12 (p899) |
| RG-T1.5.6.1-05 | MUST | slave | both | The software clear must still take effect for one cycle to create a new interrupt edge, after which q returns to 1 since d is still 1. *(when: RW1C interrupt vector when software clears a bit while hardware d input is still 1)* | T1.5.6.1:s16, T1.5.6.1:s17 (p906) |

## T1.5.6.2 HWExt RW1C etc.

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RG-T1.5.6.2-01 | MAY | any | scenario | RW1C, RW1S and similar register types may be created with hwext true. | T1.5.6.2:s1 (p914) |
| RG-T1.5.6.2-02 | MAY | any | scenario | hwqe may be set true for RW1C, RW1S and similar register types. *(when: when clearing is to be monitored by external hardware)* | T1.5.6.2:s5 (p919) |
