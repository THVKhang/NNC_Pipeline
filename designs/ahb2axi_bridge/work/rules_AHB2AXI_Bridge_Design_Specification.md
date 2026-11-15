# Extracted rules - AHB2AXI_Bridge_Design_Specification.md

```
rules: 288  by strength {'MUST': 216, 'SHOULD': 3, 'MAY': 13, 'MUST_NOT': 56}  by check {'none': 71, 'both': 59, 'scenario': 89, 'assertion': 69}
normative sentences: 108  cited 108  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 27 (0 from cache)  cost US$0.8708  tokens in 135401 out 40821
```


## T1 AHB-to-AXI4 Bridge Design Specification / Đặc tả thiết kế cầu nối AHB sang AXI4

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1-01 | MUST | system | none | Requirements stated with 'shall' are mandatory and must be testable. | T1:s4 (p17) |
| AA-T1-02 | SHOULD | system | none | Requirements stated with 'should' are recommendations. | T1:s4 (p17) |
| AA-T1-03 | MAY | system | none | Items stated with 'may' are optional. | T1:s4 (p17) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-1.1-01 | MUST | system | both | The bridge must serialize reads and must never issue speculative reads. | 1.1:s4, 1.1:s9 (p48) |
| AA-1.1-02 | MAY | system | scenario | The bridge may aggregate eligible bufferable Normal Write-back AHB write bursts into AXI4 bursts of up to 16 beats. *(when: Eligible bufferable Normal Write-back AHB write bursts)* | 1.1:s5, 1.1:s10 (p48) |
| AA-1.1-03 | MUST_NOT | system | scenario | The bridge must never merge Device writes. *(when: Device writes)* | 1.1:s5, 1.1:s10 (p48) |
| AA-1.1-04 | MUST | system | both | Reads must always use AXI single-beat transactions. *(when: AHB read transfers)* | 1.1:s19 (p58) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-1.3-01 | MUST | system | scenario | The bridge must provide Full AHB5 Subordinate to AXI4 Manager conversion (FEAT-001). | 1.3:s1 (p83) |
| AA-1.3-02 | MUST | system | scenario | The bridge must use one shared synchronous clock and reset (FEAT-002). | 1.3:s2 (p84) |
| AA-1.3-03 | MUST | system | both | The bridge must implement strict no-speculation serialized reads (FEAT-003). | 1.3:s3 (p85) |
| AA-1.3-04 | MUST | system | scenario | The bridge must support conditional aggregation of bufferable Normal Write-back fixed writes up to 16 beats (FEAT-004). *(when: Bufferable Normal Write-back; full fixed burst; uniform AXI address attributes)* | 1.3:s4 (p86) |
| AA-1.3-05 | MAY | system | scenario | Rotating AXI read/write IDs are an optional configuration with ID-count parameters 1..8, default 1. *(when: ID-count parameters 1..8; default 1)* | 1.3:s5 (p87) |
| AA-1.3-06 | MUST | system | both | The bridge must convert AHB HWSTRB to AXI WSTRB (FEAT-007). | 1.3:s6 (p88) |
| AA-1.3-07 | MUST_NOT | system | none | Parity, exclusive and CSR functions are not included and must be disabled in this revision. *(when: This revision)* | 1.3:s7 (p89) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-2.1-01 | MUST | system | none | The RTL shall follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory baseline for naming, hierarchy, single-clock, reset and synthesis. | 2.1:s3 (p99) |
| AA-2.1-02 | MUST_NOT | system | none | The page-word-count check of converted standards must not be treated as a word-for-word legal or semantic review. | 2.1:s8 (p104) |
| AA-2.1-03 | MUST_NOT | system | none | Licensed PDFs and converted Markdown must remain outside the deliverable folder and must not be copied or redistributed. | 2.1:s9 (p104) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-2.2-01 | MUST_NOT | system | none | User-approved decisions in §20 may restrict legal protocol behavior but must not contradict it. | 2.2:s3 (p111) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-3-01 | MUST | system | none | Verification must be derived from this specification and REF-001/REF-002, not from generated RTL or internal RTL names/structure. | 3:s2, 3:s4, 3:s26 (p135) |
| AA-3-02 | MUST | system | both | The bridge must convert every accepted supported AHB transfer to AXI4 without loss, duplication or data alteration. *(when: For every supported AHB transfer accepted by the IP)* | 3:s5 (p141) |
| AA-3-03 | MUST | slave | both | AHB address/control must be sampled only when HSEL=1, HREADY=1 and HTRANS is NONSEQ or SEQ. | 3:s6 (p142) |
| AA-3-04 | MUST_NOT | slave | assertion | IDLE or BUSY transfers must not issue AXI requests. *(when: HTRANS is IDLE or BUSY)* | 3:s6 (p142) |
| AA-3-05 | MUST | slave | both | Each accepted AHB read must issue exactly one AXI single-beat AR transaction. *(when: Each accepted AHB read)* | 3:s7 (p143) |
| AA-3-06 | MUST_NOT | slave | assertion | No read request may be issued before its AHB address is accepted. | 3:s7 (p143) |
| AA-3-07 | MUST | slave | both | AHB SINGLE and undefined-length INCR transfers and every read beat must map to AXI single-beat transactions. *(when: AHB SINGLE, undefined-length INCR transfers, and every read beat)* | 3:s8 (p144) |
| AA-3-08 | MAY | slave | scenario | Such a write burst may map to a matching AXI burst only after all data beats are captured and burst-scoped attributes are constant. *(when: Legal bufferable Normal Write-back fixed write burst of 4, 8 or 16 beats, all data beats captured and burst-scoped AXI address attributes constant)* | 3:s9 (p145) |
| AA-3-09 | MUST | slave | scenario | Otherwise the bridge must issue ordered AXI single-beat writes. *(when: Burst aggregation conditions are not met)* | 3:s9 (p145) |
| AA-3-10 | MUST | slave | both | Non-bufferable writes must use single-beat AXI transactions. *(when: Non-bufferable writes)* | 3:s9 (p145) |
| AA-3-11 | MUST | slave | both | AXI WDATA/WSTRB must preserve each AHB HWDATA/HWSTRB beat. | 3:s10 (p146) |
| AA-3-12 | MUST | slave | assertion | WLAST must identify the final beat of each AXI write transaction. | 3:s10 (p146) |
| AA-3-13 | MUST | slave | both | AHB responses must remain in transfer order. | 3:s11 (p147) |
| AA-3-14 | MUST | slave | scenario | All B statuses must be combined and any error reported on the terminal AHB beat. *(when: Aggregated or multi-single Normal Write-back bufferable burst)* | 3:s11 (p147) |
| AA-3-15 | MAY | slave | scenario | Earlier beats may receive OKAY once safely buffered. *(when: Earlier beats of such a burst once safely buffered)* | 3:s11 (p147) |
| AA-3-16 | MUST_NOT | slave | scenario | Device memory transfers must not be merged or have their size changed. *(when: Device memory transfers)* | 3:s12 (p148) |
| AA-3-17 | MUST | slave | scenario | Device-E writes must use ordered AXI single-beat transactions and wait for each final-destination BRESP before the AHB response. *(when: Device-E writes)* | 3:s12 (p148) |
| AA-3-18 | MUST_NOT | slave | scenario | No early AHB write response is allowed without a visibility guarantee. *(when: Without a visibility guarantee)* | 3:s12 (p148) |
| AA-3-19 | MUST_NOT | slave | both | An early-terminated fixed write burst must never produce an incomplete AXI burst. *(when: AHB fixed write burst terminated early)* | 3:s13 (p149) |
| AA-3-20 | MUST | slave | scenario | Captured but unissued accepted write beats must be emitted as ordered AXI single-beat transactions without reissuing beats already sent. *(when: Early-terminated fixed write burst)* | 3:s13 (p149) |
| AA-3-21 | MUST | slave | scenario | The terminal AHB response must be held until all corresponding B responses arrive, and any non-OKAY status reported on it. *(when: Early-terminated fixed write burst)* | 3:s13 (p149) |
| AA-3-22 | MUST_NOT | slave | assertion | No AXI burst may cross a 4 KiB boundary. | 3:s14 (p150) |
| AA-3-23 | MUST | slave | scenario | The bridge must preserve beat order and aggregate all sub-burst responses onto the final AHB beat. *(when: Defensive splitting is needed)* | 3:s14 (p150) |
| AA-3-24 | MUST | system | scenario | The single top module m_ahb2axi_top must expose exactly the fixed clock, reset, AHB and AXI ports listed in §6.2. | 3:s15 (p151) |
| AA-3-25 | MUST_NOT | system | scenario | AHB/AXI USER sideband and zero-width optional ports must not be present. | 3:s15 (p151) |
| AA-3-26 | MUST | system | scenario | AHB and AXI interfaces must use the same rising-edge clock input i_clk_core. | 3:s16 (p152) |
| AA-3-27 | MUST_NOT | system | scenario | No second clock port or clock-domain crossing is permitted. | 3:s16 (p152) |
| AA-3-28 | MUST | system | scenario | The bridge must expose one active-low reset input i_rst_n_core and use it directly without an internal reset synchronizer. | 3:s17 (p153) |
| AA-3-29 | MUST | system | none | The SoC reset source must synchronize deassertion to i_clk_core before the reset reaches the IP. | 3:s17 (p153) |
| AA-3-30 | MUST | slave | scenario | Reset must clear all bridge/FIFO valid state. *(when: On reset)* | 3:s17 (p153) |
| AA-3-31 | MUST_NOT | slave | both | No pre-reset response may be returned after reset release. *(when: After reset release)* | 3:s17 (p153) |
| AA-3-32 | MUST | slave | both | AXI OKAY must map to AHB OKAY. *(when: AXI response is OKAY)* | 3:s18 (p154) |
| AA-3-33 | MUST | slave | both | These must map to the AHB two-cycle ERROR response. *(when: AXI response is SLVERR, DECERR or unexpected EXOKAY)* | 3:s18 (p154) |
| AA-3-34 | MUST | slave | both | Such transfers must return two-cycle AHB ERROR. *(when: HMASTLOCK, HPROT[6]=1, reserved/unsupported HPROT, unsupported HSIZE or misaligned transfer)* | 3:s19 (p155) |
| AA-3-35 | MUST_NOT | slave | assertion | No AXI request must be issued for the rejected transfer. *(when: Transfer rejected with AHB ERROR)* | 3:s19 (p155) |
| AA-3-36 | MUST | system | scenario | Read and write ID-count parameters must be in the range 1..8. | 3:s20 (p156) |
| AA-3-37 | MUST | slave | both | Each direction must rotate IDs through 0..count-1. *(when: After each completed AXI transaction)* | 3:s20 (p156) |
| AA-3-38 | MUST_NOT | slave | scenario | ID rotation must not imply multiple outstanding requests. | 3:s20 (p156) |
| AA-3-39 | MAY | slave | scenario | The bridge may accept one AHB beat per i_clk_core cycle. *(when: Eligible Normal Write-back fixed write bursts while buffer capacity is available)* | 3:s21 (p157) |
| AA-3-40 | MUST | slave | scenario | Terminal completion must wait for all required BRESPs. *(when: Eligible bufferable fixed write bursts)* | 3:s21 (p157) |
| AA-3-41 | MUST | slave | both | AR/AW handshake must occur within 6 i_clk_core cycles of accepted AHB address. *(when: Single read or single-beat write, synchronous queue has space and AXI READY remains high)* | 3:s22 (p158) |
| AA-3-42 | MUST | slave | scenario | The AW timing target starts after the full burst or its early termination has been captured. *(when: Fixed-length writes)* | 3:s22 (p158) |
| AA-3-43 | MUST_NOT | slave | none | The bridge must not guarantee a bound for full completion, AXI response latency, or traffic under external stalls. | 3:s23 (p159) |
| AA-3-44 | MUST | system | none | RTL must follow REF-003; the single top module contains only structural instances and each module is in a same-named file. | 3:s24 (p160) |
| AA-3-45 | MUST_NOT | system | scenario | The IP must have no software-visible CSR interface; all configuration is static at elaboration. | 3:s25 (p161) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-4-01 | MUST_NOT | system | none | m_ahb2axi_top must not define USER-width parameters or an optional USER port profile; no USER sidebands exist. | 4:s4, 4:s6 (p170) |
| AA-4-02 | MUST | system | scenario | A parameter value outside its legal range must be treated as an elaboration error. *(when: When a parameter is set outside its legal range)* | 4:s5, 4:s7 (p170) |

