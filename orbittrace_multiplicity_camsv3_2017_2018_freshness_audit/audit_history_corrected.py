#!/usr/bin/env python3
"""Audit-only correction: prior freshness-audit source is provenance, not exposure."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = Path(__file__).with_name('audit_history.py')
spec = importlib.util.spec_from_file_location('cams_freshness_base_audit', SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load base audit')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

_original = mod.classify_target_hit


def corrected_classify(hit: dict, year: int) -> str:
    p = hit['path'].lower()
    prior_audit_paths = (
        'orbittrace_multiplicity_camsv3_2016_2017_freshness_audit/',
        '.github/workflows/orbittrace-multiplicity-camsv3-2016-2017-freshness-audit.yml',
    )
    if p.startswith(prior_audit_paths):
        return 'prior_freshness_audit_only'
    return _original(hit, year)


mod.classify_target_hit = corrected_classify
raise SystemExit(mod.main())
