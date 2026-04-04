# Task 1.4 Makefile for rampart_i2c (Path A)
TOPLEVEL_LANG = verilog
SIM ?= icarus

DUT_NAME := $(shell grep 'dut_id:' metadata.yaml | awk '{print $$2}')

# Handle local repo and extracted-submission layouts.
DUT_PATH ?= $(if $(wildcard ../../../../duts),../../../../duts,$(if $(wildcard ../../../duts),../../../duts,$(if $(wildcard ../../duts),../../duts,.)))
ifneq (,$(wildcard $(DUT_PATH)))
  VERILOG_SOURCES = $(shell find $(DUT_PATH)/common -name "*.sv") \
                    $(shell find $(DUT_PATH)/$(DUT_NAME) -name "*.sv") \
                    assertions/protocol_assertions.sv \
                    assertions/functional_assertions.sv \
                    assertions/structural_assertions.sv \
                    assertions/liveness_assertions.sv \
                    icarus_assert_wrapper.sv \
                    bind_file.sv
else
  $(error "ERROR: Could not find DUTs directory. Set DUT_PATH=/custom/path if needed.")
endif

TOPLEVEL = $(DUT_NAME)
ICARUS_TOPLEVEL = icarus_assert_wrapper
MODULE = tests.test_with_assertions
export PYTHONPATH := .:./tests:./testbench:$(PYTHONPATH)
USER_COMPILE_ARGS ?=

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
  TOPLEVEL = $(ICARUS_TOPLEVEL)
endif

ifeq ($(SIM),verilator)
  COMPILE_ARGS += -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

COMPILE_ARGS += $(USER_COMPILE_ARGS)

.PHONY: compile simulate coverage clean

compile:
	@$(MAKE) --no-print-directory SIM=$(SIM) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) sim

simulate: compile

coverage:
	@$(MAKE) --no-print-directory SIM=verilator TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) \
		EXTRA_ARGS="--coverage --coverage-line --coverage-toggle" sim

clean::
	rm -rf sim_build obj_dir __pycache__ testbench/__pycache__ tests/__pycache__ results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim
