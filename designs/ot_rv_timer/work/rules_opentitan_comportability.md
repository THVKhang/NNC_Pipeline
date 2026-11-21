# Extracted rules - opentitan_comportability.md

```
rules: 69  by strength {'MUST': 37, 'SHOULD': 9, 'MAY': 18, 'MUST_NOT': 5}  by check {'none': 39, 'both': 5, 'scenario': 19, 'assertion': 6}
normative sentences: 50  cited 50  skipped 0  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 2 (2 from cache)  cost US$0.0  tokens in 0 out 0
```


## T1.5.2 Clocking

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.2-01 | MUST | system | none | Each peripheral must specify clocking via a nonempty list of clocking items, each defining clock and reset in fields named clock and reset. | T1.5.2:s2, T1.5.2:s3, T1.5.2:s4, T1.5.2:s5 (p128) |
| CP-T1.5.2-02 | SHOULD | system | none | Exactly one clocking item dictionary should have boolean field primary set to true. *(when: When there are several clocking items)* | T1.5.2:s8 (p134) |
| CP-T1.5.2-03 | MUST | system | none | The primary clock is used to clock any device interfaces. | T1.5.2:s9 (p134) |
| CP-T1.5.2-04 | MUST | system | both | Resets within the design are asynchronous active low: assertion is asynchronous to any clock, deassertion is synchronized to the clock of the associated storage element. | T1.5.2:s10, T1.5.2.1:s1 (p139) |
| CP-T1.5.2-05 | SHOULD | system | none | Security sensitive storage elements need special care, e.g. synchronous reset after chip-wide reset to a randomized value. *(when: For security sensitive storage elements)* | T1.5.2:s11, T1.5.2.1:s4, T1.5.2.1:s5 (p139) |
| CP-T1.5.2-06 | MAY | system | none | The clock and reset fields of a clocking item are optional. *(when: For blocks that generate clocks or resets)* | T1.5.2:s15 (p143) |
| CP-T1.5.2-07 | MUST | system | none | The primary clock item must have both clock and reset fields. | T1.5.2:s16 (p143) |

## T1.5.2.1 Details and rationale for asynchronous active low reset strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.2.1-01 | MAY | system | none | Tradeoff notes on asynchronous active low versus synchronous active high reset are informative only. | T1.5.2.1:s7, T1.5.2.1:s8 (p157) |

## T1.5.3 Bus Interfaces

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.3-01 | MAY | system | none | Peripherals can connect to the chip bus. | T1.5.3:s1 (p164) |
| CP-T1.5.3-02 | MUST | system | none | Every peripheral must expose at least one device interface on the chip bus. | T1.5.3:s2 (p164) |
| CP-T1.5.3-03 | MAY | system | none | Peripherals can act as bus host on some occasions, though the processor being primary host is preferred. | T1.5.3:s3 (p164) |
| CP-T1.5.3-04 | SHOULD | system | none | The bus_interfaces attribute should contain a list of dictionaries describing the interfaces the peripheral exposes. | T1.5.3:s7 (p172) |
| CP-T1.5.3-05 | MUST | system | none | The peripheral must have protocol of tlul since all peripherals use TL-UL. | T1.5.3:s10, T1.5.3:s11 (p178) |
| CP-T1.5.3-06 | MUST | system | none | Each bus interface entry must contain a direction of either host or device. | T1.5.3:s14, T1.5.3:s15 (p185) |
| CP-T1.5.3-07 | MUST | master | scenario | All bus hosts must use the same clock as the defined primary host clock. | T1.5.3:s16 (p185) |
| CP-T1.5.3-08 | MAY | system | none | An entry may include a name, which is added as a prefix to the module's top-level port names. | T1.5.3:s20, T1.5.3:s21 (p192) |
| CP-T1.5.3-09 | MUST | system | none | The name field must be provided to avoid port name collisions. *(when: When another entry in the list has the same direction)* | T1.5.3:s22 (p192) |

