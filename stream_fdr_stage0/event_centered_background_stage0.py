from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.spatial import cKDTree

import matched_analog_eprocess as analog
import predictive_eprocess_pilot as common
import tensor_background_stage0 as voxel

OUT_DIR = Path("stream_fdr_stage0/results/event_centered_background_stage0")
YEARS = common.YEARS
RADII = (0.8, 1.0, 1.2)
OUTER_MULTIPLIER = 2.5
METHODS = (
    "robust_group_sparse",
    "pooled_deviance",
    "recurrent_deviance",
    "recurrent_raw",
    "svd_residual",
)
PRIMARY = "robust_group_sparse"
BASELINES = tuple(method for method in METHODS if method != PRIMARY)
CALIBRATION_NULL_SCENES = 128
TEST_NULL_SCENES = 128
INJECTION_REPLICATES = 96
BOOTSTRAP_REPLICATES = 8000
THRESHOLD_QUANTILE = 0.95
DETECTION_DISTANCE = 2.0
M2026_DISTANCE = 2.0
POSITIVE_EPSILON = 1e-7
CONDITIONS = voxel.CONDITIONS
RECURRING_STREAM_CONDITIONS = voxel.RECURRING_STREAM_CONDITIONS


@dataclass(frozen=True)
class SceneResult:
    score: float
    candidate_raw: np.ndarray
    radius: float
    annual_support: int


def local_expected(inner: np.ndarray, outer: np.ndarray, radius: float) -> np.ndarray:
    shell = np.maximum(outer - inner, 0).astype(np.float64)
    outer_radius = OUTER_MULTIPLIER * radius
    volume_ratio = radius**3 / (outer_radius**3 - radius**3)
    return (shell + 0.5) * volume_ratio


def signed_root_poisson_deviance(observed: np.ndarray, expected: np.ndarray) -> np.ndarray:
    observed = observed.astype(np.float64)
    expected = np.maximum(expected.astype(np.float64), 1e-12)
    term = np.where(
        observed > 0.0,
        observed * np.log(np.maximum(observed, 1e-12) / expected) - (observed - expected),
        expected,
    )
    deviance = np.sqrt(np.maximum(2.0 * term, 0.0))
    return np.sign(observed - expected) * deviance


