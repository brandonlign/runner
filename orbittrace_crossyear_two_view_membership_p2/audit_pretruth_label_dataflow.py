#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_pretruth_label_dataflow.py CANONICAL_RUNTIME")
    path = Path(sys.argv[1])
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    hidden_loads = sorted(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "hidden_labels" and isinstance(node.ctx, ast.Load)
    )
    require(hidden_loads, "hidden_labels is never evaluated; audit target changed")

    membership_freeze_lines: list[int] = []
    model_freeze_lines: list[int] = []
    parse_store_lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, (ast.Tuple, ast.List)):
                    names = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
                    if "hidden_labels" in names:
                        parse_store_lines.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "write_text" and isinstance(node.func.value, ast.BinOp):
                pass
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr in {"write_text", "write_bytes"}:
                src = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                if "p2_model_pretruth" in src:
                    model_freeze_lines.append(node.lineno)
                if "p2_membership_pretruth" in src or "p2_expanded_families.json.gz" in src:
                    membership_freeze_lines.append(node.lineno)

    require(len(parse_store_lines) == 1, f"expected one inherited hidden-label parse binding, got {parse_store_lines}")
    require(model_freeze_lines, "model pretruth freeze write not found")
    require(membership_freeze_lines, "membership pretruth freeze write not found")
    last_model_freeze = max(model_freeze_lines)
    last_membership_freeze = max(membership_freeze_lines)
    first_truth_load = min(hidden_loads)

    require(last_model_freeze < first_truth_load, "known-shower truth is loaded before model freeze")
    require(last_membership_freeze < first_truth_load, "known-shower truth is loaded before membership freeze")

    # The canonical runtime is allowed to retain the inherited parser's hidden-label
    # dictionary in memory, but it may not READ it before the pretruth payload is
    # immutable. Keep the set of truth reads narrow and explicit.
    source = path.read_text(encoding="utf-8")
    load_context = []
    lines = source.splitlines()
    for lineno in hidden_loads:
        lo = max(1, lineno - 1)
        hi = min(len(lines), lineno + 1)
        load_context.append("\n".join(lines[lo - 1:hi]))
    joined = "\n".join(load_context)
    for token in (
        "evaluate_order(hidden_labels, families, v8_order)",
        "evaluate_order(hidden_labels, expanded, v8_order)",
        "label_totals(hidden_labels, v8.mult)",
    ):
        require(token in joined, f"unexpected/missing truth-read site: {token}")
    require(len(hidden_loads) == 3, f"unexpected number of hidden-label reads: {hidden_loads}")

    # Independently ensure the raw orbital side-channel parser never asks for a
    # catalogue label/shower field. Only the exact seven geometry/orbit headers
    # are admitted by exact_header_positions().
    func = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "exact_header_positions"
    )
    func_text = ast.get_source_segment(source, func) or ""
    for required in ("Unique trajectory", "Sol lon", '"q"', '"e"', '"i"', '"peri"', '"node"'):
        require(required in func_text, f"missing required raw field {required}")
    for forbidden in ("IAU", "shower", "Shower", "code", "label"):
        require(forbidden not in func_text, f"label-like raw field leaked into orbit parser: {forbidden}")

    print("PASS_P2_PRETRUTH_LABEL_DATAFLOW_AUDIT")
    print(f"inherited_hidden_label_binding_line={parse_store_lines[0]}")
    print(f"last_model_freeze_line={last_model_freeze}")
    print(f"last_membership_freeze_line={last_membership_freeze}")
    print(f"first_hidden_label_read_line={first_truth_load}")
    print(f"hidden_label_read_lines={hidden_loads}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
