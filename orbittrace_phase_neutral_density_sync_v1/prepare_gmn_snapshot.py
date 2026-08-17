#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import run_development as parent_runner

YEARS = parent_runner.YEARS
MONTH_KEYS = parent_runner.MONTH_KEYS
BLIND = parent_runner.BLIND


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            for row in rows:
                payload = json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
                gz.write(payload + b"\n")


def write_json_gz(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(payload)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--label-free-output", type=Path, required=True)
    ap.add_argument("--truth-output", type=Path, required=True)
    a = ap.parse_args()
    a.label_free_output.mkdir(parents=True, exist_ok=True)
    a.truth_output.mkdir(parents=True, exist_ok=True)

    req(parent_runner.sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(parent_runner.sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")
    qmod = parent_runner.load_module(a.quality_source, "phase_neutral_snapshot_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-phase-neutral-density-sync-v1-snapshot-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    ids: set[str] = set()
    counts: dict[str, int] = {}
    row_paths: dict[str, str] = {}
    row_shas: dict[str, str] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"normalization changed {year} count")
        req(all(not (BLIND[0] <= float(row["sol"]) <= BLIND[1]) for row in rows), f"protected region survived {year}")
        for row in rows:
            eid = str(row["id"])
            req(eid not in ids, f"duplicate event id {eid}")
            ids.add(eid)
        path = a.label_free_output / f"gmn_{year}_rows.jsonl.gz"
        write_jsonl_gz(path, rows)
        counts[str(year)] = len(rows)
        row_paths[str(year)] = path.name
        row_shas[str(year)] = sha(path)

    req(all(eid in ids for eid in hidden_sealed), "hidden truth contains event outside accessible snapshot")
    # The truth payload is sealed into its own artifact and is not copied into the label-free root.
    truth_rows = [[str(eid), str(label)] for eid, label in sorted(hidden_sealed.items())]
    truth_path = a.truth_output / "gmn_truth.json.gz"
    write_json_gz(truth_path, truth_rows)
    truth_sha = sha(truth_path)

    label_manifest = {
        "schema": "ORBITTRACE_PHASE_NEUTRAL_GMN_LABEL_FREE_SNAPSHOT_V1",
        "scientific_role": "METHOD_INDEPENDENT_TARGET_EXCLUDED_GMN_2022_2023_SNAPSHOT",
        "years": list(YEARS),
        "events_by_year": counts,
        "events_total": sum(counts.values()),
        "source_keys": [x["key"] for x in sources],
        "row_files": row_paths,
        "row_sha256": row_shas,
        "blind_exclusion": list(BLIND),
        "event_order_preserved": True,
        "labels_present": False,
        "hdbscan_fit_executed": False,
        "method_evaluation_executed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    label_manifest_path = a.label_free_output / "manifest.json"
    label_manifest_path.write_text(json.dumps(label_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")

    truth_manifest = {
        "schema": "ORBITTRACE_PHASE_NEUTRAL_GMN_SEALED_TRUTH_V1",
        "scientific_role": "SEALED_TRUTH_FOR_PAIRED_WITHIN_SNAPSHOT_DEVELOPMENT_ONLY",
        "truth_file": truth_path.name,
        "truth_sha256": truth_sha,
        "truth_entries": len(truth_rows),
        "accessible_event_count": len(ids),
        "blind_exclusion": list(BLIND),
        "method_evaluation_executed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    truth_manifest_path = a.truth_output / "manifest.json"
    truth_manifest_path.write_text(json.dumps(truth_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")

    print(json.dumps({
        "label_free_manifest_sha256": sha(label_manifest_path),
        "truth_manifest_sha256": sha(truth_manifest_path),
        "events_by_year": counts,
        "events_total": len(ids),
        "truth_entries": len(truth_rows),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
