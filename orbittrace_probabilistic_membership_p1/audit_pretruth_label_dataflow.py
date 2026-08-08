#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path


MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse",
    "update", "setdefault", "add", "discard", "difference_update",
    "intersection_update", "symmetric_difference_update",
}
ALLOWED_TRUTH_CALLS = {"evaluate_order", "label_totals"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def target_names(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            out.add(child.id)
    return out


def enclosing_call(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.Call | None:
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, ast.Call):
            return cur
    return None


def call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_pretruth_label_dataflow.py FROZEN_P1_RUNTIME")
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    main_fn = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )

    # The inherited parser may bind the truth dictionary early, but the P1
    # protocol requires that its values are not read until the membership
    # payload is immutable and hashed.
    hidden_stores = sorted(
        node.lineno
        for node in ast.walk(main_fn)
        if isinstance(node, ast.Name) and node.id == "hidden_labels" and isinstance(node.ctx, ast.Store)
    )
    hidden_load_nodes = [
        node for node in ast.walk(main_fn)
        if isinstance(node, ast.Name) and node.id == "hidden_labels" and isinstance(node.ctx, ast.Load)
    ]
    hidden_loads = sorted(node.lineno for node in hidden_load_nodes)
    require(hidden_stores, "hidden_labels binding not found in main")
    require(hidden_loads, "hidden_labels is never read in main; audit target changed")

    freeze_assignments = []
    for node in ast.walk(main_fn):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names: set[str] = set()
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    names |= target_names(target)
            else:
                names |= target_names(node.target)
            if "membership_pretruth_sha256" in names:
                freeze_assignments.append(node)
    require(len(freeze_assignments) == 1, f"expected exactly one membership_pretruth_sha256 assignment, got {len(freeze_assignments)}")
    freeze = freeze_assignments[0]
    freeze_text = ast.get_source_segment(source, freeze) or ""
    require("expanded" in freeze_text, "pretruth membership hash no longer commits expanded memberships")

    first_truth_load = min(hidden_loads)
    require(freeze.lineno < first_truth_load, "known-shower truth is read before membership pretruth hash")

    # Every truth read must occur inside an explicit evaluation-only call.
    observed_truth_calls: list[tuple[int, str]] = []
    for node in hidden_load_nodes:
        call = enclosing_call(node, parents)
        require(call is not None, f"hidden_labels read outside a call at line {node.lineno}")
        name = call_name(call)
        observed_truth_calls.append((node.lineno, name))
        require(name in ALLOWED_TRUTH_CALLS, f"hidden_labels enters non-evaluation call {name!r} at line {node.lineno}")
    require(any(name == "evaluate_order" for _, name in observed_truth_calls), "exact v8 evaluate_order truth read not found")

    # Between the immutable membership hash and first truth evaluation, reject
    # reassignment or obvious in-place mutation of the expanded payload. This
    # makes the pretruth hash a real freeze rather than a ceremonial checksum.
    for node in ast.walk(main_fn):
        if not hasattr(node, "lineno") or not (freeze.lineno < node.lineno < first_truth_load):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]
            names = set().union(*(target_names(target) for target in targets)) if targets else set()
            require("expanded" not in names, f"expanded reassigned after pretruth hash at line {node.lineno}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id == "expanded" and node.func.attr in MUTATING_METHODS:
                raise RuntimeError(f"expanded mutated via .{node.func.attr} after pretruth hash at line {node.lineno}")

    # Ensure the exact source still contains the intended ordering markers.
    require("v8.mult.evaluate_order(hidden_labels, expanded, v8_order)" in source, "expanded P1 evaluation site changed")
    require("membership_pretruth_sha256" in source, "membership pretruth hash marker missing")

    print("PASS_P1_PRETRUTH_LABEL_DATAFLOW_AUDIT")
    print(f"hidden_label_store_lines={hidden_stores}")
    print(f"membership_pretruth_hash_line={freeze.lineno}")
    print(f"first_hidden_label_read_line={first_truth_load}")
    print(f"truth_calls={observed_truth_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
