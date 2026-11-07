# Extracted rules - vlsit_tilelink_ul_opentitan_tlul.md

```
rules: 41  by strength {'MUST_NOT': 4, 'MUST': 20, 'MAY': 12, 'SHOULD': 5}  by check {'assertion': 10, 'both': 9, 'none': 9, 'scenario': 13}
normative sentences: 28  cited 28  skipped 1  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 4 (0 from cache)  cost US$0.1231  tokens in 20279 out 5642
```


## T3.1 Features

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1-01 | MUST_NOT | any | assertion | Burst transactions are not supported; transaction sizes are up to bus width only (byte, 2B, 4B). | T3.1:s8, T3.2:s11 (p43) |

## T3.2 Description

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.2-01 | MUST | any | both | Apart from the user extensions, all functionality follows the TL-UL specification, with user extension signals using TL-UL timing and naming conventions. | T3.2:s3, T3.2:s4, T3.2:s5, T3.3:s1 (p52) |
| TL-T3.2-02 | MAY | system | none | Existing TL-UL IP blocks may be used directly in devices not needing the additional sideband signals, or be adapted to use the added features. *(when: For devices that do not need the additional sideband signals)* | T3.2:s6 (p52) |
| TL-T3.2-03 | MUST | master | assertion | The bus carries at most one request (read or write) per cycle. | T3.2:s9 (p70) |
| TL-T3.2-04 | MUST | slave | assertion | The bus carries at most one response (read or write) per cycle. | T3.2:s10 (p71) |
| TL-T3.2-05 | MAY | interconnect | none | Bus primitives can be combined to form a crossbar of any M hosts to any N devices. | T3.2:s14 (p74) |

## T3.3 Compatibility

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.3-01 | MAY | any | scenario | Bus primitives, hosts and peripherals developed using the extended specification can be used with blocks using the base specification. | T3.3:s2 (p82) |
| TL-T3.3-02 | MUST | destination | scenario | Baseline receiver blocks ignore the user signals. *(when: When a block is a receiver using the base specification)* | T3.3:s3 (p82) |
| TL-T3.3-03 | MUST | source | scenario | Baseline source blocks generate a project-specific default value for the user signals. *(when: When a baseline block acts as a source)* | T3.3:s3 (p82) |
| TL-T3.3-04 | MAY | any | none | Blocks can be modified to make use of the user extensions. | T3.3:s4 (p82) |

## T4.1.1 Reset Timing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.1-01 | MAY | master | scenario | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles while reset is asserted. *(when: during reset assertion)* | T4.1.1:s1 (p156) |
| TL-T4.1.1-02 | MAY | slave | scenario | TL-UL devices within the library tolerate reset windows shorter than 100 cycles. *(when: reset window shorter than TileLink 100 cycles)* | T4.1.1:s2 (p156) |

## T4.1.3.1 Usage of Address

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.1-01 | MUST | interconnect | both | All request steering must be made as a function of the address (a_address) only, not a_source or a_user. | T4.1.3.1:s1, T4.1.3.1:s5 (p234) |

## T4.1.3.2 Usage of Source and Sink ID Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.2-01 | MAY | master | scenario | A host may use a_source/d_source to ascribe request identifiers since TL-UL does not guarantee in-order responses. *(when: when response reordering is required)* | T4.1.3.2:s3 (p242) |
| TL-T4.1.3.2-02 | MUST | system | none | The fabric architect must ensure AIW is large enough for outstanding host requests plus maximum source ID growth added by bus primitives. | T4.1.3.2:s7 (p249) |
| TL-T4.1.3.2-03 | MUST | system | none | The fabric must provide enough host ID bits to maintain required ID values, such as AXI RID or WID. *(when: when converting from hosts such as AXI using RID or WID)* | T4.1.3.2:s9 (p249) |

## T4.1.3.2.1 Source ID growth

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.2.1-01 | SHOULD | interconnect | assertion | Assertions should ensure no significant bits of a_source are lost in M:1 sockets. *(when: in M:1 sockets)* | T4.1.3.2.1:s5 (p263) |

## T4.1.3.2.2 Source ID requirements for host elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.2.2-01 | MUST_NOT | master | none | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | T4.1.3.2.2:s1 (p276) |

## T4.1.3.2.3 Source ID requirements for device elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.2.3-01 | MUST | slave | assertion | A device must return the associated a_source value on d_source of the response. | T4.1.3.2.3:s1 (p286) |

