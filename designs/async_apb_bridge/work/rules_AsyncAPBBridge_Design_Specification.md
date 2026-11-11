# Extracted rules - AsyncAPBBridge_Design_Specification.md

```
rules: 304  by strength {'MUST': 260, 'MUST_NOT': 33, 'MAY': 6, 'SHOULD': 5}  by check {'none': 83, 'scenario': 83, 'assertion': 69, 'both': 69}
normative sentences: 166  cited 155  skipped 13  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 27 (0 from cache)  cost US$0.9877  tokens in 154163 out 47267
```


## T1 Asynchronous APB Bridge Design Specification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-T1-01 | MUST | any | none | Requirements stated with 'shall' are mandatory and must be testable. | T1:s6 (p19) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-1.1-01 | MUST_NOT | system | scenario | The multi-bit request and response bundles must never be sampled by a synchronizer; only one-bit control signals pass through synchronizers. *(when: multi-bit request and response bundles crossing the domains)* | 1.1:s7 (p52) |
| AB2-1.1-02 | MUST | source | assertion | The source must hold the multi-bit request and response bundles stable for the whole handshake. *(when: during the whole handshake)* | 1.1:s7 (p52) |
| AB2-1.1-03 | MUST | destination | assertion | The destination must load the multi-bit bundle only after the associated control bit has arrived. *(when: after the control bit has arrived in the destination domain)* | 1.1:s7 (p52) |
| AB2-1.1-04 | MUST | system | none | The timing of the bundle paths must be bounded by set_max_delay constraints (Section 17). | 1.1:s7 (p52) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-1.3-01 | MUST | system | scenario | The bridge must always support APB4 write and read transfers across two asynchronous clocks (FEAT-001, REQ-FUNC-001 to REQ-FUNC-009). *(when: always)* | 1.3:s1 (p86) |
| AB2-1.3-02 | MUST | system | scenario | The bridge must always transport wait states and error responses across the crossing (FEAT-002). *(when: always)* | 1.3:s2 (p87) |
| AB2-1.3-03 | MUST | system | scenario | The bridge must provide the two-phase handshake when PARA_APBCDC_HS_TYPE is 0 (FEAT-003). *(when: PARA_APBCDC_HS_TYPE = 0)* | 1.3:s3 (p88) |
| AB2-1.3-04 | MUST | system | scenario | The bridge must provide the four-phase handshake when PARA_APBCDC_HS_TYPE is 1 (FEAT-004). *(when: PARA_APBCDC_HS_TYPE = 1)* | 1.3:s4 (p89) |
| AB2-1.3-05 | MUST | system | none | The bridge must support selectable synchronizer depth with PARA_APBCDC_CELL_TYPE 1 to 4; 0 is for simulation only (FEAT-005). *(when: PARA_APBCDC_CELL_TYPE 1 to 4)* | 1.3:s5 (p90) |
| AB2-1.3-06 | MUST | system | scenario | The bridge must provide APB5 wake-up signaling when PARA_APBCDC_APB5 is 1 (FEAT-006). *(when: PARA_APBCDC_APB5 = 1)* | 1.3:s6 (p91) |
| AB2-1.3-07 | MUST | system | scenario | The bridge must provide the APB5 user signals when PARA_APBCDC_APB5 is 1 and the width is above 0 (FEAT-007). *(when: PARA_APBCDC_APB5 = 1 and user signal width above 0)* | 1.3:s7 (p92) |
| AB2-1.3-08 | MUST | system | none | The IP must always deliver an executable SDC with the crossing constraints (FEAT-008). *(when: always)* | 1.3:s8 (p93) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-2.1-01 | MUST | system | none | The IP must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding, hierarchy, reset, CDC and naming baseline. | 2.1:s3 (p103) |
| AB2-2.1-02 | MUST | system | none | The Synopsys option -ignore_clock_latency must be confirmed in the Synopsys documentation (OI-004), as REF-007 describes Vivado only. | 2.1:s7 (p107) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-2.2-01 | MUST | system | none | The RTL must comply with REF-003 baseline; conflicts are resolved by revising the requirement or choosing a compliant implementation, not by a local RTL exception. | 2.2:s4, 2.2:s5 (p113) |