def recurring_scores(annual_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    positive = np.maximum(annual_values, 0.0)
    support = np.sum(positive > POSITIVE_EPSILON, axis=0)
    scores = np.sum(positive, axis=0) - np.max(positive, axis=0)
    scores = np.where(support >= 3, scores, 0.0)
    return scores, support


def scan_at_radius(
    scene: dict[int, np.ndarray],
    candidate_raw: np.ndarray,
    candidate_embedding: np.ndarray,
    radius: float,
) -> tuple[dict[str, SceneResult], dict[str, object]]:
    inner_rows: list[np.ndarray] = []
    expected_rows: list[np.ndarray] = []
    for year in YEARS:
        embedding = common.geometry.raw_to_embedding(scene[year])
        tree = cKDTree(embedding)
        inner = np.asarray(
            tree.query_ball_point(candidate_embedding, radius, return_length=True),
            dtype=np.float64,
        )
        outer = np.asarray(
            tree.query_ball_point(
                candidate_embedding,
                OUTER_MULTIPLIER * radius,
                return_length=True,
            ),
            dtype=np.float64,
        )
        inner_rows.append(inner)
        expected_rows.append(local_expected(inner, outer, radius))

    inner_matrix = np.vstack(inner_rows)
    expected_matrix = np.vstack(expected_rows)
    deviance = signed_root_poisson_deviance(inner_matrix, expected_matrix)

    _, sparse, rpca_diagnostics = voxel.robust_column_sparse_decomposition(deviance)
    primary_scores, primary_support = recurring_scores(np.maximum(sparse, 0.0))

    positive_deviance = np.maximum(deviance, 0.0)
    recurrent_deviance_scores, recurrent_deviance_support = recurring_scores(positive_deviance)
    pooled_scores = np.sum(positive_deviance, axis=0)
    pooled_support = np.sum(positive_deviance > POSITIVE_EPSILON, axis=0)

    raw_scores, raw_support = recurring_scores(inner_matrix)

    left, singular_values, right = np.linalg.svd(deviance, full_matrices=False)
    retained = min(2, len(singular_values))
    rank_two = (left[:, :retained] * singular_values[:retained]) @ right[:retained]
    svd_scores, svd_support = recurring_scores(np.maximum(deviance - rank_two, 0.0))

    arrays = {
        "robust_group_sparse": (primary_scores, primary_support),
        "pooled_deviance": (pooled_scores, pooled_support),
        "recurrent_deviance": (recurrent_deviance_scores, recurrent_deviance_support),
        "recurrent_raw": (raw_scores, raw_support),
        "svd_residual": (svd_scores, svd_support),
    }
    results: dict[str, SceneResult] = {}
    for method, (scores, support) in arrays.items():
        index = int(np.argmax(scores))
        results[method] = SceneResult(
            score=float(scores[index]),
            candidate_raw=candidate_raw[index].copy(),
            radius=radius,
            annual_support=int(support[index]),
        )
    return results, {
        "rpca": rpca_diagnostics,
        "candidate_count": len(candidate_raw),
    }


def scan_scene(scene: dict[int, np.ndarray]) -> tuple[dict[str, SceneResult], dict[str, object]]:
    candidate_raw = np.vstack([scene[year] for year in YEARS])
    candidate_embedding = common.geometry.raw_to_embedding(candidate_raw)
    best: dict[str, SceneResult] = {}
    radius_diagnostics: dict[str, object] = {}
    for radius in RADII:
        results, diagnostics = scan_at_radius(
            scene,
            candidate_raw,
            candidate_embedding,
            radius,
        )
        radius_diagnostics[str(radius)] = diagnostics
        for method, result in results.items():
            previous = best.get(method)
            if previous is None or result.score > previous.score:
                best[method] = result
    return best, {"radii": radius_diagnostics}


def empirical_threshold(values: Iterable[float]) -> float:
    array = np.sort(np.asarray(list(values), dtype=np.float64))
    index = int(math.ceil(THRESHOLD_QUANTILE * len(array))) - 1
    return float(array[max(0, min(index, len(array) - 1))])


def result_distance(result: SceneResult, truth: np.ndarray) -> float:
    return common.raw_distance(result.candidate_raw, truth)


def calibrate(pools: dict[int, analog.YearPool]) -> tuple[dict[str, float], dict[str, list[float]]]:
    rng = np.random.default_rng(701001)
    scores = {method: [] for method in METHODS}
    for _ in range(CALIBRATION_NULL_SCENES):
        scene, _ = voxel.choose_scene(pools, rng)
        results, _ = scan_scene(scene)
        for method in METHODS:
            scores[method].append(results[method].score)
    return {method: empirical_threshold(scores[method]) for method in METHODS}, scores


def evaluate_nulls(
    pools: dict[int, analog.YearPool],
    thresholds: dict[str, float],
) -> dict[str, object]:
    rng = np.random.default_rng(702001)
    accepted = {method: [] for method in METHODS}
    diagnostics: list[dict[str, object]] = []
    for _ in range(TEST_NULL_SCENES):
        scene, center = voxel.choose_scene(pools, rng)
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
            "wilson_95": list(common.wilson_interval(count, TEST_NULL_SCENES)),
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
    selected_radii = {method: [] for method in METHODS}
    for _ in range(INJECTION_REPLICATES):
        background, _ = voxel.choose_scene(pools, rng)
        truth = voxel.choose_truth(background, rng)
        injected = voxel.inject_condition(background, condition, truth, rng)
        results, _ = scan_scene(injected)
        for method in METHODS:
            passes = results[method].score > thresholds[method]
            distance = result_distance(results[method], truth)
            near = distance <= DETECTION_DISTANCE
            accepted[method].append(passes)
            recovered[method].append(passes and near)
            distances[method].append(distance)
            selected_radii[method].append(results[method].radius)

    methods: dict[str, object] = {}
    for method in METHODS:
        accepted_values = np.asarray(accepted[method], dtype=bool)
        recovered_values = np.asarray(recovered[method], dtype=bool)
        count = int(np.sum(recovered_values))
        methods[method] = {
            "acceptance_count": int(np.sum(accepted_values)),
            "acceptance_rate": float(np.mean(accepted_values)),
            "recovery_count": count,
            "recovery_rate": float(np.mean(recovered_values)),
            "recovery_wilson_95": list(common.wilson_interval(count, INJECTION_REPLICATES)),
            "accepted": accepted_values.astype(int).tolist(),
            "recovered": recovered_values.astype(int).tolist(),
            "distances": distances[method],
            "selected_radius_counts": {
                str(radius): int(sum(value == radius for value in selected_radii[method]))
                for radius in RADII
            },
        }
    return {"methods": methods}


def evaluate_m2026(
    pools: dict[int, analog.YearPool],
    thresholds: dict[str, float],
) -> dict[str, object]:
    rng = np.random.default_rng(712001)
    scene: dict[int, np.ndarray] = {}
    for year in YEARS:
        sample = analog.sample_window(pools[year], 10.0, voxel.EVENTS_PER_YEAR, rng)
        if sample is None:
            raise RuntimeError(f"M2026-A1 window lacks {voxel.EVENTS_PER_YEAR} events for {year}")
        scene[year] = sample
    results, diagnostics = scan_scene(scene)
    reference = common.m2026_reference_raw()
    methods = {}
    for method in METHODS:
        distance = result_distance(results[method], reference)
        methods[method] = {
            "score": results[method].score,
            "threshold": thresholds[method],
            "accepted": results[method].score > thresholds[method],
            "distance_to_reference": distance,
            "near_reference": distance <= M2026_DISTANCE,
            "candidate_raw": results[method].candidate_raw.tolist(),
            "selected_radius": results[method].radius,
            "annual_support": results[method].annual_support,
        }
    return {"methods": methods, "diagnostics": diagnostics}


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
    best_baseline = max(BASELINES, key=lambda method: float(np.mean(baseline_arrays[method])))
    best_values = baseline_arrays[best_baseline]
    gain = float(np.mean(primary_sparse - best_values))
    interval = paired_bootstrap_interval(primary_sparse, best_values, seed=713001)

    rates = {
        condition: conditions[condition]["methods"][PRIMARY]["recovery_rate"]
        for condition in CONDITIONS
    }
    artifact_acceptance = conditions["one_year_artifact"]["methods"][PRIMARY]["acceptance_rate"]
    ridge_acceptance = conditions["broad_recurring_ridge"]["methods"][PRIMARY]["acceptance_rate"]
    primary_null = nulls["methods"][PRIMARY]

    every_not_inferior = True
    individual_margins: dict[str, object] = {}
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
        "sparse_gain_ge_0_10": gain >= 0.10,
        "sparse_bootstrap_lower_gt_0": interval[0] > 0.0,
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
        "sparse_gain": gain,
        "sparse_gain_paired_bootstrap_95": list(interval),
        "condition_primary_recovery": rates,
        "artifact_primary_acceptance": artifact_acceptance,
        "ridge_primary_acceptance": ridge_acceptance,
        "individual_margins": individual_margins,
        "gates": gates,
        "verdict": "CONTINUE_TO_STRUCTURED_POISSON_TENSOR_BENCHMARK"
        if all(gates.values())
        else "KILL_EVENT_CENTERED_ROBUST_BACKGROUND_DIRECTION",
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    lines = [
        "# Event-centered robust-background confirmation",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "The primary method applies robust low-rank plus column-group-sparse decomposition to annual local-density fields evaluated at observed meteor centers. GhostStream was excluded.",
        "",
        "## Null behavior",
        "",
        "| Method | FPR | Wilson 95% |",
        "|---|---:|---|",
    ]
    for method in METHODS:
        result = payload["test_null_results"]["methods"][method]
        lines.append(f"| {method} | {result['false_positive_rate']:.3f} | {result['wilson_95']} |")
    lines.extend(
        [
            "",
            "## Recovery and artifact acceptance",
            "",
            "| Condition | robust sparse | pooled deviance | recurrent deviance | recurrent raw | SVD residual |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for condition in CONDITIONS:
        methods = payload["conditions"][condition]["methods"]
        metric = "acceptance_rate" if condition in {"one_year_artifact", "broad_recurring_ridge"} else "recovery_rate"
        lines.append(
            f"| {condition} | {methods['robust_group_sparse'][metric]:.3f} "
            f"| {methods['pooled_deviance'][metric]:.3f} "
            f"| {methods['recurrent_deviance'][metric]:.3f} "
            f"| {methods['recurrent_raw'][metric]:.3f} "
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
            f"- selected radius: {external['selected_radius']}",
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
            seed=703001 + index * 1000,
        )
        for index, condition in enumerate(CONDITIONS)
    }
    external = evaluate_m2026(pools, thresholds)
    decision = decide(test_null_results, conditions, external)
    payload = {
        "configuration": {
            "years": YEARS,
            "events_per_year": voxel.EVENTS_PER_YEAR,
            "radii": RADII,
            "outer_multiplier": OUTER_MULTIPLIER,
            "rpca_lambda": voxel.RPCA_LAMBDA,
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
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = markdown_report(payload)
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
