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
from scipy.stats import spearmanr

EXPECTED_V4_SHA256 = {
    "sparse_support_v4_development.json": "9a60fd97eacb33d4fa5d29344eebe3ba784c38423763d2f2b8e5b9a7bedcbd7c",
    "sparse_support_v4_rankings.json": "b0f1ea824b28e6e4f6f871360ddc25aead6202668ee2d7ee026adb65eb851c13",
    "sparse_support_v4_family_scores.json.gz": "852f3b4c7e5b617b98b421f172cd99fbe14f91ca7f0f9dff8ad08a8e0623dbae",
}
EXPECTED_FIXED4_SHA256 = "80568774b1e2fd9a0723e66c02b432e8437d069ccd16abba09ef1c22815f0f12"
EXPECTED_FAMILIES = 197
EXPECTED_QUALIFIED = 90
RRF_K = 60


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


def evaluate(order: list[str], per_label: list[dict[str, Any]]) -> dict[str, Any]:
    ranks = {fid: rank for rank, fid in enumerate(order, start=1)}
    qualified = [row for row in per_label if row.get("qualified") and row.get("family_id")]
    require(len(qualified) == EXPECTED_QUALIFIED, "qualified-label count changed")
    label_rows = []
    for row in qualified:
        fid = str(row["family_id"])
        require(fid in ranks, f"missing qualified family {fid}")
        label_rows.append((str(row["label"]), fid, ranks[fid]))
    rank_values = np.asarray([rank for _, _, rank in label_rows], dtype=float)
    recovered = sorted(label for label, _, rank in label_rows if rank <= 100)
    return {
        "recovered_at_100": len(recovered),
        "recovered_labels_at_100": recovered,
        "mrr": float(np.mean(1.0 / rank_values)),
        "median_rank": float(np.median(rank_values)),
    }


def rrf_order(a: list[str], b: list[str]) -> list[str]:
    require(set(a) == set(b) and len(a) == len(b), "RRF universe mismatch")
    ra = {fid: i for i, fid in enumerate(a, start=1)}
    rb = {fid: i for i, fid in enumerate(b, start=1)}
    score = {fid: 1.0 / (RRF_K + ra[fid]) + 1.0 / (RRF_K + rb[fid]) for fid in a}
    return sorted(score, key=lambda fid: (-score[fid], fid))


