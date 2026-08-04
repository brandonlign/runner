from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

SOURCE_PARTS = Path("dual_coherence_rescue_stage0/source_parts")
OUTPUT = Path("output")
EXPECTED_SHA256 = "d03c5013e0e75bea7c4ddf896a0f3c0fa108df1bff192e836144674287840dbc"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    parts = sorted(SOURCE_PARTS.glob("part*.b64"))
    encoded = "".join("".join(part.read_text().split()) for part in parts)
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"unexpected decoded harness SHA-256: {digest}")

    decoded_path = OUTPUT / "decoded_dual_coherence_harness.py"
    decoded_path.write_bytes(source)
    tree = ast.parse(source.decode("utf-8"))
    functions: list[dict[str, object]] = []
    classes: list[dict[str, object]] = []
    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "signature": ast.unparse(node.args),
                    "line": node.lineno,
                    "end_line": node.end_lineno,
                }
            )
        elif isinstance(node, ast.ClassDef):
            methods = [
                {
                    "name": child.name,
                    "signature": ast.unparse(child.args),
                    "line": child.lineno,
                    "end_line": child.end_lineno,
                }
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({"name": node.name, "line": node.lineno, "methods": methods})

    summary = {
        "decoded_sha256": digest,
        "decoded_bytes": len(source),
        "parts": [part.name for part in parts],
        "imports": imports,
        "functions": functions,
        "classes": classes,
    }
    (OUTPUT / "harness_ast.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Multiscale subset scan harness audit",
        "",
        "This is a no-score interface audit of the previously frozen odd-year development harness.",
        "",
        f"- decoded source SHA-256: `{digest}`",
        f"- decoded source bytes: {len(source)}",
        f"- top-level functions: {len(functions)}",
        f"- classes: {len(classes)}",
        "",
        "## Functions",
        "",
    ]
    for item in functions:
        lines.append(f"- `{item['name']}({item['signature']})` — lines {item['line']}–{item['end_line']}")
    (OUTPUT / "HARNESS_AUDIT.md").write_text("\n".join(lines) + "\n")
    print((OUTPUT / "HARNESS_AUDIT.md").read_text())


if __name__ == "__main__":
    main()
