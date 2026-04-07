# Verification Plan

## Features
- TL-UL CSR read/write compliance
- Reset behavior and default CSR values
- CFG mode control: hmac_en, sha_en, endian_swap, digest_swap
- CMD W1S sequencing: hash_start, hash_process, hash_stop
- STATUS register correctness: fifo_full, fifo_empty, fifo_depth, sha_idle
- Message FIFO push/pop behavior and depth tracking
- SHA-256 bare mode functional flow
- HMAC functional flow with key processing and double-pass operation
- Partial-block padding and finalization behavior
- Digest register readout and byte-swap behavior
- WIPE_SECRET zeroization of key/state
- Unmapped address error response
- Backpressure handling on TL-UL ready/valid
- Interrupt and alert pin sanity
- Illegal configuration handling: hmac_en without sha_en
- Multi-block streaming across arbitrary chunk sizes

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
- cfg_mode_matrix: Exercise valid and invalid CFG combinations across bare SHA and HMAC modes, including endian_swap and digest_swap permutations.
- sha_single_block_known_vector: Program bare SHA mode, hash a single 512-bit message block, and compare digest against a golden SHA-256 reference.
- sha_multi_block_streaming: Write a message in multiple FIFO chunks, issue hash_process across block boundaries, and verify final digest matches the reference model.
- sha_partial_block_padding: Finalize messages of varying non-block-aligned lengths to validate automatic padding and length encoding.
- hmac_known_vector: Load a known HMAC key and message, run the full HMAC sequence, and compare the final digest against a software reference.
- hmac_key_zeroization_wipe: After HMAC operation, write WIPE_SECRET and confirm key registers and secret-related state are cleared.
- fifo_full_empty_depth: Fill the 32-entry FIFO to capacity, verify fifo_full assertion and depth tracking, then drain and verify fifo_empty.
- cmd_sequence_illegal_order: Attempt hash_process and hash_stop before hash_start, and verify the DUT either ignores or flags the sequence per observed RTL behavior without deadlock.
- digest_swap_endian_swap: Independently toggle endian_swap and digest_swap to confirm byte-order transformations on input words and digest output words.

## Random Tests
- constrained_random_sha_stream: Randomize message lengths, chunk sizes, FIFO write pacing, and command timing in bare SHA mode while checking against a Python SHA-256 model.
- constrained_random_hmac_stream: Randomize key values, message lengths, and streaming patterns in HMAC mode, including partial blocks and finalization, with golden HMAC comparison.
- tlul_csr_fuzzer: Randomly issue aligned CSR reads/writes, reserved-bit writes, and unmapped accesses to stress TL-UL protocol handling and register decode.
- status_polling_stress: Randomly poll STATUS during active hashing to validate fifo_depth, fifo_empty/full, and sha_idle transitions under concurrent traffic.

## Risk Areas
- HMAC double-pass sequencing (high): The design performs an inner hash followed by an automatic outer hash; bugs here can silently corrupt authentication results and are high impact.
- Padding and message length handling (high): SHA-256 finalization is error-prone for partial blocks and multi-block streams; off-by-one or length encoding defects are likely.
- FIFO depth/full/empty control (high): The 32-entry FIFO is central to streaming operation; incorrect backpressure or depth accounting can cause data loss or deadlock.
- CFG illegal mode combinations (medium): hmac_en without sha_en is explicitly invalid and may expose undefined internal state or unexpected behavior.
- Byte-order transformations (medium): endian_swap and digest_swap affect interoperability and are easy to implement incorrectly, but are localized to data formatting.
- WIPE_SECRET zeroization (high): Secret clearing must reliably remove key material and internal state; failures are security-relevant but likely limited in scope.
- TL-UL protocol corner cases (medium): Unmapped access, ready/valid backpressure, and same-cycle response behavior can cause integration issues, though functional scope is narrower.
- Interrupt and alert outputs (low): Only lightly specified in the excerpt; basic sanity is needed, but exhaustive validation is lower priority within the time budget.
