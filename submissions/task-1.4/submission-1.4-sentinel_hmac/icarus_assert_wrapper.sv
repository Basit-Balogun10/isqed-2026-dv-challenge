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
  output logic [2:0]  intr_o,
  output logic        alert_o
);

  logic        dut_tl_a_ready_o;
  logic        dut_tl_d_valid_o;
  logic [2:0]  dut_tl_d_opcode_o;
  logic [31:0] dut_tl_d_data_o;
  logic [7:0]  dut_tl_d_source_o;
  logic        dut_tl_d_error_o;
  logic [2:0]  dut_intr_o;
  logic        dut_alert_o;

  assign tl_a_ready_o = dut_tl_a_ready_o;
  assign tl_d_valid_o = dut_tl_d_valid_o;
  assign tl_d_opcode_o = dut_tl_d_opcode_o;
  assign tl_d_data_o = dut_tl_d_data_o;
  assign tl_d_source_o = dut_tl_d_source_o;
  assign tl_d_error_o = dut_tl_d_error_o;
  assign intr_o = dut_intr_o;
  assign alert_o = dut_alert_o;

  sentinel_hmac u_dut (
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
    .intr_o(dut_intr_o),
    .alert_o(dut_alert_o)
  );

  sentinel_hmac_protocol_assertions u_sentinel_protocol_assertions (
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
    .tl_req_valid(u_dut.tl_req_valid),
    .tl_is_write(u_dut.tl_is_write),
    .tl_is_read(u_dut.tl_is_read)
  );

  sentinel_hmac_functional_assertions u_sentinel_functional_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .cfg_hmac_en(u_dut.cfg_hmac_en),
    .cfg_sha_en(u_dut.cfg_sha_en),
    .cmd_hash_start(u_dut.cmd_hash_start),
    .cmd_hash_stop(u_dut.cmd_hash_stop),
    .wipe_secret(u_dut.wipe_secret),
    .state_q(u_dut.state_q),
    .state_d(u_dut.state_d),
    .intr_state(u_dut.intr_state),
    .intr_enable(u_dut.intr_enable),
    .intr_o(intr_o),
    .msg_len_lo(u_dut.msg_len_lo),
    .msg_len_hi(u_dut.msg_len_hi),
    .tl_is_write(u_dut.tl_is_write),
    .tl_addr(u_dut.tl_addr[7:0]),
    .tl_wdata(u_dut.tl_wdata)
  );

  sentinel_hmac_structural_assertions u_sentinel_structural_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .state_q(u_dut.state_q),
    .fifo_full(u_dut.fifo_full),
    .fifo_empty(u_dut.fifo_empty),
    .fifo_count(u_dut.fifo_count),
    .tl_d_valid_o(tl_d_valid_o),
    .tl_d_opcode_o(tl_d_opcode_o),
    .alert_o(alert_o)
  );

  sentinel_hmac_liveness_assertions u_sentinel_liveness_assertions (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .cfg_sha_en(u_dut.cfg_sha_en),
    .cmd_hash_start(u_dut.cmd_hash_start),
    .cmd_hash_stop(u_dut.cmd_hash_stop),
    .state_q(u_dut.state_q),
    .intr_fifo_empty_pulse(u_dut.intr_fifo_empty_pulse),
    .intr_state(u_dut.intr_state),
    .tl_req_valid(u_dut.tl_req_valid),
    .tl_d_valid_o(tl_d_valid_o)
  );

endmodule
