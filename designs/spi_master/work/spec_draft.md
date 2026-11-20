# Specification draft: spi_master

Agent A0 (opus, spec-v1) wrote `spec/spi_master_Design_Specification.md` from the designer's description in 1 attempt(s), cost US$1.08.

**This is a proposal.** Read it, correct it, and answer the open questions in the text before running the flow: the verification and the RTL are generated from this text only. Gate G1 records its hash.

Shape check: 28 sections, 15 ports, 1 parameters, 97 requirement IDs, 145 normative sentences.

## Assumptions A0 made (the description did not say)

- i_rst_n is asserted asynchronously and released synchronously to i_clk. The environment provides the release synchroniser.
- The environment keeps i_cmd_valid = 0 during reset. o_cmd_ready = 1 during reset (as the description says) does not make a handshake, and no command is accepted while i_rst_n = 0.
- The description says 'at least one half period'. The spec fixes the CS lead and trail at exactly D cycles and makes the gap between bursts at least D cycles (exactly D when the next command is waiting), so the verification is deterministic.
- A command is accepted at edge A. SCLK edges come at A + k*D for k = 1..16, so the first edge comes D cycles after o_cs_n falls. In a continuous burst the next command is accepted exactly at SCLK edge 16 of the previous byte.
- o_cmd_ready is a function of state only, with no combinational path from any input. It is 1 only in Idle (after D-1 blocked cycles following the o_cs_n rise), in Pause, or in the last cycle of a non-last transfer, and always only when o_rsp_valid = 0.
- Reading of the no-loss rule: a new transfer starts only when o_rsp_valid = 0. The byte finishing at the same edge is shown. If it is still not taken when the next transfer ends, that next byte is held inside the master (at most one held byte) and no further transfer starts.
- The received byte is put on the response stream at SCLK edge 16 (A + 16*D) in all modes, even though with CPHA = 0 the last bit is sampled at edge 15.
- With CPHA = 0, MOSI bit 7 is launched at the acceptance edge (the CS fall, or SCLK edge 16 of the previous byte). With CPHA = 1 it is launched at SCLK edge 1. MOSI never changes at a sampling edge and holds its last value in Idle, Pause and Trail.
- While o_cs_n = 1 (including reset), o_sclk follows i_cpol combinationally. While o_cs_n = 0, it comes from the CPOL value captured at burst start.
- i_cpol and i_cpha are captured at the acceptance edge of the first command of a burst. Changes during a burst are ignored and not reported.
- i_miso is sampled directly at the i_clk edge where o_sclk makes the sampling transition. The value captured is the one in the cycle just before that edge.
- Reset during a burst aborts it at once. The partial byte, the shown byte and any held byte are discarded. The minimum CS gap is not guaranteed across a reset.
- o_rsp_data is 8'h00 after reset and keeps the last loaded byte while o_rsp_valid = 0.
- The command source may withdraw i_cmd_valid before acceptance. Only the values at the handshake edge matter.
- Pause has no timeout: o_cs_n stays low until the next command arrives.
- An illegal PARA_SPI_CLK_DIV (outside 1 to 255) causes an elaboration error.
- CFG-MAX (PARA_SPI_CLK_DIV = 255) was added to the run set as the upper parameter extreme, besides the default and minimum dividers the designer asked for.
- In the port table, i_cmd_valid has reset value 0 (an environment obligation), following the template example. The other inputs have 'Not applicable'.

## Open questions for the designer

- OQ-001: Should a transfer be allowed to start in the last cycle when the shown response is taken in that same cycle? This needs a combinational path from i_rsp_ready to o_cmd_ready and would avoid a pause. Interim: no.
- OQ-002: Is D = 1 (25 MHz SCLK at 50 MHz i_clk) meant for real slaves, given the one-cycle (20 ns) MISO round-trip budget? Interim: legal and verified in simulation; silicon timing is the integrator's job.
- OQ-003: Should o_mosi be driven to a fixed level (0) in Idle instead of holding its last value? Interim: hold.
- OQ-004: What is the area budget on GF180MCU?
- OQ-005: Should Pause have a timeout that releases o_cs_n when no command arrives? Interim: no timeout.
- OQ-006: Should the master guarantee that o_cs_n stays high for at least D cycles after reset release before the next burst? Interim: no.
- OQ-007: Should CFG-MAX (D = 255) stay in the run set, given the longer simulation time? Interim: kept.
