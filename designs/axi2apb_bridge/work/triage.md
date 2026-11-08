# Failure triage

Failures: 14; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_018_long_apb_wait — CHK-018: ACCESS lasts 1001 edges for write got 1

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AXI2APB_Bridge_Design_Specification.md:328 OP-002 Write: "APB write per beat; WSTRB→PSTRB; accumulate PSLVERR | One B after final APB completion"; spec:298 "APB PADDR clears bits [1:0]"; rules.json:1249 AB-3-39 (REQ-ERR-005) "The bridge shall have no APB timeout; hold access while PREADY=0 and wait indefinitely". contract.json:707 CHK-016 beat-address formula: "INCR: addr_0=A ... o_apb_paddr == addr_k & 32'hFFFF_FFFC". contract.json:742 CHK-018 stimulus: "Single-beat read at 0x0000_5000 ... A single-beat write is then run in the same way"; contract.json:743 expected: "ACCESS lasts exactly 1001 edges". |
| RTL does | rtl/m_axi2apb_wr_seq.sv:332 loads reg_wr_addr<=AWADDR (0x5000) at the AW handshake. In ENUM_ST_WDAT, on the W handshake, wr_seq.sv:340-345 captures data/strb AND already does reg_wr_addr <= w_wr_nxt_addr, where for INCR w_wr_nxt_addr = (reg_wr_addr & ~mask) + size (wr_seq.sv:231) = 0x5004. Only after that does the FSM go to ENUM_ST_REQ (wr_seq.sv:255-256), and o_req_addr = {reg_wr_addr[31:2],2'b00} (wr_seq.sv:294) = 0x5004. apb_ctrl.sv:256-258 latches i_wr_req_addr into reg_apb_addr, which drives o_apb_paddr (apb_ctrl.sv:188/196). So the single write beat goes to PADDR 0x5004, not 0x5000. The read sequencer advances only after the R handshake (rd_seq.sv:374-378), so the read half went to 0x5000 and passed. This test got past the read check at test line 1023 and failed only at the write check at line 1035. |
| Test does | test_axi2apb_bridge.py:1015 sets the completer wait to `WAIT if x["paddr"] == 0x5000 else 0`. Line 1029 sends a single-beat INCR write to 0x5000. _check_long_wait (line 987) expects x.access == 1001. The completer keys its wait on PADDR==0x5000. The bridge drove 0x5004, so the completer added 0 waits and the transfer had 1 ACCESS edge. The expected 1001 comes from the contract stimulus and the CHK-016 address formula, where the write's PADDR equals AWADDR 0x5000. |
| A_rtl_wrong | For: The write sequencer moves the address forward when it captures the W beat (wr_seq.sv:344) and before the APB request goes out (wr_seq.sv:294, 306-307). So beat 0 is issued at AWADDR+size. This breaks CHK-016's addr_0=A (contract.json:707). The read path, which advances after the beat (rd_seq.sv:374-378), passed the same scenario. Every other write failure in this run shows the same +size shift.<br>Against: The RTL does not mishandle the long wait itself. The wait was never applied, so this failure does not exercise the no-timeout behaviour. |
| B_test_wrong | For: The test ties wait injection to an exact PADDR (line 1015). Any address error therefore shows up as an ACCESS-count failure, which hides the real symptom.<br>Against: The expected PADDR of 0x5000 is correct under the CHK-016 formula and contract.json:742. The test's expectation is right; only the error message is indirect. |
| C_spec_unclear | For: OP-002 (spec:328) says "APB write per beat" and, unlike OP-001 (spec:327), does not repeat "INCR and WRAP follow AXI address rules".<br>Against: REQ-IF-002 (spec:110) covers bursts for both directions. CHK-016 (contract.json:707) gives addr_0=A for both directions. WF-006 (spec:346) shows a byte write at 0x1001 going to PADDR=0x1000, so the first write beat uses AWADDR. |
| Options | Fix RTL (recommended): in m_axi2apb_wr_seq.sv, remove `reg_wr_addr <= w_wr_nxt_addr;` from the W-capture block (line 344). Advance the address after the beat's APB request instead, e.g. `if (reg_fsm_wr_current_state==ENUM_ST_REQ && i_req_ready) reg_wr_addr <= w_wr_nxt_addr;` (apb_ctrl.sv:256-258 latches the address on that edge), or on `ENUM_ST_WAIT && i_rsp_valid`, the same way rd_seq.sv:374-378 does it. Optional test improvement, without weakening anything: add an explicit `assert x.pay['paddr']==0x5000` before the ACCESS-count check so the message points at the real cause. Spec: optionally add "INCR and WRAP follow AXI address rules" to OP-002 (spec:328) to match OP-001. |

## 2. test_chk_019_arbitration_round_robin — CHK-016: paddr=0x00000200 for transfer 0 of write id=2 addr=0x200 len=1 got 0x00000204

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:707 CHK-016: "INCR: addr_0=A, and addr_k=(A & ~(S-1)) + k*S for k>=1 ... o_apb_paddr == addr_k & 32'hFFFF_FFFC". rules.json:3246 AB-10.2-02 (spec:328) "APB write per beat". spec:110 REQ-IF-002 "support FIXED (1–16 beats), INCR (1–256 beats), and WRAP". |
| RTL does | For W1 (AWADDR=0x200, INCR, len 1, size 2), wr_seq.sv:332 sets reg_wr_addr=0x200. The first W handshake in WDAT (wr_seq.sv:340-344) updates reg_wr_addr to w_wr_nxt_addr=0x204 (wr_seq.sv:231) before ENUM_ST_REQ drives o_req_addr from reg_wr_addr (wr_seq.sv:294). Transfer 0 therefore goes out at 0x204 and transfer 1 at 0x208. The arbitration checks at test lines 1055-1064 all passed; the failure comes from the scoreboard b.score() at line 1065. |
| Test does | Lines 1049-1052 issue R1/R2/W1/W2 as 2-beat INCR transactions. After the arbitration-order asserts pass, b.score() calls _score_one (line 859). That compares each APB transfer's paddr with beat_addrs() (lines 87-101, the CHK-016 formula), which gives 0x200 for k=0. |
| A_rtl_wrong | For: The address moves forward before the APB request is issued (wr_seq.sv:344 vs 294/306). For INCR the first beat must be at A (contract.json:707). The read sequencer advances after the beat (rd_seq.sv:374-378) and its reads were not flagged.<br>Against: None found. The arbitration behaviour this test targets passed. |
| B_test_wrong | For: The failing assertion is the general scoreboard rather than the CHK-019 arbitration checks.<br>Against: beat_addrs (lines 94-95) implements contract.json:707 exactly: a = addr when k==0. Expecting 0x200 is correct. |
| C_spec_unclear | For: OP-002 (spec:328) does not restate the AXI address rule for writes.<br>Against: CHK-016 (contract.json:707) and WF-006 (spec:346) state the first-beat address without ambiguity. |
| Options | Fix RTL: in m_axi2apb_wr_seq.sv, stop updating reg_wr_addr at the W handshake (line 344). Advance it after the beat's APB request is accepted (ENUM_ST_REQ && i_req_ready) or completed (ENUM_ST_WAIT && i_rsp_valid). The test needs no change. Optional spec clarification: in OP-002, state that write beats follow the same FIXED/INCR/WRAP address rules as reads. |

## 3. test_chk_020_wvalid_before_aw — CHK-020: APB addresses 0x3000..0x300C got ['0x3004','0x3008','0x300c','0x3010']

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:775 CHK-020 expected: "4 APB writes follow at 0x3000,0x3004,0x3008,0x300C, each carrying the matching WDATA/WSTRB". spec:163: "WVALID may precede AW but WREADY remains low until AW. Perform one APB write per beat". contract.json:707 CHK-016 INCR addr_0=A. |
| RTL does | The early-W part passed (test lines 1094-1105): WREADY stayed low until AW, because o_axi_wready is asserted only in WDAT/DRAIN (wr_seq.sv:303-305). After AW, each W handshake in WDAT moves reg_wr_addr forward (wr_seq.sv:344) before REQ drives o_req_addr (wr_seq.sv:294). The four APB writes therefore go to 0x3004, 0x3008, 0x300C and 0x3010. 0x3010 is outside the declared 16-byte burst 0x3000-0x300F. |
| Test does | Line 1091 sends a 4-beat INCR write at AWADDR=0x3000, size 2, with W asserted 10 edges before AW. Line 1106 expects the paddr list [0x3000,0x3004,0x3008,0x300C], taken directly from contract.json:775. |
| A_rtl_wrong | For: Every beat is shifted by +4, which matches a pre-increment at wr_seq.sv:344. The last beat writes 0x3010, an address the AXI burst never covered. The early-W ordering, which is what this test targets, behaves correctly.<br>Against: None found. |
| B_test_wrong | For: None. The expected list is copied word for word from the contract.<br>Against: contract.json:775 lists 0x3000..0x300C explicitly. |
| C_spec_unclear | For: OP-002 (spec:328) does not spell out the write address rule.<br>Against: The CHK-020 expected text and the CHK-016 formula are explicit. |
| Options | Fix RTL: in wr_seq, move the address advance (line 344) so it happens after the beat's APB request (REQ && i_req_ready) or completion (WAIT && i_rsp_valid). No test change is needed. |

## 4. test_chk_021_response_backpressure — CHK-016: paddr=0x0000b000 for transfer 0 of write id=12 addr=0xb000 len=7 got 0x0000b004

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:707 CHK-016 (INCR addr_0=A, paddr == addr_k & ~3). contract.json:790 CHK-021 expected: "The total of APB transfers per transaction equals AxLEN+1" and "All assertions" via b.final(). spec:328 OP-002 "APB write per beat". |
| RTL does | For each 8-beat INCR write at 0xB000+i*0x100, wr_seq.sv:344 moves reg_wr_addr forward on each W handshake before the APB request (wr_seq.sv:294, 306). Beats 0..7 therefore go to 0xB004..0xB020 instead of 0xB000..0xB01C. The backpressure checks (lines 1127-1142) all passed; the failure comes from b.final() → score() → _score_one line 859. |
| Test does | Line 1125 creates writes at 0xB000 + i*0x100, len 7, size 2, INCR. Lines 1123/1121 apply BREADY and PREADY stalls. b.final() at line 1143 scores each transaction against beat_addrs() (CHK-016 formula, lines 87-101), which expects transfer 0 at 0xB000. |
| A_rtl_wrong | For: This is the same +size pre-advance as the other write failures. The backpressure behaviour under test is correct; only the write addresses are wrong.<br>Against: None found. |
| B_test_wrong | For: The scoreboard check is a side check, not the focus of CHK-021.<br>Against: The scoreboard follows the CHK-016 formula from contract.json:707, and CHK-027/CHK-021 require all CHK-001..016 assertions to pass. |
| C_spec_unclear | For: OP-002 (spec:328) does not restate the address rules.<br>Against: CHK-016 is explicit, and WF-005/WF-006 (spec:345-346) describe the write PADDR sequence. |
| Options | Fix RTL in wr_seq (line 344): advance reg_wr_addr after the APB request or response for the beat, not when the W beat is captured. The test needs no change. |

## 5. test_chk_023_unsupported_writes — CHK-016: paddr=0x00007160 for transfer 0 of write id=1 addr=0x7160 len=1 got 0x00007164

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:842 CHK-023 expected: "The legal write that follows completes with APB writes and o_axi_bresp=2'b00". contract.json:707 CHK-016 INCR addr_0=A. spec:328 OP-002. |
| RTL does | The failing transaction is the legal recovery write ('good', AWADDR=0x7160, INCR len 1), not the unsupported one. For the unsupported write, the DRAIN path (wr_seq.sv:251, 270-273, 346-347) behaved correctly: the test's asserts at lines 1193-1202 passed. For the good write, wr_seq.sv:344 moves the address to 0x7164 when it captures W beat 0, before REQ drives o_req_addr (wr_seq.sv:294). Transfer 0 therefore goes to 0x7164 and transfer 1 to 0x7168. |
| Test does | Line 1190 creates good = 2-beat INCR write at 0x7100+8*rand (0x7160 here). b.score() at line 1203 compares it against beat_addrs(), which gives 0x7160 for k=0. |
| A_rtl_wrong | For: Same write-address pre-advance (wr_seq.sv:344). The unsupported-write handling that CHK-023 targets is correct.<br>Against: None found. |
| B_test_wrong | For: None specific.<br>Against: The expected value comes from the CHK-016 formula (contract.json:707). |
| C_spec_unclear | For: OP-002 does not restate the address rule.<br>Against: CHK-016 is explicit. |
| Options | Fix RTL in wr_seq (move the address advance from line 344 to after the beat's APB handshake). No test change. Once fixed, rerun to confirm the unsupported-write drain still passes. |

## 6. test_chk_025_write_pslverr — CHK-025: transfer0: 4 APB writes at 0x4000..0x400C got ['0x4004','0x4008','0x400c','0x4010']

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:879 CHK-025 expected: "Each variant performs all 4 APB writes, at 0x4000..0x400C, with the matching PWDATA/PSTRB". rules.json:3246 AB-10.2-02 "APB write per beat; WSTRB→PSTRB; accumulate PSLVERR". |
| RTL does | For the INCR write at 0x4000 (len 3, size 2), wr_seq.sv:344 advances reg_wr_addr on each W capture before the REQ state presents it (wr_seq.sv:294). The APB addresses come out as 0x4004..0x4010. PSLVERR accumulation (wr_seq.sv:348-349) is not involved: the test fails on the address list at line 1258, before the error checks. |
| Test does | Line 1255 sends a write at 0x4000, len 3, size 2, INCR. Error injection is by APB sequence number (line 1252), so it does not depend on the address. Line 1258 expects [0x4000,0x4004,0x4008,0x400C], from contract.json:879. |
| A_rtl_wrong | For: The +4 shift on every beat matches wr_seq.sv:344. The final beat writes 0x4010, which is outside the AXI burst.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected list comes word for word from contract.json:879. |
| C_spec_unclear | For: OP-002 (spec:328) does not restate the address rule.<br>Against: The CHK-025 expected text is explicit. |
| Options | Fix RTL in wr_seq (line 344): advance the address after the APB request or response for the beat. No test change. |

## 7. test_chk_026_unmapped_default_completer — CHK-016: paddr=0x80000000 for transfer 0 of write id=14 addr=0x80000000 len=1 got 0x80000004

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:893 CHK-026 expected: "The write makes 2 APB writes and returns one B with o_axi_bresp=2'b10". contract.json:707 CHK-016 INCR addr_0=A. The read side expects "2 APB reads at 0x8000_0000 and 0x8000_0004". |
| RTL does | The read half passed (test line 1278 checks 0x80000000/0x80000004): rd_seq advances only after R (rd_seq.sv:374-378). For the write, wr_seq.sv:344 advances to 0x80000004 on W beat 0, before the APB request (wr_seq.sv:294). The two APB writes therefore go to 0x80000004 and 0x80000008. |
| Test does | Line 1286 sends a 2-beat INCR write at UNMAPPED_BASE=0x80000000. Lines 1289-1293 pass (2 writes, access==1, SLVERR). b.final() at line 1294 runs _score_one, whose CHK-016 check (line 859) expects 0x80000000 for k=0. |
| A_rtl_wrong | For: Reads at the same address are correct and writes are shifted by +4. The difference is the order of address advance and request (wr_seq.sv:344 vs rd_seq.sv:374-378).<br>Against: None found. The SLVERR mapping that this test targets is correct. |
| B_test_wrong | For: None.<br>Against: The expected address follows the CHK-016 formula. |
| C_spec_unclear | For: The CHK-026 expected text does not list the write PADDRs explicitly.<br>Against: CHK-016 applies to all supported transactions, and the read side of the same check lists 0x8000_0000 as the first address. |
| Options | Fix RTL in wr_seq (line 344). No test change. Optional: to aid debug, add the explicit write paddr list [0x80000000,0x80000004] in the test, as the read side already has, without weakening anything. |

## 8. test_chk_027_random_legal_bursts — CHK-027: INCR 256 ends at 0x13FC got 0x1400

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:923 CHK-027 stimulus: "INCR AxLEN=255, AxSIZE=2 from 0x0000_1000 (ends at 0x0000_13FF)". contract.json:924 expected: "o_apb_paddr follows the CHK-016 beat-address formula with bits [1:0] cleared". spec:110 REQ-IF-002 INCR 1–256 beats. |
| RTL does | For the write corner (wq is checked first in the loop at test line 1318), wr_seq.sv:344 advances reg_wr_addr on each W capture before issuing the APB request (wr_seq.sv:294). The 256 beats therefore go to 0x1004..0x1400, and the last write lands at 0x1400, outside the declared 0x1000-0x13FF burst. The same pre-advance would make the 0x1F00/0x1FF0 corners write at 0x2000, across the 4-KiB page that the bridge's own check (wr_seq.sv:190-200) treats as illegal. A related failure in the random regression (sim.log:806) shows the WRAP version: write at 0x364C len 3, transfer 0 at 0x3640, the wrapped next address from wr_seq.sv:232-236. |
| Test does | Line 1304 sets the corner dict(addr=0x1000, ln=255, size=2, INCR) and sends a write then a read (lines 1314-1315). Line 1323 expects the last paddr to be 0x13FC: 0x1000 + 255*4, per contract.json:923. |
| A_rtl_wrong | For: The last address is one beat past the burst end, which matches the pre-increment at wr_seq.sv:344. The WRAP case in sim.log:806 shows the same off-by-one-beat pattern. Reads are not affected.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: 0x13FC is stated directly by contract.json:923 ("ends at 0x0000_13FF"). |
| C_spec_unclear | For: OP-002 (spec:328) does not restate the address rule for writes.<br>Against: CHK-016 and CHK-027 are explicit and cover both directions. |
| Options | Fix RTL in wr_seq: register the next address only after the beat's APB request is accepted or completed, so beat k uses addr_k. This fixes the INCR, WRAP and FIXED-unaligned write sequences. No test change. |

## 9. test_chk_028_subword_unaligned — CHK-028: paddr=0x1000 got 0x1004

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:939 CHK-028 expected: "Byte write to 0x1003 gives o_apb_paddr=0x0000_1000 ... Every write has o_apb_paddr=AWADDR & ~3". spec:298 "APB PADDR clears bits [1:0]"; spec:307 "APB PADDR is word-aligned"; spec:346 WF-006 "byte write at 0x1001, APB PADDR=0x1000"; rules.json:3069 AB-9-11. |
| RTL does | For a size-0 single write at 0x1003, wr_seq.sv:344 sets reg_wr_addr to (0x1003 & ~0) + 1 = 0x1004 at the W handshake (wr_seq.sv:231). o_req_addr = {0x1004[31:2],2'b00} = 0x1004 (wr_seq.sv:294). The earlier singles at 0x1000/0x1001/0x1002 also advanced (to 0x1001..0x1003), but those still align down to 0x1000, so the bug stayed hidden until the 0x1003 case. |
| Test does | Line 1354 lists the singles. Line 1357 sends a single-beat write with size 0 at 0x1003 and strobe 0x8. Line 1362 expects paddr == addr & ~3 = 0x1000, per contract.json:939. |
| A_rtl_wrong | For: A single-beat write should never advance before its only APB transfer. The +1 byte advance crosses the word boundary only for 0x1003, which matches the observed pass/fail pattern exactly. The strobe 0x8 with PADDR 0x1004 would also write the wrong byte.<br>Against: The align-down logic itself (wr_seq.sv:294) is correct. |
| B_test_wrong | For: None.<br>Against: The expected value comes from contract.json:939 and spec WF-006. |
| C_spec_unclear | For: None material.<br>Against: spec:298/307 and contract.json:939 are explicit. |
| Options | Fix RTL in wr_seq (line 344): advance after the APB request or response. No test change. |

## 10. test_chk_029_prot_passthrough — CHK-016: paddr=0x00006000 for transfer 0 of write id=11 addr=0x6000 len=1 prot=4 got 0x00006004

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:707 CHK-016 (INCR addr_0=A). contract.json:955-956 CHK-029: "send a 2-beat INCR read and a 2-beat INCR write to 0x0000_6000 ... Every transaction completes with OKAY and correct data". spec:305 "AxPROT/PPROT ... Direct copy". |
| RTL does | The PPROT pass-through is correct (wr_seq.sv:297, 336). The write at 0x6000 len 1 has its address advanced to 0x6004 at the W capture (wr_seq.sv:344) before REQ (wr_seq.sv:294), so the APB writes go to 0x6004/0x6008. The test's own asserts at lines 1408-1415 passed; the failure is in b.score() at line 1416. |
| Test does | Line 1405 sends a 2-beat INCR write at 0x6000. b.score() → _score_one line 859 compares against beat_addrs(), which gives 0x6000 for k=0. |
| A_rtl_wrong | For: Same pre-advance bug as the other write failures. The PROT behaviour under test is correct.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The scoreboard implements the CHK-016 formula. |
| C_spec_unclear | For: OP-002 does not restate the address rule.<br>Against: CHK-016 is explicit. |
| Options | Fix RTL in wr_seq (line 344). No test change. |

## 11. test_chk_030_id_echo — CHK-016: paddr=0x00006800 for transfer 0 of write id=0 addr=0x6800 len=5 got 0x00006804

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:707 CHK-016 INCR addr_0=A, addr_k=(A&~(S-1))+k*S. spec:328 OP-002 "APB write per beat". spec:300 "ID ... Echo unchanged". |
| RTL does | The ID echo is correct (wr_seq.sv:290, 331). For the 6-beat INCR write at 0x6800, wr_seq.sv:344 advances reg_wr_addr on each W capture before the REQ state (wr_seq.sv:294, 306). Transfers 0..5 go to 0x6804..0x6818 instead of 0x6800..0x6814. The failure is raised from b.final() → _score_one line 859. |
| Test does | test_chk_030 (scored via b.final() at line 1458) sends writes at 0x6800 len 5, size 2, INCR. The scoreboard expects transfer 0 at beat_addrs()[0] = 0x6800. |
| A_rtl_wrong | For: Same +size pre-advance. The ID echo under test is not involved.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected address follows contract.json:707. |
| C_spec_unclear | For: OP-002 does not restate the address rule.<br>Against: CHK-016 is explicit. |
| Options | Fix RTL in wr_seq (line 344). No test change. |

## 12. test_chk_031_reset_mid_transaction — CHK-016: paddr=0x00007800 for transfer 0 of write id=6 addr=0x7800 len=0 got 0x00007804

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:707 CHK-016 INCR addr_0=A (a single-beat write: PADDR = AWADDR & ~3). spec:298 "APB PADDR clears bits [1:0]". spec:328 OP-002. |
| RTL does | After the reset (handled by wr_seq.sv:316-327), a single-beat INCR write at 0x7800 is accepted (wr_seq.sv:332). On its only W handshake, wr_seq.sv:344 sets reg_wr_addr to 0x7804, and that address is issued in REQ (wr_seq.sv:294). The reset behaviour is not involved: the failure comes from b.score() inside _tie_after_reset (test line 1480), on a completed, non-aborted transaction. |
| Test does | _tie_after_reset (called at line 1502) runs post-reset traffic including a single-beat write at 0x7800 (AxVALID handshake edge 3) and then scores it. _score_one line 859 expects 0x7800. |
| A_rtl_wrong | For: Even a single-beat write is issued one beat past AWADDR, which can only come from the pre-advance at wr_seq.sv:344.<br>Against: None found. Reset values and abort handling are not implicated. |
| B_test_wrong | For: Reset-related tracking could in principle mislabel transactions.<br>Against: The transaction was scored as non-aborted (aborted ones are skipped at test lines 822-827). Its handshake edge 3 is after the reset, and the address shift is the same as in tests with no reset. |
| C_spec_unclear | For: None material.<br>Against: CHK-016 is explicit, and a single-beat write's address is AWADDR & ~3 (spec:298). |
| Options | Fix RTL in wr_seq (line 344): advance the address only after the beat's APB request or response. No test change. Rerun to confirm the reset-specific checks still pass. |

