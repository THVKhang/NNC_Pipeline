# Extracted rules - AXI2APB_Bridge_Design_Specification.md

```
rules: 190  by strength {'MUST': 160, 'SHOULD': 1, 'MAY': 5, 'MUST_NOT': 24}  by check {'none': 44, 'both': 41, 'scenario': 59, 'assertion': 46}
normative sentences: 88  cited 87  skipped 1  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 24 (0 from cache)  cost US$0.6369  tokens in 113316 out 26775
```


## T1 AXI2APB Bridge Design Specification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-T1-01 | MUST | any | none | Requirements stated with 'shall' are mandatory and must be testable. | T1:s4 (p16) |
| AB-T1-02 | SHOULD | any | none | Statements using 'should' are recommendations. | T1:s4 (p16) |
| AB-T1-03 | MAY | any | none | Statements using 'may' are optional behaviours. | T1:s4 (p16) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-1.1-01 | MUST | system | both | The bridge converts transactions from one AXI4 Manager into ordered APB4 transfers through one APB port. | 1.1:s1 (p47) |
| AB-1.1-02 | MUST | system | both | The bridge uses one shared clock and has only one global transaction active at a time. | 1.1:s2, 1.1:s3 (p47) |
| AB-1.1-03 | MUST | system | scenario | The bridge supports AXI4 read/write channels, FIXED/INCR/WRAP bursts, 32-bit addresses/data, 1/2/4-byte transfers, IDs, PSTRB, PPROT, error propagation and defensive request rejection. | 1.1:s4 (p49) |

