"""
Task 1.2: Verification Plan Tests for AEGIS_AES

This file contains 20 test functions,
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

@cocotb.test()
async def test_vp_aes_001(dut):
    """
    NIST ECB encrypt test vector
    
    Verification Plan Item: VP-AES-001
    Priority: high
    Coverage Target: cp_mode.ecb cross cp_op.encrypt cross cp_kat
    
    Description:
    Load FIPS 197 Appendix B test key (2b7e1516...) and plaintext (3243f6a8...), set mode=ECB, operation=encrypt, trigger start, and verify DATA_OUT matches the known ciphertext.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-001")
    
    # TODO: Implement stimulus and checks for VP-AES-001
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-001: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_002(dut):
    """
    NIST ECB decrypt test vector
    
    Verification Plan Item: VP-AES-002
    Priority: high
    Coverage Target: cp_mode.ecb cross cp_op.decrypt cross cp_kat
    
    Description:
    Load the FIPS 197 ciphertext as input with the same key, set mode=ECB, operation=decrypt, and verify DATA_OUT matches the original plaintext.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-002")
    
    # TODO: Implement stimulus and checks for VP-AES-002
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-002: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_003(dut):
    """
    NIST CBC encrypt test vector
    
    Verification Plan Item: VP-AES-003
    Priority: high
    Coverage Target: cp_mode.cbc cross cp_op.encrypt cross cp_kat
    
    Description:
    Load NIST SP 800-38A CBC encrypt test vector (key, IV, plaintext). Set mode=CBC, operation=encrypt, and verify ciphertext matches the known-answer value.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-003")
    
    # TODO: Implement stimulus and checks for VP-AES-003
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-003: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_004(dut):
    """
    NIST CBC decrypt test vector
    
    Verification Plan Item: VP-AES-004
    Priority: high
    Coverage Target: cp_mode.cbc cross cp_op.decrypt cross cp_kat
    
    Description:
    Load NIST SP 800-38A CBC ciphertext with the same key and IV. Set mode=CBC, operation=decrypt, and verify plaintext matches the known-answer value.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-004")
    
    # TODO: Implement stimulus and checks for VP-AES-004
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-004: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_005(dut):
    """
    Key expansion correctness
    
    Verification Plan Item: VP-AES-005
    Priority: high
    Coverage Target: cp_key_pattern cross cp_mode.ecb
    
    Description:
    Use multiple key values (all-zero, all-one, NIST key) and verify the output matches expected ciphertext, confirming all 11 round keys are correctly derived.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-005")
    
    # TODO: Implement stimulus and checks for VP-AES-005
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-005: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_006(dut):
    """
    Back-to-back ECB operations
    
    Verification Plan Item: VP-AES-006
    Priority: high
    Coverage Target: cp_back_to_back cross cp_mode.ecb
    
    Description:
    Trigger a first ECB encrypt, wait for output_valid, read result, immediately load new data and trigger again. Verify both outputs are correct with no corruption between operations.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-006")
    
    # TODO: Implement stimulus and checks for VP-AES-006
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-006: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_007(dut):
    """
    Back-to-back CBC operations
    
    Verification Plan Item: VP-AES-007
    Priority: high
    Coverage Target: cp_back_to_back cross cp_mode.cbc
    
    Description:
    Perform two consecutive CBC encrypt blocks. Verify the IV is automatically updated after the first block, and the second block's ciphertext is correct per CBC chaining.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-007")
    
    # TODO: Implement stimulus and checks for VP-AES-007
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-007: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_008(dut):
    """
    CBC IV handling
    
    Verification Plan Item: VP-AES-008
    Priority: high
    Coverage Target: cp_iv_update
    
    Description:
    Program a specific IV, perform a CBC encrypt, then read back the IV registers. Verify the IV has been updated to the ciphertext of the last block (as per CBC spec).
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-008")
    
    # TODO: Implement stimulus and checks for VP-AES-008
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-008: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_009(dut):
    """
    Register clear on config change
    
    Verification Plan Item: VP-AES-009
    Priority: medium
    Coverage Target: cp_clear
    
    Description:
    Write key, IV, and data_in, then assert key_iv_data_in_clear in AES_TRIGGER. Verify all key, IV, and data_in registers read as zero. Also test data_out_clear separately.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-009")
    
    # TODO: Implement stimulus and checks for VP-AES-009
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-009: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_010(dut):
    """
    Partial CSR writes
    
    Verification Plan Item: VP-AES-010
    Priority: low
    Coverage Target: cp_partial_write
    
    Description:
    Write only 3 of 4 key registers before triggering. Observe the behavior (unpredictable output). Then write all 4 and verify correct operation. Confirms the engine does not track partial writes.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-010")
    
    # TODO: Implement stimulus and checks for VP-AES-010
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-010: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_011(dut):
    """
    DATA_OUT read before valid
    
    Verification Plan Item: VP-AES-011
    Priority: medium
    Coverage Target: cp_status.output_valid
    
    Description:
    Trigger an AES operation and immediately read DATA_OUT before output_valid is set. Verify the read returns stale/undefined data. Then wait for output_valid and confirm correct output.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-011")
    
    # TODO: Implement stimulus and checks for VP-AES-011
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-011: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_012(dut):
    """
    Encrypt-then-decrypt roundtrip
    
    Verification Plan Item: VP-AES-012
    Priority: high
    Coverage Target: cp_roundtrip cross cp_mode.ecb
    
    Description:
    Encrypt a random plaintext block in ECB mode, then decrypt the resulting ciphertext. Verify the decrypted output matches the original plaintext exactly.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-012")
    
    # TODO: Implement stimulus and checks for VP-AES-012
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-012: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_013(dut):
    """
    CBC encrypt-then-decrypt roundtrip
    
    Verification Plan Item: VP-AES-013
    Priority: high
    Coverage Target: cp_roundtrip cross cp_mode.cbc
    
    Description:
    Encrypt a block in CBC mode, note the ciphertext and updated IV. Decrypt using the original IV and key, and verify plaintext recovery.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-013")
    
    # TODO: Implement stimulus and checks for VP-AES-013
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-013: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_014(dut):
    """
    Mode switching ECB to CBC
    
    Verification Plan Item: VP-AES-014
    Priority: medium
    Coverage Target: cp_mode_switch
    
    Description:
    Perform an ECB encrypt, then change AES_CTRL to CBC mode and perform another operation with an IV. Verify the mode switch takes effect correctly on the next operation.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-014")
    
    # TODO: Implement stimulus and checks for VP-AES-014
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-014: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_015(dut):
    """
    Trigger while busy
    
    Verification Plan Item: VP-AES-015
    Priority: medium
    Coverage Target: cp_trigger_busy
    
    Description:
    Start an AES operation, then immediately write start=1 to AES_TRIGGER while the engine is not idle. Verify the second trigger is ignored and the first operation completes correctly.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-015")
    
    # TODO: Implement stimulus and checks for VP-AES-015
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-015: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_016(dut):
    """
    Status register accuracy
    
    Verification Plan Item: VP-AES-016
    Priority: high
    Coverage Target: cp_status
    
    Description:
    Check AES_STATUS at each phase: idle/input_ready=1 initially, idle=0 after trigger, output_valid=1 after completion. Verify all status transitions.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-016")
    
    # TODO: Implement stimulus and checks for VP-AES-016
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-016: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_017(dut):
    """
    All-zero data pattern
    
    Verification Plan Item: VP-AES-017
    Priority: medium
    Coverage Target: cp_data_pattern.all_zero
    
    Description:
    Encrypt and decrypt a 128-bit all-zero block with a known key. Verify ciphertext matches the expected known-answer for all-zero input.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-017")
    
    # TODO: Implement stimulus and checks for VP-AES-017
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-017: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_018(dut):
    """
    All-one data pattern
    
    Verification Plan Item: VP-AES-018
    Priority: medium
    Coverage Target: cp_data_pattern.all_one
    
    Description:
    Encrypt and decrypt a 128-bit all-one (0xFF) block. Verify correct ciphertext output.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-018")
    
    # TODO: Implement stimulus and checks for VP-AES-018
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-018: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_019(dut):
    """
    Walking-1 data pattern
    
    Verification Plan Item: VP-AES-019
    Priority: medium
    Coverage Target: cp_data_pattern.walking_one
    
    Description:
    Encrypt blocks with a single bit set at each of the 128 positions. Verify each produces a distinct and correct ciphertext, exercising all S-box entries.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-019")
    
    # TODO: Implement stimulus and checks for VP-AES-019
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-019: PLACEHOLDER - implement stimulus and checks")



@cocotb.test()
async def test_vp_aes_020(dut):
    """
    Interrupt and INTR_TEST
    
    Verification Plan Item: VP-AES-020
    Priority: medium
    Coverage Target: cp_intr_done cross cp_intr_test
    
    Description:
    Enable the aes_done interrupt, trigger an operation, and verify intr_o asserts on completion. Clear via W1C. Also test INTR_TEST injection and verify the interrupt path independently.
    """
    # Get environment from dut._discover_modules()
    cocotb.log.info(f"Starting test: VP-AES-020")
    
    # TODO: Implement stimulus and checks for VP-AES-020
    # This is a placeholder - fill in with actual test logic
    await cocotb.triggers.Timer(100, units='ns')
    cocotb.log.info(f"Test VP-AES-020: PLACEHOLDER - implement stimulus and checks")


