# Evaluation Rubrics — Agentic AI Design Verification Challenge 2026

## Evaluation Philosophy

Every submission receives two types of evaluation:

1. **Automated Evaluation** — Objective, reproducible, runs on organizer infrastructure
2. **Judge Evaluation** — Qualitative assessment by a panel of verification engineers

The automated/judge split varies per task (see below). Automated scores are computed immediately during each evaluation cycle. Judge scores are added during periodic review sessions and finalized before the competition ends.

---

## Automated Evaluation Pipeline

All automated evaluation follows this pipeline:

```
1. VALIDATE  → Check submission structure, required files, metadata
2. COMPILE   → Compile testbench + DUT with Verilator (timeout: 2 min)
3. SIMULATE  → Run tests (timeout: 10 min per DUT, 60 min for Phase 4 agents)
4. COVERAGE  → Parse Verilator coverage DB, compute line/branch/toggle/FSM metrics
5. BUGS      → Re-compile against hidden buggy RTL variants, check for detection
6. SCORE     → Compute total based on task-specific formula
```

### Compilation Check
- Submission must compile cleanly with Verilator 5.x
- Secondary check with Icarus Verilog 12+ (warnings allowed, errors fail)
- Compilation failure = 0 score for that submission

### Coverage Measurement
- **Code coverage** via `verilator --coverage`: line, branch, toggle
- **FSM coverage** extracted from Verilator's FSM analysis
- **Functional coverage** via cocotb-coverage or pyuvm covergroups (participant-defined)
- Scores computed as: `improvement = (submission_coverage - baseline_coverage) / (target_coverage - baseline_coverage) * max_points`

### Bug Detection
- Submission's testbench is compiled against each buggy RTL variant (compiled with `-DSEED_BUG_N`)
- If any test fails or assertion fires → bug detected (true positive)
- Submission also runs against clean RTL → any failure = false positive (penalty)
- Bug detection score: `(true_positives * pts_per_bug) - (false_positives * penalty_per_fp)`

---

## Per-Task Evaluation Details

