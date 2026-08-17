#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from typing import Any


def load_original() -> Any:
    path = Path(__file__).with_name("run_development.py")
    spec = importlib.util.spec_from_file_location("cv_survival_frozen_original", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen original runner {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


original = load_original()
_cache: dict[int, tuple[dict[str, int], list[set[str]]]] = {}


def cached_best_fold_jaccard(full_members: set[str], fold: int, fold_candidates: list[dict[str, Any]]) -> float:
    retained = {eid for eid in full_members if original.bucket(eid) != fold}
    original.req(retained, f"full candidate became empty in fold {fold}")

    key = id(fold_candidates)
    cached = _cache.get(key)
    if cached is None:
        event_owner: dict[str, int] = {}
        candidate_sets: list[set[str]] = []
        for i, c in enumerate(fold_candidates):
            ids = set(map(str, c["event_ids"]))
            candidate_sets.append(ids)
            for eid in ids:
                original.req(eid not in event_owner, f"fold {fold} event belongs to multiple flat candidates")
                event_owner[eid] = i
        cached = (event_owner, candidate_sets)
        _cache[key] = cached

    event_owner, candidate_sets = cached
    overlaps: Counter[int] = Counter()
    for eid in retained:
        idx = event_owner.get(eid)
        if idx is not None:
            overlaps[idx] += 1
    if not overlaps:
        return 0.0

    best = 0.0
    for idx, ov in overlaps.items():
        other = candidate_sets[idx]
        union = len(retained) + len(other) - ov
        original.req(union > 0, "invalid Jaccard union")
        best = max(best, ov / union)
    return float(best)


original.best_fold_jaccard = cached_best_fold_jaccard


if __name__ == "__main__":
    raise SystemExit(original.main())