## 2.3 Compliance declaration

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-2.3-01 | MUST | system | scenario | The IP implements the AMBA APB Issue D completer role on the requester-side interface and requester role on the completer-side interface, with PSTRB, PPROT, PSLVERR always present and APB5 signals in the APB5 profile. | 2.3:s1 (p123) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-3-01 | MUST | system | both | The bridge shall start exactly one completer-side APB transfer with the same PWRITE, PADDR, PPROT, PSTRB and, for a write, PWDATA as driven in the Setup phase. *(when: For every requester-side APB transfer)* | 3:s1 (p129) |
| AB2-3-02 | MUST | system | both | In APB5 the completer-side transfer shall carry the same PAUSER and, for a write, the same PWUSER as the requester-side Setup phase. *(when: APB5, for every requester-side transfer)* | 3:s1 (p129) |
| AB2-3-03 | MUST | system | both | The bridge shall return the completer-side PRDATA of a read and PSLVERR unchanged on the requester side, valid in the cycle where PREADY is high. *(when: Completer-side transfer responds)* | 3:s2 (p130) |
| AB2-3-04 | MUST | system | both | In APB5 the bridge shall return PRUSER of a read and PBUSER unchanged on the requester side, valid when PREADY is high. *(when: APB5)* | 3:s2 (p130) |
| AB2-3-05 | MUST | system | both | Transfers shall be carried in start order, one completer-side transfer per requester-side transfer, with no loss and no duplicate. | 3:s3 (p131) |
| AB2-3-06 | MUST_NOT | system | both | No new completer-side transfer shall start before the response of the previous one has been delivered. *(when: Previous transfer response not yet delivered)* | 3:s3 (p131) |
| AB2-3-07 | MUST | system | assertion | Requester-side PREADY shall be low from the Setup phase until the response is available. *(when: Requester side, from Setup phase until response available)* | 3:s4 (p132) |
| AB2-3-08 | MUST | system | assertion | Requester-side PREADY shall then be high for exactly one i_clk_mst cycle, in a cycle in which PSEL and PENABLE are high. *(when: Response available)* | 3:s4 (p132) |
| AB2-3-09 | MUST | system | both | Requester-side PREADY shall be raised only after the completer-side PREADY was seen, so completer wait states extend the requester-side transfer. *(when: Completer inserts wait states)* | 3:s5 (p133) |
| AB2-3-10 | MUST | system | scenario | The bridge shall wait without limit for the completer response, with no timeout. *(when: Completer waits)* | 3:s5 (p133) |
| AB2-3-11 | MUST_NOT | system | assertion | Requester-side PSLVERR shall not be high outside the PREADY cycle. | 3:s6 (p134) |
| AB2-3-12 | MUST_NOT | system | both | Requester-side PSLVERR shall not be high unless the completer-side PSLVERR was high at the end of the transfer. *(when: Completer-side PSLVERR was low at end of the completer-side transfer)* | 3:s6 (p134) |
| AB2-3-13 | MUST | system | both | The bridge shall accept the Setup phase of a new requester-side transfer in the cycle following the PREADY cycle (back-to-back). *(when: After the PREADY cycle)* | 3:s7, 3:s28 (p135) |
| AB2-3-14 | MUST | system | assertion | On the completer side the bridge shall drive PSEL high for the whole transfer. *(when: Completer-side transfer)* | 3:s8 (p136) |
| AB2-3-15 | MUST | system | assertion | PENABLE shall be low in the Setup cycle and high from the next cycle until the transfer completes. *(when: Completer-side transfer)* | 3:s8 (p136) |
| AB2-3-16 | MUST | system | assertion | The bridge shall keep PADDR, PPROT, PWRITE, PWDATA, PSTRB, PAUSER and PWUSER unchanged from the Setup phase until PREADY is seen high. *(when: Completer side, from Setup until PREADY seen high)* | 3:s8 (p136) |
| AB2-3-17 | MUST | system | assertion | The bridge shall drive PSEL and PENABLE low when no transfer is in progress. *(when: No transfer in progress on completer side)* | 3:s8 (p136) |
| AB2-3-18 | MUST | system | both | PPROT and PSTRB shall be forwarded unchanged. | 3:s9 (p137) |
| AB2-3-19 | MUST_NOT | system | scenario | The bridge does not check that PSTRB is low in a read; it forwards what the requester drove. *(when: Read transfer)* | 3:s9 (p137) |
| AB2-3-20 | MUST | system | none | The IP shall expose exactly the ports of Section 6.2 of the configured revision. | 3:s10 (p138) |
| AB2-3-21 | MUST | system | none | Every output of both APB interfaces shall be a flip-flop output with no logic after it, so it is glitch-free. | 3:s11 (p139) |
| AB2-3-22 | MUST | system | both | Outputs that need not be valid shall hold a stable value (reset value zero). *(when: Outputs not required to be valid)* | 3:s12 (p140) |
| AB2-3-23 | MUST | system | assertion | PSLVERR shall be low when PREADY is low. *(when: PREADY low)* | 3:s12 (p140) |
| AB2-3-24 | MUST | system | both | The request bit shall toggle once per transfer and the acknowledge bit shall toggle once per transfer (two-phase handshake). *(when: PARA_APBCDC_HS_TYPE = 0)* | 3:s13 (p141) |
| AB2-3-25 | MUST | system | both | The four-phase handshake shall sequence request high, acknowledge high, request low, acknowledge low. *(when: PARA_APBCDC_HS_TYPE = 1)* | 3:s13 (p141) |
| AB2-3-26 | MUST | system | scenario | The function seen on the two APB interfaces shall be the same for both handshake types. | 3:s13 (p141) |
| AB2-3-27 | MUST | system | assertion | The request bundle in the requester-side hold register shall not change from the request launch edge until the acknowledge was seen. *(when: From request launch edge until acknowledge seen)* | 3:s14 (p142) |
| AB2-3-28 | MUST | system | assertion | The response bundle in the completer-side hold register shall not change from the acknowledge launch edge until the next request was seen. *(when: From acknowledge launch edge until next request seen)* | 3:s14 (p142) |
| AB2-3-29 | MUST | system | both | The request bit shall be launched at the same edge the request bundle is loaded, and the acknowledge bit at the same edge the response bundle is loaded. | 3:s15 (p143) |
| AB2-3-30 | MUST_NOT | system | none | There shall be no logic between a launch flip-flop and its synchronizer. | 3:s15 (p143) |
| AB2-3-31 | MUST | system | both | The requester side shall raise PREADY only after the acknowledge returned to 0. *(when: Four-phase handshake (CFG-4PH))* | 3:s16 (p144) |
| AB2-3-32 | MUST | system | scenario | The IP shall be correct for any frequency ratio and phase of i_clk_mst and i_clk_slv, including equal frequency. | 3:s17 (p145) |
| AB2-3-33 | MUST | system | none | Only the five crossings (request, request bundle, acknowledge, response bundle, wake-up) shall exist between the clock domains. | 3:s18 (p146) |
| AB2-3-34 | MUST | system | none | Each control bit shall cross through a synchronizer and no bundle bit shall cross through one. | 3:s18 (p146) |
| AB2-3-35 | MUST | system | none | Synchronizer depth shall follow PARA_APBCDC_CELL_TYPE: 1 and 2 two stages, 3 three stages, 4 four stages. | 3:s19 (p147) |
| AB2-3-36 | MUST_NOT | system | none | The value 0 (no stage) is for simulation only and shall not be used in a netlist. *(when: Netlist)* | 3:s19 (p147) |
| AB2-3-37 | MUST | system | both | Both resets shall be active-low with asynchronous assertion. | 3:s20 (p148) |
| AB2-3-38 | MUST | system | both | Every flip-flop of the domain shall be at its reset value: payload registers 0, request 0, acknowledge 0, FSMs IDLE, PSEL, PENABLE, PREADY, PSLVERR, PWAKEUP 0. *(when: While a reset is asserted)* | 3:s20 (p148) |
| AB2-3-39 | MUST | system | scenario | The two resets shall be asserted together and each released synchronously to its domain clock, outside the IP. | 3:s21 (p149) |
| AB2-3-40 | MUST | system | scenario | A transfer in flight when a reset is asserted is lost. *(when: Transfer in flight when reset asserted)* | 3:s21 (p149) |
| AB2-3-41 | MUST_NOT | system | none | Asserting only one reset is not supported. | 3:s21 (p149) |
| AB2-3-42 | MUST | system | both | o_apb_pwakeup shall be a flip-flop output that is high whenever the synchronized i_apb_pwakeup is high or a completer-side transfer is in progress. *(when: APB5)* | 3:s22 (p150) |
| AB2-3-43 | MUST | system | assertion | o_apb_pwakeup shall be high no later than o_apb_psel. *(when: APB5)* | 3:s22 (p150) |
| AB2-3-44 | MUST | system | both | PAUSER, PWUSER, PRUSER, PBUSER shall be transported with the same timing rules as the other request and response fields; a signal with width parameter 0 is not present. *(when: APB5)* | 3:s23 (p151) |
| AB2-3-45 | MUST | system | both | The APB5 signals shall have no effect: o_apb_pwakeup is 0 and user outputs are 0. *(when: PARA_APBCDC_APB5 = 0)* | 3:s24 (p152) |
| AB2-3-46 | MUST | system | scenario | The IP shall accept the parameter values of Section 8. | 3:s25 (p153) |
| AB2-3-47 | MAY | system | none | Behavior with an illegal parameter value is not specified and the IP does not check it. *(when: Illegal parameter value)* | 3:s25 (p153) |
| AB2-3-48 | MUST | system | both | Duration from first Setup cycle to end of the requester PREADY cycle shall not exceed (N+3) x T_mst + (N+3+w) x T_slv. *(when: HS_TYPE 0)* | 3:s26 (p154) |
| AB2-3-49 | MUST | system | both | Duration from first Setup cycle to end of the requester PREADY cycle shall not exceed (2N+4) x T_mst + (2N+4+w) x T_slv. *(when: HS_TYPE 1)* | 3:s27 (p155) |
| AB2-3-50 | MUST | system | both | The bridge shall carry one transfer at a time. | 3:s28 (p156) |
| AB2-3-51 | MUST | system | none | The IP shall be delivered with a Synopsys-dialect SDC defining the two clocks, interface budgets and exceptions of the five crossings, with budgets computed from clock periods and synchronizer depth. | 3:s29 (p157) |
| AB2-3-52 | MUST | system | none | Each crossing path shall be constrained by set_max_delay with clock latency ignored. | 3:s30 (p158) |
| AB2-3-53 | MUST_NOT | system | none | No set_clock_groups -asynchronous and no set_false_path, other than the hold-only false path of the crossings, shall exist between the two clocks. *(when: Between the two clocks)* | 3:s30 (p158) |
| AB2-3-54 | MUST | system | none | The clock latency difference between launch and capture flip-flops of every crossing shall be smaller than the one-destination-period guard band. *(when: After clock-tree synthesis)* | 3:s31 (p159) |
| AB2-3-55 | MUST | system | none | The RTL shall comply with REF-003 and use the hierarchy of Section 14.2. | 3:s32 (p160) |
| AB2-3-56 | MUST | system | none | Synchronizer cells shall be instantiated only inside wrapper m_vlsit_apbcdc_cell_sync, named u_dont_touch_ followed by the function, with a simulation model adding random extra output latency of 0, 1 or 2 destination cycles. | 3:s33 (p161) |
| AB2-3-57 | MUST | system | none | Every waveform of the Section 10.3 plan shall exist as an image with its WaveJSON source, and the prototype scripts shall reproduce them. | 3:s34 (p162) |
| AB2-3-58 | MUST | system | none | The random regression shall cover both handshake types, two synchronizer depths, APB4 and APB5, at least ten clock ratios including equal and 9:1 both directions, with wait states and errors, and report no error. | 3:s35 (p163) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-4-01 | MUST | system | scenario | CFG-MIN must be based on CFG-APB4 with FEAT-004, FEAT-006 and FEAT-007 disabled, ADDR_W 1 and DATA_W 8, as the smallest legal instance verified by TEST-014. *(when: CFG-MIN configuration)* | 4:s6 (p176) |
| AB2-4-02 | MUST | system | scenario | FEAT-004, FEAT-006 and FEAT-007 must be selected by an elaboration-time parameter and be present or absent, not enabled or disabled at run time. *(when: FEAT-004, FEAT-006 and FEAT-007 are selected by a parameter at elaboration)* | 4:s7 (p178) |
| AB2-4-03 | MUST_NOT | system | none | Parameter combinations listed as illegal in Section 8 must not be used. | 4:s8 (p178) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-5.3-01 | MUST | master | scenario | The mst block loads reg_req_payload with PWRITE, PADDR, PPROT, PSTRB, PWDATA (and PAUSER, PWUSER in APB5) and launches the request. *(when: i_apb_psel is high, i_apb_penable is low (Setup phase) and the mst FSM is in IDLE)* | 5.3:s2 (p201) |
| AB2-5.3-02 | MUST | master | both | With the two-phase handshake reg_req toggles; with the four-phase handshake reg_req rises. *(when: Setup capture launches the request)* | 5.3:s2 (p201) |
| AB2-5.3-03 | MUST | master | assertion | Loading reg_req_payload and launching the request happen at the same clock edge. *(when: Setup capture)* | 5.3:s3 (p201) |
| AB2-5.3-04 | MUST | slave | scenario | The slv FSM loads reg_apb_payload from reg_req_payload, which has been stable for at least N destination periods, then raises PSEL (Setup). *(when: slv FSM sees the request event after u_sync_req)* | 5.3:s4, 5.3:s5 (p202) |
| AB2-5.3-05 | MUST | slave | assertion | PENABLE (Access) is raised one cycle after PSEL. *(when: after PSEL is raised for Setup)* | 5.3:s5 (p202) |
| AB2-5.3-06 | MUST | slave | assertion | The slv FSM waits in ACCESS until the completer drives PREADY. *(when: slv FSM in ACCESS)* | 5.3:s7 (p203) |
| AB2-5.3-07 | MUST | slave | assertion | At that edge the slv block loads reg_resp_hold with PRDATA, PSLVERR, PRUSER, PBUSER, drops PSEL and PENABLE, and launches the acknowledge (toggle or rise). *(when: completer drives PREADY in ACCESS)* | 5.3:s8 (p203) |
| AB2-5.3-08 | MUST | master | both | The mst FSM loads the response output registers from reg_resp_hold and raises PREADY for one cycle (state RESP). *(when: two-phase handshake and mst FSM sees the acknowledge event via u_sync_ack)* | 5.3:s10, 5.3:s11 (p204) |
| AB2-5.3-09 | MUST | master | scenario | The mst FSM first drops the request, waits for the acknowledge to fall, then loads the response and raises PREADY. *(when: four-phase handshake)* | 5.3:s12 (p204) |
| AB2-5.3-10 | MUST | slave | scenario | The slv FSM waits in REQ0 for the request to fall and then drops the acknowledge. *(when: four-phase handshake, slv FSM in REQ0)* | 5.3:s12 (p204) |
| AB2-5.3-11 | MUST | master | scenario | The mst FSM returns to IDLE and captures the next Setup phase driven in the cycle after the PREADY cycle. *(when: after the PREADY cycle)* | 5.3:s14 (p205) |
| AB2-5.3-12 | MUST | system | scenario | i_apb_pwakeup is registered in the mst block, crosses through u_sync_wk, and drives o_apb_pwakeup through a flip-flop in the slv block together with an in-progress term. *(when: APB5)* | 5.3:s15 (p206) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-5.4-01 | MUST | system | assertion | At most one transfer is in flight, and the FSMs are in IDLE only between transfers. | 5.4:s1 (p210) |
| AB2-5.4-02 | MUST | system | assertion | The request and response bundles change only while the handshake is not in the phase in which the other domain may load them. | 5.4:s2 (p211) |
| AB2-5.4-03 | MUST | system | assertion | With the two-phase handshake the request and acknowledge bits are equal; with the four-phase handshake both are 0. *(when: no transfer in flight)* | 5.4:s3 (p212) |
| AB2-5.4-04 | MUST | master | assertion | Requester-side PREADY is high only in state RESP, for one cycle per transfer. | 5.4:s4 (p213) |
| AB2-5.4-05 | MUST | slave | assertion | Completer-side PSEL is high only in states SETUP and ACCESS. | 5.4:s5 (p214) |
| AB2-5.4-06 | MUST | system | assertion | Every flip-flop that drives an APB output is reset to 0. *(when: reset)* | 5.4:s6 (p215) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-6.1-01 | MUST | system | none | The IP provides interface IF-001, an AMBA APB4/APB5 Issue D completer interface (requests in, responses out) in CLK-MST, in all configurations. | 6.1:s1 (p223) |
| AB2-6.1-02 | MUST | system | none | The IP provides interface IF-002, an AMBA APB4/APB5 Issue D requester interface (requests out, responses in) in CLK-SLV, in all configurations. | 6.1:s2 (p224) |
| AB2-6.1-03 | MUST | system | none | The IP provides interface IF-003 as receiver of clocks and hardware resets (inputs) for CLK-MST and CLK-SLV, in all configurations. | 6.1:s3 (p225) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-6.2-01 | MUST | slave | assertion | o_apb_pslverr is a flop output that is high only in the o_apb_pready cycle, loaded with o_apb_pready and cleared at the next edge; reset value 0. | 6.2:s20 (p247) |
| AB2-6.2-02 | MUST | slave | assertion | o_apb_pwrite is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: o_apb_psel is high)* | 6.2:s27 (p254) |
| AB2-6.2-03 | MUST | slave | assertion | o_apb_paddr is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: o_apb_psel is high)* | 6.2:s28 (p255) |
| AB2-6.2-04 | MUST | slave | assertion | o_apb_pprot is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: o_apb_psel is high)* | 6.2:s29 (p256) |
| AB2-6.2-05 | MUST | slave | assertion | o_apb_pstrb is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: o_apb_psel is high)* | 6.2:s30 (p257) |
| AB2-6.2-06 | MUST | slave | assertion | o_apb_pwdata is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: o_apb_psel and o_apb_pwrite are high)* | 6.2:s31 (p258) |
| AB2-6.2-07 | MUST | slave | assertion | o_apb_pauser is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: CFG-USER and o_apb_psel is high)* | 6.2:s33 (p260) |
| AB2-6.2-08 | MUST | slave | assertion | o_apb_pwuser is loaded with the request and stays stable until the transfer completes; reset value 0. *(when: CFG-USER and o_apb_psel and o_apb_pwrite are high)* | 6.2:s34 (p261) |

