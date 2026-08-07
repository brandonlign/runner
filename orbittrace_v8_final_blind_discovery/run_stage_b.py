#!/usr/bin/env python3
"""Frozen Stage B: verify Stage A first, then exact-ID reveal against a sealed reference bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")
MONTH_KEYS = tuple(
    [f"{year}-{month:02d}" for year in (2022, 2023, 2024, 2025) for month in range(1, 13)]
    + [f"2026-{month:02d}" for month in range(1, 8)]
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def zip_json(path: Path, suffix: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        names = [name for name in zf.namelist() if name.endswith(suffix)]
        require(len(names) == 1, f"expected exactly one {suffix}: {names}")
        return json.loads(zf.read(names[0]).decode("utf-8"))


def load_stage_a(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = zip_json(path, "stage_a_freeze.json")
    ranked = zip_json(path, "blind_families.json")
    require(freeze.get("schema") == "orbittrace-v8-stage-a-freeze-v1", "wrong Stage A freeze schema")
    require(freeze.get("verdict") == "PASS_STAGE_A_BLIND_DISCOVERY_FREEZE", "Stage A did not freeze successfully")
    require(freeze.get("withheld_reference_loaded") is False, "Stage A accessed withheld reference")
    require(freeze.get("target_identity_available") is False, "Stage A had target identity")
    require(freeze.get("source_labels_used") is False, "Stage A used source labels")
    require(all(freeze.get("integrity_gates", {}).values()), "Stage A integrity gates did not all pass")
    require(ranked.get("schema") == "orbittrace-v8-stage-a-ranked-families-v1", "wrong ranked-family schema")
    actual = sha256_json(ranked)
    require(actual == freeze.get("blind_families_sha256"), "Stage A inner ranked-family hash mismatch")
    families = ranked.get("families")
    require(isinstance(families, list) and len(families) == int(freeze.get("family_count", -1)), "Stage A family count mismatch")
    require([int(f["rank"]) for f in families] == list(range(1, len(families) + 1)), "Stage A ranks are not complete/unique")
    expected_order = sorted(
        families,
        key=lambda f: (-float(f["multiplicity_worst_year"]), -float(f["multiplicity_geometric_mean"]), str(f["family_id"])),
    )
    require([f["family_id"] for f in expected_order] == [f["family_id"] for f in families], "Stage A ranking does not reproduce frozen sort")
    sealed = str(freeze.get("sealed_withheld_reference_artifact_sha256", ""))
    require(bool(HEX64.fullmatch(sealed)), "Stage A did not seal a withheld-reference artifact hash")
    return freeze, ranked


def preflight(stage_a_artifact: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    freeze, ranked = load_stage_a(stage_a_artifact)
    result = {
        "schema": "orbittrace-v8-stage-b-preflight-v1",
        "verdict": "PASS_STAGE_B_PREFLIGHT_BEFORE_REFERENCE_ACCESS",
        "stage_a_blind_families_sha256": freeze["blind_families_sha256"],
        "sealed_withheld_reference_artifact_sha256": freeze["sealed_withheld_reference_artifact_sha256"],
        "family_count": len(ranked["families"]),
        "withheld_reference_access": False,
    }
    (output / "stage_b_preflight.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def load_reference(path: Path, expected_zip_sha256: str) -> dict[str, Any]:
    actual_zip_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual_zip_sha == expected_zip_sha256, "withheld-reference ZIP does not match hash sealed before Stage A")
    reference = zip_json(path, "withheld_reference.json")
    require(set(reference) == {"schema", "events"}, "withheld reference must contain only schema and events")
    require(reference.get("schema") == "orbittrace-withheld-reference-v1", "wrong withheld-reference schema")
    events = reference.get("events")
    require(isinstance(events, list) and events, "withheld-reference event list is empty")
    ids: set[str] = set()
    for event in events:
        require(isinstance(event, dict) and set(event) == {"event_id", "month_key"}, "reference events must contain only event_id and month_key")
        event_id = str(event["event_id"])
        month_key = str(event["month_key"])
        require(event_id and event_id not in ids, "withheld-reference IDs must be nonempty and unique")
        require(month_key in MONTH_KEYS, f"reference event outside frozen Stage A month universe: {month_key}")
        ids.add(event_id)
    return reference


def classify_family(family: dict[str, Any], reference_ids: set[str], reference_year: dict[str, int]) -> dict[str, Any]:
    family_ids = set(map(str, family["event_ids"]))
    overlap_ids = sorted(family_ids & reference_ids)
    per_year = Counter(reference_year[event_id] for event_id in overlap_ids)
    overlap = len(overlap_ids)
    precision = overlap / int(family["event_count"]) if int(family["event_count"]) else 0.0
    full = bool(
        int(family["rank"]) <= 25
        and int(family["year_count"]) >= 4
        and overlap >= 16
        and sum(count >= 4 for count in per_year.values()) >= 3
    )
    partial = bool(
        int(family["rank"]) <= 100
        and int(family["year_count"]) >= 3
        and overlap >= 12
        and sum(count >= 4 for count in per_year.values()) >= 2
    )
    return {
        "rank": int(family["rank"]),
        "family_id": str(family["family_id"]),
        "family_year_count": int(family["year_count"]),
        "family_event_count": int(family["event_count"]),
        "overlap": overlap,
        "overlap_ids": overlap_ids,
        "overlap_by_year": {str(year): int(per_year[year]) for year in sorted(per_year)},
        "precision": float(precision),
        "full_rule": full,
        "partial_rule": partial,
    }


def select_best(rows: list[dict[str, Any]]) -> dict[str, Any]:
    require(rows, "cannot select from empty rows")
    return sorted(rows, key=lambda r: (int(r["rank"]), -int(r["overlap"]), -float(r["precision"]), str(r["family_id"])))[0]


def reveal(stage_a_artifact: Path, preflight_json: Path, reference_artifact: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    pre = json.loads(preflight_json.read_text())
    require(pre.get("verdict") == "PASS_STAGE_B_PREFLIGHT_BEFORE_REFERENCE_ACCESS", "Stage B preflight missing/failed")
    require(pre.get("withheld_reference_access") is False, "preflight had reference access")
    freeze, ranked = load_stage_a(stage_a_artifact)
    require(pre.get("stage_a_blind_families_sha256") == freeze["blind_families_sha256"], "preflight/Stage A hash mismatch")
    reference = load_reference(reference_artifact, str(freeze["sealed_withheld_reference_artifact_sha256"]))
    reference_ids = {str(event["event_id"]) for event in reference["events"]}
    reference_year = {str(event["event_id"]): int(str(event["month_key"])[:4]) for event in reference["events"]}
    rows = [classify_family(family, reference_ids, reference_year) for family in ranked["families"]]
    full = [row for row in rows if row["full_rule"]]
    partial = [row for row in rows if row["partial_rule"]]
    if full:
        verdict = "FULL_BLIND_INDEPENDENT_RECOVERY"
        selected = select_best(full)
    elif partial:
        verdict = "PARTIAL_BLIND_INDEPENDENT_RECOVERY"
        selected = select_best(partial)
    else:
        verdict = "NO_BLIND_INDEPENDENT_RECOVERY"
        selected = select_best([row for row in rows if row["overlap"] > 0]) if any(row["overlap"] > 0 for row in rows) else None
    result = {
        "schema": "orbittrace-v8-stage-b-reveal-v1",
        "verdict": verdict,
        "stage_a_blind_families_sha256": freeze["blind_families_sha256"],
        "withheld_reference_artifact_sha256": hashlib.sha256(reference_artifact.read_bytes()).hexdigest(),
        "reference_event_count": len(reference_ids),
        "matching_rule": "exact stable GMN event-ID equality; zero tolerance",
        "full_rule": {"rank_max": 25, "family_years_min": 4, "overlap_min": 16, "years_with_overlap_ge4_min": 3},
        "partial_rule": {"rank_max": 100, "family_years_min": 3, "overlap_min": 12, "years_with_overlap_ge4_min": 2},
        "selected_family": selected,
        "all_family_overlaps": rows,
        "family_structure_or_rank_modified": False,
    }
    (output / "stage_b_reveal.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = [
        "# Stage B reveal",
        "",
        f"`{verdict}`",
        "",
        f"- Stage A ranked-family SHA-256: `{freeze['blind_families_sha256']}`",
        f"- reference event count: **{len(reference_ids)}**",
        "- matching: **exact event-ID equality (zero tolerance)**",
    ]
    if selected is not None:
        md += [f"- selected blind rank: **{selected['rank']}**", f"- exact overlap: **{selected['overlap']}**"]
    (output / "STAGE_B_REVEAL.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"verdict": verdict, "selected_family": selected}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("preflight")
    a.add_argument("--stage-a-artifact", required=True, type=Path)
    a.add_argument("--output", required=True, type=Path)
    b = sub.add_parser("reveal")
    b.add_argument("--stage-a-artifact", required=True, type=Path)
    b.add_argument("--preflight-json", required=True, type=Path)
    b.add_argument("--reference-artifact", required=True, type=Path)
    b.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.command == "preflight":
        return preflight(args.stage_a_artifact, args.output)
    return reveal(args.stage_a_artifact, args.preflight_json, args.reference_artifact, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
