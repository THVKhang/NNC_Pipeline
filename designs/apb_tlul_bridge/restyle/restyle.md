# Restyled RTL: apb_tlul_bridge

Status: **clean** after 1 attempt(s) (agent A16, opus); cost US$0.93. `rtl/` of the design is unchanged; the rewrite is in `restyle/rtl/`. Adopting it is the designer's decision.

## Equivalence with the original

**PROVEN** (BMC PASS, proof PASS, depth 20). PROVEN: every output equal in every cycle for every input sequence after reset, for this configuration; registers without reset start at 0 in both versions.

## Rule findings (docs/RTL_RULES.md)

| | Errors | Warnings | Notes |
|---|---|---|---|
| original | 0 | 6 | 0 |
| restyled | 0 | 0 | 0 |

## Suspected bugs in the original (not fixed: behaviour kept)

- original/m_tlul_if.sv:89 (with original/m_apb_if.sv:69, 90-91): Not a bug in normal use, reported for the reviewer. w_load is gated by the TL-UL FSM being IDLE, but the APB FSM goes to BUSY on w_req_launch whether or not the TL-UL side loaded the request. If a launch ever came while the TL-UL FSM was not IDLE, the APB FSM would wait in BUSY for a response to a request that was never issued, and the transfer would hang. The invariant 'TL-UL FSM is idle whenever the APB FSM is idle' (BR-5.4-06) should make this case unreachable, so I kept it unchanged.
- original/m_apb_if.sv:95-97, 115: Observation only. BUSY -> DONE (and so PREADY) depends only on i_resp_valid; i_apb_psel and i_apb_penable are not checked. BR-3-18 (PREADY only in an Access cycle) therefore holds only if the APB requester keeps to the protocol. I kept the behaviour as it is.

## Open points

- RR-40: PARA_SRC_ID is a 32-bit typed parameter, and only bits [PARA_SRC_W-1:0] are used (now through localparam LPARA_SRC_ID). The original does the same. If some Verilator version reports the unused upper bits of the parameter, the only fixes are a lint waiver or a change to how the parameter is compared. Comparing the full 32 bits would change behaviour for out-of-range PARA_SRC_ID values, so I kept the bit-select.
- BR-3-33 / BR-8-09 (illegal parameter values reported at elaboration) is not in the original RTL, and I did not add it. An elaboration check would have to be simulation-only code or $error, and RR-11 forbids system tasks in synthesizable RTL; it belongs in the verification source set.
