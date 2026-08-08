#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter import adapter
from orbittrace_v6_literature_adapter.parallel_exact_rescore import install as install_parallel_exact


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", required=True, choices=("hdbscan", "sugar"))
    p.add_argument("--year", required=True, type=int, choices=adapter.YEARS)
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--id-manifest", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--parallel-exact-workers", type=int, default=4)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    v6 = load_module(args.v6_source, f"orbittrace_v6_lf_pretruth_{args.panel}_{args.year}")
    old = load_module(args.base_runner, f"orbittrace_v6_lf_base_{args.panel}_{args.year}")
    exact = load_module(args.exact_row_runner, f"orbittrace_v6_lf_exact_geometry_{args.panel}_{args.year}")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    adapter.configure_transfer_modules(v6, old, support)
    execution = install_parallel_exact(v6, workers=args.parallel_exact_workers, min_parallel_records=256)

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
    native_background_ids = {str(x) for x in entry["native_background_ids"]}
    require(len(scan_ids) == int(entry["scan_count"]), "scan count mismatch")
    require(len(native_background_ids) == int(entry["native_background_count"]), "native-background count mismatch")
    require(native_background_ids <= scan_ids, "native-background IDs outside scan")

    scan_events = exact.read_exact_geometry(args.year, args.archive, scan_ids, base)
    require(all(not (adapter.BLIND_LOW <= float(e["sol"]) <= adapter.BLIND_HIGH) for e in scan_events),
            "target interval entered panel-year scan")
    # v6-LF scientific rule: every matched scan row enters the geometry-only null reservoir.
    # The competitor-native background subset is verified above for manifest integrity but is never used for calibration membership.
    calibration = [dict(event, complex_key="SPORADIC") for event in scan_events]
    require(len(calibration) == len(scan_events), "all-event calibration count mismatch")
    require([str(e["id"]) for e in calibration] == [str(e["id"]) for e in scan_events], "all-event calibration ID order mismatch")
    for scan, cal in zip(scan_events, calibration):
        require(all(scan[k] == cal[k] for k in ("id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau")),
                f"all-event calibration geometry mismatch {scan['id']}")

    print(
        f"V6_LF_PANEL_YEAR_START panel={args.panel} year={args.year} rows={len(scan_events)} "
        f"calibration={len(calibration)} native_background_unused={len(native_background_ids)}",
        flush=True,
    )
    audit, anchors, components = v6.scan_year_v6(
        old, args.year, scan_events, calibration, candidate, base, scorer, support
    )
    require(len(audit["supported_bins"]) >= 30, "insufficient supported calibration bins")
    require(audit["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(audit["max_primary_proposals_per_year"] == 36864, "annual proposal budget changed")
    require(int(audit["calibration_events"]) == len(scan_events), "v6-LF scan/calibration identity changed")

    checkpoint = {
        "classification": "v6 exact-row pretruth panel-year checkpoint",
        "method_variant": "v6-LF all-event Mondrian null",
        "panel": args.panel,
        "year": args.year,
        "id_manifest_sha256": manifest_sha,
        "blind_exclusion": [adapter.BLIND_LOW, adapter.BLIND_HIGH],
        "truth_accessed": False,
        "mapping_accessed": False,
        "competitor_cluster_labels_accessed": False,
        "native_background_membership_used_for_calibration": False,
        "calibration_reservoir": "all exact matched scan rows",
        "scan_count": len(scan_events),
        "calibration_count": len(calibration),
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "execution": {
            "parallel_exact_enabled": int(args.parallel_exact_workers) > 1,
            "parallel_exact_workers": int(execution["workers"]),
            "parallel_exact_min_records": int(execution["min_parallel_records"]),
            "parallel_exact_start_method": str(execution["start_method"]),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    args.output.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print(
        f"V6_LF_PANEL_YEAR_DONE panel={args.panel} year={args.year} anchors={len(anchors)} "
        f"components={len(components)} checkpoint_sha256={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
