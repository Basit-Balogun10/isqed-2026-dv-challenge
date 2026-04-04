module icarus_assert_wrapper (
  input  logic        clk_i,
  input  logic        rst_ni,
  input  logic        tl_a_valid_i,
  output logic        tl_a_ready_o,
  input  logic [2:0]  tl_a_opcode_i,
  input  logic [31:0] tl_a_address_i,
  input  logic [31:0] tl_a_data_i,
  input  logic [3:0]  tl_a_mask_i,
  input  logic [7:0]  tl_a_source_i,
  input  logic [1:0]  tl_a_size_i,
  output logic        tl_d_valid_o,
  input  logic        tl_d_ready_i,
  output logic [2:0]  tl_d_opcode_o,
  output logic [31:0] tl_d_data_o,
  output logic [7:0]  tl_d_source_o,
  output logic        tl_d_error_o,
  input  logic        scl_i,
  output logic        scl_o,
  output logic        scl_oe_o,
  input  logic        sda_i,
  output logic        sda_o,
  output logic        sda_oe_o,
  output logic [15:0] intr_o,
  output logic        alert_o
);

  logic        dut_tl_a_ready_o;
  logic        dut_tl_d_valid_o;
  logic [2:0]  dut_tl_d_opcode_o;
  logic [31:0] dut_tl_d_data_o;
  logic [7:0]  dut_tl_d_source_o;
  logic        dut_tl_d_error_o;
  logic        dut_scl_o;
  logic        dut_scl_oe_o;
  logic        dut_sda_o;
  logic        dut_sda_oe_o;
  logic [15:0] dut_intr_o;
  logic        dut_alert_o;

  assign tl_a_ready_o = dut_tl_a_ready_o;
  assign tl_d_valid_o = dut_tl_d_valid_o;
  assign tl_d_opcode_o = dut_tl_d_opcode_o;
  assign tl_d_data_o = dut_tl_d_data_o;
  assign tl_d_source_o = dut_tl_d_source_o;
  assign tl_d_error_o = dut_tl_d_error_o;
  assign scl_o = dut_scl_o;
  assign scl_oe_o = dut_scl_oe_o;
  assign sda_o = dut_sda_o;
  assign sda_oe_o = dut_sda_oe_o;
  assign intr_o = dut_intr_o;
  assign alert_o = dut_alert_o;

  rampart_i2c u_dut (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .tl_a_valid_i(tl_a_valid_i),
    .tl_a_ready_o(dut_tl_a_ready_o),
    .tl_a_opcode_i(tl_a_opcode_i),
    .tl_a_address_i(tl_a_address_i),
    .tl_a_data_i(tl_a_data_i),
    .tl_a_mask_i(tl_a_mask_i),
    .tl_a_source_i(tl_a_source_i),
    .tl_a_size_i(tl_a_size_i),
    .tl_d_valid_o(dut_tl_d_valid_o),
    .tl_d_ready_i(tl_d_ready_i),
    .tl_d_opcode_o(dut_tl_d_opcode_o),
    .tl_d_data_o(dut_tl_d_data_o),
    .tl_d_source_o(dut_tl_d_source_o),
    .tl_d_error_o(dut_tl_d_error_o),
    .scl_i(scl_i),
    .scl_o(dut_scl_o),
    .scl_oe_o(dut_scl_oe_o),
    .sda_i(sda_i),
    .sda_o(dut_sda_o),
    .sda_oe_o(dut_sda_oe_o),
    .intr_o(dut_intr_o),
    .alert_o(dut_alert_o)
  );

  rampart_i2c_protocol_assertions u_rampart_protocol_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .tl_a_valid_i(tl_a_valid_i),
    .tl_a_ready_o(tl_a_ready_o),
    .tl_a_opcode_i(tl_a_opcode_i),
    .tl_a_address_i(tl_a_address_i),
    .tl_a_data_i(tl_a_data_i),
    .tl_a_mask_i(tl_a_mask_i),
    .tl_a_source_i(tl_a_source_i),
    .tl_a_size_i(tl_a_size_i),
    .tl_d_valid_o(tl_d_valid_o),
    .tl_d_ready_i(tl_d_ready_i),
    .tl_d_opcode_o(tl_d_opcode_o),
    .tl_d_data_o(tl_d_data_o),
    .tl_d_source_o(tl_d_source_o),
    .tl_d_error_o(tl_d_error_o),
    .scl_o(scl_o),
    .sda_o(sda_o)
  );

  rampart_i2c_functional_assertions u_rampart_functional_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .ctrl_host_enable(u_dut.ctrl_host_enable),
    .ctrl_target_enable(u_dut.ctrl_target_enable),
    .ctrl_line_loopback(u_dut.ctrl_line_loopback),
    .host_timeout_event(u_dut.host_timeout_event),
    .host_arb_lost(u_dut.host_arb_lost),
    .host_state(u_dut.host_state),
    .tgt_state(u_dut.tgt_state),
    .intr_state(u_dut.intr_state),
    .intr_enable(u_dut.intr_enable),
    .intr_o(intr_o),
    .scl_oe_o(scl_oe_o),
    .sda_oe_o(sda_oe_o),
    .scl_in(u_dut.scl_in),
    .sda_in(u_dut.sda_in)
  );

  rampart_i2c_structural_assertions u_rampart_structural_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .host_state(u_dut.host_state),
    .tgt_state(u_dut.tgt_state),
    .fmt_fifo_empty(u_dut.fmt_fifo_empty),
    .fmt_fifo_full(u_dut.fmt_fifo_full),
    .fmt_fifo_level(u_dut.fmt_fifo_level),
    .rx_fifo_empty(u_dut.rx_fifo_empty),
    .rx_fifo_full(u_dut.rx_fifo_full),
    .rx_fifo_level(u_dut.rx_fifo_level),
    .tx_fifo_empty(u_dut.tx_fifo_empty),
    .tx_fifo_full(u_dut.tx_fifo_full),
    .tx_fifo_level(u_dut.tx_fifo_level),
    .acq_fifo_empty(u_dut.acq_fifo_empty),
    .acq_fifo_full(u_dut.acq_fifo_full),
    .acq_fifo_level(u_dut.acq_fifo_level),
    .tl_d_valid_o(tl_d_valid_o),
    .tl_d_opcode_o(tl_d_opcode_o),
    .alert_o(alert_o)
  );

  rampart_i2c_liveness_assertions u_rampart_liveness_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .ctrl_host_enable(u_dut.ctrl_host_enable),
    .ctrl_target_enable(u_dut.ctrl_target_enable),
    .fmt_fifo_empty(u_dut.fmt_fifo_empty),
    .host_state(u_dut.host_state),
    .tgt_state(u_dut.tgt_state),
    .start_det(u_dut.start_det),
    .stop_det(u_dut.stop_det),
    .trans_complete_det(u_dut.trans_complete_det),
    .tl_a_valid_i(tl_a_valid_i),
    .tl_a_ready_o(tl_a_ready_o),
    .tl_d_valid_o(tl_d_valid_o)
  );

endmodule
