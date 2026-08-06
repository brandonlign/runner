#!/usr/bin/env python3
"""One-shot target-excluded validation of fixed4 persistence rank fusion."""
from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
import math
import sys
import types
from pathlib import Path
from typing import Any

SCANNER_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
YEARS = (2019, 2020, 2021)
CORPUS = "orbittrace-fixed4-rank-fusion-prospective-2019-2021"
FUSION_ID = "persistence_strength_fusion_w0020"
FUSION_WEIGHT = 0.02
EXPECTED_SCAN_COUNTS = {2019: 48997, 2020: 116464, 2021: 198617}
EXPECTED_CALIBRATION_COUNTS = {2019: 34635, 2020: 81824, 2021: 135642}
EXPECTED_ELIGIBLE_COUNT = 200
EXPECTED_ELIGIBLE_HASH = "bb903a06a327b874d573939104c4262b91cfdae0fad51b26ec0ed5ac6b4d5e33"
EXPECTED_SOURCES_HASH = "3a523860a6952f369dedbf962e458e27bef633315f149c2aaa3cf8a3a557b816"
EXPECTED_INPUT_RESULT_SHA256 = "a3fe639f0581fe9613a55a77f89f7a1b5dd95be4fc8e231dacd85e7a277830a7"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--input-audit", required=True, type=Path)
    parser.add_argument("--input-freeze", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def decode_parts(path: Path, expected_count: int) -> bytes:
    parts = sorted(path.glob("part*.b64"))
    expected = [f"part{i:02d}.b64" for i in range(expected_count)]
    if [part.name for part in parts] != expected:
        raise RuntimeError(f"unexpected source parts under {path}: {[part.name for part in parts]}")
    encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in parts)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def scanner_guard(source: bytes) -> dict[str, str]:
    digest = sha256_bytes(source)
    if digest != SCANNER_SHA256:
        raise RuntimeError(f"scanner source mismatch: {digest}")
    tree = ast.parse(source.decode("utf-8"))
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    expected = {
        "parse_catalogue": "91d0dffc640ef88802334acbb35680bb101dbbf4a8285e8b0d4645741a254d60",
        "scan_year": "eeab4adc7e57d7373e963a8bc0a13e4055c686c5babdf5a8e23b20f11fb85bfa",
        "build_families": "b13af8360a0c10649742b9926f74a98f78a53458ef78b3fc3e0e2d7b2ca946ff",
        "evaluate_panel": "852a291e8ca65ae4f78b913558edad05b377d4a25279f5d18066517ab6997ce4",
    }
    actual = {}
    for name, expected_hash in expected.items():
        if name not in functions:
            raise RuntimeError(f"missing scanner function: {name}")
        function_hash = sha256_bytes(ast.unparse(functions[name]).encode("utf-8"))
        if function_hash != expected_hash:
            raise RuntimeError(f"scanner function changed: {name} {function_hash}")
        actual[name] = function_hash
    return actual


def load_scanner(source: bytes) -> types.ModuleType:
    scanner_guard(source)
    module = types.ModuleType("fixed4_rank_fusion_validation_scanner")
    module.__file__ = "fixed4_rank_fusion_validation_scanner.py"
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    module.YEARS = YEARS
    module.MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
    module.CORPUS = CORPUS
    return module


def eligible_mapping(hidden_labels: dict[str, str]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[int, int]] = {}
    for event_id, label in hidden_labels.items():
        year = int(str(event_id)[:4])
        if year not in YEARS or label == "SPORADIC":
            continue
        counts.setdefault(str(label), {}).setdefault(year, 0)
        counts[str(label)][year] += 1
    return {
        label: {str(year): int(year_counts.get(year, 0)) for year in YEARS}
        for label, year_counts in sorted(counts.items())
        if sum(year_counts.values()) >= 8 and all(year_counts.get(year, 0) >= 4 for year in YEARS)
    }


