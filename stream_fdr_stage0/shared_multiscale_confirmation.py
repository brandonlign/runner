from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.spatial import cKDTree

import shared_scan_pilot as v1

ROOT = Path("stream_fdr_stage0")
OUT_DIR = ROOT / "results" / "shared_multiscale_confirmation"
NETWORKS = v1.NETWORKS
METHODS = v1.METHODS
PRIMARY = v1.PRIMARY
ELIGIBLE_BASELINES = ("pooled", "max_network", "second_network")
RADII = (0.70, 0.90, 1.10, 1.30)
CALIBRATION_NULL_SCENES = 72
TEST_NULL_SCENES = 72
INJECTION_REPLICATES = 96
DETECTION_DISTANCE = 1.5
M2026_DISTANCE = 2.0
BOOTSTRAP_REPLICATES = 5000

DISPERSIONS = {
    "compact": np.asarray([0.60, 0.60, 0.40], dtype=np.float64),
    "nominal": np.asarray([0.90, 0.90, 0.60], dtype=np.float64),
    "diffuse": np.asarray([1.50, 1.50, 1.00], dtype=np.float64),
}
BALANCED_PATTERN = {"CAMS": 4, "GMN": 4, "EDMOND": 4, "SonotaCo": 4}
HETEROGENEOUS_PATTERN = {"CAMS": 4, "GMN": 6, "EDMOND": 3, "SonotaCo": 3}
GMN_ONLY_PATTERN = {"CAMS": 0, "GMN": 10, "EDMOND": 0, "SonotaCo": 0}
STRONG_PATTERN = {"CAMS": 8, "GMN": 8, "EDMOND": 8, "SonotaCo": 8}
DROPOUT_NETWORKS = ("CAMS", "EDMOND", "SonotaCo")
DROPOUT_PATTERN = {"CAMS": 4, "EDMOND": 4, "SonotaCo": 4}


@dataclass(frozen=True)
class MultiResult:
    score: float
    candidate_raw: np.ndarray
    candidate_embedding: np.ndarray
    radius: float


def scan_at_radius(
    scene: dict[str, np.ndarray],
    radius: float,
    network_names: tuple[str, ...],
) -> dict[str, v1.MethodResult]:
    raw_candidates = np.vstack([scene[name] for name in network_names])
    candidate_embedding = v1.raw_to_embedding(raw_candidates)
    network_embeddings = {
        name: v1.raw_to_embedding(scene[name])
        for name in network_names
    }

    per_network_scores: list[np.ndarray] = []
    for name in network_names:
        tree = cKDTree(network_embeddings[name])
        inner = tree.query_ball_point(candidate_embedding, radius, return_length=True)
        outer = tree.query_ball_point(
            candidate_embedding,
            v1.OUTER_MULTIPLIER * radius,
            return_length=True,
        )
        per_network_scores.append(v1.poisson_excess_llr(inner, outer, radius))

    matrix = np.vstack(per_network_scores)
    positive_support = np.sum(matrix > 0.0, axis=0)
    total = np.sum(matrix, axis=0)
    largest = np.max(matrix, axis=0)
    sorted_scores = np.sort(matrix, axis=0)

    shared_loo = np.where(positive_support >= 2, total - largest, 0.0)
    shared_sum = np.where(positive_support >= 2, total, 0.0)
    max_network = largest
    second_network = sorted_scores[-2] if len(network_names) >= 2 else np.zeros_like(largest)

    pooled_embedding = np.vstack([network_embeddings[name] for name in network_names])
    pooled_tree = cKDTree(pooled_embedding)
    pooled_inner = pooled_tree.query_ball_point(candidate_embedding, radius, return_length=True)
    pooled_outer = pooled_tree.query_ball_point(
        candidate_embedding,
        v1.OUTER_MULTIPLIER * radius,
        return_length=True,
    )
    pooled = v1.poisson_excess_llr(pooled_inner, pooled_outer, radius)

    arrays = {
        "shared_loo": shared_loo,
        "pooled": pooled,
        "max_network": max_network,
        "second_network": second_network,
        "shared_sum": shared_sum,
    }
    results: dict[str, v1.MethodResult] = {}
    for method, values in arrays.items():
        index = int(np.argmax(values))
        results[method] = v1.MethodResult(
            score=float(values[index]),
            candidate_raw=raw_candidates[index].copy(),
            candidate_embedding=candidate_embedding[index].copy(),
        )
    return results


