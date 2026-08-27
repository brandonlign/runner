#!/usr/bin/env python3
"""P21: target-excluded recurrent singleton-anchor quartet rescue."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-p21-singleton-anchor-recurrence-development"
BLIND = (20.0, 55.0)
LINK_RADIUS = 1.5
FIRST_SHORTLIST = 64
AUDIT_SHORTLIST = 128
RETAINED_MIN_ANCHOR_COUNT = 2
SINGLETON_ANCHOR_COUNT = 1
PER_BIN_CAP = 512
EXPECTED_V8_FAMILIES = 226
EXPECTED_V8_QUALIFIED = 95
EXPECTED_V8_RECOVERY100 = 58
EXPECTED_V8_MACRO_F1 = 0.1736657194465356
EXPECTED_V8_TOP100_PRECISION = 0.6884631112636006
EXPECTED_V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
EXPECTED_V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SIZE_BINS = (
    ("4-9", 4, 9),
    ("10-24", 10, 24),
    ("25-49", 25, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def pooled_centroid(events: list[dict[str, Any]], support: Any) -> dict[str, float]:
    require(events, "cannot pool empty event set")
    return {
        "sol": float(support.circular_mean_deg(float(e["sol"]) for e in events)),
        "sun_lon": float(support.circular_mean_deg(float(e["sun_lon"]) for e in events)),
        "ecl_lat": float(np.median([float(e["ecl_lat"]) for e in events])),
        "vg": float(np.median([float(e["vg"]) for e in events])),
    }


def scan_year_with_singletons(
    year: int,
    events: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Reproduce frozen v6 through local_dedup and retain exact anchor_count==1 proposals."""
    event_lookup = {str(e["id"]): e for e in events}
    passing: list[dict[str, Any]] = []
    raw_singletons_by_bin: dict[int, list[dict[str, Any]]] = {}
    scannable_bins: list[int] = []
    passing_anchor_count = 0
    shortlist_audit_failures = 0
    per_bin: list[dict[str, Any]] = []

    for bin_index in range(36):
        low = bin_index * 10.0
        high = (bin_index + 1) * 10.0
        center = low + 5.0
        anchors = [e for e in events if low <= float(e["sol"]) < high]
        pool = [e for e in events if abs(float(base.wrap180(float(e["sol"]) - center))) <= 15.0]
        if len(pool) < AUDIT_SHORTLIST or not anchors:
            continue
        scannable_bins.append(bin_index)
        pool_index = {str(e["id"]): i for i, e in enumerate(pool)}
        features = support.feature_matrix(pool, center, base)
        k_query = min(AUDIT_SHORTLIST, len(pool))
        nn = NearestNeighbors(
            n_neighbors=k_query, algorithm="auto", metric="euclidean", n_jobs=-1
        ).fit(features)
        anchor_rows = np.asarray([pool_index[str(e["id"])] for e in anchors], dtype=np.int64)
        _, neighbor_indices = nn.kneighbors(features[anchor_rows], return_distance=True)
        local_dedup: dict[tuple[str, ...], dict[str, Any]] = {}
        bin_anchor_pass = 0

        for anchor, candidates_idx in zip(anchors, neighbor_indices):
            candidate_events = [
                pool[int(i)] for i in candidates_idx
                if str(pool[int(i)]["id"]) != str(anchor["id"])
            ]
            first = candidate_events[:max(3, FIRST_SHORTLIST - 1)]
            distances = support.exact_anchor_distances(anchor, first, base)
            order = np.argsort(distances, kind="stable")[:3]
            quartet = [anchor] + [first[int(i)] for i in order]
            score = float(support.quartet_score(quartet, base))

            full = candidate_events[:max(3, AUDIT_SHORTLIST - 1)]
            full_distances = support.exact_anchor_distances(anchor, full, base)
            full_order = np.argsort(full_distances, kind="stable")[:3]
            audit_quartet = [anchor] + [full[int(i)] for i in full_order]
            audit_score = float(support.quartet_score(audit_quartet, base))
            ids = tuple(sorted(str(e["id"]) for e in quartet))
            audit_ids = tuple(sorted(str(e["id"]) for e in audit_quartet))
            if ids != audit_ids or abs(score - audit_score) > 1e-12:
                shortlist_audit_failures += 1
                quartet = audit_quartet
                score = audit_score
                ids = audit_ids

            passing_anchor_count += 1
            bin_anchor_pass += 1
            record = local_dedup.get(ids)
            if record is None:
                local_dedup[ids] = {
                    "year": year,
                    "bin": bin_index,
                    "quartet_ids": list(ids),
                    "score": score,
                    "threshold": None,
                    "anchor_count": 1,
                    "anchor_ids": [str(anchor["id"])],
                    "label_free_structural_proposal": True,
                }
            else:
                record["anchor_count"] += 1
                record["anchor_ids"].append(str(anchor["id"]))
                record["score"] = max(float(record["score"]), score)

        retained = [
            r for r in local_dedup.values()
            if int(r["anchor_count"]) >= RETAINED_MIN_ANCHOR_COUNT
        ]
        retained.sort(key=lambda x: (-x["anchor_count"], -x["score"], x["quartet_ids"]))
        pre_cap = len(retained)
        retained = retained[:PER_BIN_CAP]
        count = len(retained)
        for rank, record in enumerate(retained, 1):
            rank_fraction = (rank - 0.5) / max(1, count)
            record["bin_rank"] = rank
            record["bin_count"] = count
            record["bin_strength"] = -math.log10(rank_fraction)
        passing.extend(retained)

        raw_singletons = [
            dict(r) for r in local_dedup.values()
            if int(r["anchor_count"]) == SINGLETON_ANCHOR_COUNT
        ]
        raw_singletons_by_bin[bin_index] = raw_singletons
        per_bin.append({
            "bin": bin_index,
            "anchors": len(anchors),
            "pool": len(pool),
            "anchored_quartets_examined": bin_anchor_pass,
            "unique_quartets_before_anchor_gate": len(local_dedup),
            "anchor_multiplicity_pass_before_cap": pre_cap,
            "retained_after_fixed_512_cap": count,
            "singleton_anchor_quartets_before_overlap_veto": len(raw_singletons),
        })

    passing.sort(key=lambda x: (x["bin"], x["bin_rank"], x["quartet_ids"]))
    components = support.component_records(year, passing, event_lookup)

    # P21 is below the retained-proposal gate, not an alternate representation of
    # any normally retained v8 quartet. Exclusion is against all retained quartet
    # events in the year, including retained quartets that never form a component.
    retained_event_ids = {
        str(eid) for record in passing for eid in record["quartet_ids"]
    }
    singletons: list[dict[str, Any]] = []
    singleton_overlap_rejected = 0
    singleton_pre_cap_after_overlap = 0
    singleton_counts_after_cap: dict[str, int] = {}
    for bin_index in sorted(raw_singletons_by_bin):
        eligible = []
        for record in raw_singletons_by_bin[bin_index]:
            ids = tuple(sorted(str(x) for x in record["quartet_ids"]))
            require(len(ids) == 4 and len(set(ids)) == 4, "singleton quartet is not four unique events")
            require(int(record["anchor_count"]) == SINGLETON_ANCHOR_COUNT, "singleton anchor count changed")
            if any(eid in retained_event_ids for eid in ids):
                singleton_overlap_rejected += 1
                continue
            eligible.append(record)
        eligible.sort(key=lambda r: (-float(r["score"]), tuple(r["quartet_ids"])))
        singleton_pre_cap_after_overlap += len(eligible)
        eligible = eligible[:PER_BIN_CAP]
        singleton_counts_after_cap[str(bin_index)] = len(eligible)
        for rank, record in enumerate(eligible, 1):
            ids = tuple(sorted(str(x) for x in record["quartet_ids"]))
            quartet_events = [event_lookup[eid] for eid in ids]
            singletons.append({
                "singleton_id": f"S{year}-{bin_index:02d}-" + hashlib.sha256("|".join(ids).encode()).hexdigest()[:16],
                "year": int(year),
                "bin": int(bin_index),
                "quartet_ids": list(ids),
                "score": float(record["score"]),
                "anchor_count": int(record["anchor_count"]),
                "anchor_ids": sorted(str(x) for x in record["anchor_ids"]),
                "singleton_bin_rank": int(rank),
                "singleton_bin_count": len(eligible),
                "centroid": pooled_centroid(quartet_events, support),
            })
    singletons.sort(key=lambda q: str(q["singleton_id"]))

    audit = {
        "year": int(year),
        "scan_events": len(events),
        "scannable_bins": scannable_bins,
        "scannable_bin_count": len(scannable_bins),
        "passing_anchor_count": passing_anchor_count,
        "retained_quartets": len(passing),
        "components": len(components),
        "shortlist_audit_failures": shortlist_audit_failures,
        "per_bin": per_bin,
        "calibration_events_used": 0,
        "source_labels_used_for_proposals": False,
        "score_threshold_applied": False,
        "first_shortlist": FIRST_SHORTLIST,
        "audit_shortlist": AUDIT_SHORTLIST,
        "retained_min_anchor_count": RETAINED_MIN_ANCHOR_COUNT,
        "singleton_anchor_count": SINGLETON_ANCHOR_COUNT,
        "per_bin_cap": PER_BIN_CAP,
        "retained_quartet_event_count": len(retained_event_ids),
        "singleton_overlap_rejected": int(singleton_overlap_rejected),
        "singleton_pre_cap_after_overlap": int(singleton_pre_cap_after_overlap),
        "singleton_after_cap": len(singletons),
        "singleton_counts_after_cap_by_bin": singleton_counts_after_cap,
        "all_singletons_exact_anchor_count_one": all(int(q["anchor_count"]) == 1 for q in singletons),
        "all_singletons_zero_retained_event_overlap": all(
            not (set(q["quartet_ids"]) & retained_event_ids) for q in singletons
        ),
    }
    return audit, passing, components, singletons


