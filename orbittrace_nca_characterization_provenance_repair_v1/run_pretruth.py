#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

FROZEN_BUILDER_BLOB = "6214be3da3afdf2e629fd34be980c0405c1abeae"
MISREAD_OLD_VALUE = 69
CORRECT_POSITIVE_BOUNDARY_EDGE_COUNT = 4021


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def main() -> int:
    builder = Path("orbittrace_nca_orbittrace_characterization_v1/build_pretruth.py")
    if git_blob(builder) != FROZEN_BUILDER_BLOB:
        raise RuntimeError("scientific Stage-1 builder changed")

    spec = importlib.util.spec_from_file_location("frozen_nca_characterization_builder", builder)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen Stage-1 builder")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    if int(mod.EXPECTED_BOUNDARY_EDGES) != MISREAD_OLD_VALUE:
        raise RuntimeError("unexpected pre-repair provenance constant")

    # Technical provenance correction only. The frozen C++ scorer prints
    # `b=<blevels.size()>`; the old 69 was therefore an outer-level count,
    # not the binary x/boundary-record count. Run 32308654983 reconstructed
    # the exact parent with 28,994 internal edges and 4,021 positive boundary
    # records before canonical IDs were available. No scientific rule changes.
    mod.EXPECTED_BOUNDARY_EDGES = CORRECT_POSITIVE_BOUNDARY_EDGE_COUNT
    sys.argv = [str(builder)] + sys.argv[1:]
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
