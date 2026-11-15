// filelist.f - RTL files in compile order (leaf modules first, top last).
// Top module: m_ahb2axi_top
// Paths are relative to the folder of this file; run tools from that folder.
// Modified by NNC: the upstream list points to ../../002_SyncFIFO/rtl/; those files (same upstream commit)
// are copied into this folder, with the SRAM model and the macro wrapper so that every branch elaborates.
m_ahb2axi_ahb_if.sv
m_ahb2axi_axi_if.sv
VLSIT_CELL_SRAM_1W1R.sv
m_vlsit_sfifo_ram_macro.sv
m_vlsit_sfifo_mem.sv
m_vlsit_sfifo_rd.sv
m_vlsit_sfifo_wr.sv
m_vlsit_sfifo_top.sv
m_ahb2axi_ctrl.sv
m_ahb2axi_top.sv
