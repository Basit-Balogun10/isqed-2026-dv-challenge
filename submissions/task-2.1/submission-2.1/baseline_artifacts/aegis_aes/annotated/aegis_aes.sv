//      // verilator_coverage annotation
        import dv_common_pkg::*;
        
        module aegis_aes (
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
~000011   output logic [2:0]  tl_d_opcode_o,
%000000   output logic [31:0] tl_d_data_o,
%000000   output logic [7:0]  tl_d_source_o,
%000000   output logic        tl_d_error_o,
%000000   output logic        intr_o,
%000000   output logic        alert_o
        );
        
          localparam int unsigned NUM_ROUNDS = 10;
        
 010976   function automatic logic [7:0] sbox_fwd(input logic [7:0] v);
 010976     case (v)
%000000       8'h00: return 8'h63; 8'h01: return 8'h7C; 8'h02: return 8'h77; 8'h03: return 8'h7B;
%000000       8'h04: return 8'hF2; 8'h05: return 8'h6B; 8'h06: return 8'h6F; 8'h07: return 8'hC5;
%000000       8'h08: return 8'h30; 8'h09: return 8'h01; 8'h0A: return 8'h67; 8'h0B: return 8'h2B;
%000000       8'h0C: return 8'hFE; 8'h0D: return 8'hD7; 8'h0E: return 8'hAB; 8'h0F: return 8'h76;
%000000       8'h10: return 8'hCA; 8'h11: return 8'h82; 8'h12: return 8'hC9; 8'h13: return 8'h7D;
%000000       8'h14: return 8'hFA; 8'h15: return 8'h59; 8'h16: return 8'h47; 8'h17: return 8'hF0;
%000000       8'h18: return 8'hAD; 8'h19: return 8'hD4; 8'h1A: return 8'hA2; 8'h1B: return 8'hAF;
%000000       8'h1C: return 8'h9C; 8'h1D: return 8'hA4; 8'h1E: return 8'h72; 8'h1F: return 8'hC0;
%000000       8'h20: return 8'hB7; 8'h21: return 8'hFD; 8'h22: return 8'h93; 8'h23: return 8'h26;
%000000       8'h24: return 8'h36; 8'h25: return 8'h3F; 8'h26: return 8'hF7; 8'h27: return 8'hCC;
%000000       8'h28: return 8'h34; 8'h29: return 8'hA5; 8'h2A: return 8'hE5; 8'h2B: return 8'hF1;
%000000       8'h2C: return 8'h71; 8'h2D: return 8'hD8; 8'h2E: return 8'h31; 8'h2F: return 8'h15;
%000000       8'h30: return 8'h04; 8'h31: return 8'hC7; 8'h32: return 8'h23; 8'h33: return 8'hC3;
%000000       8'h34: return 8'h18; 8'h35: return 8'h96; 8'h36: return 8'h05; 8'h37: return 8'h9A;
%000000       8'h38: return 8'h07; 8'h39: return 8'h12; 8'h3A: return 8'h80; 8'h3B: return 8'hE2;
%000000       8'h3C: return 8'hEB; 8'h3D: return 8'h27; 8'h3E: return 8'hB2; 8'h3F: return 8'h75;
%000000       8'h40: return 8'h09; 8'h41: return 8'h83; 8'h42: return 8'h2C; 8'h43: return 8'h1A;
%000000       8'h44: return 8'h1B; 8'h45: return 8'h6E; 8'h46: return 8'h5A; 8'h47: return 8'hA0;
%000000       8'h48: return 8'h52; 8'h49: return 8'h3B; 8'h4A: return 8'hD6; 8'h4B: return 8'hB3;
%000000       8'h4C: return 8'h29; 8'h4D: return 8'hE3; 8'h4E: return 8'h2F; 8'h4F: return 8'h84;
%000000       8'h50: return 8'h53; 8'h51: return 8'hD1; 8'h52: return 8'h00; 8'h53: return 8'hED;
%000000       8'h54: return 8'h20; 8'h55: return 8'hFC; 8'h56: return 8'hB1; 8'h57: return 8'h5B;
%000000       8'h58: return 8'h6A; 8'h59: return 8'hCB; 8'h5A: return 8'hBE; 8'h5B: return 8'h39;
%000000       8'h5C: return 8'h4A; 8'h5D: return 8'h4C; 8'h5E: return 8'h58; 8'h5F: return 8'hCF;
%000000       8'h60: return 8'hD0; 8'h61: return 8'hEF; 8'h62: return 8'hAA; 8'h63: return 8'hFB;
%000000       8'h64: return 8'h43; 8'h65: return 8'h4D; 8'h66: return 8'h33; 8'h67: return 8'h85;
%000000       8'h68: return 8'h45; 8'h69: return 8'hF9; 8'h6A: return 8'h02; 8'h6B: return 8'h7F;
%000000       8'h6C: return 8'h50; 8'h6D: return 8'h3C; 8'h6E: return 8'h9F; 8'h6F: return 8'hA8;
%000000       8'h70: return 8'h51; 8'h71: return 8'hA3; 8'h72: return 8'h40; 8'h73: return 8'h8F;
%000000       8'h74: return 8'h92; 8'h75: return 8'h9D; 8'h76: return 8'h38; 8'h77: return 8'hF5;
%000000       8'h78: return 8'hBC; 8'h79: return 8'hB6; 8'h7A: return 8'hDA; 8'h7B: return 8'h21;
%000000       8'h7C: return 8'h10; 8'h7D: return 8'hFF; 8'h7E: return 8'hF3; 8'h7F: return 8'hD2;
%000000       8'h80: return 8'hCD; 8'h81: return 8'h0C; 8'h82: return 8'h13; 8'h83: return 8'hEC;
%000000       8'h84: return 8'h5F; 8'h85: return 8'h97; 8'h86: return 8'h44; 8'h87: return 8'h17;
%000000       8'h88: return 8'hC4; 8'h89: return 8'hA7; 8'h8A: return 8'h7E; 8'h8B: return 8'h3D;
%000000       8'h8C: return 8'h64; 8'h8D: return 8'h5D; 8'h8E: return 8'h19; 8'h8F: return 8'h73;
%000000       8'h90: return 8'h60; 8'h91: return 8'h81; 8'h92: return 8'h4F; 8'h93: return 8'hDC;
%000000       8'h94: return 8'h22; 8'h95: return 8'h2A; 8'h96: return 8'h90; 8'h97: return 8'h88;
%000000       8'h98: return 8'h46; 8'h99: return 8'hEE; 8'h9A: return 8'hB8; 8'h9B: return 8'h14;
%000000       8'h9C: return 8'hDE; 8'h9D: return 8'h5E; 8'h9E: return 8'h0B; 8'h9F: return 8'hDB;
%000000       8'hA0: return 8'hE0; 8'hA1: return 8'h32; 8'hA2: return 8'h3A; 8'hA3: return 8'h0A;
%000000       8'hA4: return 8'h49; 8'hA5: return 8'h06; 8'hA6: return 8'h24; 8'hA7: return 8'h5C;
%000000       8'hA8: return 8'hC2; 8'hA9: return 8'hD3; 8'hAA: return 8'hAC; 8'hAB: return 8'h62;
%000000       8'hAC: return 8'h91; 8'hAD: return 8'h95; 8'hAE: return 8'hE4; 8'hAF: return 8'h79;
%000000       8'hB0: return 8'hE7; 8'hB1: return 8'hC8; 8'hB2: return 8'h37; 8'hB3: return 8'h6D;
%000000       8'hB4: return 8'h8D; 8'hB5: return 8'hD5; 8'hB6: return 8'h4E; 8'hB7: return 8'hA9;
%000000       8'hB8: return 8'h6C; 8'hB9: return 8'h56; 8'hBA: return 8'hF4; 8'hBB: return 8'hEA;
%000000       8'hBC: return 8'h65; 8'hBD: return 8'h7A; 8'hBE: return 8'hAE; 8'hBF: return 8'h08;
%000000       8'hC0: return 8'hBA; 8'hC1: return 8'h78; 8'hC2: return 8'h25; 8'hC3: return 8'h2E;
%000000       8'hC4: return 8'h1C; 8'hC5: return 8'hA6; 8'hC6: return 8'hB4; 8'hC7: return 8'hC6;
%000000       8'hC8: return 8'hE8; 8'hC9: return 8'hDD; 8'hCA: return 8'h74; 8'hCB: return 8'h1F;
%000000       8'hCC: return 8'h4B; 8'hCD: return 8'hBD; 8'hCE: return 8'h8B; 8'hCF: return 8'h8A;
%000000       8'hD0: return 8'h70; 8'hD1: return 8'h3E; 8'hD2: return 8'hB5; 8'hD3: return 8'h66;
%000000       8'hD4: return 8'h48; 8'hD5: return 8'h03; 8'hD6: return 8'hF6; 8'hD7: return 8'h0E;
%000000       8'hD8: return 8'h61; 8'hD9: return 8'h35; 8'hDA: return 8'h57; 8'hDB: return 8'hB9;
%000000       8'hDC: return 8'h86; 8'hDD: return 8'hC1; 8'hDE: return 8'h1D; 8'hDF: return 8'h9E;
%000000       8'hE0: return 8'hE1; 8'hE1: return 8'hF8; 8'hE2: return 8'h98; 8'hE3: return 8'h11;
%000000       8'hE4: return 8'h69; 8'hE5: return 8'hD9; 8'hE6: return 8'h8E; 8'hE7: return 8'h94;
%000000       8'hE8: return 8'h9B; 8'hE9: return 8'h1E; 8'hEA: return 8'h87; 8'hEB: return 8'hE9;
%000000       8'hEC: return 8'hCE; 8'hED: return 8'h55; 8'hEE: return 8'h28; 8'hEF: return 8'hDF;
%000000       8'hF0: return 8'h8C; 8'hF1: return 8'hA1; 8'hF2: return 8'h89; 8'hF3: return 8'h0D;
%000000       8'hF4: return 8'hBF; 8'hF5: return 8'hE6; 8'hF6: return 8'h42; 8'hF7: return 8'h68;
%000000       8'hF8: return 8'h41; 8'hF9: return 8'h99; 8'hFA: return 8'h2D; 8'hFB: return 8'h0F;
%000000       8'hFC: return 8'hB0; 8'hFD: return 8'h54; 8'hFE: return 8'hBB; 8'hFF: return 8'h16;
%000000       default: return 8'h00;
            endcase
          endfunction
        
