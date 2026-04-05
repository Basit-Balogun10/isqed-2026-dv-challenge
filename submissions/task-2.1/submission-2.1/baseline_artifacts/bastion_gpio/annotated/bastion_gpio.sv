//      // verilator_coverage annotation
        module bastion_gpio
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
%000001   output logic [31:0] tl_d_data_o,
%000000   output logic [7:0]  tl_d_source_o,
%000000   output logic        tl_d_error_o,
%000000   input  logic [31:0] gpio_i,
%000000   output logic [31:0] gpio_o,
%000001   output logic [31:0] gpio_oe_o,
%000000   output logic [31:0] intr_o,
%000000   output logic        alert_o
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
        
%000000   logic [31:0] reg_data_out;
%000001   logic [31:0] reg_dir;
%000000   logic [31:0] reg_intr_state;
%000000   logic [31:0] reg_intr_enable;
%000000   logic [31:0] reg_intr_test;
%000000   logic [31:0] reg_intr_ctrl_en_rising;
%000000   logic [31:0] reg_intr_ctrl_en_falling;
%000000   logic [31:0] reg_intr_ctrl_en_lvlhigh;
%000000   logic [31:0] reg_intr_ctrl_en_lvllow;
        
%000000   logic [31:0] gpio_sync_q1;
%000000   logic [31:0] gpio_sync_q2;
%000000   logic [31:0] gpio_sync_prev;
        
%000000   logic [31:0] rising_edge_det;
%000000   logic [31:0] falling_edge_det;
        
%000000   logic [31:0] intr_rising;
%000000   logic [31:0] intr_falling;
%000000   logic [31:0] intr_lvlhigh;
%000000   logic [31:0] intr_lvllow;
%000000   logic [31:0] intr_combined;
        
%000000   logic [31:0] intr_state_set;
%000001   logic [31:0] intr_state_clr;
        
 000015   logic        tl_req_valid;
%000004   logic        tl_is_write;
 000011   logic        tl_is_read;
%000007   logic [31:0] tl_addr;
%000002   logic [31:0] tl_wdata;
%000002   logic [31:0] tl_rdata;
%000000   logic        tl_error;
%000000   logic [7:0]  tl_source;
        
 000015   logic        pending_resp;
%000001   logic [31:0] resp_data;
%000000   logic [7:0]  resp_source;
%000000   logic        resp_error;
%000005   logic        resp_is_read;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       gpio_sync_q1 <= 32'h0;
%000005       gpio_sync_q2 <= 32'h0;
 000126     end else begin
 000126       gpio_sync_q1 <= gpio_i;
 000126       gpio_sync_q2 <= gpio_sync_q1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       gpio_sync_prev <= 32'h0;
 000126     end else begin
 000126       gpio_sync_prev <= gpio_sync_q2;
            end
          end
        
%000001   always_comb begin
%000001     rising_edge_det  = gpio_sync_q2 & ~gpio_sync_prev;
%000001     falling_edge_det = ~gpio_sync_q2 & gpio_sync_prev;
          end
        
%000001   always_comb begin
%000001     intr_rising  = rising_edge_det & reg_intr_ctrl_en_rising;
%000001     intr_falling = falling_edge_det & reg_intr_ctrl_en_falling;
%000001     intr_lvlhigh = gpio_sync_q2 & reg_intr_ctrl_en_lvlhigh;
%000001     intr_lvllow  = ~gpio_sync_q2 & reg_intr_ctrl_en_lvllow;
          end
        
%000001   always_comb begin
%000001     intr_combined = intr_rising | intr_falling | intr_lvlhigh | intr_lvllow;
          end
        
%000001   always_comb begin
%000001     intr_state_set = intr_combined | reg_intr_test;
          end
        
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
 000614       ADDR_DATA_IN: begin
 000614         tl_rdata = gpio_sync_q2;
              end
 000018       ADDR_DATA_OUT: begin
 000018         tl_rdata = reg_data_out;
              end
 000018       ADDR_DIR: begin
 000018         tl_rdata = reg_dir;
              end
 000018       ADDR_INTR_STATE: begin
 000018         tl_rdata = reg_intr_state;
              end
