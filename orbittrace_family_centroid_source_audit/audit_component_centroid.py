#!/usr/bin/env python3
"""Source-only audit of frozen component centroid construction; no catalogue access."""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

SUPPORT_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
ROOT = Path("orbittrace_fixed4_support_wrapper_development/source_parts")
OUT = Path("output")


def decode_parts(root: Path) -> bytes:
    paths = sorted(root.glob("part*.b64"))
    if not paths:
        raise RuntimeError("support source parts missing")
    encoded = "".join("".join(p.read_text(encoding="ascii").split()) for p in paths)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"missing function {name}")


def called_names(node: ast.AST) -> list[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        fn = child.func
        if isinstance(fn, ast.Name):
            names.add(fn.id)
        elif isinstance(fn, ast.Attribute):
            names.add(fn.attr)
    return sorted(names)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    source = decode_parts(ROOT)
    digest = hashlib.sha256(source).hexdigest()
    if digest != SUPPORT_SHA256:
        raise RuntimeError(f"support source changed: {digest}")
    text = source.decode("utf-8")
    tree = ast.parse(text)
    target = function_node(tree, "component_records")
    target_source = ast.get_source_segment(text, target)
    if not target_source:
        raise RuntimeError("could not recover component_records source")
    calls = called_names(target)
    helpers: dict[str, str] = {}
    for name in calls:
        try:
            node = function_node(tree, name)
        except RuntimeError:
            continue
        segment = ast.get_source_segment(text, node)
        if segment:
            helpers[name] = segment
    result = {
        "verdict": "PASS_COMPONENT_CENTROID_SOURCE_AUDIT",
        "support_source_sha256": digest,
        "catalogue_access": False,
        "scientific_value_access": False,
        "target_information_access": False,
        "component_records_arguments": [a.arg for a in target.args.args],
        "component_records_called_names": calls,
        "helper_functions_recovered": sorted(helpers),
    }
    (OUT / "component_centroid_source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (OUT / "component_records_source.py").write_text(target_source + "\n")
    (OUT / "component_centroid_helpers.txt").write_text(
        "\n\n".join(f"### {name}\n{helpers[name]}" for name in sorted(helpers)) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print("COMPONENT_RECORDS_SOURCE_BEGIN")
    print(target_source)
    print("COMPONENT_RECORDS_SOURCE_END")
    for name in sorted(helpers):
        print(f"HELPER_{name}_BEGIN")
        print(helpers[name])
        print(f"HELPER_{name}_END")


if __name__ == "__main__":
    main()
