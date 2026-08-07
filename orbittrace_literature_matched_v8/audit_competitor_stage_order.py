#!/usr/bin/env python3
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

HDB_EXPECTED = "a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2"
SUGAR_CORE_EXPECTED = "5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb"
SUGAR_RUNNER_EXPECTED = "adbeb8a8737079f8cd63568d8684733dce09f724305ef9605f22423a57fda936"


def decode_parts(root: Path, names: list[str]) -> bytes:
    enc = "".join("".join((root / name).read_text().split()) for name in names)
    return gzip.decompress(base64.b64decode(enc, validate=True))


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def inspect_source(payload: bytes, expected: str, name: str) -> dict:
    digest = sha(payload)
    if digest != expected:
        raise RuntimeError(f"{name} source hash mismatch {digest}")
    text = payload.decode("utf-8")
    tree = ast.parse(text)
    funcs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append({
                "name": node.name,
                "args": [a.arg for a in node.args.posonlyargs + node.args.args],
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", None),
            })
    needles = (
        "BLIND", "blind", "20.0", "55.0", "HDBSCAN", "DBSCAN", "fit_predict",
        "quality", "reference", "coverage", "assignment", "cluster", "events",
        "minimum_cluster_size", "minimum_samples", "clone", "recurrence", "overlap",
    )
    relevant = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if any(token in line for token in needles):
            relevant.append({"line": i, "text": line[:500]})
    return {
        "name": name,
        "sha256": digest,
        "functions": funcs,
        "relevant_lines": relevant,
        "line_count": len(lines),
    }


def main() -> None:
    hdb_root = Path("orbittrace_literature_comparison/hdbscan_catalogue_runner_parts")
    hdb = decode_parts(hdb_root, [f"part{i:02d}.b64" for i in range(5)])
    sugar_core_root = Path("orbittrace_literature_comparison/sugar_uncertainty_core_parts")
    sugar_core = decode_parts(sugar_core_root, [f"part{i:02d}.b64" for i in range(3)])
    sugar_run_root = Path("orbittrace_literature_comparison/sugar_uncertainty_2025_runner_parts")
    sugar_runner = decode_parts(sugar_run_root, [f"part{i:02d}.b64" for i in range(4)])
    result = {
        "verdict": "PASS_SOURCE_ONLY_COMPETITOR_STAGE_ORDER_AUDIT",
        "data_accessed": False,
        "orbittrace_target_accessed": False,
        "excluded_interval_contents_accessed": False,
        "sources": {
            "hdbscan": inspect_source(hdb, HDB_EXPECTED, "hdbscan_2025_runner"),
            "sugar_core": inspect_source(sugar_core, SUGAR_CORE_EXPECTED, "sugar_uncertainty_core"),
            "sugar_runner": inspect_source(sugar_runner, SUGAR_RUNNER_EXPECTED, "sugar_2025_runner"),
        },
    }
    out = Path("output_stage_order")
    out.mkdir(parents=True, exist_ok=True)
    (out / "competitor_stage_order_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
