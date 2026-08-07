#!/usr/bin/env python3
"""Develop OrbitTrace sparse-support v4 on target-excluded 2022-2023 only."""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

import numpy as np

import multi_anchor_energy_v3 as v3
import wavelet_episode_comparator as brown

YEARS = (2022, 2023)
CORPUS = "orbittrace-sparse-support-v4-development"
EPISODE_SIZE = 128
CALIBRATION_PER_BIN = 512
CALIBRATION_DENOMINATOR = 513
RRF_K = 60
BROWN_EQ_TOL = 1e-10
EXPECTED_FAMILY_COUNT = 197
EXPECTED_ELIGIBLE_LABELS = 355
EXPECTED_QUALIFIED_LABELS = 90
FIXED4_RECOVERED100 = 61
FIXED4_QUALIFIED = 90
FIXED4_TOP100_PRECISION = 0.6809376504699393


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support-source-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--fixed4-scaffold-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_frozen_runtime() -> Any:
    path = Path("/tmp/run_wavelet_catalogue_v3_development.py")
    if not path.is_file():
        raise RuntimeError("frozen catalogue-v3 runtime was not decoded before execution")
    spec = importlib.util.spec_from_file_location("sparse_support_v4_frozen_runtime", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    if tuple(module.YEARS) != YEARS:
        raise RuntimeError(f"unexpected frozen development years: {module.YEARS}")
    return module


def conservative_pvalue(score: float, calibration: np.ndarray) -> float:
    values = np.asarray(calibration, dtype=np.float64)
    if values.shape != (CALIBRATION_PER_BIN,) or not np.all(np.isfinite(values)):
        raise RuntimeError("invalid calibration panel")
    return float((1 + np.sum(values >= float(score))) / CALIBRATION_DENOMINATOR)


def score_episode(episode: Any) -> tuple[float, float, float]:
    details = v3.episode_score_details(episode)
    v3_score = float(details["score"])
    brown_from_v3 = float(details["brown_peak"])
    independent_brown = float(brown.wavelet_episode_score(episode))
    difference = abs(brown_from_v3 - independent_brown)
    if difference > BROWN_EQ_TOL:
        raise RuntimeError(
            f"Brown comparator mismatch: v3 brown_peak={brown_from_v3} independent={independent_brown} diff={difference}"
        )
    if not (math.isfinite(v3_score) and math.isfinite(independent_brown)):
        raise RuntimeError("non-finite episode score")
    return v3_score, independent_brown, difference


def calibrate_year(
    year: int,
    calibration_events: list[dict[str, Any]],
    base: Any,
    scorer: Any,
) -> tuple[dict[int, dict[str, np.ndarray]], dict[str, Any]]:
    factory = scorer.MondrianWindowFactory(base, calibration_events)
    supported: list[int] = []
    panels: dict[int, dict[str, np.ndarray]] = {}
    max_brown_difference = 0.0

    for bin_index in range(36):
        try:
            factory.make(
                year,
                bin_index,
                scorer.stable_seed("sparse-support-v4-support", CORPUS, year, bin_index),
            )
        except RuntimeError:
            continue
        supported.append(bin_index)

        v3_scores = np.empty(CALIBRATION_PER_BIN, dtype=np.float64)
        brown_scores = np.empty(CALIBRATION_PER_BIN, dtype=np.float64)
        for index in range(CALIBRATION_PER_BIN):
            episode = factory.make(
                year,
                bin_index,
                scorer.stable_seed("sparse-support-v4-calibration", CORPUS, year, bin_index, index),
            )
            v3_score, brown_score, difference = score_episode(episode)
            v3_scores[index] = v3_score
            brown_scores[index] = brown_score
            max_brown_difference = max(max_brown_difference, difference)
        panels[bin_index] = {"v3": v3_scores, "brown": brown_scores}

    if set(panels) != set(supported):
        raise RuntimeError("supported calibration-bin construction changed")
    return panels, {
        "year": year,
        "supported_bins": supported,
        "supported_bin_count": len(supported),
        "null_episodes": len(supported) * CALIBRATION_PER_BIN,
        "calibration_per_bin": CALIBRATION_PER_BIN,
        "denominator": CALIBRATION_DENOMINATOR,
        "max_brown_equivalence_difference": max_brown_difference,
    }


def build_local_episode(
    family: dict[str, Any],
    year: int,
    scan_events: list[dict[str, Any]],
    runtime: Any,
    base: Any,
) -> tuple[Any, dict[str, Any]]:
    centroid = family["centroids"].get(str(year))
    if centroid is None:
        raise RuntimeError(f"family {family['family_id']} missing {year} centroid")
    center_sol = float(centroid["sol"])
    window_events = runtime.window_events_for_center(scan_events, center_sol, base)
    if len(window_events) < EPISODE_SIZE:
        raise RuntimeError(
            f"family {family['family_id']} year {year} has only {len(window_events)} events in frozen 10-degree window"
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
    metadata = {
        "window_event_count": len(window_events),
        "episode_size": len(chosen),
        "centroid": {
            "sol": center_sol,
            "sun_lon": float(centroid["sun_lon"]),
            "ecl_lat": float(centroid["ecl_lat"]),
            "vg": float(centroid["vg"]),
        },
        "selected_max_r2": float(np.max(distances[selected])),
    }
    return episode, metadata


def score_families(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    calibration: dict[int, dict[int, dict[str, np.ndarray]]],
    runtime: Any,
    base: Any,
    scorer: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    max_brown_difference = 0.0
    unsupported_candidate_bins: list[dict[str, Any]] = []
    episode_sizes: list[int] = []

    for family_index, family in enumerate(families, start=1):
        per_year: dict[str, Any] = {}
        for year in YEARS:
            episode, metadata = build_local_episode(family, year, scan_by_year[year], runtime, base)
            v3_score, brown_score, difference = score_episode(episode)
            max_brown_difference = max(max_brown_difference, difference)
            episode_sizes.append(int(metadata["episode_size"]))
            bin_index = int(scorer.mondrian_bin_of(float(metadata["centroid"]["sol"])))
            if bin_index not in calibration[year]:
                unsupported_candidate_bins.append({
                    "family_id": family["family_id"],
                    "year": year,
                    "bin": bin_index,
                })
                continue
            p_v3 = conservative_pvalue(v3_score, calibration[year][bin_index]["v3"])
            p_brown = conservative_pvalue(brown_score, calibration[year][bin_index]["brown"])
            per_year[str(year)] = {
                **metadata,
                "bin": bin_index,
                "v3_score": v3_score,
                "brown_score": brown_score,
                "p_v3": p_v3,
                "p_brown": p_brown,
                "brown_equivalence_difference": difference,
            }
        if len(per_year) != len(YEARS):
            continue
        v3_ps = [float(per_year[str(year)]["p_v3"]) for year in YEARS]
        brown_ps = [float(per_year[str(year)]["p_brown"]) for year in YEARS]
        v3_scores = [float(per_year[str(year)]["v3_score"]) for year in YEARS]
        brown_scores = [float(per_year[str(year)]["brown_score"]) for year in YEARS]
        rows.append({
            "family_id": str(family["family_id"]),
            "per_year": per_year,
            "v3_worst_year_p": max(v3_ps),
            "v3_fisher": float(-2.0 * sum(math.log(value) for value in v3_ps)),
            "v3_min_year_score": min(v3_scores),
            "brown_worst_year_p": max(brown_ps),
            "brown_fisher": float(-2.0 * sum(math.log(value) for value in brown_ps)),
            "brown_min_year_score": min(brown_scores),
        })
        if family_index % 25 == 0 or family_index == len(families):
            print(f"sparse-support family scoring {family_index}/{len(families)}", flush=True)

    return rows, {
        "families_requested": len(families),
        "families_scored": len(rows),
        "episode_count": len(episode_sizes),
        "episode_sizes": sorted(set(episode_sizes)),
        "max_brown_equivalence_difference": max_brown_difference,
        "unsupported_candidate_bins": unsupported_candidate_bins,
    }


def ordered_family_ids(scored: list[dict[str, Any]], method: str) -> list[str]:
    if method == "v3":
        ordered = sorted(
            scored,
            key=lambda row: (
                float(row["v3_worst_year_p"]),
                -float(row["v3_fisher"]),
                -float(row["v3_min_year_score"]),
                str(row["family_id"]),
            ),
        )
    elif method == "brown":
        ordered = sorted(
            scored,
            key=lambda row: (
                float(row["brown_worst_year_p"]),
                -float(row["brown_fisher"]),
                -float(row["brown_min_year_score"]),
                str(row["family_id"]),
            ),
        )
    else:
        raise ValueError(method)
    return [str(row["family_id"]) for row in ordered]


def rrf_order(v3_order: list[str], persistence_order: list[str]) -> tuple[list[str], dict[str, float]]:
    if set(v3_order) != set(persistence_order) or len(v3_order) != len(persistence_order):
        raise RuntimeError("rank-fusion family universe mismatch")
    v3_rank = {family_id: rank for rank, family_id in enumerate(v3_order, start=1)}
    persistence_rank = {
        family_id: rank for rank, family_id in enumerate(persistence_order, start=1)
    }
    scores = {
        family_id: 1.0 / (RRF_K + v3_rank[family_id]) + 1.0 / (RRF_K + persistence_rank[family_id])
        for family_id in v3_order
    }
    order = sorted(scores, key=lambda family_id: (-scores[family_id], family_id))
    return order, scores


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
    if set(order) != set(family_by_id) or len(order) != len(family_by_id):
        raise RuntimeError("evaluation ranking family universe mismatch")
    eligible = eligible_labels(hidden_labels)
    rank_map = {family_id: rank for rank, family_id in enumerate(order, start=1)}

    dominant_precision: dict[str, float] = {}
    for family_id, family in family_by_id.items():
        counts = Counter(hidden_labels.get(event_id, "SPORADIC") for event_id in family["event_ids"])
        counts.pop("SPORADIC", None)
        dominant = counts.most_common(1)[0][1] if counts else 0
        dominant_precision[family_id] = dominant / int(family["event_count"]) if family["event_count"] else 0.0

    qualified_labels: set[str] = set()
    ranks: list[int] = []
    f1s: list[float] = []
    per_label: list[dict[str, Any]] = []
    recovered100 = 0
    recovered500 = 0
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
        f1, precision, overlap, family_id = max(
            matches, key=lambda item: (item[0], item[1], item[2], item[3])
        )
        rank = rank_map[family_id]
        qualified = bool(precision >= 0.5 and overlap >= 4)
        if qualified:
            qualified_labels.add(label)
            ranks.append(rank)
            f1s.append(f1)
            recovered100 += int(rank <= 100)
            recovered500 += int(rank <= 500)
        per_label.append({
            "label": label,
            "rank": rank,
            "qualified": qualified,
            "family_id": family_id,
            "overlap": int(overlap),
            "precision": float(precision),
            "recall": float(overlap / total),
            "f1": float(f1),
        })

    top100 = order[:100]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(qualified_labels),
        "recovered_at_100": recovered100,
        "recovered_at_500": recovered500,
        "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
        "median_rank": float(np.median(ranks)) if ranks else None,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "top100_dominant_precision": float(np.mean([dominant_precision[family_id] for family_id in top100])) if top100 else 0.0,
        "per_label": per_label,
    }


def compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "per_label"}


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if not all(v3.self_test().values()):
        raise RuntimeError("frozen multi-anchor v3 self-test failed")
    if not all(brown.self_test().values()):
        raise RuntimeError("frozen Brown comparator self-test failed")

    scaffold = json.loads(args.fixed4_scaffold_json.read_text())
    if scaffold["years"] != [2022, 2023] or len(scaffold["families"]) != EXPECTED_FAMILY_COUNT:
        raise RuntimeError("fixed4 development scaffold changed")
    persistence_order = [str(value) for value in scaffold["rankings"]["persistence"]]
    families = scaffold["families"]
    family_ids = [str(family["family_id"]) for family in families]
    if len(set(family_ids)) != EXPECTED_FAMILY_COUNT or set(persistence_order) != set(family_ids):
        raise RuntimeError("fixed4 family identifiers/ranking changed")

    runtime = load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    # `load_sources` expects the old baseline field on its namespace even though
    # the scientific baseline JSON is not used during source reconstruction.
    setattr(args, "fixed4_baseline_json", args.fixed4_scaffold_json)
    _candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    if sorted(scan_by_year) != list(YEARS) or sorted(calibration_by_year) != list(YEARS):
        raise RuntimeError("catalogue year universe changed")

    calibration: dict[int, dict[int, dict[str, np.ndarray]]] = {}
    calibration_summary: list[dict[str, Any]] = []
    for year in YEARS:
        panels, summary = calibrate_year(year, calibration_by_year[year], base, scorer)
        calibration[year] = panels
        calibration_summary.append(summary)
        print(
            f"sparse-support calibration {year}: bins={summary['supported_bin_count']} nulls={summary['null_episodes']}",
            flush=True,
        )

    scored, scoring_summary = score_families(
        families, scan_by_year, calibration, runtime, base, scorer
    )
    if len(scored) != EXPECTED_FAMILY_COUNT:
        print(
            "SPARSE_SUPPORT_INCOMPLETE_FAMILY_SCORING " + json.dumps(scoring_summary, sort_keys=True),
            flush=True,
        )

    v3_order = ordered_family_ids(scored, "v3") if len(scored) == EXPECTED_FAMILY_COUNT else []
    brown_order = ordered_family_ids(scored, "brown") if len(scored) == EXPECTED_FAMILY_COUNT else []
    rrf_rank, rrf_scores = (
        rrf_order(v3_order, persistence_order)
        if len(v3_order) == EXPECTED_FAMILY_COUNT
        else ([], {})
    )

    if len(v3_order) == EXPECTED_FAMILY_COUNT:
        metrics_full = {
            "v3": evaluate_order(hidden_labels, families, v3_order),
            "brown": evaluate_order(hidden_labels, families, brown_order),
            "fixed4_persistence": evaluate_order(hidden_labels, families, persistence_order),
            "rrf": evaluate_order(hidden_labels, families, rrf_rank),
        }
    else:
        metrics_full = {
            name: {
                "eligible_labels": len(eligible_labels(hidden_labels)),
                "qualified_matches": 0,
                "recovered_at_100": 0,
                "recovered_at_500": 0,
                "mrr": 0.0,
                "median_rank": None,
                "macro_f1": 0.0,
                "top100_dominant_precision": 0.0,
                "per_label": [],
            }
            for name in ("v3", "brown", "fixed4_persistence", "rrf")
        }
    metrics = {name: compact_metrics(value) for name, value in metrics_full.items()}

    calibration_all_exact = all(
        summary["null_episodes"] == summary["supported_bin_count"] * CALIBRATION_PER_BIN
        and summary["calibration_per_bin"] == CALIBRATION_PER_BIN
        and summary["denominator"] == CALIBRATION_DENOMINATOR
        for summary in calibration_summary
    )
    max_brown_difference = max(
        [summary["max_brown_equivalence_difference"] for summary in calibration_summary]
        + [float(scoring_summary["max_brown_equivalence_difference"])]
    )
    exact_episode_sizes = scoring_summary["episode_sizes"] == [EPISODE_SIZE]
    fixed4_reproduced = (
        metrics["fixed4_persistence"]["eligible_labels"] == EXPECTED_ELIGIBLE_LABELS
        and metrics["fixed4_persistence"]["qualified_matches"] == EXPECTED_QUALIFIED_LABELS
        and metrics["fixed4_persistence"]["recovered_at_100"] == FIXED4_RECOVERED100
        and abs(metrics["fixed4_persistence"]["top100_dominant_precision"] - FIXED4_TOP100_PRECISION) < 1e-15
    )

    gates = {
        "exact_197_family_fixed4_scaffold": len(families) == EXPECTED_FAMILY_COUNT,
        "target_excluded_development_years_exact": sorted(scan_by_year) == list(YEARS),
        "frozen_v3_and_brown_self_tests": all(v3.self_test().values()) and all(brown.self_test().values()),
        "at_least_30_supported_bins_each_year": all(summary["supported_bin_count"] >= 30 for summary in calibration_summary),
        "exact_512_nulls_per_supported_bin": calibration_all_exact,
        "all_197_families_scored_in_both_years": len(scored) == EXPECTED_FAMILY_COUNT and not scoring_summary["unsupported_candidate_bins"],
        "all_local_episode_sizes_exact_128": exact_episode_sizes,
        "brown_equivalence_within_1e_10_everywhere": max_brown_difference <= BROWN_EQ_TOL,
        "fixed4_family_evaluation_reproduced": fixed4_reproduced,
        "v3_recovered_at_100_at_least_48": metrics["v3"]["recovered_at_100"] >= 48,
        "v3_top100_precision_at_least_050": metrics["v3"]["top100_dominant_precision"] >= 0.50,
        "v3_recovery_at_least_brown": metrics["v3"]["recovered_at_100"] >= metrics["brown"]["recovered_at_100"],
        "rrf_recovered_at_100_at_least_fixed4_61": metrics["rrf"]["recovered_at_100"] >= FIXED4_RECOVERED100,
        "rrf_top100_precision_at_least_060": metrics["rrf"]["top100_dominant_precision"] >= 0.60,
    }
    verdict = (
        "PASS_SPARSE_SUPPORT_V4_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_SPARSE_SUPPORT_V4_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "corpus": CORPUS,
            "blind_exclusion": [float(support.BLIND_LOW), float(support.BLIND_HIGH)],
            "candidate_scaffold": "frozen fixed4 persistence families from 2022-2023 development only",
            "family_count": EXPECTED_FAMILY_COUNT,
            "window_width_deg": float(runtime.WINDOW_WIDTH_DEG),
            "episode_size": EPISODE_SIZE,
            "calibration_per_bin": CALIBRATION_PER_BIN,
            "calibration_denominator": CALIBRATION_DENOMINATOR,
            "v3_family_ranking": "worst-year empirical p, Fisher evidence, minimum-year score, family id",
            "brown_family_ranking": "same recurrence ranking on frozen Brown comparator",
            "rrf_k": RRF_K,
            "rrf_weights": "equal v3 and fixed4-persistence reciprocal ranks",
        },
        "development_scaffold": {
            "source_run": int(scaffold["source_run"]),
            "family_count": len(families),
            "frozen_persistence_metrics": scaffold["persistence_metrics"],
        },
        "catalogue_sources": catalogue_sources,
        "calibration_summary": calibration_summary,
        "family_scoring_summary": scoring_summary,
        "metrics": metrics,
        "gates": gates,
        "max_brown_equivalence_difference": max_brown_difference,
        "claim_boundary": (
            "Development-only target-free proposal/ranking architecture on exposed 2022-2023 data. "
            "No 2024-2026 catalogue or OrbitTrace target information was used."
        ),
    }
    (args.output / "sparse_support_v4_development.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "sparse_support_v4_family_scores.json.gz").write_bytes(
        gzip.compress(json.dumps(scored, separators=(",", ":")).encode())
    )
    if rrf_scores:
        (args.output / "sparse_support_v4_rankings.json").write_text(
            json.dumps({
                "v3": v3_order,
                "brown": brown_order,
                "fixed4_persistence": persistence_order,
                "rrf": rrf_rank,
                "rrf_scores": rrf_scores,
            }, indent=2) + "\n",
            encoding="utf-8",
        )

    lines = [
        "# OrbitTrace sparse-support v4 development",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- fixed4 proposal families: **{len(families)}**",
        f"- fully scored families: **{len(scored)}**",
        f"- supported calibration bins 2022/2023: **{calibration_summary[0]['supported_bin_count']} / {calibration_summary[1]['supported_bin_count']}**",
        f"- v3 recovered@100: **{metrics['v3']['recovered_at_100']}**; precision: **{metrics['v3']['top100_dominant_precision']:.4f}**",
        f"- Brown recovered@100: **{metrics['brown']['recovered_at_100']}**; precision: **{metrics['brown']['top100_dominant_precision']:.4f}**",
        f"- fixed4 persistence recovered@100: **{metrics['fixed4_persistence']['recovered_at_100']}**; precision: **{metrics['fixed4_persistence']['top100_dominant_precision']:.4f}**",
        f"- fixed v3+fixed4 RRF recovered@100: **{metrics['rrf']['recovered_at_100']}**; precision: **{metrics['rrf']['top100_dominant_precision']:.4f}**",
        f"- maximum independent Brown equivalence difference: **{max_brown_difference:.3e}**",
        "",
        "No 2024-2026 catalogue or OrbitTrace target information was opened by this run.",
    ]
    (args.output / "SPARSE_SUPPORT_V4_DEVELOPMENT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
