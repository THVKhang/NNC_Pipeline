# Extracted rules - opentitan_comportability.md

```
rules: 63  by strength {'SHOULD': 8, 'MUST': 35, 'MAY': 16, 'MUST_NOT': 4}  by check {'none': 38, 'scenario': 16, 'assertion': 6, 'both': 3}
normative sentences: 50  cited 44  skipped 8  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 2 (0 from cache)  cost US$0.1224  tokens in 15615 out 6668
```


## T1.5.2 Clocking

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.2-01 | SHOULD | system | none | Exactly one clocking item dictionary should have the boolean field primary set to true. *(when: When the clocking element has several clocking items)* | T1.5.2:s8 (p134) |
| CP-T1.5.2-02 | MUST | system | none | Special care will be required for security sensitive storage elements. *(when: For security sensitive storage elements)* | T1.5.2:s11 (p139) |
| CP-T1.5.2-03 | MAY | system | none | The clock and reset fields of a clocking item are optional. *(when: For blocks that generate clocks or resets)* | T1.5.2:s15 (p143) |
| CP-T1.5.2-04 | MUST | system | none | The primary clock clocking item must have both clock and reset fields. | T1.5.2:s16 (p143) |

## T1.5.2.1 Details and rationale for asynchronous active low reset strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.2.1-01 | SHOULD | system | none | Security storage elements should be handled with care regardless of reset methodology, since they might leak sensitive state content. *(when: For security storage elements)* | T1.5.2.1:s4 (p154) |
| CP-T1.5.2.1-02 | MAY | system | none | Care may include synchronously resetting the value after chip-wide reset to a randomized value. *(when: Handling security storage elements)* | T1.5.2.1:s5 (p154) |
| CP-T1.5.2.1-03 | MAY | system | none | Asynchronous active low reset incurs slightly more area and needs more hand-holding but is more common. | T1.5.2.1:s7 (p157) |
| CP-T1.5.2.1-04 | MAY | system | none | Synchronous active high reset is slightly more efficient but requires a clock edge to take effect. | T1.5.2.1:s8 (p158) |

## T1.5.3 Bus Interfaces

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.3-01 | MAY | system | none | Peripherals can connect to the chip bus. | T1.5.3:s1 (p164) |
| CP-T1.5.3-02 | MUST | system | none | Every peripheral must expose at least one device interface on the chip bus. | T1.5.3:s2 (p164) |
| CP-T1.5.3-03 | MAY | master | none | Peripherals can act as a bus host, though the preferred model is the processor being primary host. *(when: On some occasions)* | T1.5.3:s3 (p164) |
| CP-T1.5.3-04 | SHOULD | system | none | The bus_interfaces attribute in the configuration file should contain a list of dictionaries describing the interfaces the peripheral exposes. | T1.5.3:s7 (p172) |
| CP-T1.5.3-05 | MUST | system | none | The peripheral must have a protocol of tlul. | T1.5.3:s11 (p178) |
| CP-T1.5.3-06 | MUST | system | none | Each bus_interfaces entry must contain a direction, which must be either host or device. | T1.5.3:s14, T1.5.3:s15 (p185) |
| CP-T1.5.3-07 | MUST | master | scenario | All bus hosts must use the same clock as the defined primary host clock. | T1.5.3:s16 (p185) |
| CP-T1.5.3-08 | MUST | system | none | An entry must include a name so port names do not collide. *(when: When another entry in the list has the same direction)* | T1.5.3:s22 (p192) |

## T1.5.5 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.5-01 | MUST | system | none | The module must have an output named intr_name_o for each interrupt name. *(when: For each item name in the interrupt list)* | T1.5.5:s4 (p222) |

## T1.6 Register Handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.6-01 | MUST | system | none | All lowRISC peripheral designs must conform to the register specification. | T1.6:s2 (p334) |

## T1.8 Interrupt Handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8-01 | MUST | system | none | All interrupts shall have common naming, hardware interfaces, and software interfaces. *(when: Where possible, except inherited IP too tricky to convert)* | T1.8:s2 (p476) |

## T1.8.1 Conventions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.1-01 | MUST | source | assertion | Wired CIP interrupts use active-high level-triggering. | T1.8.1:s1 (p481) |

## T1.8.2 Defining Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.2-01 | MUST | system | none | The name key, a string naming the interrupt, is required. *(when: For each entry in interrupt_list)* | T1.8.2:s4 (p498) |
| CP-T1.8.2-02 | MAY | system | none | The desc key, a string describing the interrupt, is optional. *(when: For each entry in interrupt_list)* | T1.8.2:s5 (p499) |
| CP-T1.8.2-03 | MAY | system | none | The type key is optional, selecting Event or Status, defaulting to Event if unspecified. *(when: For each entry in interrupt_list)* | T1.8.2:s6 (p500) |

