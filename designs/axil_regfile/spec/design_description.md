# AXI4-Lite register file: design description

Written as the input of `nnc spec-draft` (the designer's short description; the specification is drafted from it).

A small bank of 32-bit control registers for a single-clock SoC, written and read by a CPU through an AXI4-Lite
subordinate port. The register values drive the SoC logic directly; one extra read-only register shows a status
word from the SoC.

Interfaces (one clock `i_clk`, one active-low asynchronous reset `i_rst_n`; the AXI4-Lite port uses the usual
signal names with an `i_s_axi_`/`o_s_axi_` prefix):
- Write address: `i_s_axi_awvalid`, `o_s_axi_awready`, `i_s_axi_awaddr[PARA_ADDR_W-1:0]`, `i_s_axi_awprot[2:0]`
  (ignored).
- Write data: `i_s_axi_wvalid`, `o_s_axi_wready`, `i_s_axi_wdata[31:0]`, `i_s_axi_wstrb[3:0]`.
- Write response: `o_s_axi_bvalid`, `i_s_axi_bready`, `o_s_axi_bresp[1:0]`.
- Read address: `i_s_axi_arvalid`, `o_s_axi_arready`, `i_s_axi_araddr[PARA_ADDR_W-1:0]`, `i_s_axi_arprot[2:0]`
  (ignored).
- Read data: `o_s_axi_rvalid`, `i_s_axi_rready`, `o_s_axi_rdata[31:0]`, `o_s_axi_rresp[1:0]`.
- SoC side: `o_regs[PARA_NUM_REGS*32-1:0]` (register k is bits 32k+31..32k, the current value, registered) and
  `i_status[31:0]` (sampled when read).

A transfer on any channel happens at a rising clock edge where its valid and ready are both 1. A source keeps
valid at 1 and its payload stable until the transfer happens (this port relies on that for its inputs and
obeys it for its outputs). Ready may depend on valid.

Parameters: `PARA_NUM_REGS` (number of read/write registers, legal 1 to 16, default 8) and `PARA_ADDR_W` (address
width, legal 7 to 16, default 8; 7 bits are needed to reach the status register at 0x40).

Register map (byte addresses; bits [1:0] of an address are ignored, so every access is to a whole aligned word):
- `0x00 + 4k`, k = 0 .. PARA_NUM_REGS-1: register k, read/write, reset value 0.
- `0x40`: status, read-only, returns `i_status`. A write to it changes nothing and answers OKAY.
- Any other address: no register. A write changes nothing, a read returns 0; both answer SLVERR (`2'b10`).
- Response OKAY is `2'b00`. EXOKAY and DECERR are never used.

Writes: the write address and the write data may arrive in either order or at the same edge; the port takes
both before it answers. Only one write is in progress at a time: after taking an address it takes no other
address until the response has been taken, and the same for data. A byte lane of the register is written only
when its `wstrb` bit is 1. The write response comes at the earliest one cycle after both the address and the data
have been taken, and stays until taken. The written value appears on `o_regs` from the cycle after the edge at
which the register was written.

Reads: one read in progress at a time; the data come at the earliest one cycle after the address is taken and
stay stable until taken. A read and a write may run at the same time on their own channels. When a read and a
write of the same register are in progress together, the read returns either the old or the new value, never a
mix; which one is up to the RTL (the specification should say which, if it decides).

Reset: every register is 0, no response valid, `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready` may be 1
or 0 but nothing is taken during reset.

Target: GF180MCU, 50 MHz. Verify the default configuration, `PARA_NUM_REGS` = 1 and 16, write strobes, the
status register, unmapped addresses, address and data in both orders, and back-pressure on both response
channels.
