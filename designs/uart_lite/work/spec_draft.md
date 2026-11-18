# Specification draft: uart_lite

Agent A0 (opus, spec-v1) wrote `spec/uart_lite_Design_Specification.md` from the designer's description in 1 attempt(s), cost US$0.72.

**This is a proposal.** Read it, correct it, and answer the open questions in the text before running the flow: the verification and the RTL are generated from this text only. Gate G1 records its hash.

Shape check: 45 sections, 12 ports, 1 parameters, 77 requirement IDs, 114 normative sentences.

## Assumptions A0 made (the description did not say)

- o_tx_ready is 1 while i_rst_n is 0 (its idle value), and no transmit handshake can happen during reset (D-001).
- The reset release is synchronised to i_clk outside the block; the block has no reset synchronizer (D-008, ENV-001).
- The middle-of-bit sampling offset is H = floor(N/2) edges after the detected start edge T0; data bit i is sampled at T0+H+(i+1)N and the stop bit at M = T0+H+9N (D-002).
- o_rx_valid rises at V = M+2, where M is the edge at which i_rxd is sampled by the first synchronizer stage; this is how 'the cycle after the middle of the stop bit' is read (D-003).
- Start detection needs a synchronised 1 followed by a 0 while the receiver is idle; after a frame error with the line still low, no new frame starts until the line goes high (D-005).
- The synchronizer and the previous-sample flip-flop reset to 1, so a low line at reset release is detected as a start bit (D-006).
- If the held byte is taken at the same edge at which a new byte completes, the new byte is loaded with no overrun (D-004).
- o_rx_data and o_rx_frame_err keep the last loaded values while o_rx_valid = 0 and are 0 after reset (D-007).
- Reset during a transmission abandons the frame and o_txd returns to 1 at once; reset during a reception discards the partial frame and any held byte.
- The frame-error flag of a byte dropped by overrun is not reported.
- Every output is driven directly by a flip-flop (no input-to-output combinational path).
- i_tx_valid may drop without a handshake; the block puts no stability obligation on the transmit or receive stream inputs.
- Illegal parameter values should stop elaboration; their behaviour is not verified.
- Two extra configurations were added: CFG-ODD (N=5) and CFG-MAX (N=65535, reduced number of frames).
- No area budget; 50 MHz applies at the worst-case GF180MCU corner.

## Open questions for the designer

- Confirm that o_tx_ready may be 1 while reset is asserted (the alternative is 0 during reset and 1 from the first cycle after release).
- Confirm the exact receive latency V = M + 2 (2-cycle synchronizer latency, output updated at the edge at which the synchronised stop bit is evaluated).
- Confirm that a held line-low (break) gives exactly one 0x00 byte with o_rx_frame_err = 1 and that a 1-to-0 transition is needed before the next frame.
- Is an area budget required for the GF180MCU implementation?
- Which PVT corner does the 50 MHz timing target apply to?
- Is the simulation time of CFG-MAX (N=65535, 655350 cycles per frame) acceptable in the regression, and can the flow run a reduced test list for one configuration?
- Should illegal values of PARA_UART_CLKS_PER_BIT be a hard elaboration error (shall) instead of a recommendation (should)?
