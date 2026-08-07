#!/usr/bin/env python3
"""Prospectively evaluate sparse-support multiplicity v5 on blinded GMN 2020-2021."""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from scipy.stats import spearmanr

import multi_anchor_energy_v3 as v3
import wavelet_episode_comparator as brown

YEARS = (2020, 2021)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
EPISODE_SIZE = 128
BROWN_EQ_TOL = 1e-10
EXPECTED_SUPPORT_YEARS = (2022, 2023, 2024, 2025)
EXPECTED_SUPPORT_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
MIN_SUPPORTED_BINS = 24
MIN_FAMILIES = 100
MIN_QUALIFIED = 30
TOP_K = 100


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--factorization-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_frozen_runtime() -> Any:
    path = Path("/tmp/run_wavelet_catalogue_v3_development.py")
    require(path.is_file(), "frozen catalogue-v3 runtime was not decoded")
    spec = importlib.util.spec_from_file_location("multiplicity_v5_frozen_runtime", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    require(tuple(module.YEARS) == (2022, 2023), "frozen wavelet runtime source years changed")
    require(float(module.WINDOW_WIDTH_DEG) == 10.0, "frozen local-window width changed")
    require(int(module.EPISODE_SIZE) == EPISODE_SIZE, "frozen local episode size changed")
    return module


def score_episode(episode: Any) -> tuple[float, float, float, float]:
    details = v3.episode_score_details(episode)
    v3_score = float(details["score"])
    brown_from_v3 = float(details["brown_peak"])
    independent_brown = float(brown.wavelet_episode_score(episode))
    difference = abs(brown_from_v3 - independent_brown)
    require(difference <= BROWN_EQ_TOL, f"Brown comparator mismatch: {difference}")
    require(math.isfinite(v3_score) and math.isfinite(independent_brown), "non-finite episode score")
    require(independent_brown > 0.0, "Brown peak must be positive for multiplicity factorization")
    multiplicity = (v3_score / independent_brown) ** 2
    require(1.0 - 1e-10 <= multiplicity <= 4.0 + 1e-10, f"multiplicity outside [1,4]: {multiplicity}")
    return v3_score, independent_brown, multiplicity, difference


def build_local_episode(
    family: dict[str, Any],
    year: int,
    scan_events: list[dict[str, Any]],
    runtime: Any,
    base: Any,
) -> tuple[Any, dict[str, Any]]:
    centroid = family.get("centroids", {}).get(str(year))
    require(centroid is not None, f"family {family['family_id']} missing centroid for {year}")
    center_sol = float(centroid["sol"])
    window_events = runtime.window_events_for_center(scan_events, center_sol, base)
    require(
        len(window_events) >= EPISODE_SIZE,
        f"family {family['family_id']} year {year} has only {len(window_events)} events in local window",
    )
    anchor = {
        "sol": center_sol,
        "sun_lon": float(centroid["sun_lon"]),
        "ecl_lat": float(centroid["ecl_lat"]),
        "vg": float(centroid["vg"]),
    }
    distances = runtime.exact_wavelet_r2(anchor, window_events)
    selected = runtime.stable_smallest_indices(distances, EPISODE_SIZE)
    chosen = [window_events[int(index)] for index in selected]
    episode = SimpleNamespace(
        sun_lon=np.asarray([float(event["sun_lon"]) for event in chosen], dtype=np.float64),
        ecl_lat=np.asarray([float(event["ecl_lat"]) for event in chosen], dtype=np.float64),
        vg=np.asarray([float(event["vg"]) for event in chosen], dtype=np.float64),
    )
    return episode, {
        "window_event_count": len(window_events),
        "episode_size": len(chosen),
        "selected_max_r2": float(np.max(distances[selected])),
        "centroid": anchor,
    }


def score_families(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    runtime: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    max_difference = 0.0
    episode_sizes: list[int] = []
    multiplicities: list[float] = []
    for index, family in enumerate(families, start=1):
        require(sorted(int(y) for y in family["years"]) == list(YEARS), f"family years changed: {family['family_id']}")
        per_year: dict[str, Any] = {}
        for year in YEARS:
            episode, metadata = build_local_episode(family, year, scan_by_year[year], runtime, base)
            v3_score, brown_score, multiplicity, difference = score_episode(episode)
            max_difference = max(max_difference, difference)
            episode_sizes.append(int(metadata["episode_size"]))
            multiplicities.append(multiplicity)
            per_year[str(year)] = {
                **metadata,
                "v3_score": v3_score,
                "brown_score": brown_score,
                "multiplicity": multiplicity,
                "brown_equivalence_difference": difference,
            }
        ms = [float(per_year[str(year)]["multiplicity"]) for year in YEARS]
        vs = [float(per_year[str(year)]["v3_score"]) for year in YEARS]
        bs = [float(per_year[str(year)]["brown_score"]) for year in YEARS]
        rows.append({
            "family_id": str(family["family_id"]),
            "per_year": per_year,
            "multiplicity_worst_year": min(ms),
            "multiplicity_geometric_mean": math.sqrt(ms[0] * ms[1]),
            "v3_min_year_score": min(vs),
            "brown_min_year_score": min(bs),
        })
        if index % 25 == 0 or index == len(families):
            print(f"multiplicity-v5 scoring {index}/{len(families)}", flush=True)
    return rows, {
        "families_requested": len(families),
        "families_scored": len(rows),
        "episode_count": len(episode_sizes),
        "episode_sizes": sorted(set(episode_sizes)),
        "max_brown_equivalence_difference": max_difference,
        "multiplicity_distribution": {
            "min": float(np.min(multiplicities)) if multiplicities else None,
            "p05": float(np.quantile(multiplicities, 0.05)) if multiplicities else None,
            "median": float(np.median(multiplicities)) if multiplicities else None,
            "p95": float(np.quantile(multiplicities, 0.95)) if multiplicities else None,
            "max": float(np.max(multiplicities)) if multiplicities else None,
        },
    }


def rank_scored(scored: list[dict[str, Any]], method: str) -> list[str]:
    if method == "multiplicity":
        ordered = sorted(
            scored,
            key=lambda row: (
                -float(row["multiplicity_worst_year"]),
                -float(row["multiplicity_geometric_mean"]),
                str(row["family_id"]),
            ),
        )
    elif method == "v3":
        ordered = sorted(scored, key=lambda row: (-float(row["v3_min_year_score"]), str(row["family_id"])))
    elif method == "brown":
        ordered = sorted(scored, key=lambda row: (-float(row["brown_min_year_score"]), str(row["family_id"])))
    else:
        raise ValueError(method)
    return [str(row["family_id"]) for row in ordered]


def eligible_labels(hidden_labels: dict[str, str]) -> dict[str, Counter[int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for event_id, label in hidden_labels.items():
        year = int(str(event_id)[:4])
        if year in YEARS and label != "SPORADIC":
            counts[label][year] += 1
    return {
        label: per_year
        for label, per_year in counts.items()
        if sum(per_year.values()) >= 8 and all(per_year.get(year, 0) >= 4 for year in YEARS)
    }


def evaluate_order(
    hidden_labels: dict[str, str],
    families: list[dict[str, Any]],
    order: list[str],
) -> dict[str, Any]:
    family_by_id = {str(family["family_id"]): family for family in families}
    require(set(order) == set(family_by_id) and len(order) == len(family_by_id), "ranking universe mismatch")
    eligible = eligible_labels(hidden_labels)
    rank_map = {family_id: rank for rank, family_id in enumerate(order, start=1)}

    dominant_precision: dict[str, float] = {}
    for family_id, family in family_by_id.items():
        counts = Counter(hidden_labels.get(event_id, "SPORADIC") for event_id in family["event_ids"])
        counts.pop("SPORADIC", None)
        dominant = counts.most_common(1)[0][1] if counts else 0
        dominant_precision[family_id] = dominant / int(family["event_count"]) if family["event_count"] else 0.0

    qualified = 0
    ranks: list[int] = []
    f1s: list[float] = []
    recovered100 = 0
    recovered500 = 0
    per_label: list[dict[str, Any]] = []
    for label in sorted(eligible):
        total = int(sum(eligible[label].values()))
        matches: list[tuple[float, float, int, str]] = []
        for family_id, family in family_by_id.items():
            overlap = sum(hidden_labels.get(event_id) == label for event_id in family["event_ids"])
            if overlap < 4:
                continue
            precision = overlap / int(family["event_count"])
            recall = overlap / total
            f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
            matches.append((f1, precision, overlap, family_id))
        if not matches:
            per_label.append({"label": label, "rank": None, "qualified": False})
            continue
        f1, precision, overlap, family_id = max(matches, key=lambda item: (item[0], item[1], item[2], item[3]))
        rank = rank_map[family_id]
        is_qualified = bool(precision >= 0.5 and overlap >= 4)
        if is_qualified:
            qualified += 1
            ranks.append(rank)
            f1s.append(f1)
            recovered100 += int(rank <= TOP_K)
            recovered500 += int(rank <= 500)
        per_label.append({
            "label": label,
            "rank": rank,
            "qualified": is_qualified,
            "family_id": family_id,
            "overlap": int(overlap),
            "precision": float(precision),
            "recall": float(overlap / total),
            "f1": float(f1),
        })

    top100 = order[:TOP_K]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": qualified,
        "recovered_at_100": recovered100,
        "recovered_at_500": recovered500,
        "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
        "median_rank": float(np.median(ranks)) if ranks else None,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "top100_dominant_precision": float(np.mean([dominant_precision[fid] for fid in top100])) if top100 else 0.0,
        "per_label": per_label,
    }


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "per_label"}


def rank_spearman(a: list[str], b: list[str]) -> float:
    require(set(a) == set(b), "Spearman ranking universe mismatch")
    universe = sorted(a)
    ra = {fid: rank for rank, fid in enumerate(a, 1)}
    rb = {fid: rank for rank, fid in enumerate(b, 1)}
    return float(spearmanr([ra[fid] for fid in universe], [rb[fid] for fid in universe]).statistic)


def overlap100(a: list[str], b: list[str]) -> int:
    return len(set(a[:TOP_K]) & set(b[:TOP_K]))


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source_audit = json.loads(args.source_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_MULTIPLICITY_V5_SUPPORT_SOURCE_AUDIT", "support source audit did not pass")
    require(source_audit["support_sha256"] == EXPECTED_SUPPORT_SHA256, "support source hash changed")
    require(tuple(source_audit["constants"]["YEARS"]) == EXPECTED_SUPPORT_YEARS, "audited support source years changed")
    require(source_audit["catalogue_access"] is False, "source audit unexpectedly accessed catalogue")

    factorization = json.loads(args.factorization_json.read_text())
    require(factorization["verdict"] == "V3_NON_BROWN_TERM_RETAINS_EXPLORATORY_RANKING_SIGNAL", "factorization diagnostic did not support successor")
    require(factorization["blindness"]["catalogue_access"] is False, "factorization diagnostic unexpectedly accessed catalogue")
    require(factorization["evaluations"]["multiplicity"]["recovered_at_100"] == 60, "factorization development result changed")
    require(factorization["evaluations"]["brown"]["recovered_at_100"] == 54, "Brown development result changed")
    require(factorization["evaluations"]["fixed4"]["recovered_at_100"] == 61, "fixed4 development result changed")

    require(all(v3.self_test().values()), "frozen multi-anchor v3 self-test failed")
    require(all(brown.self_test().values()), "frozen Brown comparator self-test failed")
    runtime = load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(tuple(support.YEARS) == EXPECTED_SUPPORT_YEARS, "support source initial year universe changed")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "minimum family years changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")

    # This is the only temporal change to the immutable scanner. It occurs before
    # the first catalogue call and changes no detector, calibration, or ranking constant.
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    require(tuple(support.YEARS) == YEARS and tuple(support.MONTH_KEYS) == MONTH_KEYS, "holdout temporal substitution failed")

    # load_sources expects this legacy argument to exist; it is not used to select
    # any scientific result in this successor.
    setattr(args, "fixed4_baseline_json", args.factorization_json)
    _candidate, base, scorer = support.load_sources(args)

    # FIRST HOLDOUT DATA ACCESS occurs here, after every method/gate above is fixed.
    scan_by_year, calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "holdout scan-year universe changed")
    require(sorted(calibration_by_year) == list(YEARS), "holdout calibration-year universe changed")
    require([source["key"] for source in catalogue_sources] == list(MONTH_KEYS), "holdout monthly source universe changed")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = support.scan_year(
            year,
            scan_by_year[year],
            calibration_by_year[year],
            _candidate,
            base,
            scorer,
        )
        scan_audits.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)
        print(
            f"multiplicity-v5 fixed4 proposals {year}: components={len(year_components)} retained_quartets={len(passing)}",
            flush=True,
        )

    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(fid) for fid in support_rankings["persistence"]]
    family_ids = [str(family["family_id"]) for family in families]
    require(set(persistence_order) == set(family_ids) and len(persistence_order) == len(family_ids), "fixed4 persistence universe mismatch")

    scored, scoring_summary = score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every recurrent family received a multiplicity score")
    multiplicity_order = rank_scored(scored, "multiplicity")
    brown_order = rank_scored(scored, "brown")
    v3_order = rank_scored(scored, "v3")
    rankings = {
        "multiplicity": multiplicity_order,
        "brown": brown_order,
        "v3": v3_order,
        "fixed4_persistence": persistence_order,
    }

    # Labels are first consulted for ranking evaluation only after every order exists.
    metrics_full = {
        name: evaluate_order(hidden_labels, families, order)
        for name, order in rankings.items()
    }
    metrics = {name: compact(value) for name, value in metrics_full.items()}

    correlations = {
        "multiplicity_brown_spearman": rank_spearman(multiplicity_order, brown_order),
        "multiplicity_v3_spearman": rank_spearman(multiplicity_order, v3_order),
        "multiplicity_fixed4_spearman": rank_spearman(multiplicity_order, persistence_order),
    }
    overlaps = {
        "multiplicity_brown_top100": overlap100(multiplicity_order, brown_order),
        "multiplicity_v3_top100": overlap100(multiplicity_order, v3_order),
        "multiplicity_fixed4_top100": overlap100(multiplicity_order, persistence_order),
    }

    supported_bins_ok = all(len(audit["supported_bins"]) >= MIN_SUPPORTED_BINS for audit in scan_audits)
    exact_family_years = all(sorted(int(year) for year in family["years"]) == list(YEARS) for family in families)
    exact_episode_sizes = scoring_summary["episode_sizes"] == [EPISODE_SIZE] if families else False
    same_qualified = len({metrics[name]["qualified_matches"] for name in metrics}) == 1
    qualified_count = metrics["multiplicity"]["qualified_matches"]

    validity_gates = {
        "source_and_self_test_guards": True,
        "exact_2020_2021_temporal_substitution": tuple(support.YEARS) == YEARS and tuple(support.MONTH_KEYS) == MONTH_KEYS,
        "exact_24_monthly_sources": len(catalogue_sources) == 24 and [source["key"] for source in catalogue_sources] == list(MONTH_KEYS),
        "blind_exclusion_before_labels_guarded_by_frozen_source": float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0,
        "at_least_24_supported_fixed4_bins_each_year": supported_bins_ok,
        "all_recurrent_families_have_both_years": exact_family_years,
        "all_local_episode_sizes_exact_128": exact_episode_sizes,
        "brown_equivalence_within_1e_10_everywhere": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "at_least_30_qualified_known_showers": qualified_count >= MIN_QUALIFIED and same_qualified,
    }

    fixed4_recovery = int(metrics["fixed4_persistence"]["recovered_at_100"])
    multiplicity_recovery = int(metrics["multiplicity"]["recovered_at_100"])
    brown_recovery = int(metrics["brown"]["recovered_at_100"])
    required_vs_fixed4 = int(math.ceil(0.90 * fixed4_recovery))
    scientific_gates = {
        "multiplicity_recovers_at_least_one_more_than_brown": multiplicity_recovery >= brown_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_fixed4": multiplicity_recovery >= required_vs_fixed4,
        "multiplicity_top100_precision_at_least_050": float(metrics["multiplicity"]["top100_dominant_precision"]) >= 0.50,
    }

    if not all(validity_gates.values()):
        if not validity_gates["at_least_100_recurrent_families"] or not validity_gates["at_least_30_qualified_known_showers"]:
            verdict = "INCONCLUSIVE_MULTIPLICITY_V5_HOLDOUT_POWER"
        else:
            verdict = "FAIL_MULTIPLICITY_V5_HOLDOUT_INTEGRITY"
    elif all(scientific_gates.values()):
        verdict = "PASS_MULTIPLICITY_V5_TARGET_EXCLUDED_HOLDOUT"
    else:
        verdict = "FAIL_MULTIPLICITY_V5_TARGET_EXCLUDED_HOLDOUT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(MONTH_KEYS),
            "blind_exclusion": [20.0, 55.0],
            "proposal_generator": "exact frozen fixed4 support-normalized scanner",
            "support_source_sha256": EXPECTED_SUPPORT_SHA256,
            "primary_ranking": "min per-year multiplicity descending, geometric-mean multiplicity descending, family id",
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "episode_size": EPISODE_SIZE,
            "top_k": TOP_K,
            "no_multiplicity_pvalue": True,
            "no_rrf": True,
            "no_threshold_search": True,
            "no_weight_search": True,
        },
        "catalogue_sources": catalogue_sources,
        "fixed4_scan_audits": scan_audits,
        "passing_quartet_counts": passing_counts,
        "family_count": len(families),
        "family_scoring_summary": scoring_summary,
        "metrics": metrics,
        "correlations": correlations,
        "top100_overlaps": overlaps,
        "validity_gates": validity_gates,
        "scientific_gates": scientific_gates,
        "required_multiplicity_recovery_vs_fixed4": required_vs_fixed4,
        "claim_boundary": (
            "Prospectively preregistered target-excluded GMN 2020-2021 holdout. "
            "No event with solar longitude 20-55 degrees and no OrbitTrace target information entered the method. "
            "A pass freezes the ranking architecture but does not authorize target access until a separate final discovery protocol is committed."
        ),
    }
    (args.output / "multiplicity_v5_holdout.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "multiplicity_v5_rankings.json").write_text(json.dumps(rankings, indent=2) + "\n")
    (args.output / "multiplicity_v5_family_scores.json.gz").write_bytes(
        gzip.compress(json.dumps(scored, separators=(",", ":")).encode())
    )
    (args.output / "multiplicity_v5_families.json.gz").write_bytes(
        gzip.compress(json.dumps(families, separators=(",", ":")).encode())
    )
    (args.output / "multiplicity_v5_evaluation.json.gz").write_bytes(
        gzip.compress(json.dumps(metrics_full, separators=(",", ":")).encode())
    )

    lines = [
        "# OrbitTrace sparse-support multiplicity v5 holdout",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- recurrent fixed4 families: **{len(families)}**",
        f"- qualified known showers: **{qualified_count}**",
        f"- multiplicity recovered@100: **{multiplicity_recovery}**; precision: **{metrics['multiplicity']['top100_dominant_precision']:.4f}**",
        f"- Brown recovered@100: **{brown_recovery}**; precision: **{metrics['brown']['top100_dominant_precision']:.4f}**",
        f"- total-v3 recovered@100: **{metrics['v3']['recovered_at_100']}**; precision: **{metrics['v3']['top100_dominant_precision']:.4f}**",
        f"- fixed4 persistence recovered@100: **{fixed4_recovery}**; precision: **{metrics['fixed4_persistence']['top100_dominant_precision']:.4f}**",
        f"- required multiplicity recovery for 90% fixed4 gate: **{required_vs_fixed4}**",
        f"- multiplicity vs fixed4 rank Spearman: **{correlations['multiplicity_fixed4_spearman']:.4f}**",
        f"- maximum Brown-equivalence difference: **{scoring_summary['max_brown_equivalence_difference']:.3e}**",
        "",
        "The 20°–55° solar-longitude interval remained excluded before labels and was not accessed by this method.",
    ]
    (args.output / "MULTIPLICITY_V5_HOLDOUT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