%000000   function automatic logic [7:0] sbox_inv(input logic [7:0] v);
%000000     case (v)
%000000       8'h00: return 8'h52; 8'h01: return 8'h09; 8'h02: return 8'h6A; 8'h03: return 8'hD5;
%000000       8'h04: return 8'h30; 8'h05: return 8'h36; 8'h06: return 8'hA5; 8'h07: return 8'h38;
%000000       8'h08: return 8'hBF; 8'h09: return 8'h40; 8'h0A: return 8'hA3; 8'h0B: return 8'h9E;
%000000       8'h0C: return 8'h81; 8'h0D: return 8'hF3; 8'h0E: return 8'hD7; 8'h0F: return 8'hFB;
%000000       8'h10: return 8'h7C; 8'h11: return 8'hE3; 8'h12: return 8'h39; 8'h13: return 8'h82;
%000000       8'h14: return 8'h9B; 8'h15: return 8'h2F; 8'h16: return 8'hFF; 8'h17: return 8'h87;
%000000       8'h18: return 8'h34; 8'h19: return 8'h8E; 8'h1A: return 8'h43; 8'h1B: return 8'h44;
%000000       8'h1C: return 8'hC4; 8'h1D: return 8'hDE; 8'h1E: return 8'hE9; 8'h1F: return 8'hCB;
%000000       8'h20: return 8'h54; 8'h21: return 8'h7B; 8'h22: return 8'h94; 8'h23: return 8'h32;
%000000       8'h24: return 8'hA6; 8'h25: return 8'hC2; 8'h26: return 8'h23; 8'h27: return 8'h3D;
%000000       8'h28: return 8'hEE; 8'h29: return 8'h4C; 8'h2A: return 8'h95; 8'h2B: return 8'h0B;
%000000       8'h2C: return 8'h42; 8'h2D: return 8'hFA; 8'h2E: return 8'hC3; 8'h2F: return 8'h4E;
%000000       8'h30: return 8'h08; 8'h31: return 8'h2E; 8'h32: return 8'hA1; 8'h33: return 8'h66;
%000000       8'h34: return 8'h28; 8'h35: return 8'hD9; 8'h36: return 8'h24; 8'h37: return 8'hB2;
%000000       8'h38: return 8'h76; 8'h39: return 8'h5B; 8'h3A: return 8'hA2; 8'h3B: return 8'h49;
%000000       8'h3C: return 8'h6D; 8'h3D: return 8'h8B; 8'h3E: return 8'hD1; 8'h3F: return 8'h25;
%000000       8'h40: return 8'h72; 8'h41: return 8'hF8; 8'h42: return 8'hF6; 8'h43: return 8'h64;
%000000       8'h44: return 8'h86; 8'h45: return 8'h68; 8'h46: return 8'h98; 8'h47: return 8'h16;
%000000       8'h48: return 8'hD4; 8'h49: return 8'hA4; 8'h4A: return 8'h5C; 8'h4B: return 8'hCC;
%000000       8'h4C: return 8'h5D; 8'h4D: return 8'h65; 8'h4E: return 8'hB6; 8'h4F: return 8'h92;
%000000       8'h50: return 8'h6C; 8'h51: return 8'h70; 8'h52: return 8'h48; 8'h53: return 8'h50;
%000000       8'h54: return 8'hFD; 8'h55: return 8'hED; 8'h56: return 8'hB9; 8'h57: return 8'hDA;
%000000       8'h58: return 8'h5E; 8'h59: return 8'h15; 8'h5A: return 8'h46; 8'h5B: return 8'h57;
%000000       8'h5C: return 8'hA7; 8'h5D: return 8'h8D; 8'h5E: return 8'h9D; 8'h5F: return 8'h84;
%000000       8'h60: return 8'h90; 8'h61: return 8'hD8; 8'h62: return 8'hAB; 8'h63: return 8'h00;
%000000       8'h64: return 8'h8C; 8'h65: return 8'hBC; 8'h66: return 8'hD3; 8'h67: return 8'h0A;
%000000       8'h68: return 8'hF7; 8'h69: return 8'hE4; 8'h6A: return 8'h58; 8'h6B: return 8'h05;
%000000       8'h6C: return 8'hB8; 8'h6D: return 8'hB3; 8'h6E: return 8'h45; 8'h6F: return 8'h06;
%000000       8'h70: return 8'hD0; 8'h71: return 8'h2C; 8'h72: return 8'h1E; 8'h73: return 8'h8F;
%000000       8'h74: return 8'hCA; 8'h75: return 8'h3F; 8'h76: return 8'h0F; 8'h77: return 8'h02;
%000000       8'h78: return 8'hC1; 8'h79: return 8'hAF; 8'h7A: return 8'hBD; 8'h7B: return 8'h03;
%000000       8'h7C: return 8'h01; 8'h7D: return 8'h13; 8'h7E: return 8'h8A; 8'h7F: return 8'h6B;
%000000       8'h80: return 8'h3A; 8'h81: return 8'h91; 8'h82: return 8'h11; 8'h83: return 8'h41;
%000000       8'h84: return 8'h4F; 8'h85: return 8'h67; 8'h86: return 8'hDC; 8'h87: return 8'hEA;
%000000       8'h88: return 8'h97; 8'h89: return 8'hF2; 8'h8A: return 8'hCF; 8'h8B: return 8'hCE;
%000000       8'h8C: return 8'hF0; 8'h8D: return 8'hB4; 8'h8E: return 8'hE6; 8'h8F: return 8'h73;
%000000       8'h90: return 8'h96; 8'h91: return 8'hAC; 8'h92: return 8'h74; 8'h93: return 8'h22;
%000000       8'h94: return 8'hE7; 8'h95: return 8'hAD; 8'h96: return 8'h35; 8'h97: return 8'h85;
%000000       8'h98: return 8'hE2; 8'h99: return 8'hF9; 8'h9A: return 8'h37; 8'h9B: return 8'hE8;
%000000       8'h9C: return 8'h1C; 8'h9D: return 8'h75; 8'h9E: return 8'hDF; 8'h9F: return 8'h6E;
%000000       8'hA0: return 8'h47; 8'hA1: return 8'hF1; 8'hA2: return 8'h1A; 8'hA3: return 8'h71;
%000000       8'hA4: return 8'h1D; 8'hA5: return 8'h29; 8'hA6: return 8'hC5; 8'hA7: return 8'h89;
%000000       8'hA8: return 8'h6F; 8'hA9: return 8'hB7; 8'hAA: return 8'h62; 8'hAB: return 8'h0E;
%000000       8'hAC: return 8'hAA; 8'hAD: return 8'h18; 8'hAE: return 8'hBE; 8'hAF: return 8'h1B;
%000000       8'hB0: return 8'hFC; 8'hB1: return 8'h56; 8'hB2: return 8'h3E; 8'hB3: return 8'h4B;
%000000       8'hB4: return 8'hC6; 8'hB5: return 8'hD2; 8'hB6: return 8'h79; 8'hB7: return 8'h20;
%000000       8'hB8: return 8'h9A; 8'hB9: return 8'hDB; 8'hBA: return 8'hC0; 8'hBB: return 8'hFE;
%000000       8'hBC: return 8'h78; 8'hBD: return 8'hCD; 8'hBE: return 8'h5A; 8'hBF: return 8'hF4;
%000000       8'hC0: return 8'h1F; 8'hC1: return 8'hDD; 8'hC2: return 8'hA8; 8'hC3: return 8'h33;
%000000       8'hC4: return 8'h88; 8'hC5: return 8'h07; 8'hC6: return 8'hC7; 8'hC7: return 8'h31;
%000000       8'hC8: return 8'hB1; 8'hC9: return 8'h12; 8'hCA: return 8'h10; 8'hCB: return 8'h59;
%000000       8'hCC: return 8'h27; 8'hCD: return 8'h80; 8'hCE: return 8'hEC; 8'hCF: return 8'h5F;
%000000       8'hD0: return 8'h60; 8'hD1: return 8'h51; 8'hD2: return 8'h7F; 8'hD3: return 8'hA9;
%000000       8'hD4: return 8'h19; 8'hD5: return 8'hB5; 8'hD6: return 8'h4A; 8'hD7: return 8'h0D;
%000000       8'hD8: return 8'h2D; 8'hD9: return 8'hE5; 8'hDA: return 8'h7A; 8'hDB: return 8'h9F;
%000000       8'hDC: return 8'h93; 8'hDD: return 8'hC9; 8'hDE: return 8'h9C; 8'hDF: return 8'hEF;
%000000       8'hE0: return 8'hA0; 8'hE1: return 8'hE0; 8'hE2: return 8'h3B; 8'hE3: return 8'h4D;
%000000       8'hE4: return 8'hAE; 8'hE5: return 8'h2A; 8'hE6: return 8'hF5; 8'hE7: return 8'hB0;
%000000       8'hE8: return 8'hC8; 8'hE9: return 8'hEB; 8'hEA: return 8'hBB; 8'hEB: return 8'h3C;
%000000       8'hEC: return 8'h83; 8'hED: return 8'h53; 8'hEE: return 8'h99; 8'hEF: return 8'h61;
%000000       8'hF0: return 8'h17; 8'hF1: return 8'h2B; 8'hF2: return 8'h04; 8'hF3: return 8'h7E;
%000000       8'hF4: return 8'hBA; 8'hF5: return 8'h77; 8'hF6: return 8'hD6; 8'hF7: return 8'h26;
%000000       8'hF8: return 8'hE1; 8'hF9: return 8'h69; 8'hFA: return 8'h14; 8'hFB: return 8'h63;
%000000       8'hFC: return 8'h55; 8'hFD: return 8'h21; 8'hFE: return 8'h0C; 8'hFF: return 8'h7D;
%000000       default: return 8'h00;
            endcase
          endfunction
        
 010976   function automatic logic [7:0] xtime(input logic [7:0] b);
