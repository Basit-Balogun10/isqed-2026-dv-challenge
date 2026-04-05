.PHONY: compile simulate coverage clean validate

PYTHON ?= python3
ANALYSIS_DIR := analysis

compile: validate

simulate: validate

coverage: validate

validate:
	$(PYTHON) preprocessing/log_parser.py --validate $(ANALYSIS_DIR)

clean:
	rm -rf __pycache__ .pytest_cache