## 6.3 Protocol behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-6.3-01 | MUST | master | assertion | A transfer starts with a one-cycle Setup phase (PSEL high, PENABLE low), followed by the Access phase (PENABLE high), which ends in the cycle where PREADY is high. *(when: start of an APB transfer)* | 6.3:s4 (p274) |
| AB2-6.3-02 | MAY | master | scenario | After PREADY the bus may return to IDLE or go directly to the Setup phase of the next transfer. *(when: after the cycle where PREADY is high)* | 6.3:s5 (p274) |
| AB2-6.3-03 | MUST | master | both | PADDR, PPROT, PENABLE, PWRITE, PAUSER, PSTRB, active PWDATA lanes and PWUSER of a write are valid whenever PSEL is high; the bridge captures them in the Setup cycle. *(when: PSEL is high)* | 6.3:s7 (p275) |
| AB2-6.3-04 | MUST | slave | assertion | PREADY is valid when PSEL and PENABLE are high. *(when: PSEL and PENABLE are high)* | 6.3:s8 (p275) |
| AB2-6.3-05 | MUST | slave | assertion | PRDATA of a read, PSLVERR, PRUSER of a read and PBUSER are valid when PSEL, PENABLE and PREADY are high. *(when: PSEL, PENABLE and PREADY are high)* | 6.3:s9 (p275) |
| AB2-6.3-06 | MUST | master | assertion | PADDR, PPROT, PWRITE, PWDATA, PSTRB, PAUSER and PWUSER must not change between Setup and Access phase and while PREADY is low. *(when: between the Setup and Access phase and while PREADY is low)* | 6.3:s11 (p276) |
| AB2-6.3-07 | MUST | system | both | The bridge guarantees stability of the completer-side fields by loading them into reg_apb_payload once, relying on requester stability only in the Setup cycle. *(when: completer side)* | 6.3:s12 (p276) |
| AB2-6.3-08 | MUST | system | assertion | The bridge raises the requester-side PREADY only after the completer-side PREADY. *(when: completer extends the Access phase with PREADY low)* | 6.3:s14 (p277) |
| AB2-6.3-09 | MUST | slave | assertion | PSLVERR is valid only in the last cycle of a transfer. | 6.3:s16 (p278) |
| AB2-6.3-10 | MUST | system | both | The bridge forwards PRDATA and PSLVERR together without masking, even for a read with an error. *(when: a transfer completes with an error)* | 6.3:s17 (p278) |
| AB2-6.3-11 | MUST | master | assertion | PSTRB must be low in a read. *(when: read transfer)* | 6.3:s19 (p279) |
| AB2-6.3-12 | MUST | system | both | The bridge forwards PSTRB as received. | 6.3:s20 (p279) |
| AB2-6.3-13 | MUST | master | assertion | PWAKEUP must be glitch-free to be sampled asynchronously and must stay high until PREADY when high in the same cycle as PSEL. *(when: APB5; PWAKEUP high in the same cycle as PSEL)* | 6.3:s22 (p280) |
| AB2-6.3-14 | MAY | master | scenario | PWAKEUP may be asserted before, during or after PSEL. *(when: APB5)* | 6.3:s22 (p280) |
| AB2-6.3-15 | SHOULD | master | assertion | PWAKEUP should be asserted one cycle before PSEL. *(when: APB5)* | 6.3:s22 (p280) |
| AB2-6.3-16 | MAY | slave | scenario | A completer may wait for PWAKEUP before driving PREADY. *(when: APB5)* | 6.3:s23 (p280) |
| AB2-6.3-17 | MUST | master | assertion | PAUSER and PWUSER are valid with PSEL (PWUSER also with PWRITE) and keep their value through Setup and Access phases. *(when: APB5)* | 6.3:s25 (p281) |
| AB2-6.3-18 | MUST | slave | assertion | PRUSER and PBUSER are valid in the PREADY cycle. *(when: APB5)* | 6.3:s25 (p281) |
| AB2-6.3-19 | SHOULD | system | none | A domain-crossing bridge should provide all user signals. *(when: domain-crossing bridge)* | 6.3:s27 (p281) |
| AB2-6.3-20 | MUST | system | scenario | The bridge performs one completer-side transfer and returns the response. *(when: write or read without wait states, completer PREADY in the first Access cycle)* | 6.3:s28 (p285) |
| AB2-6.3-21 | MUST | system | both | Requester-side PREADY stays low until the completer response. *(when: completer holds PREADY low for any number of cycles)* | 6.3:s29 (p286) |
| AB2-6.3-22 | MUST | system | both | The bridge returns PSLVERR with PREADY and forwards the data. *(when: completer answers with PSLVERR)* | 6.3:s30 (p287) |
| AB2-6.3-23 | MUST | system | scenario | The bridge accepts a back-to-back transfer whose Setup phase follows right after PREADY. *(when: next Setup phase immediately after PREADY)* | 6.3:s31 (p288) |
| AB2-6.3-24 | MUST | system | both | The bridge ignores PENABLE high without a preceding Setup cycle and starts no transfer. *(when: PENABLE high without a preceding Setup cycle)* | 6.3:s32 (p289) |
| AB2-6.3-25 | MUST | system | scenario | The bridge does not detect the change and uses the values captured in the Setup phase. *(when: requester changes a field during the Access phase)* | 6.3:s33 (p290) |
| AB2-6.3-26 | MUST | system | scenario | The bridge waits without limit for the completer PREADY. *(when: completer never drives PREADY)* | 6.3:s34 (p291) |
| AB2-6.3-27 | MUST_NOT | system | scenario | A single reset asserted alone is not supported; both resets must be asserted together, and a transfer in flight is lost on reset. *(when: one reset asserted alone)* | 6.3:s35 (p292) |
| AB2-6.3-28 | MUST | system | scenario | The transfer in flight is lost when reset is asserted mid-transfer. *(when: reset in the middle of a transfer)* | 6.3:s35 (p292) |

