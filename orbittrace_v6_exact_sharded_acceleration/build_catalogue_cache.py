from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

from orbittrace_v6_checkpointed_fallback.common import event_rows_sha256, load_module, require, sha256_bytes
from orbittrace_v6_exact_sharded_acceleration.common import FROZEN_V6_SHA256, REPAIRED_V6_SHA256


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repaired-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_bytes(args.repaired_source.read_bytes()) == REPAIRED_V6_SHA256, "repaired v6 hash changed")
    v6 = load_module(args.repaired_source, "orbittrace_v6_accel_catalogue_cache")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    del candidate, scorer

    print("V6_ACCEL_CATALOGUE_PARSE_START", flush=True)
    scan_by_year, calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    # The support parser already replaces every scan label with iau=0/complex_key=HIDDEN
    # and calibration labels with iau=0/complex_key=SPORADIC after the blind exclusion.
    for year in (2022, 2023):
        require(all(int(row.get("iau", -1)) == 0 for row in scan_by_year[year]), f"scan label sentinel changed {year}")
        require(all(str(row.get("complex_key")) == "HIDDEN" for row in scan_by_year[year]), f"scan hidden sentinel changed {year}")
        require(all(int(row.get("iau", -1)) == 0 for row in calibration_by_year[year]), f"calibration label sentinel changed {year}")
        require(all(str(row.get("complex_key")) == "SPORADIC" for row in calibration_by_year[year]), f"calibration sentinel changed {year}")
    # Do not serialize hidden_labels. They remain only in this process and are discarded.
    del hidden_labels

    source_hashes = {}
    for year in (2022, 2023):
        source_rows = [row for row in sources if str(row.get("key", "")).startswith(str(year))]
        source_hashes[str(year)] = hashlib.sha256(
            json.dumps(source_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()

    payload = {
        "format": "orbittrace-v6-target-excluded-catalogue-cache-v1",
        "frozen_v6_sha256": FROZEN_V6_SHA256,
        "repaired_v6_sha256": REPAIRED_V6_SHA256,
        "scan_by_year": {year: scan_by_year[year] for year in (2022, 2023)},
        "calibration_by_year": {year: calibration_by_year[year] for year in (2022, 2023)},
        "sources": sources,
        "year_sources_sha256": source_hashes,
        "hashes": {
            str(year): {
                "scan": event_rows_sha256(scan_by_year[year]),
                "calibration": event_rows_sha256(calibration_by_year[year]),
            }
            for year in (2022, 2023)
        },
        "firewall": {
            "target_interval_remains_excluded": True,
            "real_hidden_labels_not_serialized": True,
            "scan_label_fields_are_sentinels_only": True,
        },
    }
    raw = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / "catalogue_cache.pkl"
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    (args.output / "catalogue_cache.sha256").write_text(digest + "\n")
    manifest = {
        "checkpoint_sha256": digest,
        "scan_rows": {str(year): len(scan_by_year[year]) for year in (2022, 2023)},
        "calibration_rows": {str(year): len(calibration_by_year[year]) for year in (2022, 2023)},
        "hashes": payload["hashes"],
        "year_sources_sha256": source_hashes,
        "sources": sources,
        "firewall": payload["firewall"],
    }
    (args.output / "catalogue_cache.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("V6_ACCEL_CATALOGUE_PARSE_DONE", json.dumps({k: manifest[k] for k in ("scan_rows", "calibration_rows")}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
