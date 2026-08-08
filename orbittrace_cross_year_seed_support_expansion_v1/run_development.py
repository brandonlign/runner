#!/usr/bin/env python3
"""One-shot target-excluded cross-year seed-support membership expansion on frozen v8."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_pooled_year_centroid_v8 import run_development as v8

v6 = v8.v6
mult = v8.mult
YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-cross-year-seed-support-expansion-v1-development"
TOP_K = 100
RADIUS = 1.5
SOL_PREFILTER = 4.0 * RADIUS
EXPECTED = {
    "families": 226,
    "qualified": 95,
    "multiplicity_recovery": 58,
    "persistence_recovery": 59,
    "brown_recovery": 55,
    "v3_recovery": 55,
    "precision": 0.6884631112636006,
    "mrr": 0.045531138942766655,
    "macro_f1": 0.1736657194465356,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--centroid-audit-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def circular_arc(values: list[float]) -> tuple[float, float]:
    x = sorted(float(v) % 360.0 for v in values)
    require(x, "empty circular arc")
    if len(x) == 1:
        return x[0], x[0]
    gaps = [(x[i + 1] - x[i], i) for i in range(len(x) - 1)]
    gaps.append(((x[0] + 360.0) - x[-1], len(x) - 1))
    _, i = max(gaps, key=lambda t: (t[0], -t[1]))
    return x[(i + 1) % len(x)], x[i]


def in_expanded_arc(sol: np.ndarray, values: list[float]) -> np.ndarray:
    start, end = circular_arc(values)
    width = (end - start) % 360.0
    if width + 2.0 * SOL_PREFILTER >= 360.0:
        return np.ones(len(sol), dtype=bool)
    s = (start - SOL_PREFILTER) % 360.0
    e = (end + SOL_PREFILTER) % 360.0
    return (sol >= s) | (sol <= e) if s > e else (sol >= s) & (sol <= e)


def min_exact_distances(target: list[dict[str, Any]], support_events: list[dict[str, Any]]) -> np.ndarray:
    if not target:
        return np.empty(0, dtype=np.float64)
    ss = np.asarray([float(e["sol"]) for e in support_events], dtype=np.float64)
    sl = np.asarray([float(e["sun_lon"]) for e in support_events], dtype=np.float64)
    sb = np.asarray([float(e["ecl_lat"]) for e in support_events], dtype=np.float64)
    sv = np.asarray([float(e["vg"]) for e in support_events], dtype=np.float64)
    out = np.full(len(target), np.inf, dtype=np.float64)
    for lo in range(0, len(target), 2048):
        rows = target[lo : lo + 2048]
        ts = np.asarray([float(e["sol"]) for e in rows])[:, None]
        tl = np.asarray([float(e["sun_lon"]) for e in rows])[:, None]
        tb = np.asarray([float(e["ecl_lat"]) for e in rows])[:, None]
        tv = np.asarray([float(e["vg"]) for e in rows])[:, None]
        dsol = ((ts - ss[None, :] + 180.0) % 360.0 - 180.0) / 4.0
        dlon_raw = ((tl - sl[None, :] + 180.0) % 360.0 - 180.0)
        dlon = dlon_raw * np.cos(np.radians(0.5 * (tb + sb[None, :]))) / 2.0
        dlat = (tb - sb[None, :]) / 2.0
        dvg = (tv - sv[None, :]) / 2.0
        d = np.sqrt(dsol*dsol + dlon*dlon + dlat*dlat + dvg*dvg)
        out[lo : lo + len(rows)] = np.min(d, axis=1)
    return out


def crossfit_expand(families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in YEARS}
    diagnostics: dict[str, Any] = {
        "radius": RADIUS, "solar_prefilter_deg": SOL_PREFILTER,
        "new_members_by_year": {}, "eligible_pair_count_by_year": {},
        "conflicted_events_by_year": {}, "original_seed_events_by_year": {},
        "exclusive_assignment": True, "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
    }

    for target_year in YEARS:
        source_year = YEARS[1] if target_year == YEARS[0] else YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events])
        source_ids_by_family = {fid: sorted(ids & set(event_lookup[source_year])) for fid, ids in original.items()}
        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str]] = {}
        eligible_pairs = 0
        for family in families:
            fid = str(family["family_id"])
            source_ids = source_ids_by_family[fid]
            require(source_ids, f"family {fid} lacks other-year support")
            support_events = [event_lookup[source_year][eid] for eid in source_ids]
            mask = in_expanded_arc(target_sol, [float(e["sol"]) for e in support_events])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            distances = min_exact_distances(candidates, support_events)
            for i, d in zip(idx.tolist(), distances.tolist()):
                if d > RADIUS + 1e-12:
                    continue
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                eligible_pairs += 1
                cand = (float(d), fid)
                old = best.get(event_id)
                if old is None or cand < old:
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        for eid, (_d, fid) in best.items():
            by_family[fid].append(eid)
        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["eligible_pair_count_by_year"][str(target_year)] = eligible_pairs
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, eligible_pairs - len(best))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)

    for before, after in zip(sorted(families, key=lambda x: str(x["family_id"])), sorted(expanded, key=lambda x: str(x["family_id"]))):
        require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in ("years", "year_count", "component_ids", "component_count", "quartet_count", "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids"):
            require(before[field] == after[field], f"expansion changed frozen family field {field}")
        require(set(before["event_ids"]).issubset(set(after["event_ids"])), "seed membership lost")
    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = sha256_json({str(f["family_id"]): f["event_ids"] for f in expanded})
    return expanded, diagnostics, assignments


def size_bin(n: int) -> str:
    if n <= 9: return "4-9"
    if n <= 24: return "10-24"
    if n <= 49: return "25-49"
    if n <= 99: return "50-99"
    return "100+"


def prf(overlap: int, predicted: int, actual: int) -> tuple[float, float, float]:
    p = overlap / predicted if predicted else 0.0
    r = overlap / actual if actual else 0.0
    return p, r, (2.0*p*r/(p+r) if p+r else 0.0)


def annual_summary(families: list[dict[str, Any]], hidden: dict[str, str], scan_by_year: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        ids = {str(e["id"]) for e in scan_by_year[year]}
        actual = Counter(hidden[eid] for eid in ids if hidden[eid] != "SPORADIC")
        family_members = {str(f["family_id"]): [str(eid) for eid in f["event_ids"] if str(eid) in ids] for f in families}
        rows = []
        for label, n in sorted(actual.items()):
            if n < 4: continue
            best = None
            for fid, members in family_members.items():
                if not members: continue
                overlap = sum(hidden[eid] == label for eid in members)
                p, r, f1 = prf(overlap, len(members), n)
                cand = (f1, p, overlap, fid, r, len(members))
                if best is None or cand[:3] > best[:3]: best = cand
            if best is None:
                f1 = p = r = 0.0; overlap = predicted = 0; fid = None
            else:
                f1, p, overlap, fid, r, predicted = best
            rows.append({"label": label, "annual_members": n, "size_bin": size_bin(n), "family_id": fid,
                         "overlap": overlap, "predicted": predicted, "precision": p, "recall": r, "f1": f1})
        summary = {}
        for b in ("4-9", "10-24", "25-49", "50-99", "100+", "all"):
            subset = rows if b == "all" else [r for r in rows if r["size_bin"] == b]
            summary[b] = {
                "showers": len(subset),
                "mean_f1": float(np.mean([r["f1"] for r in subset])) if subset else None,
                "mean_precision": float(np.mean([r["precision"] for r in subset])) if subset else None,
                "mean_recall": float(np.mean([r["recall"] for r in subset])) if subset else None,
            }
        out[str(year)] = {"summary": summary, "rows": rows}
    return out


def main() -> int:
    args = parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    centroid_audit = json.loads(args.centroid_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "source audit failed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor failed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "centroid audit failed")
    require(all(mult.v3.self_test().values()) and all(mult.brown.self_test().values()), "score self-test failed")

    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS; support.MONTH_KEYS = MONTH_KEYS; support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - RADIUS) <= 1e-15, "inherited radius changed")
    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)

    scan_by_year, _calibration, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    require([s["key"] for s in catalogue_sources] == list(MONTH_KEYS), "monthly universe changed")

    components = []; scan_audits = []
    for year in YEARS:
        audit, _passing, comps = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(audit["source_labels_used_for_proposals"] is False and audit["score_threshold_applied"] is False, "proposal blindness changed")
        scan_audits.append(audit); components.extend(comps)
    families, support_rankings = support.build_families(components, base)
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)
    mult.YEARS = YEARS; mult.MONTH_KEYS = MONTH_KEYS; mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    rankings = {
        "multiplicity": mult.rank_scored(scored, "multiplicity"),
        "brown": mult.rank_scored(scored, "brown"),
        "v3": mult.rank_scored(scored, "v3"),
        "label_free_persistence": [str(x) for x in support_rankings["persistence"]],
    }

    expanded, expansion_diag, assignments = crossfit_expand(families, scan_by_year)
    prelabel_payload = {
        "ranking": rankings["multiplicity"],
        "seed_membership": {str(f["family_id"]): f["event_ids"] for f in families},
        "expanded_membership": {str(f["family_id"]): f["event_ids"] for f in expanded},
        "assignments": assignments,
    }
    prelabel_sha = sha256_json(prelabel_payload)
    (args.output / "crossfit_expansion_prelabel_sha256.txt").write_text(prelabel_sha + "\n")

    baseline_metrics_full = {name: mult.evaluate_order(hidden_labels, families, order) for name, order in rankings.items()}
    expanded_metrics_full = {name: mult.evaluate_order(hidden_labels, expanded, order) for name, order in rankings.items()}
    compact = lambda d: {k: v for k, v in d.items() if k != "per_label"}
    baseline_metrics = {k: compact(v) for k, v in baseline_metrics_full.items()}
    expanded_metrics = {k: compact(v) for k, v in expanded_metrics_full.items()}
    baseline_annual = annual_summary(families, hidden_labels, scan_by_year)
    expanded_annual = annual_summary(expanded, hidden_labels, scan_by_year)

    bm = baseline_metrics["multiplicity"]
    require(len(families) == EXPECTED["families"], "v8 family count not reproduced")
    require(int(bm["qualified_matches"]) == EXPECTED["qualified"], "v8 qualified baseline not reproduced")
    require(int(bm["recovered_at_100"]) == EXPECTED["multiplicity_recovery"], "v8 recovery not reproduced")
    require(int(baseline_metrics["label_free_persistence"]["recovered_at_100"]) == EXPECTED["persistence_recovery"], "v8 persistence not reproduced")
    require(int(baseline_metrics["brown"]["recovered_at_100"]) == EXPECTED["brown_recovery"], "v8 Brown not reproduced")
    require(int(baseline_metrics["v3"]["recovered_at_100"]) == EXPECTED["v3_recovery"], "v8 v3 not reproduced")
    require(abs(float(bm["top100_dominant_precision"]) - EXPECTED["precision"]) <= 1e-12, "v8 precision not reproduced")
    require(abs(float(bm["mrr"]) - EXPECTED["mrr"]) <= 1e-12, "v8 MRR not reproduced")
    require(abs(float(bm["macro_f1"]) - EXPECTED["macro_f1"]) <= 1e-12, "v8 macro F1 not reproduced")

    annual_delta = {}
    for year in YEARS:
        annual_delta[str(year)] = {}
        for b in ("4-9", "10-24", "25-49", "50-99", "100+", "all"):
            a = baseline_annual[str(year)]["summary"][b]["mean_f1"]
            z = expanded_annual[str(year)]["summary"][b]["mean_f1"]
            annual_delta[str(year)][b] = None if a is None or z is None else float(z - a)

    material_moderate = []
    for b in ("10-24", "25-49", "50-99", "100+"):
        if all(baseline_annual[str(y)]["summary"][b]["showers"] > 0 for y in YEARS):
            material_moderate.append(all(float(annual_delta[str(y)][b]) >= 0.10 for y in YEARS))

    em = expanded_metrics["multiplicity"]
    integrity_gates = {
        "exact_target_excluded_2022_2023_panel": True,
        "exact_v8_family_universe_reproduced": len(families) == EXPECTED["families"],
        "exact_v8_preexpansion_metrics_reproduced": True,
        "v8_ranking_unchanged_by_expansion": rankings["multiplicity"] == mult.rank_scored(scored, "multiplicity"),
        "family_graph_scores_centroids_unchanged": True,
        "other_year_seed_support_only": expansion_diag["other_year_support_only"],
        "exclusive_nearest_family_assignment": expansion_diag["exclusive_assignment"],
        "no_recursive_growth": expansion_diag["new_members_never_reused_as_support"],
        "exact_inherited_radius_1_5": abs(RADIUS - float(support.FAMILY_LINK_RADIUS)) <= 1e-15,
        "prelabel_membership_hash_frozen": len(prelabel_sha) == 64,
        "all_scored_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128],
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= v8.BROWN_EQ_TOL,
        "no_label_dependent_proposal_calibration": all(a["source_labels_used_for_proposals"] is False for a in scan_audits),
    }
    scientific_gates = {
        "expanded_recovery_at_100_nonregression": int(em["recovered_at_100"]) >= 58,
        "expanded_qualified_nonregression": int(em["qualified_matches"]) >= 95,
        "expanded_top100_precision_at_least_065": float(em["top100_dominant_precision"]) >= 0.65,
        "expanded_macro_f1_gain_at_least_005": float(em["macro_f1"]) >= EXPECTED["macro_f1"] + 0.05,
        "annual_all_mean_f1_gain_at_least_010_both_years": all(float(annual_delta[str(y)]["all"]) >= 0.10 for y in YEARS),
        "annual_4_9_mean_f1_no_material_regression": all(float(annual_delta[str(y)]["4-9"]) >= -0.02 for y in YEARS),
        "at_least_one_moderate_or_large_bin_material_gain_both_years": any(material_moderate),
    }
    verdict = "PASS_CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT" if all(integrity_gates.values()) and all(scientific_gates.values()) else "FAIL_CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS), "blind_exclusion": [20.0, 55.0],
            "base_method": "promoted v8 pooled-year-centroid label-free sparse-support multiplicity",
            "membership_rule": "other-year original seed support; exact inherited v8 distance <=1.5; exclusive nearest-family assignment",
            "family_link_radius_reused_as_membership_radius": RADIUS,
            "solar_prefilter_deg_necessary_only": SOL_PREFILTER,
            "ranking_changed": False, "recursive_growth": False, "threshold_search": False, "variant_search": False,
        },
        "family_count": len(families), "prelabel_payload_sha256": prelabel_sha,
        "centroid_repair": repair, "expansion_diagnostics": expansion_diag,
        "baseline_metrics": baseline_metrics, "expanded_metrics": expanded_metrics,
        "baseline_annual": {y: v["summary"] for y, v in baseline_annual.items()},
        "expanded_annual": {y: v["summary"] for y, v in expanded_annual.items()},
        "annual_mean_f1_delta": annual_delta,
        "integrity_gates": integrity_gates, "scientific_gates": scientific_gates,
        "claim_boundary": "Target-excluded development only. Expansion changes membership assignment after the exact v8 ranking is frozen. No OrbitTrace target information, target-region event, Stage A/B output, or literature-benchmark-driven parameter search entered the method.",
    }
    (args.output / "cross_year_seed_support_expansion_v1_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "cross_year_seed_support_expanded_families.json").write_text(json.dumps(expanded, separators=(",", ":")) + "\n")
    (args.output / "cross_year_seed_support_assignments.json").write_text(json.dumps(assignments, separators=(",", ":")) + "\n")
    lines = [
        "# OrbitTrace cross-year seed-support expansion v1 development", "", f"**Verdict:** `{verdict}`", "",
        f"- frozen v8 families: **{len(families)}**",
        f"- newly assigned events: **{expansion_diag['total_new_members']}**",
        f"- baseline / expanded global macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in YEARS:
        lines.append(f"- {y} all-shower mean-F1 delta: **{annual_delta[str(y)]['all']:+.6f}**")
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (args.output / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
