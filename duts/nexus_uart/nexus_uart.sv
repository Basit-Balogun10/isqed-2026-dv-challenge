module nexus_uart
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

  output logic        uart_tx_o,
  input  logic        uart_rx_i,
  output logic [6:0]  intr_o,
  output logic        alert_o
);

  localparam int unsigned FIFO_DEPTH = 32;
  localparam int unsigned FIFO_AW    = 5;
  localparam int unsigned NUM_IRQS   = 7;

  localparam logic [31:0] ADDR_CTRL       = 32'h00;
  localparam logic [31:0] ADDR_STATUS     = 32'h04;
  localparam logic [31:0] ADDR_TXDATA     = 32'h08;
  localparam logic [31:0] ADDR_RXDATA     = 32'h0C;
  localparam logic [31:0] ADDR_FIFO_CTRL  = 32'h10;
  localparam logic [31:0] ADDR_INTR_STATE = 32'h14;
  localparam logic [31:0] ADDR_INTR_ENABLE = 32'h18;
  localparam logic [31:0] ADDR_INTR_TEST  = 32'h1C;

  typedef enum logic [3:0] {
    TX_IDLE,
    TX_START,
    TX_DATA,
    TX_PARITY,
    TX_STOP,
    TX_STOP2
  } tx_state_e;

  typedef enum logic [3:0] {
    RX_IDLE,
    RX_START_DET,
    RX_DATA,
    RX_PARITY,
    RX_STOP,
    RX_STOP2
  } rx_state_e;

  logic        ctrl_tx_enable;
  logic        ctrl_rx_enable;
  logic [15:0] ctrl_baud_divisor;
  logic [1:0]  ctrl_parity_mode;
  logic        ctrl_stop_bits;
  logic        ctrl_loopback_en;
  logic [31:0] ctrl_reg;

  logic [4:0]  fifo_ctrl_tx_watermark;
  logic [4:0]  fifo_ctrl_rx_watermark;
  logic        fifo_ctrl_tx_rst;
  logic        fifo_ctrl_rx_rst;

  logic [NUM_IRQS-1:0] intr_state;
  logic [NUM_IRQS-1:0] intr_enable;
  logic [NUM_IRQS-1:0] intr_hw_set;

  logic [7:0]  tx_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] tx_wptr;
  logic [FIFO_AW:0] tx_rptr;
  logic        tx_fifo_empty;
  logic        tx_fifo_full;
  logic [5:0]  tx_fifo_level;
  logic        tx_fifo_push;
  logic        tx_fifo_pop;
  logic [7:0]  tx_fifo_wdata;
  logic [7:0]  tx_fifo_rdata;

  logic [7:0]  rx_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] rx_wptr;
  logic [FIFO_AW:0] rx_rptr;
  logic        rx_fifo_empty;
  logic        rx_fifo_full;
  logic [5:0]  rx_fifo_level;
  logic        rx_fifo_push;
  logic        rx_fifo_pop;
  logic [7:0]  rx_fifo_wdata;
  logic [7:0]  rx_fifo_rdata;

  logic        rx_overrun_sticky;
  logic        rx_parity_err_sticky;
  logic        rx_frame_err_sticky;

  tx_state_e   tx_state;
  logic [15:0] tx_baud_cnt;
  logic        tx_baud_tick;
  logic [2:0]  tx_bit_idx;
  logic [7:0]  tx_shift_reg;
  logic        tx_parity_bit;

  rx_state_e   rx_state;
  logic [15:0] rx_baud_cnt;
  logic        rx_os_tick;
  logic [3:0]  rx_os_cnt;
  logic [2:0]  rx_bit_idx;
  logic [7:0]  rx_shift_reg;
  logic        rx_parity_calc;

  logic        rx_expected_parity;

  logic        rx_serial_in;
  logic        rx_serial_q;
  logic        rx_serial_qq;

  logic [31:0] rx_timeout_cnt;
  logic        rx_timeout_event;
  logic [31:0] rx_timeout_thresh;
  logic        rx_active;

  logic        tl_req_valid;
  logic        tl_req_write;
  logic [31:0] tl_req_addr;
  logic [31:0] tl_req_wdata;
  logic [31:0] tl_rsp_rdata;
  logic        tl_rsp_error;
  logic        tl_rsp_pending;

  always_comb begin
    tl_req_valid = tl_a_valid_i & tl_a_ready_o;
    tl_req_write = (tl_a_opcode_i == 3'd0) || (tl_a_opcode_i == 3'd1);
    tl_req_addr  = {tl_a_address_i[31:2], 2'b00};
    tl_req_wdata = tl_a_data_i;
  end

  always_comb begin
    tl_a_ready_o = !tl_rsp_pending || tl_d_ready_i;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tl_rsp_pending <= 1'b0;
      tl_d_valid_o   <= 1'b0;
      tl_d_opcode_o  <= 3'd0;
      tl_d_data_o    <= 32'd0;
      tl_d_source_o  <= 8'd0;
      tl_d_error_o   <= 1'b0;
    end else begin
      if (tl_rsp_pending && tl_d_ready_i) begin
        tl_rsp_pending <= 1'b0;
        tl_d_valid_o   <= 1'b0;
      end
      if (tl_req_valid) begin
        tl_rsp_pending <= 1'b1;
        tl_d_valid_o   <= 1'b1;
        tl_d_opcode_o  <= tl_req_write ? 3'd0 : 3'd1;
        tl_d_data_o    <= tl_rsp_rdata;
        tl_d_source_o  <= tl_a_source_i;
        tl_d_error_o   <= tl_rsp_error;
      end
    end
  end

  always_comb begin
    tl_rsp_rdata = 32'h0;
    tl_rsp_error = 1'b0;
    tx_fifo_push = 1'b0;
    tx_fifo_wdata = 8'h0;
    rx_fifo_pop  = 1'b0;

    if (tl_req_valid) begin
      if (tl_req_write) begin
        case (tl_req_addr)
          ADDR_CTRL,
          ADDR_TXDATA,
          ADDR_FIFO_CTRL,
          ADDR_INTR_STATE,
          ADDR_INTR_ENABLE,
          ADDR_INTR_TEST: ;
          ADDR_STATUS,
          ADDR_RXDATA: tl_rsp_error = 1'b1;
          default: tl_rsp_error = 1'b1;
        endcase

        if (tl_req_addr == ADDR_TXDATA) begin
          tx_fifo_push  = 1'b1;
          tx_fifo_wdata = tl_req_wdata[7:0];
        end
      end else begin
        case (tl_req_addr)
          ADDR_CTRL:        tl_rsp_rdata = ctrl_reg;
          ADDR_STATUS:      tl_rsp_rdata = {13'b0, rx_frame_err_sticky, rx_parity_err_sticky,
                                             rx_overrun_sticky, rx_fifo_level, tx_fifo_level,
                                             rx_fifo_full, rx_fifo_empty, tx_fifo_full, tx_fifo_empty};
          ADDR_TXDATA:      begin tl_rsp_rdata = 32'h0; tl_rsp_error = 1'b1; end
          ADDR_RXDATA:      begin
                              tl_rsp_rdata = {24'h0, rx_fifo_rdata};
                              rx_fifo_pop  = ~rx_fifo_empty;
                            end
          ADDR_FIFO_CTRL:   tl_rsp_rdata = {20'b0, 2'b0, fifo_ctrl_rx_watermark, fifo_ctrl_tx_watermark};
          ADDR_INTR_STATE:  tl_rsp_rdata = {25'b0, intr_state};
          ADDR_INTR_ENABLE: tl_rsp_rdata = {25'b0, intr_enable};
          ADDR_INTR_TEST:   tl_rsp_rdata = 32'h0;
          default:          tl_rsp_error = 1'b1;
        endcase
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      ctrl_reg          <= 32'h0;
      ctrl_tx_enable    <= 1'b0;
      ctrl_rx_enable    <= 1'b0;
      ctrl_baud_divisor <= 16'h0;
      ctrl_parity_mode  <= 2'b00;
      ctrl_stop_bits    <= 1'b0;
      ctrl_loopback_en  <= 1'b0;
    end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_CTRL) begin
      ctrl_reg          <= tl_req_wdata;
      ctrl_tx_enable    <= tl_req_wdata[0];
      ctrl_rx_enable    <= tl_req_wdata[1];
      ctrl_baud_divisor <= tl_req_wdata[17:2];
      ctrl_parity_mode  <= tl_req_wdata[19:18];
      ctrl_stop_bits    <= tl_req_wdata[20];
      ctrl_loopback_en  <= tl_req_wdata[21];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fifo_ctrl_tx_watermark <= 5'd1;
      fifo_ctrl_rx_watermark <= 5'd1;
      fifo_ctrl_tx_rst       <= 1'b0;
      fifo_ctrl_rx_rst       <= 1'b0;
    end else begin
      if (fifo_ctrl_tx_rst) fifo_ctrl_tx_rst <= 1'b0;
      if (fifo_ctrl_rx_rst) fifo_ctrl_rx_rst <= 1'b0;

      if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_FIFO_CTRL) begin
        fifo_ctrl_tx_watermark <= tl_req_wdata[4:0];
        fifo_ctrl_rx_watermark <= tl_req_wdata[9:5];
        fifo_ctrl_tx_rst       <= tl_req_wdata[10];
        fifo_ctrl_rx_rst       <= tl_req_wdata[11];
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_state  <= '0;
      intr_enable <= '0;
    end else begin
      intr_state <= intr_state | intr_hw_set;

      if (tl_req_valid && tl_req_write) begin
        if (tl_req_addr == ADDR_INTR_STATE) begin
          intr_state <= (intr_state | intr_hw_set) & ~tl_req_wdata[NUM_IRQS-1:0];
        end
        if (tl_req_addr == ADDR_INTR_ENABLE) begin
          intr_enable <= tl_req_wdata[NUM_IRQS-1:0];
        end
        if (tl_req_addr == ADDR_INTR_TEST) begin
          intr_state <= intr_state | intr_hw_set | tl_req_wdata[NUM_IRQS-1:0];
        end
      end
    end
  end

  always_comb begin
    intr_o = intr_state & intr_enable;
  end

  always_comb begin
    tx_fifo_empty = (tx_wptr == tx_rptr);
    tx_fifo_full  = (tx_wptr[FIFO_AW] != tx_rptr[FIFO_AW]) &&
                    (tx_wptr[FIFO_AW-1:0] == tx_rptr[FIFO_AW-1:0]);
    tx_fifo_level = tx_wptr - tx_rptr;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_wptr <= '0;
    end else if (fifo_ctrl_tx_rst) begin
      tx_wptr <= '0;
    end else if (tx_fifo_push && !tx_fifo_full) begin
      tx_fifo_mem[tx_wptr[FIFO_AW-1:0]] <= tx_fifo_wdata;
      tx_wptr <= tx_wptr + 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_rptr <= '0;
    end else if (fifo_ctrl_tx_rst) begin
      tx_rptr <= '0;
    end else if (tx_fifo_pop && !tx_fifo_empty) begin
      tx_rptr <= tx_rptr + 1'b1;
    end
  end

  always_comb begin
    tx_fifo_rdata = tx_fifo_mem[tx_rptr[FIFO_AW-1:0]];
  end

  always_comb begin
    rx_fifo_empty = (rx_wptr == rx_rptr);
    rx_fifo_full  = (rx_wptr[FIFO_AW] != rx_rptr[FIFO_AW]) &&
                    (rx_wptr[FIFO_AW-1:0] == rx_rptr[FIFO_AW-1:0]);
    rx_fifo_level = rx_wptr - rx_rptr;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_wptr <= '0;
    end else if (fifo_ctrl_rx_rst) begin
      rx_wptr <= '0;
    end else if (rx_fifo_push && !rx_fifo_full) begin
      rx_fifo_mem[rx_wptr[FIFO_AW-1:0]] <= rx_fifo_wdata;
      rx_wptr <= rx_wptr + 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_rptr <= '0;
    end else if (fifo_ctrl_rx_rst) begin
      rx_rptr <= '0;
    end else if (rx_fifo_pop && !rx_fifo_empty) begin
      rx_rptr <= rx_rptr + 1'b1;
    end
  end

  always_comb begin
    rx_fifo_rdata = rx_fifo_mem[rx_rptr[FIFO_AW-1:0]];
  end

  logic tx_fifo_pop_req;
  assign tx_fifo_pop = tx_fifo_pop_req;

  always_comb begin
    tx_baud_tick = (tx_baud_cnt == ctrl_baud_divisor) && (ctrl_baud_divisor != 16'h0);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_baud_cnt <= 16'h0;
    end else begin
      if (tx_state == TX_IDLE || tx_baud_tick) begin
        tx_baud_cnt <= 16'h0;
      end else begin
        tx_baud_cnt <= tx_baud_cnt + 16'h1;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_state     <= TX_IDLE;
      uart_tx_o    <= 1'b1;
      tx_bit_idx   <= 3'h0;
      tx_shift_reg <= 8'h0;
      tx_parity_bit <= 1'b0;
      tx_fifo_pop_req <= 1'b0;
    end else begin
      tx_fifo_pop_req <= 1'b0;

      case (tx_state)
        TX_IDLE: begin
          uart_tx_o <= 1'b1;
          if (ctrl_tx_enable && !tx_fifo_empty) begin
            tx_shift_reg <= tx_fifo_rdata;
            tx_fifo_pop_req <= 1'b1;
            tx_state <= TX_START;
            tx_bit_idx <= 3'h0;
            if (ctrl_parity_mode == 2'b01)
              tx_parity_bit <= ^tx_fifo_rdata;
            else if (ctrl_parity_mode == 2'b10)
              tx_parity_bit <= ~(^tx_fifo_rdata);
            else
              tx_parity_bit <= 1'b0;
          end
        end

        TX_START: begin
          uart_tx_o <= 1'b0;
          if (tx_baud_tick) begin
            tx_state <= TX_DATA;
            tx_bit_idx <= 3'h0;
          end
        end

        TX_DATA: begin
          uart_tx_o <= tx_shift_reg[tx_bit_idx];
          if (tx_baud_tick) begin
            if (tx_bit_idx == 3'd7) begin
              if (ctrl_parity_mode != 2'b00)
                tx_state <= TX_PARITY;
              else
                tx_state <= TX_STOP;
            end else begin
              tx_bit_idx <= tx_bit_idx + 3'h1;
            end
          end
        end

        TX_PARITY: begin
          uart_tx_o <= tx_parity_bit;
          if (tx_baud_tick) begin
            tx_state <= TX_STOP;
          end
        end

        TX_STOP: begin
          uart_tx_o <= 1'b1;
          if (tx_baud_tick) begin
            if (ctrl_stop_bits)
              tx_state <= TX_STOP2;
            else
              tx_state <= TX_IDLE;
          end
        end

        TX_STOP2: begin
          uart_tx_o <= 1'b1;
          if (tx_baud_tick) begin
            tx_state <= TX_IDLE;
          end
        end

        default: tx_state <= TX_IDLE;
      endcase
    end
  end

  always_comb begin
    rx_serial_in = ctrl_loopback_en ? uart_tx_o : uart_rx_i;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_serial_q  <= 1'b1;
      rx_serial_qq <= 1'b1;
    end else begin
      rx_serial_q  <= rx_serial_in;
      rx_serial_qq <= rx_serial_q;
    end
  end

  logic [15:0] rx_os_divisor;
  always_comb begin
    rx_os_divisor = {4'b0, ctrl_baud_divisor[15:4]};
  end

  always_comb begin
    rx_os_tick = (rx_baud_cnt == rx_os_divisor) && (ctrl_baud_divisor != 16'h0);
  end

  always_comb begin
    if (ctrl_parity_mode == 2'b01)
      rx_expected_parity = rx_parity_calc;
    else
      rx_expected_parity = ~rx_parity_calc;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_baud_cnt <= 16'h0;
    end else begin
      if (rx_state == RX_IDLE || rx_os_tick) begin
        rx_baud_cnt <= 16'h0;
      end else begin
        rx_baud_cnt <= rx_baud_cnt + 16'h1;
      end
    end
  end

  logic        rx_push_valid;
  logic [7:0]  rx_push_data;
  logic        rx_parity_error_det;
  logic        rx_frame_error_det;
  logic        rx_overflow_det;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_state       <= RX_IDLE;
      rx_os_cnt      <= 4'h0;
      rx_bit_idx     <= 3'h0;
      rx_shift_reg   <= 8'h0;
      rx_parity_calc <= 1'b0;
      rx_push_valid  <= 1'b0;
      rx_push_data   <= 8'h0;
      rx_parity_error_det <= 1'b0;
      rx_frame_error_det  <= 1'b0;
      rx_overflow_det     <= 1'b0;
      rx_active      <= 1'b0;
    end else begin
      rx_push_valid       <= 1'b0;
      rx_parity_error_det <= 1'b0;
      rx_frame_error_det  <= 1'b0;
      rx_overflow_det     <= 1'b0;

      case (rx_state)
        RX_IDLE: begin
          rx_os_cnt  <= 4'h0;
          rx_bit_idx <= 3'h0;
          rx_active  <= 1'b0;
          if (ctrl_rx_enable && rx_serial_qq == 1'b0) begin
            rx_state  <= RX_START_DET;
            rx_os_cnt <= 4'h1;
            rx_active <= 1'b1;
          end
        end

        RX_START_DET: begin
          if (rx_os_tick) begin
            rx_os_cnt <= rx_os_cnt + 4'h1;
            if (rx_os_cnt == 4'd8) begin
              if (rx_serial_qq == 1'b0) begin
                rx_state      <= RX_DATA;
                rx_os_cnt     <= 4'h0;
                rx_bit_idx    <= 3'h0;
                rx_parity_calc <= 1'b0;
              end else begin
                rx_state <= RX_IDLE;
              end
            end
          end
        end

        RX_DATA: begin
          if (rx_os_tick) begin
            rx_os_cnt <= rx_os_cnt + 4'h1;
            if (rx_os_cnt == 4'd15) begin
              rx_os_cnt <= 4'h0;
            end
            if (rx_os_cnt == 4'd8) begin
              rx_shift_reg[rx_bit_idx] <= rx_serial_qq;
              rx_parity_calc <= rx_parity_calc ^ rx_serial_qq;
              if (rx_bit_idx == 3'd7) begin
                if (ctrl_parity_mode != 2'b00)
                  rx_state <= RX_PARITY;
                else
                  rx_state <= RX_STOP;
                rx_os_cnt <= 4'h0;
              end else begin
                rx_bit_idx <= rx_bit_idx + 3'h1;
              end
            end
          end
        end

        RX_PARITY: begin
          if (rx_os_tick) begin
            rx_os_cnt <= rx_os_cnt + 4'h1;
            if (rx_os_cnt == 4'd15) begin
              rx_os_cnt <= 4'h0;
            end
            if (rx_os_cnt == 4'd8) begin
              if (rx_serial_qq != rx_expected_parity) begin
                rx_parity_error_det <= 1'b1;
              end
              rx_state  <= RX_STOP;
              rx_os_cnt <= 4'h0;
            end
          end
        end

        RX_STOP: begin
          if (rx_os_tick) begin
            rx_os_cnt <= rx_os_cnt + 4'h1;
            if (rx_os_cnt == 4'd15) begin
              rx_os_cnt <= 4'h0;
            end
            if (rx_os_cnt == 4'd8) begin
              if (rx_serial_qq == 1'b0) begin
                rx_frame_error_det <= 1'b1;
              end
              if (ctrl_stop_bits) begin
                rx_state  <= RX_STOP2;
                rx_os_cnt <= 4'h0;
              end else begin
                if (rx_fifo_full) begin
                  rx_overflow_det <= 1'b1;
                end else begin
                  rx_push_valid <= 1'b1;
                  rx_push_data  <= rx_shift_reg;
                end
                rx_state <= RX_IDLE;
              end
            end
          end
        end

        RX_STOP2: begin
          if (rx_os_tick) begin
            rx_os_cnt <= rx_os_cnt + 4'h1;
            if (rx_os_cnt == 4'd15) begin
              rx_os_cnt <= 4'h0;
            end
            if (rx_os_cnt == 4'd8) begin
              if (rx_serial_qq == 1'b0) begin
                rx_frame_error_det <= 1'b1;
              end
              if (rx_fifo_full) begin
                rx_overflow_det <= 1'b1;
              end else begin
                rx_push_valid <= 1'b1;
                rx_push_data  <= rx_shift_reg;
              end
              rx_state <= RX_IDLE;
            end
          end
        end

        default: rx_state <= RX_IDLE;
      endcase
    end
  end

  assign rx_fifo_push  = rx_push_valid;
  assign rx_fifo_wdata = rx_push_data;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_overrun_sticky    <= 1'b0;
      rx_parity_err_sticky <= 1'b0;
      rx_frame_err_sticky  <= 1'b0;
    end else begin
      if (fifo_ctrl_rx_rst) begin
        rx_overrun_sticky    <= 1'b0;
        rx_parity_err_sticky <= 1'b0;
        rx_frame_err_sticky  <= 1'b0;
      end else begin
        if (rx_overflow_det)     rx_overrun_sticky    <= 1'b1;
        if (rx_parity_error_det) rx_parity_err_sticky <= 1'b1;
        if (rx_frame_error_det)  rx_frame_err_sticky  <= 1'b1;
      end
    end
  end

  always_comb begin
    rx_timeout_thresh = {16'h0, ctrl_baud_divisor} * 32'd16;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_timeout_cnt   <= 32'h0;
      rx_timeout_event <= 1'b0;
    end else begin
      rx_timeout_event <= 1'b0;
      if (rx_active || rx_state != RX_IDLE) begin
        rx_timeout_cnt <= 32'h0;
      end else if (!rx_fifo_empty && ctrl_rx_enable) begin
        if (rx_serial_qq == 1'b1) begin
          if (rx_timeout_cnt < rx_timeout_thresh) begin
            rx_timeout_cnt <= rx_timeout_cnt + 32'h1;
          end else begin
            rx_timeout_event <= 1'b1;
          end
        end else begin
          rx_timeout_cnt <= 32'h0;
        end
      end else begin
        rx_timeout_cnt <= 32'h0;
      end
    end
  end

  always_comb begin
    intr_hw_set = '0;

    if (tx_fifo_level <= {1'b0, fifo_ctrl_tx_watermark} && ctrl_tx_enable)
      intr_hw_set[0] = 1'b1;

    if (rx_fifo_level >= {1'b0, fifo_ctrl_rx_watermark} && ctrl_rx_enable)
      intr_hw_set[1] = 1'b1;

    if (tx_fifo_empty && ctrl_tx_enable)
      intr_hw_set[2] = 1'b1;

    if (rx_overflow_det)
      intr_hw_set[3] = 1'b1;

    if (rx_frame_error_det)
      intr_hw_set[4] = 1'b1;

    if (rx_parity_error_det)
      intr_hw_set[5] = 1'b1;

    if (rx_timeout_event)
      intr_hw_set[6] = 1'b1;
  end

  assign alert_o = 1'b0;

endmodule
