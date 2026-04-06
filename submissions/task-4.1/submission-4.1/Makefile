PYTHON ?= python3
AGENT_ENTRY ?= agent/run_agent.py

RTL ?= ../../../duts/nexus_uart
SPEC ?= ../../../specs/nexus_uart_spec.md
CSR_MAP ?= ../../../csr_maps/nexus_uart_csr.hjson
output_dir ?= output
OUTPUT_DIR ?= $(output_dir)
SIMULATOR ?= auto
MAX_ITERATIONS ?= 4
MAX_REPAIR_GENERATIONS ?= 1
ITERATION_MODE ?= auto
MIN_ITERATIONS ?= 4
AUTO_EXTENSION_STEP ?= 2
TIMEOUT_MINUTES ?= 0

.PHONY: help setup compile simulate coverage run_agent clean

help:
	@echo "Task 4.1 AutoVerifier targets:"
	@echo "  make setup"
	@echo "  make run_agent RTL=<path> SPEC=<path> CSR_MAP=<path> output_dir=<path> SIMULATOR=<auto|icarus|verilator|both> MAX_ITERATIONS=<1..12> ITERATION_MODE=<fixed|auto> MIN_ITERATIONS=<1..12> AUTO_EXTENSION_STEP=<>=1> TIMEOUT_MINUTES=<>=0>"

setup:
	@echo "[INFO] Creating virtual environment (.venv)"
	@python3 -m venv .venv
	@echo "[INFO] Installing dependencies from agent/requirements.txt"
	@. .venv/bin/activate && pip install -r agent/requirements.txt
	@echo "[INFO] Configure API key with either:"
	@echo "       cp .env.example .env && edit OPENAI_API_KEY"
	@echo "       or export OPENAI_API_KEY=<your_key>"

compile:
	@$(PYTHON) $(AGENT_ENTRY) --rtl "$(RTL)" --spec "$(SPEC)" --csr_map "$(CSR_MAP)" --output_dir "$(OUTPUT_DIR)" --simulator "$(SIMULATOR)" --max_iterations "$(MAX_ITERATIONS)" --max_repair_generations_per_iteration "$(MAX_REPAIR_GENERATIONS)" --iteration_mode "$(ITERATION_MODE)" --min_iterations "$(MIN_ITERATIONS)" --auto_extension_step "$(AUTO_EXTENSION_STEP)" --timeout_minutes "$(TIMEOUT_MINUTES)"

simulate: compile
	@echo "[INFO] Task 4.1 uses agent-driven simulation flow; see $(OUTPUT_DIR)/report.md"

coverage: compile
	@echo "[INFO] Coverage artifacts are generated under $(OUTPUT_DIR)/coverage"

run_agent: compile

clean:
	rm -rf output output_* __pycache__ agent/src/__pycache__ agent/__pycache__
