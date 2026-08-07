#!/usr/bin/env python3
"""Execute the exact frozen catalogue-v3 runner with block exact rescoring.

The frozen scientific runner is decoded and audited separately to
`/tmp/run_wavelet_catalogue_v3_development.py`. This wrapper imports that exact
source, replaces only `exact_rescore_window` with the equivalence-tested bounded
block implementation, then delegates to the original `main()` unchanged.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import block_exact_rescore

FROZEN_RUNTIME = Path("/tmp/run_wavelet_catalogue_v3_development.py")


def main() -> None:
    if not FROZEN_RUNTIME.is_file():
        raise RuntimeError("frozen catalogue runtime must be decoded and audited before wrapper execution")
    spec = importlib.util.spec_from_file_location("orbittrace_catalogue_v3_frozen_runtime", FROZEN_RUNTIME)
    runtime = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(runtime)

    original = runtime.exact_rescore_window
    replacement = block_exact_rescore.make_exact_rescore_window(runtime)
    if original is replacement:
        raise RuntimeError("block runtime replacement was not isolated")
    runtime.exact_rescore_window = replacement
    print(
        "PASS_BLOCK_RUNTIME_PATCH "
        f"block_size={block_exact_rescore.DEFAULT_BLOCK_SIZE} "
        "scientific_runner=unchanged",
        flush=True,
    )
    runtime.main()


if __name__ == "__main__":
    main()
