#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("topomodal_representative_share_frozen_runner", path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def repaired_metric_record(raw: dict[str, Any], eligible_count: int) -> dict[str, Any]:
    req(eligible_count > 0, "zero eligible-label denominator")
    first = raw.get("first_rank_by_label")
    req(isinstance(first, dict), "missing first_rank_by_label")
    req(len(first) == eligible_count, "first-rank map no longer spans exact eligible-label set")
    reciprocal = 0.0
    recovered = 0
    for rank in first.values():
        if rank is None:
            continue
        r = int(rank)
        req(r >= 1, "invalid first rank")
        reciprocal += 1.0 / r
        recovered += 1
    out = {k: v for k, v in raw.items() if k != "first_rank_by_label"}
    out["mrr_zero_filled"] = float(reciprocal / eligible_count)
    out["eligible_label_count"] = int(eligible_count)
    out["recovered_label_count"] = int(recovered)
    req(recovered == int(raw["qualified_matches"]), "recovered-count adapter diverged from inherited metrics")
    return out


def main() -> int:
    runner_path = Path(__file__).with_name("train_evaluate.py")
    mod = load_module(runner_path)
    mod.metric_record = repaired_metric_record
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
