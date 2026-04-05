//      // verilator_coverage annotation
        module rampart_i2c
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
%000003   output logic [31:0] tl_d_data_o,
%000000   output logic [7:0]  tl_d_source_o,
%000004   output logic        tl_d_error_o,
%000001   input  logic        scl_i,
%000000   output logic        scl_o,
 000010   output logic        scl_oe_o,
%000001   input  logic        sda_i,
%000000   output logic        sda_o,
%000004   output logic        sda_oe_o,
%000000   output logic [15:0] intr_o,
%000000   output logic        alert_o
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
        
%000001   logic        ctrl_host_enable;
%000000   logic        ctrl_target_enable;
%000000   logic        ctrl_line_loopback;
%000001   logic [31:0] ctrl_reg;
        
%000000   logic [15:0] timing_tlow;
%000000   logic [15:0] timing_thigh;
%000000   logic [15:0] timing_t_r;
%000000   logic [15:0] timing_t_f;
%000000   logic [15:0] timing_tsu_sta;
%000000   logic [15:0] timing_thd_sta;
%000000   logic [15:0] timing_tsu_dat;
%000000   logic [15:0] timing_thd_dat;
%000000   logic [15:0] timing_tsu_sto;
%000000   logic [15:0] timing_t_buf;
        
%000000   logic [6:0]  target_address;
%000000   logic [6:0]  target_mask;
        
%000000   logic        ovrd_txovrden;
%000001   logic        ovrd_sclval;
%000001   logic        ovrd_sdaval;
        
%000000   logic [19:0] host_timeout_val;
%000000   logic        host_timeout_en;
        
%000001   logic [NUM_IRQS-1:0] intr_state;
%000000   logic [NUM_IRQS-1:0] intr_enable;
%000001   logic [NUM_IRQS-1:0] intr_hw_set;
        
          logic [12:0] fmt_fifo_mem [FIFO_DEPTH];
%000001   logic [FIFO_AW:0] fmt_wptr;
%000001   logic [FIFO_AW:0] fmt_rptr;
%000002   logic        fmt_fifo_empty;
%000000   logic        fmt_fifo_full;
%000001   logic [6:0]  fmt_fifo_level;
%000001   logic        fmt_fifo_push;
%000001   logic        fmt_fifo_pop;
%000001   logic [12:0] fmt_fifo_wdata;
%000001   logic [12:0] fmt_fifo_rdata;
        
          logic [7:0]  rx_fifo_mem [FIFO_DEPTH];
%000000   logic [FIFO_AW:0] rx_wptr;
%000000   logic [FIFO_AW:0] rx_rptr;
%000001   logic        rx_fifo_empty;
%000000   logic        rx_fifo_full;
%000000   logic [6:0]  rx_fifo_level;
%000000   logic        rx_fifo_push;
%000000   logic        rx_fifo_pop;
%000000   logic [7:0]  rx_fifo_wdata;
%000000   logic [7:0]  rx_fifo_rdata;
        
          logic [7:0]  tx_fifo_mem [FIFO_DEPTH];
%000000   logic [FIFO_AW:0] tx_wptr;
%000000   logic [FIFO_AW:0] tx_rptr;
%000001   logic        tx_fifo_empty;
%000000   logic        tx_fifo_full;
%000000   logic [6:0]  tx_fifo_level;
%000000   logic        tx_fifo_push;
%000000   logic        tx_fifo_pop;
%000000   logic [7:0]  tx_fifo_wdata;
%000000   logic [7:0]  tx_fifo_rdata;
        
          logic [9:0]  acq_fifo_mem [FIFO_DEPTH];
%000000   logic [FIFO_AW:0] acq_wptr;
%000000   logic [FIFO_AW:0] acq_rptr;
%000001   logic        acq_fifo_empty;
%000000   logic        acq_fifo_full;
%000000   logic [6:0]  acq_fifo_level;
%000000   logic        acq_fifo_push;
%000000   logic        acq_fifo_pop;
%000000   logic [9:0]  acq_fifo_wdata;
%000000   logic [9:0]  acq_fifo_rdata;
        
%000000   logic        fifo_ctrl_fmt_rst;
%000000   logic        fifo_ctrl_rx_rst;
%000000   logic        fifo_ctrl_tx_rst;
%000000   logic        fifo_ctrl_acq_rst;
        
%000001   logic        scl_in;
%000001   logic        sda_in;
%000001   logic        scl_in_q;
%000001   logic        sda_in_q;
%000001   logic        scl_in_qq;
%000001   logic        sda_in_qq;
        
 000010   logic        host_scl_oe;
%000004   logic        host_sda_oe;
%000000   logic        tgt_scl_oe;
%000000   logic        tgt_sda_oe;
        
%000001   host_state_e host_state;
%000000   tgt_state_e  tgt_state;
        
%000000   logic [15:0] host_timing_cnt;
%000005   logic [3:0]  host_bit_idx;
%000001   logic [7:0]  host_shift_reg;
%000000   logic        host_ack_received;
%000000   logic [7:0]  host_read_byte_cnt;
%000000   logic [7:0]  host_read_shift;
%000000   logic        host_read_rcont;
%000000   logic        host_read_stop;
%000000   logic        host_cmd_start;
%000000   logic        host_cmd_stop;
%000000   logic        host_cmd_readb;
%000000   logic        host_cmd_rcont;
%000000   logic        host_cmd_nakok;
%000001   logic [7:0]  host_cmd_byte;
%000000   logic        host_arb_lost;
        
%000000   logic [6:0]  tgt_addr_shift;
%000000   logic        tgt_rw_bit;
%000000   logic [3:0]  tgt_bit_idx;
%000000   logic [7:0]  tgt_rx_shift;
%000000   logic [7:0]  tgt_tx_shift;
%000000   logic        tgt_addr_match;
%000000   logic        tgt_stretch_needed;
        
%000000   logic [19:0] host_timeout_cnt;
%000000   logic        host_timeout_event;
%000000   logic        bus_active;
        
 000015   logic        tl_req_valid;
 000012   logic        tl_req_write;
%000007   logic [31:0] tl_req_addr;
%000002   logic [31:0] tl_req_wdata;
%000001   logic [3:0]  tl_req_mask;
%000000   logic [7:0]  tl_req_source;
%000003   logic [31:0] tl_rsp_rdata;
%000004   logic        tl_rsp_error;
 000015   logic        tl_rsp_pending;
        
 000686   always_comb begin
