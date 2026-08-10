#!/usr/bin/env python3
"""Exact structural equivalence proof for pair-portable hard/P19/P20 generation.

No performance metric is computed. The generated pre-truth structures must equal the frozen
GMN P19/P20 prelabel payloads exactly. This is the acceptance test for using the transport
adapter on any unseen two-year pair.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from orbittrace_urc_pair_portable_generators_v1 import generators

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_P19_PRELABEL_FILE_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_PRELABEL_FILE_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def first_list_difference(left: list[Any], right: list[Any]) -> dict[str, Any]:
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {
                "index": i,
                "left_sha256": canonical_sha(a),
                "right_sha256": canonical_sha(b),
                "left_family_id": a.get("family_id") if isinstance(a, dict) else None,
                "right_family_id": b.get("family_id") if isinstance(b, dict) else None,
            }
    if len(left) != len(right):
        return {"index": min(len(left), len(right)), "left_length": len(left), "right_length": len(right)}
    return {"equal": True}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v8-source", type=Path, required=True)
    p.add_argument("--p19-source", type=Path, required=True)
    p.add_argument("--p20-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha(args.p19_prelabel_json) == EXPECTED_P19_PRELABEL_FILE_SHA, "P19 prelabel file changed")
    require(sha(args.p20_prelabel_json) == EXPECTED_P20_PRELABEL_FILE_SHA, "P20 prelabel file changed")
    ref19 = json.loads(args.p19_prelabel_json.read_text())
    ref20 = json.loads(args.p20_prelabel_json.read_text())

    v8 = load_module(args.v8_source, "frozen_v8_pair_generator")
    p19 = load_module(args.p19_source, "frozen_p19_pair_generator")
    p20 = load_module(args.p20_source, "frozen_p20_pair_generator")
    v6 = p19.v6
    mult = p19.mult
    require(p20.mult is not None, "P20 multiplicity runtime unavailable")

    require(all(mult.v3.self_test().values()), "v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    generators.configure_pair(YEARS, support=support, mult=mult, v6=v6, v8=v8, p19=p19, p20=p20)
    # Reproduce the context under which the P19 hard+soft artifact was originally built.
    # Individual generator helpers later switch to their own frozen context as required.
    support.CORPUS = p19.CORPUS
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence gate changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal retention changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _calibration, _hidden_labels_unused, sources = support.parse_catalogue(base)
    require(sorted(scan) == list(YEARS), "GMN years changed")
    require([x["key"] for x in sources] == list(MONTH_KEYS), "GMN month universe changed")

    built = generators.build_union_pair(
        years=YEARS,
        scan_by_year=scan,
        support=support,
        base=base,
        runtime=runtime,
        v6=v6,
        v8=v8,
        p19=p19,
        p20=p20,
        mult=mult,
    )

    hard19 = [p19.structural_family_payload(f) for f in built["hard"]["hard_families"]]
    soft19 = [p19.structural_family_payload(f) for f in built["p19_soft"]]
    hard20 = [p20.structural_family_payload(f) for f in built["hard"]["hard_families"]]
    soft20 = [p20.structural_family_payload(f) for f in built["p20"]["soft_families"]]
    quartets20 = {str(year): built["p20"]["quartets_by_year"][year] for year in YEARS}

    diagnostics = {
        "hard_order": {
            "generated_sha256": canonical_sha(built["hard_order"]),
            "p19_reference_sha256": canonical_sha(ref19["hard_order"]),
            "p20_reference_sha256": canonical_sha(ref20["hard_order"]),
            "equal": built["hard_order"] == ref19["hard_order"] == ref20["hard_order"],
        },
        "hard_p19": {
            "generated_sha256": canonical_sha(hard19),
            "reference_sha256": canonical_sha(ref19["hard_families"]),
            "equal": hard19 == ref19["hard_families"],
            "first_difference": first_list_difference(hard19, ref19["hard_families"]),
        },
        "p19_soft": {
            "generated_count": len(soft19),
            "reference_count": len(ref19["soft_families"]),
            "generated_sha256": canonical_sha(soft19),
            "reference_sha256": canonical_sha(ref19["soft_families"]),
            "equal": soft19 == ref19["soft_families"],
            "first_difference": first_list_difference(soft19, ref19["soft_families"]),
            "generated_diagnostics": built["p19_diagnostics"],
            "reference_diagnostics": ref19["soft_diagnostics"],
        },
        "p20_soft": {
            "generated_count": len(soft20),
            "reference_count": len(ref20["soft_families"]),
            "generated_sha256": canonical_sha(soft20),
            "reference_sha256": canonical_sha(ref20["soft_families"]),
            "equal": soft20 == ref20["soft_families"],
            "first_difference": first_list_difference(soft20, ref20["soft_families"]),
        },
        "p20_quartets": {
            "generated_sha256": canonical_sha(quartets20),
            "reference_sha256": canonical_sha(ref20["isolated_quartets"]),
            "equal": quartets20 == ref20["isolated_quartets"],
        },
        "p19_support_context": p19.CORPUS,
        "p20_support_context": p20.CORPUS,
        "performance_metric_computed": False,
        "truth_labels_used_by_generator": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    (args.output / "urc_pair_portable_generator_equivalence_diagnostics_v1.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(diagnostics, indent=2, sort_keys=True))

    require(built["hard_order"] == ref19["hard_order"] == ref20["hard_order"], "hard multiplicity order differs")
    require(hard19 == ref19["hard_families"], "portable hard families differ from P19 prelabel")
    require(hard20 == ref20["hard_families"], "portable hard families differ from P20 prelabel")
    require(soft19 == ref19["soft_families"], "portable P19 soft families differ")
    require(soft20 == ref20["soft_families"], "portable P20 soft families differ")
    require(quartets20 == ref20["isolated_quartets"], "portable P20 isolated quartets differ")
    require(built["p19_diagnostics"] == ref19["soft_diagnostics"], "portable P19 diagnostics differ")
    require(built["p20"]["isolated_audits"] == ref20["isolated_audits"], "portable P20 isolated audits differ")
    require(built["p20"]["soft_diagnostics"] == ref20["soft_diagnostics"], "portable P20 recurrence diagnostics differ")

    structural = {
        "hard_order": built["hard_order"],
        "hard_families": hard19,
        "p19_soft_families": soft19,
        "p20_soft_families": soft20,
        "p20_isolated_quartets": quartets20,
    }
    result = {
        "verdict": "PASS_URC_PAIR_PORTABLE_GENERATOR_GMN_EQUIVALENCE",
        "years": list(YEARS),
        "hard_count": len(hard19),
        "p19_soft_count": len(soft19),
        "p20_soft_count": len(soft20),
        "union_count": len(built["families"]),
        "canonical_structural_sha256": canonical_sha(structural),
        "exact_hard_order_match": True,
        "exact_hard_family_match": True,
        "exact_p19_family_match": True,
        "exact_p20_family_match": True,
        "exact_p20_isolated_quartet_match": True,
        "performance_metric_computed": False,
        "truth_labels_used_by_generator": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "target_information_access": False,
    }
    require((result["hard_count"], result["p19_soft_count"], result["p20_soft_count"], result["union_count"]) == (226, 1075, 3203, 4504), "reference candidate counts changed")
    (args.output / "urc_pair_portable_generator_gmn_equivalence_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
