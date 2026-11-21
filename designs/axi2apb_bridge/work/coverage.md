# Coverage closure

Metric **toggle**, target 85.0 %, status **target_met**.

## Measured baseline (the designer chooses whether to set a target, and on which metric)

| Metric | Covered | Percent |
|---|---|---|
| line | 738/746 | 98.9 % |
| block | 209/218 | 95.9 % |
| expression | 102/106 | 96.2 % |
| toggle | 4032/4666 | 86.4 % |
| functional | 39/40 | 97.5 % |

Design scope: left out: never-executed points of package code that the elaborated design does not contain (Verilator instruments every function of an imported package, called or not), and toggles of signal bits that Yosys constant propagation proves constant with the run's parameters, except on signals where the simulator recorded a toggle of such a bit (then the signal counts whole). Left out:
- toggle: 24 points (over all points 4032/4690, 86.0 %)

### Functional cover points never hit

- COVP-024: Illegal FIXED or WRAP length accepted

### Uncovered code items (simulator coverage; read with the RTL)

| Metric | File | Points | Lines |
|---|---|---|---|
| block | m_axi2apb_apb_ctrl.sv | 4 | 111, 115, 126, 147 |
| block | m_axi2apb_rd_seq.sv | 2 | 274, 297 |
| block | m_axi2apb_wr_seq.sv | 3 | 257, 261, 280 |
| expression | m_axi2apb_apb_ctrl.sv | 4 | 111, 115 |
| line | m_axi2apb_apb_ctrl.sv | 4 | 126, 127, 147, 148 |
| line | m_axi2apb_rd_seq.sv | 2 | 297, 298 |
| line | m_axi2apb_wr_seq.sv | 2 | 280, 281 |
| toggle | m_axi2apb_apb_ctrl.sv | 8 | 49, 80 |
| toggle | m_axi2apb_bridge.sv | 8 | 39, 57, 63 |
| toggle | m_axi2apb_rd_seq.sv | 310 | 61, 97, 101, 103, 105, 106, 109, 111, 112, 113, 115, 116 |
| toggle | m_axi2apb_wr_seq.sv | 308 | 64, 107, 109, 111, 112, 115, 117, 118, 119, 121, 122 |

## Closure

| Round | Coverage | Scenarios | Tests added | Note |
|---|---|---|---|---|
| baseline | 75.1 % (3506/4666) | | | |
| 1 | 86.4 % (4032/4666) | 6 | test_cov_101_upper_half_reads, test_cov_102_upper_half_writes, test_cov_103_unsupported_large_size_reads, test_cov_104_unsupported_large_size_writes, test_cov_105_top_of_space_4k_cross_reads, test_cov_106_top_of_space_4k_cross_writes |  |

## Points claimed unreachable by legal stimulus (designer review; still counted)

| Points | Rules | Reason |
|---|---|---|
| m_axi2apb_rd_seq.sv:112 w_rd_size_mask, m_axi2apb_wr_seq.sv:118 w_wr_size_mask, m_axi2apb_rd_seq.sv:101 w_ar_size_bytes, m_axi2apb_rd_seq.sv:111 w_rd_size_bytes, m_axi2apb_wr_seq.sv:107 w_aw_size_bytes, m_axi2apb_wr_seq.sv:117 w_wr_size_bytes | AB-9-06, AB-3-08 | The size field is 3 bits wide, so the largest transfer size it can encode is 2^7 = 128 bytes, even for an unsupported size. The single-beat byte count and its low-bit mask can never reach bit 8 or above, so bits 8 to 31 are constant for every input. |
| m_axi2apb_rd_seq.sv:105 w_ar_wrap_bytes, m_axi2apb_wr_seq.sv:111 w_aw_wrap_bytes, m_axi2apb_rd_seq.sv:106 w_ar_wrap_mask, m_axi2apb_wr_seq.sv:112 w_aw_wrap_mask | AB-9-06, AB-3-07, AB-9-07 | Wrap-range figures are 2^(AxSIZE + log2(beats)). AxSIZE is at most 7 and the longest wrap length the spec decodes is 16 beats, so the range is at most 2^11 bytes. The wrap byte count bits 12 and up, and the matching mask bits 11 and up, never change. The AR/AW-side bits 10 and 11 are already covered. |
| m_axi2apb_rd_seq.sv:115 w_rd_wrap_bytes, m_axi2apb_wr_seq.sv:121 w_wr_wrap_bytes, m_axi2apb_rd_seq.sv:116 w_rd_wrap_mask, m_axi2apb_wr_seq.sv:122 w_wr_wrap_mask | AB-9-06, AB-3-07 | Partly reachable. COV-103 and COV-104 cover the reachable bits: wrap byte count bits 10 and 11, and mask bits 9 and 10. The same 2^11-byte ceiling (AxSIZE <= 7, at most 16 decoded beats) keeps wrap byte count bits 12 to 31 at 0 and mask bits 11 to 31 at 1. |
| m_axi2apb_rd_seq.sv:109 w_ar_total_bytes, m_axi2apb_wr_seq.sv:115 w_aw_total_bytes | AB-3-07, AB-9-07, AB-9-06 | The total burst length is at most 256 beats times 128 bytes (largest encodable size) = 2^15 bytes. Total-byte bits 16 to 32 can never be set by any input. |
| m_axi2apb_rd_seq.sv:103 w_ar_wrap_log2, m_axi2apb_rd_seq.sv:113 w_rd_wrap_log2, m_axi2apb_wr_seq.sv:109 w_aw_wrap_log2, m_axi2apb_wr_seq.sv:119 w_wr_wrap_log2 | AB-3-07 | The wrap length code covers only 2, 4, 8 and 16 beats, so its log2 value is at most 4. Bit 3 of that code is never set. |
| m_axi2apb_apb_ctrl.sv:49 o_apb_paddr, m_axi2apb_apb_ctrl.sv:80 reg_apb_addr, m_axi2apb_bridge.sv:63 o_apb_paddr | AB-3-10, AB-6.2-09, AB-9-13 | Partly reachable. COV-101 and COV-102 cover the reachable bits, 16 to 30 (bit 31 is already covered). PADDR bits [1:0] must always be 0 (word alignment, CHK-004), so those bits cannot toggle. |
| m_axi2apb_bridge.sv:39 o_axi_bresp, m_axi2apb_bridge.sv:57 o_axi_rresp, m_axi2apb_rd_seq.sv:61 o_axi_rresp, m_axi2apb_rd_seq.sv:97 reg_rd_resp, m_axi2apb_wr_seq.sv:64 o_axi_bresp | AB-3-30, AB-3-37, AB-3-41, AB-12-11, AB-10.2-03, AB-10.2-04, AB-3-19 | The bridge returns only OKAY (2'b00) or SLVERR (2'b10) on B and R. It never returns DECERR, and it cannot return EXOKAY because exclusive access is not implemented. Bit 0 of BRESP/RRESP is therefore always 0. |
