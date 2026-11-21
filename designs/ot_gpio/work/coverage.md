# Coverage closure

Metric **toggle**, target 90.0 %, status **target_unmet**.

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
| baseline | 87.5 % (69874/79856) | | | |
| 2 | None % (None/None) | 0 |  | no scenario with legal, specification-level stimulus |

## Points claimed unreachable by legal stimulus (designer review; still counted)

| Points | Rules | Reason |
|---|---|---|
| gpio.sv:43 racl_error_o.request_address, gpio_reg_top.sv:26 racl_error_o.request_address, gpio.sv:42 racl_policies_i, gpio_reg_top.sv:25 racl_policies_i, gpio.sv:43 racl_error_o.ctn_uid, gpio.sv:43 racl_error_o.overflow, gpio.sv:43 racl_error_o.racl_role, gpio.sv:43 racl_error_o.read_access, gpio.sv:43 racl_error_o.valid | GP-1-01 | RACL is disabled in this configuration. The wrapper ties the RACL policy input to zero and leaves the RACL error output unconnected, so no access is ever rejected and these signals stay constant. |
| gpio.sv:31 tl_i.a_address, gpio_reg_top.sv:18 tl_i.a_address, gpio_reg_top.sv:52 tl_reg_h2d.a_address, ot_gpio_nnc.sv:29 i_a_address, ot_gpio_nnc.sv:67 tl_h2d.a_address, ot_gpio_nnc.sv:67 tl_h2d_intg.a_address, ot_gpio_nnc.sv:67 tl_h2d_raw.a_address, tlul_adapter_reg.sv:111 tl_i.a_address, tlul_cmd_intg_chk.sv:13 tl_i.a_address, tlul_cmd_intg_chk.sv:21 cmd.addr, tlul_cmd_intg_gen.sv:15 tl_i.a_address, tlul_cmd_intg_gen.sv:16 tl_o.a_address, tlul_cmd_intg_gen.sv:19 cmd.addr, tlul_cmd_intg_gen.sv:21 unused_cmd_payload, tlul_err.sv:12 tl_i.a_address, prim_secded_inv_64_57_dec.sv:8 data_i, prim_secded_inv_64_57_dec.sv:9 data_o, prim_secded_inv_64_57_enc.sv:8 data_i, prim_secded_inv_64_57_enc.sv:9 data_o | GP-10-21, CHK-011 | Address bits 10 and up stay 0 because legal requests must use offsets below 0x400 (D-012, monitor rule (d)). The command-integrity encoder and decoder inputs and outputs from payload bit 17 up are either those address bits or fixed zero padding of the 57-bit payload, so they never toggle. The same applies to the response-integrity encoder, whose payload is only 6 bits wide. |
| gpio.sv:31 tl_i.a_param, gpio_reg_top.sv:18 tl_i.a_param, gpio_reg_top.sv:52 tl_reg_h2d.a_param, ot_gpio_nnc.sv:26 i_a_param, ot_gpio_nnc.sv:67 tl_h2d.a_param, ot_gpio_nnc.sv:67 tl_h2d_intg.a_param, ot_gpio_nnc.sv:67 tl_h2d_raw.a_param, tlul_adapter_reg.sv:111 tl_i.a_param, tlul_cmd_intg_chk.sv:13 tl_i.a_param, tlul_cmd_intg_gen.sv:15 tl_i.a_param, tlul_cmd_intg_gen.sv:16 tl_o.a_param, tlul_err.sv:12 tl_i.a_param | GP-10-44 | D-022: tests drive i_a_param = 0. A non-zero a_param is out of scope, so the A-channel a_param path stays constant. |
| tlul_rsp_intg_gen.sv:31 tl_i.d_param, tlul_rsp_intg_gen.sv:32 tl_o.d_param, gpio.sv:32 tl_o.d_param, gpio_reg_top.sv:19 tl_o.d_param, gpio_reg_top.sv:53 tl_reg_d2h.d_param, gpio_reg_top.sv:90 tl_o_pre.d_param, ot_gpio_nnc.sv:68 tl_d2h.d_param, tlul_adapter_reg.sv:112 tl_o.d_param, tlul_adapter_reg.sv:229 tl_o_pre.d_param, tlul_rsp_intg_chk.sv:15 tl_i.d_param, tlul_rsp_intg_gen.sv:31 tl_i.d_sink, tlul_rsp_intg_gen.sv:32 tl_o.d_sink, gpio.sv:32 tl_o.d_sink, gpio_reg_top.sv:19 tl_o.d_sink | GP-10-27, GP-10-44 | The device always returns d_param = 0 and d_sink = 0 (fixed response fields, and D-015 does not check them). No port stimulus changes them. |
| tlul_rsp_intg_gen.sv:31 tl_i.d_opcode, tlul_rsp_intg_gen.sv:32 tl_o.d_opcode, gpio.sv:32 tl_o.d_opcode, gpio_reg_top.sv:19 tl_o.d_opcode, gpio_reg_top.sv:53 tl_reg_d2h.d_opcode, gpio_reg_top.sv:90 tl_o_pre.d_opcode, ot_gpio_nnc.sv:38 o_d_opcode, ot_gpio_nnc.sv:68 tl_d2h.d_opcode, tlul_adapter_reg.sv:112 tl_o.d_opcode, tlul_adapter_reg.sv:148 rspop_q, tlul_adapter_reg.sv:229 tl_o_pre.d_opcode, tlul_rsp_intg_chk.sv:15 tl_i.d_opcode, tlul_rsp_intg_chk.sv:22 rsp.opcode, tlul_rsp_intg_gen.sv:37 gen_rsp_intg.rsp.opcode, tlul_rsp_intg_gen.sv:38 gen_rsp_intg.unused_payload, gpio.sv:32 tl_o.d_user.rsp_intg | GP-10-27, TL-T3.1.3.5-08 | The only response opcodes are AccessAck (0) and AccessAckData (1), so d_opcode bits 1 and 2 are always 0. That holds for error responses too. The matching payload bits of the response-integrity encoder are also constant, and so is response-integrity bit 6 at the gpio boundary, because the only payload bit it depends on is d_opcode bit 1. |
| gpio.sv:31 tl_i.a_user.rsvd, gpio_reg_top.sv:18 tl_i.a_user.rsvd, gpio_reg_top.sv:52 tl_reg_h2d.a_user.rsvd, ot_gpio_nnc.sv:67 tl_h2d.a_user.rsvd, ot_gpio_nnc.sv:67 tl_h2d_intg.a_user.rsvd, ot_gpio_nnc.sv:67 tl_h2d_raw.a_user.rsvd, tlul_adapter_reg.sv:111 tl_i.a_user.rsvd, tlul_cmd_intg_chk.sv:13 tl_i.a_user.rsvd, tlul_cmd_intg_gen.sv:15 tl_i.a_user.rsvd, tlul_cmd_intg_gen.sv:16 tl_o.a_user.rsvd, tlul_err.sv:12 tl_i.a_user.rsvd | GP-4.1-02 | The wrapper sets a_user.rsvd to a constant 0. It is not a port, so the test bench cannot drive it. |
| ot_gpio_nnc.sv:67 tl_h2d_raw.a_user.cmd_intg, ot_gpio_nnc.sv:67 tl_h2d_raw.a_user.data_intg, tlul_cmd_intg_gen.sv:15 tl_i.a_user.cmd_intg, tlul_cmd_intg_gen.sv:15 tl_i.a_user.data_intg | GP-4.2-01, GP-10-44 | The wrapper builds the raw request with fixed default a_user integrity fields and then replaces them with integrity it computes itself. The raw fields are therefore constant and cannot be driven from a port. |
| prim_secded_inv_39_32_dec.sv:10 syndrome_o, prim_secded_inv_39_32_dec.sv:11 err_o, tlul_data_integ_dec.sv:17 data_err | GP-4.2-01, GP-4.2-02 | The wrapper always generates correct A-channel data integrity. Its only fault-injection input (i_a_intg_flip) inverts bit 0 of the command integrity and never touches the data integrity, so the write-data integrity decoder never sees a syndrome or error. |
| prim_secded_inv_64_57_dec.sv:10 syndrome_o | GP-4.2-02 | Command-integrity corruption can only invert bit 0 of cmd_intg, which produces a single-bit syndrome in bit 0 only. Syndrome bits 1 to 6 would need other integrity or payload bits to be corrupted, and no port can do that. |
| tlul_rsp_intg_gen.sv:31 tl_i.d_user.data_intg, tlul_rsp_intg_gen.sv:31 tl_i.d_user.rsp_intg, tlul_rsp_intg_gen.sv:32 tl_o.d_user.rsp_intg, gpio_reg_top.sv:53 tl_reg_d2h.d_user.data_intg, gpio_reg_top.sv:53 tl_reg_d2h.d_user.rsp_intg, gpio_reg_top.sv:90 tl_o_pre.d_user.data_intg, gpio_reg_top.sv:90 tl_o_pre.d_user.rsp_intg, tlul_adapter_reg.sv:112 tl_o.d_user.data_intg, tlul_adapter_reg.sv:112 tl_o.d_user.rsp_intg, tlul_adapter_reg.sv:229 tl_o_pre.d_user.data_intg, tlul_adapter_reg.sv:229 tl_o_pre.d_user.rsp_intg, tlul_rsp_intg_gen.sv:32 tl_o.d_user.data_intg | GP-4.3-01, GP-4.3-02, GP-10-44 | Response integrity (rsp_intg and data_intg) is generated only at the final stage that drives the bus. The intermediate response-path copies of d_user, from the register adapter up to the input of the generator, are wired to zero, so they never toggle under any stimulus. The bit layout of d_user is also out of scope (D-022). |
| tlul_rsp_intg_chk.sv:21 rsp_err | GP-4.3-01, GP-4.3-02, TL-T3.1.3.3-02 | The response-integrity checker in the wrapper only reports an error when a D beat carries wrong integrity. The DUT always generates correct response integrity, and CHK-005 requires o_d_intg_err = 0 in every cycle, so the checker's error bits stay at 0. |
| prim_onehot_check.sv:61 err_tree | GP-4.2-01, GP-4.2-02, RG-T1.4.1-01 | The error tree of the write-enable one-hot check only toggles when two register write strobes are active at once. Each TL-UL request decodes exactly one address, so legal stimulus can never produce more than one strobe. The only fault injection available (i_a_intg_flip) corrupts command integrity and cannot create multi-hot strobes. |
| prim_onehot_check.sv:60 and_tree, prim_buf.sv:9 out_o, prim_onehot_check.sv:40 oh_i, prim_reg_we_check.sv:22 oh_buf, prim_onehot_check.sv:59 or_tree, prim_buf.sv:12 inv | RG-T1.5.3-01 | Write-enable vector bits 4, 16 and 17 belong to the read-only registers DATA_IN, HW_STRAPS_DATA_IN_VALID and HW_STRAPS_DATA_IN. Read-only registers have no write enable, so these bits are tied to 0, along with their buffer copies. The listed and-tree and or-tree nodes are either on that constant-zero path (the address check is off and its address input is tied to zero) or above leaves that are tied off past the last register, so they never toggle. |
| prim_subreg.sv:24 wd, prim_subreg_arb.sv:17 wd, prim_subreg_arb.sv:47 gen_ro.unused_wd | RG-T1.5.3-01, GP-T5.19-01 | HW_STRAPS_DATA_IN is read-only, so its write-data input is tied to zero. Software writes to it have no effect. |
| gpio.sv:143 unused_per_pin_intr_ctrl_qe | GP-T5.22-01, GP-T3.2.2-01 | This signal is the XOR of the four field write strobes of a PER_PIN_INTR_CTRL_i register. All fields of the register share one write strobe, so the XOR of four equal bits is always 0, whatever is written. |
| gpio.sv:28 sampled_straps_o.data, gpio_reg_top.sv:199 hw_straps_data_in_qs, ot_gpio_nnc.sv:62 o_straps_data, ot_gpio_nnc.sv:71 sampled_straps.data | GP-T5.19-02, GP-10-14 | These points are missing only in the configurations with GpioAsHwStrapsEn=0. There, strap sampling is absent and HW_STRAPS_DATA_IN and the strap data output are fixed at 0. In the GpioAsHwStrapsEn=1 configurations, CHK-031 already toggles every bit (sample S, reset, sample the complement S2). |
| prim_filter_ctr.sv:25 thresh_i | GP-T2.2-05, GP-T3.2.3-03 | The input-filter threshold is a fixed design constant (the specified 16-cycle stability window), not something software can program. Its bits never return to 0 after initialisation. |
| gpio.sv:38 alert_rx_i, ot_gpio_nnc.sv:69 alert_rx | GP-1-03, AH-T1.3.4-03 | The wrapper's alert receiver never issues ping requests (its ping request input is tied to 0), so the ping differential pair never toggles. |
