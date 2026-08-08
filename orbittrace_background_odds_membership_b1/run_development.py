#!/usr/bin/env python3
"""Cross-year background-odds membership over the immutable OrbitTrace v8 discovery core."""
from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from gmn_python_api import data_directory as dd
from sklearn.covariance import LedoitWolf

import literature_comparators as dshcmp
from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1
from orbittrace_cross_year_conformal_density_expansion_v3 import run_development as v3
from orbittrace_cross_year_trajectory_conformal_expansion_v4 import run_development as v4

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
ACTIVITY_PADDING_DEG = 6.0
DENSITY_CEILING = 1.5
TRAJECTORY_CEILING = 1.5
POSTERIOR_LOG_ODDS_CUTOFF = 0.0
FEATURES = ("log1p_density_d2", "log1p_trajectory_residual", "log1p_median_D_SH")
EXPECTED_ORBIT_EVENT_COUNT = 738682


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def raw_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
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
    require(positions == {"id": 0, "sol": 5, "q": 37, "e": 25, "i": 27, "peri": 29, "node": 31},
            f"unexpected raw schema positions: {positions}")
    require(len(fields) == 86, f"unexpected raw schema field count: {len(fields)}")
    return fields, positions


def parse_target_excluded_orbits(
    scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[dict[int, dict[str, tuple[float, float, float, float, float]]], list[dict[str, Any]]]:
    allowed = {year: {str(e["id"]) for e in scan_by_year[year]} for year in YEARS}
    out: dict[int, dict[str, tuple[float, float, float, float, float]]] = {year: {} for year in YEARS}
    audits: list[dict[str, Any]] = []
    for key in MONTH_KEYS:
        year = int(key[:4])
        text = dd.get_monthly_file_content_by_date(key)
        fields, pos = raw_header_positions(text)
        month_allowed = {eid for eid in allowed[year] if eid.startswith(key.replace("-", ""))}
        found: dict[str, tuple[float, float, float, float, float]] = {}
        short_rows = 0
        for raw in text.splitlines():
            if not raw or raw.startswith("#"):
                continue
            parts = [x.strip() for x in raw.split(";")]
            if len(parts) <= max(pos.values()):
                short_rows += 1
                continue
            eid = parts[pos["id"]]
            if eid not in month_allowed:
                continue
            sol = float(parts[pos["sol"]]) % 360.0
            # The geometry parser must already have removed the target interval. Refuse to
            # decode any orbital value if an allowed scan ID violates that firewall.
            require(not (20.0 <= sol <= 55.0), f"target-region scan ID reached orbit parser: {eid}")
            values = tuple(float(parts[pos[name]]) for name in ("q", "e", "i", "peri", "node"))
            require(all(math.isfinite(x) for x in values), f"non-finite orbit for {eid}")
            require(eid not in found, f"duplicate orbit ID in {key}: {eid}")
            found[eid] = values  # type: ignore[assignment]
        missing = month_allowed - set(found)
        require(not missing, f"missing target-excluded orbit rows in {key}: {len(missing)}")
        out[year].update(found)
        audits.append({
            "key": key,
            "raw_header_field_count": len(fields),
            "target_excluded_scan_ids": len(month_allowed),
            "valid_orbits": len(found),
            "short_rows_skipped": short_rows,
            "duplicate_ids_removed": 0,
            "label_column_accessed": False,
            "trajectory_dataframe_parser_invoked": False,
            "target_region_orbit_decoded": False,
            "orbit_columns": {name: name for name in ("q", "e", "i", "peri", "node")},
        })
        print(f"B1_ORBIT_MONTH_DONE key={key} valid_orbits={len(found)}", flush=True)
    total = sum(len(x) for x in out.values())
    require(total == sum(len(scan_by_year[y]) for y in YEARS), "orbit/scan event universe mismatch")
    require(total == EXPECTED_ORBIT_EVENT_COUNT, f"unexpected frozen orbit event count: {total}")
    return out, audits


def cross_dsh(
    left: list[tuple[float, float, float, float, float]],
    right: list[tuple[float, float, float, float, float]],
) -> np.ndarray:
    if not left or not right:
        return np.empty((len(left), len(right)), dtype=np.float64)
    la = np.asarray(left, dtype=np.float64)
    ra = np.asarray(right, dtype=np.float64)
    q1, e1 = la[:, 0][:, None], la[:, 1][:, None]
    q2, e2 = ra[:, 0][None, :], ra[:, 1][None, :]
    i1, i2 = np.radians(la[:, 2])[:, None], np.radians(ra[:, 2])[None, :]
    p1, p2 = np.radians(la[:, 3])[:, None], np.radians(ra[:, 3])[None, :]
    n1, n2 = np.radians(la[:, 4])[:, None], np.radians(ra[:, 4])[None, :]
    node_delta = dshcmp.wrap_pi(n2 - n1)
    cos_i = np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(node_delta)
    mutual_i = np.arccos(np.clip(cos_i, -1.0, 1.0))
    denominator = np.cos(0.5 * mutual_i)
    numerator = np.cos(0.5 * (i1 + i2)) * np.sin(0.5 * node_delta)
    ratio = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=np.abs(denominator) > 1e-15)
    peri_delta = dshcmp.wrap_pi(p2 - p1 + 2.0 * np.arcsin(np.clip(ratio, -1.0, 1.0)))
    plane = 2.0 * np.sin(0.5 * mutual_i)
    peri_term = 0.5 * (e1 + e2) * 2.0 * np.sin(0.5 * peri_delta)
    squared = (q1 - q2) ** 2 + (e1 - e2) ** 2 + plane ** 2 + peri_term ** 2
    result = np.sqrt(np.maximum(squared, 0.0))
    require(np.all(np.isfinite(result)), "non-finite rectangular D_SH")
    return result


