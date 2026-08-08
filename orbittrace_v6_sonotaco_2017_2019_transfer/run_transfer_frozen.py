#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v6_sonotaco_2017_2019_transfer import run_transfer_corrected as corrected
from orbittrace_v6_sonotaco_2017_2019_transfer.parallel_exact_rescore import install as install_parallel_exact

_ORIGINAL_PREFLIGHT = corrected.preflight_before_survey_scoring
_ORIGINAL_LOAD_MODULE = corrected.legacy.load_module


def exact_namespace_preflight(v6, old, parsed, calibration_by_year, candidate, base, scorer):
    # The actual current-v6 transfer scan sets these same identifiers inside
    # current_v6_transfer. Set them before the pre-scientific null calibration
    # as well so supported-bin eligibility and later survey scoring share the
    # exact deterministic calibration seed namespace.
    old.YEARS = corrected.YEARS
    old.MONTH_KEYS = tuple()
    old.CORPUS = corrected.legacy.CORPUS_V6
    return _ORIGINAL_PREFLIGHT(v6, old, parsed, calibration_by_year, candidate, base, scorer)


def accelerated_load_module(path, name):
    module = _ORIGINAL_LOAD_MODULE(path, name)
    if name == "orbittrace_transfer_corrected_v6":
        config = install_parallel_exact(module, workers=4, min_parallel_records=256)
        module._orbittrace_transfer_execution = {
            "parallel_exact_enabled": True,
            "parallel_exact_workers": int(config["workers"]),
            "min_parallel_records": int(config["min_parallel_records"]),
            "scientific_body": config["scientific_body"],
        }
    return module


def main() -> int:
    corrected.preflight_before_survey_scoring = exact_namespace_preflight
    corrected.legacy.load_module = accelerated_load_module
    try:
        return int(corrected.main())
    finally:
        corrected.preflight_before_survey_scoring = _ORIGINAL_PREFLIGHT
        corrected.legacy.load_module = _ORIGINAL_LOAD_MODULE


if __name__ == "__main__":
    raise SystemExit(main())
