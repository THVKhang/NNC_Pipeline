# Coverage closure

Metric **functional**, target 100.0 %, status **target_unmet**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 11212/11616 | 96.5 % |
| block | 1090/1164 | 93.6 % |
| expression | 6600/10174 | 64.9 % |
| toggle | 69874/79856 | 87.5 % |
| functional | 38/40 | 95.0 % |

Design scope: left out: never-executed points of package code that the elaborated design does not contain (Verilator instruments every function of an imported package, called or not), and toggles of signal bits that Yosys constant propagation proves constant with the run's parameters, except on signals where the simulator recorded a toggle of such a bit (then the signal counts whole). Left out:
- block: 1288 points (over all points 1090/2452, 44.5 %)
- expression: 21732 points (over all points 6600/31906, 20.7 %)
- line: 9736 points (over all points 11212/21352, 52.5 %)
- toggle: 3328 points (over all points 69898/83184, 84.0 %)

### Functional cover points never hit

- COVP-012: Back-to-back A handshakes
- COVP-013: Two or more outstanding requests

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | gpio_reg_top.sv | 8 | 6161, 6162 |
| block | prim_alert_receiver.sv | 16 | 178, 207, 229, 236 |
| block | prim_alert_sender.sv | 28 | 229, 230, 238, 239, 253 |
| block | prim_subreg.sv | 22 | 61, 63 |
| expression | gpio.sv | 800 | 155, 177, 199, 221, 243, 265, 287, 309, 331, 353, 375, 397, 419, 441, 463 |
| line | gpio.sv | 10 | 28, 42, 143 |
| line | gpio_reg_top.sv | 184 | 25, 50, 170, 176, 198, 199, 1384, 1424, 1464, 1504, 1544, 1584, 1624, 1664, 1704, 1744, 1784, 1824, 1864, 1904, 1944, 1984, 2024, 2064, 2104, 2144, 2184, 2224, 2264, 2304, 2344, 2384, 2424, 2464, 2504, 2544, 2584, 2624, 6021, 6022, 6162, 6163, 6164, 6166, 6167, 7769, 7783 |
| line | ot_gpio_nnc.sv | 22 | 26, 39, 42, 45, 61, 62, 71 |
| line | prim_alert_receiver.sv | 68 | 48, 49, 98, 101, 102, 104, 179, 207, 208, 229, 236, 237, 238, 239, 240, 241, 242 |
| line | prim_alert_sender.sv | 44 | 229, 230, 231, 232, 233, 234, 238, 239, 240, 241, 253 |
| line | prim_onehot_check.sv | 8 | 41, 61 |
| line | prim_secded_inv_39_32_dec.sv | 8 | 10, 11 |
| line | prim_subreg.sv | 12 | 19, 61, 62 |
| line | prim_subreg_arb.sv | 8 | 46, 47 |
| line | tlul_adapter_reg.sv | 8 | 116, 124 |
| line | tlul_cmd_intg_chk.sv | 4 | 20 |
| line | tlul_data_integ_dec.sv | 8 | 14, 17 |
| line | tlul_err.sv | 8 | 31, 35 |
| line | tlul_rsp_intg_chk.sv | 12 | 18, 21, 32 |
| toggle | gpio.sv | 960 | 28, 31, 32, 38, 42, 43, 143 |
| toggle | gpio_reg_top.sv | 1516 | 18, 19, 25, 26, 52, 53, 90, 198, 199, 1384, 1424, 1464, 1504, 1544, 1584, 1624, 1664, 1704, 1744, 1784, 1824, 1864, 1904, 1944, 1984, 2024, 2064, 2104, 2144, 2184, 2224, 2264, 2304, 2344, 2384, 2424, 2464, 2504, 2544, 2584, 2624, 7783 |
| toggle | ot_gpio_nnc.sv | 1332 | 26, 29, 38, 45, 61, 62, 67, 68, 69, 71 |
| toggle | prim_alert_receiver.sv | 32 | 49, 56, 99 |
| toggle | prim_alert_sender.sv | 48 | 65, 74, 155, 156 |
| toggle | prim_buf.sv | 36 | 9, 12 |
| toggle | prim_filter_ctr.sv | 16 | 25 |
| toggle | prim_onehot_check.sv | 1008 | 40, 59, 60, 61, 107 |
| toggle | prim_reg_we_check.sv | 24 | 22 |
| toggle | prim_secded_inv_39_32_dec.sv | 72 | 10, 11 |
| toggle | prim_secded_inv_64_57_dec.sv | 632 | 8, 9, 10, 11 |
| toggle | prim_secded_inv_64_57_enc.sv | 576 | 8, 9 |
| toggle | prim_subreg.sv | 292 | 19, 23, 24, 27, 31, 41 |
| toggle | prim_subreg_arb.sv | 540 | 16, 17, 20, 27, 46, 47 |
| toggle | tlul_adapter_reg.sv | 576 | 111, 112, 148, 229 |
| toggle | tlul_cmd_intg_chk.sv | 432 | 13, 19, 20, 21 |
| toggle | tlul_cmd_intg_gen.sv | 888 | 15, 16, 19, 21 |
| toggle | tlul_data_integ_dec.sv | 24 | 14, 17 |
| toggle | tlul_err.sv | 256 | 12, 31, 35 |
| toggle | tlul_rsp_intg_chk.sv | 96 | 15, 18, 21, 22 |
| toggle | tlul_rsp_intg_gen.sv | 576 | 31, 32, 35, 37, 38 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 90.0 % (36/40) | | | |
| 1 | 95.0 % (38/40) | 2 | test_cov_101_putpartial_fullword, test_cov_102_mask_size_combinations |  |
| 2 | None % (None/None) | 0 |  | no scenario with legal, specification-level stimulus |

