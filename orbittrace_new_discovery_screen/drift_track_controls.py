#!/usr/bin/env python3
"""Compute-only implementation of the raw drift-track control benchmark.

Scientific protocol:
  brandonlign/orbittrace-raw
  pipeline/discovery_search/DRIFT_TRACK_CONTROL_BENCHMARK.md

The benchmark is deliberately target-aware only at evaluation time. Candidate
local clusters, graph links, track fitting, and orbit gates never receive the
published control coordinates.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

from orbittrace_new_discovery_screen import corrected_allseason_month as base

WINDOW_WIDTH = 2.0
WINDOW_STRIDE = 1.0
HALF_WINDOW = WINDOW_WIDTH / 2.0
LINK_RADIANT_DEG = 5.0
LINK_JACCARD = 0.08
TRACK_RESIDUAL_RADIUS = 2.0
TRACK_SCALES = np.asarray([3.5, 3.0, 2.5], dtype=float)
MIN_TRACK_NODES = 3
MIN_TRACK_MEMBERS = 12
MIN_TRACK_SOLAR_SPAN = 3.0
MAX_TRACK_RMS = 1.5
MIN_VALID_ORBITS = 10
MIN_VALID_ORBIT_FRACTION = 0.80
MAX_D50 = 0.12
MAX_D90 = 0.25

VARIANTS = {
    "A_EOM_5_3": {"selection": "eom", "min_cluster_size": 5, "min_samples": 3},
    "B_LEAF_5_3": {"selection": "leaf", "min_cluster_size": 5, "min_samples": 3},
    "C_EOM_8_4": {"selection": "eom", "min_cluster_size": 8, "min_samples": 4},
    "D_LEAF_8_4": {"selection": "leaf", "min_cluster_size": 8, "min_samples": 4},
}

CONTROLS = {
    "M2025-P1": {
        "month": 7,
        "activity": [122.0, 131.0],
        "ref_sol": 125.8,
        "slon": 253.4,
        "beta": -30.6,
        "vg": 61.4,
    },
    "M2025-S1": {
        "month": 9,
        "activity": [170.0, 176.0],
        "ref_sol": 172.9,
        "slon": 141.2,
        "beta": 27.4,
        "vg": 12.5,
    },
    "M2025-S2": {
        "month": 9,
        "activity": [166.9, 188.4],
        "ref_sol": 181.3,
        "slon": 163.6,
        "beta": -71.5,
        "vg": 22.1,
    },
    "M2025-U1": {
        "month": 10,
        "activity": [206.0, 214.0],
        "ref_sol": 211.0,
        "slon": 153.6,
        "beta": 11.3,
        "vg": 14.0,
    },
}


def circular_mean(values: np.ndarray) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def unwrap_about(values: np.ndarray, reference: float) -> np.ndarray:
    return float(reference) + base.circ_diff(np.asarray(values, dtype=float), float(reference))


def prepare_all_quality(frame: pd.DataFrame, year: int, month: int) -> dict[str, Any]:
    missing = [column for column in base.BASE_COLUMNS if column not in frame.columns]
    if missing:
        raise RuntimeError(f"GMN {year}-{month:02d} missing columns: {missing}")
    data = frame[base.BASE_COLUMNS].copy()
    numeric = [
        "sol_lon_deg",
        "lamgeo_deg",
        "betgeo_deg",
        "vgeo_km_s",
        *base.ORBIT_COLUMNS,
        *base.SIGMA_COLUMNS,
        "medianfiterr_arcsec",
        "num_stat",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    valid = np.isfinite(
        data[["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s"]].to_numpy(float)
    ).all(axis=1)
    valid &= data["sol_lon_deg"].between(0, 360).to_numpy()
    valid &= data["lamgeo_deg"].between(0, 360).to_numpy()
    valid &= data["betgeo_deg"].between(-90, 90).to_numpy()
    valid &= data["vgeo_km_s"].between(5, 75).to_numpy()
    valid &= data["num_stat"].fillna(0).to_numpy(float) >= 2
    valid &= data["medianfiterr_arcsec"].fillna(9999).to_numpy(float) <= 180
    data = data.loc[valid].reset_index(drop=True)
    sol = data["sol_lon_deg"].to_numpy(float)
    slon = base.circ_diff(data["lamgeo_deg"].to_numpy(float), sol) % 360.0
    beta = data["betgeo_deg"].to_numpy(float)
    vg = data["vgeo_km_s"].to_numpy(float)
    sol_reference = circular_mean(sol)
    sol_unwrapped = unwrap_about(sol, sol_reference)
    return {
        "data": data,
        "sol": sol,
        "sol_unwrapped": sol_unwrapped,
        "sol_reference": sol_reference,
        "slon": slon,
        "beta": beta,
        "vg": vg,
    }


def window_centers(sol_unwrapped: np.ndarray) -> list[float]:
    low = math.floor(float(np.min(sol_unwrapped))) + HALF_WINDOW
    high = math.ceil(float(np.max(sol_unwrapped))) - HALF_WINDOW
    if high < low:
        return []
    count = int(math.floor((high - low) / WINDOW_STRIDE)) + 1
    return [low + index * WINDOW_STRIDE for index in range(count)]


def build_nodes(prepared: dict[str, Any], variant_name: str) -> list[dict[str, Any]]:
    config = VARIANTS[variant_name]
    nodes: list[dict[str, Any]] = []
    data = prepared["data"]
    slon = prepared["slon"]
    beta = prepared["beta"]
    vg = prepared["vg"]
    sol_u = prepared["sol_unwrapped"]
    for center_index, center in enumerate(window_centers(sol_u)):
        idx = np.flatnonzero(np.abs(sol_u - center) <= HALF_WINDOW)
        if len(idx) < max(20, int(config["min_cluster_size"]) * 2):
            continue
        matrix = np.column_stack([slon[idx] / 3.5, beta[idx] / 3.0, vg[idx] / 2.5])
        # Circular longitude needs a local unwrap so a cluster cannot be split at 0/360.
        local_ref = circular_mean(slon[idx])
        matrix[:, 0] = unwrap_about(slon[idx], local_ref) / 3.5
        model = HDBSCAN(
            min_cluster_size=int(config["min_cluster_size"]),
            min_samples=int(config["min_samples"]),
            cluster_selection_method=str(config["selection"]),
            n_jobs=-1,
        )
        labels = model.fit_predict(matrix)
        probs = np.asarray(model.probabilities_, dtype=float)
        for label in sorted(int(value) for value in np.unique(labels) if int(value) >= 0):
            local = np.flatnonzero(labels == label)
            members = idx[local]
            if len(members) < int(config["min_cluster_size"]):
                continue
            ids = data.iloc[members]["unique_trajectory_identifier"].astype(str).tolist()
            nodes.append(
                {
                    "node_id": len(nodes),
                    "window_index": int(center_index),
                    "window_center_unwrapped": float(center),
                    "members": members,
                    "event_ids": ids,
                    "event_set": set(ids),
                    "slon": circular_mean(slon[members]),
                    "beta": float(np.median(beta[members])),
                    "vg": float(np.median(vg[members])),
                    "mean_probability": float(np.mean(probs[local])),
                }
            )
    return nodes


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def linked_components(nodes: list[dict[str, Any]]) -> list[list[int]]:
    if not nodes:
        return []
    by_window: dict[int, list[int]] = defaultdict(list)
    for index, node in enumerate(nodes):
        by_window[int(node["window_index"])].append(index)
    uf = UnionFind(len(nodes))
    for window, left_indices in by_window.items():
        right_indices = by_window.get(window + 1, [])
        for left_index in left_indices:
            left = nodes[left_index]
            for right_index in right_indices:
                right = nodes[right_index]
                radiant = base.spherical_sep(
                    float(left["slon"]),
                    float(left["beta"]),
                    float(right["slon"]),
                    float(right["beta"]),
                )
                if radiant > LINK_RADIANT_DEG:
                    continue
                speed_limit = max(1.5, 0.10 * 0.5 * (float(left["vg"]) + float(right["vg"])))
                if abs(float(left["vg"]) - float(right["vg"])) > speed_limit:
                    continue
                intersection = len(left["event_set"] & right["event_set"])
                if intersection < 1:
                    continue
                union = len(left["event_set"] | right["event_set"])
                jaccard = intersection / union if union else 0.0
                if jaccard < LINK_JACCARD:
                    continue
                uf.union(left_index, right_index)
    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(nodes)):
        groups[uf.find(index)].append(index)
    return list(groups.values())


def fit_line_track(prepared: dict[str, Any], nodes: list[dict[str, Any]], component: list[int]) -> dict[str, Any] | None:
    if len(component) < MIN_TRACK_NODES:
        return None
    event_ids: set[str] = set()
    for node_index in component:
        event_ids.update(nodes[node_index]["event_ids"])
    if len(event_ids) < MIN_TRACK_MEMBERS:
        return None
    data = prepared["data"]
    id_series = data["unique_trajectory_identifier"].astype(str)
    indices = np.flatnonzero(id_series.isin(event_ids).to_numpy())
    if len(indices) < MIN_TRACK_MEMBERS:
        return None
    sol_u = prepared["sol_unwrapped"][indices]
    slon = prepared["slon"][indices]
    beta = prepared["beta"][indices]
    vg = prepared["vg"][indices]
    slon_ref = circular_mean(slon)
    slon_u = unwrap_about(slon, slon_ref)
    keep = np.ones(len(indices), dtype=bool)
    coefficients: list[np.ndarray] = []
    residual_r2 = np.full(len(indices), np.inf)
    for _iteration in range(3):
        if int(keep.sum()) < MIN_TRACK_MEMBERS:
            return None
        x = sol_u[keep]
        x0 = float(np.median(x))
        y = [slon_u[keep], beta[keep], vg[keep]]
        coefficients = [np.polyfit(x - x0, axis, 1) for axis in y]
        pred = np.column_stack(
            [
                np.polyval(coefficients[0], sol_u - x0),
                np.polyval(coefficients[1], sol_u - x0),
                np.polyval(coefficients[2], sol_u - x0),
            ]
        )
        actual = np.column_stack([slon_u, beta, vg])
        residual = actual - pred
        residual_r2 = np.sum((residual / TRACK_SCALES[None, :]) ** 2, axis=1)
        new_keep = residual_r2 <= TRACK_RESIDUAL_RADIUS**2
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
    if int(keep.sum()) < MIN_TRACK_MEMBERS:
        return None
    kept_indices = indices[keep]
    solar_span = float(np.max(prepared["sol_unwrapped"][kept_indices]) - np.min(prepared["sol_unwrapped"][kept_indices]))
    if solar_span < MIN_TRACK_SOLAR_SPAN:
        return None
    rms = float(np.sqrt(np.mean(residual_r2[keep])))
    if rms > MAX_TRACK_RMS:
        return None
    frame = data.iloc[kept_indices].reset_index(drop=True)
    orbit_mask = base.valid_orbits(frame)
    valid_count = int(orbit_mask.sum())
    if valid_count < MIN_VALID_ORBITS or valid_count / len(frame) < MIN_VALID_ORBIT_FRACTION:
        return None
    orbit = base.orbit_summary(frame.loc[orbit_mask, base.ORBIT_COLUMNS].to_numpy(float))
    if orbit["median_d"] > MAX_D50 or orbit["q90_d"] > MAX_D90:
        return None
    x0 = float(np.median(prepared["sol_unwrapped"][kept_indices]))
    # Refit exactly on retained members for the final reported track.
    final_sol = prepared["sol_unwrapped"][kept_indices]
    final_slon_ref = circular_mean(prepared["slon"][kept_indices])
    final_slon = unwrap_about(prepared["slon"][kept_indices], final_slon_ref)
    final_beta = prepared["beta"][kept_indices]
    final_vg = prepared["vg"][kept_indices]
    final_coeff = [
        np.polyfit(final_sol - x0, final_slon, 1),
        np.polyfit(final_sol - x0, final_beta, 1),
        np.polyfit(final_sol - x0, final_vg, 1),
    ]
    label_counts = Counter(base.code_text(value) or "<SPORADIC>" for value in frame["iau_code"].tolist())
    return {
        "node_count": int(len(component)),
        "members": int(len(frame)),
        "solar_span_deg": solar_span,
        "solar_min_unwrapped": float(np.min(final_sol)),
        "solar_max_unwrapped": float(np.max(final_sol)),
        "reference_sol_unwrapped": x0,
        "reference_slon_unwrapped": float(final_coeff[0][1]),
        "reference_beta": float(final_coeff[1][1]),
        "reference_vg": float(final_coeff[2][1]),
        "slopes": {
            "slon_per_sol": float(final_coeff[0][0]),
            "beta_per_sol": float(final_coeff[1][0]),
            "vg_per_sol": float(final_coeff[2][0]),
        },
        "normalized_rms": rms,
        "orbit_median_d": float(orbit["median_d"]),
        "orbit_q90_d": float(orbit["q90_d"]),
        "orbit_medoid": np.asarray(orbit["medoid"], dtype=float).tolist(),
        "valid_orbit_count": valid_count,
        "label_counts": dict(label_counts.most_common(12)),
        "event_ids": frame["unique_trajectory_identifier"].astype(str).tolist(),
    }


def tracks_for_variant(prepared: dict[str, Any], variant_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    nodes = build_nodes(prepared, variant_name)
    components = linked_components(nodes)
    tracks: list[dict[str, Any]] = []
    for component in components:
        track = fit_line_track(prepared, nodes, component)
        if track is not None:
            tracks.append(track)
    tracks.sort(key=lambda item: (-item["members"], item["normalized_rms"], item["reference_slon_unwrapped"]))
    return tracks, {
        "local_nodes": int(len(nodes)),
        "graph_components": int(len(components)),
        "retained_tracks": int(len(tracks)),
    }


def track_prediction(track: dict[str, Any], sol: float, prepared: dict[str, Any]) -> tuple[float, float, float]:
    target_u = float(prepared["sol_reference"] + base.circ_diff(sol, prepared["sol_reference"]))
    dx = target_u - float(track["reference_sol_unwrapped"])
    slon = (float(track["reference_slon_unwrapped"]) + float(track["slopes"]["slon_per_sol"]) * dx) % 360.0
    beta = float(track["reference_beta"]) + float(track["slopes"]["beta_per_sol"]) * dx
    vg = float(track["reference_vg"]) + float(track["slopes"]["vg_per_sol"]) * dx
    return slon, beta, vg


def evaluate_control(control_name: str, control: dict[str, Any], tracks: list[dict[str, Any]], prepared: dict[str, Any]) -> dict[str, Any]:
    start_u = float(prepared["sol_reference"] + base.circ_diff(control["activity"][0], prepared["sol_reference"]))
    end_u = float(prepared["sol_reference"] + base.circ_diff(control["activity"][1], prepared["sol_reference"]))
    if end_u < start_u:
        start_u, end_u = end_u, start_u
    matches = []
    for index, track in enumerate(tracks):
        if float(track["solar_max_unwrapped"]) < start_u or float(track["solar_min_unwrapped"]) > end_u:
            continue
        slon, beta, vg = track_prediction(track, float(control["ref_sol"]), prepared)
        radiant = base.spherical_sep(slon, beta, float(control["slon"]), float(control["beta"]))
        speed = abs(vg - float(control["vg"]))
        speed_limit = max(1.5, 0.10 * float(control["vg"]))
        eligible = radiant <= 5.0 and speed <= speed_limit
        score = math.sqrt((radiant / 5.0) ** 2 + (speed / speed_limit) ** 2)
        matches.append(
            {
                "track_index": int(index),
                "eligible": bool(eligible),
                "score": float(score),
                "radiant_sep_deg": float(radiant),
                "speed_delta_km_s": float(speed),
                "predicted_slon": float(slon),
                "predicted_beta": float(beta),
                "predicted_vg": float(vg),
                "track_members": int(track["members"]),
                "track_nodes": int(track["node_count"]),
                "track_solar_span_deg": float(track["solar_span_deg"]),
                "track_slopes": track["slopes"],
                "track_label_counts": track["label_counts"],
            }
        )
    matches.sort(key=lambda item: (not item["eligible"], item["score"], -item["track_members"]))
    best = matches[0] if matches else None
    return {
        "control": control_name,
        "recovered": bool(best is not None and best["eligible"]),
        "best": best,
    }


def compact_track(track: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in track.items() if key != "event_ids"}


def main() -> int:
    months = [7, 9, 10]
    month_results: dict[str, Any] = {}
    for month in months:
        print(f"Loading 2025-{month:02d} positive-control month", flush=True)
        prepared = prepare_all_quality(base.load_month(2025, month), 2025, month)
        variant_results: dict[str, Any] = {}
        controls_here = {name: value for name, value in CONTROLS.items() if int(value["month"]) == month}
        for variant_name in VARIANTS:
            print(f"  variant {variant_name}", flush=True)
            tracks, diagnostics = tracks_for_variant(prepared, variant_name)
            control_eval = {
                name: evaluate_control(name, control, tracks, prepared)
                for name, control in controls_here.items()
            }
            print(
                f"    nodes={diagnostics['local_nodes']} tracks={len(tracks)} "
                + " ".join(f"{name}={item['recovered']}" for name, item in control_eval.items()),
                flush=True,
            )
            variant_results[variant_name] = {
                "diagnostics": diagnostics,
                "controls": control_eval,
                "tracks": [compact_track(track) for track in tracks],
            }
        month_results[str(month)] = {
            "quality_rows": int(len(prepared["data"])),
            "variants": variant_results,
        }

    aggregate: dict[str, Any] = {}
    for variant_name, config in VARIANTS.items():
        recovered = 0
        member_sum = 0
        retained_tracks = 0
        controls: dict[str, Any] = {}
        for month in months:
            result = month_results[str(month)]["variants"][variant_name]
            retained_tracks += int(result["diagnostics"]["retained_tracks"])
            for control_name, evaluation in result["controls"].items():
                controls[control_name] = evaluation
                if evaluation["recovered"]:
                    recovered += 1
                    member_sum += int(evaluation["best"]["track_members"])
        aggregate[variant_name] = {
            "config": config,
            "controls_recovered": int(recovered),
            "control_associated_member_sum": int(member_sum),
            "retained_tracks": int(retained_tracks),
            "controls": controls,
        }

    def selection_key(name: str) -> tuple[Any, ...]:
        row = aggregate[name]
        config = VARIANTS[name]
        return (
            -int(row["controls_recovered"]),
            -int(row["control_associated_member_sum"]),
            int(row["retained_tracks"]),
            -int(int(config["min_cluster_size"]) == 8),
            -int(str(config["selection"]) == "eom"),
            name,
        )

    selected = min(VARIANTS, key=selection_key)
    sufficient = int(aggregate[selected]["controls_recovered"]) >= 3
    output = {
        "stage": "drift_track_control_benchmark_v1",
        "scientific_protocol": "orbittrace-raw/pipeline/discovery_search/DRIFT_TRACK_CONTROL_BENCHMARK.md",
        "months": months,
        "controls": CONTROLS,
        "variants": VARIANTS,
        "month_results": month_results,
        "aggregate": aggregate,
        "selected_variant": selected,
        "selected_variant_sufficient_for_discovery_handoff": bool(sufficient),
        "verdict": "PROMOTE_SELECTED_VARIANT" if sufficient else "DETECTOR_FAMILY_INSUFFICIENT",
    }
    out = Path("drift_track_control_results")
    out.mkdir(parents=True, exist_ok=True)
    (out / "drift_track_control_benchmark.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Drift-track positive-control benchmark",
        "",
        f"**Verdict:** `{output['verdict']}`",
        f"Selected variant: **{selected}**.",
        "",
        "| variant | controls recovered | control member sum | retained tracks | P1 | S1 | S2 | U1 |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for name in VARIANTS:
        row = aggregate[name]
        status = {control: row["controls"].get(control, {}).get("recovered", False) for control in CONTROLS}
        lines.append(
            f"| {name} | {row['controls_recovered']} | {row['control_associated_member_sum']} | {row['retained_tracks']} | "
            f"{status['M2025-P1']} | {status['M2025-S1']} | {status['M2025-S2']} | {status['M2025-U1']} |"
        )
    lines.extend(["", "## Best control matches", ""])
    for control_name in CONTROLS:
        evaluation = aggregate[selected]["controls"].get(control_name)
        if not evaluation:
            continue
        best = evaluation.get("best")
        if best is None:
            lines.append(f"- {control_name}: no candidate track overlapped its activity interval.")
        else:
            lines.append(
                f"- {control_name}: recovered={evaluation['recovered']}; N={best['track_members']}; "
                f"radiant separation={best['radiant_sep_deg']:.2f} deg; speed delta={best['speed_delta_km_s']:.2f} km/s; "
                f"slopes={best['track_slopes']}; labels={best['track_label_counts']}."
            )
    markdown = "\n".join(lines) + "\n"
    (out / "DRIFT_TRACK_CONTROL_BENCHMARK.md").write_text(markdown, encoding="utf-8")
    print(markdown, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
