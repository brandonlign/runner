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


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def target_names(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            out.add(child.id)
    return out


def assignment_targets(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Assign):
        return set().union(*(target_names(target) for target in node.targets))
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        return target_names(node.target)
    return set()


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


def named_assignments(main_fn: ast.FunctionDef, name: str) -> list[ast.AST]:
    return [
        node
        for node in ast.walk(main_fn)
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and name in assignment_targets(node)
    ]


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

    # The inherited parser may bind the truth dictionary early. The scientific
    # invariant is stronger and narrower: main must not LOAD any truth value
    # until the complete expanded membership payload has been serialized,
    # hashed, and written in immutable pre-truth form.
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
    require(len(hidden_stores) == 1, f"expected one hidden_labels binding, got {hidden_stores}")
    require(hidden_loads, "hidden_labels is never read in main; audit target changed")
    first_truth_load = min(hidden_loads)

    payload_assignments = named_assignments(main_fn, "frozen_payload")
    require(len(payload_assignments) == 1, f"expected one frozen_payload assignment, got {len(payload_assignments)}")
    payload_assign = payload_assignments[0]
    payload_text = ast.get_source_segment(source, payload_assign) or ""
    require("json.dumps(expanded" in payload_text, "frozen_payload no longer serializes expanded memberships directly")
    require("sort_keys=True" in payload_text, "frozen_payload deterministic sorting changed")
    require("separators=(\",\", \":\")" in payload_text, "frozen_payload canonical separators changed")

    sha_assignments = named_assignments(main_fn, "membership_sha")
    require(len(sha_assignments) == 1, f"expected one membership_sha assignment, got {len(sha_assignments)}")
    sha_assign = sha_assignments[0]
    sha_text = ast.get_source_segment(source, sha_assign) or ""
    require("hashlib.sha256(frozen_payload).hexdigest()" in sha_text, "membership_sha no longer hashes exact frozen_payload")

    sha_writes: list[ast.Expr] = []
    payload_writes: list[ast.Expr] = []
    for node in ast.walk(main_fn):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        text = ast.get_source_segment(source, node) or ""
        if "p1_membership_pretruth.sha256" in text and ".write_text(" in text:
            sha_writes.append(node)
        if "p1_expanded_families.json.gz" in text and ".write_bytes(" in text:
            payload_writes.append(node)
    require(len(sha_writes) == 1, f"expected one membership SHA write, got {[n.lineno for n in sha_writes]}")
    require(len(payload_writes) == 1, f"expected one expanded-payload write, got {[n.lineno for n in payload_writes]}")
    sha_write = sha_writes[0]
    payload_write = payload_writes[0]
    sha_write_text = ast.get_source_segment(source, sha_write) or ""
    payload_write_text = ast.get_source_segment(source, payload_write) or ""
    require("membership_sha" in sha_write_text, "pretruth SHA file is not written from membership_sha")
    require("gzip.compress(frozen_payload)" in payload_write_text, "expanded-family artifact is not the hashed frozen_payload")

    require(
        payload_assign.lineno < sha_assign.lineno < sha_write.lineno < payload_write.lineno < first_truth_load,
        "membership serialize/hash/write chain no longer completes before first truth read",
    )

    # Every truth read must occur inside the exact v8 evaluator. P1 has exactly
    # two intended reads: expanded P1 evaluation and exact-v8 baseline replay.
    observed_truth_calls: list[tuple[int, str]] = []
    for node in hidden_load_nodes:
        call = enclosing_call(node, parents)
        require(call is not None, f"hidden_labels read outside a call at line {node.lineno}")
        name = call_name(call)
        observed_truth_calls.append((node.lineno, name))
        require(name == "evaluate_order", f"hidden_labels enters non-evaluation call {name!r} at line {node.lineno}")
    require(len(hidden_load_nodes) == 2, f"unexpected number of P1 truth reads: {hidden_loads}")

    # Once serialization begins, expanded cannot be reassigned or mutated before
    # evaluation. The byte string written to disk is therefore exactly the
    # membership object that the evaluator receives.
    for node in ast.walk(main_fn):
        if not hasattr(node, "lineno") or not (payload_assign.lineno < node.lineno < first_truth_load):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            require("expanded" not in assignment_targets(node), f"expanded reassigned after serialization at line {node.lineno}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id == "expanded" and node.func.attr in MUTATING_METHODS:
                raise RuntimeError(f"expanded mutated via .{node.func.attr} after serialization at line {node.lineno}")

    require("v8.mult.evaluate_order(hidden_labels, expanded, v8_order)" in source, "expanded P1 evaluation site changed")
    require("v8.mult.evaluate_order(hidden_labels, families, v8_order)" in source, "exact-v8 baseline evaluation site changed")
    require('"membership_pretruth_sha256": membership_sha' in source, "reported membership checksum no longer uses frozen membership_sha")

    print("PASS_P1_PRETRUTH_LABEL_DATAFLOW_AUDIT")
    print(f"hidden_label_binding_line={hidden_stores[0]}")
    print(f"payload_serialize_line={payload_assign.lineno}")
    print(f"membership_sha_line={sha_assign.lineno}")
    print(f"membership_sha_write_line={sha_write.lineno}")
    print(f"expanded_payload_write_line={payload_write.lineno}")
    print(f"first_hidden_label_read_line={first_truth_load}")
    print(f"truth_calls={observed_truth_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
