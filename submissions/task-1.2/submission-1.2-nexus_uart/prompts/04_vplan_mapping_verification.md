# Key Prompt 4: Vplan Mapping Traceability

## Prompt (to Copilot)

```
For Task 1.2 submission evaluation, the platform will verify:
1. vplan_mapping.yaml is valid YAML
2. Every test_name in vplan_mapping.yaml refers to an actual @cocotb.test() function
3. Every test_name has matching @cocotb.test() with same name
4. Every coverage_bin in vplan_mapping was extracted from the original vplan
5. All tests run without failure on clean RTL

What format should vplan_mapping.yaml follow? And how should we verify this before submitting?
```

## Response (Copilot)

```yaml
# vplan_mapping.yaml - Correct format (per Task 1.2 requirements)

mappings:
  - vp_id: "VP-UART-001"                           # Exact copy from vplan.yaml
    test_name: "tests.test_vplan_items::test_vp_001_basic_tx"  # Must match function name
    coverage_bins: ["cp_tx_data", "cp_baud_div.mid"]  # Parsed from vplan coverage_target
    description: "Basic transmit at standard baud"

  - vp_id: "VP-UART-002"
    test_name: "tests.test_vplan_items::test_vp_002_basic_rx"
    coverage_bins: ["cp_rx_data", "cp_baud_div.mid"]
    description: "Basic receive at standard baud"
```

Verification checklist before submission:
1. Parse vplan_mapping.yaml → can PyYAML load it without error?
2. For each mapping, extract test_name and split on `::`
3. Search test_vplan_items.py for: @cocotb.test() followed by async def {function_name}
4. Count matches: should equal number of mappings
5. Count VP-IDs in vplan_mapping: should equal count in vplan.yaml
6. Run all tests: make SIM=icarus → TESTS=N PASS=N FAIL=0

This creates a machine-verifiable chain: vplan.yaml → vplan_mapping.yaml → test_vplan_items.py
```
