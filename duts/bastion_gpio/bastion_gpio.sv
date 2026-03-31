module bastion_gpio
  import dv_common_pkg::*;
(
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
  input  logic [31:0] gpio_i,
  output logic [31:0] gpio_o,
  output logic [31:0] gpio_oe_o,
  output logic [31:0] intr_o,
  output logic        alert_o
);

  localparam logic [31:0] ADDR_DATA_IN              = 32'h00;
  localparam logic [31:0] ADDR_DATA_OUT             = 32'h04;
  localparam logic [31:0] ADDR_DIR                  = 32'h08;
  localparam logic [31:0] ADDR_INTR_STATE           = 32'h0C;
  localparam logic [31:0] ADDR_INTR_ENABLE          = 32'h10;
  localparam logic [31:0] ADDR_INTR_TEST            = 32'h14;
  localparam logic [31:0] ADDR_INTR_CTRL_EN_RISING  = 32'h18;
  localparam logic [31:0] ADDR_INTR_CTRL_EN_FALLING = 32'h1C;
  localparam logic [31:0] ADDR_INTR_CTRL_EN_LVLHIGH = 32'h20;
  localparam logic [31:0] ADDR_INTR_CTRL_EN_LVLLOW  = 32'h24;
  localparam logic [31:0] ADDR_MASKED_OUT_LOWER     = 32'h28;
  localparam logic [31:0] ADDR_MASKED_OUT_UPPER     = 32'h2C;

  logic [31:0] reg_data_out;
  logic [31:0] reg_dir;
  logic [31:0] reg_intr_state;
  logic [31:0] reg_intr_enable;
  logic [31:0] reg_intr_test;
  logic [31:0] reg_intr_ctrl_en_rising;
  logic [31:0] reg_intr_ctrl_en_falling;
  logic [31:0] reg_intr_ctrl_en_lvlhigh;
  logic [31:0] reg_intr_ctrl_en_lvllow;

  logic [31:0] gpio_sync_q1;
  logic [31:0] gpio_sync_q2;
  logic [31:0] gpio_sync_prev;

  logic [31:0] rising_edge_det;
  logic [31:0] falling_edge_det;

  logic [31:0] intr_rising;
  logic [31:0] intr_falling;
  logic [31:0] intr_lvlhigh;
  logic [31:0] intr_lvllow;
  logic [31:0] intr_combined;

  logic [31:0] intr_state_set;
  logic [31:0] intr_state_clr;

  logic        tl_req_valid;
  logic        tl_is_write;
  logic        tl_is_read;
  logic [31:0] tl_addr;
  logic [31:0] tl_wdata;
  logic [31:0] tl_rdata;
  logic        tl_error;
  logic [7:0]  tl_source;

  logic        pending_resp;
  logic [31:0] resp_data;
  logic [7:0]  resp_source;
  logic        resp_error;
  logic        resp_is_read;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      gpio_sync_q1 <= 32'h0;
      gpio_sync_q2 <= 32'h0;
    end else begin
      gpio_sync_q1 <= gpio_i;
      gpio_sync_q2 <= gpio_sync_q1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      gpio_sync_prev <= 32'h0;
    end else begin
      gpio_sync_prev <= gpio_sync_q2;
    end
  end

  always_comb begin
    rising_edge_det  = gpio_sync_q2 & ~gpio_sync_prev;
    falling_edge_det = ~gpio_sync_q2 & gpio_sync_prev;
  end

  always_comb begin
    intr_rising  = rising_edge_det & reg_intr_ctrl_en_rising;
    intr_falling = falling_edge_det & reg_intr_ctrl_en_falling;
    intr_lvlhigh = gpio_sync_q2 & reg_intr_ctrl_en_lvlhigh;
    intr_lvllow  = ~gpio_sync_q2 & reg_intr_ctrl_en_lvllow;
  end

  always_comb begin
    intr_combined = intr_rising | intr_falling | intr_lvlhigh | intr_lvllow;
  end

  always_comb begin
    intr_state_set = intr_combined | reg_intr_test;
  end

  always_comb begin
    tl_req_valid = tl_a_valid_i & tl_a_ready_o;
    tl_is_write  = tl_req_valid & ((tl_a_opcode_i == 3'd0) | (tl_a_opcode_i == 3'd1));
    tl_is_read   = tl_req_valid & (tl_a_opcode_i == 3'd4);
    tl_addr      = {tl_a_address_i[31:2], 2'b00};
    tl_wdata     = tl_a_data_i;
    tl_source    = tl_a_source_i;
  end

  always_comb begin
    tl_a_ready_o = !pending_resp | tl_d_ready_i;
  end

  always_comb begin
    tl_rdata = 32'h0;
    tl_error = 1'b0;

    case (tl_addr)
      ADDR_DATA_IN: begin
        tl_rdata = gpio_sync_q2;
      end
      ADDR_DATA_OUT: begin
        tl_rdata = reg_data_out;
      end
      ADDR_DIR: begin
        tl_rdata = reg_dir;
      end
      ADDR_INTR_STATE: begin
        tl_rdata = reg_intr_state;
      end
      ADDR_INTR_ENABLE: begin
        tl_rdata = reg_intr_enable;
      end
      ADDR_INTR_TEST: begin
        tl_rdata = reg_intr_test;
      end
      ADDR_INTR_CTRL_EN_RISING: begin
        tl_rdata = reg_intr_ctrl_en_rising;
      end
      ADDR_INTR_CTRL_EN_FALLING: begin
        tl_rdata = reg_intr_ctrl_en_falling;
      end
      ADDR_INTR_CTRL_EN_LVLHIGH: begin
        tl_rdata = reg_intr_ctrl_en_lvlhigh;
      end
      ADDR_INTR_CTRL_EN_LVLLOW: begin
        tl_rdata = reg_intr_ctrl_en_lvllow;
      end
      ADDR_MASKED_OUT_LOWER: begin
        tl_rdata = {16'h0, reg_data_out[15:0]};
      end
      ADDR_MASKED_OUT_UPPER: begin
        tl_rdata = {16'h0, reg_data_out[31:16]};
      end
      default: begin
        tl_rdata = 32'h0;
      end
    endcase
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      pending_resp <= 1'b0;
      resp_data    <= 32'h0;
      resp_source  <= 8'h0;
      resp_error   <= 1'b0;
      resp_is_read <= 1'b0;
    end else begin
      if (pending_resp & tl_d_ready_i) begin
        pending_resp <= 1'b0;
      end
      if (tl_req_valid) begin
        pending_resp <= 1'b1;
        resp_data    <= tl_rdata;
        resp_source  <= tl_source;
        resp_error   <= tl_error;
        resp_is_read <= tl_is_read;
      end
    end
  end

  always_comb begin
    tl_d_valid_o  = pending_resp;
    tl_d_data_o   = resp_data;
    tl_d_source_o = resp_source;
    tl_d_error_o  = resp_error;
    tl_d_opcode_o = resp_is_read ? 3'd1 : 3'd0;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_data_out <= 32'h0;
    end else begin
      if (tl_is_write) begin
        case (tl_addr)
          ADDR_DATA_OUT: begin
            reg_data_out <= tl_wdata;
          end
          ADDR_MASKED_OUT_LOWER: begin
            for (int i = 0; i < 16; i++) begin
              if (tl_wdata[i + 16]) begin
                reg_data_out[i] <= tl_wdata[i];
              end
            end
          end
          ADDR_MASKED_OUT_UPPER: begin
            for (int i = 0; i < 16; i++) begin
              if (tl_wdata[i + 16]) begin
                reg_data_out[i + 16] <= tl_wdata[i];
              end
            end
          end
          default: ;
        endcase
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_dir <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_DIR)) begin
      reg_dir <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_enable <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
      reg_intr_enable <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_test <= 32'h0;
    end else begin
      if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
        reg_intr_test <= tl_wdata;
      end else begin
        reg_intr_test <= 32'h0;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_ctrl_en_rising <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_RISING)) begin
      reg_intr_ctrl_en_rising <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_ctrl_en_falling <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_FALLING)) begin
      reg_intr_ctrl_en_falling <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_ctrl_en_lvlhigh <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_LVLHIGH)) begin
      reg_intr_ctrl_en_lvlhigh <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_ctrl_en_lvllow <= 32'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_LVLLOW)) begin
      reg_intr_ctrl_en_lvllow <= tl_wdata;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_state <= 32'h0;
    end else begin
      reg_intr_state <= (reg_intr_state | intr_state_set) & ~intr_state_clr;
    end
  end

  always_comb begin
    intr_state_clr = 32'h0;
    if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
      intr_state_clr = tl_wdata;
    end
  end

  always_comb begin
    intr_o = reg_intr_state & reg_intr_enable;
  end

  always_comb begin
    gpio_o    = reg_data_out;
    gpio_oe_o = reg_dir;
  end

  assign alert_o = 1'b0;

endmodule
