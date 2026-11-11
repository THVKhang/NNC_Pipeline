// filelist.f - RTL files in compile order (leaf modules first, top last).
// Top module: m_vlsit_apbcdc_top
// Paths are relative to the folder of this file; run tools from that folder.
// Added by NNC: the library files of 000_Common needed to elaborate every branch, in the order of the
// upstream lint/filelist_lint.f (synchronizer cells, synchronizer wrapper).
// The +define+VLSIT_SYNTHESIS of that list is NOT set here: without it the synchronizer wrapper uses its
// metastability model (spec REQ-RTL-002, Section 15.1); set `nnc config <design> defines=VLSIT_SYNTHESIS`
// for the synthesis branch.
VLSIT_CELL_SYNC_DFF_RN.sv
VLSIT_CELL_SYNC_DFF_SN.sv
VLSIT_CELL_SYNC_2FF_RN.sv
VLSIT_CELL_SYNC_2FF_SN.sv
VLSIT_CELL_SYNC_3FF_RN.sv
VLSIT_CELL_SYNC_3FF_SN.sv
VLSIT_CELL_SYNC_4FF_RN.sv
VLSIT_CELL_SYNC_4FF_SN.sv
m_vlsit_apbcdc_cell_sync.sv
m_vlsit_apbcdc_sync.sv
m_vlsit_apbcdc_mst.sv
m_vlsit_apbcdc_slv.sv
m_vlsit_apbcdc_top.sv
