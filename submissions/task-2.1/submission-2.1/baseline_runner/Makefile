TOPLEVEL_LANG = verilog

PWD=$(shell pwd)
PROJ_ROOT=$(PWD)/../../../..

DUT ?= nexus_uart
SIM ?= verilator

VERILOG_SOURCES = $(PROJ_ROOT)/duts/common/dv_common_pkg.sv \
                  $(PROJ_ROOT)/duts/$(DUT)/$(DUT).sv
TOPLEVEL = $(DUT)
MODULE = tests.test_smoke_baseline

export PYTHONPATH := $(PWD):$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
endif

ifeq ($(SIM),verilator)
	COMPILE_ARGS += -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

.PHONY: run clean

run:
	@$(MAKE) --no-print-directory SIM=$(SIM) TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) sim

clean::
	rm -rf sim_build obj_dir __pycache__ testbench/__pycache__ tests/__pycache__ results.xml coverage.dat

include $(shell cocotb-config --makefiles)/Makefile.sim
