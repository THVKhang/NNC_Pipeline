# Smoke test of the simulation layer (cocotb + Verilator + SVA).
# Run on Linux/WSL with the tools on PATH (source /etc/profile.d/nnc.sh):  make
# SIM=icarus is not supported here: Icarus has no concurrent SVA.
SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(CURDIR)/chk_handshake.sv
COCOTB_TOPLEVEL = tb_top
COCOTB_TEST_MODULES = test_smoke
EXTRA_ARGS += --assert -Wno-fatal
SIM_BUILD ?= $(CURDIR)/sim_build

include $(shell cocotb-config --makefiles)/Makefile.sim
