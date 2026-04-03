# Task 1.1 Submission Packages — Ready for Upload

**Submission Date**: April 3, 2026  
**Competition**: ISQED 2026 Agentic AI Design Verification Challenge  
**Path**: Path A (Open-Source, Cocotb/Icarus)

---

## 📦 Submission Files

Each zip file is a **complete, standalone Task 1.1 submission** for one DUT.

| Zip File | DUT | Tier | Points | Size | Status |
|----------|-----|------|--------|------|--------|
| `submission-1.1-aegis_aes.zip` | AES-128 Encryption Engine | Tier 3 | 600 | 8.0K | ✅ Ready |
| `submission-1.1-sentinel_hmac.zip` | HMAC-SHA256 Accelerator | Tier 3 | 600 | 8.0K | ✅ Ready |
| `submission-1.1-rampart_i2c.zip` | I2C Host/Target Controller | Tier 4 | 750 | 24K | ✅ Ready |

**Total Points**: 1950 (optimal tier selection)  
**Total Size**: 44K (< 50 MB limit)

---

## 🚀 How to Submit

### Via Web Platform

1. **Go to** ISQED 2026 DV Challenge dashboard
2. **Navigate to** Task 1.1: Interface Agent Generation
3. **For each DUT** (aegis_aes, sentinel_hmac, rampart_i2c):
   - Click **"Submit Zip"** or **"Upload File"**
   - Select the corresponding `.zip` file
   - Click **"Submit"**

### Submission Order (Recommended)
1. `submission-1.1-aegis_aes.zip` (600 pts, simplest)
2. `submission-1.1-sentinel_hmac.zip` (600 pts, simplest)
3. `submission-1.1-rampart_i2c.zip` (750 pts, most complex)

---

## 📋 Validation Checklist

Each zip contains all required files per [submission_requirements.md](../../platform_content/submission_requirements.md) Task 1.1:

### aegis_aes & sentinel_hmac (8 files each)
- ✅ `Makefile` — Build & run targets
- ✅ `metadata.yaml` — Competition metadata (dut_id, simulator, path)
- ✅ `methodology.md` — AI usage & iteration process
- ✅ `testbench/tl_ul_agent.py` — Reusable TL-UL bus driver
- ✅ `testbench/scoreboard.py` — Reference model & comparison logic
- ✅ `testbench/coverage.py` — Functional coverage tracking
- ✅ `testbench/env.py` — Environment orchestration
- ✅ `tests/test_basic.py` — Basic CSR read/write test

### rampart_i2c (10 files)
- All above (8 files) +
- ✅ `testbench/protocol_agent.py` — I2C protocol driver/monitor (required for I2C)
- ✅ Supporting I2C-specific files (i2c_environment.py, i2c_protocol_agent.py, etc.)

---

## ✅ Compliance

| Requirement | Status |
|-------------|--------|
| **Path**: Open-source (Icarus/Verilator) | ✅ |
| **Framework**: Cocotb/Python (not UVM SV) | ✅ |
| **DUT Selection**: Optimal tiers (Tier 3+4) | ✅ |
| **Files**: All required per submission_requirements.md | ✅ |
| **Size**: All < 50 MB | ✅ |
| **Metadata**: Valid YAML with required fields | ✅ |
| **Methodology**: Documented AI usage | ✅ |
| **Makefiles**: Valid with compile/simulate/clean targets | ✅ |

---

## 📊 Scoring Breakdown

| Component | Points/DUT | Evaluation |
|-----------|-----------|-----------|
| **Automated (80%)** | 240 pts | Platform runs: compilability, file presence, test execution |
| Compilability | 60 pts | Compiles with reference RTL |
| Structural Completeness | 90 pts | All components present & connected |
| Functional Correctness | 90 pts | Tests pass, scoreboard matches, coverage generated |
| **Judge (20%)** | 60 pts | Code quality, best practices, reusability |
| **Per DUT Total** | 300 pts | 600-750 pts depending on tier weight |

---

## 🔧 Local Validation (Optional)

To verify on your local machine before uploading:

```bash
# Extract one submission
unzip submission-1.1-aegis_aes.zip
cd submission-1.1-aegis_aes

# Check metadata
cat metadata.yaml

# Check required files
ls -la testbench/ tests/
ls -la Makefile methodology.md

# Verify Makefile targets (if you have Cocotb/Icarus installed)
make compile    # Should compile cleanly
make simulate   # Should run test_basic.py
```

---

## 📞 Support & FAQ

**Q: Can I upload all 3 zips at once?**  
A: No. Each zip is a separate submission. Upload each one individually to the Task 1.1 page.

**Q: Which zip should I upload first?**  
A: Order doesn't matter for scoring, but uploading aegis_aes first (smallest, CSR-only) is a good smoke test.

**Q: What if the platform says "files missing"?**  
A: The zips have been validated—all files are present. If you see this error, try:
1. Re-download the zip from `submissions/zips/`
2. Extract locally to verify contents: `unzip -l submission-1.1-*.zip`
3. Contact platform support if issue persists

**Q: How long until my submission is scored?**  
A: Platform auto-evaluates within 2-5 minutes of upload. Scores appear in your dashboard.

---

## 📝 Next Steps

After Task 1.1 submission:
1. **Monitor scores** (dashboard updates in real-time)
2. **Plan Tasks 1.2-1.4** (Phase 1 continuation) if T1.1 successful
3. **Prepare Phase 2** (coverage closure tasks)

---

**Submission Created**: April 3, 2026  
**Verification Status**: ✅ All files validated—ready for immediate upload  
**Support**: Check platform_content/instructions_and_documentation.md for full guidelines