## 6.4 Interrupts and events

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-6.4-01 | MUST | system | none | The IP has no interrupt or event output; errors travel as PSLVERR of the transfer. | 6.4:s1 (p312) |

## 7.2 CDC and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-7.2-01 | MUST | system | scenario | Only the five listed crossings (CDC-001 to CDC-005) join the CLK-MST and CLK-SLV domains; no other path exists between them. | 7.2:s1 (p325) |
| AB2-7.2-02 | MUST | system | both | Each data bundle must be held stable and loaded by the destination only after its control bit arrives, so no bundle bit passes through a synchronizer. *(when: Crossing of data bundles between domains)* | 7.2:s2 (p325) |
| AB2-7.2-03 | MUST | master | both | The request bundle reg_req_payload must be held in mst, loaded at the launch edge of the request bit, and loaded into reg_apb_payload in slv at the edge that sees the request event, without a synchronizer. *(when: Request launch (CDC-001))* | 7.2:s3 (p329) |
| AB2-7.2-04 | MUST | system | assertion | The request hold register reg_req_payload and reg_apb_payload must reset to 0. *(when: Reset)* | 7.2:s3 (p329) |
| AB2-7.2-05 | MUST | system | scenario | reg_req must cross to slv through N-stage synchronizer u_sync_req with no logic between the flop and the first stage, its stages reset to 0 by i_rst_n_slv. | 7.2:s4 (p330) |
| AB2-7.2-06 | MUST | system | scenario | reg_ack must cross to mst through N-stage synchronizer u_sync_ack with no logic before the first stage, reset to 0 by i_rst_n_mst. | 7.2:s5 (p331) |
| AB2-7.2-07 | MUST | slave | both | reg_resp_hold must be held in slv, loaded at the launch edge of the acknowledge bit, and loaded into reg_resp_payload in mst at the edge that sees the acknowledge event, without a synchronizer. *(when: Response return (CDC-004))* | 7.2:s6 (p332) |
| AB2-7.2-08 | MUST | system | assertion | reg_resp_hold and reg_resp_payload must reset to 0. *(when: Reset)* | 7.2:s6 (p332) |
| AB2-7.2-09 | MUST | system | scenario | reg_wakeup, a registered copy of i_apb_pwakeup, must cross to slv through N-stage synchronizer u_sync_wk, reset to 0 by i_rst_n_slv. *(when: APB5 only)* | 7.2:s7 (p333) |
| AB2-7.2-10 | MUST | system | none | The two resets are asserted together and each released synchronously to its own clock, outside the IP. | 7.2:s8, 7.3:s4 (p335) |
| AB2-7.2-11 | MAY | system | scenario | Release of one reset while the other domain is still in reset is allowed; no request is launched or seen because the mst FSM leaves IDLE only on a Setup phase. *(when: One domain released while the other is still in reset)* | 7.2:s9 (p335) |

## 7.3 Reset domains and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-7.3-01 | MUST | master | assertion | On i_rst_n_mst assertion (active-low, asynchronous), all mst-block state resets: registers 0, FSM IDLE, o_apb_pready and o_apb_pslverr 0. *(when: i_rst_n_mst asserted)* | 7.3:s1 (p341) |
| AB2-7.3-02 | MUST | slave | assertion | On i_rst_n_slv assertion (active-low, asynchronous), all slv-block state resets: registers 0, FSM IDLE, including o_apb_psel, o_apb_penable and o_apb_pwakeup. *(when: i_rst_n_slv asserted)* | 7.3:s2 (p342) |
| AB2-7.3-03 | MUST_NOT | system | none | The IP must contain no reset synchronizer; both resets must arrive already synchronized. | 7.3:s3 (p344) |
| AB2-7.3-04 | MUST_NOT | master | assertion | No transfer may start before both resets are released; the requester keeps i_apb_psel low until then. *(when: Until both resets are released)* | 7.3:s5 (p344) |
| AB2-7.3-05 | MUST_NOT | system | none | Stopped-clock, warm-reset and retention cases are not supported. | 7.3:s6 (p344) |