## 5.1 Overview and block responsibilities

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-5.1-01 | MUST | system | scenario | All sequential logic and FIFO clock/reset pins use the shared i_clk_core and i_rst_n_core. | 5.1:s5 (p176) |
| AA-5.1-02 | MUST | system | both | The combinational AXI adapter uses i_rst_n_core only to suppress AXI VALID/READY during reset. *(when: During reset)* | 5.1:s5, 5.1:s10 (p176) |
| AA-5.1-03 | MUST_NOT | system | none | The top port list contains no AHB or AXI USER sideband signals. | 5.1:s7 (p176) |
| AA-5.1-04 | MUST | system | none | The five FIFO instances have depths 2, 16, 2, 2 and 2 entries respectively, with software-reset inactive and both clock/reset pins tied to shared inputs. | 5.1:s14, 5.1:s15 (p186) |
| AA-5.1-05 | MUST_NOT | system | none | The design contains no clock-domain crossing or CDC synchronizer. | 5.1:s16, 5.4:s10 (p186) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-5.3-01 | MUST | master | both | The bridge issues ARLEN=0 and ARBURST=INCR, accepts one R beat with RLAST=1, and returns HRDATA and HRESP in the AHB data phase. *(when: For an AHB read)* | 5.3:s1, 5.4:s8 (p198) |
| AA-5.3-02 | MUST_NOT | slave | both | The bridge must not accept the next AHB read while the current read is unresolved. *(when: While the current AHB read is unresolved)* | 5.3:s2 (p198) |
| AA-5.3-03 | MUST | master | scenario | Issue one AXI write with AWLEN=0, one W beat with WLAST=1, wait for the B response, then return AHB completion/error. *(when: Write single, undefined INCR, or non-bufferable fixed burst beat)* | 5.3:s3 (p200) |
| AA-5.3-04 | MUST | master | scenario | Fixed non-bufferable bursts are serialized beat by beat. *(when: Fixed non-bufferable bursts)* | 5.3:s4 (p200) |
| AA-5.3-05 | MUST | master | scenario | Collect all 4/8/16 AHB address/data beats in order. *(when: Eligible Normal Write-back fixed write burst)* | 5.3:s5 (p202) |
| AA-5.3-06 | MUST | master | scenario | If all AXI address attributes are constant, emit one matching INCR/WRAP AXI burst; otherwise emit ordered AXI single-beat writes. *(when: Eligible fixed write burst collected)* | 5.3:s6 (p202) |
| AA-5.3-07 | MUST | master | scenario | Keep Device-E and non-bufferable writes as single AXI writes. *(when: Device-E or non-bufferable writes)* | 5.3:s7 (p202) |
| AA-5.3-08 | MAY | slave | scenario | Earlier safely buffered Normal Write-back beats may complete OKAY. *(when: Earlier safely buffered Normal Write-back beats)* | 5.3:s8 (p202) |
| AA-5.3-09 | MUST | slave | scenario | The terminal AHB beat waits for the required B response(s). *(when: Terminal AHB beat of buffered write burst)* | 5.3:s8 (p202) |
| AA-5.3-10 | MUST | master | both | Assert WLAST only on the last W beat, wait for BRESP, and apply the response to the final AHB beat. *(when: Bufferable fixed write burst)* | 5.3:s13 (p208) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-5.4-01 | MUST | system | assertion | AHB and AXI interface signals are sampled or driven relative to the rising edge of i_clk_core. | 5.4:s1 (p212) |
| AA-5.4-02 | MUST_NOT | master | assertion | No AXI read address is issued before the corresponding AHB read address is accepted. | 5.4:s3 (p214) |
| AA-5.4-03 | MUST | system | scenario | AHB and AXI transaction order is preserved, with no read speculation or response reordering. | 5.4:s4 (p215) |
| AA-5.4-04 | MUST | master | assertion | AXI VALID and payload remain stable until the READY handshake. *(when: AXI VALID asserted and READY not yet high)* | 5.4:s5 (p216) |
| AA-5.4-05 | MUST_NOT | master | scenario | An AXI burst is issued only when the complete AHB fixed write burst has been captured. *(when: AHB fixed write burst not completely captured)* | 5.4:s6 (p217) |
| AA-5.4-06 | MUST | system | both | At most one read and one write transaction are outstanding; a later AHB transaction must not pass a stalled response. | 5.4:s7 (p218) |
| AA-5.4-07 | MUST | master | assertion | WLAST is high exactly on the final AXI W beat; read ARLEN is always zero and expected RLAST is one. | 5.4:s8 (p219) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-6.1-01 | MUST | system | scenario | The bridge must provide IF-001, a required AHB5 (IHI 0033 Version C) Subordinate interface, clocked by i_clk_core and reset by i_rst_n_core, in configuration CFG-BASE. | 6.1:s1 (p238) |
| AA-6.1-02 | MUST | system | scenario | The bridge must provide IF-002, a required AXI4 (IHI 0022 Issue H.c) Manager interface, clocked by i_clk_core and reset by i_rst_n_core, in configuration CFG-BASE. | 6.1:s2 (p239) |
| AA-6.1-03 | MUST | system | scenario | The bridge must provide IF-003, a single required active-low shared reset from the reset controller, with asynchronous assert and SoC-synchronized release before the IP boundary. | 6.1:s3 (p240) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-6.2-01 | MUST | system | both | AHB and AXI interface signals must use the rising edge of i_clk_core, and i_rst_n_core must be the only reset input. | 6.2:s2, 6.2:s3 (p244) |

