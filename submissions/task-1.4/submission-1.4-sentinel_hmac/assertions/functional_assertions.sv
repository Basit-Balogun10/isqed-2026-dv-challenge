module sentinel_hmac_functional_assertions (
  input logic        clk_i,
  input logic        rst_ni,
  input logic        cfg_hmac_en,
  input logic        cfg_sha_en,
  input logic        cmd_hash_start,
  input logic        cmd_hash_stop,
  input logic        wipe_secret,
  input logic [3:0]  state_q,
  input logic [3:0]  state_d,
  input logic [2:0]  intr_state,
  input logic [2:0]  intr_enable,
  input logic [2:0]  intr_o,
  input logic [31:0] msg_len_lo,
  input logic [31:0] msg_len_hi,
  input logic        tl_is_write,
  input logic [7:0]  tl_addr,
  input logic [31:0] tl_wdata
);

  localparam logic [3:0] ST_IDLE = 4'd0;
  localparam logic [3:0] ST_DONE = 4'd12;

  logic hash_start_prev;
  logic intr_enable_write_prev;
  logic [2:0] intr_enable_wdata_prev;
  logic done_transition_prev;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      hash_start_prev        <= 1'b0;
      intr_enable_write_prev <= 1'b0;
      intr_enable_wdata_prev <= 3'd0;
      done_transition_prev   <= 1'b0;
    end else begin
      assert (intr_o == (intr_state & intr_enable))
        else $error("intr_o must equal intr_state & intr_enable");

      if (hash_start_prev) begin
        assert (state_q != ST_IDLE)
          else $error("hash_start with sha_en did not leave IDLE state");
        assert (msg_len_lo == 32'd0 && msg_len_hi == 32'd0)
          else $error("hash_start did not reset message-length counters");
      end

      if (intr_enable_write_prev) begin
        assert (intr_enable == intr_enable_wdata_prev)
          else $error("INTR_ENABLE write did not update intr_enable register");
      end

      if (done_transition_prev) begin
        assert (intr_state[0])
          else $error("Transition into DONE did not set hmac_done interrupt");
      end

      hash_start_prev        <= (cmd_hash_start && cfg_sha_en && state_q == ST_IDLE);
      intr_enable_write_prev <= (tl_is_write && tl_addr == 8'h5C);
      intr_enable_wdata_prev <= tl_wdata[2:0];
      done_transition_prev   <= (state_q != ST_DONE && state_d == ST_DONE);
    end
  end

endmodule
