#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import types
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import OAS
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
V6_STRUCTURAL_FAMILIES_SHA256 = "f76b8448f299ccf078fc5978c0890b9a084f131080db8d2136b5e6dba77edc7b"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
DSH_COMPARATOR_SHA256 = "85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a"
EXPECTED_FAMILY_COUNT = 226
EXPECTED_BASELINE_QUALIFIED = 95
EXPECTED_BASELINE_RECOVERY100 = 58
EXPECTED_BASELINE_MRR = 0.045531138942766655
EXPECTED_BASELINE_TOP100_PRECISION = 0.6884631112636006
EXPECTED_BASELINE_MACRO_F1 = 0.1736657194465356
WINDOW_HALF_WIDTH_DEG = 5.0
MIN_DIRECTION_NEGATIVES = 128
LOGISTIC_C = 1.0
LOGISTIC_MAX_ITER = 1000
LOGISTIC_TOL = 1e-10
RESPONSIBILITY_THRESHOLD = 0.5
MACRO_F1_GAIN_GATE = 0.08
TOP100_PRECISION_FLOOR = 0.65
LARGE_TOTAL_MIN = 100
LARGE_RECALL_MULTIPLIER = 1.5
LARGE_PRECISION_FLOOR = 0.85
DSH_BATCH_SIZE = 512


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v6-structural-families-json-gz", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--dsh-comparator", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_dsh_module(path: Path) -> types.ModuleType:
    digest = sha256_file(path)
    require(digest == DSH_COMPARATOR_SHA256, f"D_SH comparator hash changed: {digest}")
    module = load_module(path, "orbittrace_p2_exact_dsh_comparator")
    require(hasattr(module, "pairwise_dsh"), "pairwise_dsh missing")
    return module


def circular_mean_deg(values: list[float]) -> float:
    a = np.radians(np.asarray(values, dtype=np.float64))
    return float(np.degrees(np.arctan2(np.mean(np.sin(a)), np.mean(np.cos(a)))) % 360.0)


def pooled_centroid(rows: list[dict[str, Any]]) -> dict[str, float]:
    require(bool(rows), "empty centroid")
    return {
        "sol": circular_mean_deg([float(e["sol"]) for e in rows]),
        "sun_lon": circular_mean_deg([float(e["sun_lon"]) for e in rows]),
        "ecl_lat": float(np.median([float(e["ecl_lat"]) for e in rows])),
        "vg": float(np.median([float(e["vg"]) for e in rows])),
    }


def residual_matrix(events: list[dict[str, Any]], center: dict[str, float], base: types.ModuleType) -> np.ndarray:
    sol = np.asarray([float(e["sol"]) for e in events], dtype=np.float64)
    lon = np.asarray([float(e["sun_lon"]) for e in events], dtype=np.float64)
    lat = np.asarray([float(e["ecl_lat"]) for e in events], dtype=np.float64)
    vg = np.asarray([float(e["vg"]) for e in events], dtype=np.float64)
    d_sol = np.asarray([float(base.wrap180(float(x) - float(center["sol"]))) for x in sol], dtype=np.float64) / 4.0
    raw_lon = np.asarray([float(base.wrap180(float(x) - float(center["sun_lon"]))) for x in lon], dtype=np.float64)
    d_lon = raw_lon * np.cos(np.radians(0.5 * (lat + float(center["ecl_lat"])))) / 2.0
    d_lat = (lat - float(center["ecl_lat"])) / 2.0
    d_vg = (vg - float(center["vg"])) / 2.0
    out = np.column_stack((d_sol, d_lon, d_lat, d_vg))
    require(np.all(np.isfinite(out)), "non-finite observation residual")
    return out


def source_observation_model(
    rows: list[dict[str, Any]], base: types.ModuleType
) -> tuple[dict[str, float], np.ndarray, dict[str, Any]]:
    require(len(rows) >= 4, "source-year family has <4 seeds")
    center = pooled_centroid(rows)
    x = residual_matrix(rows, center, base)
    model = OAS(assume_centered=False).fit(x)
    cov = np.asarray(model.covariance_, dtype=np.float64)
    sign, logdet = np.linalg.slogdet(cov)
    if sign > 0 and np.isfinite(logdet):
        inverse = np.linalg.inv(cov)
        inverse_method = "inverse"
    else:
        inverse = np.linalg.pinv(cov)
        inverse_method = "moore_penrose_pseudoinverse"
    require(np.all(np.isfinite(inverse)), "non-finite covariance inverse")
    return center, inverse, {
        "seed_count": len(rows),
        "oas_shrinkage": float(model.shrinkage_),
        "covariance": cov.tolist(),
        "inverse_method": inverse_method,
    }


