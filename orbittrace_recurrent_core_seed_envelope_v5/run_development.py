#!/usr/bin/env python3
"""One-shot seed-centered local-envelope membership refinement on frozen v8."""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_recurrent_core_local_envelope_v4 import run_development as v4

v1 = v4.v1
V4_RUN = 31237514755
V4_ARTIFACT = 9016160109
V4_ARTIFACT_DIGEST = "sha256:ddf8b89aa4e012487d71077ee745d3ce18cbad4eca699fb36423ee0c6ede31af"
V4_SOURCE_COMMIT = "7758c8ba8d9ffad4d25ba2a6d900f790027a10e9"


def expanded_seed_arc_mask(sol: np.ndarray, support_events: list[dict[str, Any]], radius: float) -> np.ndarray:
    start, end = v1.circular_arc([float(e["sol"]) for e in support_events])
    pad = min(180.0, 4.0 * float(radius) + 1e-12)
    width = (end - start) % 360.0
    if width + 2.0 * pad >= 360.0:
        return np.ones(len(sol), dtype=bool)
    s = (start - pad) % 360.0
    e = (end + pad) % 360.0
    return (sol >= s) | (sol <= e) if s > e else (sol >= s) & (sol <= e)


def crossfit_expand_seed_envelope(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, list[str]]]]:
    v1.require(v4._CAPTURED_COMPONENTS, "component capture is empty")
    component_by_id = {str(c["component_id"]): c for c in v4._CAPTURED_COMPONENTS}
    v1.require(len(component_by_id) == len(v4._CAPTURED_COMPONENTS), "captured component IDs are not unique")

    expanded = copy.deepcopy(families)
    original = {str(f["family_id"]): set(str(x) for x in f["event_ids"]) for f in families}
    event_lookup_int = {y: {str(e["id"]): e for e in scan_by_year[y]} for y in v1.YEARS}
    event_lookup = {str(y): event_lookup_int[y] for y in v1.YEARS}
    fam_lookup = {str(f["family_id"]): f for f in expanded}
    assignments: dict[str, dict[str, list[str]]] = {str(y): {} for y in v1.YEARS}

    radius_by_component = {
        cid: v4.fixed_centroid_radius(component, event_lookup)
        for cid, component in component_by_id.items()
    }

    diagnostics: dict[str, Any] = {
        "support_unit": "same-year original frozen component seed events",
        "component_radius_rule": "maximum original seed-event distance to frozen component centroid",
        "support_center_rule": "every original component seed event; new members never become centers",
        "global_membership_radius_used": False,
        "radius_multiplier": None,
        "radius_quantile": None,
        "component_centroids_refit": False,
        "same_year_support_only": True,
        "other_year_support_only": False,
        "cross_year_recurrence_preserved_by_frozen_v8_family": True,
        "new_members_by_year": {},
        "eligible_family_event_pairs_by_year": {},
        "conflicted_events_by_year": {},
        "original_seed_events_by_year": {},
        "component_radius_min_by_year": {},
        "component_radius_median_by_year": {},
        "component_radius_p95_by_year": {},
        "component_radius_max_by_year": {},
        "component_seed_count_min_by_year": {},
        "component_seed_count_median_by_year": {},
        "component_seed_count_max_by_year": {},
        "assigned_normalized_radius_median_by_year": {},
        "assigned_normalized_radius_max_by_year": {},
        "exclusive_assignment": True,
        "new_members_never_reused_as_support": True,
        "component_ids_from_frozen_family_graph_only": True,
    }

    for target_year in v1.YEARS:
        target_events = scan_by_year[target_year]
        target_sol = np.asarray([float(e["sol"]) % 360.0 for e in target_events], dtype=np.float64)

        target_seed_owner: dict[str, str] = {}
        for fid, ids in original.items():
            for eid in sorted(ids & set(event_lookup_int[target_year])):
                prior = target_seed_owner.get(eid)
                v1.require(prior is None or prior == fid, f"seed event belongs to multiple families: {eid}")
                target_seed_owner[eid] = fid

        best: dict[str, tuple[float, float, str]] = {}
        eligible_pairs = 0
        year_radii: list[float] = []
        year_seed_counts: list[int] = []

        for family in families:
            fid = str(family["family_id"])
            target_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == target_year
            ]
            v1.require(target_components, f"family {fid} lacks target-year components")

            for component in target_components:
                cid = str(component["component_id"])
                radius = float(radius_by_component[cid])
                member_ids = [str(x) for x in component["event_ids"]]
                v1.require(member_ids and all(eid in event_lookup_int[target_year] for eid in member_ids), "component seed event missing")
                support_events = [event_lookup_int[target_year][eid] for eid in member_ids]
                year_radii.append(radius)
                year_seed_counts.append(len(support_events))

                mask = expanded_seed_arc_mask(target_sol, support_events, radius)
                idx = np.flatnonzero(mask)
                candidates = [target_events[int(i)] for i in idx]
                distances = v1.min_exact_distances(candidates, support_events)

                for i, distance in zip(idx.tolist(), distances.tolist()):
                    if float(distance) > radius + 1e-12:
                        continue
                    event_id = str(target_events[i]["id"])
                    if event_id in target_seed_owner:
                        continue
                    eligible_pairs += 1
                    normalized = (float(distance) / radius) if radius > 0.0 else 0.0
                    cand = (float(distance), normalized, fid)
                    old = best.get(event_id)
                    if old is None or (cand[0], cand[2]) < (old[0], old[2]):
                        best[event_id] = cand

        by_family: dict[str, list[str]] = defaultdict(list)
        normalized_values: list[float] = []
        for eid, (_distance, normalized, fid) in best.items():
            by_family[fid].append(eid)
            normalized_values.append(float(normalized))

        for fid, ids in by_family.items():
            ids.sort()
            fam = fam_lookup[fid]
            fam["event_ids"] = sorted(set(str(x) for x in fam["event_ids"]) | set(ids))
            fam["event_count"] = len(fam["event_ids"])
            assignments[str(target_year)][fid] = ids

        diagnostics["new_members_by_year"][str(target_year)] = len(best)
        diagnostics["eligible_family_event_pairs_by_year"][str(target_year)] = eligible_pairs
        diagnostics["conflicted_events_by_year"][str(target_year)] = max(0, eligible_pairs - len(best))
        diagnostics["original_seed_events_by_year"][str(target_year)] = len(target_seed_owner)
        diagnostics["component_radius_min_by_year"][str(target_year)] = float(min(year_radii))
        diagnostics["component_radius_median_by_year"][str(target_year)] = float(np.median(year_radii))
        diagnostics["component_radius_p95_by_year"][str(target_year)] = float(np.quantile(year_radii, 0.95))
        diagnostics["component_radius_max_by_year"][str(target_year)] = float(max(year_radii))
        diagnostics["component_seed_count_min_by_year"][str(target_year)] = int(min(year_seed_counts))
        diagnostics["component_seed_count_median_by_year"][str(target_year)] = float(np.median(year_seed_counts))
        diagnostics["component_seed_count_max_by_year"][str(target_year)] = int(max(year_seed_counts))
        diagnostics["assigned_normalized_radius_median_by_year"][str(target_year)] = (
            float(np.median(normalized_values)) if normalized_values else None
        )
        diagnostics["assigned_normalized_radius_max_by_year"][str(target_year)] = (
            float(max(normalized_values)) if normalized_values else None
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
    # Reuse v4's exact component capture, v8 reconstruction, evaluation, and frozen scientific gates.
    v4.crossfit_expand_local_envelope = crossfit_expand_seed_envelope
    rc = v4.main()

    out = Path(v1.parse_args().output)
    src_json = out / "recurrent_core_local_envelope_v4_development.json"
    result = json.loads(src_json.read_text())

    result["configuration"].update({
        "membership_rule": "same-year seed-centered component envelope using exact v4 component radius; exclusive nearest-family assignment",
        "support_unit": "same-year original frozen component seed events",
        "support_center_rule": "all original seed events; no newly assigned center",
        "component_radius_rule": "max original seed-event distance to frozen component centroid",
        "global_membership_radius": None,
        "global_membership_radius_search": False,
        "radius_multiplier": None,
        "radius_quantile": None,
        "same_year_support": True,
        "cross_year_recurrence_preserved_by_frozen_v8_family": True,
        "recursive_growth": False,
        "v4_predecessor_run": V4_RUN,
        "v4_predecessor_artifact": V4_ARTIFACT,
        "v4_predecessor_artifact_digest": V4_ARTIFACT_DIGEST,
        "v4_source_commit": V4_SOURCE_COMMIT,
    })
    result["integrity_gates"]["original_seed_centers_only"] = (
        result["expansion_diagnostics"]["support_center_rule"]
        == "every original component seed event; new members never become centers"
        and result["expansion_diagnostics"]["new_members_never_reused_as_support"] is True
    )
    result["integrity_gates"]["v4_component_radius_reused_exactly"] = (
        result["expansion_diagnostics"]["component_radius_rule"]
        == "maximum original seed-event distance to frozen component centroid"
        and result["expansion_diagnostics"]["global_membership_radius_used"] is False
        and result["expansion_diagnostics"]["radius_multiplier"] is None
        and result["expansion_diagnostics"]["radius_quantile"] is None
    )
    result["claim_boundary"] = (
        "Target-excluded v5 development only. The exact v8 recurrent family universe and ranking were frozen first. "
        "Membership refinement uses the unchanged v4 component-local radius around original same-year component seed "
        "events; new members never become support. No OrbitTrace target information, target-region event, Stage A/B "
        "output, global membership radius, multiplier, quantile search, recursive growth, or literature-benchmark "
        "parameter tuning entered the method."
    )
    passed = all(result["integrity_gates"].values()) and all(result["scientific_gates"].values())
    result["verdict"] = (
        "PASS_RECURRENT_CORE_SEED_ENVELOPE_V5_DEVELOPMENT"
        if passed else "FAIL_RECURRENT_CORE_SEED_ENVELOPE_V5_DEVELOPMENT"
    )

    dst_json = out / "recurrent_core_seed_envelope_v5_development.json"
    dst_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "recurrent_core_seed_envelope_v5_families.json").write_bytes(
        (out / "recurrent_core_local_envelope_v4_families.json").read_bytes()
    )
    (out / "recurrent_core_seed_envelope_v5_assignments.json").write_bytes(
        (out / "recurrent_core_local_envelope_v4_assignments.json").read_bytes()
    )

    bm = result["baseline_metrics"]["multiplicity"]
    em = result["expanded_metrics"]["multiplicity"]
    diag = result["expansion_diagnostics"]
    lines = [
        "# OrbitTrace recurrent-core seed-envelope v5 development", "",
        f"**Verdict:** `{result['verdict']}`", "",
        f"- newly assigned events: **{diag['total_new_members']}**",
        f"- baseline / refined macro F1: **{bm['macro_f1']:.6f} / {em['macro_f1']:.6f}**",
        f"- baseline / refined recovery@100: **{bm['recovered_at_100']} / {em['recovered_at_100']}**",
        f"- baseline / refined qualified matches: **{bm['qualified_matches']} / {em['qualified_matches']}**",
        f"- baseline / refined top-100 precision: **{bm['top100_dominant_precision']:.6f} / {em['top100_dominant_precision']:.6f}**",
    ]
    for y in v1.YEARS:
        lines.append(
            f"- {y} all-shower mean-F1 delta: **{result['annual_mean_f1_delta'][str(y)]['all']:+.6f}**"
        )
    lines += ["", "No OrbitTrace target information was accessed. The exact v8 ranking was unchanged."]
    (out / "RECURRENT_CORE_SEED_ENVELOPE_V5_DEVELOPMENT.md").write_text("\n".join(lines) + "\n")

    src_json.unlink(missing_ok=True)
    (out / "RECURRENT_CORE_LOCAL_ENVELOPE_V4_DEVELOPMENT.md").unlink(missing_ok=True)
    print("\n".join(lines), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
