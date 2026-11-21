// Formal environment: obligations of the DUT's environment (agent A13, from the specification).
// Reviewed at gate G3: an assumption that is too strong hides real bugs.
module nnc_env #(
  parameter int GpioAsyncOn = 1,
  parameter int GpioAsHwStrapsEn = 1
) (
  input  logic                        clk_i,
  input  logic                        rst_ni,
  input  logic                        i_a_valid,
  input  logic                        o_a_ready,
  input  logic [2:0]                  i_a_opcode,
  input  logic [2:0]                  i_a_param,
  input  logic [1:0]                  i_a_size,
  input  logic [7:0]                  i_a_source,
  input  logic [31:0]                 i_a_address,
  input  logic [3:0]                  i_a_mask,
  input  logic [31:0]                 i_a_data,
  input  logic                        i_a_instr,
  input  logic                        i_a_intg_flip,
  input  logic                        o_d_valid,
  input  logic                        i_d_ready,
  input  logic [2:0]                  o_d_opcode,
  input  logic [2:0]                  o_d_param,
  input  logic [1:0]                  o_d_size,
  input  logic [7:0]                  o_d_source,
  input  logic                        o_d_sink,
  input  logic [31:0]                 o_d_data,
  input  logic                        o_d_error,
  input  logic                        o_d_intg_err,
  input  logic                        o_alert,
  input  logic                        o_alert_integ_fail,
  input  logic [31:0]                 i_gpio,
  input  logic [31:0]                 o_gpio,
  input  logic [31:0]                 o_gpio_en,
  input  logic [31:0]                 o_intr_gpio,
  input  logic                        i_strap_en,
  input  logic                        o_straps_valid,
  input  logic [31:0]                 o_straps_data
);

  // ---------------------------------------------------------------------------
  // Helper signals (derived from interface signals only)
  // ---------------------------------------------------------------------------
  wire a_hs       = rst_ni && i_a_valid && o_a_ready;
  wire d_hs       = rst_ni && o_d_valid && i_d_ready;
  wire a_is_write = (i_a_opcode == 3'd0) || (i_a_opcode == 3'd1);

  // cycles since reset release (0 = first cycle with rst_ni = 1), saturating
  reg [2:0] rel_cnt = 3'd0;
  always @(posedge clk_i) begin
    if (!rst_ni)               rel_cnt <= 3'd0;
    else if (rel_cnt != 3'd7)  rel_cnt <= rel_cnt + 3'd1;
  end

  // A-channel request waiting for a_ready in the previous cycle
  reg a_wait_q = 1'b0;
  always @(posedge clk_i) a_wait_q <= rst_ni && i_a_valid && !o_a_ready;

  // outstanding a_source identifiers (cleared on reset: pending responses are discarded)
  reg  [255:0] src_out = 256'd0;
  wire [255:0] src_clr = d_hs ? (256'd1 << o_d_source) : 256'd0;
  wire [255:0] src_set = a_hs ? (256'd1 << i_a_source) : 256'd0;
  always @(posedge clk_i) begin
    if (!rst_ni) src_out <= 256'd0;
    else         src_out <= (src_out & ~src_clr) | src_set;
  end

  // previous i_gpio value and length of the current run of unchanged i_gpio
  reg [31:0] gpio_q    = 32'd0;
  reg        gpio_q_vld = 1'b0;
  reg [5:0]  gpio_stab = 6'd0;
  always @(posedge clk_i) begin
    gpio_q     <= i_gpio;
    gpio_q_vld <= 1'b1;
    if (!gpio_q_vld || (i_gpio != gpio_q)) gpio_stab <= 6'd0;
    else if (gpio_stab != 6'd63)           gpio_stab <= gpio_stab + 6'd1;
  end

  // strap sampling tracking: first assertion of i_strap_en after reset, 8-cycle post window
  reg       strap_seen = 1'b0;
  reg [3:0] strap_post = 4'd0;
  always @(posedge clk_i) begin
    if (!rst_ni) begin
      strap_seen <= 1'b0;
      strap_post <= 4'd0;
    end else if (!strap_seen && i_strap_en) begin
      strap_seen <= 1'b1;
      strap_post <= 4'd8;
    end else if (strap_post != 4'd0) begin
      strap_post <= strap_post - 4'd1;
    end
  end

  // ---------------------------------------------------------------------------
  // ENV-01: i_a_valid is 0 while rst_ni = 0 and in the first cycle after release (GP-10-30, TL-T3.1.1-01)
  // ---------------------------------------------------------------------------
  always @(posedge clk_i)
    if (!rst_ni || (rel_cnt == 3'd0)) assume (!i_a_valid);

  // ---------------------------------------------------------------------------
  // ENV-02: TL-UL host rule: a pending A request (a_valid=1, a_ready=0) stays valid
  //         with all A-channel fields stable until accepted (GP-4.1-04)
  // ---------------------------------------------------------------------------
  always @(posedge clk_i)
    if (rst_ni && a_wait_q) begin
      assume (i_a_valid);
      assume ($stable(i_a_opcode));
      assume ($stable(i_a_param));
      assume ($stable(i_a_size));
      assume ($stable(i_a_source));
      assume ($stable(i_a_address));
      assume ($stable(i_a_mask));
      assume ($stable(i_a_data));
      assume ($stable(i_a_instr));
      assume ($stable(i_a_intg_flip));
    end

  // ---------------------------------------------------------------------------
  // ENV-03: a distinct a_source per outstanding request (GP-10-26, TL-T3.1.3.2-01)
  // ---------------------------------------------------------------------------
  always @(posedge clk_i)
    if (rst_ni && i_a_valid) assume (!src_out[i_a_source]);

  // ---------------------------------------------------------------------------
  // ENV-04: requests at offset 0x400 and above are not used (GP-10-21)
  // ENV-05: no write (PutFullData/PutPartialData) with i_a_instr = 1 (GP-10-19)
  // ENV-06: no combined ALERT_TEST (offset 0x0C) write that sets fatal_fault and clears regwen
  //         in the same write (0x0000_0001); 0x8000_0001 is used instead (GP-10-15)
  // ---------------------------------------------------------------------------
  always @(posedge clk_i)
    if (rst_ni && i_a_valid) begin
      // ENV-04
      assume (i_a_address[31:10] == 22'd0);
      // ENV-05
      assume (!(i_a_instr && a_is_write));
      // ENV-06
      assume (!(a_is_write && (i_a_address[9:0] == 10'h00C) &&
                i_a_mask[0] && i_a_mask[3] && i_a_data[0] && !i_a_data[31]));
    end

  // ---------------------------------------------------------------------------
  // ENV-07: i_strap_en = 0 while rst_ni = 0 and for at least 4 cycles after release (GP-10-10)
  // ENV-08: at the first rising edge of i_strap_en, i_gpio has been constant for the
  //         24 preceding cycles (GP-10-10, GP-T3.2.3.1-01)
  // ENV-09: i_gpio stays constant for 8 cycles after that rising edge (GP-10-10, GP-T3.2.3.1-01)
  // ---------------------------------------------------------------------------
  always @(posedge clk_i)
    if (GpioAsHwStrapsEn != 0) begin
      // ENV-07
      if (!rst_ni || (rel_cnt < 3'd4)) assume (!i_strap_en);
      // ENV-08
      if (rst_ni && !strap_seen && i_strap_en)
        assume (gpio_q_vld && (i_gpio == gpio_q) && (gpio_stab >= 6'd23));
      // ENV-09
      if (rst_ni && (strap_post != 4'd0)) assume (i_gpio == gpio_q);
    end

  // ---------------------------------------------------------------------------
  // ENV-10: after a write that may change CTRL_EN_INPUT_FILTER[i] (CTRL_EN_INPUT_FILTER at 0x3C,
  //         byte lanes per a_mask, or PER_PIN_INTR_CTRL_i at 0x204+8*i with byte 0), i_gpio[i]
  //         is kept constant for 24 cycles (GP-10-09)
  // ---------------------------------------------------------------------------
  wire filt_w_full = a_hs && a_is_write && (i_a_address[9:2] == 8'h0F);
  wire filt_w_pin  = a_hs && a_is_write && (i_a_address[9:8] == 2'b10) &&
                     i_a_address[2] && i_a_mask[0];
  wire [31:0] filt_hit =
      (filt_w_full ? {{8{i_a_mask[3]}}, {8{i_a_mask[2]}}, {8{i_a_mask[1]}}, {8{i_a_mask[0]}}} : 32'd0) |
      (filt_w_pin  ? (32'd1 << i_a_address[7:3]) : 32'd0);

  genvar g;
  generate
    for (g = 0; g < 32; g = g + 1) begin : g_filt_win
      reg [4:0] cnt = 5'd0;
      always @(posedge clk_i) begin
        if (!rst_ni)              cnt <= 5'd0;
        else if (filt_hit[g])     cnt <= 5'd24;
        else if (cnt != 5'd0)     cnt <= cnt - 5'd1;
      end
      always @(posedge clk_i)
        if (rst_ni && (cnt != 5'd0)) assume (i_gpio[g] == gpio_q[g]);
    end
  endgenerate
endmodule
