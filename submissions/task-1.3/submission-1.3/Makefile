# Task 1.3 Makefile - Generic CSR Test Generation (Path A)
TOPLEVEL_LANG = verilog
SIM ?= icarus
DUT ?= bastion_gpio
PYTHON ?= python3

# Path detection for local repo and extracted submission layouts.
PROJECT_ROOT ?= $(if $(wildcard ../../../duts),../../..,$(if $(wildcard ../../duts),../..,$(if $(wildcard ../duts),..,.)))
DUT_PATH ?= $(if $(wildcard $(PROJECT_ROOT)/duts),$(PROJECT_ROOT)/duts,$(if $(wildcard ./duts),./duts,.))
CSR_MAP_DIR ?= $(if $(wildcard ./csr_maps),./csr_maps,$(if $(wildcard $(PROJECT_ROOT)/csr_maps),$(PROJECT_ROOT)/csr_maps,.))

GENERATOR = generator/csr_test_generator.py
CSR_MAPS := $(wildcard $(CSR_MAP_DIR)/*_csr.hjson)

TOPLEVEL = $(DUT)
MODULE = generated_tests.test_csr_$(DUT)
export PYTHONPATH := .:./generated_tests:$(PYTHONPATH)

ifneq (,$(wildcard $(DUT_PATH)))
  VERILOG_SOURCES = $(shell find $(DUT_PATH)/common -name "*.sv") $(shell find $(DUT_PATH)/$(DUT) -name "*.sv")
else
  $(error "ERROR: Could not find DUT path. Set DUT_PATH=/path/to/duts")
endif

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
endif

ifeq ($(SIM),verilator)
	COMPILE_ARGS += -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

.PHONY: generate compile simulate coverage clean list-maps

generate:
	@mkdir -p generated_tests
	@if [ -z "$(CSR_MAPS)" ]; then \
		echo "[FAIL] No CSR maps found under $(CSR_MAP_DIR)"; \
		exit 1; \
	fi
	@for map in $(CSR_MAPS); do \
		dut=$$(basename "$$map" _csr.hjson); \
		out="generated_tests/test_csr_$$dut.py"; \
		echo "[GEN] $$map -> $$out"; \
		$(PYTHON) $(GENERATOR) --csr-map "$$map" --output "$$out"; \
	done

list-maps:
	@for map in $(CSR_MAPS); do echo $$map; done

compile: generate
	@$(MAKE) --no-print-directory SIM=$(SIM) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) sim

simulate: compile

coverage: generate
	@$(MAKE) --no-print-directory SIM=verilator TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) \
		EXTRA_ARGS="--coverage --coverage-line --coverage-toggle" sim

clean::
	rm -rf sim_build obj_dir __pycache__ generated_tests/__pycache__ results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