## T1.7.2.1 Shared clock and reset / Clock và reset dùng chung

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.2.1-01 | MUST | system | scenario | AHB HCLK and AXI ACLK must both map to the single clock i_clk_core. | T1.7.2.1:s1 (p247) |
| AA-T1.7.2.1-02 | MUST_NOT | system | scenario | The bridge must not expose separate protocol clock pins for AHB or AXI; only i_clk_core is the clock. | T1.7.2.1:s1 (p247) |

## T1.7.2.2 Consolidated port list / Danh sách cổng tổng hợp

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.2.2-01 | MUST_NOT | system | none | The IP must not implement any AHB or AXI USER sideband ports. | T1.7.2.2:s1 (p251) |
| AA-T1.7.2.2-02 | MUST | system | none | i_rst_n_core asserts asynchronously and is deasserted synchronously by the SoC before the IP boundary; it is 1 after release. | T1.7.2.2:s3 (p256) |
| AA-T1.7.2.2-03 | MUST | master | assertion | i_ahb_hsel is 0, i_ahb_htrans is IDLE, i_ahb_hwrite is 0, i_ahb_hburst is SINGLE and i_ahb_hmastlock is 0 at reset/idle. *(when: During reset/idle)* | T1.7.2.2:s4, T1.7.2.2:s7, T1.7.2.2:s8, T1.7.2.2:s10, T1.7.2.2:s13 (p257) |
| AA-T1.7.2.2-04 | MUST | slave | scenario | The bridge ignores i_ahb_hready, i_axi_awready, i_axi_wready and i_axi_arready during bridge reset; they are externally unconstrained. *(when: During bridge reset)* | T1.7.2.2:s5, T1.7.2.2:s28, T1.7.2.2:s33, T1.7.2.2:s47 (p258) |
| AA-T1.7.2.2-05 | MUST | slave | assertion | o_ahb_hreadyout is 1 during reset. *(when: During reset)* | T1.7.2.2:s16 (p269) |
| AA-T1.7.2.2-06 | MUST | slave | assertion | o_ahb_hresp is 0 (OKAY) at reset. *(when: During reset)* | T1.7.2.2:s17 (p270) |
| AA-T1.7.2.2-07 | MUST | slave | assertion | An o_ahb_hresp ERROR follows the AHB two-cycle error response. *(when: When an ERROR response is given)* | T1.7.2.2:s17 (p270) |
| AA-T1.7.2.2-08 | MUST | slave | assertion | o_ahb_hrdata is 0 at reset. *(when: During reset)* | T1.7.2.2:s18 (p271) |
| AA-T1.7.2.2-09 | MUST | master | assertion | o_axi_awid, o_axi_awaddr, o_axi_awlen, o_axi_awsize, o_axi_awcache and o_axi_awprot are 0 at reset. *(when: During reset)* | T1.7.2.2:s19, T1.7.2.2:s20, T1.7.2.2:s21, T1.7.2.2:s22, T1.7.2.2:s25, T1.7.2.2:s26 (p272) |
| AA-T1.7.2.2-10 | MUST | master | assertion | o_axi_awburst is INCR at reset. *(when: During reset)* | T1.7.2.2:s23 (p276) |
| AA-T1.7.2.2-11 | MUST | master | assertion | o_axi_awlock and o_axi_arlock are constant 0 (tied low). | T1.7.2.2:s24, T1.7.2.2:s43 (p277) |
| AA-T1.7.2.2-12 | MUST | master | assertion | o_axi_awvalid is held high until i_axi_awready. *(when: While o_axi_awvalid is high and i_axi_awready is low)* | T1.7.2.2:s27 (p280) |
| AA-T1.7.2.2-13 | MUST | master | assertion | o_axi_awvalid, o_axi_wvalid, o_axi_bready, o_axi_arvalid and o_axi_rready are 0 at reset. *(when: During reset)* | T1.7.2.2:s27, T1.7.2.2:s32, T1.7.2.2:s37, T1.7.2.2:s46, T1.7.2.2:s53 (p280) |
| AA-T1.7.2.2-14 | MUST | master | assertion | o_axi_wdata, o_axi_wstrb and o_axi_wvalid are held until i_axi_wready. *(when: While o_axi_wvalid is high and i_axi_wready is low)* | T1.7.2.2:s29, T1.7.2.2:s30, T1.7.2.2:s32 (p282) |
| AA-T1.7.2.2-15 | MUST | master | assertion | o_axi_wdata, o_axi_wstrb and o_axi_wlast are 0 at reset. *(when: During reset)* | T1.7.2.2:s29, T1.7.2.2:s30, T1.7.2.2:s31 (p282) |
| AA-T1.7.2.2-16 | MUST | master | assertion | o_axi_wlast is high only on the final beat of a write burst. | T1.7.2.2:s31 (p284) |
| AA-T1.7.2.2-17 | MUST | slave | assertion | i_axi_bvalid is 0 during reset. *(when: During reset)* | T1.7.2.2:s36 (p289) |
| AA-T1.7.2.2-18 | MUST | slave | assertion | i_axi_bvalid is held until o_axi_bready. *(when: While i_axi_bvalid is high and o_axi_bready is low)* | T1.7.2.2:s36 (p289) |
| AA-T1.7.2.2-19 | MUST | master | assertion | o_axi_arid, o_axi_araddr, o_axi_arsize, o_axi_arcache and o_axi_arprot are 0 at reset. *(when: During reset)* | T1.7.2.2:s38, T1.7.2.2:s39, T1.7.2.2:s41, T1.7.2.2:s44, T1.7.2.2:s45 (p291) |
| AA-T1.7.2.2-20 | MUST | master | assertion | o_axi_arlen is always zero, so every read is a single beat. | T1.7.2.2:s40 (p293) |
| AA-T1.7.2.2-21 | MUST | master | assertion | o_axi_arburst is INCR, including at reset. | T1.7.2.2:s42 (p295) |
| AA-T1.7.2.2-22 | MUST | master | assertion | o_axi_arvalid is held high until i_axi_arready. *(when: While o_axi_arvalid is high and i_axi_arready is low)* | T1.7.2.2:s46 (p299) |
| AA-T1.7.2.2-23 | MUST | slave | assertion | i_axi_rlast is expected high for each single-beat read. *(when: For each single-beat read response)* | T1.7.2.2:s51 (p304) |
| AA-T1.7.2.2-24 | MUST | slave | assertion | i_axi_rvalid is 0 during reset. *(when: During reset)* | T1.7.2.2:s52 (p305) |
| AA-T1.7.2.2-25 | MUST | slave | assertion | i_axi_rvalid is held until o_axi_rready. *(when: While i_axi_rvalid is high and o_axi_rready is low)* | T1.7.2.2:s52 (p305) |

