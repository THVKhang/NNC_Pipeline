# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 2948/3208 | 91.9 % |
| block | 807/909 | 88.8 % |
| expression | 663/886 | 74.8 % |
| toggle | 26577/26946 | 98.6 % |
| functional | 39/40 | 97.5 % |

### Functional cover points never hit

- COVP-040: slv restart after reset during a transfer

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_vlsit_apbcdc_cell_sync.sv | 22 | 137, 139 |
| block | m_vlsit_apbcdc_mst.sv | 40 | 169, 170, 193 |
| block | m_vlsit_apbcdc_slv.sv | 40 | 167, 168, 180 |
| expression | m_vlsit_apbcdc_cell_sync.sv | 11 | 182 |
| expression | m_vlsit_apbcdc_mst.sv | 114 | 137, 167, 170, 181, 185, 192, 214 |
| expression | m_vlsit_apbcdc_slv.sv | 98 | 134, 165, 168, 179, 180, 207 |
| line | m_vlsit_apbcdc_cell_sync.sv | 2 | 106 |
| line | m_vlsit_apbcdc_mst.sv | 92 | 92, 93, 98, 119, 129, 169, 170, 171, 194 |
| line | m_vlsit_apbcdc_slv.sv | 102 | 84, 85, 86, 98, 121, 127, 167, 168, 169, 181 |
| line | m_vlsit_apbcdc_top.sv | 64 | 88, 89, 103, 104, 105, 118 |
| toggle | m_vlsit_apbcdc_cell_sync.sv | 13 | 106 |
| toggle | m_vlsit_apbcdc_mst.sv | 104 | 92, 93, 98, 119, 129 |
| toggle | m_vlsit_apbcdc_slv.sv | 124 | 84, 85, 86, 98, 121, 127 |
| toggle | m_vlsit_apbcdc_top.sv | 128 | 88, 89, 103, 104, 105, 118 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 90.8 % (246/271) | | | |
