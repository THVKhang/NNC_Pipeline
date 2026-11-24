# Verification report — c_uart

Generated 2026-11-24T08:31:14+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 6 — {'FAILED': 6} |
| Checks | 11 — {'FAIL': 5, 'PASS': 6} |
| Tests | {'fail': 3, 'pass': 5} |
| Run set | 2 runs in 2 configurations (base, xrand); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 97.6 % (120/123 lines) |
| Code coverage (RTL), block | 97.6 % (41/42 statement blocks and branch arms); 2 points left out (package code the design does not contain), all points 93.2 % (41/44) |
| Code coverage (RTL), expression | 88.9 % (8/9 condition terms) |
| Code coverage (RTL), toggle | 67.6 % (250/370 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 90.0 % (36/40 cover points of the specification) |
| Mutation score | 83.3 % (10 killed / 2 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Clock/reset domain crossings (structural, `nnc cdc`) | clean: no crossing over 1 configuration(s), work/cdc.md |
| Triage | 4 failure(s), 4 analysed: work/triage.md |
| Agent cost | US$2.8069 in 12 calls (A1 0.0284, A12 0.1042, A2 0.0374, A3 0.0191, A4 0.2472, A5 0.0514, A6 0.2332, A7 1.2352, A9 0.8509) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | **not met** — FAIL 5 |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 2 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 6 rules with attributed mutants |
| Clock/reset domain crossings: no structural violation (RR-33) | met — clean: no crossing (work/cdc.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — the design configuration | defaults | — | — | ran | {'fail': 3, 'pass': 5} | CHK-001 | 0 |
| xrand.s1 — the design configuration with random initial values of every variable without a reset: a check that passes only because flops start at 0 fails here | defaults | — | — | ran | {'fail': 3, 'pass': 5} | CHK-001 | 0 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T09:57:44+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T09:59:43+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T10:10:46+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | m_axis output stalls (holds valid and data) while m_axis_tready is low | **FAIL** | hits 810, fails 2; fails in base.s1, xrand.s1 |
| CHK-002 | assertion | rx_overrun_error is a single-cycle pulse | **PASS** | hits 2, fails 0; hit in 2/2 runs |
| CHK-003 | assertion | rx_frame_error is a single-cycle pulse | **PASS** | hits 2, fails 0; hit in 2/2 runs |
| CHK-004 | assertion | tx_busy is high whenever txd is driving a low (frame) level | **PASS** | hits 25984, fails 0; hit in 2/2 runs |
| CHK-005 | test | RX path: each received frame gives exactly one m_axis transfer under backpressure | **FAIL** | test_chk_005_rx_backpressure, test_regression_random; failed in base.s1, xrand.s1 |
| CHK-006 | test | rx_busy is high while a reception is in progress and low when idle | **PASS** | test_chk_006_rx_busy; verified in base.s1, xrand.s1 |
| CHK-007 | test | Overrun: one-cycle rx_overrun_error pulse and the new word is discarded | **FAIL** | test_chk_007_rx_overrun; failed in base.s1, xrand.s1 |
| CHK-008 | test | Frame error: one-cycle rx_frame_error pulse and the received word is discarded | **FAIL** | test_chk_008_rx_frame_error; failed in base.s1, xrand.s1 |
| CHK-009 | test | TX path: words are accepted only on s_axis handshakes and sent once each, in order | **PASS** | test_chk_009_tx_handshake_order; verified in base.s1, xrand.s1 |
| CHK-010 | test | Prescale sets the data rate: bit period is 8*prescale clock cycles | **PASS** | test_chk_010_prescale_rate; verified in base.s1, xrand.s1 |
| CHK-011 | test | tx_busy is high while a transmission is in progress and low when idle | **FAIL** | test_chk_011_tx_busy, test_regression_random; failed in base.s1, xrand.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| UA-T1.3-01 |  | The prescale input must be set to Fclk / (baud * 8) to determine the data rate. | CHK-005:FAIL, CHK-009:PASS, CHK-010:PASS | 100.0 % (10/10) | **FAILED** |
| UA-T1.3-04 |  | The destination must not accept data unless tready is high. | CHK-005:FAIL, CHK-009:PASS | 100.0 % (5/5) | **FAILED** |
| UA-T1.3-05 |  | Data is transferred from source to destination only when both tvalid and tready are high; otherwise the bus is stalled and no transfer occurs. | CHK-001:FAIL, CHK-005:FAIL, CHK-007:FAIL, CHK-009:PASS | 100.0 % (10/10) | **FAILED** |
| UA-T1.3-06 |  | Both the transmitter and receiver interfaces drive busy high while an operation is taking place. | CHK-004:PASS, CHK-006:PASS, CHK-011:FAIL | 100.0 % (8/8) | **FAILED** |
| UA-T1.3-07 |  | The receiver emits a single-cycle pulse on overrun_error and discards the newly received word. | CHK-001:FAIL, CHK-002:PASS, CHK-007:FAIL | 100.0 % (5/5) | **FAILED** |
| UA-T1.3-08 |  | The receiver emits a single-cycle pulse on frame_error and discards the received word. | CHK-003:PASS, CHK-008:FAIL | 100.0 % (3/3) | **FAILED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | uart_rx.v:120 | eq_to_ne | killed | test_chk_005_rx_backpressure, test_chk_006_rx_busy, test_chk_010_prescale_rate | UA-T1.3-08, UA-T1.3-07, UA-T1.3-05, UA-T1.3-06, UA-T1.3-01 |  |
| M02 | uart_tx.v:105 | zero_to_one | survived |  |  | claimed: data_reg is 9 bits and bit_cnt starts at 9, so there are only 8 shifts at line 105. The bit shifted into data_reg[8] would reach txd only on a 9th shift, which  |
| M03 | uart_rx.v:107 | negate_if | killed | test_chk_005_rx_backpressure, test_chk_006_rx_busy, test_chk_010_prescale_rate | UA-T1.3-06, UA-T1.3-05, UA-T1.3-01, UA-T1.3-08, UA-T1.3-07 |  |
| M04 | uart_tx.v:97 | one_to_zero | survived |  |  | claimed: The top bit of data_reg (the constant 1 loaded here) is never shifted out. Only 8 shifts occur, which output data bits 0..7, and the stop bit is driven separate |
| M05 | uart_tx.v:89 | eq_to_ne | killed | test_chk_009_tx_handshake_order, test_chk_010_prescale_rate, test_chk_011_tx_busy | UA-T1.3-04, UA-T1.3-05, UA-T1.3-06, UA-T1.3-01 |  |
| M06 | uart_rx.v:101 | and_to_or | killed | test_chk_005_rx_backpressure | UA-T1.3-05, UA-T1.3-04, UA-T1.3-07, UA-T1.3-01 |  |
| M07 | uart_tx.v:102 | negate_if | killed | test_chk_009_tx_handshake_order, test_chk_010_prescale_rate, test_chk_011_tx_busy | UA-T1.3-01, UA-T1.3-06, UA-T1.3-05 |  |
| M08 | uart_rx.v:101 | negate_if | killed | test_chk_005_rx_backpressure, test_chk_006_rx_busy, test_chk_010_prescale_rate | UA-T1.3-05, UA-T1.3-04, UA-T1.3-07, UA-T1.3-01 |  |
| M09 | uart_tx.v:106 | eq_to_ne | killed | test_chk_009_tx_handshake_order, test_chk_010_prescale_rate, test_chk_011_tx_busy | UA-T1.3-01, UA-T1.3-06, UA-T1.3-05 |  |
| M10 | uart_tx.v:89 | negate_if | killed | test_chk_009_tx_handshake_order, test_chk_010_prescale_rate, test_chk_011_tx_busy | UA-T1.3-04, UA-T1.3-05, UA-T1.3-06, UA-T1.3-01 |  |
| M11 | uart_rx.v:105 | negate_if | killed | test_chk_005_rx_backpressure, test_chk_006_rx_busy, test_chk_010_prescale_rate | UA-T1.3-01, UA-T1.3-06, UA-T1.3-05, UA-T1.3-08, UA-T1.3-07 |  |
| M12 | uart_tx.v:93 | negate_if | killed | test_chk_009_tx_handshake_order, test_chk_010_prescale_rate, test_chk_011_tx_busy | UA-T1.3-04, UA-T1.3-05, UA-T1.3-06, UA-T1.3-01 |  |

## Not verified by this run

- Formal proof (`nnc config <ip> formal=on`) was not run.
- Domain crossings were checked structurally (synchronizer structure, `nnc cdc`); gray coding and handshake protocols are not proven by that check.
- Sign-off STA, place and route and DFT are outside this flow (docs/SIGNOFF_SCOPE.md); `nnc rtl-check` gives a synthesis estimate of area and the longest combinational path.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.
