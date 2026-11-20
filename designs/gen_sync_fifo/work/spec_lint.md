# Specification gaps: gen_sync_fifo

Agent A18 read only the specification and listed what it leaves open or states inconsistently ({'high': 4, 'medium': 7, 'low': 1}; 0 without a valid line reference). Nothing was changed: answer each question or amend the specification before approving gate G1.

## GAP-001 [high] contradiction

**Scenario.** Write domain, PTR_RETIME any. The controller drives i_rst_n_sw = 0 for exactly one write cycle N (sampled at edge E_N). In cycle N+1 i_rst_n_sw = 1 and the writer drives i_wr_en = 1 with the FIFO not full. Later, the write FSM moves from REL to RUN at edge E_k and the writer drives i_wr_en = 1 in the cycle after E_k.

**The specification says.** REQ-SRST-006: "o_sw_rst_busy ... shall be 1 from the cycle after the write FSM takes the request until the cycle in which the write FSM is back in RUN." FSM table: ENUM_ST_REQ "o_sw_rst_busy 1", ENUM_ST_RUN "o_sw_rst_busy 0". 10.7: "The write FSM leaves RUN, o_sw_rst_busy rises in the next cycle". SVA-010: "o_sw_rst_busy is 1 exactly while the write FSM is not in RUN (one cycle behind the state)". Write block = "o_sw_rst_busy flop OR i_rst_n_sw = 0".

**Left open.** It is not stated whether busy is loaded from the next state (so it is 1 in the first REQ cycle and 0 in the first RUN cycle) or is a register of the current state (so it lags the state by one cycle). With the lagging version, block is 0 in cycle N+1 after a one-cycle pulse, so a write is accepted during REQ. That word is then silently discarded when PTR resets the pointer. Also with the lagging version, writes stay blocked for one extra cycle after RUN. The table-driven RTL and SVA-010 would disagree on both edges.

**Question.** Is o_sw_rst_busy loaded at the same edge as the FSM's transition (1 in every non-RUN cycle, 0 in the first RUN cycle), or one cycle after the state? If it lags, must a write in the cycle right after a one-cycle i_rst_n_sw pulse be blocked by some other term?

**Readings.**
- busy = registered (next_state != RUN): rises at E_N together with the REQ entry and falls at E_k together with the RUN entry, so the write in cycle N+1 is blocked
- busy = registered (current_state != RUN), one cycle behind the state as SVA-010 says: the write in cycle N+1 is accepted and then discarded, and writes stay blocked for one cycle after RUN
- busy rises one cycle after the REQ entry but falls with the RUN entry (the literal reading of REQ-SRST-006), which is asymmetric

References: spec/SyncFIFO_Design_Specification.md:154, spec/SyncFIFO_Design_Specification.md:388, spec/SyncFIFO_Design_Specification.md:389, spec/SyncFIFO_Design_Specification.md:392, spec/SyncFIFO_Design_Specification.md:527, spec/SyncFIFO_Design_Specification.md:560, spec/SyncFIFO_Design_Specification.md:563, spec/SyncFIFO_Design_Specification.md:639, spec/SyncFIFO_Design_Specification.md:734 (9/9 checked)

## GAP-002 [high] request_while_busy

**Scenario.** The controller gives a one-cycle low pulse on i_rst_n_sw that starts a sequence. It then gives a second one-cycle low pulse while the write FSM is in REQ or PTR, or in REL, and drives i_rst_n_sw = 1 before the FSM returns to RUN.

**The specification says.** REQ-SRST-008: "A request that arrives while a sequence is running (a low pulse in REL, or a second pulse) shall be served as a new sequence when the write FSM is back in RUN." 10.7: "A new low level during REL is served after the write FSM is back in RUN." FSM table: RUN exits on "i_rst_n_sw = 0: REQ"; HOLD exits on "i_rst_n_sw = 1". The write block state list (busy, request, FSM, pointer, flags) has no pending-request flop.

**Left open.** RUN only looks at the current level of i_rst_n_sw, so a short pulse that ends before RUN is lost unless a pending flop latches it. No such flop is listed. It is also open whether a pulse during REQ or PTR is merged into the current sequence (whose HOLD has already ended or not) or queued as a second full sequence.

**Question.** Must the write side latch a low pulse of i_rst_n_sw that arrives in REQ, PTR or REL and start a new sequence after RUN even if i_rst_n_sw is back at 1? Is a pulse in REQ or PTR merged with the current sequence or served as a second sequence?

