# Specification gaps: spi_master

Agent A18 read only the specification and listed what it leaves open or states inconsistently ({'medium': 2, 'low': 3}; 0 without a valid line reference). Nothing was changed: answer each question or amend the specification before approving gate G1.

## GAP-001 [medium] simultaneous_events

**Scenario.** The environment asserts i_rst_n (asynchronously) at the same instant as a rising edge of i_clk. At that edge one of three things would otherwise happen: (a) i_cmd_valid = 1 and o_cmd_ready = 1, so a command handshake; (b) o_rsp_valid = 1 and i_rsp_ready = 1, so a response handshake; (c) it is edge A + 16·D, where the received byte is loaded or held.

**The specification says.** Handshakes are defined only at "An edge at which `i_rst_n` = 1" (spec:48-49). Assertion "may be asynchronous" (ENV-001). On assertion, outputs take reset values "at once, without waiting for an edge" (REQ-RST-001). The reset tests only "assert `i_rst_n` between `i_clk` edges" (VER-007).

**Left open.** The text does not say what "`i_rst_n` = 1 at an edge" means when the falling edge of reset lines up with the clock edge. So it does not decide whether that command counts as accepted, or whether that response counts as delivered. If the response counts as delivered, the scoreboard must expect it; if not, REQ-RST-009 discards it. This also matters for the AXI-Stream view of the consumer, which saw valid & ready high at that edge.

**Question.** If reset assertion coincides with an i_clk edge, does that edge count as an edge with i_rst_n = 1 (handshake happens, so the response counts as delivered and the command as accepted), or with i_rst_n = 0? Or is this case excluded by an environment obligation (a minimum distance between reset assertion and the clock edge)?

**Readings.**
- The edge counts as a reset edge: no command is accepted, the shown byte is discarded, and the scoreboard expects no response.
- The handshake completes at that edge and reset takes effect right after it: the response counts as delivered and the command is accepted and then aborted with no response.
- The case is illegal or untested: the environment must keep reset assertion away from clock edges, and checkers ignore it.

References: spec/spi_master_Design_Specification.md:48, spec/spi_master_Design_Specification.md:49, spec/spi_master_Design_Specification.md:113, spec/spi_master_Design_Specification.md:129, spec/spi_master_Design_Specification.md:444, spec/spi_master_Design_Specification.md:472 (6/6 checked)

## GAP-002 [medium] initial_state

**Scenario.** Simulation starts, or the device powers up, with i_rst_n = 1 and no reset pulse, or with the first reset coming only after some i_clk edges. During this time i_cpol may also be X/Z while o_sclk follows it combinationally.

**The specification says.** The port table gives reset values (spec:85-97). REQ-RST-001 to REQ-RST-006 define outputs only "While `i_rst_n` = 0". The environment duties are ENV-001 (synchronous release) and ENV-002 (i_cmd_valid = 0 during reset). i_cpol has reset value "Not applicable" and o_sclk "follows it combinationally" during reset (REQ-RST-003).

**Left open.** No requirement says the environment must apply reset before the first edge or before the first command. Nothing says what outputs (o_cs_n, o_cmd_ready, o_rsp_valid) may show before the first reset, or whether checkers must be disabled until then. No requirement says i_cpol must be at a known level during reset or Idle, even though o_sclk shows it directly.

**Question.** Is the environment required to assert i_rst_n at power-up before any command, and are outputs undefined (and checks off) before the first reset? Must i_cpol and i_cpha be driven to known levels at all times while o_cs_n = 1?

**Readings.**
- Outputs are undefined before the first reset. The testbench must reset first, and assertions are gated until the first reset release.
- Outputs must already show reset values at time zero (initialised flops), and checkers run from time zero.
- i_cpol may be X during reset or Idle, and an X on o_sclk is acceptable.
- i_cpol must always be 0 or 1. This is an unstated ENV obligation.

References: spec/spi_master_Design_Specification.md:85, spec/spi_master_Design_Specification.md:92, spec/spi_master_Design_Specification.md:96, spec/spi_master_Design_Specification.md:113, spec/spi_master_Design_Specification.md:117, spec/spi_master_Design_Specification.md:444, spec/spi_master_Design_Specification.md:446 (7/7 checked)