def mahalanobis_distance(
    events: list[dict[str, Any]],
    center: dict[str, float],
    inverse: np.ndarray,
    base: types.ModuleType,
) -> np.ndarray:
    x = residual_matrix(events, center, base)
    d2 = np.einsum("ij,jk,ik->i", x, inverse, x, optimize=True)
    d2 = np.maximum(d2, 0.0)
    out = np.sqrt(d2)
    require(np.all(np.isfinite(out)), "non-finite observation distance")
    return out


def exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    schema_lines = [line for line in text.splitlines() if line.startswith("# Unique trajectory;")]
    require(len(schema_lines) == 1, f"raw schema header not unique: {len(schema_lines)}")
    fields = [field.strip() for field in schema_lines[0][1:].split(";")]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f"raw schema field {name!r} not unique: {hits}")
        return hits[0]

    positions = {
        "id": exact("Unique trajectory"),
        "sol": exact("Sol lon"),
        "q": exact("q"),
        "e": exact("e"),
        "i": exact("i"),
        "peri": exact("peri"),
        "node": exact("node"),
    }
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == "Q"]
    require(len(q_upper) == 1 and q_upper[0] != positions["q"], "q/Q schema identity changed")
    return fields, positions


def parse_float_token(token: str) -> float | None:
    try:
        value = float(token.strip())
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def parse_target_excluded_orbits(
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: types.ModuleType,
) -> tuple[dict[str, dict[str, float]], list[dict[str, Any]]]:
    allowed = {year: {str(e["id"]) for e in scan_by_year[year]} for year in YEARS}
    orbit_by_id: dict[str, dict[str, float]] = {}
    audits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        year = int(key[:4])
        text = support.dd.get_monthly_file_content_by_date(key)
        fields, positions = exact_header_positions(text)
        max_index = max(positions.values())
        admitted = valid = duplicate = short = 0
        for raw in text.splitlines():
            if not raw.strip() or raw.startswith("#"):
                continue
            tokens = raw.split(";")
            if len(tokens) <= max_index:
                short += 1
                continue
            event_id = str(tokens[positions["id"]]).strip()
            sol = parse_float_token(tokens[positions["sol"]])
            if not event_id or sol is None or not (0.0 <= sol <= 360.0):
                continue
            if float(support.BLIND_LOW) <= sol <= float(support.BLIND_HIGH):
                continue
            if event_id not in allowed[year]:
                continue
            admitted += 1
            values = {
                name: parse_float_token(tokens[index])
                for name, index in positions.items()
                if name not in {"id", "sol"}
            }
            if any(value is None for value in values.values()):
                continue
            q = float(values["q"])
            eccentricity = float(values["e"])
            inc = float(values["i"])
            peri = float(values["peri"])
            node = float(values["node"])
            if not (
                q > 0.0
                and 0.0 <= eccentricity < 2.0
                and 0.0 <= inc <= 180.0
                and 0.0 <= peri < 360.0
                and 0.0 <= node < 360.0
            ):
                continue
            if event_id in seen:
                duplicate += 1
                continue
            seen.add(event_id)
            valid += 1
            orbit_by_id[event_id] = {
                "q": q,
                "e": eccentricity,
                "i": inc,
                "peri": peri,
                "node": node,
            }
        audits.append({
            "key": key,
            "raw_header_field_count": len(fields),
            "target_excluded_scan_ids": admitted,
            "valid_orbits": valid,
            "duplicate_ids_removed": duplicate,
            "short_rows_skipped": short,
            "q_field_index": positions["q"],
            "orbit_columns": {name: fields[index] for name, index in positions.items() if name not in {"id", "sol"}},
            "trajectory_dataframe_parser_invoked": False,
            "label_column_accessed": False,
            "target_region_orbit_decoded": False,
        })
    require(set(orbit_by_id).issubset(set().union(*allowed.values())), "orbit parser emitted non-scan event")
    return orbit_by_id, audits