~010976     return {b[6], b[5], b[4], b[3]^b[7], b[2]^b[7], b[1], b[0]^b[7], b[7]};
          endfunction
        
%000000   function automatic logic [7:0] xtime4(input logic [7:0] b);
%000000     return xtime(xtime(b));
          endfunction
        
%000000   function automatic logic [31:0] bswap32(input logic [31:0] w);
%000000     return {w[7:0], w[15:8], w[23:16], w[31:24]};
          endfunction
        
%000000   function automatic logic [31:0] sub_word(input logic [31:0] w);
%000000     return {sbox_fwd(w[31:24]), sbox_fwd(w[23:16]), sbox_fwd(w[15:8]), sbox_fwd(w[7:0])};
          endfunction
        
%000000   function automatic logic [31:0] rot_word(input logic [31:0] w);
%000000     return {w[23:16], w[15:8], w[7:0], w[31:24]};
          endfunction
        
%000000   function automatic logic [7:0] get_rcon(input logic [3:0] idx);
%000000     case (idx)
%000000       4'd0: return 8'h01; 4'd1: return 8'h02; 4'd2: return 8'h04; 4'd3: return 8'h08;
%000000       4'd4: return 8'h10; 4'd5: return 8'h20; 4'd6: return 8'h40; 4'd7: return 8'h80;
%000000       4'd8: return 8'h1b; 4'd9: return 8'h36;
%000000       default: return 8'h00;
            endcase
          endfunction
        
        
 000686   function automatic logic [127:0] sub_bytes_fwd(input logic [127:0] s);
            logic [127:0] r;
 000686     r[  7:  0] = sbox_fwd(s[  7:  0]); r[ 15:  8] = sbox_fwd(s[ 15:  8]);
 000686     r[ 23: 16] = sbox_fwd(s[ 23: 16]); r[ 31: 24] = sbox_fwd(s[ 31: 24]);
 000686     r[ 39: 32] = sbox_fwd(s[ 39: 32]); r[ 47: 40] = sbox_fwd(s[ 47: 40]);
 000686     r[ 55: 48] = sbox_fwd(s[ 55: 48]); r[ 63: 56] = sbox_fwd(s[ 63: 56]);
 000686     r[ 71: 64] = sbox_fwd(s[ 71: 64]); r[ 79: 72] = sbox_fwd(s[ 79: 72]);
 000686     r[ 87: 80] = sbox_fwd(s[ 87: 80]); r[ 95: 88] = sbox_fwd(s[ 95: 88]);
 000686     r[103: 96] = sbox_fwd(s[103: 96]); r[111:104] = sbox_fwd(s[111:104]);
 000686     r[119:112] = sbox_fwd(s[119:112]); r[127:120] = sbox_fwd(s[127:120]);
 000686     return r;
          endfunction
        
