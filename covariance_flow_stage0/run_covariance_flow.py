from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rebound
from scipy.linalg import null_space
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
MATCHING_DIR = ROOT / "dynamical_matching_stage0"
if str(MATCHING_DIR) not in sys.path:
    sys.path.insert(0, str(MATCHING_DIR))
import run_static_matching as matching  # noqa: E402

YEARS = (2019, 2021, 2023, 2025)
CONTROL_MONTH = {4: 12, 6: 4, 7: 8, 13: 11}
CONTROLS = tuple(sorted(CONTROL_MONTH))
SPORADIC_GROUPS_PER_SHOWER = 4
EVENTS_PER_YEAR = 5
GROUP_SIZE = 20
SEED_LIMIT = 500
K_VALUES = (5, 8, 12, 20, 32, 50, 80)
MAX_EVENT_REUSE = 4
ORBIT_DISTANCE_TOLERANCE = 0.50
ROTATIONS = 2000
LOOKBACK_YEARS = 100.0
FLOW_STEP = 1.0e-5
GRADIENT_STEP = 1.0e-6
ENERGY_TOLERANCE = 1.0e-8
RIDGE_RELATIVE = 1.0e-10


@dataclass(frozen=True)
class Group:
    group_id: str
    label: str
    control: int
    subgroup: int
    events: list[dict[str, Any]]
    orbit_match_distance: float | None


@dataclass(frozen=True)
class FlowResult:
    jacobian: np.ndarray
    relative_energy_error: float
    medoid_event_id: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def load_clone_ready_events(path: Path) -> list[dict[str, Any]]:
    events = matching.load_events(path)
    events = [event for event in events if event.get("uncertainty_ok", False)]
    if not events:
        raise RuntimeError("No clone-ready events")
    return events


def wrap_angle_deg(value: float) -> float:
    return value % 360.0


def element_feature(
    a: float,
    e: float,
    inc_deg: float,
    peri_deg: float,
    node_deg: float,
) -> np.ndarray:
    inc = math.radians(inc_deg)
    varpi = math.radians(peri_deg + node_deg)
    node = math.radians(node_deg)
    half_sin = math.sin(0.5 * inc)
    return np.asarray(
        [
            math.log(a),
            e * math.cos(varpi),
            e * math.sin(varpi),
            half_sin * math.cos(node),
            half_sin * math.sin(node),
        ],
        dtype=np.float64,
    )


def event_feature(event: dict[str, Any]) -> np.ndarray:
    return element_feature(
        float(event["a"]),
        float(event["e"]),
        float(event["i"]),
        float(event["peri"]),
        float(event["node"]),
    )


def inverse_feature(vector: np.ndarray) -> tuple[float, float, float, float, float]:
    log_a, h, k, p, q = [float(value) for value in vector]
    a = math.exp(log_a)
    e = math.hypot(h, k)
    if not (0.0 < a < 100.0 and 0.0 <= e < 0.999999):
        raise ValueError(f"Invalid inverse orbit a={a}, e={e}")
    varpi = math.atan2(k, h)
    half_sin = min(max(math.hypot(p, q), 0.0), 0.999999999)
    inc = 2.0 * math.asin(half_sin)
    node = math.atan2(q, p)
    peri = varpi - node
    return (
        a,
        e,
        math.degrees(inc),
        wrap_angle_deg(math.degrees(peri)),
        wrap_angle_deg(math.degrees(node)),
    )


def event_mean_anomaly_deg(event: dict[str, Any]) -> float:
    mean_anomaly = finite(event.get("M"))
    if mean_anomaly is not None:
        return wrap_angle_deg(mean_anomaly)
    true_anomaly = finite(event.get("f"))
    if true_anomaly is None:
        raise RuntimeError(f"No anomaly for {event.get('id')}")
    e = float(event["e"])
    f = math.radians(true_anomaly)
    eccentric_anomaly = 2.0 * math.atan2(
        math.sqrt(max(1.0 - e, 0.0)) * math.sin(0.5 * f),
        math.sqrt(1.0 + e) * math.cos(0.5 * f),
    )
    return wrap_angle_deg(
        math.degrees(eccentric_anomaly - e * math.sin(eccentric_anomaly))
    )