def rank_spearman(a: list[str], b: list[str]) -> float:
    require(set(a) == set(b), "correlation universe mismatch")
    universe = sorted(a)
    ra = {fid: i for i, fid in enumerate(a, start=1)}
    rb = {fid: i for i, fid in enumerate(b, start=1)}
    return float(spearmanr([ra[x] for x in universe], [rb[x] for x in universe]).statistic)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    paths = {name: args.v4_dir / name for name in EXPECTED_V4_SHA256}
    for name, expected in EXPECTED_V4_SHA256.items():
        require(paths[name].is_file(), f"missing {name}")
        require(sha256(paths[name]) == expected, f"digest mismatch: {name}")
    require(args.fixed4_json.is_file(), "missing fixed4 artifact")
    require(sha256(args.fixed4_json) == EXPECTED_FIXED4_SHA256, "fixed4 digest mismatch")

    development = json.loads(paths["sparse_support_v4_development.json"].read_text())
    rankings = json.loads(paths["sparse_support_v4_rankings.json"].read_text())
    with gzip.open(paths["sparse_support_v4_family_scores.json.gz"], "rt") as f:
        scores = json.load(f)
    fixed4 = json.loads(args.fixed4_json.read_text())

    require(development["verdict"] == "FAIL_SPARSE_SUPPORT_V4_DEVELOPMENT", "unexpected v4 verdict")
    require(len(scores) == EXPECTED_FAMILIES, "family count changed")
    fixed_metrics = fixed4["panel_results"]["development"]["evaluation"]["metrics"]["persistence"]
    per_label = fixed_metrics["per_label"]
    require(fixed_metrics["qualified_matches"] == EXPECTED_QUALIFIED, "fixed4 qualified count changed")

    orders = {
        "v3": [str(x) for x in rankings["v3"]],
        "brown": [str(x) for x in rankings["brown"]],
        "fixed4": [str(x) for x in rankings["fixed4_persistence"]],
    }
    universe = set(orders["fixed4"])
    require(len(universe) == EXPECTED_FAMILIES, "fixed4 universe changed")
    for name, order in orders.items():
        require(len(order) == EXPECTED_FAMILIES and set(order) == universe, f"{name} universe changed")

    factor_rows = []
    all_multiplicity = []
    for row in scores:
        per_year = {}
        values = []
        for year in ("2022", "2023"):
            v3 = float(row["per_year"][year]["v3_score"])
            brown = float(row["per_year"][year]["brown_score"])
            require(math.isfinite(v3) and math.isfinite(brown) and brown > 0.0, "invalid factorization score")
            multiplicity = (v3 / brown) ** 2
            require(1.0 - 1e-10 <= multiplicity <= 4.0 + 1e-10, "multiplicity outside exact top-four bounds")
            values.append(multiplicity)
            all_multiplicity.append(multiplicity)
            per_year[year] = {"v3": v3, "brown": brown, "multiplicity": multiplicity}
        factor_rows.append({
            "family_id": str(row["family_id"]),
            "per_year": per_year,
            "worst_year_multiplicity": min(values),
            "geometric_mean_multiplicity": math.sqrt(values[0] * values[1]),
        })

    multiplicity_order = [
        row["family_id"]
        for row in sorted(
            factor_rows,
            key=lambda row: (
                -float(row["worst_year_multiplicity"]),
                -float(row["geometric_mean_multiplicity"]),
                str(row["family_id"]),
            ),
        )
    ]
    require(len(multiplicity_order) == EXPECTED_FAMILIES and set(multiplicity_order) == universe, "multiplicity universe changed")
    fusion_order = rrf_order(orders["fixed4"], multiplicity_order)

    evaluations = {
        "brown": evaluate(orders["brown"], per_label),
        "v3": evaluate(orders["v3"], per_label),
        "fixed4": evaluate(orders["fixed4"], per_label),
        "multiplicity": evaluate(multiplicity_order, per_label),
        "fixed4_multiplicity_rrf": evaluate(fusion_order, per_label),
    }

    overlaps = {
        "multiplicity_brown_top100": len(set(multiplicity_order[:100]) & set(orders["brown"][:100])),
        "multiplicity_v3_top100": len(set(multiplicity_order[:100]) & set(orders["v3"][:100])),
        "multiplicity_fixed4_top100": len(set(multiplicity_order[:100]) & set(orders["fixed4"][:100])),
        "fusion_fixed4_top100": len(set(fusion_order[:100]) & set(orders["fixed4"][:100])),
    }
    correlations = {
        "multiplicity_brown_spearman": rank_spearman(multiplicity_order, orders["brown"]),
        "multiplicity_v3_spearman": rank_spearman(multiplicity_order, orders["v3"]),
        "multiplicity_fixed4_spearman": rank_spearman(multiplicity_order, orders["fixed4"]),
    }

    no_independent_support = bool(
        evaluations["multiplicity"]["recovered_at_100"] <= evaluations["brown"]["recovered_at_100"]
        and evaluations["fixed4_multiplicity_rrf"]["recovered_at_100"] < evaluations["fixed4"]["recovered_at_100"]
    )
    verdict = (
        "NO_SUPPORT_FOR_V3_NON_BROWN_TERM_AS_INDEPENDENT_RANKING_SIGNAL"
        if no_independent_support
        else "V3_NON_BROWN_TERM_RETAINS_EXPLORATORY_RANKING_SIGNAL"
    )

    m = np.asarray(all_multiplicity, dtype=float)
    result = {
        "verdict": verdict,
        "blindness": {
            "artifact_only": True,
            "catalogue_access": False,
            "later_year_access": False,
            "orbittrace_target_access": False,
        },
        "factorization": "multiplicity=(v3_energy/brown_peak)^2",
        "multiplicity_distribution": {
            "min": float(np.min(m)),
            "p05": float(np.quantile(m, 0.05)),
            "median": float(np.median(m)),
            "p95": float(np.quantile(m, 0.95)),
            "max": float(np.max(m)),
        },
        "evaluations": evaluations,
        "overlaps": overlaps,
        "correlations": correlations,
        "interpretation_rule_passed": no_independent_support,
        "rankings": {
            "multiplicity": multiplicity_order,
            "fixed4_multiplicity_rrf": fusion_order,
        },
    }
    (args.output / "v3_factorization_diagnostic.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    md = f"""# OrbitTrace v3 factorization diagnostic

Verdict: **`{verdict}`**

- multiplicity recovered@100: **{evaluations['multiplicity']['recovered_at_100']}**
- Brown recovered@100: **{evaluations['brown']['recovered_at_100']}**
- v3 recovered@100: **{evaluations['v3']['recovered_at_100']}**
- fixed4 recovered@100: **{evaluations['fixed4']['recovered_at_100']}**
- fixed4 + multiplicity RRF recovered@100: **{evaluations['fixed4_multiplicity_rrf']['recovered_at_100']}**
- multiplicity vs Brown rank Spearman: **{correlations['multiplicity_brown_spearman']:.6f}**
- multiplicity vs fixed4 rank Spearman: **{correlations['multiplicity_fixed4_spearman']:.6f}**
- multiplicity median / 5-95% range: **{float(np.median(m)):.4f} / {float(np.quantile(m, 0.05)):.4f}-{float(np.quantile(m, 0.95)):.4f}**

This run factors the already-frozen v3 score into Brown amplitude and its unique dimensionless top-four multiplicity term. It performs no threshold or weight search and opens no catalogue.
"""
    (args.output / "V3_FACTORIZATION_DIAGNOSTIC.md").write_text(md)
    print(md, end="")


if __name__ == "__main__":
    main()
