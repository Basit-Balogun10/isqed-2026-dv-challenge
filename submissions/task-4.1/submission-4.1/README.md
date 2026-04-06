# Task 4.1 AutoVerifier

**⚠️ EVALUATION INSTRUCTIONS: This agentic pipeline requires an OpenAI API key to function. Please create a `.env` file in this directory from `.env.example` and insert a valid `OPENAI_API_KEY`, or export `OPENAI_API_KEY` directly in your shell before running the agent.**

## Quick Start

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r agent/requirements.txt
```

1. Configure API key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

Alternative:

```bash
export OPENAI_API_KEY=sk-your-key-goes-here
```

1. Run the agent:

```bash
python agent/run_agent.py \
  --rtl <path_to_rtl_dir_or_file> \
  --spec <path_to_spec.md> \
  --csr_map <path_to_csr.hjson> \
  --output_dir <path_to_output_dir> \
  --simulator auto \
  --max_iterations 4 \
  --max_repair_generations_per_iteration 1 \
  --iteration_mode auto \
  --min_iterations 4 \
  --auto_extension_step 2 \
  --timeout_minutes 0

# Bounds:
# - max_iterations and min_iterations are clamped to [1, 12]
# - auto mode may extend iterations in +auto_extension_step chunks up to cap=12
# - timeout_minutes=0 disables global timeout lock (non-zero enables graceful timeout stop)
```

## Makefile Usage

```bash
make setup
make run_agent RTL=<path> SPEC=<path> CSR_MAP=<path> output_dir=<path> SIMULATOR=<auto|icarus|verilator|both> MAX_ITERATIONS=<1..12> ITERATION_MODE=<fixed|auto> MIN_ITERATIONS=<1..12> AUTO_EXTENSION_STEP=<>=1> TIMEOUT_MINUTES=<>=0>
```

## Output Structure

The agent writes results under the provided output directory:

- `testbench/`
- `tests/`
- `coverage/`
- `assertions/`
- `bug_reports/`
- `report.md`
- `agent_log.json`

## Test Generation Quality

- Directed and random plan entries are compiled into requirement-tagged cocotb tests with explicit assertions.
- Generated tests use DUT register metadata (name, offset, reset value, swaccess) to choose semantic operations.
- Random tests remain separate from directed tests and include constrained stress over control/datapath/interrupt/reset behaviors.
- If functional coverage plateaus across consecutive iterations and remains far from goal, the agent escalates generation with a stronger model and adds a plateau-focused test.
- Each iteration sends failing simulator errors, failing test source code, and RTL context back to the LLM for targeted module rewrites.
- After each rewrite attempt, the full regression suite is rerun (both directed and random) to catch regressions immediately.

## Iteration Controls

- `--max_iterations`: Initial iteration budget (default `4`).
- `--iteration_mode`: `fixed` or `auto` (default `auto`).
- `--min_iterations`: Minimum rounds in `auto` mode before early stop is allowed (default `4`).
- `--auto_extension_step`: Extra rounds granted per extension event in `auto` mode (default `2`).
- `--max_repair_generations_per_iteration`: Number of rewrite attempts per iteration (default `1`).
- `--timeout_minutes`: Global timeout lock for further LLM calls; run still finalizes artifacts and report (default `0`, disabled).

The final `report.md` and `iteration_log.json` include:

- Iteration mode and extension events
- Stop reason (`target met`, `budget exhausted`, `cap reached`, or `timeout`)
- Timeout reason when timeout lock is active

## Troubleshooting

- `ModuleNotFoundError: No module named 'openai'`:
  - Activate `.venv` and run `pip install -r agent/requirements.txt`.
- `ModuleNotFoundError` for `yaml` or `hjson`:
  - Run `pip install -r agent/requirements.txt`.
- `OPENAI_API_KEY is required for Task 4.1 online mode`:
  - Export `OPENAI_API_KEY` or populate `.env` in this directory.
