//      // verilator_coverage annotation
        module citadel_spi
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
%000000   output logic        tl_d_error_o,
%000001   output logic        sclk_o,
%000001   output logic [3:0]  csn_o,
%000000   output logic        mosi_o,
%000000   input  logic        miso_i,
%000000   output logic [3:0]  intr_o,
%000000   output logic        alert_o
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
        
%000001   logic        reg_spien;
%000000   logic        reg_output_en;
%000001   logic [15:0] reg_clkdiv;
%000001   logic [3:0]  reg_csn_lead;
%000001   logic [3:0]  reg_csn_trail;
%000001   logic [3:0]  reg_csn_idle;
%000001   logic        reg_cpol;
%000000   logic        reg_cpha;
%000001   logic [1:0]  reg_csid;
%000000   logic [2:0]  reg_error_enable;
%000000   logic [2:0]  reg_error_status;
%000001   logic [3:0]  reg_intr_state;
%000000   logic [3:0]  reg_intr_enable;
%000000   logic [3:0]  reg_intr_test;
        
%000000   logic [7:0]  tx_fifo_mem [TX_FIFO_DEPTH];
%000000   logic [3:0]  tx_fifo_wptr;
%000000   logic [3:0]  tx_fifo_rptr;
%000000   logic [4:0]  tx_fifo_cnt;
%000000   logic        tx_fifo_full;
%000001   logic        tx_fifo_empty;
%000000   logic        tx_fifo_push;
%000000   logic        tx_fifo_pop;
%000000   logic [7:0]  tx_fifo_wdata;
%000000   logic [7:0]  tx_fifo_rdata;
        
%000000   logic [7:0]  rx_fifo_mem [RX_FIFO_DEPTH];
%000000   logic [3:0]  rx_fifo_wptr;
%000000   logic [3:0]  rx_fifo_rptr;
%000000   logic [4:0]  rx_fifo_cnt;
%000000   logic        rx_fifo_full;
%000001   logic        rx_fifo_empty;
%000000   logic        rx_fifo_push;
%000001   logic        rx_fifo_pop;
%000000   logic [7:0]  rx_fifo_wdata;
%000000   logic [7:0]  rx_fifo_rdata;
        
%000000   logic [1:0]  cmd_fifo_mem_direction [CMD_FIFO_DEPTH];
%000000   logic        cmd_fifo_mem_csaat     [CMD_FIFO_DEPTH];
%000000   logic [1:0]  cmd_fifo_mem_speed     [CMD_FIFO_DEPTH];
%000000   logic [8:0]  cmd_fifo_mem_len       [CMD_FIFO_DEPTH];
%000000   logic [1:0]  cmd_fifo_wptr;
%000000   logic [1:0]  cmd_fifo_rptr;
%000000   logic [2:0]  cmd_fifo_cnt;
%000000   logic        cmd_fifo_full;
%000001   logic        cmd_fifo_empty;
%000000   logic        cmd_fifo_push;
%000000   logic        cmd_fifo_pop;
%000000   logic [1:0]  cmd_fifo_wdata_direction;
%000000   logic        cmd_fifo_wdata_csaat;
%000000   logic [1:0]  cmd_fifo_wdata_speed;
%000000   logic [8:0]  cmd_fifo_wdata_len;
%000000   logic [1:0]  cmd_fifo_rdata_direction;
%000000   logic        cmd_fifo_rdata_csaat;
%000000   logic [1:0]  cmd_fifo_rdata_speed;
%000000   logic [8:0]  cmd_fifo_rdata_len;
        
%000000   spi_fsm_e    fsm_state;
%000000   spi_fsm_e    fsm_next;
        
%000000   logic [15:0] clk_div_cnt;
%000000   logic        clk_div_tick;
%000000   logic        clk_div_active;
%000001   logic        sclk_int;
%000000   logic [3:0]  timing_cnt;
%000000   logic        timing_done;
        
