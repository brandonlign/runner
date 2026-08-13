from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.special import logsumexp

import predictive_eprocess_pilot as v1

ROOT = Path("stream_fdr_stage0")
OUT_DIR = ROOT / "results" / "matched_analog_eprocess"
YEARS = v1.YEARS
ORDERS = v1.ORDERS
RADII = v1.RADII
PRIMARY = "multi_order_adaptive"
METHODS = v1.METHODS
NONADAPTIVE_BASELINES = ("fixed_candidate", "single_split")
TARGET_EVENTS_PER_YEAR = 60
CONTROL_EVENTS_PER_YEAR = 60
CONTROL_OFFSETS = tuple(range(40, 321, 20))
MIN_CONTROLS_PER_YEAR = 10
WINDOW_HALF_WIDTH_DEG = 10.0
LOG_THRESHOLD = math.log(10.0)
P_CALIBRATOR_LOG_CONSTANT = math.log(0.5)
DETECTION_DISTANCE = 1.5
M2026_DISTANCE = 2.0
NULL_SCENES = 128
INJECTION_REPLICATES = 96
BOOTSTRAP_REPLICATES = 8000

NOMINAL_SCATTER = np.asarray([1.0, 1.0, 0.65], dtype=np.float64)
DIFFUSE_SCATTER = np.asarray([2.0, 2.0, 1.30], dtype=np.float64)
CONDITIONS = (
    "recurring_moderate",
    "recurring_sparse",
    "intermittent_sparse",
    "late_onset_sparse",
    "diffuse_recurring",
    "strong_recurring",
    "one_year_artifact",
)


@dataclass(frozen=True)
class YearPool:
    solar_extended: np.ndarray
    raw_extended: np.ndarray


@dataclass(frozen=True)
class AnalogScene:
    center_solar_longitude: float
    target_by_year: dict[int, np.ndarray]
    controls_by_year: dict[int, tuple[np.ndarray, ...]]
    control_offsets_by_year: dict[int, tuple[int, ...]]


@dataclass(frozen=True)
class PreparedAnalogScene:
    target: v1.PreparedScene
    control_embeddings_by_year: dict[int, tuple[np.ndarray, ...]]


@dataclass(frozen=True)
class Evaluation:
    log_evalues: dict[str, float]
    order_log_evalues: list[float]
    localization_raw: np.ndarray | None
    localization_radius: float | None


def make_year_pools() -> tuple[dict[int, v1.YearCatalog], dict[int, YearPool]]:
    catalogs = v1.load_gmn_by_year()
    pools: dict[int, YearPool] = {}
    for year in YEARS:
        catalog = catalogs[year]
        order = np.argsort(catalog.solar_longitude)
        solar = catalog.solar_longitude[order]
        raw = catalog.raw_features[order]
        pools[year] = YearPool(
            solar_extended=np.concatenate([solar, solar + 360.0]),
            raw_extended=np.vstack([raw, raw]),
        )
    return catalogs, pools


def window_indices(pool: YearPool, center: float) -> np.ndarray:
    normalized = center % 360.0
    query_center = normalized + 360.0 if normalized < WINDOW_HALF_WIDTH_DEG else normalized
    lower = query_center - WINDOW_HALF_WIDTH_DEG
    upper = query_center + WINDOW_HALF_WIDTH_DEG
    left = int(np.searchsorted(pool.solar_extended, lower, side="left"))
    right = int(np.searchsorted(pool.solar_extended, upper, side="right"))
    return np.arange(left, right, dtype=np.int64)


