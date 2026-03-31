module citadel_spi
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
  output logic        sclk_o,
  output logic [3:0]  csn_o,
  output logic        mosi_o,
  input  logic        miso_i,
  output logic [3:0]  intr_o,
  output logic        alert_o
);

  localparam logic [31:0] ADDR_CTRL         = 32'h00;
  localparam logic [31:0] ADDR_STATUS       = 32'h04;
  localparam logic [31:0] ADDR_CONFIGOPTS   = 32'h08;
  localparam logic [31:0] ADDR_CSID         = 32'h0C;
  localparam logic [31:0] ADDR_COMMAND      = 32'h10;
  localparam logic [31:0] ADDR_TXDATA       = 32'h14;
  localparam logic [31:0] ADDR_RXDATA       = 32'h18;
  localparam logic [31:0] ADDR_ERROR_ENABLE = 32'h1C;
  localparam logic [31:0] ADDR_ERROR_STATUS = 32'h20;
  localparam logic [31:0] ADDR_INTR_STATE   = 32'h24;
  localparam logic [31:0] ADDR_INTR_ENABLE  = 32'h28;
  localparam logic [31:0] ADDR_INTR_TEST    = 32'h2C;

  localparam int unsigned TX_FIFO_DEPTH = 16;
  localparam int unsigned RX_FIFO_DEPTH = 16;
  localparam int unsigned CMD_FIFO_DEPTH = 4;

  typedef enum logic [2:0] {
    FSM_IDLE,
    FSM_CS_SETUP,
    FSM_DATA_XFER,
    FSM_CS_HOLD,
    FSM_CS_IDLE
  } spi_fsm_e;

  typedef enum logic [1:0] {
    DIR_TX   = 2'd0,
    DIR_RX   = 2'd1,
    DIR_BIDIR = 2'd2
  } spi_dir_e;

  logic        reg_spien;
  logic        reg_output_en;
  logic [15:0] reg_clkdiv;
  logic [3:0]  reg_csn_lead;
  logic [3:0]  reg_csn_trail;
  logic [3:0]  reg_csn_idle;
  logic        reg_cpol;
  logic        reg_cpha;
  logic [1:0]  reg_csid;
  logic [2:0]  reg_error_enable;
  logic [2:0]  reg_error_status;
  logic [3:0]  reg_intr_state;
  logic [3:0]  reg_intr_enable;
  logic [3:0]  reg_intr_test;

  logic [7:0]  tx_fifo_mem [TX_FIFO_DEPTH];
  logic [3:0]  tx_fifo_wptr;
  logic [3:0]  tx_fifo_rptr;
  logic [4:0]  tx_fifo_cnt;
  logic        tx_fifo_full;
  logic        tx_fifo_empty;
  logic        tx_fifo_push;
  logic        tx_fifo_pop;
  logic [7:0]  tx_fifo_wdata;
  logic [7:0]  tx_fifo_rdata;

  logic [7:0]  rx_fifo_mem [RX_FIFO_DEPTH];
  logic [3:0]  rx_fifo_wptr;
  logic [3:0]  rx_fifo_rptr;
  logic [4:0]  rx_fifo_cnt;
  logic        rx_fifo_full;
  logic        rx_fifo_empty;
  logic        rx_fifo_push;
  logic        rx_fifo_pop;
  logic [7:0]  rx_fifo_wdata;
  logic [7:0]  rx_fifo_rdata;

  logic [1:0]  cmd_fifo_mem_direction [CMD_FIFO_DEPTH];
  logic        cmd_fifo_mem_csaat     [CMD_FIFO_DEPTH];
  logic [1:0]  cmd_fifo_mem_speed     [CMD_FIFO_DEPTH];
  logic [8:0]  cmd_fifo_mem_len       [CMD_FIFO_DEPTH];
  logic [1:0]  cmd_fifo_wptr;
  logic [1:0]  cmd_fifo_rptr;
  logic [2:0]  cmd_fifo_cnt;
  logic        cmd_fifo_full;
  logic        cmd_fifo_empty;
  logic        cmd_fifo_push;
  logic        cmd_fifo_pop;
  logic [1:0]  cmd_fifo_wdata_direction;
  logic        cmd_fifo_wdata_csaat;
  logic [1:0]  cmd_fifo_wdata_speed;
  logic [8:0]  cmd_fifo_wdata_len;
  logic [1:0]  cmd_fifo_rdata_direction;
  logic        cmd_fifo_rdata_csaat;
  logic [1:0]  cmd_fifo_rdata_speed;
  logic [8:0]  cmd_fifo_rdata_len;

  spi_fsm_e    fsm_state;
  spi_fsm_e    fsm_next;

  logic [15:0] clk_div_cnt;
  logic        clk_div_tick;
  logic        clk_div_active;
  logic        sclk_int;
  logic [3:0]  timing_cnt;
  logic        timing_done;

  logic [1:0]  active_cmd_direction;
  logic        active_cmd_csaat;
  logic [1:0]  active_cmd_speed;
  logic [8:0]  active_cmd_len;
  logic        active_cmd_valid;
  logic [8:0]  byte_cnt;
  logic [2:0]  bit_cnt;
  logic [7:0]  shift_tx;
  logic [7:0]  shift_rx;
  logic        byte_done;
  logic        segment_done;
  logic        need_tx;
  logic        need_rx;
  logic        tx_underflow_evt;
  logic        rx_overflow_evt;
  logic        cmd_invalid_evt;

  logic [2:0]  error_status_set;
  logic [2:0]  error_status_clr;
  logic [3:0]  intr_state_set;
  logic [3:0]  intr_state_clr;

  logic        spi_done_evt;

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

  logic        leading_edge;
  logic        trailing_edge;
  logic        sample_edge;
  logic        output_edge;
  logic        first_bit_out;

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
      ADDR_CTRL: begin
        tl_rdata = {30'h0, reg_output_en, reg_spien};
      end
      ADDR_STATUS: begin
        tl_rdata = {16'h0,
                    cmd_fifo_empty, cmd_fifo_full,
                    rx_fifo_cnt[3:0], rx_fifo_empty, rx_fifo_full,
                    tx_fifo_cnt[3:0], tx_fifo_empty, tx_fifo_full,
                    (fsm_state != FSM_IDLE), (fsm_state == FSM_IDLE)};
      end
      ADDR_CONFIGOPTS: begin
        tl_rdata = {2'b00, reg_cpha, reg_cpol,
                    reg_csn_idle, reg_csn_trail, reg_csn_lead, reg_clkdiv};
      end
      ADDR_CSID: begin
        tl_rdata = {30'h0, reg_csid};
      end
      ADDR_COMMAND: begin
        tl_rdata = 32'h0;
      end
      ADDR_TXDATA: begin
        tl_rdata = 32'h0;
      end
      ADDR_RXDATA: begin
        tl_rdata = {24'h0, rx_fifo_rdata};
      end
      ADDR_ERROR_ENABLE: begin
        tl_rdata = {29'h0, reg_error_enable};
      end
      ADDR_ERROR_STATUS: begin
        tl_rdata = {29'h0, reg_error_status};
      end
      ADDR_INTR_STATE: begin
        tl_rdata = {28'h0, reg_intr_state};
      end
      ADDR_INTR_ENABLE: begin
        tl_rdata = {28'h0, reg_intr_enable};
      end
      ADDR_INTR_TEST: begin
        tl_rdata = {28'h0, reg_intr_test};
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
      reg_spien     <= 1'b0;
      reg_output_en <= 1'b0;
    end else if (tl_is_write && (tl_addr == ADDR_CTRL)) begin
      reg_spien     <= tl_wdata[0];
      reg_output_en <= tl_wdata[1];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_clkdiv    <= 16'h0;
      reg_csn_lead  <= 4'h0;
      reg_csn_trail <= 4'h0;
      reg_csn_idle  <= 4'h0;
      reg_cpol      <= 1'b0;
      reg_cpha      <= 1'b0;
    end else if (tl_is_write && (tl_addr == ADDR_CONFIGOPTS)) begin
      reg_clkdiv    <= tl_wdata[15:0];
      reg_csn_lead  <= tl_wdata[19:16];
      reg_csn_trail <= tl_wdata[23:20];
      reg_csn_idle  <= tl_wdata[27:24];
      reg_cpol      <= tl_wdata[28];
      reg_cpha      <= tl_wdata[29];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_csid <= 2'h0;
    end else if (tl_is_write && (tl_addr == ADDR_CSID)) begin
      reg_csid <= tl_wdata[1:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_error_enable <= 3'h0;
    end else if (tl_is_write && (tl_addr == ADDR_ERROR_ENABLE)) begin
      reg_error_enable <= tl_wdata[2:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_enable <= 4'h0;
    end else if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
      reg_intr_enable <= tl_wdata[3:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_test <= 4'h0;
    end else begin
      if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
        reg_intr_test <= tl_wdata[3:0];
      end else begin
        reg_intr_test <= 4'h0;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_fifo_wptr <= 4'h0;
      tx_fifo_rptr <= 4'h0;
      tx_fifo_cnt  <= 5'h0;
    end else begin
      if (tx_fifo_push && tx_fifo_pop) begin
        tx_fifo_wptr <= tx_fifo_wptr + 4'h1;
        tx_fifo_rptr <= tx_fifo_rptr + 4'h1;
      end else if (tx_fifo_push && !tx_fifo_full) begin
        tx_fifo_wptr <= tx_fifo_wptr + 4'h1;
        tx_fifo_cnt  <= tx_fifo_cnt + 5'h1;
      end else if (tx_fifo_pop && !tx_fifo_empty) begin
        tx_fifo_rptr <= tx_fifo_rptr + 4'h1;
        tx_fifo_cnt  <= tx_fifo_cnt - 5'h1;
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (tx_fifo_push && !tx_fifo_full) begin
      tx_fifo_mem[tx_fifo_wptr] <= tx_fifo_wdata;
    end
  end

  always_comb begin
    tx_fifo_rdata = tx_fifo_mem[tx_fifo_rptr];
    tx_fifo_full  = (tx_fifo_cnt == 5'd16);
    tx_fifo_empty = (tx_fifo_cnt == 5'd0);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_fifo_wptr <= 4'h0;
      rx_fifo_rptr <= 4'h0;
      rx_fifo_cnt  <= 5'h0;
    end else begin
      if (rx_fifo_push && rx_fifo_pop) begin
        rx_fifo_wptr <= rx_fifo_wptr + 4'h1;
        rx_fifo_rptr <= rx_fifo_rptr + 4'h1;
      end else if (rx_fifo_push && !rx_fifo_full) begin
        rx_fifo_wptr <= rx_fifo_wptr + 4'h1;
        rx_fifo_cnt  <= rx_fifo_cnt + 5'h1;
      end else if (rx_fifo_pop && !rx_fifo_empty) begin
        rx_fifo_rptr <= rx_fifo_rptr + 4'h1;
        rx_fifo_cnt  <= rx_fifo_cnt - 5'h1;
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (rx_fifo_push && !rx_fifo_full) begin
      rx_fifo_mem[rx_fifo_wptr] <= rx_fifo_wdata;
    end
  end

  always_comb begin
    rx_fifo_rdata = rx_fifo_mem[rx_fifo_rptr];
    rx_fifo_full  = (rx_fifo_cnt == 5'd16);
    rx_fifo_empty = (rx_fifo_cnt == 5'd0);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      cmd_fifo_wptr <= 2'h0;
      cmd_fifo_rptr <= 2'h0;
      cmd_fifo_cnt  <= 3'h0;
    end else begin
      if (cmd_fifo_push && cmd_fifo_pop) begin
        cmd_fifo_wptr <= cmd_fifo_wptr + 2'h1;
        cmd_fifo_rptr <= cmd_fifo_rptr + 2'h1;
      end else if (cmd_fifo_push && !cmd_fifo_full) begin
        cmd_fifo_wptr <= cmd_fifo_wptr + 2'h1;
        cmd_fifo_cnt  <= cmd_fifo_cnt + 3'h1;
      end else if (cmd_fifo_pop && !cmd_fifo_empty) begin
        cmd_fifo_rptr <= cmd_fifo_rptr + 2'h1;
        cmd_fifo_cnt  <= cmd_fifo_cnt - 3'h1;
      end
    end
  end

  always_ff @(posedge clk_i) begin
    if (cmd_fifo_push && !cmd_fifo_full) begin
      cmd_fifo_mem_direction[cmd_fifo_wptr] <= cmd_fifo_wdata_direction;
      cmd_fifo_mem_csaat[cmd_fifo_wptr]     <= cmd_fifo_wdata_csaat;
      cmd_fifo_mem_speed[cmd_fifo_wptr]     <= cmd_fifo_wdata_speed;
      cmd_fifo_mem_len[cmd_fifo_wptr]       <= cmd_fifo_wdata_len;
    end
  end

  always_comb begin
    cmd_fifo_rdata_direction = cmd_fifo_mem_direction[cmd_fifo_rptr];
    cmd_fifo_rdata_csaat     = cmd_fifo_mem_csaat[cmd_fifo_rptr];
    cmd_fifo_rdata_speed     = cmd_fifo_mem_speed[cmd_fifo_rptr];
    cmd_fifo_rdata_len       = cmd_fifo_mem_len[cmd_fifo_rptr];
    cmd_fifo_full  = (cmd_fifo_cnt == 3'd4);
    cmd_fifo_empty = (cmd_fifo_cnt == 3'd0);
  end

  always_comb begin
    tx_fifo_push  = 1'b0;
    tx_fifo_wdata = 8'h0;
    if (tl_is_write && (tl_addr == ADDR_TXDATA)) begin
      tx_fifo_push  = 1'b1;
      tx_fifo_wdata = tl_wdata[7:0];
    end
  end

  always_comb begin
    rx_fifo_pop = 1'b0;
    if (tl_is_read && (tl_addr == ADDR_RXDATA)) begin
      rx_fifo_pop = 1'b1;
    end
  end

  always_comb begin
    cmd_fifo_push           = 1'b0;
    cmd_fifo_wdata_direction = 2'd0;
    cmd_fifo_wdata_csaat     = 1'b0;
    cmd_fifo_wdata_speed     = 2'd0;
    cmd_fifo_wdata_len       = 9'd0;
    cmd_invalid_evt          = 1'b0;
    if (tl_is_write && (tl_addr == ADDR_COMMAND)) begin
      if (cmd_fifo_full) begin
        cmd_invalid_evt = 1'b1;
      end else begin
        cmd_fifo_push            = 1'b1;
        cmd_fifo_wdata_len       = tl_wdata[8:0];
        cmd_fifo_wdata_speed     = tl_wdata[10:9];
        cmd_fifo_wdata_csaat     = tl_wdata[11];
        cmd_fifo_wdata_direction = tl_wdata[13:12];
      end
    end
  end

  always_comb begin
    clk_div_active = (fsm_state != FSM_IDLE);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      clk_div_cnt <= 16'h0;
    end else begin
      if (clk_div_active) begin
        if (clk_div_cnt == reg_clkdiv) begin
          clk_div_cnt <= 16'h0;
        end else begin
          clk_div_cnt <= clk_div_cnt + 16'h1;
        end
      end else begin
        clk_div_cnt <= 16'h0;
      end
    end
  end

  always_comb begin
    clk_div_tick = clk_div_active && (clk_div_cnt == reg_clkdiv);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      sclk_int <= 1'b0;
    end else begin
      if (fsm_state != FSM_DATA_XFER) begin
        sclk_int <= reg_cpol;
      end else if (clk_div_tick) begin
        sclk_int <= ~sclk_int;
      end
    end
  end

  always_comb begin
    if (reg_cpol) begin
      leading_edge  = clk_div_tick && sclk_int;
      trailing_edge = clk_div_tick && !sclk_int;
    end else begin
      leading_edge  = clk_div_tick && !sclk_int;
      trailing_edge = clk_div_tick && sclk_int;
    end
  end

  always_comb begin
    if (reg_cpha) begin
      sample_edge = trailing_edge;
      output_edge = leading_edge;
    end else begin
      sample_edge = leading_edge;
      output_edge = trailing_edge;
    end
  end

  always_comb begin
    need_tx = active_cmd_valid &&
              (active_cmd_direction == DIR_TX || active_cmd_direction == DIR_BIDIR);
    need_rx = active_cmd_valid &&
              (active_cmd_direction == DIR_RX || active_cmd_direction == DIR_BIDIR);
  end

  always_comb begin
    byte_done    = (bit_cnt == 3'd7) && sample_edge;
    segment_done = byte_done && (byte_cnt == active_cmd_len);
  end

  always_comb begin
    tx_underflow_evt = 1'b0;
    if (fsm_state == FSM_DATA_XFER && need_tx && bit_cnt == 3'd0 &&
        !first_bit_out && tx_fifo_empty && output_edge) begin
      tx_underflow_evt = 1'b1;
    end
  end

  always_comb begin
    rx_overflow_evt = 1'b0;
    if (fsm_state == FSM_DATA_XFER && byte_done && need_rx && rx_fifo_full) begin
      rx_overflow_evt = 1'b1;
    end
  end

  always_comb begin
    tx_fifo_pop = 1'b0;
    if (fsm_state == FSM_DATA_XFER && need_tx && byte_done && !tx_fifo_empty) begin
      tx_fifo_pop = 1'b1;
    end
    if (fsm_state == FSM_CS_SETUP && timing_done && need_tx && !tx_fifo_empty) begin
      tx_fifo_pop = 1'b1;
    end
  end

  always_comb begin
    rx_fifo_push  = 1'b0;
    rx_fifo_wdata = shift_rx;
    if (fsm_state == FSM_DATA_XFER && byte_done && need_rx && !rx_fifo_full) begin
      rx_fifo_push = 1'b1;
    end
  end

  always_comb begin
    cmd_fifo_pop = 1'b0;
    spi_done_evt = 1'b0;

    case (fsm_state)
      FSM_IDLE: begin
        if (reg_spien && !cmd_fifo_empty) begin
          cmd_fifo_pop = 1'b1;
        end
      end
      FSM_CS_HOLD: begin
        if (timing_done) begin
          spi_done_evt = 1'b1;
        end
      end
      FSM_CS_IDLE: begin
        if (timing_done && !cmd_fifo_empty) begin
          cmd_fifo_pop = 1'b1;
        end
      end
      default: ;
    endcase

    if (fsm_state == FSM_DATA_XFER && segment_done && active_cmd_csaat && !cmd_fifo_empty) begin
      cmd_fifo_pop = 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      active_cmd_direction <= 2'd0;
      active_cmd_csaat     <= 1'b0;
      active_cmd_speed     <= 2'd0;
      active_cmd_len       <= 9'd0;
      active_cmd_valid     <= 1'b0;
    end else begin
      if (cmd_fifo_pop && !cmd_fifo_empty) begin
        active_cmd_direction <= cmd_fifo_rdata_direction;
        active_cmd_csaat     <= cmd_fifo_rdata_csaat;
        active_cmd_speed     <= cmd_fifo_rdata_speed;
        active_cmd_len       <= cmd_fifo_rdata_len;
        active_cmd_valid     <= 1'b1;
      end
      if (fsm_state == FSM_CS_HOLD && timing_done) begin
        active_cmd_valid <= 1'b0;
      end
      if (fsm_state == FSM_CS_IDLE && timing_done && cmd_fifo_empty) begin
        active_cmd_valid <= 1'b0;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fsm_state <= FSM_IDLE;
    end else begin
      fsm_state <= fsm_next;
    end
  end

  always_comb begin
    fsm_next = fsm_state;

    case (fsm_state)
      FSM_IDLE: begin
        if (reg_spien && !cmd_fifo_empty) begin
          fsm_next = FSM_CS_SETUP;
        end
      end

      FSM_CS_SETUP: begin
        if (timing_done) begin
          fsm_next = FSM_DATA_XFER;
        end
      end

      FSM_DATA_XFER: begin
        if (segment_done) begin
          if (active_cmd_csaat) begin
            if (!cmd_fifo_empty) begin
              fsm_next = FSM_DATA_XFER;
            end
          end else begin
            fsm_next = FSM_CS_HOLD;
          end
        end
      end

      FSM_CS_HOLD: begin
        if (timing_done) begin
          fsm_next = FSM_CS_IDLE;
        end
      end

      FSM_CS_IDLE: begin
        if (timing_done) begin
          if (!cmd_fifo_empty) begin
            fsm_next = FSM_CS_SETUP;
          end else begin
            fsm_next = FSM_IDLE;
          end
        end
      end

      default: begin
        fsm_next = FSM_IDLE;
      end
    endcase

    if (!reg_spien && fsm_state != FSM_IDLE) begin
      fsm_next = FSM_IDLE;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      timing_cnt <= 4'h0;
    end else begin
      case (fsm_state)
        FSM_IDLE: begin
          timing_cnt <= 4'h0;
        end
        FSM_CS_SETUP: begin
          if (clk_div_tick || reg_csn_lead == 4'h0) begin
            if (timing_cnt < reg_csn_lead) begin
              timing_cnt <= timing_cnt + 4'h1;
            end
          end
        end
        FSM_CS_HOLD: begin
          if (clk_div_tick || reg_csn_trail == 4'h0) begin
            if (timing_cnt < reg_csn_trail) begin
              timing_cnt <= timing_cnt + 4'h1;
            end
          end
        end
        FSM_CS_IDLE: begin
          if (clk_div_tick || reg_csn_idle == 4'h0) begin
            if (timing_cnt < reg_csn_idle) begin
              timing_cnt <= timing_cnt + 4'h1;
            end
          end
        end
        FSM_DATA_XFER: begin
          if (segment_done) begin
            timing_cnt <= 4'h0;
          end
        end
        default: begin
          timing_cnt <= 4'h0;
        end
      endcase
    end
  end

  always_comb begin
    timing_done = 1'b0;
    case (fsm_state)
      FSM_CS_SETUP: begin
        if (reg_csn_lead == 4'h0) begin
          timing_done = 1'b1;
        end else begin
          timing_done = (timing_cnt == reg_csn_lead);
        end
      end
      FSM_CS_HOLD: begin
        if (reg_csn_trail == 4'h0) begin
          timing_done = 1'b1;
        end else begin
          timing_done = (timing_cnt == reg_csn_trail);
        end
      end
      FSM_CS_IDLE: begin
        if (reg_csn_idle == 4'h0) begin
          timing_done = 1'b1;
        end else begin
          timing_done = (timing_cnt == reg_csn_idle);
        end
      end
      default: timing_done = 1'b0;
    endcase
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      bit_cnt      <= 3'd0;
      byte_cnt     <= 9'd0;
      shift_tx     <= 8'h0;
      shift_rx     <= 8'h0;
      first_bit_out <= 1'b0;
    end else begin
      case (fsm_state)
        FSM_CS_SETUP: begin
          if (timing_done) begin
            bit_cnt      <= 3'd0;
            byte_cnt     <= 9'd0;
            first_bit_out <= 1'b0;
            if (need_tx && !tx_fifo_empty) begin
              shift_tx <= tx_fifo_rdata;
            end else begin
              shift_tx <= 8'h0;
            end
            shift_rx <= 8'h0;
          end
        end

        FSM_DATA_XFER: begin
          if (segment_done && active_cmd_csaat && !cmd_fifo_empty) begin
            bit_cnt       <= 3'd0;
            byte_cnt      <= 9'd0;
            first_bit_out <= 1'b0;
            if ((cmd_fifo_rdata_direction == DIR_TX || cmd_fifo_rdata_direction == DIR_BIDIR)
                && !tx_fifo_empty) begin
              shift_tx <= tx_fifo_rdata;
            end else begin
              shift_tx <= 8'h0;
            end
            shift_rx <= 8'h0;
          end else begin
            if (output_edge && !first_bit_out) begin
              first_bit_out <= 1'b1;
            end

            if (sample_edge) begin
              shift_rx <= {shift_rx[6:0], miso_i};
              if (bit_cnt == 3'd7) begin
                bit_cnt <= 3'd0;
                if (byte_cnt < active_cmd_len) begin
                  byte_cnt <= byte_cnt + 9'd1;
                  if (need_tx && !tx_fifo_empty) begin
                    shift_tx <= tx_fifo_rdata;
                  end
                end
              end else begin
                bit_cnt <= bit_cnt + 3'd1;
              end
            end

            if (output_edge && need_tx) begin
              shift_tx <= {shift_tx[6:0], 1'b0};
            end
          end
        end

        FSM_IDLE: begin
          bit_cnt       <= 3'd0;
          byte_cnt      <= 9'd0;
          shift_tx      <= 8'h0;
          shift_rx      <= 8'h0;
          first_bit_out <= 1'b0;
        end

        default: ;
      endcase
    end
  end

  always_comb begin
    if (reg_output_en) begin
      mosi_o = (fsm_state == FSM_DATA_XFER && need_tx) ? shift_tx[7] : 1'b0;
    end else begin
      mosi_o = 1'b0;
    end
  end

  always_comb begin
    if (reg_output_en) begin
      sclk_o = sclk_int;
    end else begin
      sclk_o = reg_cpol;
    end
  end

  always_comb begin
    csn_o = 4'hF;
    if (reg_output_en) begin
      case (fsm_state)
        FSM_CS_SETUP, FSM_DATA_XFER, FSM_CS_HOLD: begin
          csn_o[reg_csid] = 1'b0;
        end
        default: ;
      endcase
    end
  end

  always_comb begin
    error_status_set = 3'h0;
    if (tx_underflow_evt && reg_error_enable[0]) begin
      error_status_set[0] = 1'b1;
    end
    if (rx_overflow_evt && reg_error_enable[1]) begin
      error_status_set[1] = 1'b1;
    end
    if (cmd_invalid_evt && reg_error_enable[2]) begin
      error_status_set[2] = 1'b1;
    end
  end

  always_comb begin
    error_status_clr = 3'h0;
    if (tl_is_write && (tl_addr == ADDR_ERROR_STATUS)) begin
      error_status_clr = tl_wdata[2:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_error_status <= 3'h0;
    end else begin
      reg_error_status <= (reg_error_status | error_status_set) & ~error_status_clr;
    end
  end

  always_comb begin
    intr_state_set = reg_intr_test;
    if (spi_done_evt) begin
      intr_state_set[0] = 1'b1;
    end
    if (!rx_fifo_empty && rx_fifo_cnt >= 5'd4) begin
      intr_state_set[1] = 1'b1;
    end
    if (tx_fifo_cnt <= 5'd4) begin
      intr_state_set[2] = 1'b1;
    end
    if (|reg_error_status) begin
      intr_state_set[3] = 1'b1;
    end
  end

  always_comb begin
    intr_state_clr = 4'h0;
    if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
      intr_state_clr = tl_wdata[3:0];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      reg_intr_state <= 4'h0;
    end else begin
      reg_intr_state <= (reg_intr_state | intr_state_set) & ~intr_state_clr;
    end
  end

  always_comb begin
    intr_o = reg_intr_state & reg_intr_enable;
  end

  assign alert_o = 1'b0;

endmodule
