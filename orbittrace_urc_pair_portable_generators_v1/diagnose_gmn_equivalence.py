#!/usr/bin/env python3
"""Temporary transport diagnostic wrapper for the frozen GMN equivalence proof.

Scientific generation is unchanged. This replaces only the verifier's diagnostic formatter so
an exact-structure failure reports the first nested field/value mismatch rather than hashes only.
"""
from __future__ import annotations

from typing import Any

from orbittrace_urc_pair_portable_generators_v1 import verify_gmn_equivalence as verify


def first_nested_difference(left: Any, right: Any, path: str = "$") -> dict[str, Any]:
    if type(left) is not type(right):
        return {"path": path, "kind": "type", "left_type": type(left).__name__, "right_type": type(right).__name__, "left": left, "right": right}
    if isinstance(left, dict):
        lk, rk = set(left), set(right)
        if lk != rk:
            return {"path": path, "kind": "keys", "left_only": sorted(lk-rk), "right_only": sorted(rk-lk)}
        for key in sorted(lk):
            if left[key] != right[key]:
                return first_nested_difference(left[key], right[key], f"{path}.{key}")
        return {"equal": True}
    if isinstance(left, list):
        if len(left) != len(right):
            return {"path": path, "kind": "length", "left_length": len(left), "right_length": len(right)}
        for i, (a, b) in enumerate(zip(left, right)):
            if a != b:
                return first_nested_difference(a, b, f"{path}[{i}]")
        return {"equal": True}
    if left != right:
        out = {"path": path, "kind": "value", "left": left, "right": right}
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            out["absolute_delta"] = abs(float(left) - float(right))
        return out
    return {"equal": True}


def diagnostic_list_difference(left: list[Any], right: list[Any]) -> dict[str, Any]:
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {
                "index": i,
                "left_sha256": verify.canonical_sha(a),
                "right_sha256": verify.canonical_sha(b),
                "left_family_id": a.get("family_id") if isinstance(a, dict) else None,
                "right_family_id": b.get("family_id") if isinstance(b, dict) else None,
                "first_nested_difference": first_nested_difference(a, b),
            }
    if len(left) != len(right):
        return {"index": min(len(left), len(right)), "left_length": len(left), "right_length": len(right)}
    return {"equal": True}


verify.first_list_difference = diagnostic_list_difference

if __name__ == "__main__":
    raise SystemExit(verify.main())
