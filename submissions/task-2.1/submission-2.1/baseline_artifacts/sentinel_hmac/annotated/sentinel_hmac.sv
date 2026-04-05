//      // verilator_coverage annotation
        import dv_common_pkg::*;
        
        module sentinel_hmac (
 000116   input  logic        clk_i,
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
%000002   output logic [31:0] tl_d_data_o,
%000000   output logic [7:0]  tl_d_source_o,
%000000   output logic        tl_d_error_o,
        
%000000   output logic [2:0]  intr_o,
%000000   output logic        alert_o
        );
        
          localparam int FifoDepth = 32;
        
%000000   function automatic logic [31:0] h_init(input int idx);
%000000     case (idx)
%000000       0: return 32'h6a09e667;
%000000       1: return 32'hbb67ae85;
%000000       2: return 32'h3c6ef372;
%000000       3: return 32'ha54ff53a;
%000000       4: return 32'h510e527f;
%000000       5: return 32'h9b05688c;
%000000       6: return 32'h1f83d9ab;
%000000       7: return 32'h5be0cd19;
%000000       default: return 32'h0;
            endcase
          endfunction
        
 000611   function automatic logic [31:0] k_const(input int idx);
 000611     case (idx)
%000000        0: return 32'h428a2f98;  1: return 32'h71374491;
%000000        2: return 32'hb5c0fbcf;  3: return 32'he9b5dba5;
%000000        4: return 32'h3956c25b;  5: return 32'h59f111f1;
%000000        6: return 32'h923f82a4;  7: return 32'hab1c5ed5;
%000000        8: return 32'hd807aa98;  9: return 32'h12835b01;
%000000       10: return 32'h243185be; 11: return 32'h550c7dc3;
%000000       12: return 32'h72be5d74; 13: return 32'h80deb1fe;
%000000       14: return 32'h9bdc06a7; 15: return 32'hc19bf174;
%000000       16: return 32'he49b69c1; 17: return 32'hefbe4786;
%000000       18: return 32'h0fc19dc6; 19: return 32'h240ca1cc;
%000000       20: return 32'h2de92c6f; 21: return 32'h4a7484aa;
%000000       22: return 32'h5cb0a9dc; 23: return 32'h76f988da;
%000000       24: return 32'h983e5152; 25: return 32'ha831c66d;
%000000       26: return 32'hb00327c8; 27: return 32'hbf597fc7;
%000000       28: return 32'hc6e00bf3; 29: return 32'hd5a79147;
%000000       30: return 32'h06ca6351; 31: return 32'h14292967;
%000000       32: return 32'h27b70a85; 33: return 32'h2e1b2138;
%000000       34: return 32'h4d2c6dfc; 35: return 32'h53380d13;
%000000       36: return 32'h650a7354; 37: return 32'h766a0abb;
%000000       38: return 32'h81c2c92e; 39: return 32'h92722c85;
%000000       40: return 32'ha2bfe8a1; 41: return 32'ha81a664b;
%000000       42: return 32'hc24b8b70; 43: return 32'hc76c51a3;
%000000       44: return 32'hd192e819; 45: return 32'hd6990624;
%000000       46: return 32'hf40e3585; 47: return 32'h106aa070;
%000000       48: return 32'h19a4c116; 49: return 32'h1e376c08;
%000000       50: return 32'h2748774c; 51: return 32'h34b0bcb5;
%000000       52: return 32'h391c0cb3; 53: return 32'h4ed8aa4a;
%000000       54: return 32'h5b9cca4f; 55: return 32'h682e6ff3;
%000000       56: return 32'h748f82ee; 57: return 32'h78a5636f;
%000000       58: return 32'h84c87814; 59: return 32'h8cc70208;
%000000       60: return 32'h90befffa; 61: return 32'ha4506ceb;
%000000       62: return 32'hbef9a3f7; 63: return 32'hc67178f2;
%000000       default: return 32'h0;
            endcase
          endfunction
        
 000611   function automatic logic [31:0] sigma0(input logic [31:0] x);
 000611     return ({x[6:0], x[31:7]} ^ {x[17:0], x[31:18]} ^ (x >> 3));
          endfunction
        
 000611   function automatic logic [31:0] sigma1(input logic [31:0] x);
 000611     return ({x[16:0], x[31:17]} ^ {x[18:0], x[31:19]} ^ (x >> 10));
          endfunction
        
 000611   function automatic logic [31:0] big_sigma0(input logic [31:0] x);
 000611     return ({x[1:0], x[31:2]} ^ {x[12:0], x[31:13]} ^ {x[21:0], x[31:22]});
          endfunction
        
 000611   function automatic logic [31:0] big_sigma1(input logic [31:0] x);
 000611     return ({x[5:0], x[31:6]} ^ {x[10:0], x[31:11]} ^ {x[24:0], x[31:25]});
          endfunction
        
 000611   function automatic logic [31:0] ch_fn(input logic [31:0] e_v, f_v, g_v);
 000611     return ((e_v & f_v) ^ (~e_v & g_v));
          endfunction
        
 000611   function automatic logic [31:0] maj_fn(input logic [31:0] a_v, b_v, c_v);
 000611     return ((a_v & b_v) ^ (a_v & c_v) ^ (b_v & c_v));
          endfunction
        
