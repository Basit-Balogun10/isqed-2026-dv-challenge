# Task 4.2 Regression Agent

This submission implements a CI/CD-style regression agent for commit-stream verdicting.

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

## Preferred Modes

Preferred operation for live commit feeds is HTTP mode. Preferred operation for
single payload scripting is stdin mode.

1. Preferred live mode (HTTP, compatibility runner defaults to HTTP):

```bash
python run_regression_agent.py \
  --baseline_rtl ../../duts/nexus_uart \
  --baseline_env ../../skeleton_envs/nexus_uart \
  --output_dir output_http
```

Endpoints:

1. `GET /health`
1. `POST /commit` with one commit object (or `{ "commit": { ... } }`)
1. `POST /stream` with list or `{ "commits": [...] }`

1. Preferred scripting mode (stdin):

```bash
cat sample_commit_stream.json | python agent/run_agent.py \
  --listen stdin \
  --rtl_base ../../duts/nexus_uart \
  --test_suite ../../skeleton_envs/nexus_uart \
  --output_dir output_stdin
```

## Canonical Evaluator Mode

For schema-canonical automated evaluation, use file mode via `agent/run_agent.py`.
This runner defaults to `--listen file` and supports the exact Task 4.2
submission interface.

```bash
python agent/run_agent.py \
  --commit_stream sample_commit_stream.json \
  --rtl_base ../../duts/nexus_uart \
  --test_suite ../../skeleton_envs/nexus_uart \
  --output_dir output_file
```

Compatibility aliases are accepted:

1. `--baseline_rtl` maps to `--rtl_base`
1. `--baseline_env` maps to `--test_suite`

## Included Sample Stream

This submission includes a bundled sample stream for judge convenience:

1. `sample_commit_stream.json`

## Model Policy

1. Primary model is fixed to `gpt-5.4-mini`.
1. Reasoning effort is fixed to `xhigh`.
1. No escalation model path is enabled.

## Output Artifacts

The agent writes:

1. `output_dir/verdicts/commit_01.json`, `commit_02.json`, ...
1. `output_dir/agent_log.json`
1. `output_dir/stream_summary.json`
1. `output_dir/bug_ledger_snapshot.json`

Each verdict JSON includes required fields:

1. `commit_id`
1. `verdict` (`PASS`, `FAIL`, `COVERAGE_REGRESSION`)
1. `confidence`
1. `tests_run`
1. `tests_total`
1. `failures`
1. `bug_description`
1. `affected_module`
1. `decision_time_seconds`

## Makefile Usage

```bash
make compile
make run_agent LISTEN=file COMMIT_STREAM=sample_commit_stream.json RTL_BASE=../../duts/nexus_uart TEST_SUITE=../../skeleton_envs/nexus_uart output_dir=output_file
```

## Monitored Execution

Use monitored runner to show progress, verdict counts, and spend telemetry:

```bash
bash ../../scripts/run-4.2-monitored.sh \
  --commit-stream submissions/task-4.2/submission-4.2/sample_commit_stream.json \
  --rtl-base duts/nexus_uart \
  --test-suite skeleton_envs/nexus_uart \
  --output-dir submissions/task-4.2/submission-4.2/output_monitored_eval
```

## Troubleshooting

1. `ModuleNotFoundError` for OpenAI/yaml:
   - Activate `.venv` and reinstall requirements.
1. `OPENAI_API_KEY is required for Task 4.2 online mode`:
   - Export `OPENAI_API_KEY` in the shell that launches the agent.
1. No output files generated:
   - Ensure `--rtl_base` and `--test_suite` point to existing directories.
