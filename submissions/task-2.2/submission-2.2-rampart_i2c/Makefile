TOPLEVEL_LANG = verilog
SIM ?= icarus
DUT_NAME := rampart_i2c

# Works for repo layout and extracted ZIP layout.
DUT_PATH ?= $(if $(wildcard ../../../../duts),../../../../duts,$(if $(wildcard ../../../duts),../../../duts,$(if $(wildcard ../../duts),../../duts,.)))
ifneq (,$(wildcard $(DUT_PATH)))
  VERILOG_SOURCES = $(shell find $(DUT_PATH)/common -name "*.sv") $(shell find $(DUT_PATH)/$(DUT_NAME) -name "*.sv")
else
  $(error "ERROR: Could not find DUTs directory. Set DUT_PATH=/custom/path if needed.")
endif

TOPLEVEL = $(DUT_NAME)
COCOTB_TEST_MODULES = $(shell find tests -maxdepth 1 -type f -name 'test_*.py' | sort | sed 's#/#.#g;s#.py$$##' | paste -sd, -)
export PYTHONPATH := .:./tests:./testbench:$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

ifeq ($(SIM),verilator)
  COMPILE_ARGS += -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

COVERAGE_SIM ?= verilator
COVERAGE_EXTRA_ARGS = --coverage --coverage-line --coverage-toggle --coverage-expr

.PHONY: compile simulate coverage clean

compile:
	@$(MAKE) --no-print-directory SIM=$(SIM) MODULE=tests.test_reference sim

simulate:
	@$(MAKE) --no-print-directory SIM=$(SIM) COCOTB_TEST_MODULES=$(COCOTB_TEST_MODULES) sim

coverage:
	@rm -f coverage.dat coverage.info
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory SIM=$(COVERAGE_SIM) COCOTB_TEST_MODULES=$(COCOTB_TEST_MODULES) EXTRA_ARGS="$(COVERAGE_EXTRA_ARGS)" sim
	@if command -v verilator_coverage >/dev/null 2>&1; then \
		verilator_coverage --write-info coverage.info coverage.dat >/dev/null 2>&1 || true; \
	fi

clean::
	rm -rf sim_build obj_dir __pycache__ testbench/__pycache__ tests/__pycache__ results.xml coverage.dat coverage.info

include $(shell cocotb-config --makefiles)/Makefile.sim
