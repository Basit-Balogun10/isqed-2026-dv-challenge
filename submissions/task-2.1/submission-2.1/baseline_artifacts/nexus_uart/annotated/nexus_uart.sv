//      // verilator_coverage annotation
        module nexus_uart
          import dv_common_pkg::*;
        (
 000131   input  logic        clk_i,
%000001   input  logic        rst_ni,
        
 000015   input  logic        tl_a_valid_i,
%000001   output logic        tl_a_ready_o,
~000011   input  logic [2:0]  tl_a_opcode_i,
%000007   input  logic [31:0] tl_a_address_i,
%000002   input  logic [31:0] tl_a_data_i,
%000001   input  logic [3:0]  tl_a_mask_i,
%000000   input  logic [7:0]  tl_a_source_i,
%000001   input  logic [1:0]  tl_a_size_i,
        
 000015   output logic        tl_d_valid_o,
%000001   input  logic        tl_d_ready_i,
%000005   output logic [2:0]  tl_d_opcode_o,
%000004   output logic [31:0] tl_d_data_o,
%000000   output logic [7:0]  tl_d_source_o,
%000003   output logic        tl_d_error_o,
        
%000001   output logic        uart_tx_o,
%000000   input  logic        uart_rx_i,
%000000   output logic [6:0]  intr_o,
%000000   output logic        alert_o
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
        
%000001   logic        ctrl_tx_enable;
%000000   logic        ctrl_rx_enable;
%000000   logic [15:0] ctrl_baud_divisor;
%000000   logic [1:0]  ctrl_parity_mode;
%000000   logic        ctrl_stop_bits;
%000000   logic        ctrl_loopback_en;
%000001   logic [31:0] ctrl_reg;
        
%000001   logic [4:0]  fifo_ctrl_tx_watermark;
%000001   logic [4:0]  fifo_ctrl_rx_watermark;
%000000   logic        fifo_ctrl_tx_rst;
%000000   logic        fifo_ctrl_rx_rst;
        
%000001   logic [NUM_IRQS-1:0] intr_state;
%000000   logic [NUM_IRQS-1:0] intr_enable;
%000002   logic [NUM_IRQS-1:0] intr_hw_set;
        
%000001   logic [7:0]  tx_fifo_mem [FIFO_DEPTH];
%000001   logic [FIFO_AW:0] tx_wptr;
%000001   logic [FIFO_AW:0] tx_rptr;
%000002   logic        tx_fifo_empty;
%000000   logic        tx_fifo_full;
%000001   logic [5:0]  tx_fifo_level;
%000001   logic        tx_fifo_push;
%000001   logic        tx_fifo_pop;
%000001   logic [7:0]  tx_fifo_wdata;
%000001   logic [7:0]  tx_fifo_rdata;
        
%000000   logic [7:0]  rx_fifo_mem [FIFO_DEPTH];
%000000   logic [FIFO_AW:0] rx_wptr;
%000000   logic [FIFO_AW:0] rx_rptr;
%000001   logic        rx_fifo_empty;
%000000   logic        rx_fifo_full;
%000000   logic [5:0]  rx_fifo_level;
%000000   logic        rx_fifo_push;
%000000   logic        rx_fifo_pop;
%000000   logic [7:0]  rx_fifo_wdata;
%000000   logic [7:0]  rx_fifo_rdata;
        
%000000   logic        rx_overrun_sticky;
%000000   logic        rx_parity_err_sticky;
%000000   logic        rx_frame_err_sticky;
        
%000001   tx_state_e   tx_state;
~000045   logic [15:0] tx_baud_cnt;
%000000   logic        tx_baud_tick;
%000000   logic [2:0]  tx_bit_idx;
%000001   logic [7:0]  tx_shift_reg;
%000000   logic        tx_parity_bit;
        
%000000   rx_state_e   rx_state;
%000000   logic [15:0] rx_baud_cnt;
%000000   logic        rx_os_tick;
%000000   logic [3:0]  rx_os_cnt;
%000000   logic [2:0]  rx_bit_idx;
%000000   logic [7:0]  rx_shift_reg;
%000000   logic        rx_parity_calc;
        
%000001   logic        rx_expected_parity;
        
%000000   logic        rx_serial_in;
%000001   logic        rx_serial_q;
%000001   logic        rx_serial_qq;
        
%000000   logic [31:0] rx_timeout_cnt;
%000000   logic        rx_timeout_event;
%000000   logic [31:0] rx_timeout_thresh;
%000000   logic        rx_active;
        
 000015   logic        tl_req_valid;
 000012   logic        tl_req_write;
%000007   logic [31:0] tl_req_addr;
%000002   logic [31:0] tl_req_wdata;
%000004   logic [31:0] tl_rsp_rdata;
%000004   logic        tl_rsp_error;
 000015   logic        tl_rsp_pending;
        
 000686   always_comb begin
~000686     tl_req_valid = tl_a_valid_i & tl_a_ready_o;
~000686     tl_req_write = (tl_a_opcode_i == 3'd0) || (tl_a_opcode_i == 3'd1);
 000686     tl_req_addr  = {tl_a_address_i[31:2], 2'b00};
 000686     tl_req_wdata = tl_a_data_i;
          end
        
 000686   always_comb begin
~000686     tl_a_ready_o = !tl_rsp_pending || tl_d_ready_i;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tl_rsp_pending <= 1'b0;
%000005       tl_d_valid_o   <= 1'b0;
%000005       tl_d_opcode_o  <= 3'd0;
%000005       tl_d_data_o    <= 32'd0;
%000005       tl_d_source_o  <= 8'd0;
%000005       tl_d_error_o   <= 1'b0;
 000126     end else begin
 000111       if (tl_rsp_pending && tl_d_ready_i) begin
 000015         tl_rsp_pending <= 1'b0;
 000015         tl_d_valid_o   <= 1'b0;
              end
 000111       if (tl_req_valid) begin
 000015         tl_rsp_pending <= 1'b1;
 000015         tl_d_valid_o   <= 1'b1;
~000015         tl_d_opcode_o  <= tl_req_write ? 3'd0 : 3'd1;
 000015         tl_d_data_o    <= tl_rsp_rdata;
 000015         tl_d_source_o  <= tl_a_source_i;
 000015         tl_d_error_o   <= tl_rsp_error;
              end
            end
          end
        
 000686   always_comb begin
 000686     tl_rsp_rdata = 32'h0;
 000686     tl_rsp_error = 1'b0;
 000686     tx_fifo_push = 1'b0;
 000686     tx_fifo_wdata = 8'h0;
 000686     rx_fifo_pop  = 1'b0;
        
 000596     if (tl_req_valid) begin
 000066       if (tl_req_write) begin
 000024         case (tl_req_addr)
                  ADDR_CTRL,
                  ADDR_TXDATA,
                  ADDR_FIFO_CTRL,
                  ADDR_INTR_STATE,
                  ADDR_INTR_ENABLE,
 000012           ADDR_INTR_TEST: ;
                  ADDR_STATUS,
 000012           ADDR_RXDATA: tl_rsp_error = 1'b1;
%000000           default: tl_rsp_error = 1'b1;
                endcase
        
~000018         if (tl_req_addr == ADDR_TXDATA) begin
%000006           tx_fifo_push  = 1'b1;
%000006           tx_fifo_wdata = tl_req_wdata[7:0];
                end
 000066       end else begin
 000066         case (tl_req_addr)
 000012           ADDR_CTRL:        tl_rsp_rdata = ctrl_reg;
 000012           ADDR_STATUS:      tl_rsp_rdata = {13'b0, rx_frame_err_sticky, rx_parity_err_sticky,
 000012                                              rx_overrun_sticky, rx_fifo_level, tx_fifo_level,
 000012                                              rx_fifo_full, rx_fifo_empty, tx_fifo_full, tx_fifo_empty};
 000012           ADDR_TXDATA:      begin tl_rsp_rdata = 32'h0; tl_rsp_error = 1'b1; end
 000012           ADDR_RXDATA:      begin
 000012                               tl_rsp_rdata = {24'h0, rx_fifo_rdata};
~000066                               rx_fifo_pop  = ~rx_fifo_empty;
                                    end
%000006           ADDR_FIFO_CTRL:   tl_rsp_rdata = {20'b0, 2'b0, fifo_ctrl_rx_watermark, fifo_ctrl_tx_watermark};
%000006           ADDR_INTR_STATE:  tl_rsp_rdata = {25'b0, intr_state};
%000006           ADDR_INTR_ENABLE: tl_rsp_rdata = {25'b0, intr_enable};
%000000           ADDR_INTR_TEST:   tl_rsp_rdata = 32'h0;
%000000           default:          tl_rsp_error = 1'b1;
                endcase
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       ctrl_reg          <= 32'h0;
%000005       ctrl_tx_enable    <= 1'b0;
%000005       ctrl_rx_enable    <= 1'b0;
%000005       ctrl_baud_divisor <= 16'h0;
%000005       ctrl_parity_mode  <= 2'b00;
%000005       ctrl_stop_bits    <= 1'b0;
%000005       ctrl_loopback_en  <= 1'b0;
~000125     end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_CTRL) begin
%000001       ctrl_reg          <= tl_req_wdata;
%000001       ctrl_tx_enable    <= tl_req_wdata[0];
%000001       ctrl_rx_enable    <= tl_req_wdata[1];
%000001       ctrl_baud_divisor <= tl_req_wdata[17:2];
%000001       ctrl_parity_mode  <= tl_req_wdata[19:18];
%000001       ctrl_stop_bits    <= tl_req_wdata[20];
%000001       ctrl_loopback_en  <= tl_req_wdata[21];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fifo_ctrl_tx_watermark <= 5'd1;
%000005       fifo_ctrl_rx_watermark <= 5'd1;
%000005       fifo_ctrl_tx_rst       <= 1'b0;
%000005       fifo_ctrl_rx_rst       <= 1'b0;
 000126     end else begin
~000126       if (fifo_ctrl_tx_rst) fifo_ctrl_tx_rst <= 1'b0;
~000126       if (fifo_ctrl_rx_rst) fifo_ctrl_rx_rst <= 1'b0;
        
~000126       if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_FIFO_CTRL) begin
%000000         fifo_ctrl_tx_watermark <= tl_req_wdata[4:0];
%000000         fifo_ctrl_rx_watermark <= tl_req_wdata[9:5];
%000000         fifo_ctrl_tx_rst       <= tl_req_wdata[10];
%000000         fifo_ctrl_rx_rst       <= tl_req_wdata[11];
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       intr_state  <= '0;
%000005       intr_enable <= '0;
 000126     end else begin
 000126       intr_state <= intr_state | intr_hw_set;
        
~000122       if (tl_req_valid && tl_req_write) begin
%000004         if (tl_req_addr == ADDR_INTR_STATE) begin
%000000           intr_state <= (intr_state | intr_hw_set) & ~tl_req_wdata[NUM_IRQS-1:0];
                end
%000004         if (tl_req_addr == ADDR_INTR_ENABLE) begin
%000000           intr_enable <= tl_req_wdata[NUM_IRQS-1:0];
                end
%000004         if (tl_req_addr == ADDR_INTR_TEST) begin
%000000           intr_state <= intr_state | intr_hw_set | tl_req_wdata[NUM_IRQS-1:0];
                end
              end
            end
          end
        
%000001   always_comb begin
%000001     intr_o = intr_state & intr_enable;
          end
        
 000686   always_comb begin
 000686     tx_fifo_empty = (tx_wptr == tx_rptr);
~000686     tx_fifo_full  = (tx_wptr[FIFO_AW] != tx_rptr[FIFO_AW]) &&
 000686                     (tx_wptr[FIFO_AW-1:0] == tx_rptr[FIFO_AW-1:0]);
 000686     tx_fifo_level = tx_wptr - tx_rptr;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_wptr <= '0;
%000000     end else if (fifo_ctrl_tx_rst) begin
%000000       tx_wptr <= '0;
~000125     end else if (tx_fifo_push && !tx_fifo_full) begin
%000001       tx_fifo_mem[tx_wptr[FIFO_AW-1:0]] <= tx_fifo_wdata;
%000001       tx_wptr <= tx_wptr + 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_rptr <= '0;
%000000     end else if (fifo_ctrl_tx_rst) begin
%000000       tx_rptr <= '0;
~000125     end else if (tx_fifo_pop && !tx_fifo_empty) begin
%000001       tx_rptr <= tx_rptr + 1'b1;
            end
          end
        
%000001   always_comb begin
%000001     tx_fifo_rdata = tx_fifo_mem[tx_rptr[FIFO_AW-1:0]];
          end
        
 000686   always_comb begin
 000686     rx_fifo_empty = (rx_wptr == rx_rptr);
~000686     rx_fifo_full  = (rx_wptr[FIFO_AW] != rx_rptr[FIFO_AW]) &&
 000686                     (rx_wptr[FIFO_AW-1:0] == rx_rptr[FIFO_AW-1:0]);
 000686     rx_fifo_level = rx_wptr - rx_rptr;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_wptr <= '0;
%000000     end else if (fifo_ctrl_rx_rst) begin
%000000       rx_wptr <= '0;
~000126     end else if (rx_fifo_push && !rx_fifo_full) begin
%000000       rx_fifo_mem[rx_wptr[FIFO_AW-1:0]] <= rx_fifo_wdata;
%000000       rx_wptr <= rx_wptr + 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_rptr <= '0;
%000000     end else if (fifo_ctrl_rx_rst) begin
%000000       rx_rptr <= '0;
~000126     end else if (rx_fifo_pop && !rx_fifo_empty) begin
%000000       rx_rptr <= rx_rptr + 1'b1;
            end
          end
        
%000001   always_comb begin
%000001     rx_fifo_rdata = rx_fifo_mem[rx_rptr[FIFO_AW-1:0]];
          end
        
%000001   logic tx_fifo_pop_req;
          assign tx_fifo_pop = tx_fifo_pop_req;
        
 000686   always_comb begin
~000686     tx_baud_tick = (tx_baud_cnt == ctrl_baud_divisor) && (ctrl_baud_divisor != 16'h0);
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_baud_cnt <= 16'h0;
 000126     end else begin
~000090       if (tx_state == TX_IDLE || tx_baud_tick) begin
 000036         tx_baud_cnt <= 16'h0;
 000090       end else begin
 000090         tx_baud_cnt <= tx_baud_cnt + 16'h1;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_state     <= TX_IDLE;
%000005       uart_tx_o    <= 1'b1;
%000005       tx_bit_idx   <= 3'h0;
%000005       tx_shift_reg <= 8'h0;
%000005       tx_parity_bit <= 1'b0;
%000005       tx_fifo_pop_req <= 1'b0;
 000126     end else begin
 000126       tx_fifo_pop_req <= 1'b0;
        
 000126       case (tx_state)
 000036         TX_IDLE: begin
 000036           uart_tx_o <= 1'b1;
~000124           if (ctrl_tx_enable && !tx_fifo_empty) begin
%000001             tx_shift_reg <= tx_fifo_rdata;
%000001             tx_fifo_pop_req <= 1'b1;
%000001             tx_state <= TX_START;
%000001             tx_bit_idx <= 3'h0;
%000000             if (ctrl_parity_mode == 2'b01)
%000000               tx_parity_bit <= ^tx_fifo_rdata;
%000001             else if (ctrl_parity_mode == 2'b10)
%000000               tx_parity_bit <= ~(^tx_fifo_rdata);
                    else
%000001               tx_parity_bit <= 1'b0;
                  end
                end
        
 000090         TX_START: begin
 000090           uart_tx_o <= 1'b0;
~000090           if (tx_baud_tick) begin
%000000             tx_state <= TX_DATA;
%000000             tx_bit_idx <= 3'h0;
                  end
                end
        
%000000         TX_DATA: begin
%000000           uart_tx_o <= tx_shift_reg[tx_bit_idx];
%000000           if (tx_baud_tick) begin
%000000             if (tx_bit_idx == 3'd7) begin
%000000               if (ctrl_parity_mode != 2'b00)
%000000                 tx_state <= TX_PARITY;
                      else
%000000                 tx_state <= TX_STOP;
%000000             end else begin
%000000               tx_bit_idx <= tx_bit_idx + 3'h1;
                    end
                  end
                end
        
%000000         TX_PARITY: begin
%000000           uart_tx_o <= tx_parity_bit;
%000000           if (tx_baud_tick) begin
%000000             tx_state <= TX_STOP;
                  end
                end
        
%000000         TX_STOP: begin
%000000           uart_tx_o <= 1'b1;
%000000           if (tx_baud_tick) begin
%000000             if (ctrl_stop_bits)
%000000               tx_state <= TX_STOP2;
                    else
%000000               tx_state <= TX_IDLE;
                  end
                end
        
%000000         TX_STOP2: begin
%000000           uart_tx_o <= 1'b1;
%000000           if (tx_baud_tick) begin
%000000             tx_state <= TX_IDLE;
                  end
                end
        
%000000         default: tx_state <= TX_IDLE;
              endcase
            end
          end
        
 000686   always_comb begin
~000686     rx_serial_in = ctrl_loopback_en ? uart_tx_o : uart_rx_i;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_serial_q  <= 1'b1;
%000005       rx_serial_qq <= 1'b1;
 000126     end else begin
 000126       rx_serial_q  <= rx_serial_in;
 000126       rx_serial_qq <= rx_serial_q;
            end
          end
        
%000000   logic [15:0] rx_os_divisor;
%000001   always_comb begin
%000001     rx_os_divisor = {4'b0, ctrl_baud_divisor[15:4]};
          end
        
 000686   always_comb begin
~000686     rx_os_tick = (rx_baud_cnt == rx_os_divisor) && (ctrl_baud_divisor != 16'h0);
          end
        
 000686   always_comb begin
~000686     if (ctrl_parity_mode == 2'b01)
%000000       rx_expected_parity = rx_parity_calc;
            else
~000686       rx_expected_parity = ~rx_parity_calc;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_baud_cnt <= 16'h0;
 000126     end else begin
~000126       if (rx_state == RX_IDLE || rx_os_tick) begin
 000126         rx_baud_cnt <= 16'h0;
%000000       end else begin
%000000         rx_baud_cnt <= rx_baud_cnt + 16'h1;
              end
            end
          end
        
%000000   logic        rx_push_valid;
%000000   logic [7:0]  rx_push_data;
%000000   logic        rx_parity_error_det;
%000000   logic        rx_frame_error_det;
%000000   logic        rx_overflow_det;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_state       <= RX_IDLE;
%000005       rx_os_cnt      <= 4'h0;
%000005       rx_bit_idx     <= 3'h0;
%000005       rx_shift_reg   <= 8'h0;
%000005       rx_parity_calc <= 1'b0;
%000005       rx_push_valid  <= 1'b0;
%000005       rx_push_data   <= 8'h0;
%000005       rx_parity_error_det <= 1'b0;
%000005       rx_frame_error_det  <= 1'b0;
%000005       rx_overflow_det     <= 1'b0;
%000005       rx_active      <= 1'b0;
 000126     end else begin
 000126       rx_push_valid       <= 1'b0;
 000126       rx_parity_error_det <= 1'b0;
 000126       rx_frame_error_det  <= 1'b0;
 000126       rx_overflow_det     <= 1'b0;
        
 000126       case (rx_state)
 000126         RX_IDLE: begin
 000126           rx_os_cnt  <= 4'h0;
 000126           rx_bit_idx <= 3'h0;
 000126           rx_active  <= 1'b0;
~000126           if (ctrl_rx_enable && rx_serial_qq == 1'b0) begin
%000000             rx_state  <= RX_START_DET;
%000000             rx_os_cnt <= 4'h1;
%000000             rx_active <= 1'b1;
                  end
                end
        
%000000         RX_START_DET: begin
%000000           if (rx_os_tick) begin
%000000             rx_os_cnt <= rx_os_cnt + 4'h1;
%000000             if (rx_os_cnt == 4'd8) begin
%000000               if (rx_serial_qq == 1'b0) begin
%000000                 rx_state      <= RX_DATA;
%000000                 rx_os_cnt     <= 4'h0;
%000000                 rx_bit_idx    <= 3'h0;
%000000                 rx_parity_calc <= 1'b0;
%000000               end else begin
%000000                 rx_state <= RX_IDLE;
                      end
                    end
                  end
                end
        
%000000         RX_DATA: begin
%000000           if (rx_os_tick) begin
%000000             rx_os_cnt <= rx_os_cnt + 4'h1;
%000000             if (rx_os_cnt == 4'd15) begin
%000000               rx_os_cnt <= 4'h0;
                    end
%000000             if (rx_os_cnt == 4'd8) begin
%000000               rx_shift_reg[rx_bit_idx] <= rx_serial_qq;
%000000               rx_parity_calc <= rx_parity_calc ^ rx_serial_qq;
%000000               if (rx_bit_idx == 3'd7) begin
%000000                 if (ctrl_parity_mode != 2'b00)
%000000                   rx_state <= RX_PARITY;
                        else
%000000                   rx_state <= RX_STOP;
%000000                 rx_os_cnt <= 4'h0;
%000000               end else begin
%000000                 rx_bit_idx <= rx_bit_idx + 3'h1;
                      end
                    end
                  end
                end
        
%000000         RX_PARITY: begin
%000000           if (rx_os_tick) begin
%000000             rx_os_cnt <= rx_os_cnt + 4'h1;
%000000             if (rx_os_cnt == 4'd15) begin
%000000               rx_os_cnt <= 4'h0;
                    end
%000000             if (rx_os_cnt == 4'd8) begin
%000000               if (rx_serial_qq != rx_expected_parity) begin
%000000                 rx_parity_error_det <= 1'b1;
                      end
%000000               rx_state  <= RX_STOP;
%000000               rx_os_cnt <= 4'h0;
                    end
                  end
                end
        
%000000         RX_STOP: begin
%000000           if (rx_os_tick) begin
%000000             rx_os_cnt <= rx_os_cnt + 4'h1;
%000000             if (rx_os_cnt == 4'd15) begin
%000000               rx_os_cnt <= 4'h0;
                    end
%000000             if (rx_os_cnt == 4'd8) begin
%000000               if (rx_serial_qq == 1'b0) begin
%000000                 rx_frame_error_det <= 1'b1;
                      end
%000000               if (ctrl_stop_bits) begin
%000000                 rx_state  <= RX_STOP2;
%000000                 rx_os_cnt <= 4'h0;
%000000               end else begin
%000000                 if (rx_fifo_full) begin
%000000                   rx_overflow_det <= 1'b1;
%000000                 end else begin
%000000                   rx_push_valid <= 1'b1;
%000000                   rx_push_data  <= rx_shift_reg;
                        end
%000000                 rx_state <= RX_IDLE;
                      end
                    end
                  end
                end
        
%000000         RX_STOP2: begin
%000000           if (rx_os_tick) begin
%000000             rx_os_cnt <= rx_os_cnt + 4'h1;
%000000             if (rx_os_cnt == 4'd15) begin
%000000               rx_os_cnt <= 4'h0;
                    end
%000000             if (rx_os_cnt == 4'd8) begin
%000000               if (rx_serial_qq == 1'b0) begin
%000000                 rx_frame_error_det <= 1'b1;
                      end
%000000               if (rx_fifo_full) begin
%000000                 rx_overflow_det <= 1'b1;
%000000               end else begin
%000000                 rx_push_valid <= 1'b1;
%000000                 rx_push_data  <= rx_shift_reg;
                      end
%000000               rx_state <= RX_IDLE;
                    end
                  end
                end
        
%000000         default: rx_state <= RX_IDLE;
              endcase
            end
          end
        
          assign rx_fifo_push  = rx_push_valid;
          assign rx_fifo_wdata = rx_push_data;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_overrun_sticky    <= 1'b0;
%000005       rx_parity_err_sticky <= 1'b0;
%000005       rx_frame_err_sticky  <= 1'b0;
 000126     end else begin
~000126       if (fifo_ctrl_rx_rst) begin
%000000         rx_overrun_sticky    <= 1'b0;
%000000         rx_parity_err_sticky <= 1'b0;
%000000         rx_frame_err_sticky  <= 1'b0;
 000126       end else begin
~000126         if (rx_overflow_det)     rx_overrun_sticky    <= 1'b1;
~000126         if (rx_parity_error_det) rx_parity_err_sticky <= 1'b1;
~000126         if (rx_frame_error_det)  rx_frame_err_sticky  <= 1'b1;
              end
            end
          end
        
%000001   always_comb begin
%000001     rx_timeout_thresh = {16'h0, ctrl_baud_divisor} * 32'd16;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_timeout_cnt   <= 32'h0;
%000005       rx_timeout_event <= 1'b0;
 000126     end else begin
 000126       rx_timeout_event <= 1'b0;
~000126       if (rx_active || rx_state != RX_IDLE) begin
%000000         rx_timeout_cnt <= 32'h0;
~000126       end else if (!rx_fifo_empty && ctrl_rx_enable) begin
%000000         if (rx_serial_qq == 1'b1) begin
%000000           if (rx_timeout_cnt < rx_timeout_thresh) begin
%000000             rx_timeout_cnt <= rx_timeout_cnt + 32'h1;
%000000           end else begin
%000000             rx_timeout_event <= 1'b1;
                  end
%000000         end else begin
%000000           rx_timeout_cnt <= 32'h0;
                end
 000126       end else begin
 000126         rx_timeout_cnt <= 32'h0;
              end
            end
          end
        
 000686   always_comb begin
 000686     intr_hw_set = '0;
        
~000532     if (tx_fifo_level <= {1'b0, fifo_ctrl_tx_watermark} && ctrl_tx_enable)
 000532       intr_hw_set[0] = 1'b1;
        
~000686     if (rx_fifo_level >= {1'b0, fifo_ctrl_rx_watermark} && ctrl_rx_enable)
%000000       intr_hw_set[1] = 1'b1;
        
 000521     if (tx_fifo_empty && ctrl_tx_enable)
 000521       intr_hw_set[2] = 1'b1;
        
~000686     if (rx_overflow_det)
%000000       intr_hw_set[3] = 1'b1;
        
~000686     if (rx_frame_error_det)
%000000       intr_hw_set[4] = 1'b1;
        
~000686     if (rx_parity_error_det)
%000000       intr_hw_set[5] = 1'b1;
        
~000686     if (rx_timeout_event)
%000000       intr_hw_set[6] = 1'b1;
          end
        
          assign alert_o = 1'b0;
        
        endmodule
        
