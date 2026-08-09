from __future__ import annotations

import argparse
import hashlib
import json
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


def exact_scientific_signature(records: list[dict[str, Any]]) -> list[tuple[str, int, float]]:
    """Fields that can affect exact-rescore or its frozen post-exact adjudication.

    Frozen exact_rescore_window_v6 obtains geometry from the immutable event
    window/event_lookup and reads proposal_anchor_id from each proposal record.
    Its returned record is then adjudicated by bin; window_center is retained as
    an integrity/order identity. Proposal-stage nearest/member diagnostics are
    overwritten by exact rescoring and are therefore deliberately not part of
    this scientific replay signature.
    """
    return [
        (str(row["proposal_anchor_id"]), int(row["bin"]), float(row["window_center"]))
        for row in records
    ]


def align_exact_outputs_to_records(
    outputs: list[dict[str, Any]], records: list[dict[str, Any]], center: float
) -> tuple[list[dict[str, Any]], bool]:
    """Recover the exact captured proposal order without changing any output value."""
    input_ids = [str(row["proposal_anchor_id"]) for row in records]
    output_ids = [str(row["proposal_anchor_id"]) for row in outputs]
    require(len(input_ids) == len(set(input_ids)), f"duplicate captured proposal anchor center {center}")
    require(len(output_ids) == len(set(output_ids)), f"duplicate exact output proposal anchor center {center}")
    require(len(output_ids) == len(input_ids), f"exact output cardinality mismatch center {center}")
    require(set(output_ids) == set(input_ids), f"exact output proposal set mismatch center {center}")
    if output_ids == input_ids:
        return outputs, False
    by_anchor = {str(row["proposal_anchor_id"]): row for row in outputs}
    aligned = [by_anchor[proposal_id] for proposal_id in input_ids]
    require(
        [str(row["proposal_anchor_id"]) for row in aligned] == input_ids,
        f"exact output realignment failed center {center}",
    )
    return aligned, True


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
    realigned_centers: list[float] = []
    nonsemantic_record_drift_centers: list[float] = []

    def replay_exact(old_arg, records, window_events, event_lookup, support_arg, base_arg):
        del old_arg, event_lookup, support_arg, base_arg
        require(bool(records), "unexpected empty replay exact call")
        center = float(records[0]["window_center"])
        require(center in pre["centers"], f"unexpected replay center {center}")
        require(center not in replayed, f"duplicate replay center {center}")
        spec = pre["centers"][center]
        captured_records = spec["records"]
        current_signature = exact_scientific_signature(records)
        captured_signature = exact_scientific_signature(captured_records)
        require(
            current_signature == captured_signature,
            f"scientific proposal identity changed before replay center {center}",
        )
        if canonical_sha(records) != spec["records_sha256"]:
            nonsemantic_record_drift_centers.append(center)
            print(
                f"V6_FANOUT_REPLAY_NONSEMANTIC_RECORD_DRIFT year={args.year} center={center:.1f}",
                flush=True,
            )
        ids = [str(row["id"]) for row in window_events]
        require(canonical_sha(ids) == spec["window_event_ids_sha256"], f"window events changed before replay center {center}")
        outputs, realigned = align_exact_outputs_to_records(exact_by_center[center], records, center)
        output_signature = exact_scientific_signature(outputs)
        require(output_signature == current_signature, f"saved exact output scientific identity mismatch center {center}")
        if realigned:
            realigned_centers.append(center)
            print(f"V6_FANOUT_REPLAY_REALIGNED_BY_ANCHOR year={args.year} center={center:.1f}", flush=True)
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
            "replay_scientific_signature_guard": ["proposal_anchor_id", "bin", "window_center"],
            "nonsemantic_record_drift_center_count": len(nonsemantic_record_drift_centers),
            "nonsemantic_record_drift_centers": nonsemantic_record_drift_centers,
            "replay_anchor_alignment_repair": True,
            "realigned_center_count": len(realigned_centers),
            "realigned_centers": realigned_centers,
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
        "nonsemantic_record_drift_center_count": len(nonsemantic_record_drift_centers),
        "nonsemantic_record_drift_centers": nonsemantic_record_drift_centers,
        "realigned_center_count": len(realigned_centers),
        "realigned_centers": realigned_centers,
    }, indent=2, sort_keys=True) + "\n")
    print(
        f"PASS_V6_FANOUT_YEAR_REPLAY year={args.year} anchors={len(anchors)} "
        f"components={len(components)} nonsemantic_record_drift_centers={len(nonsemantic_record_drift_centers)} "
        f"realigned_centers={len(realigned_centers)} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