## T1.5.5 Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.5.5-01 | MUST | system | none | The module must have an output named intr_name_o for each interrupt name. *(when: For each name in the interrupt list)* | T1.5.5:s4 (p222) |

## T1.6 Register Handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.6-01 | MUST | system | none | All lowRISC peripheral designs must conform to the register specification. | T1.6:s2 (p334) |

## T1.8 Interrupt Handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8-01 | SHOULD | system | none | All interrupts shall have common naming, hardware interfaces, and software interfaces. *(when: Where possible)* | T1.8:s2 (p476) |

## T1.8.1 Conventions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.1-01 | MUST | source | assertion | Wired CIP interrupts use active-high level-triggering. | T1.8.1:s1 (p481) |

## T1.8.2 Defining Interrupts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.2-01 | MUST | system | none | Each interrupt_list entry must have a required name key of type string. | T1.8.2:s2, T1.8.2:s4 (p492) |
| CP-T1.8.2-02 | MAY | system | none | Each interrupt_list entry may have an optional desc string. | T1.8.2:s5 (p499) |
| CP-T1.8.2-03 | MAY | system | none | Each entry may have an optional type, Event or Status, defaulting to Event if unspecified. | T1.8.2:s6 (p500) |

## T1.8.3 Interrupts per module

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.3-01 | MUST | system | scenario | A peripheral generates a separate wired interrupt for each interrupt source. | T1.8.3:s1 (p504) |
| CP-T1.8.3-02 | MUST_NOT | system | none | Peripherals do not send a single combined interrupt for the processor to disambiguate by querying the peripheral. | T1.8.3:s4 (p504) |

## T1.8.4 Register Creation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.4-01 | MUST | system | scenario | INTR_STATE, INTR_ENABLE and INTR_TEST registers are created at the top of the address map in that order, one bitfield per interrupt. | T1.8.4:s1, T1.8.4:s2, T1.8.4:s3 (p511) |
| CP-T1.8.4-02 | MUST_NOT | system | none | The .hjson must not define more than 32 interrupts per peripheral. | T1.8.4:s4 (p511) |
| CP-T1.8.4-03 | MUST | slave | scenario | INTR_STATE at offset 0x0 holds interrupt state, INTR_ENABLE at 0x4 masks it to intr_o, INTR_TEST at 0x8 is write-only and asserts the interrupt. | T1.8.4:s5, T1.8.4:s6, T1.8.4:s7 (p519) |
| CP-T1.8.4-04 | MUST | slave | scenario | INTR_STATE shows raw latched interrupt events and is not qualified by INTR_ENABLE. | T1.8.4:s8 (p523) |

## T1.8.5 CIP Interrupt Types

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5-01 | MAY | system | none | A designer may choose between Event and Status interrupt behaviors. | T1.8.5:s6 (p533) |
| CP-T1.8.5-02 | MUST | slave | scenario | The interrupt is cleared only by a software W1C write of the INTR_STATE bitfield. *(when: Event type interrupt)* | T1.8.5:s8, T1.8.5.1:s6 (p535) |
| CP-T1.8.5-03 | MUST | source | scenario | Interrupt requests are triggered while input is true, including immediately after the previous request is acknowledged. *(when: Status type interrupt, input persistently true)* | T1.8.5:s9 (p537) |
| CP-T1.8.5-04 | MAY | system | none | Designers may generate interrupts from instantaneous events or persistent status, making software handlers simpler and race-free. | T1.8.5:s13, T1.8.5:s14 (p542) |

## T1.8.5.1 Event Type Interrupt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5.1-01 | MUST | source | both | When the event occurs it is latched into the INTR_STATE bitfield and intr_o is latched high until acknowledged, then low. *(when: Event type interrupt)* | T1.8.5.1:s3, T1.8.5.1:s5 (p551) |
| CP-T1.8.5.1-02 | MAY | system | none | prim_intr_hw parameterized with .IntrT("Event") can generate Event interrupt hardware. | T1.8.5.1:s4 (p555) |

