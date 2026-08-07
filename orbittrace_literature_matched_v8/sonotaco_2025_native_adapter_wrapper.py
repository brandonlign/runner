#!/usr/bin/env python3
"""Expose the exact validated SonotaCo-2025 adapter through the benchmark parser API.

No scientific parser code is edited. The gzipped source already present in the repository
is decoded, hash-checked, and called verbatim.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import sys
import types
from pathlib import Path
from typing import Any

YEAR = 2025
MEMBER = "025a/_U2_20250101_S.csv"
BLIND_SOLAR_MIN = 20.0
BLIND_SOLAR_MAX = 55.0
ADAPTER_SOURCE_SHA256 = "5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518"
PART = Path(__file__).parents[1] / "sonotaco_mondrian_development" / "source_parts" / "part00.b64"


def _load_adapter() -> Any:
    encoded = "".join(PART.read_text(encoding="ascii").split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if digest != ADAPTER_SOURCE_SHA256:
        raise RuntimeError(f"native 2025 adapter source hash changed: {digest}")
    module = types.ModuleType("orbittrace_exact_sonotaco_2025_adapter")
    module.__file__ = "orbittrace_exact_sonotaco_2025_adapter.py"
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    if not hasattr(module, "parse_sonotaco_events"):
        raise RuntimeError("native 2025 adapter API changed")
    return module


_ADAPTER = _load_adapter()


def parse_sonotaco_2025_events(archive: Path, mapping_audit: Path, base: Any):
    return _ADAPTER.parse_sonotaco_events(archive, mapping_audit, base)
