#!/usr/bin/env python3
"""Decode and statically inspect the exact PR #14 baseline module without importing it."""

from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

PAYLOAD = Path("real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64")
PAYLOAD_SHA256 = "2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2"
SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return ast.unparse(node.args)


def called_names(node: ast.AST) -> list[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        target = child.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(ast.unparse(target))
    return sorted(names)


def main() -> None:
    payload = PAYLOAD.read_bytes()
    payload_hash = digest(payload)
    if payload_hash != PAYLOAD_SHA256:
        raise RuntimeError(f"baseline payload mismatch: {payload_hash}")
    encoded = "".join(payload.decode("ascii").split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    source_hash = digest(source)
    if source_hash != SOURCE_SHA256:
        raise RuntimeError(f"baseline source mismatch: {source_hash}")

    text = source.decode("utf-8")
    tree = ast.parse(text)
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    (output / "pr14_baseline.py").write_bytes(source)

    imports: list[str] = []
    assignments: list[dict] = []
    functions: list[dict] = []
    classes: list[dict] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assignments.append(
                {
                    "targets": [ast.unparse(target) for target in targets],
                    "value": ast.unparse(node.value) if node.value is not None else None,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "args": signature(node),
                    "returns": ast.unparse(node.returns) if node.returns is not None else None,
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
                            "args": signature(child),
                            "returns": ast.unparse(child.returns) if child.returns is not None else None,
                            "line_start": child.lineno,
                            "line_end": child.end_lineno,
                            "calls": called_names(child),
                            "source": ast.get_source_segment(text, child),
                        }
                    )
            classes.append(
                {
                    "name": node.name,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "line_start": node.lineno,
                    "line_end": node.end_lineno,
                    "methods": methods,
                    "source": ast.get_source_segment(text, node),
                }
            )

    audit = {
        "payload_sha256": payload_hash,
        "source_sha256": source_hash,
        "source_bytes": len(source),
        "source_lines": len(text.splitlines()),
        "imports": imports,
        "module_assignments": assignments,
        "functions": functions,
        "classes": classes,
    }
    (output / "pr14_baseline_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# PR #14 baseline static interface audit",
        "",
        f"- payload SHA-256: `{payload_hash}`",
        f"- decoded source SHA-256: `{source_hash}`",
        f"- source bytes: **{len(source):,}**",
        f"- source lines: **{len(text.splitlines()):,}**",
        f"- module functions: **{len(functions)}**",
        f"- classes: **{len(classes)}**",
        "",
        "## Module functions",
        "",
    ]
    for item in functions:
        lines.append(f"- `{item['name']}({item['args']})` — lines {item['line_start']}–{item['line_end']}")
    lines.extend(["", "## Classes", ""])
    for item in classes:
        lines.append(f"- `{item['name']}` — lines {item['line_start']}–{item['line_end']}")
        for method in item["methods"]:
            lines.append(f"  - `{method['name']}({method['args']})` — lines {method['line_start']}–{method['line_end']}")
    (output / "PR14_BASELINE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