**Readings.**
- A pending flop latches any low sample outside RUN, and exactly one extra sequence runs after RUN
- Only a level still low when the FSM reaches RUN is served (as 10.7 says for REL); short pulses are lost
- A pulse in REQ or PTR is merged into the running sequence; only a pulse in REL is queued

References: spec/SyncFIFO_Design_Specification.md:156, spec/SyncFIFO_Design_Specification.md:191, spec/SyncFIFO_Design_Specification.md:388, spec/SyncFIFO_Design_Specification.md:391, spec/SyncFIFO_Design_Specification.md:392, spec/SyncFIFO_Design_Specification.md:565, spec/SyncFIFO_Design_Specification.md:710 (7/7 checked)

## GAP-003 [high] contradiction

**Scenario.** PTR_RETIME = 0, read clock 8 ns, write clock 12 ns, with an offset. The write FSM raises the request flop at write edge t = 0. The next read edge is at t = 2 ns. A reader samples o_empty as if it changed only at read edges.

**The specification says.** Read block = "request seen on the read side (directly or through the retiming flop) OR read FSM not in RUN"; o_empty = "block OR empty flop". o_empty port: "Changes at a rising edge of i_clk_rd, except that the block term follows the request of the write side with no clock delay". Invariant 5.4: "Pointers and flags change only at a rising edge of the clock of their own domain." REQ-SRST-003: "When the request reaches the read side, reads shall be blocked". DEC-017: the handshake follows PTR_RETIME.

**Left open.** With PTR_RETIME = 0, the read block term is a write-domain flop, so o_empty and o_empty_thr toggle at a write-clock edge. That breaks the invariant and the rule that IF-002 outputs are timed to CLK-RD. With PTR_RETIME = 1, the port text's "no clock delay" contradicts the retiming flop. It is not decided whether "request seen" means the raw cross-domain request or a version registered in the read domain. That choice decides when reads become blocked, and which reads (and underflow pulses) in the window are legal.

**Question.** On the read side, is the block term taken from i_req_wr combinationally (o_empty may change at a write edge), or only from a read-domain flop (registered at the first strictly later read edge)? Which read edge is the first one at which reads are blocked?

**Readings.**
- Combinational from i_req_wr (PTR_RETIME 0): o_empty rises at the write edge, between read edges
- Block uses only read-domain state (the read FSM or a request register), so o_empty changes only at read edges and the invariant holds
- PTR_RETIME 0 is combinational and PTR_RETIME 1 is via the retiming flop, and the invariant in 5.4 is simply wrong for the block term

References: spec/SyncFIFO_Design_Specification.md:151, spec/SyncFIFO_Design_Specification.md:216, spec/SyncFIFO_Design_Specification.md:252, spec/SyncFIFO_Design_Specification.md:253, spec/SyncFIFO_Design_Specification.md:542, spec/SyncFIFO_Design_Specification.md:549, spec/SyncFIFO_Design_Specification.md:786, spec/SyncFIFO_Design_Specification.md:901 (8/8 checked)

## GAP-007 [high] back_pressure

**Scenario.** PTR_RETIME = 0, depth 4, clock ratio 11:13 (not among the 14 ratios swept). i_wr_en and i_rd_en are held at 1. The non-limited side stalls once after the initial latency.

**The specification says.** REQ-PERF-002: "there shall be only the initial latency and no gap ... This is guaranteed when the depth is at least 4 + 2 x PARA_SFIFO_PTR_RETIME." REQ-CLK-001: correct "for every such ratio". 10.4: "It is a measured sufficient condition on the prototype, not a proof for every ratio." PERF-002 marked "Hard". OI-002 open.

**Left open.** A hard "shall" for all ratios rests on a rule the spec itself says is only measured on 14 ratios. "Gap" for the faster side is defined only as "held back ... only because of the rate difference", with no measurable criterion. A test at an untested ratio cannot tell a spec violation from an expected limit.

**Question.** Is REQ-PERF-002 a pass/fail requirement for every rational ratio, or only for the listed ratios? What exact rule (for example, the number of accepted transfers per LCM period) decides that the faster side was held back "only because of the rate difference"?

**Readings.**
- Hard for all ratios: a gap at any ratio with depth ≥ 4+2R is an RTL bug
- Hard only for the 14 swept ratios; other ratios are informative
- Goal only until OI-002 is closed

References: spec/SyncFIFO_Design_Specification.md:144, spec/SyncFIFO_Design_Specification.md:159, spec/SyncFIFO_Design_Specification.md:508, spec/SyncFIFO_Design_Specification.md:599, spec/SyncFIFO_Design_Specification.md:874, spec/SyncFIFO_Design_Specification.md:907 (6/6 checked)

