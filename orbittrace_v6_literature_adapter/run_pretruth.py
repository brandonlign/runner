#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--id-manifest", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    # No parser, mapping audit, shower-truth file, or competitor assignment file
    # is accepted by this executable.  That is a deliberate process boundary.
    v6 = load_module(args.v6_source, "orbittrace_v6_pretruth_science")
    old = load_module(args.base_runner, "orbittrace_v6_pretruth_base")
    exact = load_module(args.exact_row_runner, "orbittrace_v6_pretruth_exact_geometry")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)

    require(float(support.BLIND_LOW) == adapter.BLIND_LOW and float(support.BLIND_HIGH) == adapter.BLIND_HIGH,
            "support blind interval changed")
    require(hashlib.sha256(args.archive_2023.read_bytes()).hexdigest() == exact.ARCHIVE_SHA256[2023],
            "2023 archive hash changed")
    require(hashlib.sha256(args.archive_2025.read_bytes()).hexdigest() == exact.ARCHIVE_SHA256[2025],
            "2025 archive hash changed")

    manifest = json.loads(args.id_manifest.read_text())
    require(manifest["classification"] == "pretruth exact-row ID-only manifest", "wrong manifest classification")
    require(manifest["years"] == list(adapter.YEARS), "manifest years changed")
    require(manifest["blind_exclusion"] == [adapter.BLIND_LOW, adapter.BLIND_HIGH], "manifest blind interval changed")
    manifest_digest = canonical_sha(manifest)
    sha_path = args.id_manifest.with_suffix(args.id_manifest.suffix + ".sha256")
    require(sha_path.exists() and sha_path.read_text().strip() == manifest_digest, "ID manifest SHA mismatch")

    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    results: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        scan_by_year: dict[int, list[dict[str, Any]]] = {}
        background_by_year: dict[int, set[str]] = {}
        for year in adapter.YEARS:
            entry = manifest["panels"][panel][str(year)]
            scan_ids = {str(x) for x in entry["scan_ids"]}
            background_ids = {str(x) for x in entry["native_background_ids"]}
            require(len(scan_ids) == int(entry["scan_count"]), f"scan manifest count mismatch {panel} {year}")
            require(len(background_ids) == int(entry["native_background_count"]),
                    f"background manifest count mismatch {panel} {year}")
            require(background_ids <= scan_ids, f"background IDs outside scan {panel} {year}")
            scan_by_year[year] = exact.read_exact_geometry(year, archives[year], scan_ids, base)
            background_by_year[year] = background_ids

        calibration_by_year = adapter.calibration_events_from_native_sporadic(scan_by_year, background_by_year)
        result = adapter.run_v6_panel(panel, scan_by_year, calibration_by_year, v6, old, candidate, base, scorer, support)
        results[panel] = result

    # Each panel's complete primary output was hashed internally before this file
    # can be consumed by the separate truth/evaluation process.
    out = {
        "classification": "v6 exact-row pretruth frozen primary outputs",
        "id_manifest_sha256": manifest_digest,
        "years": list(adapter.YEARS),
        "blind_exclusion": [adapter.BLIND_LOW, adapter.BLIND_HIGH],
        "panels": results,
        "truth_accessed": False,
        "mapping_accessed": False,
        "competitor_cluster_labels_accessed": False,
    }
    require(all(out["panels"][p]["primary_ranking_sha256_before_truth"] for p in ("hdbscan", "sugar")),
            "missing pretruth primary hash")
    require(all(all(not (adapter.BLIND_LOW <= float(e["sol"]) <= adapter.BLIND_HIGH)
                    for e in exact.read_exact_geometry(year, archives[year],
                        set(manifest["panels"][panel][str(year)]["scan_ids"]), base))
                for panel in ("hdbscan", "sugar") for year in adapter.YEARS),
            "target interval appeared during final integrity replay")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(canonical_sha(out) + "\n")
    print("V6_PRETRUTH_PRIMARY_FREEZE_BEGIN")
    print(json.dumps({
        "classification": out["classification"],
        "id_manifest_sha256": manifest_digest,
        "primary_hashes": {p: results[p]["primary_ranking_sha256_before_truth"] for p in ("hdbscan", "sugar")},
        "primary_family_counts": {p: len(results[p]["primary_families"]) for p in ("hdbscan", "sugar")},
        "truth_accessed": False,
    }, indent=2, sort_keys=True))
    print("V6_PRETRUTH_PRIMARY_FREEZE_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
