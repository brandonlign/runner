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
from scipy.special import logsumexp

import audit_multinetwork as audit
import shared_scan_pilot as geometry

ROOT = Path("stream_fdr_stage0")
OUT_DIR = ROOT / "results" / "predictive_eprocess"
GMN_SPEC = audit.DATASETS["GMN"]
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
RADII = (0.8, 1.0, 1.2)
OUTER_MULTIPLIER = 2.5
P0 = (1.0 / OUTER_MULTIPLIER) ** 3
PER_YEAR_EVENTS = 90
WINDOW_HALF_WIDTH_DEG = 10.0
WARMUP_YEARS = 2
MIN_SUPPORT_YEARS = 2
MIN_INNER_PER_SUPPORT_YEAR = 2
MIN_TRAIN_INNER = 4
MAX_P1 = 0.90
MIXTURE_WEIGHT = 0.50
LOG_THRESHOLD = math.log(10.0)
DETECTION_DISTANCE = 1.5
M2026_DISTANCE = 2.0
NULL_SCENES = 128
INJECTION_REPLICATES = 96
BOOTSTRAP_REPLICATES = 8000

METHODS = (
    "multi_order_adaptive",
    "chronological_adaptive",
    "fixed_candidate",
    "single_split",
    "naive_same_data",
)
VALID_BASELINES = (
    "chronological_adaptive",
    "fixed_candidate",
    "single_split",
)
PRIMARY = "multi_order_adaptive"

NOMINAL_SCATTER = np.asarray([1.0, 1.0, 0.65], dtype=np.float64)
DIFFUSE_SCATTER = np.asarray([2.0, 2.0, 1.30], dtype=np.float64)

CONDITIONS = (
    "recurring_weak",
    "intermittent",
    "late_onset",
    "diffuse_recurring",
    "strong_recurring",
    "one_year_artifact",
)


@dataclass(frozen=True)
class YearCatalog:
    solar_longitude: np.ndarray
    raw_features: np.ndarray


@dataclass(frozen=True)
class Candidate:
    index: int
    raw: np.ndarray
    embedding: np.ndarray
    radius: float
    p1: float
    train_score: float


@dataclass
class PreparedScene:
    raw_by_year: dict[int, np.ndarray]
    all_raw: np.ndarray
    all_embedding: np.ndarray
    global_indices_by_year: dict[int, np.ndarray]
    inner_counts: dict[float, np.ndarray]
    outer_counts: dict[float, np.ndarray]


@dataclass(frozen=True)
class SceneEvaluation:
    log_evalues: dict[str, float]
    order_log_evalues: list[float]
    localization_raw: np.ndarray | None
    localization_radius: float | None


def fixed_orders() -> tuple[tuple[int, ...], ...]:
    chronological = tuple(YEARS)
    reverse = tuple(reversed(YEARS))
    rotations = tuple(
        chronological[offset:] + chronological[:offset]
        for offset in (1, 2, 3)
    )
    rng = np.random.default_rng(20260803)
    random_orders: list[tuple[int, ...]] = []
    forbidden = {chronological, reverse, *rotations}
    while len(random_orders) < 3:
        candidate = tuple(int(value) for value in rng.permutation(YEARS))
        if candidate not in forbidden and candidate not in random_orders:
            random_orders.append(candidate)
    return (chronological, reverse, *rotations, *random_orders)


ORDERS = fixed_orders()


