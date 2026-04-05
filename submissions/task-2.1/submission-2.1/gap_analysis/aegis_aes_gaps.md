# aegis_aes Coverage Gaps

## Coverage Snapshot

- Line coverage: 34.33%
- Branch coverage: 8.11%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-017 | duts/aegis_aes/aegis_aes.sv | 28-92 | A narrow plaintext/key corpus touches only a small subset of S-box indices, leaving most lookup arms unvisited. |
| GAP-018 | duts/aegis_aes/aegis_aes.sv | 96-162 | Decrypt-mode campaigns are minimal, so inverse S-box table arms remain broadly uncovered. |
| GAP-019 | duts/aegis_aes/aegis_aes.sv | 530-546 | Short test runs often terminate before full key schedule progression, missing later key-expansion case arms. |
| GAP-020 | duts/aegis_aes/aegis_aes.sv | 456-466 | Mode/op register permutations and IV update paths are under-tested, especially around CBC decrypt transitions. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-017 | vp_scenario_id | VP-AES-001, VP-AES-002, VP-AES-015 | Use coverage-directed plaintext/key generation to maximize S-box input diversity during encryption rounds. |
| GAP-018 | vp_scenario_id | VP-AES-003, VP-AES-004, VP-AES-016 | Expand CBC/ECB decrypt regressions with randomized ciphertext/key sets to drive inverse substitution diversity. |
| GAP-019 | vp_scenario_id | VP-AES-006, VP-AES-007, VP-AES-017 | Drive full key expansion through all round-key indices and validate generated keys against software model. |
| GAP-020 | vp_scenario_id | VP-AES-010, VP-AES-011, VP-AES-018 | Exercise mode/op/control permutations and verify IV updates for CBC encrypt/decrypt across consecutive blocks. |

## Root Cause And Intent

### GAP-017 - sbox_forward_lookup_space
- Root cause: A narrow plaintext/key corpus touches only a small subset of S-box indices, leaving most lookup arms unvisited.
- Test intent: Use coverage-directed plaintext/key generation to maximize S-box input diversity during encryption rounds.

### GAP-018 - sbox_inverse_lookup_space
- Root cause: Decrypt-mode campaigns are minimal, so inverse S-box table arms remain broadly uncovered.
- Test intent: Expand CBC/ECB decrypt regressions with randomized ciphertext/key sets to drive inverse substitution diversity.

### GAP-019 - key_expansion_roundkey_cases
- Root cause: Short test runs often terminate before full key schedule progression, missing later key-expansion case arms.
- Test intent: Drive full key expansion through all round-key indices and validate generated keys against software model.

### GAP-020 - cbc_iv_control_programming
- Root cause: Mode/op register permutations and IV update paths are under-tested, especially around CBC decrypt transitions.
- Test intent: Exercise mode/op/control permutations and verify IV updates for CBC encrypt/decrypt across consecutive blocks.