## GAP-004 [medium] contradiction

**Scenario.** Structural check TEST-014 on the netlist of m_vlsit_sfifo_wr and m_vlsit_sfifo_rd: it traces the logic between the flag flops and the ports o_full_thr and o_empty.

**The specification says.** REQ-IF-002: o_full, o_full_thr, o_empty, o_empty_thr "shall be combined with the software reset block term by one gate ... No other logic shall exist between these flip-flops and the ports." 10.6: "o_full_thr | if block: (i_full_thr equals 0), otherwise the full-threshold flop"; read block = "request seen ... OR read FSM not in RUN"; write block = "o_sw_rst_busy flop OR i_rst_n_sw = 0".

**Left open.** o_full_thr needs a multi-bit compare of i_full_thr against 0 plus a mux, which is not one gate. The read block needs a decode of the FSM state plus an OR with the request, and the write block needs an inverter and an OR. It is unclear whether the "one gate" rule counts the logic that builds the block term, so a strict structural check would fail RTL that follows 10.6.

**Question.** Does "one gate" mean one final gate after a block term (which may itself be any logic), or must the block term be a single flop or signal? How must o_full_thr = (i_full_thr == 0) during block be built to comply?

**Readings.**
- One final AND/OR/mux after a block signal; the logic that forms the block (decode, compare) is allowed
- The block term must be a single net (for example a registered block flop), and the i_full_thr == 0 compare must be precomputed or registered
- The rule applies only to o_full and o_empty, and the threshold flags are exempt

References: spec/SyncFIFO_Design_Specification.md:142, spec/SyncFIFO_Design_Specification.md:245, spec/SyncFIFO_Design_Specification.md:527, spec/SyncFIFO_Design_Specification.md:535, spec/SyncFIFO_Design_Specification.md:542, spec/SyncFIFO_Design_Specification.md:785, spec/SyncFIFO_Design_Specification.md:714 (7/7 checked)

## GAP-005 [medium] initial_state

**Scenario.** Both hardware resets are asserted while the controller drives i_rst_n_sw = 0 (or X before its own reset), and i_rst_n_sw is still 0 at the write-reset release edge.

**The specification says.** REQ-RESET-001: "While asserted, every flip-flop of the domain shall be at its reset value: ... o_full 0". o_full = "block OR full flop", where block = "o_sw_rst_busy flop OR i_rst_n_sw = 0". i_rst_n_sw idle value "1". REQ-SRST-007: hardware reset has priority over a software reset.

**Left open.** If i_rst_n_sw = 0 during the hardware reset, o_full = 1 and o_full_thr = (i_full_thr == 0), against the stated reset value of o_full 0. It is not said whether i_rst_n_sw must be 1 during reset, or whether the hardware reset must also mask the combinational block. It is also open whether a low level held across the release starts a sequence at the first edge, or must be gated until both resets are released.

**Question.** Must the environment hold i_rst_n_sw = 1 during the hardware reset? If not, is o_full allowed to be 1 during reset, and does a low level at the release start a software-reset sequence immediately?

**Readings.**
- Environment constraint: i_rst_n_sw = 1 during reset; the reset value o_full = 0 then holds
- o_full = 1 during reset is allowed when i_rst_n_sw = 0 (block is combinational); a sequence starts at the first edge after release
- The hardware reset masks the block term, so o_full = 0 during reset regardless of i_rst_n_sw

References: spec/SyncFIFO_Design_Specification.md:147, spec/SyncFIFO_Design_Specification.md:155, spec/SyncFIFO_Design_Specification.md:242, spec/SyncFIFO_Design_Specification.md:244, spec/SyncFIFO_Design_Specification.md:331, spec/SyncFIFO_Design_Specification.md:527, spec/SyncFIFO_Design_Specification.md:534 (7/7 checked)

## GAP-006 [medium] reset_during_operation

**Scenario.** The FIFO holds 3 words. Only i_rst_n_wr is asserted (or the two resets are released several cycles apart, and the writer writes after its own release while i_rst_n_rd is still low). TEST-010/COV-006 apply a hardware reset in each FSM state.

**The specification says.** REQ-RESET-002: "The two resets shall be asserted together. No operation shall start before both resets are released." REQ-RESET-001: "While asserted, every flip-flop of the domain shall be at its reset value: ... both reset FSMs in RUN". REQ-SRST-007: "A hardware reset ... shall bring both FSMs to RUN." TEST-010: "hardware reset in every state of the sequence".