## 7.4 Power intent (if applicable)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-7.4-01 | MUST_NOT | system | none | The IP has no isolation, retention or power sequencing of its own; it sits in one always-on power domain. | 7.4:s1 (p348) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-8-01 | MUST_NOT | system | none | The IP does not include an elaboration check for illegal parameter values (REQ-PARAM-001). | 8:s3 (p352) |
| AB2-8-02 | MUST | system | scenario | PARA_APBCDC_ADDR_W, default 32 and legal range 1 to 32, sets the width of PADDR and of the request bundle. | 8:s4 (p356) |
| AB2-8-03 | MUST | system | scenario | PARA_APBCDC_DATA_W, default 32 and legal values 8, 16 or 32, sets the width of PWDATA and PRDATA; PSTRB has DATA_W/8 bits. | 8:s5 (p357) |
| AB2-8-04 | MUST | system | scenario | PARA_APBCDC_APB5 selects APB4 (0, default) or APB5 (1); APB5 adds PWAKEUP and the user signals, and user widths apply only when 1. *(when: PARA_APBCDC_APB5 = 1)* | 8:s6 (p358) |
| AB2-8-05 | MUST | system | scenario | PARA_APBCDC_USER_REQ_W (0 to 128, default 0) sets the width of PAUSER, only with PARA_APBCDC_APB5 = 1; 0 means no PAUSER. | 8:s7 (p359) |
| AB2-8-06 | MUST | system | scenario | PARA_APBCDC_USER_DATA_W (0 to DATA_W, default 0) sets the width of PWUSER and PRUSER, only with APB5 = 1; 0 means none. | 8:s8 (p360) |
| AB2-8-07 | SHOULD | system | none | PARA_APBCDC_USER_DATA_W should be an integer multiple of 8 (REF-001 3.7.3). | 8:s8 (p360) |
| AB2-8-08 | MUST | system | scenario | PARA_APBCDC_USER_RESP_W (0 to 16, default 0) sets the width of PBUSER, only with PARA_APBCDC_APB5 = 1; 0 means no PBUSER. | 8:s9 (p361) |
| AB2-8-09 | MUST | system | scenario | PARA_APBCDC_HS_TYPE selects two-phase toggle (0, default) or four-phase level (1) handshake; latency and crossing events differ but APB interface function is the same. | 8:s10 (p362) |
| AB2-8-10 | MUST | system | scenario | PARA_APBCDC_CELL_TYPE (0 to 4, default 2) selects the synchronizer cell option, with N = 2, 2, 3, 4 stages for values 1 to 4. | 8:s11 (p363) |
| AB2-8-11 | MUST_NOT | system | none | Value 0 (bypass) is for simulation only and is rejected by the SDC. *(when: PARA_APBCDC_CELL_TYPE = 0)* | 8:s11 (p363) |
| AB2-8-12 | MUST | system | scenario | LPARA_STRB_W is derived as DATA_W / 8, giving 1, 2 or 4. | 8:s12 (p364) |
| AB2-8-13 | MUST | system | scenario | LPARA_REQ_W equals ADDR_W + 3 + 1 + STRB_W + DATA_W, plus USER_REQ_W and USER_DATA_W in APB5, and is at least 7. | 8:s13 (p365) |
| AB2-8-14 | MUST | system | scenario | LPARA_RESP_W equals DATA_W + 1, plus USER_DATA_W and USER_RESP_W in APB5, and is at least 9. | 8:s14 (p366) |
| AB2-8-15 | MUST_NOT | system | none | Illegal configurations (bad data/address width, user width over limit or with APB5 = 0, out-of-range options) must not be used; the IP does not check them and behavior is unspecified. *(when: illegal parameter configuration)* | 8:s21, 8:s22 (p377) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-9-01 | MUST | system | both | The bridge must move the fields unchanged and perform no arithmetic on them. | 9:s2 (p381) |
| AB2-9-02 | MUST | system | both | The address is a byte address of width PARA_APBCDC_ADDR_W and is forwarded without extension or truncation. | 9:s3 (p385) |
| AB2-9-03 | MUST | system | both | The data word of width PARA_APBCDC_DATA_W is opaque and is forwarded without extension or truncation. | 9:s4 (p386) |
| AB2-9-04 | MUST | system | both | Write strobes have width LPARA_STRB_W, one bit per byte lane (bit n for PWDATA bits 8n+7 to 8n), and are forwarded as received without extension or truncation. | 9:s5 (p387) |
| AB2-9-05 | MUST | system | both | Protection is 3 bits wide, encoded as APB (bit 0 privileged, bit 1 non-secure, bit 2 instruction), and forwarded as received. | 9:s6 (p388) |
| AB2-9-06 | MUST | system | both | The request bundle of width LPARA_REQ_W packs fields from the least significant bit in order PADDR, PPROT, PWRITE, PSTRB, PWDATA, PAUSER, PWUSER; a zero-width field contributes no bit. | 9:s7 (p389) |
| AB2-9-07 | MUST | system | both | The response bundle of width LPARA_RESP_W packs fields from the least significant bit in order PRDATA, PSLVERR, PRUSER, PBUSER; a zero-width field contributes no bit. | 9:s8 (p390) |
| AB2-9-08 | MUST | system | both | Request and acknowledge bits are 1 bit wide; in two-phase mode the value toggles per transfer and the request and acknowledge are equal when idle. *(when: Two-phase handshake)* | 9:s9 (p391) |
| AB2-9-09 | MUST | system | both | In four-phase mode the request and acknowledge bit is 1 while a phase is requested and 0 when idle. *(when: Four-phase handshake)* | 9:s9 (p391) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-10.1-01 | MUST | master | both | The requester FSM must leave IDLE to WAIT, loading reg_req_payload and toggling reg_req (two-phase) or setting it (four-phase) at the exit edge. *(when: mst FSM in ENUM_ST_IDLE with i_apb_psel high and i_apb_penable low)* | 10.1:s4 (p403) |
| AB2-10.1-02 | MUST | master | both | In WAIT the requester must keep o_apb_pready low; on the acknowledge event it goes to RESP (two-phase, raising o_apb_pready) or clears reg_req and goes to CLOSE (four-phase). *(when: mst FSM in ENUM_ST_WAIT)* | 10.1:s5 (p404) |
| AB2-10.1-03 | MUST | master | both | In CLOSE reg_req must be 0; when the synchronized acknowledge falls the FSM loads the response registers, raises o_apb_pready and goes to RESP. *(when: mst FSM in ENUM_ST_CLOSE (four-phase))* | 10.1:s6 (p405) |
| AB2-10.1-04 | MUST | master | assertion | In RESP o_apb_pready must be high for one cycle, then the FSM returns to IDLE and clears o_apb_pready and o_apb_pslverr at the exit edge. *(when: mst FSM in ENUM_ST_RESP)* | 10.1:s7 (p406) |
| AB2-10.1-05 | MUST | slave | both | The completer FSM must go to SETUP, loading reg_apb_payload from the request bundle and driving o_apb_psel high at the exit edge. *(when: slv FSM in ENUM_ST_IDLE and request event seen (two-phase: synchronized request differs from reg_ack; four-phase: synchronized request high))* | 10.1:s9 (p412) |
| AB2-10.1-06 | MUST | slave | assertion | In SETUP o_apb_penable must be low; the FSM always moves to ACCESS and sets o_apb_penable high at the exit edge. *(when: slv FSM in ENUM_ST_SETUP)* | 10.1:s10 (p413) |
| AB2-10.1-07 | MUST | slave | both | On i_apb_pready high the FSM must load reg_resp_hold, drop o_apb_psel and o_apb_penable, toggle (two-phase) or set (four-phase) reg_ack, and go to IDLE (two-phase) or REQ0 (four-phase). *(when: slv FSM in ENUM_ST_ACCESS and i_apb_pready high)* | 10.1:s11 (p414) |
| AB2-10.1-08 | MUST | slave | both | In REQ0 the FSM must wait for the synchronized request to fall, then clear reg_ack and go to IDLE. *(when: slv FSM in ENUM_ST_REQ0 and synchronized request low (four-phase))* | 10.1:s12 (p415) |

## 10.2 Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-10.2-01 | MUST | system | scenario | The bridge must capture the fields, cross the request, run one APB write on the completer side and return the response, with PREADY for one cycle. *(when: Setup phase with PWRITE=1, mst FSM in IDLE)* | 10.2:s1 (p421) |
| AB2-10.2-02 | MUST | system | scenario | For a read the bridge must return PRDATA and PRUSER to the requester with PREADY. *(when: Setup phase with PWRITE=0)* | 10.2:s2 (p422) |
| AB2-10.2-03 | MUST | slave | scenario | The completer-side Access phase must last w + 1 cycles and requester-side PREADY must follow after the response. *(when: completer holds PREADY low for w cycles)* | 10.2:s3 (p423) |
| AB2-10.2-04 | MUST | system | both | PSLVERR must be carried in the response bundle and be high in the requester-side PREADY cycle. *(when: completer drives PSLVERR with PREADY)* | 10.2:s4 (p424) |
| AB2-10.2-05 | MUST | master | scenario | The mst FSM must be back in IDLE and capture the Setup phase immediately, starting the second transfer at once; one transfer at a time. *(when: next Setup phase in the cycle after PREADY)* | 10.2:s5 (p425) |
| AB2-10.2-06 | MUST | slave | both | o_apb_pwakeup must follow the synchronized wake-up OR the in-progress term and be high before or with o_apb_psel. *(when: APB5, i_apb_pwakeup or a transfer in progress)* | 10.2:s6 (p426) |
| AB2-10.2-07 | MUST | system | both | PAUSER and PWUSER must cross in the request bundle and PRUSER and PBUSER in the response bundle, with identical values on the other side. *(when: APB5 with user widths above 0)* | 10.2:s7 (p427) |
| AB2-10.2-08 | MUST | system | both | State of the domain must clear asynchronously, all registers at reset value, and a transfer in flight is lost. *(when: i_rst_n_mst or i_rst_n_slv low)* | 10.2:s8 (p428) |
| AB2-10.2-09 | MUST | system | scenario | The bridge must use the four-phase handshake and give the same results as OP-001 and OP-002. *(when: PARA_APBCDC_HS_TYPE = 1)* | 10.2:s9 (p429) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-10.3-01 | MUST | master | both | At E0 the request bundle must be loaded, the request bit launched, FSM to WAIT, and o_apb_pready stay low. *(when: Setup edge E0 with mst FSM in IDLE)* | 10.3:s38 (p490) |
| AB2-10.3-02 | MUST | slave | both | The slv FSM must see the event at edge N+1 of i_clk_slv, load reg_apb_payload, raise o_apb_psel, then pass SETUP and ACCESS, with o_apb_penable high from the second edge. *(when: after E0)* | 10.3:s39, 10.3:s40 (p491) |
| AB2-10.3-03 | MUST | slave | assertion | At the i_apb_pready edge the response must be held, acknowledge launched, and o_apb_psel and o_apb_penable low. *(when: i_apb_pready high in ACCESS)* | 10.3:s41 (p493) |
| AB2-10.3-04 | MUST | master | both | The mst FSM must load the response and raise o_apb_pready for one cycle, then go to IDLE. *(when: N+1 i_clk_mst edges after acknowledge launch)* | 10.3:s42 (p494) |

