// Contract shell: interface of the verification contract with no behaviour.
// Compile checks only; a run against it proves nothing about the DUT.
module uart #(
  parameter int DATA_WIDTH = 8
) (
  input  logic                        clk,
  input  logic                        rst,
  input  logic [7:0]                  s_axis_tdata,
  input  logic                        s_axis_tvalid,
  output logic                        s_axis_tready,
  output logic [7:0]                  m_axis_tdata,
  output logic                        m_axis_tvalid,
  input  logic                        m_axis_tready,
  input  logic                        rxd,
  output logic                        txd,
  output logic                        tx_busy,
  output logic                        rx_busy,
  output logic                        rx_overrun_error,
  output logic                        rx_frame_error,
  input  logic [15:0]                 prescale
);
  assign s_axis_tready = '0;
  assign m_axis_tdata = '0;
  assign m_axis_tvalid = '0;
  assign txd = '0;
  assign tx_busy = '0;
  assign rx_busy = '0;
  assign rx_overrun_error = '0;
  assign rx_frame_error = '0;
endmodule
