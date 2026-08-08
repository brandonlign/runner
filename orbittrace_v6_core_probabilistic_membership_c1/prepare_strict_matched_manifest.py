#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from orbittrace_probabilistic_membership_p1_literature.prepare_strict_id_manifest import (
    BLIND_EXCLUSION,
    EXPECTED_COUNTS,
    YEARS,
    hdbscan_ids_only,
    sugar_ids_only,
)
from orbittrace_v6_literature_adapter.prepare_id_manifest import extract_background_ids


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--hdbscan-2023", required=True, type=Path)
    p.add_argument("--hdbscan-2025", required=True, type=Path)
    p.add_argument("--sugar-2023", required=True, type=Path)
    p.add_argument("--sugar-2025", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    exact = load_module(args.exact_row_runner, "orbittrace_c1_strict_manifest_exact")
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    assignment_paths = {
        "hdbscan": {2023: args.hdbscan_2023, 2025: args.hdbscan_2025},
        "sugar": {2023: args.sugar_2023, 2025: args.sugar_2025},
    }

    # Event-ID extraction is deliberately competitor-value-blind. The imported
    # helpers are source-audited to avoid JSON-decoding HDBSCAN cluster values and
    # to raw-decode only Sugar's event_ids array.
    ids: dict[str, dict[int, list[str]]] = {"hdbscan": {}, "sugar": {}}
    for year in YEARS:
        ids["hdbscan"][year] = hdbscan_ids_only(assignment_paths["hdbscan"][year], year)
        ids["sugar"][year] = sugar_ids_only(assignment_paths["sugar"][year], year)

    panels: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        panels[panel] = {}
        for year in YEARS:
            scan_ids = ids[panel][year]
            require(len(scan_ids) == EXPECTED_COUNTS[panel][year], f"exact row count changed {panel} {year}")
            scan_set = set(scan_ids)
            require(len(scan_set) == len(scan_ids), f"duplicate exact event ID {panel} {year}")
            # Calibration comes only from the native survey shower token for the
            # already-fixed exact row IDs. No competitor cluster value is used.
            background = extract_background_ids(year, archives[year], scan_set, exact)
            require(len(background) >= 1000, f"insufficient native background support {panel} {year}")
            panels[panel][str(year)] = {
                "scan_ids": scan_ids,
                "native_background_ids": sorted(background, key=lambda x: int(x.split(":", 1)[1])),
                "scan_count": len(scan_ids),
                "native_background_count": len(background),
            }

    payload = {
        "classification": "C1 matched-literature strict pretruth ID/native-background manifest",
        "years": list(YEARS),
        "blind_exclusion": list(BLIND_EXCLUSION),
        "competitor_cluster_values_parsed": False,
        "known_shower_truth_values_parsed": False,
        "native_shower_token_access_scope": "only native background/sporadic classification for already-fixed exact row IDs",
        "competitor_values_used_for_calibration": False,
        "panels": panels,
        "input_hashes": {
            "archive_2023": hashlib.sha256(args.archive_2023.read_bytes()).hexdigest(),
            "archive_2025": hashlib.sha256(args.archive_2025.read_bytes()).hexdigest(),
            "hdbscan_2023": hashlib.sha256(args.hdbscan_2023.read_bytes()).hexdigest(),
            "hdbscan_2025": hashlib.sha256(args.hdbscan_2025.read_bytes()).hexdigest(),
            "sugar_2023": hashlib.sha256(args.sugar_2023.read_bytes()).hexdigest(),
            "sugar_2025": hashlib.sha256(args.sugar_2025.read_bytes()).hexdigest(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    digest = canonical_sha(payload)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print("PASS_C1_STRICT_MATCHED_PRETRUTH_MANIFEST")
    print("manifest_sha256", digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