## GAP-003 [low] other

**Scenario.** A verification engineer writes the reset tests of VER-007, including "with a held byte", and must decide how to drive i_rsp_ready before, during and after the reset.

**The specification says.** VER-007: "Reset tests shall assert `i_rsp_ready` … shall assert `i_rst_n` between `i_clk` edges in each phase (Transfer, Pause, Trail, Idle gap, with a held byte)."

**Left open.** The sentence is garbled: part of the requirement is missing after "assert `i_rsp_ready`". It is unclear whether i_rsp_ready must be held at 0 (needed to create a held byte), held at 1, randomised, or asserted after reset release to check that no response of the aborted transfer appears.

**Question.** What is the complete text of VER-007's requirement on i_rsp_ready in reset tests?

**Readings.**
- Hold i_rsp_ready = 0 before reset so that a shown or held byte exists, then assert reset.
- Assert i_rsp_ready = 1 during and after reset to show that no stale response comes out.
- The fragment is a leftover and there is no requirement on i_rsp_ready.

References: spec/spi_master_Design_Specification.md:472 (1/1 checked)

## GAP-004 [low] contradiction

**Scenario.** The testbench connects a standard AXI4-Stream protocol checker to the command stream (i_cmd_valid/o_cmd_ready/i_cmd_data/i_cmd_last). The stimulus drops i_cmd_valid, or changes i_cmd_data, before a handshake.

**The specification says.** REF-002 (AXI4-Stream) is cited for "Valid/ready handshake meaning only (TVALID/TREADY rules)". Separately, spec:456 says: "The command stream is not required to keep `i_cmd_valid`, `i_cmd_data` or `i_cmd_last` stable before acceptance (REQ-CMD-004)."

**Left open.** The AXI4-Stream TVALID/TREADY rules include the rule that once TVALID is asserted it must stay asserted, with stable data, until the handshake. The spec cites those rules and also waives this one. It is not stated which AXI rules apply to the command stream and which to the response stream. For example, it is not stated whether the master's o_rsp_valid must follow the stability rule (REQ-RSP-007 suggests yes) while the command stream need not.

**Question.** Which REF-002 rules apply to each stream? Is the TVALID-stability rule explicitly waived for the command stream only?

**Readings.**
- Full AXI4-Stream rules apply to both streams, so the stimulus must not withdraw i_cmd_valid. Spec:456 is then wrong.
- AXI4-Stream applies only to the handshake definition, the command stream may withdraw valid, and AXI checkers must have the stability assertion turned off for commands.

References: spec/spi_master_Design_Specification.md:37, spec/spi_master_Design_Specification.md:169, spec/spi_master_Design_Specification.md:456 (3/3 checked)

## GAP-005 [low] contradiction

**Scenario.** D = 1. The last byte of a burst is shown at edge A + 16 and o_cs_n rises at R = A + 17. i_rsp_ready = 0, so o_rsp_valid stays 1 in cycle R.

**The specification says.** The corner-case table says: "D = 1 … `o_cmd_ready` in Idle is 1 from the cycle in which `o_cs_n` rises (REQ-CMD-007 gives no blocked cycle)." REQ-CMD-006 says o_cmd_ready = 0 whenever o_rsp_valid = 1, and the Idle row of the phase table says "otherwise NOT `o_rsp_valid`".

**Left open.** The corner-case row states that o_cmd_ready = 1 with no condition on o_rsp_valid, but the normative requirements make it depend on o_rsp_valid. A reader working from the table could expect ready = 1 at R even while a response is pending.

**Question.** Should the D = 1 corner-case row say "1 from the cycle in which o_cs_n rises, if o_rsp_valid = 0"?

**Readings.**
- REQ-CMD-006/008 win: ready = NOT o_rsp_valid from cycle R.
- The table is literal: ready = 1 from R whatever o_rsp_valid is (this would contradict REQ-CMD-006).

References: spec/spi_master_Design_Specification.md:144, spec/spi_master_Design_Specification.md:173, spec/spi_master_Design_Specification.md:177, spec/spi_master_Design_Specification.md:426 (4/4 checked)

Cost: US$0.71
