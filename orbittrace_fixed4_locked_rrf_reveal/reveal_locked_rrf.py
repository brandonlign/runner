#!/usr/bin/env python3
"""Reveal OrbitTrace identifiers against an immutable locked-RRF family ranking."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_SCAN_VERDICT = "LOCKED_RRF_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL"
EXPECTED_LOCKED_RRF = {
    "persistence_weight": 0.66,
    "secondary_weight": 0.34,
    "constant": 60.0,
    "secondary_rank": "min_year_strength",
}
EXPECTED_CANONICAL_COUNTS = {2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
EXPECTED_CANONICAL_TOTAL = 95
CANONICAL_MEMBER_PATH = (
    "reconstruction/exact_downstream/primary/april_candidate_members.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-artifact", required=True, type=Path)
    parser.add_argument("--canonical-artifact", required=True, type=Path)
    parser.add_argument("--expected-scan-payload-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_names(handle: zipfile.ZipFile) -> list[str]:
    names = handle.namelist()
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"unsafe ZIP member: {name}")
    if handle.testzip() is not None:
        raise RuntimeError("ZIP CRC failure")
    return names


def unique_suffix(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one member ending in {suffix!r}, found {matches}")
    return matches[0]


def load_scan(path: Path, expected_payload_sha256: str) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_payload = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(artifact_payload)) as handle:
        names = safe_names(handle)
        scan_name = unique_suffix(names, "orbittrace_fixed4_locked_rrf_scan.json.gz")
        scan_payload = handle.read(scan_name)
        hash_names = [name for name in names if name.endswith("locked_rrf_scan_sha256.txt")]
        if len(hash_names) != 1:
            raise RuntimeError(f"expected one internal scan hash file, found {hash_names}")
        recorded = handle.read(hash_names[0]).decode("utf-8").split()[0]
    actual = sha256_bytes(scan_payload)
    if actual != expected_payload_sha256 or recorded != expected_payload_sha256:
        raise RuntimeError(
            f"scan payload hash mismatch: actual={actual}, recorded={recorded}, "
            f"expected={expected_payload_sha256}"
        )
    scan = json.loads(gzip.decompress(scan_payload))
    if scan.get("verdict") != EXPECTED_SCAN_VERDICT:
        raise RuntimeError(f"unexpected scan verdict: {scan.get('verdict')}")
    if scan.get("configuration", {}).get("locked_rrf") != EXPECTED_LOCKED_RRF:
        raise RuntimeError("locked RRF formula changed")
    families = scan.get("families")
    ranking = scan.get("rankings", {}).get("locked_rrf")
    if not isinstance(families, list) or not families:
        raise RuntimeError("scan has no families")
    if not isinstance(ranking, list) or len(ranking) != len(families):
        raise RuntimeError("locked-RRF ranking is missing or incomplete")
    family_ids = [str(family.get("family_id")) for family in families]
    if len(set(family_ids)) != len(family_ids) or set(family_ids) != set(map(str, ranking)):
        raise RuntimeError("family universe and locked-RRF ranking differ")
    return scan, {
        "scan_artifact_sha256": sha256_bytes(artifact_payload),
        "scan_payload_sha256": actual,
        "scan_payload_bytes": len(scan_payload),
        "scan_member": scan_name,
    }


def load_canonical(path: Path) -> tuple[set[str], dict[int, set[str]], dict[str, Any]]:
    artifact_payload = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(artifact_payload)) as outer:
        outer_names = safe_names(outer)
        bundle_name = unique_suffix(outer_names, "GhostStream_Expert_Review_Bundle.zip")
        bundle_payload = outer.read(bundle_name)
    with zipfile.ZipFile(io.BytesIO(bundle_payload)) as bundle:
        bundle_names = safe_names(bundle)
        member_name = unique_suffix(bundle_names, CANONICAL_MEMBER_PATH)
        member_payload = bundle.read(member_name)
    rows = list(csv.DictReader(io.StringIO(member_payload.decode("utf-8-sig"))))
    by_year: dict[int, set[str]] = {year: set() for year in EXPECTED_CANONICAL_COUNTS}
    for row in rows:
        year = int(row["year"])
        if year not in by_year:
            continue
        event_id = str(row["unique_trajectory_identifier"]).strip()
        if not event_id:
            raise RuntimeError("blank canonical trajectory identifier")
        by_year[year].add(event_id)
    counts = {year: len(values) for year, values in by_year.items()}
    if counts != EXPECTED_CANONICAL_COUNTS:
        raise RuntimeError(f"canonical year counts changed: {counts}")
    all_ids = set().union(*by_year.values())
    if len(all_ids) != EXPECTED_CANONICAL_TOTAL:
        raise RuntimeError(f"canonical total changed: {len(all_ids)}")
    return all_ids, by_year, {
        "canonical_artifact_sha256": sha256_bytes(artifact_payload),
        "canonical_bundle_sha256": sha256_bytes(bundle_payload),
        "canonical_member_table_sha256": sha256_bytes(member_payload),
        "canonical_member_path": member_name,
        "canonical_counts": {str(year): count for year, count in counts.items()},
        "canonical_members": len(all_ids),
    }


def evaluate_family(
    family: dict[str, Any],
    rank: int,
    canonical_ids: set[str],
    canonical_by_year: dict[int, set[str]],
) -> dict[str, Any]:
    event_ids = {str(value) for value in family.get("event_ids", [])}
    overlap_ids = sorted(event_ids & canonical_ids)
    overlap_by_year = {
        str(year): len(event_ids & canonical_by_year[year])
        for year in sorted(canonical_by_year)
    }
    years_with_four = sum(value >= 4 for value in overlap_by_year.values())
    year_count = int(family.get("year_count", len(family.get("years", []))))
    full = (
        rank <= 25
        and year_count >= 4
        and len(overlap_ids) >= 16
        and years_with_four >= 3
    )
    partial = (
        rank <= 100
        and year_count >= 3
        and len(overlap_ids) >= 12
        and years_with_four >= 2
    )
    event_count = len(event_ids)
    return {
        "family_id": str(family["family_id"]),
        "locked_rrf_rank": rank,
        "year_count": year_count,
        "years": [int(value) for value in family.get("years", [])],
        "event_count": event_count,
        "quartet_count": int(family.get("quartet_count", 0)),
        "anchor_count": int(family.get("anchor_count", 0)),
        "persistence_rank": int(family.get("ranks", {}).get("persistence", 0)),
        "min_year_strength_rank": int(family.get("ranks", {}).get("min_year_strength", 0)),
        "canonical_overlap": len(overlap_ids),
        "canonical_overlap_ids": overlap_ids,
        "canonical_overlap_by_year": overlap_by_year,
        "years_with_at_least_four_canonical": years_with_four,
        "precision": (len(overlap_ids) / event_count) if event_count else 0.0,
        "canonical_recall": len(overlap_ids) / EXPECTED_CANONICAL_TOTAL,
        "passes_full_rule": full,
        "passes_partial_rule": partial,
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    scan, scan_audit = load_scan(args.scan_artifact, args.expected_scan_payload_sha256)
    canonical_ids, canonical_by_year, canonical_audit = load_canonical(args.canonical_artifact)

    family_lookup = {str(family["family_id"]): family for family in scan["families"]}
    ordered_ids = [str(value) for value in scan["rankings"]["locked_rrf"]]
    evaluations = [
        evaluate_family(family_lookup[family_id], rank, canonical_ids, canonical_by_year)
        for rank, family_id in enumerate(ordered_ids, start=1)
    ]
    full_hits = [row for row in evaluations if row["passes_full_rule"]]
    partial_hits = [row for row in evaluations if row["passes_partial_rule"]]
    if full_hits:
        verdict = "FULL_LOCKED_RRF_ORBITTRACE_RECOVERY"
        selected = min(full_hits, key=lambda row: row["locked_rrf_rank"])
    elif partial_hits:
        verdict = "PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY"
        selected = min(partial_hits, key=lambda row: row["locked_rrf_rank"])
    else:
        verdict = "NO_LOCKED_RRF_ORBITTRACE_RECOVERY"
        selected = max(
            evaluations,
            key=lambda row: (
                row["canonical_overlap"],
                row["years_with_at_least_four_canonical"],
                -row["locked_rrf_rank"],
            ),
        )

    top_overlap = sorted(
        [row for row in evaluations if row["canonical_overlap"] > 0],
        key=lambda row: (-row["canonical_overlap"], row["locked_rrf_rank"]),
    )[:25]
    result = {
        "verdict": verdict,
        "classification": (
            "exact identifier reveal against a ranking frozen before canonical access; no family was "
            "merged, rescored, reranked, or replaced during reveal"
        ),
        "criteria": {
            "full": {
                "maximum_rank": 25,
                "minimum_years": 4,
                "minimum_overlap": 16,
                "minimum_years_with_four_members": 3,
            },
            "partial": {
                "maximum_rank": 100,
                "minimum_years": 3,
                "minimum_overlap": 12,
                "minimum_years_with_four_members": 2,
            },
        },
        "locked_rrf": EXPECTED_LOCKED_RRF,
        "family_count": len(evaluations),
        "scan_audit": scan_audit,
        "canonical_audit": canonical_audit,
        "full_rule_hits": [row["family_id"] for row in full_hits],
        "partial_rule_hits": [row["family_id"] for row in partial_hits],
        "selected_family": selected,
        "top_overlap_families": top_overlap,
        "claim_boundary": (
            "A full result supports target-free independent recovery by the validated locked-RRF final "
            "pipeline, not literal historical first discovery, formal shower status, or resolution of "
            "the distinct-stream versus related-branch question."
        ),
    }
    json_path = args.output / "orbittrace_fixed4_locked_rrf_reveal.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = args.output / "orbittrace_fixed4_locked_rrf_overlap.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "locked_rrf_rank", "family_id", "year_count", "event_count",
                "canonical_overlap", "years_with_at_least_four_canonical",
                "precision", "canonical_recall", "passes_full_rule", "passes_partial_rule",
            ],
        )
        writer.writeheader()
        for row in top_overlap:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    selected_label = selected["family_id"] if selected else "none"
    lines = [
        "# OrbitTrace fixed4 locked-RRF reveal",
        "",
        f"Verdict: `{verdict}`",
        "",
        f"- frozen families: **{len(evaluations):,}**",
        f"- canonical OrbitTrace members evaluated: **{EXPECTED_CANONICAL_TOTAL}**",
        f"- selected family: **{selected_label}**, locked-RRF rank **{selected['locked_rrf_rank']}**",
        f"- family years / events: **{selected['year_count']} / {selected['event_count']}**",
        f"- canonical overlap: **{selected['canonical_overlap']}**",
        f"- overlap by year: **{selected['canonical_overlap_by_year']}**",
        f"- precision / canonical recall: **{selected['precision']:.4f} / {selected['canonical_recall']:.4f}**",
        "",
        "The locked-RRF ranking was frozen and hashed before the canonical member table was retrieved. No family was merged, rescored, or reranked during reveal.",
    ]
    (args.output / "ORBITTRACE_FIXED4_LOCKED_RRF_REVEAL.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
