# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 738/746 | 98.9 % |
| block | 209/218 | 95.9 % |
| expression | 102/106 | 96.2 % |
| toggle | 3506/4690 | 74.8 % |
| functional | 39/40 | 97.5 % |

### Functional cover points never hit

- COVP-024: Illegal FIXED or WRAP length accepted

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_axi2apb_apb_ctrl.sv | 4 | 111, 115, 126, 147 |
| block | m_axi2apb_rd_seq.sv | 2 | 274, 297 |
| block | m_axi2apb_wr_seq.sv | 3 | 257, 261, 280 |
| expression | m_axi2apb_apb_ctrl.sv | 4 | 111, 115 |
| line | m_axi2apb_apb_ctrl.sv | 4 | 126, 127, 147, 148 |
| line | m_axi2apb_rd_seq.sv | 2 | 297, 298 |
| line | m_axi2apb_wr_seq.sv | 2 | 280, 281 |
| toggle | m_axi2apb_apb_ctrl.sv | 136 | 28, 37, 49, 80 |
| toggle | m_axi2apb_bridge.sv | 106 | 39, 57, 63, 80, 92 |
| toggle | m_axi2apb_rd_seq.sv | 472 | 61, 67, 90, 97, 101, 103, 105, 106, 109, 110, 111, 112, 113, 115, 116, 117, 118, 119 |
| toggle | m_axi2apb_wr_seq.sv | 470 | 64, 70, 95, 107, 109, 111, 112, 115, 116, 117, 118, 119, 121, 122, 123, 124, 125 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 97.7 % (728/745) | | | |
