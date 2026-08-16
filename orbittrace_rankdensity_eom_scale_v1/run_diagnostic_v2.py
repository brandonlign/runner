#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def load_frozen() -> Any:
    path = Path(__file__).with_name("run_diagnostic.py")
    spec = importlib.util.spec_from_file_location("orbittrace_rankdensity_eom_frozen_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen diagnostic {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    # Engineering correction only: the frozen merge tree can be >1000 nodes deep.
    # No scientific constant, formula, subset, gate, or traversal semantics changes.
    sys.setrecursionlimit(100000)
    frozen = load_frozen()
    return int(frozen.main())


if __name__ == "__main__":
    raise SystemExit(main())
