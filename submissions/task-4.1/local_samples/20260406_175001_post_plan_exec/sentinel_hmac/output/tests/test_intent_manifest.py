# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Verify reset values, TL-UL read/write access, reserved-bit behavior, and unmapped address error response.
# - cfg_mode_matrix: Program all valid CFG combinations, confirm invalid hmac_en without sha_en is rejected or safely ignored, and check mode-dependent status transitions.
# - sha256_single_block_known_vector: Run SHA-256-only mode on a known short message, issue hash_start and hash_stop, and compare digest against a software reference.
# - hmac_known_vector: Run HMAC-SHA256 on a known key/message pair, verify key processing path, and compare final digest against a software reference.
# - streaming_multi_block_hash: Write message data in multiple chunks across FIFO boundaries, use hash_process and hash_stop, and verify correct digest for a multi-block message.
# - partial_block_padding: Exercise finalization with a non-512-bit-aligned message to validate automatic SHA-256 padding and length encoding.
# - fifo_full_backpressure: Fill the 32-entry FIFO to capacity, confirm STATUS fifo_full and tl_i_ready backpressure behavior, then drain and continue operation.
# - wipe_secret_zeroization: Load key material, trigger WIPE_SECRET, and verify key registers and secret-related state are cleared without corrupting non-secret CSRs.
# - digest_swap_endian_swap: Check byte-order transformation effects on input and output by comparing swapped versus non-swapped digest results.
# - reset_during_active_operation: Assert reset while hashing is active and verify the DUT returns to a clean idle state with cleared FIFO and default CSRs.
#
# Random tests:
# - tlul_csr_fuzz: Randomize legal TL-UL CSR reads and writes across the register map, including reserved bits and repeated accesses, while checking protocol stability and mirrored CSR behavior.
# - streaming_message_fuzzer: Generate random message lengths, chunk sizes, and command interleavings within legal sequencing to stress FIFO, padding, and digest generation against a Python SHA-256/HMAC model.
# - mode_and_swap_random: Randomly vary CFG mode bits and endian/digest swap settings across multiple short transactions to maximize branch coverage in mode-dependent datapaths.
