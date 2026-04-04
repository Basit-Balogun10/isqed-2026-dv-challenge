# Task 1.4 Notes - sentinel_hmac

## Why this note exists
In this environment, Icarus Verilog fails to parse `bind` statements used in `bind_file.sv`.
Verilator supports the bind flow and continues to use it.

## Implemented workaround
To keep assertion checking active on both simulators:
- `SIM=verilator` uses top `sentinel_hmac` and keeps `bind_file.sv` in sources.
- `SIM=icarus` uses top `icarus_assert_wrapper` from `icarus_assert_wrapper.sv`.
- The wrapper instantiates the DUT plus all assertion modules directly (no bind syntax required).

This preserves dual-simulator behavior while avoiding Icarus bind parser limitations.

## Quick validation command
From repository root:

```bash
bash scripts/verify-1.4-readiness.sh --sim both
```

Expected result:
- rampart_i2c and sentinel_hmac both pass smoke checks on Icarus and Verilator.
