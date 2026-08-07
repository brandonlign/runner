#!/usr/bin/env python3
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED_SUPPORT_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
FUNCTIONS = (
    "parse_catalogue",
    "scan_year",
    "component_records",
    "build_families",
    "evaluate_panel",
    "evaluate_families",
    "load_sources",
)


def decode_parts(root: Path) -> bytes:
    paths = sorted(root.glob("part*.b64"))
    if [p.name for p in paths] != [f"part{i:02d}.b64" for i in range(4)]:
        raise RuntimeError(f"unexpected parts: {[p.name for p in paths]}")
    encoded = "".join("".join(p.read_text(encoding="ascii").split()) for p in paths)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def literal_assignments(tree: ast.Module) -> dict[str, object]:
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            out[node.targets[0].id] = ast.literal_eval(node.value)
        except Exception:
            pass
    return out


def main() -> None:
    output = Path("output")
    output.mkdir(exist_ok=True)
    source = decode_parts(Path("orbittrace_fixed4_support_wrapper_development/source_parts"))
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_SUPPORT_SHA256:
        raise RuntimeError(f"support source digest changed: {digest}")
    text = source.decode("utf-8")
    tree = ast.parse(text)
    constants = literal_assignments(tree)
    selected_constants = {
        key: constants.get(key)
        for key in (
            "YEARS", "BLIND_LOW", "BLIND_HIGH", "MONTH_KEYS", "MIN_FAMILY_YEARS",
            "FAMILY_LINK_RADIUS", "WINDOW_SIZE", "WINDOW_WIDTH_DEG", "WINDOW_STEP_DEG",
            "MIN_COMPONENT_EVENTS", "MIN_COMPONENT_ANCHORS"
        )
    }
    funcs = {}
    excerpts = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FUNCTIONS:
            segment = ast.get_source_segment(text, node)
            funcs[node.name] = {
                "args": [a.arg for a in node.args.args],
                "first_lineno": node.lineno,
                "last_lineno": getattr(node, "end_lineno", None),
            }
            excerpts.append(segment)
    result = {
        "verdict": "PASS_MULTIPLICITY_V5_SUPPORT_SOURCE_AUDIT",
        "support_sha256": digest,
        "constants": selected_constants,
        "functions": funcs,
        "catalogue_access": False,
        "target_information_access": False,
    }
    (output / "support_source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "support_source_excerpt.py").write_text("\n\n\n".join(excerpts) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("SUPPORT_SOURCE_EXCERPT_BEGIN")
    print("\n\n\n".join(excerpts))
    print("SUPPORT_SOURCE_EXCERPT_END")


if __name__ == "__main__":
    main()
