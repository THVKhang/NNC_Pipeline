# Extracted rules - spi_master_Design_Specification.md

```
rules: 226  by strength {'MUST': 188, 'MUST_NOT': 30, 'MAY': 5, 'SHOULD': 3}  by check {'both': 56, 'scenario': 67, 'assertion': 81, 'none': 22}
normative sentences: 151  cited 151  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 15 (0 from cache)  cost US$0.5203  tokens in 67473 out 28938
```


## 1.1 Purpose

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-1.1-01 | MUST | master | both | Each transfer shifts one byte out on o_mosi and one byte in from i_miso. *(when: during each transfer)* | 1.1:s2 (p9) |
| SPI-1.1-02 | MUST | master | both | Received bytes are returned on the response stream in order, one per transmitted command byte. | 1.1:s3 (p9) |
| SPI-1.1-03 | MUST_NOT | master | both | The master never drops a received byte. | 1.1:s4 (p9) |
| SPI-1.1-04 | MUST | master | both | The master stops starting new transfers while the response stream is back-pressured. *(when: when the response stream is back-pressured)* | 1.1:s4 (p9) |

## 1.2 Features

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-1.2-01 | MUST | master | both | Each command produces one 8-bit full-duplex transfer, MSB first. | 1.2:s1 (p13) |
| SPI-1.2-02 | MUST | master | both | i_cmd_last = 1 marks the last byte of a burst, and o_cs_n stays low for the whole burst. *(when: during a burst)* | 1.2:s2 (p14) |
| SPI-1.2-03 | MUST | master | scenario | SPI modes 0 to 3 are selected by i_cpol and i_cpha. | 1.2:s3 (p15) |
| SPI-1.2-04 | MUST | master | both | i_cpol and i_cpha are captured when a burst starts. *(when: when a burst starts)* | 1.2:s4 (p15) |
| SPI-1.2-05 | MUST | master | both | SCLK frequency is f(i_clk) / (2 x PARA_SPI_CLK_DIV). *(when: PARA_SPI_CLK_DIV from 1 to 255, fixed at elaboration)* | 1.2:s5 (p16) |
| SPI-1.2-06 | MUST | master | both | Slave-select timing provides lead time, trail time and minimum high time between bursts, measured in half periods. | 1.2:s6 (p17) |
| SPI-1.2-07 | MUST | master | both | There is no SCLK gap between back-to-back bytes. *(when: back-to-back bytes inside a burst when the next command is ready in time)* | 1.2:s7 (p18) |
| SPI-1.2-08 | MUST | master | both | SCLK pauses at its idle level and o_cs_n stays low. *(when: inside a burst when the next command is not ready in time)* | 1.2:s8 (p18) |
| SPI-1.2-09 | MUST | master | both | No received byte is lost: one byte is shown on the response stream and at most one more is held inside the master. *(when: under response back-pressure)* | 1.2:s9 (p19) |
| SPI-1.2-10 | MUST | master | both | Reset is asynchronous and active-low. | 1.2:s10 (p20) |

## 3 Terms

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-3-01 | MUST | master | both | A transfer whose command is accepted at edge A covers 16·D i_clk cycles, starting at edges A through A + 16·D − 1. *(when: A command is accepted at edge A)* | 3:s6 (p50) |
| SPI-3-02 | MUST | master | assertion | The k-th transition of o_sclk (SCLK edge k) happens at edge A + k·D. *(when: During a transfer with acceptance edge A, for k = 1 to 16)* | 3:s8 (p52) |
| SPI-3-03 | MUST | master | assertion | Odd SCLK edges (k = 1, 3, …, 15) leave the idle level of o_sclk. Even SCLK edges (k = 2, 4, …, 16) return o_sclk to the idle level. *(when: During a transfer)* | 3:s9 (p53) |
| SPI-3-04 | MUST | master | scenario | The values of i_cpol and i_cpha captured at the first acceptance edge of the burst (CPOL_b, CPHA_b) apply for the current burst. *(when: Within a burst)* | 3:s13 (p57) |
| SPI-3-05 | MUST | master | assertion | o_cs_n is 0 and o_sclk is at the idle level. *(when: In a pause: inside a burst after a transfer with i_cmd_last = 0 ended and no command was accepted at its SCLK edge 16)* | 3:s15 (p59) |
| SPI-3-06 | MUST | master | assertion | o_cs_n stays low for a trail of D cycles after SCLK edge 16 before going high. *(when: After SCLK edge 16 of the last transfer of a burst)* | 3:s16 (p60) |

## 4 Parameters

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-4-01 | MUST | system | none | PARA_SPI_CLK_DIV shall take a legal value from 1 to 255 (default 4), being the number of i_clk cycles in one SCLK half period D. | 4:s1 (p69) |
| SPI-4-02 | MUST | system | both | SCLK frequency shall equal f(i_clk) / (2·D), where D is PARA_SPI_CLK_DIV i_clk cycles per SCLK half period. | 4:s1 (p69) |
| SPI-4-03 | MUST | system | scenario | Elaboration of m_spi_master shall fail with an error message. *(when: When PARA_SPI_CLK_DIV is less than 1 or greater than 255)* | 4:s3 (p73) |
| SPI-4-04 | MUST | system | scenario | m_spi_master shall exhibit the specified behaviour without any other RTL change. *(when: For every PARA_SPI_CLK_DIV value from 1 to 255)* | 4:s4 (p75) |

