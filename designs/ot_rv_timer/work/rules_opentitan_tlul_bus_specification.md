# Extracted rules - opentitan_tlul_bus_specification.md

```
rules: 38  by strength {'MAY': 13, 'MUST': 17, 'SHOULD': 5, 'MUST_NOT': 2, 'SHOULD_NOT': 1}  by check {'scenario': 14, 'none': 8, 'assertion': 7, 'both': 9}
normative sentences: 28  cited 28  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 3 (3 from cache)  cost US$0.0  tokens in 0 out 0
```


## T2.2 Description

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T2.2-01 | MAY | system | scenario | Existing TL-UL IP blocks may be used directly in devices that do not need the additional sideband signals. *(when: Devices that do not need the additional sideband (user extension) signals)* | T2.2:s6 (p29) |
| TL-T2.2-02 | MAY | system | none | Existing TL-UL IP blocks can be adapted to use the added user extension features. *(when: Devices that need the added features)* | T2.2:s6 (p29) |
| TL-T2.2-03 | MUST | any | assertion | The bus carries only one request and one response per cycle, and no burst transactions. | T2.2:s9, T2.2:s10, T2.2:s11 (p47) |
| TL-T2.2-04 | MAY | interconnect | scenario | Bus primitives can be combined to form a flexible crossbar connecting any M hosts to any N devices. | T2.2:s14 (p51) |

## T2.3 Compatibility

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T2.3-01 | MAY | system | scenario | Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. | T2.3:s2 (p59) |
| TL-T2.3-02 | MUST | destination | scenario | As a receiver, a baseline block ignores the user signals. *(when: Block built to the base specification acts as a receiver)* | T2.3:s3 (p59) |
| TL-T2.3-03 | MUST | source | scenario | As a source, a baseline block generates a project-specific default value for the user signals. *(when: Baseline block acts as a source)* | T2.3:s3 (p59) |
| TL-T2.3-04 | MAY | system | none | Blocks can be modified to make use of the user extensions. | T2.3:s4 (p59) |

## T3.1.1 Reset Timing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.1-01 | MAY | master | scenario | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles during reset, unlike TileLink 1.7.1. *(when: while reset is asserted)* | T3.1.1:s1 (p133) |
| TL-T3.1.1-02 | MAY | slave | scenario | TL-UL devices tolerate reset windows shorter than 100 cycles. *(when: reset window shorter than 100 cycles)* | T3.1.1:s2 (p133) |

## T3.1.3.1 Usage of Address

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.1-01 | MUST | interconnect | scenario | Request steering must be a function of the address only; a_source and a_user must not enter into the address calculation. *(when: routing a request)* | T3.1.3.1:s1, T3.1.3.1:s3, T3.1.3.1:s4, T3.1.3.1:s5 (p211) |

## T3.1.3.2 Usage of Source and Sink ID Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2-01 | MAY | master | scenario | A host may use a_source/d_source to ascribe request identifiers, since TL-UL does not guarantee in-order responses. *(when: response reordering is required)* | T3.1.3.2:s3 (p219) |
| TL-T3.1.3.2-02 | MUST | system | none | The fabric architect must ensure AIW covers the host outstanding requests and the maximum source ID growth added by bus primitives. | T3.1.3.2:s7 (p226) |
| TL-T3.1.3.2-03 | MUST | system | none | The fabric must provide enough host ID bits to maintain those ID values. *(when: converting from a host such as AXI using RID or WID)* | T3.1.3.2:s9 (p226) |

## T3.1.3.2.1 Source ID growth

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.1-01 | MUST | interconnect | both | The primitive shifts a_source left and post-pends sub-source bits; on the response it shifts them off, shifting zeros into the top, and returns the result on d_source. *(when: a primitive adds source ID bits)* | T3.1.3.2.1:s1, T3.1.3.2.1:s4 (p240) |
| TL-T3.1.3.2.1-02 | SHOULD | interconnect | assertion | Assertions should ensure no significant bits of a_source are lost in M:1 sockets. *(when: M:1 sockets)* | T3.1.3.2.1:s5 (p240) |

## T3.1.3.2.2 Source ID requirements for host elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.2-01 | MUST_NOT | master | none | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | T3.1.3.2.2:s1 (p253) |

## T3.1.3.2.3 Source ID requirements for device elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.3-01 | MUST | slave | assertion | Devices must return the associated a_source on the response d_source. | T3.1.3.2.3:s1 (p263) |