## T1.7.3.1 AHB5 acceptance and supported profile / Nhận giao dịch AHB5 và profile hỗ trợ

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.3.1-01 | MUST | slave | both | The bridge accepts a transfer at a rising i_clk_core edge when HSEL, HREADY and HTRANS[1] are all 1. *(when: at a rising i_clk_core edge when HSEL, HREADY and HTRANS[1] are all 1)* | T1.7.3.1:s1 (p312) |
| AA-T1.7.3.1-02 | MUST | slave | both | Address/control are taken from the address phase; HWDATA/HWSTRB belong to the corresponding data phase. | T1.7.3.1:s2 (p312) |
| AA-T1.7.3.1-03 | MUST_NOT | slave | both | BUSY and IDLE transfers must not create AXI traffic. *(when: HTRANS is BUSY or IDLE)* | T1.7.3.1:s3, T1.7.3.1:s4 (p312) |
| AA-T1.7.3.1-04 | MUST | master | assertion | Supported HSIZE encodings are byte, halfword and word (0,1,2), and transfer addresses shall be naturally aligned to HSIZE. | T1.7.3.1:s5, T1.7.3.1:s6 (p313) |
| AA-T1.7.3.1-05 | MUST | slave | both | The bridge returns AHB ERROR with no AXI request for the rejected transfer; any earlier accepted write prefix is drained. *(when: HSIZE>2, misaligned access, reserved HBURST, or unsupported/reserved HPROT memory type)* | T1.7.3.1:s7, T1.7.3.1:s8 (p313) |
| AA-T1.7.3.1-06 | MUST | slave | both | AHB SINGLE and undefined INCR are converted to AXI single-beat INCR transactions. *(when: AHB SINGLE or undefined-length INCR)* | T1.7.3.1:s9 (p314) |
| AA-T1.7.3.1-07 | MUST | slave | both | Each read beat of fixed INCR/WRAP bursts issues its own single-beat AR request. *(when: fixed INCR4/8/16 or WRAP4/8/16 read)* | T1.7.3.1:s10, T1.7.3.1:s11 (p314) |
| AA-T1.7.3.1-08 | MUST | slave | both | AXI write burst aggregation is limited to complete legal Normal Write-back fixed write bursts with constant AXI address attributes. | T1.7.3.1:s12 (p315) |
| AA-T1.7.3.1-09 | MUST_NOT | slave | both | Device writes must never be merged into an AXI burst. *(when: Device writes)* | T1.7.3.1:s13, T1.7.3.1:s15 (p315) |
| AA-T1.7.3.1-10 | MUST | slave | scenario | Captured but unissued write beats are drained as ordered AXI singles without reissuing sent beats; no short AXI burst replaces the AHB burst. *(when: fixed AHB burst terminates early)* | T1.7.3.1:s14, T1.7.3.1:s16, T1.7.3.1:s24, T1.7.3.1:s26 (p315) |
| AA-T1.7.3.1-11 | MUST_NOT | master | assertion | AHB managers must not start an incrementing burst that crosses a 1 KiB boundary. *(when: incrementing burst)* | T1.7.3.1:s17 (p316) |
| AA-T1.7.3.1-12 | MUST | slave | both | The bridge keeps every AXI burst within a 4 KiB boundary, splitting defensively for out-of-profile address sequences. | T1.7.3.1:s18, T1.7.3.1:s19 (p316) |
| AA-T1.7.3.1-13 | MUST | master | assertion | HPROT remains constant throughout an AHB burst. *(when: during an AHB burst)* | T1.7.3.1:s22 (p317) |
| AA-T1.7.3.1-14 | MUST | slave | scenario | The bridge uses ordered AXI singles instead of a burst. *(when: burst-scoped AXI address attribute differs between accepted beats)* | T1.7.3.1:s23, T1.7.3.1:s25 (p317) |
| AA-T1.7.3.1-15 | MUST_NOT | slave | both | The bridge issues no exclusive requests; HMASTLOCK=1 is rejected with AHB ERROR. | T1.7.3.1:s27, T1.7.3.1:s28 (p318) |

## T1.7.3.2 AXI4 channel contract / Hợp đồng các kênh AXI4

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.3.2-01 | MUST | master | assertion | AXI4 VALID and payload remain stable until READY handshakes; AXI outputs have no combinational dependency on READY. *(when: VALID asserted and READY not yet handshaken)* | T1.7.3.2:s1, T1.7.3.2:s2 (p322) |
| AA-T1.7.3.2-02 | MUST | slave | assertion | At most one read and one write transaction may be outstanding. | T1.7.3.2:s4 (p323) |
| AA-T1.7.3.2-03 | MUST | slave | assertion | Reads are single-beat: ARLEN=0, ARBURST=INCR, RLAST=1. | T1.7.3.2:s5, T1.7.3.2:s7 (p323) |
| AA-T1.7.3.2-04 | MUST | slave | assertion | Writes are single-beat or fixed bursts up to 16 beats. | T1.7.3.2:s6, T1.7.3.2:s8 (p323) |
| AA-T1.7.3.2-05 | MUST | slave | both | AXI ID is 3 bits; each direction rotates through IDs 0..count-1 after each completed transaction. *(when: after each completed AXI transaction)* | T1.7.3.2:s9, T1.7.3.2:s10, T1.7.3.2:s12 (p324) |
| AA-T1.7.3.2-06 | MUST_NOT | slave | assertion | ID count greater than 1 does not enable concurrent transactions. *(when: ID count >1)* | T1.7.3.2:s11, T1.7.3.2:s13 (p324) |
| AA-T1.7.3.2-07 | MUST | slave | scenario | The related AHB operation remains pending indefinitely. *(when: R or B response not returned)* | T1.7.3.2:s15, T1.7.3.2:s16 (p325) |

## T1.7.3.3 HPROT mapping / Ánh xạ HPROT

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.3.3-01 | MUST | slave | both | The transfer is rejected with AHB ERROR before any AXI request is issued. *(when: HPROT[6]=1 or unlisted HPROT[6:2] pattern)* | T1.7.3.3:s4, T1.7.3.3:s5, T1.7.3.3:s14, T1.7.3.3:s16, T1.7.3.3:s17 (p329) |
| AA-T1.7.3.3-02 | MUST | slave | assertion | AxPROT[0]=HPROT[1], AxPROT[1]=HNONSEC, AxPROT[2]=~HPROT[0]. | T1.7.3.3:s6, T1.7.3.3:s7, T1.7.3.3:s8 (p333) |
| AA-T1.7.3.3-03 | MUST | slave | assertion | AxCACHE[1]=HPROT[3], AxCACHE[0]=HPROT[2]; HPROT[4]=0 gives AxCACHE[3:2]=00; HPROT[4]=1 sets direction-specific allocate bits per HPROT[5]. | T1.7.3.3:s9, T1.7.3.3:s10, T1.7.3.3:s11, T1.7.3.3:s12, T1.7.3.3:s13 (p336) |
| AA-T1.7.3.3-04 | MUST | slave | scenario | Issue one AXI single per beat, never merge, and wait for final-destination BRESP. *(when: Device-nE or Device-E write)* | T1.7.3.3:s18, T1.7.3.3:s19, T1.7.3.4:s4 (p347) |
| AA-T1.7.3.3-05 | MUST | slave | both | Writes are single-beat with no burst aggregation. *(when: Normal Non-cacheable or Write-through writes)* | T1.7.3.3:s20, T1.7.3.3:s21 (p349) |
| AA-T1.7.3.3-06 | MAY | slave | scenario | The bridge may aggregate such bursts into an AXI burst. *(when: Write-back eligible bufferable fixed burst with constant AXI address attributes)* | T1.7.3.3:s22 (p351) |

