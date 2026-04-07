# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_map: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
# - cfg_mode_matrix: Exercise CFG combinations for SHA-only, HMAC+SHA, and invalid hmac_en without sha_en; confirm legal mode acceptance and invalid configuration handling.
# - cmd_w1s_semantics: Check that CMD bits are write-1-to-set and self-clearing, and that hash_start, hash_process, and hash_stop can be issued independently and in sequence.
# - sha_single_block_known_vector: Run a bare SHA-256 known-answer test for a single-block message and compare digest register contents against a software reference model.
# - sha_multi_block_streaming: Send a message in multiple FIFO chunks, trigger hash_process across block boundaries, and verify final digest matches the reference model.
# - sha_partial_block_padding: Cover finalization with a partial block to validate automatic SHA-256 padding and message length encoding.
# - hmac_known_vector: Program a known HMAC key and message, run full HMAC flow, and verify the final digest against a software HMAC-SHA256 reference.
# - hmac_key_zeroization: After HMAC completion, write WIPE_SECRET and confirm key registers and secret-related state are cleared and remain cleared on subsequent reads.
# - fifo_status_and_backpressure: Fill the 32-entry FIFO to full, observe STATUS fifo_full/fifo_empty/fifo_depth transitions, then drain and confirm correct recovery.
# - endian_and_digest_swap: Toggle endian_swap and digest_swap independently and together, verifying message word ordering and digest byte ordering against the model.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Randomize legal TL-UL CSR reads/writes, including reserved-bit writes and repeated reads, to catch decode and side-effect issues within the 60-minute budget.
# - streaming_message_fuzzer: Generate random message lengths, chunk sizes, and hash_start/hash_process/hash_stop sequences in SHA-only mode, checking digest equivalence to a Python reference model.
# - hmac_streaming_fuzzer: Randomize keys, message lengths, and FIFO write patterns in HMAC mode to stress key expansion, inner/outer pass sequencing, and final digest correctness.
# - status_transition_fuzzer: Randomly sample FIFO occupancy and command timing to validate STATUS field monotonicity and legal transitions under back-to-back operations.
