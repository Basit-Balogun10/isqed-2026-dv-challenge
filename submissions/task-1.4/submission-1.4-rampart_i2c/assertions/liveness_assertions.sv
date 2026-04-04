module rampart_i2c_liveness_assertions (
  input logic       clk_i,
  input logic       rst_ni,
  input logic       ctrl_host_enable,
  input logic       ctrl_target_enable,
  input logic       fmt_fifo_empty,
  input logic [3:0] host_state,
  input logic [3:0] tgt_state,
  input logic       start_det,
  input logic       stop_det,
  input logic       trans_complete_det,
  input logic       tl_a_valid_i,
  input logic       tl_a_ready_o,
  input logic       tl_d_valid_o
);

  localparam logic [3:0] HOST_IDLE = 4'd0;
  localparam logic [3:0] TGT_IDLE  = 4'd0;

  logic [5:0] host_progress_ctr;
  logic [5:0] tgt_start_progress_ctr;
  logic [4:0] tgt_stop_to_idle_ctr;
  logic [2:0] trans_complete_idle_ctr;
  logic [2:0] tl_req_rsp_ctr;
  logic       tl_req_pending;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      host_progress_ctr      <= 6'd0;
      tgt_start_progress_ctr <= 6'd0;
      tgt_stop_to_idle_ctr   <= 5'd0;
      trans_complete_idle_ctr <= 3'd0;
      tl_req_rsp_ctr         <= 3'd0;
      tl_req_pending         <= 1'b0;
    end else begin
      if (ctrl_host_enable && !fmt_fifo_empty && host_state == HOST_IDLE) begin
        if (host_progress_ctr == 6'd0) begin
          host_progress_ctr <= 6'd32;
        end else begin
          assert (host_progress_ctr != 6'd1)
            else $error("Host FSM did not leave IDLE after queued command");
          host_progress_ctr <= host_progress_ctr - 6'd1;
        end
      end else begin
        host_progress_ctr <= 6'd0;
      end

      if (trans_complete_det) begin
        trans_complete_idle_ctr <= 3'd2;
      end else if (trans_complete_idle_ctr != 3'd0) begin
        if (host_state == HOST_IDLE) begin
          trans_complete_idle_ctr <= 3'd0;
        end else begin
          assert (trans_complete_idle_ctr != 3'd1)
            else $error("Host FSM did not return to IDLE after transaction complete");
          trans_complete_idle_ctr <= trans_complete_idle_ctr - 3'd1;
        end
      end

      if (ctrl_target_enable && start_det) begin
        tgt_start_progress_ctr <= 6'd32;
      end else if (tgt_start_progress_ctr != 6'd0) begin
        if (tgt_state != TGT_IDLE) begin
          tgt_start_progress_ctr <= 6'd0;
        end else begin
          assert (tgt_start_progress_ctr != 6'd1)
            else $error("Target FSM did not react to START condition");
          tgt_start_progress_ctr <= tgt_start_progress_ctr - 6'd1;
        end
      end

      if (stop_det && tgt_state != TGT_IDLE) begin
        tgt_stop_to_idle_ctr <= 5'd16;
      end else if (tgt_stop_to_idle_ctr != 5'd0) begin
        if (tgt_state == TGT_IDLE) begin
          tgt_stop_to_idle_ctr <= 5'd0;
        end else begin
          assert (tgt_stop_to_idle_ctr != 5'd1)
            else $error("Target FSM did not return to IDLE after STOP");
          tgt_stop_to_idle_ctr <= tgt_stop_to_idle_ctr - 5'd1;
        end
      end

      if (tl_a_valid_i && tl_a_ready_o) begin
        tl_req_pending <= 1'b1;
        tl_req_rsp_ctr <= 3'd4;
      end else if (tl_req_pending) begin
        if (tl_d_valid_o) begin
          tl_req_pending <= 1'b0;
        end else begin
          assert (tl_req_rsp_ctr != 3'd0)
            else $error("TL request was not followed by a bounded response");
          tl_req_rsp_ctr <= tl_req_rsp_ctr - 3'd1;
        end
      end
    end
  end

endmodule
