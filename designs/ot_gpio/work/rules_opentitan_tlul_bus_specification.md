# Extracted rules - opentitan_tlul_bus_specification.md

```
rules: 38  by strength {'MAY': 13, 'MUST': 18, 'SHOULD': 4, 'MUST_NOT': 2, 'SHOULD_NOT': 1}  by check {'scenario': 13, 'none': 9, 'assertion': 6, 'both': 10}
normative sentences: 28  cited 28  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 3 (0 from cache)  cost US$0.1106  tokens in 17187 out 5254
```


## T2.2 Description

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T2.2-01 | MAY | system | scenario | Existing TL-UL IP blocks may be used directly in devices that do not need the additional user sideband signals. *(when: devices that do not need the additional sideband signals)* | T2.2:s6 (p29) |
| TL-T2.2-02 | MAY | system | none | Existing TL-UL IP blocks can be adapted to use the added user extension features. *(when: devices that want the added features)* | T2.2:s6 (p29) |
| TL-T2.2-03 | MUST | system | assertion | The bus carries at most one request and one response per cycle, and supports no burst transactions. | T2.2:s9, T2.2:s10, T2.2:s11 (p47) |
| TL-T2.2-04 | MAY | system | none | Bus primitives can be combined to form a crossbar of any M hosts to any N devices. | T2.2:s14 (p51) |

## T2.3 Compatibility

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T2.3-01 | MAY | system | scenario | Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. | T2.3:s2 (p59) |
| TL-T2.3-02 | MUST | destination | scenario | A baseline block as receiver ignores the user signals. *(when: baseline block acting as receiver)* | T2.3:s3 (p59) |
| TL-T2.3-03 | MUST | source | scenario | A baseline block as source generates a project-specific default value for the user signals. *(when: baseline block acting as source)* | T2.3:s3 (p59) |
| TL-T2.3-04 | MAY | system | none | Blocks can be modified to make use of the user extensions. | T2.3:s4 (p59) |

## T3.1.1 Reset Timing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.1-01 | MAY | master | scenario | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles during reset, unlike the TileLink 1.7.1 requirement. *(when: while reset is asserted)* | T3.1.1:s1 (p133) |
| TL-T3.1.1-02 | MAY | slave | scenario | TL-UL devices tolerate shorter reset windows than the TileLink-specified 100 cycles. *(when: reset window shorter than 100 cycles)* | T3.1.1:s2 (p133) |

## T3.1.3.1 Usage of Address

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.1-01 | MUST | interconnect | scenario | All request steering to a device must be a function of the address only; a_source and a_user do not enter into address calculation. | T3.1.3.1:s1, T3.1.3.1:s3, T3.1.3.1:s5 (p211) |

## T3.1.3.2 Usage of Source and Sink ID Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2-01 | MAY | master | scenario | A host may use source ID bits to ascribe request identifiers, since TL-UL does not guarantee in-order responses. *(when: when response reordering is required)* | T3.1.3.2:s3 (p219) |
| TL-T3.1.3.2-02 | MUST | system | none | The fabric architect must ensure AIW is large enough for outstanding host requests plus maximum source ID growth added by bus primitives. | T3.1.3.2:s7 (p226) |
| TL-T3.1.3.2-03 | MUST | system | none | The fabric must provide enough host ID bits to maintain the converted host ID values. *(when: when converting from a host such as AXI using RID or WID)* | T3.1.3.2:s9 (p226) |

## T3.1.3.2.1 Source ID growth

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.1-01 | MUST | interconnect | both | The primitive shifts incoming a_source left and post-pends its sub-source bits. *(when: when a bus primitive adds source ID bits)* | T3.1.3.2.1:s1, T3.1.3.2.1:s3 (p240) |
| TL-T3.1.3.2.1-02 | MUST | interconnect | both | The sub-source bits are shifted off with zeros shifted into the top, and the result is returned on the originator's d_source. *(when: when the response returns through a primitive that added sub-source bits)* | T3.1.3.2.1:s4 (p240) |
| TL-T3.1.3.2.1-03 | SHOULD | interconnect | assertion | Assertions should be in place to ensure no significant bits of a_source are lost in M:1 sockets. *(when: M:1 sockets)* | T3.1.3.2.1:s5 (p240) |

## T3.1.3.2.2 Source ID requirements for host elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.2-01 | MUST_NOT | master | none | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | T3.1.3.2.2:s1 (p253) |

## T3.1.3.2.3 Source ID requirements for device elements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.2.3-01 | MUST | slave | assertion | A device must return the associated a_source value on the response d_source. | T3.1.3.2.3:s1 (p263) |