## 1.2 Deployment assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-1.2-01 | MUST | system | none | Bridge logic is technology-independent. | 1.2:s2 (p58) |
| AB-1.2-02 | MUST | system | both | AxPROT passes through to PPROT. | 1.2:s4 (p60) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-1.3-01 | MUST | system | scenario | FEAT-001 AXI4-to-APB4 conversion is required (REQ-FUNC-001). *(when: CFG-BASE)* | 1.3:s1 (p67) |
| AB-1.3-02 | MUST | system | scenario | FEAT-002 FIXED/INCR/WRAP burst support is required (REQ-IF-002). *(when: CFG-BASE)* | 1.3:s2 (p68) |
| AB-1.3-03 | MUST | system | scenario | FEAT-003 32-bit data and byte strobe support is required (REQ-IF-004). *(when: CFG-BASE)* | 1.3:s3 (p69) |
| AB-1.3-04 | MUST | system | scenario | FEAT-004 AXI ID echo is required (REQ-IF-005). *(when: CFG-BASE)* | 1.3:s4 (p70) |
| AB-1.3-05 | MUST | system | scenario | FEAT-005 protection/error mapping is required (REQ-ERR-002). *(when: CFG-BASE)* | 1.3:s5 (p71) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-2.1-01 | MUST | system | none | The RTL design must follow the VLSIT RTL Design Rules v2 as the mandatory RTL baseline. | 2.1:s3 (p81) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-2.2-01 | MUST_NOT | system | scenario | A product choice must not weaken a protocol requirement of the selected standards. | 2.2:s2, 2.2:s3 (p89) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-3-01 | MUST | master | scenario | The bridge shall convert each accepted AXI transaction into ordered APB transfers and return its AXI completion. | 3:s4 (p106) |
| AB-3-02 | MUST | master | assertion | The bridge shall keep at most one global read or write transaction active at any time. | 3:s5 (p107) |
| AB-3-03 | MUST | master | scenario | The bridge shall arbitrate between AR and AW by round-robin. *(when: When AR and AW are both pending)* | 3:s6 (p108) |
| AB-3-04 | MUST | master | scenario | The bridge shall choose AR for the first tie after reset. *(when: First AR/AW tie after reset)* | 3:s6 (p108) |
| AB-3-05 | MUST | master | scenario | The bridge shall flip the next tie preference between AR and AW after each completed transaction. *(when: After each completed transaction)* | 3:s6 (p108) |
| AB-3-06 | MUST | master | assertion | The bridge shall accept an AXI transfer only when VALID and READY are both high at rising ACLK. | 3:s7 (p109) |
| AB-3-07 | MUST | master | scenario | The bridge shall support FIXED bursts of 1–16 beats, INCR bursts of 1–256 beats, and WRAP bursts of 2, 4, 8 or 16 beats. | 3:s8 (p110) |
| AB-3-08 | MUST | master | scenario | The bridge shall support AxSIZE values 0, 1 and 2 (1, 2, 4 bytes). | 3:s9 (p111) |
| AB-3-09 | MUST | master | both | The bridge shall reject unsupported size/burst and 4-KiB-crossing transactions without any APB access. *(when: Unsupported size/burst or 4-KiB crossing)* | 3:s9 (p111) |
| AB-3-10 | MUST | master | assertion | The bridge shall align APB PADDR down to a four-byte word boundary. | 3:s10 (p112) |
| AB-3-11 | MUST | master | assertion | The bridge shall copy WSTRB to PSTRB. *(when: Write transfers)* | 3:s10 (p112) |
| AB-3-12 | MUST | master | assertion | The bridge shall drive PSTRB=0 on reads. *(when: Read transfers)* | 3:s10 (p112) |
| AB-3-13 | MUST | master | assertion | The bridge shall echo ARID on every R beat. *(when: Every R beat)* | 3:s11 (p113) |
| AB-3-14 | MUST | master | assertion | The bridge shall echo AWID on the corresponding B response. *(when: Corresponding B response)* | 3:s11 (p113) |
| AB-3-15 | MUST | master | assertion | The bridge shall copy AxPROT to PPROT. | 3:s12 (p114) |
| AB-3-16 | MUST | master | none | The bridge shall omit AxLOCK, USER, QOS and REGION ports. | 3:s12 (p114) |
| AB-3-17 | MUST | master | scenario | The bridge shall accept only AxCACHE values 0000 and 0001. | 3:s13 (p115) |
| AB-3-18 | MUST | master | both | The bridge shall return SLVERR without asserting PSEL. *(when: AxCACHE is not 0000/0001)* | 3:s13 (p115) |
| AB-3-19 | MUST_NOT | master | none | The bridge shall not implement exclusive access. | 3:s14 (p116) |
| AB-3-20 | MUST_NOT | system | none | Integration shall not send exclusive traffic to the bridge. | 3:s14 (p116) |
| AB-3-21 | MUST | master | assertion | The bridge shall hold AXI VALID and payload stable through the handshake. *(when: Until AXI handshake)* | 3:s15 (p117) |
| AB-3-22 | MUST | master | assertion | The bridge shall hold APB control and payload stable while PREADY=0. *(when: While PREADY=0)* | 3:s15 (p117) |
| AB-3-23 | MUST | any | none | The bridge shall use one shared ACLK/PCLK domain. | 3:s16 (p118) |
| AB-3-24 | MUST_NOT | any | none | The bridge shall contain no asynchronous clock crossing. | 3:s16 (p118) |
| AB-3-25 | MUST | master | none | The bridge shall use one active-low reset synchronous to ACLK. | 3:s17 (p119) |
| AB-3-26 | MUST | system | none | The SoC shall supply the reset synchronized to ACLK. | 3:s17 (p119) |
| AB-3-27 | MUST | master | assertion | AXI VALID outputs shall be low while reset is sampled active. *(when: While reset is sampled active)* | 3:s17 (p119) |
| AB-3-28 | MUST | any | scenario | PARA_AXI_ID_W shall range from 1 to 16, with default 4. | 3:s18 (p120) |
| AB-3-29 | MUST | any | scenario | PARA_AXI_ID_W shall set both read and write ID widths. | 3:s18 (p120) |
| AB-3-30 | MUST | master | both | An unsupported read shall return ARLEN+1 R beats with SLVERR. *(when: Unsupported read)* | 3:s19 (p121) |
| AB-3-31 | MUST | master | assertion | RLAST shall be asserted only on the final beat of an unsupported read. *(when: Unsupported read)* | 3:s19 (p121) |
| AB-3-32 | MUST_NOT | master | assertion | The bridge shall not perform APB access for an unsupported read. *(when: Unsupported read)* | 3:s19 (p121) |
| AB-3-33 | MUST | master | both | The bridge shall map read PSLVERR to SLVERR on that R beat. *(when: Read PSLVERR)* | 3:s20 (p122) |
| AB-3-34 | MUST | master | scenario | The bridge shall accumulate write errors into the final BRESP after all declared W beats. *(when: Write errors)* | 3:s20 (p122) |
| AB-3-35 | MUST | master | scenario | The bridge shall drain AWLEN+1 W beats for an unsupported write. *(when: Unsupported write)* | 3:s21 (p123) |
| AB-3-36 | MUST_NOT | master | assertion | The bridge shall not perform APB access for an unsupported write. *(when: Unsupported write)* | 3:s21 (p123) |
| AB-3-37 | MUST | master | both | The bridge shall then return one SLVERR B response. *(when: After draining unsupported write)* | 3:s21 (p123) |
| AB-3-38 | MUST | system | scenario | The external APB fabric shall provide a default unmapped Completer with PREADY=1 and PSLVERR=1. *(when: Unmapped address)* | 3:s22 (p124) |
| AB-3-39 | MUST_NOT | master | scenario | The bridge shall have no APB timeout. | 3:s23 (p125) |
| AB-3-40 | MUST | master | both | The bridge shall hold the APB access while PREADY=0 and wait indefinitely if PREADY never rises. *(when: While PREADY=0)* | 3:s23 (p125) |
| AB-3-41 | MUST | master | both | A completed APB transfer with PSLVERR=1 shall cause the associated AXI response to be SLVERR. *(when: Completed APB transfer with PSLVERR=1)* | 3:s24 (p126) |
| AB-3-42 | MUST_NOT | master | none | The bridge shall contain no software-visible CSR interface. | 3:s25 (p127) |
| AB-3-43 | MUST | system | none | Verification shall derive expected results from this specification and cited standards, never from generated RTL. | 3:s26 (p128) |
| AB-3-44 | MUST | system | none | Verification deliverables shall retain generated testbench sources and commands. | 3:s27 (p129) |
| AB-3-45 | MUST | system | none | Verification shall use one Makefile as the documented command entry point. | 3:s27 (p129) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-4-01 | MUST | system | scenario | CFG-BASE shall provide a full AXI4 Subordinate and an APB4 Manager with legal FIXED/INCR/WRAP bursts and ID echo. *(when: Configuration CFG-BASE)* | 4:s1 (p135) |
| AB-4-02 | MUST_NOT | system | none | CFG-BASE shall not include CDC, timeout, CSR, exclusive access, or USER/QOS/REGION features (disabled). *(when: Configuration CFG-BASE)* | 4:s1 (p135) |
| AB-4-03 | MUST | system | none | CFG-BASE shall use 32-bit AXI address/data and 32-bit APB address/data, default ID width 4, and a shared clock. *(when: Configuration CFG-BASE)* | 4:s1 (p135) |
| AB-4-04 | MAY | system | none | The AXI ID width may be configured at elaboration. *(when: At elaboration)* | 4:s3 (p137) |

