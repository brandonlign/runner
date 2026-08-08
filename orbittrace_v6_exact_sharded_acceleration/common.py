from __future__ import annotations

import hashlib
import inspect
import json
import pickle
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, require, sha256_bytes

SHARD_COUNT = 8
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
FROZEN_V6_SHA256 = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"


class _PrefixCaptured(RuntimeError):
    pass


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _fingerprint_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        if not value:
            return {"kind": type(value).__name__, "len": 0}
        if all(isinstance(row, dict) and "id" in row for row in value):
            ids = [str(row["id"]) for row in value]
            return {"kind": "event_rows", "len": len(ids), "ids_sha256": canonical_json_sha256(ids)}
        if len(value) <= 32 and all(item is None or isinstance(item, (str, int, float, bool)) for item in value):
            return list(value)
        return {"kind": type(value).__name__, "len": len(value)}
    if isinstance(value, dict):
        if len(value) <= 32 and all(isinstance(k, (str, int, float, bool)) for k in value):
            safe = {}
            for key, item in value.items():
                if item is None or isinstance(item, (str, int, float, bool)):
                    safe[str(key)] = item
                else:
                    return {"kind": "dict", "len": len(value)}
            return safe
        return {"kind": "dict", "len": len(value)}
    if hasattr(value, "shape") and hasattr(value, "dtype") and hasattr(value, "tobytes"):
        raw = value.tobytes(order="C")
        return {
            "kind": "array",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "sha256": sha256_bytes(raw),
        }
    return {"kind": type(value).__name__}


