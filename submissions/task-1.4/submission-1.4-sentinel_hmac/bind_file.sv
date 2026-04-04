`ifndef __ICARUS__

bind sentinel_hmac sentinel_hmac_protocol_assertions u_sentinel_protocol_assertions (
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
  .tl_req_valid(tl_req_valid),
  .tl_is_write(tl_is_write),
  .tl_is_read(tl_is_read)
);

bind sentinel_hmac sentinel_hmac_functional_assertions u_sentinel_functional_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .cfg_hmac_en(cfg_hmac_en),
  .cfg_sha_en(cfg_sha_en),
  .cmd_hash_start(cmd_hash_start),
  .cmd_hash_stop(cmd_hash_stop),
  .wipe_secret(wipe_secret),
  .state_q(state_q),
  .state_d(state_d),
  .intr_state(intr_state),
  .intr_enable(intr_enable),
  .intr_o(intr_o),
  .msg_len_lo(msg_len_lo),
  .msg_len_hi(msg_len_hi),
  .tl_is_write(tl_is_write),
  .tl_addr(tl_addr[7:0]),
  .tl_wdata(tl_wdata)
);

bind sentinel_hmac sentinel_hmac_structural_assertions u_sentinel_structural_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .state_q(state_q),
  .fifo_full(fifo_full),
  .fifo_empty(fifo_empty),
  .fifo_count(fifo_count),
  .tl_d_valid_o(tl_d_valid_o),
  .tl_d_opcode_o(tl_d_opcode_o),
  .alert_o(alert_o)
);

bind sentinel_hmac sentinel_hmac_liveness_assertions u_sentinel_liveness_assertions (
  .clk_i(clk_i),
  .rst_ni(rst_ni),
  .cfg_sha_en(cfg_sha_en),
  .cmd_hash_start(cmd_hash_start),
  .cmd_hash_stop(cmd_hash_stop),
  .state_q(state_q),
  .intr_fifo_empty_pulse(intr_fifo_empty_pulse),
  .intr_state(intr_state),
  .tl_req_valid(tl_req_valid),
  .tl_d_valid_o(tl_d_valid_o)
);

`endif
