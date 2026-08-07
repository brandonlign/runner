#!/usr/bin/env python3
"""Execution-only provenance correction for the preregistered exact-row benchmark.

The scientific benchmark implementation is unchanged. This wrapper replaces only the
ineligible original HDBSCAN-2023 assignment hash with the separately verified blind-safe
canonical assignment selected in HDBSCAN_2023_BLIND_RESULT_INTERPRETATION.md.
"""
from orbittrace_literature_matched_v8 import run_exact_row_benchmark as benchmark

CANONICAL_HDB23_SHA256 = "35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761"
ORIGINAL_INELIGIBLE_HDB23_SHA256 = "7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60"


def main() -> int:
    assert benchmark.ASSIGNMENT_SHA256["hdbscan"][2023] == ORIGINAL_INELIGIBLE_HDB23_SHA256
    benchmark.ASSIGNMENT_SHA256["hdbscan"][2023] = CANONICAL_HDB23_SHA256
    return benchmark.main()


if __name__ == "__main__":
    raise SystemExit(main())
