# Key Prompt 1: Test Generation Overview

## Prompt (to Copilot)

```
I have a YAML verification plan for nexus_uart (UART controller) with 20 test scenarios. 
Each scenario describes:
- VP-ID (test identifier)
- title (short name)
- description (detailed test requirement)
- priority (high/medium/low)
- coverage_target (specific coverage bins to hit)

I need to:
1. Generate one @cocotb.test() function for each VP item
2. Create vplan_mapping.yaml that links VP-ID → test_name → coverage_bins
3. Each test must use the exact coverage bins from the vplan
4. All tests must have docstrings referencing their VP-ID
5. All tests must pass on clean RTL

How should I structure the test generation to ensure traceability and coverage correctness?
```

## Response (Copilot)

```
For Task 1.2, the key insight is establishing 1:1 traceability between:
- vplan.yaml entries (verification intent)
- test function in code (implementation)
- vplan_mapping.yaml (linkage)

Structure:
1. Parse YAML vplan → extract VP-ID, description, coverage_target
2. For each vplan item:
   - Generate test_vp_NNN_slug() function
   - Add @cocotb.test() decorator
   - Write docstring with VP-ID from vplan
   - Parse coverage_target string → extract bins
3. Create vplan_mapping.yaml with:
   - vp_id: exact copy from YAML
   - test_name: module::function name
   - coverage_bins: array extracted from coverage_target

This creates a machine-verifiable mapping the evaluator can check.
```