## 5 Interface

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-5-01 | MUST | system | scenario | i_rst_n is active-low, asserted asynchronously and released synchronously to i_clk. | 5:s3 (p84) |
| SPI-5-02 | MUST | master | assertion | The environment keeps i_cmd_valid at 0 while i_rst_n = 0. *(when: while i_rst_n = 0)* | 5:s4 (p85) |
| SPI-5-03 | MUST | slave | assertion | i_cmd_valid has reset value 0. *(when: during reset)* | 5:s4 (p85) |
| SPI-5-04 | MUST | slave | assertion | o_cmd_ready has reset value 1. *(when: during reset)* | 5:s5 (p86) |
| SPI-5-05 | MUST_NOT | slave | scenario | o_cmd_ready must not depend combinationally on any input. | 5:s5 (p86) |
| SPI-5-06 | MUST | slave | scenario | i_cmd_data is captured at the command handshake as the byte to send. *(when: at the command handshake)* | 5:s6 (p87) |
| SPI-5-07 | MUST | slave | scenario | i_cmd_last is captured at the command handshake; when 1, the byte ends the burst and o_cs_n is released after it. *(when: i_cmd_last = 1 captured at the command handshake)* | 5:s7 (p88) |
| SPI-5-08 | MUST | slave | assertion | o_rsp_valid has reset value 0. *(when: during reset)* | 5:s8 (p89) |
| SPI-5-09 | MUST | slave | scenario | o_rsp_data carries the byte received during the transfer of the matching command. | 5:s10 (p91) |
| SPI-5-10 | MUST | slave | assertion | o_rsp_data has reset value 0. *(when: during reset)* | 5:s10 (p91) |
| SPI-5-11 | MUST | slave | assertion | o_sclk equals i_cpol, following it combinationally, in reset. *(when: during reset)* | 5:s11 (p92) |
| SPI-5-12 | MUST | slave | assertion | o_mosi has reset value 0. *(when: during reset)* | 5:s12 (p93) |
| SPI-5-13 | MUST | slave | assertion | o_cs_n has reset value 1. *(when: during reset)* | 5:s14 (p95) |
| SPI-5-14 | MUST_NOT | master | assertion | i_cpol may change only while o_cs_n = 1. *(when: o_cs_n = 0)* | 5:s15 (p96) |
| SPI-5-15 | MUST | slave | scenario | i_cpha = 0 samples on leading edges and i_cpha = 1 samples on trailing edges. | 5:s16 (p97) |
| SPI-5-16 | MUST_NOT | master | assertion | i_cpha may change only while o_cs_n = 1. *(when: o_cs_n = 0)* | 5:s16 (p97) |

## 6.1 Clocks

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-6.1-01 | MUST | master | scenario | All state elements of m_spi_master shall be clocked by the rising edge of i_clk, the only clock of the block. | 6.1:s1 (p103) |
| SPI-6.1-02 | MUST | master | assertion | o_sclk shall be produced as a data output timed by i_clk. | 6.1:s2 (p105) |
| SPI-6.1-03 | MUST_NOT | master | none | o_sclk shall not clock any state element inside the block. | 6.1:s2 (p105) |
| SPI-6.1-04 | MUST | master | scenario | i_miso shall be treated as synchronous to i_clk and sampled without a synchroniser. | 6.1:s3 (p107) |

## 6.2 Resets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-6.2-01 | MUST | master | assertion | All outputs shall take their reset values at once, without waiting for an edge of i_clk. *(when: When i_rst_n changes to 0)* | 6.2:s1 (p113) |
| SPI-6.2-02 | MUST | master | assertion | o_cs_n shall be 1. *(when: While i_rst_n = 0)* | 6.2:s2 (p115) |
| SPI-6.2-03 | MUST | master | assertion | o_sclk shall equal the current value of i_cpol and follow every change of i_cpol combinationally. *(when: While i_rst_n = 0)* | 6.2:s3 (p117) |
| SPI-6.2-04 | MUST | master | assertion | o_mosi shall be 0. *(when: While i_rst_n = 0)* | 6.2:s4 (p119) |
| SPI-6.2-05 | MUST | master | assertion | o_rsp_valid shall be 0 and o_rsp_data shall be 8'h00. *(when: While i_rst_n = 0)* | 6.2:s5 (p121) |
| SPI-6.2-06 | MUST | master | assertion | o_cmd_ready shall be 1. *(when: While i_rst_n = 0)* | 6.2:s6 (p123) |
| SPI-6.2-07 | MUST_NOT | master | both | The master shall not accept a command. *(when: While i_rst_n = 0, whatever the values of i_cmd_valid and o_cmd_ready)* | 6.2:s7 (p125) |
| SPI-6.2-08 | MUST | master | scenario | The transfer in progress shall be aborted. *(when: Reset asserted during a burst)* | 6.2:s8 (p127) |
| SPI-6.2-09 | MUST_NOT | master | both | No response shall be produced for the aborted transfer. *(when: Reset asserted during a burst)* | 6.2:s8 (p127) |
| SPI-6.2-10 | MUST | master | scenario | That byte shall be discarded without a response handshake. *(when: Reset asserted while a shown byte or a held byte exists)* | 6.2:s9 (p129) |
| SPI-6.2-11 | MUST | master | both | The master shall be in Idle with the gap requirement met and able to accept a command at the first edge at which i_rst_n is 1. *(when: After i_rst_n returns to 1)* | 6.2:s10 (p131) |
| SPI-6.2-12 | MUST_NOT | master | scenario | The minimum o_cs_n high time of REQ-CS-005 shall not be required; after an aborted burst the high time is the reset duration plus time until next acceptance. *(when: Across a reset)* | 6.2:s11 (p133) |

