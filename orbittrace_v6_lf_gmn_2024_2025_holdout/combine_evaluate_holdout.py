from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf
from orbittrace_v6_lf_gmn_2024_2025_holdout import holdout_context as ctx

YEARS = ctx.HOLDOUT_YEARS
MIN_FAMILIES = 50
MIN_QUALIFIED = 90
MIN_RECOVERY100 = 55
MIN_MRR = 0.040
MIN_TOP100_PRECISION = 0.60
MIN_MACRO_F1 = 0.15


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year-2024", required=True, type=Path)
    p.add_argument("--year-2025", required=True, type=Path)
    p.add_argument("--repaired-v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def load_checkpoint(path: Path, year: int) -> dict[str, Any]:
    raw = path.read_bytes()
    side = path.with_suffix(".sha256")
    lf.require(side.exists(), f"missing year SHA sidecar {year}")
    lf.require(hashlib.sha256(raw).hexdigest() == side.read_text().strip().split()[0], f"year SHA mismatch {year}")
    c = pickle.loads(raw)
    lf.require(c["format"] == "orbittrace-v6-lf-year-checkpoint-v1" and int(c["year"]) == year, f"year checkpoint identity mismatch {year}")
    lf.require(c["repaired_v6_sha256"] == lf.REPAIRED_V6_SHA256, f"repaired source mismatch {year}")
    lf.require(c["firewall"]["label_values_not_accessed"] is True, f"year label firewall mismatch {year}")
    lf.require(c["firewall"]["all_event_calibration"] is True, f"year all-event calibration mismatch {year}")
    lf.require(c["firewall"]["scientific_result_not_evaluated"] is True, f"premature evaluation in year {year}")
    return c


def write_result(output: Path, result: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "v6_lf_gmn_2024_2025_temporal_holdout.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    evaluation = result.get("evaluation") or {}
    lines = [
        "# OrbitTrace v6-LF GMN 2024/2025 temporal holdout",
        "",
        f"Verdict: **`{result['verdict']}`**",
        "",
        f"- primary families: **{result['primary_family_count']}**",
        f"- pretruth SHA-256: `{result['pretruth_sha256']}`",
    ]
    if evaluation:
        lines += [
            f"- qualified: **{evaluation['qualified_matches']}**",
            f"- recovery@100: **{evaluation['recovered_at_100']}**",
            f"- MRR: **{evaluation['mrr']:.6f}**",
            f"- top-100 precision: **{evaluation['top100_dominant_precision']:.6f}**",
            f"- macro F1: **{evaluation['macro_f1']:.6f}**",
        ]
    lines += ["", "No detector parameter was tuned on GMN 2024/2025. The target interval remained excluded."]
    (output / "V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ctx.activate()
    lf.require(lf.sha256_path(args.repaired_v6_source) == lf.REPAIRED_V6_SHA256, "repaired v6 identity changed")
    checkpoints = {2024: load_checkpoint(args.year_2024, 2024), 2025: load_checkpoint(args.year_2025, 2025)}

    v6 = lf.load_module(args.repaired_v6_source, "orbittrace_v6_lf_gmn_holdout_combine")
    old = v6.load_base_runner(args.base_runner)
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    ctx.configure_runtime(v6, old, support)
    lf.require(tuple(lf.YEARS) == YEARS and tuple(old.YEARS) == YEARS and tuple(support.YEARS) == YEARS, "holdout years not active")
    lf.require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")

    scan, calibration, geometry_audits, pretruth_ids = lf.parse_geometry_only(support, base)
    for year in YEARS:
        c = checkpoints[year]
        lf.require(lf.canonical_sha(scan[year]) == c["scan_rows_sha256"], f"scan hash mismatch at combine {year}")
        lf.require(lf.canonical_sha(calibration[year]) == c["calibration_rows_sha256"], f"calibration hash mismatch at combine {year}")
        rows = [a for a in geometry_audits if str(a["key"]).startswith(str(year))]
        audit_sha = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        lf.require(audit_sha == c["geometry_audit_sha256"], f"geometry audit mismatch at combine {year}")

    components: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []
    year_audits: list[dict[str, Any]] = []
    for year in YEARS:
        components.extend(checkpoints[year]["components"])
        anchors.extend(checkpoints[year]["anchors"])
        year_audits.append(checkpoints[year]["audit"])

    primary = v6.build_family_track_v6(old, components, base, "v3")
    rescue = v6.build_family_track_v6(old, components, base, "fixed4_rescue")
    frozen = lf.freeze_families(primary, rescue)
    pretruth_sha = lf.canonical_sha(frozen)
    frozen_raw = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()
    (args.output / "v6_lf_gmn_holdout_pretruth_families.json.gz").write_bytes(gzip.compress(frozen_raw))
    (args.output / "v6_lf_gmn_holdout_pretruth.sha256").write_text(pretruth_sha + "\n")

    pretruth_integrity = {
        "complete_12_months_each_year": all(sum(1 for a in geometry_audits if str(a["key"]).startswith(str(year))) == 12 for year in YEARS),
        "exact_repaired_v6_source": lf.sha256_path(args.repaired_v6_source) == lf.REPAIRED_V6_SHA256,
        "blind_interval_exact": [float(support.BLIND_LOW), float(support.BLIND_HIGH)] == [20.0, 55.0],
        "geometry_parser_never_accessed_label_values": all(a["label_value_accessed"] is False for a in geometry_audits),
        "all_event_calibration_exact": all(len(calibration[y]) == len(scan[y]) and [e["id"] for e in calibration[y]] == [e["id"] for e in scan[y]] for y in YEARS),
        "at_least_1000_scan_rows_each_year": all(len(scan[y]) >= 1000 for y in YEARS),
        "at_least_30_supported_bins_each_year": all(len(a["supported_bins"]) >= 30 for a in year_audits),
        "proposal_budget_exact": all(a["proposal_cap_per_window"] == 512 and a["max_primary_proposals_per_year"] == 36864 for a in year_audits),
        "pretruth_family_payload_frozen_before_truth": len(pretruth_sha) == 64,
        "at_least_50_recurrent_primary_families": len(primary) >= MIN_FAMILIES,
        "all_primary_families_span_both_holdout_years": all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in primary),
        "no_retuning_or_parameter_search": True,
    }

    base_result: dict[str, Any] = {
        "method": "v6-LF all-event Mondrian null",
        "classification": "prospectively frozen no-retuning GMN 2024/2025 temporal holdout",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [20.0, 55.0],
            "calibration_reservoir": "all geometrically valid target-excluded scan events; no shower-label selection",
            "proposal_cap_per_window": 512,
            "max_primary_proposals_per_year": 36864,
            "parameter_search": False,
            "null_trimming": False,
        },
        "pretruth_sha256": pretruth_sha,
        "scan_counts": {str(y): len(scan[y]) for y in YEARS},
        "calibration_counts": {str(y): len(calibration[y]) for y in YEARS},
        "geometry_audits": geometry_audits,
        "year_audits": year_audits,
        "anchor_count": len(anchors),
        "component_count": len(components),
        "primary_family_count": len(primary),
        "rescue_family_count": len(rescue),
        "pretruth_integrity_power_gates": pretruth_integrity,
        "scientific_gates": None,
        "evaluation": None,
        "truth_audits": [],
        "claim_boundary": "Target-excluded GMN temporal generalization only; no OrbitTrace target recovery and no retuning.",
    }

    # Family-count/support power is pre-truth. If it is inadequate, stop without
    # opening shower-label values and classify the panel as power-inconclusive.
    if not all(pretruth_integrity.values()):
        base_result["verdict"] = "POWER_INCONCLUSIVE_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT"
        base_result["truth_accessed"] = False
        write_result(args.output, base_result)
        return 0

    # FIRST shower-label value access, only after complete family/rank SHA freeze
    # and all pre-truth integrity/power gates have passed.
    hidden_labels, truth_audits = lf.parse_truth_after_freeze(support, pretruth_ids)
    truth_universe_exact = set(hidden_labels) == pretruth_ids
    lf.require(truth_universe_exact, "truth/pretruth event universe changed")
    evaluation = v6.evaluate_families_v6(hidden_labels, primary, rescue, YEARS)
    scientific_gates = {
        "qualified_at_least_90": int(evaluation["qualified_matches"]) >= MIN_QUALIFIED,
        "recovery100_at_least_55": int(evaluation["recovered_at_100"]) >= MIN_RECOVERY100,
        "mrr_at_least_0040": float(evaluation["mrr"]) >= MIN_MRR,
        "top100_precision_at_least_060": float(evaluation["top100_dominant_precision"]) >= MIN_TOP100_PRECISION,
        "macro_f1_at_least_015": float(evaluation["macro_f1"]) >= MIN_MACRO_F1,
    }
    base_result.update({
        "truth_accessed": True,
        "truth_event_universe_exact": truth_universe_exact,
        "truth_audits": truth_audits,
        "evaluation": evaluation,
        "scientific_gates": scientific_gates,
        "verdict": "PASS_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT" if all(scientific_gates.values()) else "FAIL_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT",
    })
    write_result(args.output, base_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
