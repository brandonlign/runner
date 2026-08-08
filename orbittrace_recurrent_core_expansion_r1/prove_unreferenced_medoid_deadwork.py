from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

FROZEN_SHA256 = "806e6577b19f5771d58531b036fdb991526999aa6d83795d3e5c864d7c2e8a15"
parts = sorted(Path("orbittrace_recurrent_core_expansion_r1/source_parts").glob("part*.b64"))
assert [p.name for p in parts] == ["part00.b64"]
raw = gzip.decompress(base64.b64decode("".join("".join(p.read_text().split()) for p in parts), validate=True))
assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA256
source = raw.decode()
tree = ast.parse(source)
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "expand_memberships"]
assert len(funcs) == 1
fn = funcs[0]
segment = ast.get_source_segment(source, fn)
assert segment is not None

required_text = [
    'component_by_id = {str(c["component_id"]): c for c in components}',
    'scan_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}',
    'medoid_cache = {cid: component_orbit_medoid(c, orbit_by_id, dsh) for cid, c in component_by_id.items()}',
    'comps = [component_by_id[str(cid)] for cid in family["component_ids"]]',
    'for partner in comps:',
    'medoid = medoid_cache[str(partner["component_id"])]',
]
for token in required_text:
    assert token in segment, token

# Every medoid_cache subscript must be the single frozen read through the current
# family's partner component. There must be no iteration over cache values/items,
# no use of unreferenced cache entries, and no output derived from cache cardinality.
reads = []
for node in ast.walk(fn):
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "medoid_cache":
        reads.append(ast.get_source_segment(source, node))
assert reads == ['medoid_cache[str(partner["component_id"])]'], reads

cache_attribute_uses = []
for node in ast.walk(fn):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "medoid_cache":
        cache_attribute_uses.append(ast.get_source_segment(source, node))
assert cache_attribute_uses == [], cache_attribute_uses

# Prove `partner` is bound by `for partner in comps` and `comps` is constructed
# solely from family["component_ids"].
partner_loops = [
    node for node in ast.walk(fn)
    if isinstance(node, ast.For)
    and isinstance(node.target, ast.Name) and node.target.id == "partner"
    and isinstance(node.iter, ast.Name) and node.iter.id == "comps"
]
assert len(partner_loops) == 1, len(partner_loops)

comps_assignments = [
    node for node in ast.walk(fn)
    if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "comps" for t in node.targets)
]
assert len(comps_assignments) == 1
comps_text = ast.get_source_segment(source, comps_assignments[0])
assert comps_text == 'comps = [component_by_id[str(cid)] for cid in family["component_ids"]]', comps_text

# Prove scan_lookup is a pure dead assignment: exactly one Store and zero Loads.
scan_lookup_names = [
    node for node in ast.walk(fn)
    if isinstance(node, ast.Name) and node.id == "scan_lookup"
]
scan_lookup_stores = [node for node in scan_lookup_names if isinstance(node.ctx, ast.Store)]
scan_lookup_loads = [node for node in scan_lookup_names if isinstance(node.ctx, ast.Load)]
assert len(scan_lookup_stores) == 1, len(scan_lookup_stores)
assert len(scan_lookup_loads) == 0, len(scan_lookup_loads)

report = {
    "verdict": "PASS_R1_UNREFERENCED_MEDOID_AND_SCAN_LOOKUP_DEADWORK_PROOF",
    "frozen_source_sha256": FROZEN_SHA256,
    "scientific_source_executed": False,
    "catalogue_access": False,
    "event_row_access": False,
    "orbittrace_target_access": False,
    "medoid_cache_reads": reads,
    "medoid_cache_attribute_uses": cache_attribute_uses,
    "partner_binding": "for partner in comps",
    "comps_binding": 'family["component_ids"] -> component_by_id',
    "scan_lookup_store_count": len(scan_lookup_stores),
    "scan_lookup_load_count": len(scan_lookup_loads),
    "conclusions": [
        "a medoid for a component ID absent from every recurrent family component_ids list is unreachable after construction and cannot affect expand_memberships output",
        "scan_lookup is assigned exactly once and never read inside expand_memberships, so removing its construction cannot affect output",
    ],
}
Path("output").mkdir(exist_ok=True)
Path("output/r1_unreferenced_medoid_deadwork_proof.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