## 7.1 Command stream

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.1-01 | MUST | master | assertion | The master accepts a command at an edge only when i_rst_n = 1, i_cmd_valid = 1 and o_cmd_ready = 1 at that edge. | 7.1:s1 (p163) |
| SPI-7.1-02 | MUST | master | both | The master captures i_cmd_data as the byte to send and i_cmd_last as the end-of-burst flag of that transfer. *(when: At the command acceptance edge)* | 7.1:s2 (p165) |
| SPI-7.1-03 | MUST | master | scenario | Values of i_cmd_data and i_cmd_last have no effect. *(when: At edges without a command handshake)* | 7.1:s3 (p167) |
| SPI-7.1-04 | MUST | master | scenario | The master behaves as if the command had never been presented. *(when: i_cmd_valid goes from 1 to 0 without a command handshake)* | 7.1:s4 (p169) |
| SPI-7.1-05 | MUST | master | assertion | o_cmd_ready changes only at an i_clk edge or when i_rst_n is asserted, and does not depend combinationally on any input. | 7.1:s5 (p171) |
| SPI-7.1-06 | MUST | master | assertion | o_cmd_ready is 0 in every cycle in which o_rsp_valid = 1. *(when: i_rst_n = 1 and o_rsp_valid = 1)* | 7.1:s6 (p173) |
| SPI-7.1-07 | MUST | master | assertion | o_cmd_ready is 0 in every cycle starting at an edge from R to R + D − 2 (no such cycle when D = 1). *(when: o_cs_n changes from 0 to 1 at edge R)* | 7.1:s7, 7.1:s8 (p175) |
| SPI-7.1-08 | MUST | master | assertion | o_cmd_ready is 1. *(when: In Idle with o_rsp_valid = 0, from edge R + D − 1 onward, and after reset release until the next acceptance)* | 7.1:s9 (p177) |
| SPI-7.1-09 | MUST | master | assertion | o_cmd_ready is 0. *(when: During a transfer, except its last cycle)* | 7.1:s10 (p179) |
| SPI-7.1-10 | MUST | master | assertion | o_cmd_ready is 1 if the captured i_cmd_last is 0 and o_rsp_valid is 0, and 0 otherwise. *(when: Last cycle of a transfer)* | 7.1:s11 (p181) |
| SPI-7.1-11 | MUST | master | assertion | o_cmd_ready is 1 when o_rsp_valid = 0 and 0 when o_rsp_valid = 1. *(when: In Pause)* | 7.1:s12 (p183) |
| SPI-7.1-12 | MUST | master | assertion | o_cmd_ready is 0. *(when: In Trail)* | 7.1:s13 (p185) |

## 7.2 Burst framing and slave select

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.2-01 | MUST | master | assertion | o_cs_n changes from 1 to 0 at edge A, starting a burst. *(when: Command accepted in Idle at edge A)* | 7.2:s1 (p189) |
| SPI-7.2-02 | MUST | master | assertion | o_cs_n stays 0 until edge A + 17·D, where it changes to 1. *(when: From burst start; A is the acceptance edge of the transfer with captured i_cmd_last = 1)* | 7.2:s2, 7.2:s3 (p191) |
| SPI-7.2-03 | MUST | master | assertion | o_cs_n changes only at the edges given in REQ-CS-001 and REQ-CS-002 and at the assertion of i_rst_n. | 7.2:s4 (p193) |
| SPI-7.2-04 | MUST | master | assertion | The first SCLK edge of a burst comes exactly D cycles after o_cs_n falls (edge A + D). *(when: Burst start)* | 7.2:s5 (p195) |
| SPI-7.2-05 | MUST | master | assertion | o_cs_n stays 1 for at least D cycles. *(when: Between two bursts with no reset in between)* | 7.2:s6 (p197) |
| SPI-7.2-06 | MUST | master | assertion | o_cs_n rises exactly D cycles after SCLK edge 16 of the last transfer of the burst. *(when: End of burst)* | 7.2:s7 (p199) |
| SPI-7.2-07 | MUST_NOT | master | scenario | The rise of o_cs_n does not depend on the response stream state (o_rsp_valid, i_rsp_ready, a held byte). *(when: End of burst)* | 7.2:s8 (p201) |

## 7.3 SPI mode selection

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.3-01 | MUST | master | both | The master captures i_cpol as CPOL_b and i_cpha as CPHA_b. *(when: Acceptance edge of the first command of a burst)* | 7.3:s1 (p207) |
| SPI-7.3-02 | MUST | master | both | CPOL_b and CPHA_b control o_sclk, o_mosi and the sampling of i_miso. *(when: Whole burst, including Pause and Trail)* | 7.3:s2 (p209) |
| SPI-7.3-03 | MUST | master | both | Changes of i_cpol or i_cpha have no effect on o_sclk, o_mosi, o_cs_n, i_miso sampling or response data. *(when: While o_cs_n = 0)* | 7.3:s3 (p211) |
| SPI-7.3-04 | MUST | master | both | Leading SCLK edges (odd k) are sampling edges and trailing edges (even k) are shift edges. *(when: CPHA_b = 0)* | 7.3:s4 (p213) |
| SPI-7.3-05 | MUST | master | both | Leading SCLK edges (odd k) are shift edges and trailing edges (even k) are sampling edges. *(when: CPHA_b = 1)* | 7.3:s5 (p215) |

## 7.4 SCLK generation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.4-01 | MUST | master | assertion | o_sclk toggles at each of the 16 edges A + k·D, k = 1 to 16. *(when: Transfer with acceptance edge A)* | 7.4:s1 (p228) |
| SPI-7.4-02 | MUST_NOT | master | assertion | o_sclk does not change at any edge other than A + k·D, k = 1 to 16. *(when: While o_cs_n = 0)* | 7.4:s2 (p230) |
| SPI-7.4-03 | MUST | master | assertion | o_sclk equals CPOL_b (lead half period, Pause, Trail). *(when: o_cs_n = 0 and no transfer is between its SCLK edges 1 and 16)* | 7.4:s3, 7.4:s4 (p232) |
| SPI-7.4-04 | MUST | master | assertion | o_sclk equals NOT CPOL_b for odd k and CPOL_b for even k. *(when: After SCLK edge k of a transfer)* | 7.4:s5 (p234) |
| SPI-7.4-05 | MUST | master | assertion | o_sclk equals i_cpol and follows changes of i_cpol combinationally. *(when: While o_cs_n = 1)* | 7.4:s6 (p236) |
| SPI-7.4-06 | MUST | master | assertion | o_sclk takes the value of i_cpol from edge R on. *(when: o_cs_n rises at edge R)* | 7.4:s7 (p238) |
| SPI-7.4-07 | MUST | master | assertion | The SCLK period over the joint is 2·D cycles with each half period D cycles. *(when: Transfer starts at SCLK edge 16 of the previous transfer of the same burst)* | 7.4:s8 (p240) |

