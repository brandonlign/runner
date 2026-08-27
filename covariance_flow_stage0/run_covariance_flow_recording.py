from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import rebound
from scipy.stats import spearmanr

import run_covariance_flow as base


def diagnostic_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels = np.asarray(
        [1 if record["label"] == "shower" else 0 for record in records],
        dtype=np.int32,
    )
    result: dict[str, Any] = {
        "valid_group_count": len(records),
        "valid_shower_count": int(np.sum(labels == 1)),
        "valid_sporadic_count": int(np.sum(labels == 0)),
    }
    if result["valid_shower_count"] and result["valid_sporadic_count"]:
        deconvolved_scores = np.asarray(
            [record["deconvolved_score"] for record in records],
            dtype=np.float64,
        )
        raw_scores = np.asarray(
            [record["raw_score"] for record in records],
            dtype=np.float64,
        )
        uncertainties = np.asarray(
            [record["median_log_uncertainty"] for record in records],
            dtype=np.float64,
        )
        result["valid_only_deconvolved_auroc"] = base.auc(
            labels, deconvolved_scores
        )
        result["valid_only_raw_auroc"] = base.auc(labels, raw_scores)
        rho = spearmanr(deconvolved_scores, uncertainties).statistic
        result["valid_only_score_uncertainty_spearman"] = (
            float(rho) if math.isfinite(float(rho)) else None
        )
    return result


def main() -> None:
    args = base.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    events = base.load_clone_ready_events(args.events)
    groups = base.build_groups(events)
    records: list[dict[str, Any]] = []
    invalid_groups: list[dict[str, Any]] = []

    for index, group in enumerate(groups):
        try:
            (
                raw_covariance,
                deconvolved_covariance,
                median_log_uncertainty,
            ) = base.covariance_pair(group.events)
            medoid = base.group_medoid(group.events)
            medoid_feature = base.event_feature(medoid)
            basis, node_branch, node_radius = base.tangent_basis(medoid_feature)
            flow = base.local_flow(group.events)
            (
                deconvolved_percentile,
                deconvolved_score,
                deconvolved_diagnostics,
            ) = base.orientation_percentile(
                deconvolved_covariance,
                basis,
                flow.jacobian,
                base.stable_seed("deconvolved", group.group_id),
            )
            raw_percentile, raw_score, raw_diagnostics = (
                base.orientation_percentile(
                    raw_covariance,
                    basis,
                    flow.jacobian,
                    base.stable_seed("raw", group.group_id),
                )
            )
            record = {
                "group_id": group.group_id,
                "label": group.label,
                "control": group.control,
                "subgroup": group.subgroup,
                "event_ids": [str(event["id"]) for event in group.events],
                "orbit_match_distance": group.orbit_match_distance,
                "medoid_event_id": flow.medoid_event_id,
                "node_branch": node_branch,
                "node_radius_au": node_radius,
                "relative_energy_error": flow.relative_energy_error,
                "median_log_uncertainty": median_log_uncertainty,
                "deconvolved_percentile": deconvolved_percentile,
                "deconvolved_score": deconvolved_score,
                "raw_percentile": raw_percentile,
                "raw_score": raw_score,
                "deconvolved_diagnostics": deconvolved_diagnostics,
                "raw_diagnostics": raw_diagnostics,
            }
            records.append(record)
            print(
                f"[{index + 1:02d}/{len(groups)}] VALID {group.group_id} "
                f"p={deconvolved_percentile:.4f} "
                f"energy={flow.relative_energy_error:.3e}"
            )
        except Exception as exc:  # scientific invalidity must be preserved
            invalid = {
                "group_id": group.group_id,
                "label": group.label,
                "control": group.control,
                "subgroup": group.subgroup,
                "event_ids": [str(event["id"]) for event in group.events],
                "orbit_match_distance": group.orbit_match_distance,
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            }
            invalid_groups.append(invalid)
            print(
                f"[{index + 1:02d}/{len(groups)}] INVALID {group.group_id}: "
                f"{type(exc).__name__}: {exc}"
            )

    if invalid_groups:
        gates = {
            "all_energy_errors_at_most_1e_8": False,
            "deconvolved_auroc_at_least_0_75": False,
            "three_controls_median_percentile_at_most_0_20": False,
            "ten_of_sixteen_showers_percentile_at_most_0_20": False,
            "sporadic_low_percentile_fraction_at_most_0_20": False,
            "uncertainty_spearman_absolute_at_most_0_30": False,
            "deconvolved_auroc_not_more_than_0_05_worse_than_raw": False,
            "no_control_more_than_half_positive_separation": False,
        }
        evaluation = {
            "verdict": "KILL_COVARIANCE_FLOW_LOCAL_MAP_NOT_DEFINED_FOR_ALL_GROUPS",
            "invalid_group_count": len(invalid_groups),
            "valid_group_count": len(records),
            "gates": gates,
            "valid_only_diagnostics": diagnostic_metrics(records),
        }
    else:
        evaluation = base.evaluate(records)
        evaluation["invalid_group_count"] = 0
        evaluation["valid_group_count"] = len(records)

    payload = {
        "configuration": {
            "controls": base.CONTROLS,
            "years": base.YEARS,
            "rotations": base.ROTATIONS,
            "lookback_years": base.LOOKBACK_YEARS,
            "flow_step": base.FLOW_STEP,
            "gradient_step": base.GRADIENT_STEP,
            "energy_tolerance": base.ENERGY_TOLERANCE,
            "rebound_version": rebound.__version__,
            "packaged_initial_conditions": "outer solar system",
            "source_artifact_id": 8869994126,
            "source_artifact_digest": "sha256:bc6df6971b5d306af9836b2df71aebbacd6c3f4045ea1b8c1d5268caedc2c322",
            "execution_correction": (
                "Invalid propagated perturbations are recorded as failed groups "
                "instead of aborting before the frozen all-groups gate is evaluated."
            ),
        },
        "evaluation": evaluation,
        "valid_groups": records,
        "invalid_groups": invalid_groups,
    }
    (args.output / "covariance_flow_result.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    lines = [
        "# Noise-deconvolved covariance-flow Stage-0",
        "",
        "GhostStream was excluded. Invalid local flow maps count as failures of the frozen all-groups integration gate.",
        "",
        f"- valid groups: **{len(records)}/80**",
        f"- invalid groups: **{len(invalid_groups)}/80**",
    ]
    valid_diagnostics = evaluation.get("valid_only_diagnostics", {})
    if "valid_only_deconvolved_auroc" in valid_diagnostics:
        lines.extend(
            [
                f"- valid-only deconvolved AUROC, diagnostic only: **{valid_diagnostics['valid_only_deconvolved_auroc']:.4f}**",
                f"- valid-only raw AUROC, diagnostic only: **{valid_diagnostics['valid_only_raw_auroc']:.4f}**",
            ]
        )
    lines.extend(["", "## Frozen gates", ""])
    for gate, passed in evaluation["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend(["", f"Verdict: **{evaluation['verdict']}**"])
    report = "\n".join(lines)
    (args.output / "STAGE0_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
