<!-- Excerpt of README.md, verbatim: lines 84-87, 97-112, 268-272 and 452-485 (the PCPI sentences of the introduction, the module table of picorv32.v, ENABLE_DIV and the PCPI section), under a title line written for NNC Pipeline. Source: https://github.com/YosysHQ/picorv32, commit ef203c2b0a3fb793280f5114941416c425c5b461. Licence: ISC (see ../NOTICE.md). -->

# PicoRV32 PCPI division core

The optional Pico Co-Processor Interface (PCPI) can be used to implement
non-branching instructions in an external coprocessor. Implementations
of PCPI cores that implement the M Standard Extension instructions
`MUL[H[SU|U]]` and `DIV[U]/REM[U]` are included in this package.

#### picorv32.v

This Verilog file contains the following Verilog modules:

| Module                   | Description                                                           |
| ------------------------ | --------------------------------------------------------------------- |
| `picorv32`               | The PicoRV32 CPU                                                      |
| `picorv32_axi`           | The version of the CPU with AXI4-Lite interface                       |
| `picorv32_axi_adapter`   | Adapter from PicoRV32 Memory Interface to AXI4-Lite                   |
| `picorv32_wb`            | The version of the CPU with Wishbone Master interface                 |
| `picorv32_pcpi_mul`      | A PCPI core that implements the `MUL[H[SU\|U]]` instructions          |
| `picorv32_pcpi_fast_mul` | A version of `picorv32_pcpi_fast_mul` using a single cycle multiplier |
| `picorv32_pcpi_div`      | A PCPI core that implements the `DIV[U]/REM[U]` instructions          |

Simply copy this file into your project.


#### ENABLE_DIV (default = 0)

This parameter internally enables PCPI and instantiates the `picorv32_pcpi_div`
core that implements the `DIV[U]/REM[U]` instructions. The external PCPI
interface only becomes functional when ENABLE_PCPI is set as well.

Pico Co-Processor Interface (PCPI)
----------------------------------

The Pico Co-Processor Interface (PCPI) can be used to implement non-branching
instructions in external cores:

    output        pcpi_valid
    output [31:0] pcpi_insn
    output [31:0] pcpi_rs1
    output [31:0] pcpi_rs2
    input         pcpi_wr
    input  [31:0] pcpi_rd
    input         pcpi_wait
    input         pcpi_ready

When an unsupported instruction is encountered and the PCPI feature is
activated (see ENABLE_PCPI above), then `pcpi_valid` is asserted, the
instruction word itself is output on `pcpi_insn`, the `rs1` and `rs2`
fields are decoded and the values in those registers are output
on `pcpi_rs1` and `pcpi_rs2`.

An external PCPI core can then decode the instruction, execute it, and assert
`pcpi_ready` when execution of the instruction is finished. Optionally a
result value can be written to `pcpi_rd` and `pcpi_wr` asserted. The
PicoRV32 core will then decode the `rd` field of the instruction and
write the value from `pcpi_rd` to the respective register.

When no external PCPI core acknowledges the instruction within 16 clock
cycles, then an illegal instruction exception is raised and the respective
interrupt handler is called. A PCPI core that needs more than a couple of
cycles to execute an instruction, should assert `pcpi_wait` as soon as
the instruction has been decoded successfully and keep it asserted until
it asserts `pcpi_ready`. This will prevent the PicoRV32 core from raising
an illegal instruction exception.
