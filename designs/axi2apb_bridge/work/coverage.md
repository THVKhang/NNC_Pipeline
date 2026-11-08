# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 728/745 | 97.7 % |
| block | 201/216 | 93.1 % |
| expression | 95/103 | 92.2 % |
| toggle | 3110/4690 | 66.3 % |
| functional | 36/40 | 90.0 % |

### Functional cover points never hit

- COVP-007: Read FIXED burst of 16 beats completes
- COVP-019: Write beat with zero byte strobes
- COVP-024: Illegal FIXED or WRAP length accepted
- COVP-025: INCR burst ending exactly at 4-KiB boundary is supported

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_axi2apb_apb_ctrl.sv | 4 | 111, 115, 126, 147 |
| block | m_axi2apb_rd_seq.sv | 4 | 171, 182, 274, 297 |
| block | m_axi2apb_wr_seq.sv | 7 | 172, 181, 185, 199, 238, 259, 278 |
| expression | m_axi2apb_apb_ctrl.sv | 4 | 111, 115 |
| expression | m_axi2apb_rd_seq.sv | 2 | 182 |
| expression | m_axi2apb_wr_seq.sv | 2 | 181 |
| line | m_axi2apb_apb_ctrl.sv | 4 | 126, 127, 147, 148 |
| line | m_axi2apb_rd_seq.sv | 4 | 172, 184, 297, 298 |
| line | m_axi2apb_wr_seq.sv | 9 | 104, 173, 183, 185, 186, 200, 238, 278, 279 |
| toggle | m_axi2apb_apb_ctrl.sv | 136 | 28, 37, 49, 80 |
| toggle | m_axi2apb_bridge.sv | 172 | 23, 25, 27, 39, 45, 57, 63, 80, 92 |
| toggle | m_axi2apb_rd_seq.sv | 608 | 48, 61, 67, 90, 97, 101, 103, 105, 106, 107, 108, 109, 110, 111, 112, 113, 115, 116, 117, 118, 119 |
| toggle | m_axi2apb_wr_seq.sv | 664 | 47, 49, 51, 62, 68, 93, 95, 104, 105, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 97.7 % (728/745) | | | |
