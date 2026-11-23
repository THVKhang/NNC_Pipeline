# Rules for review (Gate 1)

```
rules in 1: kept 0 (fixed 0), merged 0, rejected 1, unreviewed 0; open questions 0
calls: 1 (0 from cache)  cost US$0.0134
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.


## Rejected

| ID | Statement | Reason |
|---|---|---|
| AR-T1.1.1-01 | The axil_ram module provides AXI lite RAM whose data and address interface widths are parametrizable via DATA_WIDTH and ADDR_WIDTH. | The quote is only a module description ("AXI lite RAM with parametrizable data and address interface widths"). It states no verifiable behaviour. It does not name DATA_WIDTH or ADDR_WIDTH. It also gives no requirement a scenario or assertion could check. |
