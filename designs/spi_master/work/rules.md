# Rules for review (Gate 1)

```
rules in 226: kept 206 (fixed 18), merged 6, rejected 14, unreviewed 0; open questions 3 (raised 27, answered from the documents 24, duplicates 0)
calls: 14 (0 from cache)  cost US$0.6815
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.

## Open questions (the designer decides: `nnc answer <design> <n> "<decision>" --by <name>`)

1. Do CFG-MIN and CFG-MAX also require full-length bursts, or only the short bursts stated for CFG-MAX? (SPI-11-02, SPI-11-03) — *The documents do not say whether CFG-MIN or CFG-MAX must run full-length bursts. VER-002 sets burst lengths 1, 2 and at least 16 without tying them to a configuration. CFG-MAX is said to use 'short bursts' with no definition of short. CFG-MIN has no burst-length restriction. The designer must decide the burst lengths per configuration.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-19T07:13:19+00:00): CFG-BASE and CFG-MIN run every burst length of VER-002 (1, 2 and at least 16). CFG-MAX runs bursts of 1 and 2 bytes only ('short' = at most 2 bytes) to bound simulation time; 16-byte bursts are covered in CFG-BASE and CFG-MIN. Tests read the parameter to choose.
2. ENV-007 says reset assertion happens between i_clk edges, but SPI-12-02 allows asynchronous assertion and VER-007 requires asserting between edges; how should simulation drive assertion between edges? (SPI-12-02, SPI-12-10, SPI-12-26) — *The documents give no testbench mechanism or offset for driving assertion between i_clk edges. ENV-001 allows asynchronous assertion, ENV-007 forbids assertion at an edge, and VER-007 requires assertion between edges. These are consistent, but the exact time offset in simulation is left to the designer.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-19T07:13:20+00:00): Simulation asserts and releases i_rst_n at a falling edge of i_clk: half a period from every rising edge, so assertion is between edges (ENV-007, VER-007) and release is synchronous and stable before the next rising edge (ENV-001).
3. Which worst-case corner (PVT) is meant for timing closure? (SPI-13-01) — *Only 'worst-case corner' in GF180MCU at 50 MHz is stated. The specific PVT (process, voltage, temperature) corner is not given and must be chosen by the designer.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-19T07:13:20+00:00): The slow corner used by the flow: GF180MCU 7-track ss, 125 C, 4.50 V (gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50). The flow reports an ABC delay estimate at that corner; signoff STA is out of scope.

## Questions answered by the documents

- Exact lead time, trail time and minimum CS high time in half periods are not given; what values are required? → Lead = exactly D cycles (one half period) from o_cs_n fall to SCLK edge 1. Trail = exactly D cycles from SCLK edge 16 to o_cs_n rise. Minimum o_cs_n high time between bursts = at least D cycles (exactly D when the next command is waiting). [14:s1, 7.2:s5, 7.2:s6, 7.2:s7, 8:s6]
- Does i_cpol/i_cpha capture at burst start mean changes mid-burst are ignored, and what is the exact capture cycle relative to CS assertion? → Yes. CPOL_b/CPHA_b are captured at the acceptance edge of the first command of a burst, which is the same edge A at which o_cs_n falls. Later changes of i_cpol/i_cpha while o_cs_n = 0 have no effect until o_cs_n rises. [7.3:s1, 7.3:s3, 3:s13, 7.2:s1, 14:s7, 10:s3]
- What does 'next command ready in time' mean in cycles for gapless operation? → Gapless means a command handshake occurs at edge A+16·D: i_cmd_valid = 1 and o_cmd_ready = 1 in the last cycle of the current transfer. That needs o_rsp_valid = 0 in that cycle and the current transfer's i_cmd_last = 0. Otherwise the burst enters Pause with SCLK idle and o_cs_n low. [8:s16, 8:s17, 7.1:s11, 7:s12, 7.8:s1, 7.8:s3]
- Is SCLK edge 16 at A + 16·D, which is the first cycle after the 16·D-cycle transfer window that ends at A + 16·D − 1? The window, the edge position and the trail D cycles must agree, so the exact boundary needs settling. → Yes. The transfer covers cycles A to A+16·D−1. The last cycle starts at A+16·D−1 and ends at SCLK edge 16, which is edge A+16·D. Trail then lasts D cycles until o_cs_n rises at A+17·D. These are consistent. [3:s6, 3:s8, 3:s11, 7.2:s7, 7:s15, 7.2:s2]
- SPI-4-02 and SPI-4-04: At D=1, is SCLK = f(i_clk)/2 achievable with every timing relation (setup/sample edges) in the spec? Is any minimum D implied by the data-path timing? → D = 1 is legal, giving SCLK = f(i_clk)/2, with lead, trail and gap of 1 cycle. A shift edge and the next sampling edge are 1 cycle apart. No minimum D above 1 is imposed. Silicon timing of i_miso at D = 1 is an integrator duty (ENV-006), and D = 1 stays legal and is verified in simulation. [4:s1, 10:s17, 14:s18, 12:s16, 11:s2]
- Is the reset value of an input (i_cmd_valid) a DUT property or an environment obligation? Also, is the i_cpol/i_cpha 'may change only while o_cs_n = 1' restriction an environment constraint, and what is the behavior if violated? → The input reset value 0 of i_cmd_valid is an environment obligation (ENV-002), not a DUT property. The restriction that i_cpol/i_cpha change only while o_cs_n = 1 is an environment constraint (ENV-003). If it is violated, the master neither detects nor reports it and keeps using CPOL_b/CPHA_b until the end of the burst. [5:s4, 12:s4, 5:s15, 5:s16, 12:s5, 10:s3, 7.3:s3]
- During reset, o_sclk follows i_cpol combinationally, but i_cpol may change only while o_cs_n=1; is i_cpol allowed to change during reset? → Yes. During reset o_cs_n = 1, so the 'only while o_cs_n = 1' rule allows i_cpol to change. o_sclk must follow it combinationally, and VER-008 toggles i_cpol during reset. [5:s15, 6.2:s2, 6.2:s3, 12:s30]
- REQ-RST-001 says outputs take their reset values at once, but REQ-RST-006 and REQ-RST-007 give o_cmd_ready = 1 during reset while no command is accepted. Is o_cmd_ready = 1 during reset a handshake-ready signal that must be ignored by the source? Should a checker treat i_cmd_valid && o_cmd_ready during reset as a non-transfer? → o_cmd_ready = 1 during reset is a reset value only. A command handshake requires i_rst_n = 1, so i_cmd_valid && o_cmd_ready while i_rst_n = 0 is not a handshake and must not be accepted. The checker should treat it as a non-transfer. [6.2:s6, 6.2:s7, 3:s4, 7.1:s1, 10:s6]
- What does 'the gap requirement met' mean concretely after reset, and which signal exposes it? Does o_cmd_ready = 1 at the first edge with i_rst_n = 1 fully capture it? → After reset release the master is in Idle and can accept a command at the first edge with i_rst_n = 1. This is visible as o_cmd_ready = 1, because o_rsp_valid is 0 after reset. The minimum high time is not enforced across reset. [6.2:s10, 6.2:s11, 7.1:s9, 14:s22]
- D is not defined in these quotes (value, range, D=1 handling). Is it a fixed parameter, and can an input pin change it? Confirm before building checks that depend on it. → D is PARA_SPI_CLK_DIV, the number of i_clk cycles in one SCLK half period. It is a fixed elaboration-time parameter in the range 1 to 255, not an input pin, and cannot change at run time. D = 1 is legal and is handled by the same rules. [3:s1, 4:s1, 1.2:s5, 1.3:s3, 4:s4, 10:s17]
- What are the reset values of o_cs_n, o_sclk and o_cmd_ready on i_rst_n assertion? Is reset asynchronous? Only o_mosi (0) and o_rsp_data (8'h00) are given. → On i_rst_n assertion, o_cs_n = 1, o_sclk = current i_cpol (combinational), o_cmd_ready = 1, o_mosi = 0, o_rsp_valid = 0 and o_rsp_data = 8'h00. Reset assertion is asynchronous and release is synchronous. Outputs take reset values at once. [6.2:s1, 6.2:s2, 6.2:s3, 6.2:s4, 6.2:s5, 6.2:s6, 5:s3, 5:s11]
- If i_cmd_last=1 is captured for a transfer, can a second command be accepted before cs_n rises? REQ-CMD-010 says ready is 0 then, but a command is accepted in Idle only. Confirm that ready = 0 in Trail fully covers this. → No second command can be accepted before o_cs_n rises. In the last cycle of a transfer with captured i_cmd_last = 1, o_cmd_ready = 0. Trail has o_cmd_ready = 0. After o_cs_n rises at R, o_cmd_ready is 0 for cycles R to R+D−2, so the earliest acceptance is R+D. [7.1:s11, 7.1:s13, 7.1:s7, 7.2:s9, 7:s13]
- SPI-8-03 says o_rsp_valid becomes 1 at 16·D after acceptance, while SPI-8-11 says the response must be taken within 16·D−1 cycles of becoming valid. Is the 16·D count measured to the edge where o_rsp_valid is first visible or to the cycle before it? → o_rsp_valid = 1 is first visible in the cycle starting at edge A+16·D, where the byte is loaded (Example 1 shows it in cycle 16). The next transfer, accepted at A+16·D, has its last cycle starting at A+32·D−1. o_rsp_valid must be 0 in that cycle, so the handshake must occur at an edge no later than A+32·D−1. That is 16·D−1 edges after the valid cycle begins. [8:s4, 7.7:s3, 8:s17, 8:s18, 7.1:s11, 3:s2]
- SPI-8-07 gives o_cs_n low time 16·n·D + D, but SPI-8-04 puts the trail at D after edge 16 and SPI-8-01 puts the lead at D. Does the low time include the lead, given 0 latency from acceptance to o_cs_n low? → Yes, the low time includes the lead. o_cs_n falls at the acceptance edge A (0 latency) and rises at A_last+17·D. For n continuous bytes that is 16·n·D + D after A. Of this, the lead D is part of the first 16·D span and the trail D is the extra D. [7.2:s1, 7.2:s2, 8:s2, 8:s3, 8:s5, 8:s8]
- SPI-8-08 gives 16·n·D + 2·D for the spacing between acceptances, but SPI-8-09 gives 18·D for n=1. Do these agree with a gap of D and a lead of D? → They agree. For n = 1, 16·D + 2·D = 18·D. o_cs_n rises at A+17·D, the minimum gap is D, so the next acceptance is at A+18·D. The lead D is already counted inside the 16·D span. [8:s6, 8:s9, 8:s10, 7.2:s9, 7.1:s7]
- On reset during a transfer, o_sclk goes to i_cpol 'at once'. Does the master use the current i_cpol, or the latched CPOL_b, when i_cpol changed during the burst? → The current i_cpol is used. While i_rst_n = 0, o_sclk equals the current i_cpol and follows it combinationally. On reset during a transfer, o_sclk goes to i_cpol at once, not to the latched CPOL_b. [6.2:s3, 10:s9, 7.4:s6, 6.2:s1]
- Is 'edge A' defined unambiguously, so that the cycle of a response handshake at A + 16·D can be identified? → Yes. A is the acceptance edge, an edge with i_rst_n = 1, i_cmd_valid = 1 and o_cmd_ready = 1. A response handshake at A+16·D is an edge where o_rsp_valid and i_rsp_ready are both 1, in the cycle ending at that edge. [3:s4, 3:s7, 3:s3, 3:s5, 10:s11]
- Is the reset asynchronous or synchronous? 'At once, even mid half period' needs a defined timing relative to i_rst_n. → Reset assertion is asynchronous: outputs take reset values at once on i_rst_n falling, without waiting for an i_clk edge, even mid half period. Release is synchronous to i_clk. [5:s3, 6.2:s1, 10:s9, 12:s2, 12:s3]
- Does the general SCLK formula f(i_clk)/(2*PARA_SPI_CLK_DIV) apply to the other dividers (4 and 255)? The quote gives it only for divider 1. → Yes. The formula f(i_clk)/(2·D) is general for D = 1 to 255. The table gives 6.25 MHz for D = 4 and about 98.04 kHz for D = 255 at 50 MHz. [1.2:s5, 4:s1, 8:s12, 8:s13, 8:s14]
- ENV-008 requires reset from time zero, yet GAP-002 says outputs are undefined before the first assertion and inputs must never be X/Z; is i_rst_n itself defined at time zero? → Yes. i_rst_n is driven to 0 from time zero, before the first rising edge, for at least 2 cycles, so it is defined. Outputs before the first assertion are undefined and unchecked. All inputs must always be 0 or 1, never X or Z. [12:s13, 12:s14, 14:s13]
- Does 'during reset' in the i_cpol combinational path allow o_sclk to follow i_cpol asynchronously while i_rst_n is asserted, and does this conflict with 'o_sclk from a flip-flop while o_cs_n = 0' if o_cs_n resets to 1? → No conflict. During reset o_cs_n = 1, so o_sclk follows i_cpol through the one permitted combinational path used while o_cs_n = 1 or in reset. The 'from a flip-flop' rule applies only while o_cs_n = 0, where o_sclk is registered from CPOL_b. [13:s6, 13:s7, 6.2:s2, 6.2:s3, 14:s6, 7.4:s6]
- DEC-002 allows acceptance in the last cycle of a non-last transfer only if o_rsp_valid=0, while DEC-003 says the byte ending at the same edge is shown and one more byte can be held. Is o_rsp_valid sampled before or after that edge's update, and how is the held byte kept when i_rsp_ready stays 0? → o_rsp_valid is the registered value in the cycle ending at the edge, i.e. before that edge's update. If it was 0, or a response handshake occurs at that edge, the byte is loaded into o_rsp_data. Otherwise the byte becomes the held byte. The held byte is kept internally while i_rsp_ready = 0. Neither the shown nor the held byte is overwritten, and o_rsp_valid stays 1. At the handshake the held byte loads into o_rsp_data and o_rsp_valid stays 1. [7.7:s3, 7.7:s4, 7.7:s5, 7.7:s7, 7.7:s11, 7.7:s12, 7.7:s13, 8:s61]
- For D=1 in Idle, DEC-002 blocks acceptance for D-1 cycles (zero) while DEC-016 says o_cmd_ready equals NOT o_rsp_valid from the cycle o_cs_n rises. Does this hold for D>1 as well, and what is o_cmd_ready during the D-1 blocked cycles? → This holds for all D. In Idle, o_cmd_ready = 0 in the first D−1 cycles after o_cs_n rose (cycles R to R+D−2), and NOT o_rsp_valid from cycle R+D−1 on. For D = 1 there are no blocked cycles, so it equals NOT o_rsp_valid from the cycle o_cs_n rises. [7:s5, 7.1:s7, 7.1:s8, 7.1:s9, 10:s17, 14:s16]
- After reset, o_cs_n is high but the gap is not guaranteed. Is the first command still accepted after D-1 blocked cycles in Idle, counted from reset release? → No. After reset release there are no blocked cycles. The master is in Idle with the gap requirement deemed met, and accepts a command at the first edge with i_rst_n = 1 (o_cmd_ready = 1 since o_rsp_valid = 0). The D−1 blocked cycles apply only after o_cs_n rises at the end of a burst. The gap is not guaranteed across reset. [6.2:s10, 6.2:s11, 7.1:s9, 7.1:s7, 14:s22]


## spi_master_Design_Specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| SPI-1.1-01 |  | MUST | master | both | Each transfer shifts one byte out on o_mosi and one byte in from i_miso. *(when: during each transfer)* | keep |
| SPI-1.1-02 |  | MUST | master | both | Received bytes are returned on the response stream in order, one per transmitted command byte. | keep |
| SPI-1.1-04 |  | MUST | master | both | The master stops starting new transfers while the response stream is back-pressured. *(when: when the response stream is back-pressured)* | keep |
| SPI-1.2-01 |  | MUST | master | both | Each command produces one 8-bit full-duplex transfer, MSB first. | keep |
| SPI-1.2-02 |  | MUST | master | both | i_cmd_last = 1 marks the last byte of a burst, and o_cs_n stays low for the whole burst. *(when: during a burst)* | keep |
| SPI-1.2-03 |  | MUST | master | scenario | SPI modes 0 to 3 are selected by i_cpol and i_cpha. | keep |
| SPI-1.2-04 |  | MUST | master | both | i_cpol and i_cpha are captured when a burst starts. *(when: when a burst starts)* | keep |
| SPI-1.2-05 |  | MUST | master | both | SCLK frequency is f(i_clk) / (2 x PARA_SPI_CLK_DIV). *(when: PARA_SPI_CLK_DIV from 1 to 255, fixed at elaboration)* | keep |
| SPI-1.2-07 |  | MUST | master | both | There is no SCLK gap between back-to-back bytes. *(when: back-to-back bytes inside a burst when the next command is ready in time)* | keep |
| SPI-1.2-08 |  | MUST | master | both | SCLK pauses at its idle level and o_cs_n stays low. *(when: inside a burst when the next command is not ready in time)* | keep |
| SPI-1.2-09 |  | MUST | master | both | No received byte is lost: one byte is shown on the response stream and at most one more is held inside the master. *(when: under response back-pressure)* | keep; merged SPI-1.1-03 |
| SPI-1.2-10 |  | MUST | system | scenario | Reset is asynchronous and active-low. | fix: actor master->system, check both->scenario |
| SPI-3-01 |  | MUST | master | both | A transfer whose command is accepted at edge A covers 16·D i_clk cycles, starting at edges A through A + 16·D − 1. *(when: A command is accepted at edge A)* | keep |
| SPI-3-02 |  | MUST | master | assertion | The k-th transition of o_sclk (SCLK edge k) happens at edge A + k·D. *(when: During a transfer with acceptance edge A, for k = 1 to 16)* | keep |
| SPI-3-03 |  | MUST | master | assertion | Odd SCLK edges (k = 1, 3, …, 15) leave the idle level of o_sclk. Even SCLK edges (k = 2, 4, …, 16) return o_sclk to the idle level. *(when: During a transfer)* | keep |
| SPI-3-04 |  | MUST | master | scenario | The values of i_cpol and i_cpha captured at the first acceptance edge of the burst (CPOL_b, CPHA_b) apply for the current burst. *(when: Within a burst)* | keep |
| SPI-3-05 |  | MUST | master | assertion | o_cs_n is 0 and o_sclk is at the idle level. *(when: In a pause: inside a burst after a transfer with i_cmd_last = 0 ended and no command was accepted at its SCLK edge 16)* | keep |
| SPI-3-06 |  | MUST | master | assertion | o_cs_n stays low for a trail of D cycles after SCLK edge 16 before going high. *(when: After SCLK edge 16 of the last transfer of a burst)* | keep |
| SPI-4-02 |  | MUST | system | scenario | SCLK frequency shall equal f(i_clk) / (2·D), where D is PARA_SPI_CLK_DIV i_clk cycles per SCLK half period. | fix: check both->scenario; merged SPI-4-01 |
| SPI-4-03 | REQ-PAR-001 | MUST | system | scenario | Elaboration of m_spi_master shall fail with an error message. *(when: When PARA_SPI_CLK_DIV is less than 1 or greater than 255)* | keep |
| SPI-4-04 | REQ-PAR-002 | MUST | system | scenario | m_spi_master shall exhibit the specified behaviour without any other RTL change. *(when: For every PARA_SPI_CLK_DIV value from 1 to 255)* | keep |
| SPI-5-01 |  | MUST | system | scenario | i_rst_n is active-low, asserted asynchronously and released synchronously to i_clk. | keep |
| SPI-5-02 |  | MUST | master | assertion | The environment keeps i_cmd_valid at 0 while i_rst_n = 0. *(when: while i_rst_n = 0)* | keep |
| SPI-5-04 |  | MUST | slave | assertion | o_cmd_ready has reset value 1. *(when: during reset)* | keep |
| SPI-5-05 |  | MUST_NOT | slave | scenario | o_cmd_ready must not depend combinationally on any input. | keep |
| SPI-5-06 |  | MUST | slave | scenario | i_cmd_data is captured at the command handshake as the byte to send. *(when: at the command handshake)* | keep |
| SPI-5-07 |  | MUST | slave | scenario | i_cmd_last is captured at the command handshake; when 1, the byte ends the burst and o_cs_n is released after it. *(when: i_cmd_last = 1 captured at the command handshake)* | keep |
| SPI-5-08 |  | MUST | slave | assertion | o_rsp_valid has reset value 0. *(when: during reset)* | keep |
| SPI-5-09 |  | MUST | slave | scenario | o_rsp_data carries the byte received during the transfer of the matching command. | keep |
| SPI-5-10 |  | MUST | slave | assertion | o_rsp_data has reset value 0. *(when: during reset)* | keep |
| SPI-5-11 |  | MUST | slave | assertion | o_sclk equals i_cpol, following it combinationally, in reset. *(when: during reset)* | keep |
| SPI-5-12 |  | MUST | slave | assertion | o_mosi has reset value 0. *(when: during reset)* | keep |
| SPI-5-13 |  | MUST | slave | assertion | o_cs_n has reset value 1. *(when: during reset)* | keep |
| SPI-5-14 |  | MUST_NOT | master | assertion | i_cpol may change only while o_cs_n = 1. *(when: o_cs_n = 0)* | keep |
| SPI-5-15 |  | MUST | slave | scenario | i_cpha = 0 samples on leading edges and i_cpha = 1 samples on trailing edges. | keep |
| SPI-5-16 |  | MUST_NOT | master | assertion | i_cpha may change only while o_cs_n = 1. *(when: o_cs_n = 0)* | keep |
| SPI-6.1-01 | REQ-CLK-001 | MUST | master | none | All state elements of m_spi_master shall be clocked by the rising edge of i_clk, the only clock of the block. | fix: check scenario->none |
| SPI-6.1-02 | REQ-CLK-002 | MUST | master | none | o_sclk shall be produced as a data output timed by i_clk. | fix: check assertion->none |
| SPI-6.1-03 | REQ-CLK-002 | MUST_NOT | master | none | o_sclk shall not clock any state element inside the block. | keep |
| SPI-6.1-04 | REQ-CLK-003 | MUST | master | none | i_miso shall be treated as synchronous to i_clk and sampled without a synchroniser. | fix: check scenario->none |
| SPI-6.2-01 | REQ-RST-001 | MUST | master | assertion | All outputs shall take their reset values at once, without waiting for an edge of i_clk. *(when: When i_rst_n changes to 0)* | keep |
| SPI-6.2-02 | REQ-RST-002 | MUST | master | assertion | o_cs_n shall be 1. *(when: While i_rst_n = 0)* | keep |
| SPI-6.2-03 | REQ-RST-003 | MUST | master | assertion | o_sclk shall equal the current value of i_cpol and follow every change of i_cpol combinationally. *(when: While i_rst_n = 0)* | keep |
| SPI-6.2-04 | REQ-RST-004 | MUST | master | assertion | o_mosi shall be 0. *(when: While i_rst_n = 0)* | keep |
| SPI-6.2-05 | REQ-RST-005 | MUST | master | assertion | o_rsp_valid shall be 0 and o_rsp_data shall be 8'h00. *(when: While i_rst_n = 0)* | keep |
| SPI-6.2-06 | REQ-RST-006 | MUST | master | assertion | o_cmd_ready shall be 1. *(when: While i_rst_n = 0)* | keep |
| SPI-6.2-07 | REQ-RST-007 | MUST_NOT | master | both | The master shall not accept a command. *(when: While i_rst_n = 0, whatever the values of i_cmd_valid and o_cmd_ready)* | keep |
| SPI-6.2-08 | REQ-RST-008 | MUST | master | scenario | The transfer in progress shall be aborted. *(when: Reset asserted during a burst)* | keep; merged SPI-6.2-09 |
| SPI-6.2-10 | REQ-RST-009 | MUST | master | scenario | That byte shall be discarded without a response handshake. *(when: Reset asserted while a shown byte or a held byte exists)* | keep |
| SPI-6.2-11 | REQ-RST-010 | MUST | master | both | The master shall be in Idle with the gap requirement met and able to accept a command at the first edge at which i_rst_n is 1. *(when: After i_rst_n returns to 1)* | keep |
| SPI-6.2-12 | REQ-CS-005, REQ-RST-011 | MUST_NOT | master | scenario | The minimum o_cs_n high time of REQ-CS-005 shall not be required; after an aborted burst the high time is the reset duration plus time until next acceptance. *(when: Across a reset)* | keep |
| SPI-7.1-01 | REQ-CMD-001 | MUST | master | assertion | The master accepts a command at an edge only when i_rst_n = 1, i_cmd_valid = 1 and o_cmd_ready = 1 at that edge. | keep |
| SPI-7.1-02 | REQ-CMD-002 | MUST | master | both | The master captures i_cmd_data as the byte to send and i_cmd_last as the end-of-burst flag of that transfer. *(when: At the command acceptance edge)* | keep |
| SPI-7.1-03 | REQ-CMD-003 | MUST | master | scenario | Values of i_cmd_data and i_cmd_last have no effect. *(when: At edges without a command handshake)* | keep |
| SPI-7.1-04 | REQ-CMD-004 | MUST | master | scenario | The master behaves as if the command had never been presented. *(when: i_cmd_valid goes from 1 to 0 without a command handshake)* | keep |
| SPI-7.1-05 | REQ-CMD-005 | MUST | master | assertion | o_cmd_ready changes only at an i_clk edge or when i_rst_n is asserted, and does not depend combinationally on any input. | keep |
| SPI-7.1-06 | REQ-CMD-006 | MUST | master | assertion | o_cmd_ready is 0 in every cycle in which o_rsp_valid = 1. *(when: i_rst_n = 1 and o_rsp_valid = 1)* | keep |
| SPI-7.1-07 | REQ-CMD-007 | MUST | master | assertion | o_cmd_ready is 0 in every cycle starting at an edge from R to R + D − 2 (no such cycle when D = 1). *(when: o_cs_n changes from 0 to 1 at edge R)* | keep |
| SPI-7.1-08 | REQ-CMD-008 | MUST | master | assertion | o_cmd_ready is 1. *(when: In Idle with o_rsp_valid = 0, from edge R + D − 1 onward, and after reset release until the next acceptance)* | keep |
| SPI-7.1-09 | REQ-CMD-009 | MUST | master | assertion | o_cmd_ready is 0. *(when: During a transfer, except its last cycle)* | keep |
| SPI-7.1-10 | REQ-CMD-010 | MUST | master | assertion | o_cmd_ready is 1 if the captured i_cmd_last is 0 and o_rsp_valid is 0, and 0 otherwise. *(when: Last cycle of a transfer)* | keep |
| SPI-7.1-11 | REQ-CMD-011 | MUST | master | assertion | o_cmd_ready is 1 when o_rsp_valid = 0 and 0 when o_rsp_valid = 1. *(when: In Pause)* | keep |
| SPI-7.1-12 | REQ-CMD-012 | MUST | master | assertion | o_cmd_ready is 0. *(when: In Trail)* | keep |
| SPI-7.2-01 | REQ-CS-001 | MUST | master | assertion | o_cs_n changes from 1 to 0 at edge A, starting a burst. *(when: Command accepted in Idle at edge A)* | keep |
| SPI-7.2-02 | REQ-CS-002 | MUST | master | assertion | o_cs_n stays 0 until edge A + 17·D, where it changes to 1. *(when: From burst start; A is the acceptance edge of the transfer with captured i_cmd_last = 1)* | keep; merged SPI-7.2-06 |
| SPI-7.2-03 | REQ-CS-001, REQ-CS-002, REQ-CS-003 | MUST | master | assertion | o_cs_n changes only at the edges given in REQ-CS-001 and REQ-CS-002 and at the assertion of i_rst_n. | keep |
| SPI-7.2-04 | REQ-CS-004 | MUST | master | assertion | The first SCLK edge of a burst comes exactly D cycles after o_cs_n falls (edge A + D). *(when: Burst start)* | keep |
| SPI-7.2-05 | REQ-CS-005 | MUST | master | assertion | o_cs_n stays 1 for at least D cycles. *(when: Between two bursts with no reset in between)* | keep |
| SPI-7.2-07 | REQ-CS-007 | MUST_NOT | master | scenario | The rise of o_cs_n does not depend on the response stream state (o_rsp_valid, i_rsp_ready, a held byte). *(when: End of burst)* | keep |
| SPI-7.3-01 | REQ-MODE-001 | MUST | master | both | The master captures i_cpol as CPOL_b and i_cpha as CPHA_b. *(when: Acceptance edge of the first command of a burst)* | keep |
| SPI-7.3-02 | REQ-MODE-002 | MUST | master | both | CPOL_b and CPHA_b control o_sclk, o_mosi and the sampling of i_miso. *(when: Whole burst, including Pause and Trail)* | keep |
| SPI-7.3-03 | REQ-MODE-003 | MUST | master | both | Changes of i_cpol or i_cpha have no effect on o_sclk, o_mosi, o_cs_n, i_miso sampling or response data. *(when: While o_cs_n = 0)* | keep |
| SPI-7.3-04 | REQ-MODE-004 | MUST | master | both | Leading SCLK edges (odd k) are sampling edges and trailing edges (even k) are shift edges. *(when: CPHA_b = 0)* | keep |
| SPI-7.3-05 | REQ-MODE-005 | MUST | master | both | Leading SCLK edges (odd k) are shift edges and trailing edges (even k) are sampling edges. *(when: CPHA_b = 1)* | keep |
| SPI-7.4-01 | REQ-SCLK-001 | MUST | master | assertion | o_sclk toggles at each of the 16 edges A + k·D, k = 1 to 16. *(when: Transfer with acceptance edge A)* | keep |
| SPI-7.4-02 | REQ-SCLK-001, REQ-SCLK-002 | MUST_NOT | master | assertion | o_sclk does not change at any edge other than A + k·D, k = 1 to 16. *(when: While o_cs_n = 0)* | keep |
| SPI-7.4-03 | REQ-SCLK-003 | MUST | master | assertion | o_sclk equals CPOL_b (lead half period, Pause, Trail). *(when: o_cs_n = 0 and no transfer is between its SCLK edges 1 and 16)* | keep |
| SPI-7.4-04 | REQ-SCLK-004 | MUST | master | assertion | o_sclk equals NOT CPOL_b for odd k and CPOL_b for even k. *(when: After SCLK edge k of a transfer)* | keep |
| SPI-7.4-05 | REQ-SCLK-005 | MUST | master | assertion | o_sclk equals i_cpol and follows changes of i_cpol combinationally. *(when: While o_cs_n = 1)* | keep |
| SPI-7.4-06 | REQ-SCLK-006 | MUST | master | assertion | o_sclk takes the value of i_cpol from edge R on. *(when: o_cs_n rises at edge R)* | keep |
| SPI-7.4-07 | REQ-SCLK-007 | MUST | master | assertion | The SCLK period over the joint is 2·D cycles with each half period D cycles. *(when: Transfer starts at SCLK edge 16 of the previous transfer of the same burst)* | keep |
| SPI-7.5-01 | REQ-MOSI-001 | MUST | master | assertion | Bits of each byte are sent MSB first: d[7], d[6], …, d[0]. | keep |
| SPI-7.5-02 | REQ-MOSI-002 | MUST | master | assertion | o_mosi takes the value d[7] at the acceptance edge A. *(when: CPHA_b = 0)* | keep |
| SPI-7.5-03 | REQ-MOSI-003 | MUST | master | assertion | o_mosi takes the value d[7 − j] at edge A + 2·j·D for j = 1 to 7. *(when: CPHA_b = 0)* | keep |
| SPI-7.5-04 | REQ-MOSI-004 | MUST | master | assertion | o_mosi takes the value d[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. *(when: CPHA_b = 1)* | keep |
| SPI-7.5-05 | REQ-MOSI-002, REQ-MOSI-004, REQ-MOSI-005 | MUST_NOT | master | assertion | o_mosi does not change at any edge other than those of REQ-MOSI-002 to REQ-MOSI-004, except at the assertion of i_rst_n. | keep |
| SPI-7.5-06 | REQ-MOSI-006 | MUST | master | assertion | o_mosi keeps the last value it was given, which is 0 after reset. *(when: In Idle, Pause and Trail)* | keep |
| SPI-7.5-07 | REQ-MOSI-007 | MUST | master | assertion | o_mosi is stable in the cycle before each sampling edge and does not change at any sampling edge. *(when: All four modes)* | keep |
| SPI-7.5-08 | REQ-MOSI-002 | MUST | master | assertion | o_mosi keeps d[0] unless the next command is accepted at that edge, in which case it takes the next d[7]. *(when: CPHA_b = 0, after SCLK edge 16)* | keep |
| SPI-7.5-09 |  | MUST | master | assertion | o_mosi keeps its previous value from the acceptance edge until SCLK edge 1. *(when: CPHA_b = 1)* | keep |
| SPI-7.6-01 | REQ-MISO-001 | MUST | master | scenario | The master captures i_miso as r[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. *(when: CPHA_b = 0)* | keep |
| SPI-7.6-02 | REQ-MISO-002 | MUST | master | scenario | The master captures i_miso as r[7 − j] at edge A + (2·j + 2)·D for j = 0 to 7. *(when: CPHA_b = 1)* | keep |
| SPI-7.6-03 | REQ-MISO-003 | MUST | master | scenario | The captured value is i_miso in the cycle ending at that edge, just before o_sclk makes the sampling transition. *(when: At a sampling edge)* | keep |
| SPI-7.6-04 | REQ-MISO-004 | MUST_NOT | master | scenario | i_miso has no effect. *(when: At edges other than sampling edges of a transfer)* | keep |
| SPI-7.6-05 | REQ-MISO-005 | MUST | master | scenario | The received byte r[7:0] of a transfer is made only of the 8 bits captured during that transfer. | keep |
| SPI-7.7-01 | REQ-RSP-001 | MUST | master | scenario | Each accepted command produces exactly one response carrying the byte received during its transfer. | keep |
| SPI-7.7-02 | REQ-RSP-002 | MUST | master | scenario | Responses are delivered in command acceptance order, across burst boundaries. | keep |
| SPI-7.7-03 | REQ-RSP-003 | MUST | master | both | The master loads the received byte into o_rsp_data and sets o_rsp_valid to 1. *(when: At edge A + 16·D, if o_rsp_valid was 0 in the cycle ending at that edge or a response handshake occurs)* | keep |
| SPI-7.7-04 | REQ-RSP-003, REQ-RSP-004 | MUST | master | scenario | The received byte becomes the held byte. *(when: At edge A + 16·D, neither condition of REQ-RSP-003 holds)* | keep |
| SPI-7.7-05 | REQ-RSP-005 | MUST | master | both | The held byte is loaded into o_rsp_data and o_rsp_valid stays 1. *(when: At the edge of the response handshake of the shown byte, with a held byte)* | keep |
| SPI-7.7-06 | REQ-RSP-006 | MUST | master | assertion | o_rsp_valid changes to 0. *(when: Response handshake with no byte loaded at the same edge)* | keep |
| SPI-7.7-07 | REQ-RSP-007 | MUST | master | assertion | o_rsp_valid stays 1 and o_rsp_data does not change. *(when: o_rsp_valid = 1 and no response handshake)* | keep |
| SPI-7.7-08 | REQ-RSP-008 | MUST | master | assertion | o_rsp_data keeps the last byte loaded into it, or 8'h00 after reset. *(when: While o_rsp_valid = 0)* | keep |
| SPI-7.7-09 | REQ-RSP-009 | MUST | master | assertion | o_rsp_valid and o_rsp_data change only at i_clk edges or at the assertion of i_rst_n. | keep |
| SPI-7.7-10 | REQ-RSP-010 | MUST | master | assertion | i_rsp_ready has no effect. *(when: While o_rsp_valid = 0)* | keep |
| SPI-7.7-11 | REQ-RSP-011 | MUST_NOT | master | both | The master never overwrites a shown or held byte before it has been taken and never delivers a byte twice. | keep |
| SPI-7.7-12 | REQ-RSP-012 | MUST | master | scenario | At most two received bytes are pending at any time: one shown byte and at most one held byte. | keep |
| SPI-7.7-13 |  | MUST | master | scenario | A new transfer starts only when every earlier received byte has been taken, except the byte of the transfer ending at the same edge. | keep |
| SPI-7.8-01 | REQ-FLOW-001 | MUST | master | assertion | The new transfer uses that edge as its acceptance edge, with SCLK edge 1 D cycles after previous SCLK edge 16. *(when: Command accepted at edge A + 16·D of a transfer with captured i_cmd_last = 0)* | keep |
| SPI-7.8-02 | REQ-FLOW-002 | MUST | master | both | The master enters Pause. *(when: Transfer with captured i_cmd_last = 0 ends at edge A + 16·D without a command handshake)* | keep |
| SPI-7.8-03 | REQ-FLOW-003 | MUST | master | assertion | o_cs_n stays 0, o_sclk stays at CPOL_b and o_mosi keeps its value. *(when: In Pause)* | keep |
| SPI-7.8-04 | REQ-FLOW-004 | MUST | master | scenario | Pause lasts until a command is accepted, without any time limit. *(when: In Pause)* | keep |
| SPI-7.8-05 | REQ-FLOW-005 | MUST | master | both | A transfer starts with acceptance edge A = P, in the same burst with the same CPOL_b and CPHA_b. *(when: Command accepted in Pause at edge P)* | keep |
| SPI-7.8-06 | REQ-CS-002, REQ-FLOW-006 | MUST | master | assertion | The master enters Trail and o_cs_n rises at edge A + 17·D. *(when: Transfer with captured i_cmd_last = 1 ends at edge A + 16·D)* | keep |
| SPI-7.8-07 | REQ-FLOW-007 | MUST_NOT | master | scenario | The master does not start a transfer. *(when: A received byte is held)* | fix: check assertion->scenario |
| SPI-8-01 |  | MUST | master | assertion | SCLK edge 1 (lead) must occur D i_clk cycles after command acceptance, where D = PARA_SPI_CLK_DIV. *(when: After command acceptance)* | keep |
| SPI-8-02 |  | MUST | master | assertion | o_cs_n must go low at the acceptance edge itself (0 cycles after command acceptance) for the first byte of a burst. *(when: First byte of a burst)* | keep |
| SPI-8-03 |  | MUST | master | assertion | o_rsp_valid must become 1 16·D i_clk cycles after command acceptance. *(when: After command acceptance)* | keep |
| SPI-8-04 |  | MUST | master | assertion | o_cs_n must go high D i_clk cycles after SCLK edge 16 of the last byte (trail). *(when: After SCLK edge 16 of last byte)* | keep |
| SPI-8-05 |  | MUST | master | assertion | o_cs_n must stay high for at least D i_clk cycles between bursts. *(when: Between bursts)* | keep |
| SPI-8-06 |  | MUST | master | assertion | Byte period inside a continuous burst must be 16·D i_clk cycles. *(when: Inside a continuous burst)* | keep |
| SPI-8-07 |  | MUST | master | assertion | o_cs_n low time of an n-byte continuous burst must be 16·n·D + D i_clk cycles. *(when: n-byte continuous burst)* | keep |
| SPI-8-08 |  | MUST | master | scenario | Minimum time between first acceptances of consecutive n-byte bursts must be 16·n·D + 2·D i_clk cycles. *(when: Consecutive n-byte bursts)* | fix: check assertion->scenario |
| SPI-8-09 |  | MUST | master | scenario | The minimum period of single-byte bursts must be 18·D i_clk cycles. *(when: Single-byte bursts with i_cmd_last always 1)* | fix: check assertion->scenario |
| SPI-8-10 |  | MUST | system | scenario | The next command must be valid in the last cycle of the current transfer. *(when: For a continuous burst without SCLK pause)* | fix: actor master->system |
| SPI-8-11 |  | MUST | source | scenario | o_rsp_valid must be 0 in the last cycle of the current transfer, so the previous response must be taken within 16·D − 1 cycles of becoming valid. *(when: For a continuous burst without SCLK pause)* | fix: actor master->source |
| SPI-8-12 |  | MUST | master | assertion | The next transfer must not start at SCLK edge 16. *(when: o_rsp_valid = 1 in the last cycle of a transfer)* | keep |
| SPI-8-13 |  | MUST | master | scenario | The burst must enter Pause, or Trail if it was the last byte. *(when: o_rsp_valid = 1 in the last cycle of a transfer)* | keep |
| SPI-8-14 |  | MUST | master | scenario | That transfer's byte must become the held byte. *(when: Shown byte not yet taken at the end of a running transfer)* | keep |
| SPI-8-15 |  | MUST_NOT | master | scenario | No new transfer may start until both bytes have been taken. *(when: Until both shown and held bytes have been taken)* | keep |
| SPI-8-16 | REQ-RSP-002 | MUST | master | scenario | Responses must come out in command order. | keep |
| SPI-10-02 | REQ-ERR-001, REQ-MODE-003 | MUST | master | both | The master shall keep using CPOL_b and CPHA_b until the end of the burst. *(when: i_cpol or i_cpha changes while o_cs_n = 0)* | keep |
| SPI-10-03 | REQ-ERR-002, REQ-SCLK-006 | MUST | master | both | o_sclk shall change to i_cpol at the edge where o_cs_n rises. *(when: i_cpol differs from CPOL_b at the edge where o_cs_n rises)* | keep |
| SPI-10-04 | REQ-ERR-003 | MUST | master | both | The command shall wait without effect until a command handshake occurs. *(when: i_cmd_valid = 1 while o_cmd_ready = 0)* | keep |
| SPI-10-05 | REQ-ERR-004, REQ-RST-007 | MUST_NOT | master | assertion | The master shall not accept the command. *(when: i_cmd_valid = 1 while i_rst_n = 0)* | keep |
| SPI-10-06 | REQ-ERR-005 | MUST | master | both | The master shall keep o_rsp_valid = 1 with the same byte. *(when: the response consumer never takes a response)* | keep |
| SPI-10-07 | REQ-ERR-005 | MUST_NOT | master | both | The master shall not start any further transfer. *(when: the response consumer never takes a response)* | keep |
| SPI-10-08 | REQ-ERR-006 | MUST | master | scenario | o_cs_n shall stay 0 indefinitely. *(when: a burst is in Pause and no command ever arrives)* | fix: check both->scenario |
| SPI-10-09 | REQ-ERR-007, REQ-RST-008 | MUST | master | both | o_cs_n shall go to 1 and o_sclk to i_cpol at once, even in the middle of an SCLK half period. *(when: i_rst_n is asserted during a transfer)* | keep |
| SPI-10-10 | REQ-ERR-007, REQ-RST-008 | MUST | master | scenario | The partial byte shall be discarded. *(when: i_rst_n is asserted during a transfer)* | keep |
| SPI-10-11 | REQ-ERR-008, REQ-RST-002, REQ-RST-006 | MUST | master | both | The master shall go to the reset state of REQ-RST-002 to REQ-RST-006. *(when: i_rst_n is asserted in Pause, Trail or the Idle gap)* | keep |
| SPI-10-12 | REQ-ERR-008, REQ-RST-002, REQ-RST-006 | MUST | master | scenario | Pending bytes shall be discarded. *(when: i_rst_n is asserted in Pause, Trail or the Idle gap)* | keep |
| SPI-10-13 | REQ-ERR-009, REQ-RSP-003 | MUST | master | both | The received byte of that transfer shall load into o_rsp_data at that edge, with o_rsp_valid staying 1. *(when: a response handshake occurs at exactly edge A + 16·D of a transfer)* | keep |
| SPI-10-15 |  | MUST | master | scenario | The burst never ends; o_cs_n stays 0 and transfers continue as commands arrive. *(when: i_cmd_last = 0 forever)* | keep |
| SPI-10-16 |  | MUST | master | scenario | The half-period count shall reach 255 without overflow, giving 255-cycle half periods and 4080 cycles per byte. *(when: D = 255)* | fix: check both->scenario |
| SPI-11-01 |  | MUST | system | scenario | Verification must run every listed configuration, and since SPI mode is a run-time input, each configuration must be exercised in all four SPI modes. *(when: for each configuration CFG-BASE, CFG-MIN, CFG-MAX)* | keep |
| SPI-11-02 |  | MUST | system | scenario | With PARA_SPI_CLK_DIV=1, the smallest legal divider, SCLK must be f(i_clk)/2 and operate correctly in all four SPI modes. *(when: PARA_SPI_CLK_DIV=1 (CFG-MIN))* | fix: check both->scenario |
| SPI-11-03 |  | MUST | system | scenario | With PARA_SPI_CLK_DIV=255, the largest legal divider, the half-period counter must work at full width and operate correctly in all four SPI modes with short bursts. *(when: PARA_SPI_CLK_DIV=255 (CFG-MAX))* | keep |
| SPI-12-01 |  | MUST | system | assertion | The environment shall release i_rst_n synchronously to i_clk. | keep |
| SPI-12-02 |  | MAY | system | scenario | Assertion of i_rst_n may be asynchronous. | keep |
| SPI-12-03 |  | MUST | system | assertion | The environment shall keep i_cmd_valid = 0 while i_rst_n = 0. *(when: while i_rst_n = 0)* | keep |
| SPI-12-04 |  | MUST | system | assertion | The environment shall change i_cpol and i_cpha only while o_cs_n = 1. | keep |
| SPI-12-05 | REQ-ERR-001 | MAY | system | scenario | Error tests may deliberately violate the rule that i_cpol and i_cpha change only while o_cs_n = 1. *(when: error tests checking REQ-ERR-001)* | keep |
| SPI-12-06 |  | MUST | system | none | The SPI slave testbench model shall drive i_miso as a function of o_sclk and o_cs_n only. | keep |
| SPI-12-07 |  | MUST | system | scenario | The slave shall put bit 7 on i_miso when o_cs_n falls and the next bit after each trailing SCLK edge. *(when: CPHA = 0)* | keep |
| SPI-12-08 |  | MUST | system | scenario | The slave shall put bit 7 − j on i_miso after leading SCLK edge 2·j + 1. *(when: CPHA = 1)* | keep |
| SPI-12-09 |  | MUST | system | assertion | The slave model shall change i_miso only after the i_clk edge at which o_sclk or o_cs_n changed, never altering the value seen at a sampling edge. | keep |
| SPI-12-10 |  | MUST_NOT | system | assertion | The environment shall not assert i_rst_n at an i_clk edge; assertion happens between edges. | keep |
| SPI-12-12 |  | MUST | system | scenario | The environment shall drive i_rst_n = 0 from time zero, before the first rising i_clk edge, for at least 2 cycles. *(when: from start of operation)* | keep |
| SPI-12-13 |  | MUST | system | assertion | i_cpol, i_cpha and every other input shall always be 0 or 1, never X or Z. | keep |
| SPI-12-15 |  | MUST | system | none | i_miso shall meet setup and hold time to i_clk at each sampling edge; with D = 1, slave clock-to-output plus board round trip must fit in one period minus setup. *(when: in silicon, at each sampling edge)* | keep |
| SPI-12-16 | REQ-CMD-004 | MAY | system | scenario | The command stream may change i_cmd_valid, i_cmd_data and i_cmd_last before acceptance; stability is not required. *(when: before acceptance)* | keep |
| SPI-12-17 |  | MAY | system | scenario | The response consumer may drive i_rsp_ready with any pattern. | keep |
| SPI-12-18 |  | MUST | system | scenario | Verification shall run all four modes in every configuration of section 11, with random bytes on i_cmd_data and from the slave model. | keep |
| SPI-12-19 |  | MUST | system | scenario | Verification shall use burst lengths 1, 2 and at least 16, mixing bursts with and without pauses (i_cmd_valid gaps of 0, 1 and many cycles). | keep |
| SPI-12-20 | REQ-RSP-001, REQ-RSP-002, REQ-RSP-011 | MUST | system | scenario | A scoreboard shall check each response equals the byte sent by the slave during the matching command, in order, with no loss or duplicate. | keep |
| SPI-12-21 |  | MUST | system | both | A slave-side monitor shall check MOSI data at every sampling edge and the SCLK edge times (A + k·D). | keep |
| SPI-12-22 |  | MUST | system | both | The monitor shall also check lead, trail and gap times, the SCLK idle level and that o_mosi never changes at a sampling edge. | keep |
| SPI-12-23 | REQ-CMD-006, REQ-CMD-012 | MUST | system | both | Verification shall check o_cmd_ready cycle by cycle against REQ-CMD-006 to REQ-CMD-012, including the blocked first D − 1 Idle cycles. | fix: check assertion->both |
| SPI-12-24 |  | MUST | system | scenario | Back-pressure tests shall hold i_rsp_ready = 0 for long periods so that a held byte is created. | keep |
| SPI-12-25 | REQ-ERR-009 | MUST | system | scenario | Back-pressure tests shall cover a response handshake exactly at edge A + 16·D (REQ-ERR-009) and random i_rsp_ready patterns. | keep |
| SPI-12-26 |  | MUST | system | scenario | Reset tests shall hold i_rsp_ready = 0 before reset where a shown or held byte is wanted, and assert i_rst_n between i_clk edges in each phase (Transfer, Pause, Trail, Idle gap, held byte). | keep |
| SPI-12-27 |  | MUST | system | both | Reset tests shall check that outputs take reset values at once and no response of the aborted transfer appears. *(when: reset tests)* | keep |
| SPI-12-28 | REQ-RST-003, REQ-SCLK-005 | MUST | system | scenario | A test shall toggle i_cpol while i_rst_n = 0 and in Idle, and check o_sclk follows it in the same cycle. | keep |
| SPI-12-29 |  | MUST | system | scenario | A test shall change i_cpol and i_cpha in the cycle just before a burst-start acceptance edge and check the new values are used. | keep |
| SPI-12-30 | REQ-ERR-001, REQ-ERR-002 | MUST | system | scenario | An error test shall change i_cpol and i_cpha during a burst and check the burst finishes in the captured mode. | keep |
| SPI-12-31 |  | MUST | system | scenario | Coverage shall include mode × configuration, continuous join, pause entry and exit, held byte created and released, reset in each phase, and i_cmd_last = 1 on the first byte. | keep |
| SPI-12-32 | REQ-PAR-001 | MUST | system | scenario | REQ-PAR-001 shall be checked by elaborating once with an illegal value, not by simulation. | keep |
| SPI-13-01 | REQ-IMP-001 | MUST | system | none | The block shall meet timing at 50 MHz i_clk (20 ns period) in GF180MCU technology at worst-case corner. | keep |
| SPI-13-02 | REQ-IMP-002 | MUST | system | none | The RTL shall follow docs/RTL_RULES.md (REF-003). | keep |
| SPI-13-03 | REQ-IMP-003 | MUST | system | none | All flip-flops shall be clocked on the rising edge of i_clk and reset asynchronously by i_rst_n. | fix: check scenario->none |
| SPI-13-04 |  | MUST_NOT | system | none | The RTL shall contain no latches, no clock gating and no derived clocks. | keep |
| SPI-13-05 | REQ-IMP-004 | MUST | system | none | o_cs_n and o_mosi shall be driven directly by flip-flops. | keep |
| SPI-13-06 | REQ-IMP-005 | MUST | system | none | o_sclk shall come from a flip-flop value while o_cs_n = 0. *(when: While o_cs_n = 0)* | keep |
| SPI-13-07 |  | MUST | system | none | The only combinational path from an input to o_sclk shall be the i_cpol path, used while o_cs_n = 1 or during reset. | keep |
| SPI-13-08 | REQ-IMP-006 | SHOULD | system | none | o_sclk should be free of glitches when o_cs_n changes. *(when: When o_cs_n changes)* | fix: check assertion->none |
| SPI-13-09 |  | SHOULD | system | none | The selection between i_cpol and the internal SCLK value should be built so equal inputs give no static hazard. | keep |
| SPI-13-10 | REQ-IMP-007 | MUST | system | none | o_cmd_ready, o_rsp_valid and o_rsp_data shall be driven by flip-flops or logic of flip-flops only, with no combinational path from any input. | keep |
| SPI-13-11 | REQ-IMP-008 | MUST | system | none | i_miso shall be captured directly into a data flip-flop with no synchroniser. | keep |
| SPI-13-12 |  | MUST | any | none | The integrator shall constrain the input delay of i_miso. | keep |
| SPI-13-13 | REQ-IMP-009 | MUST | system | scenario | The half-period counter shall be wide enough for D = 255, at least 8 bits. | keep |
| SPI-14-01 |  | MUST | master | both | The master shall use exactly D cycles for lead and exactly D cycles for trail. | keep |
| SPI-14-02 |  | MUST | master | both | The gap between transfers shall be at least D cycles, and exactly D cycles when the next command is already waiting. *(when: between bursts, o_cs_n high gap)* | keep |
| SPI-14-03 |  | MUST_NOT | master | both | A command shall be accepted only in Idle (after D − 1 blocked cycles), in Pause, or in the last cycle of a non-last transfer, and only if o_rsp_valid = 0. | keep; merged SPI-14-17 |
| SPI-14-04 |  | MUST_NOT | master | scenario | o_cmd_ready shall have no combinational input path. | fix: check none->scenario |
| SPI-14-05 |  | MUST_NOT | master | both | A transfer shall start only when o_rsp_valid = 0; no byte is lost, as one more byte can be held inside the master. | keep |
| SPI-14-06 |  | MUST | master | both | The response shall appear at SCLK edge 16 (A + 16·D) in all modes, also for CPHA = 0 where the last bit is sampled at edge 15. *(when: all modes, including CPHA = 0)* | keep |
| SPI-14-07 |  | MUST | master | both | o_mosi shall hold its last value, and be 0 after reset. *(when: outside transfers, and with CPHA = 1 before edge 1)* | keep; merged SPI-14-19 |
| SPI-14-08 |  | MUST | master | both | While o_cs_n = 1, o_sclk shall be combinational from i_cpol; while o_cs_n = 0 it shall be registered from the captured CPOL_b. *(when: during reset and Idle)* | keep |
| SPI-14-09 |  | MUST | master | both | Mode input changes during a burst shall be ignored; captured values shall be used until o_cs_n rises. *(when: mode inputs change during a burst)* | keep |
| SPI-14-10 |  | MUST | master | both | Reset in the middle of a burst shall abort immediately and discard pending bytes; the gap guarantee does not apply across reset. *(when: reset asserted mid-burst)* | keep |
| SPI-14-11 |  | MUST | system | scenario | An illegal PARA_SPI_CLK_DIV shall cause an elaboration error. *(when: illegal PARA_SPI_CLK_DIV)* | keep |
| SPI-14-12 |  | MUST | master | both | o_rsp_data shall be 8'h00 after reset and otherwise keep the last loaded byte while not valid. | keep |
| SPI-14-16 | REQ-CMD-006 | MUST | master | assertion | For D = 1 in Idle, o_cmd_ready shall equal NOT o_rsp_valid from the cycle o_cs_n rises. *(when: D = 1 in Idle)* | keep |
| SPI-14-20 |  | MUST | master | both | There is no Pause timeout; o_cs_n shall stay low in Pause until the next command. *(when: in Pause)* | keep |
| SPI-14-21 | REQ-RST-011 | MAY | master | none | The master shall not enforce o_cs_n high for at least D cycles after reset release; the minimum gap is not guaranteed across reset. *(when: after reset release)* | fix: strength MUST_NOT->MAY, check scenario->none |

## Rejected

| ID | Statement | Reason |
|---|---|---|
| SPI-1.2-06 | Slave-select timing provides lead time, trail time and minimum high time between bursts, measured in half periods. | Quote names lead/trail/min-high times without values or requirements; nothing concrete to verify. |
| SPI-5-03 | i_cmd_valid has reset value 0. | i_cmd_valid is an input; reset value for an input is driven by the environment and duplicates SPI-5-02; actor slave is wrong. |
| SPI-8-17 | Transfer N+1 starts at that edge; at A_N + 32·D byte N+1 becomes held and the burst enters Pause or Trail because o_cmd_ready was forced 0. | It is a worked example, a description of one scenario, not a new requirement; it duplicates the back-pressure rules (12, 13, 14). |
| SPI-8-18 | Byte N is taken at edge H, byte N+1 is loaded at H with o_rsp_valid staying 1 and taken at H+1, then o_cmd_ready returns to 1 in Pause. | It is a worked example sequence of events rather than a separate normative rule; it restates the back-pressure behaviour. |
| SPI-9-01 | The spi_master block must not provide any software-visible registers. | The quote only describes the block ('has no software-visible registers'). It states a structural fact with no observable behaviour to check or exercise from interface signals. It is also not a normative MUST_NOT requirement. |
| SPI-10-01 | The master shall not detect or report a change of i_cpol or i_cpha while o_cs_n = 0. | Only says the master does not detect or report. No error output exists, so there is nothing to observe or exercise. The checkable part is the continued use of CPOL_b and CPHA_b, which is SPI-10-02. |
| SPI-10-14 | The master shall not detect a timing violation on i_miso. | The rule is that something is not detected. There is no observable behaviour to verify or exercise. |
| SPI-12-11 | An edge coinciding with i_rst_n assertion is not a legal case and no check covers it. | States a non-case/exclusion with no behaviour to verify or exercise; gap note. |
| SPI-12-14 | Outputs are undefined and no check applies before the first assertion of i_rst_n. | Says no check applies before first reset; nothing to verify, and MUST_NOT is misapplied. |
| SPI-14-13 | Reset asserted at an i_clk edge is not a legal case (ENV-007). | Environment assumption pointing to ENV-007; nothing to verify on the DUT. |
| SPI-14-14 | Outputs are undefined before the first reset, and inputs shall always be 0 or 1, never X (ENV-008). | Environment assumption about undefined outputs and legal inputs; not a DUT behaviour to verify. |
| SPI-14-15 | i_rsp_ready should be held at 0 before reset where a held byte is wanted. | Testbench stimulus guidance for a held byte; not a DUT requirement. |
| SPI-14-18 | D = 1 stays legal and is verified in simulation; silicon timing is an integrator duty (ENV-006). | Decision about legality and verification scope plus integrator duty; no DUT behaviour to check. |
| SPI-14-22 | CFG-MAX (D = 255) shall stay in the run set. | Test plan/run set decision, not a design behaviour. |
