SHELL := /bin/bash

.PHONY: compile simulate coverage reports clean

compile:
	@echo "Task 2.1 is analysis-only; no standalone compile artifact."

simulate: coverage

coverage:
	@echo "Collecting baseline coverage for all DUTs"
	@./analysis_scripts/collect_baseline_coverage.sh

reports:
	@echo "Generating coverage summaries and gap deliverables"
	@python3 ./analysis_scripts/summarize_coverage.py
	@python3 ./analysis_scripts/generate_gap_deliverables.py

clean:
	@echo "Cleaning generated analysis artifacts"
	@rm -rf ./baseline_artifacts
	@rm -f ./gap_analysis.yaml ./gap_summary.md ./closure_plan.md ./summary.md ./priority_table.yaml
	@find ./gap_analysis -type f -name "*_gaps.md" -delete 2>/dev/null || true