## 7.5 MOSI transmission

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.5-01 | MUST | master | assertion | Bits of each byte are sent MSB first: d[7], d[6], …, d[0]. | 7.5:s2 (p246) |
| SPI-7.5-02 | MUST | master | assertion | o_mosi takes the value d[7] at the acceptance edge A. *(when: CPHA_b = 0)* | 7.5:s3 (p248) |
| SPI-7.5-03 | MUST | master | assertion | o_mosi takes the value d[7 − j] at edge A + 2·j·D for j = 1 to 7. *(when: CPHA_b = 0)* | 7.5:s4 (p250) |
| SPI-7.5-04 | MUST | master | assertion | o_mosi takes the value d[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. *(when: CPHA_b = 1)* | 7.5:s5 (p252) |
| SPI-7.5-05 | MUST_NOT | master | assertion | o_mosi does not change at any edge other than those of REQ-MOSI-002 to REQ-MOSI-004, except at the assertion of i_rst_n. | 7.5:s6 (p254) |
| SPI-7.5-06 | MUST | master | assertion | o_mosi keeps the last value it was given, which is 0 after reset. *(when: In Idle, Pause and Trail)* | 7.5:s7, 7.5:s8 (p256) |
| SPI-7.5-07 | MUST | master | assertion | o_mosi is stable in the cycle before each sampling edge and does not change at any sampling edge. *(when: All four modes)* | 7.5:s9 (p258) |
| SPI-7.5-08 | MUST | master | assertion | o_mosi keeps d[0] unless the next command is accepted at that edge, in which case it takes the next d[7]. *(when: CPHA_b = 0, after SCLK edge 16)* | 7.5:s10 (p260) |
| SPI-7.5-09 | MUST | master | assertion | o_mosi keeps its previous value from the acceptance edge until SCLK edge 1. *(when: CPHA_b = 1)* | 7.5:s11 (p260) |

## 7.6 MISO reception

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.6-01 | MUST | master | scenario | The master captures i_miso as r[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. *(when: CPHA_b = 0)* | 7.6:s1 (p264) |
| SPI-7.6-02 | MUST | master | scenario | The master captures i_miso as r[7 − j] at edge A + (2·j + 2)·D for j = 0 to 7. *(when: CPHA_b = 1)* | 7.6:s2 (p266) |
| SPI-7.6-03 | MUST | master | scenario | The captured value is i_miso in the cycle ending at that edge, just before o_sclk makes the sampling transition. *(when: At a sampling edge)* | 7.6:s3 (p268) |
| SPI-7.6-04 | MUST_NOT | master | scenario | i_miso has no effect. *(when: At edges other than sampling edges of a transfer)* | 7.6:s4 (p270) |
| SPI-7.6-05 | MUST | master | scenario | The received byte r[7:0] of a transfer is made only of the 8 bits captured during that transfer. | 7.6:s5 (p272) |

## 7.7 Response stream

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.7-01 | MUST | master | scenario | Each accepted command produces exactly one response carrying the byte received during its transfer. | 7.7:s1 (p276) |
| SPI-7.7-02 | MUST | master | scenario | Responses are delivered in command acceptance order, across burst boundaries. | 7.7:s2 (p278) |
| SPI-7.7-03 | MUST | master | both | The master loads the received byte into o_rsp_data and sets o_rsp_valid to 1. *(when: At edge A + 16·D, if o_rsp_valid was 0 in the cycle ending at that edge or a response handshake occurs)* | 7.7:s3 (p280) |
| SPI-7.7-04 | MUST | master | scenario | The received byte becomes the held byte. *(when: At edge A + 16·D, neither condition of REQ-RSP-003 holds)* | 7.7:s4 (p282) |
| SPI-7.7-05 | MUST | master | both | The held byte is loaded into o_rsp_data and o_rsp_valid stays 1. *(when: At the edge of the response handshake of the shown byte, with a held byte)* | 7.7:s5 (p284) |
| SPI-7.7-06 | MUST | master | assertion | o_rsp_valid changes to 0. *(when: Response handshake with no byte loaded at the same edge)* | 7.7:s6 (p286) |
| SPI-7.7-07 | MUST | master | assertion | o_rsp_valid stays 1 and o_rsp_data does not change. *(when: o_rsp_valid = 1 and no response handshake)* | 7.7:s7 (p288) |
| SPI-7.7-08 | MUST | master | assertion | o_rsp_data keeps the last byte loaded into it, or 8'h00 after reset. *(when: While o_rsp_valid = 0)* | 7.7:s8 (p290) |
| SPI-7.7-09 | MUST | master | assertion | o_rsp_valid and o_rsp_data change only at i_clk edges or at the assertion of i_rst_n. | 7.7:s9 (p292) |
| SPI-7.7-10 | MUST | master | assertion | i_rsp_ready has no effect. *(when: While o_rsp_valid = 0)* | 7.7:s10 (p294) |
| SPI-7.7-11 | MUST_NOT | master | both | The master never overwrites a shown or held byte before it has been taken and never delivers a byte twice. | 7.7:s11 (p296) |
| SPI-7.7-12 | MUST | master | scenario | At most two received bytes are pending at any time: one shown byte and at most one held byte. | 7.7:s12 (p298) |
| SPI-7.7-13 | MUST | master | scenario | A new transfer starts only when every earlier received byte has been taken, except the byte of the transfer ending at the same edge. | 7.7:s14 (p300) |

## 7.8 Continuation, pause and end of burst

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-7.8-01 | MUST | master | assertion | The new transfer uses that edge as its acceptance edge, with SCLK edge 1 D cycles after previous SCLK edge 16. *(when: Command accepted at edge A + 16·D of a transfer with captured i_cmd_last = 0)* | 7.8:s1, 7.8:s2 (p304) |
| SPI-7.8-02 | MUST | master | both | The master enters Pause. *(when: Transfer with captured i_cmd_last = 0 ends at edge A + 16·D without a command handshake)* | 7.8:s3 (p306) |
| SPI-7.8-03 | MUST | master | assertion | o_cs_n stays 0, o_sclk stays at CPOL_b and o_mosi keeps its value. *(when: In Pause)* | 7.8:s4 (p308) |
| SPI-7.8-04 | MUST | master | scenario | Pause lasts until a command is accepted, without any time limit. *(when: In Pause)* | 7.8:s5 (p310) |
| SPI-7.8-05 | MUST | master | both | A transfer starts with acceptance edge A = P, in the same burst with the same CPOL_b and CPHA_b. *(when: Command accepted in Pause at edge P)* | 7.8:s6 (p312) |
| SPI-7.8-06 | MUST | master | assertion | The master enters Trail and o_cs_n rises at edge A + 17·D. *(when: Transfer with captured i_cmd_last = 1 ends at edge A + 16·D)* | 7.8:s7 (p314) |
| SPI-7.8-07 | MUST_NOT | master | assertion | The master does not start a transfer. *(when: A received byte is held)* | 7.8:s8 (p316) |

## 8 Timing and protocol

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-8-01 | MUST | master | assertion | SCLK edge 1 (lead) must occur D i_clk cycles after command acceptance, where D = PARA_SPI_CLK_DIV. *(when: After command acceptance)* | 8:s1, 8:s3 (p320) |
| SPI-8-02 | MUST | master | assertion | o_cs_n must go low at the acceptance edge itself (0 cycles after command acceptance) for the first byte of a burst. *(when: First byte of a burst)* | 8:s1, 8:s2 (p320) |
| SPI-8-03 | MUST | master | assertion | o_rsp_valid must become 1 16·D i_clk cycles after command acceptance. *(when: After command acceptance)* | 8:s1, 8:s4 (p320) |
| SPI-8-04 | MUST | master | assertion | o_cs_n must go high D i_clk cycles after SCLK edge 16 of the last byte (trail). *(when: After SCLK edge 16 of last byte)* | 8:s1, 8:s5 (p320) |
| SPI-8-05 | MUST | master | assertion | o_cs_n must stay high for at least D i_clk cycles between bursts. *(when: Between bursts)* | 8:s1, 8:s6 (p320) |
| SPI-8-06 | MUST | master | assertion | Byte period inside a continuous burst must be 16·D i_clk cycles. *(when: Inside a continuous burst)* | 8:s1, 8:s7 (p320) |
| SPI-8-07 | MUST | master | assertion | o_cs_n low time of an n-byte continuous burst must be 16·n·D + D i_clk cycles. *(when: n-byte continuous burst)* | 8:s1, 8:s8 (p320) |
| SPI-8-08 | MUST | master | assertion | Minimum time between first acceptances of consecutive n-byte bursts must be 16·n·D + 2·D i_clk cycles. *(when: Consecutive n-byte bursts)* | 8:s1, 8:s9 (p320) |
| SPI-8-09 | MUST | master | assertion | The minimum period of single-byte bursts must be 18·D i_clk cycles. *(when: Single-byte bursts with i_cmd_last always 1)* | 8:s10 (p332) |
| SPI-8-10 | MUST | master | scenario | The next command must be valid in the last cycle of the current transfer. *(when: For a continuous burst without SCLK pause)* | 8:s15, 8:s16 (p342) |
| SPI-8-11 | MUST | master | scenario | o_rsp_valid must be 0 in the last cycle of the current transfer, so the previous response must be taken within 16·D − 1 cycles of becoming valid. *(when: For a continuous burst without SCLK pause)* | 8:s15, 8:s17, 8:s18 (p342) |
| SPI-8-12 | MUST | master | assertion | The next transfer must not start at SCLK edge 16. *(when: o_rsp_valid = 1 in the last cycle of a transfer)* | 8:s19, 8:s20 (p346) |
| SPI-8-13 | MUST | master | scenario | The burst must enter Pause, or Trail if it was the last byte. *(when: o_rsp_valid = 1 in the last cycle of a transfer)* | 8:s21 (p347) |
| SPI-8-14 | MUST | master | scenario | That transfer's byte must become the held byte. *(when: Shown byte not yet taken at the end of a running transfer)* | 8:s22 (p348) |
| SPI-8-15 | MUST_NOT | master | scenario | No new transfer may start until both bytes have been taken. *(when: Until both shown and held bytes have been taken)* | 8:s23 (p348) |
| SPI-8-16 | MUST | master | scenario | Responses must come out in command order. | 8:s24 (p350) |
| SPI-8-17 | MUST | master | scenario | Transfer N+1 starts at that edge; at A_N + 32·D byte N+1 becomes held and the burst enters Pause or Trail because o_cmd_ready was forced 0. *(when: i_rsp_ready stays 0 after byte N is shown at A_N + 16·D)* | 8:s57, 8:s58, 8:s59, 8:s60, 8:s61 (p386) |
| SPI-8-18 | MUST | master | scenario | Byte N is taken at edge H, byte N+1 is loaded at H with o_rsp_valid staying 1 and taken at H+1, then o_cmd_ready returns to 1 in Pause. *(when: Back-pressure with held byte, when i_rsp_ready goes to 1)* | 8:s62, 8:s63, 8:s64, 8:s65 (p389) |

## 9 Registers

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-9-01 | MUST_NOT | system | none | The spi_master block must not provide any software-visible registers. | 9:s1 (p394) |

## 10 Errors and corner cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-10-01 | MUST_NOT | master | scenario | The master shall not detect or report a change of i_cpol or i_cpha while o_cs_n = 0. *(when: i_cpol or i_cpha changes while o_cs_n = 0)* | 10:s3 (p400) |
| SPI-10-02 | MUST | master | both | The master shall keep using CPOL_b and CPHA_b until the end of the burst. *(when: i_cpol or i_cpha changes while o_cs_n = 0)* | 10:s3 (p400) |
| SPI-10-03 | MUST | master | both | o_sclk shall change to i_cpol at the edge where o_cs_n rises. *(when: i_cpol differs from CPOL_b at the edge where o_cs_n rises)* | 10:s4 (p402) |
| SPI-10-04 | MUST | master | both | The command shall wait without effect until a command handshake occurs. *(when: i_cmd_valid = 1 while o_cmd_ready = 0)* | 10:s5 (p404) |
| SPI-10-05 | MUST_NOT | master | assertion | The master shall not accept the command. *(when: i_cmd_valid = 1 while i_rst_n = 0)* | 10:s6 (p406) |
| SPI-10-06 | MUST | master | both | The master shall keep o_rsp_valid = 1 with the same byte. *(when: the response consumer never takes a response)* | 10:s7 (p408) |
| SPI-10-07 | MUST_NOT | master | both | The master shall not start any further transfer. *(when: the response consumer never takes a response)* | 10:s7 (p408) |
| SPI-10-08 | MUST | master | both | o_cs_n shall stay 0 indefinitely. *(when: a burst is in Pause and no command ever arrives)* | 10:s8 (p410) |
| SPI-10-09 | MUST | master | both | o_cs_n shall go to 1 and o_sclk to i_cpol at once, even in the middle of an SCLK half period. *(when: i_rst_n is asserted during a transfer)* | 10:s9 (p412) |
| SPI-10-10 | MUST | master | scenario | The partial byte shall be discarded. *(when: i_rst_n is asserted during a transfer)* | 10:s9 (p412) |
| SPI-10-11 | MUST | master | both | The master shall go to the reset state of REQ-RST-002 to REQ-RST-006. *(when: i_rst_n is asserted in Pause, Trail or the Idle gap)* | 10:s10 (p414) |
| SPI-10-12 | MUST | master | scenario | Pending bytes shall be discarded. *(when: i_rst_n is asserted in Pause, Trail or the Idle gap)* | 10:s10 (p414) |
| SPI-10-13 | MUST | master | both | The received byte of that transfer shall load into o_rsp_data at that edge, with o_rsp_valid staying 1. *(when: a response handshake occurs at exactly edge A + 16·D of a transfer)* | 10:s11 (p416) |
| SPI-10-14 | MUST_NOT | master | none | The master shall not detect a timing violation on i_miso. *(when: a timing violation on i_miso occurs near a sampling edge)* | 10:s12 (p418) |
| SPI-10-15 | MUST | master | scenario | The burst never ends; o_cs_n stays 0 and transfers continue as commands arrive. *(when: i_cmd_last = 0 forever)* | 10:s16 (p425) |
| SPI-10-16 | MUST | master | both | The half-period count shall reach 255 without overflow, giving 255-cycle half periods and 4080 cycles per byte. *(when: D = 255)* | 10:s18 (p427) |

## 11 Configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-11-01 | MUST | system | scenario | Verification must run every listed configuration, and since SPI mode is a run-time input, each configuration must be exercised in all four SPI modes. *(when: for each configuration CFG-BASE, CFG-MIN, CFG-MAX)* | 11:s1, 11:s4, 11:s5 (p434) |
| SPI-11-02 | MUST | system | both | With PARA_SPI_CLK_DIV=1, the smallest legal divider, SCLK must be f(i_clk)/2 and operate correctly in all four SPI modes. *(when: PARA_SPI_CLK_DIV=1 (CFG-MIN))* | 11:s2 (p435) |
| SPI-11-03 | MUST | system | scenario | With PARA_SPI_CLK_DIV=255, the largest legal divider, the half-period counter must work at full width and operate correctly in all four SPI modes with short bursts. *(when: PARA_SPI_CLK_DIV=255 (CFG-MAX))* | 11:s3 (p436) |

## 12 Verification requirements

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-12-01 | MUST | system | assertion | The environment shall release i_rst_n synchronously to i_clk. | 12:s2 (p444) |
| SPI-12-02 | MAY | system | scenario | Assertion of i_rst_n may be asynchronous. | 12:s3 (p444) |
| SPI-12-03 | MUST | system | assertion | The environment shall keep i_cmd_valid = 0 while i_rst_n = 0. *(when: while i_rst_n = 0)* | 12:s4 (p446) |
| SPI-12-04 | MUST | system | assertion | The environment shall change i_cpol and i_cpha only while o_cs_n = 1. | 12:s5 (p448) |
| SPI-12-05 | MAY | system | scenario | Error tests may deliberately violate the rule that i_cpol and i_cpha change only while o_cs_n = 1. *(when: error tests checking REQ-ERR-001)* | 12:s6 (p448) |
| SPI-12-06 | MUST | system | none | The SPI slave testbench model shall drive i_miso as a function of o_sclk and o_cs_n only. | 12:s7 (p450) |
| SPI-12-07 | MUST | system | scenario | The slave shall put bit 7 on i_miso when o_cs_n falls and the next bit after each trailing SCLK edge. *(when: CPHA = 0)* | 12:s8 (p450) |
| SPI-12-08 | MUST | system | scenario | The slave shall put bit 7 − j on i_miso after leading SCLK edge 2·j + 1. *(when: CPHA = 1)* | 12:s9 (p450) |
| SPI-12-09 | MUST | system | assertion | The slave model shall change i_miso only after the i_clk edge at which o_sclk or o_cs_n changed, never altering the value seen at a sampling edge. | 12:s10 (p452) |
| SPI-12-10 | MUST_NOT | system | assertion | The environment shall not assert i_rst_n at an i_clk edge; assertion happens between edges. | 12:s11 (p454) |
| SPI-12-11 | MUST_NOT | system | none | An edge coinciding with i_rst_n assertion is not a legal case and no check covers it. *(when: i_rst_n assertion coincides with a clock edge)* | 12:s12 (p454) |
| SPI-12-12 | MUST | system | scenario | The environment shall drive i_rst_n = 0 from time zero, before the first rising i_clk edge, for at least 2 cycles. *(when: from start of operation)* | 12:s13 (p456) |
| SPI-12-13 | MUST | system | assertion | i_cpol, i_cpha and every other input shall always be 0 or 1, never X or Z. | 12:s14 (p456) |
| SPI-12-14 | MUST_NOT | system | none | Outputs are undefined and no check applies before the first assertion of i_rst_n. *(when: before the first assertion of i_rst_n)* | 12:s14 (p456) |
| SPI-12-15 | MUST | system | none | i_miso shall meet setup and hold time to i_clk at each sampling edge; with D = 1, slave clock-to-output plus board round trip must fit in one period minus setup. *(when: in silicon, at each sampling edge)* | 12:s15, 12:s16 (p458) |
| SPI-12-16 | MAY | system | scenario | The command stream may change i_cmd_valid, i_cmd_data and i_cmd_last before acceptance; stability is not required. *(when: before acceptance)* | 12:s17 (p460) |
| SPI-12-17 | MAY | system | scenario | The response consumer may drive i_rsp_ready with any pattern. | 12:s18 (p460) |
| SPI-12-18 | MUST | system | scenario | Verification shall run all four modes in every configuration of section 11, with random bytes on i_cmd_data and from the slave model. | 12:s20 (p464) |
| SPI-12-19 | MUST | system | scenario | Verification shall use burst lengths 1, 2 and at least 16, mixing bursts with and without pauses (i_cmd_valid gaps of 0, 1 and many cycles). | 12:s21 (p466) |
| SPI-12-20 | MUST | system | scenario | A scoreboard shall check each response equals the byte sent by the slave during the matching command, in order, with no loss or duplicate. | 12:s22 (p468) |
| SPI-12-21 | MUST | system | both | A slave-side monitor shall check MOSI data at every sampling edge and the SCLK edge times (A + k·D). | 12:s23 (p470) |
| SPI-12-22 | MUST | system | both | The monitor shall also check lead, trail and gap times, the SCLK idle level and that o_mosi never changes at a sampling edge. | 12:s24 (p470) |
| SPI-12-23 | MUST | system | assertion | Verification shall check o_cmd_ready cycle by cycle against REQ-CMD-006 to REQ-CMD-012, including the blocked first D − 1 Idle cycles. | 12:s25 (p472) |
| SPI-12-24 | MUST | system | scenario | Back-pressure tests shall hold i_rsp_ready = 0 for long periods so that a held byte is created. | 12:s26 (p474) |
| SPI-12-25 | MUST | system | scenario | Back-pressure tests shall cover a response handshake exactly at edge A + 16·D (REQ-ERR-009) and random i_rsp_ready patterns. | 12:s27 (p474) |
| SPI-12-26 | MUST | system | scenario | Reset tests shall hold i_rsp_ready = 0 before reset where a shown or held byte is wanted, and assert i_rst_n between i_clk edges in each phase (Transfer, Pause, Trail, Idle gap, held byte). | 12:s28 (p476) |
| SPI-12-27 | MUST | system | both | Reset tests shall check that outputs take reset values at once and no response of the aborted transfer appears. *(when: reset tests)* | 12:s29 (p476) |
| SPI-12-28 | MUST | system | scenario | A test shall toggle i_cpol while i_rst_n = 0 and in Idle, and check o_sclk follows it in the same cycle. | 12:s30 (p478) |
| SPI-12-29 | MUST | system | scenario | A test shall change i_cpol and i_cpha in the cycle just before a burst-start acceptance edge and check the new values are used. | 12:s31 (p480) |
| SPI-12-30 | MUST | system | scenario | An error test shall change i_cpol and i_cpha during a burst and check the burst finishes in the captured mode. | 12:s32 (p482) |
| SPI-12-31 | MUST | system | scenario | Coverage shall include mode × configuration, continuous join, pause entry and exit, held byte created and released, reset in each phase, and i_cmd_last = 1 on the first byte. | 12:s33, 12:s34, 12:s35, 12:s36, 12:s37, 12:s38, 12:s39 (p484) |
| SPI-12-32 | MUST | system | scenario | REQ-PAR-001 shall be checked by elaborating once with an illegal value, not by simulation. | 12:s43 (p496) |

## 13 Implementation constraints

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-13-01 | MUST | system | none | The block shall meet timing at 50 MHz i_clk (20 ns period) in GF180MCU technology at worst-case corner. | 13:s1 (p500) |
| SPI-13-02 | MUST | system | none | The RTL shall follow docs/RTL_RULES.md (REF-003). | 13:s2 (p502) |
| SPI-13-03 | MUST | system | scenario | All flip-flops shall be clocked on the rising edge of i_clk and reset asynchronously by i_rst_n. | 13:s3 (p504) |
| SPI-13-04 | MUST_NOT | system | none | The RTL shall contain no latches, no clock gating and no derived clocks. | 13:s4 (p504) |
| SPI-13-05 | MUST | system | none | o_cs_n and o_mosi shall be driven directly by flip-flops. | 13:s5 (p506) |
| SPI-13-06 | MUST | system | none | o_sclk shall come from a flip-flop value while o_cs_n = 0. *(when: While o_cs_n = 0)* | 13:s6 (p508) |
| SPI-13-07 | MUST | system | none | The only combinational path from an input to o_sclk shall be the i_cpol path, used while o_cs_n = 1 or during reset. | 13:s7 (p508) |
| SPI-13-08 | SHOULD | system | assertion | o_sclk should be free of glitches when o_cs_n changes. *(when: When o_cs_n changes)* | 13:s8 (p510) |
| SPI-13-09 | SHOULD | system | none | The selection between i_cpol and the internal SCLK value should be built so equal inputs give no static hazard. | 13:s9 (p510) |
| SPI-13-10 | MUST | system | none | o_cmd_ready, o_rsp_valid and o_rsp_data shall be driven by flip-flops or logic of flip-flops only, with no combinational path from any input. | 13:s10, 13:s11 (p512) |
| SPI-13-11 | MUST | system | none | i_miso shall be captured directly into a data flip-flop with no synchroniser. | 13:s12 (p514) |
| SPI-13-12 | MUST | any | none | The integrator shall constrain the input delay of i_miso. | 13:s13 (p514) |
| SPI-13-13 | MUST | system | scenario | The half-period counter shall be wide enough for D = 255, at least 8 bits. | 13:s14 (p516) |

## 14 Decisions and open questions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SPI-14-01 | MUST | master | both | The master shall use exactly D cycles for lead and exactly D cycles for trail. | 14:s1 (p524) |
| SPI-14-02 | MUST | master | both | The gap between transfers shall be at least D cycles, and exactly D cycles when the next command is already waiting. *(when: between bursts, o_cs_n high gap)* | 14:s1 (p524) |
| SPI-14-03 | MUST_NOT | master | both | A command shall be accepted only in Idle (after D − 1 blocked cycles), in Pause, or in the last cycle of a non-last transfer, and only if o_rsp_valid = 0. | 14:s2 (p525) |
| SPI-14-04 | MUST_NOT | master | none | o_cmd_ready shall have no combinational input path. | 14:s2 (p525) |
| SPI-14-05 | MUST_NOT | master | both | A transfer shall start only when o_rsp_valid = 0; no byte is lost, as one more byte can be held inside the master. | 14:s3 (p526) |
| SPI-14-06 | MUST | master | both | The response shall appear at SCLK edge 16 (A + 16·D) in all modes, also for CPHA = 0 where the last bit is sampled at edge 15. *(when: all modes, including CPHA = 0)* | 14:s4 (p527) |
| SPI-14-07 | MUST | master | both | o_mosi shall hold its last value, and be 0 after reset. *(when: outside transfers, and with CPHA = 1 before edge 1)* | 14:s5 (p528) |
| SPI-14-08 | MUST | master | both | While o_cs_n = 1, o_sclk shall be combinational from i_cpol; while o_cs_n = 0 it shall be registered from the captured CPOL_b. *(when: during reset and Idle)* | 14:s6 (p529) |
| SPI-14-09 | MUST | master | both | Mode input changes during a burst shall be ignored; captured values shall be used until o_cs_n rises. *(when: mode inputs change during a burst)* | 14:s7 (p530) |
| SPI-14-10 | MUST | master | both | Reset in the middle of a burst shall abort immediately and discard pending bytes; the gap guarantee does not apply across reset. *(when: reset asserted mid-burst)* | 14:s8 (p531) |
| SPI-14-11 | MUST | system | scenario | An illegal PARA_SPI_CLK_DIV shall cause an elaboration error. *(when: illegal PARA_SPI_CLK_DIV)* | 14:s9 (p532) |
| SPI-14-12 | MUST | master | both | o_rsp_data shall be 8'h00 after reset and otherwise keep the last loaded byte while not valid. | 14:s11 (p534) |
| SPI-14-13 | MUST_NOT | system | none | Reset asserted at an i_clk edge is not a legal case (ENV-007). | 14:s12 (p535) |
| SPI-14-14 | MUST | system | none | Outputs are undefined before the first reset, and inputs shall always be 0 or 1, never X (ENV-008). *(when: before the first reset)* | 14:s13 (p536) |
| SPI-14-15 | SHOULD | system | scenario | i_rsp_ready should be held at 0 before reset where a held byte is wanted. *(when: before reset where a held byte is wanted)* | 14:s14 (p537) |
| SPI-14-16 | MUST | master | assertion | For D = 1 in Idle, o_cmd_ready shall equal NOT o_rsp_valid from the cycle o_cs_n rises. *(when: D = 1 in Idle)* | 14:s16 (p539) |
| SPI-14-17 | MUST_NOT | master | both | A transfer shall start only when o_rsp_valid = 0 at the acceptance edge; there shall be no combinational path from i_rsp_ready to o_cmd_ready. | 14:s17 (p540) |
| SPI-14-18 | MAY | master | scenario | D = 1 stays legal and is verified in simulation; silicon timing is an integrator duty (ENV-006). | 14:s18 (p541) |
| SPI-14-19 | MUST | master | both | o_mosi shall hold its last value outside transfers rather than being driven to 0 or 1. *(when: outside transfers)* | 14:s19 (p542) |
| SPI-14-20 | MUST | master | both | There is no Pause timeout; o_cs_n shall stay low in Pause until the next command. *(when: in Pause)* | 14:s21 (p544) |
| SPI-14-21 | MUST_NOT | master | scenario | The master shall not enforce o_cs_n high for at least D cycles after reset release; the minimum gap is not guaranteed across reset. *(when: after reset release)* | 14:s22 (p545) |
| SPI-14-22 | MUST | system | none | CFG-MAX (D = 255) shall stay in the run set. | 14:s23 (p546) |