## T1.7.3.4 Protocol cases / Các trường hợp giao thức

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-T1.7.3.4-01 | MUST | slave | both | One accepted address returns one AXI R beat; no speculative or multi-beat read; AHB waits for R and maps RRESP. *(when: AHB read)* | T1.7.3.4:s1 (p357) |
| AA-T1.7.3.4-02 | MUST | slave | both | One AHB beat maps to one AXI single with no undefined-length aggregation; wait for BRESP. *(when: AHB single/INCR write)* | T1.7.3.4:s2 (p358) |
| AA-T1.7.3.4-03 | MUST | slave | scenario | A full 4/8/16-beat burst uses one AXI burst only with uniform attributes; prior beats get early OKAY and terminal HRESP reflects final B status. *(when: eligible Normal Write-back fixed write)* | T1.7.3.4:s3 (p359) |
| AA-T1.7.3.4-04 | MUST | slave | both | No AXI request for the rejected transfer; two-cycle AHB ERROR; drain any previously accepted write prefix. *(when: HMASTLOCK or shareable HPROT)* | T1.7.3.4:s5 (p361) |
| AA-T1.7.3.4-05 | MUST | slave | both | Non-OKAY maps to AHB ERROR. *(when: AXI R/B status non-OKAY)* | T1.7.3.4:s6 (p362) |

## 6.4 Interrupts and events

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-6.4-01 | MUST_NOT | system | none | The bridge IP includes no interrupt or event output port. | 6.4:s1 (p366) |
| AA-6.4-02 | MUST | slave | scenario | Supported errors are returned to the AHB master on the AHB response channel (HRESP) rather than via an interrupt or event output. *(when: When a supported error occurs)* | 6.4:s1 (p366) |

## 7.1 Shared clock

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-7.1-01 | MUST | system | scenario | AHB HCLK and AXI ACLK, and all FIFO instances, must use the same physical i_clk_core input, rising-edge, with no internal clock gating. | 7.1:s1, 7.1:s3 (p374) |

## 7.2 Clock-domain crossing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-7.2-01 | MUST_NOT | system | none | The bridge must operate in the single CLK-CORE domain and must not contain asynchronous crossings, synchronizer chains, Gray pointers or CDC FIFOs. | 7.2:s1, 7.2:s2 (p380) |
| AA-7.2-02 | MUST | system | none | Each m_vlsit_sfifo_top write/read clock input must be tied to i_clk_core and its two reset inputs tied to i_rst_n_core. | 7.2:s3 (p380) |

## 7.3 Shared reset and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-7.3-01 | MUST | system | assertion | Reset values must be HREADYOUT=1, HRESP=OKAY, AWVALID/WVALID/ARVALID=0, BREADY/RREADY=0, and FIFO valid state cleared, for all bridge logic and five FIFOs. *(when: While i_rst_n_core is asserted (low))* | 7.3:s1 (p386) |
| AA-7.3-02 | MUST | system | none | The SoC must provide one active-low reset net i_rst_n_core to both protocol sides and all FIFOs, asserted asynchronously and with deassertion synchronized to i_clk_core before the IP. | 7.3:s1, 7.3:s2, 7.3:s3 (p386) |
| AA-7.3-03 | MUST_NOT | system | none | The RTL must use i_rst_n_core directly and must not contain a reset synchronizer. | 7.3:s4 (p388) |
| AA-7.3-04 | MUST_NOT | slave | assertion | No transaction may be accepted by the bridge until reset is released. *(when: Before reset release)* | 7.3:s5 (p388) |
| AA-7.3-05 | MUST | system | none | The system must reset the connected AXI endpoint/interconnect consistently so a stale response cannot be mistaken for a new transaction. *(when: When reset discards bridge-buffered commands/data and in-flight responses)* | 7.3:s6 (p388) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-8-01 | MUST | system | scenario | PARA_RD_ID_COUNT, the number of read IDs in rotation, must default to 1 and be within the legal range 1..8. | 8:s1 (p398) |
| AA-8-02 | MUST | system | scenario | The read ID width must remain 3 regardless of PARA_RD_ID_COUNT, and the count must not increase outstanding capacity. *(when: Any PARA_RD_ID_COUNT value)* | 8:s1 (p398) |
| AA-8-03 | MUST | system | scenario | PARA_WR_ID_COUNT, the number of write IDs in rotation, must default to 1 and be within the legal range 1..8. | 8:s2 (p399) |
| AA-8-04 | MUST | system | scenario | The write ID width must remain 3 regardless of PARA_WR_ID_COUNT, and the count must not increase outstanding capacity. *(when: Any PARA_WR_ID_COUNT value)* | 8:s2 (p399) |
| AA-8-05 | MUST_NOT | system | none | No USER sideband or USER-width parameters are defined. | 8:s3 (p401) |
| AA-8-06 | MUST_NOT | system | none | AXI address, data and ID widths, FIFO depths and protocol features must not be user-overridable in this revision. | 8:s4 (p401) |
| AA-8-07 | MUST | system | none | Immediately above each RTL parameter, comments // Parameter Description, // Parameter values and // Parameter unit must appear in that order. *(when: For each RTL parameter)* | 8:s8 (p405) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-9-01 | MUST | system | assertion | The AXI address must equal the corresponding accepted AHB address (32-bit byte address). *(when: When an AHB transfer is accepted and forwarded to AXI)* | 9:s1 (p411) |
| AA-9-02 | MUST | system | assertion | HWDATA, WDATA, HRDATA and RDATA must each be 32 bits wide. | 9:s2 (p412) |
| AA-9-03 | MUST_NOT | system | assertion | The bridge must not byte-swap data between AHB and AXI. | 9:s2 (p412) |
| AA-9-04 | MUST | system | assertion | HSIZE/AxSIZE must encode 0 as 1 byte, 1 as 2 bytes and 2 as 4 bytes. | 9:s3 (p413) |
| AA-9-05 | MUST | system | scenario | The bridge must reject transfers with sizes larger than 4 bytes. *(when: When HSIZE indicates a size larger than 4 bytes)* | 9:s3 (p413) |
| AA-9-06 | MUST | system | assertion | HWSTRB[n] and WSTRB[n] must qualify byte [8n+7:8n] of HWDATA/WDATA respectively. | 9:s4 (p414) |
| AA-9-07 | MUST | system | assertion | The strobe must be passed from HWSTRB to WSTRB per beat. *(when: For each write beat)* | 9:s4 (p414) |
| AA-9-08 | MUST_NOT | system | assertion | The bridge must not perform any endian conversion. | 9:s5 (p415) |
| AA-9-09 | MUST | system | assertion | AXI LEN must equal the beat count minus one. | 9:s6 (p416) |
| AA-9-10 | MUST | system | assertion | LEN must be 0 for a single-beat transfer. *(when: Single-beat transfer)* | 9:s6 (p416) |
| AA-9-11 | MUST | system | assertion | AWLEN must be 3, 7 or 15 for an aggregated write burst before boundary split. *(when: Aggregated write burst, before boundary split)* | 9:s6 (p416) |
| AA-9-12 | MUST | system | assertion | ID must be an unsigned 3-bit value. | 9:s7 (p417) |
| AA-9-13 | MUST | system | scenario | Each direction (read and write) must rotate its ID independently through the configured count. | 9:s7 (p417) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-10.1-01 | MAY | system | scenario | An eligible fixed Normal Write-back write may remain in capture until all expected beats are received. *(when: Eligible fixed Normal Write-back write)* | 10.1:s3 (p425) |
| AA-10.1-02 | MUST | system | scenario | A terminated fixed write burst must drain its captured prefix as AXI singles. *(when: Fixed write burst terminated early)* | 10.1:s3, 10.2:s4 (p425) |
| AA-10.1-03 | MUST | system | both | The bridge must return a two-cycle AHB ERROR response and issue no AXI request for the rejected transfer. *(when: Illegal or unsupported AHB controls (lock/attribute/size/alignment/encoding))* | 10.1:s4, 10.2:s5 (p425) |

