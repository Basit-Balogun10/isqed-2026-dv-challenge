module sentinel_hmac_liveness_assertions (
  input logic       clk_i,
  input logic       rst_ni,
  input logic       cfg_sha_en,
  input logic       cmd_hash_start,
  input logic       cmd_hash_stop,
  input logic [3:0] state_q,
  input logic       intr_fifo_empty_pulse,
  input logic [2:0] intr_state,
  input logic       tl_req_valid,
  input logic       tl_d_valid_o
);

  localparam logic [3:0] ST_IDLE      = 4'd0;
  localparam logic [3:0] ST_SHA_ROUND = 4'd3;
  localparam logic [3:0] ST_DONE      = 4'd12;

  logic start_progress_prev;
  logic [6:0] round_timeout_ctr;
  logic [9:0] stop_to_done_ctr;
  logic fifo_empty_pulse_prev;
  logic restart_prev;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      start_progress_prev <= 1'b0;
      round_timeout_ctr   <= 7'd0;
      stop_to_done_ctr    <= 10'd0;
      fifo_empty_pulse_prev <= 1'b0;
      restart_prev        <= 1'b0;
    end else begin
      if (start_progress_prev) begin
        assert (state_q != ST_IDLE)
          else $error("hash_start did not move engine out of IDLE");
      end

      if (state_q == ST_SHA_ROUND) begin
        if (round_timeout_ctr == 7'd0) begin
          round_timeout_ctr <= 7'd80;
        end else begin
          assert (round_timeout_ctr != 7'd1)
            else $error("SHA round state exceeded expected bounded duration");
          round_timeout_ctr <= round_timeout_ctr - 7'd1;
        end
      end else begin
        round_timeout_ctr <= 7'd0;
      end

      if (cmd_hash_stop && state_q != ST_IDLE) begin
        stop_to_done_ctr <= 10'd700;
      end else if (stop_to_done_ctr != 10'd0) begin
        if (state_q == ST_DONE) begin
          stop_to_done_ctr <= 10'd0;
        end else begin
          assert (stop_to_done_ctr != 10'd1)
            else $error("hash_stop did not lead to DONE within bounded time");
          stop_to_done_ctr <= stop_to_done_ctr - 10'd1;
        end
      end

      if (fifo_empty_pulse_prev) begin
        assert (intr_state[1])
          else $error("fifo_empty pulse did not set interrupt state bit 1");
      end

      if (tl_req_valid) begin
        assert (tl_d_valid_o)
          else $error("Accepted TL request did not produce immediate response");
      end

      if (restart_prev) begin
        assert (state_q != ST_DONE)
          else $error("Engine did not restart from DONE on hash_start");
      end

      start_progress_prev   <= (cmd_hash_start && cfg_sha_en);
      fifo_empty_pulse_prev <= intr_fifo_empty_pulse;
      restart_prev          <= (state_q == ST_DONE && cmd_hash_start && cfg_sha_en);
    end
  end

endmodule