def transformed_measurement_covariance(event: dict[str, Any]) -> np.ndarray:
    base = np.asarray(
        [
            float(event["a"]),
            float(event["e"]),
            float(event["i"]),
            float(event["peri"]),
            float(event["node"]),
        ],
        dtype=np.float64,
    )
    sigmas = np.asarray(
        [
            float(event["a_sigma"]),
            float(event["e_sigma"]),
            float(event["i_sigma"]),
            float(event["peri_sigma"]),
            float(event["node_sigma"]),
        ],
        dtype=np.float64,
    )
    steps = np.asarray(
        [max(1e-7, 1e-6 * base[0]), 1e-7, 1e-5, 1e-5, 1e-5],
        dtype=np.float64,
    )
    jacobian = np.zeros((5, 5), dtype=np.float64)
    for column in range(5):
        plus = base.copy()
        minus = base.copy()
        plus[column] += steps[column]
        minus[column] -= steps[column]
        if column in (3, 4):
            plus[column] = wrap_angle_deg(plus[column])
            minus[column] = wrap_angle_deg(minus[column])
        if column == 0:
            minus[column] = max(minus[column], 1e-8)
        if column == 1:
            minus[column] = max(minus[column], 0.0)
            plus[column] = min(plus[column], 0.999999)
        f_plus = element_feature(*plus)
        f_minus = element_feature(*minus)
        jacobian[:, column] = (f_plus - f_minus) / (2.0 * steps[column])
    return jacobian @ np.diag(sigmas * sigmas) @ jacobian.T


def psd_projection(matrix: np.ndarray) -> np.ndarray:
    symmetric = 0.5 * (matrix + matrix.T)
    values, vectors = np.linalg.eigh(symmetric)
    values = np.maximum(values, 0.0)
    return (vectors * values[None, :]) @ vectors.T


def covariance_pair(events: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, float]:
    features = np.vstack([event_feature(event) for event in events])
    observed = np.cov(features, rowvar=False, ddof=1)
    measurement = np.mean(
        np.stack([transformed_measurement_covariance(event) for event in events]),
        axis=0,
    )
    trace = float(np.trace(observed))
    ridge = max(RIDGE_RELATIVE * trace, 1e-14)
    raw = psd_projection(observed) + ridge * np.eye(5)
    deconvolved = psd_projection(observed - measurement) + ridge * np.eye(5)
    median_log_uncertainty = float(
        np.median(np.vstack([matching.uncertainty_vector(event) for event in events]))
    )
    return raw, deconvolved, median_log_uncertainty


def node_radius_from_feature(vector: np.ndarray, ascending: bool) -> float:
    a, e, _inc, peri_deg, _node = inverse_feature(vector)
    cosine = math.cos(math.radians(peri_deg))
    denominator = 1.0 + e * cosine if ascending else 1.0 - e * cosine
    if denominator <= 1e-12:
        return math.inf
    return a * (1.0 - e * e) / denominator


def tangent_basis(medoid_feature: np.ndarray) -> tuple[np.ndarray, str, float]:
    ascending_radius = node_radius_from_feature(medoid_feature, True)
    descending_radius = node_radius_from_feature(medoid_feature, False)
    ascending = abs(ascending_radius - 1.0) <= abs(descending_radius - 1.0)
    gradient = np.zeros(5, dtype=np.float64)
    for index in range(5):
        plus = medoid_feature.copy()
        minus = medoid_feature.copy()
        plus[index] += GRADIENT_STEP
        minus[index] -= GRADIENT_STEP
        gradient[index] = (
            node_radius_from_feature(plus, ascending)
            - node_radius_from_feature(minus, ascending)
        ) / (2.0 * GRADIENT_STEP)
    norm = float(np.linalg.norm(gradient))
    if not math.isfinite(norm) or norm <= 1e-12:
        raise RuntimeError("Degenerate Earth-crossing tangent gradient")
    basis = null_space(gradient.reshape(1, -1))
    if basis.shape != (5, 4):
        raise RuntimeError(f"Unexpected tangent basis shape {basis.shape}")
    selected_radius = ascending_radius if ascending else descending_radius
    return basis, "ascending" if ascending else "descending", selected_radius


