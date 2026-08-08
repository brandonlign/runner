#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter import evaluate_frozen as frozen_v6_eval

YEARS = (2023, 2025)
BLIND_EXCLUSION = (20.0, 55.0)
PANELS = ("hdbscan", "sugar")
C1_CHECKPOINT_CLASS = "C1 matched-literature pretruth panel checkpoint"
C1_SOURCE_SHA256 = "113c579f2058126e93b93a3534aaa6108d3e827c667552ecd41ff321d7a5e3da"
REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
P1_SOURCE_SHA256 = "e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def load_pretruth(path: Path, panel: str) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip().split()[0] == hashlib.sha256(raw).hexdigest(),
            f"C1 pretruth checkpoint SHA mismatch {panel}")
    obj = pickle.loads(raw)
    require(obj["classification"] == C1_CHECKPOINT_CLASS, f"wrong C1 checkpoint classification {panel}")
    require(obj["panel"] == panel, f"wrong C1 checkpoint panel {panel}")
    require(obj["years"] == list(YEARS), f"C1 checkpoint years changed {panel}")
    require(obj["blind_exclusion"] == list(BLIND_EXCLUSION), f"C1 checkpoint blind interval changed {panel}")
    require(obj["c1_source_sha256"] == C1_SOURCE_SHA256, f"C1 source identity changed {panel}")
    require(obj["v6_source_sha256"] == REPAIRED_V6_SHA256, f"v6 source identity changed {panel}")
    require(obj["p1_source_sha256"] == P1_SOURCE_SHA256, f"P1 source identity changed {panel}")
    require(obj["pretruth"]["competitor_cluster_values_accessed"] is False, f"competitor values entered pretruth {panel}")
    require(obj["pretruth"]["known_shower_truth_accessed"] is False, f"truth entered pretruth {panel}")
    require(obj["pretruth"]["fixed4_rescue_can_seed_c1"] is False, f"fixed4 entered C1 seeds {panel}")
    require(obj["pretruth"]["new_members_can_seed_or_refit"] is False, f"C1 additions refit/grow {panel}")
    require(obj["pretruth"]["rank_and_membership_frozen_before_truth"] is True, f"pretruth freeze missing {panel}")
    require(canonical_sha(obj["v6_primary_rank"]) == obj["v6_primary_rank_pretruth_sha256"], f"rank hash changed {panel}")
    require(canonical_sha(obj["v6_primary_families"]) == obj["v6_seed_families_pretruth_sha256"], f"seed family hash changed {panel}")
    require(canonical_sha(obj["c1_expanded_families"]) == obj["c1_membership_pretruth_sha256"], f"C1 membership hash changed {panel}")
    require([str(f["family_id"]) for f in obj["v6_primary_families"]] == obj["v6_primary_rank"], f"v6 family/rank order changed {panel}")
    require([str(f["family_id"]) for f in obj["c1_expanded_families"]] == obj["v6_primary_rank"], f"C1 family/rank order changed {panel}")
    for audit in obj["year_audits"].values():
        require(audit["proposal_cap_per_window"] == 512, f"proposal cap changed {panel}")
        require(audit["max_primary_proposals_per_year"] == 36864, f"annual proposal budget changed {panel}")
    return obj


def internal_v6_report(exact: Any, checkpoint: dict[str, Any], truth: dict[str, str], years: dict[str, int]) -> dict[str, Any]:
    c1_rows, c1_summary = exact.v8_annual_with_richer_summary(checkpoint["c1_expanded_families"], truth, years)
    v6_rows, v6_summary = exact.v8_annual_with_richer_summary(checkpoint["v6_primary_families"], truth, years)
    delta: dict[str, Any] = {}
    for year in YEARS:
        y = str(year)
        delta[y] = {}
        for bin_name in (*frozen_v6_eval.BINS, "all"):
            a = c1_summary[y][bin_name]["mean_f1"]
            b = v6_summary[y][bin_name]["mean_f1"]
            delta[y][bin_name] = None if a is None or b is None else float(a - b)
    return {
        "c1_annual": c1_summary,
        "v6_seed_annual": v6_summary,
        "mean_f1_delta_c1_minus_v6": delta,
        "c1_per_label": c1_rows,
        "v6_seed_per_label": v6_rows,
    }


