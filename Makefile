# Makefile for ISQED 2026 DV Challenge - Cocotb/Verilator Build

# DUT selection (default: nexus_uart)
DUT ?= nexus_uart

# Paths
DUTS_DIR = duts
TESTS_DIR = skeleton_envs
DUT_SOURCE = $(DUTS_DIR)/$(DUT)/$(DUT).sv
DUT_COMMON = $(DUTS_DIR)/common/dv_common_pkg.sv
TEST_SOURCE = $(TESTS_DIR)/$(DUT)/test_$(DUT).py

# Simulator settings
SIM_DIR = sim_$(DUT)
VERILOG_SOURCES = $(DUT_SOURCE) $(DUT_COMMON)

# Cocotb/Verilator settings
TOPLEVEL = $(DUT)
TOPLEVEL_LANG = verilog
MODULE = test_$(DUT)
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 10ps

# Export variables for Cocotb
export PYTHONPATH := $(TESTS_DIR):$(PYTHONPATH)

.PHONY: clean sim $(DUT)

# Default target
$(DUT): sim

# Run simulation
sim:
	@echo "Building and simulating $(DUT)..."
	@mkdir -p $(SIM_DIR)
	cd $(SIM_DIR) && \
	verilator --cc --exe \
		-CFLAGS "-fPIC" \
		-LDFLAGS "-shared" \
		--top-module $(TOPLEVEL) \
		-o V$(TOPLEVEL) \
		../$(DUT_SOURCE) ../$(DUT_COMMON) && \
	make -C obj_dir -f V$(TOPLEVEL).mk V$(TOPLEVEL) && \
	cd ..

# Run cocotb tests (requires simulation compiled)
test:
	@echo "Running Cocotb tests for $(DUT)..."
	cd $(TESTS_DIR)/$(DUT) && \
	python -m cocotb.runner \
		--sources $(VERILOG_SOURCES) \
		--toplevel $(TOPLEVEL) \
		--testmodule test_$(DUT)

# Quick test (compile + run)
quicktest: sim test

# Clean
clean:
	rm -rf $(SIM_DIR) sim_* __pycache__ *.pyc .coverage coverage.xml
	find $(TESTS_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "ISQED 2026 DV Challenge Build System"
	@echo "======================================="
	@echo "Usage: make [target] [DUT=<dut_name>]"
	@echo ""
	@echo "Targets:"
	@echo "  $(DUT)         - Build and sim for DUT (default: nexus_uart)"
	@echo "  sim            - Compile RTL with Verilator"
	@echo "  test           - Run Cocotb tests"
	@echo "  quicktest      - Compile + run tests"
	@echo "  clean          - Remove build artifacts"
	@echo "  help           - Show this message"
	@echo ""
	@echo "Available DUTs:"
	@echo "  - nexus_uart"
	@echo "  - bastion_gpio"
	@echo "  - citadel_spi"
	@echo "  - rampart_i2c"
	@echo "  - warden_timer"
	@echo "  - aegis_aes"
	@echo "  - sentinel_hmac"
	@echo ""
	@echo "Examples:"
	@echo "  make nexus_uart"
	@echo "  make DUT=bastion_gpio quicktest"
