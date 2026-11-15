# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 2733/3177 | 86.0 % |
| block | 1142/1482 | 77.1 % |
| expression | 1316/1830 | 71.9 % |
| toggle | 23645/35994 | 65.7 % |
| functional | 36/40 | 90.0 % |

### Functional cover points never hit

- COVP-012: Rejected SEQ beat after captured fixed write prefix
- COVP-038: AW handshake maximum burst (AWLEN=15)
- COVP-039: AW WRAP burst handshake
- COVP-040: AW INCR burst ending exactly at 4 KiB boundary

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_ahb2axi_ctrl.sv | 100 | 325, 528, 617, 624, 626, 630, 635, 636, 639, 640, 641, 652, 702, 791, 843, 850, 864, 885, 886, 888, 890, 896, 902, 905, 919, 931 |
| block | m_vlsit_sfifo_rd.sv | 84 | 124, 175, 178, 179, 180, 183 |
| block | m_vlsit_sfifo_wr.sv | 156 | 129, 179, 182, 183, 186, 187, 188, 191, 192, 195 |
| expression | m_ahb2axi_ahb_if.sv | 9 | 97, 117 |
| expression | m_ahb2axi_ctrl.sv | 163 | 350, 429, 434, 520, 529, 544, 554, 559, 571, 612, 617, 624, 630, 636, 649, 684, 702, 703, 704, 725, 729, 853, 864, 904, 909, 918, 924 |
| expression | m_vlsit_sfifo_rd.sv | 144 | 104, 105, 109, 112, 154, 180, 217, 218 |
| expression | m_vlsit_sfifo_wr.sv | 198 | 109, 110, 114, 117, 158, 179, 192, 218, 232, 233 |
| line | m_ahb2axi_axi_if.sv | 30 | 17, 19, 22, 36, 37, 42, 44, 47, 54, 64, 66, 82, 83, 88, 90, 99 |
| line | m_ahb2axi_ctrl.sv | 237 | 55, 57, 60, 74, 75, 80, 82, 85, 92, 130, 131, 134, 145, 146, 197, 207, 208, 216, 218, 230, 231, 234, 236, 243, 274, 278, 279, 283, 325, 532, 533, 618, 625, 626, 627, 629, 635, 636, 637, 639, 640, 641, 642, 644, 652, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 792, 844, 845, 846, 847, 848, ... |
| line | m_ahb2axi_top.sv | 18 | 44, 46, 49, 63, 64, 69, 71, 74, 81 |
| line | m_vlsit_sfifo_rd.sv | 57 | 46, 50, 53, 54, 75, 76, 78, 79, 82, 95, 98, 99, 124, 176, 178, 179, 180, 181, 183 |
| line | m_vlsit_sfifo_top.sv | 21 | 47, 50, 54, 62, 66, 72, 73 |
| line | m_vlsit_sfifo_wr.sv | 81 | 45, 48, 52, 53, 54, 79, 80, 82, 83, 84, 87, 100, 103, 104, 129, 180, 182, 183, 184, 186, 187, 188, 189, 191, 192, 193, 195 |
| toggle | m_ahb2axi_axi_if.sv | 336 | 17, 19, 20, 21, 22, 36, 37, 42, 44, 46, 47, 54, 56, 64, 66, 67, 68, 82, 83, 88, 90, 92, 99, 101 |
| toggle | m_ahb2axi_ctrl.sv | 1874 | 55, 57, 58, 59, 60, 74, 75, 80, 82, 84, 85, 92, 94, 124, 125, 126, 127, 128, 129, 130, 131, 134, 137, 138, 142, 145, 146, 178, 183, 197, 200, 201, 207, 208, 216, 218, 219, 220, 230, 231, 234, 236, 238, 243, 245, 253, 274, 278, 279, 283 |
| toggle | m_ahb2axi_top.sv | 174 | 44, 46, 47, 48, 49, 63, 64, 69, 71, 73, 74, 81, 83 |
| toggle | m_vlsit_sfifo_mem.sv | 103 | 36, 41, 47, 48 |
| toggle | m_vlsit_sfifo_rd.sv | 4714 | 46, 47, 50, 53, 54, 62, 75, 76, 78, 79, 82, 91, 92, 93, 94, 95, 96, 98, 99 |
| toggle | m_vlsit_sfifo_top.sv | 326 | 46, 47, 48, 50, 53, 54, 62, 63, 66, 72, 73, 76, 78 |
| toggle | m_vlsit_sfifo_wr.sv | 4822 | 44, 45, 46, 48, 51, 52, 53, 54, 63, 79, 80, 82, 83, 84, 85, 87, 96, 97, 98, 99, 100, 101, 103, 104 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 86.0 % (2733/3177) | | | |
