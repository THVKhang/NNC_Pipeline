# Specification gaps: axil_regfile

Agent A18 read only the specification and listed what it leaves open or states inconsistently ({'medium': 2, 'low': 3}; 0 without a valid line reference). Nothing was changed: answer each question or amend the specification before approving gate G1.

## GAP-001 [medium] reset_during_operation

**Scenario.** Cycle 1: AW transfer to 0x04 at edge 1, so the write address is held. Cycle 3: the manager never sends W, and the testbench asserts i_rst_n between edges. It releases i_rst_n so that R1 is edge 6. A reference model built literally from the 'held' definition still sees an AW transfer at e <= n-1 with no B transfer, so it keeps the address 'held' forever.

**The specification says.** spec/axil_regfile_Design_Specification.md:51 "a write address is held if its AW transfer happened at an edge e <= n-1 and the B transfer of its transaction has not happened at any edge <= n-1" (lines 52-53 are the same for W and AR). Line 169: "In every cycle in which a write address is held, `o_s_axi_awready` shall be 0." Line 143: "the held state shall be discarded. No B or R response shall be given for that transaction after release". Line 139: readies "shall be 1 from edge R1".

**Left open.** The definitions of held address/data never mention reset. Because RST-009 forbids any B after reset, an AW taken before reset stays 'held' forever under these definitions. REQ-WR-002/WR-004/RD-002 then require awready/wready/arready to be 0 after reset, while REQ-RST-007 requires 1. A related problem: 'after R1' in REQ-WR-001/WR-003/RD-001 does not say whether a later reset period counts. During a second reset those cycles are 'after R1' (the first one), and WR-001 would require ready = 1 there, against REQ-RST-001.

**Question.** Should the held-address/data definitions read 'and no reset assertion has happened since the transfer'? Does 'after R1' mean 'after the most recent R1 and while i_rst_n is 1'?

**Readings.**
- Reset ends the held state: the transfer is no longer held from the reset assertion on, and the readies are 1 from the new R1 (the evident intent of RST-007/RST-009).
- Literal definition: an AW/W/AR transfer whose B/R never comes stays held, so the readies stay 0 after reset. A model coded from line 51 would predict a deadlock.
- 'After R1' means after the first R1 ever, so WR-001 applies during later reset periods and conflicts with RST-001.

References: spec/axil_regfile_Design_Specification.md:51, spec/axil_regfile_Design_Specification.md:52, spec/axil_regfile_Design_Specification.md:53, spec/axil_regfile_Design_Specification.md:54, spec/axil_regfile_Design_Specification.md:127, spec/axil_regfile_Design_Specification.md:139, spec/axil_regfile_Design_Specification.md:143, spec/axil_regfile_Design_Specification.md:167, spec/axil_regfile_Design_Specification.md:169, spec/axil_regfile_Design_Specification.md:223 (10/10 checked)

## GAP-002 [medium] initial_state

**Scenario.** The simulation starts at time 0 with i_rst_n = 1, or with i_rst_n = X, for several cycles before the testbench first drives it to 0. The checker of REQ-VER-010 compares o_regs with the model in every cycle, and the protocol checker looks at bvalid/rvalid.

**The specification says.** spec/axil_regfile_Design_Specification.md:458 "shall not rely on initial values". Line 414: "The checker shall compare `o_regs` with the reference model in every cycle". Line 409: "The testbench shall drive defined values (no X or Z) on all inputs while `i_rst_n` is 1." Lines 167/223 tie the readies only to cycles 'after R1'.

**Left open.** Nothing says the environment must assert i_rst_n before the first transfer or from time 0. Nothing says what the outputs may be, or whether checkers are active, before the first reset. REQ-VER-010 ('every cycle') would fail on X in o_regs before the first reset. REQ-VER-005 seems to require a defined (non-X) i_rst_n, but it does not say that its first value must be 0.

**Question.** Must the environment hold i_rst_n at 0 from time 0 (and for how many edges at least)? Are all output checks, including REQ-VER-010, disabled until the first reset assertion?

**Readings.**
- The environment must start with i_rst_n = 0, and outputs before the first assertion are unspecified and not checked.
- The checkers run from time 0, so the RTL must somehow give defined outputs before the first reset (which conflicts with REQ-IMP-003).
- Valids may be driven before the first reset, and the block may take transfers in that window.

References: spec/axil_regfile_Design_Specification.md:405, spec/axil_regfile_Design_Specification.md:409, spec/axil_regfile_Design_Specification.md:414, spec/axil_regfile_Design_Specification.md:416, spec/axil_regfile_Design_Specification.md:458 (5/5 checked)

## GAP-003 [low] contradiction

**Scenario.** A write completes at Ec = edge 5 and its B transfer happens at Eb = edge 6. A checker reads REQ-WR-020 with the term definition of line 46 and expects bvalid = 1 in cycle 6 'and every later cycle'.