%000000   logic [1:0]  active_cmd_direction;
%000000   logic        active_cmd_csaat;
%000000   logic [1:0]  active_cmd_speed;
%000000   logic [8:0]  active_cmd_len;
%000000   logic        active_cmd_valid;
%000000   logic [8:0]  byte_cnt;
%000000   logic [2:0]  bit_cnt;
%000000   logic [7:0]  shift_tx;
%000000   logic [7:0]  shift_rx;
%000000   logic        byte_done;
%000000   logic        segment_done;
%000000   logic        need_tx;
%000000   logic        need_rx;
%000000   logic        tx_underflow_evt;
%000000   logic        rx_overflow_evt;
%000000   logic        cmd_invalid_evt;
        
%000000   logic [2:0]  error_status_set;
%000000   logic [2:0]  error_status_clr;
%000001   logic [3:0]  intr_state_set;
%000000   logic [3:0]  intr_state_clr;
        
%000000   logic        spi_done_evt;
        
 000015   logic        tl_req_valid;
%000004   logic        tl_is_write;
 000011   logic        tl_is_read;
%000007   logic [31:0] tl_addr;
%000002   logic [31:0] tl_wdata;
%000005   logic [31:0] tl_rdata;
%000000   logic        tl_error;
%000000   logic [7:0]  tl_source;
        
 000015   logic        pending_resp;
%000003   logic [31:0] resp_data;
%000000   logic [7:0]  resp_source;
%000000   logic        resp_error;
%000005   logic        resp_is_read;
        
%000000   logic        leading_edge;
%000000   logic        trailing_edge;
%000000   logic        sample_edge;
%000000   logic        output_edge;
%000000   logic        first_bit_out;
        
 000686   always_comb begin
