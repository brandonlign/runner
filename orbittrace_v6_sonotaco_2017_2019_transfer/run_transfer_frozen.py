#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v6_sonotaco_2017_2019_transfer import run_transfer_corrected as corrected

_ORIGINAL_PREFLIGHT = corrected.preflight_before_survey_scoring


def exact_namespace_preflight(v6, old, parsed, calibration_by_year, candidate, base, scorer):
    # The actual current-v6 transfer scan sets these same identifiers inside
    # current_v6_transfer. Set them before the pre-scientific null calibration
    # as well so supported-bin eligibility and later survey scoring share the
    # exact deterministic calibration seed namespace.
    old.YEARS = corrected.YEARS
    old.MONTH_KEYS = tuple()
    old.CORPUS = corrected.legacy.CORPUS_V6
    return _ORIGINAL_PREFLIGHT(v6, old, parsed, calibration_by_year, candidate, base, scorer)


def main() -> int:
    corrected.preflight_before_survey_scoring = exact_namespace_preflight
    try:
        return int(corrected.main())
    finally:
        corrected.preflight_before_survey_scoring = _ORIGINAL_PREFLIGHT


if __name__ == "__main__":
    raise SystemExit(main())