%000000   function automatic logic [127:0] sub_bytes_inv(input logic [127:0] s);
            logic [127:0] r;
%000000     r[  7:  0] = sbox_inv(s[  7:  0]); r[ 15:  8] = sbox_inv(s[ 15:  8]);
%000000     r[ 23: 16] = sbox_inv(s[ 23: 16]); r[ 31: 24] = sbox_inv(s[ 31: 24]);
%000000     r[ 39: 32] = sbox_inv(s[ 39: 32]); r[ 47: 40] = sbox_inv(s[ 47: 40]);
%000000     r[ 55: 48] = sbox_inv(s[ 55: 48]); r[ 63: 56] = sbox_inv(s[ 63: 56]);
%000000     r[ 71: 64] = sbox_inv(s[ 71: 64]); r[ 79: 72] = sbox_inv(s[ 79: 72]);
%000000     r[ 87: 80] = sbox_inv(s[ 87: 80]); r[ 95: 88] = sbox_inv(s[ 95: 88]);
%000000     r[103: 96] = sbox_inv(s[103: 96]); r[111:104] = sbox_inv(s[111:104]);
%000000     r[119:112] = sbox_inv(s[119:112]); r[127:120] = sbox_inv(s[127:120]);
%000000     return r;
          endfunction
        
 000686   function automatic logic [127:0] shift_rows_fwd(input logic [127:0] s);
            logic [127:0] r;
 000686     r[ 31: 24] = s[ 31: 24]; r[ 63: 56] = s[ 63: 56];
 000686     r[ 95: 88] = s[ 95: 88]; r[127:120] = s[127:120];
 000686     r[ 23: 16] = s[ 55: 48]; r[ 55: 48] = s[ 87: 80];
 000686     r[ 87: 80] = s[119:112]; r[119:112] = s[ 23: 16];
 000686     r[ 15:  8] = s[ 79: 72]; r[ 47: 40] = s[111:104];
 000686     r[ 79: 72] = s[ 15:  8]; r[111:104] = s[ 47: 40];
 000686     r[  7:  0] = s[103: 96]; r[ 39: 32] = s[  7:  0];
 000686     r[ 71: 64] = s[ 39: 32]; r[103: 96] = s[ 71: 64];
 000686     return r;
          endfunction
        
