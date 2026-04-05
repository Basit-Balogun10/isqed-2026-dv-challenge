PYTHON ?= python3
SIM ?= both
FAILURE_DETAILS ?= ../../../phase3_materials/task_3_3_regression/failure_details.yaml
PATCHES_DIR ?= ../../../phase3_materials/task_3_3_regression/patches

.PHONY: validate compile simulate coverage clean

validate:
	@$(PYTHON) analysis_scripts/validate_task33.py \
		--submission-dir . \
		--failure-details $(FAILURE_DETAILS) \
		--patches-dir $(PATCHES_DIR)

compile: validate
	@echo "[INFO] Task 3.3 is analysis-first; compile gate uses structural/schema validation"

simulate: validate
	@echo "[INFO] Task 3.3 simulation replay is not bundled; using provided failure metadata inputs"

coverage: validate
	@echo "[INFO] Task 3.3 has no code-coverage target; triage quality is scored via bucketing/mapping/regression analysis"

clean:
	rm -rf __pycache__ analysis_scripts/__pycache__
