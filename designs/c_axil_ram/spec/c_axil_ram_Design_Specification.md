<!-- Excerpt of README.md, verbatim: the sections `axil_ram` module, Common signals, Common parameters and AXI4-Lite Interface Example, under a title line written for NNC Pipeline. Source: https://github.com/alexforencich/verilog-axi, commit 516bd5dadc3365b7f9e225d2af8fe0b8d804fe53. Licence: MIT (see ../NOTICE.md). -->

# Verilog AXI Components: axil_ram

### `axil_ram` module

AXI lite RAM with parametrizable data and address interface widths.

### Common signals

    awid     : Write address ID
    awaddr   : Write address
    awlen    : Write burst length
    awsize   : Write burst size
    awburst  : Write burst type
    awlock   : Write locking
    awcache  : Write cache handling
    awprot   : Write protection level
    awqos    : Write QoS setting
    awregion : Write region
    awuser   : Write user sideband signal
    awvalid  : Write address valid
    awready  : Write address ready (from slave)
    wdata    : Write data
    wstrb    : Write data strobe (byte select)
    wlast    : Write data last transfer in burst
    wuser    : Write data user sideband signal
    wvalid   : Write data valid
    wready   : Write data ready (from slave)
    bid      : Write response ID
    bresp    : Write response
    buser    : Write response user sideband signal
    bvalid   : Write response valid
    bready   : Write response ready (from master)
    arid     : Read address ID
    araddr   : Read address
    arlen    : Read burst length
    arsize   : Read burst size
    arburst  : Read burst type
    arlock   : Read locking
    arcache  : Read cache handling
    arprot   : Read protection level
    arqos    : Read QoS setting
    arregion : Read region
    aruser   : Read user sideband signal
    arvalid  : Read address valid
    arready  : Read address ready (from slave)
    rid      : Read data ID
    rdata    : Read data
    rresp    : Read response
    rlast    : Read data last transfer in burst
    ruser    : Read data user sideband signal
    rvalid   : Read response valid
    rready   : Read response ready (from master)

### Common parameters

    ADDR_WIDTH           : width of awaddr and araddr signals
    DATA_WIDTH           : width of wdata and rdata signals
    STRB_WIDTH           : width of wstrb signal
    ID_WIDTH             : width of *id signals
    AWUSER_ENABLE        : enable awuser signal
    AWUSER_WIDTH         : width of awuser signal
    WUSER_ENABLE         : enable wuser signal
    WUSER_WIDTH          : width of wuser signal
    BUSER_ENABLE         : enable buser signal
    BUSER_WIDTH          : width of buser signal
    ARUSER_ENABLE        : enable aruser signal
    ARUSER_WIDTH         : width of aruser signal
    RUSER_ENABLE         : enable ruser signal
    RUSER_WIDTH          : width of ruser signal

### AXI4-Lite Interface Example

Write

                ___     ___     ___     ___     ___    
    clk     ___/   \___/   \___/   \___/   \___/   \___
                _______
    awid    XXXX_ID____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awaddr  XXXX_ADDR__XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awlen   XXXX_00____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awsize  XXXX_0_____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awburst XXXX_0_____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awprot  XXXX_PROT__XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    awvalid ___/       \_______________________________
            ___________         _______________________
    awready            \_______/
                _______________
    wdata   XXXX_DATA__________XXXXXXXXXXXXXXXXXXXXXXXX
                _______________
    wstrb   XXXX_STRB__________XXXXXXXXXXXXXXXXXXXXXXXX
                _______________
    wvalid  ___/               \_______________________
                        _______
    wready  ___________/       \_______________________
                                        _______
    bid     XXXXXXXXXXXXXXXXXXXXXXXXXXXX_ID____XXXXXXXX
                                        _______
    bresp   XXXXXXXXXXXXXXXXXXXXXXXXXXXX_RESP__XXXXXXXX
                                        _______
    bvalid  ___________________________/       \_______
            ___________________________________________
    bready


Read

                ___     ___     ___     ___     ___    
    clk     ___/   \___/   \___/   \___/   \___/   \___
                _______
    arid    XXXX_ID____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    araddr  XXXX_ADDR__XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    arlen   XXXX_00____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    arsize  XXXX_0_____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    arburst XXXX_0_____XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    arprot  XXXX_PROT__XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                _______
    arvalid ___/       \_______________________________
            ___________________________________________
    arready
                                        _______
    rid     XXXXXXXXXXXXXXXXXXXXXXXXXXXX_ID____XXXXXXXX
                                        _______
    rdata   XXXXXXXXXXXXXXXXXXXXXXXXXXXX_DATA__XXXXXXXX
                                        _______
    rresp   XXXXXXXXXXXXXXXXXXXXXXXXXXXX_RESP__XXXXXXXX
                                        _______
    rvalid  ___________________________/       \_______
            ___________________________________________
    rready
