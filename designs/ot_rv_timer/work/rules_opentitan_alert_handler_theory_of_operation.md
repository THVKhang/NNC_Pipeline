# Extracted rules - opentitan_alert_handler_theory_of_operation.md

```
rules: 11  by strength {'MUST': 9, 'MAY': 2}  by check {'scenario': 5, 'none': 1, 'both': 4, 'assertion': 1}
normative sentences: 8  cited 8  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (1 from cache)  cost US$0.0  tokens in 0 out 0
```


## T1.3.1 Alert Definition

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.1-01 | MUST | system | scenario | Alerts must be handled by the main processor or escalated to other hardware modules to take action. *(when: An alert event with security implications occurs)* | T1.3.1:s1 (p122) |
| AH-T1.3.1-02 | MUST | slave | none | Peripherals defining alerts should instantiate one prim_alert_sender module to convert the alert event into a signal to the alert handler. *(when: A peripheral defines one or more alert signals)* | T1.3.1:s3 (p122) |

## T1.3.2 Differential Alert Signaling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.2-01 | MUST | any | both | Alerts are encoded differentially and signaled using a full handshake on the alert_p/n and ack_p/n wires. | T1.3.2:s2 (p135) |
| AH-T1.3.2-02 | MUST | slave | scenario | The alert sender must keep repeating the native alert message and handshake pattern on its output wires while the alert is true. *(when: The alert event is still true within the peripheral)* | T1.3.2:s5, T1.3.2:s7 (p135) |
| AH-T1.3.2-03 | MUST | slave | assertion | The sender waits 2 cycles between handshakes. *(when: Between repeated handshakes)* | T1.3.2:s8 (p170) |
| AH-T1.3.2-04 | MUST | master | both | The receiver must immediately propagate the first occurrence of an alert to alert_o. *(when: Initial level change on alert_tx_i.alert_p/n is received and synchronized, even if handshake lines are manipulated to emulate backpressure)* | T1.3.2:s9, T1.3.2:s10 (p173) |
| AH-T1.3.2-05 | MAY | any | scenario | The alert sender and receiver modules may be used either synchronously or asynchronously. | T1.3.2:s12 (p177) |
| AH-T1.3.2-06 | MAY | any | scenario | The signaling protocol remains the same; the additional synchronizer flops at the diff pair inputs may be omitted, giving lower latency. *(when: Synchronous use)* | T1.3.2:s13 (p177) |

## T1.3.4 Monitoring of Signal Integrity Issues

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.4-01 | MUST | master | both | The receiver must assert integ_fail_o when alert_tx_i.alert_p/n is incorrectly encoded. *(when: The alert_tx_i.alert_p/n pair is not correctly encoded at the receiver)* | T1.3.4:s1, T1.3.4:s3, T1.3.4:s4 (p232) |
| AH-T1.3.4-02 | MUST | slave | both | The sender must set alert_tx_o.alert_p/n to the same continuously toggling value, which triggers integ_fail_o on the receiver. *(when: The ping_p/n or ack_p/n pair is incorrectly encoded on the sender side)* | T1.3.4:s1, T1.3.4:s5, T1.3.4:s6, T1.3.4:s7 (p232) |
| AH-T1.3.4-03 | MUST | system | scenario | Such lock-up must always trigger either a signal integrity alert or eventually a pingfail alert. *(when: Signal integrity failures occur during ping or alert handshaking and the protocol state machines lock up)* | T1.3.4:s9, T1.3.4:s10 (p268) |