def multiscale_scan(
    scene: dict[str, np.ndarray],
    network_names: tuple[str, ...] = NETWORKS,
) -> dict[str, MultiResult]:
    best: dict[str, MultiResult] = {}
    for radius in RADII:
        radius_results = scan_at_radius(scene, radius, network_names)
        for method, result in radius_results.items():
            previous = best.get(method)
            if previous is None or result.score > previous.score:
                best[method] = MultiResult(
                    score=result.score,
                    candidate_raw=result.candidate_raw,
                    candidate_embedding=result.candidate_embedding,
                    radius=radius,
                )
    return best


def inject_component(
    scene: dict[str, np.ndarray],
    pattern: dict[str, int],
    center: np.ndarray,
    scatter: np.ndarray,
    rng: np.random.Generator,
    network_names: tuple[str, ...] = NETWORKS,
) -> dict[str, np.ndarray]:
    result = {name: scene[name].copy() for name in scene}
    for name in network_names:
        count = int(pattern.get(name, 0))
        if count <= 0:
            continue
        offset = rng.normal(0.0, [0.25, 0.25, 0.15], size=3)
        events = center + offset + rng.normal(0.0, scatter, size=(count, 3))
        events[:, 0] = (events[:, 0] + 180.0) % 360.0 - 180.0
        result[name] = np.vstack([result[name], events])
    return result


def result_distance(result: MultiResult, truth: np.ndarray) -> float:
    truth_embedding = v1.raw_to_embedding(truth.reshape(1, 3))[0]
    return float(np.linalg.norm(result.candidate_embedding - truth_embedding))


