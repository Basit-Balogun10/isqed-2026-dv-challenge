# 02 — Task 4.3 Contract Resolution Prompt

## Prompt Intent

Resolve conflicting conventions between task-page layout and submission-schema
layout without risking evaluator parser failures.

## Prompt Snapshot

- Canonical outputs: top-level `vplan.yaml`, `coverage_model.yaml`,
  `assertions.yaml`, `test_stubs/`, `report.md`, `agent_log.json`.
- Compatibility outputs: mirror copies under `tests/`, `coverage/`, and
  `assertions/` for task-page readability.
- Keep canonical CLI in `agent/run_agent.py`; add compatibility
  `run_spec_interpreter.py` wrapper.

## Outcome

- Implemented dual-layout output generation.
- Added wrapper entrypoint while preserving canonical command.
