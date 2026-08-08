from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: optimize_exact_expansion.py PATH_TO_REPAIRED_RUN_DEVELOPMENT")

path = Path(sys.argv[1])
text = path.read_text()
tree = ast.parse(text)
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "expand_memberships"]
assert len(funcs) == 1, len(funcs)
node = funcs[0]
lines = text.splitlines(keepends=True)
start = sum(len(x) for x in lines[: node.lineno - 1])
end = sum(len(x) for x in lines[: node.end_lineno])
old = text[start:end]

# The parser/comparator repairs occur earlier in the file; the R1 expansion
# function itself must still be the frozen implementation shape audited above.
for token in (
    'medoid_cache = {cid: component_orbit_medoid(c, orbit_by_id, dsh) for cid, c in component_by_id.items()}',
    'for family in families:',
    'for event in local_events:',
    'distance = scalar_dsh(orbit_by_id[eid], medoid["orbit"], dsh)',
    'assignment_rule',
    'new_members_never_become_seeds',
    'rankings_unchanged',
):
    assert token in old, token

reference = old.replace("def expand_memberships(", "def _expand_memberships_reference(", 1)

optimized = r'''
def _expand_memberships_optimized_core(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    orbit_by_id: dict[str, dict[str, float]],
    order: list[str],
    support: Any,
    base: Any,
    dsh: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import time as _time
    _t0 = _time.perf_counter()
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")
    family_rank = {fid: i for i, fid in enumerate(order, 1)}
    all_seed_ids = set().union(*(set(map(str, f["event_ids"])) for f in families))
    sol_bins: dict[int, dict[int, list[dict[str, Any]]]] = {year: defaultdict(list) for year in YEARS}
    for year in YEARS:
        for event in scan_by_year[year]:
            sol_bins[year][int(math.floor(float(event["sol"]))) % 360].append(event)

    # Exact dead-work elimination: only components referenced by recurrent families
    # can ever be used as `comp` or `partner` below. Unreferenced components cannot
    # affect any R1 proposal, assignment, rank, or gate.
    active_component_ids = sorted({str(cid) for family in families for cid in family["component_ids"]})
    require(set(active_component_ids).issubset(component_by_id), "family references unknown component")
    medoid_cache: dict[str, dict[str, Any] | None] = {}
    print(
        f"R1_EXPANSION_START families={len(families)} components_total={len(components)} "
        f"components_active={len(active_component_ids)} seeds={len(all_seed_ids)}",
        flush=True,
    )
    for medoid_i, cid in enumerate(active_component_ids, 1):
        medoid_cache[cid] = component_orbit_medoid(component_by_id[cid], orbit_by_id, dsh)
        if medoid_i % 25 == 0 or medoid_i == len(active_component_ids):
            print(
                f"R1_MEDOID_PROGRESS {medoid_i}/{len(active_component_ids)} "
                f"elapsed_s={_time.perf_counter()-_t0:.1f}",
                flush=True,
            )

    proposals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    component_attempts = 0
    component_with_partner = 0
    geometry_candidates = 0
    physical_passes = 0
    event_center_cache: dict[str, dict[str, float]] = {}
    dsh_cache: dict[tuple[str, str], float] = {}

    for family_i, family in enumerate(families, 1):
        fid = str(family["family_id"])
        comps = [component_by_id[str(cid)] for cid in family["component_ids"]]
        for comp in comps:
            component_attempts += 1
            year = int(comp["year"])
            partner_medoid_rows: list[tuple[str, dict[str, Any]]] = []
            for partner in comps:
                if int(partner["year"]) == year:
                    continue
                if float(support.centroid_distance(comp["centroid"], partner["centroid"], base)) > FAMILY_LINK_RADIUS + 1e-12:
                    continue
                medoid = medoid_cache[str(partner["component_id"])]
                if medoid is not None:
                    partner_medoid_rows.append((str(partner["component_id"]), medoid))
            if not partner_medoid_rows:
                continue
            component_with_partner += 1

            center_bin = int(math.floor(float(comp["centroid"]["sol"]))) % 360
            local_events: list[dict[str, Any]] = []
            for offset in range(-7, 8):
                local_events.extend(sol_bins[year].get((center_bin + offset) % 360, []))
            comp_centroid = comp["centroid"]
            for event in local_events:
                eid = str(event["id"])
                if eid in all_seed_ids or eid not in orbit_by_id:
                    continue
                if abs(float(base.wrap180(float(event["sol"]) - float(comp_centroid["sol"])))) > 6.0 + 1e-12:
                    continue
                center = event_center_cache.get(eid)
                if center is None:
                    center = event_center(event)
                    event_center_cache[eid] = center

                # Exact necessary-condition short circuits for the same Euclidean
                # geometry metric. If one normalized coordinate alone exceeds the
                # frozen radius, the full norm must exceed it too. Non-finite values
                # fall through to the original exact distance function.
                d_lat = (float(center["ecl_lat"]) - float(comp_centroid["ecl_lat"])) / 2.0
                if math.isfinite(d_lat) and abs(d_lat) > FAMILY_LINK_RADIUS + 1e-12:
                    continue
                d_vg = (float(center["vg"]) - float(comp_centroid["vg"])) / 2.0
                if math.isfinite(d_vg) and abs(d_vg) > FAMILY_LINK_RADIUS + 1e-12:
                    continue
                d_lon = float(base.wrap180(float(center["sun_lon"]) - float(comp_centroid["sun_lon"])))
                d_lon *= math.cos(math.radians(0.5 * (float(center["ecl_lat"]) + float(comp_centroid["ecl_lat"])))) / 2.0
                if math.isfinite(d_lon) and abs(d_lon) > FAMILY_LINK_RADIUS + 1e-12:
                    continue

                geom = float(support.centroid_distance(center, comp_centroid, base))
                if geom > FAMILY_LINK_RADIUS + 1e-12:
                    continue
                geometry_candidates += 1
                best_phys: tuple[float, str, dict[str, Any]] | None = None
                for partner_cid, medoid in partner_medoid_rows:
                    medoid_eid = str(medoid["event_id"])
                    cache_key = (eid, medoid_eid)
                    distance = dsh_cache.get(cache_key)
                    if distance is None:
                        distance = scalar_dsh(orbit_by_id[eid], medoid["orbit"], dsh)
                        dsh_cache[cache_key] = distance
                    row = (distance, partner_cid, medoid)
                    if best_phys is None or (row[0], row[1], row[2]["event_id"]) < (best_phys[0], best_phys[1], best_phys[2]["event_id"]):
                        best_phys = row
                assert best_phys is not None
                if best_phys[0] > DSH_THRESHOLD + 1e-15:
                    continue
                physical_passes += 1
                proposals[eid].append({
                    "event_id": eid,
                    "family_id": fid,
                    "family_rank": family_rank[fid],
                    "year": year,
                    "component_id": str(comp["component_id"]),
                    "partner_component_id": best_phys[1],
                    "partner_medoid_event_id": str(best_phys[2]["event_id"]),
                    "dsh": float(best_phys[0]),
                    "geometry_distance": geom,
                })
        if family_i % 10 == 0 or family_i == len(families):
            print(
                f"R1_EXPANSION_PROGRESS families={family_i}/{len(families)} "
                f"components={component_attempts} geom_pass={geometry_candidates} "
                f"physical_pass={physical_passes} dsh_cache={len(dsh_cache)} "
                f"elapsed_s={_time.perf_counter()-_t0:.1f}",
                flush=True,
            )

    assignments: dict[str, dict[str, Any]] = {}
    for eid, rows in proposals.items():
        assignments[eid] = min(rows, key=lambda r: (r["dsh"], r["geometry_distance"], r["family_rank"], r["family_id"], r["component_id"]))

    expanded = copy.deepcopy(families)
    expanded_by_id = {str(f["family_id"]): f for f in expanded}
    additions_by_family: dict[str, list[str]] = defaultdict(list)
    for eid, row in assignments.items():
        additions_by_family[str(row["family_id"])].append(eid)
    for fid, family in expanded_by_id.items():
        original = set(map(str, family["event_ids"]))
        additions = set(additions_by_family.get(fid, []))
        require(not (original & additions), "seed event was treated as expansion")
        family["event_ids"] = sorted(original | additions)
        family["event_count"] = len(family["event_ids"])
        family["r1_added_event_ids"] = sorted(additions)
        family["r1_added_event_count"] = len(additions)

    require(all(set(map(str, orig["event_ids"])).issubset(set(map(str, expanded_by_id[str(orig["family_id"])]["event_ids"]))) for orig in families), "R1 removed a frozen seed event")
    print(
        f"R1_EXPANSION_COMPLETE assigned={len(assignments)} proposals={len(proposals)} "
        f"elapsed_s={_time.perf_counter()-_t0:.1f}",
        flush=True,
    )
    return expanded, {
        "component_attempts": component_attempts,
        "components_with_valid_direct_partner_medoid": component_with_partner,
        "geometry_candidate_tests": geometry_candidates,
        "physical_pass_proposals": physical_passes,
        "unique_nonseed_events_proposed": len(proposals),
        "unique_nonseed_events_assigned": len(assignments),
        "families_gaining_members": sum(bool(v) for v in additions_by_family.values()),
        "total_added_members": len(assignments),
        "conflicted_nonseed_events": sum(len(v) > 1 for v in proposals.values()),
        "assignment_rule": "minimum D_SH, then geometry distance, then frozen v8 rank, family id, component id",
        "new_members_never_become_seeds": True,
        "seed_events_never_reassigned": True,
        "rankings_unchanged": True,
    }


def expand_memberships(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    orbit_by_id: dict[str, dict[str, float]],
    order: list[str],
    support: Any,
    base: Any,
    dsh: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import os as _os
    sample_n = min(int(_os.environ.get("R1_EQUIVALENCE_SAMPLE_FAMILIES", "8")), len(families))
    require(sample_n >= 1, "R1 equivalence sample must contain at least one family")
    sample_families = copy.deepcopy(families[:sample_n])
    sample_component_ids = {str(cid) for family in sample_families for cid in family["component_ids"]}
    sample_components = [c for c in components if str(c["component_id"]) in sample_component_ids]
    reference = _expand_memberships_reference(
        copy.deepcopy(sample_families), copy.deepcopy(sample_components), scan_by_year,
        orbit_by_id, order, support, base, dsh,
    )
    optimized = _expand_memberships_optimized_core(
        copy.deepcopy(sample_families), copy.deepcopy(sample_components), scan_by_year,
        orbit_by_id, order, support, base, dsh,
    )
    require(reference == optimized, "optimized R1 expansion differs from frozen reference on bounded deterministic sample")
    print(
        f"PASS_R1_BOUNDED_EXACT_EQUIVALENCE families={sample_n} components={len(sample_components)}",
        flush=True,
    )
    if _os.environ.get("R1_EQUIVALENCE_ONLY") == "1":
        Path("output").mkdir(exist_ok=True)
        Path("output/PASS_R1_BOUNDED_EXACT_EQUIVALENCE.txt").write_text(
            f"families={sample_n}\ncomponents={len(sample_components)}\n"
        )
        raise SystemExit(42)
    return _expand_memberships_optimized_core(
        families, components, scan_by_year, orbit_by_id, order, support, base, dsh,
    )
'''.lstrip("\n")

patched = text[:start] + reference + "\n\n" + optimized + text[end:]
ast.parse(patched)
path.write_text(patched)

out = Path("output")
out.mkdir(exist_ok=True)
record = {
    "optimization_scope": [
        "skip medoid construction for components not referenced by recurrent families",
        "cache event_center by event id",
        "cache exact scalar D_SH by event id and partner medoid event id",
        "exact necessary-condition short-circuits for latitude, speed and longitude geometry terms",
        "progress logging only",
    ],
    "old_expand_sha256": hashlib.sha256(old.encode()).hexdigest(),
    "new_expand_sha256": hashlib.sha256((reference + "\n\n" + optimized).encode()).hexdigest(),
    "bounded_equivalence_sample_families_default": 8,
    "numerical_approximation": False,
    "scientific_rule_changed": False,
    "distance_definition_changed": False,
    "dsh_definition_changed": False,
    "medoid_definition_changed": False,
    "conflict_resolution_changed": False,
    "ranking_changed": False,
    "promotion_gate_changed": False,
}
(out / "r1_exact_performance_optimization.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
