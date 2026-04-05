//      // verilator_coverage annotation
        import dv_common_pkg::*;
        
        module warden_timer (
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
        
%000000   output logic [2:0]  intr_o,
%000000   output logic        alert_o
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
        
~000063   logic [63:0] mtime_q;
~000064   logic [63:0] mtime_d;
%000001   logic [63:0] mtimecmp0_q;
%000001   logic [63:0] mtimecmp0_d;
%000000   logic [63:0] mtimecmp1_q;
%000000   logic [63:0] mtimecmp1_d;
%000000   logic [11:0] prescaler_q;
%000000   logic [11:0] prescaler_d;
%000000   logic [11:0] prescale_cnt_q;
%000000   logic [11:0] prescale_cnt_d;
        
%000000   logic        wd_enable_q;
%000000   logic        wd_enable_d;
%000000   logic        wd_lock_q;
%000000   logic        wd_lock_d;
%000000   logic [31:0] wd_bark_thresh_q;
%000000   logic [31:0] wd_bark_thresh_d;
%000000   logic [31:0] wd_bite_thresh_q;
%000000   logic [31:0] wd_bite_thresh_d;
%000000   logic [31:0] wd_count_q;
%000000   logic [31:0] wd_count_d;
        
%000001   logic [2:0]  intr_state_q;
%000001   logic [2:0]  intr_state_d;
%000000   logic [2:0]  intr_enable_q;
%000000   logic [2:0]  intr_enable_d;
%000000   logic [2:0]  intr_test_q;
%000000   logic [2:0]  intr_test_d;
        
%000001   logic        timer0_expired;
%000001   logic        timer1_expired;
%000000   logic        wd_bark;
%000000   logic        wd_bite;
        
 000015   logic        tl_txn_valid;
%000004   logic        tl_is_write;
 000011   logic        tl_is_read;
%000007   logic [31:0] tl_addr;
%000002   logic [31:0] tl_wdata;
%000001   logic [3:0]  tl_wmask;
%000000   logic [7:0]  tl_source;
%000001   logic [1:0]  tl_size;
        
 000015   logic        rsp_valid_q;
 000015   logic        rsp_valid_d;
%000003   logic [31:0] rsp_data_q;
%000005   logic [31:0] rsp_data_d;
%000000   logic [7:0]  rsp_source_q;
%000000   logic [7:0]  rsp_source_d;
%000000   logic        rsp_error_q;
%000000   logic        rsp_error_d;
%000005   logic [2:0]  rsp_opcode_q;
%000005   logic [2:0]  rsp_opcode_d;
        
%000000   logic        pet_write;
%000001   logic        prescale_tick;
%000001   logic        addr_valid;
~000063   logic [31:0] rd_data;
        
%000002   logic [31:0] masked_wdata;
        
 000531   assign masked_wdata[31:24] = tl_wmask[3] ? tl_wdata[31:24] : 8'h00;
 000531   assign masked_wdata[23:16] = tl_wmask[2] ? tl_wdata[23:16] : 8'h00;
 000531   assign masked_wdata[15:8]  = tl_wmask[1] ? tl_wdata[15:8]  : 8'h00;
 000531   assign masked_wdata[7:0]   = tl_wmask[0] ? tl_wdata[7:0]   : 8'h00;
        
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
        
 000686   always_comb begin
 000686     prescale_cnt_d = prescale_cnt_q;
 000686     mtime_d        = mtime_q;
        
~000686     if (prescale_tick) begin
 000686       prescale_cnt_d = 12'd0;
 000686       mtime_d        = mtime_q + 64'd1;
%000000     end else begin
%000000       prescale_cnt_d = prescale_cnt_q + 12'd1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       prescale_cnt_q <= 12'd0;
 000126     end else begin
 000126       prescale_cnt_q <= prescale_cnt_d;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       mtime_q <= 64'd0;
 000126     end else begin
 000126       mtime_q <= mtime_d;
            end
          end
        
          assign pet_write = tl_is_write & (tl_addr == ADDR_WATCHDOG_PET);
        
 000686   always_comb begin
 000686     wd_count_d = wd_count_q;
        
%000000     if (pet_write) begin
%000000       wd_count_d = 32'd0;
~000686     end else if (wd_enable_q) begin
%000000       wd_count_d = wd_count_q + 32'd1;
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       wd_count_q <= 32'd0;
 000126     end else begin
 000126       wd_count_q <= wd_count_d;
            end
          end
        
 000686   always_comb begin
 000686     intr_state_d = intr_state_q;
        
 000464     if (timer0_expired) begin
 000222       intr_state_d[0] = 1'b1;
            end
        
~000686     if (timer1_expired) begin
 000686       intr_state_d[1] = 1'b1;
            end
        
~000686     if (wd_bark) begin
%000000       intr_state_d[2] = 1'b1;
            end
        
~000686     if (tl_is_write && (tl_addr == ADDR_INTR_STATE)) begin
%000000       intr_state_d = intr_state_d & ~masked_wdata[2:0];
            end
        
~000686     if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
%000000       intr_state_d = intr_state_d | masked_wdata[2:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       intr_state_q <= 3'd0;
 000126     end else begin
 000126       intr_state_q <= intr_state_d;
            end
          end
        
 000686   always_comb begin
 000686     mtimecmp0_d = mtimecmp0_q;
        
~000680     if (tl_is_write && (tl_addr == ADDR_MTIMECMP0_LOW)) begin
%000006       if (tl_wmask[0]) mtimecmp0_d[7:0]   = tl_wdata[7:0];
%000006       if (tl_wmask[1]) mtimecmp0_d[15:8]   = tl_wdata[15:8];
%000006       if (tl_wmask[2]) mtimecmp0_d[23:16]  = tl_wdata[23:16];
%000006       if (tl_wmask[3]) mtimecmp0_d[31:24]  = tl_wdata[31:24];
            end
        
~000680     if (tl_is_write && (tl_addr == ADDR_MTIMECMP0_HIGH)) begin
%000006       if (tl_wmask[0]) mtimecmp0_d[39:32]  = tl_wdata[7:0];
%000006       if (tl_wmask[1]) mtimecmp0_d[47:40]  = tl_wdata[15:8];
%000006       if (tl_wmask[2]) mtimecmp0_d[55:48]  = tl_wdata[23:16];
%000006       if (tl_wmask[3]) mtimecmp0_d[63:56]  = tl_wdata[31:24];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       mtimecmp0_q <= 64'd0;
 000126     end else begin
 000126       mtimecmp0_q <= mtimecmp0_d;
            end
          end
        
 000686   always_comb begin
 000686     mtimecmp1_d = mtimecmp1_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_MTIMECMP1_LOW)) begin
