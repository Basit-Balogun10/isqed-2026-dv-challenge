# Baseline Comparison

This report compares adaptive CDG against a fixed-policy static baseline 
using equal iteration count and cycle budget.

Adaptive AUC (combined coverage vs cycles): 6981359.62
Baseline AUC (combined coverage vs cycles): 6623373.94
Efficiency ratio (adaptive / baseline): 1.0540

Adaptive final combined coverage: 75.99%
Baseline final combined coverage: 71.82%

Interpretation:
- Ratio > 1.0 means adaptive loop outperformed fixed static policy.
- Ratio < 1.0 means static policy performed better for this run.
