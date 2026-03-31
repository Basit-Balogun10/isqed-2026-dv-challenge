package dv_common_pkg;

  localparam logic [2:0] TL_OP_PUT_FULL    = 3'd0;
  localparam logic [2:0] TL_OP_PUT_PARTIAL = 3'd1;
  localparam logic [2:0] TL_OP_GET         = 3'd4;

  localparam logic [2:0] TL_OP_ACCESS_ACK      = 3'd0;
  localparam logic [2:0] TL_OP_ACCESS_ACK_DATA = 3'd1;

  typedef enum logic [2:0] {
    CSR_RW   = 3'd0,
    CSR_RO   = 3'd1,
    CSR_W1C  = 3'd2,
    CSR_W1S  = 3'd3,
    CSR_W0C  = 3'd4,
    CSR_RC   = 3'd5
  } csr_access_e;

endpackage
