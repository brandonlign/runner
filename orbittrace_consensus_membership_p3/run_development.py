#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import types
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
EXPECTED_FAMILY_COUNT = 226
P1_PRETRUTH_SHA256 = "ba0269bab1e3db76bd981364225a815d719d8154348c5c39d124ece0f400f73a"
V8_QUALIFIED = 95
V8_RECOVERY100 = 58
V8_MRR = 0.045531138942766655
V8_TOP100_PRECISION = 0.6884631112636006
V8_MACRO_F1 = 0.1736657194465356
MACRO_F1_MIN = V8_MACRO_F1 + 0.08
TOP100_PRECISION_MIN = 0.65
LARGE_TOTAL_MIN = 100
LARGE_RECALL_MULTIPLIER = 1.5
LARGE_PRECISION_MIN = 0.85


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def load_json_gz(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))


def load_module(path: Path, name: str) -> types.ModuleType:
    require(path.is_file(), f"missing source: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_parts(family: dict[str, Any], added_key: str) -> tuple[set[str], set[str]]:
    all_ids = set(map(str, family["event_ids"]))
    additions = set(map(str, family.get(added_key, [])))
    require(additions.issubset(all_ids), f"{added_key} not subset of membership for {family['family_id']}")
    seeds = all_ids - additions
    require(seeds, f"empty seed set for {family['family_id']}")
    return seeds, additions


def freeze_consensus(
    p1: list[dict[str, Any]], p2: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    require(len(p1) == len(p2) == EXPECTED_FAMILY_COUNT, "parent family count mismatch")
    ids1 = [str(f["family_id"]) for f in p1]
    ids2 = [str(f["family_id"]) for f in p2]
    require(ids1 == ids2, "parent family order mismatch")
    require(len(set(ids1)) == EXPECTED_FAMILY_COUNT, "family IDs not unique")

    p3: list[dict[str, Any]] = []
    baseline: list[dict[str, Any]] = []
    global_seen: set[str] = set()
    p1_add_total = p2_add_total = p3_add_total = 0
    disagreement_overlap = 0
    families_gaining = 0
    family_audit: list[dict[str, Any]] = []

    for f1, f2 in zip(p1, p2):
        fid = str(f1["family_id"])
        require(str(f2["family_id"]) == fid, "family alignment changed")
        seeds1, add1 = parent_parts(f1, "p1_added_event_ids")
        seeds2, add2 = parent_parts(f2, "p2_added_event_ids")
        require(seeds1 == seeds2, f"parent seed mismatch for {fid}")

        additions = add1 & add2
        p1_add_total += len(add1)
        p2_add_total += len(add2)
        p3_add_total += len(additions)
        families_gaining += int(bool(additions))

        # Events added by both parents but to different families are excluded automatically;
        # record later from parent-wide maps for audit.
        require(not (global_seen & additions), f"P3 nonseed duplicated across families at {fid}")
        global_seen |= additions

        base = copy.deepcopy(f1)
        for key in ("p1_added_event_ids", "p1_added_event_count", "p2_added_event_ids", "p2_added_event_count"):
            base.pop(key, None)
        base["event_ids"] = sorted(seeds1)
        base["event_count"] = len(seeds1)
        baseline.append(base)

        out = copy.deepcopy(base)
        out["p3_added_event_ids"] = sorted(additions)
        out["p3_added_event_count"] = len(additions)
        out["event_ids"] = sorted(seeds1 | additions)
        out["event_count"] = len(out["event_ids"])
        p3.append(out)

        family_audit.append({
            "family_id": fid,
            "seed_count": len(seeds1),
            "p1_added": len(add1),
            "p2_added": len(add2),
            "p3_intersection_added": len(additions),
        })

    # Explicitly count same-event parent disagreements without using any score.
    p1_owner: dict[str, str] = {}
    p2_owner: dict[str, str] = {}
    for f in p1:
        _, adds = parent_parts(f, "p1_added_event_ids")
        for eid in adds:
            require(eid not in p1_owner, f"P1 addition assigned twice: {eid}")
            p1_owner[eid] = str(f["family_id"])
    for f in p2:
        _, adds = parent_parts(f, "p2_added_event_ids")
        for eid in adds:
            require(eid not in p2_owner, f"P2 addition assigned twice: {eid}")
            p2_owner[eid] = str(f["family_id"])
    for eid in set(p1_owner) & set(p2_owner):
        disagreement_overlap += int(p1_owner[eid] != p2_owner[eid])
        if p1_owner[eid] == p2_owner[eid]:
            require(eid in global_seen, f"same-family parent agreement missing from P3: {eid}")
        else:
            require(eid not in global_seen, f"parent disagreement leaked into P3: {eid}")

    audit = {
        "family_count": len(p3),
        "p1_added_total": p1_add_total,
        "p2_added_total": p2_add_total,
        "p3_same_family_intersection_total": p3_add_total,
        "families_gaining_members": families_gaining,
        "events_added_by_both_parents_to_different_families": disagreement_overlap,
        "p3_nonseed_unique": len(global_seen) == p3_add_total,
        "consensus_operator": "exact same-family stable-event-ID intersection only",
        "family_audit": family_audit,
    }
    return baseline, p3, audit


def label_totals(hidden_labels: dict[str, str], mult: types.ModuleType) -> dict[str, int]:
    eligible = mult.eligible_labels(hidden_labels)
    return {label: int(sum(per_year.values())) for label, per_year in eligible.items()}


def large_summary(metrics: dict[str, Any], totals: dict[str, int], subset: set[str]) -> dict[str, Any]:
    rows = {str(row["label"]): row for row in metrics["per_label"]}
    values = []
    for label in sorted(subset):
        row = rows[label]
        values.append({
            "label": label,
            "total": totals[label],
            "qualified": bool(row.get("qualified", False)),
            "precision": float(row.get("precision", 0.0)),
            "recall": float(row.get("recall", 0.0)),
            "f1": float(row.get("f1", 0.0)),
        })
    return {
        "labels": len(values),
        "mean_precision": float(np.mean([v["precision"] for v in values])) if values else 0.0,
        "mean_recall": float(np.mean([v["recall"] for v in values])) if values else 0.0,
        "mean_f1": float(np.mean([v["f1"] for v in values])) if values else 0.0,
        "qualified": int(sum(v["qualified"] for v in values)),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--p1-families", required=True, type=Path)
    p.add_argument("--p1-sha", required=True, type=Path)
    p.add_argument("--p2-families", required=True, type=Path)
    p.add_argument("--p2-sha", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    p1_expected = args.p1_sha.read_text().strip()
    p2_expected = args.p2_sha.read_text().strip()
    require(p1_expected == P1_PRETRUTH_SHA256, f"P1 pretruth SHA changed: {p1_expected}")
    require(len(p2_expected) == 64 and all(c in "0123456789abcdef" for c in p2_expected), "invalid P2 pretruth SHA")

    p1 = load_json_gz(args.p1_families)
    p2 = load_json_gz(args.p2_families)
    require(canonical_sha(p1) == p1_expected, "P1 pretruth family payload hash mismatch")
    require(canonical_sha(p2) == p2_expected, "P2 pretruth family payload hash mismatch")

    # Critical P3 pretruth operation: no catalogue parser or truth source is loaded before this freeze.
    baseline_families, p3_families, consensus_audit = freeze_consensus(p1, p2)
    p3_sha = canonical_sha(p3_families)
    raw = json.dumps(p3_families, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    (args.output / "p3_expanded_families.json.gz").write_bytes(gzip.compress(raw))
    (args.output / "p3_membership_pretruth.sha256").write_text(p3_sha + "\n")
    (args.output / "p3_consensus_pretruth_audit.json").write_text(
        json.dumps({"p3_membership_pretruth_sha256": p3_sha, **consensus_audit}, indent=2, sort_keys=True) + "\n"
    )

    # FIRST truth-capable source loading occurs only after the P3 membership is durably frozen.
    old = load_module(args.base_runner, "orbittrace_p3_base_runner")
    v8 = load_module(args.v8_runner, "orbittrace_p3_exact_v8_runner")
    support = old.load_support_module(args.support_source_parts)
    source_args = types.SimpleNamespace(
        candidate_payload=args.candidate_payload,
        baseline_payload=args.baseline_payload,
        scorer_parts=args.scorer_parts,
    )
    _, base, _ = support.load_sources(source_args)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    scan_by_year, _, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")

    order = [str(f["family_id"]) for f in baseline_families]
    require(len(order) == EXPECTED_FAMILY_COUNT and len(set(order)) == EXPECTED_FAMILY_COUNT, "v8 order invalid")
    v8.mult.YEARS = YEARS
    v8.mult.TOP_K = 100
    baseline = v8.mult.evaluate_order(hidden_labels, baseline_families, order)
    p3 = v8.mult.evaluate_order(hidden_labels, p3_families, order)

    require(int(baseline["qualified_matches"]) == V8_QUALIFIED, "v8 qualified baseline mismatch")
    require(int(baseline["recovered_at_100"]) == V8_RECOVERY100, "v8 recovery baseline mismatch")
    require(abs(float(baseline["mrr"]) - V8_MRR) <= 1e-15, "v8 MRR baseline mismatch")
    require(abs(float(baseline["top100_dominant_precision"]) - V8_TOP100_PRECISION) <= 1e-12, "v8 precision baseline mismatch")
    require(abs(float(baseline["macro_f1"]) - V8_MACRO_F1) <= 1e-12, "v8 macro-F1 baseline mismatch")

    totals = label_totals(hidden_labels, v8.mult)
    large_labels = {
        str(row["label"])
        for row in baseline["per_label"]
        if bool(row.get("qualified", False)) and totals.get(str(row["label"]), 0) >= LARGE_TOTAL_MIN
    }
    require(bool(large_labels), "empty frozen large-shower subset")
    baseline_large = large_summary(baseline, totals, large_labels)
    p3_large = large_summary(p3, totals, large_labels)

    gates = {
        "exact_v8_226_family_order": len(p3_families) == EXPECTED_FAMILY_COUNT
        and [str(f["family_id"]) for f in p3_families] == order,
        "exact_v8_seed_members_preserved": all(
            set(map(str, b["event_ids"])).issubset(set(map(str, x["event_ids"])))
            for b, x in zip(baseline_families, p3_families)
        ),
        "exact_p1_pretruth_identity": p1_expected == P1_PRETRUTH_SHA256,
        "exact_p2_pretruth_payload_hash_verified": canonical_sha(p2) == p2_expected,
        "same_family_intersection_only": consensus_audit["consensus_operator"] == "exact same-family stable-event-ID intersection only",
        "p3_nonseed_unique": consensus_audit["p3_nonseed_unique"] is True,
        "membership_frozen_before_truth_evaluation": len(p3_sha) == 64,
        "expansion_nonvacuous": int(consensus_audit["p3_same_family_intersection_total"]) > 0,
        "qualified_matches_no_regression": int(p3["qualified_matches"]) >= V8_QUALIFIED,
        "recovery_at_100_no_regression": int(p3["recovered_at_100"]) >= V8_RECOVERY100,
        "top100_dominant_precision_at_least_065": float(p3["top100_dominant_precision"]) >= TOP100_PRECISION_MIN,
        "macro_f1_gain_at_least_008": float(p3["macro_f1"]) >= MACRO_F1_MIN,
        "large_shower_mean_recall_at_least_15x_v8": float(p3_large["mean_recall"]) >= LARGE_RECALL_MULTIPLIER * float(baseline_large["mean_recall"]),
        "large_shower_mean_precision_at_least_085": float(p3_large["mean_precision"]) >= LARGE_PRECISION_MIN,
    }
    verdict = "PASS_DUAL_MEMBERSHIP_CONSENSUS_P3_DEVELOPMENT" if all(gates.values()) else "FAIL_DUAL_MEMBERSHIP_CONSENSUS_P3_NO_GO"

    result = {
        "verdict": verdict,
        "classification": "exact same-family intersection of frozen P1 and frozen P2 nonseed assignments on immutable promoted-v8 cores/rank",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "family_count": EXPECTED_FAMILY_COUNT,
            "consensus_operator": "same-family exact event-ID intersection",
            "new_scores": False,
            "new_fitted_parameters": False,
            "new_thresholds": False,
            "ranking_after_membership": "unchanged exact promoted-v8 multiplicity order",
            "parameter_search": False,
        },
        "sources": sources,
        "parent_pretruth_sha256": {"p1": p1_expected, "p2": p2_expected},
        "membership_pretruth_sha256": p3_sha,
        "baseline_v8": {k: v for k, v in baseline.items() if k != "per_label"},
        "p3": {k: v for k, v in p3.items() if k != "per_label"},
        "baseline_large_shower": baseline_large,
        "p3_large_shower": p3_large,
        "consensus_audit": consensus_audit,
        "gates": gates,
        "claim_boundary": "Target-excluded development only; P3 requires frozen matched-literature superiority and no-retuning external validation before any target-containing deployment.",
    }
    (args.output / "dual_membership_consensus_p3_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    summary = (
        "# OrbitTrace P3 dual-membership consensus development\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- v8 -> P3 macro F1: **{baseline['macro_f1']:.6f} -> {p3['macro_f1']:.6f}**\n"
        f"- v8 -> P3 qualified: **{baseline['qualified_matches']} -> {p3['qualified_matches']}**\n"
        f"- v8 -> P3 recovery@100: **{baseline['recovered_at_100']} -> {p3['recovered_at_100']}**\n"
        f"- v8 -> P3 top-100 precision: **{baseline['top100_dominant_precision']:.6f} -> {p3['top100_dominant_precision']:.6f}**\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p3_large['mean_recall']:.6f}**\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p3_large['mean_precision']:.6f}**\n"
        f"- P1 additions: **{consensus_audit['p1_added_total']:,}**; P2 additions: **{consensus_audit['p2_added_total']:,}**; consensus additions: **{consensus_audit['p3_same_family_intersection_total']:,}**\n"
        f"- P3 pretruth SHA-256: `{p3_sha}`\n\n"
        "No target-region event or OrbitTrace target information was used.\n"
    )
    (args.output / "DUAL_MEMBERSHIP_CONSENSUS_P3_DEVELOPMENT.md").write_text(summary)
    print(summary, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
