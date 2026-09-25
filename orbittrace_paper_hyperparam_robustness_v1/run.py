#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader
from sklearn.cluster import HDBSCAN

OUT = Path("orbittrace_paper_hyperparam_robustness_v1/output")
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent

CENTER = np.array([-149.297555, 7.450070, 37.422240, 36.901963], dtype=float)
CENTER_SCALE = np.array([0.881191, 0.579296, 1.099081, 1.329625], dtype=float)
SOL_HALF_WIDTH = 12.5
ASSOC_SOL_MAX = 3.989
BASE = {
    "lon_scale": 3.5,
    "beta_scale": 3.0,
    "speed_scale": 2.5,
    "sol_scale": 2.5,
    "min_cluster_size": 8,
    "min_samples": 4,
}

BASE_COLUMNS = [
    "unique_trajectory_identifier", "beginning_utc_time", "iau_code",
    "sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s",
    "medianfiterr_arcsec", "num_stat", "participating_stations",
]


def circ_diff(value: np.ndarray | float, center: np.ndarray | float) -> np.ndarray:
    return (np.asarray(value) - np.asarray(center) + 180.0) % 360.0 - 180.0


def circ_center(values: np.ndarray) -> float:
    x = np.deg2rad(np.asarray(values, dtype=float))
    return float(np.rad2deg(math.atan2(float(np.sin(x).mean()), float(np.cos(x).mean()))) % 360.0)


def shower_label(value: Any) -> str:
    if pd.isna(value):
        return "SPORADIC"
    text = str(value).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return "SPORADIC" if text in {"", "-1", "0", "...", "NONE", "NAN", "SPO", "SPORADIC"} else text