def load_gmn_by_year() -> dict[int, YearCatalog]:
    path = audit.DATA_DIR / "gmn_shober_2026_subset.csv"
    audit.download(GMN_SPEC["url"], path)
    digest = audit.md5sum(path)
    if digest != GMN_SPEC["md5"]:
        raise RuntimeError(
            f"GMN MD5 mismatch: expected {GMN_SPEC['md5']}, got {digest}"
        )

    solar: dict[int, list[float]] = {year: [] for year in YEARS}
    features: dict[int, list[tuple[float, float, float]]] = {
        year: [] for year in YEARS
    }
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        columns = {
            semantic: audit.pick_column(header, aliases)
            for semantic, aliases in audit.ALIASES.items()
        }
        for required in ("solar_longitude", "ra_geo", "dec_geo", "vg"):
            if not columns.get(required):
                raise RuntimeError(f"Missing GMN column for {required}: {columns}")

        for row in reader:
            year_value = audit.parse_year(row, columns)
            if year_value is None:
                continue
            year = int(year_value)
            if year not in YEARS:
                continue
            ls = audit.as_float(row.get(columns["solar_longitude"], ""))
            ra = audit.as_float(row.get(columns["ra_geo"], ""))
            dec = audit.as_float(row.get(columns["dec_geo"], ""))
            vg = audit.as_float(row.get(columns["vg"], ""))
            if None in (ls, ra, dec, vg):
                continue
            assert ls is not None and ra is not None and dec is not None and vg is not None
            if not (
                0.0 <= ls < 360.0
                and 0.0 <= ra < 360.0
                and -90.0 <= dec <= 90.0
                and 5.0 <= vg <= 80.0
            ):
                continue
            ecliptic_longitude, ecliptic_latitude = audit.equatorial_to_ecliptic(
                ra, dec
            )
            sun_centered_longitude = audit.wrap180(ecliptic_longitude - ls)
            solar[year].append(ls)
            features[year].append(
                (sun_centered_longitude, ecliptic_latitude, vg)
            )

    result = {
        year: YearCatalog(
            solar_longitude=np.asarray(solar[year], dtype=np.float64),
            raw_features=np.asarray(features[year], dtype=np.float64),
        )
        for year in YEARS
    }
    for year, catalog in result.items():
        if len(catalog.solar_longitude) == 0:
            raise RuntimeError(f"No usable GMN events for {year}")
    return result


def circular_delta(values: np.ndarray, center: float) -> np.ndarray:
    return (values - center + 180.0) % 360.0 - 180.0


def choose_null_longitude(rng: np.random.Generator) -> float:
    while True:
        center = float(rng.uniform(0.0, 360.0))
        if abs(audit.wrap180(center - 10.0)) >= 35.0:
            return center


def sample_scene(
    catalogs: dict[int, YearCatalog],
    center_ls: float,
    rng: np.random.Generator,
) -> dict[int, np.ndarray]:
    scene: dict[int, np.ndarray] = {}
    for year in YEARS:
        catalog = catalogs[year]
        mask = np.abs(circular_delta(catalog.solar_longitude, center_ls)) <= WINDOW_HALF_WIDTH_DEG
        indices = np.flatnonzero(mask)
        if len(indices) < PER_YEAR_EVENTS:
            raise RuntimeError(
                f"Only {len(indices)} events for {year} near solar longitude {center_ls:.2f}"
            )
        chosen = rng.choice(indices, size=PER_YEAR_EVENTS, replace=False)
        scene[year] = catalog.raw_features[chosen].copy()
    return scene


def prepare_scene(raw_by_year: dict[int, np.ndarray]) -> PreparedScene:
    all_raw_parts: list[np.ndarray] = []
    global_indices_by_year: dict[int, np.ndarray] = {}
    cursor = 0
    for year in YEARS:
        values = raw_by_year[year]
        all_raw_parts.append(values)
        global_indices_by_year[year] = np.arange(
            cursor, cursor + len(values), dtype=np.int64
        )
        cursor += len(values)
    all_raw = np.vstack(all_raw_parts)
    all_embedding = geometry.raw_to_embedding(all_raw)

    inner_counts: dict[float, np.ndarray] = {}
    outer_counts: dict[float, np.ndarray] = {}
    for radius in RADII:
        inner_rows: list[np.ndarray] = []
        outer_rows: list[np.ndarray] = []
        for year in YEARS:
            year_embedding = geometry.raw_to_embedding(raw_by_year[year])
            tree = cKDTree(year_embedding)
            inner_rows.append(
                np.asarray(
                    tree.query_ball_point(
                        all_embedding, radius, return_length=True
                    ),
                    dtype=np.int32,
                )
            )
            outer_rows.append(
                np.asarray(
                    tree.query_ball_point(
                        all_embedding,
                        OUTER_MULTIPLIER * radius,
                        return_length=True,
                    ),
                    dtype=np.int32,
                )
            )
        inner_counts[radius] = np.vstack(inner_rows)
        outer_counts[radius] = np.vstack(outer_rows)

    return PreparedScene(
        raw_by_year=raw_by_year,
        all_raw=all_raw,
        all_embedding=all_embedding,
        global_indices_by_year=global_indices_by_year,
        inner_counts=inner_counts,
        outer_counts=outer_counts,
    )


