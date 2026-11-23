# Rules for review (Gate 1)

```
rules in 10: kept 6 (fixed 2), merged 0, rejected 4, unreviewed 0; open questions 1 (raised 1, answered from the documents 0, duplicates 0)
calls: 2 (0 from cache)  cost US$0.0565
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.

## Open questions (the designer decides: `nnc answer <design> <n> "<decision>" --by <name>`)

1. On overrun, is the newly received word discarded while the older word in the tdata register is retained? What exactly defines the busy window on the receiver (start bit to stop bit)? (UA-T1.3-07, UA-T1.3-06) — *The documents do not settle either part. (1) T1.3:s13 says an overrun_error pulse is emitted and 'the word is discarded' when the word in the tdata output register is not read before another word is received. It does not say whether 'the word' is the newly received word or the older word in tdata, so retention of the older word is not stated. (2) T1.3:s11 says only that 'busy' is high 'when an operation is taking place'. It does not say whether busy spans start bit to stop bit, or when it asserts and deasserts on the receiver. The designer must specify which word is dropped on overrun and the exact receiver busy assertion and deassertion points.*
   - **Decision:** none yet


## c_uart_Design_Specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| UA-T1.3-01 |  | SHOULD | system | scenario | The prescale input must be set to Fclk / (baud * 8) to determine the data rate. | fix: strength MUST->SHOULD |
| UA-T1.3-04 |  | MUST_NOT | destination | assertion | The destination must not accept data unless tready is high. *(when: when tready is low)* | keep |
| UA-T1.3-05 |  | MUST_NOT | any | assertion | Data is transferred from source to destination only when both tvalid and tready are high; otherwise the bus is stalled and no transfer occurs. | fix: strength MUST->MUST_NOT, actor source->any |
| UA-T1.3-06 |  | MUST | system | both | Both the transmitter and receiver interfaces drive busy high while an operation is taking place. *(when: when an operation is taking place)* | keep |
| UA-T1.3-07 |  | MUST | system | both | The receiver emits a single-cycle pulse on overrun_error and discards the newly received word. *(when: when the word in the tdata output register is not read before another word is received)* | keep |
| UA-T1.3-08 |  | MUST | system | both | The receiver emits a single-cycle pulse on frame_error and discards the received word. *(when: when the receiver does not get a stop bit of the right level)* | keep |

## Rejected

| ID | Statement | Reason |
|---|---|---|
| UA-T1.3-02 | Because prescale is not buffered internally, care should be used when changing it at run time to avoid corrupt data. | Advisory caution to the integrator about unbuffered prescale; nothing concrete to verify. |
| UA-T1.3-03 | tdata is considered valid when tvalid is high. | Defines the meaning of tvalid (data is valid); a definition, not a checkable constraint. |
| UA-T1.4-01 | Running the included testbenches requires cocotb, cocotbext-axi, and Icarus Verilog. | Tool prerequisite, not a design behavior to verify. |
| UA-T1.4-02 | The testbenches can be run with pytest directly (requires cocotb-test), pytest via tox, or via cocotb makefiles. | Describes ways to run testbenches, not a design behavior to verify. |