## 10.4 Arbitration, buffering, and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-10.4-01 | MUST | system | scenario | The bridge has no arbitration: one requester-side interface and one completer-side interface, handling one transfer at a time. | 10.4:s1 (p498) |
| AB2-10.4-02 | MUST_NOT | master | assertion | A new Setup phase must not be driven by the requester before PREADY, since APB is non-pipelined. *(when: A transfer is in progress and PREADY has not yet completed it)* | 10.4:s3 (p498) |
| AB2-10.4-03 | MUST | system | scenario | Duration D from first Setup cycle to end of PREADY cycle must not exceed (N+3)xT_mst + (N+3+w)xT_slv; for equal clocks 2N+6+w cycles. *(when: Two-phase handshake, N synchronizer stages, w completer wait states)* | 10.4:s8 (p504) |
| AB2-10.4-04 | MUST | system | scenario | Duration D from first Setup cycle to end of PREADY cycle must not exceed (2N+4)xT_mst + (2N+4+w)xT_slv; for equal clocks 4N+8+w cycles. *(when: Four-phase handshake, N synchronizer stages, w completer wait states)* | 10.4:s9 (p505) |
| AB2-10.4-05 | MUST | system | scenario | Throughput is one transfer per duration D, with no pipelining of transfers. | 10.4:s19 (p517) |

## 10.5 Memories and storage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-10.5-01 | MUST_NOT | system | none | The IP must contain no memory or macro; the only storage is the registers of the two bundles and the control flip-flops. | 10.5:s1 (p521) |

## 11 Register and programming model

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-11-01 | MUST_NOT | system | none | The IP must not provide software-visible registers; it is configured only by parameters (Section 8). | 11:s1 (p525) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-12-01 | MUST | interconnect | both | The bridge must forward the completer PSLVERR so that o_apb_pslverr is high in the o_apb_pready cycle. *(when: Completer drives PSLVERR with PREADY)* | 12:s1 (p531) |
| AB2-12-02 | MUST | interconnect | scenario | The next transfer must be independent of a previous transfer that completed with an error. *(when: After a transfer completed with PSLVERR)* | 12:s1 (p531) |
| AB2-12-03 | MUST | interconnect | scenario | The bridge must wait without limit for PREADY, and the requester sees PREADY low during the wait. *(when: Completer never drives PREADY)* | 12:s2 (p532) |
| AB2-12-04 | MUST | system | scenario | The hang condition is cleared by reset; recovery is by a system watchdog or a reset of both domains. *(when: Completer never drives PREADY (ERR-002))* | 12:s2 (p532) |
| AB2-12-05 | MUST | interconnect | scenario | The in-flight transfer must be lost and all state cleared; both resets must be released and the transfer restarted. *(when: Reset asserted while a transfer is in flight)* | 12:s3 (p533) |
| AB2-12-06 | MUST | interconnect | scenario | The bridge must use the values of the Setup cycle and must ignore PENABLE without a Setup; the violation is not detected. *(when: Requester breaks APB rules by Setup without Access, field change during Access, or PENABLE without Setup)* | 12:s4 (p534) |
| AB2-12-07 | MUST_NOT | any | none | Behavior is not specified and no detection is provided; integrators must not rely on any behavior when only one reset is asserted or a parameter is illegal. *(when: One reset asserted alone, or illegal parameter value)* | 12:s5 (p535) |
| AB2-12-08 | MUST_NOT | interconnect | scenario | The bridge must have no sticky error, no error counter and no error output other than PSLVERR. | 12:s6 (p537) |
| AB2-12-09 | MUST_NOT | interconnect | none | The bridge has no data protection (parity or ECC), so a corrupted bundle bit is not detected. | 12:s7 (p537) |

## 13 Performance, power, and area

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-13-01 | MUST | system | scenario | Two-phase transfer duration must be at most (N + 3) x T_mst + (N + 3 + w) x T_slv. *(when: Two-phase transfer, any clock ratio)* | 13:s1 (p543) |
| AB2-13-02 | MUST | system | scenario | Four-phase transfer duration must be at most (2N + 4) x T_mst + (2N + 4 + w) x T_slv. *(when: Four-phase transfer, any clock ratio)* | 13:s2 (p544) |
| AB2-13-03 | MUST | system | both | Only one transfer is in flight, and the next Setup phase is accepted in the cycle after PREADY. *(when: Any configuration)* | 13:s3 (p545) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-14.1-01 | MUST | system | none | The RTL must follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding authority. | 14.1:s1 (p556) |
| AB2-14.1-02 | MUST | system | none | The RTL must comply with REF-003 except for the single deviation DEC-021 (PRT-03). | 14.1:s2 (p556) |
| AB2-14.1-03 | MUST | system | none | RTL must use one module per file with file name equal to module name, a structural top, ANSI ports with input wire and output logic, and reg_, w_, p_ff_, p_com_ naming. | 14.1:s3 (p556) |
| AB2-14.1-04 | MUST | system | none | FSMs must be named reg_fsm_hs_current_state and w_fsm_hs_nxt_state with ENUM_ST_* state names. | 14.1:s3 (p556) |
| AB2-14.1-05 | MUST | system | none | Parameters must be named PARA_APBCDC_* with the three PAR-02 comment lines; names at most 30 characters; NAM-08 abbreviations used, with payload written in full. | 14.1:s3 (p556) |
| AB2-14.1-06 | MUST | system | none | Cell instances must be named u_dont_touch_ followed by the function and only inside the wrapper; comment lines at most 100 characters; port layout and grouping follow REF-003 FIL-05 and FIL-06. | 14.1:s3 (p556) |
| AB2-14.1-07 | MUST | system | both | Every flip-flop must have an asynchronous reset to 0. | 14.1:s4 (p556) |
| AB2-14.1-08 | MUST_NOT | system | none | SVA, testbench or prototype code must not be in the synthesis file list. | 14.1:s5 (p556) |
| AB2-14.1-09 | MUST | system | none | The register and instance names used by the SDC must be kept as named in the RTL. | 14.1:s6 (p556) |

## 14.2 RTL hierarchy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-14.2-01 | MUST | system | none | m_vlsit_apbcdc_top must be the structural top holding ports, parameters, interconnect and instances. | 14.2:s1 (p562) |
| AB2-14.2-02 | MUST | system | none | m_vlsit_apbcdc_mst must be the requester-side block in CLK-MST/RST-MST and m_vlsit_apbcdc_slv the completer-side block in CLK-SLV/RST-SLV, instantiated in the top. | 14.2:s2, 14.2:s3 (p563) |
| AB2-14.2-03 | MUST | system | none | Synchronizers must be m_vlsit_apbcdc_sync instances in the destination domain (mst: u_sync_ack; slv: u_sync_req, u_sync_wk), built per bit from m_vlsit_apbcdc_cell_sync wrappers. | 14.2:s4, 14.2:s5 (p565) |
| AB2-14.2-04 | MUST | system | none | State must be owned only by the mst block, the slv block and the synchronizers as listed. | 14.2:s6 (p568) |
| AB2-14.2-05 | MUST_NOT | system | none | There must be no register logic and no protocol adapter other than the two FSMs. | 14.2:s7 (p568) |

