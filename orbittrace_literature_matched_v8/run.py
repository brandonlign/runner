#!/usr/bin/env python3
"""Thin execution wrapper; changes only the survey-year globals consumed by v8 helpers."""
from orbittrace_literature_matched_v8 import run_matched_benchmark as benchmark

benchmark.v8.YEARS = benchmark.YEARS
benchmark.v8.MONTH_KEYS = tuple()

if __name__ == "__main__":
    raise SystemExit(benchmark.main())