**The specification says.** spec/axil_regfile_Design_Specification.md:46 "'From edge n' means 'in cycle n+1 and every later cycle'." Line 205: "`o_s_axi_bvalid` shall be 1 from edge Ec". Line 209: "`o_s_axi_bvalid` shall be 0 from edge Eb". Line 139: readies "shall be 1 from edge R1". Line 169: awready 0 while held.

**Left open.** Read literally, 'from edge n' means forever after edge n. So REQ-WR-020 contradicts REQ-WR-022, REQ-RD-004 contradicts RD-006, and REQ-RST-007 contradicts WR-002/WR-004/RD-002. The intended meaning seems to be 'starting in cycle n+1, until another requirement changes it', but the defined term does not say so.

**Question.** Should 'from edge n' be redefined as 'starting in cycle n+1' (the start point only), with the end set by the matching 'shall be 0 from' or 'held' requirement?

**Readings.**
- 'From edge n' gives only the first cycle; other requirements decide how long the value lasts.
- 'From edge n' means for all later cycles, which makes the requirement pairs contradict each other.

References: spec/axil_regfile_Design_Specification.md:46, spec/axil_regfile_Design_Specification.md:139, spec/axil_regfile_Design_Specification.md:205, spec/axil_regfile_Design_Specification.md:209, spec/axil_regfile_Design_Specification.md:229, spec/axil_regfile_Design_Specification.md:233 (6/6 checked)

## GAP-004 [low] contradiction

**Scenario.** An RTL designer who reads Q-003 as still open builds the cheaper design with awready/wready/arready = 1 during reset. The testbench, written to REQ-RST-001/RST-006, flags ready = 1 while i_rst_n = 0.

**The specification says.** spec/axil_regfile_Design_Specification.md:472 D-001: "0 during reset and in the cycle that ends at R1; 1 from R1". Line 487 Q-003: "Should the readies be 0 during reset (D-001), or is a cheaper design with readies at 1 during reset wanted? | Open: 0 is assumed". Lines 127 and 137 state the requirement as fixed.

**Left open.** The same behaviour is recorded both as a decision (D-001, REQ-RST-001/006) and as an open question for the designer (Q-003). The readies during reset and in the cycle that ends at R1 may still change.

**Question.** Is D-001 final, so that Q-003 can be closed, or may RTL drive the readies to 1 during reset? If they may be 1, what stops a transfer at R1 (REQ-RST-005/006)?

**Readings.**
- The readies are 0 during reset and in the cycle that ends at R1 (D-001, binding).
- The readies may be 1 during reset (Q-003 still open). Transfers are then blocked only by the i_rst_n condition in the transfer definition, and REQ-RST-001/006 become wrong.

References: spec/axil_regfile_Design_Specification.md:127, spec/axil_regfile_Design_Specification.md:137, spec/axil_regfile_Design_Specification.md:472, spec/axil_regfile_Design_Specification.md:487 (4/4 checked)

## GAP-005 [low] reset_during_operation

**Scenario.** Cycle 2: the manager raises awvalid with awaddr = 0x08 while awready = 0, because a write address is already held. Cycle 3: i_rst_n is asserted. During reset the manager drops awvalid to 0. After R1 it raises awvalid again with a different address, 0x0C.

**The specification says.** spec/axil_regfile_Design_Specification.md:401 "the manager shall keep a valid at 1, and its payload stable, from the cycle it rises until the edge of its transfer." Line 372: dropping a valid or changing a payload before the transfer makes "the behaviour of the block ... not specified". Line 409: "During reset the valids may be 0 or 1." Line 145: a valid held through reset is "treated as a new transfer request".

**Left open.** Nothing says whether a reset releases the manager from the REQ-VER-001 obligation for a valid that rose before the reset. If it does not, dropping awvalid during reset, or changing awaddr after R1, is a handshake violation under REQ-ERR-010, and a protocol checker would flag the stimulus that REQ-VER-005/VER-040 allow.

**Question.** Does a reset assertion end the manager's valid/payload stability obligation for a request that rose before it, so that after R1 the valid and payload may be changed freely?

**Readings.**
- Reset cancels the obligation: valids and payloads may change during reset and after R1, and the block behaviour is fully specified.
- The obligation holds across reset: dropping or changing a pre-reset request is a manager violation (REQ-ERR-010), and the behaviour is unspecified.

References: spec/axil_regfile_Design_Specification.md:145, spec/axil_regfile_Design_Specification.md:372, spec/axil_regfile_Design_Specification.md:401, spec/axil_regfile_Design_Specification.md:409, spec/axil_regfile_Design_Specification.md:448 (5/5 checked)

Cost: US$0.51
