from __future__ import annotations

import ast
import base64
import gzip
import hashlib
from pathlib import Path

parts_dir = Path("orbittrace_fixed4_support_wrapper_development/source_parts")
parts = sorted(parts_dir.glob("part*.b64"))
assert parts, f"no support source parts in {parts_dir}"
raw = gzip.decompress(base64.b64decode("".join("".join(p.read_text().split()) for p in parts), validate=True))
source = raw.decode()
tree = ast.parse(source)
lines = source.splitlines()

wanted = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in {"centroid_distance", "event_center"}:
        wanted[node.name] = (node.lineno, node.end_lineno)

print("PASS_R1_SUPPORT_GEOMETRY_STATIC_AUDIT")
print(f"support_source_sha256={hashlib.sha256(raw).hexdigest()}")
print("scientific_source_executed=false")
print("catalogue_access=false")
print("event_row_access=false")
print("orbittrace_target_access=false")
for name, (start, end) in sorted(wanted.items()):
    print(f"R1_SUPPORT_BEGIN {name} lines={start}-{end}")
    for lineno in range(start, end + 1):
        print(f"{lineno:04d}: {lines[lineno-1]}")
    print(f"R1_SUPPORT_END {name}")
assert "centroid_distance" in wanted, wanted
