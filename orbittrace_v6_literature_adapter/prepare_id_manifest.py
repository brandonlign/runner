#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import zipfile
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


def extract_background_ids(year: int, archive: Path, requested: set[str], exact: Any) -> set[str]:
    """Read only sol + native shower token for already-fixed exact event IDs."""
    require(year in adapter.YEARS, f"unexpected year {year}")
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == exact.ARCHIVE_SHA256[year],
            f"archive hash changed {year}")
    prefix = f"SNM{year}:"
    row_indices: dict[int, str] = {}
    for event_id in requested:
        require(event_id.startswith(prefix), f"wrong-year event ID {event_id}")
        idx = int(event_id.split(":", 1)[1])
        require(idx >= 0 and idx not in row_indices, f"invalid/duplicate event ID {event_id}")
        row_indices[idx] = event_id

    found: set[str] = set()
    background: set[str] = set()
    with zipfile.ZipFile(archive) as zf:
        member = exact.MEMBERS[year]
        require(member in zf.namelist(), f"missing archive member {member}")
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            header = next(reader)
            while header and header[-1].strip() == "":
                header = header[:-1]
            names = [exact.norm_header(x) for x in header]
            require("soldeg" in names and "shower" in names, f"missing native fields {year}")
            sol_col = names.index("soldeg")
            shower_col = names.index("shower")
            width = len(header)
            for row_index, raw_row in enumerate(reader):
                event_id = row_indices.get(row_index)
                if event_id is None:
                    continue
                row = list(raw_row)
                while len(row) > width and row[-1].strip() == "":
                    row.pop()
                require(len(row) >= width, f"short requested row {event_id}")
                try:
                    sol = float(row[sol_col]) % 360.0
                except Exception as exc:
                    raise RuntimeError(f"invalid solar longitude {event_id}") from exc
                require(math.isfinite(sol), f"nonfinite solar longitude {event_id}")
                require(not (adapter.BLIND_LOW <= sol <= adapter.BLIND_HIGH),
                        f"requested exact row enters target interval {event_id}")
                token = row[shower_col]
                if adapter.native_background_token(token):
                    background.add(event_id)
                found.add(event_id)

    require(found == requested, f"native-token row universe mismatch {year}")
    return background


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

    exact = load_module(args.exact_row_runner, "orbittrace_frozen_exact_row_manifest")
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    assignments = {
        "hdbscan": {
            2023: exact.load_hdbscan(args.hdbscan_2023, 2023),
            2025: exact.load_hdbscan(args.hdbscan_2025, 2025),
        },
        "sugar": {
            2023: exact.load_sugar(args.sugar_2023, 2023),
            2025: exact.load_sugar(args.sugar_2025, 2025),
        },
    }

    panels: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        panels[panel] = {}
        for year in adapter.YEARS:
            scan_ids = set(assignments[panel][year])
            background_ids = extract_background_ids(year, archives[year], scan_ids, exact)
            require(len(scan_ids) >= 1000 and len(background_ids) >= 1000,
                    f"insufficient exact-row/calibration support {panel} {year}")
            panels[panel][str(year)] = {
                "scan_ids": sorted(scan_ids, key=lambda x: int(x.split(":", 1)[1])),
                "native_background_ids": sorted(background_ids, key=lambda x: int(x.split(":", 1)[1])),
                "scan_count": len(scan_ids),
                "native_background_count": len(background_ids),
            }

    payload = {
        "classification": "pretruth exact-row ID-only manifest",
        "years": list(adapter.YEARS),
        "blind_exclusion": [adapter.BLIND_LOW, adapter.BLIND_HIGH],
        "native_background_rule": "exact source-audited SonotaCo 2023/2025 background_token; no mapping; no ESV",
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
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(hashlib.sha256(canonical).hexdigest() + "\n")
    print("PASS_V6_PRETRUTH_ID_MANIFEST")
    print("manifest_sha256", hashlib.sha256(canonical).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
