#!/usr/bin/env python3
"""Implementation-only loader correction for the preregistered multiplicity-v5 holdout.

The first v5 execution stopped before support.parse_catalogue().  Source-only audit
proved that the catalogue-v3 helper executes the exact raw fixed4 support module and
then overwrites four module globals.  This wrapper verifies that exact loader state,
restores the audited raw fixed4 non-temporal globals plus raw YEARS so the unchanged
v5 guard can verify it, and then delegates to the unchanged preregistered holdout.
The unchanged holdout itself performs the only scientific temporal substitution to
2020-2021 before its first catalogue call.
"""
from __future__ import annotations

from typing import Any

import run_holdout as core

RUNTIME_PRESENTED_YEARS = (2022, 2023)
RUNTIME_PRESENTED_CORPUS = "gmn-wavelet-catalogue-v3-development-2022-2023-excluding-sol20-55"
RUNTIME_PRESENTED_RANKING_VARIANTS = ("wavelet_recurrence",)

RAW_FIXED4_YEARS = (2022, 2023, 2024, 2025)
RAW_FIXED4_CORPUS = "gmn-known-shower-wrapper-development-2022-2025-excluding-sol20-55"
RAW_FIXED4_RANKING_VARIANTS = (
    "persistence",
    "mean_year_strength",
    "sqrt_support_strength",
    "min_year_strength",
    "size_penalized_strength",
)


def corrected_load_frozen_runtime() -> Any:
    runtime = core.load_frozen_runtime_original()
    original_loader = runtime.load_support_module

    def load_support_module(root: Any) -> Any:
        support = original_loader(root)
        core.require(
            tuple(support.YEARS) == RUNTIME_PRESENTED_YEARS,
            "catalogue-v3 loader presented unexpected support years",
        )
        core.require(
            str(support.CORPUS) == RUNTIME_PRESENTED_CORPUS,
            "catalogue-v3 loader presented unexpected support corpus",
        )
        core.require(
            tuple(support.RANKING_VARIANTS) == RUNTIME_PRESENTED_RANKING_VARIANTS,
            "catalogue-v3 loader presented unexpected ranking variants",
        )

        # Restore the exact audited raw fixed4 wrapper state.  MONTH_KEYS is not
        # restored because the unchanged v5 implementation replaces both YEARS and
        # MONTH_KEYS with its preregistered 2020-2021 panel before first data access.
        support.YEARS = RAW_FIXED4_YEARS
        support.CORPUS = RAW_FIXED4_CORPUS
        support.RANKING_VARIANTS = RAW_FIXED4_RANKING_VARIANTS

        core.require(tuple(support.YEARS) == RAW_FIXED4_YEARS, "raw fixed4 years restoration failed")
        core.require(str(support.CORPUS) == RAW_FIXED4_CORPUS, "raw fixed4 corpus restoration failed")
        core.require(
            tuple(support.RANKING_VARIANTS) == RAW_FIXED4_RANKING_VARIANTS,
            "raw fixed4 ranking-variant restoration failed",
        )
        return support

    runtime.load_support_module = load_support_module
    return runtime


# Preserve a direct handle to the unchanged implementation before replacing the
# one entry point whose wrapper behavior was proven incorrect source-only.
core.load_frozen_runtime_original = core.load_frozen_runtime
core.load_frozen_runtime = corrected_load_frozen_runtime


if __name__ == "__main__":
    raise SystemExit(core.main())
