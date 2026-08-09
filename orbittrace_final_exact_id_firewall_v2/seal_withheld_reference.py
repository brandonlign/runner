#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

SOURCE_SCHEMA = "orbittrace-withheld-reference-v1"
SEALED_SCHEMA = "orbittrace-withheld-exact-ids-v2"
SEAL_SCHEMA = "orbittrace-withheld-exact-ids-seal-v1"
YEARS = (2022, 2023)
SOURCE_MONTH_RE = re.compile(r"^(202[2-5]-(0[1-9]|1[0-2])|2026-0[1-7])$")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source(zip_path: Path) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".json"):
                continue
            try:
                obj = json.loads(zf.read(info).decode("utf-8"))
            except Exception:
                continue
            if isinstance(obj, dict) and obj.get("schema") == SOURCE_SCHEMA:
                matches.append(obj)
    require(len(matches) == 1, "source artifact must contain exactly one withheld-reference-v1 JSON")
    return matches[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-zip", required=True, type=Path)
    p.add_argument("--source-artifact-id", required=True)
    p.add_argument("--source-zip-sha256", required=True)
    p.add_argument("--seal-run-id", required=True)
    p.add_argument("--freeze-commit", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(re.fullmatch(r"[0-9]+", str(args.source_artifact_id)) is not None, "source artifact ID invalid")
    require(re.fullmatch(r"[0-9a-f]{64}", str(args.source_zip_sha256)) is not None, "source ZIP SHA invalid")
    require(re.fullmatch(r"[0-9]+", str(args.seal_run_id)) is not None, "seal run ID invalid")
    require(re.fullmatch(r"[0-9a-f]{40}", str(args.freeze_commit)) is not None, "freeze commit invalid")
    require(file_sha(args.source_zip) == args.source_zip_sha256, "source withheld-reference ZIP digest changed")

    source = load_source(args.source_zip)
    require(set(source) == {"schema", "events"}, "source withheld reference contains unexpected top-level fields")
    events = source["events"]
    require(isinstance(events, list) and events, "source withheld reference events missing")

    sealed_events: list[dict[str, Any]] = []
    seen: set[str] = set()
    by_year = {year: 0 for year in YEARS}
    for row in events:
        require(isinstance(row, dict) and set(row) == {"event_id", "month_key"}, "source event contains non-ID fields")
        event_id = str(row["event_id"])
        month_key = str(row["month_key"])
        require(event_id and event_id not in seen, "blank/duplicate source event ID")
        require(SOURCE_MONTH_RE.fullmatch(month_key) is not None, "source month key is outside frozen historical schema")
        seen.add(event_id)
        year = int(month_key[:4])
        if year not in YEARS:
            # Historical reference can include later years. Final exact-ID recovery is
            # preregistered only on GMN 2022/2023, so later years are deterministically dropped.
            continue
        sealed_events.append({"id": event_id, "year": year})
        by_year[year] += 1

    require(all(by_year[year] > 0 for year in YEARS), "withheld reference lacks one frozen discovery year")
    sealed_events.sort(key=lambda row: (int(row["year"]), str(row["id"])))
    payload = {
        "schema": SEALED_SCHEMA,
        "events": sealed_events,
        "provenance": {
            "source_schema": SOURCE_SCHEMA,
            "source_artifact_id": str(args.source_artifact_id),
            "source_zip_sha256": str(args.source_zip_sha256),
            "transform": "exact event_id + deterministic month_key year extraction; retain 2022/2023 only",
            "freeze_commit": str(args.freeze_commit),
        },
    }
    payload_sha = canonical_sha(payload)
    payload_path = args.output / "withheld_exact_ids.json"
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (args.output / "withheld_exact_ids.json.sha256").write_text(payload_sha + "\n")

    seal = {
        "schema": SEAL_SCHEMA,
        "freeze_commit": str(args.freeze_commit),
        "seal_run_id": str(args.seal_run_id),
        "source_reference_artifact_id": str(args.source_artifact_id),
        "source_reference_zip_sha256": str(args.source_zip_sha256),
        "sealed_payload_sha256": payload_sha,
        "sealed_payload_schema": SEALED_SCHEMA,
        "discovery_years": list(YEARS),
        "target_ids_logged": False,
        "target_counts_logged": False,
        "coordinates_or_orbits_permitted": False,
    }
    (args.output / "seal_manifest.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    print("PASS_ORBITTRACE_WITHHELD_EXACT_ID_SEAL")
    print(f"SEALED_PAYLOAD_SHA256={payload_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