## T1.8.5.2 Status Type Interrupt

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.5.2-01 | MUST | system | assertion | A status type interrupt must drive a wired level-triggered interrupt directly from the hardware input signal, qualified only by INTR_ENABLE, staying asserted while the input is asserted. *(when: Status type interrupt)* | T1.8.5.2:s1, T1.8.5.2:s2 (p585) |
| CP-T1.8.5.2-02 | MUST | system | scenario | The wired status interrupt must not deassert until the root cause of the hardware input signal is addressed by software intervention. *(when: Status type interrupt)* | T1.8.5.2:s3, T1.8.5.2:s4 (p585) |
| CP-T1.8.5.2-03 | MUST_NOT | slave | scenario | Software cannot acknowledge a status type interrupt through INTR_STATE, which is read-only (ro) in this context. *(when: Status type interrupt)* | T1.8.5.2:s5 (p585) |
| CP-T1.8.5.2-04 | MAY | system | none | The generic component prim_intr_hw can generate the correct status interrupt hardware when parameterized with .IntrT("Status"). *(when: Generating status type interrupt hardware)* | T1.8.5.2:s6 (p591) |
| CP-T1.8.5.2-05 | SHOULD | master | none | Software should mask the interrupt, at the peripheral or further up the tree such as the PLIC. *(when: SW cannot address the root cause or wishes to defer handling)* | T1.8.5.2:s8 (p617) |
| CP-T1.8.5.2-06 | MAY | master | scenario | Masking at the peripheral can be achieved by clearing the corresponding bit in INTR_ENABLE. *(when: Masking at the peripheral)* | T1.8.5.2:s9 (p617) |

## T1.8.6 Interrupt Hardware Implementation (Event Type)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.8.6-01 | MAY | system | none | The block diagram shows one possible hardware implementation of interrupt foo; other implementations are permitted. | T1.8.6:s1 (p622) |
| CP-T1.8.6-02 | MUST | slave | assertion | The event must set the associated bit in INTR_STATE to 1. *(when: Event foo is detected)* | T1.8.6:s7 (p630) |
| CP-T1.8.6-03 | MAY | master | scenario | A write of 1 to the associated foo bit of INTR_TEST can set the corresponding INTR_STATE bit. *(when: Write of 1 to the foo bit of INTR_TEST)* | T1.8.6:s8 (p630) |
| CP-T1.8.6-04 | MUST | slave | assertion | The outgoing interrupt intr_foo_o must be the INTR_STATE output ANDed with INTR_ENABLE. | T1.8.6:s9 (p630) |
| CP-T1.8.6-05 | MUST | slave | both | A write of 1 to an INTR_STATE bit clears the latched value, but INTR_STATE returns to true if the event is still active. *(when: Software writes 1 to the INTR_STATE bit)* | T1.8.6:s10, T1.8.6:s11 (p636) |
| CP-T1.8.6-06 | MUST_NOT | slave | assertion | Hardware must not clear the latched interrupt state; only software can clear it. | T1.8.6:s12 (p636) |

