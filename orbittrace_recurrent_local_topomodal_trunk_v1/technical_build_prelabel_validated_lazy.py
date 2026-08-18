#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import build_prelabel as frozen


def load_helper(path: Path):
    spec = importlib.util.spec_from_file_location("validated_lazy_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validated lazy helper: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--validated-lazy-helper", type=Path, required=True)
    known, rest = ap.parse_known_args()
    helper = load_helper(known.validated_lazy_helper)
    frozen.local_trunk = helper.local_trunk_lazy
    sys.argv = [sys.argv[0], *rest]
    return frozen.main()


if __name__ == "__main__":
    raise SystemExit(main())
