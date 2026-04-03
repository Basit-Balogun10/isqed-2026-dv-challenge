# Key Prompt 2: Automated Vplan Parsing

## Prompt (to Copilot)

```
Write a Python script that:
1. Reads vplan YAML file (each entry has id, title, description, priority, coverage_target)
2. For each vplan item, generates a @cocotb.test() function template that:
   - Uses function name: test_vp_NNN_slug (where NNN is item index, slug is slugified title)
   - Includes docstring with the VP-ID from vplan
   - Has @cocotb.test() decorator
   - Includes skeleton: Clock setup, reset, Timer loop, logging
3. Also generates vplan_mapping.yaml with:
   - vp_id from vplan
   - test_name = tests.test_vplan_items::test_vp_NNN_slug
   - coverage_bins parsed from coverage_target string

Goal: 100% automation, zero manual edits needed for test file structure.
```

## Response (Copilot)

```python
# Key insight: Use YAML parsing + templating to ensure consistency
import yaml
from pathlib import Path

def generate_tests_for_dut(dut_name):
    vplan_file = Path(f"vplans/{dut_name}_vplan.yaml")
    with open(vplan_file) as f:
        vplan_data = yaml.safe_load(f)
    
    test_file_content = TEST_FILE_HEADER.format(dut_name=dut_name, total_tests=len(vplan_data["vplan"]))
    vplan_mapping = VPLAN_MAPPING_HEADER.format(dut_name=dut_name)
    
    for i, item in enumerate(vplan_data["vplan"]):
        vp_id = item.get("id")
        test_slug = slugify(item.get("title"))
        coverage_target = item.get("coverage_target", "")
        
        # Generate test
        test_func = TEMPLATE_TEST.format(
            test_id=f"{i+1:03d}",
            test_slug=test_slug,
            vp_id=vp_id,
            coverage_target=coverage_target
        )
        test_file_content += test_func
        
        # Generate mapping
        vplan_item = VPLAN_MAPPING_ITEM.format(
            vp_id=vp_id,
            test_name=f"test_vp_{i+1:03d}_{test_slug}",
            coverage_bins=extract_coverage_bins(coverage_target)
        )
        vplan_mapping += vplan_item

Comment: This approach ensures:
- Every vplan entry → exactly one test function
- No manual mapping errors
- Coverage bins extracted directly from source (vplan YAML)
- Filename matches test_name reference
```
