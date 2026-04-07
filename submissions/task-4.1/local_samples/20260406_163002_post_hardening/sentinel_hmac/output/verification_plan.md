# Verification Plan

## Features
- TL-UL CSR read/write compliance
- CFG mode control: hmac_en, sha_en, endian_swap, digest_swap
- CMD sequencing: hash_start, hash_process, hash_stop
- STATUS reporting: fifo_full, fifo_empty, fifo_depth, sha_idle
- Message FIFO depth and backpressure behavior
- SHA-256 bare hash flow
- HMAC key processing flow
- Padding and finalization behavior
- Digest register readout and byte-order handling
- WIPE_SECRET zeroization behavior
- Invalid configuration handling
- Unmapped address error response
- Interrupt and alert smoke checks
- Reset recovery and state clearing
- Multi-block streaming operation

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
- cfg_mode_sanity: Program valid CFG combinations for bare SHA and HMAC modes, confirm illegal hmac_en without sha_en is rejected or safely ignored per RTL behavior, and check status reflects idle/empty after configuration.
- bare_sha_single_block_known_vector: Run a single-block SHA-256 test with a known message and compare digest registers against a software reference model, including digest_swap and endian_swap permutations.
- bare_sha_multi_block_streaming: Exercise hash_start, repeated message writes, hash_process, and hash_stop across multiple 512-bit blocks to verify streaming accumulation and final digest correctness.
- hmac_known_vector: Program a known 256-bit key and message, execute full HMAC flow, and compare final digest against a software HMAC-SHA256 reference.
- fifo_depth_and_full_empty: Fill the 32-entry FIFO to observe fifo_depth, fifo_full, and fifo_empty transitions, then drain through processing to confirm status updates and no data loss.
- wipe_secret_zeroization: After loading key material and/or completing an HMAC operation, write WIPE_SECRET and verify key registers and secret-related state are cleared while non-secret control/status behavior remains functional.
- reset_during_active_operation: Assert reset while a hash operation is in progress and confirm all state, FIFO contents, status bits, and digest outputs return to reset values without bus lockup.
- interrupt_and_alert_smoke: Check that interrupt outputs and alert_o remain quiescent in nominal flows and only assert if the RTL exposes completion/error signaling; otherwise confirm stable inactive behavior.

## Random Tests
- tlul_csr_fuzz_smoke: Randomize legal TL-UL reads and writes across the CSR map, including reserved bits and repeated accesses, to catch decode, masking, and side-effect issues within the time budget.
- random_message_streaming_sha: Generate random message lengths, chunk sizes, and command interleavings for bare SHA mode, then compare digest results to a Python reference model.
- random_message_streaming_hmac: Generate random keys and messages for HMAC mode with varied chunking and finalization timing, checking digest correctness against a software reference.
- random_endian_digest_swap_matrix: Randomly sweep endian_swap and digest_swap combinations across representative messages to validate byte-order transformations and register packing.
- fifo_pressure_random: Apply randomized write bursts and processing commands to stress FIFO occupancy, backpressure, and status coherence without exceeding the 60-minute execution budget.

## Risk Areas
- CMD sequencing and self-clearing behavior (high): W1S command registers are prone to edge-trigger and race-condition bugs, especially around hash_start/hash_process/hash_stop ordering and repeated writes.
- HMAC key expansion and double-pass finalization (high): HMAC introduces extra internal state, ipad/opad processing, and automatic outer hash sequencing, which are common sources of functional mismatch.
- Padding and partial-block handling (high): SHA-256 finalization with arbitrary message lengths is error-prone, especially when the FIFO contains partial blocks at hash_stop.
- FIFO depth/status coherence (high): The 32-entry FIFO and status bits must remain consistent under bursty writes and processing; off-by-one errors are likely.
- Byte-order transformations (medium): endian_swap and digest_swap can silently corrupt data paths if word/byte ordering is implemented inconsistently.
- WIPE_SECRET zeroization scope (medium): Secret clearing must remove key material and internal state without breaking subsequent operations; scope ambiguity increases risk.
- TL-UL decode and error response (medium): Unmapped address handling and reserved-bit masking are straightforward but important for bus robustness.
- Interrupt and alert behavior (low): These outputs may be lightly implemented or unused; smoke coverage is sufficient within the time budget.