~000686     tl_req_valid  = tl_a_valid_i & tl_a_ready_o;
~000686     tl_req_write  = (tl_a_opcode_i == TL_OP_PUT_FULL) ||
 000686                     (tl_a_opcode_i == TL_OP_PUT_PARTIAL);
 000686     tl_req_addr   = {tl_a_address_i[31:2], 2'b00};
 000686     tl_req_wdata  = tl_a_data_i;
 000686     tl_req_mask   = tl_a_mask_i;
 000686     tl_req_source = tl_a_source_i;
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
~000015         tl_d_opcode_o  <= tl_req_write ? TL_OP_ACCESS_ACK : TL_OP_ACCESS_ACK_DATA;
 000015         tl_d_data_o    <= tl_rsp_rdata;
 000015         tl_d_source_o  <= tl_req_source;
 000015         tl_d_error_o   <= tl_rsp_error;
              end
            end
          end
        
 000686   always_comb begin
 000686     tl_rsp_rdata   = 32'h0;
 000686     tl_rsp_error   = 1'b0;
 000686     fmt_fifo_push  = 1'b0;
 000686     fmt_fifo_wdata = 13'h0;
 000686     rx_fifo_pop    = 1'b0;
 000686     tx_fifo_push   = 1'b0;
 000686     tx_fifo_wdata  = 8'h0;
 000686     acq_fifo_pop   = 1'b0;
        
 000596     if (tl_req_valid) begin
 000066       if (tl_req_write) begin
 000024         case (tl_req_addr)
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
 000012           ADDR_INTR_TEST: ;
 000012           default: tl_rsp_error = 1'b1;
                endcase
        
~000018         if (tl_req_addr == ADDR_FDATA) begin
%000006           fmt_fifo_push  = 1'b1;
%000006           fmt_fifo_wdata = tl_req_wdata[12:0];
                end
        
~000024         if (tl_req_addr == ADDR_TXDATA) begin
%000000           tx_fifo_push  = 1'b1;
%000000           tx_fifo_wdata = tl_req_wdata[7:0];
                end
 000066       end else begin
 000066         case (tl_req_addr)
 000012           ADDR_CTRL:              tl_rsp_rdata = ctrl_reg;
 000012           ADDR_STATUS:            tl_rsp_rdata = {22'b0,
 000012                                                    tgt_stretch_needed,
 000012                                                    bus_active,
 000012                                                    tgt_state == TGT_IDLE,
 000012                                                    host_state == HOST_IDLE,
 000012                                                    rx_fifo_empty, rx_fifo_full,
 000012                                                    tx_fifo_empty, tx_fifo_full,
 000012                                                    fmt_fifo_empty, fmt_fifo_full};
 000012           ADDR_RDATA: begin
 000012             tl_rsp_rdata = {24'h0, rx_fifo_rdata};
~000066             rx_fifo_pop  = ~rx_fifo_empty;
                  end
 000012           ADDR_FDATA: begin
 000012             tl_rsp_rdata = 32'h0;
 000012             tl_rsp_error = 1'b1;
                  end
%000006           ADDR_FIFO_CTRL:         tl_rsp_rdata = 32'h0;
%000006           ADDR_FIFO_STATUS:       tl_rsp_rdata = {4'b0, acq_fifo_level, tx_fifo_level,
%000006                                                    rx_fifo_level, fmt_fifo_level};
%000006           ADDR_OVRD:              tl_rsp_rdata = {29'b0, ovrd_sdaval, ovrd_sclval, ovrd_txovrden};
%000000           ADDR_TIMING0:           tl_rsp_rdata = {timing_thigh, timing_tlow};
%000000           ADDR_TIMING1:           tl_rsp_rdata = {timing_t_r, timing_t_f};
%000000           ADDR_TIMING2:           tl_rsp_rdata = {timing_tsu_sta, timing_thd_sta};
%000000           ADDR_TIMING3:           tl_rsp_rdata = {timing_tsu_dat, timing_thd_dat};
%000000           ADDR_TIMING4:           tl_rsp_rdata = {timing_tsu_sto, timing_t_buf};
%000000           ADDR_TARGET_ID:         tl_rsp_rdata = {18'b0, target_mask, target_address};
%000000           ADDR_ACQDATA: begin
%000000             tl_rsp_rdata = {22'h0, acq_fifo_rdata};
~000066             acq_fifo_pop = ~acq_fifo_empty;
                  end
%000000           ADDR_TXDATA: begin
%000000             tl_rsp_rdata = 32'h0;
%000000             tl_rsp_error = 1'b1;
                  end
%000000           ADDR_HOST_TIMEOUT_CTRL: tl_rsp_rdata = {11'b0, host_timeout_en, host_timeout_val};
%000000           ADDR_INTR_STATE:        tl_rsp_rdata = {16'b0, intr_state};
%000000           ADDR_INTR_ENABLE:       tl_rsp_rdata = {16'b0, intr_enable};
%000000           ADDR_INTR_TEST:         tl_rsp_rdata = 32'h0;
%000000           default:                tl_rsp_error = 1'b1;
                endcase
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       ctrl_reg           <= 32'h0;
%000005       ctrl_host_enable   <= 1'b0;
%000005       ctrl_target_enable <= 1'b0;
%000005       ctrl_line_loopback <= 1'b0;
~000125     end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_CTRL) begin
%000001       ctrl_reg           <= tl_req_wdata;
%000001       ctrl_host_enable   <= tl_req_wdata[0];
%000001       ctrl_target_enable <= tl_req_wdata[1];
%000001       ctrl_line_loopback <= tl_req_wdata[2];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       timing_tlow    <= 16'h0;
%000005       timing_thigh   <= 16'h0;
%000005       timing_t_f     <= 16'h0;
%000005       timing_t_r     <= 16'h0;
%000005       timing_thd_sta <= 16'h0;
%000005       timing_tsu_sta <= 16'h0;
%000005       timing_thd_dat <= 16'h0;
%000005       timing_tsu_dat <= 16'h0;
%000005       timing_t_buf   <= 16'h0;
%000005       timing_tsu_sto <= 16'h0;
~000122     end else if (tl_req_valid && tl_req_write) begin
%000004       case (tl_req_addr)
%000000         ADDR_TIMING0: begin
%000000           timing_tlow  <= tl_req_wdata[15:0];
%000000           timing_thigh <= tl_req_wdata[31:16];
                end
%000000         ADDR_TIMING1: begin
%000000           timing_t_f <= tl_req_wdata[15:0];
%000000           timing_t_r <= tl_req_wdata[31:16];
                end
%000000         ADDR_TIMING2: begin
%000000           timing_thd_sta <= tl_req_wdata[15:0];
%000000           timing_tsu_sta <= tl_req_wdata[31:16];
                end
%000000         ADDR_TIMING3: begin
%000000           timing_thd_dat <= tl_req_wdata[15:0];
%000000           timing_tsu_dat <= tl_req_wdata[31:16];
                end
%000000         ADDR_TIMING4: begin
%000000           timing_t_buf   <= tl_req_wdata[15:0];
%000000           timing_tsu_sto <= tl_req_wdata[31:16];
                end
%000004         default: ;
              endcase
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       target_address <= 7'h0;
%000005       target_mask    <= 7'h0;
~000126     end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_TARGET_ID) begin
%000000       target_address <= tl_req_wdata[6:0];
%000000       target_mask    <= tl_req_wdata[13:7];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       ovrd_txovrden <= 1'b0;
%000005       ovrd_sclval   <= 1'b1;
%000005       ovrd_sdaval   <= 1'b1;
~000126     end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_OVRD) begin
%000000       ovrd_txovrden <= tl_req_wdata[0];
%000000       ovrd_sclval   <= tl_req_wdata[1];
%000000       ovrd_sdaval   <= tl_req_wdata[2];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       host_timeout_val <= 20'h0;
%000005       host_timeout_en  <= 1'b0;
~000126     end else if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_HOST_TIMEOUT_CTRL) begin
%000000       host_timeout_val <= tl_req_wdata[19:0];
%000000       host_timeout_en  <= tl_req_wdata[20];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fifo_ctrl_fmt_rst <= 1'b0;
%000005       fifo_ctrl_rx_rst  <= 1'b0;
%000005       fifo_ctrl_tx_rst  <= 1'b0;
%000005       fifo_ctrl_acq_rst <= 1'b0;
 000126     end else begin
~000126       if (fifo_ctrl_fmt_rst) fifo_ctrl_fmt_rst <= 1'b0;
~000126       if (fifo_ctrl_rx_rst)  fifo_ctrl_rx_rst  <= 1'b0;
~000126       if (fifo_ctrl_tx_rst)  fifo_ctrl_tx_rst  <= 1'b0;
~000126       if (fifo_ctrl_acq_rst) fifo_ctrl_acq_rst <= 1'b0;
        
~000126       if (tl_req_valid && tl_req_write && tl_req_addr == ADDR_FIFO_CTRL) begin
%000000         fifo_ctrl_fmt_rst <= tl_req_wdata[0];
%000000         fifo_ctrl_rx_rst  <= tl_req_wdata[1];
%000000         fifo_ctrl_tx_rst  <= tl_req_wdata[2];
%000000         fifo_ctrl_acq_rst <= tl_req_wdata[3];
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
 000686     fmt_fifo_empty = (fmt_wptr == fmt_rptr);
~000686     fmt_fifo_full  = (fmt_wptr[FIFO_AW] != fmt_rptr[FIFO_AW]) &&
 000686                      (fmt_wptr[FIFO_AW-1:0] == fmt_rptr[FIFO_AW-1:0]);
 000686     fmt_fifo_level = fmt_wptr - fmt_rptr;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fmt_wptr <= '0;
%000000     end else if (fifo_ctrl_fmt_rst) begin
%000000       fmt_wptr <= '0;
~000125     end else if (fmt_fifo_push && !fmt_fifo_full) begin
%000001       fmt_fifo_mem[fmt_wptr[FIFO_AW-1:0]] <= fmt_fifo_wdata;
%000001       fmt_wptr <= fmt_wptr + 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fmt_rptr <= '0;
%000000     end else if (fifo_ctrl_fmt_rst) begin
%000000       fmt_rptr <= '0;
~000125     end else if (fmt_fifo_pop && !fmt_fifo_empty) begin
%000001       fmt_rptr <= fmt_rptr + 1'b1;
            end
          end
        
%000001   always_comb begin
%000001     fmt_fifo_rdata = fmt_fifo_mem[fmt_rptr[FIFO_AW-1:0]];
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
~000126     end else if (tx_fifo_push && !tx_fifo_full) begin
%000000       tx_fifo_mem[tx_wptr[FIFO_AW-1:0]] <= tx_fifo_wdata;
%000000       tx_wptr <= tx_wptr + 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_rptr <= '0;
%000000     end else if (fifo_ctrl_tx_rst) begin
%000000       tx_rptr <= '0;
~000126     end else if (tx_fifo_pop && !tx_fifo_empty) begin
%000000       tx_rptr <= tx_rptr + 1'b1;
            end
          end
        
%000001   always_comb begin
%000001     tx_fifo_rdata = tx_fifo_mem[tx_rptr[FIFO_AW-1:0]];
          end
        
 000686   always_comb begin
 000686     acq_fifo_empty = (acq_wptr == acq_rptr);
~000686     acq_fifo_full  = (acq_wptr[FIFO_AW] != acq_rptr[FIFO_AW]) &&
 000686                      (acq_wptr[FIFO_AW-1:0] == acq_rptr[FIFO_AW-1:0]);
 000686     acq_fifo_level = acq_wptr - acq_rptr;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       acq_wptr <= '0;
%000000     end else if (fifo_ctrl_acq_rst) begin
%000000       acq_wptr <= '0;
~000126     end else if (acq_fifo_push && !acq_fifo_full) begin
%000000       acq_fifo_mem[acq_wptr[FIFO_AW-1:0]] <= acq_fifo_wdata;
%000000       acq_wptr <= acq_wptr + 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       acq_rptr <= '0;
%000000     end else if (fifo_ctrl_acq_rst) begin
%000000       acq_rptr <= '0;
~000126     end else if (acq_fifo_pop && !acq_fifo_empty) begin
%000000       acq_rptr <= acq_rptr + 1'b1;
            end
          end
        
%000001   always_comb begin
%000001     acq_fifo_rdata = acq_fifo_mem[acq_rptr[FIFO_AW-1:0]];
          end
        
 000686   always_comb begin
~000686     if (ctrl_line_loopback) begin
%000000       scl_in = ~scl_oe_o;
%000000       sda_in = ~sda_oe_o;
 000686     end else begin
 000686       scl_in = scl_i;
 000686       sda_in = sda_i;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       scl_in_q  <= 1'b1;
%000005       sda_in_q  <= 1'b1;
%000005       scl_in_qq <= 1'b1;
%000005       sda_in_qq <= 1'b1;
 000126     end else begin
 000126       scl_in_q  <= scl_in;
 000126       sda_in_q  <= sda_in;
 000126       scl_in_qq <= scl_in_q;
 000126       sda_in_qq <= sda_in_q;
            end
          end
        
%000000   logic scl_rising;
%000000   logic scl_falling;
%000000   logic sda_rising;
%000000   logic sda_falling;
%000000   logic start_det;
%000000   logic stop_det;
        
 000686   always_comb begin
~000686     scl_rising  = ~scl_in_qq & scl_in_q;
~000686     scl_falling = scl_in_qq & ~scl_in_q;
~000686     sda_rising  = ~sda_in_qq & sda_in_q;
~000686     sda_falling = sda_in_qq & ~sda_in_q;
~000686     start_det   = scl_in_qq & scl_in_q & sda_in_qq & ~sda_in_q;
~000686     stop_det    = scl_in_qq & scl_in_q & ~sda_in_qq & sda_in_q;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       bus_active <= 1'b0;
 000126     end else begin
%000000       if (start_det) begin
%000000         bus_active <= 1'b1;
~000126       end else if (stop_det) begin
%000000         bus_active <= 1'b0;
              end
            end
          end
        
          assign scl_o = 1'b0;
          assign sda_o = 1'b0;
        
 000686   always_comb begin
~000686     if (ovrd_txovrden) begin
%000000       scl_oe_o = ~ovrd_sclval;
%000000       sda_oe_o = ~ovrd_sdaval;
 000686     end else begin
~000686       scl_oe_o = host_scl_oe | tgt_scl_oe;
~000686       sda_oe_o = host_sda_oe | tgt_sda_oe;
            end
          end
        
%000001   logic        fmt_pop_req;
          assign fmt_fifo_pop = fmt_pop_req;
        
%000001   always_comb begin
%000001     host_cmd_byte  = fmt_fifo_rdata[7:0];
%000001     host_cmd_start = fmt_fifo_rdata[8];
%000001     host_cmd_stop  = fmt_fifo_rdata[9];
%000001     host_cmd_readb = fmt_fifo_rdata[10];
%000001     host_cmd_rcont = fmt_fifo_rdata[11];
%000001     host_cmd_nakok = fmt_fifo_rdata[12];
          end
        
%000001   logic host_timing_done;
%000001   always_comb begin
%000001     host_timing_done = (host_timing_cnt == 16'h0);
          end
        
 000010   logic host_scl_drive_low;
%000004   logic host_sda_drive_low;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       host_state         <= HOST_IDLE;
%000005       host_timing_cnt    <= 16'h0;
%000005       host_bit_idx       <= 4'h0;
%000005       host_shift_reg     <= 8'h0;
%000005       host_ack_received  <= 1'b0;
%000005       host_read_byte_cnt <= 8'h0;
%000005       host_read_shift    <= 8'h0;
%000005       host_read_rcont    <= 1'b0;
%000005       host_read_stop     <= 1'b0;
%000005       host_arb_lost      <= 1'b0;
%000005       host_scl_drive_low <= 1'b0;
%000005       host_sda_drive_low <= 1'b0;
%000005       fmt_pop_req        <= 1'b0;
 000126     end else begin
 000126       fmt_pop_req   <= 1'b0;
 000126       host_arb_lost <= 1'b0;
        
~000126       if (host_timing_cnt > 16'h0) begin
%000000         host_timing_cnt <= host_timing_cnt - 16'h1;
              end
        
 000126       case (host_state)
 000104         HOST_IDLE: begin
 000104           host_scl_drive_low <= 1'b0;
 000104           host_sda_drive_low <= 1'b0;
 000104           host_bit_idx       <= 4'h0;
~000124           if (ctrl_host_enable && !fmt_fifo_empty) begin
%000000             if (host_cmd_start) begin
%000000               host_sda_drive_low <= 1'b0;
%000000               host_scl_drive_low <= 1'b0;
%000000               host_state         <= HOST_START;
%000000               host_timing_cnt    <= timing_tsu_sta;
%000000               host_shift_reg     <= host_cmd_byte;
%000001             end else if (host_cmd_readb) begin
%000000               host_read_byte_cnt <= host_cmd_byte;
%000000               host_read_rcont    <= host_cmd_rcont;
%000000               host_read_stop     <= host_cmd_stop;
%000000               host_state         <= HOST_READ_BYTE;
%000000               host_bit_idx       <= 4'h0;
%000000               host_scl_drive_low <= 1'b1;
%000000               host_sda_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_thd_dat;
%000000               fmt_pop_req        <= 1'b1;
%000001             end else begin
%000001               host_shift_reg     <= host_cmd_byte;
%000001               host_state         <= HOST_WRITE_BYTE;
%000001               host_bit_idx       <= 4'h0;
%000001               host_scl_drive_low <= 1'b1;
%000001               host_sda_drive_low <= ~host_cmd_byte[7];
%000001               host_timing_cnt    <= timing_thd_dat;
%000001               fmt_pop_req        <= 1'b1;
                    end
                  end
                end
        
%000000         HOST_START: begin
%000000           if (host_timing_done) begin
%000000             host_sda_drive_low <= 1'b1;
%000000             host_timing_cnt    <= timing_thd_sta;
%000000             host_state         <= HOST_ADDR_BYTE;
%000000             host_bit_idx       <= 4'h0;
                  end
                end
        
%000000         HOST_ADDR_BYTE: begin
%000000           if (host_timing_done) begin
%000000             if (host_bit_idx == 4'h0 && host_scl_drive_low == 1'b0) begin
%000000               host_scl_drive_low <= 1'b1;
%000000               host_sda_drive_low <= ~host_shift_reg[7];
%000000               host_timing_cnt    <= timing_tlow;
%000000               host_bit_idx       <= 4'h0;
%000000             end else if (host_scl_drive_low) begin
%000000               host_scl_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_thigh;
%000000             end else begin
%000000               if (!host_sda_drive_low && !sda_in_q) begin
%000000                 host_arb_lost      <= 1'b1;
%000000                 host_scl_drive_low <= 1'b0;
%000000                 host_sda_drive_low <= 1'b0;
%000000                 host_state         <= HOST_IDLE;
%000000                 fmt_pop_req        <= 1'b1;
%000000               end else begin
%000000                 host_scl_drive_low <= 1'b1;
%000000                 if (host_bit_idx < 4'd7) begin
%000000                   host_bit_idx       <= host_bit_idx + 4'h1;
%000000                   host_sda_drive_low <= ~host_shift_reg[6 - host_bit_idx[2:0]];
%000000                   host_timing_cnt    <= timing_tlow;
%000000                 end else begin
%000000                   host_sda_drive_low <= 1'b0;
%000000                   host_timing_cnt    <= timing_tlow;
%000000                   host_state         <= HOST_ADDR_ACK;
%000000                   host_bit_idx       <= 4'h0;
                        end
                      end
                    end
                  end
                end
        
%000000         HOST_ADDR_ACK: begin
%000000           if (host_timing_done) begin
%000000             if (host_scl_drive_low) begin
%000000               host_scl_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_thigh;
%000000             end else begin
%000000               host_ack_received <= ~sda_in_q;
%000000               host_scl_drive_low <= 1'b1;
%000000               host_timing_cnt    <= timing_tlow;
%000000               fmt_pop_req        <= 1'b1;
        
%000000               if (sda_in_q && !host_cmd_nakok) begin
%000000                 host_state <= HOST_STOP;
%000000               end else if (host_cmd_stop && !host_cmd_readb) begin
%000000                 host_state <= HOST_STOP;
%000000               end else if (host_cmd_readb) begin
%000000                 host_read_byte_cnt <= host_cmd_byte;
%000000                 host_read_rcont    <= host_cmd_rcont;
%000000                 host_read_stop     <= host_cmd_stop;
%000000                 host_state         <= HOST_READ_BYTE;
%000000                 host_bit_idx       <= 4'h0;
%000000                 host_sda_drive_low <= 1'b0;
%000000               end else begin
%000000                 host_state <= HOST_IDLE;
                      end
                    end
                  end
                end
        
 000016         HOST_WRITE_BYTE: begin
~000016           if (host_timing_done) begin
%000008             if (host_scl_drive_low) begin
%000008               host_scl_drive_low <= 1'b0;
%000008               host_timing_cnt    <= timing_thigh;
%000008             end else begin
%000008               if (!host_sda_drive_low && !sda_in_q) begin
%000000                 host_arb_lost      <= 1'b1;
%000000                 host_scl_drive_low <= 1'b0;
%000000                 host_sda_drive_low <= 1'b0;
%000000                 host_state         <= HOST_IDLE;
%000008               end else begin
%000008                 host_scl_drive_low <= 1'b1;
%000007                 if (host_bit_idx < 4'd7) begin
%000007                   host_bit_idx       <= host_bit_idx + 4'h1;
%000007                   host_sda_drive_low <= ~host_shift_reg[6 - host_bit_idx[2:0]];
%000007                   host_timing_cnt    <= timing_tlow;
%000001                 end else begin
%000001                   host_sda_drive_low <= 1'b0;
%000001                   host_timing_cnt    <= timing_tlow;
%000001                   host_state         <= HOST_WRITE_ACK;
%000001                   host_bit_idx       <= 4'h0;
                        end
                      end
                    end
                  end
                end
        
%000002         HOST_WRITE_ACK: begin
%000002           if (host_timing_done) begin
%000001             if (host_scl_drive_low) begin
%000001               host_scl_drive_low <= 1'b0;
%000001               host_timing_cnt    <= timing_thigh;
%000001             end else begin
%000001               host_ack_received  <= ~sda_in_q;
%000001               host_scl_drive_low <= 1'b1;
%000001               host_timing_cnt    <= timing_tlow;
        
%000001               if (sda_in_q && !host_cmd_nakok) begin
%000001                 host_state <= HOST_STOP;
%000000               end else if (!fmt_fifo_empty) begin
%000000                 if (fmt_fifo_rdata[8]) begin
%000000                   host_state <= HOST_RSTART_SETUP;
%000000                 end else if (fmt_fifo_rdata[10]) begin
%000000                   host_read_byte_cnt <= fmt_fifo_rdata[7:0];
%000000                   host_read_rcont    <= fmt_fifo_rdata[11];
%000000                   host_read_stop     <= fmt_fifo_rdata[9];
%000000                   host_state         <= HOST_READ_BYTE;
%000000                   host_bit_idx       <= 4'h0;
%000000                   host_sda_drive_low <= 1'b0;
%000000                   fmt_pop_req        <= 1'b1;
%000000                 end else begin
%000000                   host_shift_reg     <= fmt_fifo_rdata[7:0];
%000000                   host_sda_drive_low <= ~fmt_fifo_rdata[7];
%000000                   host_state         <= HOST_WRITE_BYTE;
%000000                   host_bit_idx       <= 4'h0;
%000000                   fmt_pop_req        <= 1'b1;
                        end
%000000               end else begin
%000000                 host_state <= HOST_STOP;
                      end
                    end
                  end
                end
        
%000000         HOST_READ_BYTE: begin
%000000           if (host_timing_done) begin
%000000             if (host_scl_drive_low) begin
%000000               host_scl_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_thigh;
%000000               host_sda_drive_low <= 1'b0;
%000000             end else begin
%000000               host_read_shift <= {host_read_shift[6:0], sda_in_q};
%000000               host_scl_drive_low <= 1'b1;
%000000               host_timing_cnt    <= timing_tlow;
        
%000000               if (host_bit_idx < 4'd7) begin
%000000                 host_bit_idx <= host_bit_idx + 4'h1;
%000000               end else begin
%000000                 host_state   <= HOST_READ_ACK;
%000000                 host_bit_idx <= 4'h0;
                      end
                    end
                  end
                end
        
%000000         HOST_READ_ACK: begin
%000000           if (host_timing_done) begin
%000000             if (host_scl_drive_low && host_bit_idx == 4'h0) begin
%000000               if (host_read_rcont) begin
%000000                 host_sda_drive_low <= 1'b1;
%000000               end else begin
%000000                 host_sda_drive_low <= 1'b0;
                      end
%000000               host_scl_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_thigh;
%000000               host_bit_idx       <= 4'h1;
%000000             end else begin
%000000               host_scl_drive_low <= 1'b1;
%000000               host_sda_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_tlow;
%000000               host_bit_idx       <= 4'h0;
        
%000000               if (host_read_byte_cnt > 8'h1) begin
%000000                 host_read_byte_cnt <= host_read_byte_cnt - 8'h1;
%000000                 host_state <= HOST_READ_BYTE;
%000000               end else if (host_read_stop) begin
%000000                 host_state <= HOST_STOP;
%000000               end else if (!fmt_fifo_empty) begin
%000000                 if (fmt_fifo_rdata[8]) begin
%000000                   host_state <= HOST_RSTART_SETUP;
%000000                 end else begin
%000000                   host_state <= HOST_IDLE;
                        end
%000000               end else begin
%000000                 host_state <= HOST_IDLE;
                      end
                    end
                  end
                end
        
%000003         HOST_STOP: begin
%000003           if (host_timing_done) begin
%000001             if (host_bit_idx == 4'h0) begin
%000001               host_scl_drive_low <= 1'b1;
%000001               host_sda_drive_low <= 1'b1;
%000001               host_timing_cnt    <= timing_tlow;
%000001               host_bit_idx       <= 4'h1;
%000001             end else if (host_bit_idx == 4'h1) begin
%000001               host_scl_drive_low <= 1'b0;
%000001               host_timing_cnt    <= timing_tsu_sto;
%000001               host_bit_idx       <= 4'h2;
%000001             end else begin
%000001               host_sda_drive_low <= 1'b0;
%000001               host_scl_drive_low <= 1'b0;
%000001               host_timing_cnt    <= timing_t_buf;
%000001               host_state         <= HOST_WAIT_BUS_FREE;
%000001               host_bit_idx       <= 4'h0;
                    end
                  end
                end
        
%000000         HOST_RSTART_SETUP: begin
%000000           if (host_timing_done) begin
%000000             if (host_bit_idx == 4'h0) begin
%000000               host_sda_drive_low <= 1'b0;
%000000               host_scl_drive_low <= 1'b1;
%000000               host_timing_cnt    <= timing_tlow;
%000000               host_bit_idx       <= 4'h1;
%000000             end else if (host_bit_idx == 4'h1) begin
%000000               host_scl_drive_low <= 1'b0;
%000000               host_timing_cnt    <= timing_tsu_sta;
%000000               host_bit_idx       <= 4'h2;
%000000             end else begin
%000000               host_sda_drive_low <= 1'b1;
%000000               host_timing_cnt    <= timing_thd_sta;
%000000               host_shift_reg     <= fmt_fifo_rdata[7:0];
%000000               fmt_pop_req        <= 1'b1;
%000000               host_state         <= HOST_ADDR_BYTE;
%000000               host_bit_idx       <= 4'h0;
                    end
                  end
                end
        
%000001         HOST_WAIT_BUS_FREE: begin
%000001           if (host_timing_done) begin
%000001             host_state <= HOST_IDLE;
                  end
                end
        
%000000         default: host_state <= HOST_IDLE;
              endcase
        
 000103       if (!ctrl_host_enable) begin
 000023         host_state         <= HOST_IDLE;
 000023         host_scl_drive_low <= 1'b0;
 000023         host_sda_drive_low <= 1'b0;
 000023         host_timing_cnt    <= 16'h0;
              end
            end
          end
        
          assign host_scl_oe = host_scl_drive_low;
          assign host_sda_oe = host_sda_drive_low;
        
%000000   logic rx_push_valid;
%000000   logic [7:0] rx_push_data;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_push_valid <= 1'b0;
%000005       rx_push_data  <= 8'h0;
 000126     end else begin
 000126       rx_push_valid <= 1'b0;
~000126       if (host_state == HOST_READ_ACK && host_timing_done &&
%000000           host_bit_idx != 4'h0) begin
%000000         rx_push_valid <= 1'b1;
%000000         rx_push_data  <= host_read_shift;
              end
            end
          end
        
          assign rx_fifo_push  = rx_push_valid;
          assign rx_fifo_wdata = rx_push_data;
        
%000000   logic tgt_scl_drive_low;
%000000   logic tgt_sda_drive_low;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tgt_state          <= TGT_IDLE;
%000005       tgt_addr_shift     <= 7'h0;
%000005       tgt_rw_bit         <= 1'b0;
%000005       tgt_bit_idx        <= 4'h0;
%000005       tgt_rx_shift       <= 8'h0;
%000005       tgt_tx_shift       <= 8'h0;
%000005       tgt_addr_match     <= 1'b0;
%000005       tgt_stretch_needed <= 1'b0;
%000005       tgt_scl_drive_low  <= 1'b0;
%000005       tgt_sda_drive_low  <= 1'b0;
%000005       acq_fifo_push      <= 1'b0;
%000005       acq_fifo_wdata     <= 10'h0;
%000005       tx_fifo_pop        <= 1'b0;
 000126     end else begin
 000126       acq_fifo_push  <= 1'b0;
 000126       tx_fifo_pop    <= 1'b0;
        
~000126       if (stop_det && tgt_state != TGT_IDLE) begin
%000000         if (tgt_addr_match) begin
%000000           acq_fifo_push  <= 1'b1;
%000000           acq_fifo_wdata <= {2'b10, 8'h0};
                end
%000000         tgt_state          <= TGT_IDLE;
%000000         tgt_scl_drive_low  <= 1'b0;
%000000         tgt_sda_drive_low  <= 1'b0;
%000000         tgt_stretch_needed <= 1'b0;
 000126       end else begin
        
 000126         case (tgt_state)
 000126           TGT_IDLE: begin
 000126             tgt_scl_drive_low  <= 1'b0;
 000126             tgt_sda_drive_low  <= 1'b0;
 000126             tgt_bit_idx        <= 4'h0;
 000126             tgt_addr_match     <= 1'b0;
 000126             tgt_stretch_needed <= 1'b0;
~000126             if (ctrl_target_enable && start_det) begin
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000               tgt_bit_idx <= 4'h0;
                    end
                  end
        
%000000           TGT_ADDR_RECV: begin
%000000             if (start_det) begin
%000000               tgt_bit_idx <= 4'h0;
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000             end else if (scl_rising) begin
%000000               if (tgt_bit_idx < 4'd7) begin
%000000                 tgt_addr_shift <= {tgt_addr_shift[5:0], sda_in_q};
%000000                 tgt_bit_idx    <= tgt_bit_idx + 4'h1;
%000000               end else begin
%000000                 tgt_rw_bit  <= sda_in_q;
%000000                 tgt_bit_idx <= 4'h0;
        
%000000                 tgt_addr_match <= ((tgt_addr_shift ^ target_address) & target_mask) == 7'h0;
                      end
%000000             end else if (scl_falling && tgt_bit_idx == 4'h0 && tgt_addr_shift != 7'h0) begin
%000000               if (tgt_addr_match) begin
%000000                 tgt_state         <= TGT_ADDR_ACK;
%000000                 tgt_sda_drive_low <= 1'b1;
        
%000000                 acq_fifo_push  <= 1'b1;
%000000                 acq_fifo_wdata <= {2'b01, tgt_addr_shift[6:0], tgt_rw_bit};
%000000               end else begin
%000000                 tgt_state         <= TGT_IDLE;
%000000                 tgt_sda_drive_low <= 1'b0;
                      end
                    end
                  end
        
%000000           TGT_ADDR_ACK: begin
%000000             if (scl_falling) begin
%000000               tgt_sda_drive_low <= 1'b0;
%000000               if (tgt_rw_bit) begin
%000000                 if (tx_fifo_empty) begin
%000000                   tgt_state          <= TGT_STRETCH;
%000000                   tgt_scl_drive_low  <= 1'b1;
%000000                   tgt_stretch_needed <= 1'b1;
%000000                 end else begin
%000000                   tgt_tx_shift      <= tx_fifo_rdata;
%000000                   tx_fifo_pop       <= 1'b1;
%000000                   tgt_state         <= TGT_DATA_TX;
%000000                   tgt_bit_idx       <= 4'h0;
%000000                   tgt_sda_drive_low <= ~tx_fifo_rdata[7];
                        end
%000000               end else begin
%000000                 tgt_state   <= TGT_DATA_RX;
%000000                 tgt_bit_idx <= 4'h0;
                      end
                    end
                  end
        
%000000           TGT_DATA_RX: begin
%000000             if (start_det) begin
%000000               if (tgt_addr_match) begin
%000000                 acq_fifo_push  <= 1'b1;
%000000                 acq_fifo_wdata <= {2'b11, 8'h0};
                      end
%000000               tgt_bit_idx <= 4'h0;
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000             end else if (scl_rising) begin
%000000               tgt_rx_shift <= {tgt_rx_shift[6:0], sda_in_q};
%000000               tgt_bit_idx  <= tgt_bit_idx + 4'h1;
%000000             end else if (scl_falling && tgt_bit_idx == 4'd8) begin
%000000               tgt_bit_idx <= 4'h0;
%000000               if (acq_fifo_full) begin
%000000                 tgt_state          <= TGT_STRETCH;
%000000                 tgt_scl_drive_low  <= 1'b1;
%000000                 tgt_stretch_needed <= 1'b1;
%000000               end else begin
%000000                 acq_fifo_push     <= 1'b1;
%000000                 acq_fifo_wdata    <= {2'b00, tgt_rx_shift};
%000000                 tgt_state         <= TGT_DATA_RX_ACK;
%000000                 tgt_sda_drive_low <= 1'b1;
                      end
                    end
                  end
        
%000000           TGT_DATA_RX_ACK: begin
%000000             if (start_det) begin
%000000               tgt_sda_drive_low <= 1'b0;
%000000               if (tgt_addr_match) begin
%000000                 acq_fifo_push  <= 1'b1;
%000000                 acq_fifo_wdata <= {2'b11, 8'h0};
                      end
%000000               tgt_bit_idx <= 4'h0;
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000             end else if (scl_falling) begin
%000000               tgt_sda_drive_low <= 1'b0;
%000000               tgt_state         <= TGT_DATA_RX;
%000000               tgt_bit_idx       <= 4'h0;
                    end
                  end
        
%000000           TGT_DATA_TX: begin
%000000             if (start_det) begin
%000000               tgt_sda_drive_low <= 1'b0;
%000000               if (tgt_addr_match) begin
%000000                 acq_fifo_push  <= 1'b1;
%000000                 acq_fifo_wdata <= {2'b11, 8'h0};
                      end
%000000               tgt_bit_idx <= 4'h0;
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000             end else if (scl_falling) begin
%000000               if (tgt_bit_idx < 4'd7) begin
%000000                 tgt_bit_idx       <= tgt_bit_idx + 4'h1;
%000000                 tgt_sda_drive_low <= ~tgt_tx_shift[6 - tgt_bit_idx[2:0]];
%000000               end else begin
%000000                 tgt_sda_drive_low <= 1'b0;
%000000                 tgt_state         <= TGT_DATA_TX_ACK;
%000000                 tgt_bit_idx       <= 4'h0;
                      end
                    end
                  end
        
%000000           TGT_DATA_TX_ACK: begin
%000000             if (start_det) begin
%000000               if (tgt_addr_match) begin
%000000                 acq_fifo_push  <= 1'b1;
%000000                 acq_fifo_wdata <= {2'b11, 8'h0};
                      end
%000000               tgt_bit_idx <= 4'h0;
%000000               tgt_state   <= TGT_ADDR_RECV;
%000000             end else if (scl_rising) begin
%000000               if (sda_in_q) begin
%000000                 tgt_state <= TGT_IDLE;
                      end
%000000             end else if (scl_falling) begin
%000000               if (tx_fifo_empty) begin
%000000                 tgt_state          <= TGT_STRETCH;
%000000                 tgt_scl_drive_low  <= 1'b1;
%000000                 tgt_stretch_needed <= 1'b1;
%000000               end else begin
%000000                 tgt_tx_shift      <= tx_fifo_rdata;
%000000                 tx_fifo_pop       <= 1'b1;
%000000                 tgt_state         <= TGT_DATA_TX;
%000000                 tgt_bit_idx       <= 4'h0;
%000000                 tgt_sda_drive_low <= ~tx_fifo_rdata[7];
                      end
                    end
                  end
        
%000000           TGT_STRETCH: begin
%000000             tgt_scl_drive_low <= 1'b1;
~000126             if (tgt_rw_bit && !tx_fifo_empty) begin
%000000               tgt_scl_drive_low  <= 1'b0;
%000000               tgt_stretch_needed <= 1'b0;
%000000               tgt_tx_shift       <= tx_fifo_rdata;
%000000               tx_fifo_pop        <= 1'b1;
%000000               tgt_state          <= TGT_DATA_TX;
%000000               tgt_bit_idx        <= 4'h0;
%000000               tgt_sda_drive_low  <= ~tx_fifo_rdata[7];
%000000             end else if (!tgt_rw_bit && !acq_fifo_full) begin
%000000               tgt_scl_drive_low  <= 1'b0;
%000000               tgt_stretch_needed <= 1'b0;
%000000               acq_fifo_push      <= 1'b1;
%000000               acq_fifo_wdata     <= {2'b00, tgt_rx_shift};
%000000               tgt_state          <= TGT_DATA_RX_ACK;
%000000               tgt_sda_drive_low  <= 1'b1;
                    end
                  end
        
%000000           TGT_STOP_DET: begin
%000000             tgt_state          <= TGT_IDLE;
%000000             tgt_scl_drive_low  <= 1'b0;
%000000             tgt_sda_drive_low  <= 1'b0;
%000000             tgt_stretch_needed <= 1'b0;
                  end
        
%000000           default: tgt_state <= TGT_IDLE;
                endcase
              end
        
~000126       if (!ctrl_target_enable) begin
 000126         tgt_state          <= TGT_IDLE;
 000126         tgt_scl_drive_low  <= 1'b0;
 000126         tgt_sda_drive_low  <= 1'b0;
 000126         tgt_stretch_needed <= 1'b0;
              end
            end
          end
        
          assign tgt_scl_oe = tgt_scl_drive_low;
          assign tgt_sda_oe = tgt_sda_drive_low;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       host_timeout_cnt   <= 20'h0;
%000005       host_timeout_event <= 1'b0;
 000126     end else begin
 000126       host_timeout_event <= 1'b0;
~000126       if (host_timeout_en) begin
%000000         if (!scl_in_q) begin
%000000           if (host_timeout_cnt < host_timeout_val) begin
%000000             host_timeout_cnt <= host_timeout_cnt + 20'h1;
%000000           end else begin
%000000             host_timeout_event <= 1'b1;
                  end
%000000         end else begin
%000000           host_timeout_cnt <= 20'h0;
                end
 000126       end else begin
 000126         host_timeout_cnt <= 20'h0;
              end
            end
          end
        
%000000   logic sda_interference_det;
%000000   logic scl_interference_det;
%000000   logic sda_unstable_det;
        
 000686   always_comb begin
 000686     scl_interference_det = ctrl_host_enable && !host_scl_drive_low &&
~000686                            (host_state != HOST_IDLE) && !scl_in_q;
        
 000686     sda_interference_det = ctrl_host_enable && !host_sda_drive_low &&
 000686                            (host_state == HOST_WRITE_BYTE || host_state == HOST_ADDR_BYTE) &&
~000686                            !sda_in_q && scl_in_q;
        
 000686     sda_unstable_det = scl_in_q && scl_in_qq &&
 000686                        (sda_in_q != sda_in_qq) &&
~000686                        !start_det && !stop_det &&
 000686                        bus_active;
          end
        
%000000   logic fmt_overflow_det;
%000000   logic rx_overflow_det;
%000000   logic tx_overflow_det;
%000001   logic nak_det;
%000001   logic trans_complete_det;
        
 000686   always_comb begin
~000686     fmt_overflow_det = fmt_fifo_push && fmt_fifo_full;
~000686     rx_overflow_det  = rx_fifo_push && rx_fifo_full;
~000686     tx_overflow_det  = tx_fifo_push && tx_fifo_full;
        
 000686     nak_det = (host_state == HOST_ADDR_ACK || host_state == HOST_WRITE_ACK) &&
 000686               host_timing_done && !host_scl_drive_low &&
~000686               sda_in_q && !host_cmd_nakok;
        
 000686     trans_complete_det = (host_state != HOST_IDLE) &&
~000686                          fmt_fifo_empty &&
 000686                          (host_state == HOST_WAIT_BUS_FREE && host_timing_done);
          end
        
 000686   always_comb begin
 000686     intr_hw_set = '0;
        
~000532     if (fmt_fifo_level <= 7'd1 && ctrl_host_enable)
 000532       intr_hw_set[0] = 1'b1;
        
~000686     if (rx_fifo_level >= 7'd1 && ctrl_host_enable)
%000000       intr_hw_set[1] = 1'b1;
        
~000686     if (acq_fifo_level >= 7'd1 && ctrl_target_enable)
%000000       intr_hw_set[2] = 1'b1;
        
~000686     if (rx_overflow_det)
%000000       intr_hw_set[3] = 1'b1;
        
~000681     if (nak_det)
%000005       intr_hw_set[4] = 1'b1;
        
~000686     if (scl_interference_det)
%000000       intr_hw_set[5] = 1'b1;
        
~000686     if (sda_interference_det)
%000000       intr_hw_set[6] = 1'b1;
        
~000686     if (tgt_stretch_needed && host_timeout_event)
%000000       intr_hw_set[7] = 1'b1;
        
~000686     if (sda_unstable_det)
%000000       intr_hw_set[8] = 1'b1;
        
~000681     if (trans_complete_det)
%000005       intr_hw_set[9] = 1'b1;
        
~000686     if (tx_fifo_empty && ctrl_target_enable)
%000000       intr_hw_set[10] = 1'b1;
        
~000686     if (tx_fifo_level <= 7'd1 && ctrl_target_enable)
%000000       intr_hw_set[11] = 1'b1;
        
~000686     if (acq_fifo_full && ctrl_target_enable)
%000000       intr_hw_set[12] = 1'b1;
        
~000686     if (stop_det && tgt_addr_match && ctrl_target_enable)
%000000       intr_hw_set[13] = 1'b1;
        
~000686     if (host_timeout_event)
%000000       intr_hw_set[14] = 1'b1;
        
~000686     if (host_arb_lost)
%000000       intr_hw_set[15] = 1'b1;
          end
        
          assign alert_o = 1'b0;
        
        endmodule
        
