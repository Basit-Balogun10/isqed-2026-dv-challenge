# Verification Plan

## Features
- TL-UL CSR access compliance for 32-bit register reads/writes
- AES-128 ECB encrypt/decrypt functional flow
- AES-128 CBC encrypt/decrypt functional flow with IV handling
- 128-bit key programming across four consecutive CSR writes
- 128-bit data input/output programming across four consecutive CSR accesses
- Interrupt generation on operation completion
- Status polling for output_valid and input_ready behavior
- Back-to-back block operation sequencing
- Key/IV/data clear behavior via trigger bits
- Reset behavior and CSR default state
- Register field packing and little-endian word ordering
- TL-UL ready/response handshake stability under backpressure
- Alert output observation for fatal error conditions
- FSM state progression across IDLE, KEY_EXPAND, INIT_CBC, ROUND, and DONE

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_sanity: Verify reset deassertion, TL-UL accessibility, readable/writable CSR defaults, and that status/control registers respond without protocol errors.
- aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, trigger ECB encryption, and compare ciphertext against a golden model.
- aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, trigger ECB decryption, and compare recovered plaintext against a golden model.
- aes_cbc_encrypt_known_vector: Program key, IV, and plaintext, trigger CBC encryption, and verify ciphertext plus IV update behavior against a golden model.
- aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext, trigger CBC decryption, and verify plaintext recovery and IV update behavior.
- back_to_back_block_operations: Issue consecutive start triggers with new input data and confirm the DUT accepts the next block when input_ready indicates availability.
- clear_triggers: Exercise key_iv_data_in_clear and data_out_clear independently and confirm registers are zeroized without corrupting unrelated control/status behavior.
- interrupt_completion_flow: Enable/observe completion interrupt behavior and confirm intr_o asserts on done and deasserts according to the design's completion semantics.
- tlul_backpressure_and_wait_states: Apply host-side ready deassertion and randomized TL-UL request spacing to verify stable request/response handling under backpressure.

## Random Tests
- csr_fuzz_smoke: Randomize legal CSR writes and reads across key, IV, data, control, trigger, and status registers while checking TL-UL protocol correctness and basic register coherency.
- mode_operation_randomized: Randomly select ECB/CBC and encrypt/decrypt operations with constrained legal sequences, then compare outputs to a Python AES reference model.
- multi_block_stream_randomized: Generate short random block streams to stress back-to-back operation handling, output retention, and IV chaining in CBC mode.
- reset_interruption_randomized: Assert reset at random points during idle and active operation to verify safe recovery, no protocol deadlock, and clean post-reset CSR state.

## Risk Areas
- AES algorithm correctness (high): Core functionality depends on correct key expansion, round transformations, and inverse cipher behavior; a single mismatch breaks all cryptographic outputs.
- CBC IV chaining and update semantics (high): CBC mode adds stateful dependency across blocks and is prone to off-by-one or ordering bugs in IV capture/update.
- Back-to-back operation sequencing (high): FSM transitions and input_ready/output_valid timing are likely to expose race conditions or stale data reuse.
- TL-UL CSR access integrity (high): Incorrect register addressing, byte ordering, or handshake behavior can block all software interaction and is fast to validate early.
- Trigger clear interactions (medium): Simultaneous clear/start behavior is explicitly underdefined and may reveal implementation-specific hazards or unintended side effects.
- Interrupt and alert signaling (medium): Completion interrupt and fatal alert outputs are externally visible integration points that may be miswired or incorrectly timed.
- Reset recovery (medium): Asynchronous reset during active processing can expose state retention bugs, though it is typically less complex than algorithmic correctness.
- Non-functional throughput/pipelining assumptions (low): The design claims back-to-back support, but exact latency is implementation-dependent; verify only observable readiness and completion behavior within the time budget.
