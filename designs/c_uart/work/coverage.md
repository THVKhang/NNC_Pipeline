# Coverage closure

Metric **line**, target None %, status **not_requested**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 120/123 | 97.6 % |
| block | 41/44 | 93.2 % |
| expression | 8/9 | 88.9 % |
| toggle | 274/370 | 74.1 % |
| functional | 36/40 | 90.0 % |

### Functional cover points never hit

- COVP-021: good reception after an overrun (recovery)
- COVP-035: tx start with large prescale (256+)
- COVP-038: reset released after tx activity
- COVP-039: reset released after rx activity

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | uart_rx.v | 2 | 109, 120 |
| block | uart_tx.v | 1 | 106 |
| expression | uart_rx.v | 1 | 109 |
| line | uart_rx.v | 3 | 112, 113, 114 |
| toggle | uart.v | 24 | 71 |
| toggle | uart_rx.v | 24 | 62 |
| toggle | uart_tx.v | 48 | 60, 70 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 97.6 % (120/123) | | | |
