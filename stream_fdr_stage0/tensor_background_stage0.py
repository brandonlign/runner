from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

import matched_analog_eprocess as analog
import predictive_eprocess_pilot as common

OUT_DIR = Path("stream_fdr_stage0/results/tensor_background_stage0")
YEARS = common.YEARS
METHODS = (
    "robust_group_sparse",
    "pooled_raw",
    "recurrent_raw",
    "median_residual",
    "svd_residual",
)
PRIMARY = "robust_group_sparse"
BASELINES = tuple(method for method in METHODS if method != PRIMARY)

LON_BINS = 12
LAT_BINS = 8
SPEED_BINS = 8
CELL_COUNT = LON_BINS * LAT_BINS * SPEED_BINS
EVENTS_PER_YEAR = 60
CALIBRATION_NULL_SCENES = 128
TEST_NULL_SCENES = 128
INJECTION_REPLICATES = 96
BOOTSTRAP_REPLICATES = 8000
THRESHOLD_QUANTILE = 0.95
DETECTION_DISTANCE = 2.0
M2026_DISTANCE = 2.0
RPCA_LAMBDA = 1.0 / math.sqrt(len(YEARS))
RPCA_MAX_ITERATIONS = 80
RPCA_TOLERANCE = 1e-6
POSITIVE_EPSILON = 1e-7

COMPACT_SCATTER = np.asarray([3.0, 3.0, 1.5], dtype=np.float64)
DIFFUSE_SCATTER = np.asarray([12.0, 9.0, 4.0], dtype=np.float64)
RIDGE_SCATTER = np.asarray([28.0, 14.0, 5.0], dtype=np.float64)
DRIFT_PER_YEAR = np.asarray([4.0, 1.5, 0.35], dtype=np.float64)

CONDITIONS = (
    "recurring_sparse",
    "recurring_moderate",
    "intermittent",
    "late_onset",
    "diffuse_recurring",
    "drifting_recurring",
    "strong_recurring",
    "one_year_artifact",
    "broad_recurring_ridge",
)
RECURRING_STREAM_CONDITIONS = (
    "recurring_sparse",
    "recurring_moderate",
    "intermittent",
    "late_onset",
    "diffuse_recurring",
    "drifting_recurring",
    "strong_recurring",
)


@dataclass(frozen=True)
class SceneResult:
    score: float
    cell_index: int
    raw_center: np.ndarray
    annual_support: int


def cell_tuple(index: int) -> tuple[int, int, int]:
    speed = index % SPEED_BINS
    quotient = index // SPEED_BINS
    latitude = quotient % LAT_BINS
    longitude = quotient // LAT_BINS
    return longitude, latitude, speed


def cell_index(longitude: int, latitude: int, speed: int) -> int:
    return (longitude * LAT_BINS + latitude) * SPEED_BINS + speed


def raw_to_cell_indices(raw: np.ndarray) -> np.ndarray:
    longitude = np.floor((raw[:, 0] + 180.0) / 360.0 * LON_BINS).astype(int)
    longitude %= LON_BINS
    latitude = np.floor((raw[:, 1] + 90.0) / 180.0 * LAT_BINS).astype(int)
    latitude = np.clip(latitude, 0, LAT_BINS - 1)
    speed = np.floor((raw[:, 2] - 5.0) / 70.0 * SPEED_BINS).astype(int)
    speed = np.clip(speed, 0, SPEED_BINS - 1)
    return (longitude * LAT_BINS + latitude) * SPEED_BINS + speed


def cell_center(index: int) -> np.ndarray:
    longitude, latitude, speed = cell_tuple(index)
    return np.asarray(
        [
            -180.0 + (longitude + 0.5) * 360.0 / LON_BINS,
            -90.0 + (latitude + 0.5) * 180.0 / LAT_BINS,
            5.0 + (speed + 0.5) * 70.0 / SPEED_BINS,
        ],
        dtype=np.float64,
    )


def build_neighborhoods() -> tuple[np.ndarray, ...]:
    neighborhoods: list[np.ndarray] = []
    for index in range(CELL_COUNT):
        longitude, latitude, speed = cell_tuple(index)
        values: list[int] = []
        for dlon in (-1, 0, 1):
            for dlat in (-1, 0, 1):
                for dspeed in (-1, 0, 1):
                    new_latitude = latitude + dlat
                    new_speed = speed + dspeed
                    if not (0 <= new_latitude < LAT_BINS):
                        continue
                    if not (0 <= new_speed < SPEED_BINS):
                        continue
                    new_longitude = (longitude + dlon) % LON_BINS
                    values.append(
                        cell_index(new_longitude, new_latitude, new_speed)
                    )
        neighborhoods.append(np.asarray(sorted(set(values)), dtype=np.int64))
    return tuple(neighborhoods)


