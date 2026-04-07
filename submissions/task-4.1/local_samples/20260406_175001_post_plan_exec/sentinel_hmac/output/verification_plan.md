# Verification Plan

## Features
- TL-UL CSR read/write access with same-cycle response and unmapped address error handling
- CFG register programming for hmac_en, sha_en, endian_swap, and digest_swap
- CMD W1S sequencing for hash_start, hash_process, and hash_stop
- STATUS register observation for fifo_full, fifo_empty, fifo_depth, and sha_idle
- WIPE_SECRET zeroization behavior for key registers and internal secret state
- HMAC mode key processing and SHA-256-only mode operation
- Message FIFO depth management and backpressure behavior
- Multi-block streaming hash flow with partial and full block handling
- Digest register readout and byte-swap behavior
- Interrupt and alert pin sanity checks
- Reset recovery and post-reset register defaults
- Invalid configuration handling for hmac_en without sha_en

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Verify reset values, TL-UL read/write access, reserved-bit behavior, and unmapped address error response.
- cfg_mode_matrix: Program all valid CFG combinations, confirm invalid hmac_en without sha_en is rejected or safely ignored, and check mode-dependent status transitions.
- sha256_single_block_known_vector: Run SHA-256-only mode on a known short message, issue hash_start and hash_stop, and compare digest against a software reference.
- hmac_known_vector: Run HMAC-SHA256 on a known key/message pair, verify key processing path, and compare final digest against a software reference.
- streaming_multi_block_hash: Write message data in multiple chunks across FIFO boundaries, use hash_process and hash_stop, and verify correct digest for a multi-block message.
- partial_block_padding: Exercise finalization with a non-512-bit-aligned message to validate automatic SHA-256 padding and length encoding.
- fifo_full_backpressure: Fill the 32-entry FIFO to capacity, confirm STATUS fifo_full and tl_i_ready backpressure behavior, then drain and continue operation.
- wipe_secret_zeroization: Load key material, trigger WIPE_SECRET, and verify key registers and secret-related state are cleared without corrupting non-secret CSRs.
- digest_swap_endian_swap: Check byte-order transformation effects on input and output by comparing swapped versus non-swapped digest results.
- reset_during_active_operation: Assert reset while hashing is active and verify the DUT returns to a clean idle state with cleared FIFO and default CSRs.

## Random Tests
- tlul_csr_fuzz: Randomize legal TL-UL CSR reads and writes across the register map, including reserved bits and repeated accesses, while checking protocol stability and mirrored CSR behavior.
- streaming_message_fuzzer: Generate random message lengths, chunk sizes, and command interleavings within legal sequencing to stress FIFO, padding, and digest generation against a Python SHA-256/HMAC model.
- mode_and_swap_random: Randomly vary CFG mode bits and endian/digest swap settings across multiple short transactions to maximize branch coverage in mode-dependent datapaths.

## Risk Areas
- HMAC key expansion and double-pass sequencing (high): Most complex control path; errors here can silently produce incorrect digests even when basic SHA-256 mode passes.
- Padding and final block handling (high): Off-by-one and length-encoding bugs are common in SHA-256 finalization, especially for partial blocks and multi-block streams.
- FIFO depth, backpressure, and command ordering (high): The 32-entry FIFO and process/stop sequencing can expose deadlocks or dropped words under boundary conditions.
- CFG invalid combinations and mode gating (medium): Illegal hmac_en without sha_en may lead to undefined internal state if not handled defensively.
- WIPE_SECRET zeroization completeness (medium): Security-sensitive state clearing must cover key registers and internal secret state without disturbing functional CSRs.
- Endian and digest byte swapping (medium): Byte-order transforms are easy to mis-implement and can cause mismatches only on specific message patterns.
- TL-UL unmapped address and reserved-bit handling (low): Protocol compliance issues are usually localized but important for integration robustness.
