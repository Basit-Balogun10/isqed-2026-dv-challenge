module sentinel_hmac_structural_assertions (
  input logic       clk_i,
  input logic       rst_ni,
  input logic [3:0] state_q,
  input logic       fifo_full,
  input logic       fifo_empty,
  input logic [5:0] fifo_count,
  input logic       tl_d_valid_o,
  input logic [2:0] tl_d_opcode_o,
  input logic       alert_o
);

  localparam logic [3:0] ST_DONE = 4'd12;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      // No checks during reset.
    end else begin
      assert (alert_o == 1'b0)
        else $error("alert_o must remain low in reference RTL");

      assert (state_q <= ST_DONE)
        else $error("State machine entered illegal encoded state");

      assert (fifo_count <= 6'd32)
        else $error("FIFO count exceeded depth");

      assert (!(fifo_full && fifo_empty))
        else $error("FIFO cannot be full and empty simultaneously");

      if (fifo_empty) begin
        assert (fifo_count == 6'd0)
          else $error("fifo_empty asserted with nonzero count");
      end

      if (fifo_full) begin
        assert (fifo_count == 6'd32)
          else $error("fifo_full asserted without full count");
      end

      if (tl_d_valid_o) begin
        assert ((tl_d_opcode_o == 3'd0) || (tl_d_opcode_o == 3'd1))
          else $error("TL-D opcode must be AccessAck/AccessAckData");
      end
    end
  end

endmodule
