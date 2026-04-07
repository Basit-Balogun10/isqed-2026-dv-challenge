# Verification Plan

## Features
- TL-UL CSR read/write access with byte-addressed 32-bit registers
- AES-128 ECB encrypt/decrypt functional flow
- AES-128 CBC encrypt/decrypt functional flow with IV handling
- 128-bit key programming via four consecutive 32-bit writes
- 128-bit data input programming via four consecutive 32-bit writes
- 128-bit data output readback via four consecutive 32-bit reads
- start trigger sequencing and operation completion interrupt
- status polling for input_ready and output_valid
- back-to-back block operation support
- key/IV/data input clear behavior
- data output clear behavior
- reset behavior and CSR default state
- TL-UL protocol compliance on basic legal transactions
- alert output observation for fatal error conditions
- FSM state progression across IDLE, KEY_EXPAND, INIT_CBC, ROUND, DONE

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- smoke_reset_and_csr_sanity: Verify reset deassertion, TL-UL accessibility, readable/writable CSR map basics, and expected default values for status/control registers.
- aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, start ECB encryption, and compare output against a golden FIPS-197 vector.
- aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, start ECB decryption, and verify recovered plaintext matches the golden vector.
- aes_cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, start operation, and verify ciphertext and IV update behavior against a golden model.
- aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, start operation, and verify plaintext recovery and IV chaining behavior.
- back_to_back_block_sequence: Issue consecutive start triggers with new input data after input_ready, confirming output retention, throughput continuity, and no lost transactions.
- clear_key_iv_data_and_output: Exercise key_iv_data_in_clear and data_out_clear separately, confirming all targeted registers are zeroized and normal operation resumes afterward.
- interrupt_completion_and_status_polling: Verify intr_o assertion on operation completion and consistency between interrupt timing and status bits output_valid/input_ready.

## Random Tests
- tlul_csr_fuzz_legal_accesses: Randomize legal TL-UL read/write sequences across all implemented CSRs, including partial programming order variations, while checking protocol stability and CSR side effects.
- mode_operation_randomized_regression: Randomly vary ECB/CBC, encrypt/decrypt, key/data values, and start timing to validate functional correctness against a Python AES reference model.
- multi_block_cbc_chaining_random: Generate random multi-block CBC streams to stress IV update, chaining correctness, and back-to-back operation behavior.
- reset_interruption_random: Assert reset at random points during idle and active operation to confirm safe recovery, CSR reinitialization, and absence of stuck status or interrupt behavior.

## Risk Areas
- AES algorithm correctness in ECB/CBC encrypt/decrypt (high): Core functionality is the highest-value risk; any mismatch in round logic, key schedule, or inverse transforms breaks the DUT's primary purpose.
- CBC IV update and chaining semantics (high): CBC introduces stateful behavior across blocks and is prone to off-by-one or update-order bugs, especially for multi-block sequences.
- Back-to-back operation handling (high): The FSM includes DONE-to-new-operation behavior and input_ready gating, which are common sources of race conditions and dropped transactions.
- Trigger sequencing and clear-bit interaction (medium): The spec notes undefined behavior when start and clear are asserted together, so the implementation may have corner-case hazards around trigger decoding.
- TL-UL register access integrity (medium): The block is bus-attached and must correctly handle 32-bit CSR accesses, ordering of 128-bit word writes, and readback consistency.
- Interrupt and status timing (medium): Completion signaling must align with output_valid and software polling expectations; timing bugs can cause software-visible deadlocks.
- Reset and zeroization behavior (medium): Security-related clear paths and reset behavior must reliably scrub sensitive state without corrupting normal operation.
- Alert output behavior (low): Alert functionality is likely low-frequency but important to observe for fatal error paths; limited time suggests basic observability only.
