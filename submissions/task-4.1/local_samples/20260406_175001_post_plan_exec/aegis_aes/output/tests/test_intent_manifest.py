# Auto-generated test intent summary
#
# Directed tests:
# - smoke_reset_and_csr_sanity: Verify reset deassertion, TL-UL accessibility, readable/writable CSR map basics, and expected default values for status/control registers.
# - aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, start ECB encryption, and compare output against a golden FIPS-197 vector.
# - aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, start ECB decryption, and verify recovered plaintext matches the golden vector.
# - aes_cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, start operation, and verify ciphertext and IV update behavior against a golden model.
# - aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, start operation, and verify plaintext recovery and IV chaining behavior.
# - back_to_back_block_sequence: Issue consecutive start triggers with new input data after input_ready, confirming output retention, throughput continuity, and no lost transactions.
# - clear_key_iv_data_and_output: Exercise key_iv_data_in_clear and data_out_clear separately, confirming all targeted registers are zeroized and normal operation resumes afterward.
# - interrupt_completion_and_status_polling: Verify intr_o assertion on operation completion and consistency between interrupt timing and status bits output_valid/input_ready.
#
# Random tests:
# - tlul_csr_fuzz_legal_accesses: Randomize legal TL-UL read/write sequences across all implemented CSRs, including partial programming order variations, while checking protocol stability and CSR side effects.
# - mode_operation_randomized_regression: Randomly vary ECB/CBC, encrypt/decrypt, key/data values, and start timing to validate functional correctness against a Python AES reference model.
# - multi_block_cbc_chaining_random: Generate random multi-block CBC streams to stress IV update, chaining correctness, and back-to-back operation behavior.
# - reset_interruption_random: Assert reset at random points during idle and active operation to confirm safe recovery, CSR reinitialization, and absence of stuck status or interrupt behavior.