def self_test_cross_dsh() -> None:
    sample = [
        (0.31, 0.81, 7.0, 112.0, 44.0),
        (0.33, 0.79, 8.0, 115.0, 45.0),
        (0.77, 0.42, 31.0, 271.0, 180.0),
        (0.55, 0.61, 16.0, 210.0, 92.0),
        (0.24, 0.88, 4.0, 101.0, 40.0),
    ]
    q, e, inc, peri, node = zip(*sample)
    square = dshcmp.pairwise_dsh(q, e, inc, peri, node)
    rectangular = cross_dsh(sample[:2], sample[2:])
    require(np.allclose(rectangular, square[:2, 2:], rtol=0.0, atol=2e-15), "rectangular D_SH self-test failed")


def orbit_loo_median(orbits: list[tuple[float, float, float, float, float]]) -> np.ndarray:
    q, e, inc, peri, node = zip(*orbits)
    d = dshcmp.pairwise_dsh(q, e, inc, peri, node)
    d = d.copy()
    np.fill_diagonal(d, np.nan)
    return np.nanmedian(d, axis=1)


def candidate_orbit_median(
    ids: list[str],
    orbit_lookup: dict[str, tuple[float, float, float, float, float]],
    source_orbits: list[tuple[float, float, float, float, float]],
) -> np.ndarray:
    if not ids:
        return np.empty(0, dtype=np.float64)
    out = np.empty(len(ids), dtype=np.float64)
    for lo in range(0, len(ids), 1024):
        chunk = ids[lo:lo + 1024]
        values = [orbit_lookup[eid] for eid in chunk]
        out[lo:lo + len(chunk)] = np.median(cross_dsh(values, source_orbits), axis=1)
    return out