## 5.1 Overview and block responsibilities

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-5.1-01 | MUST | system | none | The top module m_axi2apb_bridge contains only child instances and port wiring, with no other logic. | 5.1:s2, 5.1:s5 (p143) |
| AB-5.1-02 | MUST | system | scenario | m_axi2apb_apb_ctrl arbitrates between AR and AW requests in round-robin order. *(when: When both AR and AW requests are pending)* | 5.1:s3, 5.1:s6, 5.1:s10 (p143) |
| AB-5.1-03 | MUST | master | scenario | AXI response backpressure must stall the sequencer that owns the transaction. *(when: When AXI response backpressure occurs (RREADY or BREADY low))* | 5.1:s4, 5.1:s7 (p143) |
| AB-5.1-04 | MUST | system | both | m_axi2apb_apb_ctrl retains the transaction owner until the final R or B response completes. *(when: From grant until the final R or B response)* | 5.1:s10 (p149) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-5.3-01 | MUST | slave | both | The bridge performs one APB read per beat in AXI order, then presents RVALID/RDATA/RRESP/RLAST/RID and holds them until RREADY. *(when: After AR accepted and validated)* | 5.3:s1 (p161) |
| AB-5.3-02 | MUST | slave | both | The bridge accepts AW first and then W beats in order. | 5.3:s2, 5.3:s4, 5.3:s5 (p163) |
| AB-5.3-03 | MAY | master | scenario | The master may assert WVALID before the AW address is accepted. | 5.3:s3, 5.3:s5 (p163) |
| AB-5.3-04 | MUST | slave | assertion | WREADY must remain low until AW has been accepted. *(when: Until AW has been accepted)* | 5.3:s3, 5.3:s5 (p163) |
| AB-5.3-05 | MUST | slave | both | The bridge performs one APB write per beat and returns B only after the last APB completion. *(when: After the last APB write completion)* | 5.3:s4, 5.3:s6 (p163) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-5.4-01 | MUST | system | both | Only one transaction owns the bridge at a time; read and write transactions must not interleave. | 5.4:s1 (p167) |
| AB-5.4-02 | MUST | master | assertion | APB transfers must be sequential. | 5.4:s2 (p168) |
| AB-5.4-03 | MUST | master | assertion | APB payload and control signals must remain stable during wait. *(when: During an APB wait)* | 5.4:s2 (p168) |
| AB-5.4-04 | MUST | slave | assertion | IDs are retained and echoed unchanged in the response (RID equals ARID, BID equals AWID). | 5.4:s3 (p169) |
| AB-5.4-05 | MUST | slave | both | The read beat count is ARLEN+1 and the legal write beat count is AWLEN+1. | 5.4:s4 (p170) |
| AB-5.4-06 | MUST | slave | assertion | AXI response payload must remain stable while VALID=1 and READY=0. *(when: While VALID=1 and READY=0 on an AXI response channel)* | 5.4:s5 (p171) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-6.1-01 | MUST | slave | scenario | The bridge must implement the required AXI4 (IHI 0022 H.c) Subordinate interface IF-001 on CLK-AXI in CFG-BASE. | 6.1:s1 (p179) |
| AB-6.1-02 | MUST | master | scenario | The bridge must implement the required APB4 (IHI 0024 D) Manager/Requester interface IF-002 on CLK-AXI with PCLK=ACLK in CFG-BASE. | 6.1:s2 (p180) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-6.2-01 | MUST | master | assertion | APB setup phase must have o_apb_psel=1 and o_apb_penable=0; access phase has both 1 and completes when i_apb_pready=1. *(when: During an APB transfer)* | 6.2:s2, 6.2:s3 (p184) |
| AB-6.2-02 | MUST | slave | assertion | o_axi_bid and o_axi_bresp must remain stable until the B handshake completes. *(when: o_axi_bvalid=1 until B handshake)* | 6.2:s20, 6.2:s21 (p204) |
| AB-6.2-03 | MUST | slave | assertion | o_axi_bid and o_axi_bresp must be 0 in reset. *(when: During reset)* | 6.2:s20, 6.2:s21 (p204) |
| AB-6.2-04 | MUST | slave | assertion | o_axi_rid, o_axi_rdata and o_axi_rresp must remain stable until the R handshake completes. *(when: o_axi_rvalid=1 until R handshake)* | 6.2:s33, 6.2:s34, 6.2:s35 (p217) |
| AB-6.2-05 | MUST | slave | assertion | o_axi_rid, o_axi_rdata and o_axi_rresp must be 0 in reset. *(when: During reset)* | 6.2:s33, 6.2:s34, 6.2:s35 (p217) |
| AB-6.2-06 | MUST | slave | assertion | o_axi_rlast must be high only on the final read beat. | 6.2:s36 (p220) |
| AB-6.2-07 | MUST | master | assertion | o_apb_paddr, o_apb_pwrite and o_apb_pprot must remain stable through the transfer. *(when: During an APB transfer)* | 6.2:s39, 6.2:s40, 6.2:s43 (p223) |
| AB-6.2-08 | MUST | master | assertion | o_apb_paddr, o_apb_pwrite, o_apb_pwdata, o_apb_pstrb and o_apb_pprot must be 0 when idle. *(when: When APB is idle)* | 6.2:s39, 6.2:s40, 6.2:s41, 6.2:s42, 6.2:s43 (p223) |
| AB-6.2-09 | MUST | master | assertion | o_apb_paddr must be a word-aligned byte address. | 6.2:s39 (p223) |
| AB-6.2-10 | MUST | master | assertion | o_apb_pwdata must remain stable during wait states. *(when: APB write transfer waiting for i_apb_pready)* | 6.2:s41 (p225) |
| AB-6.2-11 | MUST | master | assertion | o_apb_pstrb must remain stable through the access. *(when: During an APB access)* | 6.2:s42 (p226) |
| AB-6.2-12 | MUST | master | assertion | o_apb_pstrb must be zero on reads. *(when: APB read transfer)* | 6.2:s42 (p226) |
| AB-6.2-13 | MUST | master | assertion | o_apb_pprot must be a copy of the corresponding AxPROT. *(when: APB transfer)* | 6.2:s43 (p227) |