## 10.2 Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-10.2-01 | MUST | system | both | The bridge must issue one AR with ARLEN=0, receive one R beat, and complete AHB with HRDATA and HRESP derived from RRESP. *(when: Accepted read, any HBURST)* | 10.2:s1 (p433) |
| AA-10.2-02 | MUST | system | both | The bridge must issue one AW with AWLEN=0 and one W beat with WLAST=1, wait for BRESP, and map the response to that AHB transfer. *(when: SINGLE, undefined INCR beat, Device-E beat, or non-bufferable fixed-burst beat)* | 10.2:s2 (p434) |
| AA-10.2-03 | MUST | system | scenario | The bridge must issue one AW/W burst of up to 16 beats, splitting at 4 KiB if needed; the terminal AHB beat waits for all corresponding BRESPs. *(when: Complete eligible bufferable Normal Write-back INCR4/8/16 or WRAP4/8/16 burst with uniform address attributes)* | 10.2:s3 (p435) |
| AA-10.2-04 | MAY | system | scenario | Earlier accepted beats of an AXI write burst may return OKAY before the BRESPs arrive. *(when: OP-WR-BURST earlier accepted beats)* | 10.2:s3 (p435) |
| AA-10.2-05 | MUST | system | scenario | The bridge must issue ordered AXI singles for remaining captured beats, not reissue completed beats, and aggregate relevant B errors to the terminal AHB beat. *(when: Normal Write-back fixed burst with varying AXI address attributes, or captured unissued prefix of early-terminated fixed write)* | 10.2:s4 (p436) |
| AA-10.2-06 | MUST | system | both | On assertion of i_rst_n_core the bridge must drop in-flight queues and VALID state and drive HREADYOUT=1 during reset. *(when: i_rst_n_core asserted)* | 10.2:s6 (p438) |
| AA-10.2-07 | MUST_NOT | system | scenario | No stale response may appear after reset once the AXI endpoint/interconnect is reset consistently. *(when: After AXI endpoint/interconnect is reset consistently)* | 10.2:s6 (p438) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-10.3-01 | MUST | system | none | AHB and AXI sides must share the single rising-edge clock i_clk_core and single reset i_rst_n_core. | 10.3:s3, 10.4:s1 (p442) |

## 10.4 Arbitration, buffering, and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-10.4-01 | MUST_NOT | system | both | The bridge must serialize reads and must not accept the next AHB read until the current R data/status returns. *(when: Current read's R data/status not yet returned)* | 10.4:s2, 10.4:s3 (p458) |
| AA-10.4-02 | MAY | system | scenario | The bridge can accept one AHB beat per i_clk_core cycle. *(when: Eligible Normal Write-back fixed writes while the 16-entry buffer has room)* | 10.4:s5 (p459) |
| AA-10.4-03 | MUST | system | both | The bridge must wait for each single-beat BRESP and must not acknowledge Device-E before the final destination responds. *(when: Device-E and non-bufferable writes)* | 10.4:s6 (p459) |
| AA-10.4-04 | SHOULD | system | assertion | The AR/AW handshake should complete within 6 i_clk_core cycles of the accepted AHB address. *(when: Single read or single-beat write, synchronous queue has space and AXI READY stays high)* | 10.4:s8 (p460) |
| AA-10.4-05 | MUST | system | scenario | The AW latency bound starts after the complete AHB burst or its early termination is captured, not from the first AHB address; no AXI burst is issued before capture. *(when: Fixed-length write burst)* | 10.4:s9, 10.4:s11, 10.4:s12 (p460) |
| AA-10.4-06 | MAY | system | none | Absolute latency and MB/s throughput remain TBD until the shared clock frequency is supplied. | 10.4:s16 (p462) |
| AA-10.4-07 | MUST | system | scenario | Read/write arbitration must follow AHB acceptance order, and no later transaction may bypass an unresolved AHB operation. | 10.4:s19, 10.4:s20 (p463) |

## 10.5 Memories and storage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-10.5-01 | MUST | system | none | Write-data storage must hold at least one complete 16-beat burst. | 10.5:s2 (p467) |
| AA-10.5-02 | MUST | system | none | Command and response stores must hold one active transaction. | 10.5:s3 (p467) |
| AA-10.5-03 | MUST | system | scenario | FIFO pointer and validity state must be cleared by the shared reset; payload contents need not be reset. | 10.5:s4 (p467) |
| AA-10.5-04 | MUST | system | none | Both clock pins and both hardware-reset pins of each FIFO must connect to i_clk_core and i_rst_n_core respectively. | 10.5:s5 (p467) |

## 11.1 CSR specification source

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-11.1-01 | MUST_NOT | system | none | The IP has no software-visible registers and no CSR workbook is required. | 11.1:s1, 11.1:s3, 11.1:s4 (p473) |
| AA-11.1-02 | MUST | system | none | ID rotation is configured through static elaboration parameters chosen by the SoC integrator, not by software sequences. *(when: At build/elaboration time)* | 11.1:s2, 11.2:s2 (p473) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-12-01 | MUST | slave | both | The bridge must reject a transfer with HMASTLOCK=1 using a two-cycle ERROR response and issue no AXI request for it. *(when: HMASTLOCK=1 on a transfer)* | 12:s1 (p483) |
| AA-12-02 | MUST | slave | scenario | The bridge must drain any accepted write prefix before giving the terminal ERROR response for a transfer rejected for HMASTLOCK=1. *(when: HMASTLOCK=1 rejection with an accepted write prefix)* | 12:s1 (p483) |
| AA-12-03 | MUST | slave | both | The bridge must reject a transfer with HPROT[6]=1 or unsupported/reserved HPROT using a two-cycle ERROR response, with no AXI request or side effect for the rejected beat. *(when: HPROT[6]=1 or unsupported/reserved HPROT)* | 12:s2 (p484) |
| AA-12-04 | MUST | slave | scenario | The bridge must drain any accepted write prefix when rejecting a beat for HPROT error. *(when: HPROT rejection with an accepted write prefix)* | 12:s2 (p484) |
| AA-12-05 | MUST | slave | both | The bridge must reject a transfer with HSIZE>2, misalignment or reserved HBURST using a two-cycle ERROR response, with no AXI request or side effect for the rejected beat. *(when: HSIZE>2, misalignment, or reserved HBURST)* | 12:s3 (p485) |
| AA-12-06 | MUST | slave | scenario | The bridge must drain any accepted write prefix when rejecting a beat for HSIZE, misalignment or reserved HBURST. *(when: HSIZE/alignment/HBURST rejection with an accepted write prefix)* | 12:s3 (p485) |
| AA-12-07 | MUST | slave | both | The bridge must consume the R beat and return a two-cycle AHB ERROR response for the read, reporting the mapped error. *(when: AXI RRESP is SLVERR, DECERR or EXOKAY)* | 12:s4 (p486) |
| AA-12-08 | MUST | slave | both | The bridge must return a two-cycle ERROR for a single write, or on the terminal AHB beat of a Normal Write-back burst, when BRESP is SLVERR/DECERR/EXOKAY. *(when: AXI BRESP is SLVERR, DECERR or EXOKAY)* | 12:s5 (p487) |
| AA-12-09 | MUST | slave | scenario | Earlier buffered beats must remain acknowledged, and the terminal status must reflect all B responses. *(when: Normal Write-back burst with a B error)* | 12:s5 (p487) |
| AA-12-10 | MUST | master | assertion | The bridge must hold VALID and payload stable until the AXI handshake completes. *(when: AXI READY is low while a request is pending)* | 12:s6 (p488) |
| AA-12-11 | MUST_NOT | slave | scenario | The bridge must not implement an internal timeout; AHB waits indefinitely and recovery is left to a system-level watchdog/reset. *(when: AXI R/B response never arrives)* | 12:s7 (p489) |
| AA-12-12 | MUST | slave | both | Only captured, unissued prefix beats use AXI singles, drained in order; the bridge must not send an incomplete AXI burst. *(when: Fixed write burst terminates early)* | 12:s8 (p490) |
| AA-12-13 | MUST | slave | scenario | The terminal AHB response must wait for all relevant B responses, aggregate errors, and not reissue completed beats. *(when: Fixed write burst terminates early)* | 12:s8 (p490) |
| AA-12-14 | MUST | system | scenario | In-flight state is discarded and the bridge and connected endpoint/interconnect are reset consistently. *(when: Coordinated reset during a transaction)* | 12:s9 (p491) |
| AA-12-15 | MUST | slave | none | An external AXI protocol checker must report the violation; the endpoint is in violation and the bridge does not promise recovery. *(when: AXI response ID/RLAST violates AXI4)* | 12:s10 (p492) |
| AA-12-16 | MUST | slave | assertion | In the first ERROR cycle HREADYOUT must be low and in the second ERROR cycle HREADYOUT must be high. *(when: AHB ERROR response)* | 12:s11 (p494) |
| AA-12-17 | MUST_NOT | slave | assertion | AXI errors must not be returned as AHB split responses. *(when: AXI error)* | 12:s12, 12:s13 (p494) |

## 13 Performance, power, and area

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-13-01 | SHOULD | system | scenario | A single request should be issued within at most 6 i_clk_core cycles; this is a cycle-based design target requiring implementation verification. *(when: Under the §10.4 conditions, for a single request)* | 13:s5 (p504) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-14.1-01 | MUST | system | none | RTL shall be synthesizable SystemVerilog following VLSIT RTL Design Rules v2 using logic declarations, with no package, plain always, always_latch, define/undef, or signed types. | 14.1:s1, 14.1:s4 (p515) |
| AA-14.1-02 | MUST | system | none | RTL shall use always_comb and always_ff with process prefixes p_com_ and p_ff_ respectively, and document each logic section with comments. | 14.1:s1, 14.1:s4 (p515) |
| AA-14.1-03 | MUST | system | none | Active-low reset names shall use prefix i_rst_n_ followed by the clock-domain name. | 14.1:s1, 14.1:s4 (p515) |
| AA-14.1-04 | MUST | system | none | Parameters use uppercase PARA_ names, localparams use uppercase LPARA_ names, and enum type names end in _type_def. | 14.1:s2, 14.1:s5 (p515) |
| AA-14.1-05 | MUST | system | none | Protocol signal names follow section 6. | 14.1:s3, 14.1:s6 (p515) |

## 14.2 RTL hierarchy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-14.2-01 | MUST | system | none | m_ahb2axi_top is the single structural top with fixed AHB/AXI ports and instantiates only u_ahb2axi_ctrl. | 14.2:s1, 14.2:s7, 14.2:s10 (p523) |
| AA-14.2-02 | MUST | system | none | m_ahb2axi_ctrl instantiates one m_ahb2axi_ahb_if (u_ahb2axi_ahb_if) and one m_ahb2axi_axi_if (u_ahb2axi_axi_if) plus its control RTL. | 14.2:s2, 14.2:s3, 14.2:s4, 14.2:s7, 14.2:s10 (p524) |
| AA-14.2-03 | MUST | system | none | m_ahb2axi_ctrl instantiates five m_vlsit_sfifo_top FIFOs named u_vlsit_sfifo_top_0 through _4, with indexes starting at zero. | 14.2:s3, 14.2:s5, 14.2:s7, 14.2:s9, 14.2:s10, 14.2:s12 (p525) |
| AA-14.2-04 | MUST | system | none | Both clock pins of each FIFO instance tie to i_clk_core and both hardware-reset pins tie to i_rst_n_core. | 14.2:s5 (p527) |
| AA-14.2-05 | MUST | system | none | Each module is stored in a file with the same basename as the module. | 14.2:s8, 14.2:s11 (p529) |

## 14.3 Synthesis assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-14.3-01 | MUST | system | none | The synthesis flow shall use sole top m_ahb2axi_top, legal parameter overrides, library, a single i_clk_core constraint, reset treatment and memory mapping. *(when: synthesis)* | 14.3:s2, 14.3:s5 (p533) |
| AA-14.3-02 | MAY | system | none | The five synchronous FIFO storage arrays may map to registers or approved single-clock memory macros. *(when: synthesis)* | 14.3:s3, 14.3:s6 (p533) |
| AA-14.3-03 | MUST | system | none | The FIFO storage implementation must meet the FIFO contract. *(when: synthesis)* | 14.3:s3, 14.3:s6 (p533) |
| AA-14.3-04 | MUST_NOT | system | none | The design must have no latches, inferred tri-states, or technology cells outside dedicated wrappers. | 14.3:s4, 14.3:s7 (p533) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-15.1-01 | MUST | system | none | AHB master and AXI Subordinate BFMs shall be independent of each other. | 15.1:s3, 15.1:s7 (p539) |
| AA-15.1-02 | MUST | system | none | Expected transactions shall be computed from accepted AHB pin activity and stated mappings, not from RTL hierarchy, internal state or generated names. *(when: When computing expected transactions in verification)* | 15.1:s3, 15.1:s7 (p539) |
| AA-15.1-03 | MUST | system | none | All test sources and run commands shall be retained in the verification deliverable. | 15.1:s4, 15.1:s8 (p539) |
| AA-15.1-04 | MUST | system | none | The verification flow owner shall place all run commands in one Makefile. | 15.1:s4, 15.1:s8 (p539) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-15.2-01 | MUST | master | both | AXI VALID and payload shall remain stable during READY stalls; no completion bound is asserted and the bridge has no internal timeout. *(when: During AXI READY stalls and delayed or missing R/B responses (TEST-07))* | 15.2:s7 (p553) |
| AA-15.2-02 | MUST | system | scenario | Protocol checks shall report no violation on legal traffic and shall report injected endpoint violations. *(when: Independent AHB/AXI protocol compliance checks (TEST-10))* | 15.2:s10 (p556) |

## 15.3 Assertions and coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-15.3-01 | MUST | master | assertion | AXI VALID and payload must remain stable while READY=0. *(when: While the corresponding READY is 0)* | 15.3:s1 (p562) |
| AA-15.3-02 | MUST_NOT | master | assertion | No AXI read may be issued before AHB acceptance. *(when: Before AHB acceptance of the read)* | 15.3:s1 (p562) |
| AA-15.3-03 | MUST | master | assertion | ARLEN must be 0 for single-beat reads. *(when: Single-beat read)* | 15.3:s1 (p562) |
| AA-15.3-04 | MUST | master | assertion | WLAST must be asserted at exactly the final W beat. | 15.3:s1 (p562) |
| AA-15.3-05 | MUST_NOT | master | assertion | No AW may be issued before the complete aggregated AHB burst is captured. *(when: Before complete aggregated AHB burst is captured)* | 15.3:s1 (p562) |
| AA-15.3-06 | MUST | slave | assertion | AHB responses must be returned in order. | 15.3:s1 (p562) |
| AA-15.3-07 | MUST | slave | assertion | AHB ERROR response must last two cycles. *(when: AHB ERROR response)* | 15.3:s1 (p562) |
| AA-15.3-08 | MUST | master | assertion | Reset must clear AXI VALID. *(when: Reset asserted)* | 15.3:s1 (p562) |
| AA-15.3-09 | MUST | master | assertion | ID values must remain below the configured ID count. | 15.3:s1 (p562) |
| AA-15.3-10 | MUST | system | none | Functional coverage shall cross direction, size, burst type, HPROT memory type, bufferable/non-bufferable, strobe mask, response status, READY stall length, uniform/varying address attributes, early termination, ID count and reset timing. | 15.3:s2, 15.3:s3 (p562) |

