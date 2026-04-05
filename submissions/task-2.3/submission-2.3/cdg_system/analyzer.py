"""Task-page compatibility shim.

Maps task_2_3_coverage_directed_generation.md naming (analyzer.py)
to submission_requirements naming (coverage_analyzer.py).
"""

from .coverage_analyzer import CoverageAnalyzer, CoverageMetrics

__all__ = ["CoverageAnalyzer", "CoverageMetrics"]
