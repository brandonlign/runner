#!/usr/bin/env python3
"""Pre-result adapter binding #850 stress to the final corrected strict-group #846 source.

The five salts, fixed-policy semantics, model/threshold/cap prohibition, gates, and data are
unchanged. This adapter only unwraps #846's pre-result strict-group wrapper so run_stress.py
operates on the corrected module rather than either superseded leaking execution.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).with_name("run_stress.py")
spec = importlib.util.spec_from_file_location("orbittrace_event_membership_fixed_stress_base", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {SOURCE}")
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)

_original_load_module = stress.load_module


def corrected_load_module(path: Path) -> Any:
    loaded = _original_load_module(path)
    return getattr(loaded, "module", loaded)


stress.load_module = corrected_load_module
stress.EXPECTED_SOURCE_COMMIT = "e5733a57488b7b8dff26c15ff76f679810efac9c"

if __name__ == "__main__":
    raise SystemExit(stress.main())