~000686     tl_req_valid = tl_a_valid_i & tl_a_ready_o;
~000686     tl_is_write  = tl_req_valid & ((tl_a_opcode_i == 3'd0) | (tl_a_opcode_i == 3'd1));
 000686     tl_is_read   = tl_req_valid & (tl_a_opcode_i == 3'd4);
 000686     tl_addr      = {tl_a_address_i[31:2], 2'b00};
 000686     tl_wdata     = tl_a_data_i;
 000686     tl_source    = tl_a_source_i;
          end
        
 000686   always_comb begin
~000686     tl_a_ready_o = !pending_resp | tl_d_ready_i;
          end
        
 000686   always_comb begin
 000686     tl_rdata = 32'h0;
 000686     tl_error = 1'b0;
        
 000686     case (tl_addr)
 000614       ADDR_CTRL: begin
 000614         tl_rdata = {30'h0, reg_output_en, reg_spien};
              end
 000018       ADDR_STATUS: begin
 000018         tl_rdata = {16'h0,
 000018                     cmd_fifo_empty, cmd_fifo_full,
 000018                     rx_fifo_cnt[3:0], rx_fifo_empty, rx_fifo_full,
 000018                     tx_fifo_cnt[3:0], tx_fifo_empty, tx_fifo_full,
 000018                     (fsm_state != FSM_IDLE), (fsm_state == FSM_IDLE)};
              end
 000018       ADDR_CONFIGOPTS: begin
 000018         tl_rdata = {2'b00, reg_cpha, reg_cpol,
 000018                     reg_csn_idle, reg_csn_trail, reg_csn_lead, reg_clkdiv};
              end
 000018       ADDR_CSID: begin
 000018         tl_rdata = {30'h0, reg_csid};
              end
%000006       ADDR_COMMAND: begin
%000006         tl_rdata = 32'h0;
              end
%000006       ADDR_TXDATA: begin
%000006         tl_rdata = 32'h0;
              end
%000006       ADDR_RXDATA: begin
%000006         tl_rdata = {24'h0, rx_fifo_rdata};
              end
%000000       ADDR_ERROR_ENABLE: begin
%000000         tl_rdata = {29'h0, reg_error_enable};
              end
%000000       ADDR_ERROR_STATUS: begin
%000000         tl_rdata = {29'h0, reg_error_status};
              end
%000000       ADDR_INTR_STATE: begin
%000000         tl_rdata = {28'h0, reg_intr_state};
              end
%000000       ADDR_INTR_ENABLE: begin
%000000         tl_rdata = {28'h0, reg_intr_enable};
              end
%000000       ADDR_INTR_TEST: begin
%000000         tl_rdata = {28'h0, reg_intr_test};
              end
%000000       default: begin
%000000         tl_rdata = 32'h0;
              end
            endcase
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       pending_resp <= 1'b0;
%000005       resp_data    <= 32'h0;
%000005       resp_source  <= 8'h0;
%000005       resp_error   <= 1'b0;
%000005       resp_is_read <= 1'b0;
 000126     end else begin
 000111       if (pending_resp & tl_d_ready_i) begin
 000015         pending_resp <= 1'b0;
              end
 000111       if (tl_req_valid) begin
 000015         pending_resp <= 1'b1;
 000015         resp_data    <= tl_rdata;
 000015         resp_source  <= tl_source;
 000015         resp_error   <= tl_error;
 000015         resp_is_read <= tl_is_read;
              end
            end
          end
        
 000686   always_comb begin
 000686     tl_d_valid_o  = pending_resp;
 000686     tl_d_data_o   = resp_data;
 000686     tl_d_source_o = resp_source;
 000686     tl_d_error_o  = resp_error;
 000686     tl_d_opcode_o = resp_is_read ? 3'd1 : 3'd0;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_spien     <= 1'b0;
%000005       reg_output_en <= 1'b0;
~000125     end else if (tl_is_write && (tl_addr == ADDR_CTRL)) begin
%000001       reg_spien     <= tl_wdata[0];
%000001       reg_output_en <= tl_wdata[1];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_clkdiv    <= 16'h0;
%000005       reg_csn_lead  <= 4'h0;
%000005       reg_csn_trail <= 4'h0;
%000005       reg_csn_idle  <= 4'h0;
%000005       reg_cpol      <= 1'b0;
%000005       reg_cpha      <= 1'b0;
~000125     end else if (tl_is_write && (tl_addr == ADDR_CONFIGOPTS)) begin
%000001       reg_clkdiv    <= tl_wdata[15:0];
%000001       reg_csn_lead  <= tl_wdata[19:16];
%000001       reg_csn_trail <= tl_wdata[23:20];
%000001       reg_csn_idle  <= tl_wdata[27:24];
%000001       reg_cpol      <= tl_wdata[28];
%000001       reg_cpha      <= tl_wdata[29];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_csid <= 2'h0;
~000125     end else if (tl_is_write && (tl_addr == ADDR_CSID)) begin
%000001       reg_csid <= tl_wdata[1:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_error_enable <= 3'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_ERROR_ENABLE)) begin
%000000       reg_error_enable <= tl_wdata[2:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_enable <= 4'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
%000000       reg_intr_enable <= tl_wdata[3:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_test <= 4'h0;
 000126     end else begin
~000126       if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
%000000         reg_intr_test <= tl_wdata[3:0];
 000126       end else begin
 000126         reg_intr_test <= 4'h0;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tx_fifo_wptr <= 4'h0;
%000005       tx_fifo_rptr <= 4'h0;
%000005       tx_fifo_cnt  <= 5'h0;
 000126     end else begin
~000126       if (tx_fifo_push && tx_fifo_pop) begin
%000000         tx_fifo_wptr <= tx_fifo_wptr + 4'h1;
%000000         tx_fifo_rptr <= tx_fifo_rptr + 4'h1;
~000126       end else if (tx_fifo_push && !tx_fifo_full) begin
%000000         tx_fifo_wptr <= tx_fifo_wptr + 4'h1;
%000000         tx_fifo_cnt  <= tx_fifo_cnt + 5'h1;
~000126       end else if (tx_fifo_pop && !tx_fifo_empty) begin
%000000         tx_fifo_rptr <= tx_fifo_rptr + 4'h1;
%000000         tx_fifo_cnt  <= tx_fifo_cnt - 5'h1;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i) begin
~000131     if (tx_fifo_push && !tx_fifo_full) begin
%000000       tx_fifo_mem[tx_fifo_wptr] <= tx_fifo_wdata;
            end
          end
        
%000001   always_comb begin
%000001     tx_fifo_rdata = tx_fifo_mem[tx_fifo_rptr];
%000001     tx_fifo_full  = (tx_fifo_cnt == 5'd16);
%000001     tx_fifo_empty = (tx_fifo_cnt == 5'd0);
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rx_fifo_wptr <= 4'h0;
%000005       rx_fifo_rptr <= 4'h0;
%000005       rx_fifo_cnt  <= 5'h0;
 000126     end else begin
~000126       if (rx_fifo_push && rx_fifo_pop) begin
%000000         rx_fifo_wptr <= rx_fifo_wptr + 4'h1;
%000000         rx_fifo_rptr <= rx_fifo_rptr + 4'h1;
~000126       end else if (rx_fifo_push && !rx_fifo_full) begin
%000000         rx_fifo_wptr <= rx_fifo_wptr + 4'h1;
%000000         rx_fifo_cnt  <= rx_fifo_cnt + 5'h1;
~000126       end else if (rx_fifo_pop && !rx_fifo_empty) begin
%000000         rx_fifo_rptr <= rx_fifo_rptr + 4'h1;
%000000         rx_fifo_cnt  <= rx_fifo_cnt - 5'h1;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i) begin
~000131     if (rx_fifo_push && !rx_fifo_full) begin
%000000       rx_fifo_mem[rx_fifo_wptr] <= rx_fifo_wdata;
            end
          end
        
%000001   always_comb begin
%000001     rx_fifo_rdata = rx_fifo_mem[rx_fifo_rptr];
%000001     rx_fifo_full  = (rx_fifo_cnt == 5'd16);
%000001     rx_fifo_empty = (rx_fifo_cnt == 5'd0);
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       cmd_fifo_wptr <= 2'h0;
%000005       cmd_fifo_rptr <= 2'h0;
%000005       cmd_fifo_cnt  <= 3'h0;
 000126     end else begin
~000126       if (cmd_fifo_push && cmd_fifo_pop) begin
%000000         cmd_fifo_wptr <= cmd_fifo_wptr + 2'h1;
%000000         cmd_fifo_rptr <= cmd_fifo_rptr + 2'h1;
~000126       end else if (cmd_fifo_push && !cmd_fifo_full) begin
%000000         cmd_fifo_wptr <= cmd_fifo_wptr + 2'h1;
%000000         cmd_fifo_cnt  <= cmd_fifo_cnt + 3'h1;
~000126       end else if (cmd_fifo_pop && !cmd_fifo_empty) begin
%000000         cmd_fifo_rptr <= cmd_fifo_rptr + 2'h1;
%000000         cmd_fifo_cnt  <= cmd_fifo_cnt - 3'h1;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i) begin
~000131     if (cmd_fifo_push && !cmd_fifo_full) begin
%000000       cmd_fifo_mem_direction[cmd_fifo_wptr] <= cmd_fifo_wdata_direction;
%000000       cmd_fifo_mem_csaat[cmd_fifo_wptr]     <= cmd_fifo_wdata_csaat;
%000000       cmd_fifo_mem_speed[cmd_fifo_wptr]     <= cmd_fifo_wdata_speed;
%000000       cmd_fifo_mem_len[cmd_fifo_wptr]       <= cmd_fifo_wdata_len;
            end
          end
        
%000001   always_comb begin
%000001     cmd_fifo_rdata_direction = cmd_fifo_mem_direction[cmd_fifo_rptr];
%000001     cmd_fifo_rdata_csaat     = cmd_fifo_mem_csaat[cmd_fifo_rptr];
%000001     cmd_fifo_rdata_speed     = cmd_fifo_mem_speed[cmd_fifo_rptr];
%000001     cmd_fifo_rdata_len       = cmd_fifo_mem_len[cmd_fifo_rptr];
%000001     cmd_fifo_full  = (cmd_fifo_cnt == 3'd4);
%000001     cmd_fifo_empty = (cmd_fifo_cnt == 3'd0);
          end
        
 000686   always_comb begin
 000686     tx_fifo_push  = 1'b0;
 000686     tx_fifo_wdata = 8'h0;
~000686     if (tl_is_write && (tl_addr == ADDR_TXDATA)) begin
%000000       tx_fifo_push  = 1'b1;
%000000       tx_fifo_wdata = tl_wdata[7:0];
            end
          end
        
 000686   always_comb begin
 000686     rx_fifo_pop = 1'b0;
~000680     if (tl_is_read && (tl_addr == ADDR_RXDATA)) begin
%000006       rx_fifo_pop = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     cmd_fifo_push           = 1'b0;
 000686     cmd_fifo_wdata_direction = 2'd0;
 000686     cmd_fifo_wdata_csaat     = 1'b0;
 000686     cmd_fifo_wdata_speed     = 2'd0;
 000686     cmd_fifo_wdata_len       = 9'd0;
 000686     cmd_invalid_evt          = 1'b0;
~000686     if (tl_is_write && (tl_addr == ADDR_COMMAND)) begin
%000000       if (cmd_fifo_full) begin
%000000         cmd_invalid_evt = 1'b1;
%000000       end else begin
%000000         cmd_fifo_push            = 1'b1;
%000000         cmd_fifo_wdata_len       = tl_wdata[8:0];
%000000         cmd_fifo_wdata_speed     = tl_wdata[10:9];
%000000         cmd_fifo_wdata_csaat     = tl_wdata[11];
%000000         cmd_fifo_wdata_direction = tl_wdata[13:12];
              end
            end
          end
        
%000001   always_comb begin
%000001     clk_div_active = (fsm_state != FSM_IDLE);
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       clk_div_cnt <= 16'h0;
 000126     end else begin
~000126       if (clk_div_active) begin
%000000         if (clk_div_cnt == reg_clkdiv) begin
%000000           clk_div_cnt <= 16'h0;
%000000         end else begin
%000000           clk_div_cnt <= clk_div_cnt + 16'h1;
                end
 000126       end else begin
 000126         clk_div_cnt <= 16'h0;
              end
            end
          end
        
 000686   always_comb begin
~000686     clk_div_tick = clk_div_active && (clk_div_cnt == reg_clkdiv);
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       sclk_int <= 1'b0;
 000126     end else begin
 000126       if (fsm_state != FSM_DATA_XFER) begin
 000126         sclk_int <= reg_cpol;
%000000       end else if (clk_div_tick) begin
%000000         sclk_int <= ~sclk_int;
              end
            end
          end
        
 000686   always_comb begin
 000464     if (reg_cpol) begin
~000464       leading_edge  = clk_div_tick && sclk_int;
~000464       trailing_edge = clk_div_tick && !sclk_int;
 000222     end else begin
~000222       leading_edge  = clk_div_tick && !sclk_int;
~000222       trailing_edge = clk_div_tick && sclk_int;
            end
          end
        
 000686   always_comb begin
~000686     if (reg_cpha) begin
%000000       sample_edge = trailing_edge;
%000000       output_edge = leading_edge;
 000686     end else begin
 000686       sample_edge = leading_edge;
 000686       output_edge = trailing_edge;
            end
          end
        
 000686   always_comb begin
~000686     need_tx = active_cmd_valid &&
 000686               (active_cmd_direction == DIR_TX || active_cmd_direction == DIR_BIDIR);
~000686     need_rx = active_cmd_valid &&
 000686               (active_cmd_direction == DIR_RX || active_cmd_direction == DIR_BIDIR);
          end
        
 000686   always_comb begin
~000686     byte_done    = (bit_cnt == 3'd7) && sample_edge;
~000686     segment_done = byte_done && (byte_cnt == active_cmd_len);
          end
        
 000686   always_comb begin
 000686     tx_underflow_evt = 1'b0;
~000686     if (fsm_state == FSM_DATA_XFER && need_tx && bit_cnt == 3'd0 &&
~000686         !first_bit_out && tx_fifo_empty && output_edge) begin
%000000       tx_underflow_evt = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     rx_overflow_evt = 1'b0;
~000686     if (fsm_state == FSM_DATA_XFER && byte_done && need_rx && rx_fifo_full) begin
%000000       rx_overflow_evt = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     tx_fifo_pop = 1'b0;
~000686     if (fsm_state == FSM_DATA_XFER && need_tx && byte_done && !tx_fifo_empty) begin
%000000       tx_fifo_pop = 1'b1;
            end
~000686     if (fsm_state == FSM_CS_SETUP && timing_done && need_tx && !tx_fifo_empty) begin
%000000       tx_fifo_pop = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     rx_fifo_push  = 1'b0;
 000686     rx_fifo_wdata = shift_rx;
~000686     if (fsm_state == FSM_DATA_XFER && byte_done && need_rx && !rx_fifo_full) begin
%000000       rx_fifo_push = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     cmd_fifo_pop = 1'b0;
 000686     spi_done_evt = 1'b0;
        
 000686     case (fsm_state)
 000686       FSM_IDLE: begin
~000686         if (reg_spien && !cmd_fifo_empty) begin
%000000           cmd_fifo_pop = 1'b1;
                end
              end
%000000       FSM_CS_HOLD: begin
%000000         if (timing_done) begin
%000000           spi_done_evt = 1'b1;
                end
              end
%000000       FSM_CS_IDLE: begin
~000686         if (timing_done && !cmd_fifo_empty) begin
%000000           cmd_fifo_pop = 1'b1;
                end
              end
%000000       default: ;
            endcase
        
~000686     if (fsm_state == FSM_DATA_XFER && segment_done && active_cmd_csaat && !cmd_fifo_empty) begin
%000000       cmd_fifo_pop = 1'b1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       active_cmd_direction <= 2'd0;
%000005       active_cmd_csaat     <= 1'b0;
%000005       active_cmd_speed     <= 2'd0;
%000005       active_cmd_len       <= 9'd0;
%000005       active_cmd_valid     <= 1'b0;
 000126     end else begin
~000126       if (cmd_fifo_pop && !cmd_fifo_empty) begin
%000000         active_cmd_direction <= cmd_fifo_rdata_direction;
%000000         active_cmd_csaat     <= cmd_fifo_rdata_csaat;
%000000         active_cmd_speed     <= cmd_fifo_rdata_speed;
%000000         active_cmd_len       <= cmd_fifo_rdata_len;
%000000         active_cmd_valid     <= 1'b1;
              end
~000126       if (fsm_state == FSM_CS_HOLD && timing_done) begin
%000000         active_cmd_valid <= 1'b0;
              end
~000126       if (fsm_state == FSM_CS_IDLE && timing_done && cmd_fifo_empty) begin
%000000         active_cmd_valid <= 1'b0;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fsm_state <= FSM_IDLE;
 000126     end else begin
 000126       fsm_state <= fsm_next;
            end
          end
        
 000686   always_comb begin
 000686     fsm_next = fsm_state;
        
 000686     case (fsm_state)
 000686       FSM_IDLE: begin
~000686         if (reg_spien && !cmd_fifo_empty) begin
%000000           fsm_next = FSM_CS_SETUP;
                end
              end
        
%000000       FSM_CS_SETUP: begin
%000000         if (timing_done) begin
%000000           fsm_next = FSM_DATA_XFER;
                end
              end
        
%000000       FSM_DATA_XFER: begin
%000000         if (segment_done) begin
%000000           if (active_cmd_csaat) begin
%000000             if (!cmd_fifo_empty) begin
%000000               fsm_next = FSM_DATA_XFER;
                    end
%000000           end else begin
%000000             fsm_next = FSM_CS_HOLD;
                  end
                end
              end
        
%000000       FSM_CS_HOLD: begin
%000000         if (timing_done) begin
%000000           fsm_next = FSM_CS_IDLE;
                end
              end
        
%000000       FSM_CS_IDLE: begin
%000000         if (timing_done) begin
%000000           if (!cmd_fifo_empty) begin
%000000             fsm_next = FSM_CS_SETUP;
%000000           end else begin
%000000             fsm_next = FSM_IDLE;
                  end
                end
              end
        
%000000       default: begin
%000000         fsm_next = FSM_IDLE;
              end
            endcase
        
~000686     if (!reg_spien && fsm_state != FSM_IDLE) begin
%000000       fsm_next = FSM_IDLE;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       timing_cnt <= 4'h0;
 000126     end else begin
 000126       case (fsm_state)
 000126         FSM_IDLE: begin
 000126           timing_cnt <= 4'h0;
                end
%000000         FSM_CS_SETUP: begin
~000091           if (clk_div_tick || reg_csn_lead == 4'h0) begin
%000000             if (timing_cnt < reg_csn_lead) begin
%000000               timing_cnt <= timing_cnt + 4'h1;
                    end
                  end
                end
%000000         FSM_CS_HOLD: begin
~000091           if (clk_div_tick || reg_csn_trail == 4'h0) begin
%000000             if (timing_cnt < reg_csn_trail) begin
%000000               timing_cnt <= timing_cnt + 4'h1;
                    end
                  end
                end
%000000         FSM_CS_IDLE: begin
~000091           if (clk_div_tick || reg_csn_idle == 4'h0) begin
%000000             if (timing_cnt < reg_csn_idle) begin
%000000               timing_cnt <= timing_cnt + 4'h1;
                    end
                  end
                end
%000000         FSM_DATA_XFER: begin
%000000           if (segment_done) begin
%000000             timing_cnt <= 4'h0;
                  end
                end
%000000         default: begin
%000000           timing_cnt <= 4'h0;
                end
              endcase
            end
          end
        
 000686   always_comb begin
 000686     timing_done = 1'b0;
 000686     case (fsm_state)
%000000       FSM_CS_SETUP: begin
%000000         if (reg_csn_lead == 4'h0) begin
%000000           timing_done = 1'b1;
%000000         end else begin
%000000           timing_done = (timing_cnt == reg_csn_lead);
                end
              end
%000000       FSM_CS_HOLD: begin
%000000         if (reg_csn_trail == 4'h0) begin
%000000           timing_done = 1'b1;
%000000         end else begin
%000000           timing_done = (timing_cnt == reg_csn_trail);
                end
              end
%000000       FSM_CS_IDLE: begin
%000000         if (reg_csn_idle == 4'h0) begin
%000000           timing_done = 1'b1;
%000000         end else begin
%000000           timing_done = (timing_cnt == reg_csn_idle);
                end
              end
 000686       default: timing_done = 1'b0;
            endcase
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       bit_cnt      <= 3'd0;
%000005       byte_cnt     <= 9'd0;
%000005       shift_tx     <= 8'h0;
%000005       shift_rx     <= 8'h0;
%000005       first_bit_out <= 1'b0;
 000126     end else begin
 000126       case (fsm_state)
%000000         FSM_CS_SETUP: begin
%000000           if (timing_done) begin
%000000             bit_cnt      <= 3'd0;
%000000             byte_cnt     <= 9'd0;
%000000             first_bit_out <= 1'b0;
%000000             if (need_tx && !tx_fifo_empty) begin
%000000               shift_tx <= tx_fifo_rdata;
%000000             end else begin
%000000               shift_tx <= 8'h0;
                    end
%000000             shift_rx <= 8'h0;
                  end
                end
        
%000000         FSM_DATA_XFER: begin
~000126           if (segment_done && active_cmd_csaat && !cmd_fifo_empty) begin
%000000             bit_cnt       <= 3'd0;
%000000             byte_cnt      <= 9'd0;
%000000             first_bit_out <= 1'b0;
%000000             if ((cmd_fifo_rdata_direction == DIR_TX || cmd_fifo_rdata_direction == DIR_BIDIR)
%000000                 && !tx_fifo_empty) begin
%000000               shift_tx <= tx_fifo_rdata;
%000000             end else begin
%000000               shift_tx <= 8'h0;
                    end
%000000             shift_rx <= 8'h0;
%000000           end else begin
%000000             if (output_edge && !first_bit_out) begin
%000000               first_bit_out <= 1'b1;
                    end
        
%000000             if (sample_edge) begin
%000000               shift_rx <= {shift_rx[6:0], miso_i};
%000000               if (bit_cnt == 3'd7) begin
%000000                 bit_cnt <= 3'd0;
%000000                 if (byte_cnt < active_cmd_len) begin
%000000                   byte_cnt <= byte_cnt + 9'd1;
%000000                   if (need_tx && !tx_fifo_empty) begin
%000000                     shift_tx <= tx_fifo_rdata;
                          end
                        end
%000000               end else begin
%000000                 bit_cnt <= bit_cnt + 3'd1;
                      end
                    end
        
%000000             if (output_edge && need_tx) begin
%000000               shift_tx <= {shift_tx[6:0], 1'b0};
                    end
                  end
                end
        
 000126         FSM_IDLE: begin
 000126           bit_cnt       <= 3'd0;
 000126           byte_cnt      <= 9'd0;
 000126           shift_tx      <= 8'h0;
 000126           shift_rx      <= 8'h0;
 000126           first_bit_out <= 1'b0;
                end
        
%000000         default: ;
              endcase
            end
          end
        
 000686   always_comb begin
~000686     if (reg_output_en) begin
%000000       mosi_o = (fsm_state == FSM_DATA_XFER && need_tx) ? shift_tx[7] : 1'b0;
 000686     end else begin
 000686       mosi_o = 1'b0;
            end
          end
        
 000686   always_comb begin
~000686     if (reg_output_en) begin
%000000       sclk_o = sclk_int;
 000686     end else begin
 000686       sclk_o = reg_cpol;
            end
          end
        
 000686   always_comb begin
 000686     csn_o = 4'hF;
~000686     if (reg_output_en) begin
%000000       case (fsm_state)
%000000         FSM_CS_SETUP, FSM_DATA_XFER, FSM_CS_HOLD: begin
%000000           csn_o[reg_csid] = 1'b0;
                end
%000000         default: ;
              endcase
            end
          end
        
 000686   always_comb begin
 000686     error_status_set = 3'h0;
~000686     if (tx_underflow_evt && reg_error_enable[0]) begin
%000000       error_status_set[0] = 1'b1;
            end
~000686     if (rx_overflow_evt && reg_error_enable[1]) begin
%000000       error_status_set[1] = 1'b1;
            end
~000686     if (cmd_invalid_evt && reg_error_enable[2]) begin
%000000       error_status_set[2] = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     error_status_clr = 3'h0;
~000686     if (tl_is_write && (tl_addr == ADDR_ERROR_STATUS)) begin
%000000       error_status_clr = tl_wdata[2:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_error_status <= 3'h0;
 000126     end else begin
 000126       reg_error_status <= (reg_error_status | error_status_set) & ~error_status_clr;
            end
          end
        
 000686   always_comb begin
 000686     intr_state_set = reg_intr_test;
~000686     if (spi_done_evt) begin
%000000       intr_state_set[0] = 1'b1;
            end
~000686     if (!rx_fifo_empty && rx_fifo_cnt >= 5'd4) begin
%000000       intr_state_set[1] = 1'b1;
            end
~000686     if (tx_fifo_cnt <= 5'd4) begin
 000686       intr_state_set[2] = 1'b1;
            end
~000686     if (|reg_error_status) begin
%000000       intr_state_set[3] = 1'b1;
            end
          end
        
 000686   always_comb begin
 000686     intr_state_clr = 4'h0;
~000686     if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
%000000       intr_state_clr = tl_wdata[3:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_state <= 4'h0;
 000126     end else begin
 000126       reg_intr_state <= (reg_intr_state | intr_state_set) & ~intr_state_clr;
            end
          end
        
%000001   always_comb begin
%000001     intr_o = reg_intr_state & reg_intr_enable;
          end
        
          assign alert_o = 1'b0;
        
        endmodule
        
