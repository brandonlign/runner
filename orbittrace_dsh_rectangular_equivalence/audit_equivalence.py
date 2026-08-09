#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

from rectangular_dsh import rectangular_dsh

CANONICAL_SHA256 = "85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load(path: Path):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CANONICAL_SHA256, "canonical D_SH source changed")
    spec = importlib.util.spec_from_file_location("canonical_dsh", path)
    require(spec is not None and spec.loader is not None, "cannot import canonical D_SH module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panel(rng: np.random.Generator, n: int) -> tuple[np.ndarray, ...]:
    return (
        rng.uniform(0.01, 1.4, n).astype(np.float64),
        rng.uniform(0.001, 0.999, n).astype(np.float64),
        rng.uniform(0.0, 179.999999, n).astype(np.float64),
        rng.uniform(-720.0, 720.0, n).astype(np.float64),
        rng.uniform(-720.0, 720.0, n).astype(np.float64),
    )


def canonical_block(module, left, right):
    joined = tuple(np.concatenate((a, b)) for a, b in zip(left, right))
    square = module.pairwise_dsh(*joined)
    return square[: len(left[0]), len(left[0]) :]


def direct_block(left, right):
    return rectangular_dsh(*left, *right)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--canonical", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    module = load(args.canonical)
    rng = np.random.default_rng(20260809)

    tests: list[tuple[str, tuple[np.ndarray, ...], tuple[np.ndarray, ...]]] = []
    for n_left, n_right in ((1, 1), (7, 13), (100, 266), (512, 5), (512, 53), (512, 266)):
        tests.append((f"random_{n_left}x{n_right}", panel(rng, n_left), panel(rng, n_right)))

    # Deterministic edge panel exercises wrap boundaries, nearly coplanar and
    # nearly retrograde planes, circular/high-e orbits, and peri/node aliases.
    left = (
        np.array([0.01, 0.1, 0.5, 1.0, 1.4], dtype=np.float64),
        np.array([0.001, 0.2, 0.5, 0.9, 0.999], dtype=np.float64),
        np.array([0.0, 1e-12, 89.999999, 179.999999, 45.0], dtype=np.float64),
        np.array([-720.0, -180.0, 0.0, 359.999999, 720.0], dtype=np.float64),
        np.array([-360.000001, -180.0, 0.0, 180.0, 359.999999], dtype=np.float64),
    )
    right = (
        np.array([0.02, 0.11, 0.51, 1.01, 1.39, 0.7], dtype=np.float64),
        np.array([0.002, 0.21, 0.49, 0.89, 0.998, 0.7], dtype=np.float64),
        np.array([1e-12, 0.0, 90.000001, 179.999998, 45.000001, 135.0], dtype=np.float64),
        np.array([720.0, 180.0, -1e-12, -359.999999, -720.0, 181.0], dtype=np.float64),
        np.array([360.000001, 180.0, -1e-12, -180.0, -359.999999, 1.0], dtype=np.float64),
    )
    tests.append(("deterministic_edges_5x6", left, right))

    results = []
    for name, a, b in tests:
        t0 = time.perf_counter(); expected = canonical_block(module, a, b); t1 = time.perf_counter()
        actual = direct_block(a, b); t2 = time.perf_counter()
        exact = bool(np.array_equal(expected, actual))
        max_abs = float(np.max(np.abs(expected - actual))) if expected.size else 0.0
        require(exact and max_abs == 0.0, f"rectangular D_SH mismatch {name}: max_abs={max_abs}")
        results.append({
            "name": name,
            "shape": list(expected.shape),
            "bitwise_equal": exact,
            "max_abs_difference": max_abs,
            "canonical_square_seconds": t1 - t0,
            "rectangular_seconds": t2 - t1,
        })
        print(f"PASS_DSH_RECTANGULAR_EXACT {name} {expected.shape}", flush=True)

    payload = {
        "classification": "ENGINEERING_ONLY_EXACT_DSH_RECTANGULAR_EQUIVALENCE",
        "canonical_sha256": CANONICAL_SHA256,
        "scientific_parameters_changed": False,
        "target_data_accessed": False,
        "known_shower_truth_accessed": False,
        "tests": results,
        "all_bitwise_equal": all(r["bitwise_equal"] for r in results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print("PASS_DSH_RECTANGULAR_EQUIVALENCE_AUDIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
