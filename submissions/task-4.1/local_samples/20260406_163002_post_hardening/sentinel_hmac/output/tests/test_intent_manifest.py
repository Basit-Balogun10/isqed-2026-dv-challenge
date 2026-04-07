# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_map: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
# - cfg_mode_sanity: Program valid CFG combinations for bare SHA and HMAC modes, confirm illegal hmac_en without sha_en is rejected or safely ignored per RTL behavior, and check status reflects idle/empty after configuration.
# - bare_sha_single_block_known_vector: Run a single-block SHA-256 test with a known message and compare digest registers against a software reference model, including digest_swap and endian_swap permutations.
# - bare_sha_multi_block_streaming: Exercise hash_start, repeated message writes, hash_process, and hash_stop across multiple 512-bit blocks to verify streaming accumulation and final digest correctness.
# - hmac_known_vector: Program a known 256-bit key and message, execute full HMAC flow, and compare final digest against a software HMAC-SHA256 reference.
# - fifo_depth_and_full_empty: Fill the 32-entry FIFO to observe fifo_depth, fifo_full, and fifo_empty transitions, then drain through processing to confirm status updates and no data loss.
# - wipe_secret_zeroization: After loading key material and/or completing an HMAC operation, write WIPE_SECRET and verify key registers and secret-related state are cleared while non-secret control/status behavior remains functional.
# - reset_during_active_operation: Assert reset while a hash operation is in progress and confirm all state, FIFO contents, status bits, and digest outputs return to reset values without bus lockup.
# - interrupt_and_alert_smoke: Check that interrupt outputs and alert_o remain quiescent in nominal flows and only assert if the RTL exposes completion/error signaling; otherwise confirm stable inactive behavior.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Randomize legal TL-UL reads and writes across the CSR map, including reserved bits and repeated accesses, to catch decode, masking, and side-effect issues within the time budget.
# - random_message_streaming_sha: Generate random message lengths, chunk sizes, and command interleavings for bare SHA mode, then compare digest results to a Python reference model.
# - random_message_streaming_hmac: Generate random keys and messages for HMAC mode with varied chunking and finalization timing, checking digest correctness against a software reference.
# - random_endian_digest_swap_matrix: Randomly sweep endian_swap and digest_swap combinations across representative messages to validate byte-order transformations and register packing.
# - fifo_pressure_random: Apply randomized write bursts and processing commands to stress FIFO occupancy, backpressure, and status coherence without exceeding the 60-minute execution budget.
