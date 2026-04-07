# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_sanity: Verify reset deassertion, TL-UL accessibility, readable/writable CSR defaults, and that status/control registers respond without protocol errors.
# - aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, trigger ECB encryption, and compare ciphertext against a golden model.
# - aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, trigger ECB decryption, and compare recovered plaintext against a golden model.
# - aes_cbc_encrypt_known_vector: Program key, IV, and plaintext, trigger CBC encryption, and verify ciphertext plus IV update behavior against a golden model.
# - aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext, trigger CBC decryption, and verify plaintext recovery and IV update behavior.
# - back_to_back_block_operations: Issue consecutive start triggers with new input data and confirm the DUT accepts the next block when input_ready indicates availability.
# - clear_triggers: Exercise key_iv_data_in_clear and data_out_clear independently and confirm registers are zeroized without corrupting unrelated control/status behavior.
# - interrupt_completion_flow: Enable/observe completion interrupt behavior and confirm intr_o asserts on done and deasserts according to the design's completion semantics.
# - tlul_backpressure_and_wait_states: Apply host-side ready deassertion and randomized TL-UL request spacing to verify stable request/response handling under backpressure.
#
# Random tests:
# - csr_fuzz_smoke: Randomize legal CSR writes and reads across key, IV, data, control, trigger, and status registers while checking TL-UL protocol correctness and basic register coherency.
# - mode_operation_randomized: Randomly select ECB/CBC and encrypt/decrypt operations with constrained legal sequences, then compare outputs to a Python AES reference model.
# - multi_block_stream_randomized: Generate short random block streams to stress back-to-back operation handling, output retention, and IV chaining in CBC mode.
# - reset_interruption_randomized: Assert reset at random points during idle and active operation to verify safe recovery, no protocol deadlock, and clean post-reset CSR state.