%000000   function automatic logic [31:0] endian_swap32(input logic [31:0] d);
%000000     return {d[7:0], d[15:8], d[23:16], d[31:24]};
          endfunction
        
          typedef enum logic [3:0] {
            ST_IDLE,
            ST_HMAC_IPAD,
            ST_SHA_WAIT_BLOCK,
            ST_SHA_ROUND,
            ST_SHA_DONE_BLOCK,
            ST_PAD_FILL,
            ST_PAD_LENGTH,
            ST_HMAC_INNER_DONE,
            ST_HMAC_OPAD,
            ST_HMAC_OUTER_MSG,
            ST_HMAC_OUTER_PAD,
            ST_HMAC_OUTER_LEN,
            ST_DONE
          } state_e;
        
%000000   state_e state_q, state_d;
        
%000001   logic        cfg_hmac_en;
%000000   logic        cfg_sha_en;
%000000   logic        cfg_endian_swap;
%000000   logic        cfg_digest_swap;
        
%000000   logic        cmd_hash_start;
%000000   logic        cmd_hash_process;
%000000   logic        cmd_hash_stop;
        
%000001   logic        wipe_secret;
        
%000000   logic [31:0] key_reg [8];
%000000   logic [31:0] digest_reg [8];
%000000   logic [31:0] msg_len_lo;
%000000   logic [31:0] msg_len_hi;
        
%000000   logic [2:0]  intr_state;
%000000   logic [2:0]  intr_enable;
        
          logic [31:0] fifo_mem [FifoDepth];
%000000   logic [5:0]  fifo_wptr;
%000000   logic [5:0]  fifo_rptr;
%000000   logic [5:0]  fifo_count;
%000000   logic        fifo_full;
%000001   logic        fifo_empty;
%000000   logic        fifo_push;
%000000   logic        fifo_pop;
%000000   logic [31:0] fifo_wdata;
%000000   logic [31:0] fifo_rdata;
%000001   logic        fifo_was_empty;
        
          logic [31:0] block_reg [16];
%000000   logic [3:0]  block_idx;
%000000   logic        block_ready;
        
%000000   logic [31:0] h_reg [8];
%000000   logic [31:0] a_val, b_val, c_val, d_val, e_val, f_val, g_val, h_val;
%000000   logic [6:0]  round_cnt;
          logic [31:0] w_reg [16];
%000000   logic [31:0] w_cur;
        
%000000   logic        hash_stop_pending;
%000000   logic        hash_process_pending;
%000000   logic [31:0] inner_digest [8];
%000000   logic        pad_extra_pending;
        
          logic [31:0] pad_block [16];
        
%000000   logic [63:0] total_msg_bits;
        
 000015   logic        tl_req_valid;
%000004   logic        tl_is_write;
 000011   logic        tl_is_read;
%000007   logic [31:0] tl_addr;
%000002   logic [31:0] tl_wdata;
%000001   logic [3:0]  tl_wmask;
%000002   logic [31:0] tl_rdata;
%000000   logic        tl_err;
 000015   logic        tl_resp_valid;
        
