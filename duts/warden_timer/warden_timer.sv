import dv_common_pkg::*;

module warden_timer (
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

  localparam logic [31:0] ADDR_MTIME_LOW            = 32'h00;
  localparam logic [31:0] ADDR_MTIME_HIGH           = 32'h04;
  localparam logic [31:0] ADDR_MTIMECMP0_LOW        = 32'h08;
  localparam logic [31:0] ADDR_MTIMECMP0_HIGH       = 32'h0C;
  localparam logic [31:0] ADDR_MTIMECMP1_LOW        = 32'h10;
  localparam logic [31:0] ADDR_MTIMECMP1_HIGH       = 32'h14;
  localparam logic [31:0] ADDR_PRESCALER            = 32'h18;
  localparam logic [31:0] ADDR_WATCHDOG_CTRL        = 32'h1C;
  localparam logic [31:0] ADDR_WATCHDOG_BARK_THRESH = 32'h20;
  localparam logic [31:0] ADDR_WATCHDOG_BITE_THRESH = 32'h24;
  localparam logic [31:0] ADDR_WATCHDOG_PET         = 32'h28;
  localparam logic [31:0] ADDR_WATCHDOG_COUNT       = 32'h2C;
  localparam logic [31:0] ADDR_INTR_STATE           = 32'h30;
  localparam logic [31:0] ADDR_INTR_ENABLE          = 32'h34;
  localparam logic [31:0] ADDR_INTR_TEST            = 32'h38;

  localparam logic [31:0] ADDR_MAX                  = 32'h38;

  logic [63:0] mtime_q;
  logic [63:0] mtime_d;
  logic [63:0] mtimecmp0_q;
  logic [63:0] mtimecmp0_d;
  logic [63:0] mtimecmp1_q;
  logic [63:0] mtimecmp1_d;
  logic [11:0] prescaler_q;
  logic [11:0] prescaler_d;
  logic [11:0] prescale_cnt_q;
  logic [11:0] prescale_cnt_d;

  logic        wd_enable_q;
  logic        wd_enable_d;
  logic        wd_lock_q;
  logic        wd_lock_d;
  logic [31:0] wd_bark_thresh_q;
  logic [31:0] wd_bark_thresh_d;
  logic [31:0] wd_bite_thresh_q;
  logic [31:0] wd_bite_thresh_d;
  logic [31:0] wd_count_q;
  logic [31:0] wd_count_d;

  logic [2:0]  intr_state_q;
  logic [2:0]  intr_state_d;
  logic [2:0]  intr_enable_q;
  logic [2:0]  intr_enable_d;
  logic [2:0]  intr_test_q;
  logic [2:0]  intr_test_d;

  logic        timer0_expired;
  logic        timer1_expired;
  logic        wd_bark;
  logic        wd_bite;

  logic        tl_txn_valid;
  logic        tl_is_write;
  logic        tl_is_read;
  logic [31:0] tl_addr;
  logic [31:0] tl_wdata;
  logic [3:0]  tl_wmask;
  logic [7:0]  tl_source;
  logic [1:0]  tl_size;

  logic        rsp_valid_q;
  logic        rsp_valid_d;
  logic [31:0] rsp_data_q;
  logic [31:0] rsp_data_d;
  logic [7:0]  rsp_source_q;
  logic [7:0]  rsp_source_d;
  logic        rsp_error_q;
  logic        rsp_error_d;
  logic [2:0]  rsp_opcode_q;
  logic [2:0]  rsp_opcode_d;

  logic        pet_write;
  logic        prescale_tick;
  logic        addr_valid;
  logic [31:0] rd_data;

  logic [31:0] masked_wdata;

  assign masked_wdata[31:24] = tl_wmask[3] ? tl_wdata[31:24] : 8'h00;
  assign masked_wdata[23:16] = tl_wmask[2] ? tl_wdata[23:16] : 8'h00;
  assign masked_wdata[15:8]  = tl_wmask[1] ? tl_wdata[15:8]  : 8'h00;
  assign masked_wdata[7:0]   = tl_wmask[0] ? tl_wdata[7:0]   : 8'h00;

  assign tl_a_ready_o = tl_d_ready_i | ~rsp_valid_q;

  assign tl_txn_valid = tl_a_valid_i & tl_a_ready_o;
  assign tl_is_write  = tl_txn_valid & ((tl_a_opcode_i == TL_OP_PUT_FULL) |
                                          (tl_a_opcode_i == TL_OP_PUT_PARTIAL));
  assign tl_is_read   = tl_txn_valid & (tl_a_opcode_i == TL_OP_GET);
  assign tl_addr      = {tl_a_address_i[31:2], 2'b00};
  assign tl_wdata     = tl_a_data_i;
  assign tl_wmask     = tl_a_mask_i;
  assign tl_source    = tl_a_source_i;
  assign tl_size      = tl_a_size_i;

  assign addr_valid = (tl_addr <= ADDR_MAX) & (tl_addr[1:0] == 2'b00);

  assign timer0_expired = (mtime_q >= mtimecmp0_q);
  assign timer1_expired = (mtime_q >= mtimecmp1_q);
  assign wd_bark        = wd_enable_q & (wd_count_q >= wd_bark_thresh_q) &
                          (wd_bark_thresh_q != 32'd0);
  assign wd_bite        = wd_enable_q & (wd_count_q >= wd_bite_thresh_q) &
                          (wd_bite_thresh_q != 32'd0);

  assign alert_o = wd_bite;

  assign intr_o[0] = intr_state_q[0] & intr_enable_q[0];
  assign intr_o[1] = intr_state_q[1] & intr_enable_q[1];
  assign intr_o[2] = intr_state_q[2] & intr_enable_q[2];

  assign prescale_tick = (prescale_cnt_q == prescaler_q);

  always_comb begin
    prescale_cnt_d = prescale_cnt_q;
    mtime_d        = mtime_q;

    if (prescale_tick) begin
      prescale_cnt_d = 12'd0;
      mtime_d        = mtime_q + 64'd1;
    end else begin
      prescale_cnt_d = prescale_cnt_q + 12'd1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      prescale_cnt_q <= 12'd0;
    end else begin
      prescale_cnt_q <= prescale_cnt_d;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      mtime_q <= 64'd0;
    end else begin
      mtime_q <= mtime_d;
    end
  end

  assign pet_write = tl_is_write & (tl_addr == ADDR_WATCHDOG_PET);

  always_comb begin
    wd_count_d = wd_count_q;

    if (pet_write) begin
      wd_count_d = 32'd0;
    end else if (wd_enable_q) begin
      wd_count_d = wd_count_q + 32'd1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      wd_count_q <= 32'd0;
    end else begin
      wd_count_q <= wd_count_d;
    end
  end

  always_comb begin
    intr_state_d = intr_state_q;

    if (timer0_expired) begin
      intr_state_d[0] = 1'b1;
    end

    if (timer1_expired) begin
      intr_state_d[1] = 1'b1;
    end

    if (wd_bark) begin
      intr_state_d[2] = 1'b1;
    end

    if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
      intr_state_d = intr_state_d & ~masked_wdata[2:0];
    end

    if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
      intr_state_d = intr_state_d | masked_wdata[2:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_state_q <= 3'd0;
    end else begin
      intr_state_q <= intr_state_d;
    end
  end

  always_comb begin
    mtimecmp0_d = mtimecmp0_q;

    if (tl_is_write && (tl_addr == ADDR_MTIMECMP0_LOW)) begin
      if (tl_wmask[0]) mtimecmp0_d[7:0]   = tl_wdata[7:0];
      if (tl_wmask[1]) mtimecmp0_d[15:8]   = tl_wdata[15:8];
      if (tl_wmask[2]) mtimecmp0_d[23:16]  = tl_wdata[23:16];
      if (tl_wmask[3]) mtimecmp0_d[31:24]  = tl_wdata[31:24];
    end

    if (tl_is_write && (tl_addr == ADDR_MTIMECMP0_HIGH)) begin
      if (tl_wmask[0]) mtimecmp0_d[39:32]  = tl_wdata[7:0];
      if (tl_wmask[1]) mtimecmp0_d[47:40]  = tl_wdata[15:8];
      if (tl_wmask[2]) mtimecmp0_d[55:48]  = tl_wdata[23:16];
      if (tl_wmask[3]) mtimecmp0_d[63:56]  = tl_wdata[31:24];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      mtimecmp0_q <= 64'd0;
    end else begin
      mtimecmp0_q <= mtimecmp0_d;
    end
  end

  always_comb begin
    mtimecmp1_d = mtimecmp1_q;

    if (tl_is_write && (tl_addr == ADDR_MTIMECMP1_LOW)) begin
      if (tl_wmask[0]) mtimecmp1_d[7:0]   = tl_wdata[7:0];
      if (tl_wmask[1]) mtimecmp1_d[15:8]   = tl_wdata[15:8];
      if (tl_wmask[2]) mtimecmp1_d[23:16]  = tl_wdata[23:16];
      if (tl_wmask[3]) mtimecmp1_d[31:24]  = tl_wdata[31:24];
    end

    if (tl_is_write && (tl_addr == ADDR_MTIMECMP1_HIGH)) begin
      if (tl_wmask[0]) mtimecmp1_d[39:32]  = tl_wdata[7:0];
      if (tl_wmask[1]) mtimecmp1_d[47:40]  = tl_wdata[15:8];
      if (tl_wmask[2]) mtimecmp1_d[55:48]  = tl_wdata[23:16];
      if (tl_wmask[3]) mtimecmp1_d[63:56]  = tl_wdata[31:24];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      mtimecmp1_q <= 64'd0;
    end else begin
      mtimecmp1_q <= mtimecmp1_d;
    end
  end

  always_comb begin
    prescaler_d = prescaler_q;

    if (tl_is_write && (tl_addr == ADDR_PRESCALER)) begin
      prescaler_d = masked_wdata[11:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      prescaler_q <= 12'd0;
    end else begin
      prescaler_q <= prescaler_d;
    end
  end

  always_comb begin
    wd_enable_d = wd_enable_q;
    wd_lock_d   = wd_lock_q;

    if (tl_is_write && (tl_addr == ADDR_WATCHDOG_CTRL)) begin
      if (!wd_lock_q) begin
        wd_enable_d = masked_wdata[0];
        wd_lock_d   = masked_wdata[1];
      end else begin
        wd_lock_d = wd_lock_q | masked_wdata[1];
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      wd_enable_q <= 1'b0;
      wd_lock_q   <= 1'b0;
    end else begin
      wd_enable_q <= wd_enable_d;
      wd_lock_q   <= wd_lock_d;
    end
  end

  always_comb begin
    wd_bark_thresh_d = wd_bark_thresh_q;

    if (tl_is_write && (tl_addr == ADDR_WATCHDOG_BARK_THRESH) && !wd_lock_q) begin
      if (tl_wmask[0]) wd_bark_thresh_d[7:0]   = tl_wdata[7:0];
      if (tl_wmask[1]) wd_bark_thresh_d[15:8]   = tl_wdata[15:8];
      if (tl_wmask[2]) wd_bark_thresh_d[23:16]  = tl_wdata[23:16];
      if (tl_wmask[3]) wd_bark_thresh_d[31:24]  = tl_wdata[31:24];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      wd_bark_thresh_q <= 32'd0;
    end else begin
      wd_bark_thresh_q <= wd_bark_thresh_d;
    end
  end

  always_comb begin
    wd_bite_thresh_d = wd_bite_thresh_q;

    if (tl_is_write && (tl_addr == ADDR_WATCHDOG_BITE_THRESH) && !wd_lock_q) begin
      if (tl_wmask[0]) wd_bite_thresh_d[7:0]   = tl_wdata[7:0];
      if (tl_wmask[1]) wd_bite_thresh_d[15:8]   = tl_wdata[15:8];
      if (tl_wmask[2]) wd_bite_thresh_d[23:16]  = tl_wdata[23:16];
      if (tl_wmask[3]) wd_bite_thresh_d[31:24]  = tl_wdata[31:24];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      wd_bite_thresh_q <= 32'd0;
    end else begin
      wd_bite_thresh_q <= wd_bite_thresh_d;
    end
  end

  always_comb begin
    intr_enable_d = intr_enable_q;

    if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
      intr_enable_d = masked_wdata[2:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_enable_q <= 3'd0;
    end else begin
      intr_enable_q <= intr_enable_d;
    end
  end

  always_comb begin
    intr_test_d = intr_test_q;

    if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
      intr_test_d = masked_wdata[2:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_test_q <= 3'd0;
    end else begin
      intr_test_q <= intr_test_d;
    end
  end

  always_comb begin
    rd_data = 32'd0;

    case (tl_addr)
      ADDR_MTIME_LOW: begin
        rd_data = mtime_q[31:0];
      end

      ADDR_MTIME_HIGH: begin
        rd_data = mtime_q[63:32];
      end

      ADDR_MTIMECMP0_LOW: begin
        rd_data = mtimecmp0_q[31:0];
      end

      ADDR_MTIMECMP0_HIGH: begin
        rd_data = mtimecmp0_q[63:32];
      end

      ADDR_MTIMECMP1_LOW: begin
        rd_data = mtimecmp1_q[31:0];
      end

      ADDR_MTIMECMP1_HIGH: begin
        rd_data = mtimecmp1_q[63:32];
      end

      ADDR_PRESCALER: begin
        rd_data = {20'd0, prescaler_q};
      end

      ADDR_WATCHDOG_CTRL: begin
        rd_data = {30'd0, wd_lock_q, wd_enable_q};
      end

      ADDR_WATCHDOG_BARK_THRESH: begin
        rd_data = wd_bark_thresh_q;
      end

      ADDR_WATCHDOG_BITE_THRESH: begin
        rd_data = wd_bite_thresh_q;
      end

      ADDR_WATCHDOG_PET: begin
        rd_data = 32'd0;
      end

      ADDR_WATCHDOG_COUNT: begin
        rd_data = wd_count_q;
      end

      ADDR_INTR_STATE: begin
        rd_data = {29'd0, intr_state_q};
      end

      ADDR_INTR_ENABLE: begin
        rd_data = {29'd0, intr_enable_q};
      end

      ADDR_INTR_TEST: begin
        rd_data = {29'd0, intr_test_q};
      end

      default: begin
        rd_data = 32'd0;
      end
    endcase
  end

  always_comb begin
    rsp_valid_d  = rsp_valid_q;
    rsp_data_d   = rsp_data_q;
    rsp_source_d = rsp_source_q;
    rsp_error_d  = rsp_error_q;
    rsp_opcode_d = rsp_opcode_q;

    if (tl_d_ready_i | ~rsp_valid_q) begin
      if (tl_txn_valid) begin
        rsp_valid_d  = 1'b1;
        rsp_source_d = tl_source;
        rsp_error_d  = ~addr_valid;

        if (tl_is_read) begin
          rsp_data_d   = rd_data;
          rsp_opcode_d = TL_OP_ACCESS_ACK_DATA;
        end else begin
          rsp_data_d   = 32'd0;
          rsp_opcode_d = TL_OP_ACCESS_ACK;
        end
      end else begin
        rsp_valid_d = 1'b0;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rsp_valid_q  <= 1'b0;
      rsp_data_q   <= 32'd0;
      rsp_source_q <= 8'd0;
      rsp_error_q  <= 1'b0;
      rsp_opcode_q <= 3'd0;
    end else begin
      rsp_valid_q  <= rsp_valid_d;
      rsp_data_q   <= rsp_data_d;
      rsp_source_q <= rsp_source_d;
      rsp_error_q  <= rsp_error_d;
      rsp_opcode_q <= rsp_opcode_d;
    end
  end

  assign tl_d_valid_o  = rsp_valid_q;
  assign tl_d_data_o   = rsp_data_q;
  assign tl_d_source_o = rsp_source_q;
  assign tl_d_error_o  = rsp_error_q;
  assign tl_d_opcode_o = rsp_opcode_q;

`ifdef FORMAL

  logic f_past_valid;

  initial f_past_valid = 1'b0;

  always_ff @(posedge clk_i) begin
    f_past_valid <= 1'b1;
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(tl_txn_valid && tl_is_read)) begin
        assert (tl_d_valid_o);
        assert (tl_d_opcode_o == TL_OP_ACCESS_ACK_DATA);
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(tl_txn_valid && tl_is_write)) begin
        assert (tl_d_valid_o);
        assert (tl_d_opcode_o == TL_OP_ACCESS_ACK);
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (!rst_ni) begin
      assert (mtime_q == 64'd0);
      assert (prescale_cnt_q == 12'd0);
      assert (wd_count_q == 32'd0);
      assert (wd_enable_q == 1'b0);
      assert (wd_lock_q == 1'b0);
      assert (intr_state_q == 3'd0);
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(wd_lock_q) && $past(rst_ni)) begin
        assert (wd_lock_q == 1'b1);
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(pet_write)) begin
        assert (wd_count_q == 32'd0);
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(wd_lock_q) && $past(tl_is_write) &&
          $past(tl_addr == ADDR_WATCHDOG_BARK_THRESH)) begin
        assert (wd_bark_thresh_q == $past(wd_bark_thresh_q));
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(wd_lock_q) && $past(tl_is_write) &&
          $past(tl_addr == ADDR_WATCHDOG_BITE_THRESH)) begin
        assert (wd_bite_thresh_q == $past(wd_bite_thresh_q));
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(wd_lock_q) && $past(tl_is_write) &&
          $past(tl_addr == ADDR_WATCHDOG_CTRL)) begin
        assert (wd_enable_q == $past(wd_enable_q));
      end
    end
  end

  always_comb begin
    assert (intr_o[0] == (intr_state_q[0] & intr_enable_q[0]));
    assert (intr_o[1] == (intr_state_q[1] & intr_enable_q[1]));
    assert (intr_o[2] == (intr_state_q[2] & intr_enable_q[2]));
  end

  always_comb begin
    if (wd_enable_q && (wd_count_q >= wd_bite_thresh_q) &&
        (wd_bite_thresh_q != 32'd0)) begin
      assert (alert_o == 1'b1);
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(prescale_cnt_q == prescaler_q)) begin
        assert (prescale_cnt_q == 12'd0);
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni) && !$past(pet_write)) begin
      if ($past(wd_enable_q)) begin
        assert (wd_count_q == $past(wd_count_q) + 32'd1);
      end else begin
        assert (wd_count_q == $past(wd_count_q));
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(tl_is_write && (tl_addr == ADDR_INTR_STATE))) begin
        if ($past(intr_state_q[0]) && $past(masked_wdata[0])) begin
          if (!timer0_expired) begin
            assert (intr_state_q[0] == 1'b0);
          end
        end
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (f_past_valid && $past(rst_ni)) begin
      if ($past(tl_is_write && (tl_addr == ADDR_INTR_TEST) && masked_wdata[0])) begin
        assert (intr_state_q[0] == 1'b1);
      end
    end
  end

`endif

endmodule
