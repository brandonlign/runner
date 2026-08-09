from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter import adapter


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def materialize(args: Any, tag: str) -> dict[str, Any]:
    """Materialize exact pairwise rows with the frozen v6-LF all-event null.

    The ID-only manifest and geometry archive are available pretruth. Competitor
    assignments and known-shower mapping remain absent. Native-background IDs are
    integrity-checked but never select calibration membership.
    """
    v6 = load_module(args.v6_source, f"orbittrace_v6_lf_lit_fanout_v6_{tag}")
    old = load_module(args.base_runner, f"orbittrace_v6_lf_lit_fanout_base_{tag}")
    exact = load_module(args.exact_row_runner, f"orbittrace_v6_lf_lit_fanout_exact_{tag}")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    adapter.configure_transfer_modules(v6, old, support)

    manifest = json.loads(args.id_manifest.read_text())
    require(manifest["classification"] == "pretruth exact-row ID-only manifest", "wrong manifest classification")
    require(manifest["years"] == list(adapter.YEARS), "manifest years changed")
    require(manifest["blind_exclusion"] == [adapter.BLIND_LOW, adapter.BLIND_HIGH], "blind interval changed")
    manifest_sha = canonical_sha(manifest)
    sidecar = args.id_manifest.with_suffix(args.id_manifest.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip() == manifest_sha, "manifest SHA mismatch")

    require(hashlib.sha256(args.archive.read_bytes()).hexdigest() == exact.ARCHIVE_SHA256[args.year], "archive hash changed")
    entry = manifest["panels"][args.panel][str(args.year)]
    scan_ids = {str(value) for value in entry["scan_ids"]}
    native_ids = {str(value) for value in entry["native_background_ids"]}
    require(len(scan_ids) == int(entry["scan_count"]), "scan count mismatch")
    require(len(native_ids) == int(entry["native_background_count"]), "native-background count mismatch")
    require(native_ids <= scan_ids, "native-background IDs outside scan")

    scan_events = exact.read_exact_geometry(args.year, args.archive, scan_ids, base)
    require(len(scan_events) == len(scan_ids), "exact geometry row count mismatch")
    require(all(not (adapter.BLIND_LOW <= float(event["sol"]) <= adapter.BLIND_HIGH) for event in scan_events), "target interval entered scan")
    calibration = [dict(event, complex_key="SPORADIC") for event in scan_events]
    require(len(calibration) == len(scan_events), "all-event calibration count mismatch")
    require([str(e["id"]) for e in calibration] == [str(e["id"]) for e in scan_events], "all-event calibration order mismatch")
    for scan, cal in zip(scan_events, calibration):
        require(all(scan[key] == cal[key] for key in ("id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau")), f"calibration geometry mismatch {scan['id']}")

    return {
        "v6": v6,
        "old": old,
        "exact": exact,
        "support": support,
        "candidate": candidate,
        "base": base,
        "scorer": scorer,
        "manifest_sha": manifest_sha,
        "scan_events": scan_events,
        "calibration": calibration,
        "scan_count": len(scan_events),
        "calibration_count": len(calibration),
        "native_background_count": len(native_ids),
    }
