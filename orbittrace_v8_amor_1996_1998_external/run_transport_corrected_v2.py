#!/usr/bin/env python3
"""Transport-only wrapper: whitespace tokens + strict one-terminal-comma numeric decoder."""
from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path

TARGET=Path(__file__).with_name('run_external_validation.py')
NUMERIC_CORE=re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$')


def strict_comma_float(token):
    try:
        text=token.decode('ascii','strict') if isinstance(token,(bytes,bytearray)) else str(token)
    except Exception:
        return None
    if not text.endswith(',') or text.endswith(',,'):
        return None
    core=text[:-1]
    if not NUMERIC_CORE.fullmatch(core):
        return None
    try:
        value=float(core)
    except Exception:
        return None
    return value if math.isfinite(value) else None


def main()->int:
    spec=importlib.util.spec_from_file_location('frozen_v8_amor_external',TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError('could not load frozen AMOR external runner')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.split_csv=lambda raw: raw.strip().split()
    module.parse_float_token=strict_comma_float
    return int(module.main())


if __name__=='__main__':
    raise SystemExit(main())
