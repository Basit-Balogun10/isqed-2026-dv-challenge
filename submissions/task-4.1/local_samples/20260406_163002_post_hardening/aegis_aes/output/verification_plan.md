# Verification Plan

## Features
- TL-UL CSR read/write access with byte-addressed 32-bit registers
- AES-128 ECB and CBC mode control via CSRs
- AES encrypt and decrypt operation sequencing
- 128-bit key programming across four 32-bit writes
- 128-bit IV programming across four 32-bit writes
- 128-bit data input programming across four 32-bit writes
- 128-bit data output readback across four 32-bit reads
- Start trigger handling and operation completion interrupt
- Status polling for output_valid and input_ready behavior
- Back-to-back block operation support
- Key/IV/data input clear behavior
- Data output clear behavior
- Reset behavior and CSR default state
- CBC IV update across multi-block sequences
- TL-UL protocol compliance under ready/valid handshakes
- Alert output observation for fatal error conditions

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_sanity: Apply reset, verify TL-UL accessibility, confirm CSR defaults, and check that status/interrupt/alert outputs are quiescent after reset.
- ecb_encrypt_known_vector: Program a known AES-128 key and plaintext in ECB mode, trigger encryption, poll for completion, and compare ciphertext against a golden reference.
- ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext in ECB mode, trigger decryption, and verify recovered plaintext matches the golden reference.
- cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, trigger operation, and verify ciphertext plus IV update behavior against a golden model.
- cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, trigger operation, and verify plaintext plus IV update behavior against a golden model.
- back_to_back_ecb_blocks: Issue consecutive ECB start triggers with new input data as soon as input_ready allows, verifying output retention, throughput behavior, and no data corruption between blocks.
- clear_trigger_behavior: Exercise key_iv_data_in_clear and data_out_clear separately, confirming that programmed registers are zeroized and that output clearing does not disturb unrelated control state.
- interrupt_completion_flow: Enable interrupt generation if supported by CSR map, start an operation, and verify intr_o asserts on completion and deasserts according to expected acknowledge/clear behavior.

## Random Tests
- tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads and writes over the discovered CSR space, checking protocol stability, legal access behavior, and absence of bus hangs within the time budget.
- mode_operation_random_matrix: Randomize ECB/CBC, encrypt/decrypt, key/data values, and start timing across a small set of transactions, comparing results to a software AES reference model.
- back_to_back_random_stream: Generate a short stream of random blocks with randomized inter-block gaps to stress input_ready, DONE-to-IDLE transitions, and output overwrite hazards.
- reset_during_idle_and_busy: Assert reset at random points during idle and active operation to validate safe recovery, CSR reinitialization, and no stuck interrupt or alert conditions.

## Risk Areas
- AES algorithm correctness in ECB/CBC encrypt and decrypt paths (high): Core functionality is the highest-value risk; any mismatch against FIPS-197 behavior breaks the block cipher engine.
- Key expansion and round-key reuse (high): Implementation-dependent key schedule timing and caching can introduce subtle state bugs across consecutive operations.
- CBC IV handling and multi-block chaining (high): IV update semantics are easy to implement incorrectly and directly affect chained ciphertext/plaintext correctness.
- Back-to-back operation sequencing (high): DONE/input_ready transitions and output overwrite behavior are explicitly supported and likely to expose FSM timing issues.
- TL-UL CSR access ordering and partial 128-bit register assembly (medium): The design relies on four-word programming for key, IV, and data; word ordering or write acceptance bugs are common integration failures.
- Trigger bit interactions with clear operations (medium): The spec notes undefined behavior when start and clear are asserted together, so the implementation may have corner-case hazards.
- Interrupt and alert signaling (medium): Completion interrupt and fatal alert outputs are externally visible and must not glitch or remain stuck.
- Reset recovery and quiescent state (medium): Asynchronous reset can expose FSM and CSR initialization issues, especially with active bus traffic.
- Low-probability TL-UL protocol corner cases (low): Within a 60-minute autonomous budget, exhaustive bus stress is not feasible, so only a bounded smoke/fuzz pass is practical.
