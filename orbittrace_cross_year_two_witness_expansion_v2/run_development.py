#!/usr/bin/env python3
"""One-shot two-witness cross-year membership expansion on the exact frozen v8 seeds."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

MIN_SUPPORT_WITNESSES = 2
V1_RUN = 31233617751
V1_ARTIFACT = 9014893340
V1_ARTIFACT_DIGEST = "sha256:b780f688e034bc26ff16b389d80877e88130c26c2749b4b9c341ed1deeec05e4"
V1_SOURCE_COMMIT = "e87a61909f06b2c8f4e763a2f915d13b5c365620"


def min_distance_and_support_count(
    target: list[dict[str, Any]], support_events: list[dict[str, Any]]
) -> tuple[np.ndarray, np.ndarray]:
    if not target:
        return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.int32)
    ss = np.asarray([float(e["sol"]) for e in support_events], dtype=np.float64)
    sl = np.asarray([float(e["sun_lon"]) for e in support_events], dtype=np.float64)
    sb = np.asarray([float(e["ecl_lat"]) for e in support_events], dtype=np.float64)
    sv = np.asarray([float(e["vg"]) for e in support_events], dtype=np.float64)
    out_min = np.full(len(target), np.inf, dtype=np.float64)
    out_count = np.zeros(len(target), dtype=np.int32)
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
        out_min[lo : lo + len(rows)] = np.min(d, axis=1)
        out_count[lo : lo + len(rows)] = np.sum(d <= v1.RADIUS + 1e-12, axis=1).astype(np.int32)
    return out_min, out_count


def crossfit_expand_two_witness(
    families: list[dict[str, Any]], scan_by_year: dict[int, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}
    diagnostics: dict[str, Any] = {
        "radius": v1.RADIUS,
        "solar_prefilter_deg": v1.SOL_PREFILTER,
        "min_distinct_other_year_seed_witnesses": MIN_SUPPORT_WITNESSES,
        "new_members_by_year": {},
        "single_witness_pairs_rejected_by_year": {},
        "one_or_more_witness_pairs_by_year": {},
        "two_or_more_witness_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "assigned_support_count_median_by_year": {},
        "assigned_support_count_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "other_year_support_only": True,
        "witness_count_selected_by_search": False,
        "witness_count_inherited_from_v8_min_anchor_count": 2,
    }

    for target_year in v1.YEARS:
        source_year = v1.YEARS[1] if target_year == v1.YEARS[0] else v1.YEARS[0]
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events])
        source_ids_by_family = {
            fid: sorted(ids & set(event_lookup[source_year])) for fid, ids in original.items()
        }
        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, str, int]] = {}
        one_plus_pairs = 0
        two_plus_pairs = 0
        single_rejected = 0
        for family in families:
            fid = str(family["family_id"])
            source_ids = source_ids_by_family[fid]
            v1.require(source_ids, f"family {fid} lacks other-year support")
            support_events = [event_lookup[source_year][eid] for eid in source_ids]
            mask = v1.in_expanded_arc(target_sol, [float(e["sol"]) for e in support_events])
            idx = np.flatnonzero(mask)
            candidates = [target_events[int(i)] for i in idx]
            distances, support_counts = min_distance_and_support_count(candidates, support_events)
            for i, d, count in zip(idx.tolist(), distances.tolist(), support_counts.tolist()):
                if d > v1.RADIUS + 1e-12:
                    continue
                event_id = str(target_events[i]["id"])
                if event_id in target_seed_owner:
                    continue
                one_plus_pairs += 1
                if int(count) < MIN_SUPPORT_WITNESSES:
                    single_rejected += 1
                    continue
                two_plus_pairs += 1
                cand = (float(d), fid, int(count))
                old = best.get(event_id)
                if old is None or (cand[0], cand[1]) < (old[0], old[1]):
                    best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        assigned_counts: list[int] = []
        for eid, (_d, fid, count) in best.items():
            by_family[fid].append(eid)
            assigned_counts.append(int(count))
        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["one_or_more_witness_pairs_by_year"][str(target_year)] = one_plus_pairs
        diagnostics["two_or_more_witness_pairs_by_year"][str(target_year)] = two_plus_pairs
        diagnostics["single_witness_pairs_rejected_by_year"][str(target_year)] = single_rejected
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, two_plus_pairs - len(best))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)
        diagnostics["assigned_support_count_median_by_year"][str(target_year)] = (
            float(np.median(assigned_counts)) if assigned_counts else None
        )
        diagnostics["assigned_support_count_max_by_year"][str(target_year)] = (
            int(max(assigned_counts)) if assigned_counts else None
        )

    for before, after in zip(
        sorted(families, key=lambda x: str(x["family_id"])),
        sorted(expanded, key=lambda x: str(x["family_id"])),
    ):
        v1.require(str(before["family_id"]) == str(after["family_id"]), "family IDs changed")
        for field in (
            "years", "year_count", "component_ids", "component_count", "quartet_count",
            "anchor_count", "best_score", "year_strengths", "ranking_scores", "ranks", "centroids",
        ):
            v1.require(before[field] == after[field], f"expansion changed frozen family field {field}")
        v1.require(set(before["event_ids"]).issubset(set(after["event_ids"])), "seed membership lost")

    diagnostics["total_new_members"] = sum(diagnostics["new_members_by_year"].values())
    diagnostics["expanded_membership_sha256"] = v1.sha256_json(
        {str(f["family_id"]): f["event_ids"] for f in expanded}
    )
    return expanded, diagnostics, assignments


def main() -> int:
    v1.crossfit_expand = crossfit_expand_two_witness
    v1.CORPUS = "orbittrace-cross-year-two-witness-expansion-v2-development"
    rc = v1.main()
    out = Path(v1.parse_args().output)
    src_json = out / "cross_year_seed_support_expansion_v1_development.json"
    result = json.loads(src_json.read_text())
    result["configuration"].update({
        "membership_rule": "at least two distinct other-year original v8 seed witnesses within exact inherited distance <=1.5; exclusive nearest-family assignment",
        "min_distinct_other_year_seed_witnesses": MIN_SUPPORT_WITNESSES,
        "witness_count_source": "exact inherited v8/fixed4 MIN_ANCHOR_COUNT=2 repeated-support principle",
        "witness_count_search": False,
        "v1_predecessor_run": V1_RUN,
        "v1_predecessor_artifact": V1_ARTIFACT,
        "v1_predecessor_artifact_digest": V1_ARTIFACT_DIGEST,
        "v1_source_commit": V1_SOURCE_COMMIT,
    })
    result["integrity_gates"]["minimum_two_distinct_other_year_seed_witnesses"] = (
        int(result["expansion_diagnostics"]["min_distinct_other_year_seed_witnesses"]) == 2
    )
    result["integrity_gates"]["witness_count_not_selected_by_search"] = (
        result["expansion_diagnostics"]["witness_count_selected_by_search"] is False
    )
    result["claim_boundary"] = (
        "Target-excluded v2 development only. The exact v8 family universe and ranking were frozen first. "
        "The sole successor change is a two-distinct-other-year-seed witness requirement inherited from "
        "the existing v8 repeated-support minimum. No OrbitTrace target information, target-region event, "
        "Stage A/B output, witness-count search, radius search, or literature-benchmark parameter tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_CROSS_YEAR_TWO_WITNESS_EXPANSION_V2_DEVELOPMENT"
        if passed else "FAIL_CROSS_YEAR_TWO_WITNESS_EXPANSION_V2_DEVELOPMENT"
    )

    dst_json = out / "cross_year_two_witness_expansion_v2_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "cross_year_two_witness_expanded_families.json").write_bytes(
        (out / "cross_year_seed_support_expanded_families.json").read_bytes()
    )
    (out / "cross_year_two_witness_assignments.json").write_bytes(
        (out / "cross_year_seed_support_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    diag = result["expansion_diagnostics"]
    lines = [
        "# OrbitTrace cross-year two-witness expansion v2 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- single-witness family-event pairs rejected: **{sum(diag['single_witness_pairs_rejected_by_year'].values())}**",
        f"- baseline / expanded macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / expanded recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / expanded qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / expanded top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(
            f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "CROSS_YEAR_TWO_WITNESS_EXPANSION_V2_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")
    src_json.unlink(missing_ok=True)
    (out / "CROSS_YEAR_SEED_SUPPORT_EXPANSION_V1_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