## 6.3 Protocol behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-6.3-01 | MUST | slave | scenario | A legal AXI read (FIXED/INCR/WRAP, size 0–2, cache 0000/0001) must be supported and performed as APB transfers. *(when: AXI read is legal: FIXED/INCR/WRAP, size 0-2, cache 0000/0001, no 4-KiB crossing)* | 6.3:s1 (p238) |
| AB-6.3-02 | MUST | slave | both | The bridge must issue no APB transfer and return ARLEN+1 R beats with RRESP SLVERR. *(when: AXI read request is unsupported or crosses a 4-KiB boundary)* | 6.3:s1 (p238) |
| AB-6.3-03 | MUST | master | scenario | A legal AXI write consists of an AW request followed by the declared number of W beats; W data may arrive before AW. *(when: AXI write)* | 6.3:s2 (p239) |
| AB-6.3-04 | MAY | master | scenario | W beats may arrive before the AW request. *(when: AXI write)* | 6.3:s2 (p239) |
| AB-6.3-05 | MUST | slave | both | The bridge must issue no APB transfer, drain the W beats, then return a B response with SLVERR. *(when: AW request is unsupported)* | 6.3:s2 (p239) |
| AB-6.3-06 | MAY | system | none | AXI protocol violations are outside the guaranteed profile, so bridge behavior is not guaranteed for them. *(when: AXI protocol violations)* | 6.3:s2 (p239) |
| AB-6.3-07 | MUST | slave | both | The bridge must perform one APB transfer per AXI beat. *(when: legal APB transfer)* | 6.3:s3 (p240) |
| AB-6.3-08 | MUST | slave | scenario | The bridge must hold the APB access indefinitely and not time out. *(when: PREADY never rises during the access phase)* | 6.3:s3 (p240) |
| AB-6.3-09 | MUST | slave | both | The bridge must sample PSLVERR on the completed APB transfer. *(when: APB transfer completes)* | 6.3:s4 (p241) |
| AB-6.3-10 | MUST | slave | both | The bridge must return the read beat with RRESP SLVERR, treating read data as invalid. *(when: APB read completes with PSLVERR)* | 6.3:s4 (p241) |
| AB-6.3-11 | MUST | slave | both | The bridge must accumulate the write error and report it in BRESP. *(when: APB write completes with PSLVERR)* | 6.3:s4 (p241) |
| AB-6.3-12 | MUST | slave | scenario | The external default Completer must respond with PREADY=1 and PSLVERR=1, and the bridge must then return AXI SLVERR. *(when: address is unmapped)* | 6.3:s5 (p242) |
| AB-6.3-13 | MUST_NOT | system | none | A missing default responder for unmapped addresses is an integration violation and must not occur. *(when: integration)* | 6.3:s5 (p242) |
| AB-6.3-14 | MUST | slave | both | The bridge must reject the request before issuing any APB traffic. *(when: burst request crosses a 4-KiB address boundary)* | 6.3:s6, 6.3:s7 (p244) |
| AB-6.3-15 | MUST_NOT | master | assertion | A burst must not cross a 4-KiB address boundary. *(when: AXI4 burst)* | 6.3:s6 (p244) |

