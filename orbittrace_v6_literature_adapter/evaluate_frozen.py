#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter import adapter

BINS = ("4-9", "10-24", "25-49", "50-99", "100+")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def subset_mean(rows: list[dict[str, Any]], bins: set[str]) -> float | None:
    values = [float(row["f1"]) for row in rows if str(row["size_bin"]) in bins]
    return float(sum(values) / len(values)) if values else None


def annual_pairwise_gates(
    v6_rows: list[dict[str, Any]],
    v6_summary: dict[str, Any],
    comp_rows: list[dict[str, Any]],
    comp_summary: dict[str, Any],
) -> dict[str, Any]:
    require({r["label"] for r in v6_rows} == {r["label"] for r in comp_rows}, "annual truth label sets differ")
    require(len(v6_rows) == len(comp_rows), "annual evaluation denominator differs")
    for bin_name in BINS:
        require(v6_summary[bin_name]["showers"] == comp_summary[bin_name]["showers"],
                f"size-bin denominator differs {bin_name}")

    all_delta = float(v6_summary["all"]["mean_f1"] - comp_summary["all"]["mean_f1"])
    bin_delta: dict[str, float | None] = {}
    nonempty_bin_deltas: list[float] = []
    for bin_name in BINS:
        vf = v6_summary[bin_name]["mean_f1"]
        cf = comp_summary[bin_name]["mean_f1"]
        if vf is None or cf is None:
            bin_delta[bin_name] = None
        else:
            d = float(vf - cf)
            bin_delta[bin_name] = d
            nonempty_bin_deltas.append(d)

    v6_4_24 = subset_mean(v6_rows, {"4-9", "10-24"})
    comp_4_24 = subset_mean(comp_rows, {"4-9", "10-24"})
    delta_4_24 = None if v6_4_24 is None or comp_4_24 is None else float(v6_4_24 - comp_4_24)

    broad = {
        "macro_f1_gain_ge_0_05": all_delta >= 0.05,
        "no_size_stratum_regression_gt_0_05": bool(nonempty_bin_deltas) and min(nonempty_bin_deltas) >= -0.05,
        "at_least_two_strata_gain_ge_0_10": sum(d >= 0.10 for d in nonempty_bin_deltas) >= 2,
        "f1_gt_0_5_count_not_lower": int(v6_summary["all"]["f1_gt_0_5"]) >= int(comp_summary["all"]["f1_gt_0_5"]),
    }
    sparse = {
        "four_to_nine_gain_ge_0_10": bin_delta["4-9"] is not None and float(bin_delta["4-9"]) >= 0.10,
        "four_to_twentyfour_gain_ge_0_10": delta_4_24 is not None and delta_4_24 >= 0.10,
        "macro_f1_not_more_than_0_10_lower": all_delta >= -0.10,
        "retain_at_least_80pct_f1_gt_0_5_count": (
            int(v6_summary["all"]["f1_gt_0_5"]) >= 0.80 * int(comp_summary["all"]["f1_gt_0_5"])
        ),
    }
    return {
        "macro_f1_delta_v6_minus_comparator": all_delta,
        "size_bin_delta_v6_minus_comparator": bin_delta,
        "combined_4_24": {"v6_mean_f1": v6_4_24, "comparator_mean_f1": comp_4_24, "delta": delta_4_24},
        "broad_gates": broad,
        "sparse_gates": sparse,
        "broad_pass": all(broad.values()),
        "sparse_pass": all(sparse.values()),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth", required=True, type=Path)
    p.add_argument("--exact-row-runner", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2023", required=True, type=Path)
    p.add_argument("--parser-2025", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--hdbscan-2023", required=True, type=Path)
    p.add_argument("--hdbscan-2025", required=True, type=Path)
    p.add_argument("--sugar-2023", required=True, type=Path)
    p.add_argument("--sugar-2025", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    pretruth = json.loads(args.pretruth.read_text())
    pre_sha = canonical_sha(pretruth)
    pre_sha_path = args.pretruth.with_suffix(args.pretruth.suffix + ".sha256")
    require(pre_sha_path.exists() and pre_sha_path.read_text().strip() == pre_sha, "pretruth SHA mismatch")
    require(pretruth["classification"] == "v6 exact-row pretruth frozen primary outputs", "wrong pretruth classification")
    require(pretruth["truth_accessed"] is False and pretruth["mapping_accessed"] is False,
            "pretruth process boundary not clean")
    require(pretruth["competitor_cluster_labels_accessed"] is False, "competitor labels entered pretruth")
    require(pretruth["years"] == list(adapter.YEARS), "pretruth years changed")
    require(pretruth["blind_exclusion"] == [adapter.BLIND_LOW, adapter.BLIND_HIGH], "pretruth blind interval changed")
    for panel in ("hdbscan", "sugar"):
        require(bool(pretruth["panels"][panel]["primary_ranking_sha256_before_truth"]), f"missing primary hash {panel}")

    exact = load_module(args.exact_row_runner, "orbittrace_posttruth_exact")
    old = load_module(args.base_runner, "orbittrace_posttruth_base")
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)

    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    require(exact.sha256_file(args.mapping_audit) == exact.MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    for year in adapter.YEARS:
        require(exact.sha256_file(archives[year]) == exact.ARCHIVE_SHA256[year], f"archive hash changed {year}")

    assignments = {
        "hdbscan": {2023: exact.load_hdbscan(args.hdbscan_2023, 2023), 2025: exact.load_hdbscan(args.hdbscan_2025, 2025)},
        "sugar": {2023: exact.load_sugar(args.sugar_2023, 2023), 2025: exact.load_sugar(args.sugar_2025, 2025)},
    }
    panel_ids = {panel: {year: set(assignments[panel][year]) for year in adapter.YEARS} for panel in ("hdbscan", "sugar")}
    parsers = {
        2023: load_module(args.parser_2023, "orbittrace_posttruth_2023"),
        2025: load_module(args.parser_2025, "orbittrace_posttruth_2025"),
    }

    # This is the first point in this process where mapped shower truth is loaded.
    truth_by_panel = exact.parse_common_truth(parsers, archives, args.mapping_audit, base, panel_ids)

    panel_results: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        truth = truth_by_panel[panel]
        years = {event_id: int(event_id[3:7]) for event_id in truth}
        families = pretruth["panels"][panel]["primary_families"]
        family_ids = {str(event_id) for family in families for event_id in family["event_ids"]}
        require(family_ids <= set(truth), f"v6 family member outside common truth {panel}")

        v6_rows_by_year, v6_summary = exact.v8_annual_with_richer_summary(families, truth, years)
        comp_rows_by_year: dict[str, list[dict[str, Any]]] = {}
        comp_summary: dict[str, Any] = {}
        gates_by_year: dict[str, Any] = {}
        for year in adapter.YEARS:
            rows, summary = exact.best_competitor_matches(assignments[panel][year], truth, year)
            comp_rows_by_year[str(year)] = rows
            comp_summary[str(year)] = summary
            gates_by_year[str(year)] = annual_pairwise_gates(v6_rows_by_year[str(year)], v6_summary[str(year)], rows, summary)

        broad_pass = all(gates_by_year[str(year)]["broad_pass"] for year in adapter.YEARS)
        sparse_pass = all(gates_by_year[str(year)]["sparse_pass"] for year in adapter.YEARS)
        panel_results[panel] = {
            "exact_event_rows": {str(year): len(assignments[panel][year]) for year in adapter.YEARS},
            "v6_primary_family_count": len(families),
            "pretruth_primary_ranking_sha256": pretruth["panels"][panel]["primary_ranking_sha256_before_truth"],
            "v6_annual": v6_summary,
            "competitor_annual": comp_summary,
            "pairwise_gates": gates_by_year,
            "broad_pairwise_pass": broad_pass,
            "sparse_pairwise_pass": sparse_pass,
            "v6_false_positive_burden": exact.burden_for_families(families, truth),
            "competitor_false_positive_burden": {str(year): exact.burden_for_clusters(assignments[panel][year], truth) for year in adapter.YEARS},
            "v6_per_label": v6_rows_by_year,
            "competitor_per_label": comp_rows_by_year,
        }

    broad = all(panel_results[p]["broad_pairwise_pass"] for p in ("hdbscan", "sugar"))
    sparse = all(panel_results[p]["sparse_pairwise_pass"] for p in ("hdbscan", "sugar"))
    classification = "BROAD_CATALOGUE_SUPERIORITY" if broad else ("SPARSE_STREAM_SUPERIORITY" if sparse else "NO_LITERATURE_SUPERIORITY")

    result = {
        "classification": classification,
        "pretruth_sha256": pre_sha,
        "years": list(adapter.YEARS),
        "blind_exclusion": [adapter.BLIND_LOW, adapter.BLIND_HIGH],
        "pairwise_only_no_cross_denominator_comparison": True,
        "panels": panel_results,
        "broad_catalogue_superiority": broad,
        "sparse_stream_superiority": sparse,
        "claim_boundary": (
            "Matched SonotaCo exact-row comparison only. No result here is pristine external validation or target authorization. "
            "Sugar and HDBSCAN are adjudicated on separate exact pairwise universes; their F1 values are never mixed across denominators."
        ),
    }
    require(all(math.isfinite(float(panel_results[p]["pairwise_gates"][str(y)]["macro_f1_delta_v6_minus_comparator"]))
                for p in ("hdbscan", "sugar") for y in adapter.YEARS), "nonfinite literature endpoint")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(canonical_sha(result) + "\n")
    print("ORBITTRACE_V6_LITERATURE_RESULT_BEGIN")
    print(json.dumps({
        "classification": classification,
        "broad_catalogue_superiority": broad,
        "sparse_stream_superiority": sparse,
        "pretruth_sha256": pre_sha,
        "panel_passes": {
            p: {
                "broad": panel_results[p]["broad_pairwise_pass"],
                "sparse": panel_results[p]["sparse_pairwise_pass"],
            } for p in ("hdbscan", "sugar")
        },
    }, indent=2, sort_keys=True))
    print("ORBITTRACE_V6_LITERATURE_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
