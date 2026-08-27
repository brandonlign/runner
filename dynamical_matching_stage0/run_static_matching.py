from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

YEARS = (2019, 2021, 2023, 2025)
CONTROL_MONTH = {4: 12, 6: 4, 7: 8, 13: 11}
CONTROLS = tuple(sorted(CONTROL_MONTH))
GROUPS_PER_CONTROL = 4
EVENTS_PER_YEAR = 5
GROUP_SIZE = len(YEARS) * EVENTS_PER_YEAR
SEED_LIMIT = 300
K_VALUES = (5, 8, 12, 20, 32, 50)
VARIATIONS = 3
MAX_MATCHES = 24
MIN_MATCHES = 12
MAX_EVENT_REUSE = 4
MAX_JACCARD = 0.25
A_JUPITER = 5.2044
ORBIT_TOL = 0.50
UNCERTAINTY_TOL = 0.50
EPS = 1e-12


@dataclass(frozen=True)
class Scale:
    center: np.ndarray
    scale: np.ndarray


@dataclass
class Candidate:
    ids: tuple[str, ...]
    indices: tuple[int, ...]
    id_set: frozenset[str]
    score: float
    diagnostics: dict[str, float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--data-gate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not event.get("quality_ok", False):
                raise RuntimeError(f"Non-quality event at selected-events line {line_number}")
            events.append(event)
    if not events:
        raise RuntimeError("No selected events loaded")
    return events


def tisserand(event: dict[str, Any]) -> float:
    supplied = finite(event.get("Tj"))
    if supplied is not None:
        return supplied
    a = float(event["a"])
    e = float(event["e"])
    inc = math.radians(float(event["i"]))
    inside = max(0.0, (a / A_JUPITER) * (1.0 - e * e))
    return A_JUPITER / a + 2.0 * math.cos(inc) * math.sqrt(inside)


def orbit_vector(event: dict[str, Any]) -> np.ndarray:
    a = max(float(event["a"]), EPS)
    return np.asarray(
        [math.log(a), float(event["e"]), float(event["i"]), float(event["q"]), tisserand(event)],
        dtype=np.float64,
    )


def anomaly_sigma(event: dict[str, Any]) -> float:
    value = finite(event.get("f_sigma"))
    if value is None:
        value = finite(event.get("M_sigma"))
    if value is None:
        raise RuntimeError(f"Missing anomaly sigma for {event.get('id')}")
    return value


def uncertainty_vector(event: dict[str, Any]) -> np.ndarray:
    floors = (1e-12, 1e-12, 1e-9, 1e-9, 1e-9, 1e-9)
    values = (
        float(event["a_sigma"]),
        float(event["e_sigma"]),
        float(event["i_sigma"]),
        float(event["peri_sigma"]),
        float(event["node_sigma"]),
        anomaly_sigma(event),
    )
    return np.asarray(
        [math.log10(max(value, floor)) for value, floor in zip(values, floors)],
        dtype=np.float64,
    )


def robust_scale(matrix: np.ndarray) -> Scale:
    center = np.median(matrix, axis=0)
    q25 = np.percentile(matrix, 25.0, axis=0)
    q75 = np.percentile(matrix, 75.0, axis=0)
    scale = (q75 - q25) / 1.349
    scale = np.where(scale < 1e-6, 1e-6, scale)
    return Scale(center=center, scale=scale)


def standardized(matrix: np.ndarray, scale: Scale) -> np.ndarray:
    return (matrix - scale.center) / scale.scale


def quality_key(event: dict[str, Any]) -> tuple[float, float, float, float, str]:
    uncertainty_sum = float(np.sum(uncertainty_vector(event)))
    fit_error = finite(event.get("fiterr"))
    qc = finite(event.get("Qc"))
    num_stat = finite(event.get("num_stat"))
    return (
        uncertainty_sum,
        fit_error if fit_error is not None else math.inf,
        -(qc if qc is not None else -math.inf),
        -(num_stat if num_stat is not None else -math.inf),
        str(event.get("id") or ""),
    )


def wrap_pi(values: np.ndarray) -> np.ndarray:
    return (values + np.pi) % (2.0 * np.pi) - np.pi


def pairwise_d_sh(events: list[dict[str, Any]]) -> np.ndarray:
    e = np.asarray([float(event["e"]) for event in events], dtype=np.float64)
    q = np.asarray([float(event["q"]) for event in events], dtype=np.float64)
    inc = np.radians([float(event["i"]) for event in events])
    peri = np.radians([float(event["peri"]) for event in events])
    node = np.radians([float(event["node"]) for event in events])

    e1, e2 = e[:, None], e[None, :]
    q1, q2 = q[:, None], q[None, :]
    i1, i2 = inc[:, None], inc[None, :]
    w1, w2 = peri[:, None], peri[None, :]
    o1, o2 = node[:, None], node[None, :]

    delta_node = wrap_pi(o2 - o1)
    cos_i = np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(delta_node)
    plane_angle = np.arccos(np.clip(cos_i, -1.0, 1.0))
    denominator = np.cos(0.5 * plane_angle)
    denominator = np.where(np.abs(denominator) < 1e-12, 1e-12, denominator)
    argument = np.cos(0.5 * (i1 + i2)) * np.sin(0.5 * delta_node) / denominator
    perihelion_angle = wrap_pi(w2 - w1 + 2.0 * np.arcsin(np.clip(argument, -1.0, 1.0)))

    d2 = (
        (e2 - e1) ** 2
        + (q2 - q1) ** 2
        + (2.0 * np.sin(0.5 * plane_angle)) ** 2
        + (((e1 + e2) * 0.5) * (2.0 * np.sin(0.5 * perihelion_angle))) ** 2
    )
    upper = np.triu_indices(len(events), k=1)
    values = np.sqrt(np.maximum(d2[upper], 0.0))
    if len(values) != len(events) * (len(events) - 1) // 2:
        raise RuntimeError("Unexpected D_SH pair count")
    return values


def group_metrics(
    events: list[dict[str, Any]],
    orbit_scale: Scale,
    uncertainty_scale: Scale,
) -> dict[str, Any]:
    orbit = np.vstack([orbit_vector(event) for event in events])
    uncertainty = np.vstack([uncertainty_vector(event) for event in events])
    orbit_median_z = standardized(np.median(orbit, axis=0)[None, :], orbit_scale)[0]
    uncertainty_median_z = standardized(
        np.median(uncertainty, axis=0)[None, :], uncertainty_scale
    )[0]
    distances = pairwise_d_sh(events)
    return {
        "orbit_median_z": orbit_median_z,
        "uncertainty_median_z": uncertainty_median_z,
        "d_median": float(np.median(distances)),
        "d_q90": float(np.percentile(distances, 90.0)),
    }


def match_candidate(
    target: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[bool, dict[str, float]]:
    orbit_distance = float(
        np.linalg.norm(candidate["orbit_median_z"] - target["orbit_median_z"])
    )
    uncertainty_distance = float(
        np.linalg.norm(
            candidate["uncertainty_median_z"] - target["uncertainty_median_z"]
        )
    )
    median_tolerance = max(0.002, 0.10 * target["d_median"])
    q90_tolerance = max(0.003, 0.15 * target["d_q90"])
    median_error = abs(candidate["d_median"] - target["d_median"])
    q90_error = abs(candidate["d_q90"] - target["d_q90"])
    diagnostics = {
        "orbit_distance": orbit_distance,
        "uncertainty_distance": uncertainty_distance,
        "d_median": candidate["d_median"],
        "d_q90": candidate["d_q90"],
        "d_median_abs_error": median_error,
        "d_q90_abs_error": q90_error,
        "d_median_relative_error": median_error / max(target["d_median"], 1e-12),
        "d_q90_relative_error": q90_error / max(target["d_q90"], 1e-12),
    }
    passed = bool(
        orbit_distance <= ORBIT_TOL
        and uncertainty_distance <= UNCERTAINTY_TOL
        and median_error <= median_tolerance
        and q90_error <= q90_tolerance
    )
    diagnostics["score"] = (
        orbit_distance / ORBIT_TOL
        + uncertainty_distance / UNCERTAINTY_TOL
        + median_error / median_tolerance
        + q90_error / q90_tolerance
    )
    return passed, diagnostics


def build_shower_groups(events: list[dict[str, Any]], control: int) -> list[list[dict[str, Any]]]:
    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if int(event["iau"]) == control and int(event["year"]) in YEARS:
            by_year[int(event["year"])].append(event)
    for year in YEARS:
        by_year[year].sort(key=quality_key)
        if len(by_year[year]) < GROUPS_PER_CONTROL * EVENTS_PER_YEAR:
            raise RuntimeError(
                f"Control {control} has only {len(by_year[year])} usable events in {year}"
            )
        by_year[year] = by_year[year][: GROUPS_PER_CONTROL * EVENTS_PER_YEAR]

    groups: list[list[dict[str, Any]]] = [[] for _ in range(GROUPS_PER_CONTROL)]
    for year in YEARS:
        selected = by_year[year]
        for group_index in range(GROUPS_PER_CONTROL):
            groups[group_index].extend(
                selected[group_index::GROUPS_PER_CONTROL][:EVENTS_PER_YEAR]
            )
    for group in groups:
        if len(group) != GROUP_SIZE or Counter(int(event["year"]) for event in group) != Counter(
            {year: EVENTS_PER_YEAR for year in YEARS}
        ):
            raise RuntimeError(f"Invalid shower subgroup for control {control}")
    all_ids = [str(event["id"]) for group in groups for event in group]
    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError(f"Shower subgroups for control {control} are not disjoint")
    return groups


def top_k_indices(values: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(values))
    if k <= 0:
        return np.asarray([], dtype=np.int64)
    if k == len(values):
        indices = np.arange(len(values), dtype=np.int64)
    else:
        indices = np.argpartition(values, k - 1)[:k]
    return indices[np.argsort(values[indices], kind="mergesort")]


def candidate_groups_for_target(
    target_events: list[dict[str, Any]],
    target_metrics: dict[str, Any],
    sporadic_by_year: dict[int, list[dict[str, Any]]],
    orbit_scale: Scale,
    uncertainty_scale: Scale,
    control: int,
    subgroup_index: int,
) -> tuple[list[Candidate], int]:
    matrices: dict[int, dict[str, np.ndarray]] = {}
    pooled_events: list[dict[str, Any]] = []
    pooled_orbit_z: list[np.ndarray] = []
    for year in YEARS:
        events = sporadic_by_year[year]
        orbit = np.vstack([orbit_vector(event) for event in events])
        uncertainty = np.vstack([uncertainty_vector(event) for event in events])
        orbit_z = standardized(orbit, orbit_scale)
        uncertainty_z = standardized(uncertainty, uncertainty_scale)
        matrices[year] = {
            "orbit_z": orbit_z,
            "uncertainty_z": uncertainty_z,
        }
        pooled_events.extend(events)
        pooled_orbit_z.extend(orbit_z)

    pooled_orbit = np.vstack(pooled_orbit_z)
    seed_distance = np.linalg.norm(
        pooled_orbit - target_metrics["orbit_median_z"][None, :], axis=1
    )
    seed_indices = top_k_indices(seed_distance, min(SEED_LIMIT, len(seed_distance)))
    seeds = [pooled_events[int(index)] for index in seed_indices]

    unique_candidates: dict[tuple[str, ...], Candidate] = {}
    evaluated = 0
    for seed_number, seed in enumerate(seeds):
        seed_orbit_z = standardized(orbit_vector(seed)[None, :], orbit_scale)[0]
        nearest: dict[int, np.ndarray] = {}
        for year in YEARS:
            orbit_distance = np.linalg.norm(
                matrices[year]["orbit_z"] - seed_orbit_z[None, :], axis=1
            )
            uncertainty_distance = np.linalg.norm(
                matrices[year]["uncertainty_z"]
                - target_metrics["uncertainty_median_z"][None, :],
                axis=1,
            )
            combined = orbit_distance + 0.25 * uncertainty_distance
            nearest[year] = top_k_indices(combined, max(K_VALUES))

        for k in K_VALUES:
            for variation in range(VARIATIONS):
                selected_indices: list[int] = []
                selected_events: list[dict[str, Any]] = []
                valid = True
                for year in YEARS:
                    neighborhood = nearest[year][: min(k, len(nearest[year]))]
                    if len(neighborhood) < EVENTS_PER_YEAR:
                        valid = False
                        break
                    if variation == 0:
                        chosen = neighborhood[:EVENTS_PER_YEAR]
                    else:
                        rng = np.random.default_rng(
                            stable_seed(control, subgroup_index, seed_number, k, variation, year)
                        )
                        chosen = np.sort(
                            rng.choice(neighborhood, size=EVENTS_PER_YEAR, replace=False)
                        )
                    for index in chosen:
                        selected_indices.append(int(index))
                        selected_events.append(sporadic_by_year[year][int(index)])
                if not valid:
                    continue
                evaluated += 1
                ids = tuple(sorted(str(event["id"]) for event in selected_events))
                if len(ids) != GROUP_SIZE or len(set(ids)) != GROUP_SIZE:
                    continue
                if ids in unique_candidates:
                    continue
                metrics = group_metrics(selected_events, orbit_scale, uncertainty_scale)
                passed, diagnostics = match_candidate(target_metrics, metrics)
                if not passed:
                    continue
                candidate = Candidate(
                    ids=ids,
                    indices=tuple(selected_indices),
                    id_set=frozenset(ids),
                    score=float(diagnostics["score"]),
                    diagnostics=diagnostics,
                )
                unique_candidates[ids] = candidate

    candidates = sorted(unique_candidates.values(), key=lambda item: (item.score, item.ids))
    return candidates, evaluated


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    return len(left & right) / len(left | right)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    events = load_events(args.events)
    data_gate = json.loads(args.data_gate.read_text(encoding="utf-8"))

    by_control: dict[int, list[dict[str, Any]]] = {
        control: [event for event in events if int(event["iau"]) == control]
        for control in CONTROLS
    }
    all_sporadic = [event for event in events if int(event["iau"]) == -1]

    result_controls: list[dict[str, Any]] = []
    matched_payload: dict[str, Any] = {
        "input": {
            "events_sha256": sha256_file(args.events),
            "data_gate_sha256": sha256_file(args.data_gate),
            "source_artifact_id": 8869994126,
            "source_artifact_digest": "sha256:bc6df6971b5d306af9836b2df71aebbacd6c3f4045ea1b8c1d5268caedc2c322",
        },
        "controls": [],
    }

    all_subgroups_pass = True
    for control in CONTROLS:
        month = CONTROL_MONTH[control]
        shower_groups = build_shower_groups(events, control)
        sporadic_by_year = {
            year: [
                event
                for event in all_sporadic
                if int(event["year"]) == year and int(event["month"]) == month
            ]
            for year in YEARS
        }
        for year in YEARS:
            if len(sporadic_by_year[year]) < 50:
                raise RuntimeError(
                    f"Insufficient sporadics for control {control}, year {year}: "
                    f"{len(sporadic_by_year[year])}"
                )

        sporadic_events = [event for year in YEARS for event in sporadic_by_year[year]]
        orbit_scale = robust_scale(np.vstack([orbit_vector(event) for event in sporadic_events]))
        uncertainty_scale = robust_scale(
            np.vstack([uncertainty_vector(event) for event in sporadic_events])
        )

        candidate_lists: list[list[Candidate]] = []
        subgroup_records: list[dict[str, Any]] = []
        for subgroup_index, target_events in enumerate(shower_groups):
            target_metrics = group_metrics(target_events, orbit_scale, uncertainty_scale)
            candidates, evaluated = candidate_groups_for_target(
                target_events,
                target_metrics,
                sporadic_by_year,
                orbit_scale,
                uncertainty_scale,
                control,
                subgroup_index,
            )
            candidate_lists.append(candidates)
            subgroup_records.append(
                {
                    "subgroup_index": subgroup_index,
                    "target_ids": [str(event["id"]) for event in target_events],
                    "target_year_counts": dict(
                        Counter(str(event["year"]) for event in target_events)
                    ),
                    "target_d_median": target_metrics["d_median"],
                    "target_d_q90": target_metrics["d_q90"],
                    "candidate_constructions_evaluated": evaluated,
                    "eligible_before_reuse_filter": len(candidates),
                    "accepted": [],
                }
            )

        usage: Counter[str] = Counter()
        pointers = [0 for _ in subgroup_records]
        accepted_sets: list[list[frozenset[str]]] = [[] for _ in subgroup_records]
        made_progress = True
        while made_progress and any(
            len(record["accepted"]) < MAX_MATCHES for record in subgroup_records
        ):
            made_progress = False
            for subgroup_index, record in enumerate(subgroup_records):
                if len(record["accepted"]) >= MAX_MATCHES:
                    continue
                candidates = candidate_lists[subgroup_index]
                while pointers[subgroup_index] < len(candidates):
                    candidate = candidates[pointers[subgroup_index]]
                    pointers[subgroup_index] += 1
                    if any(usage[event_id] >= MAX_EVENT_REUSE for event_id in candidate.ids):
                        continue
                    if any(
                        jaccard(candidate.id_set, existing) > MAX_JACCARD
                        for existing in accepted_sets[subgroup_index]
                    ):
                        continue
                    for event_id in candidate.ids:
                        usage[event_id] += 1
                    accepted_sets[subgroup_index].append(candidate.id_set)
                    record["accepted"].append(
                        {
                            "ids": list(candidate.ids),
                            "score": candidate.score,
                            **candidate.diagnostics,
                        }
                    )
                    made_progress = True
                    break

        control_passed = True
        for record in subgroup_records:
            accepted_count = len(record["accepted"])
            record["accepted_count"] = accepted_count
            record["passed_minimum"] = accepted_count >= MIN_MATCHES
            control_passed &= record["passed_minimum"]
            all_subgroups_pass &= record["passed_minimum"]
            if record["accepted"]:
                for key in (
                    "orbit_distance",
                    "uncertainty_distance",
                    "d_median_relative_error",
                    "d_q90_relative_error",
                ):
                    values = [float(item[key]) for item in record["accepted"]]
                    record[f"accepted_{key}_median"] = float(np.median(values))
                    record[f"accepted_{key}_worst"] = float(max(values))

        reuse_values = list(usage.values())
        control_record = {
            "control": control,
            "month": month,
            "sporadic_counts": {
                str(year): len(sporadic_by_year[year]) for year in YEARS
            },
            "subgroups": subgroup_records,
            "passed": control_passed,
            "distinct_sporadic_events_used": len(usage),
            "maximum_event_reuse": max(reuse_values) if reuse_values else 0,
            "event_reuse_histogram": dict(Counter(reuse_values)),
        }
        result_controls.append(control_record)
        matched_payload["controls"].append(control_record)

    verdict = (
        "PROCEED_TO_PREDICTABILITY_NORMALIZED_PROPAGATION"
        if all_subgroups_pass
        else "KILL_DYNAMICAL_COHERENCE_STATIC_MATCHING"
    )
    summary = {
        "verdict": verdict,
        "gate": "every_16_subgroups_at_least_12_matches",
        "passed": all_subgroups_pass,
        "controls": result_controls,
        "input": matched_payload["input"],
        "data_gate_original_verdict": data_gate.get("verdict"),
        "correction_document": "dynamical_matching_stage0/FEASIBILITY_CORRECTION.md",
    }
    (args.output / "static_matching.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    with gzip.open(args.output / "matched_groups.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(matched_payload, handle, separators=(",", ":"))

    lines = [
        "# Predictability-normalized dynamics: static matched-null gate",
        "",
        "GhostStream was excluded. No orbital propagation was performed.",
        "",
        "| Control | Subgroup | Eligible before reuse | Accepted | Pass |",
        "|---:|---:|---:|---:|---|",
    ]
    for control_record in result_controls:
        for subgroup in control_record["subgroups"]:
            lines.append(
                f"| {control_record['control']} | {subgroup['subgroup_index']} "
                f"| {subgroup['eligible_before_reuse_filter']:,} "
                f"| {subgroup['accepted_count']} "
                f"| {'yes' if subgroup['passed_minimum'] else 'no'} |"
            )
    lines.extend(
        [
            "",
            "Frozen requirement: all 16 subgroups must have at least 12 matches.",
            "",
            f"Verdict: **{verdict}**",
        ]
    )
    report = "\n".join(lines)
    (args.output / "STATIC_MATCHING_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