## T4.1.3.3 Usage of User Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.3-01 | MUST | interconnect | both | The bus fabric must not rely on user bits for transport and must pass a_user and d_user on blindly. | T4.1.3.3:s2, T4.1.3.3:s4 (p306) |
| TL-T4.1.3.3-02 | MUST | any | assertion | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | T4.1.3.3:s3 (p306) |
| TL-T4.1.3.3-03 | MUST | system | none | Usage of user bits within a project must be assigned project-wide. | T4.1.3.3:s4 (p306) |
| TL-T4.1.3.3-04 | MUST | any | scenario | Bus hosts and devices must understand the usage of user bits and apply them appropriately. | T4.1.3.3:s5 (p306) |

## T4.1.3.4 Usage of Opcode, Size and Mask

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.4-01 | MAY | master | scenario | a_opcode may designate a write (Put) or read (Get), and writes may be full (PutFullData) or partial (PutPartialData). | T4.1.3.4:s1, T4.1.3.4:s2 (p342) |
| TL-T4.1.3.4-02 | MUST_NOT | master | assertion | TL-UL hosts in this project must not use non-contiguous a_mask values. | T4.1.3.4:s9 (p354) |
| TL-T4.1.3.4-03 | MAY | slave | scenario | A device may assert d_error if it does not support a given contiguous or non-contiguous subword a_mask. *(when: when the device does not support a subword mask)* | T4.1.3.4:s11 (p361) |
| TL-T4.1.3.4-04 | SHOULD | master | assertion | For PutFullData, a_size should be 'h2 for a 32b write ('h3 for 64b bus width). *(when: a_opcode is PutFullData (3'b000))* | T4.1.3.4:s12 (p367) |
| TL-T4.1.3.4-05 | MUST | master | assertion | For PutPartialData, a_size must encode the number of bytes transmitted as 2^a_size. *(when: a_opcode is PutPartialData (3'b001))* | T4.1.3.4:s13 (p368) |
| TL-T4.1.3.4-06 | SHOULD | master | assertion | For PutPartialData, the bits of a_mask should indicate valid byte lanes. *(when: a_opcode is PutPartialData)* | T4.1.3.4:s13 (p368) |
| TL-T4.1.3.4-07 | SHOULD | slave | both | Bus devices should return an error for undefined a_opcode values. *(when: a_opcode is undefined (3'b01x, 3'b101, 3'b11x))* | T4.1.3.4:s15 (p370) |
| TL-T4.1.3.4-08 | SHOULD | master | scenario | Undefined d_opcode values should return an error. *(when: d_opcode is undefined (3'b01x, 3'b1xx))* | T4.1.3.4:s18 (p376) |

## T4.1.3.5 Explicit Error Cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T4.1.3.5-01 | MUST | slave | both | TL-UL devices must raise d_error when a request carries a wrong opcode. *(when: request has a wrong opcode)* | T4.1.3.5:s1, T4.1.3.5:s2, T4.1.3.5:s3 (p380) |
| TL-T4.1.3.5-02 | MUST_NOT | master | both | a_size must not be greater than 2; a request violating this must cause the device to raise d_error. | T4.1.3.5:s1, T4.1.3.5:s2, T4.1.3.5:s4, T4.1.3.5:s5 (p380) |
| TL-T4.1.3.5-03 | MUST | master | both | Inactive lanes must be marked with 'b0 in a_mask; violation must cause the device to raise d_error. | T4.1.3.5:s1, T4.1.3.5:s4, T4.1.3.5:s6 (p380) |
| TL-T4.1.3.5-04 | MUST | master | both | PutFullData must mark all active lanes with a 'b1 in a_mask; violation must cause the device to raise d_error. *(when: a_opcode is PutFullData)* | T4.1.3.5:s1, T4.1.3.5:s4, T4.1.3.5:s7 (p380) |
| TL-T4.1.3.5-05 | MUST | slave | both | TL-UL devices must raise d_error for accesses to non-existent addresses. *(when: request accesses a non-existent address)* | T4.1.3.5:s1, T4.1.3.5:s10 (p380) |
| TL-T4.1.3.5-06 | MAY | slave | scenario | Depending on device support, a non-contiguous a_mask may lead to d_error. *(when: a_mask is non-contiguous)* | T4.1.3.5:s8 (p388) |
| TL-T4.1.3.5-07 | MUST | slave | scenario | Register files always assume aligned 32-bit accesses. *(when: accessing register files)* | T4.1.3.5:s9 (p389) |
| TL-T4.1.3.5-08 | MUST | master | scenario | The host side must discard orphaned responses and responses with the wrong opcode. *(when: response is orphaned or has the wrong opcode)* | T4.1.3.5:s11 (p392) |
| TL-T4.1.3.5-09 | MAY | system | none | A critical hardware error may in future be raised for protocol violations; this is not yet implemented. | T4.1.3.5:s12 (p392) |
| TL-T4.1.3.5-10 | MAY | any | none | Devices and hosts may implement additional more restrictive checks if needed. | T4.1.3.5:s14 (p395) |