def empirical_threshold(values: Iterable[float], quantile: float = 0.95) -> float:
    array = np.sort(np.asarray(list(values), dtype=np.float64))
    index = int(math.ceil(quantile * len(array))) - 1
    return float(array[max(0, min(index, len(array) - 1))])


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def paired_bootstrap_interval(
    primary: np.ndarray,
    baseline: np.ndarray,
    seed: int,
) -> tuple[float, float]:
    if primary.shape != baseline.shape:
        raise ValueError("Paired arrays must have matching shapes")
    difference = primary.astype(np.float64) - baseline.astype(np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(difference), size=(BOOTSTRAP_REPLICATES, len(difference)))
    means = np.mean(difference[indices], axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def make_null_scores(
    data: dict[str, v1.NetworkData],
    scene_count: int,
    seed: int,
    network_names: tuple[str, ...] = NETWORKS,
) -> dict[str, list[float]]:
    rng = np.random.default_rng(seed)
    scores = {method: [] for method in METHODS}
    completed = 0
    attempts = 0
    while completed < scene_count:
        attempts += 1
        if attempts > scene_count * 30:
            raise RuntimeError("Could not construct enough null scenes")
        center_ls = v1.choose_scene_longitude(rng)
        try:
            scene = v1.sample_background_scene(data, center_ls, rng)
        except RuntimeError:
            continue
        results = multiscale_scan(scene, network_names)
        for method in METHODS:
            scores[method].append(results[method].score)
        completed += 1
    return scores


def evaluate_condition(
    data: dict[str, v1.NetworkData],
    thresholds: dict[str, float],
    pattern: dict[str, int],
    scatter: np.ndarray,
    seed: int,
    network_names: tuple[str, ...] = NETWORKS,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    accepted = {method: [] for method in METHODS}
    located = {method: [] for method in METHODS}
    selected_radii = {method: [] for method in METHODS}
    completed = 0
    attempts = 0
    while completed < INJECTION_REPLICATES:
        attempts += 1
        if attempts > INJECTION_REPLICATES * 30:
            raise RuntimeError("Could not construct enough injection scenes")
        center_ls = v1.choose_scene_longitude(rng)
        try:
            background = v1.sample_background_scene(data, center_ls, rng)
        except RuntimeError:
            continue
        source_network = network_names[int(rng.integers(0, len(network_names)))]
        source = background[source_network]
        truth = source[int(rng.integers(0, len(source)))].copy()
        scene = inject_component(background, pattern, truth, scatter, rng, network_names)
        results = multiscale_scan(scene, network_names)
        for method in METHODS:
            passes = results[method].score > thresholds[method]
            near = result_distance(results[method], truth) <= DETECTION_DISTANCE
            accepted[method].append(bool(passes))
            located[method].append(bool(passes and near))
            selected_radii[method].append(results[method].radius)
        completed += 1

    summary = {}
    for method in METHODS:
        accepted_array = np.asarray(accepted[method], dtype=bool)
        located_array = np.asarray(located[method], dtype=bool)
        recovery_count = int(np.sum(located_array))
        recovery_ci = wilson_interval(recovery_count, INJECTION_REPLICATES)
        summary[method] = {
            "accepted_count": int(np.sum(accepted_array)),
            "accepted_rate": float(np.mean(accepted_array)),
            "recovery_count": recovery_count,
            "recovery_rate": float(np.mean(located_array)),
            "recovery_wilson_95": list(recovery_ci),
            "located": located_array.astype(int).tolist(),
            "selected_radius_counts": {
                str(radius): int(sum(chosen == radius for chosen in selected_radii[method]))
                for radius in RADII
            },
        }
    return summary


def evaluate_m2026(
    data: dict[str, v1.NetworkData],
    thresholds: dict[str, float],
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    scene = v1.sample_background_scene(data, center_ls=10.0, rng=rng)
    reference = v1.m2026_reference_raw()
    results = multiscale_scan(scene)
    return {
        method: {
            "score": result.score,
            "threshold": thresholds[method],
            "accepted": result.score > thresholds[method],
            "distance_to_reference": result_distance(result, reference),
            "near_reference": result_distance(result, reference) <= M2026_DISTANCE,
            "selected_radius": result.radius,
            "candidate_raw": result.candidate_raw.tolist(),
        }
        for method, result in results.items()
    }


def summarize_null(
    test_scores: dict[str, list[float]],
    thresholds: dict[str, float],
) -> dict[str, object]:
    result = {}
    for method in METHODS:
        exceedances = int(np.sum(np.asarray(test_scores[method]) > thresholds[method]))
        interval = wilson_interval(exceedances, TEST_NULL_SCENES)
        result[method] = {
            "false_positive_count": exceedances,
            "false_positive_rate": exceedances / TEST_NULL_SCENES,
            "wilson_95": list(interval),
        }
    return result


def group_gain(
    conditions: dict[str, dict[str, object]],
    condition_names: list[str],
    seed: int,
) -> dict[str, object]:
    primary = np.concatenate(
        [np.asarray(conditions[name][PRIMARY]["located"], dtype=int) for name in condition_names]
    )
    baseline_arrays = {
        method: np.concatenate(
            [np.asarray(conditions[name][method]["located"], dtype=int) for name in condition_names]
        )
        for method in ELIGIBLE_BASELINES
    }
    best_method = max(baseline_arrays, key=lambda method: float(np.mean(baseline_arrays[method])))
    best = baseline_arrays[best_method]
    interval = paired_bootstrap_interval(primary, best, seed)
    return {
        "primary_mean_recovery": float(np.mean(primary)),
        "best_baseline": best_method,
        "best_baseline_mean_recovery": float(np.mean(best)),
        "gain": float(np.mean(primary - best)),
        "paired_bootstrap_95": list(interval),
    }


def run() -> dict[str, object]:
    data = {name: v1.load_network(name, v1.audit.DATASETS[name]) for name in NETWORKS}

    calibration_scores = make_null_scores(data, CALIBRATION_NULL_SCENES, seed=181001)
    thresholds = {method: empirical_threshold(calibration_scores[method]) for method in METHODS}
    test_scores = make_null_scores(data, TEST_NULL_SCENES, seed=182001)
    null_summary = summarize_null(test_scores, thresholds)

    conditions: dict[str, dict[str, object]] = {}
    condition_index = 0
    balanced_names = []
    heterogeneous_names = []
    for dispersion_name, scatter in DISPERSIONS.items():
        balanced_name = f"balanced_{dispersion_name}"
        heterogeneous_name = f"heterogeneous_{dispersion_name}"
        balanced_names.append(balanced_name)
        heterogeneous_names.append(heterogeneous_name)
        conditions[balanced_name] = evaluate_condition(
            data,
            thresholds,
            BALANCED_PATTERN,
            scatter,
            seed=183001 + condition_index * 1000,
        )
        condition_index += 1
        conditions[heterogeneous_name] = evaluate_condition(
            data,
            thresholds,
            HETEROGENEOUS_PATTERN,
            scatter,
            seed=183001 + condition_index * 1000,
        )
        condition_index += 1

    conditions["gmn_only_artifact"] = evaluate_condition(
        data,
        thresholds,
        GMN_ONLY_PATTERN,
        DISPERSIONS["nominal"],
        seed=190001,
    )
    conditions["strong_shared"] = evaluate_condition(
        data,
        thresholds,
        STRONG_PATTERN,
        DISPERSIONS["nominal"],
        seed=191001,
    )

    dropout_calibration = make_null_scores(
        data,
        CALIBRATION_NULL_SCENES,
        seed=192001,
        network_names=DROPOUT_NETWORKS,
    )
    dropout_thresholds = {
        method: empirical_threshold(dropout_calibration[method])
        for method in METHODS
    }
    dropout_test = make_null_scores(
        data,
        TEST_NULL_SCENES,
        seed=193001,
        network_names=DROPOUT_NETWORKS,
    )
    dropout_null_summary = summarize_null(dropout_test, dropout_thresholds)
    dropout_condition = evaluate_condition(
        data,
        dropout_thresholds,
        DROPOUT_PATTERN,
        DISPERSIONS["nominal"],
        seed=194001,
        network_names=DROPOUT_NETWORKS,
    )

    balanced_gain = group_gain(conditions, balanced_names, seed=195001)
    heterogeneous_gain = group_gain(conditions, heterogeneous_names, seed=196001)
    external = evaluate_m2026(data, thresholds, seed=197001)

    individual_not_inferior = True
    individual_comparisons = {}
    for name in balanced_names + heterogeneous_names:
        primary_rate = conditions[name][PRIMARY]["recovery_rate"]
        best_method = max(
            ELIGIBLE_BASELINES,
            key=lambda method: conditions[name][method]["recovery_rate"],
        )
        best_rate = conditions[name][best_method]["recovery_rate"]
        margin = primary_rate - best_rate
        individual_comparisons[name] = {
            "primary": primary_rate,
            "best_baseline": best_method,
            "best_baseline_rate": best_rate,
            "margin": margin,
        }
        individual_not_inferior = individual_not_inferior and margin >= -0.10

    artifact_rate = conditions["gmn_only_artifact"][PRIMARY]["recovery_rate"]
    strong_rate = conditions["strong_shared"][PRIMARY]["recovery_rate"]
    dropout_primary = dropout_condition[PRIMARY]["recovery_rate"]
    dropout_pooled = dropout_condition["pooled"]["recovery_rate"]
    primary_null = null_summary[PRIMARY]

    gates = {
        "null_rate_le_0_10": primary_null["false_positive_rate"] <= 0.10,
        "null_wilson_upper_le_0_15": primary_null["wilson_95"][1] <= 0.15,
        "balanced_mean_gain_ge_0_10": balanced_gain["gain"] >= 0.10,
        "balanced_bootstrap_lower_gt_0": balanced_gain["paired_bootstrap_95"][0] > 0.0,
        "heterogeneous_mean_gain_ge_0_10": heterogeneous_gain["gain"] >= 0.10,
        "heterogeneous_bootstrap_lower_gt_0": heterogeneous_gain["paired_bootstrap_95"][0] > 0.0,
        "every_dispersion_not_inferior_by_0_10": individual_not_inferior,
        "gmn_only_artifact_recovery_le_0_10": artifact_rate <= 0.10,
        "strong_shared_recovery_ge_0_90": strong_rate >= 0.90,
        "m2026_accepted_near_reference": bool(
            external[PRIMARY]["accepted"] and external[PRIMARY]["near_reference"]
        ),
        "dropout_recovery_ge_0_50": dropout_primary >= 0.50,
        "dropout_gain_over_pooled_ge_0_05": dropout_primary - dropout_pooled >= 0.05,
    }

    decision = {
        "primary_method": PRIMARY,
        "balanced_group": balanced_gain,
        "heterogeneous_group": heterogeneous_gain,
        "individual_comparisons": individual_comparisons,
        "artifact_recovery": artifact_rate,
        "strong_shared_recovery": strong_rate,
        "dropout_primary_recovery": dropout_primary,
        "dropout_pooled_recovery": dropout_pooled,
        "gates": gates,
        "verdict": "CONTINUE_TO_FULL_SHARED_MODEL_BENCHMARK"
        if all(gates.values())
        else "KILL_OR_REDESIGN_SHARED_NETWORK_FORMULATION",
    }

    return {
        "configuration": {
            "networks": NETWORKS,
            "radii": RADII,
            "calibration_null_scenes": CALIBRATION_NULL_SCENES,
            "test_null_scenes": TEST_NULL_SCENES,
            "injection_replicates": INJECTION_REPLICATES,
            "dispersions": {name: values.tolist() for name, values in DISPERSIONS.items()},
            "patterns": {
                "balanced": BALANCED_PATTERN,
                "heterogeneous": HETEROGENEOUS_PATTERN,
                "gmn_only": GMN_ONLY_PATTERN,
                "strong": STRONG_PATTERN,
                "dropout": DROPOUT_PATTERN,
            },
            "dropout_networks": DROPOUT_NETWORKS,
            "python": os.sys.version,
            "numpy": np.__version__,
        },
        "network_event_counts": {name: len(data[name].solar_longitude) for name in NETWORKS},
        "thresholds": thresholds,
        "null_summary": null_summary,
        "conditions": conditions,
        "dropout_thresholds": dropout_thresholds,
        "dropout_null_summary": dropout_null_summary,
        "dropout_condition": dropout_condition,
        "external_m2026_control": external,
        "decision": decision,
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    lines = [
        "# Multiplicity-calibrated multiscale confirmation",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "The maximum over candidate locations and the complete frozen scale grid is calibrated under the null. GhostStream was excluded.",
        "",
        "## Primary summary",
        "",
        f"- independent-null FPR: {payload['null_summary'][PRIMARY]['false_positive_rate']:.3f}",
        f"- independent-null Wilson 95% interval: {payload['null_summary'][PRIMARY]['wilson_95']}",
        f"- balanced mean recovery: {decision['balanced_group']['primary_mean_recovery']:.3f}",
        f"- balanced best baseline: {decision['balanced_group']['best_baseline']} at {decision['balanced_group']['best_baseline_mean_recovery']:.3f}",
        f"- balanced gain: {decision['balanced_group']['gain']:.3f}, paired-bootstrap 95% {decision['balanced_group']['paired_bootstrap_95']}",
        f"- heterogeneous mean recovery: {decision['heterogeneous_group']['primary_mean_recovery']:.3f}",
        f"- heterogeneous best baseline: {decision['heterogeneous_group']['best_baseline']} at {decision['heterogeneous_group']['best_baseline_mean_recovery']:.3f}",
        f"- heterogeneous gain: {decision['heterogeneous_group']['gain']:.3f}, paired-bootstrap 95% {decision['heterogeneous_group']['paired_bootstrap_95']}",
        f"- GMN-only artifact recovery: {decision['artifact_recovery']:.3f}",
        f"- strong shared recovery: {decision['strong_shared_recovery']:.3f}",
        f"- no-GMN recovery: {decision['dropout_primary_recovery']:.3f} versus pooled {decision['dropout_pooled_recovery']:.3f}",
        "",
        "## Recovery by condition",
        "",
        "| Condition | shared_loo | pooled | max_network | second_network | shared_sum |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, condition in payload["conditions"].items():
        lines.append(
            f"| {name} | {condition['shared_loo']['recovery_rate']:.3f} "
            f"| {condition['pooled']['recovery_rate']:.3f} "
            f"| {condition['max_network']['recovery_rate']:.3f} "
            f"| {condition['second_network']['recovery_rate']:.3f} "
            f"| {condition['shared_sum']['recovery_rate']:.3f} |"
        )
    lines.extend([
        "",
        "## Frozen gates",
        "",
    ])
    for gate, passed in decision["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    external = payload["external_m2026_control"][PRIMARY]
    lines.extend([
        "",
        "## External M2026-A1 control",
        "",
        f"- accepted: {external['accepted']}",
        f"- near published reference: {external['near_reference']}",
        f"- distance: {external['distance_to_reference']:.3f}",
        f"- score / threshold: {external['score']:.3f} / {external['threshold']:.3f}",
        f"- selected radius: {external['selected_radius']}",
    ])
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = run()
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = markdown_report(payload)
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
