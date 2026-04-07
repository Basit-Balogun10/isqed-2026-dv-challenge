# Verification Plan

## Features
- TL-UL CSR read/write access with byte-addressed 32-bit registers
- AES-128 ECB encrypt/decrypt functional path
- AES-128 CBC encrypt/decrypt functional path with IV handling
- 128-bit key programming via four consecutive CSR writes
- 128-bit data input programming via four consecutive CSR writes
- 128-bit data output readback via four consecutive CSR reads
- Start trigger sequencing and operation completion interrupt
- Status polling for output_valid and input_ready behavior
- Back-to-back block operation support
- Key/IV/data input clear behavior
- Data output clear behavior
- Reset behavior and CSR default state
- Alert output sanity and fatal-error observation
- TL-UL protocol compliance on basic legal transactions
- Register access permissions and address map sanity
- AES round-trip correctness against a software reference model

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- smoke_reset_and_csr_map: Verify reset deassertion, TL-UL connectivity, readable/writable CSR locations, WO/RW access behavior, and that reserved/undefined addresses do not crash the DUT.
- aes_ecb_encrypt_known_vector: Program a known AES-128 key and plaintext, start ECB encryption, and compare ciphertext against a software reference model.
- aes_ecb_decrypt_known_vector: Program a known AES-128 key and ciphertext, start ECB decryption, and compare recovered plaintext against the reference model.
- aes_cbc_encrypt_known_vector: Program key, IV, and plaintext for CBC encryption, verify ciphertext and IV update behavior against the reference model.
- aes_cbc_decrypt_known_vector: Program key, IV, and ciphertext for CBC decryption, verify plaintext recovery and IV update behavior against the reference model.
- back_to_back_block_processing: Issue consecutive start triggers with new input data and confirm the DUT accepts the next block when input_ready indicates availability, preserving output ordering.
- clear_controls_behavior: Exercise key_iv_data_in_clear and data_out_clear separately, confirming registers are zeroized and that clear operations do not corrupt unrelated control/status state.
- interrupt_completion_flow: Verify intr_o asserts on operation completion and that status/output readback can be used to clear or acknowledge the completed transaction in the expected software flow.

## Random Tests
- tlul_csr_fuzz_legal_ops: Run constrained-random TL-UL reads and writes over valid CSR addresses, checking protocol stability, access permissions, and no unexpected alerting on legal traffic.
- aes_mode_op_randomized: Randomize mode, encrypt/decrypt selection, key, IV, and data blocks across ECB/CBC operations and compare results to a Python AES reference model.
- multi_block_cbc_stream: Generate short random CBC sequences of 2 to 4 blocks to stress IV chaining, output overwrite timing, and back-to-back operation handling.
- reset_interruption_stress: Assert reset during idle and during active operation at random times to confirm safe recovery, CSR reinitialization, and no stuck interrupt or alert conditions.

## Risk Areas
- AES algorithm correctness (high): Primary functional risk because the DUT implements a full AES-128 datapath with multiple rounds and key expansion; a single transformation bug breaks all crypto results.
- CBC IV chaining and update semantics (high): CBC introduces stateful behavior across blocks; incorrect IV update or first-block handling will only appear in multi-block scenarios.
- Back-to-back operation sequencing (high): Throughput-oriented control flow can expose race conditions between input_ready, start trigger, and output overwrite behavior.
- CSR access permissions and packing (medium): 128-bit values are split across four 32-bit registers and include WO/RW distinctions; address or ordering mistakes are common integration bugs.
- Clear-trigger side effects (medium): The spec notes undefined interaction when clear and start are asserted together, so separate clear-path validation is important while avoiding ambiguous combinations.
- Interrupt and status signaling (medium): Software flow depends on intr_o, output_valid, and input_ready; mismatches can make the block appear hung even if datapath is correct.
- Alert output behavior (low): Alert is likely tied to fatal internal conditions, but with limited time it should be sanity-checked rather than exhaustively fault-injected.
