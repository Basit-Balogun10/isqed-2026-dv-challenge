module rampart_i2c
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
  input  logic        scl_i,
  output logic        scl_o,
  output logic        scl_oe_o,
  input  logic        sda_i,
  output logic        sda_o,
  output logic        sda_oe_o,
  output logic [15:0] intr_o,
  output logic        alert_o
);

  localparam int unsigned FIFO_DEPTH = 64;
  localparam int unsigned FIFO_AW    = 6;
  localparam int unsigned NUM_IRQS   = 16;

  localparam logic [31:0] ADDR_CTRL              = 32'h00;
  localparam logic [31:0] ADDR_STATUS            = 32'h04;
  localparam logic [31:0] ADDR_RDATA             = 32'h08;
  localparam logic [31:0] ADDR_FDATA             = 32'h0C;
  localparam logic [31:0] ADDR_FIFO_CTRL         = 32'h10;
  localparam logic [31:0] ADDR_FIFO_STATUS       = 32'h14;
  localparam logic [31:0] ADDR_OVRD              = 32'h18;
  localparam logic [31:0] ADDR_TIMING0           = 32'h1C;
  localparam logic [31:0] ADDR_TIMING1           = 32'h20;
  localparam logic [31:0] ADDR_TIMING2           = 32'h24;
  localparam logic [31:0] ADDR_TIMING3           = 32'h28;
  localparam logic [31:0] ADDR_TIMING4           = 32'h2C;
  localparam logic [31:0] ADDR_TARGET_ID         = 32'h30;
  localparam logic [31:0] ADDR_ACQDATA           = 32'h34;
  localparam logic [31:0] ADDR_TXDATA            = 32'h38;
  localparam logic [31:0] ADDR_HOST_TIMEOUT_CTRL = 32'h3C;
  localparam logic [31:0] ADDR_INTR_STATE        = 32'h40;
  localparam logic [31:0] ADDR_INTR_ENABLE       = 32'h44;
  localparam logic [31:0] ADDR_INTR_TEST         = 32'h48;

  typedef enum logic [3:0] {
    HOST_IDLE,
    HOST_START,
    HOST_ADDR_BYTE,
    HOST_ADDR_ACK,
    HOST_WRITE_BYTE,
    HOST_WRITE_ACK,
    HOST_READ_BYTE,
    HOST_READ_ACK,
    HOST_STOP,
    HOST_RSTART_SETUP,
    HOST_WAIT_BUS_FREE
  } host_state_e;

  typedef enum logic [3:0] {
    TGT_IDLE,
    TGT_START_DET,
    TGT_ADDR_RECV,
    TGT_ADDR_ACK,
    TGT_DATA_RX,
    TGT_DATA_RX_ACK,
    TGT_DATA_TX,
    TGT_DATA_TX_ACK,
    TGT_STRETCH,
    TGT_STOP_DET
  } tgt_state_e;

  logic        ctrl_host_enable;
  logic        ctrl_target_enable;
  logic        ctrl_line_loopback;
  logic [31:0] ctrl_reg;

  logic [15:0] timing_tlow;
  logic [15:0] timing_thigh;
  logic [15:0] timing_t_r;
  logic [15:0] timing_t_f;
  logic [15:0] timing_tsu_sta;
  logic [15:0] timing_thd_sta;
  logic [15:0] timing_tsu_dat;
  logic [15:0] timing_thd_dat;
  logic [15:0] timing_tsu_sto;
  logic [15:0] timing_t_buf;

  logic [6:0]  target_address;
  logic [6:0]  target_mask;

  logic        ovrd_txovrden;
  logic        ovrd_sclval;
  logic        ovrd_sdaval;

  logic [19:0] host_timeout_val;
  logic        host_timeout_en;

  logic [NUM_IRQS-1:0] intr_state;
  logic [NUM_IRQS-1:0] intr_enable;
  logic [NUM_IRQS-1:0] intr_hw_set;

  logic [12:0] fmt_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] fmt_wptr;
  logic [FIFO_AW:0] fmt_rptr;
  logic        fmt_fifo_empty;
  logic        fmt_fifo_full;
  logic [6:0]  fmt_fifo_level;
  logic        fmt_fifo_push;
  logic        fmt_fifo_pop;
  logic [12:0] fmt_fifo_wdata;
  logic [12:0] fmt_fifo_rdata;

  logic [7:0]  rx_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] rx_wptr;
  logic [FIFO_AW:0] rx_rptr;
  logic        rx_fifo_empty;
  logic        rx_fifo_full;
  logic [6:0]  rx_fifo_level;
  logic        rx_fifo_push;
  logic        rx_fifo_pop;
  logic [7:0]  rx_fifo_wdata;
  logic [7:0]  rx_fifo_rdata;

  logic [7:0]  tx_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] tx_wptr;
  logic [FIFO_AW:0] tx_rptr;
  logic        tx_fifo_empty;
  logic        tx_fifo_full;
  logic [6:0]  tx_fifo_level;
  logic        tx_fifo_push;
  logic        tx_fifo_pop;
  logic [7:0]  tx_fifo_wdata;
  logic [7:0]  tx_fifo_rdata;

  logic [9:0]  acq_fifo_mem [FIFO_DEPTH];
  logic [FIFO_AW:0] acq_wptr;
  logic [FIFO_AW:0] acq_rptr;
  logic        acq_fifo_empty;
  logic        acq_fifo_full;
  logic [6:0]  acq_fifo_level;
  logic        acq_fifo_push;
  logic        acq_fifo_pop;
  logic [9:0]  acq_fifo_wdata;
  logic [9:0]  acq_fifo_rdata;

  logic        fifo_ctrl_fmt_rst;
  logic        fifo_ctrl_rx_rst;
  logic        fifo_ctrl_tx_rst;
  logic        fifo_ctrl_acq_rst;

  logic        scl_in;
  logic        sda_in;
  logic        scl_in_q;
  logic        sda_in_q;
  logic        scl_in_qq;
  logic        sda_in_qq;

  logic        host_scl_oe;
  logic        host_sda_oe;
  logic        tgt_scl_oe;
  logic        tgt_sda_oe;

  host_state_e host_state;
  tgt_state_e  tgt_state;

  logic [15:0] host_timing_cnt;
  logic [3:0]  host_bit_idx;
  logic [7:0]  host_shift_reg;
  logic        host_ack_received;
  logic [7:0]  host_read_byte_cnt;
  logic [7:0]  host_read_shift;
  logic        host_read_rcont;
  logic        host_read_stop;
  logic        host_cmd_start;
  logic        host_cmd_stop;
  logic        host_cmd_readb;
  logic        host_cmd_rcont;
  logic        host_cmd_nakok;
  logic [7:0]  host_cmd_byte;
  logic        host_arb_lost;

  logic [6:0]  tgt_addr_shift;
  logic        tgt_rw_bit;
  logic [3:0]  tgt_bit_idx;
  logic [7:0]  tgt_rx_shift;
  logic [7:0]  tgt_tx_shift;
  logic        tgt_addr_match;
  logic        tgt_stretch_needed;

  logic [19:0] host_timeout_cnt;
  logic        host_timeout_event;
  logic        bus_active;

  logic        tl_req_valid;
  logic        tl_req_write;
  logic [31:0] tl_req_addr;
  logic [31:0] tl_req_wdata;
  logic [3:0]  tl_req_mask;
  logic [7:0]  tl_req_source;
  logic [31:0] tl_rsp_rdata;
  logic        tl_rsp_error;
  logic        tl_rsp_pending;

  always_comb begin
    tl_req_valid  = tl_a_valid_i & tl_a_ready_o;
    tl_req_write  = (tl_a_opcode_i == TL_OP_PUT_FULL) ||
                    (tl_a_opcode_i == TL_OP_PUT_PARTIAL);
    tl_req_addr   = {tl_a_address_i[31:2], 2'b00};
    tl_req_wdata  = tl_a_data_i;
    tl_req_mask   = tl_a_mask_i;
    tl_req_source = tl_a_source_i;
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
        tl_d_opcode_o  <= tl_req_write ? TL_OP_ACCESS_ACK : TL_OP_ACCESS_ACK_DATA;
        tl_d_data_o    <= tl_rsp_rdata;
        tl_d_source_o  <= tl_req_source;
        tl_d_error_o   <= tl_rsp_error;
      end
    end
  end

  always_comb begin
    tl_rsp_rdata   = 32'h0;
    tl_rsp_error   = 1'b0;
    fmt_fifo_push  = 1'b0;
    fmt_fifo_wdata = 13'h0;
    rx_fifo_pop    = 1'b0;
    tx_fifo_push   = 1'b0;
    tx_fifo_wdata  = 8'h0;
    acq_fifo_pop   = 1'b0;

    if (tl_req_valid) begin
      if (tl_req_write) begin
        case (tl_req_addr)
          ADDR_CTRL,
          ADDR_FDATA,
          ADDR_FIFO_CTRL,
          ADDR_OVRD,
          ADDR_TIMING0,
          ADDR_TIMING1,
          ADDR_TIMING2,
          ADDR_TIMING3,
          ADDR_TIMING4,
          ADDR_TARGET_ID,
          ADDR_TXDATA,
          ADDR_HOST_TIMEOUT_CTRL,
          ADDR_INTR_STATE,
          ADDR_INTR_ENABLE,
          ADDR_INTR_TEST: ;
          default: tl_rsp_error = 1'b1;
        endcase

        if (tl_req_addr == ADDR_FDATA) begin
          fmt_fifo_push  = 1'b1;
          fmt_fifo_wdata = tl_req_wdata[12:0];
        end

        if (tl_req_addr == ADDR_TXDATA) begin
          tx_fifo_push  = 1'b1;
          tx_fifo_wdata = tl_req_wdata[7:0];
        end
      end else begin
        case (tl_req_addr)
          ADDR_CTRL:              tl_rsp_rdata = ctrl_reg;
          ADDR_STATUS:            tl_rsp_rdata = {22'b0,
                                                   tgt_stretch_needed,
                                                   bus_active,
                                                   tgt_state == TGT_IDLE,
                                                   host_state == HOST_IDLE,
                                                   rx_fifo_empty, rx_fifo_full,
                                                   tx_fifo_empty, tx_fifo_full,
                                                   fmt_fifo_empty, fmt_fifo_full};
          ADDR_RDATA: begin
            tl_rsp_rdata = {24'h0, rx_fifo_rdata};
            rx_fifo_pop  = ~rx_fifo_empty;
          end
          ADDR_FDATA: begin
            tl_rsp_rdata = 32'h0;
            tl_rsp_error = 1'b1;
          end
          ADDR_FIFO_CTRL:         tl_rsp_rdata = 32'h0;
          ADDR_FIFO_STATUS:       tl_rsp_rdata = {4'b0, acq_fifo_level, tx_fifo_level,
                                                   rx_fifo_level, fmt_fifo_level};
          ADDR_OVRD:              tl_rsp_rdata = {29'b0, ovrd_sdaval, ovrd_sclval, ovrd_txovrden};
          ADDR_TIMING0:           tl_rsp_rdata = {timing_thigh, timing_tlow};
          ADDR_TIMING1:           tl_rsp_rdata = {timing_t_r, timing_t_f};
          ADDR_TIMING2:           tl_rsp_rdata = {timing_tsu_sta, timing_thd_sta};
          ADDR_TIMING3:           tl_rsp_rdata = {timing_tsu_dat, timing_thd_dat};
          ADDR_TIMING4:           tl_rsp_rdata = {timing_tsu_sto, timing_t_buf};
          ADDR_TARGET_ID:         tl_rsp_rdata = {18'b0, target_mask, target_address};
          ADDR_ACQDATA: begin
            tl_rsp_rdata = {22'h0, acq_fifo_rdata};
            acq_fifo_pop = ~acq_fifo_empty;
          end
          ADDR_TXDATA: begin
            tl_rsp_rdata = 32'h0;
            tl_rsp_error = 1'b1;
          end
          ADDR_HOST_TIMEOUT_CTRL: tl_rsp_rdata = {11'b0, host_timeout_en, host_timeout_val};
          ADDR_INTR_STATE:        tl_rsp_rdata = {16'b0, intr_state};
          ADDR_INTR_ENABLE:       tl_rsp_rdata = {16'b0, intr_enable};
          ADDR_INTR_TEST:         tl_rsp_rdata = 32'h0;
          default:                tl_rsp_error = 1'b1;
        endcase
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      ctrl_reg           <= 32'h0;
      ctrl_host_enable   <= 1'b0;
      ctrl_target_enable <= 1'b0;
      ctrl_line_loopback <= 1'b0;
    end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_CTRL) begin
      ctrl_reg           <= tl_req_wdata;
      ctrl_host_enable   <= tl_req_wdata[0];
      ctrl_target_enable <= tl_req_wdata[1];
      ctrl_line_loopback <= tl_req_wdata[2];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      timing_tlow    <= 16'h0;
      timing_thigh   <= 16'h0;
      timing_t_f     <= 16'h0;
      timing_t_r     <= 16'h0;
      timing_thd_sta <= 16'h0;
      timing_tsu_sta <= 16'h0;
      timing_thd_dat <= 16'h0;
      timing_tsu_dat <= 16'h0;
      timing_t_buf   <= 16'h0;
      timing_tsu_sto <= 16'h0;
    end else if (tl_req_valid && tl_req_write) begin
      case (tl_req_addr)
        ADDR_TIMING0: begin
          timing_tlow  <= tl_req_wdata[15:0];
          timing_thigh <= tl_req_wdata[31:16];
        end
        ADDR_TIMING1: begin
          timing_t_f <= tl_req_wdata[15:0];
          timing_t_r <= tl_req_wdata[31:16];
        end
        ADDR_TIMING2: begin
          timing_thd_sta <= tl_req_wdata[15:0];
          timing_tsu_sta <= tl_req_wdata[31:16];
        end
        ADDR_TIMING3: begin
          timing_thd_dat <= tl_req_wdata[15:0];
          timing_tsu_dat <= tl_req_wdata[31:16];
        end
        ADDR_TIMING4: begin
          timing_t_buf   <= tl_req_wdata[15:0];
          timing_tsu_sto <= tl_req_wdata[31:16];
        end
        default: ;
      endcase
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      target_address <= 7'h0;
      target_mask    <= 7'h0;
    end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_TARGET_ID) begin
      target_address <= tl_req_wdata[6:0];
      target_mask    <= tl_req_wdata[13:7];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      ovrd_txovrden <= 1'b0;
      ovrd_sclval   <= 1'b1;
      ovrd_sdaval   <= 1'b1;
    end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_OVRD) begin
      ovrd_txovrden <= tl_req_wdata[0];
      ovrd_sclval   <= tl_req_wdata[1];
      ovrd_sdaval   <= tl_req_wdata[2];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      host_timeout_val <= 20'h0;
      host_timeout_en  <= 1'b0;
    end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_HOST_TIMEOUT_CTRL) begin
      host_timeout_val <= tl_req_wdata[19:0];
      host_timeout_en  <= tl_req_wdata[20];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fifo_ctrl_fmt_rst <= 1'b0;
      fifo_ctrl_rx_rst  <= 1'b0;
      fifo_ctrl_tx_rst  <= 1'b0;
      fifo_ctrl_acq_rst <= 1'b0;
    end else begin
      if (fifo_ctrl_fmt_rst) fifo_ctrl_fmt_rst <= 1'b0;
      if (fifo_ctrl_rx_rst)  fifo_ctrl_rx_rst  <= 1'b0;
      if (fifo_ctrl_tx_rst)  fifo_ctrl_tx_rst  <= 1'b0;
      if (fifo_ctrl_acq_rst) fifo_ctrl_acq_rst <= 1'b0;

      if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_FIFO_CTRL) begin
        fifo_ctrl_fmt_rst <= tl_req_wdata[0];
        fifo_ctrl_rx_rst  <= tl_req_wdata[1];
        fifo_ctrl_tx_rst  <= tl_req_wdata[2];
        fifo_ctrl_acq_rst <= tl_req_wdata[3];
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
    fmt_fifo_empty = (fmt_wptr == fmt_rptr);
    fmt_fifo_full  = (fmt_wptr[FIFO_AW] != fmt_rptr[FIFO_AW]) &&
                     (fmt_wptr[FIFO_AW-1:0] == fmt_rptr[FIFO_AW-1:0]);
    fmt_fifo_level = fmt_wptr - fmt_rptr;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fmt_wptr <= '0;
    end else if (fifo_ctrl_fmt_rst) begin
      fmt_wptr <= '0;
    end else if (fmt_fifo_push && !fmt_fifo_full) begin
      fmt_fifo_mem[fmt_wptr[FIFO_AW-1:0]] <= fmt_fifo_wdata;
      fmt_wptr <= fmt_wptr + 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fmt_rptr <= '0;
    end else if (fifo_ctrl_fmt_rst) begin
      fmt_rptr <= '0;
    end else if (fmt_fifo_pop && !fmt_fifo_empty) begin
      fmt_rptr <= fmt_rptr + 1'b1;
    end
  end

  always_comb begin
    fmt_fifo_rdata = fmt_fifo_mem[fmt_rptr[FIFO_AW-1:0]];
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
    acq_fifo_empty = (acq_wptr == acq_rptr);
    acq_fifo_full  = (acq_wptr[FIFO_AW] != acq_rptr[FIFO_AW]) &&
                     (acq_wptr[FIFO_AW-1:0] == acq_rptr[FIFO_AW-1:0]);
    acq_fifo_level = acq_wptr - acq_rptr;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      acq_wptr <= '0;
    end else if (fifo_ctrl_acq_rst) begin
      acq_wptr <= '0;
    end else if (acq_fifo_push && !acq_fifo_full) begin
      acq_fifo_mem[acq_wptr[FIFO_AW-1:0]] <= acq_fifo_wdata;
      acq_wptr <= acq_wptr + 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      acq_rptr <= '0;
    end else if (fifo_ctrl_acq_rst) begin
      acq_rptr <= '0;
    end else if (acq_fifo_pop && !acq_fifo_empty) begin
      acq_rptr <= acq_rptr + 1'b1;
    end
  end

  always_comb begin
    acq_fifo_rdata = acq_fifo_mem[acq_rptr[FIFO_AW-1:0]];
  end

  always_comb begin
    if (ctrl_line_loopback) begin
      scl_in = ~scl_oe_o;
      sda_in = ~sda_oe_o;
    end else begin
      scl_in = scl_i;
      sda_in = sda_i;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      scl_in_q  <= 1'b1;
      sda_in_q  <= 1'b1;
      scl_in_qq <= 1'b1;
      sda_in_qq <= 1'b1;
    end else begin
      scl_in_q  <= scl_in;
      sda_in_q  <= sda_in;
      scl_in_qq <= scl_in_q;
      sda_in_qq <= sda_in_q;
    end
  end

  logic scl_rising;
  logic scl_falling;
  logic sda_rising;
  logic sda_falling;
  logic start_det;
  logic stop_det;

  always_comb begin
    scl_rising  = ~scl_in_qq & scl_in_q;
    scl_falling = scl_in_qq & ~scl_in_q;
    sda_rising  = ~sda_in_qq & sda_in_q;
    sda_falling = sda_in_qq & ~sda_in_q;
    start_det   = scl_in_qq & scl_in_q & sda_in_qq & ~sda_in_q;
    stop_det    = scl_in_qq & scl_in_q & ~sda_in_qq & sda_in_q;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      bus_active <= 1'b0;
    end else begin
      if (start_det) begin
        bus_active <= 1'b1;
      end else if (stop_det) begin
        bus_active <= 1'b0;
      end
    end
  end

  assign scl_o = 1'b0;
  assign sda_o = 1'b0;

  always_comb begin
    if (ovrd_txovrden) begin
      scl_oe_o = ~ovrd_sclval;
      sda_oe_o = ~ovrd_sdaval;
    end else begin
      scl_oe_o = host_scl_oe | tgt_scl_oe;
      sda_oe_o = host_sda_oe | tgt_sda_oe;
    end
  end

  logic        fmt_pop_req;
  assign fmt_fifo_pop = fmt_pop_req;

  always_comb begin
    host_cmd_byte  = fmt_fifo_rdata[7:0];
    host_cmd_start = fmt_fifo_rdata[8];
    host_cmd_stop  = fmt_fifo_rdata[9];
    host_cmd_readb = fmt_fifo_rdata[10];
    host_cmd_rcont = fmt_fifo_rdata[11];
    host_cmd_nakok = fmt_fifo_rdata[12];
  end

  logic host_timing_done;
  always_comb begin
    host_timing_done = (host_timing_cnt == 16'h0);
  end

  logic host_scl_drive_low;
  logic host_sda_drive_low;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      host_state         <= HOST_IDLE;
      host_timing_cnt    <= 16'h0;
      host_bit_idx       <= 4'h0;
      host_shift_reg     <= 8'h0;
      host_ack_received  <= 1'b0;
      host_read_byte_cnt <= 8'h0;
      host_read_shift    <= 8'h0;
      host_read_rcont    <= 1'b0;
      host_read_stop     <= 1'b0;
      host_arb_lost      <= 1'b0;
      host_scl_drive_low <= 1'b0;
      host_sda_drive_low <= 1'b0;
      fmt_pop_req        <= 1'b0;
    end else begin
      fmt_pop_req   <= 1'b0;
      host_arb_lost <= 1'b0;

      if (host_timing_cnt > 16'h0) begin
        host_timing_cnt <= host_timing_cnt - 16'h1;
      end

      case (host_state)
        HOST_IDLE: begin
          host_scl_drive_low <= 1'b0;
          host_sda_drive_low <= 1'b0;
          host_bit_idx       <= 4'h0;
          if (ctrl_host_enable && !fmt_fifo_empty) begin
            if (host_cmd_start) begin
              host_sda_drive_low <= 1'b0;
              host_scl_drive_low <= 1'b0;
              host_state         <= HOST_START;
              host_timing_cnt    <= timing_tsu_sta;
              host_shift_reg     <= host_cmd_byte;
            end else if (host_cmd_readb) begin
              host_read_byte_cnt <= host_cmd_byte;
              host_read_rcont    <= host_cmd_rcont;
              host_read_stop     <= host_cmd_stop;
              host_state         <= HOST_READ_BYTE;
              host_bit_idx       <= 4'h0;
              host_scl_drive_low <= 1'b1;
              host_sda_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thd_dat;
              fmt_pop_req        <= 1'b1;
            end else begin
              host_shift_reg     <= host_cmd_byte;
              host_state         <= HOST_WRITE_BYTE;
              host_bit_idx       <= 4'h0;
              host_scl_drive_low <= 1'b1;
              host_sda_drive_low <= ~host_cmd_byte[7];
              host_timing_cnt    <= timing_thd_dat;
              fmt_pop_req        <= 1'b1;
            end
          end
        end

        HOST_START: begin
          if (host_timing_done) begin
            host_sda_drive_low <= 1'b1;
            host_timing_cnt    <= timing_thd_sta;
            host_state         <= HOST_ADDR_BYTE;
            host_bit_idx       <= 4'h0;
          end
        end

        HOST_ADDR_BYTE: begin
          if (host_timing_done) begin
            if (host_bit_idx == 4'h0 && host_scl_drive_low == 1'b0) begin
              host_scl_drive_low <= 1'b1;
              host_sda_drive_low <= ~host_shift_reg[7];
              host_timing_cnt    <= timing_tlow;
              host_bit_idx       <= 4'h0;
            end else if (host_scl_drive_low) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
            end else begin
              if (!host_sda_drive_low && !sda_in_q) begin
                host_arb_lost      <= 1'b1;
                host_scl_drive_low <= 1'b0;
                host_sda_drive_low <= 1'b0;
                host_state         <= HOST_IDLE;
                fmt_pop_req        <= 1'b1;
              end else begin
                host_scl_drive_low <= 1'b1;
                if (host_bit_idx < 4'd7) begin
                  host_bit_idx       <= host_bit_idx + 4'h1;
                  host_sda_drive_low <= ~host_shift_reg[6 - host_bit_idx[2:0]];
                  host_timing_cnt    <= timing_tlow;
                end else begin
                  host_sda_drive_low <= 1'b0;
                  host_timing_cnt    <= timing_tlow;
                  host_state         <= HOST_ADDR_ACK;
                  host_bit_idx       <= 4'h0;
                end
              end
            end
          end
        end

        HOST_ADDR_ACK: begin
          if (host_timing_done) begin
            if (host_scl_drive_low) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
            end else begin
              host_ack_received <= ~sda_in_q;
              host_scl_drive_low <= 1'b1;
              host_timing_cnt    <= timing_tlow;
              fmt_pop_req        <= 1'b1;

              if (sda_in_q && !host_cmd_nakok) begin
                host_state <= HOST_STOP;
              end else if (host_cmd_stop && !host_cmd_readb) begin
                host_state <= HOST_STOP;
              end else if (host_cmd_readb) begin
                host_read_byte_cnt <= host_cmd_byte;
                host_read_rcont    <= host_cmd_rcont;
                host_read_stop     <= host_cmd_stop;
                host_state         <= HOST_READ_BYTE;
                host_bit_idx       <= 4'h0;
                host_sda_drive_low <= 1'b0;
              end else begin
                host_state <= HOST_IDLE;
              end
            end
          end
        end

        HOST_WRITE_BYTE: begin
          if (host_timing_done) begin
            if (host_scl_drive_low) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
            end else begin
              if (!host_sda_drive_low && !sda_in_q) begin
                host_arb_lost      <= 1'b1;
                host_scl_drive_low <= 1'b0;
                host_sda_drive_low <= 1'b0;
                host_state         <= HOST_IDLE;
              end else begin
                host_scl_drive_low <= 1'b1;
                if (host_bit_idx < 4'd7) begin
                  host_bit_idx       <= host_bit_idx + 4'h1;
                  host_sda_drive_low <= ~host_shift_reg[6 - host_bit_idx[2:0]];
                  host_timing_cnt    <= timing_tlow;
                end else begin
                  host_sda_drive_low <= 1'b0;
                  host_timing_cnt    <= timing_tlow;
                  host_state         <= HOST_WRITE_ACK;
                  host_bit_idx       <= 4'h0;
                end
              end
            end
          end
        end

        HOST_WRITE_ACK: begin
          if (host_timing_done) begin
            if (host_scl_drive_low) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
            end else begin
              host_ack_received  <= ~sda_in_q;
              host_scl_drive_low <= 1'b1;
              host_timing_cnt    <= timing_tlow;

              if (sda_in_q && !host_cmd_nakok) begin
                host_state <= HOST_STOP;
              end else if (!fmt_fifo_empty) begin
                if (fmt_fifo_rdata[8]) begin
                  host_state <= HOST_RSTART_SETUP;
                end else if (fmt_fifo_rdata[10]) begin
                  host_read_byte_cnt <= fmt_fifo_rdata[7:0];
                  host_read_rcont    <= fmt_fifo_rdata[11];
                  host_read_stop     <= fmt_fifo_rdata[9];
                  host_state         <= HOST_READ_BYTE;
                  host_bit_idx       <= 4'h0;
                  host_sda_drive_low <= 1'b0;
                  fmt_pop_req        <= 1'b1;
                end else begin
                  host_shift_reg     <= fmt_fifo_rdata[7:0];
                  host_sda_drive_low <= ~fmt_fifo_rdata[7];
                  host_state         <= HOST_WRITE_BYTE;
                  host_bit_idx       <= 4'h0;
                  fmt_pop_req        <= 1'b1;
                end
              end else begin
                host_state <= HOST_STOP;
              end
            end
          end
        end

        HOST_READ_BYTE: begin
          if (host_timing_done) begin
            if (host_scl_drive_low) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
              host_sda_drive_low <= 1'b0;
            end else begin
              host_read_shift <= {host_read_shift[6:0], sda_in_q};
              host_scl_drive_low <= 1'b1;
              host_timing_cnt    <= timing_tlow;

              if (host_bit_idx < 4'd7) begin
                host_bit_idx <= host_bit_idx + 4'h1;
              end else begin
                host_state   <= HOST_READ_ACK;
                host_bit_idx <= 4'h0;
              end
            end
          end
        end

        HOST_READ_ACK: begin
          if (host_timing_done) begin
            if (host_scl_drive_low && host_bit_idx == 4'h0) begin
              if (host_read_rcont) begin
                host_sda_drive_low <= 1'b1;
              end else begin
                host_sda_drive_low <= 1'b0;
              end
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_thigh;
              host_bit_idx       <= 4'h1;
            end else begin
              host_scl_drive_low <= 1'b1;
              host_sda_drive_low <= 1'b0;
              host_timing_cnt    <= timing_tlow;
              host_bit_idx       <= 4'h0;

              if (host_read_byte_cnt > 8'h1) begin
                host_read_byte_cnt <= host_read_byte_cnt - 8'h1;
                host_state <= HOST_READ_BYTE;
              end else if (host_read_stop) begin
                host_state <= HOST_STOP;
              end else if (!fmt_fifo_empty) begin
                if (fmt_fifo_rdata[8]) begin
                  host_state <= HOST_RSTART_SETUP;
                end else begin
                  host_state <= HOST_IDLE;
                end
              end else begin
                host_state <= HOST_IDLE;
              end
            end
          end
        end

        HOST_STOP: begin
          if (host_timing_done) begin
            if (host_bit_idx == 4'h0) begin
              host_scl_drive_low <= 1'b1;
              host_sda_drive_low <= 1'b1;
              host_timing_cnt    <= timing_tlow;
              host_bit_idx       <= 4'h1;
            end else if (host_bit_idx == 4'h1) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_tsu_sto;
              host_bit_idx       <= 4'h2;
            end else begin
              host_sda_drive_low <= 1'b0;
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_t_buf;
              host_state         <= HOST_WAIT_BUS_FREE;
              host_bit_idx       <= 4'h0;
            end
          end
        end

        HOST_RSTART_SETUP: begin
          if (host_timing_done) begin
            if (host_bit_idx == 4'h0) begin
              host_sda_drive_low <= 1'b0;
              host_scl_drive_low <= 1'b1;
              host_timing_cnt    <= timing_tlow;
              host_bit_idx       <= 4'h1;
            end else if (host_bit_idx == 4'h1) begin
              host_scl_drive_low <= 1'b0;
              host_timing_cnt    <= timing_tsu_sta;
              host_bit_idx       <= 4'h2;
            end else begin
              host_sda_drive_low <= 1'b1;
              host_timing_cnt    <= timing_thd_sta;
              host_shift_reg     <= fmt_fifo_rdata[7:0];
              fmt_pop_req        <= 1'b1;
              host_state         <= HOST_ADDR_BYTE;
              host_bit_idx       <= 4'h0;
            end
          end
        end

        HOST_WAIT_BUS_FREE: begin
          if (host_timing_done) begin
            host_state <= HOST_IDLE;
          end
        end

        default: host_state <= HOST_IDLE;
      endcase

      if (!ctrl_host_enable) begin
        host_state         <= HOST_IDLE;
        host_scl_drive_low <= 1'b0;
        host_sda_drive_low <= 1'b0;
        host_timing_cnt    <= 16'h0;
      end
    end
  end

  assign host_scl_oe = host_scl_drive_low;
  assign host_sda_oe = host_sda_drive_low;

  logic rx_push_valid;
  logic [7:0] rx_push_data;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      rx_push_valid <= 1'b0;
      rx_push_data  <= 8'h0;
    end else begin
      rx_push_valid <= 1'b0;
      if (host_state == HOST_READ_ACK && host_timing_done &&
          host_bit_idx != 4'h0) begin
        rx_push_valid <= 1'b1;
        rx_push_data  <= host_read_shift;
      end
    end
  end

  assign rx_fifo_push  = rx_push_valid;
  assign rx_fifo_wdata = rx_push_data;

  logic tgt_scl_drive_low;
  logic tgt_sda_drive_low;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tgt_state          <= TGT_IDLE;
      tgt_addr_shift     <= 7'h0;
      tgt_rw_bit         <= 1'b0;
      tgt_bit_idx        <= 4'h0;
      tgt_rx_shift       <= 8'h0;
      tgt_tx_shift       <= 8'h0;
      tgt_addr_match     <= 1'b0;
      tgt_stretch_needed <= 1'b0;
      tgt_scl_drive_low  <= 1'b0;
      tgt_sda_drive_low  <= 1'b0;
      acq_fifo_push      <= 1'b0;
      acq_fifo_wdata     <= 10'h0;
      tx_fifo_pop        <= 1'b0;
    end else begin
      acq_fifo_push  <= 1'b0;
      tx_fifo_pop    <= 1'b0;

      if (stop_det && tgt_state != TGT_IDLE) begin
        if (tgt_addr_match) begin
          acq_fifo_push  <= 1'b1;
          acq_fifo_wdata <= {2'b10, 8'h0};
        end
        tgt_state          <= TGT_IDLE;
        tgt_scl_drive_low  <= 1'b0;
        tgt_sda_drive_low  <= 1'b0;
        tgt_stretch_needed <= 1'b0;
      end else begin

        case (tgt_state)
          TGT_IDLE: begin
            tgt_scl_drive_low  <= 1'b0;
            tgt_sda_drive_low  <= 1'b0;
            tgt_bit_idx        <= 4'h0;
            tgt_addr_match     <= 1'b0;
            tgt_stretch_needed <= 1'b0;
            if (ctrl_target_enable && start_det) begin
              tgt_state   <= TGT_ADDR_RECV;
              tgt_bit_idx <= 4'h0;
            end
          end

          TGT_ADDR_RECV: begin
            if (start_det) begin
              tgt_bit_idx <= 4'h0;
              tgt_state   <= TGT_ADDR_RECV;
            end else if (scl_rising) begin
              if (tgt_bit_idx < 4'd7) begin
                tgt_addr_shift <= {tgt_addr_shift[5:0], sda_in_q};
                tgt_bit_idx    <= tgt_bit_idx + 4'h1;
              end else begin
                tgt_rw_bit  <= sda_in_q;
                tgt_bit_idx <= 4'h0;

                tgt_addr_match <= ((tgt_addr_shift ^ target_address) & target_mask) == 7'h0;
              end
            end else if (scl_falling && tgt_bit_idx == 4'h0 && tgt_addr_shift != 7'h0) begin
              if (tgt_addr_match) begin
                tgt_state         <= TGT_ADDR_ACK;
                tgt_sda_drive_low <= 1'b1;

                acq_fifo_push  <= 1'b1;
                acq_fifo_wdata <= {2'b01, tgt_addr_shift[6:0], tgt_rw_bit};
              end else begin
                tgt_state         <= TGT_IDLE;
                tgt_sda_drive_low <= 1'b0;
              end
            end
          end

          TGT_ADDR_ACK: begin
            if (scl_falling) begin
              tgt_sda_drive_low <= 1'b0;
              if (tgt_rw_bit) begin
                if (tx_fifo_empty) begin
                  tgt_state          <= TGT_STRETCH;
                  tgt_scl_drive_low  <= 1'b1;
                  tgt_stretch_needed <= 1'b1;
                end else begin
                  tgt_tx_shift      <= tx_fifo_rdata;
                  tx_fifo_pop       <= 1'b1;
                  tgt_state         <= TGT_DATA_TX;
                  tgt_bit_idx       <= 4'h0;
                  tgt_sda_drive_low <= ~tx_fifo_rdata[7];
                end
              end else begin
                tgt_state   <= TGT_DATA_RX;
                tgt_bit_idx <= 4'h0;
              end
            end
          end

          TGT_DATA_RX: begin
            if (start_det) begin
              if (tgt_addr_match) begin
                acq_fifo_push  <= 1'b1;
                acq_fifo_wdata <= {2'b11, 8'h0};
              end
              tgt_bit_idx <= 4'h0;
              tgt_state   <= TGT_ADDR_RECV;
            end else if (scl_rising) begin
              tgt_rx_shift <= {tgt_rx_shift[6:0], sda_in_q};
              tgt_bit_idx  <= tgt_bit_idx + 4'h1;
            end else if (scl_falling && tgt_bit_idx == 4'd8) begin
              tgt_bit_idx <= 4'h0;
              if (acq_fifo_full) begin
                tgt_state          <= TGT_STRETCH;
                tgt_scl_drive_low  <= 1'b1;
                tgt_stretch_needed <= 1'b1;
              end else begin
                acq_fifo_push     <= 1'b1;
                acq_fifo_wdata    <= {2'b00, tgt_rx_shift};
                tgt_state         <= TGT_DATA_RX_ACK;
                tgt_sda_drive_low <= 1'b1;
              end
            end
          end

          TGT_DATA_RX_ACK: begin
            if (start_det) begin
              tgt_sda_drive_low <= 1'b0;
              if (tgt_addr_match) begin
                acq_fifo_push  <= 1'b1;
                acq_fifo_wdata <= {2'b11, 8'h0};
              end
              tgt_bit_idx <= 4'h0;
              tgt_state   <= TGT_ADDR_RECV;
            end else if (scl_falling) begin
              tgt_sda_drive_low <= 1'b0;
              tgt_state         <= TGT_DATA_RX;
              tgt_bit_idx       <= 4'h0;
            end
          end

          TGT_DATA_TX: begin
            if (start_det) begin
              tgt_sda_drive_low <= 1'b0;
              if (tgt_addr_match) begin
                acq_fifo_push  <= 1'b1;
                acq_fifo_wdata <= {2'b11, 8'h0};
              end
              tgt_bit_idx <= 4'h0;
              tgt_state   <= TGT_ADDR_RECV;
            end else if (scl_falling) begin
              if (tgt_bit_idx < 4'd7) begin
                tgt_bit_idx       <= tgt_bit_idx + 4'h1;
                tgt_sda_drive_low <= ~tgt_tx_shift[6 - tgt_bit_idx[2:0]];
              end else begin
                tgt_sda_drive_low <= 1'b0;
                tgt_state         <= TGT_DATA_TX_ACK;
                tgt_bit_idx       <= 4'h0;
              end
            end
          end

          TGT_DATA_TX_ACK: begin
            if (start_det) begin
              if (tgt_addr_match) begin
                acq_fifo_push  <= 1'b1;
                acq_fifo_wdata <= {2'b11, 8'h0};
              end
              tgt_bit_idx <= 4'h0;
              tgt_state   <= TGT_ADDR_RECV;
            end else if (scl_rising) begin
              if (sda_in_q) begin
                tgt_state <= TGT_IDLE;
              end
            end else if (scl_falling) begin
              if (tx_fifo_empty) begin
                tgt_state          <= TGT_STRETCH;
                tgt_scl_drive_low  <= 1'b1;
                tgt_stretch_needed <= 1'b1;
              end else begin
                tgt_tx_shift      <= tx_fifo_rdata;
                tx_fifo_pop       <= 1'b1;
                tgt_state         <= TGT_DATA_TX;
                tgt_bit_idx       <= 4'h0;
                tgt_sda_drive_low <= ~tx_fifo_rdata[7];
              end
            end
          end

          TGT_STRETCH: begin
            tgt_scl_drive_low <= 1'b1;
            if (tgt_rw_bit && !tx_fifo_empty) begin
              tgt_scl_drive_low  <= 1'b0;
              tgt_stretch_needed <= 1'b0;
              tgt_tx_shift       <= tx_fifo_rdata;
              tx_fifo_pop        <= 1'b1;
              tgt_state          <= TGT_DATA_TX;
              tgt_bit_idx        <= 4'h0;
              tgt_sda_drive_low  <= ~tx_fifo_rdata[7];
            end else if (!tgt_rw_bit && !acq_fifo_full) begin
              tgt_scl_drive_low  <= 1'b0;
              tgt_stretch_needed <= 1'b0;
              acq_fifo_push      <= 1'b1;
              acq_fifo_wdata     <= {2'b00, tgt_rx_shift};
              tgt_state          <= TGT_DATA_RX_ACK;
              tgt_sda_drive_low  <= 1'b1;
            end
          end

          TGT_STOP_DET: begin
            tgt_state          <= TGT_IDLE;
            tgt_scl_drive_low  <= 1'b0;
            tgt_sda_drive_low  <= 1'b0;
            tgt_stretch_needed <= 1'b0;
          end

          default: tgt_state <= TGT_IDLE;
        endcase
      end

      if (!ctrl_target_enable) begin
        tgt_state          <= TGT_IDLE;
        tgt_scl_drive_low  <= 1'b0;
        tgt_sda_drive_low  <= 1'b0;
        tgt_stretch_needed <= 1'b0;
      end
    end
  end

  assign tgt_scl_oe = tgt_scl_drive_low;
  assign tgt_sda_oe = tgt_sda_drive_low;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      host_timeout_cnt   <= 20'h0;
      host_timeout_event <= 1'b0;
    end else begin
      host_timeout_event <= 1'b0;
      if (host_timeout_en) begin
        if (!scl_in_q) begin
          if (host_timeout_cnt < host_timeout_val) begin
            host_timeout_cnt <= host_timeout_cnt + 20'h1;
          end else begin
            host_timeout_event <= 1'b1;
          end
        end else begin
          host_timeout_cnt <= 20'h0;
        end
      end else begin
        host_timeout_cnt <= 20'h0;
      end
    end
  end

  logic sda_interference_det;
  logic scl_interference_det;
  logic sda_unstable_det;

  always_comb begin
    scl_interference_det = ctrl_host_enable && !host_scl_drive_low &&
                           (host_state != HOST_IDLE) && !scl_in_q;

    sda_interference_det = ctrl_host_enable && !host_sda_drive_low &&
                           (host_state == HOST_WRITE_BYTE || host_state == HOST_ADDR_BYTE) &&
                           !sda_in_q && scl_in_q;

    sda_unstable_det = scl_in_q && scl_in_qq &&
                       (sda_in_q != sda_in_qq) &&
                       !start_det && !stop_det &&
                       bus_active;
  end

  logic fmt_overflow_det;
  logic rx_overflow_det;
  logic tx_overflow_det;
  logic nak_det;
  logic trans_complete_det;

  always_comb begin
    fmt_overflow_det = fmt_fifo_push && fmt_fifo_full;
    rx_overflow_det  = rx_fifo_push && rx_fifo_full;
    tx_overflow_det  = tx_fifo_push && tx_fifo_full;

    nak_det = (host_state == HOST_ADDR_ACK || host_state == HOST_WRITE_ACK) &&
              host_timing_done && !host_scl_drive_low &&
              sda_in_q && !host_cmd_nakok;

    trans_complete_det = (host_state != HOST_IDLE) &&
                         fmt_fifo_empty &&
                         (host_state == HOST_WAIT_BUS_FREE && host_timing_done);
  end

  always_comb begin
    intr_hw_set = '0;

    if (fmt_fifo_level <= 7'd1 && ctrl_host_enable)
      intr_hw_set[0] = 1'b1;

    if (rx_fifo_level >= 7'd1 && ctrl_host_enable)
      intr_hw_set[1] = 1'b1;

    if (acq_fifo_level >= 7'd1 && ctrl_target_enable)
      intr_hw_set[2] = 1'b1;

    if (rx_overflow_det)
      intr_hw_set[3] = 1'b1;

    if (nak_det)
      intr_hw_set[4] = 1'b1;

    if (scl_interference_det)
      intr_hw_set[5] = 1'b1;

    if (sda_interference_det)
      intr_hw_set[6] = 1'b1;

    if (tgt_stretch_needed && host_timeout_event)
      intr_hw_set[7] = 1'b1;

    if (sda_unstable_det)
      intr_hw_set[8] = 1'b1;

    if (trans_complete_det)
      intr_hw_set[9] = 1'b1;

    if (tx_fifo_empty && ctrl_target_enable)
      intr_hw_set[10] = 1'b1;

    if (tx_fifo_level <= 7'd1 && ctrl_target_enable)
      intr_hw_set[11] = 1'b1;

    if (acq_fifo_full && ctrl_target_enable)
      intr_hw_set[12] = 1'b1;

    if (stop_det && tgt_addr_match && ctrl_target_enable)
      intr_hw_set[13] = 1'b1;

    if (host_timeout_event)
      intr_hw_set[14] = 1'b1;

    if (host_arb_lost)
      intr_hw_set[15] = 1'b1;
  end

  assign alert_o = 1'b0;

endmodule