%000000   function automatic logic [127:0] shift_rows_inv(input logic [127:0] s);
            logic [127:0] r;
%000000     r[ 31: 24] = s[ 31: 24]; r[ 63: 56] = s[ 63: 56];
%000000     r[ 95: 88] = s[ 95: 88]; r[127:120] = s[127:120];
%000000     r[ 23: 16] = s[119:112]; r[ 55: 48] = s[ 23: 16];
%000000     r[ 87: 80] = s[ 55: 48]; r[119:112] = s[ 87: 80];
%000000     r[ 15:  8] = s[ 79: 72]; r[ 47: 40] = s[111:104];
%000000     r[ 79: 72] = s[ 15:  8]; r[111:104] = s[ 47: 40];
%000000     r[  7:  0] = s[ 39: 32]; r[ 39: 32] = s[ 71: 64];
%000000     r[ 71: 64] = s[103: 96]; r[103: 96] = s[  7:  0];
%000000     return r;
          endfunction
        
 002744   function automatic logic [31:0] mix_single_column_fwd(input logic [31:0] din);
            logic [7:0] d0, d1, d2, d3;
            logic [7:0] x0, x1, x2, x3;
            logic [7:0] xm0, xm1, xm2, xm3;
            logic [7:0] o0, o1, o2, o3;
 002744     d0 = din[31:24]; d1 = din[23:16]; d2 = din[15:8]; d3 = din[7:0];
 002744     x0 = d0 ^ d3; x1 = d3 ^ d2; x2 = d2 ^ d1; x3 = d1 ^ d0;
 002744     xm0 = xtime(x0); xm1 = xtime(x1); xm2 = xtime(x2); xm3 = xtime(x3);
 002744     o0 = d1 ^ xm3 ^ x1; // 2*d0 ^ 3*d1 ^ d2 ^ d3
 002744     o1 = d0 ^ xm2 ^ x1; // d0 ^ 2*d1 ^ 3*d2 ^ d3
 002744     o2 = d3 ^ xm1 ^ x3; // d0 ^ d1 ^ 2*d2 ^ 3*d3
 002744     o3 = d2 ^ xm0 ^ x3; // 3*d0 ^ d1 ^ d2 ^ 2*d3
 002744     return {o0, o1, o2, o3};
          endfunction
        
%000000   function automatic logic [31:0] mix_single_column_inv(input logic [31:0] din);
            logic [7:0] d0, d1, d2, d3;
            logic [7:0] x0, x1, x2, x3;
            logic [7:0] xm0, xm1, xm2, xm3;
            logic [7:0] yp0, yp1, y0, y1, y2p, y2, z0, z1;
            logic [7:0] o0, o1, o2, o3;
%000000     d0 = din[31:24]; d1 = din[23:16]; d2 = din[15:8]; d3 = din[7:0];
%000000     x0 = d0 ^ d3; x1 = d3 ^ d2; x2 = d2 ^ d1; x3 = d1 ^ d0;
%000000     xm0 = xtime(x0); xm1 = xtime(x1); xm2 = xtime(x2); xm3 = xtime(x3);
%000000     yp0 = d3 ^ d1; yp1 = d2 ^ d0;
%000000     y0 = xtime4(yp0); y1 = xtime4(yp1);
%000000     y2p = y0 ^ y1; y2 = xtime(y2p);
%000000     z0 = y2 ^ y0; z1 = y2 ^ y1;
%000000     o0 = d1 ^ xm3 ^ x1 ^ z1;
%000000     o1 = d0 ^ xm2 ^ x1 ^ z0;
%000000     o2 = d3 ^ xm1 ^ x3 ^ z1;
%000000     o3 = d2 ^ xm0 ^ x3 ^ z0;
%000000     return {o0, o1, o2, o3};
          endfunction
        
 000686   function automatic logic [127:0] mix_columns_fwd(input logic [127:0] s);
 000686     return {mix_single_column_fwd(s[127:96]), mix_single_column_fwd(s[95:64]),
 000686             mix_single_column_fwd(s[63:32]),  mix_single_column_fwd(s[31:0])};
          endfunction
        
%000000   function automatic logic [127:0] mix_columns_inv(input logic [127:0] s);
%000000     return {mix_single_column_inv(s[127:96]), mix_single_column_inv(s[95:64]),
%000000             mix_single_column_inv(s[63:32]),  mix_single_column_inv(s[31:0])};
          endfunction
        
          typedef enum logic [2:0] {
            FSM_IDLE    = 3'd0,
            FSM_KEY_EXP = 3'd1,
            FSM_INIT    = 3'd2,
            FSM_ROUND   = 3'd3,
            FSM_DONE    = 3'd4
          } fsm_state_e;
        
%000000   fsm_state_e fsm_q;
        
%000001   logic [31:0] key_reg     [4];
%000000   logic [31:0] iv_reg      [4];
%000000   logic [31:0] data_in_reg [4];
%000000   logic [31:0] data_out_reg[4];
        
%000000   logic        ctrl_mode_q;
%000000   logic        ctrl_op_q;
        
%000000   logic        trigger_start;
%000000   logic        trigger_key_clear;
%000000   logic        trigger_dout_clear;
        
%000000   logic        output_valid_q;
%000001   logic        input_ready_q;
        
%000000   logic        intr_state_q;
%000000   logic        intr_enable_q;
        
          logic [127:0] round_key   [11]; // 11 round keys stored as 128-bit
%000000   logic [3:0]   key_exp_ctr_q;
%000000   logic         key_exp_done_q;
%000000   logic [31:0]  ke_last_w   [4];  // last 4 words of key expansion
        
