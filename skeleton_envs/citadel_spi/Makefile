TOPLEVEL_LANG = verilog

PWD=$(shell pwd)
PROJ_ROOT=$(PWD)/../..

VERILOG_SOURCES = $(PROJ_ROOT)/duts/common/dv_common_pkg.sv $(PROJ_ROOT)/duts/citadel_spi/citadel_spi.sv
TOPLEVEL = citadel_spi
MODULE = test_basic

SIM ?= icarus

ifeq ($(SIM),icarus)
  COMPILE_ARGS = -g2012
else ifeq ($(SIM),vcs)
  COMPILE_ARGS = -sverilog +v2k -full64
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
