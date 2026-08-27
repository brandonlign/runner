from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.spatial import cKDTree

import audit_multinetwork as audit

ROOT = Path("stream_fdr_stage0")
OUT_DIR = ROOT / "results" / "shared_scan_pilot"
NETWORKS = ("CAMS", "GMN", "EDMOND", "SonotaCo")
METHODS = ("shared_loo", "pooled", "max_network", "second_network", "shared_sum")
PRIMARY = "shared_loo"

WINDOW_HALF_WIDTH_DEG = 10.0
BACKGROUND_PER_NETWORK = 600
CALIBRATION_NULL_SCENES = 36
TEST_NULL_SCENES = 36
INJECTION_REPLICATES = 32
RADII = (0.8, 1.0, 1.2)
OUTER_MULTIPLIER = 2.5
DETECTION_DISTANCE = 1.5
MIN_INNER_COUNT = 3

LON_SCALE_DEG = 3.0
LAT_SCALE_DEG = 3.0
VG_SCALE_KM_S = 2.0
LON_EMBED_SCALE = 1.0 / math.radians(LON_SCALE_DEG)

INJECTION_PATTERNS = {
    "balanced_weak": {"CAMS": 4, "GMN": 4, "EDMOND": 4, "SonotaCo": 4},
    "heterogeneous_weak": {"CAMS": 4, "GMN": 6, "EDMOND": 3, "SonotaCo": 3},
    "three_network_weak": {"CAMS": 4, "GMN": 5, "EDMOND": 0, "SonotaCo": 4},
    "gmn_only_artifact": {"CAMS": 0, "GMN": 10, "EDMOND": 0, "SonotaCo": 0},
    "strong_shared": {"CAMS": 8, "GMN": 8, "EDMOND": 8, "SonotaCo": 8},
}


@dataclass(frozen=True)
class NetworkData:
    solar_longitude: np.ndarray
    raw_features: np.ndarray  # sun-centered ecliptic longitude, ecliptic latitude, Vg


@dataclass(frozen=True)
class MethodResult:
    score: float
    candidate_raw: np.ndarray
    candidate_embedding: np.ndarray


def circular_delta_array(values: np.ndarray, center: float) -> np.ndarray:
    return (values - center + 180.0) % 360.0 - 180.0


def raw_to_embedding(raw: np.ndarray) -> np.ndarray:
    longitude_radians = np.radians(raw[:, 0])
    return np.column_stack(
        [
            np.cos(longitude_radians) * LON_EMBED_SCALE,
            np.sin(longitude_radians) * LON_EMBED_SCALE,
            raw[:, 1] / LAT_SCALE_DEG,
            raw[:, 2] / VG_SCALE_KM_S,
        ]
    )


def load_network(name: str, spec: dict[str, str]) -> NetworkData:
    path = audit.DATA_DIR / f"{name.lower()}_shober_2026_subset.csv"
    audit.download(spec["url"], path)
    digest = audit.md5sum(path)
    if digest != spec["md5"]:
        raise RuntimeError(f"{name}: MD5 mismatch; expected {spec['md5']}, got {digest}")

    solar_longitudes: list[float] = []
    raw_features: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        columns = {
            semantic: audit.pick_column(header, aliases)
            for semantic, aliases in audit.ALIASES.items()
        }
        required = ("solar_longitude", "ra_geo", "dec_geo", "vg")
        if not all(columns.get(key) for key in required):
            raise RuntimeError(f"{name}: incompatible columns: {columns}")

        for row in reader:
            year = audit.parse_year(row, columns)
            ls = audit.as_float(row.get(columns["solar_longitude"], ""))
            ra = audit.as_float(row.get(columns["ra_geo"], ""))
            dec = audit.as_float(row.get(columns["dec_geo"], ""))
            vg = audit.as_float(row.get(columns["vg"], ""))
            if None in (year, ls, ra, dec, vg):
                continue
            assert year is not None and ls is not None and ra is not None and dec is not None and vg is not None
            if not (1800 <= year <= 2200 and 0 <= ls < 360 and 0 <= ra < 360 and -90 <= dec <= 90 and 5 <= vg <= 80):
                continue
            ecliptic_longitude, ecliptic_latitude = audit.equatorial_to_ecliptic(ra, dec)
            sun_centered_longitude = audit.wrap180(ecliptic_longitude - ls)
            solar_longitudes.append(ls)
            raw_features.append((sun_centered_longitude, ecliptic_latitude, vg))

    return NetworkData(
        solar_longitude=np.asarray(solar_longitudes, dtype=np.float64),
        raw_features=np.asarray(raw_features, dtype=np.float64),
    )


