from __future__ import annotations

import ast
import base64
import gzip
import hashlib
from pathlib import Path

FROZEN_SHA256 = "806e6577b19f5771d58531b036fdb991526999aa6d83795d3e5c864d7c2e8a15"
parts = sorted(Path("orbittrace_recurrent_core_expansion_r1/source_parts").glob("part*.b64"))
assert [p.name for p in parts] == ["part00.b64"]
raw = gzip.decompress(base64.b64decode("".join("".join(p.read_text().split()) for p in parts), validate=True))
assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA256
source = raw.decode()
tree = ast.parse(source)
lines = source.splitlines()

wanted = {"component_orbit_medoid", "expand_memberships", "scalar_dsh"}
found = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in wanted:
        found[node.name] = (node.lineno, node.end_lineno)
assert set(found) == wanted, found

print("PASS_R1_HOTSPOT_SOURCE_STATIC_AUDIT")
print("scientific_source_executed=false")
print("catalogue_access=false")
print("event_row_access=false")
print("orbittrace_target_access=false")
for name in ("scalar_dsh", "component_orbit_medoid", "expand_memberships"):
    start, end = found[name]
    print(f"R1_HOTSPOT_BEGIN {name} lines={start}-{end}")
    for lineno in range(start, end + 1):
        print(f"{lineno:04d}: {lines[lineno-1]}")
    print(f"R1_HOTSPOT_END {name}")