def min_exact_dsh_to_source(
    event_ids: list[str],
    source_seed_ids: list[str],
    orbit_by_id: dict[str, dict[str, float]],
    dsh: types.ModuleType,
) -> np.ndarray:
    require(bool(source_seed_ids), "empty source orbit set")
    require(all(eid in orbit_by_id for eid in source_seed_ids), "source seed missing valid orbit")
    require(all(eid in orbit_by_id for eid in event_ids), "candidate event missing valid orbit")
    source = [orbit_by_id[eid] for eid in source_seed_ids]
    result = np.empty(len(event_ids), dtype=np.float64)
    for start in range(0, len(event_ids), DSH_BATCH_SIZE):
        ids = event_ids[start:start + DSH_BATCH_SIZE]
        candidate = [orbit_by_id[eid] for eid in ids]
        combined = candidate + source
        matrix = dsh.pairwise_dsh(
            [o["q"] for o in combined],
            [o["e"] for o in combined],
            [o["i"] for o in combined],
            [o["peri"] for o in combined],
            [o["node"] for o in combined],
        )
        b = len(candidate)
        cross = np.asarray(matrix[:b, b:], dtype=np.float64)
        require(cross.shape == (b, len(source)), "D_SH cross slice shape changed")
        result[start:start + b] = np.min(cross, axis=1)
    require(np.all(np.isfinite(result)), "non-finite D_SH feature")
    return result


def wrapped_window_mask(
    events: list[dict[str, Any]], target_centroid_sol: float, base: types.ModuleType
) -> np.ndarray:
    delta = np.asarray(
        [abs(float(base.wrap180(float(e["sol"]) - float(target_centroid_sol)))) for e in events],
        dtype=np.float64,
    )
    return delta <= WINDOW_HALF_WIDTH_DEG + 1e-15


def label_totals(hidden_labels: dict[str, str], mult: types.ModuleType) -> dict[str, int]:
    eligible = mult.eligible_labels(hidden_labels)
    return {label: int(sum(per_year.values())) for label, per_year in eligible.items()}


