`ifndef __ICARUS__

bind rampart_i2c rampart_i2c_protocol_assertions u_rampart_protocol_assertions (
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

bind rampart_i2c rampart_i2c_functional_assertions u_rampart_functional_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .ctrl_host_enable(ctrl_host_enable),
  .ctrl_target_enable(ctrl_target_enable),
  .ctrl_line_loopback(ctrl_line_loopback),
  .host_timeout_event(host_timeout_event),
  .host_arb_lost(host_arb_lost),
  .host_state(host_state),
  .tgt_state(tgt_state),
  .intr_state(intr_state),
  .intr_enable(intr_enable),
  .intr_o(intr_o),
  .scl_oe_o(scl_oe_o),
  .sda_oe_o(sda_oe_o),
  .scl_in(scl_in),
  .sda_in(sda_in)
);

bind rampart_i2c rampart_i2c_structural_assertions u_rampart_structural_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .host_state(host_state),
  .tgt_state(tgt_state),
  .fmt_fifo_empty(fmt_fifo_empty),
  .fmt_fifo_full(fmt_fifo_full),
  .fmt_fifo_level(fmt_fifo_level),
  .rx_fifo_empty(rx_fifo_empty),
  .rx_fifo_full(rx_fifo_full),
  .rx_fifo_level(rx_fifo_level),
  .tx_fifo_empty(tx_fifo_empty),
  .tx_fifo_full(tx_fifo_full),
  .tx_fifo_level(tx_fifo_level),
  .acq_fifo_empty(acq_fifo_empty),
  .acq_fifo_full(acq_fifo_full),
  .acq_fifo_level(acq_fifo_level),
  .tl_d_valid_o(tl_d_valid_o),
  .tl_d_opcode_o(tl_d_opcode_o),
  .alert_o(alert_o)
);

bind rampart_i2c rampart_i2c_liveness_assertions u_rampart_liveness_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .ctrl_host_enable(ctrl_host_enable),
  .ctrl_target_enable(ctrl_target_enable),
  .fmt_fifo_empty(fmt_fifo_empty),
  .host_state(host_state),
  .tgt_state(tgt_state),
  .start_det(start_det),
  .stop_det(stop_det),
  .trans_complete_det(trans_complete_det),
  .tl_a_valid_i(tl_a_valid_i),
  .tl_a_ready_o(tl_a_ready_o),
  .tl_d_valid_o(tl_d_valid_o)
);

`endif