def binomial_log_lr(k: np.ndarray, n: np.ndarray, p1: np.ndarray | float) -> np.ndarray:
    kf = np.asarray(k, dtype=np.float64)
    nf = np.asarray(n, dtype=np.float64)
    p1f = np.clip(np.asarray(p1, dtype=np.float64), P0 + 1e-8, MAX_P1)
    return (
        kf * np.log(p1f / P0)
        + (nf - kf) * np.log((1.0 - p1f) / (1.0 - P0))
    )


def discover_candidate(
    prepared: PreparedScene,
    train_years: Iterable[int],
    cache: dict[tuple[int, ...], Candidate | None],
) -> Candidate | None:
    key = tuple(sorted(int(year) for year in train_years))
    if key in cache:
        return cache[key]
    if len(key) < MIN_SUPPORT_YEARS:
        cache[key] = None
        return None

    row_indices = np.asarray([YEARS.index(year) for year in key], dtype=np.int64)
    candidate_indices = np.concatenate(
        [prepared.global_indices_by_year[year] for year in key]
    )

    best: Candidate | None = None
    best_score = -math.inf
    for radius in RADII:
        inner_by_year = prepared.inner_counts[radius][row_indices][:, candidate_indices]
        outer_by_year = prepared.outer_counts[radius][row_indices][:, candidate_indices]
        k = np.sum(inner_by_year, axis=0).astype(np.float64)
        n = np.sum(outer_by_year, axis=0).astype(np.float64)
        support = np.sum(
            inner_by_year >= MIN_INNER_PER_SUPPORT_YEAR,
            axis=0,
        )
        p1 = np.clip((k + 0.5) / (n + 1.0), P0 + 1e-8, MAX_P1)
        score = binomial_log_lr(k, n, p1)
        valid = (
            (k >= MIN_TRAIN_INNER)
            & (support >= MIN_SUPPORT_YEARS)
            & (p1 > P0 + 1e-6)
        )
        score = np.where(valid, score, -np.inf)
        local_index = int(np.argmax(score))
        local_score = float(score[local_index])
        if math.isfinite(local_score) and local_score > best_score:
            global_index = int(candidate_indices[local_index])
            best_score = local_score
            best = Candidate(
                index=global_index,
                raw=prepared.all_raw[global_index].copy(),
                embedding=prepared.all_embedding[global_index].copy(),
                radius=radius,
                p1=float(p1[local_index]),
                train_score=local_score,
            )

    cache[key] = best
    return best


def predictive_log_e(
    prepared: PreparedScene,
    candidate: Candidate | None,
    test_years: Iterable[int],
) -> float:
    if candidate is None:
        return 0.0
    rows = np.asarray([YEARS.index(int(year)) for year in test_years], dtype=np.int64)
    k = float(np.sum(prepared.inner_counts[candidate.radius][rows, candidate.index]))
    n = float(np.sum(prepared.outer_counts[candidate.radius][rows, candidate.index]))
    log_lr = float(binomial_log_lr(np.asarray(k), np.asarray(n), candidate.p1))
    # log((1-w) + w*LR), computed stably. Downward clipping avoids overflow
    # and cannot invalidate an e-value.
    log_e = float(
        np.logaddexp(
            math.log(1.0 - MIXTURE_WEIGHT),
            math.log(MIXTURE_WEIGHT) + min(log_lr, 200.0),
        )
    )
    return log_e


def order_eprocess(
    prepared: PreparedScene,
    order: tuple[int, ...],
    cache: dict[tuple[int, ...], Candidate | None],
) -> tuple[float, list[float]]:
    log_e = 0.0
    increments: list[float] = []
    for reveal_index in range(WARMUP_YEARS, len(order)):
        train_years = order[:reveal_index]
        test_year = order[reveal_index]
        candidate = discover_candidate(prepared, train_years, cache)
        increment = predictive_log_e(prepared, candidate, (test_year,))
        log_e += increment
        increments.append(increment)
    return log_e, increments