def choose_scene_longitude(rng: np.random.Generator) -> float:
    while True:
        center = float(rng.uniform(0.0, 360.0))
        # Keep the M2026-A1 region untouched until the external control.
        if abs(audit.wrap180(center - 10.0)) >= 35.0:
            return center


def sample_background_scene(
    data: dict[str, NetworkData],
    center_ls: float,
    rng: np.random.Generator,
    per_network: int = BACKGROUND_PER_NETWORK,
) -> dict[str, np.ndarray]:
    scene: dict[str, np.ndarray] = {}
    for name in NETWORKS:
        network = data[name]
        mask = np.abs(circular_delta_array(network.solar_longitude, center_ls)) <= WINDOW_HALF_WIDTH_DEG
        indices = np.flatnonzero(mask)
        if len(indices) < max(200, per_network // 2):
            raise RuntimeError(f"{name}: only {len(indices)} events near solar longitude {center_ls:.2f}")
        take = min(per_network, len(indices))
        chosen = rng.choice(indices, size=take, replace=False)
        scene[name] = network.raw_features[chosen].copy()
    return scene


def choose_injection_center(scene: dict[str, np.ndarray], rng: np.random.Generator) -> np.ndarray:
    # Select a physically occupied point without optimizing for low or high background.
    source_network = NETWORKS[int(rng.integers(0, len(NETWORKS)))]
    source = scene[source_network]
    return source[int(rng.integers(0, len(source)))].copy()


def inject_shared_component(
    scene: dict[str, np.ndarray],
    pattern: dict[str, int],
    center: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    injected: dict[str, np.ndarray] = {}
    for name in NETWORKS:
        count = int(pattern[name])
        background = scene[name]
        if count <= 0:
            injected[name] = background.copy()
            continue
        network_offset = rng.normal(0.0, [0.25, 0.25, 0.15], size=3)
        events = center + network_offset + rng.normal(
            0.0,
            [0.90, 0.90, 0.60],
            size=(count, 3),
        )
        events[:, 0] = (events[:, 0] + 180.0) % 360.0 - 180.0
        injected[name] = np.vstack([background, events])
    return injected


def poisson_excess_llr(inner: np.ndarray, outer: np.ndarray, radius: float) -> np.ndarray:
    shell = np.maximum(outer - inner, 0)
    outer_radius = OUTER_MULTIPLIER * radius
    volume_ratio = radius**3 / (outer_radius**3 - radius**3)
    expected = (shell + 0.5) * volume_ratio
    observed = inner.astype(np.float64)
    score = np.zeros_like(observed)
    valid = (observed >= MIN_INNER_COUNT) & (observed > expected)
    score[valid] = observed[valid] * np.log(observed[valid] / expected[valid]) - (
        observed[valid] - expected[valid]
    )
    return score


def scan_scene(scene: dict[str, np.ndarray], radius: float) -> dict[str, MethodResult]:
    raw_candidates = np.vstack([scene[name] for name in NETWORKS])
    candidate_embedding = raw_to_embedding(raw_candidates)
    network_embeddings = {name: raw_to_embedding(scene[name]) for name in NETWORKS}

    per_network_scores: list[np.ndarray] = []
    for name in NETWORKS:
        tree = cKDTree(network_embeddings[name])
        inner = tree.query_ball_point(candidate_embedding, radius, return_length=True)
        outer = tree.query_ball_point(
            candidate_embedding,
            OUTER_MULTIPLIER * radius,
            return_length=True,
        )
        per_network_scores.append(poisson_excess_llr(inner, outer, radius))

    matrix = np.vstack(per_network_scores)
    positive_support = np.sum(matrix > 0.0, axis=0)
    total = np.sum(matrix, axis=0)
    largest = np.max(matrix, axis=0)
    sorted_scores = np.sort(matrix, axis=0)

    shared_loo = np.where(positive_support >= 2, total - largest, 0.0)
    shared_sum = np.where(positive_support >= 2, total, 0.0)
    max_network = largest
    second_network = sorted_scores[-2]

    pooled_embedding = np.vstack([network_embeddings[name] for name in NETWORKS])
    pooled_tree = cKDTree(pooled_embedding)
    pooled_inner = pooled_tree.query_ball_point(candidate_embedding, radius, return_length=True)
    pooled_outer = pooled_tree.query_ball_point(
        candidate_embedding,
        OUTER_MULTIPLIER * radius,
        return_length=True,
    )
    pooled = poisson_excess_llr(pooled_inner, pooled_outer, radius)

    score_arrays = {
        "shared_loo": shared_loo,
        "pooled": pooled,
        "max_network": max_network,
        "second_network": second_network,
        "shared_sum": shared_sum,
    }
    results: dict[str, MethodResult] = {}
    for method, values in score_arrays.items():
        index = int(np.argmax(values))
        results[method] = MethodResult(
            score=float(values[index]),
            candidate_raw=raw_candidates[index].copy(),
            candidate_embedding=candidate_embedding[index].copy(),
        )
    return results


def distance_to_truth(result: MethodResult, truth: np.ndarray) -> float:
    truth_embedding = raw_to_embedding(truth.reshape(1, 3))[0]
    return float(np.linalg.norm(result.candidate_embedding - truth_embedding))


def empirical_threshold(values: Iterable[float], quantile: float = 0.95) -> float:
    array = np.sort(np.asarray(list(values), dtype=np.float64))
    index = int(math.ceil(quantile * len(array))) - 1
    index = max(0, min(index, len(array) - 1))
    return float(array[index])


def make_null_scores(
    data: dict[str, NetworkData],
    radius: float,
    scene_count: int,
    seed: int,
) -> dict[str, list[float]]:
    rng = np.random.default_rng(seed)
    scores = {method: [] for method in METHODS}
    completed = 0
    attempts = 0
    while completed < scene_count:
        attempts += 1
        if attempts > scene_count * 20:
            raise RuntimeError("Could not construct enough null scenes")
        center_ls = choose_scene_longitude(rng)
        try:
            scene = sample_background_scene(data, center_ls, rng)
        except RuntimeError:
            continue
        results = scan_scene(scene, radius)
        for method in METHODS:
            scores[method].append(results[method].score)
        completed += 1
    return scores


def evaluate_pattern(
    data: dict[str, NetworkData],
    radius: float,
    thresholds: dict[str, float],
    pattern: dict[str, int],
    seed: int,
) -> dict[str, dict[str, float | int]]:
    rng = np.random.default_rng(seed)
    accepted = {method: 0 for method in METHODS}
    located = {method: 0 for method in METHODS}
    completed = 0
    attempts = 0
    while completed < INJECTION_REPLICATES:
        attempts += 1
        if attempts > INJECTION_REPLICATES * 20:
            raise RuntimeError("Could not construct enough injection scenes")
        center_ls = choose_scene_longitude(rng)
        try:
            background = sample_background_scene(data, center_ls, rng)
        except RuntimeError:
            continue
        truth = choose_injection_center(background, rng)
        scene = inject_shared_component(background, pattern, truth, rng)
        results = scan_scene(scene, radius)
        for method in METHODS:
            passes_score = results[method].score > thresholds[method]
            is_near = distance_to_truth(results[method], truth) <= DETECTION_DISTANCE
            accepted[method] += int(passes_score)
            located[method] += int(passes_score and is_near)
        completed += 1

    return {
        method: {
            "accepted": accepted[method],
            "located": located[method],
            "acceptance_rate": accepted[method] / INJECTION_REPLICATES,
            "recovery_rate": located[method] / INJECTION_REPLICATES,
        }
        for method in METHODS
    }


def m2026_reference_raw() -> np.ndarray:
    solar_longitude = 11.8
    ra = 209.0
    dec = -20.3
    vg = 29.8
    ecliptic_longitude, ecliptic_latitude = audit.equatorial_to_ecliptic(ra, dec)
    return np.asarray(
        [audit.wrap180(ecliptic_longitude - solar_longitude), ecliptic_latitude, vg],
        dtype=np.float64,
    )


def evaluate_m2026(
    data: dict[str, NetworkData],
    radius: float,
    thresholds: dict[str, float],
    seed: int,
) -> dict[str, dict[str, float | bool | list[float]]]:
    rng = np.random.default_rng(seed)
    scene = sample_background_scene(data, center_ls=10.0, rng=rng)
    reference = m2026_reference_raw()
    results = scan_scene(scene, radius)
    return {
        method: {
            "score": results[method].score,
            "threshold": thresholds[method],
            "accepted": results[method].score > thresholds[method],
            "distance_to_reference": distance_to_truth(results[method], reference),
            "near_reference": distance_to_truth(results[method], reference) <= 2.0,
            "candidate_raw": results[method].candidate_raw.tolist(),
        }
        for method in METHODS
    }


def run_radius(data: dict[str, NetworkData], radius: float) -> dict[str, object]:
    seed_offset = int(round(radius * 1000))
    calibration = make_null_scores(
        data,
        radius,
        CALIBRATION_NULL_SCENES,
        seed=41000 + seed_offset,
    )
    thresholds = {method: empirical_threshold(calibration[method]) for method in METHODS}
    test_null = make_null_scores(
        data,
        radius,
        TEST_NULL_SCENES,
        seed=51000 + seed_offset,
    )
    test_fpr = {
        method: float(np.mean(np.asarray(test_null[method]) > thresholds[method]))
        for method in METHODS
    }

    injections = {}
    for pattern_index, (name, pattern) in enumerate(INJECTION_PATTERNS.items()):
        injections[name] = evaluate_pattern(
            data,
            radius,
            thresholds,
            pattern,
            seed=61000 + seed_offset + pattern_index * 1000,
        )

    external = evaluate_m2026(
        data,
        radius,
        thresholds,
        seed=71000 + seed_offset,
    )
    return {
        "radius": radius,
        "thresholds": thresholds,
        "calibration_null_scores": calibration,
        "test_null_scores": test_null,
        "test_false_positive_rate": test_fpr,
        "injections": injections,
        "external_m2026_control": external,
    }


def decide(results: dict[str, dict[str, object]]) -> dict[str, object]:
    central = results["1.0"]
    injections = central["injections"]
    eligible_baselines = ("pooled", "max_network", "second_network")

    balanced_primary = injections["balanced_weak"][PRIMARY]["recovery_rate"]
    balanced_best = max(
        injections["balanced_weak"][method]["recovery_rate"]
        for method in eligible_baselines
    )
    heterogeneous_primary = injections["heterogeneous_weak"][PRIMARY]["recovery_rate"]
    heterogeneous_best = max(
        injections["heterogeneous_weak"][method]["recovery_rate"]
        for method in eligible_baselines
    )
    artifact_acceptance = injections["gmn_only_artifact"][PRIMARY]["acceptance_rate"]
    strong_recovery = injections["strong_shared"][PRIMARY]["recovery_rate"]
    external = central["external_m2026_control"][PRIMARY]

    alternate_recoveries = []
    for radius in ("0.8", "1.2"):
        alternate_recoveries.extend(
            [
                results[radius]["injections"]["balanced_weak"][PRIMARY]["recovery_rate"],
                results[radius]["injections"]["heterogeneous_weak"][PRIMARY]["recovery_rate"],
            ]
        )
    central_floor = min(balanced_primary, heterogeneous_primary)
    worst_alternate_drop = max(
        central_floor - min(alternate_recoveries),
        0.0,
    )

    gates = {
        "independent_null_fpr_le_0_15": central["test_false_positive_rate"][PRIMARY] <= 0.15,
        "balanced_gain_ge_0_10": balanced_primary - balanced_best >= 0.10,
        "heterogeneous_gain_ge_0_10": heterogeneous_primary - heterogeneous_best >= 0.10,
        "gmn_only_acceptance_le_0_10": artifact_acceptance <= 0.10,
        "strong_shared_recovery_ge_0_80": strong_recovery >= 0.80,
        "m2026_accepted_near_reference": bool(external["accepted"] and external["near_reference"]),
        "alternate_radius_drop_le_0_20": worst_alternate_drop <= 0.20,
    }
    return {
        "primary_method": PRIMARY,
        "balanced_primary_recovery": balanced_primary,
        "balanced_best_eligible_baseline": balanced_best,
        "heterogeneous_primary_recovery": heterogeneous_primary,
        "heterogeneous_best_eligible_baseline": heterogeneous_best,
        "artifact_acceptance": artifact_acceptance,
        "strong_shared_recovery": strong_recovery,
        "worst_alternate_radius_drop": worst_alternate_drop,
        "gates": gates,
        "verdict": "CONTINUE_TO_FULL_SHARED_MODEL_BENCHMARK"
        if all(gates.values())
        else "KILL_OR_REDESIGN_SHARED_NETWORK_FORMULATION",
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    lines = [
        "# Shared-support surrogate pilot",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "This runner-only pilot tests the core shared-network hypothesis before any full hierarchical model is built. GhostStream was not used.",
        "",
        "## Central radius results",
        "",
        "| Method | Null FPR | Balanced recovery | Heterogeneous recovery | Three-network recovery | GMN-only acceptance | Strong recovery |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    central = payload["results_by_radius"]["1.0"]
    for method in METHODS:
        lines.append(
            f"| {method} | {central['test_false_positive_rate'][method]:.3f} "
            f"| {central['injections']['balanced_weak'][method]['recovery_rate']:.3f} "
            f"| {central['injections']['heterogeneous_weak'][method]['recovery_rate']:.3f} "
            f"| {central['injections']['three_network_weak'][method]['recovery_rate']:.3f} "
            f"| {central['injections']['gmn_only_artifact'][method]['acceptance_rate']:.3f} "
            f"| {central['injections']['strong_shared'][method]['recovery_rate']:.3f} |"
        )
    lines.extend([
        "",
        "## Frozen gates",
        "",
    ])
    for gate, passed in decision["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend([
        "",
        "## External M2026-A1 control",
        "",
    ])
    for method in METHODS:
        result = central["external_m2026_control"][method]
        lines.append(
            f"- `{method}`: accepted={result['accepted']}, near={result['near_reference']}, "
            f"distance={result['distance_to_reference']:.3f}, score={result['score']:.3f}, threshold={result['threshold']:.3f}"
        )
    lines.extend([
        "",
        "The M2026-A1 control is an external positive benchmark only. It was excluded from null calibration, injection design, and threshold selection.",
    ])
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {name: load_network(name, audit.DATASETS[name]) for name in NETWORKS}
    results_by_radius = {str(radius): run_radius(data, radius) for radius in RADII}
    decision = decide(results_by_radius)
    payload = {
        "configuration": {
            "networks": NETWORKS,
            "window_half_width_deg": WINDOW_HALF_WIDTH_DEG,
            "background_per_network": BACKGROUND_PER_NETWORK,
            "calibration_null_scenes": CALIBRATION_NULL_SCENES,
            "test_null_scenes": TEST_NULL_SCENES,
            "injection_replicates": INJECTION_REPLICATES,
            "radii": RADII,
            "outer_multiplier": OUTER_MULTIPLIER,
            "detection_distance": DETECTION_DISTANCE,
            "minimum_inner_count": MIN_INNER_COUNT,
            "injection_patterns": INJECTION_PATTERNS,
            "python": os.sys.version,
            "numpy": np.__version__,
        },
        "network_event_counts": {name: len(data[name].solar_longitude) for name in NETWORKS},
        "results_by_radius": results_by_radius,
        "decision": decision,
    }
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = markdown_report(payload)
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
