# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_sanity: Apply reset, verify TL-UL accessibility, confirm CSR defaults, and check that status/interrupt/alert outputs are quiescent after reset.
# - ecb_encrypt_known_vector: Program a known AES-128 key and plaintext in ECB mode, trigger encryption, poll for completion, and compare ciphertext against a golden reference.
# - ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext in ECB mode, trigger decryption, and verify recovered plaintext matches the golden reference.
# - cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, trigger operation, and verify ciphertext plus IV update behavior against a golden model.
# - cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, trigger operation, and verify plaintext plus IV update behavior against a golden model.
# - back_to_back_ecb_blocks: Issue consecutive ECB start triggers with new input data as soon as input_ready allows, verifying output retention, throughput behavior, and no data corruption between blocks.
# - clear_trigger_behavior: Exercise key_iv_data_in_clear and data_out_clear separately, confirming that programmed registers are zeroized and that output clearing does not disturb unrelated control state.
# - interrupt_completion_flow: Enable interrupt generation if supported by CSR map, start an operation, and verify intr_o asserts on completion and deasserts according to expected acknowledge/clear behavior.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads and writes over the discovered CSR space, checking protocol stability, legal access behavior, and absence of bus hangs within the time budget.
# - mode_operation_random_matrix: Randomize ECB/CBC, encrypt/decrypt, key/data values, and start timing across a small set of transactions, comparing results to a software AES reference model.
# - back_to_back_random_stream: Generate a short stream of random blocks with randomized inter-block gaps to stress input_ready, DONE-to-IDLE transitions, and output overwrite hazards.
# - reset_during_idle_and_busy: Assert reset at random points during idle and active operation to validate safe recovery, CSR reinitialization, and no stuck interrupt or alert conditions.
