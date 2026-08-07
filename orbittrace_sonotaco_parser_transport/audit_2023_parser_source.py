#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6"
INTERESTING_FUNCTIONS = (
    "parse_sonotaco_2023_events",
    "normalize_label",
    "main",
)


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


def main() -> None:
    source_path = Path("input/run_sonotaco_2023_fixed4_confirmation.py")
    out = Path("output")
    out.mkdir(exist_ok=True)
    payload = source_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"2023 parser source digest mismatch: {digest}")
    text = payload.decode("utf-8")
    tree = ast.parse(text)
    constants = literal_assignments(tree)

    functions = {}
    excerpts = []
    all_functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            all_functions.append(node.name)
            if node.name in INTERESTING_FUNCTIONS or "download" in node.name.lower() or "archive" in node.name.lower() or "parse" in node.name.lower():
                segment = ast.get_source_segment(text, node)
                functions[node.name] = {
                    "args": [a.arg for a in node.args.args],
                    "lineno": node.lineno,
                    "end_lineno": getattr(node, "end_lineno", None),
                }
                if segment:
                    excerpts.append(segment)

    year_tokens = {}
    for token in (
        "2023", "023a", "SNM2023", "sonotaco-2023", "47_087",
        "9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430",
        "3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685",
    ):
        year_tokens[token] = text.count(token)

    result = {
        "verdict": "PASS_SONOTACO_2023_PARSER_SOURCE_AUDIT",
        "source_sha256": digest,
        "catalogue_access": False,
        "scientific_score_access": False,
        "shower_label_data_access": False,
        "target_information_access": False,
        "constants": constants,
        "all_functions": all_functions,
        "selected_functions": functions,
        "year_specific_token_counts": year_tokens,
        "imports": [
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ],
    }
    (out / "sonotaco_2023_parser_source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "sonotaco_2023_parser_source_excerpts.py").write_text("\n\n\n".join(excerpts) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("SONOTACO_2023_PARSER_SOURCE_EXCERPTS_BEGIN")
    print("\n\n\n".join(excerpts))
    print("SONOTACO_2023_PARSER_SOURCE_EXCERPTS_END")


if __name__ == "__main__":
    main()