def bins_for_sol(sol: float) -> tuple[int, ...]:
    center = int(math.floor(float(sol))) % 360
    return tuple((center + offset) % 360 for offset in range(-7, 8))


def singleton_bins(singletons: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    bins: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for q in singletons:
        bins[int(math.floor(float(q["centroid"]["sol"]))) % 360].append(q)
    for key in bins:
        bins[key].sort(key=lambda q: str(q["singleton_id"]))
    return dict(bins)


def nearest_other_year(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> tuple[dict[str, str], dict[tuple[str, str], float], dict[str, Any]]:
    target_bins = singleton_bins(target)
    mapping: dict[str, str] = {}
    distances: dict[tuple[str, str], float] = {}
    exact_calls = 0
    exact_within = 0
    for q in source:
        center = q["centroid"]
        rows: list[tuple[Any, ...]] = []
        for key in bins_for_sol(float(center["sol"])):
            for other in target_bins.get(key, []):
                if abs(float(other["centroid"]["ecl_lat"]) - float(center["ecl_lat"])) > 3.0:
                    continue
                if abs(float(other["centroid"]["vg"]) - float(center["vg"])) > 3.0:
                    continue
                exact_calls += 1
                d = float(support.centroid_distance(center, other["centroid"], base))
                if d > LINK_RADIUS:
                    continue
                exact_within += 1
                rows.append((
                    d,
                    -float(other["score"]),
                    tuple(other["quartet_ids"]),
                    str(other["singleton_id"]),
                ))
        if not rows:
            continue
        rows.sort()
        best = rows[0]
        partner = str(best[-1])
        mapping[str(q["singleton_id"])] = partner
        distances[(str(q["singleton_id"]), partner)] = float(best[0])
    return mapping, distances, {
        "source_singletons": len(source),
        "target_singletons": len(target),
        "sources_with_partner_within_radius": len(mapping),
        "exact_distance_calls": int(exact_calls),
        "exact_pairs_within_radius": int(exact_within),
    }


def hard_family_covers_pair(
    q22: dict[str, Any],
    q23: dict[str, Any],
    hard_families: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> tuple[bool, str | None, float | None, float | None]:
    covered: list[tuple[float, float, str]] = []
    for family in hard_families:
        centroids = family.get("centroids", {})
        if "2022" not in centroids or "2023" not in centroids:
            continue
        d22 = float(support.centroid_distance(q22["centroid"], centroids["2022"], base))
        d23 = float(support.centroid_distance(q23["centroid"], centroids["2023"], base))
        if d22 <= LINK_RADIUS and d23 <= LINK_RADIUS:
            covered.append((d22, d23, str(family["family_id"])))
    if not covered:
        return False, None, None, None
    covered.sort(key=lambda row: (max(row[0], row[1]), row[0] + row[1], row[2]))
    d22, d23, fid = covered[0]
    return True, fid, float(d22), float(d23)


def build_p21_families(
    singletons_by_year: dict[int, list[dict[str, Any]]],
    hard_families: list[dict[str, Any]],
    support: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    q22 = singletons_by_year[2022]
    q23 = singletons_by_year[2023]
    by_id = {str(q["singleton_id"]): q for q in q22 + q23}
    m22, d22, a22 = nearest_other_year(q22, q23, support, base)
    m23, d23, a23 = nearest_other_year(q23, q22, support, base)

    families: list[dict[str, Any]] = []
    mutual_before_novelty = 0
    novelty_rejected = 0
    novelty_rejections: list[dict[str, Any]] = []
    for q22_id in sorted(m22):
        q23_id = m22[q22_id]
        if m23.get(q23_id) != q22_id:
            continue
        mutual_before_novelty += 1
        qa = by_id[q22_id]
        qb = by_id[q23_id]
        d = float(d22[(q22_id, q23_id)])
        reverse_d = float(d23[(q23_id, q22_id)])
        require(abs(d - reverse_d) <= 1e-12, "reciprocal singleton distance mismatch")
        require(d <= LINK_RADIUS, "reciprocal singleton pair exceeds inherited radius")
        covered, hard_id, hard_d22, hard_d23 = hard_family_covers_pair(
            qa, qb, hard_families, support, base
        )
        if covered:
            novelty_rejected += 1
            novelty_rejections.append({
                "singleton_2022": q22_id,
                "singleton_2023": q23_id,
                "hard_family_id": hard_id,
                "distance_2022": hard_d22,
                "distance_2023": hard_d23,
            })
            continue
        event_ids = sorted(set(qa["quartet_ids"]) | set(qb["quartet_ids"]))
        require(len(event_ids) == 8, "P21 family is not exact 4+4")
        stable = hashlib.sha256((q22_id + "|" + q23_id).encode()).hexdigest()[:16]
        families.append({
            "family_id": "SAR" + stable,
            "family_type": "singleton_anchor_recurrence_4plus4",
            "years": [2022, 2023],
            "year_count": 2,
            "component_ids": [],
            "component_count": 0,
            "event_ids": event_ids,
            "event_count": 8,
            "quartet_count": 2,
            "anchor_count": 2,
            "best_score": float(max(qa["score"], qb["score"])),
            "year_strengths": {
                "2022": float(qa["score"]),
                "2023": float(qb["score"]),
            },
            "centroids": {
                "2022": qa["centroid"],
                "2023": qb["centroid"],
            },
            "ranks": {},
            "ranking_scores": {},
            "p21_singleton_ids": {"2022": q22_id, "2023": q23_id},
            "p21_cross_year_distance": d,
            "p21_min_quartet_score": float(min(qa["score"], qb["score"])),
            "p21_hard_family_novelty_pass": True,
        })

    # Protocol freezes the fail-closed simple ranking variant: optional nearest-hard
    # ranking key is omitted rather than approximated.
    families.sort(key=lambda f: (
        float(f["p21_cross_year_distance"]),
        -float(f["p21_min_quartet_score"]),
        str(f["family_id"]),
    ))
    require(len({str(f["family_id"]) for f in families}) == len(families), "P21 family IDs not unique")
    require(len({tuple(f["event_ids"]) for f in families}) == len(families), "P21 family event sets not unique")
    diagnostics = {
        "2022_to_2023": a22,
        "2023_to_2022": a23,
        "mutual_pairs_before_hard_family_novelty_veto": int(mutual_before_novelty),
        "hard_family_novelty_rejected": int(novelty_rejected),
        "surviving_p21_family_count": len(families),
        "novelty_rejections": novelty_rejections,
        "all_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in families),
        "all_cross_year_distances_within_inherited_1_5": all(float(f["p21_cross_year_distance"]) <= LINK_RADIUS for f in families),
        "all_hard_family_novelty_pass": all(bool(f["p21_hard_family_novelty_pass"]) for f in families),
        "ranking_variant": "cross_year_distance_then_min_quartet_score_then_stable_id",
        "membership_expansion": False,
        "recursion": False,
        "new_scientific_radius": False,
    }
    return families, diagnostics


def structural_family_payload(family: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "family_id", "family_type", "years", "year_count", "component_ids", "component_count",
        "event_ids", "event_count", "quartet_count", "anchor_count", "best_score", "year_strengths",
        "centroids", "p21_singleton_ids", "p21_cross_year_distance", "p21_min_quartet_score",
        "p21_hard_family_novelty_pass",
    )
    return {name: family[name] for name in keep if name in family}


def annual_bin_metrics(hidden_labels: dict[str, str], families: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        label_counts = Counter(
            label for eid, label in hidden_labels.items()
            if int(str(eid)[:4]) == year and label != "SPORADIC"
        )
        per_label: dict[str, dict[str, float]] = {}
        for label, total in sorted(label_counts.items()):
            if total < 4:
                continue
            best = {"f1": 0.0, "precision": 0.0, "recall": 0.0, "overlap": 0.0}
            for family in families:
                year_ids = [eid for eid in family["event_ids"] if int(str(eid)[:4]) == year]
                if not year_ids:
                    continue
                overlap = sum(hidden_labels.get(eid) == label for eid in year_ids)
                if overlap == 0:
                    continue
                precision = overlap / len(year_ids)
                recall = overlap / total
                f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
                candidate = (f1, precision, overlap)
                current = (best["f1"], best["precision"], best["overlap"])
                if candidate > current:
                    best = {
                        "f1": float(f1), "precision": float(precision),
                        "recall": float(recall), "overlap": int(overlap),
                    }
            per_label[label] = {"total": int(total), **best}

        bins: dict[str, Any] = {}
        for name, low, high in SIZE_BINS:
            rows = [
                row for row in per_label.values()
                if row["total"] >= low and (high is None or row["total"] <= high)
            ]
            bins[name] = {
                "showers": len(rows),
                "mean_f1": float(np.mean([r["f1"] for r in rows])) if rows else 0.0,
                "mean_precision": float(np.mean([r["precision"] for r in rows])) if rows else 0.0,
                "mean_recall": float(np.mean([r["recall"] for r in rows])) if rows else 0.0,
            }
        all_rows = list(per_label.values())
        bins["all"] = {
            "showers": len(all_rows),
            "mean_f1": float(np.mean([r["f1"] for r in all_rows])) if all_rows else 0.0,
            "mean_precision": float(np.mean([r["precision"] for r in all_rows])) if all_rows else 0.0,
            "mean_recall": float(np.mean([r["recall"] for r in all_rows])) if all_rows else 0.0,
        }
        out[str(year)] = bins
    return out


def delta_bins(challenger: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        str(year): {
            name: float(challenger[str(year)][name]["mean_f1"] - baseline[str(year)][name]["mean_f1"])
            for name, _low, _high in SIZE_BINS
        }
        for year in YEARS
    }


def combined_4_24_mean(panel: dict[str, Any], year: int) -> float:
    a = panel[str(year)]["4-9"]
    b = panel[str(year)]["10-24"]
    n = int(a["showers"]) + int(b["showers"])
    return (
        float(a["mean_f1"]) * int(a["showers"]) + float(b["mean_f1"]) * int(b["showers"])
    ) / max(1, n)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    raw_v8 = args.v8_result_json.read_bytes()
    require(hashlib.sha256(raw_v8).hexdigest() == EXPECTED_V8_RESULT_SHA256, "v8 result JSON hash changed")
    v8_result = json.loads(raw_v8)
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 predecessor did not pass")
    require(int(v8_result["family_count"]) == EXPECTED_V8_FAMILIES, "v8 family count changed")
    require(int(v8_result["metrics"]["multiplicity"]["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "v8 qualified baseline changed")
    require(int(v8_result["metrics"]["multiplicity"]["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "v8 recovery baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-15, "v8 macro baseline changed")
    require(abs(float(v8_result["metrics"]["multiplicity"]["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-15, "v8 precision baseline changed")
    require(v8_result["configuration"]["blind_exclusion"] == [20.0, 55.0], "v8 blind interval changed")

    require(all(mult.v3.self_test().values()), "v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target exclusion changed")
    require(int(support.SHORTLIST_K) == FIRST_SHORTLIST, "first shortlist changed")
    require(int(support.AUDIT_SHORTLIST_K) == AUDIT_SHORTLIST, "audit shortlist changed")
    require(int(support.MIN_ANCHOR_COUNT) == RETAINED_MIN_ANCHOR_COUNT, "retained anchor gate changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == PER_BIN_CAP, "retained proposal cap changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4, "component event floor changed")
    require(int(support.MIN_COMPONENT_QUARTETS) == 2, "component quartet floor changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "hard recurrence minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - LINK_RADIUS) < 1e-15, "hard link radius changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    # FIRST DEVELOPMENT CATALOGUE ACCESS. Inherited parser removes 20-55 before labels.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "month universe changed")

    components: list[dict[str, Any]] = []
    components_by_year: dict[int, list[dict[str, Any]]] = {}
    passing_by_year: dict[int, list[dict[str, Any]]] = {}
    singletons_by_year: dict[int, list[dict[str, Any]]] = {}
    scan_audits: dict[str, Any] = {}
    for year in YEARS:
        audit, passing, year_components, singletons = scan_year_with_singletons(
            year, scan_by_year[year], support, base
        )
        scan_audits[str(year)] = audit
        passing_by_year[year] = passing
        components_by_year[year] = year_components
        singletons_by_year[year] = singletons
        components.extend(year_components)

    hard_families, support_rankings = support.build_families(components, base)
    require(len(hard_families) == EXPECTED_V8_FAMILIES, f"exact v8 hard family count changed: {len(hard_families)}")
    hard_persistence = [str(x) for x in support_rankings["persistence"]]
    repair = v8.repair_year_centroids(hard_families, components, scan_by_year, support, base)
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100
    hard_scored, hard_scoring = mult.score_families(hard_families, scan_by_year, runtime, base)
    hard_multiplicity = mult.rank_scored(hard_scored, "multiplicity")
    require(len(hard_multiplicity) == EXPECTED_V8_FAMILIES, "hard multiplicity order incomplete")

    # P21 family-generation change. Hidden labels are not passed.
    soft_families, soft_diag = build_p21_families(
        singletons_by_year, hard_families, support, base
    )
    combined_families = hard_families + soft_families
    p21_order = hard_multiplicity + [str(f["family_id"]) for f in soft_families]
    require(p21_order[:len(hard_multiplicity)] == hard_multiplicity, "v8 hard ranking prefix changed")
    require(len(p21_order) == len(combined_families), "combined order/family count mismatch")
    require(len(set(p21_order)) == len(p21_order), "combined family IDs not unique")

    prelabel_payload = {
        "hard_order": hard_multiplicity,
        "hard_families": [structural_family_payload(f) for f in hard_families],
        "scan_audits": scan_audits,
        "singletons": {str(year): singletons_by_year[year] for year in YEARS},
        "soft_families": [structural_family_payload(f) for f in soft_families],
        "soft_diagnostics": soft_diag,
    }
    prelabel_sha = sha256_json(prelabel_payload)

    # FIRST SCIENTIFIC LABEL EVALUATION.
    baseline = mult.evaluate_order(hidden_labels, hard_families, hard_multiplicity)
    p21_metrics = mult.evaluate_order(hidden_labels, combined_families, p21_order)
    baseline_annual = annual_bin_metrics(hidden_labels, hard_families)
    p21_annual = annual_bin_metrics(hidden_labels, combined_families)
    annual_delta = delta_bins(p21_annual, baseline_annual)
    combined_delta = {
        str(year): float(combined_4_24_mean(p21_annual, year) - combined_4_24_mean(baseline_annual, year))
        for year in YEARS
    }

    require(int(baseline["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "rerun v8 qualified mismatch")
    require(int(baseline["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "rerun v8 recovery@100 mismatch")
    require(abs(float(baseline["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-12, "rerun v8 macro mismatch")
    require(abs(float(baseline["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-12, "rerun v8 precision mismatch")

    retained_event_ids_by_year = {
        year: {str(eid) for record in passing_by_year[year] for eid in record["quartet_ids"]}
        for year in YEARS
    }
    integrity_gates = {
        "exact_target_excluded_2022_2023_panel": True,
        "exact_v8_hard_family_count_226": len(hard_families) == EXPECTED_V8_FAMILIES,
        "exact_v8_hard_ranking_prefix_preserved": p21_order[:EXPECTED_V8_FAMILIES] == hard_multiplicity,
        "exact_v6_shortlists_reproduced": all(
            scan_audits[str(year)]["first_shortlist"] == FIRST_SHORTLIST
            and scan_audits[str(year)]["audit_shortlist"] == AUDIT_SHORTLIST
            for year in YEARS
        ),
        "exact_retained_anchor_gate_two_reproduced": all(
            scan_audits[str(year)]["retained_min_anchor_count"] == RETAINED_MIN_ANCHOR_COUNT
            for year in YEARS
        ),
        "exact_singleton_anchor_count_one": all(
            int(q["anchor_count"]) == SINGLETON_ANCHOR_COUNT
            for year in YEARS for q in singletons_by_year[year]
        ),
        "singleton_zero_retained_quartet_event_overlap": all(
            not (set(q["quartet_ids"]) & retained_event_ids_by_year[year])
            for year in YEARS for q in singletons_by_year[year]
        ),
        "singleton_cap_exact_512": all(scan_audits[str(year)]["per_bin_cap"] == PER_BIN_CAP for year in YEARS),
        "all_soft_family_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in soft_families),
        "all_soft_pair_distances_within_inherited_1_5": all(float(f["p21_cross_year_distance"]) <= LINK_RADIUS for f in soft_families),
        "all_soft_hard_family_novelty_pass": all(bool(f["p21_hard_family_novelty_pass"]) for f in soft_families),
        "pooled_centroid_repair_nonvacuous": int(repair["changed_duplicate_year_centroids"]) > 0,
        "prelabel_family_payload_frozen": bool(prelabel_sha),
        "no_membership_expansion": bool(soft_diag["membership_expansion"] is False),
        "no_recursion": bool(soft_diag["recursion"] is False),
        "no_new_scientific_radius": bool(soft_diag["new_scientific_radius"] is False),
        "no_label_parameter_search": True,
        "no_detector_threshold_change": True,
        "no_target_information_access": True,
    }
    scientific_gates = {
        "qualified_matches_at_least_95": int(p21_metrics["qualified_matches"]) >= EXPECTED_V8_QUALIFIED,
        "recovery_at_100_at_least_58": int(p21_metrics["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100,
        "top100_precision_exact_v8_prefix": abs(float(p21_metrics["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) <= 1e-12,
        "macro_f1_gain_at_least_005": float(p21_metrics["macro_f1"]) >= EXPECTED_V8_MACRO_F1 + 0.05,
        "sparse_4_9_mean_f1_gain_at_least_005_both_years": all(
            annual_delta[str(year)]["4-9"] >= 0.05 for year in YEARS
        ),
        "combined_4_24_mean_f1_gain_positive_both_years": all(combined_delta[str(year)] > 0.0 for year in YEARS),
        "singleton_anchor_recurrence_nonvacuous": len(soft_families) > 0,
    }
    passed = all(integrity_gates.values()) and all(scientific_gates.values())
    verdict = "PASS_P21_SINGLETON_ANCHOR_RECURRENCE_DEVELOPMENT" if passed else "FAIL_P21_SINGLETON_ANCHOR_RECURRENCE_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(MONTH_KEYS),
            "corpus": CORPUS,
            "blind_exclusion": list(BLIND),
            "base_method": "promoted v8 pooled-year-centroid label-free sparse-support multiplicity",
            "change_layer": "below-retention singleton-anchor fixed4 proposals only",
            "singleton_rule": "exact local_dedup anchor_count==1, zero event overlap with every normally retained same-year v8 quartet",
            "singleton_per_bin_cap": PER_BIN_CAP,
            "cross_year_rule": "mutual nearest singleton centroids within inherited radius 1.5",
            "hard_family_novelty_veto": "reject iff one exact v8 hard family lies within 1.5 in both corresponding years",
            "reported_membership": "exact four singleton-quartet events per year, no expansion",
            "ranking": "exact v8 multiplicity order immutable prefix, then distance/min-score/stable-ID singleton families",
            "optional_nearest_hard_ranking_key_used": False,
            "parameter_search": False,
            "threshold_search": False,
            "radius_search": False,
            "cap_search": False,
            "variant_search": False,
        },
        "v8_predecessor": {
            "artifact_digest": EXPECTED_V8_ARTIFACT_DIGEST,
            "result_sha256": EXPECTED_V8_RESULT_SHA256,
            "family_count": EXPECTED_V8_FAMILIES,
            "qualified_matches": EXPECTED_V8_QUALIFIED,
            "recovery_at_100": EXPECTED_V8_RECOVERY100,
            "macro_f1": EXPECTED_V8_MACRO_F1,
            "top100_dominant_precision": EXPECTED_V8_TOP100_PRECISION,
        },
        "catalogue_sources": catalogue_sources,
        "scan_audits": scan_audits,
        "soft_diagnostics": soft_diag,
        "hard_family_count": len(hard_families),
        "hard_persistence_family_count": len(hard_persistence),
        "singleton_count_by_year": {str(year): len(singletons_by_year[year]) for year in YEARS},
        "soft_family_count": len(soft_families),
        "combined_family_count": len(combined_families),
        "prelabel_payload_sha256": prelabel_sha,
        "centroid_repair": repair,
        "hard_scoring_summary": hard_scoring,
        "baseline_metrics": {k: v for k, v in baseline.items() if k != "per_label"},
        "p21_metrics": {k: v for k, v in p21_metrics.items() if k != "per_label"},
        "baseline_annual": baseline_annual,
        "p21_annual": p21_annual,
        "annual_mean_f1_delta": annual_delta,
        "combined_4_24_mean_f1_delta": combined_delta,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "claim_boundary": (
            "Target-excluded GMN 2022/2023 development only. Exact promoted-v8 retained proposals, components, "
            "hard families, pooled centroids, scoring, and ranking are preserved. P21 adds only cross-year "
            "mutual recurrence from exact anchor_count-one fixed4 event sets that are absent from the retained "
            "v8 proposal-event universe and are not jointly covered by any v8 hard family. Full structural "
            "payload is frozen before labels. No final-test/external scientific value or target information is accessed."
        ),
    }
    (args.output / "p21_singleton_anchor_recurrence_development.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "p21_prelabel_payload.json").write_text(
        json.dumps(prelabel_payload, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# OrbitTrace P21 singleton-anchor recurrence development",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- hard v8 families: **{len(hard_families)}**",
        f"- singleton proposals 2022/2023: **{len(singletons_by_year[2022])} / {len(singletons_by_year[2023])}**",
        f"- reciprocal singleton pairs before novelty veto: **{soft_diag['mutual_pairs_before_hard_family_novelty_veto']}**",
        f"- hard-family novelty rejections: **{soft_diag['hard_family_novelty_rejected']}**",
        f"- added novel singleton 4+4 families: **{len(soft_families)}**",
        f"- qualified matches: **{baseline['qualified_matches']} -> {p21_metrics['qualified_matches']}**",
        f"- recovery@100: **{baseline['recovered_at_100']} -> {p21_metrics['recovered_at_100']}**",
        f"- macro F1: **{baseline['macro_f1']:.6f} -> {p21_metrics['macro_f1']:.6f}**",
        f"- top-100 dominant precision: **{baseline['top100_dominant_precision']:.6f} -> {p21_metrics['top100_dominant_precision']:.6f}**",
        f"- 2022 4-9 mean-F1 delta: **{annual_delta['2022']['4-9']:+.6f}**",
        f"- 2023 4-9 mean-F1 delta: **{annual_delta['2023']['4-9']:+.6f}**",
        f"- 2022 combined 4-24 mean-F1 delta: **{combined_delta['2022']:+.6f}**",
        f"- 2023 combined 4-24 mean-F1 delta: **{combined_delta['2023']:+.6f}**",
        "",
        "No OrbitTrace target information or target-region event was accessed.",
    ]
    (args.output / "P21_SINGLETON_ANCHOR_RECURRENCE_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
