#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = Path(__file__).with_name('diagnose.py')
spec = importlib.util.spec_from_file_location('orbittrace_source_density_frozen_diagnose', SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError('unable to load frozen source-density diagnostic')
diagnose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnose)

# Immutable #950 pretruth manifest cardinalities. Prior execution attempts
# stopped before #1046 status; only this factual provenance constant is repaired.
diagnose.EXPECTED_SOURCES = {'hard': 19, 'p19': 53, 'p20': 157}

if __name__ == '__main__':
    raise SystemExit(diagnose.main())
