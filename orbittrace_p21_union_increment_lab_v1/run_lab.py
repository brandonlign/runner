#!/usr/bin/env python3
"""Development-only diagnostic: does frozen P21 add material unique coverage beyond hard+P19+P20?"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult
YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--p21-prelabel-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def eligible(hidden: dict[str, str]) -> tuple[dict[str, Counter[int]], dict[str, int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for eid, label in hidden.items():
        if label == "SPORADIC":
            continue
        year = int(str(eid)[:4])
        if year in YEARS:
            counts[label][year] += 1
    keep = {
        label: per_year for label, per_year in counts.items()
        if sum(per_year.values()) >= 8 and all(per_year.get(y, 0) >= 4 for y in YEARS)
    }
    return keep, {label: int(sum(v.values())) for label, v in keep.items()}


def dedup(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: dict[tuple[str, ...], dict[str, Any]] = {}
    for fam in families:
        key = tuple(sorted(str(x) for x in fam["event_ids"]))
        prior = out.get(key)
        if prior is None or str(fam["family_id"]) < str(prior["family_id"]):
            out[key] = fam
    return list(out.values())


def qualified_labels(
    hidden: dict[str, str],
    eligible_labels: dict[str, Counter[int]],
    families: list[dict[str, Any]],
) -> set[str]:
    qualified: set[str] = set()
    for fam in families:
        ids = [str(x) for x in fam["event_ids"]]
        if not ids:
            continue
        counts = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
        for label, overlap in counts.items():
            if label not in eligible_labels or overlap < 4:
                continue
            precision = overlap / len(ids)
            if precision >= 0.5:
                qualified.add(label)
    return qualified


def size_bin(total: int) -> str:
    if total <= 9:
        return "8-9"
    if total <= 24:
        return "10-24"
    if total <= 49:
        return "25-49"
    if total <= 99:
        return "50-99"
    return "100+"


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    p19 = json.loads(args.p19_prelabel_json.read_text())
    p20 = json.loads(args.p20_prelabel_json.read_text())
    p21 = json.loads(args.p21_prelabel_json.read_text())

    hard = p19["hard_families"]
    require([f["family_id"] for f in hard] == [f["family_id"] for f in p20["hard_families"]], "P19/P20 hard universes differ")
    require([f["family_id"] for f in hard] == [f["family_id"] for f in p21["hard_families"]], "P19/P21 hard universes differ")
    p19_soft = p19["soft_families"]
    p20_soft = p20["soft_families"]
    p21_soft = p21["soft_families"]

    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-p21-union-increment-lab-v1"
    support.RANKING_VARIANTS = ("persistence",)
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target firewall changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _calibration_by_year, hidden, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "GMN year universe changed")
    require([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month universe changed")

    eligible_labels, totals = eligible(hidden)
    groups = {
        "hard": dedup(hard),
        "p19_soft": dedup(p19_soft),
        "p20_soft": dedup(p20_soft),
        "p21_soft": dedup(p21_soft),
        "existing_union": dedup(hard + p19_soft + p20_soft),
        "p21_augmented_union": dedup(hard + p19_soft + p20_soft + p21_soft),
    }
    coverage = {name: qualified_labels(hidden, eligible_labels, fams) for name, fams in groups.items()}
    increment = coverage["p21_augmented_union"] - coverage["existing_union"]
    p21_only_vs_existing = coverage["p21_soft"] - coverage["existing_union"]

    bin_increment = Counter(size_bin(totals[label]) for label in increment)
    sparse_increment = sum(v for k, v in bin_increment.items() if k in {"8-9", "10-24"})
    # Frozen before result: require a meaningful catalogue-level increment, not a few isolated labels.
    material = len(increment) >= 10 and sparse_increment >= 3
    verdict = "MATERIAL_P21_UNIQUE_COVERAGE" if material else "NO_MATERIAL_P21_UNIQUE_COVERAGE"

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "material_increment_gate": {"new_qualified_labels_at_least": 10, "new_8_24_labels_at_least": 3},
        },
        "eligible_known_showers": len(eligible_labels),
        "family_counts": {name: len(fams) for name, fams in groups.items()},
        "qualified_coverage": {name: len(labels) for name, labels in coverage.items()},
        "p21_unique_increment": {
            "count": len(increment),
            "sparse_8_24_count": int(sparse_increment),
            "size_bins": dict(sorted(bin_increment.items())),
            "labels_sha_only": __import__("hashlib").sha256("|".join(sorted(increment)).encode()).hexdigest(),
        },
        "p21_soft_only_beyond_existing_union_count": len(p21_only_vs_existing),
        "integrity": {
            "candidate_generation_recomputed": False,
            "frozen_prelabel_payloads_only": True,
            "sonotaco_2013_2014_access": False,
            "maarsy_access": False,
            "target_information_access": False,
        },
    }
    (args.output / "p21_union_increment_lab_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "P21_UNION_INCREMENT_LAB_V1.md").write_text(
        "# P21 unique-coverage increment diagnostic\n\n"
        f"- verdict: `{verdict}`\n"
        f"- existing P19+P20 union qualified coverage: **{len(coverage['existing_union'])}**\n"
        f"- P21-augmented qualified coverage: **{len(coverage['p21_augmented_union'])}**\n"
        f"- new qualified streams from P21: **{len(increment)}**\n"
        f"- new 8-24-member streams from P21: **{sparse_increment}**\n"
        f"- P21 soft families: **{len(p21_soft)}**\n"
    )
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
