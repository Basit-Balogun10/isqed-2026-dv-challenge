# Task 1.2 Makefile for sentinel_hmac - Cocotb 2.0+ Verification Plan Tests
# Supports Verilator and Icarus Verilog - Dual-simulator compliant
TOPLEVEL_LANG = verilog
SIM ?= icarus

DUT_NAME := $(shell grep 'dut_id:' metadata.yaml | awk '{print $$2}')

# Path detection: handles both nested (project/submissions/task-1.2/) and flat (eval/submission-1.2/) structures
DUT_PATH ?= $(if $(wildcard ../../../../duts),../../../../duts,$(if $(wildcard ../../../duts),../../../duts,$(if $(wildcard ../../duts),../../duts,.)))
ifneq (,$(wildcard $(DUT_PATH)))
  VERILOG_SOURCES = $(shell find $(DUT_PATH)/common -name "*.sv") $(shell find $(DUT_PATH)/$(DUT_NAME) -name "*.sv")
else
  $(error "ERROR: Could not find DUTs directory. Set DUT_PATH=/custom/path if needed.")
endif

TOPLEVEL = $(DUT_NAME)

# Cocotb 2.0+ test discovery
COCOTB_TEST_MODULES = tests
export PYTHONPATH := .:./tests:./testbench:$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
endif

ifeq ($(SIM),verilator)
  # Suppress vendor RTL warnings in sentinel_hmac (width truncation, unsigned comparison)
  COMPILE_ARGS = -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