## 15.4 Formal and reset/timing checks

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-15.4-01 | MUST | system | none | Formal checks shall prove ordering, no duplication/loss, no speculative read, no AXI boundary crossing and response mapping. *(when: Under legal protocol assumptions)* | 15.4:s1, 15.4:s3 (p566) |
| AA-15.4-02 | MUST | system | none | Static timing analysis shall treat all bridge and FIFO paths as single-clock synchronous paths under i_clk_core, with no CDC paths or asynchronous clock groups. | 15.4:s2, 15.4:s4 (p566) |
| AA-15.4-03 | MUST | system | none | Reset analysis shall verify the one-reset contract, asynchronous assertion, SoC-synchronized deassertion before the IP boundary, and clearing of FIFO valid state. | 15.4:s3, 15.4:s5 (p566) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-16-01 | MUST_NOT | system | none | The IP includes no IP-specific DFT mode, scan port, MBIST port or test interrupt. | 16:s1 (p570) |
| AA-16-02 | MUST | system | none | Standard-cell scan insertion and FIFO memory test are owned by the SoC DFT flow, and this interface assumption is confirmed during DFT integration. *(when: During DFT integration)* | 16:s2 (p570) |

## 17.1.1 Clock and analysis scenarios

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-17.1.1-01 | MUST | system | none | The SoC integrator shall supply the i_clk_core clock frequency/period and uncertainty before static timing analysis. *(when: before STA)* | 17.1.1:s2 (p582) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-17.1.3-01 | MUST_NOT | system | none | No clock-domain crossing exceptions are required; the bridge, AHB, AXI and FIFOs use one synchronous clock domain. | 17.1.3:s1, 17.1.3:s3 (p590) |
| AA-17.1.3-02 | MUST_NOT | system | none | Asynchronous clock groups or false paths must not be declared between bridge logic and FIFO pointers. *(when: timing constraints between bridge logic and FIFO pointers)* | 17.1.3:s2, 17.1.3:s4 (p590) |
| AA-17.1.3-03 | MUST | system | none | Only justified reset, generated-clock or memory-macro constraints supplied by the selected library and SoC flow shall be applied; no numeric exception is invented. *(when: when applying timing exceptions)* | 17.1.3:s3, 17.1.3:s5 (p590) |

## 17.2 Physical assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-17.2-01 | MUST | system | none | The synchronous FIFO storage must be mapped to standard cells or a compatible single-clock memory macro. | 17.2:s2, 17.2:s4 (p594) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-18-01 | MUST | slave | both | The bridge must preserve HNONSEC and translate supported HPROT fields per §6.3. | 18:s1 (p600) |
| AA-18-02 | MUST | slave | scenario | The bridge must reject Shareable transfers and unsupported HPROT combinations. *(when: When a transfer is Shareable or uses an unsupported HPROT combination)* | 18:s1 (p600) |
| AA-18-03 | MUST_NOT | slave | scenario | The bridge must not implement address-based access control. | 18:s1 (p600) |
| AA-18-04 | MUST | slave | scenario | The bridge must reject transfers with HMASTLOCK; exclusive/atomic access is not implemented. *(when: When HMASTLOCK is asserted)* | 18:s2 (p601) |
| AA-18-05 | MUST | master | assertion | The AXI lock outputs must be tied low. | 18:s2 (p601) |
| AA-18-06 | MUST_NOT | slave | none | AHB parity must be disabled and no ECC may be added to data or FIFOs. | 18:s3 (p602) |
| AA-18-07 | MUST | system | none | The bridge must use one shared clock and reset, with no CDC or independent reset domains. | 18:s4 (p603) |
| AA-18-08 | MUST | slave | scenario | AXI response errors must be returned on AHB. *(when: When an AXI response error occurs)* | 18:s6 (p605) |
| AA-18-09 | MUST_NOT | slave | scenario | The bridge must not add any timeout or retry. | 18:s6 (p605) |

## 20.1 Assumptions and open items

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-20.1-01 | MUST | system | none | Open items OI-001 through OI-006 remain TBD pending SoC integration inputs; they are required for timing closure, latency validation, area closure, reset policy and tool selection. | 20.1:s1, 20.1:s2, 20.1:s3, 20.1:s4, 20.1:s5, 20.1:s7 (p641) |
| AA-20.1-02 | MUST | system | none | No product-behavior choice remains open. | 20.1:s8 (p650) |

## 20.2 Assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-20.2-01 | MUST | slave | both | The bridge must return AHB ERROR for unsupported size, misaligned address or reserved transfer encodings without issuing any AXI transaction. *(when: AHB transfer has unsupported size, misaligned address or reserved transfer encoding)* | 20.2:s1 (p656) |
| AA-20.2-02 | MUST_NOT | slave | scenario | The bridge must not provide an interrupt/event output; errors are reported only as synchronous AHB responses. | 20.2:s2 (p657) |
| AA-20.2-03 | MUST | slave | scenario | The AHB transfer remains pending when the AXI response never arrives, with no out-of-band error notification. *(when: AXI response never arrives)* | 20.2:s2 (p657) |
| AA-20.2-04 | MUST | system | none | SoC scan insertion and FIFO memory test are external integration responsibilities. | 20.2:s3 (p658) |

## 20.3 Decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-20.3-01 | MUST | system | none | AHB, AXI and all FIFO instances must use one shared rising-edge clock input i_clk_core. | 20.3:s4 (p667) |
| AA-20.3-02 | MUST | slave | both | The bridge must reject transfers with HPROT[6] equal to 1. *(when: HPROT[6]=1)* | 20.3:s9 (p672) |
| AA-20.3-03 | MUST | slave | scenario | Errors of eligible Normal Write-back bufferable fixed writes must be reported at the terminal AHB beat. *(when: Eligible Normal Write-back bufferable fixed write has an error)* | 20.3:s14 (p677) |
| AA-20.3-04 | MUST | slave | scenario | Device-E and non-bufferable writes must wait for BRESP on each beat. *(when: Device-E or non-bufferable writes)* | 20.3:s14 (p677) |
| AA-20.3-05 | MUST | slave | assertion | The bridge must issue a request within 6 i_clk_core cycles when queue space exists and READY is high. *(when: queue space available and READY high)* | 20.3:s17 (p680) |
| AA-20.3-06 | MUST | slave | both | A non-OKAY AXI response, including unexpected EXOKAY, must map to a two-cycle AHB ERROR response. *(when: AXI response is non-OKAY, including unexpected EXOKAY)* | 20.3:s18 (p681) |

## 20.4 Dependencies

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-20.4-01 | MUST | system | none | System reset controller and AXI endpoint must follow the shared reset contract. | 20.4:s3 (p691) |

## 21 Glossary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AA-21-01 | MUST_NOT | slave | scenario | The bridge must not merge Device-E (bufferable Device memory) writes. *(when: AHB write is to Device-E (bufferable Device memory))* | 21:s8 (p705) |
| AA-21-02 | MUST | slave | scenario | The bridge must wait for the final-destination BRESP before completing a Device-E write. *(when: AHB write is to Device-E (bufferable Device memory))* | 21:s8 (p705) |
| AA-21-03 | MUST_NOT | slave | both | The bridge must not issue an AXI read before its AHB address has been accepted (no speculation). *(when: AHB read address has not yet been accepted)* | 21:s10 (p707) |
