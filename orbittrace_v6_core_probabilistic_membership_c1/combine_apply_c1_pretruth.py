#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

YEARS = (2023, 2025)
BLIND_EXCLUSION = (20.0, 55.0)
C1_SOURCE_SHA256 = "113c579f2058126e93b93a3534aaa6108d3e827c667552ecd41ff321d7a5e3da"
P1_SOURCE_SHA256 = "e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508"
P1_TRANSFER_COMMIT = "785554905113626bebffecdd441616238eb76b04"
P1_TRANSFER_GIT_BLOB = "498daf762bc82a664679998ea751feecff8033de"
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_checkpoint(path: Path, panel: str, year: int, manifest_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip().split()[0] == hashlib.sha256(raw).hexdigest(),
            f"checkpoint SHA mismatch {panel} {year}")
    obj = pickle.loads(raw)
    require(obj["classification"] == "v6 exact-row pretruth panel-year checkpoint", f"wrong checkpoint type {panel} {year}")
    require(obj["panel"] == panel and int(obj["year"]) == year, f"checkpoint identity changed {panel} {year}")
    require(obj["id_manifest_sha256"] == manifest_sha, f"manifest mismatch {panel} {year}")
    require(obj["blind_exclusion"] == [20.0, 55.0], f"blind exclusion changed {panel} {year}")
    require(obj["truth_accessed"] is False, f"truth entered pretruth checkpoint {panel} {year}")
    require(obj["mapping_accessed"] is False, f"mapping entered pretruth checkpoint {panel} {year}")
    require(obj["competitor_cluster_labels_accessed"] is False, f"competitor labels entered pretruth checkpoint {panel} {year}")
    require(obj["audit"]["proposal_cap_per_window"] == 512, f"proposal cap changed {panel} {year}")
    require(obj["audit"]["max_primary_proposals_per_year"] == 36864, f"annual budget changed {panel} {year}")
    return obj


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", required=True, choices=("hdbscan", "sugar"))
    p.add_argument("--strict-manifest", required=True, type=Path)
    p.add_argument("--checkpoint-2023", required=True, type=Path)
    p.add_argument("--checkpoint-2025", required=True, type=Path)
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--p1-source", required=True, type=Path)
    p.add_argument("--p1-transfer-runner", required=True, type=Path)
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.v6_source) == REPAIRED_V6_SHA256, "repaired v6 source changed")
    require(sha256_file(args.p1_source) == P1_SOURCE_SHA256, "P1 scientific source changed")

    manifest = json.loads(args.strict_manifest.read_text())
    require(manifest["classification"] == "C1 matched-literature strict pretruth ID/native-background manifest", "wrong C1 manifest type")
    require(manifest["years"] == list(YEARS), "manifest years changed")
    require(manifest["blind_exclusion"] == list(BLIND_EXCLUSION), "manifest blind interval changed")
    require(manifest["competitor_cluster_values_parsed"] is False, "competitor cluster values entered manifest")
    require(manifest["known_shower_truth_values_parsed"] is False, "known-shower truth entered manifest")
    require(manifest["competitor_values_used_for_calibration"] is False, "competitor values entered calibration")
    manifest_sha = canonical_sha(manifest)
    sidecar = args.strict_manifest.with_suffix(args.strict_manifest.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip() == manifest_sha, "strict manifest SHA mismatch")

    checkpoints = {
        2023: load_checkpoint(args.checkpoint_2023, args.panel, 2023, manifest_sha),
        2025: load_checkpoint(args.checkpoint_2025, args.panel, 2025, manifest_sha),
    }

    v6 = load_module(args.v6_source, f"orbittrace_c1_matched_v6_{args.panel}")
    old = load_module(args.base_runner, f"orbittrace_c1_matched_base_{args.panel}")
    p1 = load_module(args.p1_source, f"orbittrace_c1_matched_p1_{args.panel}")
    transfer = load_module(args.p1_transfer_runner, f"orbittrace_c1_matched_membership_{args.panel}")
    exact = load_module(args.exact_row_runner, f"orbittrace_c1_matched_exact_rows_{args.panel}")
    require(tuple(transfer.YEARS) == YEARS, "P1 transfer year tuple changed")
    require(hasattr(transfer, "apply_exact_p1_membership"), "shared P1 membership function unavailable")

    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    scan_ids = {
        year: set(map(str, manifest["panels"][args.panel][str(year)]["scan_ids"]))
        for year in YEARS
    }
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    scan_by_year = {
        year: exact.read_exact_geometry(year, archives[year], scan_ids[year], base)
        for year in YEARS
    }
    for year in YEARS:
        require(len(scan_by_year[year]) == int(manifest["panels"][args.panel][str(year)]["scan_count"]),
                f"exact row count changed {args.panel} {year}")
        require(all(not (BLIND_EXCLUSION[0] <= float(e["sol"]) <= BLIND_EXCLUSION[1]) for e in scan_by_year[year]),
                f"target interval entered C1 matched scan {args.panel} {year}")

    all_components = checkpoints[2023]["components"] + checkpoints[2025]["components"]
    primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
    require(primary_families, f"no primary families {args.panel}")
    rank_order = [str(f["family_id"]) for f in primary_families]
    require(len(rank_order) == len(set(rank_order)), f"duplicate primary family ID {args.panel}")

    expanded, diagnostics = transfer.apply_exact_p1_membership(p1, primary_families, scan_by_year, base)
    require([str(f["family_id"]) for f in expanded] == rank_order, f"C1 changed v6 rank {args.panel}")
    for i, family in enumerate(primary_families):
        seeds = set(map(str, family["event_ids"]))
        members = set(map(str, expanded[i]["event_ids"]))
        require(seeds <= members, f"C1 removed seed family={family['family_id']}")

    payload = {
        "classification": "C1 matched-literature pretruth panel checkpoint",
        "panel": args.panel,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND_EXCLUSION),
        "c1_source_sha256": C1_SOURCE_SHA256,
        "v6_source_sha256": REPAIRED_V6_SHA256,
        "p1_source_sha256": P1_SOURCE_SHA256,
        "p1_transfer_commit": P1_TRANSFER_COMMIT,
        "p1_transfer_git_blob": P1_TRANSFER_GIT_BLOB,
        "strict_manifest_sha256": manifest_sha,
        "exact_event_rows": {str(y): len(scan_by_year[y]) for y in YEARS},
        "v6_primary_families": primary_families,
        "v6_primary_rank": rank_order,
        "v6_primary_rank_pretruth_sha256": canonical_sha(rank_order),
        "v6_seed_families_pretruth_sha256": canonical_sha(primary_families),
        "c1_expanded_families": expanded,
        "c1_membership_pretruth_sha256": canonical_sha(expanded),
        "c1_diagnostics": diagnostics,
        "pretruth": {
            "competitor_cluster_values_accessed": False,
            "known_shower_truth_accessed": False,
            "fixed4_rescue_can_seed_c1": False,
            "new_members_can_seed_or_refit": False,
            "rank_and_membership_frozen_before_truth": True,
        },
        "year_audits": {str(y): checkpoints[y]["audit"] for y in YEARS},
    }
    args.output.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
    digest = sha256_file(args.output)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print(
        f"PASS_C1_MATCHED_PRETRUTH panel={args.panel} families={len(primary_families)} "
        f"assigned={diagnostics['assigned_nonseed_events']} checkpoint_sha={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