## 6.4 Interrupts and events

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-6.4-01 | MUST_NOT | slave | none | The baseline bridge has no interrupt port. *(when: approved baseline)* | 6.4:s1, 6.4:s2 (p250) |

## 7.2 CDC and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-7.2-01 | MUST | system | scenario | The SoC must provide i_rst_n_axi synchronous to CLK-AXI (i_clk_axi). | 7.2:s2, 7.2:s3 (p262) |

## 7.3 Reset domains and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-7.3-01 | MUST | slave | assertion | PSEL and PENABLE must be 0 after the active reset edge, and AXI VALID outputs must be 0 during reset. *(when: After active reset edge of i_rst_n_axi)* | 7.3:s1 (p272) |
| AB-7.3-02 | MUST | system | scenario | Reset is sampled on the rising edge of i_clk_axi, and i_rst_n_axi must be kept active for at least one rising edge. *(when: When reset is asserted)* | 7.3:s2, 7.3:s4 (p274) |
| AB-7.3-03 | MUST | system | none | The SoC owns reset synchronization and must coordinate the reset of the AXI Manager with the APB fabric. | 7.3:s3, 7.3:s5 (p274) |
| AB-7.3-04 | MUST | slave | scenario | Reset cancels in-flight local state; completion or rollback of an interrupted transfer is not guaranteed. *(when: When reset is asserted during a transfer)* | 7.3:s4, 7.3:s6 (p274) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-8-01 | MUST | system | scenario | PARA_AXI_ID_W must be declared as parameter logic [31:0] with default value 4. | 8:s1 (p282) |
| AB-8-02 | MUST | system | none | The comments Parameter Description, Parameter values and Parameter unit must immediately precede the PARA_AXI_ID_W declaration. | 8:s2, 8:s3, 8:s5 (p282) |
| AB-8-03 | MUST | system | scenario | PARA_AXI_ID_W legal range is 1 to 16 inclusive; any invalid value must cause an elaboration error. *(when: When PARA_AXI_ID_W is outside the legal range 1 to 16 inclusive)* | 8:s4 (p286) |
| AB-8-04 | MUST | system | scenario | PARA_AXI_ID_W must set the width of the AXI read/write ID ports, shared between read and write. | 8:s4 (p286) |
| AB-8-05 | MUST | system | scenario | Address, data and APB widths must be fixed at 32 bits. | 8:s6 (p288) |
| AB-8-06 | MUST | system | scenario | CFG-BASE must elaborate with hierarchy m_axi2apb_bridge containing m_axi2apb_rd_seq, m_axi2apb_wr_seq and m_axi2apb_apb_ctrl, and ID widths 1, 4, 16 must pass elaboration, lint and synthesis checks. *(when: Configuration CFG-BASE with PARA_AXI_ID_W=4)* | 8:s7 (p292) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-9-01 | MUST | master | assertion | APB PADDR must clear address bits [1:0] of the 32-bit AXI byte address. | 9:s1 (p298) |
| AB-9-02 | MUST | slave | scenario | A burst that crosses a 4-KiB boundary must be rejected. *(when: A burst would cross a 4-KiB boundary)* | 9:s1 (p298) |
| AB-9-03 | MUST_NOT | master | both | The 32-bit data path must not rotate byte lanes between AXI and APB. | 9:s2 (p299) |
| AB-9-04 | MUST | slave | scenario | An unsupported size must be answered with SLVERR. *(when: AxSIZE is unsupported)* | 9:s2, 9:s4 (p299) |
| AB-9-05 | MUST | slave | assertion | The AXI ID must be echoed unchanged in the response without remapping. | 9:s3 (p300) |
| AB-9-06 | MUST | slave | scenario | AxSIZE values other than 0, 1 and 2 must be rejected. *(when: AxSIZE is not 0, 1 or 2)* | 9:s4 (p301) |
| AB-9-07 | MUST | slave | scenario | The declared AxLEN (beats minus one, 1–256 beats) must control the expected beat count of the burst. | 9:s5 (p302) |
| AB-9-08 | MUST | slave | scenario | A reserved AxBURST value must be rejected; FIXED, INCR and WRAP are the legal values. *(when: AxBURST holds the reserved value)* | 9:s6 (p303) |
| AB-9-09 | MUST | slave | scenario | AxCACHE encodings other than 0000 and 0001 must be rejected; AxCACHE is used for validation only. *(when: AxCACHE is not 0000 or 0001)* | 9:s7 (p304) |
| AB-9-10 | MUST | master | assertion | AxPROT must be copied directly to PPROT with no translation. | 9:s8 (p305) |
| AB-9-11 | MUST | master | assertion | For subword writes, WSTRB must be copied to PSTRB unchanged. *(when: Subword write)* | 9:s9 (p307) |
| AB-9-12 | MUST | master | assertion | The Manager must assert only PSTRB lanes legal for the address and size. | 9:s9, 9:s11 (p307) |
| AB-9-13 | MUST | master | assertion | APB PADDR must be word-aligned. | 9:s10 (p307) |
| AB-9-14 | MUST | master | scenario | PRDATA must be returned in bus lanes, and the Manager selects the requested bytes using AXI address and size. *(when: Read)* | 9:s11 (p307) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-10.1-01 | MUST | slave | scenario | In IDLE the bridge arbitrates between AR and AW and selects a transaction upon address handshake. *(when: In IDLE after reset release)* | 10.1:s1 (p315) |
| AB-10.1-02 | MUST | slave | scenario | In READ the bridge validates the request, performs an APB read per beat, returns ARLEN+1 R beats, and exits after the final R handshake. *(when: AR accepted and supported)* | 10.1:s2 (p316) |
| AB-10.1-03 | MUST | slave | scenario | In WRITE the bridge accepts W, performs an APB write per beat, returns one B, and exits on B handshake. *(when: AW accepted and supported)* | 10.1:s3 (p317) |
| AB-10.1-04 | MUST | slave | both | In REJECT_READ the bridge performs no APB access and returns error beats with SLVERR and zero data, with final RLAST, then exits after final R handshake. *(when: Unsupported AR accepted)* | 10.1:s4 (p318) |
| AB-10.1-05 | MUST | slave | both | In REJECT_WRITE the bridge drains the declared W count with no APB access and returns B with SLVERR. *(when: Unsupported AW accepted)* | 10.1:s5 (p319) |
| AB-10.1-06 | MUST | slave | both | Reset returns the bridge to IDLE, clears local state, deselects APB, and cancels in-flight work. *(when: Reset asserted in any state)* | 10.1:s6, 10.2:s5 (p321) |