## 14.2.1 Ports of the internal modules

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-14.2.1-01 | MUST | system | none | Internal module ports must use the Section 6.2 columns, types and APB port names, with internal bundle widths LPARA_REQ_W and LPARA_RESP_W. | 14.2.1:s1, 14.2.1:s2 (p572) |
| AB2-14.2.1-02 | MUST | master | both | o_req must be a flop output launched at the Setup edge, resetting to 0, toggling per transfer in two-phase and high during the request phase in four-phase. | 14.2.1:s4 (p578) |
| AB2-14.2.1-03 | MUST | master | both | o_req_payload must be the hold register loaded at the Setup edge, reset 0, valid and stable. *(when: From launch of o_req until the acknowledge was seen)* | 14.2.1:s5 (p579) |
| AB2-14.2.1-04 | MUST | master | both | o_wakeup must be a flop output registering i_apb_pwakeup one cycle later, with reset value 0. *(when: CFG-APB5)* | 14.2.1:s6 (p580) |
| AB2-14.2.1-05 | MUST | master | none | i_ack must be synchronized in CLK-MST through the first synchronizer stage from the slv launch flop. | 14.2.1:s7 (p581) |
| AB2-14.2.1-06 | MUST | master | both | i_resp_payload must be valid and stable when the acknowledge event is seen and loaded in CLK-MST at that edge. | 14.2.1:s8 (p582) |
| AB2-14.2.1-07 | MUST | slave | none | i_req must be synchronized in CLK-SLV via the first synchronizer stage from the mst launch flop. | 14.2.1:s10 (p588) |
| AB2-14.2.1-08 | MUST | slave | both | i_req_payload must be valid and stable when the request event is seen and loaded in CLK-SLV at that edge. | 14.2.1:s11 (p589) |
| AB2-14.2.1-09 | MUST | slave | none | i_wakeup must be synchronized in CLK-SLV via the first synchronizer stage from the mst launch flop. *(when: CFG-APB5)* | 14.2.1:s12 (p590) |
| AB2-14.2.1-10 | MUST | slave | both | o_ack must be a flop output launched at the edge that sees i_apb_pready, reset 0, toggling per transfer in two-phase and high during the acknowledge phase in four-phase. | 14.2.1:s13 (p591) |
| AB2-14.2.1-11 | MUST | slave | both | o_resp_payload must be the hold register loaded at the edge that sees i_apb_pready, reset 0, valid and stable. *(when: From launch of o_ack until the next request event)* | 14.2.1:s14 (p592) |
| AB2-14.2.1-12 | MUST | system | both | m_vlsit_apbcdc_sync must sample i_data at every i_clk_dst edge, with o_data from the last stage, N stages later, resetting to 0 on active-low i_rst_n_dst. | 14.2.1:s16, 14.2.1:s17, 14.2.1:s18, 14.2.1:s19 (p598) |
| AB2-14.2.1-13 | MUST | system | none | m_vlsit_apbcdc_cell_sync must be a one-bit wrapper with i_d, o_q, PARA_APBCDC_CELL_TYPE and PARA_APBCDC_CELL_RST_VAL set to 0 for all control bits. | 14.2.1:s20 (p603) |
| AB2-14.2.1-14 | MAY | system | none | Pin and cell names of library cells may keep the library style and are exempt from the naming rule. | 14.2.1:s21 (p603) |

## 14.3 Synthesis assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-14.3-01 | MUST | system | none | Synthesis must use top m_vlsit_apbcdc_top with the listed files and configurations, and define VLSIT_SYNTHESIS for synthesis, lint, CDC and formal. | 14.3:s1, 14.3:s3, 14.3:s6 (p609) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-15.1-01 | MUST | system | scenario | Metastability behaviour, reset in the middle of random traffic and the APB protocol assertions shall be verified on the RTL. *(when: Prototype lacked a metastability model, reset in mid random traffic and APB protocol assertions)* | 15.1:s6 (p622) |
| AB2-15.1-02 | MUST | system | scenario | Every quick-run simulation on the RTL must finish with zero failures, zero assertion failures and no assertion left unexercised. *(when: Quick run on delivered RTL, 16 configurations, synthesis and simulation branches, seeds 1 to 3)* | 15.1:s7 (p624) |
| AB2-15.1-03 | MUST | system | scenario | Every third configuration uses a requester changing fields in the Access phase to check Setup values are used, and every third APB5 configuration uses a requester never driving PWAKEUP. *(when: Every third configuration, and every third APB5 configuration)* | 15.1:s8 (p624) |
| AB2-15.1-04 | MUST | system | scenario | All 12 RTL waveforms must match the figure WaveJSON, internal rows included, and assertions must pass in the metastability branch for each scenario. *(when: Simulating the 12 plan waveforms on the RTL)* | 15.1:s8 (p624) |
| AB2-15.1-05 | MUST | system | none | The fault of the completer side loading its request register every cycle instead of at the request event must be shown by the structural check (TEST-015) and the SDC (TEST-016). *(when: Fault whose effect is a timing property only, equivalent in simulation (completer side loading request register every cycle))* | 15.1:s9 (p624) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-15.2-01 | MUST | slave | assertion | PSLVERR must be high only in the PREADY cycle. *(when: Reads and writes with PSLVERR)* | 15.2:s5 (p634) |
| AB2-15.2-02 | MUST | system | scenario | Elaboration, lint and simulation must pass for the legal parameter extremes. *(when: Legal extremes: ADDR_W 1 and 32, DATA_W 8/16/32, user widths 0 and maximum, CELL_TYPE 1 to 4)* | 15.2:s14 (p643) |

## 15.3 Assertions and coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-15.3-01 | MUST | system | none | Assertions and coverage are disabled while either reset is asserted, except SVA-016 which remains enabled. *(when: while either reset is asserted, except SVA-016)* | 15.3:s2 (p652) |
| AB2-15.3-02 | MUST | master | assertion | When o_apb_pready is high, i_apb_psel and i_apb_penable must be high (SVA-001, never fails). *(when: o_apb_pready is high)* | 15.3:s4 (p656) |
| AB2-15.3-03 | MUST | slave | assertion | o_apb_pready must be high for exactly one cycle per transfer (SVA-002). *(when: per transfer)* | 15.3:s5 (p657) |
| AB2-15.3-04 | MUST | slave | assertion | o_apb_pslverr high must imply o_apb_pready high (SVA-003). *(when: o_apb_pslverr is high)* | 15.3:s6 (p658) |
| AB2-15.3-05 | MUST | system | scenario | The requester-side response must equal the completer-side response of the same transfer (SVA-004, checked by scoreboard). *(when: for each transfer)* | 15.3:s7 (p659) |
| AB2-15.3-06 | MUST | master | assertion | o_apb_penable must rise one cycle after o_apb_psel, and o_apb_penable high must imply o_apb_psel high (SVA-005). | 15.3:s8 (p660) |
| AB2-15.3-07 | MUST | master | assertion | Completer-side fields must not change while o_apb_psel is high and i_apb_pready is low (SVA-006). *(when: o_apb_psel high and i_apb_pready low)* | 15.3:s9 (p661) |
| AB2-15.3-08 | MUST | master | assertion | o_apb_psel and o_apb_penable must be low when no transfer is in progress and in reset (SVA-007). *(when: no transfer in progress or in reset)* | 15.3:s10 (p662) |
| AB2-15.3-09 | MUST | system | scenario | Completer-side fields must equal the values of the requester-side Setup cycle (SVA-008, checked by scoreboard). | 15.3:s11 (p663) |
| AB2-15.3-10 | MUST | system | scenario | The number of completer-side transfers must equal the number of requester-side transfers (SVA-009, scoreboard). | 15.3:s12 (p664) |
| AB2-15.3-11 | MUST_NOT | master | assertion | No second completer-side Setup phase may occur before o_apb_pready of the previous transfer (SVA-010). *(when: previous transfer not yet completed by o_apb_pready)* | 15.3:s13 (p665) |
| AB2-15.3-12 | MUST | source | assertion | The request hold register must be stable from request launch until acknowledge is seen, and the response hold register stable from acknowledge launch until the next request is seen (SVA-011). *(when: request: from launch until acknowledge seen; response: from acknowledge launch until next request seen)* | 15.3:s14 (p666) |
| AB2-15.3-13 | MUST | any | assertion | In two-phase handshake the request bit must change exactly once and the acknowledge bit exactly once per transfer (SVA-012). *(when: two-phase handshake)* | 15.3:s15 (p667) |
| AB2-15.3-14 | MUST | any | assertion | In four-phase handshake the sequence must be request high, acknowledge high, request low, acknowledge low, then o_apb_pready (SVA-013). *(when: four-phase handshake)* | 15.3:s16 (p668) |
| AB2-15.3-15 | MUST | master | assertion | o_apb_pwakeup must be high no later than o_apb_psel (SVA-014). *(when: APB5)* | 15.3:s17 (p669) |
| AB2-15.3-16 | MUST | master | assertion | o_apb_pwakeup must stay high until i_apb_pready when it is high with o_apb_psel (SVA-015). *(when: APB5, o_apb_pwakeup high with o_apb_psel)* | 15.3:s18 (p670) |
| AB2-15.3-17 | MUST | system | assertion | In reset every output must be at its reset value (SVA-016). *(when: in reset)* | 15.3:s19 (p671) |
| AB2-15.3-18 | MUST_NOT | system | assertion | After reset no output may be unknown; o_apb_prdata must not be unknown when o_apb_pready of a read is high (SVA-017). *(when: after reset)* | 15.3:s20 (p672) |
| AB2-15.3-19 | MUST | system | assertion | The duration of every transfer must be within the bound of REQ-PERF-001 or REQ-PERF-002 (SVA-018). *(when: every transfer)* | 15.3:s21 (p673) |