**Left open.** Each reset clears only its own domain, yet the text says one domain's reset puts both FSMs in RUN. With a write-only reset the write pointer goes to 0 while the read pointer does not, so the occupancy is wrong and stale words get read. It is not said whether a single-domain reset is illegal stimulus or must be handled. It is also not said whether "no operation before both are released" is enforced by the IP or is an environment assumption that TEST-001 merely respects. "Together" is not defined for asynchronous assertion on two clocks.

**Question.** Is asserting only one hardware reset legal? If so, what must the other domain do. If not, should TEST-010 always assert both? Must the IP block writes or reads until both resets are released, or is that purely the environment's duty?

**Readings.**
- Single-domain reset is illegal; TEST-010 asserts both; the IP need not handle it
- Single-domain reset is legal, and the IP must cross-reset or flush the other side (for example by forcing a software-reset-like sequence)
- The IP gates acceptance until both resets are released, which is checked by TEST-001
- Environment-only constraint; behaviour is undefined if violated

References: spec/SyncFIFO_Design_Specification.md:147, spec/SyncFIFO_Design_Specification.md:148, spec/SyncFIFO_Design_Specification.md:155, spec/SyncFIFO_Design_Specification.md:335, spec/SyncFIFO_Design_Specification.md:701, spec/SyncFIFO_Design_Specification.md:710, spec/SyncFIFO_Design_Specification.md:741, spec/SyncFIFO_Design_Specification.md:882 (8/8 checked)

## GAP-008 [medium] contradiction

**Scenario.** PTR_RETIME = 0. The FIFO holds one visible word. The writer stores a second word at write edge E_w, which coincides with read edge E_r where the reader takes the first word.

**The specification says.** REQ-FUNC-002: "After an accepted read, o_rd_data shall show the next word (show-ahead) without a bubble when another word is stored." 6.3: "o_rd_data shows the next word in the next cycle, with no bubble, if another word is visible." 10.3: a coincident edge does not count as strictly later.

**Left open.** The two texts differ: "stored" requires no bubble even when the second word is not yet visible to the read side, while "visible" allows o_empty to rise for a cycle. A scoreboard checker written from REQ-FUNC-002 flags a bubble that the look-ahead design (DEC-013) necessarily produces.

**Question.** Is the show-ahead no-bubble guarantee conditioned on the next word being stored, or visible in the read view at the read edge?

**Readings.**
- "Visible": a bubble (o_empty = 1 for a cycle) is legal when the next word was written at the same or a later edge
- "Stored": no bubble whenever the word exists, which would require a bypass the architecture does not have

References: spec/SyncFIFO_Design_Specification.md:132, spec/SyncFIFO_Design_Specification.md:278, spec/SyncFIFO_Design_Specification.md:483 (3/3 checked)

## GAP-009 [medium] simultaneous_events

**Scenario.** CFG-MACRO, PTR_RETIME = 0, write clock 12 ns, read clock 8 ns with a 2 ns offset. A write into an empty FIFO at E_w; the read port samples the same address at E_r1 = E_w + 2 ns, and o_rd_data must show the new word after E_r1.

**The specification says.** REQ-PERF-003: "o_empty shall fall after the first rising edge of i_clk_rd that is strictly later than the write edge ... o_rd_data shall show the new word at that moment." 10.5: "A read of the address that is written at the same edge returns the old word ... Reading the old word during a collision is part of the contract of the memory model". REQ-RTL-002: the SRAM "shall behave like the array branch".

**Left open.** "Collision" is defined only for the same edge. The required write-to-read separation is not stated: with a real two-clock SRAM, a read edge very shortly after the write edge may return old or undefined data. Yet REQ-PERF-003 demands the new word at E_r1. It is open whether the macro branch must meet this exactly or may need an extra read edge.

**Question.** What minimum separation between a write edge and a later read edge must the memory (array and macro) support to return the new word? Is REQ-PERF-003's latency binding for CFG-MACRO at every ratio and phase?

**Readings.**
- Any strictly later read edge returns the new word (an ideal model); the macro must meet it via STA
- Only a separation of at least the macro's write-to-read time is guaranteed; otherwise the latency is one read edge more, or PTR_RETIME = 1 is required

References: spec/SyncFIFO_Design_Specification.md:160, spec/SyncFIFO_Design_Specification.md:164, spec/SyncFIFO_Design_Specification.md:517, spec/SyncFIFO_Design_Specification.md:663, spec/SyncFIFO_Design_Specification.md:712, spec/SyncFIFO_Design_Specification.md:906 (6/6 checked)