def evaluate_panel(
    panel: str,
    checkpoint: dict[str, Any],
    exact: Any,
    base: Any,
    parsers: dict[int, Any],
    archives: dict[int, Path],
    mapping_audit: Path,
    assignments_path: dict[str, dict[int, Path]],
) -> dict[str, Any]:
    # FIRST competitor cluster-value access for this panel. All pretruth hashes
    # were verified in load_pretruth() before this function is called.
    if panel == "hdbscan":
        assignments = {year: exact.load_hdbscan(assignments_path[panel][year], year) for year in YEARS}
    else:
        assignments = {year: exact.load_sugar(assignments_path[panel][year], year) for year in YEARS}
    expected_ids = {year: set(assignments[year]) for year in YEARS}
    require({str(y): len(expected_ids[y]) for y in YEARS} == checkpoint["exact_event_rows"],
            f"exact event rows changed {panel}")

    # FIRST mapped known-shower truth access for this panel.
    truth = exact.parse_common_truth(parsers, archives, mapping_audit, base, {panel: expected_ids})[panel]
    years = {event_id: int(event_id[3:7]) for event_id in truth}
    c1_families = checkpoint["c1_expanded_families"]
    family_members = {str(eid) for f in c1_families for eid in f["event_ids"]}
    require(family_members <= set(truth), f"C1 member lies outside common truth {panel}")

    c1_rows_by_year, c1_summary = exact.v8_annual_with_richer_summary(c1_families, truth, years)
    comparator_rows: dict[str, Any] = {}
    comparator_summary: dict[str, Any] = {}
    gates: dict[str, Any] = {}
    for year in YEARS:
        rows, summary = exact.best_competitor_matches(assignments[year], truth, year)
        y = str(year)
        comparator_rows[y] = rows
        comparator_summary[y] = summary
        gates[y] = frozen_v6_eval.annual_pairwise_gates(c1_rows_by_year[y], c1_summary[y], rows, summary)

    return {
        "status": "ELIGIBLE_EVALUATED",
        "exact_event_rows": checkpoint["exact_event_rows"],
        "v6_primary_family_count": len(checkpoint["v6_primary_families"]),
        "v6_primary_rank_pretruth_sha256": checkpoint["v6_primary_rank_pretruth_sha256"],
        "c1_membership_pretruth_sha256": checkpoint["c1_membership_pretruth_sha256"],
        "c1_diagnostics": checkpoint["c1_diagnostics"],
        "c1_annual": c1_summary,
        "competitor_annual": comparator_summary,
        "pairwise_gates": gates,
        "broad_pairwise_pass": all(gates[str(y)]["broad_pass"] for y in YEARS),
        "sparse_pairwise_pass": all(gates[str(y)]["sparse_pass"] for y in YEARS),
        "c1_false_positive_burden": exact.burden_for_families(c1_families, truth),
        "competitor_false_positive_burden": {str(y): exact.burden_for_clusters(assignments[y], truth) for y in YEARS},
        "internal_v6_nonregression": internal_v6_report(exact, checkpoint, truth, years),
        "c1_per_label": c1_rows_by_year,
        "competitor_per_label": comparator_rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hdbscan-pretruth", required=True, type=Path)
    p.add_argument("--sugar-pretruth", required=True, type=Path)
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

    checkpoints = {
        "hdbscan": load_pretruth(args.hdbscan_pretruth, "hdbscan"),
        "sugar": load_pretruth(args.sugar_pretruth, "sugar"),
    }
    # No competitor assignments or truth have been loaded above this line.
    exact = load_module(args.exact_row_runner, "orbittrace_c1_matched_posttruth_exact")
    old = load_module(args.base_runner, "orbittrace_c1_matched_posttruth_base")
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    require(exact.sha256_file(args.mapping_audit) == exact.MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    for year in YEARS:
        require(exact.sha256_file(archives[year]) == exact.ARCHIVE_SHA256[year], f"archive hash changed {year}")
    parsers = {
        2023: load_module(args.parser_2023, "orbittrace_c1_truth_2023"),
        2025: load_module(args.parser_2025, "orbittrace_c1_truth_2025"),
    }
    assignment_paths = {
        "hdbscan": {2023: args.hdbscan_2023, 2025: args.hdbscan_2025},
        "sugar": {2023: args.sugar_2023, 2025: args.sugar_2025},
    }

    results = {
        panel: evaluate_panel(panel, checkpoints[panel], exact, base, parsers, archives, args.mapping_audit, assignment_paths)
        for panel in PANELS
    }
    broad = all(results[p]["broad_pairwise_pass"] for p in PANELS)
    sparse = all(results[p]["sparse_pairwise_pass"] for p in PANELS)
    if broad:
        classification = "BROAD_CATALOGUE_SUPERIORITY"
    elif sparse:
        classification = "SPARSE_STREAM_SUPERIORITY"
    else:
        classification = "NO_LITERATURE_SUPERIORITY"

    for panel in PANELS:
        for year in YEARS:
            require(math.isfinite(float(results[panel]["pairwise_gates"][str(year)]["macro_f1_delta_v6_minus_comparator"])),
                    f"nonfinite C1 matched endpoint {panel} {year}")

    result = {
        "classification": classification,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND_EXCLUSION),
        "c1_source_sha256": C1_SOURCE_SHA256,
        "pairwise_only_no_cross_denominator_comparison": True,
        "broad_catalogue_superiority": broad,
        "sparse_stream_superiority": sparse,
        "panels": results,
        "claim_boundary": (
            "Matched SonotaCo exact-row comparison only. C1 uses the exact frozen v6 literature superiority bars. "
            "This is not pristine external validation and does not authorize target access."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    digest = canonical_sha(result)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print("ORBITTRACE_C1_MATCHED_RESULT_BEGIN")
    print(json.dumps({
        "classification": classification,
        "broad_catalogue_superiority": broad,
        "sparse_stream_superiority": sparse,
        "panel_passes": {p: {"broad": results[p]["broad_pairwise_pass"], "sparse": results[p]["sparse_pairwise_pass"]} for p in PANELS},
    }, indent=2, sort_keys=True))
    print("ORBITTRACE_C1_MATCHED_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
