from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

FROZEN_V6_SHA256 = "a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9"

BEFORE = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    components = primary_components + rescue_components
'''
AFTER = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components
'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def apply_exact_two_line_repair(frozen_path: Path, repaired_path: Path) -> str:
    raw = frozen_path.read_bytes()
    require(sha256_bytes(raw) == FROZEN_V6_SHA256, "frozen v6 source hash changed")
    original = raw.decode("utf-8")
    require(original.count(BEFORE) == 1, "exact repair anchor changed")
    patched = original.replace(BEFORE, AFTER, 1)
    require(patched.count(AFTER) == 1, "exact repair insertion failed")
    require(patched.replace(AFTER, BEFORE, 1) == original, "repair is not exactly reversible")
    repaired_path.write_text(patched, encoding="utf-8")
    return sha256_bytes(patched.encode("utf-8"))


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def normalized_event_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in rows:
        out.append({
            "id": str(event["id"]),
            "year": int(event["year"]),
            "sol": float(event["sol"]),
            "sun_lon": float(event["sun_lon"]),
            "ecl_lat": float(event["ecl_lat"]),
            "vg": float(event["vg"]),
            "iau": int(event.get("iau", 0)),
            "complex_key": str(event.get("complex_key", "")),
        })
    return out


def event_rows_sha256(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        normalized_event_rows(rows),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(payload)
