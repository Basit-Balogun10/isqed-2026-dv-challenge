# Verification Plan

## Features
- TL-UL CSR read/write compliance
- Reset behavior and default CSR values
- CFG mode selection: HMAC vs SHA-only
- Invalid configuration handling: hmac_en without sha_en
- W1S command semantics for CMD and WIPE_SECRET
- FIFO depth/full/empty status reporting
- Message streaming through 32-entry write FIFO
- SHA-256 block processing and finalization
- HMAC key expansion and double-pass sequencing
- Endian swap and digest swap behavior
- Digest register readback correctness
- Interrupt and alert pin sanity
- Unmapped address error response
- Backpressure and ready/valid handshake behavior
- Zeroization after WIPE_SECRET
- Partial-block padding and multi-block message support

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map: Verify reset values, TL-UL read/write access to all implemented CSRs, reserved-bit read-as-zero behavior, and unmapped address error response.
- cfg_mode_matrix: Exercise CFG combinations for SHA-only, HMAC+SHA, and invalid hmac_en without sha_en; confirm legal mode acceptance and invalid configuration handling.
- cmd_w1s_semantics: Check that CMD bits are write-1-to-set and self-clearing, and that hash_start, hash_process, and hash_stop can be issued independently and in sequence.
- sha_single_block_known_vector: Run a bare SHA-256 known-answer test for a single-block message and compare digest register contents against a software reference model.
- sha_multi_block_streaming: Send a message in multiple FIFO chunks, trigger hash_process across block boundaries, and verify final digest matches the reference model.
- sha_partial_block_padding: Cover finalization with a partial block to validate automatic SHA-256 padding and message length encoding.
- hmac_known_vector: Program a known HMAC key and message, run full HMAC flow, and verify the final digest against a software HMAC-SHA256 reference.
- hmac_key_zeroization: After HMAC completion, write WIPE_SECRET and confirm key registers and secret-related state are cleared and remain cleared on subsequent reads.
- fifo_status_and_backpressure: Fill the 32-entry FIFO to full, observe STATUS fifo_full/fifo_empty/fifo_depth transitions, then drain and confirm correct recovery.
- endian_and_digest_swap: Toggle endian_swap and digest_swap independently and together, verifying message word ordering and digest byte ordering against the model.

## Random Tests
- tlul_csr_fuzz_smoke: Randomize legal TL-UL CSR reads/writes, including reserved-bit writes and repeated reads, to catch decode and side-effect issues within the 60-minute budget.
- streaming_message_fuzzer: Generate random message lengths, chunk sizes, and hash_start/hash_process/hash_stop sequences in SHA-only mode, checking digest equivalence to a Python reference model.
- hmac_streaming_fuzzer: Randomize keys, message lengths, and FIFO write patterns in HMAC mode to stress key expansion, inner/outer pass sequencing, and final digest correctness.
- status_transition_fuzzer: Randomly sample FIFO occupancy and command timing to validate STATUS field monotonicity and legal transitions under back-to-back operations.

## Risk Areas
- HMAC double-pass sequencing (high): The design performs an inner SHA pass followed by an automatic outer pass; sequencing bugs can silently corrupt digests and are high impact.
- Padding and partial-block finalization (high): Automatic SHA-256 padding and message length encoding are common sources of off-by-one and boundary errors, especially with streaming input.
- FIFO depth/full/empty accounting (high): The 32-entry message FIFO directly affects data acceptance and block formation; incorrect status or overflow handling can break all modes.
- CFG invalid mode combinations (medium): hmac_en without sha_en is explicitly invalid and may trigger undefined internal behavior if not handled defensively.
- W1S command self-clear behavior (medium): Edge-triggered command registers are prone to sticky-bit or missed-pulse bugs that are easy to miss without directed checks.
- Endian and digest byte swapping (medium): Byte-order transformations are integration-sensitive and can produce correct-looking but mismatched digests if implemented inconsistently.
- Secret wipe zeroization (high): Key register clearing and internal state reset are security-sensitive and should be verified even in a non-production competition RTL.
- TL-UL error response on unmapped access (low): Address decode and error signaling are basic bus compliance items that can block software bring-up if incorrect.