def feature_matrix(d2: np.ndarray, residual: np.ndarray, orbit_median: np.ndarray) -> np.ndarray:
    x = np.column_stack((d2, residual, orbit_median)).astype(np.float64, copy=False)
    require(x.ndim == 2 and x.shape[1] == 3 and np.all(np.isfinite(x)), "invalid B1 feature matrix")
    require(np.all(x >= 0.0), "negative B1 distance feature")
    return np.log1p(x)


def fit_gaussian(x: np.ndarray) -> dict[str, np.ndarray | float]:
    require(len(x) >= 4 and x.shape[1] == 3, f"insufficient Gaussian training sample: {x.shape}")
    model = LedoitWolf(assume_centered=False).fit(x)
    covariance = np.asarray(model.covariance_, dtype=np.float64)
    precision = np.asarray(model.precision_, dtype=np.float64)
    sign, logdet = np.linalg.slogdet(covariance)
    require(sign > 0 and math.isfinite(float(logdet)), "non-positive Ledoit-Wolf covariance")
    return {"mean": np.asarray(model.location_, dtype=np.float64), "precision": precision, "logdet": float(logdet)}


def gaussian_logpdf(model: dict[str, np.ndarray | float], x: np.ndarray) -> np.ndarray:
    mean = np.asarray(model["mean"], dtype=np.float64)
    precision = np.asarray(model["precision"], dtype=np.float64)
    delta = x - mean[None, :]
    quad = np.einsum("ij,jk,ik->i", delta, precision, delta)
    return -0.5 * (3.0 * math.log(2.0 * math.pi) + float(model["logdet"]) + quad)


