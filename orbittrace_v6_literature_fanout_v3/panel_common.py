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
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def materialize(args: Any, module_tag: str) -> dict[str, Any]:
    """Materialize the already-frozen exact-row pretruth panel universe.

    This deliberately mirrors `orbittrace_v6_literature_adapter/run_pretruth_year.py`:
    the ID-only manifest selects exact geometry rows and the native-background ID
    subset, while known-shower truth and competitor cluster labels remain absent.
    """
    v6 = load_module(args.v6_source, f"orbittrace_lit_fanout_v6_{module_tag}")
    old = load_module(args.base_runner, f"orbittrace_lit_fanout_base_{module_tag}")
    exact = load_module(args.exact_row_runner, f"orbittrace_lit_fanout_exact_{module_tag}")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    adapter.configure_transfer_modules(v6, old, support)

    manifest = json.loads(args.id_manifest.read_text())
    require(manifest["classification"] == "pretruth exact-row ID-only manifest", "wrong manifest classification")
    require(manifest["years"] == list(adapter.YEARS), "manifest years changed")
    require(manifest["blind_exclusion"] == [adapter.BLIND_LOW, adapter.BLIND_HIGH], "manifest blind interval changed")
    manifest_sha = canonical_sha(manifest)
    manifest_sha_file = args.id_manifest.with_suffix(args.id_manifest.suffix + ".sha256")
    require(manifest_sha_file.exists() and manifest_sha_file.read_text().strip() == manifest_sha, "manifest SHA mismatch")

    require(hashlib.sha256(args.archive.read_bytes()).hexdigest() == exact.ARCHIVE_SHA256[args.year], "archive hash changed")
    entry = manifest["panels"][args.panel][str(args.year)]
    scan_ids = {str(x) for x in entry["scan_ids"]}
    background_ids = {str(x) for x in entry["native_background_ids"]}
    require(len(scan_ids) == int(entry["scan_count"]), "scan count mismatch")
    require(len(background_ids) == int(entry["native_background_count"]), "background count mismatch")
    require(background_ids <= scan_ids, "background IDs outside scan")

    scan_events = exact.read_exact_geometry(args.year, args.archive, scan_ids, base)
    require(all(not (adapter.BLIND_LOW <= float(e["sol"]) <= adapter.BLIND_HIGH) for e in scan_events), "target interval entered panel-year scan")
    calibration = [dict(event, complex_key="SPORADIC") for event in scan_events if str(event["id"]) in background_ids]
    require(len(calibration) == len(background_ids), "calibration ID materialization mismatch")
    require(len(calibration) >= 1000, "insufficient panel-year calibration reservoir")
    return {
        "v6": v6,
        "old": old,
        "exact": exact,
        "support": support,
        "candidate": candidate,
        "base": base,
        "scorer": scorer,
        "manifest": manifest,
        "manifest_sha": manifest_sha,
        "scan_events": scan_events,
        "calibration": calibration,
        "scan_count": len(scan_events),
        "calibration_count": len(calibration),
    }
