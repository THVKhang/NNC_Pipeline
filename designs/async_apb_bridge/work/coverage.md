# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 246/271 | 90.8 % |
| block | 67/77 | 87.0 % |
| expression | 54/74 | 73.0 % |
| toggle | 2315/2350 | 98.5 % |
| functional | 33/40 | 82.5 % |

### Functional cover points never hit

- COVP-028: APB5 Setup with wake-up raised before PSEL
- COVP-029: APB5 Setup with wake-up low
- COVP-030: APB5 Setup with nonzero PAUSER
- COVP-031: APB5 write Setup with nonzero PWUSER
- COVP-032: APB5 read completed with nonzero PRUSER
- COVP-033: APB5 completion with nonzero PBUSER
- COVP-040: slv restart after reset during a transfer

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_vlsit_apbcdc_cell_sync.sv | 2 | 137, 139 |
| block | m_vlsit_apbcdc_mst.sv | 4 | 169, 170, 193 |
| block | m_vlsit_apbcdc_slv.sv | 4 | 167, 168, 180 |
| expression | m_vlsit_apbcdc_cell_sync.sv | 1 | 182 |
| expression | m_vlsit_apbcdc_mst.sv | 10 | 137, 167, 170, 181, 185, 192, 214 |
| expression | m_vlsit_apbcdc_slv.sv | 9 | 134, 165, 168, 179, 180, 207 |
| line | m_vlsit_apbcdc_mst.sv | 9 | 92, 93, 98, 119, 129, 169, 170, 171, 194 |
| line | m_vlsit_apbcdc_slv.sv | 10 | 84, 85, 86, 98, 121, 127, 167, 168, 169, 181 |
| line | m_vlsit_apbcdc_top.sv | 6 | 88, 89, 103, 104, 105, 118 |
| toggle | m_vlsit_apbcdc_cell_sync.sv | 1 | 106 |
| toggle | m_vlsit_apbcdc_mst.sv | 10 | 92, 93, 98, 119, 129 |
| toggle | m_vlsit_apbcdc_slv.sv | 12 | 84, 85, 86, 98, 121, 127 |
| toggle | m_vlsit_apbcdc_top.sv | 12 | 88, 89, 103, 104, 105, 118 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 90.8 % (246/271) | | | |
