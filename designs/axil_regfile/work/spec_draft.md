# Specification draft: axil_regfile

Agent A0 (opus, spec-v1) wrote `spec/axil_regfile_Design_Specification.md` from the designer's description in 2 attempt(s), cost US$1.27.

**This is a proposal.** Read it, correct it, and answer the open questions in the text before running the flow: the verification and the RTL are generated from this text only. Gate G1 records its hash.

Shape check: 35 sections, 23 ports, 3 parameters, 123 requirement IDs, 144 normative sentences.

## Assumptions A0 made (the description did not say)

- The width of o_regs is given by the local parameter LPARA_REGS_W. Its Description cell holds only the expression PARA_NUM_REGS*32 so that the flow can read it (this fixes the reported error).
- o_s_axi_awready, o_s_axi_wready and o_s_axi_arready are 0 during reset and in the cycle that ends at the first edge after release. They are 1 from that edge.
- The readies are registered and do not depend on the valids, so the block has no combinational path from an input to an output.
- The write response latency is exactly 1 cycle after Ec (the later of the AW and W transfers), and the read data latency is exactly 1 cycle after the AR transfer.
- The register is written at Ec, and the new value is on o_regs from the cycle that starts at Ec.
- A read samples the register or i_status at the edge of its AR transfer. A write completing at that same edge gives the old value, and a write completing earlier gives the new value.
- The decode compares all bits [PARA_ADDR_W-1:2] of the address. An address with a 1 in any bit at or above bit 7 is unmapped, so no register appears at more than one address.
- bresp, rresp and rdata are 0 during reset. Outside reset, they are not specified and not checked while their valid is 0.
- Asserting reset discards any held or pending transaction. No response is given for it after release, and it writes no register.
- Configurations were added for PARA_ADDR_W = 7 and 16, including PARA_NUM_REGS = 16 with PARA_ADDR_W = 7.
- Illegal parameter values should stop elaboration with an error. This is not verified.

## Open questions for the designer

- Is a throughput of one write and one read every 2 cycles enough for the CPU?
- Is there an area budget for the GF180MCU implementation?
- Should the readies be 0 during reset (as assumed), or is a cheaper design with readies at 1 during reset wanted?