## GAP-010 [medium] parameter_extremes

**Scenario.** Equal clock frequencies with a small fixed phase offset (for example, read edge 0.1 ns after the write edge), or nominally coincident edges with clock skew in gate-level simulation or silicon. PTR_RETIME = 0 and 1.

**The specification says.** 10.3: "When the two edges coincide ... the edge that coincides does not count as 'strictly later'". REQ-CLK-001: any rational ratio, fixed phase. 17.1.2: "When the clock ratio makes the interval between a launch edge and a capture edge very small, PARA_SFIFO_PTR_RETIME = 1 shall be used or the ratio changed." Crossing path with PTR_RETIME 1: "flop to flop only", still single-cycle.

**Left open.** No minimum launch-to-capture interval or phase offset is defined. Coincident and strictly later are separated only by an ideal zero. With PTR_RETIME = 1 the crossing is still a single-cycle path over the same tiny interval, so the stated remedy does not remove the constraint. The legal phase relation, and the latency REQ-PERF-003 expects under skew, are therefore undefined.

**Question.** Is there a minimum non-zero interval between a launch edge of one clock and the next capture edge of the other? How should a test choose the expected latency when edges are nominally coincident but skewed?

**Readings.**
- Edges are either exactly coincident (in phase) or separated by at least one path delay; the integrator guarantees this
- Any offset is legal, and closing timing is entirely the integrator's job (PTR_RETIME 1 does not change the interval)
- Equal-frequency clocks must be in phase; offsets are only allowed between different frequencies

References: spec/SyncFIFO_Design_Specification.md:144, spec/SyncFIFO_Design_Specification.md:483, spec/SyncFIFO_Design_Specification.md:788, spec/SyncFIFO_Design_Specification.md:790, spec/SyncFIFO_Design_Specification.md:798 (5/5 checked)

## GAP-011 [medium] other

**Scenario.** The integrator changes i_full_thr from 6 to 3 while the FIFO is empty and idle, or while o_sw_rst_busy = 1, and then checks o_full_thr in the following cycles.

**The specification says.** Ports: "set before use and not changed while the FIFO is in use". 6.3 table: "The flag may take a wrong value for some cycles". ERR-004: "Not detected; behavior not specified". EXC-001: false path on the threshold ports.

**Left open.** "In use" is undefined: whether a change is legal under hardware reset only, during a software reset, or when the FIFO is idle. The two texts also differ on the consequence: "wrong for some cycles" (bounded, self-correcting) versus "behavior not specified". Tests cannot tell whether to check o_full_thr after a change, or after how many cycles.

**Question.** When may i_full_thr and i_empty_thr legally change (only in hardware reset, during a software reset, or when idle), and after how many edges must the threshold flags be correct again?

**Readings.**
- Only during the hardware reset; any other change gives unspecified behaviour
- Allowed at any time; the flag is correct from a bounded number of edges later (for example, 2 edges)
- Allowed while o_sw_rst_busy = 1 or the FIFO is idle

References: spec/SyncFIFO_Design_Specification.md:137, spec/SyncFIFO_Design_Specification.md:241, spec/SyncFIFO_Design_Specification.md:290, spec/SyncFIFO_Design_Specification.md:590, spec/SyncFIFO_Design_Specification.md:796 (5/5 checked)

## GAP-012 [low] other

**Scenario.** The controller asserts i_rst_n_sw = 0 and then releases it to 1 while o_sw_rst_busy is still 1, and the writer drives i_wr_en = 1.

**The specification says.** ASM-004: "The controller holds off writes while o_sw_rst_busy is 1 and i_rst_n_sw is 0". REQ-SRST-006: "The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1." REQ-SRST-002: writes blocked until busy is 0, and blocked writes are dropped without o_overflow.

**Left open.** ASM-004 uses AND where the complement of REQ-SRST-006 is OR. It is unclear whether writes issued while busy = 1 and i_rst_n_sw = 1 are an environment violation (a checker error) or a legal request that is silently dropped.

**Question.** Should ASM-004 read "busy is 1 or i_rst_n_sw is 0"? Is a write request during the block an assumption violation or a legal, silently dropped request?

**Readings.**
- OR: any request during the block violates the environment assumption
- The request is legal and dropped without a pulse (ERR-003); ASM-004 is informative only

References: spec/SyncFIFO_Design_Specification.md:150, spec/SyncFIFO_Design_Specification.md:154, spec/SyncFIFO_Design_Specification.md:589, spec/SyncFIFO_Design_Specification.md:884 (4/4 checked)

Cost: US$0.97
