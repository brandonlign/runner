#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

P2_SOURCE_SHA256 = "7637b6fb310ee3f24f1de8479a34d10c594dc55471eee55b8854e1c28787e8dd"
EXECUTION_ONLY_DSH_BATCH_SIZE = 64


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    source = Path(__file__).with_name("run_development.py")
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == P2_SOURCE_SHA256, "frozen P2 scientific source changed")

    spec = importlib.util.spec_from_file_location("orbittrace_p2_frozen_batch64", source)
    require(spec is not None and spec.loader is not None, "cannot load frozen P2 source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    require(int(module.DSH_BATCH_SIZE) == 512, "unexpected frozen P2 default D_SH batch")
    # Candidate batching is an execution-only partition of calls to the exact
    # SHA-pinned Southworth-Hawkins comparator. Synthetic source-only audits
    # proved bitwise identical minima for batch sizes 8..512. No feature,
    # threshold, membership, model, event universe, or comparator formula changes.
    module.DSH_BATCH_SIZE = EXECUTION_ONLY_DSH_BATCH_SIZE
    require(int(module.DSH_BATCH_SIZE) == 64, "batch64 wrapper assignment failed")
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
