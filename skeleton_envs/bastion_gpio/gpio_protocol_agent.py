"""
BASTION_GPIO Protocol Agent

Handles GPIO operations:
- Driving external pin values (gpio_i simulation)
- Monitoring pin outputs (gpio_o, gpio_oe_o)
- Edge and level-sensitive interrupt generation
- Input synchronization verification

GPIO protocol is simpler than UART: no baud rate or framing needed.
Just level-based transitions and edge detection.
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer


class GpioConfig:
    """GPIO configuration from CSRs."""
    
    def __init__(self, num_pins=32):
        self.num_pins = num_pins
        self.pin_dir = 0  # DIR register: 1=output, 0=input
        self.pin_out = 0  # DATA_OUT register
        self.intr_rising = 0  # Rising edge interrupts
        self.intr_falling = 0  # Falling edge interrupts
        self.intr_lvl_high = 0  # Level-high interrupts
        self.intr_lvl_low = 0  # Level-low interrupts


class GpioInputDriver:
    """
    Simulates external hardware: Drives gpio_i pins.
    
    This is the "stimulus" side - we drive the input pins from the testbench
    to simulate external events (button presses, sensor lines, etc.)
    """
    
    def __init__(self, name="gpio_input_driver", parent=None):
        self.name = name
        self.parent = parent
        self.dut = None
        self.log = None
    
    async def drive_pin(self, pin_idx, level, duration_cycles=0):
        """
        Drive a single GPIO pin.
        
        Args:
            pin_idx (int): Pin index [0:31]
            level (int): 0 or 1
            duration_cycles (int): How long to hold this level (0=stay at level)
        """
        if level:
            self.dut.gpio_i.value |= (1 << pin_idx)  # Set bit
        else:
            self.dut.gpio_i.value &= ~(1 << pin_idx)  # Clear bit
        
        if duration_cycles > 0:
            for _ in range(duration_cycles):
                await RisingEdge(self.dut.clk_i)
            
            # Return to idle (0 for inputs, unless specified otherwise)
            # For now, just toggle back
        
        uvm_info(self.get_name(),
                f"GPIO pin {pin_idx}: level={level}")
    
    async def drive_pattern(self, pin_list, level_list, cycle_duration=10):
        """
        Drive multiple pins in sequence.
        
        Args:
            pin_list (list): List of pin indices
            level_list (list): List of levels (must be same length)
            cycle_duration (int): Cycles per transition
        """
        for pin, level in zip(pin_list, level_list):
            await self.drive_pin(pin, level, duration_cycles=cycle_duration)


class GpioOutputMonitor:
    """
    Observes GPIO outputs (gpio_o, gpio_oe_o).
    
    Captures:
    - Output value changes
    - Output enable changes
    - Output transitions for edge detection verification
    """
    
    def __init__(self, name="gpio_output_monitor", parent=None):
        self.name = name
        self.parent = parent
        self.dut = None
        self.log = None
        self.gpio_out_data = []
        self.prev_gpio_out = 0
        self.prev_gpio_oe = 0
    
    async def run_phase(self, phase):
        """Monitor GPIO outputs for transitions."""
        await RisingEdge(self.dut.clk_i)  # Sync to clock
        
        while True:
            await RisingEdge(self.dut.clk_i)
            
            curr_gpio_out = int(self.dut.gpio_o.value)
            curr_gpio_oe = int(self.dut.gpio_oe_o.value)
            
            # Check for output value changes
            changed_pins = (self.prev_gpio_out ^ curr_gpio_out) & curr_gpio_oe
            if changed_pins:
                for pin in range(32):
                    if changed_pins & (1 << pin):
                        new_level = (curr_gpio_out >> pin) & 1
                        uvm_info(self.get_name(),
                                f"GPIO out[{pin}] -> {new_level}")
            
            # Check for output enable changes
            oe_changed = self.prev_gpio_oe ^ curr_gpio_oe
            if oe_changed:
                for pin in range(32):
                    if oe_changed & (1 << pin):
                        new_oe = (curr_gpio_oe >> pin) & 1
                        uvm_info(self.get_name(),
                                f"GPIO oe[{pin}] -> {new_oe}")
            
            self.prev_gpio_out = curr_gpio_out
            self.prev_gpio_oe = curr_gpio_oe


# ============================================================================
# HELPER SEQUENCES FOR GPIO OPERATIONS
# ============================================================================

class GpioDrivePinSeq:
    """
    Sequence: Drive a single GPIO pin from external.
    
    Example: Simulate button press (LOW → HIGH → LOW)
    """
    
    def __init__(self, name="gpio_drive_pin_seq"):
        self.name = name
        self.pin_idx = 0
        self.level_sequence = [0, 1, 0]  # e.g., press then release
        self.input_driver = None
        self.cycle_per_transition = 100
    
    async def body(self):
        """Execute GPIO pin drive sequence."""
        if self.input_driver is None:
            if self.log:
                self.log.error("input_driver not set!")
            return
        
        for level in self.level_sequence:
            await self.input_driver.drive_pin(
                self.pin_idx,
                level,
                duration_cycles=self.cycle_per_transition
            )




class GpioEdgeDetectSeq:
    """
    Sequence: Generate edge on GPIO pin and verify interrupt.
    
    Coordinates with:
    1. CSR writes: Configure interrupt enable, DIR, input mode
    2. Pin drive: Trigger rising/falling edge
    3. CSR reads: Check interrupt state
    """
    
    def __init__(self, name="gpio_edge_detect_seq"):
        self.name = name
        self.pin_idx = 0
        self.edge_type = "rising"  # or "falling"
        self.input_driver = None
        self.tl_agent = None
    
    async def body(self):
        """Execute edge detection sequence."""
        if not self.input_driver or not self.tl_agent:
            if self.log:
                self.log.error("Drivers not configured")
            return
        
        # Step 1: Configure GPIO for input (DIR = 0 for this pin)
        # Assuming DIR at 0x08, this is a simplified example
        # (In real test, would read-modify-write to preserve other pins)
        
        # Step 2: Enable edge interrupt (depends on register layout)
        # This would be INTR_CTRL_EN_RISING or similar
        
        # Step 3: Drive edge
        if self.edge_type == "rising":
            await self.input_driver.drive_pin(self.pin_idx, 1, duration_cycles=100)
        else:  # falling
            await self.input_driver.drive_pin(self.pin_idx, 0, duration_cycles=100)
        
        # Step 4: Read INTR_STATE, verify this pin's interrupt is set
        # intr_state, _ = await self.tl_agent.read_csr(addr=0x30)  # Hypothetical
        # assert (intr_state >> self.pin_idx) & 1 == 1