def evaluate_prepared_scene(prepared: PreparedScene) -> SceneEvaluation:
    cache: dict[tuple[int, ...], Candidate | None] = {}
    order_logs: list[float] = []
    for order in ORDERS:
        log_e, _ = order_eprocess(prepared, order, cache)
        order_logs.append(log_e)

    multi_order = float(logsumexp(order_logs) - math.log(len(order_logs)))
    chronological = order_logs[0]

    fixed_candidate = discover_candidate(
        prepared,
        YEARS[:WARMUP_YEARS],
        cache,
    )
    fixed_log_e = 0.0
    for year in YEARS[WARMUP_YEARS:]:
        fixed_log_e += predictive_log_e(prepared, fixed_candidate, (year,))

    split_candidate = discover_candidate(prepared, YEARS[:3], cache)
    split_log_e = predictive_log_e(prepared, split_candidate, YEARS[3:])

    all_candidate = discover_candidate(prepared, YEARS, cache)
    naive_log_e = predictive_log_e(prepared, all_candidate, YEARS)

    return SceneEvaluation(
        log_evalues={
            "multi_order_adaptive": multi_order,
            "chronological_adaptive": chronological,
            "fixed_candidate": fixed_log_e,
            "single_split": split_log_e,
            "naive_same_data": naive_log_e,
        },
        order_log_evalues=order_logs,
        localization_raw=None if all_candidate is None else all_candidate.raw.copy(),
        localization_radius=None if all_candidate is None else all_candidate.radius,
    )


def raw_distance(a: np.ndarray, b: np.ndarray) -> float:
    embeddings = geometry.raw_to_embedding(np.vstack([a, b]))
    return float(np.linalg.norm(embeddings[0] - embeddings[1]))


def choose_truth(scene: dict[int, np.ndarray], rng: np.random.Generator) -> np.ndarray:
    year = YEARS[int(rng.integers(0, len(YEARS)))]
    values = scene[year]
    return values[int(rng.integers(0, len(values)))].copy()


def condition_counts(condition: str, rng: np.random.Generator) -> dict[int, int]:
    if condition == "recurring_weak":
        return {year: 3 for year in YEARS}
    if condition == "intermittent":
        active = set(int(value) for value in rng.choice(YEARS, size=5, replace=False))
        return {year: (4 if year in active else 0) for year in YEARS}
    if condition == "late_onset":
        return {year: (0 if year <= 2020 else 4) for year in YEARS}
    if condition == "diffuse_recurring":
        return {year: 4 for year in YEARS}
    if condition == "strong_recurring":
        return {year: 6 for year in YEARS}
    if condition == "one_year_artifact":
        active_year = YEARS[int(rng.integers(0, len(YEARS)))]
        return {year: (15 if year == active_year else 0) for year in YEARS}
    raise KeyError(condition)


def inject_condition(
    scene: dict[int, np.ndarray],
    condition: str,
    truth: np.ndarray,
    rng: np.random.Generator,
) -> tuple[dict[int, np.ndarray], dict[int, int]]:
    counts = condition_counts(condition, rng)
    scatter = DIFFUSE_SCATTER if condition == "diffuse_recurring" else NOMINAL_SCATTER
    result: dict[int, np.ndarray] = {}
    for year in YEARS:
        background = scene[year]
        count = counts[year]
        if count <= 0:
            result[year] = background.copy()
            continue
        year_offset = rng.normal(0.0, [0.20, 0.20, 0.12], size=3)
        events = truth + year_offset + rng.normal(0.0, scatter, size=(count, 3))
        events[:, 0] = (events[:, 0] + 180.0) % 360.0 - 180.0
        result[year] = np.vstack([background, events])
    return result, counts


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(
        (p * (1.0 - p) + z * z / (4.0 * total)) / total
    ) / denominator
    return max(0.0, center - half), min(1.0, center + half)


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


def build_random_background(
    catalogs: dict[int, YearCatalog],
    rng: np.random.Generator,
) -> tuple[dict[int, np.ndarray], float]:
    for _ in range(100):
        center_ls = choose_null_longitude(rng)
        try:
            return sample_scene(catalogs, center_ls, rng), center_ls
        except RuntimeError:
            continue
    raise RuntimeError("Could not construct a seven-year background scene")


