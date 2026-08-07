#!/usr/bin/env python3
"""Frozen one-shot prospective 2016 v8 scientific gates.

This evaluator is source-audited and hashed before the prospective archive is
scientifically scored. It contains no tuning path and no alternative v8 method.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SELECTED = "orbittrace_v3_fixed4_offset_pos050_v8"
BROWN = "brown2010_wavelet_episode_core"
FIXED4 = "orbittrace_fixed4"
V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
REPORTING_ALPHA = "0.05"
FPR_CAP = 0.055
WORST_SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03
EXPECTED_SUPPORTED_BINS = [0,1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]
EXPECTED_ELIGIBLE_SHOWERS = 30
EXPECTED_CALIBRATION_ROWS = 4224
EXPECTED_NEGATIVE_ROWS = 2112
EXPECTED_POSITIVE_ROWS = 480
EXPECTED_ARCHIVE_SHA256 = "f1fc4586d3efe71b9dc419261c9ad252c5d4f12e80439e94b56c86445520e530"
EXPECTED_MEMBER_SHA256 = "6035614d6aa663f0ab0ed63e8e93f439d6e3969307085fc872eb2aaeff79be1f"
EXPECTED_PARSER_SHA256 = "96035178fba30ecbfcbc53e35745b2032417ee9989a850009aeddb0041150cf2"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text())
    metrics = payload["metrics"]
    for method in (SELECTED, BROWN, FIXED4, V3):
        if method not in metrics:
            raise RuntimeError(f"required prospective method missing: {method}")

    selected = metrics[SELECTED]
    brown = metrics[BROWN]
    fixed4 = metrics[FIXED4]
    v3 = metrics[V3]
    rs = selected["recall"][REPORTING_ALPHA]
    rb = brown["recall"][REPORTING_ALPHA]
    rf = fixed4["recall"][REPORTING_ALPHA]
    freeze = payload.get("prospective_2016_freeze", {})
    configuration = payload.get("configuration", {})

    gates = {
        "selected_auc_above_brown": float(selected["weak_auc"]) > float(brown["weak_auc"]),
        "selected_k4_at_least_fixed4": float(rs["4"]) >= float(rf["4"]),
        "selected_k6_within_003_brown": float(rs["6"]) >= float(rb["6"]) - RECALL_TOLERANCE,
        "selected_k8_within_003_brown": float(rs["8"]) >= float(rb["8"]) - RECALL_TOLERANCE,
        "selected_k12_within_003_brown": float(rs["12"]) >= float(rb["12"]) - RECALL_TOLERANCE,
        "selected_fpr_005_at_most_0055": float(selected["fpr"][REPORTING_ALPHA]) <= FPR_CAP,
        "selected_worst_sector_fpr_005_at_most_008": float(selected["worst_sector_fpr_005"]) <= WORST_SECTOR_FPR_CAP,
        "all_runner_integrity_gates": all(bool(value) for value in payload["gates"].values()),
        "year_exact_2016": int(configuration.get("year", -1)) == 2016,
        "corpus_exact": configuration.get("corpus") == "sonotaco-2016-prospective",
        "supported_bins_exact": list(configuration.get("supported_bins", [])) == EXPECTED_SUPPORTED_BINS,
        "eligible_showers_exact": int(configuration.get("eligible_showers", -1)) == EXPECTED_ELIGIBLE_SHOWERS,
        "calibration_per_bin_exact": int(configuration.get("calibration_per_bin", -1)) == 128,
        "negative_per_bin_exact": int(configuration.get("negative_per_bin", -1)) == 64,
        "positive_replicates_exact": int(configuration.get("positive_replicates", -1)) == 4,
        "archive_hash_exact": freeze.get("archive_sha256") == EXPECTED_ARCHIVE_SHA256,
        "member_hash_exact": freeze.get("member_sha256") == EXPECTED_MEMBER_SHA256,
        "parser_hash_exact": freeze.get("parser_sha256") == EXPECTED_PARSER_SHA256,
        "frozen_supported_bins_exact": freeze.get("supported_bins") == EXPECTED_SUPPORTED_BINS,
        "frozen_eligible_showers_exact": int(freeze.get("eligible_showers", -1)) == EXPECTED_ELIGIBLE_SHOWERS,
        "frozen_episode_counts_exact": (
            int(freeze.get("calibration_rows", -1)) == EXPECTED_CALIBRATION_ROWS
            and int(freeze.get("negative_rows", -1)) == EXPECTED_NEGATIVE_ROWS
            and int(freeze.get("positive_rows", -1)) == EXPECTED_POSITIVE_ROWS
        ),
        "selected_method_exact": freeze.get("selected_method") == SELECTED,
        "selected_offset_exact": float(freeze.get("selected_offset", -999.0)) == 0.50,
    }

    verdict = "PASS_V8_SONOTACO_2016_PROSPECTIVE_VALIDATION" if all(gates.values()) else "FAIL_V8_SONOTACO_2016_PROSPECTIVE_VALIDATION"
    result = {
        "verdict": verdict,
        "classification": "one-shot prospective validation; no post-result tuning authorized",
        "year": 2016,
        "selected_method": SELECTED,
        "selected_offset": 0.50,
        "metrics": {
            "selected_weak_auc": selected["weak_auc"],
            "brown_weak_auc": brown["weak_auc"],
            "fixed4_weak_auc": fixed4["weak_auc"],
            "v3_weak_auc": v3["weak_auc"],
            "selected_fpr_005": selected["fpr"][REPORTING_ALPHA],
            "selected_worst_sector_fpr_005": selected["worst_sector_fpr_005"],
            "selected_recall_005": rs,
            "brown_recall_005": rb,
            "fixed4_recall_005": rf,
        },
        "gates": gates,
        "freeze": freeze,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "V8_SONOTACO_2016_PROSPECTIVE_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    lines = [
        "# OrbitTrace v8 SonotaCo 2016 prospective validation",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Selected AUROC: **{float(selected['weak_auc']):.6f}** vs Brown **{float(brown['weak_auc']):.6f}**",
        "",
        f"Selected FPR .05: **{float(selected['fpr'][REPORTING_ALPHA]):.6f}**; worst sector: **{float(selected['worst_sector_fpr_005']):.6f}**",
        "",
        "Selected recall k=4/6/8/12: **" + " / ".join(f"{float(rs[str(k)]):.6f}" for k in (4,6,8,12)) + "**",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    (args.output / "V8_SONOTACO_2016_PROSPECTIVE_RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
