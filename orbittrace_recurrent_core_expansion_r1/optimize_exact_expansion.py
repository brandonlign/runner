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

for token in (
    'scan_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}',
    'medoid_cache = {cid: component_orbit_medoid(c, orbit_by_id, dsh) for cid, c in component_by_id.items()}',
    'for family in families:',
    'for event in local_events:',
    'geom = float(support.centroid_distance(event_center(event), comp["centroid"], base))',
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

    # Frozen `scan_lookup` is intentionally omitted: static inspection proves it is
    # assigned but never read anywhere in expand_memberships.
    sol_bins: dict[int, dict[int, list[dict[str, Any]]]] = {year: defaultdict(list) for year in YEARS}
    for year in YEARS:
        for event in scan_by_year[year]:
            sol_bins[year][int(math.floor(float(event["sol"]))) % 360].append(event)

    # Exact dead-work elimination only. Frozen-source static proof establishes that
    # medoid_cache is read only as medoid_cache[str(partner["component_id"])], with
    # partner bound by `for partner in comps` and comps constructed solely from the
    # current recurrent family's component_ids.
    active_component_ids = sorted({str(cid) for family in families for cid in family["component_ids"]})
    require(set(active_component_ids).issubset(component_by_id), "family references unknown component")
    medoid_cache: dict[str, dict[str, Any] | None] = {}
    print(
        f"R1_EXPANSION_START families={len(families)} components_total={len(components)} "
        f"components_active={len(active_component_ids)} components_skipped={len(components)-len(active_component_ids)} "
        f"seeds={len(all_seed_ids)}",
        flush=True,
    )
    for medoid_i, cid in enumerate(active_component_ids, 1):
        component = component_by_id[cid]
        seed_count = len(component.get("event_ids", []))
        if seed_count >= 100:
            print(
                f"R1_MEDOID_LARGE_BEGIN {medoid_i}/{len(active_component_ids)} "
                f"component={cid} seed_events={seed_count} elapsed_s={_time.perf_counter()-_t0:.1f}",
                flush=True,
            )
        medoid_cache[cid] = component_orbit_medoid(component, orbit_by_id, dsh)
        if seed_count >= 100:
            medoid = medoid_cache[cid]
            valid_count = 0 if medoid is None else int(medoid["valid_orbit_count"])
            print(
                f"R1_MEDOID_LARGE_DONE {medoid_i}/{len(active_component_ids)} "
                f"component={cid} valid_orbits={valid_count} elapsed_s={_time.perf_counter()-_t0:.1f}",
                flush=True,
            )
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

    # Exact memoization of the unchanged frozen scalar_dsh call. The cache key uses
    # the candidate event ID plus the identity of the exact orbit dict returned by
    # component_orbit_medoid, so it cannot conflate different medoid orbit objects.
    dsh_cache: dict[tuple[str, int], float] = {}
    dsh_cache_hits = 0

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
            for event in local_events:
                eid = str(event["id"])
                if eid in all_seed_ids or eid not in orbit_by_id:
                    continue
                if abs(float(base.wrap180(float(event["sol"]) - float(comp["centroid"]["sol"])))) > 6.0 + 1e-12:
                    continue
                # Preserve the exact frozen geometry expression byte-for-byte.
                geom = float(support.centroid_distance(event_center(event), comp["centroid"], base))
                if geom > FAMILY_LINK_RADIUS + 1e-12:
                    continue
                geometry_candidates += 1
                best_phys: tuple[float, str, dict[str, Any]] | None = None
                for partner_cid, medoid in partner_medoid_rows:
                    cache_key = (eid, id(medoid["orbit"]))
                    if cache_key in dsh_cache:
                        distance = dsh_cache[cache_key]
                        dsh_cache_hits += 1
                    else:
                        # Preserve the exact frozen scalar D_SH implementation for every cache miss.
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
                f"physical_pass={physical_passes} dsh_cache_entries={len(dsh_cache)} "
                f"dsh_cache_hits={dsh_cache_hits} elapsed_s={_time.perf_counter()-_t0:.1f}",
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
        f"dsh_cache_entries={len(dsh_cache)} dsh_cache_hits={dsh_cache_hits} "
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
    import time as _time
    sample_n = min(int(_os.environ.get("R1_EQUIVALENCE_SAMPLE_FAMILIES", "8")), len(families))
    require(sample_n >= 1, "R1 equivalence sample must contain at least one family")
    full_active_component_ids = {str(cid) for family in families for cid in family["component_ids"]}
    sample_families = copy.deepcopy(families[:sample_n])
    sample_component_ids = {str(cid) for family in sample_families for cid in family["component_ids"]}
    sample_components = [c for c in components if str(c["component_id"]) in sample_component_ids]

    # Include one real target-excluded unreferenced component when available. The
    # frozen reference computes its medoid; the optimized function must skip it and
    # still return an exactly equal complete result.
    extras = [c for c in components if str(c["component_id"]) not in sample_component_ids]
    valid_extras = [c for c in extras if len(c.get("event_ids", [])) >= MIN_VALID_PARTNER_ORBITS]
    extra = min(valid_extras or extras, key=lambda c: (len(c.get("event_ids", [])), str(c["component_id"]))) if extras else None
    if extra is not None:
        sample_components.append(extra)
    extra_count = int(extra is not None)

    print(
        f"R1_EQUIVALENCE_CONTEXT families_total={len(families)} components_total={len(components)} "
        f"components_active={len(full_active_component_ids)} components_skippable={len(components)-len(full_active_component_ids)} "
        f"sample_families={sample_n} sample_components={len(sample_components)} "
        f"unreferenced_test_components={extra_count}",
        flush=True,
    )

    _reference_t0 = _time.perf_counter()
    reference_result = _expand_memberships_reference(
        copy.deepcopy(sample_families), copy.deepcopy(sample_components), scan_by_year,
        orbit_by_id, order, support, base, dsh,
    )
    reference_s = _time.perf_counter() - _reference_t0
    print(f"R1_EQUIVALENCE_REFERENCE_COMPLETE elapsed_s={reference_s:.3f}", flush=True)

    _optimized_t0 = _time.perf_counter()
    optimized_result = _expand_memberships_optimized_core(
        copy.deepcopy(sample_families), copy.deepcopy(sample_components), scan_by_year,
        orbit_by_id, order, support, base, dsh,
    )
    optimized_s = _time.perf_counter() - _optimized_t0
    require(reference_result == optimized_result, "optimized R1 expansion differs from frozen reference on bounded deterministic sample")
    speedup = reference_s / optimized_s if optimized_s > 0 else float("inf")
    print(
        f"PASS_R1_BOUNDED_EXACT_EQUIVALENCE families={sample_n} components={len(sample_components)} "
        f"unreferenced_test_components={extra_count} reference_s={reference_s:.3f} "
        f"optimized_s={optimized_s:.3f} speedup_x={speedup:.3f}",
        flush=True,
    )
    if _os.environ.get("R1_EQUIVALENCE_ONLY") == "1":
        Path("output").mkdir(exist_ok=True)
        Path("output/PASS_R1_BOUNDED_EXACT_EQUIVALENCE.txt").write_text(
            f"families={sample_n}\ncomponents={len(sample_components)}\n"
            f"unreferenced_test_components={extra_count}\nreference_s={reference_s:.6f}\n"
            f"optimized_s={optimized_s:.6f}\nspeedup_x={speedup:.6f}\n"
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
        "remove frozen scan_lookup assignment proven unused within expand_memberships",
        "memoize unchanged scalar D_SH by candidate event id and exact medoid orbit object identity",
        "progress and timing logging only",
    ],
    "old_expand_sha256": hashlib.sha256(old.encode()).hexdigest(),
    "new_expand_sha256": hashlib.sha256((reference + "\n\n" + optimized).encode()).hexdigest(),
    "bounded_equivalence_sample_families_default": 8,
    "bounded_equivalence_includes_real_unreferenced_component_when_available": True,
    "numerical_approximation": False,
    "geometry_prefilter_added": False,
    "event_center_memoization": False,
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
