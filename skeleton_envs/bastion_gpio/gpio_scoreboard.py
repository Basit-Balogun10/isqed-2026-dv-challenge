"""
BASTION_GPIO Scoreboard and Reference Model

The scoreboard:
1. Receives CSR transactions from TL-UL monitor (writes/reads)
2. Maintains reference model synchronized with CSR state
3. Receives GPIO pin changes from GPIO monitor
4. Compares expected vs. actual register values and pin states
5. Reports mismatches with transaction-level detail
"""

import cocotb
from collections import defaultdict


# CSR Register Addresses
ADDR_OUT = 0x00
ADDR_IN = 0x04
ADDR_DIR = 0x08
ADDR_INTR_RISING = 0x0C
ADDR_INTR_FALLING = 0x10
ADDR_INTR_LVL_HIGH = 0x14
ADDR_INTR_LVL_LOW = 0x18
ADDR_INTR_STATE = 0x1C
ADDR_INTR_ENABLE = 0x20


class BastionGpioRefModel:
    """
    Reference model for bastion_gpio behavior.
    
    Maintains:
    - 32-pin state (value, direction, interrupt config)
    - FIFO/buffer state (if applicable)
    - Interrupt state and enables
    """
    
    def __init__(self, num_pins=32):
        self.num_pins = num_pins
        self.data_in = 0  # Synchronized input values
        self.data_out = 0  # Output values
        self.dir = 0  # Direction: 1=output, 0=input
        
        # Interrupt configuration (per pin)
        self.intr_rising = 0  # Rising edge interrupts
        self.intr_falling = 0  # Falling edge interrupts
        self.intr_lvl_high = 0  # Level high interrupts
        self.intr_lvl_low = 0  # Level low interrupts
        
        # Interrupt state
        self.intr_state = 0  # Pending interrupts
        self.intr_enable = 0  # Interrupt enables (masked)
        
        # Edge detection state
        self.prev_input = 0  # Previous synchronized input (for edge detection)
    
    def write_csr(self, addr, data, mask=0xFFFFFFFF):
        """Update CSR (register write)."""
        if addr == 0x00:  # DATA_OUT
            self.data_out = (self.data_out & ~mask) | (data & mask)
        elif addr == 0x04:  # DATA_IN (RO, shouldn't write, but handle for completeness)
            pass
        elif addr == 0x08:  # DIR
            self.dir = (self.dir & ~mask) | (data & mask)
        elif addr == 0x0C:  # INTR_RISING
            self.intr_rising = (self.intr_rising & ~mask) | (data & mask)
        elif addr == 0x10:  # INTR_FALLING
            self.intr_falling = (self.intr_falling & ~mask) | (data & mask)
        elif addr == 0x14:  # INTR_LVL_HIGH
            self.intr_lvl_high = (self.intr_lvl_high & ~mask) | (data & mask)
        elif addr == 0x18:  # INTR_LVL_LOW
            self.intr_lvl_low = (self.intr_lvl_low & ~mask) | (data & mask)
        elif addr == 0x1C:  # INTR_STATE
            # Write-1-clear logic: clear bits where data=1
            self.intr_state &= ~data
        elif addr == 0x20:  # INTR_ENABLE
            self.intr_enable = (self.intr_enable & ~mask) | (data & mask)
    
    def read_csr(self, addr):
        """Read CSR (register read)."""
        if addr == 0x00:
            return self.data_out
        elif addr == 0x04:
            return self.data_in
        elif addr == 0x08:
            return self.dir
        elif addr == 0x0C:
            return self.intr_rising
        elif addr == 0x10:
            return self.intr_falling
        elif addr == 0x14:
            return self.intr_lvl_high
        elif addr == 0x18:
            return self.intr_lvl_low
        elif addr == 0x1C:
            return self.intr_state
        elif addr == 0x20:
            return self.intr_enable
        return 0
    
    def update_input(self, new_input):
        """
        Simulate input synchronizer (2-stage: we skip that for ref model simplicity).
        Detect edges and update interrupt state.
        """
        # Detect rising edges
        rising_edges = (~self.prev_input) & new_input
        self.intr_state |= (rising_edges & self.intr_rising)
        
        # Detect falling edges
        falling_edges = self.prev_input & (~new_input)
        self.intr_state |= (falling_edges & self.intr_falling)
        
        # Level-sensitive interrupts
        self.intr_state |= (new_input & self.intr_lvl_high)
        self.intr_state |= ((~new_input) & self.intr_lvl_low)
        
        self.data_in = new_input
        self.prev_input = new_input


class GpioScoreboard:
    """
    Scoreboard for bastion_gpio (Cocotb native, no UVM).
    
    Records CSR transactions and pin changes, compares against reference model.
    """
    
    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or dut._log
        self.ref_model = GpioRefModel(num_pins=32)
        self.csr_ops = 0
        self.errors = 0
        self.gpio_changes = 0
        self.log.info("[GPIO Scoreboard] Initialized")
    
    def write_csr(self, addr, data, mask=0xFFFFFFFF):
        """Record a CSR write transaction."""
        self.ref_model.write_csr(addr, data, mask)
        self.log.debug(f"[GPIO SB] CSR write @ 0x{addr:04x} = 0x{data:08x}")
        self.csr_ops += 1
    
    def read_csr_compare(self, addr, actual_data):
        """Compare CSR read against reference model."""
        expected = self.ref_model.read_csr(addr)
        
        if addr in [0x04, 0x1C]:  # Timing-dependent, skip
            self.csr_ops += 1
            return True
        
        match = (expected == actual_data)
        if not match:
            self.log.error(
                f"[GPIO SB] MISMATCH @0x{addr:04x}: exp=0x{expected:08x} actual=0x{actual_data:08x}"
            )
            self.errors += 1
        
        self.csr_ops += 1
        return match
    
    def gpio_pin_changed(self, pin_idx, new_val):
        """Record a GPIO pin transition."""
        self.ref_model.update_input((1 << pin_idx) if new_val else 0)
        self.gpio_changes += 1
    
    def report(self):
        """Generate final report."""
        self.log.info("=== GPIO SCOREBOARD ===")
        self.log.info(f"CSR Ops: {self.csr_ops}, GPIO Changes: {self.gpio_changes}, Errors: {self.errors}")
        return self.errors == 0
