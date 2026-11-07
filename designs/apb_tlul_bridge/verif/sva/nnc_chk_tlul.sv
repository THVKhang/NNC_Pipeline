module nnc_chk_tlul #(
  parameter int PARA_ADDR_W = 32,
  parameter int PARA_SRC_W = 8,
  parameter int PARA_SRC_ID = 0,
  parameter int PARA_A_USER_W = 1,
  parameter int PARA_D_SINK_W = 1,
  parameter int PARA_D_USER_W = 1
) (
  input  logic                        i_clk_core,
  input  logic                        i_rst_n_core,
  input  logic                        i_apb_psel,
  input  logic                        i_apb_penable,
  input  logic                        i_apb_pwrite,
  input  logic [(PARA_ADDR_W)-1:0]    i_apb_paddr,
  input  logic [2:0]                  i_apb_pprot,
  input  logic [3:0]                  i_apb_pstrb,
  input  logic [31:0]                 i_apb_pwdata,
  input  logic                        o_apb_pready,
  input  logic [31:0]                 o_apb_prdata,
  input  logic                        o_apb_pslverr,
  input  logic                        o_tlul_a_valid,
  input  logic                        i_tlul_a_ready,
  input  logic [2:0]                  o_tlul_a_opcode,
  input  logic [2:0]                  o_tlul_a_param,
  input  logic [1:0]                  o_tlul_a_size,
  input  logic [(PARA_SRC_W)-1:0]     o_tlul_a_source,
  input  logic [(PARA_ADDR_W)-1:0]    o_tlul_a_address,
  input  logic [3:0]                  o_tlul_a_mask,
  input  logic [31:0]                 o_tlul_a_data,
  input  logic [(PARA_A_USER_W)-1:0]  o_tlul_a_user,
  input  logic                        i_tlul_d_valid,
  input  logic                        o_tlul_d_ready,
  input  logic [2:0]                  i_tlul_d_opcode,
  input  logic [(PARA_SRC_W)-1:0]     i_tlul_d_source,
  input  logic [31:0]                 i_tlul_d_data,
  input  logic                        i_tlul_d_error,
  input  logic [2:0]                  i_tlul_d_param,
  input  logic [1:0]                  i_tlul_d_size,
  input  logic [(PARA_D_SINK_W)-1:0]  i_tlul_d_sink,
  input  logic [(PARA_D_USER_W)-1:0]  i_tlul_d_user
);

  int unsigned fails_CHK_014 = 0;
  int unsigned hits_CHK_014 = 0;
  int unsigned fails_CHK_015 = 0;
  int unsigned hits_CHK_015 = 0;
  int unsigned fails_CHK_016 = 0;
  int unsigned hits_CHK_016 = 0;
  int unsigned fails_CHK_017 = 0;
  int unsigned hits_CHK_017 = 0;

  // helper registers: previous-cycle samples of the APB request and A valid
  logic       h_prev_rst;
  logic       h_prev_valid;
  logic       h_prev_psel;
  logic       h_prev_penable;
  logic       h_prev_pwrite;
  logic [1:0] h_prev_addr_lo;
  logic [3:0] h_prev_pstrb;

  always_ff @(posedge i_clk_core) begin
    h_prev_rst     <= i_rst_n_core;
    h_prev_valid   <= o_tlul_a_valid;
    h_prev_psel    <= i_apb_psel;
    h_prev_penable <= i_apb_penable;
    h_prev_pwrite  <= i_apb_pwrite;
    h_prev_addr_lo <= i_apb_paddr[1:0];
    h_prev_pstrb   <= i_apb_pstrb;
  end

  // CHK-014: A request starts only after a legal Setup (BR-5.4-05, BR-15.3-07, BR-20-05, BR-1.1-01)
  a_CHK_014: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (h_prev_rst && !h_prev_valid && o_tlul_a_valid) |->
      (h_prev_psel && !h_prev_penable && (h_prev_addr_lo == 2'b00) &&
       (!h_prev_pwrite || (h_prev_pstrb == 4'b1111))))
    else begin fails_CHK_014++; $display("NNC_FAIL CHK-014 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (h_prev_rst && !h_prev_valid && o_tlul_a_valid)) hits_CHK_014 <= hits_CHK_014 + 1;

  // CHK-015: Channel A held and stable until accepted (BR-3-08, BR-5.4-03, BR-6.3-07, BR-15.3-02, BR-10.1-04, BR-6.2-06, BR-6.2-07, BR-6.2-11, BR-6.2-13)
  a_CHK_015: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_tlul_a_valid && !i_tlul_a_ready) |=>
      (o_tlul_a_valid && $stable(o_tlul_a_opcode) && $stable(o_tlul_a_address) &&
       $stable(o_tlul_a_data) && $stable(o_tlul_a_param) && $stable(o_tlul_a_size) &&
       $stable(o_tlul_a_mask) && $stable(o_tlul_a_source) && $stable(o_tlul_a_user)))
    else begin fails_CHK_015++; $display("NNC_FAIL CHK-015 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_tlul_a_valid && !i_tlul_a_ready)) hits_CHK_015 <= hits_CHK_015 + 1;

  // CHK-016: a_valid drops after the handshake (accepted once) (BR-6.2-06, BR-10.1-04)
  a_CHK_016: assert property (@(posedge i_clk_core) disable iff (!i_rst_n_core)
    (o_tlul_a_valid && i_tlul_a_ready) |=> !o_tlul_a_valid)
    else begin fails_CHK_016++; $display("NNC_FAIL CHK-016 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (!(!i_rst_n_core) && (o_tlul_a_valid && i_tlul_a_ready)) hits_CHK_016 <= hits_CHK_016 + 1;

  // CHK-017: Constant A-channel fields and legal opcode, size, mask and address (BR-2.3-04, BR-2.3-05, BR-3-20, BR-6.2-07, BR-6.2-08, BR-6.2-09, BR-6.2-10, BR-6.2-11, BR-6.2-12, BR-6.2-14, BR-8-04, BR-8-05, BR-8-08, BR-9-05, BR-9-07, BR-9-08, BR-15.3-04, BR-15.3-05, BR-20-06, BR-20-09, BR-1.1-04, TL-T3.1-01, TL-T3.3-03, TL-T4.1.3.3-02, TL-T4.1.3.4-02, TL-T4.1.3.4-04, TL-T4.1.3.5-07)
  a_CHK_017: assert property (@(posedge i_clk_core)
    1'b1 |->
      (o_tlul_a_param == 3'b000 && o_tlul_a_size == 2'b10 && o_tlul_a_mask == 4'b1111 &&
       o_tlul_a_source == PARA_SRC_W'(PARA_SRC_ID) && o_tlul_a_user == '0 &&
       o_tlul_a_opcode[1:0] == 2'b00 && o_tlul_a_address[1:0] == 2'b00))
    else begin fails_CHK_017++; $display("NNC_FAIL CHK-017 @%0t", $time); end
  always_ff @(posedge i_clk_core) if (1'b1) hits_CHK_017 <= hits_CHK_017 + 1;

  final begin
    $display("NNC_CHECK CHK-014 hits=%0d fails=%0d", hits_CHK_014, fails_CHK_014);
    $display("NNC_CHECK CHK-015 hits=%0d fails=%0d", hits_CHK_015, fails_CHK_015);
    $display("NNC_CHECK CHK-016 hits=%0d fails=%0d", hits_CHK_016, fails_CHK_016);
    $display("NNC_CHECK CHK-017 hits=%0d fails=%0d", hits_CHK_017, fails_CHK_017);
  end
endmodule
