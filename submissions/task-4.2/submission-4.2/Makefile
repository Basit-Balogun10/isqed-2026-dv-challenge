PYTHON ?= python3
AGENT_ENTRY ?= agent/run_agent.py

COMMIT_STREAM ?= ../../task-4.2/sample_commit_stream.json
RTL_BASE ?= ../../../duts/nexus_uart
TEST_SUITE ?= ../../../skeleton_envs/nexus_uart
LISTEN ?= file
PORT ?= 8080
output_dir ?= output
OUTPUT_DIR ?= $(output_dir)

.PHONY: help setup compile simulate coverage run_agent clean

help:
	@echo "Task 4.2 Regression Agent targets:"
	@echo "  make setup"
	@echo "  make compile"
	@echo "  make run_agent LISTEN=file COMMIT_STREAM=<path> RTL_BASE=<path> TEST_SUITE=<path> output_dir=<path>"
	@echo "  make run_agent LISTEN=stdin RTL_BASE=<path> TEST_SUITE=<path> output_dir=<path> < commits.json"
	@echo "  make run_agent LISTEN=http PORT=8080 RTL_BASE=<path> TEST_SUITE=<path> output_dir=<path>"

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
	@echo "[INFO] Use 'make run_agent ...' to execute commit-stream simulation"

coverage: compile
	@echo "[INFO] Coverage deltas are emitted per-commit by run_agent"

run_agent:
	@$(PYTHON) $(AGENT_ENTRY) \
		--listen "$(LISTEN)" \
		--port "$(PORT)" \
		--commit_stream "$(COMMIT_STREAM)" \
		--rtl_base "$(RTL_BASE)" \
		--test_suite "$(TEST_SUITE)" \
		--output_dir "$(OUTPUT_DIR)"

clean:
	rm -rf output output_* __pycache__ agent/__pycache__ agent/src/__pycache__
