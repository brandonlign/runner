#!/usr/bin/env python3
"""Run only the preregistered exact-event-row v8 vs full Sugar panel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from orbittrace_literature_matched_v8 import run_exact_row_benchmark as b

v8 = b.v8
YEARS = b.YEARS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2023", required=True, type=Path)
    p.add_argument("--parser-2025", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--sugar-2023", required=True, type=Path)
    p.add_argument("--sugar-2025", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def fmt(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.6f}"


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    b.require(b.sha256_file(args.mapping_audit) == b.MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    for year in YEARS:
        b.require(b.sha256_file(archives[year]) == b.ARCHIVE_SHA256[year], f"archive hash changed {year}")

    assignments = {
        2023: b.load_sugar(args.sugar_2023, 2023),
        2025: b.load_sugar(args.sugar_2025, 2025),
    }
    b.require({str(year): len(assignments[year]) for year in YEARS} == {"2023": 30414, "2025": 23200}, "Sugar row counts changed")

    b.require(all(v8.mult.v3.self_test().values()), "v3 self-test failed")
    b.require(all(v8.mult.brown.self_test().values()), "Brown self-test failed")
    runtime = v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    b.require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    b.require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) <= 1e-15, "family link radius changed")
    b.require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = "sonotaco-sugar-exact-row-literature-pairwise"
    support.RANKING_VARIANTS = b.RAW_FIXED4_RANKING_VARIANTS
    _candidate, base, _scorer = support.load_sources(args)

    v8.YEARS = YEARS
    v8.MONTH_KEYS = tuple()
    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()

    ids_by_year = {year: set(assignments[year]) for year in YEARS}
    scan_by_year = {
        year: b.read_exact_geometry(year, archives[year], ids_by_year[year], base)
        for year in YEARS
    }

    # Freeze complete v8 proposals, recurrent families, centroids, scores, and ranking BEFORE labels.
    v8_panel = b.run_v8_panel("sugar", scan_by_year, support, runtime, base)

    parsers = {
        2023: b.load_module(args.parser_2023, "sugar_exact_truth_2023"),
        2025: b.load_module(args.parser_2025, "sugar_exact_truth_2025"),
    }
    truth = b.parse_common_truth(parsers, archives, args.mapping_audit, base, {"sugar": ids_by_year})["sugar"]
    years = {event_id: int(event_id[3:7]) for event_id in truth}
    families = v8_panel["families"]

    v8_rows, v8_summary = b.v8_annual_with_richer_summary(families, truth, years)
    sugar_rows: dict[str, Any] = {}
    sugar_summary: dict[str, Any] = {}
    for year in YEARS:
        rows, summary = b.best_competitor_matches(assignments[year], truth, year)
        sugar_rows[str(year)] = rows
        sugar_summary[str(year)] = summary
    comparison = b.compare_summaries(v8_summary, sugar_summary)
    recurrent_rows, recurrent_summary = b.broad.best_recurrent_matches(families, truth, years)
    ranking = b.broad.ranking_metrics(families, v8_panel["multiplicity_order"], truth, years)

    integrity = {
        "exact_sugar_assignment_hashes": True,
        "exact_archive_hashes": True,
        "exact_mapping_audit_hash": True,
        "v8_rank_frozen_before_common_label_parse": True,
        "no_v8_parameter_change": True,
        "exact_row_counts_preserved": all(len(scan_by_year[y]) == len(assignments[y]) for y in YEARS),
        "excluded_interval_absent_from_all_exact_rows": all(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan_by_year[y]) for y in YEARS),
        "zero_source_labels_in_v8_proposals": all(a["source_labels_used_for_proposals"] is False for a in v8_panel["scan_audits"]),
        "no_score_threshold_in_v8_proposals": all(a["score_threshold_applied"] is False for a in v8_panel["scan_audits"]),
        "all_scored_episode_sizes_exact_128": v8_panel["scoring_summary"]["episode_sizes"] == [128] if families else True,
        "brown_equivalence_exact": float(v8_panel["scoring_summary"]["max_brown_equivalence_difference"]) == 0.0,
    }
    verdict = "PASS_V8_SUGAR_EXACT_ROW_PAIRWISE" if all(integrity.values()) else "FAIL_V8_SUGAR_EXACT_ROW_INTEGRITY"
    result = {
        "verdict": verdict,
        "classification": "exact-event-row comparison of frozen v8 against the frozen full Sugar retained-master assignments",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "v8_source_commit": "c9d6c44704013ba0c9430100e98a29a56b453304",
            "family_link_radius": 1.5,
            "episode_size": 128,
            "no_v8_parameter_change": True,
            "labels_loaded_only_after_v8_ranking_frozen": True,
            "material_delta_gate": 0.10,
        },
        "exact_event_rows": {str(year): len(assignments[year]) for year in YEARS},
        "v8_family_count": len(families),
        "v8_component_count": v8_panel["components"],
        "v8_retained_quartets": v8_panel["quartets"],
        "v8_runtime_seconds": v8_panel["runtime_seconds"],
        "v8_annual": v8_summary,
        "sugar_annual": sugar_summary,
        "comparison": comparison,
        "v8_recurrent": recurrent_summary,
        "v8_ranking": {k: v for k, v in ranking.items() if k != "per_label"},
        "false_positive_burden": {
            "v8": b.burden_for_families(families, truth),
            "sugar": {str(year): b.burden_for_clusters(assignments[year], truth) for year in YEARS},
        },
        "integrity_gates": integrity,
        "claim_boundary": "Exact rows and common mapped labels are identical for v8 and Sugar. Sugar remains an annual uncertainty-aware catalogue method while v8 proposals require cross-year recurrence, so annual F1 is a common recognition endpoint rather than an assertion of identical optimization objectives. No OrbitTrace target information or excluded-interval contents were accessed.",
    }
    args.output.joinpath("v8_sugar_exact_row.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_sugar_exact_v8_per_label.json").write_text(json.dumps(v8_rows, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_sugar_exact_sugar_per_label.json").write_text(json.dumps(sugar_rows, indent=2, sort_keys=True) + "\n")
    args.output.joinpath("v8_sugar_exact_recurrent_per_label.json").write_text(json.dumps(recurrent_rows, indent=2, sort_keys=True) + "\n")

    lines = [
        "# OrbitTrace v8 vs full Sugar — exact-event-row benchmark",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- exact rows: 2023={len(assignments[2023])}, 2025={len(assignments[2025])}",
        f"- v8 recurrent families: {len(families)}",
        f"- v8 runtime: {v8_panel['runtime_seconds']:.3f} s",
        f"- preregistered 4–9 win gate: **{comparison['preregistered_gate_v8_beats_4_9_both_years']}**",
        f"- preregistered 4–24 win gate: **{comparison['preregistered_gate_v8_beats_4_24_both_years']}**",
        "",
        "| Year | Bin | Showers | v8 mean F1 | Sugar mean F1 | delta |",
        "|---:|:---|---:|---:|---:|---:|",
    ]
    for year in YEARS:
        for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+", "all"):
            c = comparison["by_year_and_bin"][str(year)][bin_name]
            lines.append(f"| {year} | {bin_name} | {c['showers']} | {fmt(c['v8']['mean_f1'])} | {fmt(c['competitor']['mean_f1'])} | {fmt(c['delta_mean_f1_v8_minus_competitor'])} |")
    lines += ["", "No v8 parameter was changed. No OrbitTrace target information was accessed."]
    args.output.joinpath("V8_SUGAR_EXACT_ROW.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