## T3.1.3.3 Usage of User Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.3-01 | MUST | any | none | Bus hosts and devices must understand the usage of user bits and apply them appropriately. | T3.1.3.3:s2, T3.1.3.3:s5 (p283) |
| TL-T3.1.3.3-02 | MUST | any | assertion | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | T3.1.3.3:s3 (p283) |
| TL-T3.1.3.3-03 | MUST | interconnect | both | The bus fabric must not rely on user bits for transport and must pass them on blindly; usage must be assigned project-wide. | T3.1.3.3:s4 (p283) |

## T3.1.3.4 Usage of Opcode, Size and Mask

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.4-01 | MAY | master | scenario | a_opcode may designate a write (Put) or read (Get); writes may be full (PutFullData) or partial (PutPartialData). | T3.1.3.4:s1, T3.1.3.4:s2 (p319) |
| TL-T3.1.3.4-02 | SHOULD_NOT | master | assertion | TL-UL hosts in this project should not use non-contiguous a_mask values such as 0b1001. | T3.1.3.4:s9 (p331) |
| TL-T3.1.3.4-03 | MAY | slave | scenario | Devices may assert d_error if they do not support a particular subword a_mask. *(when: device does not support a subword mask)* | T3.1.3.4:s11 (p338) |
| TL-T3.1.3.4-04 | SHOULD | master | assertion | For PutFullData, a_size should be 'h2 for a 32b write ('h3 for 64b bus). *(when: a_opcode is PutFullData)* | T3.1.3.4:s12 (p344) |
| TL-T3.1.3.4-05 | SHOULD | master | assertion | For PutPartialData, a_size should encode 2^a_size bytes and the a_mask bits should indicate the valid byte lanes. *(when: a_opcode is PutPartialData)* | T3.1.3.4:s13 (p345) |
| TL-T3.1.3.4-06 | SHOULD | slave | both | Devices should return an error for undefined request opcodes. *(when: a_opcode is 3'b01x, 3'b101 or 3'b11x)* | T3.1.3.4:s15 (p347) |
| TL-T3.1.3.4-07 | SHOULD | any | scenario | Undefined response opcodes d_opcode 3'b01x and 3'b1xx should return an error. *(when: d_opcode is 3'b01x or 3'b1xx)* | T3.1.3.4:s18 (p353) |

## T3.1.3.5 Explicit Error Cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.5-01 | MUST | slave | both | TL-UL devices must raise a runtime error via d_error when a request carries a wrong opcode. *(when: request has a wrong opcode)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s3 (p357) |
| TL-T3.1.3.5-02 | MUST_NOT | master | both | a_size must not be greater than 2; a request violating this is flagged by the device with d_error. *(when: request issued)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s4, T3.1.3.5:s5 (p357) |
| TL-T3.1.3.5-03 | MUST | master | both | Inactive lanes must be marked with 'b0 in a_mask; violation is flagged by the device with d_error. *(when: request has inactive lanes)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s4, T3.1.3.5:s6 (p357) |
| TL-T3.1.3.5-04 | MUST | master | both | PutFullData must mark all active lanes with a 'b1 in a_mask; violation is flagged by the device with d_error. *(when: a_opcode is PutFullData)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s4, T3.1.3.5:s7 (p357) |
| TL-T3.1.3.5-05 | MUST | slave | both | TL-UL devices must raise a runtime error via d_error for accesses to non-existent addresses. *(when: request accesses a non-existent address)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s10 (p357) |
| TL-T3.1.3.5-06 | MAY | slave | scenario | A device may return an error via d_error for a non-contiguous a_mask, depending on device support. *(when: a_mask is non-contiguous)* | T3.1.3.5:s8 (p365) |
| TL-T3.1.3.5-07 | MUST | master | both | Register files always assume aligned 32-bit accesses, so accesses to them must be aligned 32-bit. *(when: accessing register files)* | T3.1.3.5:s9 (p366) |
| TL-T3.1.3.5-08 | MUST | master | scenario | A host must discard orphaned responses (no valid request counterpart) and responses with the wrong opcode. *(when: response is orphaned or has the wrong opcode)* | T3.1.3.5:s11 (p369) |
| TL-T3.1.3.5-09 | MAY | system | none | Raising a critical hardware error on protocol-check violations is planned but not yet implemented. | T3.1.3.5:s12 (p369) |
| TL-T3.1.3.5-10 | MAY | any | none | Devices and hosts may implement additional, more restrictive checks if needed. | T3.1.3.5:s14 (p372) |
