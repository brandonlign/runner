from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import (
    FROZEN_V6_SHA256,
    event_rows_sha256,
    load_module,
    require,
    sha256_bytes,
)

FLOAT_REL_TOL = 1e-12
FLOAT_ABS_TOL = 1e-12


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--preexact-checkpoint", required=True, type=Path)
    p.add_argument("--exact-shards-dir", required=True, type=Path)
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))


def load_pickle_with_sidecar(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA sidecar {path.name}")
    digest = sha256_bytes(raw)
    require(digest == sidecar.read_text().strip().split()[0], f"SHA mismatch {path.name}")
    return pickle.loads(raw), digest


def semantic_record_equivalence(captured: Any, replayed: Any, center: float) -> dict[str, Any]:
    """Permit only machine-precision float drift; everything else stays exact."""
    stats = {"float_values": 0, "max_abs_float_delta": 0.0, "max_rel_float_delta": 0.0}

    def compare(a: Any, b: Any, path: str) -> None:
        if isinstance(a, bool) or isinstance(b, bool):
            require(type(a) is type(b) and a == b, f"semantic boolean mismatch center {center} path {path}: {a!r} != {b!r}")
            return
        if isinstance(a, float) or isinstance(b, float):
            require(isinstance(a, (int, float)) and isinstance(b, (int, float)), f"semantic numeric type mismatch center {center} path {path}")
            af = float(a)
            bf = float(b)
            require(math.isfinite(af) and math.isfinite(bf), f"nonfinite proposal float center {center} path {path}")
            delta = abs(af - bf)
            scale = max(abs(af), abs(bf), FLOAT_ABS_TOL)
            rel = delta / scale
            stats["float_values"] += 1
            stats["max_abs_float_delta"] = max(float(stats["max_abs_float_delta"]), delta)
            stats["max_rel_float_delta"] = max(float(stats["max_rel_float_delta"]), rel)
            require(
                math.isclose(af, bf, rel_tol=FLOAT_REL_TOL, abs_tol=FLOAT_ABS_TOL),
                f"semantic float mismatch center {center} path {path}: captured={af:.17g} replayed={bf:.17g} abs={delta:.3g} rel={rel:.3g}",
            )
            return
        if isinstance(a, dict) or isinstance(b, dict):
            require(isinstance(a, dict) and isinstance(b, dict), f"semantic dict type mismatch center {center} path {path}")
            require(set(a) == set(b), f"semantic dict keys mismatch center {center} path {path}: {sorted(set(a) ^ set(b))}")
            for key in sorted(a, key=str):
                compare(a[key], b[key], f"{path}.{key}")
            return
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            require(isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)), f"semantic sequence type mismatch center {center} path {path}")
            require(len(a) == len(b), f"semantic sequence length mismatch center {center} path {path}: {len(a)} != {len(b)}")
            for index, (av, bv) in enumerate(zip(a, b)):
                compare(av, bv, f"{path}[{index}]")
            return
        require(type(a) is type(b) and a == b, f"semantic value mismatch center {center} path {path}: {a!r} != {b!r}")

    compare(captured, replayed, "records")
    return stats


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_pickle_with_sidecar(args.preexact_checkpoint)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format changed")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact hidden-label firewall failed")

    shard_paths = sorted(args.exact_shards_dir.glob(f"v6_exact_{args.year}_shard_*.pkl"))
    require(bool(shard_paths), "no exact shard files")
    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    shard_count: int | None = None
    seen_indices: set[int] = set()
    for path in shard_paths:
        shard, _digest = load_pickle_with_sidecar(path)
        require(shard["format"] == "orbittrace-v6-exact-center-shard-v2", f"exact shard format changed {path.name}")
        require(int(shard["year"]) == args.year, f"exact shard year mismatch {path.name}")
        require(shard["preexact_sha256"] == pre_sha, f"exact shard preexact mismatch {path.name}")
        require(shard["scan_rows_sha256"] == pre["scan_rows_sha256"], f"exact shard scan mismatch {path.name}")
        require(shard["firewall"]["target_interval_remains_excluded"] is True, f"exact shard firewall failed {path.name}")
        require(shard["firewall"]["labels_not_evaluated"] is True, f"exact shard label firewall failed {path.name}")
        current_count = int(shard["shard_count"])
        shard_count = current_count if shard_count is None else shard_count
        require(current_count == shard_count, "mixed exact shard counts")
        index = int(shard["shard_index"])
        require(index not in seen_indices, f"duplicate exact shard index {index}")
        seen_indices.add(index)
        for center in shard["centers"]:
            center = float(center)
            require(center not in exact_by_center, f"duplicate exact center {center}")
            exact_by_center[center] = shard["exact_by_center"][center]
    require(shard_count is not None, "missing shard count")
    require(seen_indices == set(range(shard_count)), f"incomplete exact shards: {sorted(seen_indices)} / {shard_count}")
    ordered_centers = [float(value) for value in pre["ordered_centers"]]
    require(set(exact_by_center) == set(ordered_centers), "exact center coverage mismatch")

    repaired_sha = sha256_bytes(args.repaired_source.read_bytes())
    require(repaired_sha == pre["repaired_v6_sha256"], "repaired source mismatch")
    v6 = load_module(args.repaired_source, f"orbittrace_v6_fanout_replay_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan input changed before replay")
    require(event_rows_sha256(calibration) == pre["calibration_rows_sha256"], "calibration input changed before replay")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval present in replay scan")
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(
        json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    require(source_sha == pre["year_sources_sha256"], "source identity changed before replay")

    original_exact = v6.exact_rescore_window_v6
    replayed: list[float] = []
    semantic_fallback_centers: list[float] = []
    max_abs_float_delta = 0.0
    max_rel_float_delta = 0.0

    def replay_exact(old_arg, records, window_events, event_lookup, support_arg, base_arg):
        nonlocal max_abs_float_delta, max_rel_float_delta
        del old_arg, event_lookup, support_arg, base_arg
        require(bool(records), "unexpected empty replay exact call")
        center = float(records[0]["window_center"])
        require(center in pre["centers"], f"unexpected replay center {center}")
        require(center not in replayed, f"duplicate replay center {center}")
        spec = pre["centers"][center]
        if canonical_sha(records) != spec["records_sha256"]:
            stats = semantic_record_equivalence(spec["records"], records, center)
            semantic_fallback_centers.append(center)
            max_abs_float_delta = max(max_abs_float_delta, float(stats["max_abs_float_delta"]))
            max_rel_float_delta = max(max_rel_float_delta, float(stats["max_rel_float_delta"]))
            print(
                f"V6_FANOUT_REPLAY_SEMANTIC_EQUIVALENCE year={args.year} center={center:.1f} "
                f"float_values={stats['float_values']} max_abs={stats['max_abs_float_delta']:.3g} max_rel={stats['max_rel_float_delta']:.3g}",
                flush=True,
            )
        ids = [str(row["id"]) for row in window_events]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window events changed before replay center {center}")
        outputs = exact_by_center[center]
        require(
            [str(row["proposal_anchor_id"]) for row in outputs]
            == [str(row["proposal_anchor_id"]) for row in spec["records"]],
            f"exact output/captured proposal order mismatch center {center}",
        )
        require(
            [str(row["proposal_anchor_id"]) for row in records]
            == [str(row["proposal_anchor_id"]) for row in spec["records"]],
            f"replay/captured proposal order mismatch center {center}",
        )
        replayed.append(center)
        return outputs

    v6.exact_rescore_window_v6 = replay_exact
    try:
        audit, anchors, components = v6.scan_year_v6(old, args.year, scan, calibration, candidate, base, scorer, support)
    finally:
        v6.exact_rescore_window_v6 = original_exact

    require(replayed == ordered_centers, "exact replay center order changed")
    require(int(audit["year"]) == args.year, "year audit mismatch")
    require(int(audit["proposal_cap_per_window"]) == 512, "proposal cap changed")
    require(int(audit["max_primary_proposals_per_year"]) == 36864, "annual proposal budget changed")

    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "calibration_rows_sha256": pre["calibration_rows_sha256"],
        "year_sources_sha256": pre["year_sources_sha256"],
        "execution": {
            "exact_fanout_v2": True,
            "exact_shard_count": shard_count,
            "preexact_sha256": pre_sha,
            "semantic_record_equivalence_fallback": True,
            "semantic_float_rel_tol": FLOAT_REL_TOL,
            "semantic_float_abs_tol": FLOAT_ABS_TOL,
            "semantic_fallback_center_count": len(semantic_fallback_centers),
            "semantic_fallback_centers": semantic_fallback_centers,
            "max_abs_float_delta": max_abs_float_delta,
            "max_rel_float_delta": max_rel_float_delta,
        },
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "firewall": {
            "target_interval_remains_excluded": True,
            "hidden_labels_not_saved": True,
            "scientific_result_not_evaluated_in_year_job": True,
        },
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_year_{args.year}.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    path.with_suffix(".sha256").write_text(digest + "\n")
    (args.output / f"v6_year_{args.year}.json").write_text(json.dumps({
        "year": args.year,
        "checkpoint_sha256": digest,
        "anchors": len(anchors),
        "components": len(components),
        "exact_shard_count": shard_count,
        "preexact_sha256": pre_sha,
        "semantic_fallback_center_count": len(semantic_fallback_centers),
        "semantic_fallback_centers": semantic_fallback_centers,
        "max_abs_float_delta": max_abs_float_delta,
        "max_rel_float_delta": max_rel_float_delta,
    }, indent=2, sort_keys=True) + "\n")
    print(
        f"PASS_V6_FANOUT_YEAR_REPLAY year={args.year} anchors={len(anchors)} components={len(components)} "
        f"semantic_fallback_centers={len(semantic_fallback_centers)} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
