# Task 1.1 + 1.2 Manual Verification Workflow

This file gives you a repeatable, manual way to verify submission readiness against:

1. File structure / required files
2. Specific requirements sanity checks
3. Automated evaluation checks
4. ZIP reverse-testing

## Separate ZIP-First Runs (Recommended)

```bash
source .venv/bin/activate
bash scripts/verify-1.1-readiness.sh --sim both
bash scripts/verify-1.2-readiness.sh --sim both
```

## Combined Convenience Wrapper (Optional)

```bash
source .venv/bin/activate
bash scripts/verify-readiness.sh --tasks 1.1,1.2 --sim both
```

## Quick Mode (Static/ZIP validation only)

```bash
source .venv/bin/activate
bash scripts/verify-1.1-readiness.sh --quick
bash scripts/verify-1.2-readiness.sh --quick
```

## Manual Step-by-step Commands

### Task 1.1

```bash
# ZIP-first full verification (package -> extract checks -> reverse-test)
source .venv/bin/activate
bash scripts/verify-1.1-readiness.sh --sim both

# Optional: check ZIP status table only
bash scripts/manage-1.1-submissions.sh status
```

### Task 1.2

```bash
# ZIP-first full verification (package -> extract checks -> reverse-test)
source .venv/bin/activate
bash scripts/verify-1.2-readiness.sh --sim both

# Optional: check ZIP status table only
bash scripts/manage-1.2-submissions.sh status
```

## ZIP Directory Convention

-   Task 1.1 ZIP output directory: `submissions/zips-1.1`
-   Task 1.2 ZIP output directory: `submissions/zips-1.2`