def screened_features(
    events: list[dict[str, Any]],
    source_events: list[dict[str, Any]],
    trajectory_model: dict[str, float],
    orbit_lookup: dict[str, tuple[float, float, float, float, float]],
    source_orbits: list[tuple[float, float, float, float, float]],
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not events:
        return [], np.empty((0, 3)), np.empty(0), np.empty(0), np.empty(0)
    d1, d2 = v3.target_d1_d2(events, source_events)
    residual = v4.trajectory_residuals(trajectory_model, events)
    keep = (d2 <= DENSITY_CEILING + 1e-12) & (residual <= TRAJECTORY_CEILING + 1e-12)
    kept_events = [event for event, k in zip(events, keep.tolist()) if k and str(event["id"]) in orbit_lookup]
    if not kept_events:
        return [], np.empty((0, 3)), np.empty(0), np.empty(0), np.empty(0)
    kept_ids = [str(event["id"]) for event in kept_events]
    positions = [i for i, (event, k) in enumerate(zip(events, keep.tolist())) if k and str(event["id"]) in orbit_lookup]
    kd2 = np.asarray([d2[i] for i in positions], dtype=np.float64)
    kres = np.asarray([residual[i] for i in positions], dtype=np.float64)
    kom = candidate_orbit_median(kept_ids, orbit_lookup, source_orbits)
    return kept_events, feature_matrix(kd2, kres, kom), kd2, kres, kom


def crossfit_expand_background_odds(
    families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    self_test_cross_dsh()
    orbits, orbit_audits = parse_target_excluded_orbits(scan_by_year)
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in YEARS}
    diagnostics: dict[str, Any] = {
        "architecture": "cross-year stream-vs-local-field background-odds membership",
        "features": list(FEATURES),
        "stream_density_model": "3D Gaussian with Ledoit-Wolf covariance on other-year original-seed LOO features",
        "background_density_model": "3D Gaussian with Ledoit-Wolf covariance on same-source-year screened non-family events",
        "prior_odds": "n_original_orbit_valid_source_seeds / n_screened_source_background_events",
        "acceptance_rule": "transferred log posterior odds > 0 under observed-seed prior",
        "posterior_log_odds_cutoff": POSTERIOR_LOG_ODDS_CUTOFF,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "density_ceiling": DENSITY_CEILING,
        "trajectory_ceiling": TRAJECTORY_CEILING,
        "orbital_statistic": "median Southworth-Hawkins D_SH to all original other-year orbit-valid seeds",
        "new_members_by_year": {},
        "candidate_pairs_after_screens_by_year": {},
        "positive_odds_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "families_skipped_insufficient_background_by_year": {},
        "assigned_log_odds_median_by_year": {},
        "assigned_log_odds_min_by_year": {},
        "source_background_count_median_by_year": {},
        "source_seed_count_median_by_year": {},
        "original_seed_events_by_year": {},
        "orbit_event_count": sum(len(x) for x in orbits.values()),
        "orbit_parse_audits": orbit_audits,
        "label_access_during_membership": False,
        "new_members_never_reused_as_support": True,
        "other_year_original_seed_support_only": True,
        "other_year_support_only": True,
        "exclusive_assignment": True,
        "exclusive_assignment_rule": "largest transferred log posterior odds; then smaller orbital median; then smaller d2; then stable family id",
        "parameter_search": False,
        "posterior_cutoff_search": False,
        "covariance_model_search": False,
        "feature_weight_search": False,
        "orbit_threshold_search": False,
    }

    for target_year in YEARS:
        source_year = YEARS[1] if target_year == YEARS[0] else YEARS[0]
        target_events = scan_by_year[target_year]
        source_all = scan_by_year[source_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events], dtype=np.float64)
        source_sol = np.asarray([float(e["sol"]) % 360.0 for e in source_all], dtype=np.float64)
        all_target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = all_target_seed_owner.get(eid)
                require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                all_target_seed_owner[eid] = fid

        best: dict[str, tuple[float, float, float, str]] = {}
        candidate_pairs = positive_pairs = skipped_background = 0
        source_bg_counts: list[int] = []
        source_seed_counts: list[int] = []

        for family_index, family in enumerate(families, start=1):
            fid = str(family["family_id"])
            source_ids_all = sorted(original[fid] & set(event_lookup[source_year]))
            source_id_set = set(source_ids_all)
            source_ids = [eid for eid in source_ids_all if eid in orbits[source_year]]
            require(len(source_ids) >= 4, f"family {fid} has fewer than four orbit-valid other-year original seeds")
            source_events = [event_lookup[source_year][eid] for eid in source_ids]
            source_orbits = [orbits[source_year][eid] for eid in source_ids]
            source_seed_counts.append(len(source_events))

            trajectory = v4.fit_trajectory(source_events)
            stream_d2 = v3.source_leave_one_out_d2(source_events)
            stream_residual = v4.loo_residuals(source_events)
            stream_orbit = orbit_loo_median(source_orbits)
            x_stream = feature_matrix(stream_d2, stream_residual, stream_orbit)

            src_mask = v4.in_activity_arc(source_sol, [float(e["sol"]) for e in source_events])
            source_candidates = [source_all[int(i)] for i in np.flatnonzero(src_mask)]
            source_candidates = [e for e in source_candidates if str(e["id"]) not in source_id_set]
            bg_events, x_bg, _bd2, _bres, _borb = screened_features(
                source_candidates, source_events, trajectory, orbits[source_year], source_orbits
            )
            if len(bg_events) < 4:
                skipped_background += 1
                continue
            source_bg_counts.append(len(bg_events))
            stream_model = fit_gaussian(x_stream)
            background_model = fit_gaussian(x_bg)
            log_prior_odds = math.log(len(source_events) / len(bg_events))

            tgt_mask = v4.in_activity_arc(target_sol, [float(e["sol"]) for e in source_events])
            target_candidates = [target_events[int(i)] for i in np.flatnonzero(tgt_mask)]
            target_candidates = [e for e in target_candidates if str(e["id"]) not in all_target_seed_owner]
            kept, x_target, td2, _tres, torb = screened_features(
                target_candidates, source_events, trajectory, orbits[target_year], source_orbits
            )
            candidate_pairs += len(kept)
            if len(kept):
                log_odds = log_prior_odds + gaussian_logpdf(stream_model, x_target) - gaussian_logpdf(background_model, x_target)
                for event, odds, d2, om in zip(kept, log_odds.tolist(), td2.tolist(), torb.tolist()):
                    if float(odds) <= POSTERIOR_LOG_ODDS_CUTOFF:
                        continue
                    positive_pairs += 1
                    eid = str(event["id"])
                    cand = (float(odds), float(om), float(d2), fid)
                    old = best.get(eid)
                    if old is None or (-cand[0], cand[1], cand[2], cand[3]) < (-old[0], old[1], old[2], old[3]):
                        best[eid] = cand
            if family_index % 10 == 0 or family_index == len(families):
                print(
                    f"B1_FAMILY_PROGRESS target_year={target_year} family={family_index}/{len(families)} "
                    f"candidate_pairs={candidate_pairs} positive_pairs={positive_pairs}",
                    flush=True,
                )

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_odds: list[float] = []
        for eid, (odds, _om, _d2, fid) in best.items():
            by_family[fid].append(eid)
            assigned_odds.append(float(odds))
        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["candidate_pairs_after_screens_by_year"][str(target_year)] = candidate_pairs
        diagnostics["positive_odds_pairs_by_year"][str(target_year)] = positive_pairs
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, positive_pairs - len(best))
        diagnostics["families_skipped_insufficient_background_by_year"][str(target_year)] = skipped_background
        diagnostics["assigned_log_odds_median_by_year"][str(target_year)] = float(np.median(assigned_odds)) if assigned_odds else None
        diagnostics["assigned_log_odds_min_by_year"][str(target_year)] = float(min(assigned_odds)) if assigned_odds else None
        diagnostics["source_background_count_median_by_year"][str(target_year)] = float(np.median(source_bg_counts)) if source_bg_counts else None
        diagnostics["source_seed_count_median_by_year"][str(target_year)] = float(np.median(source_seed_counts)) if source_seed_counts else None
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(all_target_seed_owner)

    for before, after in zip(
        sorted(families, key=lambda x: str(x["family_id"])),
        sorted(expanded, key=lambda x: str(x["family_id"])),
    ):
        require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in (
            "years", "year_count", "component_ids", "component_count", "quartet_count",
            "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids",
        ):
            require(before[field] == after[field], f"B1 changed frozen family field {field}")
        require(set(before["event_ids"]).issubset(set(after["event_ids"])), "B1 lost original seed membership")

    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = v1.sha256_json(
        {str(f["family_id"]): f["event_ids"] for f in expanded}
    )
    return expanded, diagnostics, assignments