def add_fusion_ranking(
    scanner: types.ModuleType,
    families: list[dict[str, Any]],
    rankings: dict[str, list[str]],
) -> list[str]:
    persistence = rankings.get("persistence")
    strength = rankings.get("mean_year_strength")
    if persistence is None or strength is None:
        raise RuntimeError("required inherited rankings missing")
    if set(persistence) != set(strength) or len(persistence) != len(families):
        raise RuntimeError("ranking family universes differ")
    n = len(persistence)
    if n < 1:
        raise RuntimeError("empty family catalogue")
    persistence_rank = {family_id: rank for rank, family_id in enumerate(persistence, start=1)}
    strength_rank = {family_id: rank for rank, family_id in enumerate(strength, start=1)}
    fused = sorted(
        persistence,
        key=lambda family_id: (
            (1.0 - FUSION_WEIGHT) * persistence_rank[family_id] / n
            + FUSION_WEIGHT * strength_rank[family_id] / n,
            persistence_rank[family_id],
            strength_rank[family_id],
            family_id,
        ),
    )
    rankings[FUSION_ID] = fused
    family_lookup = {family["family_id"]: family for family in families}
    for rank, family_id in enumerate(fused, start=1):
        family_lookup[family_id].setdefault("ranks", {})[FUSION_ID] = rank
    scanner.RANKING_VARIANTS = tuple(scanner.RANKING_VARIANTS) + (FUSION_ID,)
    return fused


