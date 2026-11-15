# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 2632/2657 | 99.1 % |
| block | 858/897 | 95.7 % |
| expression | 980/1000 | 98.0 % |
| toggle | 15804/15884 | 99.5 % |
| functional | 40/40 | 100.0 % |

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | VLSIT_CELL_SRAM_1W1R.sv | 1 | 65 |
| block | m_vlsit_afifo_cell_sync.sv | 18 | 137, 139 |
| block | m_vlsit_afifo_rd.sv | 10 | 172 |
| block | m_vlsit_afifo_wr.sv | 10 | 188 |
| expression | VLSIT_CELL_SRAM_1W1R.sv | 1 | 65 |
| expression | m_vlsit_afifo_cell_sync.sv | 9 | 182 |
| expression | m_vlsit_afifo_wr.sv | 10 | 185 |
| line | VLSIT_CELL_SRAM_1W1R.sv | 2 | 41, 45 |
| line | m_vlsit_afifo_cell_sync.sv | 1 | 106 |
| line | m_vlsit_afifo_mem.sv | 1 | 68 |
| line | m_vlsit_afifo_ram_macro.sv | 1 | 35 |
| line | m_vlsit_afifo_rd.sv | 10 | 172 |
| line | m_vlsit_afifo_wr.sv | 10 | 188 |
| toggle | VLSIT_CELL_SRAM_1W1R.sv | 66 | 41, 45 |
| toggle | m_vlsit_afifo_cell_sync.sv | 10 | 106 |
| toggle | m_vlsit_afifo_mem.sv | 2 | 68 |
| toggle | m_vlsit_afifo_ram_macro.sv | 2 | 35 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 99.3 % (266/268) | | | |
