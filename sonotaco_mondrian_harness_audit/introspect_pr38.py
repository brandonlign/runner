#!/usr/bin/env python3
"""Statically decode and inspect the exact PR #38 scorer without importing it."""

from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
PART_HASHES = {
    "part00.b64": "6b5a5a449f381b6d47ecde6981ff301aee47927de1763cd124ca165713230104",
    "part01.b64": "3460d412c23e45b1fa729af769a192ea11554d278b49cd38bb13c12e4496fb79",
    "part02.b64": "f2853f0e5c3f6e0b8d127d919f2d7bf53ca284e6f33ee065ebea81e4477582ad",
    "part03.b64": "9104365b8e786e3e0c33aa4e1badd01c96c02404879898221694b1e07a134b42",
}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def annotation(node: ast.AST | None) -> str | None:
    return ast.unparse(node) if node is not None else None


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
    parameters = []
    for arg, default in zip(positional, defaults, strict=True):
        parameters.append(
            {
                "name": arg.arg,
                "kind": "positional_only" if arg in node.args.posonlyargs else "positional_or_keyword",
                "annotation": annotation(arg.annotation),
                "default": ast.unparse(default) if default is not None else None,
            }
        )
    if node.args.vararg is not None:
        parameters.append(
            {
                "name": node.args.vararg.arg,
                "kind": "var_positional",
                "annotation": annotation(node.args.vararg.annotation),
                "default": None,
            }
        )
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
        parameters.append(
            {
                "name": arg.arg,
                "kind": "keyword_only",
                "annotation": annotation(arg.annotation),
                "default": ast.unparse(default) if default is not None else None,
            }
        )
    if node.args.kwarg is not None:
        parameters.append(
            {
                "name": node.args.kwarg.arg,
                "kind": "var_keyword",
                "annotation": annotation(node.args.kwarg.annotation),
                "default": None,
            }
        )
    return {"parameters": parameters, "returns": annotation(node.returns)}


def called_names(node: ast.AST) -> list[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        target = child.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            pieces = [target.attr]
            value = target.value
            while isinstance(value, ast.Attribute):
                pieces.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                pieces.append(value.id)
            names.add(".".join(reversed(pieces)))
    return sorted(names)


def main() -> None:
    root = Path("mondrian_clique_development/source_parts_v2")
    parts = sorted(root.glob("part*.b64"))
    expected_names = list(PART_HASHES)
    if [part.name for part in parts] != expected_names:
        raise RuntimeError(f"unexpected source parts: {[part.name for part in parts]}")

    encoded_parts: list[str] = []
    observed_parts: dict[str, str] = {}
    for part in parts:
        payload = part.read_bytes()
        observed = digest(payload)
        observed_parts[part.name] = observed
        if observed != PART_HASHES[part.name]:
            raise RuntimeError(f"source part mismatch for {part.name}: {observed}")
        encoded_parts.append("".join(payload.decode("ascii").split()))

    source = gzip.decompress(base64.b64decode("".join(encoded_parts), validate=True))
    source_hash = digest(source)
    if source_hash != SOURCE_SHA256:
        raise RuntimeError(f"decoded source mismatch: {source_hash}")

    text = source.decode("utf-8")
    tree = ast.parse(text)
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    (output / "pr38_mondrian_scorer.py").write_bytes(source)

    imports: list[str] = []
    assignments: list[dict] = []
    functions: list[dict] = []
    classes: list[dict] = []
    cli_calls: list[dict] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target_nodes = node.targets if isinstance(node, ast.Assign) else [node.target]
            targets = [ast.unparse(target) for target in target_nodes]
            value_node = node.value
            assignments.append(
                {
                    "targets": targets,
                    "value": ast.unparse(value_node) if value_node is not None else None,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "signature": signature(node),
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "calls": called_names(node),
                    "source": ast.get_source_segment(text, node),
                }
            )
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(
                        {
                            "name": child.name,
                            "signature": signature(child),
                            "line_start": child.lineno,
                            "line_end": child.end_lineno,
                            "calls": called_names(child),
                        }
                    )
            classes.append(
                {
                    "name": node.name,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "methods": methods,
                    "source": ast.get_source_segment(text, node),
                }
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"add_argument", "ArgumentParser"}:
            continue
        cli_calls.append(
            {
                "call": ast.unparse(node),
                "line_start": node.lineno,
                "line_end": node.end_lineno,
            }
        )

    audit = {
        "source_sha256": source_hash,
        "source_bytes": len(source),
        "source_lines": len(text.splitlines()),
        "part_sha256": observed_parts,
        "imports": imports,
        "module_assignments": assignments,
        "classes": classes,
        "functions": functions,
        "cli_calls": cli_calls,
    }
    (output / "pr38_harness_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# PR #38 scorer static harness audit",
        "",
        f"- decoded source SHA-256: `{source_hash}`",
        f"- source bytes: **{len(source):,}**",
        f"- source lines: **{len(text.splitlines()):,}**",
        f"- module functions: **{len(functions)}**",
        f"- classes: **{len(classes)}**",
        "",
        "## Function interfaces",
        "",
    ]
    for item in functions:
        params = ", ".join(parameter["name"] for parameter in item["signature"]["parameters"])
        lines.append(
            f"- `{item['name']}({params})` — lines {item['line_start']}–{item['line_end']}"
        )
    (output / "PR38_HARNESS_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