%000000   logic        sha_start_block;
        
%000000   logic        returning_from_pad;
%000000   logic        returning_from_hmac_ipad;
%000000   logic        returning_from_opad;
%000000   logic        returning_from_outer_msg;
%000000   logic        returning_from_outer_pad;
        
%000000   logic [3:0]  pad_start_word;
%000000   logic        pad_needs_extra_block;
%000001   logic [63:0] pad_total_bits;
        
          assign tl_a_ready_o = tl_d_ready_i;
        
          assign tl_req_valid = tl_a_valid_i & tl_a_ready_o;
          assign tl_is_write  = tl_req_valid & (tl_a_opcode_i == 3'd0);
          assign tl_is_read   = tl_req_valid & (tl_a_opcode_i == 3'd4);
          assign tl_addr      = tl_a_address_i;
          assign tl_wdata     = tl_a_data_i;
          assign tl_wmask     = tl_a_mask_i;
        
          assign tl_resp_valid = tl_req_valid;
        
          assign tl_d_valid_o  = tl_resp_valid;
 000475   assign tl_d_opcode_o = tl_is_write ? 3'd0 : 3'd1;
          assign tl_d_data_o   = tl_rdata;
          assign tl_d_source_o = tl_a_source_i;
          assign tl_d_error_o  = tl_err;
        
          assign fifo_count = fifo_wptr - fifo_rptr;
          assign fifo_full  = (fifo_count == FifoDepth[5:0]);
          assign fifo_empty = (fifo_count == 6'd0);
          assign fifo_rdata = fifo_mem[fifo_rptr[4:0]];
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       fifo_wptr <= 6'd0;
%000000     end else if (cmd_hash_start) begin
%000000       fifo_wptr <= 6'd0;
%000001     end else if (wipe_secret) begin
%000001       fifo_wptr <= 6'd0;
~000110     end else if (fifo_push && !fifo_full) begin
%000000       fifo_mem[fifo_wptr[4:0]] <= fifo_wdata;
%000000       fifo_wptr <= fifo_wptr + 6'd1;
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       fifo_rptr <= 6'd0;
%000000     end else if (cmd_hash_start) begin
%000000       fifo_rptr <= 6'd0;
%000001     end else if (wipe_secret) begin
%000001       fifo_rptr <= 6'd0;
~000110     end else if (fifo_pop && !fifo_empty) begin
%000000       fifo_rptr <= fifo_rptr + 6'd1;
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       fifo_was_empty <= 1'b1;
 000111     end else begin
 000111       fifo_was_empty <= fifo_empty;
            end
          end
        
%000001   logic intr_fifo_empty_pulse;
          assign intr_fifo_empty_pulse = fifo_empty & ~fifo_was_empty;
        
 000611   always_comb begin
 000611     cmd_hash_start   = 1'b0;
 000611     cmd_hash_process = 1'b0;
 000611     cmd_hash_stop    = 1'b0;
 000611     wipe_secret      = 1'b0;
 000611     fifo_push        = 1'b0;
 000611     fifo_wdata       = 32'd0;
 000611     tl_rdata         = 32'd0;
 000611     tl_err           = 1'b0;
        
 000587     if (tl_is_write) begin
 000024       case (tl_addr[7:0])
%000006         8'h04: begin
%000006           if (tl_wdata[0]) cmd_hash_start   = 1'b1;
%000006           if (tl_wdata[1]) cmd_hash_process = 1'b1;
%000006           if (tl_wdata[2]) cmd_hash_stop    = 1'b1;
                end
%000006         8'h0C: begin
%000006           if (tl_wdata[0]) wipe_secret = 1'b1;
                end
%000000         8'h64: begin
%000000           fifo_push = 1'b1;
~000024           fifo_wdata = cfg_endian_swap ? endian_swap32(tl_wdata) : tl_wdata;
                end
 000012         default: ;
              endcase
            end
        
 000545     if (tl_is_read) begin
 000066       case (tl_addr[7:0])
 000012         8'h00: tl_rdata = {28'd0, cfg_digest_swap, cfg_endian_swap, cfg_sha_en, cfg_hmac_en};
 000012         8'h04: tl_rdata = 32'd0;
~000066         8'h08: tl_rdata = {23'd0, (state_q == ST_IDLE || state_q == ST_DONE), fifo_count, fifo_empty, fifo_full};
 000012         8'h0C: tl_rdata = 32'd0;
%000006         8'h10: tl_rdata = 32'd0;
%000006         8'h14: tl_rdata = 32'd0;
%000006         8'h18: tl_rdata = 32'd0;
%000000         8'h1C: tl_rdata = 32'd0;
%000000         8'h20: tl_rdata = 32'd0;
%000000         8'h24: tl_rdata = 32'd0;
%000000         8'h28: tl_rdata = 32'd0;
%000000         8'h2C: tl_rdata = 32'd0;
~000066         8'h30: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[0]) : digest_reg[0];
~000066         8'h34: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[1]) : digest_reg[1];
~000066         8'h38: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[2]) : digest_reg[2];
~000066         8'h3C: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[3]) : digest_reg[3];
~000066         8'h40: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[4]) : digest_reg[4];
~000066         8'h44: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[5]) : digest_reg[5];
~000066         8'h48: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[6]) : digest_reg[6];
~000066         8'h4C: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[7]) : digest_reg[7];
%000000         8'h50: tl_rdata = msg_len_lo;
%000000         8'h54: tl_rdata = msg_len_hi;
%000000         8'h58: tl_rdata = {29'd0, intr_state};
%000000         8'h5C: tl_rdata = {29'd0, intr_enable};
%000000         8'h60: tl_rdata = 32'd0;
%000000         8'h64: tl_rdata = 32'd0;
%000000         default: begin
%000000           tl_rdata = 32'd0;
%000000           tl_err   = 1'b1;
                end
              endcase
            end
        