%000006       ADDR_INTR_ENABLE: begin
%000006         tl_rdata = reg_intr_enable;
              end
%000006       ADDR_INTR_TEST: begin
%000006         tl_rdata = reg_intr_test;
              end
%000006       ADDR_INTR_CTRL_EN_RISING: begin
%000006         tl_rdata = reg_intr_ctrl_en_rising;
              end
%000000       ADDR_INTR_CTRL_EN_FALLING: begin
%000000         tl_rdata = reg_intr_ctrl_en_falling;
              end
%000000       ADDR_INTR_CTRL_EN_LVLHIGH: begin
%000000         tl_rdata = reg_intr_ctrl_en_lvlhigh;
              end
%000000       ADDR_INTR_CTRL_EN_LVLLOW: begin
%000000         tl_rdata = reg_intr_ctrl_en_lvllow;
              end
%000000       ADDR_MASKED_OUT_LOWER: begin
%000000         tl_rdata = {16'h0, reg_data_out[15:0]};
              end
%000000       ADDR_MASKED_OUT_UPPER: begin
%000000         tl_rdata = {16'h0, reg_data_out[31:16]};
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
%000005       reg_data_out <= 32'h0;
 000126     end else begin
~000122       if (tl_is_write) begin
%000004         case (tl_addr)
%000001           ADDR_DATA_OUT: begin
%000001             reg_data_out <= tl_wdata;
                  end
%000000           ADDR_MASKED_OUT_LOWER: begin
%000000             for (int i = 0; i < 16; i++) begin
%000000               if (tl_wdata[i + 16]) begin
%000000                 reg_data_out[i] <= tl_wdata[i];
                      end
                    end
                  end
%000000           ADDR_MASKED_OUT_UPPER: begin
%000000             for (int i = 0; i < 16; i++) begin
%000000               if (tl_wdata[i + 16]) begin
%000000                 reg_data_out[i + 16] <= tl_wdata[i];
                      end
                    end
                  end
%000003           default: ;
                endcase
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_dir <= 32'h0;
~000125     end else if (tl_is_write && (tl_addr == ADDR_DIR)) begin
%000001       reg_dir <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_enable <= 32'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
%000000       reg_intr_enable <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_test <= 32'h0;
 000126     end else begin
~000126       if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
%000000         reg_intr_test <= tl_wdata;
 000126       end else begin
 000126         reg_intr_test <= 32'h0;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_ctrl_en_rising <= 32'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_RISING)) begin
%000000       reg_intr_ctrl_en_rising <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_ctrl_en_falling <= 32'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_FALLING)) begin
%000000       reg_intr_ctrl_en_falling <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_ctrl_en_lvlhigh <= 32'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_LVLHIGH)) begin
%000000       reg_intr_ctrl_en_lvlhigh <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_ctrl_en_lvllow <= 32'h0;
~000126     end else if (tl_is_write && (tl_addr == ADDR_INTR_CTRL_EN_LVLLOW)) begin
%000000       reg_intr_ctrl_en_lvllow <= tl_wdata;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       reg_intr_state <= 32'h0;
 000126     end else begin
 000126       reg_intr_state <= (reg_intr_state | intr_state_set) & ~intr_state_clr;
            end
          end
        
 000686   always_comb begin
 000686     intr_state_clr = 32'h0;
~000680     if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
%000006       intr_state_clr = tl_wdata;
            end
          end
        
%000001   always_comb begin
%000001     intr_o = reg_intr_state & reg_intr_enable;
          end
        
%000001   always_comb begin
%000001     gpio_o    = reg_data_out;
%000001     gpio_oe_o = reg_dir;
          end
        
          assign alert_o = 1'b0;
        
        endmodule
        
