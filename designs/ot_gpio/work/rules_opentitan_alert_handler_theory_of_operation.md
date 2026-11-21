# Extracted rules - opentitan_alert_handler_theory_of_operation.md

```
rules: 13  by strength {'MUST': 11, 'MAY': 2}  by check {'none': 2, 'scenario': 5, 'both': 5, 'assertion': 1}
normative sentences: 8  cited 8  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 1 (0 from cache)  cost US$0.0339  tokens in 4646 out 1898
```


## T1.3.1 Alert Definition

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.1-01 | MUST | system | none | Alerts are events with security implications and must be handled by the main processor or escalated to other hardware modules for action. *(when: An event has security implications)* | T1.3.1:s1 (p122) |
| AH-T1.3.1-02 | MUST | slave | none | Peripherals defining alerts must instantiate a prim_alert_sender to convert the alert event into a signal to the alert handler. *(when: A peripheral defines an alert signal)* | T1.3.1:s3 (p122) |
| AH-T1.3.1-03 | MAY | any | scenario | The differential signaling submodules may use either a synchronous or an asynchronous clocking scheme. | T1.3.1:s5 (p122) |

## T1.3.2 Differential Alert Signaling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.2-01 | MUST | any | both | Alerts are differentially encoded and signaled with a full handshake on alert_p/n and ack_p/n, repeated as long as the alert is true. *(when: Alert is signaled)* | T1.3.2:s2, T1.3.2:s7 (p135) |
| AH-T1.3.2-02 | MUST | any | scenario | The full handshake must back-pressure alert messages correctly so no alert is lost at the asynchronous boundary regardless of clock ratio. *(when: Alert crosses an asynchronous boundary)* | T1.3.2:s4 (p135) |
| AH-T1.3.2-03 | MUST | slave | both | The native alert message is repeated on the output wires as long as the alert event remains true. *(when: Alert event is still true within the peripheral)* | T1.3.2:s5 (p135) |
| AH-T1.3.2-04 | MUST | slave | assertion | The sender waits 2 cycles between handshakes. *(when: Alert handshake repeats)* | T1.3.2:s8 (p170) |
| AH-T1.3.2-05 | MUST | master | both | The receiver must immediately propagate the first alert occurrence to alert_o after synchronizing the initial level change on alert_tx_i.alert_p/n. *(when: Initial level change on alert_tx_i.alert_p/n received and synchronized, even if handshake lines are manipulated to emulate backpressure)* | T1.3.2:s9, T1.3.2:s10 (p173) |
| AH-T1.3.2-06 | MAY | any | scenario | The alert sender and receiver modules can be used either synchronously or asynchronously. | T1.3.2:s12 (p177) |
| AH-T1.3.2-07 | MUST | any | scenario | The signaling protocol remains the same in both synchronous and asynchronous use; synchronizer flops at the diff pair inputs may be omitted. *(when: Sync or async use)* | T1.3.2:s13 (p177) |

## T1.3.4 Monitoring of Signal Integrity Issues

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AH-T1.3.4-01 | MUST | master | both | The receiver must assert integ_fail_o when alert_tx_i.alert_p/n is incorrectly encoded. *(when: alert_tx_i.alert_p/n pair is not correctly encoded at the receiver)* | T1.3.4:s1, T1.3.4:s3, T1.3.4:s4 (p232) |
| AH-T1.3.4-02 | MUST | slave | both | The sender must set alert_tx_o.alert_p/n to the same continuously toggling value, causing the receiver to assert integ_fail_o. *(when: ping_p/n or ack_p/n pair is not correctly encoded at the sender)* | T1.3.4:s1, T1.3.4:s5, T1.3.4:s6, T1.3.4:s7 (p232) |
| AH-T1.3.4-03 | MUST | system | scenario | A protocol lock-up must always trigger either a signal integrity alert or eventually a pingfail alert. *(when: Signal integrity failures occur during ping or alert handshaking and the protocol locks up)* | T1.3.4:s9, T1.3.4:s10 (p268) |
