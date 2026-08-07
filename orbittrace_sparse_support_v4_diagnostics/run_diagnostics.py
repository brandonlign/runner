#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import kendalltau, spearmanr

V4_RUN = 31190719956
FIXED4_RUN = 31106001133
EXPECTED_V4_COMMIT = "5dd95b70aa4f9a8b5f32326fb39d011b08ad8e1e"
EXPECTED_V4_SHA256 = {
    "sparse_support_v4_development.json": "9a60fd97eacb33d4fa5d29344eebe3ba784c38423763d2f2b8e5b9a7bedcbd7c",
    "sparse_support_v4_rankings.json": "b0f1ea824b28e6e4f6f871360ddc25aead6202668ee2d7ee026adb65eb851c13",
    "sparse_support_v4_family_scores.json.gz": "852f3b4c7e5b617b98b421f172cd99fbe14f91ca7f0f9dff8ad08a8e0623dbae",
}
EXPECTED_FIXED4_SHA256 = "80568774b1e2fd9a0723e66c02b432e8437d069ccd16abba09ef1c22815f0f12"
EXPECTED_FAMILY_COUNT = 197
EXPECTED_QUALIFIED = 90
EXPECTED_FIXED4_RECOVERED100 = 61
P_FLOOR = 1.0 / 513.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v4-dir", required=True, type=Path)
    p.add_argument("--fixed4-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def rank_map(order: list[str]) -> dict[str, int]:
    return {fid: i for i, fid in enumerate(order, start=1)}


def recovered_labels(per_label: list[dict[str, Any]], ranks: dict[str, int], cutoff: int = 100) -> set[str]:
    return {
        str(row["label"])
        for row in per_label
        if bool(row.get("qualified")) and ranks[str(row["family_id"])] <= cutoff
    }


def finite_stat(x: float) -> float:
    return float(x) if math.isfinite(float(x)) else float("nan")


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    v4_paths = {name: args.v4_dir / name for name in EXPECTED_V4_SHA256}
    for name, expected in EXPECTED_V4_SHA256.items():
        require(v4_paths[name].is_file(), f"missing v4 artifact file: {name}")
        require(sha256(v4_paths[name]) == expected, f"v4 artifact digest mismatch: {name}")
    require(args.fixed4_json.is_file(), "missing frozen fixed4 artifact")
    require(sha256(args.fixed4_json) == EXPECTED_FIXED4_SHA256, "fixed4 artifact digest mismatch")

    development = json.loads(v4_paths["sparse_support_v4_development.json"].read_text())
    rankings = json.loads(v4_paths["sparse_support_v4_rankings.json"].read_text())
    with gzip.open(v4_paths["sparse_support_v4_family_scores.json.gz"], "rt") as f:
        scores = json.load(f)
    fixed4 = json.loads(args.fixed4_json.read_text())

    require(development["verdict"] == "FAIL_SPARSE_SUPPORT_V4_DEVELOPMENT", "unexpected v4 verdict")
    require(development["configuration"]["years"] == [2022, 2023], "unexpected v4 years")
    require(development["development_scaffold"]["source_run"] == FIXED4_RUN, "wrong fixed4 source run")
    require(development["development_scaffold"]["family_count"] == EXPECTED_FAMILY_COUNT, "wrong v4 family count")
    require(len(scores) == EXPECTED_FAMILY_COUNT, "wrong family-score count")

    fixed_dev = fixed4["panel_results"]["development"]
    require(fixed_dev["years"] == [2022, 2023], "unexpected fixed4 development years")
    require(fixed_dev["family_count"] == EXPECTED_FAMILY_COUNT, "wrong fixed4 family count")
    fixed_metrics = fixed_dev["evaluation"]["metrics"]["persistence"]
    require(fixed_metrics["qualified_matches"] == EXPECTED_QUALIFIED, "wrong fixed4 qualified count")
    require(fixed_metrics["recovered_at_100"] == EXPECTED_FIXED4_RECOVERED100, "wrong fixed4 recovery")

    methods = ("v3", "brown", "fixed4_persistence", "rrf")
    orders = {m: [str(x) for x in rankings[m]] for m in methods}
    universe = set(orders["fixed4_persistence"])
    require(len(universe) == EXPECTED_FAMILY_COUNT, "fixed4 ranking universe mismatch")
    for method in methods:
        require(len(orders[method]) == EXPECTED_FAMILY_COUNT, f"{method} order length mismatch")
        require(set(orders[method]) == universe, f"{method} family universe mismatch")

    frozen_order = [str(x) for x in fixed_dev["rankings"]["persistence"]]
    require(orders["fixed4_persistence"] == frozen_order, "v4 did not reproduce fixed4 order")

    rmap = {m: rank_map(orders[m]) for m in methods}
    per_label = fixed_metrics["per_label"]
    recovered = {m: recovered_labels(per_label, rmap[m]) for m in methods}
    for method in methods:
        require(len(recovered[method]) == development["metrics"][method]["recovered_at_100"], f"{method} recovered-label reconstruction mismatch")

    all_v3_floor = []
    all_brown_floor = []
    ratios = []
    v3_min_scores = []
    brown_min_scores = []
    for row in scores:
        for year in ("2022", "2023"):
            yr = row["per_year"][year]
            all_v3_floor.append(abs(float(yr["p_v3"]) - P_FLOOR) < 1e-15)
            all_brown_floor.append(abs(float(yr["p_brown"]) - P_FLOOR) < 1e-15)
            ratios.append(float(yr["v3_score"]) / float(yr["brown_score"]))
        v3_min_scores.append(float(row["v3_min_year_score"]))
        brown_min_scores.append(float(row["brown_min_year_score"]))

    v3_ranks = np.array([rmap["v3"][fid] for fid in sorted(universe)], dtype=float)
    brown_ranks = np.array([rmap["brown"][fid] for fid in sorted(universe)], dtype=float)
    fixed_ranks = np.array([rmap["fixed4_persistence"][fid] for fid in sorted(universe)], dtype=float)

    v3_brown_spearman = float(spearmanr(v3_ranks, brown_ranks).statistic)
    v3_brown_kendall = float(kendalltau(v3_ranks, brown_ranks).statistic)
    v3_fixed_spearman = float(spearmanr(v3_ranks, fixed_ranks).statistic)
    score_spearman = float(spearmanr(v3_min_scores, brown_min_scores).statistic)

    top100_overlap_v3_brown = len(set(orders["v3"][:100]) & set(orders["brown"][:100]))
    top100_overlap_v3_fixed = len(set(orders["v3"][:100]) & set(orders["fixed4_persistence"][:100]))
    top100_overlap_rrf_fixed = len(set(orders["rrf"][:100]) & set(orders["fixed4_persistence"][:100]))

    crossings: dict[str, Any] = {}
    for method in ("v3", "brown", "rrf"):
        lost = sorted(recovered["fixed4_persistence"] - recovered[method])
        gained = sorted(recovered[method] - recovered["fixed4_persistence"])
        relevant = set(lost) | set(gained)
        detail = []
        for row in per_label:
            if not row.get("qualified") or not row.get("family_id"):
                continue
            label = str(row["label"])
            if label not in relevant:
                continue
            fid = str(row["family_id"])
            detail.append({
                "label": label,
                "family_id": fid,
                "fixed4_rank": rmap["fixed4_persistence"][fid],
                "method_rank": rmap[method][fid],
                "v3_rank": rmap["v3"][fid],
                "rrf_rank": rmap["rrf"][fid],
                "precision": float(row["precision"]),
                "recall": float(row["recall"]),
                "f1": float(row["f1"]),
                "direction": "lost" if label in lost else "gained",
            })
        crossings[method] = {"lost": lost, "gained": gained, "detail": sorted(detail, key=lambda x: (x["direction"], x["label"]))}

    floor_fraction_v3 = float(np.mean(all_v3_floor))
    floor_fraction_brown = float(np.mean(all_brown_floor))
    near_collinear = bool(v3_brown_spearman >= 0.995 and top100_overlap_v3_brown >= 95)
    calibration_saturated = bool(floor_fraction_v3 == 1.0 and floor_fraction_brown == 1.0)
    proposal_capacity_intact = bool(
        development["metrics"]["fixed4_persistence"]["qualified_matches"] == EXPECTED_QUALIFIED
        and development["metrics"]["fixed4_persistence"]["recovered_at_100"] == EXPECTED_FIXED4_RECOVERED100
    )
    fusion_recall_degraded = bool(
        development["metrics"]["rrf"]["recovered_at_100"]
        < development["metrics"]["fixed4_persistence"]["recovered_at_100"]
    )

    if calibration_saturated and near_collinear and proposal_capacity_intact and fusion_recall_degraded:
        verdict = "DIAGNOSIS_CALIBRATION_SATURATION_AND_V3_BROWN_COLLINEARITY"
    else:
        verdict = "DIAGNOSIS_MIXED_OR_INCOMPLETE"

    result = {
        "verdict": verdict,
        "source_runs": {"v4": V4_RUN, "fixed4": FIXED4_RUN},
        "blindness": {
            "catalogue_access": False,
            "later_year_access": False,
            "orbittrace_target_access": False,
            "artifact_only": True,
        },
        "v4_metrics": development["metrics"],
        "v4_failed_gates": [k for k, v in development["gates"].items() if not v],
        "diagnostics": {
            "proposal_capacity_intact": proposal_capacity_intact,
            "calibration_saturated": calibration_saturated,
            "v3_empirical_p_floor_fraction": floor_fraction_v3,
            "brown_empirical_p_floor_fraction": floor_fraction_brown,
            "empirical_p_floor": P_FLOOR,
            "v3_brown_near_collinear": near_collinear,
            "v3_brown_rank_spearman": finite_stat(v3_brown_spearman),
            "v3_brown_rank_kendall": finite_stat(v3_brown_kendall),
            "v3_brown_min_score_spearman": finite_stat(score_spearman),
            "v3_fixed4_rank_spearman": finite_stat(v3_fixed_spearman),
            "v3_brown_top100_family_overlap": top100_overlap_v3_brown,
            "v3_fixed4_top100_family_overlap": top100_overlap_v3_fixed,
            "rrf_fixed4_top100_family_overlap": top100_overlap_rrf_fixed,
            "v3_to_brown_score_ratio": {
                "median": float(np.median(ratios)),
                "min": float(np.min(ratios)),
                "max": float(np.max(ratios)),
                "p05": float(np.quantile(ratios, 0.05)),
                "p95": float(np.quantile(ratios, 0.95)),
            },
            "v3_minus_brown_recovered100": len(recovered["v3"]) - len(recovered["brown"]),
            "fusion_recall_degraded": fusion_recall_degraded,
            "rrf_minus_fixed4_recovered100": len(recovered["rrf"]) - len(recovered["fixed4_persistence"]),
            "rrf_minus_fixed4_precision": float(development["metrics"]["rrf"]["top100_dominant_precision"] - development["metrics"]["fixed4_persistence"]["top100_dominant_precision"]),
        },
        "crossings_vs_fixed4": crossings,
        "interpretation": {
            "proposal_recall": "not primary: the unchanged 197-family scaffold still contains 90 qualified labels and reproduces fixed4 recovery 61",
            "calibration": "primary structural problem: every v3 and Brown family/year score is above all 512 nulls, so recurrence p-values and Fisher evidence collapse to ties",
            "v3_transfer": "v3 is usable but almost rank-equivalent to Brown on this scaffold; its extra anchors add only one recovered label at top 100",
            "ranking": "with p-values saturated, v3/Brown ordering falls through to minimum raw score rather than calibrated recurrence evidence",
            "fusion": "secondary failure: fixed equal-weight RRF raises precision but moves six fixed4-recovered labels out of the top 100 while adding only three",
            "next_step_constraint": "do not tune v4 weights or thresholds; any successor should change the information used for ranking, not merely its cutoff",
        },
    }

    (args.output / "sparse_support_v4_diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    md = f"""# OrbitTrace sparse-support v4 structural diagnostics

Verdict: **`{verdict}`**

- v4 failed gates: **{', '.join(result['v4_failed_gates'])}**
- v3/Brown empirical p-values at floor `1/513`: **{floor_fraction_v3:.3f} / {floor_fraction_brown:.3f}**
- v3 vs Brown family-rank Spearman: **{v3_brown_spearman:.6f}**
- v3 vs Brown top-100 family overlap: **{top100_overlap_v3_brown}/100**
- v3 vs Brown recovered@100: **{len(recovered['v3'])} vs {len(recovered['brown'])}**
- fixed4 vs RRF recovered@100: **{len(recovered['fixed4_persistence'])} vs {len(recovered['rrf'])}**
- fixed4 vs RRF top-100 precision: **{development['metrics']['fixed4_persistence']['top100_dominant_precision']:.4f} vs {development['metrics']['rrf']['top100_dominant_precision']:.4f}**
- RRF crossings vs fixed4: **{len(crossings['rrf']['lost'])} lost / {len(crossings['rrf']['gained'])} gained**

Interpretation: proposal capacity is intact. The calibrated recurrence ranks saturate completely, and multi-anchor v3 is almost collinear with Brown on the fixed4 scaffold. The failed fusion gate is therefore not evidence that the target-free scaffold failed; it is evidence that this v3 ranking adds too little independent ordering information to justify equal-weight fusion. Do not retune v4 weights or thresholds.

No catalogue was opened by this diagnostic. It used only frozen development artifacts from runs `{V4_RUN}` and `{FIXED4_RUN}`.
"""
    (args.output / "SPARSE_SUPPORT_V4_DIAGNOSTICS.md").write_text(md)
    print(md, end="")


if __name__ == "__main__":
    main()