def main() -> int:
    require(ACTIVITY_PADDING_DEG == v4.ACTIVITY_PADDING_DEG == 6.0, "activity padding ancestry changed")
    require(DENSITY_CEILING == v1.RADIUS == 1.5, "density ceiling ancestry changed")
    require(TRAJECTORY_CEILING == v4.RESIDUAL_CEILING == 1.5, "trajectory ceiling ancestry changed")
    v1.crossfit_expand = crossfit_expand_background_odds
    v1.CORPUS = "orbittrace-background-odds-membership-b1-development"
    rc = v1.main()
    out = Path(v1.parse_args().output)
    src = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src.read_text())
    diag = result["expansion_diagnostics"]
    result["configuration"].update({
        "membership_architecture": "B1 cross-year local-field background odds",
        "feature_vector": list(FEATURES),
        "stream_model": "Ledoit-Wolf Gaussian over original other-year seed leave-one-out features",
        "background_model": "Ledoit-Wolf Gaussian over screened same-source-year non-family field features",
        "prior_odds": "observed original source seeds / screened source background",
        "decision_rule": "transferred posterior log odds > 0",
        "posterior_log_odds_cutoff": 0.0,
        "activity_padding_deg": ACTIVITY_PADDING_DEG,
        "density_ceiling": DENSITY_CEILING,
        "trajectory_ceiling": TRAJECTORY_CEILING,
        "orbital_summary": "median exact Southworth-Hawkins D_SH to all original other-year orbit-valid seeds",
        "parameter_search": False,
        "posterior_cutoff_search": False,
        "feature_weight_search": False,
        "covariance_model_search": False,
        "orbit_threshold_search": False,
        "ranking_changed": False,
        "recursive_growth": False,
        "target_region_orbit_decode": False,
    })
    ig = result["integrity_gates"]
    ig.update({
        "exact_background_odds_zero_cutoff": abs(float(diag["posterior_log_odds_cutoff"])) <= 1e-15,
        "exact_inherited_activity_padding_6deg": abs(float(diag["activity_padding_deg"]) - 6.0) <= 1e-15,
        "exact_inherited_density_ceiling_1_5": abs(float(diag["density_ceiling"]) - 1.5) <= 1e-15,
        "exact_inherited_trajectory_ceiling_1_5": abs(float(diag["trajectory_ceiling"]) - 1.5) <= 1e-15,
        "exact_full_template_orbital_median": diag["orbital_statistic"] == "median Southworth-Hawkins D_SH to all original other-year orbit-valid seeds",
        "all_target_excluded_events_have_orbits": int(diag["orbit_event_count"]) == EXPECTED_ORBIT_EVENT_COUNT,
        "orbit_parser_zero_label_access": all(a["label_column_accessed"] is False for a in diag["orbit_parse_audits"]),
        "orbit_parser_zero_target_region_decode": all(a["target_region_orbit_decoded"] is False for a in diag["orbit_parse_audits"]),
        "all_orbit_months_exact": [a["key"] for a in diag["orbit_parse_audits"]] == list(MONTH_KEYS),
        "background_model_is_explicit_competitor": diag["background_density_model"].startswith("3D Gaussian"),
        "membership_labels_never_accessed": diag["label_access_during_membership"] is False,
        "b1_parameters_not_selected_by_search": all([
            diag["parameter_search"] is False,
            diag["posterior_cutoff_search"] is False,
            diag["covariance_model_search"] is False,
            diag["feature_weight_search"] is False,
            diag["orbit_threshold_search"] is False,
        ]),
    })
    result["claim_boundary"] = (
        "Target-excluded B1 development only. The exact promoted-v8 discovery family universe and multiplicity ranking "
        "are frozen before B1 membership. B1 transfers a stream-vs-local-field density model from the opposite year "
        "using only original v8 seeds plus unlabeled field events; labels enter only after expanded membership is hashed. "
        "A development pass does not establish Sugar/HDBSCAN superiority or external generalization and requires frozen "
        "matched comparison plus prospective external validation before any OrbitTrace target-containing application."
    )
    passed = all(bool(x) for x in result["integrity_gates"].values()) and all(bool(x) for x in result["scientific_gates"].values())
    result["verdict"] = "PASS_BACKGROUND_ODDS_MEMBERSHIP_B1_DEVELOPMENT" if passed else "FAIL_BACKGROUND_ODDS_MEMBERSHIP_B1_DEVELOPMENT"
    result["successor_rule"] = (
        "freeze B1 and advance without retuning to matched literature comparison and fresh external validation"
        if passed else
        "preserve B1 as a no-go; do not tune B1 parameters from this result"
    )

    (out / "background_odds_membership_b1_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "background_odds_membership_b1_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "background_odds_membership_b1_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )
    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    lines = [
        "# OrbitTrace background-odds membership B1 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- baseline / B1 macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / B1 recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / B1 qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / B1 top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in YEARS:
        lines.append(f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**")
    lines += ["", "No OrbitTrace target information or target-region orbit was accessed. The exact v8 ranking was unchanged."]
    (out / "BACKGROUND_ODDS_MEMBERSHIP_B1_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    src.unlink(missing_ok=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