%000000   logic [3:0]  round_ctr_q;
        
%000000   logic [127:0] state_q;
%000004   logic [127:0] state_nxt;
        
%000000   logic [127:0] latched_key;
%000000   logic [127:0] latched_data;
%000000   logic [127:0] latched_iv;
        
%000004   logic         tl_wr_en;
 000011   logic         tl_rd_en;
%000007   logic [7:0]   tl_addr;
%000002   logic [31:0]  tl_wdata;
%000000   logic [31:0]  tl_rdata;
 000015   logic         tl_rvalid;
%000000   logic         tl_err;
%000000   logic [7:0]   tl_source_q;
 000011   logic         rd_pending_q;
        
%000000   logic        round_finishing;
%000001   logic [31:0] data_out_next [4];
%000000   logic        data_out_we;
        
%000001   logic        status_idle;
%000000   logic        status_output_valid;
%000001   logic        status_input_ready;
        
%000000   logic [127:0] current_rk;
        
          wire _unused_mask = &{1'b0, tl_a_mask_i, tl_a_size_i, tl_d_ready_i};
        
          assign tl_a_ready_o = 1'b1;
        
 000555   always_comb begin
 000555     tl_wr_en = tl_a_valid_i & (tl_a_opcode_i == 3'd0);
 000555     tl_rd_en = tl_a_valid_i & (tl_a_opcode_i == 3'd4);
 000555     tl_addr  = tl_a_address_i[7:0];
 000555     tl_wdata = tl_a_data_i;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       tl_rvalid    <= 1'b0;
%000005       tl_rdata     <= 32'h0;
%000005       tl_err       <= 1'b0;
%000005       tl_source_q  <= 8'h0;
%000005       rd_pending_q <= 1'b0;
 000126     end else begin
 000126       tl_rvalid    <= tl_a_valid_i;
 000126       tl_source_q  <= tl_a_source_i;
 000126       tl_err       <= 1'b0;
 000126       rd_pending_q <= tl_rd_en;
 000115       if (tl_rd_en) begin
 000011         case (tl_addr)
%000008           8'h00, 8'h04, 8'h08, 8'h0c: tl_rdata <= 32'h0;
%000001           8'h10: tl_rdata <= iv_reg[0];
%000001           8'h14: tl_rdata <= iv_reg[1];
%000001           8'h18: tl_rdata <= iv_reg[2];
%000000           8'h1c: tl_rdata <= iv_reg[3];
%000000           8'h20, 8'h24, 8'h28, 8'h2c: tl_rdata <= 32'h0;
%000000           8'h30: tl_rdata <= data_out_reg[0];
%000000           8'h34: tl_rdata <= data_out_reg[1];
%000000           8'h38: tl_rdata <= data_out_reg[2];
%000000           8'h3c: tl_rdata <= data_out_reg[3];
%000000           8'h40: tl_rdata <= {30'h0, ctrl_op_q, ctrl_mode_q};
%000000           8'h44: tl_rdata <= 32'h0;
%000000           8'h48: tl_rdata <= {29'h0, status_input_ready, status_output_valid, status_idle};
%000000           8'h4c: tl_rdata <= {31'h0, intr_state_q};
%000000           8'h50: tl_rdata <= {31'h0, intr_enable_q};
%000000           8'h54: tl_rdata <= 32'h0;
%000000           default: begin
%000000             tl_rdata <= 32'h0;
%000000             tl_err   <= 1'b1;
                  end
                endcase
 000115       end else begin
 000115         tl_rdata <= 32'h0;
              end
            end
          end
        
          assign tl_d_valid_o  = tl_rvalid;
 000620   assign tl_d_opcode_o = rd_pending_q ? 3'd1 : 3'd0;
          assign tl_d_data_o   = tl_rdata;
          assign tl_d_source_o = tl_source_q;
          assign tl_d_error_o  = tl_err;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       trigger_start      <= 1'b0;
%000005       trigger_key_clear  <= 1'b0;
%000005       trigger_dout_clear <= 1'b0;
 000126     end else begin
 000126       trigger_start      <= 1'b0;
 000126       trigger_key_clear  <= 1'b0;
 000126       trigger_dout_clear <= 1'b0;