def load_month(year: int) -> pd.DataFrame:
    key = f"{year}-04"
    print(f"Downloading {key}", flush=True)
    frame = reader.read_data(dd.get_monthly_file_content_by_date(key), output_camel_case=True).reset_index(drop=False)
    missing = [c for c in BASE_COLUMNS if c not in frame.columns]
    if missing:
        raise RuntimeError(f"Missing columns for {key}: {missing}")
    data = frame[BASE_COLUMNS].copy()
    data["year"] = year
    data["label"] = data["iau_code"].map(shower_label)
    for c in ["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s", "medianfiterr_arcsec", "num_stat"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    valid = np.isfinite(data[["sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s"]]).all(axis=1)
    valid &= data["sol_lon_deg"].between(0, 360)
    valid &= data["lamgeo_deg"].between(0, 360)
    valid &= data["betgeo_deg"].between(-90, 90)
    valid &= data["vgeo_km_s"].between(5, 75)
    valid &= data["num_stat"].fillna(0) >= 2
    valid &= data["medianfiterr_arcsec"].fillna(9999) <= 180
    data = data.loc[valid & (data["label"] == "SPORADIC")].copy()
    data["beginning_utc_time"] = pd.to_datetime(data["beginning_utc_time"], errors="coerce", utc=True)
    data = data.loc[data["beginning_utc_time"].notna()].copy()
    # Manuscript deduplication rule: lowest fit error, then larger station count.
    data = data.sort_values(
        ["beginning_utc_time", "medianfiterr_arcsec", "num_stat"],
        ascending=[True, True, False],
        kind="mergesort",
    ).drop_duplicates(subset=["beginning_utc_time"], keep="first")
    data["sun_lon"] = circ_diff(data["lamgeo_deg"].to_numpy(float), data["sol_lon_deg"].to_numpy(float))
    data["unique_trajectory_identifier"] = data["unique_trajectory_identifier"].astype(str)
    return data.reset_index(drop=True)


def features(data: pd.DataFrame, s: dict[str, Any]) -> np.ndarray:
    lon = np.deg2rad(np.mod(data["sun_lon"].to_numpy(float), 360.0))
    sol = np.deg2rad(np.mod(data["sol_lon_deg"].to_numpy(float), 360.0))
    lon_scale = np.deg2rad(float(s["lon_scale"]))
    sol_scale = np.deg2rad(float(s["sol_scale"]))
    return np.column_stack([
        np.cos(lon) / lon_scale,
        np.sin(lon) / lon_scale,
        data["betgeo_deg"].to_numpy(float) / float(s["beta_scale"]),
        data["vgeo_km_s"].to_numpy(float) / float(s["speed_scale"]),
        np.cos(sol) / sol_scale,
        np.sin(sol) / sol_scale,
    ])


def centroid(data: pd.DataFrame, idx: np.ndarray) -> np.ndarray:
    part = data.iloc[idx]
    sun = circ_center(np.mod(part["sun_lon"].to_numpy(float), 360.0))
    if sun > 180:
        sun -= 360.0
    sol = circ_center(part["sol_lon_deg"].to_numpy(float))
    return np.array([
        sun,
        float(np.median(part["betgeo_deg"])),
        float(np.median(part["vgeo_km_s"])),
        sol,
    ], dtype=float)


def center_distance(c: np.ndarray) -> tuple[float, float]:
    delta = np.array([
        float(circ_diff(c[0], CENTER[0])),
        c[1] - CENTER[1],
        c[2] - CENTER[2],
        float(circ_diff(c[3], CENTER[3])),
    ])
    d2 = float(np.sum((delta / CENTER_SCALE) ** 2))
    return math.sqrt(d2), abs(float(delta[3]))


def evaluate_setting(data: pd.DataFrame, canonical: pd.DataFrame, s: dict[str, Any], setting_id: str, family: str) -> dict[str, Any]:
    X = features(data, s)
    model = HDBSCAN(
        min_cluster_size=int(s["min_cluster_size"]),
        min_samples=int(s["min_samples"]),
        cluster_selection_method="leaf",
        leaf_size=60,
        n_jobs=-1,
    )
    labels = model.fit_predict(X)
    cluster_ids = [int(x) for x in np.unique(labels) if int(x) >= 0]
    associated: list[tuple[int, np.ndarray, float]] = []
    nearest: tuple[int, np.ndarray, float] | None = None
    for cid in cluster_ids:
        idx = np.flatnonzero(labels == cid)
        c = centroid(data, idx)
        dist, sol_delta = center_distance(c)
        if nearest is None or dist < nearest[2]:
            nearest = (cid, c, dist)
        if dist <= 3.0 and sol_delta <= ASSOC_SOL_MAX:
            associated.append((cid, c, dist))

    if associated:
        mask = np.isin(labels, [x[0] for x in associated])
        union_idx = np.flatnonzero(mask)
    else:
        union_idx = np.array([], dtype=int)
    union = data.iloc[union_idx]
    union_ids = set(union["unique_trajectory_identifier"].astype(str))
    canon_ids = set(canonical["unique_trajectory_identifier"].astype(str))
    overlap_ids = union_ids & canon_ids
    n_union = len(union_ids)
    n_canon = len(canon_ids)
    n_overlap = len(overlap_ids)
    precision = n_overlap / n_union if n_union else 0.0
    recall = n_overlap / n_canon if n_canon else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    jaccard = n_overlap / (n_union + n_canon - n_overlap) if n_union + n_canon - n_overlap else 0.0

    years: dict[str, Any] = {}
    for year in [2025, 2026]:
        canon_y = set(canonical.loc[canonical["year"] == year, "unique_trajectory_identifier"].astype(str))
        union_y = set(union.loc[union["year"] == year, "unique_trajectory_identifier"].astype(str))
        years[str(year)] = {
            "canonical": len(canon_y),
            "union": len(union_y),
            "overlap": len(canon_y & union_y),
        }

    return {
        "setting_id": setting_id,
        "family": family,
        **s,
        "rows": int(len(data)),
        "clusters": int(len(cluster_ids)),
        "noise_fraction": float(np.mean(labels < 0)),
        "associated_clusters": int(len(associated)),
        "associated_cluster_ids": [int(x[0]) for x in associated],
        "associated_union_members": int(n_union),
        "canonical_overlap": int(n_overlap),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "jaccard": float(jaccard),
        "year_2025_union": years["2025"]["union"],
        "year_2025_overlap": years["2025"]["overlap"],
        "year_2026_union": years["2026"]["union"],
        "year_2026_overlap": years["2026"]["overlap"],
        "nearest_centroid_distance": float(nearest[2]) if nearest else None,
        "nearest_centroid": nearest[1].tolist() if nearest else None,
        "best_associated_centroid_distance": float(min(x[2] for x in associated)) if associated else None,
        "best_associated_centroid": min(associated, key=lambda x: x[2])[1].tolist() if associated else None,
    }


def build_settings() -> list[tuple[str, str, dict[str, Any]]]:
    out: list[tuple[str, str, dict[str, Any]]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(setting_id: str, family: str, **changes: Any) -> None:
        s = dict(BASE)
        s.update(changes)
        key = tuple(s[k] for k in ["lon_scale", "beta_scale", "speed_scale", "sol_scale", "min_cluster_size", "min_samples"])
        if key in seen:
            return
        seen.add(key)
        out.append((setting_id, family, s))

    add("baseline", "baseline")
    sweeps = {
        "lon_scale": [2.5, 3.0, 3.5, 4.0, 4.5],
        "beta_scale": [2.0, 2.5, 3.0, 3.5, 4.0],
        "speed_scale": [1.5, 2.0, 2.5, 3.0, 3.5],
        "sol_scale": [1.5, 2.0, 2.5, 3.0, 3.5],
        "min_cluster_size": [6, 8, 10, 12, 15],
        "min_samples": [2, 3, 4, 5, 6],
    }
    for param, vals in sweeps.items():
        for v in vals:
            if v == BASE[param]:
                continue
            add(f"ofat_{param}_{str(v).replace('.', 'p')}", f"ofat_{param}", **{param: v})

    n = 0
    for lon in [2.5, 4.5]:
        for speed in [1.5, 3.5]:
            for mcs in [6, 12]:
                for ms in [2, 6]:
                    n += 1
                    add(f"corner_{n:02d}", "joint_corner", lon_scale=lon, speed_scale=speed, min_cluster_size=mcs, min_samples=ms)
    assert len(out) == 41, len(out)
    return out


def summarize(rows: list[dict[str, Any]], full_baseline: dict[str, Any], input_info: dict[str, Any]) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    metrics = {}
    for col in ["precision", "recall", "f1", "jaccard", "nearest_centroid_distance"]:
        vals = pd.to_numeric(frame[col], errors="coerce").dropna()
        metrics[col] = {
            "min": float(vals.min()), "median": float(vals.median()), "max": float(vals.max())
        }
    fractions = {str(t): float((frame["recall"] >= t).mean()) for t in [0.50, 0.75, 0.90]}
    both_years_8 = float(((frame["year_2025_overlap"] >= 8) & (frame["year_2026_overlap"] >= 8)).mean())
    return {
        "protocol": "orbittrace_paper_hyperparam_robustness_v1",
        "settings": int(len(rows)),
        "input": input_info,
        "baseline": BASE,
        "diagnostic_half_width_deg": SOL_HALF_WIDTH,
        "canonical_members": int(len(set(canonical_global["unique_trajectory_identifier"]))),
        "canonical_by_year": {str(k): int(v) for k, v in canonical_global.groupby("year").size().items()},
        "full_april_baseline": full_baseline,
        "recall_threshold_fractions": fractions,
        "both_years_overlap_at_least_8_fraction": both_years_8,
        "metric_summary": metrics,
        "all_settings_have_associated_cluster": bool((frame["associated_clusters"] > 0).all()),
        "all_settings": rows,
        "claim_boundary": "Retrospective target-association robustness only; no setting was selected from the result and this is not a blind reranking experiment.",
    }


def write_markdown(result: dict[str, Any]) -> None:
    rows = pd.DataFrame(result["all_settings"])
    b = rows.loc[rows["setting_id"] == "baseline"].iloc[0]
    frac = result["recall_threshold_fractions"]
    m = result["metric_summary"]
    lines = [
        "# OrbitTrace ACRF/HDBSCAN hyperparameter robustness v1 — result",
        "",
        "## Frozen design",
        "",
        f"The preregistered diagnostic evaluated **{result['settings']}** settings: 25 one-factor/baseline settings plus 16 joint corner stresses. The clustering window, canonical scoring set and association rule were fixed before execution.",
        "",
        "## Baseline",
        "",
        f"Within the fixed 25-degree diagnostic band, the manuscript setting recovered {int(b['canonical_overlap'])}/63 canonical 2025-2026 meteors in {int(b['associated_clusters'])} associated leaf cluster(s): precision={b['precision']:.3f}, recall={b['recall']:.3f}, F1={b['f1']:.3f}, Jaccard={b['jaccard']:.3f}. Year overlaps were {int(b['year_2025_overlap'])}/34 and {int(b['year_2026_overlap'])}/29.",
        "",
        f"A separate full-April baseline fit recovered {result['full_april_baseline']['canonical_overlap']}/63 canonical meteors, with precision={result['full_april_baseline']['precision']:.3f}, recall={result['full_april_baseline']['recall']:.3f}, F1={result['full_april_baseline']['f1']:.3f}.",
        "",
        "## Across the frozen 41-setting sweep",
        "",
        f"- recall >=0.50: {frac['0.5']*100:.1f}% of settings",
        f"- recall >=0.75: {frac['0.75']*100:.1f}% of settings",
        f"- recall >=0.90: {frac['0.9']*100:.1f}% of settings",
        f"- both 2025 and 2026 retain >=8 canonical overlaps: {result['both_years_overlap_at_least_8_fraction']*100:.1f}% of settings",
        f"- associated cluster found: {100.0 if result['all_settings_have_associated_cluster'] else (rows['associated_clusters'].gt(0).mean()*100):.1f}% of settings",
        f"- recall range: {m['recall']['min']:.3f} / {m['recall']['median']:.3f} / {m['recall']['max']:.3f} (min/median/max)",
        f"- precision range: {m['precision']['min']:.3f} / {m['precision']['median']:.3f} / {m['precision']['max']:.3f}",
        f"- F1 range: {m['f1']['min']:.3f} / {m['f1']['median']:.3f} / {m['f1']['max']:.3f}",
        f"- Jaccard range: {m['jaccard']['min']:.3f} / {m['jaccard']['median']:.3f} / {m['jaccard']['max']:.3f}",
        "",
        "## Claim boundary",
        "",
        result["claim_boundary"],
        "",
        "The complete per-setting table is `settings.csv` and the machine-readable result is `result.json`.",
    ]
    (OUT / "RESULT.md").write_text("\n".join(lines) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    canonical_global = pd.read_csv(HERE / "canonical_2025_2026_ids.tsv", sep="\t", names=["year", "unique_trajectory_identifier"], dtype={"year": int, "unique_trajectory_identifier": str})
    if len(canonical_global) != 63 or canonical_global["unique_trajectory_identifier"].nunique() != 63:
        raise RuntimeError("Canonical scoring table must contain exactly 63 unique IDs")

    frames = [load_month(2025), load_month(2026)]
    all_april = pd.concat(frames, ignore_index=True)
    raw_ids = set(all_april["unique_trajectory_identifier"])
    missing = sorted(set(canonical_global["unique_trajectory_identifier"]) - raw_ids)
    if missing:
        raise RuntimeError(f"Canonical IDs absent after fixed manuscript quality/dedup filters: {missing}")

    diagnostic = all_april.loc[np.abs(circ_diff(all_april["sol_lon_deg"].to_numpy(float), CENTER[3])) <= SOL_HALF_WIDTH].reset_index(drop=True)
    diag_ids = set(diagnostic["unique_trajectory_identifier"])
    missing_diag = sorted(set(canonical_global["unique_trajectory_identifier"]) - diag_ids)
    if missing_diag:
        raise RuntimeError(f"Canonical IDs outside fixed diagnostic band: {missing_diag}")

    input_info = {
        "quality_sporadics_2025": int(len(frames[0])),
        "quality_sporadics_2026": int(len(frames[1])),
        "quality_sporadics_pooled": int(len(all_april)),
        "diagnostic_rows": int(len(diagnostic)),
    }

    print(f"Full April pooled rows: {len(all_april):,}; diagnostic rows: {len(diagnostic):,}", flush=True)
    print("Running full-April baseline fit", flush=True)
    full_baseline = evaluate_setting(all_april, canonical_global, dict(BASE), "full_april_baseline", "full_april_baseline")

    settings = build_settings()
    results: list[dict[str, Any]] = []
    for i, (sid, family, s) in enumerate(settings, 1):
        print(f"[{i:02d}/{len(settings)}] {sid}: {s}", flush=True)
        row = evaluate_setting(diagnostic, canonical_global, s, sid, family)
        results.append(row)
        print(
            f"  associated={row['associated_clusters']} union={row['associated_union_members']} overlap={row['canonical_overlap']} "
            f"P={row['precision']:.3f} R={row['recall']:.3f} F1={row['f1']:.3f}",
            flush=True,
        )

    result = summarize(results, full_baseline, input_info)
    pd.DataFrame(results).to_csv(OUT / "settings.csv", index=False)
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    (OUT / "input_manifest.json").write_text(json.dumps({
        "canonical_ids_sha256": sha256_file(HERE / "canonical_2025_2026_ids.tsv"),
        "protocol_sha256": sha256_file(HERE / "PROTOCOL.md"),
        "script_sha256": sha256_file(Path(__file__)),
        **input_info,
    }, indent=2, sort_keys=True) + "\n")
    print((OUT / "RESULT.md").read_text(), flush=True)