def large_summary(metrics: dict[str, Any], totals: dict[str, int], label_subset: set[str]) -> dict[str, Any]:
    rows = {str(r["label"]): r for r in metrics["per_label"]}
    vals = []
    for label in sorted(label_subset):
        row = rows[label]
        vals.append({
            "label": label,
            "total": totals[label],
            "qualified": bool(row.get("qualified", False)),
            "precision": float(row.get("precision", 0.0)),
            "recall": float(row.get("recall", 0.0)),
            "f1": float(row.get("f1", 0.0)),
        })
    return {
        "labels": len(vals),
        "mean_precision": float(np.mean([x["precision"] for x in vals])) if vals else 0.0,
        "mean_recall": float(np.mean([x["recall"] for x in vals])) if vals else 0.0,
        "mean_f1": float(np.mean([x["f1"] for x in vals])) if vals else 0.0,
        "qualified": sum(x["qualified"] for x in vals),
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_file(args.v6_structural_families_json_gz) == V6_STRUCTURAL_FAMILIES_SHA256, "v6 structural-family artifact mismatch")
    require(sha256_file(args.v8_result_json) == V8_RESULT_SHA256, "promoted-v8 result artifact mismatch")
    dsh = load_dsh_module(args.dsh_comparator)

    old = load_module(args.base_runner, "orbittrace_p2_base_runner")
    v8 = load_module(args.v8_runner, "orbittrace_p2_exact_v8_runner")
    support = old.load_support_module(args.support_source_parts)
    source_args = types.SimpleNamespace(
        candidate_payload=args.candidate_payload,
        baseline_payload=args.baseline_payload,
        scorer_parts=args.scorer_parts,
    )
    _, base, _ = support.load_sources(source_args)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")

    scan_by_year, _, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
    orbit_by_id, orbit_audits = parse_target_excluded_orbits(scan_by_year, support)

    family_rows = json.loads(gzip.decompress(args.v6_structural_families_json_gz.read_bytes()).decode())
    v8_result = json.loads(args.v8_result_json.read_text())
    require(v8_result.get("verdict") == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "promoted v8 result did not pass")
    require(int(v8_result.get("family_count", -1)) == EXPECTED_FAMILY_COUNT, "promoted v8 family count changed")
    baseline = v8_result["metrics"]["multiplicity"]
    require(int(baseline["qualified_matches"]) == EXPECTED_BASELINE_QUALIFIED, "promoted v8 qualified identity mismatch")
    require(int(baseline["recovered_at_100"]) == EXPECTED_BASELINE_RECOVERY100, "promoted v8 recovery identity mismatch")
    require(abs(float(baseline["mrr"]) - EXPECTED_BASELINE_MRR) <= 1e-15, "promoted v8 MRR identity mismatch")
    require(abs(float(baseline["top100_dominant_precision"]) - EXPECTED_BASELINE_TOP100_PRECISION) <= 1e-12, "promoted v8 precision identity mismatch")
    require(abs(float(baseline["macro_f1"]) - EXPECTED_BASELINE_MACRO_F1) <= 1e-12, "promoted v8 macro-F1 identity mismatch")
    require(len(family_rows) == EXPECTED_FAMILY_COUNT, "structural family universe changed")

    event_lookup_by_year = {
        year: {str(e["id"]): e for e in scan_by_year[year]}
        for year in YEARS
    }

    for family in family_rows:
        pooled = {}
        for year in YEARS:
            ids = [str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year]
            rows = [event_lookup_by_year[year][eid] for eid in ids]
            require(len(rows) >= 4, f"family {family['family_id']} has <4 exact v8 seeds in {year}")
            pooled[str(year)] = v8.pooled_centroid(rows, support)
        family["centroids"] = pooled

    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = MONTH_KEYS
    v8.mult.TOP_K = 100
    v8_runtime = v8.mult.load_frozen_runtime()
    scored_v8, v8_scoring_summary = v8.mult.score_families(family_rows, scan_by_year, v8_runtime, base)
    v8_order = v8.mult.rank_scored(scored_v8, "multiplicity")
    by_id = {str(f["family_id"]): f for f in family_rows}
    require(len(v8_order) == EXPECTED_FAMILY_COUNT and set(v8_order) == set(by_id), "exact v8 ranking universe mismatch")
    families = [by_id[fid] for fid in v8_order]
    family_rank = {str(fid): index for index, fid in enumerate(v8_order)}
    global_seed_ids = set().union(*(set(map(str, f["event_ids"])) for f in families))
    require(all(seed_id in orbit_by_id for seed_id in global_seed_ids), "P2 input-ineligible: exact v8 seed missing valid orbit")

    valid_events_by_year = {
        year: [e for e in scan_by_year[year] if str(e["id"]) in orbit_by_id]
        for year in YEARS
    }
    valid_nonseed_by_year = {
        year: [e for e in valid_events_by_year[year] if str(e["id"]) not in global_seed_ids]
        for year in YEARS
    }

    directions: list[dict[str, Any]] = []
    training_x: list[np.ndarray] = []
    training_y: list[np.ndarray] = []
    training_w: list[np.ndarray] = []
    direction_audits: list[dict[str, Any]] = []

    for family_index, family in enumerate(families):
        family_id = str(family["family_id"])
        ids_by_year = {
            year: sorted(str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year)
            for year in YEARS
        }
        rows_by_year = {
            year: [event_lookup_by_year[year][eid] for eid in ids_by_year[year]]
            for year in YEARS
        }
        for source_year, target_year in ((2022, 2023), (2023, 2022)):
            source_ids = ids_by_year[source_year]
            target_ids = ids_by_year[target_year]
            require(len(source_ids) >= 4 and len(target_ids) >= 4, f"family {family_id} invalid cross-year seed support")
            require(all(eid in orbit_by_id for eid in source_ids + target_ids), f"family {family_id} seed orbit missing")

            center, inverse, obs_audit = source_observation_model(rows_by_year[source_year], base)
            target_center = pooled_centroid(rows_by_year[target_year])
            target_nonseed_events = valid_nonseed_by_year[target_year]
            mask = wrapped_window_mask(target_nonseed_events, target_center["sol"], base)
            negative_events = [event for event, keep in zip(target_nonseed_events, mask.tolist()) if keep]
            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")
            positive_events = rows_by_year[target_year]

            positive_obs = mahalanobis_distance(positive_events, center, inverse, base)
            positive_orb = min_exact_dsh_to_source(target_ids, source_ids, orbit_by_id, dsh)
            negative_ids = [str(e["id"]) for e in negative_events]
            negative_obs = mahalanobis_distance(negative_events, center, inverse, base)
            negative_orb = min_exact_dsh_to_source(negative_ids, source_ids, orbit_by_id, dsh)

            x_pos = np.column_stack((positive_obs, positive_orb))
            x_neg = np.column_stack((negative_obs, negative_orb))
            training_x.extend((x_pos, x_neg))
            training_y.extend((
                np.ones(len(x_pos), dtype=np.int8),
                np.zeros(len(x_neg), dtype=np.int8),
            ))
            training_w.extend((
                np.full(len(x_pos), 0.5 / len(x_pos), dtype=np.float64),
                np.full(len(x_neg), 0.5 / len(x_neg), dtype=np.float64),
            ))
            directions.append({
                "family_index": family_index,
                "family_id": family_id,
                "source_year": source_year,
                "target_year": target_year,
                "source_seed_ids": source_ids,
                "target_seed_ids": target_ids,
                "negative_event_ids": negative_ids,
                "negative_features": x_neg,
            })
            direction_audits.append({
                "family_id": family_id,
                "source_year": source_year,
                "target_year": target_year,
                "source_seed_count": len(source_ids),
                "positive_count": len(x_pos),
                "negative_count": len(x_neg),
                "target_centroid_sol": float(target_center["sol"]),
                **obs_audit,
            })
        print(f"P2 feature construction family {family_index + 1}/{len(families)}", flush=True)

    X = np.vstack(training_x).astype(np.float64, copy=False)
    y = np.concatenate(training_y).astype(np.int8, copy=False)
    sample_weight = np.concatenate(training_w).astype(np.float64, copy=False)
    require(X.shape[1] == 2 and len(X) == len(y) == len(sample_weight), "training matrix shape changed")
    require(np.all(np.isfinite(X)) and np.all(np.isfinite(sample_weight)), "non-finite training data")
    require(abs(float(np.sum(sample_weight[y == 1])) - 0.5 * len(directions)) <= 1e-8, "positive family-direction weight changed")
    require(abs(float(np.sum(sample_weight[y == 0])) - 0.5 * len(directions)) <= 1e-8, "negative family-direction weight changed")

    scaler = StandardScaler()
    scaler.fit(X, sample_weight=sample_weight)
    X_scaled = scaler.transform(X)
    classifier = LogisticRegression(
        penalty="l2",
        C=LOGISTIC_C,
        solver="lbfgs",
        max_iter=LOGISTIC_MAX_ITER,
        tol=LOGISTIC_TOL,
        fit_intercept=True,
        class_weight=None,
        random_state=None,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        classifier.fit(X_scaled, y, sample_weight=sample_weight)
    convergence = [w for w in caught if issubclass(w.category, ConvergenceWarning)]
    require(not convergence, f"logistic convergence warning: {[str(w.message) for w in convergence]}")
    require(int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER, "logistic solver hit max_iter")

    model_payload = {
        "feature_order": ["d_obs", "d_orb"],
        "scaler_mean": np.asarray(scaler.mean_, dtype=np.float64).tolist(),
        "scaler_scale": np.asarray(scaler.scale_, dtype=np.float64).tolist(),
        "scaler_var": np.asarray(scaler.var_, dtype=np.float64).tolist(),
        "logistic_coef": np.asarray(classifier.coef_, dtype=np.float64).tolist(),
        "logistic_intercept": np.asarray(classifier.intercept_, dtype=np.float64).tolist(),
        "logistic_n_iter": np.asarray(classifier.n_iter_, dtype=np.int64).tolist(),
        "settings": {
            "penalty": "l2",
            "C": LOGISTIC_C,
            "solver": "lbfgs",
            "max_iter": LOGISTIC_MAX_ITER,
            "tol": LOGISTIC_TOL,
            "fit_intercept": True,
            "class_weight": None,
            "family_direction_positive_total_weight": 0.5,
            "family_direction_negative_total_weight": 0.5,
            "window_half_width_deg": WINDOW_HALF_WIDTH_DEG,
        },
    }
    model_sha = canonical_sha(model_payload)
    (args.output / "p2_model_pretruth.json").write_text(json.dumps(model_payload, indent=2, sort_keys=True) + "\n")
    (args.output / "p2_model_pretruth.sha256").write_text(model_sha + "\n")

    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
    for index, direction in enumerate(directions, start=1):
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
        ids = list(direction["negative_event_ids"])
        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd in zip(ids, probabilities.tolist(), odds.tolist()):
            proposals_by_event[event_id].append({
                "family_index": int(direction["family_index"]),
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "probability": float(probability),
                "odds": float(odd),
            })
        if index % 50 == 0 or index == len(directions):
            print(f"P2 scoring direction {index}/{len(directions)}", flush=True)

    assignments: dict[str, dict[str, Any]] = {}
    conflicted = 0
    max_responsibilities: list[float] = []
    for event_id, proposals in proposals_by_event.items():
        require(event_id not in global_seed_ids, "seed entered P2 competition")
        if len(proposals) > 1:
            conflicted += 1
        denom = 1.0 + float(sum(p["odds"] for p in proposals))
        ranked = sorted(
            proposals,
            key=lambda p: (
                -float(p["odds"]) / denom,
                family_rank[str(p["family_id"])],
                str(p["family_id"]),
            ),
        )
        best = dict(ranked[0])
        responsibility = float(best["odds"] / denom)
        if responsibility <= RESPONSIBILITY_THRESHOLD:
            continue
        best["responsibility"] = responsibility
        assignments[event_id] = best
        max_responsibilities.append(responsibility)

    additions_by_family: dict[int, list[str]] = defaultdict(list)
    for event_id, rec in assignments.items():
        additions_by_family[int(rec["family_index"])].append(event_id)

    expanded: list[dict[str, Any]] = []
    for index, family in enumerate(families):
        out = json.loads(json.dumps(family))
        seeds = set(map(str, family["event_ids"]))
        additions = sorted(set(additions_by_family.get(index, [])) - global_seed_ids)
        out["p2_added_event_ids"] = additions
        out["p2_added_event_count"] = len(additions)
        out["event_ids"] = sorted(seeds | set(additions))
        out["event_count"] = len(out["event_ids"])
        expanded.append(out)

    frozen_payload = json.dumps(expanded, sort_keys=True, separators=(",", ":")).encode("utf-8")
    membership_sha = hashlib.sha256(frozen_payload).hexdigest()
    (args.output / "p2_membership_pretruth.sha256").write_text(membership_sha + "\n")
    (args.output / "p2_expanded_families.json.gz").write_bytes(gzip.compress(frozen_payload))

    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
    p2_full = v8.mult.evaluate_order(hidden_labels, expanded, v8_order)
    exact_baseline = {
        "eligible_labels": baseline["eligible_labels"],
        "qualified_matches": baseline["qualified_matches"],
        "recovered_at_100": baseline["recovered_at_100"],
        "recovered_at_500": baseline["recovered_at_500"],
        "mrr": baseline["mrr"],
        "median_rank": baseline["median_rank"],
        "macro_f1": baseline["macro_f1"],
        "top100_dominant_precision": baseline["top100_dominant_precision"],
    }
    baseline_reproduced = all(
        (abs(float(baseline_full[k]) - float(value)) <= 1e-12
         if isinstance(value, (int, float)) and value is not None
         else baseline_full[k] == value)
        for k, value in exact_baseline.items()
    )

    totals = label_totals(hidden_labels, v8.mult)
    baseline_large_labels = {
        str(row["label"])
        for row in baseline_full["per_label"]
        if bool(row.get("qualified", False)) and totals.get(str(row["label"]), 0) >= LARGE_TOTAL_MIN
    }
    require(bool(baseline_large_labels), "no exact-v8 large-shower subset")
    baseline_large = large_summary(baseline_full, totals, baseline_large_labels)
    p2_large = large_summary(p2_full, totals, baseline_large_labels)

    gates = {
        "exact_v8_226_family_order": len(expanded) == EXPECTED_FAMILY_COUNT
        and [str(f["family_id"]) for f in expanded] == [str(f["family_id"]) for f in families],
        "exact_v8_seed_members_preserved": all(
            set(map(str, family["event_ids"])).issubset(set(map(str, out["event_ids"])))
            for family, out in zip(families, expanded)
        ),
        "v8_baseline_reproduced": bool(baseline_reproduced),
        "exact_dsh_source_identity": sha256_file(args.dsh_comparator) == DSH_COMPARATOR_SHA256,
        "model_frozen_before_truth_evaluation": bool(model_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,
        "expansion_nonvacuous": len(assignments) > 0,
        "qualified_matches_no_regression": int(p2_full["qualified_matches"]) >= EXPECTED_BASELINE_QUALIFIED,
        "recovery_at_100_no_regression": int(p2_full["recovered_at_100"]) >= EXPECTED_BASELINE_RECOVERY100,
        "top100_dominant_precision_at_least_065": float(p2_full["top100_dominant_precision"]) >= TOP100_PRECISION_FLOOR,
        "macro_f1_gain_at_least_008": float(p2_full["macro_f1"]) >= EXPECTED_BASELINE_MACRO_F1 + MACRO_F1_GAIN_GATE,
        "large_shower_mean_recall_at_least_15x_v8": float(p2_large["mean_recall"]) >= LARGE_RECALL_MULTIPLIER * float(baseline_large["mean_recall"]),
        "large_shower_mean_precision_at_least_085": float(p2_large["mean_precision"]) >= LARGE_PRECISION_FLOOR,
    }
    verdict = (
        "PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO"
    )

    result = {
        "verdict": verdict,
        "classification": "cross-year self-supervised two-view membership discriminator; immutable promoted-v8 cores and rank",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [float(support.BLIND_LOW), float(support.BLIND_HIGH)],
            "v8_source_commit": V8_SOURCE_COMMIT,
            "family_count": EXPECTED_FAMILY_COUNT,
            "features": ["cross-year source-seed OAS Mahalanobis observation distance", "minimum exact D_SH to source-year immutable seed"],
            "window_half_width_deg": WINDOW_HALF_WIDTH_DEG,
            "negative_minimum_per_direction": MIN_DIRECTION_NEGATIVES,
            "family_direction_class_total_weights": {"positive": 0.5, "negative": 0.5},
            "scaler": "StandardScaler fit with frozen sample weights",
            "classifier": "LogisticRegression L2 C=1.0 lbfgs max_iter=1000 tol=1e-10",
            "background_odds_weight": 1.0,
            "responsibility_threshold": RESPONSIBILITY_THRESHOLD,
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact promoted-v8 multiplicity order",
            "parameter_search": False,
        },
        "sources": sources,
        "model_pretruth_sha256": model_sha,
        "membership_pretruth_sha256": membership_sha,
        "baseline_v8": {k: v for k, v in baseline_full.items() if k != "per_label"},
        "p2": {k: v for k, v in p2_full.items() if k != "per_label"},
        "baseline_large_shower": baseline_large,
        "p2_large_shower": p2_large,
        "gates": gates,
        "diagnostics": {
            "training_rows": int(len(X)),
            "positive_training_rows": int(np.sum(y == 1)),
            "negative_training_rows": int(np.sum(y == 0)),
            "family_directions": len(directions),
            "valid_orbit_events": len(orbit_by_id),
            "valid_nonseed_events_by_year": {str(year): len(valid_nonseed_by_year[year]) for year in YEARS},
            "proposal_events": len(proposals_by_event),
            "conflicted_proposal_events": conflicted,
            "assigned_nonseed_events": len(assignments),
            "families_gaining_members": sum(bool(additions_by_family.get(index)) for index in range(len(families))),
            "responsibility_median": float(np.median(max_responsibilities)) if max_responsibilities else None,
            "responsibility_min": float(min(max_responsibilities)) if max_responsibilities else None,
            "responsibility_max": float(max(max_responsibilities)) if max_responsibilities else None,
            "v8_scoring_summary": v8_scoring_summary,
        },
        "direction_audits": direction_audits,
        "orbit_audits": orbit_audits,
        "claim_boundary": "Target-excluded development only. A pass requires separately frozen matched Sugar/HDBSCAN comparison and no-retuning external validation before any target-containing OrbitTrace deployment.",
    }
    (args.output / "crossyear_two_view_membership_p2_development.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").write_text(
        "# OrbitTrace cross-year two-view membership P2 development\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- v8 -> P2 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\n"
        f"- v8 -> P2 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\n"
        f"- v8 -> P2 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\n"
        f"- v8 -> P2 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p2_large['mean_recall']:.6f}**\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p2_large['mean_precision']:.6f}**\n"
        f"- assigned nonseed events: **{len(assignments):,}**; conflicted proposal events: **{conflicted:,}**\n"
        f"- model SHA-256: `{model_sha}`\n"
        f"- membership SHA-256: `{membership_sha}`\n\n"
        "No OrbitTrace target information or target-region event was used.\n"
    )
    print((args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").read_text(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
