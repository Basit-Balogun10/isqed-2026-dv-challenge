# Trace 04: Aegis AES — CBC IV Wrong on Second Block

## Failing Assertion

```
ASSERTION FAILED: assert_cbc_iv_chain
  Location: aegis_aes_sva.sv:93
  Message: "In CBC mode, the IV for block N+1 must equal the ciphertext of block N"
  Failure time: cycle 200
```

## Spec Requirement

From the Aegis AES Specification, Section 5.3:

> **CBC Mode Operation:** In CBC (Cipher Block Chaining) mode, each plaintext block
> is XOR'd with the previous ciphertext block before encryption:
>
>   C[0] = AES_Encrypt(P[0] XOR IV)
>   C[n] = AES_Encrypt(P[n] XOR C[n-1])    for n >= 1
>
> The IV register must be loaded with the initial IV before the first block. After
> encrypting block N, the hardware SHALL automatically update the IV register with
> the ciphertext output C[N] so that the next block encryption uses C[N] as the IV.

## Test Scenario

1. Configure AES: mode=CBC, operation=ENCRYPT, key_len=128
2. Load key: 128'h2b7e1516_28aed2a6_abf71588_09cf4f3c
3. Load IV: 128'h00010203_04050607_08090a0b_0c0d0e0f
4. Encrypt block 0: plaintext = 128'h6bc1bee2_2e409f96_e93d7e11_7393172a
   - Expected C[0] = 128'h7649abac_8119b246_cee98e9b_12e9197d
5. Encrypt block 1: plaintext = 128'hae2d8a57_1e03ac9c_9eb76fac_45af8e51
   - Expected C[1] = 128'h5086cb9b_507219ee_95db113a_917678b2
   - This requires IV = C[0] = 128'h7649abac_8119b246_cee98e9b_12e9197d

## Observed Behavior

Block 0 encrypts correctly, producing the expected C[0]. However, block 1 produces
incorrect ciphertext because the IV register still contains the original IV
(128'h00010203_04050607_08090a0b_0c0d0e0f) instead of C[0]. The hardware does not
auto-update the IV after block 0 completes.

The XOR in the first round of block 1 uses the wrong IV, producing completely
different ciphertext.

## Signal Trace File

See `trace_04_signals.csv` for cycle-by-cycle signal values.
Key signals:
- `state_q[127:0]` — AES internal state (shows XOR result before encryption)
- `iv_reg[127:0]` — IV register value (watch for update after block 0)
- `data_out[127:0]` — ciphertext output
- `output_valid` — indicates encryption complete
- `round_cnt` — current AES round number
- `aes_state` — FSM state (IDLE, KEY_EXPAND, ENCRYPT, DONE)
- `block_cnt` — block counter in CBC mode