## T1.9.1 Alerts per Module

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.1-01 | MAY | slave | none | Each peripheral can send zero or more alerts, each a distinguishable security threat. | T1.9.1:s2 (p649) |
| CP-T1.9.1-02 | MUST | slave | scenario | Each alert originates in an internal event and must be specially handled within the peripheral and then within the alert handler module. | T1.9.1:s3 (p649) |
| CP-T1.9.1-03 | MUST | slave | scenario | A recoverable alert must be one-time triggered: the alert sender transmits a single alert event when the error condition is asserted. *(when: Recoverable alert)* | T1.9.1:s4, T1.9.1:s5, T1.9.1:s6, T1.9.1:s7 (p653) |
| CP-T1.9.1-04 | MUST | slave | scenario | A fatal alert must be continuously transmitted by the alert sender until the system is reset. *(when: Fatal alert)* | T1.9.1:s4, T1.9.1:s8, T1.9.1:s9, T1.9.1:s10 (p653) |
| CP-T1.9.1-05 | SHOULD | slave | none | Fatal alerts should also trigger local security countermeasures. *(when: Fatal alert and local countermeasures exist)* | T1.9.1:s11 (p663) |
| CP-T1.9.1-06 | SHOULD | slave | none | Error conditions should use the recommended alert type listed in the table; the regular IRQ column entries marked (x) are optional. *(when: Common error conditions)* | T1.9.1:s14, T1.9.1:s16 (p667) |
| CP-T1.9.1-07 | MAY | slave | none | A peripheral may optionally send a regular IRQ for any alert event, if needed by the programming model. *(when: Alert event occurs)* | T1.9.1:s17, T1.9.1:s18 (p681) |

## T1.9.2 Defining Alerts

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.2-01 | MUST | any | none | Alerts shall be given a meaningful name indicative of their cause. | T1.9.2:s3 (p690) |
| CP-T1.9.2-02 | MUST | any | none | Recoverable alerts must be prefixed with recov_ and fatal alerts must be prefixed with fatal_. *(when: Alert naming)* | T1.9.2:s4 (p690) |
| CP-T1.9.2-03 | MAY | any | none | Alert names may default to just recov and/or fatal, implying no more than one alert of that type is exposed. *(when: Many diverse sources bundled into one alert event)* | T1.9.2:s7, T1.9.2:s8 (p694) |

## T1.9.3 Test Alert Register Creation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.3-01 | MUST | slave | scenario | Every peripheral has a write-only (wo) ALERT_TEST register for software to test alert reporting in the alert handler. | T1.9.3:s1, T1.9.3:s2 (p700) |
| CP-T1.9.3-02 | MUST | slave | scenario | Every alert has one field bit in ALERT_TEST, connected to the test input of the corresponding prim_alert_sender. | T1.9.3:s3 (p702) |

## T1.9.4 Alert Hardware Implementation

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| CP-T1.9.4-01 | MUST | slave | assertion | Internal events are sent active-high to the prim_alert_sender within the peripheral. | T1.9.4:s1 (p707) |
| CP-T1.9.4-02 | MUST | slave | both | One prim_alert_sender must be instantiated per distinct alert event, with IsFatal set to 1 for fatal alerts so the alert is latched until reset. | T1.9.4:s2 (p707) |
| CP-T1.9.4-03 | MAY | any | none | The peripheral maintainer determines distinct alert events; multiple sources can be bundled depending on the required distinction. | T1.9.4:s3 (p710) |
| CP-T1.9.4-04 | SHOULD | any | none | Each peripheral should bundle alert sources into one or two distinct alerts, for example one fatal and one recoverable. | T1.9.4:s4 (p710) |
| CP-T1.9.4-05 | SHOULD | slave | scenario | The IP should expose a cause register for disambiguation. *(when: Comportable IP with multiple bundled alerts)* | T1.9.4:s6 (p715) |
| CP-T1.9.4-06 | MUST | slave | scenario | Cause registers for recoverable alerts must be clearable by SW or automatically cleared by HW. *(when: Cause register for recoverable alerts)* | T1.9.4:s7 (p715) |
| CP-T1.9.4-07 | MUST_NOT | slave | scenario | Cause registers for fatal alerts must not be clearable in any way and must be read-only. *(when: Cause register for fatal alerts)* | T1.9.4:s8 (p715) |
| CP-T1.9.4-08 | MUST | slave | both | The prim_alert_sender converts the event into a differentially encoded signal pair routed to the hardware alert handler. | T1.9.4:s9 (p719) |
| CP-T1.9.4-09 | MUST | system | none | The alert handler is generated with enough alert ports for each alert declared in the included peripheral configuration files. | T1.9.4:s10 (p719) |