%000000       if (tl_wmask[0]) mtimecmp1_d[7:0]   = tl_wdata[7:0];
%000000       if (tl_wmask[1]) mtimecmp1_d[15:8]   = tl_wdata[15:8];
%000000       if (tl_wmask[2]) mtimecmp1_d[23:16]  = tl_wdata[23:16];
%000000       if (tl_wmask[3]) mtimecmp1_d[31:24]  = tl_wdata[31:24];
            end
        
~000686     if (tl_is_write && (tl_addr == ADDR_MTIMECMP1_HIGH)) begin
%000000       if (tl_wmask[0]) mtimecmp1_d[39:32]  = tl_wdata[7:0];
%000000       if (tl_wmask[1]) mtimecmp1_d[47:40]  = tl_wdata[15:8];
%000000       if (tl_wmask[2]) mtimecmp1_d[55:48]  = tl_wdata[23:16];
%000000       if (tl_wmask[3]) mtimecmp1_d[63:56]  = tl_wdata[31:24];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       mtimecmp1_q <= 64'd0;
 000126     end else begin
 000126       mtimecmp1_q <= mtimecmp1_d;
            end
          end
        
 000686   always_comb begin
 000686     prescaler_d = prescaler_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_PRESCALER)) begin
%000000       prescaler_d = masked_wdata[11:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       prescaler_q <= 12'd0;
 000126     end else begin
 000126       prescaler_q <= prescaler_d;
            end
          end
        
 000686   always_comb begin
 000686     wd_enable_d = wd_enable_q;
 000686     wd_lock_d   = wd_lock_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_WATCHDOG_CTRL)) begin
%000000       if (!wd_lock_q) begin
%000000         wd_enable_d = masked_wdata[0];
%000000         wd_lock_d   = masked_wdata[1];
%000000       end else begin
%000000         wd_lock_d = wd_lock_q | masked_wdata[1];
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       wd_enable_q <= 1'b0;
%000005       wd_lock_q   <= 1'b0;
 000126     end else begin
 000126       wd_enable_q <= wd_enable_d;
 000126       wd_lock_q   <= wd_lock_d;
            end
          end
        
 000686   always_comb begin
 000686     wd_bark_thresh_d = wd_bark_thresh_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_WATCHDOG_BARK_THRESH) && !wd_lock_q) begin
%000000       if (tl_wmask[0]) wd_bark_thresh_d[7:0]   = tl_wdata[7:0];
%000000       if (tl_wmask[1]) wd_bark_thresh_d[15:8]   = tl_wdata[15:8];
%000000       if (tl_wmask[2]) wd_bark_thresh_d[23:16]  = tl_wdata[23:16];
%000000       if (tl_wmask[3]) wd_bark_thresh_d[31:24]  = tl_wdata[31:24];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       wd_bark_thresh_q <= 32'd0;
 000126     end else begin
 000126       wd_bark_thresh_q <= wd_bark_thresh_d;
            end
          end
        
 000686   always_comb begin
 000686     wd_bite_thresh_d = wd_bite_thresh_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_WATCHDOG_BITE_THRESH) && !wd_lock_q) begin