def sample_window(
    pool: YearPool,
    center: float,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray | None:
    indices = window_indices(pool, center)
    if len(indices) < count:
        return None
    chosen = rng.choice(indices, size=count, replace=False)
    return pool.raw_extended[chosen].copy()


def choose_target_longitude(rng: np.random.Generator) -> float:
    while True:
        center = float(rng.uniform(0.0, 360.0))
        if abs(v1.audit.wrap180(center - 10.0)) >= 35.0:
            return center


def build_analog_scene_at_center(
    pools: dict[int, YearPool],
    center: float,
    rng: np.random.Generator,
) -> AnalogScene:
    target_by_year: dict[int, np.ndarray] = {}
    controls_by_year: dict[int, tuple[np.ndarray, ...]] = {}
    control_offsets_by_year: dict[int, tuple[int, ...]] = {}

    for year in YEARS:
        target = sample_window(
            pools[year], center, TARGET_EVENTS_PER_YEAR, rng
        )
        if target is None:
            raise RuntimeError(
                f"Insufficient target events for {year} near {center:.2f}"
            )
        controls: list[np.ndarray] = []
        offsets: list[int] = []
        for offset in CONTROL_OFFSETS:
            control = sample_window(
                pools[year],
                center + offset,
                CONTROL_EVENTS_PER_YEAR,
                rng,
            )
            if control is not None:
                controls.append(control)
                offsets.append(offset)
        if len(controls) < MIN_CONTROLS_PER_YEAR:
            raise RuntimeError(
                f"Only {len(controls)} analogue windows for {year} near {center:.2f}"
            )
        target_by_year[year] = target
        controls_by_year[year] = tuple(controls)
        control_offsets_by_year[year] = tuple(offsets)

    return AnalogScene(
        center_solar_longitude=center,
        target_by_year=target_by_year,
        controls_by_year=controls_by_year,
        control_offsets_by_year=control_offsets_by_year,
    )


def build_random_analog_scene(
    pools: dict[int, YearPool],
    rng: np.random.Generator,
) -> AnalogScene:
    for _ in range(100):
        center = choose_target_longitude(rng)
        try:
            return build_analog_scene_at_center(pools, center, rng)
        except RuntimeError:
            continue
    raise RuntimeError("Could not construct a matched-analogue scene")


def prepare_analog_scene(scene: AnalogScene) -> PreparedAnalogScene:
    return PreparedAnalogScene(
        target=v1.prepare_scene(scene.target_by_year),
        control_embeddings_by_year={
            year: tuple(v1.geometry.raw_to_embedding(values) for values in scene.controls_by_year[year])
            for year in YEARS
        },
    )


def local_statistic_from_counts(k: float, n: float, p1: float) -> float:
    return float(
        v1.binomial_log_lr(
            np.asarray(k, dtype=np.float64),
            np.asarray(n, dtype=np.float64),
            p1,
        )
    )


def analog_log_e(
    prepared: PreparedAnalogScene,
    candidate: v1.Candidate | None,
    test_year: int,
    cache: dict[tuple[int, float, float, int], float],
) -> float:
    if candidate is None:
        return 0.0
    key = (
        candidate.index,
        candidate.radius,
        round(candidate.p1, 12),
        int(test_year),
    )
    if key in cache:
        return cache[key]

    year_row = YEARS.index(test_year)
    target_k = float(
        prepared.target.inner_counts[candidate.radius][year_row, candidate.index]
    )
    target_n = float(
        prepared.target.outer_counts[candidate.radius][year_row, candidate.index]
    )
    target_score = local_statistic_from_counts(
        target_k,
        target_n,
        candidate.p1,
    )

    control_scores: list[float] = []
    for embedding in prepared.control_embeddings_by_year[test_year]:
        distances = np.linalg.norm(embedding - candidate.embedding, axis=1)
        k = float(np.sum(distances <= candidate.radius))
        n = float(
            np.sum(distances <= v1.OUTER_MULTIPLIER * candidate.radius)
        )
        control_scores.append(
            local_statistic_from_counts(k, n, candidate.p1)
        )

    greater_or_equal = sum(
        score >= target_score for score in control_scores
    )
    p_value = (1.0 + greater_or_equal) / (len(control_scores) + 1.0)
    log_e = P_CALIBRATOR_LOG_CONSTANT - 0.5 * math.log(p_value)
    cache[key] = log_e
    return log_e


def order_eprocess(
    prepared: PreparedAnalogScene,
    order: tuple[int, ...],
    candidate_cache: dict[tuple[int, ...], v1.Candidate | None],
    evidence_cache: dict[tuple[int, float, float, int], float],
) -> float:
    log_e = 0.0
    for reveal_index in range(v1.WARMUP_YEARS, len(order)):
        train_years = order[:reveal_index]
        test_year = order[reveal_index]
        candidate = v1.discover_candidate(
            prepared.target,
            train_years,
            candidate_cache,
        )
        log_e += analog_log_e(
            prepared,
            candidate,
            test_year,
            evidence_cache,
        )
    return log_e


def evaluate_prepared(prepared: PreparedAnalogScene) -> Evaluation:
    candidate_cache: dict[tuple[int, ...], v1.Candidate | None] = {}
    evidence_cache: dict[tuple[int, float, float, int], float] = {}

    order_logs = [
        order_eprocess(
            prepared,
            order,
            candidate_cache,
            evidence_cache,
        )
        for order in ORDERS
    ]
    multi_order = float(logsumexp(order_logs) - math.log(len(order_logs)))
    chronological = order_logs[0]

    fixed_candidate = v1.discover_candidate(
        prepared.target,
        YEARS[: v1.WARMUP_YEARS],
        candidate_cache,
    )
    fixed_log = sum(
        analog_log_e(
            prepared,
            fixed_candidate,
            year,
            evidence_cache,
        )
        for year in YEARS[v1.WARMUP_YEARS :]
    )

    split_candidate = v1.discover_candidate(
        prepared.target,
        YEARS[:3],
        candidate_cache,
    )
    split_log = sum(
        analog_log_e(
            prepared,
            split_candidate,
            year,
            evidence_cache,
        )
        for year in YEARS[3:]
    )

    all_candidate = v1.discover_candidate(
        prepared.target,
        YEARS,
        candidate_cache,
    )
    naive_log = sum(
        analog_log_e(
            prepared,
            all_candidate,
            year,
            evidence_cache,
        )
        for year in YEARS
    )

    return Evaluation(
        log_evalues={
            "multi_order_adaptive": multi_order,
            "chronological_adaptive": chronological,
            "fixed_candidate": fixed_log,
            "single_split": split_log,
            "naive_same_data": naive_log,
        },
        order_log_evalues=order_logs,
        localization_raw=None
        if all_candidate is None
        else all_candidate.raw.copy(),
        localization_radius=None
        if all_candidate is None
        else all_candidate.radius,
    )


def choose_truth(
    target_by_year: dict[int, np.ndarray],
    rng: np.random.Generator,
) -> np.ndarray:
    year = YEARS[int(rng.integers(0, len(YEARS)))]
    values = target_by_year[year]
    return values[int(rng.integers(0, len(values)))].copy()


def condition_counts(
    condition: str,
    rng: np.random.Generator,
) -> dict[int, int]:
    if condition == "recurring_moderate":
        return {year: 3 for year in YEARS}
    if condition == "recurring_sparse":
        return {year: 2 for year in YEARS}
    if condition == "intermittent_sparse":
        active = set(
            int(value)
            for value in rng.choice(YEARS, size=5, replace=False)
        )
        return {year: (3 if year in active else 0) for year in YEARS}
    if condition == "late_onset_sparse":
        return {year: (0 if year <= 2020 else 3) for year in YEARS}
    if condition == "diffuse_recurring":
        return {year: 3 for year in YEARS}
    if condition == "strong_recurring":
        return {year: 5 for year in YEARS}
    if condition == "one_year_artifact":
        active_year = YEARS[int(rng.integers(0, len(YEARS)))]
        return {year: (12 if year == active_year else 0) for year in YEARS}
    raise KeyError(condition)


def inject_condition(
    scene: AnalogScene,
    condition: str,
    truth: np.ndarray,
    rng: np.random.Generator,
) -> tuple[AnalogScene, dict[int, int]]:
    counts = condition_counts(condition, rng)
    scatter = (
        DIFFUSE_SCATTER
        if condition == "diffuse_recurring"
        else NOMINAL_SCATTER
    )
    target: dict[int, np.ndarray] = {}
    for year in YEARS:
        background = scene.target_by_year[year]
        count = counts[year]
        if count <= 0:
            target[year] = background.copy()
            continue
        offset = rng.normal(0.0, [0.20, 0.20, 0.12], size=3)
        events = truth + offset + rng.normal(
            0.0,
            scatter,
            size=(count, 3),
        )
        events[:, 0] = (events[:, 0] + 180.0) % 360.0 - 180.0
        target[year] = np.vstack([background, events])
    return (
        AnalogScene(
            center_solar_longitude=scene.center_solar_longitude,
            target_by_year=target,
            controls_by_year=scene.controls_by_year,
            control_offsets_by_year=scene.control_offsets_by_year,
        ),
        counts,
    )


def raw_distance(a: np.ndarray, b: np.ndarray) -> float:
    return v1.raw_distance(a, b)


def evaluate_nulls(pools: dict[int, YearPool]) -> dict[str, object]:
    rng = np.random.default_rng(501001)
    accepted = {method: [] for method in METHODS}
    order_accepted = [[] for _ in ORDERS]
    control_counts: list[dict[str, int]] = []

    for _ in range(NULL_SCENES):
        scene = build_random_analog_scene(pools, rng)
        evaluation = evaluate_prepared(prepare_analog_scene(scene))
        control_counts.append(
            {
                str(year): len(scene.controls_by_year[year])
                for year in YEARS
            }
        )
        for method in METHODS:
            accepted[method].append(
                evaluation.log_evalues[method] >= LOG_THRESHOLD
            )
        for index, value in enumerate(evaluation.order_log_evalues):
            order_accepted[index].append(value >= LOG_THRESHOLD)

    methods: dict[str, object] = {}
    for method in METHODS:
        values = np.asarray(accepted[method], dtype=bool)
        count = int(np.sum(values))
        methods[method] = {
            "acceptance_count": count,
            "acceptance_rate": count / NULL_SCENES,
            "wilson_95": list(v1.wilson_interval(count, NULL_SCENES)),
            "accepted": values.astype(int).tolist(),
        }

    orders = []
    for order, accepted_values in zip(ORDERS, order_accepted):
        values = np.asarray(accepted_values, dtype=bool)
        count = int(np.sum(values))
        orders.append(
            {
                "order": list(order),
                "acceptance_count": count,
                "acceptance_rate": count / NULL_SCENES,
                "wilson_95": list(v1.wilson_interval(count, NULL_SCENES)),
            }
        )
    return {
        "methods": methods,
        "orders": orders,
        "control_counts": control_counts,
    }


def evaluate_condition(
    pools: dict[int, YearPool],
    condition: str,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    accepted = {method: [] for method in METHODS}
    recovered = {method: [] for method in METHODS}
    log_evalues = {method: [] for method in METHODS}
    localization_distances: list[float] = []

    for _ in range(INJECTION_REPLICATES):
        background = build_random_analog_scene(pools, rng)
        truth = choose_truth(background.target_by_year, rng)
        injected, _ = inject_condition(
            background,
            condition,
            truth,
            rng,
        )
        evaluation = evaluate_prepared(prepare_analog_scene(injected))
        distance = (
            math.inf
            if evaluation.localization_raw is None
            else raw_distance(evaluation.localization_raw, truth)
        )
        localization_distances.append(distance)
        near = distance <= DETECTION_DISTANCE
        for method in METHODS:
            passes = evaluation.log_evalues[method] >= LOG_THRESHOLD
            accepted[method].append(passes)
            recovered[method].append(passes and near)
            log_evalues[method].append(evaluation.log_evalues[method])

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
            "recovery_wilson_95": list(
                v1.wilson_interval(count, INJECTION_REPLICATES)
            ),
            "accepted": accepted_values.astype(int).tolist(),
            "recovered": recovered_values.astype(int).tolist(),
            "log_evalues": log_evalues[method],
        }
    return {
        "methods": methods,
        "localization_distances": localization_distances,
    }


def evaluate_m2026(pools: dict[int, YearPool]) -> dict[str, object]:
    rng = np.random.default_rng(509001)
    scene = build_analog_scene_at_center(pools, 10.0, rng)
    evaluation = evaluate_prepared(prepare_analog_scene(scene))
    reference = v1.m2026_reference_raw()
    distance = (
        math.inf
        if evaluation.localization_raw is None
        else raw_distance(evaluation.localization_raw, reference)
    )
    return {
        "log_evalues": evaluation.log_evalues,
        "evalues": {
            method: float(math.exp(min(value, 200.0)))
            for method, value in evaluation.log_evalues.items()
        },
        "order_log_evalues": evaluation.order_log_evalues,
        "accepted_primary": evaluation.log_evalues[PRIMARY] >= LOG_THRESHOLD,
        "localization_raw": None
        if evaluation.localization_raw is None
        else evaluation.localization_raw.tolist(),
        "localization_radius": evaluation.localization_radius,
        "distance_to_reference": distance,
        "near_reference": distance <= M2026_DISTANCE,
        "reference_raw": reference.tolist(),
        "control_counts": {
            str(year): len(scene.controls_by_year[year])
            for year in YEARS
        },
    }


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
    sparse_methods = conditions["recurring_sparse"]["methods"]
    primary_values = np.asarray(
        sparse_methods[PRIMARY]["recovered"], dtype=int
    )
    baseline_arrays = {
        method: np.asarray(
            sparse_methods[method]["recovered"], dtype=int
        )
        for method in NONADAPTIVE_BASELINES
    }
    best_baseline = max(
        NONADAPTIVE_BASELINES,
        key=lambda method: float(np.mean(baseline_arrays[method])),
    )
    best_values = baseline_arrays[best_baseline]
    gain = float(np.mean(primary_values - best_values))
    gain_interval = paired_bootstrap_interval(
        primary_values,
        best_values,
        seed=510001,
    )

    primary_null = nulls["methods"][PRIMARY]
    max_order_null = max(
        order["acceptance_rate"] for order in nulls["orders"]
    )
    rates = {
        name: conditions[name]["methods"][PRIMARY]["recovery_rate"]
        for name in CONDITIONS
    }
    artifact_acceptance = conditions["one_year_artifact"]["methods"][PRIMARY][
        "acceptance_rate"
    ]
    moderate_chrono_margin = (
        rates["recurring_moderate"]
        - conditions["recurring_moderate"]["methods"][
            "chronological_adaptive"
        ]["recovery_rate"]
    )
    sparse_chrono_margin = (
        rates["recurring_sparse"]
        - conditions["recurring_sparse"]["methods"][
            "chronological_adaptive"
        ]["recovery_rate"]
    )

    gates = {
        "null_acceptance_le_0_10": primary_null["acceptance_rate"] <= 0.10,
        "null_wilson_upper_le_0_15": primary_null["wilson_95"][1] <= 0.15,
        "every_order_null_acceptance_le_0_15": max_order_null <= 0.15,
        "sparse_gain_ge_0_10": gain >= 0.10,
        "sparse_bootstrap_lower_gt_0": gain_interval[0] > 0.0,
        "moderate_recovery_ge_0_75": rates["recurring_moderate"] >= 0.75,
        "intermittent_recovery_ge_0_40": rates["intermittent_sparse"] >= 0.40,
        "late_onset_recovery_ge_0_40": rates["late_onset_sparse"] >= 0.40,
        "diffuse_recovery_ge_0_35": rates["diffuse_recurring"] >= 0.35,
        "strong_recovery_ge_0_85": rates["strong_recurring"] >= 0.85,
        "artifact_acceptance_le_0_10": artifact_acceptance <= 0.10,
        "moderate_not_below_chrono_by_0_10": moderate_chrono_margin >= -0.10,
        "sparse_not_below_chrono_by_0_10": sparse_chrono_margin >= -0.10,
        "m2026_accepted_near_reference": bool(
            external["accepted_primary"] and external["near_reference"]
        ),
    }
    return {
        "primary_method": PRIMARY,
        "sparse_primary_recovery": float(np.mean(primary_values)),
        "sparse_best_nonadaptive_baseline": best_baseline,
        "sparse_best_baseline_recovery": float(np.mean(best_values)),
        "sparse_gain": gain,
        "sparse_gain_paired_bootstrap_95": list(gain_interval),
        "condition_primary_recovery": rates,
        "artifact_primary_acceptance": artifact_acceptance,
        "max_individual_order_null_acceptance": max_order_null,
        "moderate_margin_vs_chronological": moderate_chrono_margin,
        "sparse_margin_vs_chronological": sparse_chrono_margin,
        "gates": gates,
        "verdict": "CONTINUE_TO_KNOWN_STREAM_ANALOG_EPROCESS_BENCHMARK"
        if all(gates.values())
        else "KILL_MATCHED_ANALOG_EPROCESS_DIRECTION",
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    null_methods = payload["null_results"]["methods"]
    lines = [
        "# Matched-analogue sequential evidence Stage-0",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "Each unseen target year is rank-calibrated against prespecified solar-longitude analogue windows from that same year. GhostStream was excluded.",
        "",
        "## Null behavior",
        "",
        "| Method | Acceptance | Wilson 95% |",
        "|---|---:|---|",
    ]
    for method in METHODS:
        result = null_methods[method]
        lines.append(
            f"| {method} | {result['acceptance_rate']:.3f} | {result['wilson_95']} |"
        )
    lines.extend(
        [
            "",
            "## Recovery",
            "",
            "| Condition | multi-order | chronological | fixed candidate | fixed split | naive same-data |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for name in CONDITIONS:
        methods = payload["conditions"][name]["methods"]
        lines.append(
            f"| {name} | {methods['multi_order_adaptive']['recovery_rate']:.3f} "
            f"| {methods['chronological_adaptive']['recovery_rate']:.3f} "
            f"| {methods['fixed_candidate']['recovery_rate']:.3f} "
            f"| {methods['single_split']['recovery_rate']:.3f} "
            f"| {methods['naive_same_data']['recovery_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Sparse recurring comparison",
            "",
            f"- primary recovery: {decision['sparse_primary_recovery']:.3f}",
            f"- strongest nonadaptive baseline: `{decision['sparse_best_nonadaptive_baseline']}` at {decision['sparse_best_baseline_recovery']:.3f}",
            f"- paired gain: {decision['sparse_gain']:.3f}",
            f"- paired-bootstrap 95%: {decision['sparse_gain_paired_bootstrap_95']}",
            "",
            "## Frozen gates",
            "",
        ]
    )
    for gate, passed in decision["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    external = payload["external_m2026_control"]
    lines.extend(
        [
            "",
            "## External M2026-A1 control",
            "",
            f"- primary E-value: {external['evalues'][PRIMARY]:.6g}",
            f"- accepted: {external['accepted_primary']}",
            f"- near reference: {external['near_reference']}",
            f"- distance: {external['distance_to_reference']:.3f}",
            f"- localization radius: {external['localization_radius']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalogs, pools = make_year_pools()
    null_results = evaluate_nulls(pools)
    conditions = {
        name: evaluate_condition(
            pools,
            name,
            seed=502001 + index * 1000,
        )
        for index, name in enumerate(CONDITIONS)
    }
    external = evaluate_m2026(pools)
    decision = decide(null_results, conditions, external)
    payload = {
        "configuration": {
            "years": YEARS,
            "orders": ORDERS,
            "radii": RADII,
            "target_events_per_year": TARGET_EVENTS_PER_YEAR,
            "control_events_per_year": CONTROL_EVENTS_PER_YEAR,
            "control_offsets": CONTROL_OFFSETS,
            "minimum_controls_per_year": MIN_CONTROLS_PER_YEAR,
            "evalue_threshold": math.exp(LOG_THRESHOLD),
            "null_scenes": NULL_SCENES,
            "injection_replicates": INJECTION_REPLICATES,
            "conditions": CONDITIONS,
            "python": os.sys.version,
            "numpy": np.__version__,
        },
        "year_event_counts": {
            str(year): len(catalogs[year].solar_longitude)
            for year in YEARS
        },
        "null_results": null_results,
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