def evaluate_nulls(catalogs: dict[int, YearCatalog]) -> dict[str, object]:
    rng = np.random.default_rng(401001)
    accepted = {method: [] for method in METHODS}
    order_accepted = [[] for _ in ORDERS]
    centers: list[float] = []
    for _ in range(NULL_SCENES):
        scene, center = build_random_background(catalogs, rng)
        centers.append(center)
        evaluation = evaluate_prepared_scene(prepare_scene(scene))
        for method in METHODS:
            accepted[method].append(evaluation.log_evalues[method] >= LOG_THRESHOLD)
        for index, value in enumerate(evaluation.order_log_evalues):
            order_accepted[index].append(value >= LOG_THRESHOLD)

    summary: dict[str, object] = {}
    for method in METHODS:
        values = np.asarray(accepted[method], dtype=bool)
        count = int(np.sum(values))
        summary[method] = {
            "acceptance_count": count,
            "acceptance_rate": count / NULL_SCENES,
            "wilson_95": list(wilson_interval(count, NULL_SCENES)),
            "accepted": values.astype(int).tolist(),
        }
    order_summary = []
    for order, values_list in zip(ORDERS, order_accepted):
        values = np.asarray(values_list, dtype=bool)
        count = int(np.sum(values))
        order_summary.append(
            {
                "order": list(order),
                "acceptance_count": count,
                "acceptance_rate": count / NULL_SCENES,
                "wilson_95": list(wilson_interval(count, NULL_SCENES)),
            }
        )
    return {
        "methods": summary,
        "orders": order_summary,
        "scene_solar_longitudes": centers,
    }


