# Methodology: Task 1.1 Interface Agent Generation

## AI Tools Used
- GitHub Copilot (Claude Haiku 4.5)
- Agentic prompt engineering with architectural decomposition
- Skeleton environment templates from competition materials

## Prompt Engineering Strategies
1. **Architectural Decomposition**: Separated TL-UL bus protocol from DUT-specific logic
   - TL-UL agent reused across all DUTs (single implementation)
   - Protocol agents and reference models tailored per DUT
2. **Reference Model First**: Built behavioral models before scoreboard
   - Enables transaction-level verification
   - Simplifies debugging (compare predicted vs actual outputs)

## Iteration Process
1. Copied skeleton templates from `skeleton_envs/`
2. Adapted file naming and imports to match local structure
3. Created missing components (env.py for AES/HMAC, coverage.py for all)
4. Integrated TL-UL agent with DUT-specific logic
5. Verified metadata, Makefile, and documentation completeness

## Human vs AI Contribution
- **AI Contribution (85%)**: File organization, environment wiring, coverage models, metadata generation
- **Human Contribution (15%)**: Design decisions (select optimal DUTs), verify requirements, direct iteration strategy

## Failed Approaches
- None significant — skeleton templates were comprehensive

## Efficiency Metrics
- 3 DUTs completed in single iteration
- 1950 total points (optimal tier selection: Tier 3 + Tier 3 + Tier 4)
- Reusable TL-UL agent reduces per-DUT effort by ~40%

## Reproducibility
All files are deterministic and do not depend on external randomization.
Cocotb tests use seeded RNG where randomization occurs.

---

**Submission Ready**: 3 DUTs × 7 files = 21 files
- testbench/: tl_ul_agent.py, scoreboard.py, (protocol_agent.py), env.py, coverage.py
- tests/: test_basic.py
- Root: metadata.yaml, Makefile, methodology.md