## 15.4 Formal, CDC, and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-15.4-01 | MUST_NOT | system | none | Formal analysis is not required in this version; verification is by simulation and assertions. | 15.4:s1 (p685) |
| AB2-15.4-02 | MUST | system | scenario | A CDC tool or the structural check of TEST-015 must confirm only control bits pass through synchronizers, no logic precedes a first stage, and no other path joins the domains across the five crossings. *(when: clocks unrelated; both resets asserted together)* | 15.4:s2 (p686) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-16-01 | MUST_NOT | system | none | The RTL shall contain no latch, no combinational loop, no tri-state, no clock gating and no derived clock, so that scan insertion is possible. | 16:s1 (p692) |
| AB2-16-02 | MUST_NOT | system | none | The IP shall have no DFT ports; a test reset override belongs to the SoC wrapper or reset controller. | 16:s2 (p693) |

## 17.1.2 Interface timing budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-17.1.2-01 | MUST | system | none | EXC-001 shall constrain reg_req_payload to reg_apb_payload with set_max_delay -ignore_clock_latency of (N - 1) x T_slv and set_false_path -hold, hold not checked. *(when: Functional mode)* | 17.1.2:s6, 17.1.3:s1 (p725) |
| AB2-17.1.2-02 | MUST | system | none | EXC-002 shall constrain reg_req to u_sync_req cells with maximum delay T_slv, ignoring clock latency, and hold not checked. *(when: Functional mode)* | 17.1.2:s7, 17.1.3:s2 (p726) |
| AB2-17.1.2-03 | MUST | system | none | EXC-003 shall constrain reg_ack to u_sync_ack cells with maximum delay T_mst, ignoring clock latency, and hold not checked. *(when: Functional mode)* | 17.1.2:s8, 17.1.3:s3 (p727) |
| AB2-17.1.2-04 | MUST | system | none | EXC-004 shall constrain reg_resp_hold (slv) to reg_resp_payload (mst) with maximum delay (N - 1) x T_mst, ignoring clock latency, hold not checked. *(when: Functional mode)* | 17.1.2:s9, 17.1.3:s4 (p728) |
| AB2-17.1.2-05 | MUST | system | none | EXC-005 shall constrain reg_wakeup to u_sync_wk cells with maximum delay T_slv, ignoring clock latency, and hold not checked. *(when: APB5 only)* | 17.1.2:s10, 17.1.3:s5 (p729) |
| AB2-17.1.2-06 | MUST | system | none | Required max transition, max capacitance and max fanout shall follow the project defaults. | 17.1.2:s11 (p731) |
| AB2-17.1.2-07 | SHOULD | system | none | Placement should keep each launch flop and its first synchronizer stage adjacent. *(when: During placement)* | 17.1.2:s12 (p731) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-17.1.3-01 | MUST_NOT | system | none | The SDC shall not use set_clock_groups -asynchronous, set_false_path, or set_max_delay without the latency option between clk_mst and clk_slv. | 17.1.3:s6 (p742) |

## 17.1.4 Rationale of the crossing constraints (why -datapath_only, -ignore_clock_latency)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-17.1.4-01 | MUST | system | none | The tool semantics of -ignore_clock_latency shall be confirmed in the Synopsys documentation (OI-004). | 17.1.4:s2 (p746) |
| AB2-17.1.4-02 | MUST | system | scenario | The bundle shall be stable at the destination flop before the control bit, having crossed N synchronizer stages, tells the destination FSM to load it. | 17.1.4:s4 (p748) |
| AB2-17.1.4-03 | MUST | system | none | Crossing constraints shall use -ignore_clock_latency (Synopsys) so the independent clock trees' latency difference is not counted in the budget. | 17.1.4:s11 (p750) |
| AB2-17.1.4-04 | MUST | system | none | The post-CTS clock latency difference shall stay below the one destination period guard band (REQ-TIM-003). *(when: Post-CTS)* | 17.1.4:s15 (p751) |

## 17.2 Physical assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-17.2-01 | MUST | system | none | Each launch flop of a crossing control bit and its first synchronizer stage shall be placed adjacent. *(when: Floorplan and placement)* | 17.2:s2 (p762) |
| AB2-17.2-02 | SHOULD | system | none | The two bundle registers of each direction should be placed close to each other. *(when: Floorplan and placement)* | 17.2:s2 (p762) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-18-01 | MUST | system | scenario | The bridge only forwards PPROT and performs no security function or security decision based on it. | 18:s1 (p774) |
| AB2-18-02 | MUST | system | scenario | The hold registers keep the last transfer's contents until the next transfer replaces them, with no secure clearing. *(when: After a transfer completes, until the next transfer)* | 18:s3 (p776) |
| AB2-18-03 | MUST_NOT | system | none | The bridge does not support the APB5 parity check signals (DEC-003). | 18:s5 (p778) |

## 20.1 Open items

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-20.1-01 | MUST | system | scenario | The clock controller of the slv domain shall act on i_apb_pwakeup (or on a requester signal) before the request arrives, since the bridge cannot see requests while the clock is stopped. *(when: CFG-APB5 with gated completer-side clock i_clk_slv enabled only by a wake-up)* | 20.1:s2 (p829) |

## 20.2 Assumptions, dependencies and decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-20.2-01 | MUST | master | assertion | The APB requester must issue one Setup phase then Access until PREADY, keep fields stable, and keep PSTRB low in a read. *(when: requester drives APB transfers to the bridge (assumption ASM-001))* | 20.2:s1 (p839) |
| AB2-20.2-02 | MUST | system | none | The clock controller using PWAKEUP must keep i_clk_slv running while a request is in flight, since the bridge cannot detect a request on a stopped clock. *(when: PWAKEUP is used by a clock controller and a request is in flight)* | 20.2:s5 (p843) |
| AB2-20.2-03 | MUST | system | none | The bridge architecture must be a request/acknowledge handshake with bundled data held stable, not an asynchronous FIFO. | 20.2:s7 (p845) |
| AB2-20.2-04 | MUST | system | scenario | One parameter selects APB4 or APB5; APB5 adds PWAKEUP and user signals with configurable widths; no parity check signals are provided. | 20.2:s8 (p846) |
| AB2-20.2-05 | MUST | system | scenario | ADDR_W defaults to 32 (range 1 to 32), DATA_W defaults to 32 (8, 16 or 32), PSTRB and PPROT are always present, and user widths default to 0. | 20.2:s9 (p847) |
| AB2-20.2-06 | MUST | slave | assertion | Every APB output must be a flip-flop output; PREADY must be high only in state RESP, i.e. only once the Access phase has been reached. | 20.2:s24 (p862) |
| AB2-20.2-07 | MUST | system | both | The response must be delivered only after the handshake has closed (acknowledge low), so the next Setup phase can always be accepted. *(when: four-phase handshake selected)* | 20.2:s25 (p863) |
| AB2-20.2-08 | MUST | system | scenario | The RTL top must declare the APB5 ports in every configuration, with user widths of at least 1, unused inputs ignored and unused outputs 0. *(when: RTL top, every configuration)* | 20.2:s26 (p864) |

## 21 Glossary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB2-21-01 | MUST | source | scenario | Multi-bit bundled data must be held stable while the one-bit control signal crosses the domains. *(when: While a one-bit control signal crosses between clock domains)* | 21:s4 (p883) |
| AB2-21-02 | MUST | destination | scenario | The destination must load the bundled multi-bit data only after the control signal has arrived. *(when: Bundled data crossing with a one-bit control signal)* | 21:s4 (p883) |