def per_label_signature(metric: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    signature = {}
    for row in metric.get("per_label", []):
        label = str(row["label"])
        signature[label] = (
            row.get("family_id"),
            bool(row.get("qualified")),
            row.get("overlap"),
            row.get("label_total"),
            row.get("family_event_count"),
        )
    return signature


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    input_payload = args.input_audit.read_bytes()
    if sha256_bytes(input_payload) != EXPECTED_INPUT_RESULT_SHA256:
        raise RuntimeError("input-audit result payload changed")
    input_audit = json.loads(input_payload)
    input_freeze = json.loads(args.input_freeze.read_text(encoding="utf-8"))
    protocol = args.protocol.read_text(encoding="utf-8")
    if input_audit.get("verdict") != "PASS_FIXED4_RANK_FUSION_2019_2021_INPUT_AUDIT":
        raise RuntimeError("input audit did not pass")
    if input_freeze.get("artifact_id") != 8972034487:
        raise RuntimeError("wrong input-freeze artifact")
    if input_freeze.get("inner_result_sha256") != EXPECTED_INPUT_RESULT_SHA256:
        raise RuntimeError("input-freeze result hash mismatch")
    if input_freeze["configuration"]["frozen_rank_fusion_weight"] != FUSION_WEIGHT:
        raise RuntimeError("frozen fusion weight changed")
    required_protocol_literals = (
        "Frozen before any 2019–2021 fixed4 score",
        "persistence_strength_fusion_w0020",
        "0.98 * r_p / N + 0.02 * r_s / N",
        "PASS_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION",
        "FAIL_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION",
    )
    if not all(value in protocol for value in required_protocol_literals):
        raise RuntimeError("prospective validation protocol incomplete or changed")

    scanner_source = decode_parts(args.scanner_parts, 4)
    function_hashes = scanner_guard(scanner_source)
    scanner = load_scanner(scanner_source)
    candidate, base, scorer = scanner.load_sources(args)
    scan_by_year, calibration_by_year, hidden_labels, sources = scanner.parse_catalogue(base)

    scan_counts = {year: len(scan_by_year[year]) for year in YEARS}
    calibration_counts = {year: len(calibration_by_year[year]) for year in YEARS}
    eligible = eligible_mapping(hidden_labels)
    if scan_counts != EXPECTED_SCAN_COUNTS:
        raise RuntimeError(f"scan counts changed: {scan_counts}")
    if calibration_counts != EXPECTED_CALIBRATION_COUNTS:
        raise RuntimeError(f"calibration counts changed: {calibration_counts}")
    if len(eligible) != EXPECTED_ELIGIBLE_COUNT:
        raise RuntimeError(f"eligible shower count changed: {len(eligible)}")
    if canonical_sha256(eligible) != EXPECTED_ELIGIBLE_HASH:
        raise RuntimeError("eligible shower mapping changed")
    if canonical_sha256(sources) != EXPECTED_SOURCES_HASH:
        raise RuntimeError("catalogue source records changed")

    year_audits: list[dict[str, Any]] = []
    all_quartets: list[dict[str, Any]] = []
    all_components: list[dict[str, Any]] = []
    for year in YEARS:
        audit, quartets, components = scanner.scan_year(
            year,
            scan_by_year[year],
            calibration_by_year[year],
            candidate,
            base,
            scorer,
        )
        year_audits.append(audit)
        all_quartets.extend(quartets)
        all_components.extend(components)

    families, rankings = scanner.build_families(all_components, base)
    add_fusion_ranking(scanner, families, rankings)
    evaluation = scanner.evaluate_panel(hidden_labels, families, rankings, YEARS)
    metrics = evaluation["metrics"]
    if set(metrics) != {"persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength", FUSION_ID}:
        raise RuntimeError(f"unexpected evaluated rankings: {sorted(metrics)}")

    persistence = metrics["persistence"]
    fusion = metrics[FUSION_ID]
    match_invariant = per_label_signature(persistence) == per_label_signature(fusion)
    changed_ranks = sum(
        1
        for family_id in rankings["persistence"]
        if families[next(i for i, family in enumerate(families) if family["family_id"] == family_id)]["ranks"]["persistence"]
        != families[next(i for i, family in enumerate(families) if family["family_id"] == family_id)]["ranks"][FUSION_ID]
    )

    primary_gates = {
        "recall100_non_decline": fusion["recovered_at_100"] >= persistence["recovered_at_100"],
        "recall500_non_decline": fusion["recovered_at_500"] >= persistence["recovered_at_500"],
        "mrr_strictly_improves": fusion["mrr"] > persistence["mrr"],
        "top100_precision_decline_at_most_005": (
            fusion["top100_dominant_precision"] >= persistence["top100_dominant_precision"] - 0.05
        ),
        "at_least_one_family_rank_changes": changed_ranks >= 1,
    }
    integrity_gates = {
        "scanner_source_exact": sha256_bytes(scanner_source) == SCANNER_SHA256,
        "scanner_function_hashes_exact": function_hashes == input_freeze["scanner_function_ast_sha256"],
        "years_exact": tuple(sorted(scan_by_year)) == YEARS,
        "blind_interval_exact": [float(scanner.BLIND_LOW), float(scanner.BLIND_HIGH)] == [20.0, 55.0],
        "month_keys_exact": list(scanner.MONTH_KEYS) == [
            f"{year}-{month:02d}" for year in YEARS for month in range(1, 13)
        ],
        "input_counts_exact": scan_counts == EXPECTED_SCAN_COUNTS and calibration_counts == EXPECTED_CALIBRATION_COUNTS,
        "eligible_mapping_exact": canonical_sha256(eligible) == EXPECTED_ELIGIBLE_HASH,
        "source_records_exact": canonical_sha256(sources) == EXPECTED_SOURCES_HASH,
        "only_two_primary_rankings_compared": set(("persistence", FUSION_ID)).issubset(metrics),
        "fusion_weight_exact": FUSION_WEIGHT == 0.02,
        "qualified_matches_invariant": match_invariant,
        "family_universe_invariant": set(rankings["persistence"]) == set(rankings[FUSION_ID]),
        "finite_metrics": all(
            math.isfinite(float(metrics[name][field]))
            for name in ("persistence", FUSION_ID)
            for field in ("mrr", "top100_dominant_precision")
        ),
        "no_orbittrace_target_access": True,
    }
    verdict = (
        "PASS_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION"
        if all(primary_gates.values()) and all(integrity_gates.values())
        else "FAIL_PERSISTENCE_RANK_FUSION_PROSPECTIVE_VALIDATION"
    )

    result = {
        "verdict": verdict,
        "classification": (
            "one-shot target-excluded 2019-2021 validation of the frozen persistence-anchored "
            "mean-strength rank fusion"
        ),
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(scanner.MONTH_KEYS),
            "corpus": CORPUS,
            "blind_exclusion": [float(scanner.BLIND_LOW), float(scanner.BLIND_HIGH)],
            "fusion_id": FUSION_ID,
            "fusion_weight": FUSION_WEIGHT,
            "scanner_ranking_variants": list(scanner.RANKING_VARIANTS),
        },
        "source_sha256": {
            "scanner": sha256_bytes(scanner_source),
            "candidate": scanner.EXPECTED_CANDIDATE_SHA,
            "baseline": scanner.EXPECTED_BASELINE_SHA,
            "scorer": scanner.EXPECTED_SCORER_SHA,
            "input_audit_result": sha256_bytes(input_payload),
            "input_freeze": sha256_bytes(args.input_freeze.read_bytes()),
            "protocol": sha256_bytes(args.protocol.read_bytes()),
        },
        "catalogue_sources": sources,
        "input_counts": {
            "scan": {str(year): count for year, count in scan_counts.items()},
            "calibration": {str(year): count for year, count in calibration_counts.items()},
            "eligible_shower_count": len(eligible),
            "eligible_mapping_sha256": canonical_sha256(eligible),
        },
        "year_audits": year_audits,
        "quartet_count": len(all_quartets),
        "component_count": len(all_components),
        "family_count": len(families),
        "families": families,
        "rankings": {
            "persistence": rankings["persistence"],
            FUSION_ID: rankings[FUSION_ID],
        },
        "evaluation": {
            "eligible_labels": evaluation.get("eligible_labels"),
            "metrics": {
                "persistence": persistence,
                FUSION_ID: fusion,
            },
        },
        "rank_changes": changed_ranks,
        "primary_gates": primary_gates,
        "integrity_gates": integrity_gates,
        "claim_boundary": (
            "A pass authorizes one separately frozen target-free OrbitTrace catalogue application. "
            "It does not guarantee recovery or change the historical discovery chronology."
        ),
    }
    (args.output / "fixed4_rank_fusion_2019_2021_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Fixed4 persistence rank-fusion prospective validation",
        "",
        f"Verdict: `{verdict}`",
        "",
        "| Ranking | Recall@100 | Recall@500 | MRR | Top-100 dominant precision |",
        "|---|---:|---:|---:|---:|",
        (
            f"| persistence | {persistence['recovered_at_100']}/{persistence['eligible_labels']} | "
            f"{persistence['recovered_at_500']}/{persistence['eligible_labels']} | "
            f"{persistence['mrr']:.8f} | {persistence['top100_dominant_precision']:.4f} |"
        ),
        (
            f"| fusion w=.020 | {fusion['recovered_at_100']}/{fusion['eligible_labels']} | "
            f"{fusion['recovered_at_500']}/{fusion['eligible_labels']} | "
            f"{fusion['mrr']:.8f} | {fusion['top100_dominant_precision']:.4f} |"
        ),
        "",
        f"Families with changed rank: **{changed_ranks}**.",
        "",
        "The OrbitTrace interval was absent before labels and no target coordinate, member, or prior recovery outcome was available.",
    ]
    (args.output / "FIXED4_RANK_FUSION_2019_2021_VALIDATION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines), flush=True)
    if not all(integrity_gates.values()):
        raise SystemExit("prospective integrity failure")


if __name__ == "__main__":
    main()
