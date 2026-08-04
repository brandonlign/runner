from __future__ import annotations

import json
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    development = load("input/development/sonotaco_fixed4_final_development.json")
    robustness = load("input/robustness/sonotaco_fixed4_seed_robustness.json")
    replication = load("input/replication/sonotaco_2023_fixed4_confirmation.json")

    dev_failed = [name for name, passed in development["gates"].items() if not passed]
    robust_failed = [name for name, passed in robustness["gates"].items() if not passed]
    replication_failed = [name for name, passed in replication["gates"].items() if not passed]

    evidence_gates = {
        "development_verdict_exact": development["verdict"] == "PASS_SONOTACO_FIXED4_FINAL_DEVELOPMENT",
        "development_all_26_gates_pass": len(development["gates"]) == 26 and not dev_failed,
        "development_fixed_scale_exactly_4": development["configuration"]["candidate_solar_scale_deg_per_unit"] == 4.0,
        "robustness_verdict_exact": robustness["verdict"] == "KILL_SONOTACO_FIXED4_SEED_ROBUSTNESS",
        "robustness_exactly_one_failed_gate": robust_failed == ["median_k6_k8_no_material_drop_vs_original"],
        "robustness_two_of_three_fresh_panels_pass": robustness["fresh_full_pass_count"] == 2,
        "replication_verdict_exact": replication["verdict"] == "FAIL_SONOTACO_2023_FIXED4_CONFIRMATION",
        "replication_exactly_one_failed_gate": replication_failed == ["recall_001_k4_ge_005"],
        "replication_32_of_33_gates_pass": len(replication["gates"]) == 33 and sum(replication["gates"].values()) == 32,
        "replication_strict_k4_count_exact": abs(replication["recall"]["0.01"]["4"] - 3 / 164) < 1e-15,
        "replication_moderate_k4_pass": replication["recall"]["0.05"]["4"] >= 0.15,
        "replication_k6_k8_pass_both_alphas": (
            replication["recall"]["0.05"]["6"] >= 0.30
            and replication["recall"]["0.01"]["6"] >= 0.15
            and replication["recall"]["0.05"]["8"] >= 0.45
            and replication["recall"]["0.01"]["8"] >= 0.25
        ),
        "replication_calibration_and_auc_pass": all(
            replication["gates"][name]
            for name in (
                "pooled_fpr_005_le_006",
                "pooled_fpr_001_le_002",
                "worst_reporting_sector_fpr_005_le_012",
                "candidate_weak_auc_ge_075",
                "candidate_auc_within_003_of_strongest_comparator",
                "four_of_five_folds_auc_ge_070",
                "no_fold_auc_below_065",
            )
        ),
    }
    if not all(evidence_gates.values()):
        raise RuntimeError(f"frozen evidence mismatch: {evidence_gates}")

    final_status = "PROMISING_STRONG_TRANSFER_NOT_FULLY_ROBUSTLY_REPLICATED"
    result = {
        "status": final_status,
        "method": "coverage-normalized Mondrian anchored nearest-three complete-link four-clique detector",
        "fixed_solar_longitude_scale_deg_per_unit": 4.0,
        "development": {
            "verdict": development["verdict"],
            "gates_passed": [sum(development["gates"].values()), len(development["gates"])],
            "candidate_weak_auc": development["candidate"]["weak_auc"],
            "false_positive": development["candidate"]["fpr"],
            "worst_reporting_sector_0.05": development["candidate"]["worst_sector_fpr_005"],
            "recall": development["candidate"]["recall"],
        },
        "calibration_seed_robustness": {
            "verdict": robustness["verdict"],
            "gates_passed": [sum(robustness["gates"].values()), len(robustness["gates"])],
            "failed_gates": robust_failed,
            "fresh_full_pass_count": robustness["fresh_full_pass_count"],
            "fresh_median": robustness["fresh_median"],
        },
        "replacement_independent_replication": {
            "verdict": replication["verdict"],
            "gates_passed": [sum(replication["gates"].values()), len(replication["gates"])],
            "failed_gates": replication_failed,
            "candidate_weak_auc": replication["candidate_weak_auc"],
            "fixed_comparator_weak_auc": replication["fixed_comparator_weak_auc"],
            "false_positive": replication["false_positive"],
            "worst_reporting_sector_0.05": replication["worst_reporting_sector_0.05"],
            "recall": replication["recall"],
            "fold_candidate_aucs": [record["candidate_auc"] for record in replication["fold_results"]],
        },
        "interpretation": {
            "independently_confirmed_under_complete_standard": False,
            "strong_ranking_calibration_and_k_ge_6_transfer": True,
            "strict_tail_k4_replication": False,
            "calibration_panel_stability_under_declared_standard": False,
            "further_tuning_or_panels_authorized": False,
            "ghoststream_application_authorized_by_this_workflow": False,
        },
        "evidence_gates": evidence_gates,
    }

    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    (output / "FINAL_FIXED4_METHODOLOGY_STATUS.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    dev = result["development"]
    robust = result["calibration_seed_robustness"]
    repl = result["replacement_independent_replication"]
    lines = [
        "# Final fixed-4° methodology evidence status",
        "",
        f"**Status: `{final_status}`**",
        "",
        "The fixed-4° detector is a credible, well-calibrated methodology candidate with strong ranking and k≥6 transfer, but it did not satisfy the complete preregistered robustness-and-replication standard.",
        "",
        "## Frozen evidence",
        "",
        f"- **2025 standalone development:** `{dev['verdict']}` — {dev['gates_passed'][0]}/{dev['gates_passed'][1]} gates passed; weak AUROC {dev['candidate_weak_auc']:.6f}.",
        f"- **2025 calibration-seed robustness:** `{robust['verdict']}` — {robust['gates_passed'][0]}/{robust['gates_passed'][1]} gates passed; two of three fresh panels passed, but the fresh-panel median lost too much k=6 alpha-0.05 recall.",
        f"- **2023 replacement independent replication:** `{repl['verdict']}` — {repl['gates_passed'][0]}/{repl['gates_passed'][1]} gates passed; weak AUROC {repl['candidate_weak_auc']:.6f}.",
        "",
        "## Independent-panel performance",
        "",
        f"- pooled FPR at alpha 0.05 / 0.01: **{repl['false_positive']['0.05']:.6f} / {repl['false_positive']['0.01']:.6f}**;",
        f"- fold AUROCs: **{', '.join(f'{value:.4f}' for value in repl['fold_candidate_aucs'])}**;",
        f"- k=4 recall: **{repl['recall']['0.05']['4']:.6f} / {repl['recall']['0.01']['4']:.6f}**;",
        f"- k=6 recall: **{repl['recall']['0.05']['6']:.6f} / {repl['recall']['0.01']['6']:.6f}**;",
        f"- k=8 recall: **{repl['recall']['0.05']['8']:.6f} / {repl['recall']['0.01']['8']:.6f}**.",
        "",
        "## Defensible conclusion",
        "",
        "The method should be described as **promising and strongly transferring, but not independently confirmed under the complete frozen standard**. The replication failure is strict-tail four-member sensitivity at alpha 0.01; the seed-robustness failure is moderate k=6 calibration-panel sensitivity. These are real limitations and may not be repaired by further tuning, reseeding, additional panels, larger calibration sets, or gate changes.",
        "",
        "GhostStream remained blinded throughout this synthesis. This workflow authorizes no GhostStream application or catalogue scan.",
    ]
    (output / "FINAL_FIXED4_METHODOLOGY_STATUS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
