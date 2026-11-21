# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 11212/21352 | 52.5 % |
| block | 1090/2452 | 44.5 % |
| expression | 6576/31906 | 20.6 % |
| toggle | 69898/83184 | 84.0 % |
| functional | 36/40 | 90.0 % |

### Functional cover points never hit

- COVP-003: Legal PutPartialData handshake
- COVP-012: Back-to-back A handshakes
- COVP-013: Two or more outstanding requests
- COVP-018: Mask covering inactive lanes

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | gpio_reg_top.sv | 8 | 6161, 6162 |
| block | prim_alert_receiver.sv | 16 | 178, 207, 229, 236 |
| block | prim_alert_sender.sv | 28 | 229, 230, 238, 239, 253 |
| block | prim_mubi_pkg.sv | 628 | 28, 36, 50, 57, 64, 87, 92, 93, 113, 118, 119, 131, 138, 145, 152, 167, 170, 175, 182, 189, 196, 203, 210, 226, 231, 232, 252, 257, 258, 270, 277, 284, 291, 306, 309, 314, 321, 328, 335, 342, 349, 365, 370, 371, 391, 396, 397, 409, 416, 423, 430, 445, 448, 453, 460, 467, 474, 481, 488, 504, 509, 510 ... |
| block | prim_secded_pkg.sv | 116 | 44, 46, 48, 49, 50, 51, 52, 53, 54, 56, 58, 59, 60, 61, 62, 63, 65, 67, 68, 69, 70, 71, 72, 73, 75, 77, 78, 79, 80 |
| block | prim_subreg.sv | 20 | 61 |
| expression | gpio.sv | 800 | 155, 177, 199, 221, 243, 265, 287, 309, 331, 353, 375, 397, 419, 441, 463 |
| line | gpio.sv | 8 | 42, 143 |
| line | gpio_reg_top.sv | 180 | 25, 50, 170, 176, 1384, 1424, 1464, 1504, 1544, 1584, 1624, 1664, 1704, 1744, 1784, 1824, 1864, 1904, 1944, 1984, 2024, 2064, 2104, 2144, 2184, 2224, 2264, 2304, 2344, 2384, 2424, 2464, 2504, 2544, 2584, 2624, 6021, 6022, 6162, 6163, 6164, 6166, 6167, 7769, 7783 |
| line | ot_gpio_nnc.sv | 16 | 26, 39, 42, 45 |
| line | prim_alert_receiver.sv | 68 | 48, 49, 98, 101, 102, 104, 179, 207, 208, 229, 236, 237, 238, 239, 240, 241, 242 |
| line | prim_alert_sender.sv | 44 | 229, 230, 231, 232, 233, 234, 238, 239, 240, 241, 253 |
| line | prim_mubi_pkg.sv | 484 | 28, 36, 37, 50, 51, 57, 58, 64, 65, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 99, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 125, 131, 132, 138, 139, 145, 146, 152, 153, 167, 170, 171, 175, 176, 182, 183, 189, 190, 196, 197, 203, 204, 210, 211, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235,  ... |
| toggle | gpio.sv | 956 | 28, 31, 32, 38, 42, 43, 143 |
| toggle | gpio_reg_top.sv | 1952 | 18, 19, 25, 26, 41, 50, 52, 53, 65, 90, 170, 176, 199, 1382, 1384, 1422, 1424, 1462, 1464, 1502, 1504, 1542, 1544, 1582, 1584, 1622, 1624, 1662, 1664, 1702, 1704, 1742, 1744, 1782, 1784, 1822, 1824, 1862, 1864, 1902, 1904, 1942, 1944, 1982, 1984, 2022, 2024, 2062, 2064, 2102, 2104, 2142, 2144, 2182, ... |
| toggle | ot_gpio_nnc.sv | 1324 | 26, 29, 38, 39, 62, 67, 68, 69, 71 |
| toggle | prim_alert_receiver.sv | 24 | 45 |
| toggle | prim_buf.sv | 60 | 8, 9, 12 |
| toggle | prim_filter_ctr.sv | 16 | 25 |
| toggle | prim_onehot_check.sv | 2168 | 40, 41, 59, 60, 61 |
| toggle | prim_reg_we_check.sv | 48 | 15, 22 |
| toggle | prim_secded_inv_39_32_dec.sv | 72 | 10, 11 |
| toggle | prim_secded_inv_64_57_dec.sv | 624 | 8, 9, 10 |
| toggle | prim_secded_inv_64_57_enc.sv | 576 | 8, 9 |
| toggle | prim_subreg.sv | 628 | 19, 23, 24, 27, 28, 31 |
| toggle | prim_subreg_arb.sv | 852 | 16, 17, 20, 21, 46, 47 |
| toggle | tlul_adapter_reg.sv | 600 | 111, 112, 115, 121, 148, 229 |
| toggle | tlul_cmd_intg_chk.sv | 416 | 13, 21 |
| toggle | tlul_cmd_intg_gen.sv | 1000 | 15, 16, 19, 21 |
| toggle | tlul_data_integ_dec.sv | 16 | 17 |
| toggle | tlul_err.sv | 240 | 12 |
| toggle | tlul_rsp_intg_chk.sv | 72 | 15, 21, 22 |
| toggle | tlul_rsp_intg_gen.sv | 1096 | 31, 32, 35, 37, 38, 52 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 52.5 % (11212/21352) | | | |
