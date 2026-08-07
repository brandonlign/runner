#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PANEL_SPECS = {
    "2020_2021": {
        "verdict": "INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER",
        "json": "saamer_external_validation.json",
    },
    "2022_2023": {
        "verdict": "INCONCLUSIVE_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_POWER",
        "json": "saamer_2022_2023_external_validation.json",
    },
}
POWERED_PASS = {
    "PASS_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION",
    "PASS_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION",
}
POWERED_FAIL = {
    "FAIL_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION",
    "FAIL_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION",
}
INTEGRITY_FAIL = {
    "FAIL_LABEL_FREE_V6_SAAMER_EXTERNAL_INTEGRITY",
    "FAIL_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_INTEGRITY",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def panel_summary(name: str, result: dict) -> dict:
    verdict = result["verdict"]
    require(verdict == PANEL_SPECS[name]["verdict"], f"{name} frozen verdict changed: {verdict}")
    n = int(result["family_count"])
    q = int(result["orbital_summary"]["orbitally_corroborated_families"])
    metrics = result["metrics"]
    ranking_names = ("multiplicity", "label_free_persistence", "brown", "v3")
    require(set(ranking_names).issubset(metrics), f"{name} missing ranking metrics")
    ks = {int(metrics[key]["top_k"]) for key in ranking_names}
    require(len(ks) == 1, f"{name} top-K differs across rankings")
    k = ks.pop()
    counts = {key: int(metrics[key]["top_k_orbitally_corroborated"]) for key in ranking_names}
    pvals = {key: float(metrics[key]["hypergeometric_enrichment_p"]) for key in ranking_names}
    medians = {key: metrics[key]["median_rank"] for key in ranking_names}
    mrr = {key: float(metrics[key]["mrr"]) for key in ranking_names}

    # These are the common scientific-integrity gates shared by both panel implementations.
    integrity = result["integrity_gates"]
    power_keys = {"at_least_100_recurrent_families", "at_least_30_orbitally_corroborated_families"}
    nonpower_integrity = {key: bool(value) for key, value in integrity.items() if key not in power_keys}
    nonpower_integrity_clean = all(nonpower_integrity.values())

    return {
        "panel": name,
        "original_verdict": verdict,
        "family_count_N": n,
        "orbitally_corroborated_Q": q,
        "registered_K": k,
        "N_ge_100": n >= 100,
        "Q_ge_30": q >= 30,
        "K_less_than_N": k < n,
        "topk_equals_full_family_universe": k == n,
        "nonpower_integrity_clean": nonpower_integrity_clean,
        "nonpower_integrity_gates": nonpower_integrity,
        "topk_corroborated_counts": counts,
        "hypergeometric_p": pvals,
        "descriptive_median_rank": medians,
        "descriptive_mrr": mrr,
        "ranking_endpoint_can_distinguish_counts": len(set(counts.values())) > 1 and k < n,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-2020-2021", required=True, type=Path)
    parser.add_argument("--panel-2022-2023", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    inputs = {
        "2020_2021": json.loads(args.panel_2020_2021.read_text()),
        "2022_2023": json.loads(args.panel_2022_2023.read_text()),
    }
    summaries = {name: panel_summary(name, result) for name, result in inputs.items()}
    verdicts = {result["verdict"] for result in inputs.values()}

    if verdicts & POWERED_PASS:
        terminal_verdict = "TERMINAL_EXTERNAL_VALIDATION_POWERED_PASS"
    elif verdicts & INTEGRITY_FAIL:
        terminal_verdict = "TERMINAL_EXTERNAL_VALIDATION_INTEGRITY_FAILURE"
    elif verdicts & POWERED_FAIL:
        terminal_verdict = "TERMINAL_EXTERNAL_VALIDATION_SCIENTIFIC_FAIL"
    else:
        require(all(summary["nonpower_integrity_clean"] for summary in summaries.values()), "non-power integrity was not clean")
        require(all(not summary["N_ge_100"] for summary in summaries.values()), "unexpected powered family universe without pass/fail verdict")
        terminal_verdict = "TERMINAL_EXTERNAL_VALIDATION_INCONCLUSIVE_POWER_LIMITED"

    authorizes_target_reveal = bool(verdicts & POWERED_PASS)
    endpoint_degenerate_both = all(summary["topk_equals_full_family_universe"] for summary in summaries.values())

    result = {
        "verdict": terminal_verdict,
        "panels": summaries,
        "cross_panel_facts": {
            "completed_panels": 2,
            "all_nonpower_integrity_clean": all(summary["nonpower_integrity_clean"] for summary in summaries.values()),
            "both_panels_below_N100": all(not summary["N_ge_100"] for summary in summaries.values()),
            "Q_counts": {name: summary["orbitally_corroborated_Q"] for name, summary in summaries.items()},
            "N_counts": {name: summary["family_count_N"] for name, summary in summaries.items()},
            "registered_topk_equals_N_in_both_panels": endpoint_degenerate_both,
            "no_panel_has_powered_pass": not bool(verdicts & POWERED_PASS),
            "no_panel_has_powered_scientific_fail": not bool(verdicts & POWERED_FAIL),
        },
        "authorizes_target_reveal": authorizes_target_reveal,
        "pooling_or_new_pass_statistic_used": False,
        "reranking_performed": False,
        "catalogue_access": False,
        "target_information_access": False,
        "interpretation": (
            "Label-free v6 passed target-excluded development, and both frozen SAAMER external executions were clean on non-power integrity. "
            "However, the preregistered recurrent-family universe minimum N>=100 was missed independently in both panels (69 and 66), so K=min(100,N) equaled the full family universe in both. "
            "The registered top-K ranking-superiority endpoint therefore could not distinguish rankings. External validation remains power-limited and inconclusive; no external superiority or OrbitTrace target-reveal authorization is created by this synthesis."
        ),
        "claim_boundary": (
            "Artifact-only terminal synthesis. It does not pool panels, invent a combined significance test, alter any frozen gate, access a meteor catalogue, or access OrbitTrace target information."
        ),
    }
    (args.output / "terminal_saamer_synthesis.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# OrbitTrace label-free v6 terminal SAAMER synthesis",
        "",
        f"Verdict: **`{terminal_verdict}`**",
        "",
        f"- 2020/2021: N={summaries['2020_2021']['family_count_N']}, Q={summaries['2020_2021']['orbitally_corroborated_Q']}, K={summaries['2020_2021']['registered_K']}",
        f"- 2022/2023: N={summaries['2022_2023']['family_count_N']}, Q={summaries['2022_2023']['orbitally_corroborated_Q']}, K={summaries['2022_2023']['registered_K']}",
        f"- non-power integrity clean in both: **{result['cross_panel_facts']['all_nonpower_integrity_clean']}**",
        f"- K=N in both panels: **{endpoint_degenerate_both}**",
        f"- authorizes OrbitTrace target reveal: **{authorizes_target_reveal}**",
        "",
        "No pooled pass criterion or new significance test was introduced. The external programme is terminally power-limited under its preregistered ranking endpoint.",
    ]
    (args.output / "TERMINAL_SAAMER_SYNTHESIS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