## 10.2 Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-10.2-01 | MUST | slave | both | A read performs an APB read per beat, holds the address for FIXED and follows AXI address rules for INCR and WRAP, returns ARLEN+1 R beats with RID echoed and final RLAST, serialized. *(when: Legal accepted AR)* | 10.2:s1 (p327) |
| AB-10.2-02 | MUST | slave | both | A write performs an APB write per beat, maps WSTRB to PSTRB, accumulates PSLVERR, and returns one B only after final APB completion, serialized. *(when: Legal AW plus AWLEN+1 W beats)* | 10.2:s2 (p328) |
| AB-10.2-03 | MUST | slave | both | An unsupported read performs no APB access and returns ARLEN+1 R beats with SLVERR and zero data, honoring RREADY. *(when: Accepted AR outside profile)* | 10.2:s3 (p329) |
| AB-10.2-04 | MUST | slave | both | An unsupported write performs no APB access, drains the declared W count, and returns one SLVERR B after the final W. *(when: Accepted AW outside profile)* | 10.2:s4 (p330) |
| AB-10.2-05 | MUST | slave | both | PSLVERR on a read beat marks that beat's response as error. *(when: APB read beat returns PSLVERR)* | 10.2:s6 (p333) |
| AB-10.2-06 | MUST | slave | both | Write PSLVERR accumulates, later beats still execute, and final BRESP is SLVERR. *(when: PSLVERR on a write beat)* | 10.2:s7 (p333) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-10.3-01 | MUST | slave | assertion | While PREADY is low during APB access, the bridge keeps APB control and data stable. *(when: APB PREADY wait)* | 10.3:s8 (p347) |
| AB-10.3-02 | MUST_NOT | slave | scenario | The bridge has no internal APB timeout; it must not abort an APB transfer by timeout. | 10.3:s16 (p356) |
| AB-10.3-03 | MUST | any | none | Signals are sampled on the rising edge of CLK-AXI. | 10.3:s17 (p358) |
| AB-10.3-04 | MUST | slave | assertion | APB setup is PSEL=1/PENABLE=0, access is PSEL=1/PENABLE=1, and completion requires PREADY=1. *(when: APB transfer)* | 10.3:s18 (p358) |

