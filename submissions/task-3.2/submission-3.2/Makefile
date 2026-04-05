SIM ?= icarus
PYTHON ?= python3

# Works for repo layout and extracted ZIP layout.
DUT_PATH ?= \
	$(if $(wildcard ../../../../duts/common/dv_common_pkg.sv),../../../../duts,\
	$(if $(wildcard ../../../duts/common/dv_common_pkg.sv),../../../duts,\
	$(if $(wildcard ../../duts/common/dv_common_pkg.sv),../../duts,\
	$(if $(wildcard ../duts/common/dv_common_pkg.sv),../duts,\
	$(if $(wildcard ../../../../../duts/common/dv_common_pkg.sv),../../../../../duts,\
	$(if $(wildcard ../../../../../../duts/common/dv_common_pkg.sv),../../../../../../duts,.))))))

ifneq (,$(wildcard $(DUT_PATH)/common/dv_common_pkg.sv))
  COMMON_SV = $(DUT_PATH)/common/dv_common_pkg.sv
else
	$(error "ERROR: Could not find DUTs directory. Tried relative paths up to ../../../../../../duts. Set DUT_PATH=/custom/path if needed.")
endif

REPRO_CASES := 01 02 03 04 05
COCOTB_SIM_MK := $(shell cocotb-config --makefiles)/Makefile.sim

export PYTHONPATH := .:./reproduction_tests:./testbench:$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

ifeq ($(SIM),verilator)
  COMPILE_ARGS += -Wno-fatal -Wno-WIDTHTRUNC -Wno-WIDTHEXPAND -Wno-UNSIGNED
endif

.PHONY: validate compile simulate run_repro coverage clean

validate:
	@$(PYTHON) preprocessing/trace_validator.py --validate analysis

compile: validate
	@set -e; \
	sims="$(SIM)"; \
	if [ "$(SIM)" = "both" ]; then sims="icarus verilator"; fi; \
	for sim in $$sims; do \
	  echo "[INFO] Compile smoke with $$sim"; \
	  for dut in warden_timer nexus_uart citadel_spi aegis_aes rampart_i2c; do \
	    if [ "$$sim" = "icarus" ]; then \
	      iverilog -g2012 -o /tmp/task32_compile_$$dut.out "$(COMMON_SV)" "$(DUT_PATH)/$$dut/$$dut.sv" >/dev/null; \
	    else \
	      verilator --lint-only "$(COMMON_SV)" "$(DUT_PATH)/$$dut/$$dut.sv" >/dev/null; \
	    fi; \
	  done; \
	done

simulate: run_repro

run_repro: validate
	@set -e; \
	sims="$(SIM)"; \
	if [ "$(SIM)" = "both" ]; then sims="icarus verilator"; fi; \
	for sim in $$sims; do \
	  for case_id in $(REPRO_CASES); do \
	    case $$case_id in \
	      01) dut=warden_timer ;; \
	      02) dut=nexus_uart ;; \
	      03) dut=citadel_spi ;; \
	      04) dut=aegis_aes ;; \
	      05) dut=rampart_i2c ;; \
	      *) echo "Unknown case $$case_id"; exit 1 ;; \
	    esac; \
	    module="reproduction_tests.repro_$$case_id"; \
	    src="$(DUT_PATH)/$$dut/$$dut.sv"; \
	    echo "[INFO] Running $$module on $$dut (SIM=$$sim)"; \
	    $(MAKE) --no-print-directory -f "$(COCOTB_SIM_MK)" \
	      SIM=$$sim \
	      TOPLEVEL_LANG=verilog \
	      TOPLEVEL=$$dut \
	      MODULE=$$module \
	      VERILOG_SOURCES="$(COMMON_SV) $$src" \
	      COMPILE_ARGS="$(COMPILE_ARGS)" \
	      SIM_BUILD="sim_build/repro_$$case_id_$$sim"; \
	  done; \
	done

coverage:
	@$(MAKE) --no-print-directory run_repro SIM=verilator COMPILE_ARGS="$(COMPILE_ARGS) --coverage --coverage-line --coverage-toggle --coverage-expr"

clean:
	rm -rf sim_build obj_dir __pycache__ .pytest_cache \
	  reproduction_tests/__pycache__ testbench/__pycache__ \
	  results.xml coverage.dat coverage.info