### Task 1.1: Interface Agent Generation
**Automated (80%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Compilation | 20% of task score | Verilator + Icarus compile |
| Structural completeness | 30% | Static analysis: check for required files/classes (agent, driver, monitor, sequencer, scoreboard, env, coverage) |
| Functional correctness | 30% | Run against reference RTL, check scoreboard reports pass |

**Judge (20%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Code quality | up to 20% | UVM/cocotb best practices, factory usage, TLM ports, signal naming |

**Judge rubric for code quality:**
- 5 = Exemplary: clean architecture, reusable components, proper phase usage, meaningful names
- 4 = Good: minor style issues but functionally well-structured
- 3 = Adequate: works but has architectural shortcuts or poor naming
- 2 = Weak: significant structural problems, minimal reuse potential
- 1 = Poor: barely functional, no evidence of verification methodology understanding

---

### Task 1.2: Verification Plan to Test Suite
**Automated (85%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| No false failures | Required | All tests must pass on clean RTL |
| Per VP-item coverage | Scaled | Run test, check if targeted coverage bins are hit |
| Beyond-plan tests | Bonus | Tests that hit VP items not in the plan |
| False failures | Penalty | -10 pts per test that fails on clean RTL |

**Judge (15%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Test quality | up to 15% | Verification intent clarity, setup/check completeness, corner case awareness |

---

### Task 1.3: Register Verification Suite
**Automated (90%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Per register: reset test | 2 pts each | Read after reset, compare to documented reset value |
| Per register: RW/RO test | 3 pts each | Write pattern → read back → verify |
| Full automation bonus | 50 pts | No per-register manual code (verified by static analysis) |

**Judge (10%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Pipeline quality | up to 50 pts | How well the Hjson→test generation pipeline is designed |

---

### Task 1.4: Assertion Library
**Automated (85%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Clean RTL pass | Required | No false fires on correct RTL |
| Per bug caught | 10 pts each | Assertion fires on buggy variant |
| Per mutant caught | 5 pts each | Assertion fires on mutation-tested variant |
| Assertion count >= 20 | Required | Minimum threshold per DUT |

**Judge (15%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Assertion sophistication | up to 15% | Temporal operators, property coverage, spec alignment |

---

### Task 2.1: Coverage Gap Analysis
**Automated (30%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Gap identification accuracy | Scaled | Compare identified gaps against actual coverage DB uncovered regions |

**Judge (70%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Completeness | 100 pts | Does analysis cover all major gaps? |
| Root cause accuracy | 50 pts | Are the "why uncovered" explanations correct? |
| Prioritization | 50 pts | Is the ranking of gaps by severity/difficulty sensible? |

**Judge rubric:**
- Completeness: deduct 10 pts per major gap missed, 5 pts per minor gap missed
- Accuracy: per gap, score 0-5 based on correctness of root cause
- Prioritization: compare against expert ranking, Kendall tau correlation

---

### Task 2.2: Stimulus Engineering
**Automated (95%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Line coverage improvement | 5 pts per % point | (new - baseline) in percentage points |
| Branch coverage improvement | 7 pts per % point | Higher weight — harder to close |
| Toggle coverage improvement | 3 pts per % point | |
| FSM state coverage = 100% | 50 pt bonus | All states visited |
| FSM transition coverage = 100% | 100 pt bonus | All transitions exercised |
| Functional coverage improvement | 8 pts per % point | |
| New cross-coverage bins | 5 pts each | Previously unhit cross bins |

**Judge (5%)**
- Stimulus design quality (brief review)

---

### Task 2.3: Coverage-Directed Test Generation
**Automated (80%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Coverage per cycle | Scaled | Compare efficiency against baseline random |
| Convergence rate | Scaled | Cycles to reach 85% (fewer = better) |
| Total coverage at 100k cycles | Scaled | Fixed budget comparison |

**Judge (20%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| CDG architecture innovation | up to 60 pts | Novelty and sophistication of the adaptive system |

---

### Task 3.1: The Log Whisperer
**Automated (60%)**
| Criterion | Per Failure | Method |
|-----------|-------------|--------|
| Correct classification | 10 pts | Match against ground truth failure type |
| Correct root module | 10 pts | Match against ground truth module |

**Judge (40%)**
| Criterion | Per Failure | Assessment |
|-----------|-------------|-----------|
| Root cause description | 15 pts | Accuracy and specificity of diagnosis |
| Fix suggestion | 5 pts | Is the suggestion actionable and correct? |

---

### Task 3.2: The Trace Detective
**Automated (45%)**
| Criterion | Per Failure | Method |
|-----------|-------------|--------|
| Correct manifestation cycle | 15 pts | Exact cycle match (±2 cycle tolerance) |
| Reproduction test | 30 pts | Run minimal test — does it trigger the bug? |

**Judge (55%)**
| Criterion | Per Failure | Assessment |
|-----------|-------------|-----------|
| Signal trace quality | 30 pts | Correct dependency chain from symptom to cause |
| RTL root cause location | 25 pts | Correct file:line identification |

---

### Task 3.3: The Regression Medic
**Automated (65%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Bucketing accuracy | 100 pts | Compare buckets against ground truth (adjusted Rand index) |
| Fix-to-bug mapping | 50 pts | Correct patch → bug assignment |
| Regression detection | 50 pts | Correctly identify patches that break other tests |

**Judge (35%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Root cause descriptions | 50 pts | Accuracy and actionability per bug |
| Priority ranking | 50 pts | Compare against expert severity ranking |

---

### Task 4.1: The AutoVerifier (1000 pts)
**Automated (65%) — per unseen DUT:**
| Criterion | Points | Method |
|-----------|--------|--------|
| Environment compiles | 75 pts | Verilator / VCS |
| Scoreboard correct | 100 pts | Run against reference, check transaction matching |
| Code coverage | 0-125 pts | Scaled based on line + branch + toggle |
| Functional coverage | 0-125 pts | Scaled based on covergroup hits |
| Bugs detected | 50 pts each | True positive on seeded bugs |
| False positives | -25 pts each | Failure on clean RTL |
| Time bonus (≤30 min) | 25 pts | Agent completed within time limit |

**Judge (35%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Agent architecture | 0-75 pts | Planning, tool use, reflection loops |
| Generalizability | 0-50 pts | DUT-agnostic vs DUT-specific approaches |
| Report quality | 0-25 pts | Structured, accurate, useful summary |

---

### Task 4.2: The Regression Agent (600 pts)
**Automated (80%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Correct PASS (benign) | 20 pts each | 8 benign commits |
| Correct FAIL (bug) | 50 pts each | 6 bug-introducing commits |
| Correct bug-fix ID | 30 pts each | 4 bug-fix commits |
| Correct coverage regression | 30 pts each | 2 coverage-affecting commits |
| False positive | -20 pts each | Benign flagged as FAIL |
| False negative | -40 pts each | Bug-introducing passed |
| Speed bonus (<3 min avg) | 50 pts | Average decision time |

**Judge (20%)**
- Architecture sophistication and design quality

---

### Task 4.3: The Spec Interpreter (500 pts)
**Automated (20%)**
| Criterion | Points | Method |
|-----------|--------|--------|
| Output structure | Pass/fail | Required files present, correct format |
| YAML syntax | Pass/fail | Verification plan parses correctly |
| Code syntax | Pass/fail | Test stubs and assertions are valid Python |

**Judge (80%)**
| Criterion | Points | Assessment |
|-----------|--------|-----------|
| Vplan completeness | 0-100 pts | % of expert plan items covered |
| Vplan accuracy | 0-100 pts | % of items that are valid/relevant |
| Coverage model quality | 0-100 pts | Do coverpoints capture key behaviors? |
| Assertion quality | 0-100 pts | Correct, useful, non-trivial properties |

---

## Judge Panel Procedures

1. **Composition**: 3-5 verification engineers with industry or academic DV experience
2. **Blinding**: Judge submissions are anonymized (team names redacted)
3. **Calibration**: Judges review 2-3 submissions together to align scoring before independent review
4. **Independence**: Each submission scored by at least 2 judges; scores averaged
5. **Conflict resolution**: Scores differing by >20% trigger discussion and re-scoring
6. **Timeline**: Judge scores added within 24 hours of final submission deadline
7. **Finality**: All judge panel scores are final and binding. Qualitative assessments reflect the professional judgment of the panel and are not subject to appeal.