%000000       if (tl_wmask[0]) wd_bite_thresh_d[7:0]   = tl_wdata[7:0];
%000000       if (tl_wmask[1]) wd_bite_thresh_d[15:8]   = tl_wdata[15:8];
%000000       if (tl_wmask[2]) wd_bite_thresh_d[23:16]  = tl_wdata[23:16];
%000000       if (tl_wmask[3]) wd_bite_thresh_d[31:24]  = tl_wdata[31:24];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       wd_bite_thresh_q <= 32'd0;
 000126     end else begin
 000126       wd_bite_thresh_q <= wd_bite_thresh_d;
            end
          end
        
 000686   always_comb begin
 000686     intr_enable_d = intr_enable_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_INTR_ENABLE)) begin
%000000       intr_enable_d = masked_wdata[2:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       intr_enable_q <= 3'd0;
 000126     end else begin
 000126       intr_enable_q <= intr_enable_d;
            end
          end
        
 000686   always_comb begin
 000686     intr_test_d = intr_test_q;
        
~000686     if (tl_is_write && (tl_addr == ADDR_INTR_TEST)) begin
%000000       intr_test_d = masked_wdata[2:0];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       intr_test_q <= 3'd0;
 000126     end else begin
 000126       intr_test_q <= intr_test_d;
            end
          end
        
 000686   always_comb begin
 000686     rd_data = 32'd0;
        
 000686     case (tl_addr)
 000614       ADDR_MTIME_LOW: begin
 000614         rd_data = mtime_q[31:0];
              end
        
 000018       ADDR_MTIME_HIGH: begin
 000018         rd_data = mtime_q[63:32];
              end
        
 000018       ADDR_MTIMECMP0_LOW: begin
 000018         rd_data = mtimecmp0_q[31:0];
              end
        
 000018       ADDR_MTIMECMP0_HIGH: begin
 000018         rd_data = mtimecmp0_q[63:32];
              end
        
%000006       ADDR_MTIMECMP1_LOW: begin
%000006         rd_data = mtimecmp1_q[31:0];
              end
        
%000006       ADDR_MTIMECMP1_HIGH: begin
%000006         rd_data = mtimecmp1_q[63:32];
              end
        
%000006       ADDR_PRESCALER: begin
%000006         rd_data = {20'd0, prescaler_q};
              end
        
%000000       ADDR_WATCHDOG_CTRL: begin
%000000         rd_data = {30'd0, wd_lock_q, wd_enable_q};
              end
        
%000000       ADDR_WATCHDOG_BARK_THRESH: begin
%000000         rd_data = wd_bark_thresh_q;
              end
        
%000000       ADDR_WATCHDOG_BITE_THRESH: begin
%000000         rd_data = wd_bite_thresh_q;
              end
        
%000000       ADDR_WATCHDOG_PET: begin
%000000         rd_data = 32'd0;
              end
        
%000000       ADDR_WATCHDOG_COUNT: begin
%000000         rd_data = wd_count_q;
              end
        
%000000       ADDR_INTR_STATE: begin
%000000         rd_data = {29'd0, intr_state_q};
              end
        
%000000       ADDR_INTR_ENABLE: begin
%000000         rd_data = {29'd0, intr_enable_q};
              end
        
%000000       ADDR_INTR_TEST: begin
%000000         rd_data = {29'd0, intr_test_q};
              end
        
%000000       default: begin
%000000         rd_data = 32'd0;
              end
            endcase
          end
        
 000686   always_comb begin
 000686     rsp_valid_d  = rsp_valid_q;
 000686     rsp_data_d   = rsp_data_q;
 000686     rsp_source_d = rsp_source_q;
 000686     rsp_error_d  = rsp_error_q;
 000686     rsp_opcode_d = rsp_opcode_q;
        
~000686     if (tl_d_ready_i | ~rsp_valid_q) begin
 000596       if (tl_txn_valid) begin
 000090         rsp_valid_d  = 1'b1;
 000090         rsp_source_d = tl_source;
~000090         rsp_error_d  = ~addr_valid;
        
 000066         if (tl_is_read) begin
 000066           rsp_data_d   = rd_data;
 000066           rsp_opcode_d = TL_OP_ACCESS_ACK_DATA;
 000024         end else begin
 000024           rsp_data_d   = 32'd0;
 000024           rsp_opcode_d = TL_OP_ACCESS_ACK;
                end
 000596       end else begin
 000596         rsp_valid_d = 1'b0;
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       rsp_valid_q  <= 1'b0;
%000005       rsp_data_q   <= 32'd0;
%000005       rsp_source_q <= 8'd0;
%000005       rsp_error_q  <= 1'b0;
%000005       rsp_opcode_q <= 3'd0;
 000126     end else begin
 000126       rsp_valid_q  <= rsp_valid_d;
 000126       rsp_data_q   <= rsp_data_d;
 000126       rsp_source_q <= rsp_source_d;
 000126       rsp_error_q  <= rsp_error_d;
 000126       rsp_opcode_q <= rsp_opcode_d;
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
        
