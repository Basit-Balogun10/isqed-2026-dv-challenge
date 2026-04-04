module rampart_i2c_structural_assertions (
  input logic        clk_i,
  input logic        rst_ni,
  input logic [3:0]  host_state,
  input logic [3:0]  tgt_state,
  input logic        fmt_fifo_empty,
  input logic        fmt_fifo_full,
  input logic [6:0]  fmt_fifo_level,
  input logic        rx_fifo_empty,
  input logic        rx_fifo_full,
  input logic [6:0]  rx_fifo_level,
  input logic        tx_fifo_empty,
  input logic        tx_fifo_full,
  input logic [6:0]  tx_fifo_level,
  input logic        acq_fifo_empty,
  input logic        acq_fifo_full,
  input logic [6:0]  acq_fifo_level,
  input logic        tl_d_valid_o,
  input logic [2:0]  tl_d_opcode_o,
  input logic        alert_o
);

  localparam logic [3:0] HOST_WAIT_BUS_FREE = 4'd10;
  localparam logic [3:0] TGT_STOP_DET       = 4'd9;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      // No checks during reset.
    end else begin
      assert (alert_o == 1'b0)
        else $error("alert_o must remain low in the reference RTL");

      assert (host_state <= HOST_WAIT_BUS_FREE)
        else $error("Host FSM entered illegal encoded state");

      assert (tgt_state <= TGT_STOP_DET)
        else $error("Target FSM entered illegal encoded state");

      assert (!(fmt_fifo_empty && fmt_fifo_full))
        else $error("FMT FIFO cannot be empty and full simultaneously");
      assert (!(rx_fifo_empty && rx_fifo_full))
        else $error("RX FIFO cannot be empty and full simultaneously");
      assert (!(tx_fifo_empty && tx_fifo_full))
        else $error("TX FIFO cannot be empty and full simultaneously");
      assert (!(acq_fifo_empty && acq_fifo_full))
        else $error("ACQ FIFO cannot be empty and full simultaneously");

      assert (fmt_fifo_level <= 7'd64)
        else $error("FMT FIFO level exceeded configured depth");
      assert (rx_fifo_level <= 7'd64)
        else $error("RX FIFO level exceeded configured depth");
      assert (tx_fifo_level <= 7'd64)
        else $error("TX FIFO level exceeded configured depth");
      assert (acq_fifo_level <= 7'd64)
        else $error("ACQ FIFO level exceeded configured depth");

      if (fmt_fifo_empty) begin
        assert (fmt_fifo_level == 7'd0)
          else $error("FMT FIFO empty flag does not match level counter");
      end
      if (rx_fifo_empty) begin
        assert (rx_fifo_level == 7'd0)
          else $error("RX FIFO empty flag does not match level counter");
      end
      if (tx_fifo_empty) begin
        assert (tx_fifo_level == 7'd0)
          else $error("TX FIFO empty flag does not match level counter");
      end
      if (acq_fifo_empty) begin
        assert (acq_fifo_level == 7'd0)
          else $error("ACQ FIFO empty flag does not match level counter");
      end

      if (tl_d_valid_o) begin
        assert ((tl_d_opcode_o == 3'd0) || (tl_d_opcode_o == 3'd1))
          else $error("TL-D opcode must be AccessAck/AccessAckData");
      end
    end
  end

endmodule
