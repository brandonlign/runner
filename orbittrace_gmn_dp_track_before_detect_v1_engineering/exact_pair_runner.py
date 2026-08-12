#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

FROZEN = Path(__file__).resolve().parents[1] / "orbittrace_gmn_dp_track_before_detect_v1" / "run_development.py"


def load_frozen():
    spec = importlib.util.spec_from_file_location("orbittrace_dptbd_v1_frozen", FROZEN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen source {FROZEN}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def exact_pair_radius_counts_factory(mod):
    def exact_pair_radius_counts(tree, query_x, query_u, query_logv, ref_u, ref_logv, subtract_self, batch=2000):
        # The frozen detector uses this routine only for self-neighborhood counts:
        # query and reference arrays are identical and self is subtracted.  query_pairs
        # enumerates each non-self unordered KD-tree pair exactly once; exact physical
        # d<=1 filtering is unchanged, then both endpoints receive one count.
        if not subtract_self:
            raise RuntimeError("pair wrapper only supports frozen self-neighborhood calls")
        if len(query_x) != len(ref_u) or len(query_x) != len(ref_logv):
            raise RuntimeError("pair wrapper received non-self neighborhood shapes")
        if np.shape(tree.data) != np.shape(query_x) or not np.array_equal(np.asarray(tree.data), np.asarray(query_x)):
            raise RuntimeError("pair wrapper tree/query mismatch")
        if len(query_u) != len(ref_u) or not np.array_equal(query_u, ref_u):
            raise RuntimeError("pair wrapper radiant query/reference mismatch")
        if len(query_logv) != len(ref_logv) or not np.array_equal(query_logv, ref_logv):
            raise RuntimeError("pair wrapper speed query/reference mismatch")

        out = np.zeros(len(query_x), dtype=np.int32)
        pairs = tree.query_pairs(r=1.0 + 1e-12, output_type="ndarray")
        if len(pairs) == 0:
            return out
        # Chunk exact filtering to bound temporary arrays; this changes no arithmetic.
        chunk = 250000
        for start in range(0, len(pairs), chunk):
            p = np.asarray(pairs[start:start + chunk], dtype=np.int64)
            d2 = mod.exact_d2(query_u[p[:, 0]], query_logv[p[:, 0]], ref_u[p[:, 1]], ref_logv[p[:, 1]])
            good = p[d2 <= 1.0 + 1e-12]
            if len(good):
                np.add.at(out, good[:, 0], 1)
                np.add.at(out, good[:, 1], 1)
        return out

    return exact_pair_radius_counts


def main() -> int:
    mod = load_frozen()
    mod.exact_radius_counts = exact_pair_radius_counts_factory(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
