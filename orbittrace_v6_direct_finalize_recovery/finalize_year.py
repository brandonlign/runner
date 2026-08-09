from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import pickle
from collections import defaultdict
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
    p.add_argument("--preexact", required=True, type=Path)
    p.add_argument("--exact-dir", required=True, type=Path)
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


def load_pickle_with_sha(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA sidecar {path.name}")
    digest = sha256_bytes(raw)
    require(digest == sidecar.read_text().strip().split()[0], f"SHA mismatch {path.name}")
    return pickle.loads(raw), digest


def finalize_postexact(v6, old, year, exact_records_all, event_lookup, base, proposal_cal, v3_cal, fixed4_cal, audit):
    primary_by_anchor: dict[str, dict[str, Any]] = {}
    rescue_by_anchor: dict[str, dict[str, Any]] = {}
    exact_rejections = 0
    for exact in exact_records_all:
        bin_index = int(exact["bin"])
        exact["proposal_p_brown"] = old.empirical_upper_pvalue(exact["proposal_brown_score"], proposal_cal[bin_index])
        exact["p_v3"] = old.empirical_upper_pvalue(exact["v3_score"], v3_cal[bin_index])
        exact["p_fixed4"] = old.empirical_upper_pvalue(exact["fixed4_score"], fixed4_cal[bin_index])
        exact["v3_detected"] = bool(exact["p_v3"] <= v6.BASE_ALPHA)
        exact["rescue_detected"] = bool(exact["p_fixed4"] <= v6.RESCUE_ALPHA + 1e-15)
        if not (exact["v3_detected"] or exact["rescue_detected"]):
            exact_rejections += 1
            continue
        if exact["v3_detected"] and len(exact["v3_member_ids"]) >= old.MIN_COMPONENT_EVENTS:
            primary = dict(exact)
            primary["channel"] = "v3"
            primary["anchor_id"] = str(exact["v3_anchor_id"])
            primary["member_ids"] = list(exact["v3_member_ids"])
            anchor_id = str(primary["anchor_id"])
            prior = primary_by_anchor.get(anchor_id)
            key = (float(primary["p_v3"]), -float(primary["v3_score"]), float(primary["p_fixed4"]), str(primary["proposal_anchor_id"]))
            if prior is None or key < (
                float(prior["p_v3"]), -float(prior["v3_score"]), float(prior["p_fixed4"]), str(prior["proposal_anchor_id"])
            ):
                primary_by_anchor[anchor_id] = primary
        if exact["rescue_detected"] and len(exact["proposal_member_ids"]) >= old.MIN_COMPONENT_EVENTS:
            rescue = dict(exact)
            rescue["channel"] = "fixed4_rescue"
            rescue["anchor_id"] = str(exact["proposal_anchor_id"])
            rescue["member_ids"] = list(exact["proposal_member_ids"])
            anchor_id = str(rescue["anchor_id"])
            prior = rescue_by_anchor.get(anchor_id)
            key = (float(rescue["p_fixed4"]), float(rescue["p_v3"]), -float(rescue["fixed4_score"]), anchor_id)
            if prior is None or key < (
                float(prior["p_fixed4"]), float(prior["p_v3"]), -float(prior["fixed4_score"]), anchor_id
            ):
                rescue_by_anchor[anchor_id] = rescue

    def cap_anchor_track(records: list[dict[str, Any]], channel: str) -> list[dict[str, Any]]:
        by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_bin[int(record["bin"])].append(record)
        capped_track: list[dict[str, Any]] = []
        for _bin_index, rows in sorted(by_bin.items()):
            if channel == "v3":
                rows.sort(key=lambda row: (
                    float(row["p_v3"]), -float(row["v3_score"]), float(row["p_fixed4"]), str(row["anchor_id"])
                ))
            else:
                rows.sort(key=lambda row: (
                    float(row["p_fixed4"]), float(row["p_v3"]), -float(row["fixed4_score"]), str(row["anchor_id"])
                ))
            capped_track.extend(rows[: old.MAX_COMPONENTS_PER_BIN * 8])
        return capped_track

    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped
    primary_components = v6.component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = v6.component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components
    audit.update({
        "exact_rejections": exact_rejections,
        "retained_v3_anchors": len(primary_capped),
        "retained_rescue_anchors": len(rescue_capped),
        "retained_detected_anchors": len(capped),
        "v3_components": len(primary_components),
        "rescue_components": len(rescue_components),
        "components": len(components),
    })
    return audit, capped, components


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pre, pre_sha = load_pickle_with_sha(args.preexact)
    require(pre["format"] == "orbittrace-v6-preexact-fanout-v2", "preexact format changed")
    require(int(pre["year"]) == args.year, "preexact year mismatch")
    require(pre["firewall"]["target_interval_remains_excluded"] is True, "preexact target firewall failed")
    require(pre["firewall"]["hidden_labels_not_saved"] is True, "preexact label firewall failed")

    shard_paths = sorted(args.exact_dir.glob(f"v6_exact_{args.year}_shard_*.pkl"))
    require(bool(shard_paths), "no exact shard files")
    shard_count: int | None = None
    seen_indices: set[int] = set()
    exact_by_center: dict[float, list[dict[str, Any]]] = {}
    for path in shard_paths:
        shard, _ = load_pickle_with_sha(path)
        require(shard["format"] == "orbittrace-v6-exact-center-shard-v2", f"exact shard format changed: {path.name}")
        require(int(shard["year"]) == args.year, f"exact shard year mismatch: {path.name}")
        require(shard["preexact_sha256"] == pre_sha, f"exact shard preexact mismatch: {path.name}")
        require(shard["scan_rows_sha256"] == pre["scan_rows_sha256"], f"exact shard scan mismatch: {path.name}")
        require(shard["firewall"]["target_interval_remains_excluded"] is True and shard["firewall"]["labels_not_evaluated"] is True, f"exact shard firewall failed: {path.name}")
        current_count = int(shard["shard_count"])
        shard_count = current_count if shard_count is None else shard_count
        require(current_count == shard_count, "mixed exact shard counts")
        index = int(shard["shard_index"])
        require(index not in seen_indices, f"duplicate exact shard index {index}")
        seen_indices.add(index)
        for center, outputs in shard["exact_by_center"].items():
            c = float(center)
            require(c not in exact_by_center, f"duplicate exact center {c}")
            exact_by_center[c] = outputs
    require(shard_count is not None and seen_indices == set(range(shard_count)), f"incomplete exact shards: {sorted(seen_indices)}")
    require(set(exact_by_center) == {float(c) for c in pre["ordered_centers"]}, "exact center coverage differs from authoritative capture")

    repaired_sha = sha256_bytes(args.repaired_source.read_bytes())
    require(repaired_sha == pre["repaired_v6_sha256"], "repaired source mismatch")
    v6 = load_module(args.repaired_source, f"orbittrace_direct_finalize_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)
    scan = scan_by_year[args.year]
    calibration_events = calibration_by_year[args.year]
    require(event_rows_sha256(scan) == pre["scan_rows_sha256"], "scan rows changed")
    require(event_rows_sha256(calibration_events) == pre["calibration_rows_sha256"], "calibration rows changed")
    require(all(not (20.0 <= float(row["sol"]) <= 55.0) for row in scan), "blind interval entered recovery")
    source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(args.year))]
    source_sha = hashlib.sha256(json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    require(source_sha == pre["year_sources_sha256"], "source identity changed")

    # Use the literal frozen-v6 calibration routine. The earlier recovery draft
    # incorrectly called a nonexistent base-runner helper before reaching any
    # scientific continuation. Verify fresh calibration against every stored
    # preexact proposal p-value before consuming exact outputs.
    proposal_cal, v3_cal, fixed4_cal, calibration_summary = v6.calibrate_year_v6(
        old, args.year, calibration_events, candidate, base, scorer
    )
    supported_bins = sorted(v3_cal)
    require(sorted(proposal_cal) == supported_bins == sorted(fixed4_cal), "calibration bin universes differ")
    stored_pvalue_checks = 0
    for center in [float(c) for c in pre["ordered_centers"]]:
        spec = pre["centers"][center]
        records = spec["records"]
        require(canonical_sha(records) == spec["records_sha256"], f"captured record hash changed center {center}")
        outputs = exact_by_center[center]
        require([str(r["proposal_anchor_id"]) for r in outputs] == [str(r["proposal_anchor_id"]) for r in records], f"exact output order differs from authoritative proposals center {center}")
        for record in records:
            b = int(record["bin"])
            brown = old.empirical_upper_pvalue(record["proposal_brown_score"], proposal_cal[b])
            fixed4 = old.empirical_upper_pvalue(record["fixed4_score"], fixed4_cal[b])
            require(abs(float(brown) - float(record["proposal_p_brown"])) <= 1e-15, f"Brown calibration identity changed center {center}")
            require(abs(float(fixed4) - float(record["p_fixed4"])) <= 1e-15, f"fixed4 calibration identity changed center {center}")
            stored_pvalue_checks += 2
    require(stored_pvalue_checks == 2 * int(pre["total_records"]), "not every authoritative proposal calibration was verified")

    event_lookup = {str(event["id"]): event for event in scan}
    exact_records_all = [copy.deepcopy(row) for center in [float(c) for c in pre["ordered_centers"]] for row in exact_by_center[center]]
    require(len(exact_records_all) == int(pre["total_records"]), "exact record total differs from preexact capture")

    # Reconstruct only source-defined audit fields. Four pre-dedup count
    # diagnostics were not stored by fanout-v2 and are explicitly null; source
    # audit proved they are not used by any scientific/integrity decision gate.
    centers = [float(index * old.WINDOW_STEP_DEG) for index in range(int(360 / old.WINDOW_STEP_DEG))]
    unsupported_windows = 0
    window_count = 0
    for center in centers:
        window_events = old.window_events_for_center(scan, center, base)
        if len(window_events) < old.EPISODE_SIZE:
            unsupported_windows += 1
            continue
        window_count += 1
    proposal_cap = old.MAX_COMPONENTS_PER_BIN * v6.PROPOSALS_PER_WINDOW_FACTOR
    require(proposal_cap * int(360 / old.WINDOW_STEP_DEG) == 36 * old.MAX_COMPONENTS_PER_BIN * 8, "proposal budget identity changed")
    audit = {
        "year": args.year,
        "scan_events": len(scan),
        "calibration_events": len(calibration_events),
        "supported_bins": supported_bins,
        "calibration": calibration_summary,
        "window_count": window_count,
        "unsupported_windows": unsupported_windows,
        "prefilter_candidates": None,
        "proposal_candidates_scored": None,
        "primary_proposals_selected_before_dedup": None,
        "rescue_proposals_selected_before_dedup": None,
        "proposal_cap_per_window": proposal_cap,
        "max_primary_proposals_per_year": proposal_cap * len(centers),
        "deduplicated_exact_proposals": int(pre["total_records"]),
    }
    require(audit["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(audit["max_primary_proposals_per_year"] == 36864, "annual proposal budget changed")
    require(len(audit["supported_bins"]) >= 30, "supported calibration bin gate failed")

    audit, anchors, components = finalize_postexact(v6, old, args.year, exact_records_all, event_lookup, base, proposal_cal, v3_cal, fixed4_cal, audit)
    checkpoint = {
        "format": "orbittrace-v6-development-year-checkpoint-v1",
        "year": args.year,
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": repaired_sha,
        "scan_rows_sha256": pre["scan_rows_sha256"],
        "calibration_rows_sha256": pre["calibration_rows_sha256"],
        "year_sources_sha256": pre["year_sources_sha256"],
        "execution": {
            "direct_finalize_from_authoritative_preexact_v2": True,
            "source_fanout_run_id": 31282128101,
            "preexact_sha256": pre_sha,
            "exact_shard_count": shard_count,
            "stored_proposal_pvalue_checks": stored_pvalue_checks,
            "proposal_identity_regeneration_performed": False,
            "non_scientific_pre_dedup_diagnostics_unavailable": [
                "prefilter_candidates", "proposal_candidates_scored",
                "primary_proposals_selected_before_dedup", "rescue_proposals_selected_before_dedup",
            ],
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
    out = args.output / f"v6_year_{args.year}.pkl"
    out.write_bytes(raw)
    digest = sha256_bytes(raw)
    out.with_suffix(".sha256").write_text(digest + "\n")
    (args.output / f"v6_year_{args.year}.json").write_text(json.dumps({
        "year": args.year,
        "checkpoint_sha256": digest,
        "anchors": len(anchors),
        "components": len(components),
        "preexact_sha256": pre_sha,
        "exact_shard_count": shard_count,
        "stored_proposal_pvalue_checks": stored_pvalue_checks,
        "proposal_identity_regeneration_performed": False,
    }, indent=2, sort_keys=True) + "\n")
    print(
        f"PASS_V6_DIRECT_FINALIZE_YEAR year={args.year} anchors={len(anchors)} components={len(components)} "
        f"stored_pvalue_checks={stored_pvalue_checks} sha={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
