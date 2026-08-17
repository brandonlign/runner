#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

FROZEN_SOURCE_GIT_BLOB = "8f5699326758dd11cc46f9a209049a8ed61dee3a"


def load(path: Path):
    spec = importlib.util.spec_from_file_location("asfn_frozen_validation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen ASFN validation source")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_header_repair(mod) -> None:
    original = mod.header_or_record
    fields = tuple(mod.FIELDS)

    def repaired(tokens: list[str]) -> bool:
        if tokens and tokens[0] == "#":
            if len(tokens) < len(fields) + 1:
                raise RuntimeError("ASFN hash-prefixed header shorter than readme field list")
            got = tuple(tokens[1:1 + len(fields)])
            if tuple(x.lower() for x in got) != tuple(x.lower() for x in fields):
                raise RuntimeError(f"ASFN hash-prefixed header order changed: {got}")
            return True
        return original(tokens)

    mod.header_or_record = repaired


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "--frozen-source":
        raise RuntimeError("usage: header_repair_wrapper.py --frozen-source PATH [frozen runner args...]")
    source = Path(sys.argv[2])
    # Git blob is verified independently by the workflow before this wrapper runs.
    mod = load(source)
    install_header_repair(mod)
    sys.argv = [str(source)] + sys.argv[3:]
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
