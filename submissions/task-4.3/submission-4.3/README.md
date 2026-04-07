# Task 4.3 Spec Interpreter

This submission implements a specification-first verification artifact generator
for Task 4.3. The agent consumes only a natural-language specification
(markdown) and emits pre-RTL DV artifacts.

## Evaluator Setup Requirements

This agent uses OpenAI online calls during full analysis runs. Provide a valid
`OPENAI_API_KEY` in the execution environment before launching the agent.

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r agent/requirements.txt
```

1. Export API key:

```bash
export OPENAI_API_KEY=sk-proj-...
```

## Canonical Evaluator Mode

For schema-canonical automated evaluation, use `agent/run_agent.py`:

```bash
python agent/run_agent.py \
  --spec sample_spec.md \
  --output_dir output_eval
```

## Task-Page Compatibility Mode

For compatibility with the task-page entrypoint convention:

```bash
python run_spec_interpreter.py \
  --spec sample_spec.md \
  --output_dir output_eval
```

## Model Policy

1. Primary model is fixed to `gpt-5.4-mini`.
1. Reasoning effort is fixed to `xhigh`.
1. No escalation model path is enabled.

## Output Artifacts

The agent writes:

1. `output_dir/vplan.yaml`
1. `output_dir/test_stubs/helpers.py` + `output_dir/test_stubs/test_*.py`
1. `output_dir/coverage_model.yaml`
1. `output_dir/assertions.yaml`
1. `output_dir/report.md`
1. `output_dir/agent_log.json`

Compatibility mirrors are also emitted for task-page layout:

1. `output_dir/tests/`
1. `output_dir/coverage/coverage_model.yaml`
1. `output_dir/assertions/assertions.yaml`

## Makefile Usage

```bash
make compile
make run_agent SPEC=sample_spec.md OUTPUT_DIR=output_eval
```

## Troubleshooting

1. `ModuleNotFoundError` for OpenAI/yaml/cocotb:
   - Activate `.venv` and reinstall requirements.
1. `OPENAI_API_KEY is required for Task 4.3 online mode`:
   - Export `OPENAI_API_KEY` in the shell that launches the agent.
1. No output files generated:
   - Ensure `--spec` points to an existing markdown file.
