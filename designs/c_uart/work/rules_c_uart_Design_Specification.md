# Extracted rules - c_uart_Design_Specification.md

```
rules: 10  by strength {'MUST': 7, 'SHOULD': 1, 'MUST_NOT': 1, 'MAY': 1}  by check {'scenario': 2, 'assertion': 3, 'both': 3, 'none': 2}
normative sentences: 6  cited 6  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (0 from cache)  cost US$0.0284  tokens in 4382 out 1052
```


## T1.3 Documentation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UA-T1.3-01 | MUST | system | scenario | The prescale input must be set to Fclk / (baud * 8) to determine the data rate. | T1.3:s6 (p26) |
| UA-T1.3-02 | SHOULD | system | scenario | Because prescale is not buffered internally, care should be used when changing it at run time to avoid corrupt data. *(when: when prescale is changed at run time)* | T1.3:s7 (p26) |
| UA-T1.3-03 | MUST | source | assertion | tdata is considered valid when tvalid is high. *(when: when tvalid is high)* | T1.3:s8 (p26) |
| UA-T1.3-04 | MUST_NOT | destination | assertion | The destination must not accept data unless tready is high. *(when: when tready is low)* | T1.3:s9 (p26) |
| UA-T1.3-05 | MUST | source | assertion | Data is transferred from source to destination only when both tvalid and tready are high; otherwise the bus is stalled and no transfer occurs. | T1.3:s10 (p26) |
| UA-T1.3-06 | MUST | system | both | Both the transmitter and receiver interfaces drive busy high while an operation is taking place. *(when: when an operation is taking place)* | T1.3:s11 (p40) |
| UA-T1.3-07 | MUST | system | both | The receiver emits a single-cycle pulse on overrun_error and discards the newly received word. *(when: when the word in the tdata output register is not read before another word is received)* | T1.3:s13 (p40) |
| UA-T1.3-08 | MUST | system | both | The receiver emits a single-cycle pulse on frame_error and discards the received word. *(when: when the receiver does not get a stop bit of the right level)* | T1.3:s14 (p40) |

## T1.4 Testing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UA-T1.4-01 | MUST | system | none | Running the included testbenches requires cocotb, cocotbext-axi, and Icarus Verilog. *(when: when running the included testbenches)* | T1.4:s1 (p70) |
| UA-T1.4-02 | MAY | system | none | The testbenches can be run with pytest directly (requires cocotb-test), pytest via tox, or via cocotb makefiles. | T1.4:s2 (p70) |
