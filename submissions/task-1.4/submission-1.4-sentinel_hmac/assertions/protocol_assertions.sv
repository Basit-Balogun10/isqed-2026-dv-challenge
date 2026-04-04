module sentinel_hmac_protocol_assertions (
  input logic        clk_i,
  input logic        rst_ni,
  input logic        tl_a_valid_i,
  input logic        tl_a_ready_o,
  input logic [2:0]  tl_a_opcode_i,
  input logic [31:0] tl_a_address_i,
  input logic [31:0] tl_a_data_i,
  input logic [3:0]  tl_a_mask_i,
  input logic [7:0]  tl_a_source_i,
  input logic [1:0]  tl_a_size_i,
  input logic        tl_d_valid_o,
  input logic        tl_d_ready_i,
  input logic [2:0]  tl_d_opcode_o,
  input logic [31:0] tl_d_data_o,
  input logic [7:0]  tl_d_source_o,
  input logic        tl_d_error_o,
  input logic        tl_req_valid,
  input logic        tl_is_write,
  input logic        tl_is_read
);

  logic       a_wait_prev;
  logic [2:0] a_opcode_prev;
  logic [31:0] a_address_prev;
  logic [31:0] a_data_prev;
  logic [3:0]  a_mask_prev;
  logic [7:0]  a_source_prev;
  logic [1:0]  a_size_prev;

  logic       d_wait_prev;
  logic [2:0] d_opcode_prev;
  logic [31:0] d_data_prev;
  logic [7:0]  d_source_prev;
  logic        d_error_prev;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      a_wait_prev <= 1'b0;
      d_wait_prev <= 1'b0;
    end else begin
      if (a_wait_prev) begin
        assert (tl_a_valid_i)
          else $error("TL-A valid dropped before handshake");
        assert (tl_a_opcode_i == a_opcode_prev)
          else $error("TL-A opcode changed while waiting for ready");
        assert (tl_a_address_i == a_address_prev)
          else $error("TL-A address changed while waiting for ready");
        assert (tl_a_data_i == a_data_prev)
          else $error("TL-A data changed while waiting for ready");
        assert (tl_a_mask_i == a_mask_prev)
          else $error("TL-A mask changed while waiting for ready");
        assert (tl_a_source_i == a_source_prev)
          else $error("TL-A source changed while waiting for ready");
        assert (tl_a_size_i == a_size_prev)
          else $error("TL-A size changed while waiting for ready");
      end

      if (d_wait_prev) begin
        assert (tl_d_valid_o)
          else $error("TL-D valid dropped before handshake");
        assert (tl_d_opcode_o == d_opcode_prev)
          else $error("TL-D opcode changed while waiting for ready");
        assert (tl_d_data_o == d_data_prev)
          else $error("TL-D data changed while waiting for ready");
        assert (tl_d_source_o == d_source_prev)
          else $error("TL-D source changed while waiting for ready");
        assert (tl_d_error_o == d_error_prev)
          else $error("TL-D error changed while waiting for ready");
      end

      if (tl_a_valid_i && tl_a_ready_o) begin
        assert ((tl_a_opcode_i == 3'd0) || (tl_a_opcode_i == 3'd4))
          else $error("Unsupported request opcode accepted");
      end

      if (tl_req_valid) begin
        assert (tl_is_write || tl_is_read)
          else $error("Accepted request did not decode as read or write");
      end

      if (tl_req_valid && tl_is_write) begin
        assert (tl_d_valid_o && tl_d_opcode_o == 3'd0)
          else $error("Write request did not return AccessAck response in accepted cycle");
      end

      if (tl_req_valid && tl_is_read) begin
        assert (tl_d_valid_o && tl_d_opcode_o == 3'd1)
          else $error("Read request did not return AccessAckData response in accepted cycle");
      end

      a_wait_prev <= tl_a_valid_i && !tl_a_ready_o;
      a_opcode_prev <= tl_a_opcode_i;
      a_address_prev <= tl_a_address_i;
      a_data_prev <= tl_a_data_i;
      a_mask_prev <= tl_a_mask_i;
      a_source_prev <= tl_a_source_i;
      a_size_prev <= tl_a_size_i;

      d_wait_prev <= tl_d_valid_o && !tl_d_ready_i;
      d_opcode_prev <= tl_d_opcode_o;
      d_data_prev <= tl_d_data_o;
      d_source_prev <= tl_d_source_o;
      d_error_prev <= tl_d_error_o;

    end
  end

endmodule