~000126       if (tl_wr_en && (tl_addr == 8'h44)) begin
%000000         trigger_start      <= tl_wdata[0];
%000000         trigger_key_clear  <= tl_wdata[1];
%000000         trigger_dout_clear <= tl_wdata[2];
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       key_reg[0] <= 32'h0; key_reg[1] <= 32'h0; key_reg[2] <= 32'h0; key_reg[3] <= 32'h0;
%000005       iv_reg[0]  <= 32'h0; iv_reg[1]  <= 32'h0; iv_reg[2]  <= 32'h0; iv_reg[3]  <= 32'h0;
%000005       data_in_reg[0] <= 32'h0; data_in_reg[1] <= 32'h0;
%000005       data_in_reg[2] <= 32'h0; data_in_reg[3] <= 32'h0;
%000005       ctrl_mode_q <= 1'b0;
%000005       ctrl_op_q   <= 1'b0;
 000126     end else begin
%000000       if (trigger_key_clear) begin
%000000         key_reg[0] <= 32'h0; key_reg[1] <= 32'h0; key_reg[2] <= 32'h0; key_reg[3] <= 32'h0;
%000000         iv_reg[0]  <= 32'h0; iv_reg[1]  <= 32'h0; iv_reg[2]  <= 32'h0; iv_reg[3]  <= 32'h0;
%000000         data_in_reg[0] <= 32'h0; data_in_reg[1] <= 32'h0;
%000000         data_in_reg[2] <= 32'h0; data_in_reg[3] <= 32'h0;
~000126       end else if (round_finishing && ctrl_mode_q && !ctrl_op_q) begin
%000000         iv_reg[0] <= data_out_next[0]; iv_reg[1] <= data_out_next[1];
%000000         iv_reg[2] <= data_out_next[2]; iv_reg[3] <= data_out_next[3];
~000126       end else if (round_finishing && ctrl_mode_q && ctrl_op_q) begin
%000000         iv_reg[0] <= latched_data[31:0];   iv_reg[1] <= latched_data[63:32];
%000000         iv_reg[2] <= latched_data[95:64];  iv_reg[3] <= latched_data[127:96];
~000122       end else if (tl_wr_en) begin
%000004         case (tl_addr)
%000001           8'h00: key_reg[0] <= tl_wdata;
%000001           8'h04: key_reg[1] <= tl_wdata;
%000001           8'h08: key_reg[2] <= tl_wdata;
%000001           8'h0c: key_reg[3] <= tl_wdata;
%000000           8'h10: iv_reg[0]  <= tl_wdata;
%000000           8'h14: iv_reg[1]  <= tl_wdata;
%000000           8'h18: iv_reg[2]  <= tl_wdata;
%000000           8'h1c: iv_reg[3]  <= tl_wdata;
%000000           8'h20: data_in_reg[0] <= tl_wdata;
%000000           8'h24: data_in_reg[1] <= tl_wdata;
%000000           8'h28: data_in_reg[2] <= tl_wdata;
%000000           8'h2c: data_in_reg[3] <= tl_wdata;
%000000           8'h40: begin
%000000             ctrl_mode_q <= tl_wdata[0];
%000000             ctrl_op_q   <= tl_wdata[1];
                  end
%000000           default: ;
                endcase
              end
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       intr_state_q  <= 1'b0;
%000005       intr_enable_q <= 1'b0;
 000126     end else begin
~000126       if (round_finishing)
%000000         intr_state_q <= 1'b1;
~000126       if (tl_wr_en && (tl_addr == 8'h4c) && tl_wdata[0])
%000000         intr_state_q <= 1'b0;
~000126       if (tl_wr_en && (tl_addr == 8'h50))
%000000         intr_enable_q <= tl_wdata[0];
~000126       if (tl_wr_en && (tl_addr == 8'h54) && tl_wdata[0])
%000000         intr_state_q <= 1'b1;
            end
          end
        
          assign intr_o  = intr_state_q & intr_enable_q;
          assign alert_o = 1'b0;
        
          assign status_idle         = (fsm_q == FSM_IDLE) || (fsm_q == FSM_DONE);
          assign status_output_valid = output_valid_q;
          assign status_input_ready  = input_ready_q;
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       latched_key  <= 128'h0;
%000005       latched_data <= 128'h0;
%000005       latched_iv   <= 128'h0;
~000126     end else if (trigger_start && (fsm_q == FSM_IDLE || fsm_q == FSM_DONE)) begin
%000000       latched_key  <= {key_reg[3], key_reg[2], key_reg[1], key_reg[0]};
%000000       latched_data <= {data_in_reg[3], data_in_reg[2], data_in_reg[1], data_in_reg[0]};
%000000       latched_iv   <= {iv_reg[3], iv_reg[2], iv_reg[1], iv_reg[0]};
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       round_key[0]  <= 128'h0; round_key[1]  <= 128'h0; round_key[2]  <= 128'h0;
%000005       round_key[3]  <= 128'h0; round_key[4]  <= 128'h0; round_key[5]  <= 128'h0;
%000005       round_key[6]  <= 128'h0; round_key[7]  <= 128'h0; round_key[8]  <= 128'h0;
%000005       round_key[9]  <= 128'h0; round_key[10] <= 128'h0;
%000005       key_exp_done_q <= 1'b0;
%000005       key_exp_ctr_q  <= 4'd0;
%000005       ke_last_w[0] <= 32'h0; ke_last_w[1] <= 32'h0;
%000005       ke_last_w[2] <= 32'h0; ke_last_w[3] <= 32'h0;
 000126     end else begin
~000126       if (fsm_q == FSM_KEY_EXP && !key_exp_done_q) begin
%000000         if (key_exp_ctr_q == 4'd0) begin
%000000           round_key[0] <= latched_key;
%000000           ke_last_w[0] <= latched_key[31:0];
%000000           ke_last_w[1] <= latched_key[63:32];
%000000           ke_last_w[2] <= latched_key[95:64];
%000000           ke_last_w[3] <= latched_key[127:96];
%000000           key_exp_ctr_q <= 4'd1;
%000000         end else begin : key_exp_step
                  logic [31:0] t, w0, w1, w2, w3;
%000000           t  = sub_word(rot_word(ke_last_w[3])) ^ {get_rcon(key_exp_ctr_q - 4'd1), 24'h0};
%000000           w0 = ke_last_w[0] ^ t;
%000000           w1 = ke_last_w[1] ^ w0;
%000000           w2 = ke_last_w[2] ^ w1;
%000000           w3 = ke_last_w[3] ^ w2;
%000000           case (key_exp_ctr_q)
%000000             4'd1:  round_key[1]  <= {w3, w2, w1, w0};
%000000             4'd2:  round_key[2]  <= {w3, w2, w1, w0};
%000000             4'd3:  round_key[3]  <= {w3, w2, w1, w0};
%000000             4'd4:  round_key[4]  <= {w3, w2, w1, w0};
%000000             4'd5:  round_key[5]  <= {w3, w2, w1, w0};
%000000             4'd6:  round_key[6]  <= {w3, w2, w1, w0};
%000000             4'd7:  round_key[7]  <= {w3, w2, w1, w0};
%000000             4'd8:  round_key[8]  <= {w3, w2, w1, w0};
%000000             4'd9:  round_key[9]  <= {w3, w2, w1, w0};
%000000             4'd10: round_key[10] <= {w3, w2, w1, w0};
%000000             default: ;
                  endcase
%000000           ke_last_w[0] <= w0;
%000000           ke_last_w[1] <= w1;
%000000           ke_last_w[2] <= w2;
%000000           ke_last_w[3] <= w3;
%000000           if (key_exp_ctr_q == 4'd10)
%000000             key_exp_done_q <= 1'b1;
                  else
%000000             key_exp_ctr_q <= key_exp_ctr_q + 4'd1;
                end
              end
~000126       if (trigger_start && (fsm_q == FSM_IDLE || fsm_q == FSM_DONE)) begin
%000000         key_exp_done_q <= 1'b0;
%000000         key_exp_ctr_q  <= 4'd0;
              end
            end
          end
        
 000686   always_comb begin
 000686     case (round_ctr_q)
~000686       4'd0:  current_rk = ctrl_op_q ? round_key[10] : round_key[0];
~000686       4'd1:  current_rk = ctrl_op_q ? round_key[9]  : round_key[1];
~000686       4'd2:  current_rk = ctrl_op_q ? round_key[8]  : round_key[2];
~000686       4'd3:  current_rk = ctrl_op_q ? round_key[7]  : round_key[3];
~000686       4'd4:  current_rk = ctrl_op_q ? round_key[6]  : round_key[4];
~000686       4'd5:  current_rk = ctrl_op_q ? round_key[5]  : round_key[5];
~000686       4'd6:  current_rk = ctrl_op_q ? round_key[4]  : round_key[6];
~000686       4'd7:  current_rk = ctrl_op_q ? round_key[3]  : round_key[7];
~000686       4'd8:  current_rk = ctrl_op_q ? round_key[2]  : round_key[8];
~000686       4'd9:  current_rk = ctrl_op_q ? round_key[1]  : round_key[9];
~000686       4'd10: current_rk = ctrl_op_q ? round_key[0]  : round_key[10];
%000000       default: current_rk = 128'h0;
            endcase
          end
        
 000686   function automatic logic [127:0] enc_round(input logic [127:0] s, input logic [127:0] rk, input logic last_round);
            logic [127:0] after_sb, after_sr, after_mc;
 000686     after_sb = sub_bytes_fwd(s);
 000686     after_sr = shift_rows_fwd(after_sb);
%000000     if (last_round)
%000000       return after_sr ^ rk;
%000000     else begin
%000000       after_mc = mix_columns_fwd(after_sr);
%000000       return after_mc ^ rk;
            end
          endfunction
        
%000000   function automatic logic [127:0] dec_round(input logic [127:0] s, input logic [127:0] rk, input logic last_round);
            logic [127:0] after_isr, after_isb, after_ark;
%000000     after_isr = shift_rows_inv(s);
%000000     after_isb = sub_bytes_inv(after_isr);
%000000     after_ark = after_isb ^ rk;
%000000     if (last_round)
%000000       return after_ark;
            else
%000000       return mix_columns_inv(after_ark);
          endfunction
        
 000686   always_comb begin
~000686     if (!ctrl_op_q)
 000686       state_nxt = enc_round(state_q, current_rk, (round_ctr_q == 4'd10));
            else
%000000       state_nxt = dec_round(state_q, current_rk, (round_ctr_q == 4'd10));
          end
        
          assign round_finishing = (fsm_q == FSM_ROUND) && (round_ctr_q == 4'd10);
        
 000686   always_comb begin
 000686     data_out_next[0] = state_nxt[31:0];
 000686     data_out_next[1] = state_nxt[63:32];
 000686     data_out_next[2] = state_nxt[95:64];
 000686     data_out_next[3] = state_nxt[127:96];
~000686     if (ctrl_op_q && ctrl_mode_q) begin
%000000       data_out_next[0] = state_nxt[31:0]   ^ latched_iv[31:0];
%000000       data_out_next[1] = state_nxt[63:32]  ^ latched_iv[63:32];
%000000       data_out_next[2] = state_nxt[95:64]  ^ latched_iv[95:64];
%000000       data_out_next[3] = state_nxt[127:96] ^ latched_iv[127:96];
            end
 000686     data_out_we = round_finishing;
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       data_out_reg[0] <= 32'h0; data_out_reg[1] <= 32'h0;
%000005       data_out_reg[2] <= 32'h0; data_out_reg[3] <= 32'h0;
%000000     end else if (trigger_dout_clear) begin
%000000       data_out_reg[0] <= 32'h0; data_out_reg[1] <= 32'h0;
%000000       data_out_reg[2] <= 32'h0; data_out_reg[3] <= 32'h0;
~000126     end else if (data_out_we) begin
%000000       data_out_reg[0] <= data_out_next[0]; data_out_reg[1] <= data_out_next[1];
%000000       data_out_reg[2] <= data_out_next[2]; data_out_reg[3] <= data_out_next[3];
            end
          end
        
 000131   always_ff @(posedge clk_i or negedge rst_ni) begin
~000126     if (!rst_ni) begin
%000005       fsm_q          <= FSM_IDLE;
%000005       round_ctr_q    <= 4'd0;
%000005       output_valid_q <= 1'b0;
%000005       input_ready_q  <= 1'b1;
%000005       state_q        <= 128'h0;
 000126     end else begin
 000126       case (fsm_q)
 000126         FSM_IDLE: begin
~000126           if (trigger_start) begin
%000000             fsm_q          <= FSM_KEY_EXP;
%000000             output_valid_q <= 1'b0;
%000000             input_ready_q  <= 1'b0;
%000000             round_ctr_q    <= 4'd0;
                  end
                end
        
%000000         FSM_KEY_EXP: begin
%000000           if (key_exp_done_q) begin
%000000             fsm_q       <= FSM_INIT;
%000000             round_ctr_q <= 4'd1;
%000000             if (!ctrl_op_q) begin
%000000               if (ctrl_mode_q)
%000000                 state_q <= latched_data ^ latched_iv ^ round_key[0];
                      else
%000000                 state_q <= latched_data ^ round_key[0];
%000000             end else begin
%000000               state_q <= latched_data ^ round_key[NUM_ROUNDS];
                    end
                  end
                end
        
%000000         FSM_INIT: begin
%000000           fsm_q <= FSM_ROUND;
                end
        
%000000         FSM_ROUND: begin
%000000           state_q <= state_nxt;
%000000           if (round_ctr_q < 4'd10) begin
%000000             round_ctr_q <= round_ctr_q + 4'd1;
%000000           end else begin
%000000             fsm_q          <= FSM_DONE;
%000000             output_valid_q <= 1'b1;
%000000             input_ready_q  <= 1'b1;
                  end
                end
        
%000000         FSM_DONE: begin
%000000           if (trigger_start) begin
%000000             fsm_q          <= FSM_KEY_EXP;
%000000             output_valid_q <= 1'b0;
%000000             input_ready_q  <= 1'b0;
%000000             round_ctr_q    <= 4'd0;
                  end
                end
        
%000000         default: begin
%000000           fsm_q <= FSM_IDLE;
                end
              endcase
            end
          end
        
        endmodule
        
