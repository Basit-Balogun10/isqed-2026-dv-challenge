# Task 4.1 Local Samples

This directory stores local all-DUT validation outputs for manual inspection and GitHub examples.

Generate samples with:

```bash
bash scripts/validate-4.1-all-duts.sh --simulator both --retention full
```

Modes:

- `--retention full`: keeps rich artifacts for manual inspection (reports, tests, coverage summaries, logs, generated env/tests).
- `--retention compact`: keeps only lightweight summaries.

Heavy compile intermediates (`sim_build/`, `__pycache__/`) are pruned automatically.
