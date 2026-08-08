from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

FROZEN_SHA256 = "806e6577b19f5771d58531b036fdb991526999aa6d83795d3e5c864d7c2e8a15"
PARTS_DIR = Path("orbittrace_recurrent_core_expansion_r1/source_parts")
OUT = Path("output")
OUT.mkdir(exist_ok=True)

parts = sorted(PARTS_DIR.glob("part*.b64"))
assert [p.name for p in parts] == ["part00.b64"]
raw = gzip.decompress(
    base64.b64decode("".join("".join(p.read_text().split()) for p in parts), validate=True)
)
assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA256
source = raw.decode()
tree = ast.parse(source)

# Static-only audit: never import/execute the scientific source and never access
# catalogues, labels, event rows, target region, or scientific values.
functions = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        loops = sum(isinstance(x, (ast.For, ast.While)) for x in ast.walk(node))
        calls = []
        for x in ast.walk(node):
            if isinstance(x, ast.Call):
                f = x.func
                if isinstance(f, ast.Name):
                    calls.append(f.id)
                elif isinstance(f, ast.Attribute):
                    calls.append(f.attr)
        functions[node.name] = {
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", None),
            "loops": loops,
            "calls": sorted(set(calls)),
        }

keywords = (
    "medoid", "expand", "member", "assign", "conflict", "d_sh", "dsh",
    "evaluat", "recall", "precision", "f1", "multiplicity",
)
interesting = {
    name: meta
    for name, meta in functions.items()
    if any(k in name.lower() for k in keywords)
    or any(any(k in c.lower() for k in keywords) for c in meta["calls"])
}

marker_hits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if "multiplicity-v5 scoring" in node.value or "226/226" in node.value:
            marker_hits.append({"lineno": getattr(node, "lineno", None), "value": node.value})

loop_rank = sorted(
    ({"name": name, **meta} for name, meta in functions.items() if meta["loops"]),
    key=lambda x: (-x["loops"], x["lineno"]),
)

report = {
    "verdict": "PASS_R1_STATIC_PERFORMANCE_AUDIT",
    "frozen_source_sha256": FROZEN_SHA256,
    "scientific_source_executed": False,
    "catalogue_access": False,
    "event_row_access": False,
    "shower_label_access": False,
    "orbittrace_target_access": False,
    "target_region_access": False,
    "function_count": len(functions),
    "marker_hits": marker_hits,
    "interesting_functions": interesting,
    "loop_rank": loop_rank[:40],
}
Path(OUT / "r1_static_performance_audit.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))
