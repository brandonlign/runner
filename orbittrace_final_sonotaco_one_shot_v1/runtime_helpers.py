#!/usr/bin/env python3
"""Shared source/runtime loaders for the frozen final SonotaCo one-shot pipeline.

No network access or scientific-data parsing occurs here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def load_support_base(
    *,
    p19_module: Any,
    support_source_parts: Path,
    candidate_payload: Path,
    baseline_payload: Path,
    scorer_parts: Path,
) -> tuple[Any, Any, Any, Any]:
    """Load the exact frozen support/candidate/base/scorer sources without any GMN result input."""
    runtime = p19_module.mult.load_frozen_runtime()
    support = runtime.load_support_module(support_source_parts)
    args = SimpleNamespace(
        candidate_payload=candidate_payload,
        baseline_payload=baseline_payload,
        scorer_parts=scorer_parts,
        # Source audit #893 proved load_sources does not read this path.
        fixed4_baseline_json=Path("/tmp/orbittrace-final-no-gmn-result-input.json"),
    )
    candidate, base, scorer = support.load_sources(args)
    return runtime, support, base, scorer
