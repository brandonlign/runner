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


def load_checkpoint(path: Path, panel: str, year: int, manifest_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    sha_path = path.with_suffix(path.suffix + ".sha256")
    require(sha_path.exists() and sha_path.read_text().strip() == hashlib.sha256(raw).hexdigest(),
            f"checkpoint SHA mismatch {panel} {year}")
    checkpoint = pickle.loads(raw)
    require(checkpoint["classification"] == "v6 exact-row pretruth panel-year checkpoint", "wrong checkpoint classification")
    require(checkpoint["panel"] == panel and int(checkpoint["year"]) == year, "checkpoint panel/year mismatch")
    require(checkpoint["id_manifest_sha256"] == manifest_sha, "checkpoint manifest mismatch")
    require(checkpoint["blind_exclusion"] == [adapter.BLIND_LOW, adapter.BLIND_HIGH], "checkpoint blind interval changed")
    require(checkpoint["truth_accessed"] is False and checkpoint["mapping_accessed"] is False,
            "truth/mapping entered checkpoint")
    require(checkpoint["competitor_cluster_labels_accessed"] is False, "competitor labels entered checkpoint")
    require(len(checkpoint["audit"]["supported_bins"]) >= 30, "checkpoint calibration support failed")
    require(checkpoint["audit"]["proposal_cap_per_window"] == 512, "checkpoint proposal cap changed")
    require(checkpoint["audit"]["max_primary_proposals_per_year"] == 36864, "checkpoint annual budget changed")
    return checkpoint


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--id-manifest", required=True, type=Path)
    for panel in ("hdbscan", "sugar"):
        for year in adapter.YEARS:
            p.add_argument(f"--{panel}-{year}", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    # Still pre-truth: no parser, mapping or competitor assignment file is accepted.
    v6 = load_module(args.v6_source, "orbittrace_v6_pretruth_combiner")
    old = load_module(args.base_runner, "orbittrace_v6_pretruth_combiner_base")
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    adapter.configure_transfer_modules(v6, old, support)

    manifest = json.loads(args.id_manifest.read_text())
    manifest_sha = canonical_sha(manifest)
    manifest_sha_path = args.id_manifest.with_suffix(args.id_manifest.suffix + ".sha256")
    require(manifest_sha_path.exists() and manifest_sha_path.read_text().strip() == manifest_sha, "manifest SHA mismatch")
    require(manifest["classification"] == "pretruth exact-row ID-only manifest", "wrong manifest classification")

    results: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        checkpoints = [
            load_checkpoint(getattr(args, f"{panel}_{year}"), panel, year, manifest_sha)
            for year in adapter.YEARS
        ]
        all_anchors = [anchor for checkpoint in checkpoints for anchor in checkpoint["anchors"]]
        all_components = [component for checkpoint in checkpoints for component in checkpoint["components"]]
        audits = [checkpoint["audit"] for checkpoint in checkpoints]

        primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
        rescue_families = v6.build_family_track_v6(old, all_components, base, "fixed4_rescue")
        primary_payload = {
            "panel": panel,
            "years": list(adapter.YEARS),
            "corpus": adapter.CORPUS,
            "primary_method": "v3",
            "primary_families": primary_families,
            "scan_audits": audits,
        }
        primary_hash = canonical_sha(primary_payload)
        results[panel] = {
            "panel": panel,
            "primary_families": primary_families,
            "rescue_families": rescue_families,
            "scan_audits": audits,
            "anchor_count": len(all_anchors),
            "component_count": len(all_components),
            "primary_ranking_sha256_before_truth": primary_hash,
            "primary_payload_bytes": len(json.dumps(primary_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()),
            "panel_year_checkpoint_sha256": {
                str(year): hashlib.sha256(getattr(args, f"{panel}_{year}").read_bytes()).hexdigest()
                for year in adapter.YEARS
            },
        }
        print(f"V6_PANEL_COMBINED panel={panel} families={len(primary_families)} primary_sha256={primary_hash}", flush=True)

    out = {
        "classification": "v6 exact-row pretruth frozen primary outputs",
        "execution_form": "four independent panel-year checkpoints combined by frozen family builder",
        "id_manifest_sha256": manifest_sha,
        "years": list(adapter.YEARS),
        "blind_exclusion": [adapter.BLIND_LOW, adapter.BLIND_HIGH],
        "panels": results,
        "truth_accessed": False,
        "mapping_accessed": False,
        "competitor_cluster_labels_accessed": False,
    }
    require(all(results[p]["primary_ranking_sha256_before_truth"] for p in ("hdbscan", "sugar")), "missing primary hash")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    digest = canonical_sha(out)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print("V6_PRETRUTH_PRIMARY_FREEZE_BEGIN")
    print(json.dumps({
        "execution_form": out["execution_form"],
        "pretruth_sha256": digest,
        "primary_hashes": {panel: results[panel]["primary_ranking_sha256_before_truth"] for panel in ("hdbscan", "sugar")},
        "truth_accessed": False,
    }, indent=2, sort_keys=True))
    print("V6_PRETRUTH_PRIMARY_FREEZE_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
