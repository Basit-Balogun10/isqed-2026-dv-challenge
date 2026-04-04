module rampart_i2c_functional_assertions (
  input logic        clk_i,
  input logic        rst_ni,
  input logic        ctrl_host_enable,
  input logic        ctrl_target_enable,
  input logic        ctrl_line_loopback,
  input logic        host_timeout_event,
  input logic        host_arb_lost,
  input logic [3:0]  host_state,
  input logic [3:0]  tgt_state,
  input logic [15:0] intr_state,
  input logic [15:0] intr_enable,
  input logic [15:0] intr_o,
  input logic        scl_oe_o,
  input logic        sda_oe_o,
  input logic        scl_in,
  input logic        sda_in
);

  localparam logic [3:0] HOST_IDLE = 4'd0;
  localparam logic [3:0] TGT_IDLE  = 4'd0;

  logic timeout_event_prev;
  logic arb_lost_prev;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      timeout_event_prev <= 1'b0;
      arb_lost_prev      <= 1'b0;
    end else begin
      assert (intr_o == (intr_state & intr_enable))
        else $error("intr_o must equal intr_state & intr_enable");

      if (!ctrl_host_enable) begin
        assert (host_state == HOST_IDLE)
          else $error("Host FSM did not return to IDLE after host disable");
      end

      if (!ctrl_target_enable) begin
        assert (tgt_state == TGT_IDLE)
          else $error("Target FSM did not return to IDLE after target disable");
      end

      if (ctrl_line_loopback) begin
        assert (scl_in == ~scl_oe_o && sda_in == ~sda_oe_o)
          else $error("Loopback mode must map inputs from output enables");
      end

      if (timeout_event_prev) begin
        assert (intr_state[14])
          else $error("Host timeout event did not set interrupt bit 14");
      end

      if (arb_lost_prev) begin
        assert (intr_state[15])
          else $error("Arbitration-lost event did not set interrupt bit 15");
      end

      timeout_event_prev <= host_timeout_event;
      arb_lost_prev      <= host_arb_lost;
    end
  end

endmodule
