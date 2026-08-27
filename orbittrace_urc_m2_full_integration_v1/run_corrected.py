#!/usr/bin/env python3
"""Pre-result adapter binding the M2 full-URC integration to corrected strict-group #846."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).with_name("run_integration.py")
spec = importlib.util.spec_from_file_location("orbittrace_urc_m2_full_integration_base", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {SOURCE}")
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)

_original_load_module = integration.load_module


def corrected_load_module(path: Path, name: str) -> Any:
    loaded = _original_load_module(path, name)
    # The corrected #846 wrapper exports its patched scientific module as `module`.
    if name == "frozen_event_membership_lab":
        return getattr(loaded, "module", loaded)
    return loaded


integration.load_module = corrected_load_module

if __name__ == "__main__":
    raise SystemExit(integration.main())
