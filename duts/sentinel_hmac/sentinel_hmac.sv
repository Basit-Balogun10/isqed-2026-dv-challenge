import dv_common_pkg::*;

module sentinel_hmac (
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

  output logic [2:0]  intr_o,
  output logic        alert_o
);

  localparam int FifoDepth = 32;

  function automatic logic [31:0] h_init(input int idx);
    case (idx)
      0: return 32'h6a09e667;
      1: return 32'hbb67ae85;
      2: return 32'h3c6ef372;
      3: return 32'ha54ff53a;
      4: return 32'h510e527f;
      5: return 32'h9b05688c;
      6: return 32'h1f83d9ab;
      7: return 32'h5be0cd19;
      default: return 32'h0;
    endcase
  endfunction

  function automatic logic [31:0] k_const(input int idx);
    case (idx)
       0: return 32'h428a2f98;  1: return 32'h71374491;
       2: return 32'hb5c0fbcf;  3: return 32'he9b5dba5;
       4: return 32'h3956c25b;  5: return 32'h59f111f1;
       6: return 32'h923f82a4;  7: return 32'hab1c5ed5;
       8: return 32'hd807aa98;  9: return 32'h12835b01;
      10: return 32'h243185be; 11: return 32'h550c7dc3;
      12: return 32'h72be5d74; 13: return 32'h80deb1fe;
      14: return 32'h9bdc06a7; 15: return 32'hc19bf174;
      16: return 32'he49b69c1; 17: return 32'hefbe4786;
      18: return 32'h0fc19dc6; 19: return 32'h240ca1cc;
      20: return 32'h2de92c6f; 21: return 32'h4a7484aa;
      22: return 32'h5cb0a9dc; 23: return 32'h76f988da;
      24: return 32'h983e5152; 25: return 32'ha831c66d;
      26: return 32'hb00327c8; 27: return 32'hbf597fc7;
      28: return 32'hc6e00bf3; 29: return 32'hd5a79147;
      30: return 32'h06ca6351; 31: return 32'h14292967;
      32: return 32'h27b70a85; 33: return 32'h2e1b2138;
      34: return 32'h4d2c6dfc; 35: return 32'h53380d13;
      36: return 32'h650a7354; 37: return 32'h766a0abb;
      38: return 32'h81c2c92e; 39: return 32'h92722c85;
      40: return 32'ha2bfe8a1; 41: return 32'ha81a664b;
      42: return 32'hc24b8b70; 43: return 32'hc76c51a3;
      44: return 32'hd192e819; 45: return 32'hd6990624;
      46: return 32'hf40e3585; 47: return 32'h106aa070;
      48: return 32'h19a4c116; 49: return 32'h1e376c08;
      50: return 32'h2748774c; 51: return 32'h34b0bcb5;
      52: return 32'h391c0cb3; 53: return 32'h4ed8aa4a;
      54: return 32'h5b9cca4f; 55: return 32'h682e6ff3;
      56: return 32'h748f82ee; 57: return 32'h78a5636f;
      58: return 32'h84c87814; 59: return 32'h8cc70208;
      60: return 32'h90befffa; 61: return 32'ha4506ceb;
      62: return 32'hbef9a3f7; 63: return 32'hc67178f2;
      default: return 32'h0;
    endcase
  endfunction

  function automatic logic [31:0] sigma0(input logic [31:0] x);
    return ({x[6:0], x[31:7]} ^ {x[17:0], x[31:18]} ^ (x >> 3));
  endfunction

  function automatic logic [31:0] sigma1(input logic [31:0] x);
    return ({x[16:0], x[31:17]} ^ {x[18:0], x[31:19]} ^ (x >> 10));
  endfunction

  function automatic logic [31:0] big_sigma0(input logic [31:0] x);
    return ({x[1:0], x[31:2]} ^ {x[12:0], x[31:13]} ^ {x[21:0], x[31:22]});
  endfunction

  function automatic logic [31:0] big_sigma1(input logic [31:0] x);
    return ({x[5:0], x[31:6]} ^ {x[10:0], x[31:11]} ^ {x[24:0], x[31:25]});
  endfunction

  function automatic logic [31:0] ch_fn(input logic [31:0] e_v, f_v, g_v);
    return ((e_v & f_v) ^ (~e_v & g_v));
  endfunction

  function automatic logic [31:0] maj_fn(input logic [31:0] a_v, b_v, c_v);
    return ((a_v & b_v) ^ (a_v & c_v) ^ (b_v & c_v));
  endfunction

  function automatic logic [31:0] endian_swap32(input logic [31:0] d);
    return {d[7:0], d[15:8], d[23:16], d[31:24]};
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

  state_e state_q, state_d;

  logic        cfg_hmac_en;
  logic        cfg_sha_en;
  logic        cfg_endian_swap;
  logic        cfg_digest_swap;

  logic        cmd_hash_start;
  logic        cmd_hash_process;
  logic        cmd_hash_stop;

  logic        wipe_secret;

  logic [31:0] key_reg [8];
  logic [31:0] digest_reg [8];
  logic [31:0] msg_len_lo;
  logic [31:0] msg_len_hi;

  logic [2:0]  intr_state;
  logic [2:0]  intr_enable;

  logic [31:0] fifo_mem [FifoDepth];
  logic [5:0]  fifo_wptr;
  logic [5:0]  fifo_rptr;
  logic [5:0]  fifo_count;
  logic        fifo_full;
  logic        fifo_empty;
  logic        fifo_push;
  logic        fifo_pop;
  logic [31:0] fifo_wdata;
  logic [31:0] fifo_rdata;
  logic        fifo_was_empty;

  logic [31:0] block_reg [16];
  logic [3:0]  block_idx;
  logic        block_ready;

  logic [31:0] h_reg [8];
  logic [31:0] a_val, b_val, c_val, d_val, e_val, f_val, g_val, h_val;
  logic [6:0]  round_cnt;
  logic [31:0] w_reg [16];
  logic [31:0] w_cur;

  logic        hash_stop_pending;
  logic        hash_process_pending;
  logic [31:0] inner_digest [8];
  logic        pad_extra_pending;

  logic [31:0] pad_block [16];

  logic [63:0] total_msg_bits;

  logic        tl_req_valid;
  logic        tl_is_write;
  logic        tl_is_read;
  logic [31:0] tl_addr;
  logic [31:0] tl_wdata;
  logic [3:0]  tl_wmask;
  logic [31:0] tl_rdata;
  logic        tl_err;
  logic        tl_resp_valid;

  logic        sha_start_block;

  logic        returning_from_pad;
  logic        returning_from_hmac_ipad;
  logic        returning_from_opad;
  logic        returning_from_outer_msg;
  logic        returning_from_outer_pad;

  logic [3:0]  pad_start_word;
  logic        pad_needs_extra_block;
  logic [63:0] pad_total_bits;

  assign tl_a_ready_o = tl_d_ready_i;

  assign tl_req_valid = tl_a_valid_i & tl_a_ready_o;
  assign tl_is_write  = tl_req_valid & (tl_a_opcode_i == 3'd0);
  assign tl_is_read   = tl_req_valid & (tl_a_opcode_i == 3'd4);
  assign tl_addr      = tl_a_address_i;
  assign tl_wdata     = tl_a_data_i;
  assign tl_wmask     = tl_a_mask_i;

  assign tl_resp_valid = tl_req_valid;

  assign tl_d_valid_o  = tl_resp_valid;
  assign tl_d_opcode_o = tl_is_write ? 3'd0 : 3'd1;
  assign tl_d_data_o   = tl_rdata;
  assign tl_d_source_o = tl_a_source_i;
  assign tl_d_error_o  = tl_err;

  assign fifo_count = fifo_wptr - fifo_rptr;
  assign fifo_full  = (fifo_count == FifoDepth[5:0]);
  assign fifo_empty = (fifo_count == 6'd0);
  assign fifo_rdata = fifo_mem[fifo_rptr[4:0]];

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fifo_wptr <= 6'd0;
    end else if (cmd_hash_start) begin
      fifo_wptr <= 6'd0;
    end else if (wipe_secret) begin
      fifo_wptr <= 6'd0;
    end else if (fifo_push && !fifo_full) begin
      fifo_mem[fifo_wptr[4:0]] <= fifo_wdata;
      fifo_wptr <= fifo_wptr + 6'd1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fifo_rptr <= 6'd0;
    end else if (cmd_hash_start) begin
      fifo_rptr <= 6'd0;
    end else if (wipe_secret) begin
      fifo_rptr <= 6'd0;
    end else if (fifo_pop && !fifo_empty) begin
      fifo_rptr <= fifo_rptr + 6'd1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      fifo_was_empty <= 1'b1;
    end else begin
      fifo_was_empty <= fifo_empty;
    end
  end

  logic intr_fifo_empty_pulse;
  assign intr_fifo_empty_pulse = fifo_empty & ~fifo_was_empty;

  always_comb begin
    cmd_hash_start   = 1'b0;
    cmd_hash_process = 1'b0;
    cmd_hash_stop    = 1'b0;
    wipe_secret      = 1'b0;
    fifo_push        = 1'b0;
    fifo_wdata       = 32'd0;
    tl_rdata         = 32'd0;
    tl_err           = 1'b0;

    if (tl_is_write) begin
      case (tl_addr[7:0])
        8'h04: begin
          if (tl_wdata[0]) cmd_hash_start   = 1'b1;
          if (tl_wdata[1]) cmd_hash_process = 1'b1;
          if (tl_wdata[2]) cmd_hash_stop    = 1'b1;
        end
        8'h0C: begin
          if (tl_wdata[0]) wipe_secret = 1'b1;
        end
        8'h64: begin
          fifo_push = 1'b1;
          fifo_wdata = cfg_endian_swap ? endian_swap32(tl_wdata) : tl_wdata;
        end
        default: ;
      endcase
    end

    if (tl_is_read) begin
      case (tl_addr[7:0])
        8'h00: tl_rdata = {28'd0, cfg_digest_swap, cfg_endian_swap, cfg_sha_en, cfg_hmac_en};
        8'h04: tl_rdata = 32'd0;
        8'h08: tl_rdata = {23'd0, (state_q == ST_IDLE || state_q == ST_DONE), fifo_count, fifo_empty, fifo_full};
        8'h0C: tl_rdata = 32'd0;
        8'h10: tl_rdata = 32'd0;
        8'h14: tl_rdata = 32'd0;
        8'h18: tl_rdata = 32'd0;
        8'h1C: tl_rdata = 32'd0;
        8'h20: tl_rdata = 32'd0;
        8'h24: tl_rdata = 32'd0;
        8'h28: tl_rdata = 32'd0;
        8'h2C: tl_rdata = 32'd0;
        8'h30: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[0]) : digest_reg[0];
        8'h34: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[1]) : digest_reg[1];
        8'h38: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[2]) : digest_reg[2];
        8'h3C: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[3]) : digest_reg[3];
        8'h40: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[4]) : digest_reg[4];
        8'h44: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[5]) : digest_reg[5];
        8'h48: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[6]) : digest_reg[6];
        8'h4C: tl_rdata = cfg_digest_swap ? endian_swap32(digest_reg[7]) : digest_reg[7];
        8'h50: tl_rdata = msg_len_lo;
        8'h54: tl_rdata = msg_len_hi;
        8'h58: tl_rdata = {29'd0, intr_state};
        8'h5C: tl_rdata = {29'd0, intr_enable};
        8'h60: tl_rdata = 32'd0;
        8'h64: tl_rdata = 32'd0;
        default: begin
          tl_rdata = 32'd0;
          tl_err   = 1'b1;
        end
      endcase
    end

    if (tl_req_valid && !tl_is_write && !tl_is_read) begin
      tl_err = 1'b1;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      cfg_hmac_en     <= 1'b0;
      cfg_sha_en      <= 1'b0;
      cfg_endian_swap <= 1'b0;
      cfg_digest_swap <= 1'b0;
    end else if (tl_is_write && tl_addr[7:0] == 8'h00) begin
      cfg_hmac_en     <= tl_wdata[0];
      cfg_sha_en      <= tl_wdata[1];
      cfg_endian_swap <= tl_wdata[2];
      cfg_digest_swap <= tl_wdata[3];
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < 8; i++) key_reg[i] <= 32'd0;
    end else if (wipe_secret) begin
      for (int i = 0; i < 8; i++) key_reg[i] <= 32'd0;
    end else if (tl_is_write) begin
      case (tl_addr[7:0])
        8'h10: key_reg[0] <= tl_wdata;
        8'h14: key_reg[1] <= tl_wdata;
        8'h18: key_reg[2] <= tl_wdata;
        8'h1C: key_reg[3] <= tl_wdata;
        8'h20: key_reg[4] <= tl_wdata;
        8'h24: key_reg[5] <= tl_wdata;
        8'h28: key_reg[6] <= tl_wdata;
        8'h2C: key_reg[7] <= tl_wdata;
        default: ;
      endcase
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_state <= 3'd0;
    end else begin
      if (state_q != ST_DONE && state_d == ST_DONE)
        intr_state[0] <= 1'b1;
      if (intr_fifo_empty_pulse)
        intr_state[1] <= 1'b1;

      if (tl_is_write && tl_addr[7:0] == 8'h60) begin
        intr_state <= intr_state | tl_wdata[2:0];
      end

      if (tl_is_write && tl_addr[7:0] == 8'h58) begin
        intr_state <= intr_state & ~tl_wdata[2:0];
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      intr_enable <= 3'd0;
    end else if (tl_is_write && tl_addr[7:0] == 8'h5C) begin
      intr_enable <= tl_wdata[2:0];
    end
  end

  assign intr_o = intr_state & intr_enable;
  assign alert_o = 1'b0;

  assign total_msg_bits = {msg_len_hi, msg_len_lo};

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      msg_len_lo <= 32'd0;
      msg_len_hi <= 32'd0;
    end else if (cmd_hash_start) begin
      msg_len_lo <= 32'd0;
      msg_len_hi <= 32'd0;
    end else if (fifo_push && !fifo_full) begin
      {msg_len_hi, msg_len_lo} <= {msg_len_hi, msg_len_lo} + 64'd32;
    end
  end

  logic [31:0] w_next;
  always_comb begin
    w_next = sigma1(w_reg[14]) + w_reg[9] + sigma0(w_reg[1]) + w_reg[0];
  end

  always_comb begin
    if (round_cnt < 7'd16)
      w_cur = w_reg[round_cnt[3:0]];
    else
      w_cur = w_reg[15];
  end

  logic [31:0] t1, t2;
  always_comb begin
    t1 = h_val + big_sigma1(e_val) + ch_fn(e_val, f_val, g_val) + k_const(round_cnt[5:0]) + w_cur;
    t2 = big_sigma0(a_val) + maj_fn(a_val, b_val, c_val);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= ST_IDLE;
    end else begin
      state_q <= state_d;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      hash_stop_pending    <= 1'b0;
      hash_process_pending <= 1'b0;
    end else begin
      if (cmd_hash_start) begin
        hash_stop_pending    <= 1'b0;
        hash_process_pending <= 1'b0;
      end else begin
        if (cmd_hash_stop)    hash_stop_pending    <= 1'b1;
        if (cmd_hash_process) hash_process_pending <= 1'b1;
        if (state_d == ST_PAD_FILL || state_d == ST_PAD_LENGTH)
          hash_stop_pending <= 1'b0;
        if (state_d == ST_SHA_ROUND && state_q == ST_SHA_WAIT_BLOCK && !hash_stop_pending)
          hash_process_pending <= 1'b0;
      end
    end
  end

  always_comb begin
    pad_start_word = block_idx;
    if (cfg_hmac_en)
      pad_total_bits = total_msg_bits + 64'd512;
    else
      pad_total_bits = total_msg_bits;
    pad_needs_extra_block = (pad_start_word >= 4'd14);
  end

  always_comb begin
    for (int i = 0; i < 16; i++) pad_block[i] = 32'd0;

    for (int i = 0; i < 16; i++) begin
      if (i[3:0] < pad_start_word)
        pad_block[i] = block_reg[i];
    end

    if (pad_start_word < 4'd16) begin
      pad_block[pad_start_word] = 32'h80000000;
    end

    if (!pad_needs_extra_block) begin
      pad_block[14] = pad_total_bits[63:32];
      pad_block[15] = pad_total_bits[31:0];
    end
  end

  logic [31:0] pad_len_block [16];
  always_comb begin
    for (int i = 0; i < 14; i++) pad_len_block[i] = 32'd0;
    pad_len_block[14] = pad_total_bits[63:32];
    pad_len_block[15] = pad_total_bits[31:0];
  end

  logic [31:0] ipad_block [16];
  logic [31:0] opad_block [16];
  always_comb begin
    for (int i = 0; i < 8; i++) begin
      ipad_block[i] = key_reg[i] ^ 32'h36363636;
      opad_block[i] = key_reg[i] ^ 32'h5c5c5c5c;
    end
    for (int i = 8; i < 16; i++) begin
      ipad_block[i] = 32'h36363636;
      opad_block[i] = 32'h5c5c5c5c;
    end
  end

  logic [31:0] outer_msg_block [16];
  logic [63:0] hmac_outer_total_bits;
  always_comb begin
    hmac_outer_total_bits = 64'd768;
    for (int i = 0; i < 8; i++)
      outer_msg_block[i] = inner_digest[i];
    outer_msg_block[8]  = 32'h80000000;
    for (int i = 9; i < 14; i++)
      outer_msg_block[i] = 32'd0;
    outer_msg_block[14] = hmac_outer_total_bits[63:32];
    outer_msg_block[15] = hmac_outer_total_bits[31:0];
  end

  always_comb begin
    state_d = state_q;
    sha_start_block = 1'b0;

    case (state_q)
      ST_IDLE: begin
        if (cmd_hash_start && cfg_sha_en) begin
          if (cfg_hmac_en)
            state_d = ST_HMAC_IPAD;
          else
            state_d = ST_SHA_WAIT_BLOCK;
        end
      end

      ST_HMAC_IPAD: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_SHA_WAIT_BLOCK: begin
        if (hash_stop_pending) begin
          state_d = ST_PAD_FILL;
        end else if (block_ready) begin
          sha_start_block = 1'b1;
          state_d = ST_SHA_ROUND;
        end
      end

      ST_SHA_ROUND: begin
        if (round_cnt == 7'd63) begin
          state_d = ST_SHA_DONE_BLOCK;
        end
      end

      ST_SHA_DONE_BLOCK: begin
        if (pad_extra_pending) begin
          state_d = ST_PAD_LENGTH;
        end else if (returning_from_pad && !cfg_hmac_en) begin
          state_d = ST_DONE;
        end else if (returning_from_pad && cfg_hmac_en) begin
          state_d = ST_HMAC_INNER_DONE;
        end else if (returning_from_hmac_ipad) begin
          state_d = ST_SHA_WAIT_BLOCK;
        end else if (returning_from_opad) begin
          state_d = ST_HMAC_OUTER_MSG;
        end else if (returning_from_outer_msg) begin
          state_d = ST_DONE;
        end else if (returning_from_outer_pad) begin
          state_d = ST_HMAC_OUTER_LEN;
        end else begin
          state_d = ST_SHA_WAIT_BLOCK;
        end
      end

      ST_PAD_FILL: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_PAD_LENGTH: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_HMAC_INNER_DONE: begin
        state_d = ST_HMAC_OPAD;
      end

      ST_HMAC_OPAD: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_HMAC_OUTER_MSG: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_HMAC_OUTER_PAD: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_HMAC_OUTER_LEN: begin
        sha_start_block = 1'b1;
        state_d = ST_SHA_ROUND;
      end

      ST_DONE: begin
        if (cmd_hash_start && cfg_sha_en) begin
          if (cfg_hmac_en)
            state_d = ST_HMAC_IPAD;
          else
            state_d = ST_SHA_WAIT_BLOCK;
        end
      end

      default: state_d = ST_IDLE;
    endcase
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      returning_from_pad       <= 1'b0;
      returning_from_hmac_ipad <= 1'b0;
      returning_from_opad      <= 1'b0;
      returning_from_outer_msg <= 1'b0;
      returning_from_outer_pad <= 1'b0;
      pad_extra_pending        <= 1'b0;
    end else begin
      if (cmd_hash_start) begin
        returning_from_pad       <= 1'b0;
        returning_from_hmac_ipad <= 1'b0;
        returning_from_opad      <= 1'b0;
        returning_from_outer_msg <= 1'b0;
        returning_from_outer_pad <= 1'b0;
        pad_extra_pending        <= 1'b0;
      end

      if (state_q == ST_PAD_FILL) begin
        if (pad_needs_extra_block) begin
          returning_from_pad <= 1'b0;
          pad_extra_pending  <= 1'b1;
        end else begin
          returning_from_pad <= 1'b1;
        end
      end else if (state_q == ST_PAD_LENGTH) begin
        returning_from_pad <= 1'b1;
        pad_extra_pending  <= 1'b0;
      end else if (state_q == ST_SHA_DONE_BLOCK && returning_from_pad) begin
        returning_from_pad <= 1'b0;
      end

      if (state_q == ST_SHA_DONE_BLOCK && pad_extra_pending)
        pad_extra_pending <= 1'b0;

      if (state_q == ST_HMAC_IPAD)
        returning_from_hmac_ipad <= 1'b1;
      else if (state_q == ST_SHA_DONE_BLOCK && returning_from_hmac_ipad)
        returning_from_hmac_ipad <= 1'b0;

      if (state_q == ST_HMAC_OPAD)
        returning_from_opad <= 1'b1;
      else if (state_q == ST_SHA_DONE_BLOCK && returning_from_opad)
        returning_from_opad <= 1'b0;

      if (state_q == ST_HMAC_OUTER_MSG)
        returning_from_outer_msg <= 1'b1;
      else if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_msg)
        returning_from_outer_msg <= 1'b0;

      if (state_q == ST_HMAC_OUTER_PAD)
        returning_from_outer_pad <= 1'b1;
      else if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_pad)
        returning_from_outer_pad <= 1'b0;
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      block_idx   <= 4'd0;
      block_ready <= 1'b0;
    end else begin
      if (cmd_hash_start) begin
        block_idx   <= 4'd0;
        block_ready <= 1'b0;
      end else if (state_q == ST_SHA_DONE_BLOCK) begin
        block_idx   <= 4'd0;
        block_ready <= 1'b0;
      end else if (state_q == ST_SHA_WAIT_BLOCK && !fifo_empty && !block_ready && !hash_stop_pending) begin
        block_reg[block_idx] <= fifo_rdata;
        block_idx <= block_idx + 4'd1;
        if (block_idx == 4'd15) block_ready <= 1'b1;
      end
    end
  end

  assign fifo_pop = (state_q == ST_SHA_WAIT_BLOCK && !fifo_empty && !block_ready && !hash_stop_pending);

  logic [31:0] final_h [8];
  always_comb begin
    for (int i = 0; i < 8; i++) begin
      case (i)
        0: final_h[i] = h_reg[0] + a_val;
        1: final_h[i] = h_reg[1] + b_val;
        2: final_h[i] = h_reg[2] + c_val;
        3: final_h[i] = h_reg[3] + d_val;
        4: final_h[i] = h_reg[4] + e_val;
        5: final_h[i] = h_reg[5] + f_val;
        6: final_h[i] = h_reg[6] + g_val;
        default: final_h[i] = h_reg[7] + h_val;
      endcase
    end
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < 8; i++) h_reg[i] <= 32'd0;
      a_val <= 32'd0; b_val <= 32'd0; c_val <= 32'd0; d_val <= 32'd0;
      e_val <= 32'd0; f_val <= 32'd0; g_val <= 32'd0; h_val <= 32'd0;
      round_cnt <= 7'd0;
      for (int i = 0; i < 16; i++) w_reg[i] <= 32'd0;
      for (int i = 0; i < 8; i++) digest_reg[i] <= 32'd0;
      for (int i = 0; i < 8; i++) inner_digest[i] <= 32'd0;
    end else begin
      if (cmd_hash_start) begin
        for (int i = 0; i < 8; i++) h_reg[i] <= h_init(i);
      end

      if (wipe_secret) begin
        for (int i = 0; i < 8; i++) h_reg[i] <= 32'd0;
        for (int i = 0; i < 16; i++) w_reg[i] <= 32'd0;
        for (int i = 0; i < 8; i++) digest_reg[i] <= 32'd0;
        a_val <= 32'd0; b_val <= 32'd0; c_val <= 32'd0; d_val <= 32'd0;
        e_val <= 32'd0; f_val <= 32'd0; g_val <= 32'd0; h_val <= 32'd0;
      end

      if (sha_start_block) begin
        round_cnt <= 7'd0;
        a_val <= h_reg[0]; b_val <= h_reg[1]; c_val <= h_reg[2]; d_val <= h_reg[3];
        e_val <= h_reg[4]; f_val <= h_reg[5]; g_val <= h_reg[6]; h_val <= h_reg[7];

        if (state_q == ST_HMAC_IPAD) begin
          for (int i = 0; i < 16; i++) w_reg[i] <= ipad_block[i];
        end else if (state_q == ST_HMAC_OPAD) begin
          for (int i = 0; i < 16; i++) w_reg[i] <= opad_block[i];
        end else if (state_q == ST_HMAC_OUTER_MSG) begin
          for (int i = 0; i < 16; i++) w_reg[i] <= outer_msg_block[i];
        end else if (state_q == ST_PAD_FILL) begin
          for (int i = 0; i < 16; i++) w_reg[i] <= pad_block[i];
        end else if (state_q == ST_PAD_LENGTH) begin
          for (int i = 0; i < 16; i++) w_reg[i] <= pad_len_block[i];
        end else begin
          for (int i = 0; i < 16; i++) w_reg[i] <= block_reg[i];
        end
      end

      if (state_q == ST_SHA_ROUND) begin
        h_val <= g_val;
        g_val <= f_val;
        f_val <= e_val;
        e_val <= d_val + t1;
        d_val <= c_val;
        c_val <= b_val;
        b_val <= a_val;
        a_val <= t1 + t2;

        if (round_cnt >= 7'd15) begin
          for (int i = 0; i < 15; i++) w_reg[i] <= w_reg[i+1];
          w_reg[15] <= w_next;
        end

        round_cnt <= round_cnt + 7'd1;
      end

      if (state_q == ST_SHA_DONE_BLOCK) begin
        h_reg[0] <= h_reg[0] + a_val;
        h_reg[1] <= h_reg[1] + b_val;
        h_reg[2] <= h_reg[2] + c_val;
        h_reg[3] <= h_reg[3] + d_val;
        h_reg[4] <= h_reg[4] + e_val;
        h_reg[5] <= h_reg[5] + f_val;
        h_reg[6] <= h_reg[6] + g_val;
        h_reg[7] <= h_reg[7] + h_val;
      end

      if (state_q == ST_SHA_DONE_BLOCK && returning_from_pad) begin
        if (cfg_hmac_en) begin
          for (int i = 0; i < 8; i++)
            inner_digest[i] <= final_h[i];
        end else begin
          for (int i = 0; i < 8; i++)
            digest_reg[i] <= final_h[i];
        end
      end

      if (state_q == ST_SHA_DONE_BLOCK && returning_from_outer_msg) begin
        for (int i = 0; i < 8; i++)
          digest_reg[i] <= final_h[i];
      end

      if (state_q == ST_HMAC_INNER_DONE) begin
        for (int i = 0; i < 8; i++) h_reg[i] <= h_init(i);
      end
    end
  end

endmodule