~000611     if (tl_req_valid && !tl_is_write && !tl_is_read) begin
%000000       tl_err = 1'b1;
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       cfg_hmac_en     <= 1'b0;
%000005       cfg_sha_en      <= 1'b0;
%000005       cfg_endian_swap <= 1'b0;
%000005       cfg_digest_swap <= 1'b0;
~000110     end else if (tl_is_write && tl_addr[7:0] == 8'h00) begin
%000001       cfg_hmac_en     <= tl_wdata[0];
%000001       cfg_sha_en      <= tl_wdata[1];
%000001       cfg_endian_swap <= tl_wdata[2];
%000001       cfg_digest_swap <= tl_wdata[3];
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
~000040       for (int i = 0; i < 8; i++) key_reg[i] <= 32'd0;
%000001     end else if (wipe_secret) begin
%000008       for (int i = 0; i < 8; i++) key_reg[i] <= 32'd0;
~000107     end else if (tl_is_write) begin
%000003       case (tl_addr[7:0])
%000000         8'h10: key_reg[0] <= tl_wdata;
%000000         8'h14: key_reg[1] <= tl_wdata;
%000000         8'h18: key_reg[2] <= tl_wdata;
%000000         8'h1C: key_reg[3] <= tl_wdata;
%000000         8'h20: key_reg[4] <= tl_wdata;
%000000         8'h24: key_reg[5] <= tl_wdata;
%000000         8'h28: key_reg[6] <= tl_wdata;
%000000         8'h2C: key_reg[7] <= tl_wdata;
%000003         default: ;
              endcase
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       intr_state <= 3'd0;
 000111     end else begin
~000111       if (state_q != ST_DONE && state_d == ST_DONE)
%000000         intr_state[0] <= 1'b1;
~000111       if (intr_fifo_empty_pulse)
%000000         intr_state[1] <= 1'b1;
        
~000111       if (tl_is_write && tl_addr[7:0] == 8'h60) begin
%000000         intr_state <= intr_state | tl_wdata[2:0];
              end
        
~000111       if (tl_is_write && tl_addr[7:0] == 8'h58) begin
%000000         intr_state <= intr_state & ~tl_wdata[2:0];
              end
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       intr_enable <= 3'd0;
~000111     end else if (tl_is_write && tl_addr[7:0] == 8'h5C) begin
%000000       intr_enable <= tl_wdata[2:0];
            end
          end
        
          assign intr_o = intr_state & intr_enable;
          assign alert_o = 1'b0;
        
          assign total_msg_bits = {msg_len_hi, msg_len_lo};
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       msg_len_lo <= 32'd0;
%000005       msg_len_hi <= 32'd0;
%000000     end else if (cmd_hash_start) begin
%000000       msg_len_lo <= 32'd0;
%000000       msg_len_hi <= 32'd0;
~000111     end else if (fifo_push && !fifo_full) begin
%000000       {msg_len_hi, msg_len_lo} <= {msg_len_hi, msg_len_lo} + 64'd32;
            end
          end
        
%000000   logic [31:0] w_next;
 000611   always_comb begin
 000611     w_next = sigma1(w_reg[14]) + w_reg[9] + sigma0(w_reg[1]) + w_reg[0];
          end
        
 000611   always_comb begin
~000611     if (round_cnt < 7'd16)
 000611       w_cur = w_reg[round_cnt[3:0]];
            else
%000000       w_cur = w_reg[15];
          end
        
%000001   logic [31:0] t1, t2;
 000611   always_comb begin
 000611     t1 = h_val + big_sigma1(e_val) + ch_fn(e_val, f_val, g_val) + k_const(round_cnt[5:0]) + w_cur;
 000611     t2 = big_sigma0(a_val) + maj_fn(a_val, b_val, c_val);
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       state_q <= ST_IDLE;
 000111     end else begin
 000111       state_q <= state_d;
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       hash_stop_pending    <= 1'b0;
%000005       hash_process_pending <= 1'b0;
 000111     end else begin
~000111       if (cmd_hash_start) begin
%000000         hash_stop_pending    <= 1'b0;
%000000         hash_process_pending <= 1'b0;
 000111       end else begin
~000111         if (cmd_hash_stop)    hash_stop_pending    <= 1'b1;
~000111         if (cmd_hash_process) hash_process_pending <= 1'b1;
~000111         if (state_d == ST_PAD_FILL || state_d == ST_PAD_LENGTH)
%000000           hash_stop_pending <= 1'b0;
~000111         if (state_d == ST_SHA_ROUND && state_q == ST_SHA_WAIT_BLOCK && !hash_stop_pending)
%000000           hash_process_pending <= 1'b0;
              end
            end
          end
        
 000611   always_comb begin
 000611     pad_start_word = block_idx;
 000492     if (cfg_hmac_en)
 000492       pad_total_bits = total_msg_bits + 64'd512;
            else
 000119       pad_total_bits = total_msg_bits;
 000611     pad_needs_extra_block = (pad_start_word >= 4'd14);
          end
        
 000611   always_comb begin
 009776     for (int i = 0; i < 16; i++) pad_block[i] = 32'd0;
        
 009776     for (int i = 0; i < 16; i++) begin
~009776       if (i[3:0] < pad_start_word)
%000000         pad_block[i] = block_reg[i];
            end
        
~000611     if (pad_start_word < 4'd16) begin
%000000       pad_block[pad_start_word] = 32'h80000000;
            end
        
~000611     if (!pad_needs_extra_block) begin
 000611       pad_block[14] = pad_total_bits[63:32];
 000611       pad_block[15] = pad_total_bits[31:0];
            end
          end
        
          logic [31:0] pad_len_block [16];
 000611   always_comb begin
 008554     for (int i = 0; i < 14; i++) pad_len_block[i] = 32'd0;
 000611     pad_len_block[14] = pad_total_bits[63:32];
 000611     pad_len_block[15] = pad_total_bits[31:0];
          end
        
          logic [31:0] ipad_block [16];
          logic [31:0] opad_block [16];
 000611   always_comb begin
 004888     for (int i = 0; i < 8; i++) begin
 004888       ipad_block[i] = key_reg[i] ^ 32'h36363636;
 004888       opad_block[i] = key_reg[i] ^ 32'h5c5c5c5c;
            end
 004888     for (int i = 8; i < 16; i++) begin
 004888       ipad_block[i] = 32'h36363636;
 004888       opad_block[i] = 32'h5c5c5c5c;
            end
          end
        
          logic [31:0] outer_msg_block [16];
%000001   logic [63:0] hmac_outer_total_bits;
 000611   always_comb begin
 000611     hmac_outer_total_bits = 64'd768;
 004888     for (int i = 0; i < 8; i++)
 004888       outer_msg_block[i] = inner_digest[i];
 000611     outer_msg_block[8]  = 32'h80000000;
 003055     for (int i = 9; i < 14; i++)
 003055       outer_msg_block[i] = 32'd0;
 000611     outer_msg_block[14] = hmac_outer_total_bits[63:32];
 000611     outer_msg_block[15] = hmac_outer_total_bits[31:0];
          end
        
 000611   always_comb begin
 000611     state_d = state_q;
 000611     sha_start_block = 1'b0;
        
 000611     case (state_q)
 000611       ST_IDLE: begin
~000611         if (cmd_hash_start && cfg_sha_en) begin
%000000           if (cfg_hmac_en)
%000000             state_d = ST_HMAC_IPAD;
                  else
%000000             state_d = ST_SHA_WAIT_BLOCK;
                end
              end
        
%000000       ST_HMAC_IPAD: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_SHA_WAIT_BLOCK: begin
%000000         if (hash_stop_pending) begin
%000000           state_d = ST_PAD_FILL;
%000000         end else if (block_ready) begin
%000000           sha_start_block = 1'b1;
%000000           state_d = ST_SHA_ROUND;
                end
              end
        
%000000       ST_SHA_ROUND: begin
%000000         if (round_cnt == 7'd63) begin
%000000           state_d = ST_SHA_DONE_BLOCK;
                end
              end
        
%000000       ST_SHA_DONE_BLOCK: begin
%000000         if (pad_extra_pending) begin
%000000           state_d = ST_PAD_LENGTH;
%000000         end else if (returning_from_pad && !cfg_hmac_en) begin
%000000           state_d = ST_DONE;
%000000         end else if (returning_from_pad && cfg_hmac_en) begin
%000000           state_d = ST_HMAC_INNER_DONE;
%000000         end else if (returning_from_hmac_ipad) begin
%000000           state_d = ST_SHA_WAIT_BLOCK;
%000000         end else if (returning_from_opad) begin
%000000           state_d = ST_HMAC_OUTER_MSG;
%000000         end else if (returning_from_outer_msg) begin
%000000           state_d = ST_DONE;
%000000         end else if (returning_from_outer_pad) begin
%000000           state_d = ST_HMAC_OUTER_LEN;
%000000         end else begin
%000000           state_d = ST_SHA_WAIT_BLOCK;
                end
              end
        
%000000       ST_PAD_FILL: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_PAD_LENGTH: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_HMAC_INNER_DONE: begin
%000000         state_d = ST_HMAC_OPAD;
              end
        
%000000       ST_HMAC_OPAD: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_HMAC_OUTER_MSG: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_HMAC_OUTER_PAD: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_HMAC_OUTER_LEN: begin
%000000         sha_start_block = 1'b1;
%000000         state_d = ST_SHA_ROUND;
              end
        
%000000       ST_DONE: begin
~000611         if (cmd_hash_start && cfg_sha_en) begin
%000000           if (cfg_hmac_en)
%000000             state_d = ST_HMAC_IPAD;
                  else
%000000             state_d = ST_SHA_WAIT_BLOCK;
                end
              end
        
%000000       default: state_d = ST_IDLE;
            endcase
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       returning_from_pad       <= 1'b0;
%000005       returning_from_hmac_ipad <= 1'b0;
%000005       returning_from_opad      <= 1'b0;
%000005       returning_from_outer_msg <= 1'b0;
%000005       returning_from_outer_pad <= 1'b0;
%000005       pad_extra_pending        <= 1'b0;
 000111     end else begin
~000111       if (cmd_hash_start) begin
%000000         returning_from_pad       <= 1'b0;
%000000         returning_from_hmac_ipad <= 1'b0;
%000000         returning_from_opad      <= 1'b0;
%000000         returning_from_outer_msg <= 1'b0;
%000000         returning_from_outer_pad <= 1'b0;
%000000         pad_extra_pending        <= 1'b0;
              end
        
%000000       if (state_q == ST_PAD_FILL) begin
%000000         if (pad_needs_extra_block) begin
%000000           returning_from_pad <= 1'b0;
%000000           pad_extra_pending  <= 1'b1;
%000000         end else begin
%000000           returning_from_pad <= 1'b1;
                end
%000000       end else if (state_q == ST_PAD_LENGTH) begin
%000000         returning_from_pad <= 1'b1;
%000000         pad_extra_pending  <= 1'b0;
~000111       end else if (state_q == ST_SHA_DONE_BLOCK && returning_from_pad) begin
%000000         returning_from_pad <= 1'b0;
              end
        
~000111       if (state_q == ST_SHA_DONE_BLOCK && pad_extra_pending)
%000000         pad_extra_pending <= 1'b0;
        
%000000       if (state_q == ST_HMAC_IPAD)
%000000         returning_from_hmac_ipad <= 1'b1;
~000111       else if (state_q == ST_SHA_DONE_BLOCK && returning_from_hmac_ipad)
%000000         returning_from_hmac_ipad <= 1'b0;
        
%000000       if (state_q == ST_HMAC_OPAD)
%000000         returning_from_opad <= 1'b1;
~000111       else if (state_q == ST_SHA_DONE_BLOCK && returning_from_opad)
%000000         returning_from_opad <= 1'b0;
        
%000000       if (state_q == ST_HMAC_OUTER_MSG)
%000000         returning_from_outer_msg <= 1'b1;
~000111       else if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_msg)
%000000         returning_from_outer_msg <= 1'b0;
        
%000000       if (state_q == ST_HMAC_OUTER_PAD)
%000000         returning_from_outer_pad <= 1'b1;
~000111       else if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_pad)
%000000         returning_from_outer_pad <= 1'b0;
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
%000005       block_idx   <= 4'd0;
%000005       block_ready <= 1'b0;
 000111     end else begin
%000000       if (cmd_hash_start) begin
%000000         block_idx   <= 4'd0;
%000000         block_ready <= 1'b0;
%000000       end else if (state_q == ST_SHA_DONE_BLOCK) begin
%000000         block_idx   <= 4'd0;
%000000         block_ready <= 1'b0;
~000111       end else if (state_q == ST_SHA_WAIT_BLOCK && !fifo_empty && !block_ready && !hash_stop_pending) begin
%000000         block_reg[block_idx] <= fifo_rdata;
%000000         block_idx <= block_idx + 4'd1;
%000000         if (block_idx == 4'd15) block_ready <= 1'b1;
              end
            end
          end
        
          assign fifo_pop = (state_q == ST_SHA_WAIT_BLOCK && !fifo_empty && !block_ready && !hash_stop_pending);
        
%000000   logic [31:0] final_h [8];
 000611   always_comb begin
 004888     for (int i = 0; i < 8; i++) begin
 004888       case (i)
 000611         0: final_h[i] = h_reg[0] + a_val;
 000611         1: final_h[i] = h_reg[1] + b_val;
 000611         2: final_h[i] = h_reg[2] + c_val;
 000611         3: final_h[i] = h_reg[3] + d_val;
 000611         4: final_h[i] = h_reg[4] + e_val;
 000611         5: final_h[i] = h_reg[5] + f_val;
 000611         6: final_h[i] = h_reg[6] + g_val;
 000611         default: final_h[i] = h_reg[7] + h_val;
              endcase
            end
          end
        
 000116   always_ff @(posedge clk_i or negedge rst_ni) begin
~000111     if (!rst_ni) begin
~000040       for (int i = 0; i < 8; i++) h_reg[i] <= 32'd0;
%000005       a_val <= 32'd0; b_val <= 32'd0; c_val <= 32'd0; d_val <= 32'd0;
%000005       e_val <= 32'd0; f_val <= 32'd0; g_val <= 32'd0; h_val <= 32'd0;
%000005       round_cnt <= 7'd0;
~000080       for (int i = 0; i < 16; i++) w_reg[i] <= 32'd0;
~000040       for (int i = 0; i < 8; i++) digest_reg[i] <= 32'd0;
~000040       for (int i = 0; i < 8; i++) inner_digest[i] <= 32'd0;
 000111     end else begin
~000111       if (cmd_hash_start) begin
%000000         for (int i = 0; i < 8; i++) h_reg[i] <= h_init(i);
              end
        
~000110       if (wipe_secret) begin
%000008         for (int i = 0; i < 8; i++) h_reg[i] <= 32'd0;
~000016         for (int i = 0; i < 16; i++) w_reg[i] <= 32'd0;
%000008         for (int i = 0; i < 8; i++) digest_reg[i] <= 32'd0;
%000001         a_val <= 32'd0; b_val <= 32'd0; c_val <= 32'd0; d_val <= 32'd0;
%000001         e_val <= 32'd0; f_val <= 32'd0; g_val <= 32'd0; h_val <= 32'd0;
              end
        
~000111       if (sha_start_block) begin
%000000         round_cnt <= 7'd0;
%000000         a_val <= h_reg[0]; b_val <= h_reg[1]; c_val <= h_reg[2]; d_val <= h_reg[3];
%000000         e_val <= h_reg[4]; f_val <= h_reg[5]; g_val <= h_reg[6]; h_val <= h_reg[7];
        
%000000         if (state_q == ST_HMAC_IPAD) begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= ipad_block[i];
%000000         end else if (state_q == ST_HMAC_OPAD) begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= opad_block[i];
%000000         end else if (state_q == ST_HMAC_OUTER_MSG) begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= outer_msg_block[i];
%000000         end else if (state_q == ST_PAD_FILL) begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= pad_block[i];
%000000         end else if (state_q == ST_PAD_LENGTH) begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= pad_len_block[i];
%000000         end else begin
%000000           for (int i = 0; i < 16; i++) w_reg[i] <= block_reg[i];
                end
              end
        
~000111       if (state_q == ST_SHA_ROUND) begin
%000000         h_val <= g_val;
%000000         g_val <= f_val;
%000000         f_val <= e_val;
%000000         e_val <= d_val + t1;
%000000         d_val <= c_val;
%000000         c_val <= b_val;
%000000         b_val <= a_val;
%000000         a_val <= t1 + t2;
        
%000000         if (round_cnt >= 7'd15) begin
%000000           for (int i = 0; i < 15; i++) w_reg[i] <= w_reg[i+1];
%000000           w_reg[15] <= w_next;
                end
        
%000000         round_cnt <= round_cnt + 7'd1;
              end
        
~000111       if (state_q == ST_SHA_DONE_BLOCK) begin
%000000         h_reg[0] <= h_reg[0] + a_val;
%000000         h_reg[1] <= h_reg[1] + b_val;
%000000         h_reg[2] <= h_reg[2] + c_val;
%000000         h_reg[3] <= h_reg[3] + d_val;
%000000         h_reg[4] <= h_reg[4] + e_val;
%000000         h_reg[5] <= h_reg[5] + f_val;
%000000         h_reg[6] <= h_reg[6] + g_val;
%000000         h_reg[7] <= h_reg[7] + h_val;
              end
        
~000111       if (state_q == ST_SHA_DONE_BLOCK && returning_from_pad) begin
%000000         if (cfg_hmac_en) begin
%000000           for (int i = 0; i < 8; i++)
%000000             inner_digest[i] <= final_h[i];
%000000         end else begin
%000000           for (int i = 0; i < 8; i++)
%000000             digest_reg[i] <= final_h[i];
                end
              end
        
~000111       if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_msg) begin
%000000         for (int i = 0; i < 8; i++)
%000000           digest_reg[i] <= final_h[i];
              end
        
~000111       if (state_q == ST_HMAC_INNER_DONE) begin
%000000         for (int i = 0; i < 8; i++) h_reg[i] <= h_init(i);
              end
            end
          end
        
        endmodule
        
