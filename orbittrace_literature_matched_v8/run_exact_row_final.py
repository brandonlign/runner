#!/usr/bin/env python3
"""Final exact-row entrypoint using the independently verified blind-safe HDBSCAN-2023 assignment.

This changes only the frozen input-artifact digest accepted by the preregistered pairwise runner.
No v8, comparator, metric, label, or decision parameter changes.
"""
from orbittrace_literature_matched_v8 import run_exact_row_benchmark as benchmark

benchmark.ASSIGNMENT_SHA256["hdbscan"][2023] = "35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761"

if __name__ == "__main__":
    raise SystemExit(benchmark.main())
