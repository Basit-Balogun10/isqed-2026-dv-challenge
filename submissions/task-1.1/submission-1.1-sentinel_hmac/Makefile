# Task 1.1 Makefile for Cocotb 2.0+ - Supports Verilator and Icarus Verilog
# Resilient to different evaluation directory structures
TOPLEVEL_LANG = verilog
SIM ?= icarus

DUT_NAME := $(shell grep 'dut_id:' metadata.yaml | awk '{print $$2}')

# Path detection: try nested structure first, then flat
# Handles: project_root/submissions/task-1.1/submission-1.1-{dut}/ (us)
#     and: eval_root/submission-1.1-{dut}/ (evaluator)
DUT_PATH ?= $(if $(wildcard ../../../duts),../../../duts,$(if $(wildcard ../../duts),../../duts,$(if $(wildcard ../duts),../duts,.)))
ifneq (,$(wildcard $(DUT_PATH)))
  VERILOG_SOURCES = $(shell find $(DUT_PATH)/common -name "*.sv") $(shell find $(DUT_PATH)/$(DUT_NAME) -name "*.sv")
else
  $(error "ERROR: Could not find DUTs directory. Tried: ../../../duts ../../duts ../duts. Set DUT_PATH=/custom/path if needed.")
endif
TOPLEVEL = $(DUT_NAME)
MODULE = tests.test_basic
export PYTHONPATH := .:$(PWD)/testbench:$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
endif

ifeq ($(SIM),verilator)
  # Suppress known width/unsigned lint warnings in provided sentinel_hmac RTL.
  COMPILE_ARGS = -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