def call_fingerprint(function: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    bound = inspect.signature(function).bind_partial(*args, **kwargs)
    payload = {name: _fingerprint_value(value) for name, value in bound.arguments.items()}
    return canonical_json_sha256(payload)


def load_sidecar_pickle(path: Any) -> tuple[Any, str]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA sidecar {sidecar}")
    expected = sidecar.read_text().strip().split()[0]
    digest = sha256_bytes(raw)
    require(digest == expected, f"SHA sidecar mismatch {path}")
    return pickle.loads(raw), digest


def center_key(center: float) -> str:
    return f"{float(center):.1f}"


def locate_proposal_owner(v6: Any, old: Any, support: Any) -> tuple[str | None, Any | None]:
    """Locate the module actually referenced by scan_year_v6 for proposal_window_v6.

    The repaired v6 source delegates some catalogue helpers through its inherited
    base runner. This function is implementation plumbing only; it never changes
    which proposal function scan_year_v6 calls.
    """
    source = inspect.getsource(v6.scan_year_v6)
    candidates = (("v6", v6), ("old", old), ("support", support))
    explicit = (
        ("old.proposal_window_v6", "old", old),
        ("support.proposal_window_v6", "support", support),
        ("v6.proposal_window_v6", "v6", v6),
    )
    for token, name, owner in explicit:
        if token in source:
            require(hasattr(owner, "proposal_window_v6"), f"scan references missing {token}")
            return name, owner
    if "proposal_window_v6" in source:
        matches = [(name, owner) for name, owner in candidates if hasattr(owner, "proposal_window_v6")]
        require(len(matches) == 1, "cannot uniquely resolve proposal_window_v6 owner")
        return matches[0]
    return None, None


def capture_scan_prefix(
    v6: Any,
    old: Any,
    year: int,
    events: list[dict[str, Any]],
    calibration_events: list[dict[str, Any]],
    candidate: Any,
    base: Any,
    scorer: Any,
    support: Any,
) -> dict[str, Any]:
    """Run the exact repaired scan prefix and stop at its first exact-rescore call."""
    original = v6.exact_rescore_window_v6
    proposal_owner_name, proposal_owner = locate_proposal_owner(v6, old, support)
    original_proposal = getattr(proposal_owner, "proposal_window_v6") if proposal_owner is not None else None
    captured: dict[str, Any] = {}
    proposal_calls: list[dict[str, Any]] = []

    def proposal_capture(*args: Any, **kwargs: Any) -> Any:
        require(original_proposal is not None, "proposal capture invoked without original function")
        fingerprint = call_fingerprint(original_proposal, args, kwargs)
        result = original_proposal(*args, **kwargs)
        frozen_result = pickle.loads(pickle.dumps(result, protocol=pickle.HIGHEST_PROTOCOL))
        proposal_calls.append({"fingerprint": fingerprint, "result": frozen_result})
        return result

    def sentinel(
        old_arg: Any,
        records: list[dict[str, Any]],
        window_events: list[dict[str, Any]],
        event_lookup: dict[str, dict[str, Any]],
        support_arg: Any,
        base_arg: Any,
    ) -> list[dict[str, Any]]:
        del old_arg, records, window_events, event_lookup, support_arg, base_arg
        frame = inspect.currentframe()
        require(frame is not None and frame.f_back is not None, "cannot inspect scan prefix frame")
        caller = frame.f_back
        require(caller.f_code.co_name == "scan_year_v6", "prefix sentinel called outside scan_year_v6")
        loc = caller.f_locals
        raw_by_center = loc.get("records_by_center")
        require(raw_by_center is not None, "records_by_center absent at exact boundary")
        by_center: dict[str, list[dict[str, Any]]] = {}
        for center, rows in sorted(raw_by_center.items()):
            ordered = [dict(row) for row in sorted(rows, key=lambda row: str(row["proposal_anchor_id"]))]
            by_center[center_key(float(center))] = ordered
        require(by_center, "no exact proposal centers captured")
        captured.update({
            "format": "orbittrace-v6-exact-shard-prepare-v1",
            "year": int(year),
            "records_by_center": by_center,
            "proposal_cal": {int(k): v.copy() for k, v in loc["proposal_cal"].items()},
            "v3_cal": {int(k): v.copy() for k, v in loc["v3_cal"].items()},
            "fixed4_cal": {int(k): v.copy() for k, v in loc["fixed4_cal"].items()},
            "calibration_summary": [dict(row) for row in loc["calibration_summary"]],
            "proposal_cap": int(loc["proposal_cap"]),
            "prefilter_candidates": int(loc["prefilter_candidates"]),
            "proposal_scored": int(loc["proposal_scored"]),
            "primary_selected_total": int(loc["primary_selected_total"]),
            "rescue_selected_total": int(loc["rescue_selected_total"]),
            "window_count": int(loc["window_count"]),
            "unsupported_windows": int(loc["unsupported_windows"]),
            "center_count": len(by_center),
            "proposal_count": sum(len(rows) for rows in by_center.values()),
            "proposal_calls": proposal_calls,
            "proposal_call_count": len(proposal_calls),
            "proposal_owner": proposal_owner_name,
            "scan_rows_sha256": event_rows_sha256(events),
            "calibration_rows_sha256": event_rows_sha256(calibration_events),
            "frozen_v6_sha256": FROZEN_V6_SHA256,
            "repaired_v6_sha256": REPAIRED_V6_SHA256,
            "firewall": {
                "target_interval_remains_excluded": True,
                "hidden_labels_not_saved": True,
                "exact_rescore_not_executed_in_prepare": True,
                "proposal_outputs_captured_from_original_function": proposal_owner is not None,
            },
        })
        captured["records_by_center_sha256"] = canonical_json_sha256(captured["records_by_center"])
        raise _PrefixCaptured("exact boundary reached")

    if proposal_owner is not None:
        setattr(proposal_owner, "proposal_window_v6", proposal_capture)
    v6.exact_rescore_window_v6 = sentinel
    try:
        v6.scan_year_v6(old, year, events, calibration_events, candidate, base, scorer, support)
    except _PrefixCaptured:
        pass
    finally:
        v6.exact_rescore_window_v6 = original
        if proposal_owner is not None:
            setattr(proposal_owner, "proposal_window_v6", original_proposal)
    require(captured, "scan prefix did not reach exact boundary")
    require(captured["proposal_cap"] == 512, "proposal cap changed")
    if proposal_owner is not None:
        require(0 < captured["proposal_call_count"] <= captured["window_count"], "proposal capture count invalid")
    else:
        require(captured["proposal_call_count"] == 0, "unexpected proposal capture without owner")
    return captured


def assign_centers(
    records_by_center: dict[str, list[dict[str, Any]]],
    shard_count: int = SHARD_COUNT,
    work_by_center: dict[str, int] | None = None,
) -> list[list[str]]:
    require(shard_count > 0, "invalid shard count")
    weights = work_by_center or {key: len(rows) for key, rows in records_by_center.items()}
    require(set(weights) == set(records_by_center), "work weights do not cover centers")
    require(all(int(weights[key]) >= 0 for key in weights), "negative center work")
    assignments: list[list[str]] = [[] for _ in range(shard_count)]
    loads = [0 for _ in range(shard_count)]
    ranked = sorted(records_by_center, key=lambda key: (-int(weights[key]), float(key)))
    for key in ranked:
        shard = min(range(shard_count), key=lambda index: (loads[index], index))
        assignments[shard].append(key)
        loads[shard] += int(weights[key])
    for rows in assignments:
        rows.sort(key=float)
    flattened = [key for rows in assignments for key in rows]
    require(sorted(flattened, key=float) == sorted(records_by_center, key=float), "shard assignment coverage mismatch")
    require(len(flattened) == len(set(flattened)), "duplicate center assignment")
    return assignments


def proposal_anchor_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["proposal_anchor_id"]) for row in rows]


def shard_plan_summary(
    records_by_center: dict[str, list[dict[str, Any]]],
    shard_count: int = SHARD_COUNT,
    work_by_center: dict[str, int] | None = None,
    event_count_by_center: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    weights = work_by_center or {key: len(rows) for key, rows in records_by_center.items()}
    assignments = assign_centers(records_by_center, shard_count, weights)
    return [
        {
            "shard": index,
            "centers": centers,
            "proposals": sum(len(records_by_center[key]) for key in centers),
            "estimated_work": sum(int(weights[key]) for key in centers),
            "window_events": sum(int((event_count_by_center or {}).get(key, 0)) for key in centers),
        }
        for index, centers in enumerate(assignments)
    ]