NEIGHBORHOODS = build_neighborhoods()


def scene_count_matrix(scene: dict[int, np.ndarray]) -> np.ndarray:
    matrix = np.zeros((len(YEARS), CELL_COUNT), dtype=np.float64)
    for row, year in enumerate(YEARS):
        indices = raw_to_cell_indices(scene[year])
        matrix[row] = np.bincount(indices, minlength=CELL_COUNT)
    return matrix


def singular_value_threshold(matrix: np.ndarray, threshold: float) -> np.ndarray:
    left, singular_values, right = np.linalg.svd(matrix, full_matrices=False)
    shrunk = np.maximum(singular_values - threshold, 0.0)
    active = shrunk > 0.0
    if not np.any(active):
        return np.zeros_like(matrix)
    return (left[:, active] * shrunk[active]) @ right[active]


def column_group_threshold(matrix: np.ndarray, threshold: float) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=0)
    scale = np.maximum(1.0 - threshold / np.maximum(norms, 1e-15), 0.0)
    return matrix * scale


def robust_column_sparse_decomposition(
    transformed: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, float | int]]:
    spectral_norm = float(np.linalg.norm(transformed, 2))
    column_norm = float(np.max(np.linalg.norm(transformed, axis=0)))
    dual_norm = max(spectral_norm, column_norm / RPCA_LAMBDA, 1e-12)
    dual = transformed / dual_norm
    low_rank = np.zeros_like(transformed)
    sparse = np.zeros_like(transformed)
    mu = 1.25 / max(spectral_norm, 1e-12)
    mu_limit = mu * 1e7
    rho = 1.5
    denominator = max(float(np.linalg.norm(transformed, "fro")), 1e-12)
    relative_error = math.inf

    for iteration in range(1, RPCA_MAX_ITERATIONS + 1):
        low_rank = singular_value_threshold(
            transformed - sparse + dual / mu,
            1.0 / mu,
        )
        sparse = column_group_threshold(
            transformed - low_rank + dual / mu,
            RPCA_LAMBDA / mu,
        )
        residual = transformed - low_rank - sparse
        relative_error = float(np.linalg.norm(residual, "fro") / denominator)
        dual = dual + mu * residual
        if relative_error <= RPCA_TOLERANCE:
            break
        mu = min(mu * rho, mu_limit)

    rank = int(np.sum(np.linalg.svd(low_rank, compute_uv=False) > 1e-7))
    return low_rank, sparse, {
        "iterations": iteration,
        "relative_error": relative_error,
        "low_rank_rank": rank,
    }


def annual_neighborhood_values(values: np.ndarray) -> np.ndarray:
    result = np.zeros((len(YEARS), CELL_COUNT), dtype=np.float64)
    for index, neighborhood in enumerate(NEIGHBORHOODS):
        result[:, index] = np.sum(values[:, neighborhood], axis=1)
    return result


