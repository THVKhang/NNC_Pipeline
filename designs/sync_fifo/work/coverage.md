# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 236/238 | 99.2 % |
| block | 72/74 | 97.3 % |
| expression | 64/69 | 92.8 % |
| toggle | 1620/2296 | 70.6 % |
| functional | 40/40 | 100.0 % |

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_vlsit_sfifo_rd.sv | 1 | 183 |
| block | m_vlsit_sfifo_wr.sv | 1 | 195 |
| expression | m_vlsit_sfifo_rd.sv | 2 | 104, 105 |
| expression | m_vlsit_sfifo_wr.sv | 3 | 109, 110, 192 |
| line | m_vlsit_sfifo_rd.sv | 1 | 183 |
| line | m_vlsit_sfifo_wr.sv | 1 | 195 |
| toggle | m_vlsit_sfifo_rd.sv | 338 | 91, 92, 93, 94, 95, 96 |
| toggle | m_vlsit_sfifo_wr.sv | 338 | 96, 97, 98, 99, 100, 101 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 99.2 % (236/238) | | | |