## 10.4 Arbitration, buffering, and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-10.4-01 | MUST | slave | scenario | AR/AW arbitration is round-robin when both are pending. *(when: AR and AW both pending)* | 10.4:s1 (p362) |
| AB-10.4-02 | MUST | slave | both | The selected transaction owns the bridge until its final R handshake or B handshake. | 10.4:s2 (p362) |

## 10.5 Memories and storage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-10.5-01 | MUST_NOT | system | none | No SRAM, ROM or external FIFO is required. | 10.5:s1 (p366) |

## 11 Register and programming model

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-11-01 | MUST_NOT | system | none | The bridge must not provide a software-visible CSR; configuration is static at elaboration. | 11:s1 (p370) |

## 11.1 CSR specification source

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-11.1-01 | MUST_NOT | system | none | No CSR workbook is required for the bridge. | 11.1:s1 (p374) |

## 11.2 Software sequences

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-11.2-01 | MUST | system | none | SoC integration configures the address map and the default APB error Completer. *(when: SoC integration)* | 11.2:s2 (p378) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-12-01 | MUST | slave | both | Respond with ARLEN+1 SLVERR read beats carrying zero data and RLAST on the final beat, without issuing any APB access. *(when: Unsupported read is detected (ERR-001))* | 12:s1 (p384) |
| AB-12-02 | MUST | slave | assertion | Do not generate any APB transfer for an unsupported read. *(when: Unsupported read is detected (ERR-001))* | 12:s1 (p384) |
| AB-12-03 | MUST | slave | scenario | Reset cancels the in-progress error handling for ERR-001, ERR-002, ERR-003, ERR-004 and ERR-006. *(when: Reset occurs during error handling)* | 12:s1, 12:s2, 12:s3, 12:s4, 12:s6 (p384) |
| AB-12-04 | MUST | slave | both | Drain the expected count of W beats, then complete the write with a B response of SLVERR, without any APB access. *(when: Unsupported write is detected (ERR-002))* | 12:s2 (p385) |
| AB-12-05 | MUST | slave | assertion | Do not generate any APB transfer for an unsupported write. *(when: Unsupported write is detected (ERR-002))* | 12:s2 (p385) |
| AB-12-06 | MUST | slave | both | Return RRESP=SLVERR with RDATA=0 for the beat, and continue processing the remaining beats. *(when: APB read returns PSLVERR (ERR-003))* | 12:s3 (p386) |
| AB-12-07 | MUST | slave | both | Accumulate the error, continue the remaining write beats, and return final BRESP=SLVERR. *(when: APB write returns PSLVERR (ERR-004))* | 12:s4 (p387) |
| AB-12-08 | MUST | slave | both | Hold the APB access indefinitely with no timeout until the completer responds or system reset occurs. *(when: PREADY remains low (ERR-005))* | 12:s5 (p388) |
| AB-12-09 | MUST | slave | both | Reset deselects the APB completer. *(when: Reset occurs while PREADY is low)* | 12:s5 (p388) |
| AB-12-10 | MUST | system | scenario | Default Completer drives PREADY=1 and PSLVERR=1, and the bridge reports an AXI SLVERR response. *(when: Address is unmapped (ERR-006))* | 12:s6 (p389) |
| AB-12-11 | MUST_NOT | slave | assertion | Never report an APB failure as AXI OKAY. *(when: An APB failure occurs)* | 12:s8 (p391) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-14.1-01 | MUST | system | none | The RTL must comply with VLSIT RTL Design Rules v2. | 14.1:s1 (p408) |
| AB-14.1-02 | MUST | system | none | RTL uses one synthesizable module per .sv file with matching filename, structural top, ANSI ports (input wire, output logic, inout wire only for pad wrappers), rule-compliant names, unsigned four-state logic, explicit widths, only always_comb/always_ff, named connections, and logic-section comments. | 14.1:s2, 14.1:s4 (p408) |
| AB-14.1-03 | MUST_NOT | system | none | RTL must not use package, plain always, always_latch, two-state or signed types, define/undef, latches, multiple drivers, or unsynthesizable test code. | 14.1:s3, 14.1:s5 (p408) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-15.1-01 | MUST | system | none | The testbench and reference model must be built independently of the generated RTL. | 15.1:s2 (p434) |
| AB-15.1-02 | MUST_NOT | system | none | The RTL must not define expected results; expected results come from the independent reference model. | 15.1:s2, 15.1:s4 (p434) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-15.2-01 | MUST | system | scenario | The independent model must match the bridge addresses, data and responses for FIXED, INCR and WRAP bursts with legal sizes. *(when: FIXED/INCR/WRAP bursts with legal sizes under CFG-BASE (TEST-001))* | 15.2:s1 (p440) |
| AB-15.2-02 | MUST | system | assertion | Payload must remain stable through APB wait states and RREADY/BREADY stalls, checked by assertions. *(when: During APB wait and RREADY/BREADY stalls (TEST-003))* | 15.2:s3 (p442) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-16-01 | MUST_NOT | system | none | The baseline bridge must not include a memory macro or MBIST port. | 16:s2, 16:s4 (p468) |
| AB-16-02 | MUST_NOT | system | none | The bridge must not use internal clock gating, so no clock-gating test enable is needed. | 16:s11 (p477) |