## T3.1.3.3 Usage of User Bits

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.3-01 | MUST | any | none | Bus hosts and devices must understand the usage of user bits and apply them appropriately. | T3.1.3.3:s2, T3.1.3.3:s5 (p283) |
| TL-T3.1.3.3-02 | MUST | slave | assertion | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | T3.1.3.3:s3 (p283) |
| TL-T3.1.3.3-03 | MUST | interconnect | both | The bus fabric must not rely on user bits for transport and should pass them on blindly; user bit usage is assigned project-wide. | T3.1.3.3:s4 (p283) |

## T3.1.3.4 Usage of Opcode, Size and Mask

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.4-01 | MAY | master | scenario | a_opcode designates Get (3'b100), PutFullData (3'b000) or PutPartialData (3'b001); for PutPartialData, a_size gives 2^a_size bytes and a_mask should mark valid byte lanes. | T3.1.3.4:s1, T3.1.3.4:s2, T3.1.3.4:s12, T3.1.3.4:s13 (p319) |
| TL-T3.1.3.4-02 | SHOULD_NOT | master | assertion | TL-UL hosts should not assert non-contiguous a_mask values, only a restricted set of masks. | T3.1.3.4:s9, T3.1.3.4:s10 (p331) |
| TL-T3.1.3.4-03 | MAY | slave | scenario | A device may assert d_error if it does not support a given contiguous or non-contiguous subword mask. *(when: device does not support a subword mask)* | T3.1.3.4:s11 (p338) |
| TL-T3.1.3.4-04 | SHOULD | master | assertion | a_size should be 'h2 for a 32b write. *(when: a_opcode is PutFullData)* | T3.1.3.4:s12 (p344) |
| TL-T3.1.3.4-05 | SHOULD | slave | both | Bus devices should return an error for undefined request opcodes. *(when: a_opcode is 3'b01x, 3'b101 or 3'b11x)* | T3.1.3.4:s15 (p347) |
| TL-T3.1.3.4-06 | SHOULD | slave | both | Undefined d_opcode values should return an error. *(when: d_opcode is 3'b01x or 3'b1xx)* | T3.1.3.4:s18 (p353) |

## T3.1.3.5 Explicit Error Cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| TL-T3.1.3.5-01 | MUST | slave | both | TL-UL devices must raise a runtime error via d_error when a request carries a wrong opcode. *(when: a request has a wrong opcode)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s3 (p357) |
| TL-T3.1.3.5-02 | MUST_NOT | master | both | a_size must not be greater than 2; a request violating this is flagged by the device with d_error. *(when: a request is issued)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s4, T3.1.3.5:s5 (p357) |
| TL-T3.1.3.5-03 | MUST | slave | both | TL-UL devices must raise d_error for accesses to non-existent addresses. *(when: a request accesses a non-existent address)* | T3.1.3.5:s1, T3.1.3.5:s2, T3.1.3.5:s10 (p357) |
| TL-T3.1.3.5-04 | MUST | master | both | Inactive lanes must be marked with 'b0 in a_mask; otherwise the request has a wrong a_addr/a_size/a_mask combination and raises d_error. *(when: a request is issued)* | T3.1.3.5:s4, T3.1.3.5:s6 (p361) |
| TL-T3.1.3.5-05 | MUST | master | both | PutFullData must mark all active lanes with a 'b1 in a_mask. *(when: a_opcode is PutFullData)* | T3.1.3.5:s4, T3.1.3.5:s7 (p361) |
| TL-T3.1.3.5-06 | MAY | slave | scenario | A non-contiguous a_mask may lead to an error response, depending on device support. *(when: a_mask is non-contiguous)* | T3.1.3.5:s8 (p365) |
| TL-T3.1.3.5-07 | MUST | master | scenario | Register files always assume aligned 32-bit accesses; other accesses are in violation. *(when: accessing a register file)* | T3.1.3.5:s9 (p366) |
| TL-T3.1.3.5-08 | MUST | master | scenario | The host side must discard orphaned responses and responses with the wrong opcode. *(when: a response is orphaned (no valid request counterpart) or has the wrong opcode)* | T3.1.3.5:s11 (p369) |
| TL-T3.1.3.5-09 | MAY | system | none | Raising a critical hardware error on these violations is planned but not yet implemented. | T3.1.3.5:s12 (p369) |
| TL-T3.1.3.5-10 | MAY | any | none | Devices and hosts may implement additional more restrictive checks if needed. | T3.1.3.5:s14 (p372) |
