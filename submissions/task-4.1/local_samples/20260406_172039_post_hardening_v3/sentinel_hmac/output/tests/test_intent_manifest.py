# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
# - cfg_mode_matrix: Exercise valid and invalid CFG combinations across bare SHA and HMAC modes, including endian_swap and digest_swap permutations.
# - sha_single_block_known_vector: Program bare SHA mode, hash a single 512-bit message block, and compare digest against a golden SHA-256 reference.
# - sha_multi_block_streaming: Write a message in multiple FIFO chunks, issue hash_process across block boundaries, and verify final digest matches the reference model.
# - sha_partial_block_padding: Finalize messages of varying non-block-aligned lengths to validate automatic padding and length encoding.
# - hmac_known_vector: Load a known HMAC key and message, run the full HMAC sequence, and compare the final digest against a software reference.
# - hmac_key_zeroization_wipe: After HMAC operation, write WIPE_SECRET and confirm key registers and secret-related state are cleared.
# - fifo_full_empty_depth: Fill the 32-entry FIFO to capacity, verify fifo_full assertion and depth tracking, then drain and verify fifo_empty.
# - cmd_sequence_illegal_order: Attempt hash_process and hash_stop before hash_start, and verify the DUT either ignores or flags the sequence per observed RTL behavior without deadlock.
# - digest_swap_endian_swap: Independently toggle endian_swap and digest_swap to confirm byte-order transformations on input words and digest output words.
#
# Random tests:
# - constrained_random_sha_stream: Randomize message lengths, chunk sizes, FIFO write pacing, and command timing in bare SHA mode while checking against a Python SHA-256 model.
# - constrained_random_hmac_stream: Randomize key values, message lengths, and streaming patterns in HMAC mode, including partial blocks and finalization, with golden HMAC comparison.
# - tlul_csr_fuzzer: Randomly issue aligned CSR reads/writes, reserved-bit writes, and unmapped accesses to stress TL-UL protocol handling and register decode.
# - status_polling_stress: Randomly poll STATUS during active hashing to validate fifo_depth, fifo_empty/full, and sha_idle transitions under concurrent traffic.
