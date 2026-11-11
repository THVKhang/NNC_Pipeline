// filelist.f - RTL files in compile order (leaf modules first, top last).
// Top module: m_vlsit_afifo_top
// Paths are relative to the folder of this file; run tools from that folder.
// Added by NNC: the library files of 000_Common needed to elaborate every branch, in the order of the
// upstream lint/filelist_lint.f (synchronizer cells, SRAM model, macro and synchronizer wrappers).
// The +define+VLSIT_SYNTHESIS of that list is NOT set here: without it the synchronizer wrapper uses its
// metastability model (spec REQ-VER-001); set `nnc config <design> defines=VLSIT_SYNTHESIS` for the
// synthesis branch.
VLSIT_CELL_SYNC_DFF_RN.sv
VLSIT_CELL_SYNC_DFF_SN.sv
VLSIT_CELL_SYNC_2FF_RN.sv
VLSIT_CELL_SYNC_2FF_SN.sv
VLSIT_CELL_SYNC_3FF_RN.sv
VLSIT_CELL_SYNC_3FF_SN.sv
VLSIT_CELL_SYNC_4FF_RN.sv
VLSIT_CELL_SYNC_4FF_SN.sv
VLSIT_CELL_SRAM_1W1R.sv
m_vlsit_afifo_ram_macro.sv
m_vlsit_afifo_mem.sv
m_vlsit_afifo_cell_sync.sv
m_vlsit_afifo_sync.sv
m_vlsit_afifo_rd.sv
m_vlsit_afifo_wr.sv
m_vlsit_afifo_top.sv
