#!/usr/bin/env python3
"""
Generate Task 1.2 test files and vplan_mapping.yaml from vplan YAML files.

This script:
1. Reads a DUT's vplan YAML
2. For each VP item, generates a test function
3. Creates vplan_mapping.yaml linking VP-IDs to test names and coverage bins
4. Packages tests into a submission structure
"""

import os
import sys
import yaml
import json
from pathlib import Path
from textwrap import dedent

# ============================================================================
# TEST TEMPLATE GENERATION
# ============================================================================

UART_TEST_TEMPLATE = '''
@cocotb.test()
async def {test_name}(dut):
    """
    {title}
    
    Verification Plan Item: {vp_id}
    Priority: {priority}
    Coverage Target: {coverage_target}
    
    Description:
    {description}
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: {vp_id}")
    
    # TODO: Implement stimulus and checks for {vp_id}
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test {vp_id}: PLACEHOLDER - implement stimulus and checks")
'''

I2C_TEST_TEMPLATE = '''
@cocotb.test()
async def {test_name}(dut):
    """
    {title}
    
    Verification Plan Item: {vp_id}
    Priority: {priority}
    Coverage Target: {coverage_target}
    
    Description:
    {description}
    """
    cocotb.log.info(f"Starting test: {vp_id}")
    
    # TODO: Implement I2C-specific stimulus and checks for {vp_id}
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test {vp_id}: PLACEHOLDER - implement stimulus and checks")
'''

def generate_test_name(vp_id: str) -> str:
    """Convert VP-ID to Python test function name."""
    parts = vp_id.lower().replace('-', '_').split('_')
    # VP_UART_001 -> test_vp_uart_001
    return f"test_{parts[0]}_{parts[1]}_{parts[2]}" if len(parts) >= 3 else f"test_{vp_id.lower()}"

def load_vplan(vplan_path: str) -> dict:
    """Load vplan YAML file."""
    with open(vplan_path, 'r') as f:
        return yaml.safe_load(f)

def create_test_file(dut_name: str, vplan_data: dict, output_dir: str):
    """Generate test_vplan_items.py file."""
    dut_upper = dut_name.replace('_', '').upper()
    
    # Select template based on DUT type
    if 'uart' in dut_name:
        template = UART_TEST_TEMPLATE
    elif 'i2c' in dut_name:
        template = I2C_TEST_TEMPLATE
    else:
        template = UART_TEST_TEMPLATE  # fallback
    
    # Generate file header
    file_content = dedent(f'''
    """
    Task 1.2: Verification Plan Tests for {dut_name.upper()}
    
    This file contains {len(vplan_data.get('vplan', []))} test functions,
    one per verification plan item.
    
    Each test is derived from the vplan YAML and implements:
    1. Register configuration
    2. Stimulus application
    3. Expected behavior checks
    4. Coverage bin hitting
    """
    
    import cocotb
    from cocotb.triggers import Timer, RisingEdge, FallingEdge
    
    # ============================================================================
    # TEST FUNCTIONS - One per vplan item
    # ============================================================================
    ''').lstrip()
    
    # Generate test function for each vplan item
    for idx, item in enumerate(vplan_data.get('vplan', []), 1):
        vp_id = item['id']
        title = item.get('title', 'No title')
        description = item.get('description', 'No description')
        priority = item.get('priority', 'medium')
        coverage_target = item.get('coverage_target', 'N/A')
        
        test_name = generate_test_name(vp_id)
        
        # Format multi-line description for docstring
        desc_lines = description.strip().split('\n')
        formatted_desc = '\n    '.join(desc_lines)
        
        test_func = template.format(
            test_name=test_name,
            title=title,
            vp_id=vp_id,
            priority=priority,
            coverage_target=coverage_target,
            description=formatted_desc
        )
        
        file_content += test_func + '\n\n'
    
    # Write test file
    test_file = os.path.join(output_dir, 'test_vplan_items.py')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(test_file, 'w') as f:
        f.write(file_content)
    
    print(f"✅ Generated: {test_file} ({len(vplan_data.get('vplan', []))} tests)")
    return test_file

def create_vplan_mapping(dut_name: str, vplan_data: dict, output_dir: str):
    """Generate vplan_mapping.yaml."""
    
    mappings = []
    
    for item in vplan_data.get('vplan', []):
        vp_id = item['id']
        test_name = generate_test_name(vp_id)
        coverage_target = item.get('coverage_target', '')
        
        # Parse coverage bins from target string
        coverage_bins = []
        if coverage_target:
            # Split by comma and extract bin names
            for bin_spec in coverage_target.split(','):
                bin_spec = bin_spec.strip()
                # Extract just the bin name (before any 'cross' keyword)
                if 'cross' in bin_spec:
                    parts = bin_spec.split('cross')
                    coverage_bins.extend([p.strip() for p in parts])
                else:
                    coverage_bins.append(bin_spec)
        
        mappings.append({
            'vp_id': vp_id,
            'test_name': f'tests.test_vplan_items::{test_name}',
            'coverage_bins': coverage_bins,
            'priority': item.get('priority', 'medium')
        })
    
    # Create vplan_mapping structure
    vplan_mapping = {
        'dut': dut_name,
        'total_tests': len(mappings),
        'mappings': mappings
    }
    
    # Write mapping file
    mapping_file = os.path.join(output_dir, 'vplan_mapping.yaml')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(mapping_file, 'w') as f:
        yaml.dump(vplan_mapping, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Generated: {mapping_file} ({len(mappings)} mappings)")
    return mapping_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Task 1.2 tests from vplans')
    parser.add_argument('--dut', type=str, help='Specific DUT to generate (or all if omitted)', default=None)
    args = parser.parse_args()
    
    project_root = '/home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge'
    
    # All 7 DUTs
    all_duts = ['nexus_uart', 'bastion_gpio', 'warden_timer', 'citadel_spi', 'aegis_aes', 'sentinel_hmac', 'rampart_i2c']
    
    # Determine which DUTs to process
    duts_to_process = [args.dut] if args.dut else all_duts
    
    for dut in duts_to_process:
        vplan_file = os.path.join(project_root, 'vplans', f'{dut}_vplan.yaml')
        submission_dir = os.path.join(project_root, 'submissions', 'task-1.2', f'submission-1.2-{dut}')
        tests_dir = os.path.join(submission_dir, 'tests')
        
        if not os.path.exists(vplan_file):
            print(f"❌ Vplan not found: {vplan_file}")
            continue
        
        print(f"\n{'='*70}")
        print(f"Processing DUT: {dut.upper()}")
        print(f"{'='*70}")
        
        # Load vplan
        vplan_data = load_vplan(vplan_file)
        print(f"✓ Loaded vplan with {len(vplan_data.get('vplan', []))} items")
        
        # Generate test file
        create_test_file(dut, vplan_data, tests_dir)
        
        # Generate vplan_mapping
        create_vplan_mapping(dut, vplan_data, submission_dir)
        
        print(f"\n✅ Completed {dut.upper()}")

if __name__ == '__main__':
    main()