def recurring_score(
    annual_values: np.ndarray,
    require_support: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    positive = np.maximum(annual_values, 0.0)
    support = np.sum(positive > POSITIVE_EPSILON, axis=0)
    score = np.sum(positive, axis=0) - np.max(positive, axis=0)
    if require_support:
        score = np.where(support >= 3, score, 0.0)
    return score, support


def scan_scene(scene: dict[int, np.ndarray]) -> tuple[dict[str, SceneResult], dict[str, object]]:
    counts = scene_count_matrix(scene)
    transformed = 2.0 * np.sqrt(counts + 3.0 / 8.0)
    low_rank, sparse, diagnostics = robust_column_sparse_decomposition(transformed)

    positive_sparse = np.maximum(sparse, 0.0)
    primary_annual = annual_neighborhood_values(positive_sparse)
    primary_scores, primary_support = recurring_score(primary_annual)

    raw_annual = annual_neighborhood_values(counts)
    recurrent_raw_scores, recurrent_raw_support = recurring_score(raw_annual)
    pooled_scores = np.sum(raw_annual, axis=0)
    pooled_support = np.sum(raw_annual > 0.0, axis=0)

    median_cell = np.median(counts, axis=0, keepdims=True)
    median_positive = np.maximum(counts - median_cell, 0.0)
    median_annual = annual_neighborhood_values(median_positive)
    median_scores, median_support = recurring_score(median_annual)

    left, singular_values, right = np.linalg.svd(transformed, full_matrices=False)
    retained = min(2, len(singular_values))
    rank_two = (left[:, :retained] * singular_values[:retained]) @ right[:retained]
    svd_positive = np.maximum(transformed - rank_two, 0.0)
    svd_annual = annual_neighborhood_values(svd_positive)
    svd_scores, svd_support = recurring_score(svd_annual)

    score_arrays = {
        "robust_group_sparse": (primary_scores, primary_support),
        "pooled_raw": (pooled_scores, pooled_support),
        "recurrent_raw": (recurrent_raw_scores, recurrent_raw_support),
        "median_residual": (median_scores, median_support),
        "svd_residual": (svd_scores, svd_support),
    }
    results: dict[str, SceneResult] = {}
    for method, (scores, support) in score_arrays.items():
        index = int(np.argmax(scores))
        results[method] = SceneResult(
            score=float(scores[index]),
            cell_index=index,
            raw_center=cell_center(index),
            annual_support=int(support[index]),
        )
    return results, {
        "rpca": diagnostics,
        "count_total": float(np.sum(counts)),
        "sparse_positive_mass": float(np.sum(positive_sparse)),
        "sparse_nonzero_columns": int(
            np.sum(np.linalg.norm(sparse, axis=0) > 1e-7)
        ),
    }


def empirical_threshold(values: Iterable[float]) -> float:
    sorted_values = np.sort(np.asarray(list(values), dtype=np.float64))
    index = int(math.ceil(THRESHOLD_QUANTILE * len(sorted_values))) - 1
    return float(sorted_values[max(0, min(index, len(sorted_values) - 1))])


def choose_scene(
    pools: dict[int, analog.YearPool],
    rng: np.random.Generator,
) -> tuple[dict[int, np.ndarray], float]:
    for _ in range(200):
        center = analog.choose_target_longitude(rng)
        scene: dict[int, np.ndarray] = {}
        valid = True
        for year in YEARS:
            sample = analog.sample_window(
                pools[year], center, EVENTS_PER_YEAR, rng
            )
            if sample is None:
                valid = False
                break
            scene[year] = sample
        if valid:
            return scene, center
    raise RuntimeError("Could not construct a seven-year scene")


def choose_truth(scene: dict[int, np.ndarray], rng: np.random.Generator) -> np.ndarray:
    year = YEARS[int(rng.integers(0, len(YEARS)))]
    values = scene[year]
    return values[int(rng.integers(0, len(values)))].copy()


def counts_for_condition(
    condition: str,
    rng: np.random.Generator,
) -> dict[int, int]:
    if condition == "recurring_sparse":
        return {year: 2 for year in YEARS}
    if condition == "recurring_moderate":
        return {year: 3 for year in YEARS}
    if condition == "intermittent":
        active = set(int(value) for value in rng.choice(YEARS, size=5, replace=False))
        return {year: (3 if year in active else 0) for year in YEARS}
    if condition == "late_onset":
        return {year: (0 if year <= 2020 else 3) for year in YEARS}
    if condition in {"diffuse_recurring", "drifting_recurring"}:
        return {year: 3 for year in YEARS}
    if condition == "strong_recurring":
        return {year: 5 for year in YEARS}
    if condition == "one_year_artifact":
        active_year = YEARS[int(rng.integers(0, len(YEARS)))]
        return {year: (12 if year == active_year else 0) for year in YEARS}
    if condition == "broad_recurring_ridge":
        return {year: 8 for year in YEARS}
    raise KeyError(condition)


def inject_condition(
    scene: dict[int, np.ndarray],
    condition: str,
    truth: np.ndarray,
    rng: np.random.Generator,
) -> dict[int, np.ndarray]:
    counts = counts_for_condition(condition, rng)
    result: dict[int, np.ndarray] = {}
    for year_index, year in enumerate(YEARS):
        background = scene[year]
        count = counts[year]
        if count <= 0:
            result[year] = background.copy()
            continue
        if condition == "diffuse_recurring":
            scatter = DIFFUSE_SCATTER
        elif condition == "broad_recurring_ridge":
            scatter = RIDGE_SCATTER
        else:
            scatter = COMPACT_SCATTER
        center = truth.copy()
        if condition == "drifting_recurring":
            center = center + (year_index - 3.0) * DRIFT_PER_YEAR
        year_offset = rng.normal(0.0, [0.8, 0.8, 0.35], size=3)
        events = center + year_offset + rng.normal(0.0, scatter, size=(count, 3))
        events[:, 0] = (events[:, 0] + 180.0) % 360.0 - 180.0
        events[:, 1] = np.clip(events[:, 1], -89.9, 89.9)
        events[:, 2] = np.clip(events[:, 2], 5.01, 74.99)
        result[year] = np.vstack([background, events])
    return result


def result_distance(result: SceneResult, truth: np.ndarray) -> float:
    return common.raw_distance(result.raw_center, truth)


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    return common.wilson_interval(successes, total)


def paired_bootstrap_interval(
    primary: np.ndarray,
    baseline: np.ndarray,
    seed: int,
) -> tuple[float, float]:
    difference = primary.astype(np.float64) - baseline.astype(np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0,
        len(difference),
        size=(BOOTSTRAP_REPLICATES, len(difference)),
    )
    means = np.mean(difference[indices], axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def calibrate(
    pools: dict[int, analog.YearPool],
) -> tuple[dict[str, float], dict[str, list[float]]]:
    rng = np.random.default_rng(601001)
    scores = {method: [] for method in METHODS}
    for _ in range(CALIBRATION_NULL_SCENES):
        scene, _ = choose_scene(pools, rng)
        results, _ = scan_scene(scene)
        for method in METHODS:
            scores[method].append(results[method].score)
    thresholds = {method: empirical_threshold(scores[method]) for method in METHODS}
    return thresholds, scores


def evaluate_nulls(
    pools: dict[int, analog.YearPool],
    thresholds: dict[str, float],
) -> dict[str, object]:
    rng = np.random.default_rng(602001)
    accepted = {method: [] for method in METHODS}
    diagnostics: list[dict[str, object]] = []
    for _ in range(TEST_NULL_SCENES):
        scene, center = choose_scene(pools, rng)
        results, diagnostic = scan_scene(scene)
        diagnostic["solar_longitude"] = center
        diagnostics.append(diagnostic)
        for method in METHODS:
            accepted[method].append(results[method].score > thresholds[method])

    methods: dict[str, object] = {}
    for method in METHODS:
        values = np.asarray(accepted[method], dtype=bool)
        count = int(np.sum(values))
        methods[method] = {
            "false_positive_count": count,
            "false_positive_rate": count / TEST_NULL_SCENES,
            "wilson_95": list(wilson_interval(count, TEST_NULL_SCENES)),
            "accepted": values.astype(int).tolist(),
        }
    return {"methods": methods, "diagnostics": diagnostics}


def evaluate_condition(
    pools: dict[int, analog.YearPool],
    thresholds: dict[str, float],
    condition: str,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    accepted = {method: [] for method in METHODS}
    recovered = {method: [] for method in METHODS}
    distances = {method: [] for method in METHODS}
    for _ in range(INJECTION_REPLICATES):
        background, _ = choose_scene(pools, rng)
        truth = choose_truth(background, rng)
        injected = inject_condition(background, condition, truth, rng)
        results, _ = scan_scene(injected)
        for method in METHODS:
            passes = results[method].score > thresholds[method]
            distance = result_distance(results[method], truth)
            near = distance <= DETECTION_DISTANCE
            accepted[method].append(passes)
            recovered[method].append(passes and near)
            distances[method].append(distance)

    methods: dict[str, object] = {}
    for method in METHODS:
        accepted_values = np.asarray(accepted[method], dtype=bool)
        recovered_values = np.asarray(recovered[method], dtype=bool)
        recovered_count = int(np.sum(recovered_values))
        methods[method] = {
            "acceptance_count": int(np.sum(accepted_values)),
            "acceptance_rate": float(np.mean(accepted_values)),
            "recovery_count": recovered_count,
            "recovery_rate": float(np.mean(recovered_values)),
            "recovery_wilson_95": list(
                wilson_interval(recovered_count, INJECTION_REPLICATES)
            ),
            "accepted": accepted_values.astype(int).tolist(),
            "recovered": recovered_values.astype(int).tolist(),
            "distances": distances[method],
        }
    return {"methods": methods}


def m2026_reference_raw() -> np.ndarray:
    return common.m2026_reference_raw()


def evaluate_m2026(
    pools: dict[int, analog.YearPool],
    thresholds: dict[str, float],
) -> dict[str, object]:
    rng = np.random.default_rng(612001)
    scene: dict[int, np.ndarray] = {}
    for year in YEARS:
        sample = analog.sample_window(
            pools[year], 10.0, EVENTS_PER_YEAR, rng
        )
        if sample is None:
            raise RuntimeError(f"M2026-A1 window lacks {EVENTS_PER_YEAR} events for {year}")
        scene[year] = sample
    results, diagnostics = scan_scene(scene)
    reference = m2026_reference_raw()
    methods = {}
    for method in METHODS:
        distance = result_distance(results[method], reference)
        methods[method] = {
            "score": results[method].score,
            "threshold": thresholds[method],
            "accepted": results[method].score > thresholds[method],
            "distance_to_reference": distance,
            "near_reference": distance <= M2026_DISTANCE,
            "candidate_raw": results[method].raw_center.tolist(),
            "annual_support": results[method].annual_support,
        }
    return {"methods": methods, "diagnostics": diagnostics}


def decide(
    nulls: dict[str, object],
    conditions: dict[str, dict[str, object]],
    external: dict[str, object],
) -> dict[str, object]:
    sparse = conditions["recurring_sparse"]["methods"]
    primary_sparse = np.asarray(sparse[PRIMARY]["recovered"], dtype=int)
    baseline_arrays = {
        method: np.asarray(sparse[method]["recovered"], dtype=int)
        for method in BASELINES
    }
    best_baseline = max(
        BASELINES,
        key=lambda method: float(np.mean(baseline_arrays[method])),
    )
    best_values = baseline_arrays[best_baseline]
    sparse_gain = float(np.mean(primary_sparse - best_values))
    gain_interval = paired_bootstrap_interval(
        primary_sparse,
        best_values,
        seed=613001,
    )

    rates = {
        condition: conditions[condition]["methods"][PRIMARY]["recovery_rate"]
        for condition in CONDITIONS
    }
    artifact_acceptance = conditions["one_year_artifact"]["methods"][PRIMARY][
        "acceptance_rate"
    ]
    ridge_acceptance = conditions["broad_recurring_ridge"]["methods"][PRIMARY][
        "acceptance_rate"
    ]
    primary_null = nulls["methods"][PRIMARY]

    individual_margins: dict[str, object] = {}
    every_not_inferior = True
    for condition in RECURRING_STREAM_CONDITIONS:
        primary_rate = conditions[condition]["methods"][PRIMARY]["recovery_rate"]
        best_method = max(
            BASELINES,
            key=lambda method: conditions[condition]["methods"][method]["recovery_rate"],
        )
        best_rate = conditions[condition]["methods"][best_method]["recovery_rate"]
        margin = primary_rate - best_rate
        individual_margins[condition] = {
            "primary": primary_rate,
            "best_baseline": best_method,
            "best_baseline_rate": best_rate,
            "margin": margin,
        }
        every_not_inferior = every_not_inferior and margin >= -0.10

    external_primary = external["methods"][PRIMARY]
    gates = {
        "null_rate_le_0_10": primary_null["false_positive_rate"] <= 0.10,
        "null_wilson_upper_le_0_15": primary_null["wilson_95"][1] <= 0.15,
        "sparse_gain_ge_0_10": sparse_gain >= 0.10,
        "sparse_bootstrap_lower_gt_0": gain_interval[0] > 0.0,
        "moderate_recovery_ge_0_70": rates["recurring_moderate"] >= 0.70,
        "intermittent_recovery_ge_0_40": rates["intermittent"] >= 0.40,
        "late_recovery_ge_0_40": rates["late_onset"] >= 0.40,
        "diffuse_recovery_ge_0_35": rates["diffuse_recurring"] >= 0.35,
        "drifting_recovery_ge_0_40": rates["drifting_recurring"] >= 0.40,
        "strong_recovery_ge_0_90": rates["strong_recurring"] >= 0.90,
        "artifact_acceptance_le_0_10": artifact_acceptance <= 0.10,
        "ridge_acceptance_le_0_15": ridge_acceptance <= 0.15,
        "m2026_accepted_near_reference": bool(
            external_primary["accepted"] and external_primary["near_reference"]
        ),
        "every_recurring_condition_not_inferior_by_0_10": every_not_inferior,
    }
    return {
        "primary_method": PRIMARY,
        "sparse_primary_recovery": float(np.mean(primary_sparse)),
        "sparse_best_baseline": best_baseline,
        "sparse_best_baseline_recovery": float(np.mean(best_values)),
        "sparse_gain": sparse_gain,
        "sparse_gain_paired_bootstrap_95": list(gain_interval),
        "condition_primary_recovery": rates,
        "artifact_primary_acceptance": artifact_acceptance,
        "ridge_primary_acceptance": ridge_acceptance,
        "individual_margins": individual_margins,
        "gates": gates,
        "verdict": "CONTINUE_TO_STRUCTURED_POISSON_TENSOR_BENCHMARK"
        if all(gates.values())
        else "KILL_OR_REDESIGN_ROBUST_BACKGROUND_DECOMPOSITION",
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    null_methods = payload["test_null_results"]["methods"]
    lines = [
        "# Robust background-decomposition Stage 0",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "The primary method decomposes the seven-year phase-space count matrix into a low-rank background and a column-group-sparse residual. GhostStream was excluded.",
        "",
        "## Null behavior",
        "",
        "| Method | FPR | Wilson 95% |",
        "|---|---:|---|",
    ]
    for method in METHODS:
        result = null_methods[method]
        lines.append(
            f"| {method} | {result['false_positive_rate']:.3f} | {result['wilson_95']} |"
        )
    lines.extend(
        [
            "",
            "## Recovery and artifact acceptance",
            "",
            "| Condition | robust sparse | pooled raw | recurrent raw | median residual | SVD residual |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for condition in CONDITIONS:
        methods = payload["conditions"][condition]["methods"]
        metric = "acceptance_rate" if condition in {"one_year_artifact", "broad_recurring_ridge"} else "recovery_rate"
        lines.append(
            f"| {condition} | {methods['robust_group_sparse'][metric]:.3f} "
            f"| {methods['pooled_raw'][metric]:.3f} "
            f"| {methods['recurrent_raw'][metric]:.3f} "
            f"| {methods['median_residual'][metric]:.3f} "
            f"| {methods['svd_residual'][metric]:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Sparse recurring comparison",
            "",
            f"- primary recovery: {decision['sparse_primary_recovery']:.3f}",
            f"- strongest baseline: `{decision['sparse_best_baseline']}` at {decision['sparse_best_baseline_recovery']:.3f}",
            f"- paired gain: {decision['sparse_gain']:.3f}",
            f"- paired-bootstrap 95%: {decision['sparse_gain_paired_bootstrap_95']}",
            "",
            "## Frozen gates",
            "",
        ]
    )
    for gate, passed in decision["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    external = payload["external_m2026_control"]["methods"][PRIMARY]
    lines.extend(
        [
            "",
            "## External M2026-A1 control",
            "",
            f"- accepted: {external['accepted']}",
            f"- near reference: {external['near_reference']}",
            f"- distance: {external['distance_to_reference']:.3f}",
            f"- score / threshold: {external['score']:.3f} / {external['threshold']:.3f}",
            f"- annual support: {external['annual_support']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalogs, pools = analog.make_year_pools()
    thresholds, calibration_scores = calibrate(pools)
    test_null_results = evaluate_nulls(pools, thresholds)
    conditions = {
        condition: evaluate_condition(
            pools,
            thresholds,
            condition,
            seed=603001 + index * 1000,
        )
        for index, condition in enumerate(CONDITIONS)
    }
    external = evaluate_m2026(pools, thresholds)
    decision = decide(test_null_results, conditions, external)
    payload = {
        "configuration": {
            "years": YEARS,
            "events_per_year": EVENTS_PER_YEAR,
            "grid": {
                "longitude_bins": LON_BINS,
                "latitude_bins": LAT_BINS,
                "speed_bins": SPEED_BINS,
                "cell_count": CELL_COUNT,
            },
            "rpca_lambda": RPCA_LAMBDA,
            "rpca_max_iterations": RPCA_MAX_ITERATIONS,
            "rpca_tolerance": RPCA_TOLERANCE,
            "calibration_null_scenes": CALIBRATION_NULL_SCENES,
            "test_null_scenes": TEST_NULL_SCENES,
            "injection_replicates": INJECTION_REPLICATES,
            "threshold_quantile": THRESHOLD_QUANTILE,
            "conditions": CONDITIONS,
            "python": os.sys.version,
            "numpy": np.__version__,
        },
        "year_event_counts": {
            str(year): len(catalogs[year].solar_longitude)
            for year in YEARS
        },
        "thresholds": thresholds,
        "calibration_scores": calibration_scores,
        "test_null_results": test_null_results,
        "conditions": conditions,
        "external_m2026_control": external,
        "decision": decision,
    }
    (OUT_DIR / "result.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    report = markdown_report(payload)
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
