#!/usr/bin/env python3
"""Source-only audit of the frozen fixed4 cross-year family builder."""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

SUPPORT_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
ROOT = Path("orbittrace_fixed4_support_wrapper_development/source_parts")


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


def literal_assignments(tree: ast.Module) -> dict[str, object]:
    out: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            out[node.targets[0].id] = ast.literal_eval(node.value)
        except Exception:
            pass
    return out


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
    output = Path("output")
    output.mkdir(exist_ok=True)
    source = decode_parts(ROOT)
    digest = hashlib.sha256(source).hexdigest()
    if digest != SUPPORT_SHA256:
        raise RuntimeError(f"support source changed: {digest}")
    text = source.decode("utf-8")
    tree = ast.parse(text)
    constants = literal_assignments(tree)
    target = function_node(tree, "build_families")
    build_source = ast.get_source_segment(text, target)
    if not build_source:
        raise RuntimeError("could not recover build_families source")

    calls = called_names(target)
    helper_sources: dict[str, str] = {}
    for name in calls:
        try:
            node = function_node(tree, name)
        except RuntimeError:
            continue
        segment = ast.get_source_segment(text, node)
        if segment:
            helper_sources[name] = segment

    relevant_constant_names = sorted(
        name for name in constants
        if any(token in name for token in ("FAMILY", "YEAR", "LINK", "RADIUS", "COMPONENT"))
    )
    relevant_constants = {name: constants[name] for name in relevant_constant_names}

    result = {
        "verdict": "PASS_FAMILY_LINK_SOURCE_AUDIT",
        "support_source_sha256": digest,
        "catalogue_access": False,
        "scientific_value_access": False,
        "target_information_access": False,
        "build_families_arguments": [a.arg for a in target.args.args],
        "build_families_called_names": calls,
        "relevant_constants": relevant_constants,
        "helper_functions_recovered": sorted(helper_sources),
    }
    (output / "family_link_source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "build_families_source.py").write_text(build_source + "\n")
    (output / "family_link_helper_sources.txt").write_text(
        "\n\n".join(f"### {name}\n{helper_sources[name]}" for name in sorted(helper_sources)) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print("FAMILY_LINK_BUILD_SOURCE_BEGIN")
    print(build_source)
    print("FAMILY_LINK_BUILD_SOURCE_END")
    if helper_sources:
        print("FAMILY_LINK_HELPERS_BEGIN")
        for name in sorted(helper_sources):
            print(f"### {name}")
            print(helper_sources[name])
        print("FAMILY_LINK_HELPERS_END")


if __name__ == "__main__":
    main()