def evaluate_condition(
    catalogs: dict[int, YearCatalog],
    condition: str,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    accepted = {method: [] for method in METHODS}
    recovered = {method: [] for method in METHODS}
    log_evalues = {method: [] for method in METHODS}
    localization_distances: list[float] = []
    counts_by_replicate: list[dict[str, int]] = []

    for _ in range(INJECTION_REPLICATES):
        background, _ = build_random_background(catalogs, rng)
        truth = choose_truth(background, rng)
        injected, counts = inject_condition(background, condition, truth, rng)
        evaluation = evaluate_prepared_scene(prepare_scene(injected))
        distance = (
            math.inf
            if evaluation.localization_raw is None
            else raw_distance(evaluation.localization_raw, truth)
        )
        localization_distances.append(distance)
        counts_by_replicate.append({str(year): counts[year] for year in YEARS})
        near = distance <= DETECTION_DISTANCE
        for method in METHODS:
            passes = evaluation.log_evalues[method] >= LOG_THRESHOLD
            accepted[method].append(passes)
            recovered[method].append(passes and near)
            log_evalues[method].append(evaluation.log_evalues[method])

    result: dict[str, object] = {}
    for method in METHODS:
        accepted_array = np.asarray(accepted[method], dtype=bool)
        recovered_array = np.asarray(recovered[method], dtype=bool)
        recovered_count = int(np.sum(recovered_array))
        result[method] = {
            "acceptance_count": int(np.sum(accepted_array)),
            "acceptance_rate": float(np.mean(accepted_array)),
            "recovery_count": recovered_count,
            "recovery_rate": float(np.mean(recovered_array)),
            "recovery_wilson_95": list(
                wilson_interval(recovered_count, INJECTION_REPLICATES)
            ),
            "accepted": accepted_array.astype(int).tolist(),
            "recovered": recovered_array.astype(int).tolist(),
            "log_evalues": log_evalues[method],
        }
    return {
        "methods": result,
        "localization_distances": localization_distances,
        "counts_by_replicate": counts_by_replicate,
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


def evaluate_m2026(catalogs: dict[int, YearCatalog]) -> dict[str, object]:
    rng = np.random.default_rng(409001)
    scene = sample_scene(catalogs, 10.0, rng)
    evaluation = evaluate_prepared_scene(prepare_scene(scene))
    reference = m2026_reference_raw()
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
    }


def decide(
    nulls: dict[str, object],
    conditions: dict[str, dict[str, object]],
    external: dict[str, object],
) -> dict[str, object]:
    recurring = conditions["recurring_weak"]["methods"]
    primary_recurring = np.asarray(recurring[PRIMARY]["recovered"], dtype=int)
    baseline_arrays = {
        method: np.asarray(recurring[method]["recovered"], dtype=int)
        for method in VALID_BASELINES
    }
    best_baseline = max(
        VALID_BASELINES,
        key=lambda method: float(np.mean(baseline_arrays[method])),
    )
    best_values = baseline_arrays[best_baseline]
    gain = float(np.mean(primary_recurring - best_values))
    gain_interval = paired_bootstrap_interval(
        primary_recurring,
        best_values,
        seed=410001,
    )

    primary_null = nulls["methods"][PRIMARY]
    max_order_null = max(order["acceptance_rate"] for order in nulls["orders"])
    condition_rates = {
        name: conditions[name]["methods"][PRIMARY]["recovery_rate"]
        for name in CONDITIONS
    }
    artifact_acceptance = conditions["one_year_artifact"]["methods"][PRIMARY][
        "acceptance_rate"
    ]

    gates = {
        "null_acceptance_le_0_10": primary_null["acceptance_rate"] <= 0.10,
        "null_wilson_upper_le_0_15": primary_null["wilson_95"][1] <= 0.15,
        "recurring_gain_ge_0_10": gain >= 0.10,
        "recurring_bootstrap_lower_gt_0": gain_interval[0] > 0.0,
        "intermittent_recovery_ge_0_50": condition_rates["intermittent"] >= 0.50,
        "late_onset_recovery_ge_0_50": condition_rates["late_onset"] >= 0.50,
        "diffuse_recovery_ge_0_40": condition_rates["diffuse_recurring"] >= 0.40,
        "strong_recovery_ge_0_85": condition_rates["strong_recurring"] >= 0.85,
        "one_year_artifact_acceptance_le_0_10": artifact_acceptance <= 0.10,
        "m2026_accepted_near_reference": bool(
            external["accepted_primary"] and external["near_reference"]
        ),
        "every_order_null_acceptance_le_0_15": max_order_null <= 0.15,
    }
    return {
        "primary_method": PRIMARY,
        "recurring_primary_recovery": float(np.mean(primary_recurring)),
        "recurring_best_valid_baseline": best_baseline,
        "recurring_best_baseline_recovery": float(np.mean(best_values)),
        "recurring_gain": gain,
        "recurring_gain_paired_bootstrap_95": list(gain_interval),
        "condition_primary_recovery": condition_rates,
        "one_year_artifact_primary_acceptance": artifact_acceptance,
        "max_individual_order_null_acceptance": max_order_null,
        "gates": gates,
        "verdict": "CONTINUE_TO_KNOWN_STREAM_PREDICTIVE_BENCHMARK"
        if all(gates.values())
        else "KILL_OR_REDESIGN_PREDICTIVE_EPROCESS",
    }


def markdown_report(payload: dict[str, object]) -> str:
    decision = payload["decision"]
    null_methods = payload["null_results"]["methods"]
    lines = [
        "# Sequential predictive evidence Stage-0",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        "Candidates may adapt using revealed years, but each evidence increment is computed only on an unseen year. The primary statistic averages eight prespecified e-processes. GhostStream was excluded.",
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
            "## Primary comparison",
            "",
            f"- recurring weak recovery: {decision['recurring_primary_recovery']:.3f}",
            f"- strongest valid baseline: `{decision['recurring_best_valid_baseline']}` at {decision['recurring_best_baseline_recovery']:.3f}",
            f"- paired gain: {decision['recurring_gain']:.3f}",
            f"- paired-bootstrap 95%: {decision['recurring_gain_paired_bootstrap_95']}",
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
            f"- near published reference: {external['near_reference']}",
            f"- distance: {external['distance_to_reference']:.3f}",
            f"- localization radius: {external['localization_radius']}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalogs = load_gmn_by_year()
    null_results = evaluate_nulls(catalogs)
    conditions = {
        name: evaluate_condition(catalogs, name, seed=402001 + index * 1000)
        for index, name in enumerate(CONDITIONS)
    }
    external = evaluate_m2026(catalogs)
    decision = decide(null_results, conditions, external)
    payload = {
        "configuration": {
            "years": YEARS,
            "orders": ORDERS,
            "radii": RADII,
            "outer_multiplier": OUTER_MULTIPLIER,
            "p0": P0,
            "per_year_events": PER_YEAR_EVENTS,
            "warmup_years": WARMUP_YEARS,
            "mixture_weight": MIXTURE_WEIGHT,
            "evalue_threshold": math.exp(LOG_THRESHOLD),
            "null_scenes": NULL_SCENES,
            "injection_replicates": INJECTION_REPLICATES,
            "nominal_scatter": NOMINAL_SCATTER.tolist(),
            "diffuse_scatter": DIFFUSE_SCATTER.tolist(),
            "python": os.sys.version,
            "numpy": np.__version__,
        },
        "year_event_counts": {
            str(year): len(catalogs[year].solar_longitude) for year in YEARS
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
