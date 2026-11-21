// ot_gpio_nnc: integration wrapper of the OpenTitan gpio for NNC Pipeline.
// Written for NNC Pipeline (not part of OpenTitan). It changes no behaviour of gpio; it only
// flattens the struct ports so that a cocotb test can drive them, and it closes the two
// protocols a test bench should not have to implement:
//   - TL-UL bus integrity: the A-channel integrity (a_user.cmd_intg, a_user.data_intg) is
//     generated here with OpenTitan's tlul_cmd_intg_gen; i_a_intg_flip inverts one bit of it
//     (fault injection). The D-channel response integrity is checked here with OpenTitan's
//     tlul_rsp_intg_chk and reported on o_d_intg_err.
//   - the alert differential handshake: OpenTitan's prim_alert_receiver answers gpio's
//     alert sender and reports each alert on o_alert (ping requests are never made).
// RACL is disabled (gpio parameter EnableRacl = 0), and the alert path is synchronous
// (AlertAsyncOn = 0 on both sides). GpioAsyncOn and GpioAsHwStrapsEn are passed through.
`include "prim_assert.sv"

module ot_gpio_nnc #(
  parameter bit GpioAsyncOn      = 1'b1,   // 2-stage synchronizers on all GPIO inputs
  parameter bit GpioAsHwStrapsEn = 1'b1    // strap sampling on strap_en
) (
  input  logic        clk_i,
  input  logic        rst_ni,

  // TL-UL A channel (host to device)
  input  logic        i_a_valid,
  output logic        o_a_ready,
  input  logic [2:0]  i_a_opcode,
  input  logic [2:0]  i_a_param,
  input  logic [1:0]  i_a_size,
  input  logic [7:0]  i_a_source,
  input  logic [31:0] i_a_address,
  input  logic [3:0]  i_a_mask,
  input  logic [31:0] i_a_data,
  input  logic        i_a_instr,       // 1: instruction fetch (a_user.instr_type = MuBi4True)
  input  logic        i_a_intg_flip,   // 1: bit 0 of the generated a_user.cmd_intg is inverted

  // TL-UL D channel (device to host)
  output logic        o_d_valid,
  input  logic        i_d_ready,
  output logic [2:0]  o_d_opcode,
  output logic [2:0]  o_d_param,
  output logic [1:0]  o_d_size,
  output logic [7:0]  o_d_source,
  output logic        o_d_sink,
  output logic [31:0] o_d_data,
  output logic        o_d_error,
  output logic        o_d_intg_err,    // response integrity of the current D beat is wrong

  // Alert (fatal_fault) as seen by an alert receiver
  output logic        o_alert,         // 1 for one cycle per received alert
  output logic        o_alert_integ_fail,

  // GPIO pins (chip IO)
  input  logic [31:0] i_gpio,          // cio_gpio_i
  output logic [31:0] o_gpio,          // cio_gpio_o
  output logic [31:0] o_gpio_en,       // cio_gpio_en_o

  // Interrupts
  output logic [31:0] o_intr_gpio,     // intr_gpio_o

  // Straps
  input  logic        i_strap_en,      // strap_en_i
  output logic        o_straps_valid,  // sampled_straps_o.valid
  output logic [31:0] o_straps_data    // sampled_straps_o.data
);

  import tlul_pkg::*;

  tl_h2d_t tl_h2d_raw, tl_h2d_intg, tl_h2d;
  tl_d2h_t tl_d2h;
  prim_alert_pkg::alert_rx_t [gpio_reg_pkg::NumAlerts-1:0] alert_rx;
  prim_alert_pkg::alert_tx_t [gpio_reg_pkg::NumAlerts-1:0] alert_tx;
  gpio_pkg::gpio_straps_t sampled_straps;

  always_comb begin
    tl_h2d_raw            = TL_H2D_DEFAULT;
    tl_h2d_raw.a_valid    = i_a_valid;
    tl_h2d_raw.a_opcode   = tl_a_op_e'(i_a_opcode);
    tl_h2d_raw.a_param    = i_a_param;
    tl_h2d_raw.a_size     = i_a_size;
    tl_h2d_raw.a_source   = i_a_source;
    tl_h2d_raw.a_address  = i_a_address;
    tl_h2d_raw.a_mask     = i_a_mask;
    tl_h2d_raw.a_data     = i_a_data;
    tl_h2d_raw.a_user.instr_type = i_a_instr ? prim_mubi_pkg::MuBi4True : prim_mubi_pkg::MuBi4False;
    tl_h2d_raw.d_ready    = i_d_ready;
  end

  tlul_cmd_intg_gen u_cmd_intg_gen (
    .tl_i (tl_h2d_raw),
    .tl_o (tl_h2d_intg)
  );

  always_comb begin
    tl_h2d = tl_h2d_intg;
    tl_h2d.a_user.cmd_intg[0] = tl_h2d_intg.a_user.cmd_intg[0] ^ i_a_intg_flip;
  end

  gpio #(
    .AlertAsyncOn     (1'b0),
    .GpioAsHwStrapsEn (GpioAsHwStrapsEn),
    .GpioAsyncOn      (GpioAsyncOn),
    .EnableRacl       (1'b0)
  ) u_gpio (
    .clk_i,
    .rst_ni,
    .strap_en_i       (i_strap_en),
    .sampled_straps_o (sampled_straps),
    .tl_i             (tl_h2d),
    .tl_o             (tl_d2h),
    .intr_gpio_o      (o_intr_gpio),
    .alert_rx_i       (alert_rx),
    .alert_tx_o       (alert_tx),
    .racl_policies_i  ('0),
    .racl_error_o     (),
    .cio_gpio_i       (i_gpio),
    .cio_gpio_o       (o_gpio),
    .cio_gpio_en_o    (o_gpio_en)
  );

  tlul_rsp_intg_chk u_rsp_intg_chk (
    .tl_i  (tl_d2h),
    .err_o (o_d_intg_err)
  );

  prim_alert_receiver #(
    .AsyncOn (1'b0)
  ) u_alert_receiver (
    .clk_i,
    .rst_ni,
    .init_trig_i  (prim_mubi_pkg::MuBi4False),
    .ping_req_i   (1'b0),
    .ping_ok_o    (),
    .integ_fail_o (o_alert_integ_fail),
    .alert_o      (o_alert),
    .alert_rx_o   (alert_rx[0]),
    .alert_tx_i   (alert_tx[0])
  );

  assign o_a_ready      = tl_d2h.a_ready;
  assign o_d_valid      = tl_d2h.d_valid;
  assign o_d_opcode     = 3'(tl_d2h.d_opcode);
  assign o_d_param      = tl_d2h.d_param;
  assign o_d_size       = tl_d2h.d_size;
  assign o_d_source     = tl_d2h.d_source;
  assign o_d_sink       = tl_d2h.d_sink;
  assign o_d_data       = tl_d2h.d_data;
  assign o_d_error      = tl_d2h.d_error;
  assign o_straps_valid = sampled_straps.valid;
  assign o_straps_data  = sampled_straps.data;

endmodule
