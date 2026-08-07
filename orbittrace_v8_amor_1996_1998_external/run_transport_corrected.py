#!/usr/bin/env python3
"""Transport-only wrapper for the frozen AMOR external runner.

The preserved structure audit established whitespace-delimited AMOR members before
scientific access. This wrapper changes only the frozen runner's token splitter.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

TARGET = Path(__file__).with_name("run_external_validation.py")


def main() -> int:
    spec = importlib.util.spec_from_file_location("frozen_v8_amor_external", TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen AMOR external runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Sole correction: the pre-scientific structure audit proved these files are
    # whitespace-delimited despite the .csv suffix.
    module.split_csv = lambda raw: raw.strip().split()
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