## T1.8.3 Interrupts per module

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.3-01 | MUST | system | none | A peripheral generates a separate wired interrupt for each interrupt source. | T1.8.3:s1 (p504) |

## T1.8.4 Register Creation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.4-01 | MUST | system | scenario | INTR_STATE, INTR_ENABLE and INTR_TEST registers are created at offsets 0x0, 0x4, 0x8 with one bitfield per interrupt. | T1.8.4:s1, T1.8.4:s2, T1.8.4:s3 (p511) |
| CP-T1.8.4-02 | MUST_NOT | system | none | The .hjson must not define more than 32 interrupts per peripheral. | T1.8.4:s4 (p511) |
| CP-T1.8.4-03 | MUST | system | both | INTR_ENABLE enables/masks the output of INTR_STATE to create the wired interrupt signal intr_o. | T1.8.4:s6 (p520) |
| CP-T1.8.4-04 | MUST | system | scenario | INTR_TEST is write-only and asserts the interrupt for testing. *(when: When INTR_TEST is written)* | T1.8.4:s7 (p521) |
| CP-T1.8.4-05 | MUST | system | scenario | INTR_STATE is not qualified by INTR_ENABLE and shows the raw state of latched hardware interrupt events. | T1.8.4:s8 (p523) |

## T1.8.5 CIP Interrupt Types

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5-01 | MUST | system | scenario | The current interrupt can only be cleared by handler acknowledgement, a W1C write to INTR_STATE. *(when: Event type interrupt)* | T1.8.5:s8 (p535) |

## T1.8.5.1 Event Type Interrupt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5.1-01 | MUST | system | both | The event is latched into its INTR_STATE bitfield and intr_o goes high; a software W1C write clears it and intr_o goes low. *(when: Event type interrupt)* | T1.8.5.1:s3, T1.8.5.1:s5, T1.8.5.1:s6 (p551) |

## T1.8.5.2 Status Type Interrupt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5.2-01 | MUST | system | assertion | A status type interrupt must be a wired level-triggered signal directly from the hardware input signal, qualified only by INTR_ENABLE, asserted continuously while the input is asserted. *(when: Status type interrupt)* | T1.8.5.2:s1, T1.8.5.2:s2 (p585) |
| CP-T1.8.5.2-02 | MUST | system | assertion | The wired interrupt must not deassert until the root cause of the hardware input signal is addressed. *(when: Status type interrupt)* | T1.8.5.2:s4 (p585) |
| CP-T1.8.5.2-03 | MUST_NOT | slave | scenario | Software cannot acknowledge a status type interrupt via INTR_STATE, which is read-only (ro) in this context. *(when: Status type interrupt)* | T1.8.5.2:s5 (p585) |
| CP-T1.8.5.2-04 | MAY | system | none | prim_intr_hw parameterized with .IntrT("Status") can generate the correct hardware for status type interrupts. *(when: Status type interrupt)* | T1.8.5.2:s6 (p591) |
| CP-T1.8.5.2-05 | SHOULD | master | scenario | Software should mask the interrupt, at the peripheral or further up the tree such as the PLIC. *(when: SW cannot address the root cause or wishes to defer handling)* | T1.8.5.2:s8 (p617) |
| CP-T1.8.5.2-06 | MAY | master | scenario | Software can mask at the peripheral by clearing the corresponding bit in INTR_ENABLE. *(when: Masking a status interrupt at the peripheral)* | T1.8.5.2:s9 (p617) |

## T1.8.6 Interrupt Hardware Implementation (Event Type)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.6-01 | MAY | system | none | The block diagram shows one possible hardware implementation of an interrupt; other implementations are allowed. | T1.8.6:s1 (p622) |
| CP-T1.8.6-02 | MUST | slave | both | The event sets the associated bit in INTR_STATE to 1. *(when: Event occurs)* | T1.8.6:s7 (p630) |
| CP-T1.8.6-03 | MAY | master | scenario | A write of 1 to the foo bit of INTR_TEST can set the corresponding INTR_STATE bit. *(when: Write of 1 to foo bit of INTR_TEST)* | T1.8.6:s8 (p630) |
| CP-T1.8.6-04 | MUST | slave | assertion | The outgoing interrupt must be INTR_STATE ANDed with INTR_ENABLE. | T1.8.6:s9 (p630) |
| CP-T1.8.6-05 | MUST | slave | scenario | A write of 1 to an INTR_STATE bit clears the latched value, but if the event is still active the bit returns to true. *(when: Write of 1 to INTR_STATE bit)* | T1.8.6:s10, T1.8.6:s11 (p636) |
| CP-T1.8.6-06 | MUST_NOT | slave | assertion | Hardware must not clear the latched interrupt state; only software can. | T1.8.6:s12 (p636) |