## 17.1 Timing constraints and budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-17.1-01 | MUST | system | none | The SoC integrator must provide clock period, uncertainty, transition, latency, interface delays, loads, PVT/RC corners and timing modes before timing closure. *(when: before timing closure)* | 17.1:s1 (p485) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-17.1.3-01 | MUST | system | none | A later timing exception must have exact endpoints, mode, rationale and CDC/RDC evidence. *(when: when a timing exception is added later)* | 17.1.3:s2 (p503) |
| AB-17.1.3-02 | MUST_NOT | system | none | Broad timing exceptions must not be used. | 17.1.3:s2 (p503) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-18-01 | MUST | system | both | The bridge must map AxPROT to PPROT. | 18:s1 (p526) |
| AB-18-02 | MUST_NOT | system | scenario | The bridge must not perform a local access-control check on PPROT; APB Completers enforce PPROT. | 18:s2 (p527) |
| AB-18-03 | MUST | system | scenario | The bridge must propagate errors and provide no interrupt or status mechanism. *(when: When an error occurs)* | 18:s7 (p532) |

## 20 Assumptions, dependencies, and decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AB-20-01 | MUST | slave | scenario | The bridge must support the conversion profile: FIXED/INCR/WRAP burst types, legal lengths, 1/2/4-byte transfer sizes, and PSTRB/PPROT conversion. | 20:s4 (p570) |
| AB-20-02 | MUST | system | none | The bridge has no timeout or CSR, so the system must provide a default APB error Completer. | 20:s7 (p573) |
| AB-20-03 | MUST | master | scenario | The bridge must tolerate APB waiting indefinitely, as it has no timeout. *(when: APB completer does not respond)* | 20:s7 (p573) |
| AB-20-04 | MUST | system | none | Any lint finding must be fixed or reported under the skill rules, with no project-specific waivers. *(when: A lint finding is reported by the VLSIT v2 rule checks or Verilator/slang lint flow)* | 20:s15 (p581) |
| AB-20-05 | MUST | master | none | The AXI Manager must comply with AXI4 WLAST/AWLEN and WSTRB rules; no RTL recovery is defined for malformed write traffic. | 20:s17, 20:s21 (p583) |
| AB-20-06 | MUST | system | scenario | Reset must cancel local state without replay or rollback, which requires coordinated system reset. | 20:s18 (p584) |
| AB-20-07 | MUST | system | none | The APB address map/decoder must provide a match or a default response with PREADY=1 and PSLVERR=1. | 20:s22 (p588) |
