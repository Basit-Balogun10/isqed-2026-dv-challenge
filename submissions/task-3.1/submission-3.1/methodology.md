# Methodology

## AI Tools Used

- GitHub Copilot using GPT-5.3-Codex for log triage, hypothesis generation, RTL cross-reference,
  and structured YAML drafting.
- Local shell tooling for log indexing, pattern extraction, and consistency checks.

## Prompt Engineering Strategies

- Used evidence-first prompts that force extraction of decisive lines before classification.
- Used causality prompts that separate primary failure from warning cascades.
- Used schema-lock prompts to keep YAML format aligned with required task fields.
- Used differential prompts across similar failures (timer and i2c pairs) to avoid copy errors.

## Iteration Process

1. Loaded and reconciled Task 3.1 requirements from task description, rubric, rules, and
   submission schema.
2. Performed first-pass failure taxonomy from log signatures.
3. Mapped each failure to candidate RTL regions by searching and reading relevant modules.
4. Wrote per-failure YAML with root cause and fix grounded in both logs and RTL.
5. Consolidated cross-failure insights into summary.md and confidence rankings.
6. Added preprocessing helper for repeatable extraction and local structural validation.

## Human vs AI Contribution

- Human-led:
  - Final classification choices in ambiguous cases.
  - Final confidence calibration and signoff.
- AI-led:
  - High-volume log-to-RTL evidence harvesting.
  - Drafting and normalizing ten structured analyses.
  - Producing repeatable preprocessing helper and documentation artifacts.

## Failed Approaches

- Directly classifying from only UVM_ERROR lines was insufficient for nuanced cases.
- Assuming all failures were DUT RTL bugs overfit the data and ignored checker-model issues.
- Early broad root_line_range spans were narrowed to specific mechanisms after focused RTL reads.

## Efficiency Metrics

- Logs analyzed: 10/10
- Total log lines processed: 918
- Primary RTL files inspected: 7 DUT top modules
- Distinct failure analyses produced: 10
- Prompt evidence files provided: 6 chunk files + README + master transcript
- Runtime dependencies introduced: none beyond Python standard library for preprocessing helper

## Reproducibility

From repository root:

1. `source .venv/bin/activate`
2. `cd submissions/task-3.1/submission-3.1`
3. `python preprocessing/log_parser.py --validate analysis`
4. Optional error-context extraction:
   `python preprocessing/log_parser.py --log ../../../phase3_materials/task_3_1_logs/failure_01.log --context 4`

Prompt evidence source:

- Repository path: `submissions/task-3.1/prompts.md`
- Chunked evidence under `submission-3.1/prompts/`