## T1.9.1 Alerts per Module

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.1-01 | MAY | any | none | Each peripheral can send zero or more alerts, each a distinguishable security threat. | T1.9.1:s2 (p649) |
| CP-T1.9.1-02 | MUST | any | none | Each alert originates in an internal event and must be handled within the peripheral and then within the alert handler module. | T1.9.1:s3 (p649) |
| CP-T1.9.1-03 | MUST | source | scenario | A recoverable alert sender must transmit one single alert event when the error condition is asserted. *(when: Recoverable alert)* | T1.9.1:s4, T1.9.1:s5, T1.9.1:s7 (p653) |
| CP-T1.9.1-04 | MUST | source | scenario | A fatal alert sender must continuously transmit alert events until the system is reset. *(when: Fatal alert)* | T1.9.1:s4, T1.9.1:s8, T1.9.1:s10 (p653) |
| CP-T1.9.1-05 | SHOULD | any | none | Fatal alerts should also trigger local security countermeasures. *(when: Local security countermeasures exist)* | T1.9.1:s11 (p663) |
| CP-T1.9.1-06 | SHOULD | any | none | Error conditions should use the recommended alert type from the table; regular IRQ is optional. | T1.9.1:s14, T1.9.1:s16 (p667) |
| CP-T1.9.1-07 | MAY | any | none | A peripheral may optionally send a regular IRQ for any alert event. *(when: Alert event)* | T1.9.1:s17, T1.9.1:s18 (p681) |

## T1.9.2 Defining Alerts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.2-01 | MUST | any | none | Alerts shall be given a meaningful name indicative of their cause. | T1.9.2:s3 (p690) |
| CP-T1.9.2-02 | MUST | any | none | Recoverable alerts must be prefixed recov_ and fatal alerts must be prefixed fatal_. | T1.9.2:s4 (p690) |
| CP-T1.9.2-03 | MAY | any | none | Alert names may default to just recov and/or fatal, implying only one alert of that type is exposed. *(when: Many diverse sources bundled into one alert)* | T1.9.2:s7, T1.9.2:s8 (p694) |

## T1.9.3 Test Alert Register Creation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.3-01 | MUST | slave | scenario | Each peripheral has a write-only ALERT_TEST register for software to test alert reporting. | T1.9.3:s1, T1.9.3:s2 (p700) |
| CP-T1.9.3-02 | MUST | slave | scenario | Each alert has one field bit in ALERT_TEST, connected to the test input of the corresponding prim_alert_sender. | T1.9.3:s3 (p702) |

## T1.9.4 Alert Hardware Implementation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.4-01 | MUST | source | none | Internal events are sent active-high to the prim_alert_sender within the peripheral. | T1.9.4:s1 (p707) |
| CP-T1.9.4-02 | MUST | source | none | One prim_alert_sender must be instantiated per distinct alert event, with IsFatal set to 1 for fatal alerts. | T1.9.4:s2 (p707) |
| CP-T1.9.4-03 | MAY | any | none | The peripheral maintainer determines distinct alert events; multiple may be bundled. | T1.9.4:s3 (p710) |
| CP-T1.9.4-04 | SHOULD | any | none | Each peripheral should bundle alert sources into one or two distinct alerts, e.g. one fatal and one recoverable. | T1.9.4:s4 (p710) |
| CP-T1.9.4-05 | SHOULD | any | none | Comportable IPs with multiple bundled alerts should expose a cause register for disambiguation. *(when: IP has multiple bundled alerts)* | T1.9.4:s6 (p715) |
| CP-T1.9.4-06 | MUST | any | scenario | Recoverable alert cause registers must be clearable by SW or automatically cleared by HW. *(when: Cause register for recoverable alerts)* | T1.9.4:s7 (p715) |
| CP-T1.9.4-07 | MUST_NOT | any | scenario | Fatal alert cause registers must not be clearable and must be read-only. *(when: Cause register for fatal alerts)* | T1.9.4:s8 (p715) |
| CP-T1.9.4-08 | MUST | source | assertion | The prim_alert_sender converts the event into a differentially encoded signal pair for the alert handler. | T1.9.4:s9 (p719) |