## Points claimed unreachable by legal stimulus (designer review; still counted)

| Points | Rules | Reason |
|---|---|---|
| nnc_cov.sv:0 COVP-012, nnc_cov.sv:0 COVP-013 | GP-10-26, GP-4.1-04, GP-4.1-01, TL-T2.2-03 | The device accepts only one request at a time: it holds o_a_ready low from the moment it accepts a request until that request's response has been taken. So there can never be two accepted requests waiting for an answer, and never two A handshakes in consecutive cycles. The only edges where the host could repeat a handshake are the cycles straight after an acceptance, and a_ready is 0 then. The rules allow this. D-014 (GP-10-26) only says the host must not assume o_a_ready=1, and no rule makes the device take more than one request at a time. The host rules (GP-4.1-04, CHK-011 a) say a request must be held while a_ready is 0, so the test bench cannot force a second acceptance. Evidence: the existing outstanding/back-pressure test (CHK-038) and the random regression already queue hundreds of requests and drive them back to back with no gap. They do this with and without D-channel back-pressure, in both GpioAsyncOn settings. Neither point was hit. |
| nnc_cov.sv:0 COVP-012, nnc_cov.sv:0 COVP-013 | GP-4.1-01, GP-4.1-04, GP-10-26, TL-T2.2-03, GP-10-31, GP-10-32 | The two points are COVP-012 (A handshakes in two consecutive cycles) and COVP-013 (two or more accepted requests not yet answered). Both need the device to accept a new request while the previous response is still pending. Only the device drives a_ready (GP-4.1-01: TL-UL device interface). The host must hold a request with the same fields until a_ready=1 (GP-4.1-04, CHK-011(a)), and the test bench may not assume a_ready=1 (GP-10-26 / D-014). So no legal stimulus can force a second acceptance. The gpio register interface takes a new request only after the D handshake of the previous one: a_ready is low while a response is pending. The tests already do what would otherwise hit these points. CHK-038 and the random regression keep i_a_valid high back-to-back with zero or random 0-2 cycle gaps, use distinct a_source values, and run 1700+ requests with long stretches of i_d_ready=1. Neither point was hit, which shows the device never accepts in consecutive cycles and never holds two requests. Reset cannot make a stale entry count either: D-016 (GP-10-31/GP-10-32) discards a response pending at reset, so the outstanding count is cleared at reset. CHK-030 accepts a Get under back-pressure, resets, and then sends new requests, and that did not hit COVP-013. A request with i_a_intg_flip=1 still gets at most one response through the same single-request flow control, so it cannot create a second outstanding request. The only way to reach these points would be a device that accepts requests before answering earlier ones, and this design does not do that. |
