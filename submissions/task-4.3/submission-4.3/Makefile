PYTHON ?= python3
AGENT_ENTRY ?= agent/run_agent.py

SPEC ?= sample_spec.md
OUTPUT_DIR ?= output
CONFIG ?= agent/agent_config.yaml

.PHONY: help setup compile simulate coverage run_agent clean

help:
	@echo "Task 4.3 Spec Interpreter targets:"
	@echo "  make setup"
	@echo "  make compile"
	@echo "  make run_agent SPEC=<path_to_spec.md> OUTPUT_DIR=<output_dir>"
	@echo "  make run_agent SPEC=sample_spec.md OUTPUT_DIR=output"

setup:
	@echo "[INFO] Creating virtual environment (.venv)"
	@python3 -m venv .venv
	@echo "[INFO] Installing dependencies from agent/requirements.txt"
	@. .venv/bin/activate && pip install -r agent/requirements.txt
	@echo "[INFO] Export OPENAI_API_KEY before runtime"

compile:
	@$(PYTHON) $(AGENT_ENTRY) --help >/dev/null
	@echo "[INFO] CLI contract check passed"

simulate: compile
	@echo "[INFO] Use 'make run_agent ...' to execute spec interpretation"

coverage: compile
	@echo "[INFO] Coverage model is emitted by run_agent to coverage_model.yaml"

run_agent:
	@$(PYTHON) $(AGENT_ENTRY) \
		--spec "$(SPEC)" \
		--output_dir "$(OUTPUT_DIR)" \
		--config "$(CONFIG)"

clean:
	rm -rf output output_* __pycache__ agent/__pycache__ agent/src/__pycache__
