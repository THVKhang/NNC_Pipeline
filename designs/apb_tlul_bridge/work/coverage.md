# Coverage closure

Metric **functional**, target 100.0 %, status **target_met**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 192/200 | 96.0 % |
| block | 43/45 | 95.6 % |
| expression | 47/47 | 100.0 % |
| toggle | 1920/2002 | 95.9 % |
| functional | 40/40 | 100.0 % |

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_apb_if.sv | 1 | 100 |
| block | m_tlul_if.sv | 1 | 145 |
| line | m_apb_if.sv | 1 | 100 |
| line | m_apb_tlul_bridge.sv | 3 | 63, 65, 69 |
| line | m_tlul_if.sv | 4 | 54, 56, 60, 145 |
| toggle | m_apb_tlul_bridge.sv | 39 | 62, 63, 64, 65, 66, 67, 69 |
| toggle | m_tlul_if.sv | 43 | 53, 54, 55, 56, 57, 58, 60, 86 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 95.0 % (38/40) | | | |
| 1 | 100.0 % (40/40) | 2 | test_cov_101_long_response_delay, test_cov_102_stale_response_at_reset_release |  |