def group_medoid(events: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = np.vstack([event_feature(event) for event in events])
    scale = np.std(matrix, axis=0, ddof=1)
    scale = np.where(scale < 1e-8, 1e-8, scale)
    standardized = (matrix - np.median(matrix, axis=0)) / scale
    distances = np.linalg.norm(
        standardized[:, None, :] - standardized[None, :, :], axis=2
    )
    index = int(np.argmin(np.sum(distances, axis=1)))
    return events[index]


def add_particle_from_feature(
    simulation: rebound.Simulation,
    sun: rebound.Particle,
    vector: np.ndarray,
    mean_anomaly_deg: float,
) -> None:
    a, e, inc_deg, peri_deg, node_deg = inverse_feature(vector)
    simulation.add(
        primary=sun,
        m=0.0,
        a=a,
        e=e,
        inc=math.radians(inc_deg),
        Omega=math.radians(node_deg),
        omega=math.radians(peri_deg),
        M=math.radians(mean_anomaly_deg),
    )


def orbit_to_feature(particle: rebound.Particle, sun: rebound.Particle) -> np.ndarray:
    orbit = particle.orbit(primary=sun)
    if not (
        math.isfinite(orbit.a)
        and math.isfinite(orbit.e)
        and 0.0 < orbit.a < 100.0
        and 0.0 <= orbit.e < 0.999999
    ):
        raise RuntimeError(f"Invalid propagated orbit a={orbit.a}, e={orbit.e}")
    return element_feature(
        orbit.a,
        orbit.e,
        math.degrees(orbit.inc),
        math.degrees(orbit.omega),
        math.degrees(orbit.Omega),
    )


def local_flow(events: list[dict[str, Any]]) -> FlowResult:
    medoid = group_medoid(events)
    center = event_feature(medoid)
    mean_anomaly = event_mean_anomaly_deg(medoid)
    simulation = rebound.Simulation()
    simulation.add("outer solar system")
    simulation.integrator = "ias15"
    simulation.move_to_com()
    sun = simulation.particles[0]
    initial_energy = simulation.energy()

    for column in range(5):
        plus = center.copy()
        minus = center.copy()
        plus[column] += FLOW_STEP
        minus[column] -= FLOW_STEP
        add_particle_from_feature(simulation, sun, plus, mean_anomaly)
        add_particle_from_feature(simulation, sun, minus, mean_anomaly)

    simulation.integrate(-LOOKBACK_YEARS * 2.0 * math.pi)
    final_energy = simulation.energy()
    relative_error = abs((final_energy - initial_energy) / initial_energy)
    if relative_error > ENERGY_TOLERANCE:
        raise RuntimeError(f"Energy error {relative_error} exceeds gate")

    jacobian = np.zeros((5, 5), dtype=np.float64)
    first_test_particle = 5
    for column in range(5):
        plus_feature = orbit_to_feature(
            simulation.particles[first_test_particle + 2 * column], sun
        )
        minus_feature = orbit_to_feature(
            simulation.particles[first_test_particle + 2 * column + 1], sun
        )
        jacobian[:, column] = (plus_feature - minus_feature) / (2.0 * FLOW_STEP)
    if not np.all(np.isfinite(jacobian)):
        raise RuntimeError("Non-finite local flow Jacobian")
    return FlowResult(
        jacobian=jacobian,
        relative_energy_error=relative_error,
        medoid_event_id=str(medoid["id"]),
    )


def log_pseudodeterminant(matrix: np.ndarray, rank: int = 4) -> float:
    values = np.linalg.eigvalsh(0.5 * (matrix + matrix.T))
    values = np.sort(np.maximum(values, 1e-30))[-rank:]
    return float(np.sum(np.log(values)))


def orientation_percentile(
    covariance: np.ndarray,
    basis: np.ndarray,
    flow: np.ndarray,
    seed: int,
) -> tuple[float, float, dict[str, float]]:
    tangent = psd_projection(basis.T @ covariance @ basis)
    values, vectors = np.linalg.eigh(tangent)
    values = np.maximum(values, 1e-20)
    observed_tangent = (vectors * values[None, :]) @ vectors.T
    observed_lifted = basis @ observed_tangent @ basis.T
    observed_growth = log_pseudodeterminant(
        flow @ observed_lifted @ flow.T
    ) - float(np.sum(np.log(values)))

    rng = np.random.default_rng(seed)
    less_or_equal = 0
    rotation_growths = np.empty(ROTATIONS, dtype=np.float64)
    diagonal = np.diag(values)
    for index in range(ROTATIONS):
        gaussian = rng.normal(size=(4, 4))
        q, r = np.linalg.qr(gaussian)
        signs = np.sign(np.diag(r))
        signs[signs == 0.0] = 1.0
        q = q * signs[None, :]
        rotated = q @ diagonal @ q.T
        lifted = basis @ rotated @ basis.T
        growth = log_pseudodeterminant(flow @ lifted @ flow.T) - float(
            np.sum(np.log(values))
        )
        rotation_growths[index] = growth
        less_or_equal += int(growth <= observed_growth)
    percentile = (1.0 + less_or_equal) / (ROTATIONS + 1.0)
    diagnostics = {
        "observed_growth": observed_growth,
        "rotation_growth_p05": float(np.percentile(rotation_growths, 5.0)),
        "rotation_growth_p50": float(np.percentile(rotation_growths, 50.0)),
        "rotation_growth_p95": float(np.percentile(rotation_growths, 95.0)),
        "tangent_eigenvalue_min": float(np.min(values)),
        "tangent_eigenvalue_max": float(np.max(values)),
    }
    return percentile, -math.log10(percentile), diagnostics


def top_k_indices(values: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(values))
    if k == len(values):
        indices = np.arange(len(values))
    else:
        indices = np.argpartition(values, k - 1)[:k]
    return indices[np.argsort(values[indices], kind="mergesort")]


def orbit_median_z(events: list[dict[str, Any]], scale: matching.Scale) -> np.ndarray:
    orbit = np.vstack([matching.orbit_vector(event) for event in events])
    return matching.standardized(np.median(orbit, axis=0)[None, :], scale)[0]


def choose_sporadic_groups(
    target_events: list[dict[str, Any]],
    sporadic_by_year: dict[int, list[dict[str, Any]]],
    orbit_scale: matching.Scale,
    control: int,
    subgroup: int,
    usage: Counter[str],
) -> list[Group]:
    target_median = orbit_median_z(target_events, orbit_scale)
    matrices = {
        year: matching.standardized(
            np.vstack([matching.orbit_vector(event) for event in events]), orbit_scale
        )
        for year, events in sporadic_by_year.items()
    }
    pooled_events = [event for year in YEARS for event in sporadic_by_year[year]]
    pooled_z = np.vstack([matrices[year] for year in YEARS])
    seed_indices = top_k_indices(
        np.linalg.norm(pooled_z - target_median[None, :], axis=1),
        min(SEED_LIMIT, len(pooled_events)),
    )

    candidates: list[tuple[float, tuple[str, ...], list[dict[str, Any]]]] = []
    seen: set[tuple[str, ...]] = set()
    for seed_number, pooled_index in enumerate(seed_indices):
        seed = pooled_events[int(pooled_index)]
        seed_z = matching.standardized(
            matching.orbit_vector(seed)[None, :], orbit_scale
        )[0]
        nearest = {
            year: top_k_indices(
                np.linalg.norm(matrix - seed_z[None, :], axis=1), max(K_VALUES)
            )
            for year, matrix in matrices.items()
        }
        for k in K_VALUES:
            for variation in range(3):
                selected: list[dict[str, Any]] = []
                for year in YEARS:
                    neighborhood = nearest[year][: min(k, len(nearest[year]))]
                    if len(neighborhood) < EVENTS_PER_YEAR:
                        selected = []
                        break
                    if variation == 0:
                        chosen = neighborhood[:EVENTS_PER_YEAR]
                    else:
                        rng = np.random.default_rng(
                            stable_seed(
                                "covflow",
                                control,
                                subgroup,
                                seed_number,
                                k,
                                variation,
                                year,
                            )
                        )
                        chosen = np.sort(
                            rng.choice(
                                neighborhood,
                                EVENTS_PER_YEAR,
                                replace=False,
                            )
                        )
                    selected.extend(
                        sporadic_by_year[year][int(index)] for index in chosen
                    )
                if len(selected) != GROUP_SIZE:
                    continue
                ids = tuple(sorted(str(event["id"]) for event in selected))
                if len(set(ids)) != GROUP_SIZE or ids in seen:
                    continue
                seen.add(ids)
                distance = float(
                    np.linalg.norm(orbit_median_z(selected, orbit_scale) - target_median)
                )
                if distance <= ORBIT_DISTANCE_TOLERANCE:
                    candidates.append((distance, ids, selected))

    candidates.sort(key=lambda item: (item[0], item[1]))
    accepted: list[Group] = []
    accepted_sets: list[frozenset[str]] = []
    for distance, ids, selected in candidates:
        id_set = frozenset(ids)
        if any(usage[event_id] >= MAX_EVENT_REUSE for event_id in ids):
            continue
        if any(
            len(id_set & prior) / len(id_set | prior) > 0.25
            for prior in accepted_sets
        ):
            continue
        for event_id in ids:
            usage[event_id] += 1
        accepted_sets.append(id_set)
        accepted.append(
            Group(
                group_id=f"S{control}_{subgroup}_N{len(accepted)}",
                label="sporadic",
                control=control,
                subgroup=subgroup,
                events=selected,
                orbit_match_distance=distance,
            )
        )
        if len(accepted) == SPORADIC_GROUPS_PER_SHOWER:
            break
    if len(accepted) != SPORADIC_GROUPS_PER_SHOWER:
        raise RuntimeError(
            f"Only {len(accepted)} orbit-matched sporadic groups for control "
            f"{control} subgroup {subgroup}"
        )
    return accepted


def build_groups(events: list[dict[str, Any]]) -> list[Group]:
    groups: list[Group] = []
    sporadics = [event for event in events if int(event["iau"]) == -1]
    for control in CONTROLS:
        shower_groups = matching.build_shower_groups(events, control)
        month = CONTROL_MONTH[control]
        sporadic_by_year = {
            year: [
                event
                for event in sporadics
                if int(event["year"]) == year and int(event["month"]) == month
            ]
            for year in YEARS
        }
        orbit_scale = matching.robust_scale(
            np.vstack(
                [
                    matching.orbit_vector(event)
                    for year in YEARS
                    for event in sporadic_by_year[year]
                ]
            )
        )
        usage: Counter[str] = Counter()
        for subgroup, shower_events in enumerate(shower_groups):
            groups.append(
                Group(
                    group_id=f"S{control}_{subgroup}",
                    label="shower",
                    control=control,
                    subgroup=subgroup,
                    events=shower_events,
                    orbit_match_distance=None,
                )
            )
            groups.extend(
                choose_sporadic_groups(
                    shower_events,
                    sporadic_by_year,
                    orbit_scale,
                    control,
                    subgroup,
                    usage,
                )
            )
    shower_count = sum(group.label == "shower" for group in groups)
    sporadic_count = sum(group.label == "sporadic" for group in groups)
    if shower_count != 16 or sporadic_count != 64:
        raise RuntimeError(
            f"Unexpected group counts shower={shower_count}, "
            f"sporadic={sporadic_count}"
        )
    return groups


def auc(labels: np.ndarray, scores: np.ndarray) -> float:
    positive = labels == 1
    negative = labels == 0
    n_positive = int(np.sum(positive))
    n_negative = int(np.sum(negative))
    ranks = rankdata(scores, method="average")
    return float(
        (np.sum(ranks[positive]) - n_positive * (n_positive + 1) / 2.0)
        / (n_positive * n_negative)
    )


def evaluate(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels = np.asarray(
        [1 if record["label"] == "shower" else 0 for record in records]
    )
    deconvolved_scores = np.asarray(
        [record["deconvolved_score"] for record in records]
    )
    raw_scores = np.asarray([record["raw_score"] for record in records])
    uncertainties = np.asarray(
        [record["median_log_uncertainty"] for record in records]
    )
    deconvolved_auc = auc(labels, deconvolved_scores)
    raw_auc = auc(labels, raw_scores)
    spearman = spearmanr(deconvolved_scores, uncertainties).statistic
    spearman = float(spearman) if math.isfinite(float(spearman)) else 1.0

    control_summaries: dict[str, Any] = {}
    positive_separations: list[float] = []
    for control in CONTROLS:
        shower = [
            record
            for record in records
            if record["control"] == control and record["label"] == "shower"
        ]
        sporadic = [
            record
            for record in records
            if record["control"] == control and record["label"] == "sporadic"
        ]
        separation = float(
            np.mean([record["deconvolved_score"] for record in shower])
            - np.mean([record["deconvolved_score"] for record in sporadic])
        )
        positive_separations.append(max(separation, 0.0))
        control_summaries[str(control)] = {
            "shower_median_percentile": float(
                np.median(
                    [record["deconvolved_percentile"] for record in shower]
                )
            ),
            "shower_mean_score": float(
                np.mean([record["deconvolved_score"] for record in shower])
            ),
            "sporadic_mean_score": float(
                np.mean([record["deconvolved_score"] for record in sporadic])
            ),
            "score_separation": separation,
        }

    shower_low = sum(
        record["deconvolved_percentile"] <= 0.20
        for record in records
        if record["label"] == "shower"
    )
    sporadic_records = [
        record for record in records if record["label"] == "sporadic"
    ]
    sporadic_low_fraction = sum(
        record["deconvolved_percentile"] <= 0.20
        for record in sporadic_records
    ) / len(sporadic_records)
    controls_low = sum(
        summary["shower_median_percentile"] <= 0.20
        for summary in control_summaries.values()
    )
    total_positive_separation = sum(positive_separations)
    maximum_control_fraction = (
        max(positive_separations) / total_positive_separation
        if total_positive_separation > 0.0
        else 1.0
    )
    energy_errors = [record["relative_energy_error"] for record in records]
    gates = {
        "all_energy_errors_at_most_1e_8": max(energy_errors)
        <= ENERGY_TOLERANCE,
        "deconvolved_auroc_at_least_0_75": deconvolved_auc >= 0.75,
        "three_controls_median_percentile_at_most_0_20": controls_low >= 3,
        "ten_of_sixteen_showers_percentile_at_most_0_20": shower_low >= 10,
        "sporadic_low_percentile_fraction_at_most_0_20": sporadic_low_fraction
        <= 0.20,
        "uncertainty_spearman_absolute_at_most_0_30": abs(spearman) <= 0.30,
        "deconvolved_auroc_not_more_than_0_05_worse_than_raw": deconvolved_auc
        >= raw_auc - 0.05,
        "no_control_more_than_half_positive_separation": maximum_control_fraction
        <= 0.50,
    }
    return {
        "deconvolved_auroc": deconvolved_auc,
        "raw_auroc": raw_auc,
        "score_uncertainty_spearman": spearman,
        "shower_groups_percentile_at_most_0_20": shower_low,
        "sporadic_fraction_percentile_at_most_0_20": sporadic_low_fraction,
        "controls_with_median_percentile_at_most_0_20": controls_low,
        "maximum_control_positive_separation_fraction": maximum_control_fraction,
        "maximum_relative_energy_error": max(energy_errors),
        "control_summaries": control_summaries,
        "gates": gates,
        "verdict": (
            "PROCEED_TO_EPHEMERIS_ACCURATE_COVARIANCE_FLOW_CONFIRMATION"
            if all(gates.values())
            else "KILL_OR_REDESIGN_COVARIANCE_FLOW_ALIGNMENT"
        ),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    events = load_clone_ready_events(args.events)
    groups = build_groups(events)
    records: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        raw_covariance, deconvolved_covariance, median_log_uncertainty = (
            covariance_pair(group.events)
        )
        medoid = group_medoid(group.events)
        medoid_feature = event_feature(medoid)
        basis, node_branch, node_radius = tangent_basis(medoid_feature)
        flow = local_flow(group.events)
        (
            deconvolved_percentile,
            deconvolved_score,
            deconvolved_diagnostics,
        ) = orientation_percentile(
            deconvolved_covariance,
            basis,
            flow.jacobian,
            stable_seed("deconvolved", group.group_id),
        )
        raw_percentile, raw_score, raw_diagnostics = orientation_percentile(
            raw_covariance,
            basis,
            flow.jacobian,
            stable_seed("raw", group.group_id),
        )
        record = {
            "group_id": group.group_id,
            "label": group.label,
            "control": group.control,
            "subgroup": group.subgroup,
            "event_ids": [str(event["id"]) for event in group.events],
            "orbit_match_distance": group.orbit_match_distance,
            "medoid_event_id": flow.medoid_event_id,
            "node_branch": node_branch,
            "node_radius_au": node_radius,
            "relative_energy_error": flow.relative_energy_error,
            "median_log_uncertainty": median_log_uncertainty,
            "deconvolved_percentile": deconvolved_percentile,
            "deconvolved_score": deconvolved_score,
            "raw_percentile": raw_percentile,
            "raw_score": raw_score,
            "deconvolved_diagnostics": deconvolved_diagnostics,
            "raw_diagnostics": raw_diagnostics,
        }
        records.append(record)
        print(
            f"[{index + 1:02d}/{len(groups)}] {group.group_id} "
            f"p={deconvolved_percentile:.4f} "
            f"energy={flow.relative_energy_error:.3e}"
        )

    evaluation = evaluate(records)
    payload = {
        "configuration": {
            "controls": CONTROLS,
            "years": YEARS,
            "rotations": ROTATIONS,
            "lookback_years": LOOKBACK_YEARS,
            "flow_step": FLOW_STEP,
            "gradient_step": GRADIENT_STEP,
            "energy_tolerance": ENERGY_TOLERANCE,
            "rebound_version": rebound.__version__,
            "packaged_initial_conditions": "outer solar system",
            "source_artifact_id": 8869994126,
            "source_artifact_digest": "sha256:bc6df6971b5d306af9836b2df71aebbacd6c3f4045ea1b8c1d5268caedc2c322",
        },
        "evaluation": evaluation,
        "groups": records,
    }
    (args.output / "covariance_flow_result.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    lines = [
        "# Noise-deconvolved covariance-flow Stage-0",
        "",
        "GhostStream was excluded. Every group preserves its own tangent-covariance eigenvalues in the orientation null.",
        "",
        f"- deconvolved AUROC: **{evaluation['deconvolved_auroc']:.4f}**",
        f"- raw-covariance AUROC: **{evaluation['raw_auroc']:.4f}**",
        f"- shower groups with percentile <= 0.20: **{evaluation['shower_groups_percentile_at_most_0_20']}/16**",
        f"- sporadic low-percentile fraction: **{evaluation['sporadic_fraction_percentile_at_most_0_20']:.4f}**",
        f"- score/uncertainty Spearman rho: **{evaluation['score_uncertainty_spearman']:.4f}**",
        f"- maximum relative energy error: **{evaluation['maximum_relative_energy_error']:.3e}**",
        "",
        "## Frozen gates",
        "",
    ]
    for gate, passed in evaluation["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend(["", f"Verdict: **{evaluation['verdict']}**"])
    report = "\n".join(lines)
    (args.output / "STAGE0_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
