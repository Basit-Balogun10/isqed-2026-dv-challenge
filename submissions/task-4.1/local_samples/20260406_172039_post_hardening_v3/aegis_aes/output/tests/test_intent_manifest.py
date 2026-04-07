# Auto-generated test intent summary
#
# Directed tests:
# - smoke_reset_and_csr_map: Verify reset deassertion, TL-UL connectivity, readable/writable CSR locations, WO/RW access behavior, and that reserved/undefined addresses do not crash the DUT.
# - aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, start ECB encryption, and compare ciphertext against a software reference model.
# - aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, start ECB decryption, and compare recovered plaintext against the reference model.
# - aes_cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, verify ciphertext and IV update behavior against the reference model.
# - aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, verify plaintext recovery and IV update behavior against the reference model.
# - back_to_back_block_processing: Issue consecutive start triggers with new input data and confirm the DUT accepts the next block when input_ready indicates availability, preserving output ordering.
# - clear_controls_behavior: Exercise key_iv_data_in_clear and data_out_clear separately, confirming registers are zeroized and that clear operations do not corrupt unrelated control/status state.
# - interrupt_completion_flow: Verify intr_o asserts on operation completion and that status/output readback can be used to clear or acknowledge the completed transaction in the expected software flow.
#
# Random tests:
# - tlul_csr_fuzz_legal_ops: Run constrained-random TL-UL reads and writes over valid CSR addresses, checking protocol stability, access permissions, and no unexpected alerting on legal traffic.
# - aes_mode_op_randomized: Randomize mode, encrypt/decrypt selection, key, IV, and data blocks across ECB/CBC operations and compare results to a Python AES reference model.
# - multi_block_cbc_stream: Generate short random CBC sequences of 2 to 4 blocks to stress IV chaining, output overwrite timing, and back-to-back operation handling.
# - reset_interruption_stress: Assert reset during idle and during active operation at random times to confirm safe recovery, CSR reinitialization, and no stuck interrupt or alert conditions.
