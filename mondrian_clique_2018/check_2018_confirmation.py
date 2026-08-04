#!/usr/bin/env python3
"""Print and enforce every frozen 2018 scientific continuation gate."""

from __future__ import annotations

import json
from pathlib import Path

RESULT = Path("output/mondrian_clique_development_2018.json")


def main() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if int(result["counts"]["minimum_supported_bins"]) != 20:
        raise SystemExit(
            f"unexpected complete-year support rule: "
            f"{result['counts']['minimum_supported_bins']}"
        )
    print(
        json.dumps(
            {
                "counts": result["counts"],
                "candidate_weak_auc": result["candidate_weak_auc"],
                "comparators": result["fixed_comparator_weak_auc"],
                "false_positive": result["false_positive"],
                "worst_reporting_sector_0.05": result[
                    "worst_reporting_sector_0.05"
                ],
                "recall": result["recall"],
                "fold_results": result["fold_results"],
                "gates": result["gates"],
                "verdict": result["verdict"],
            },
            indent=2,
        )
    )
    if not all(result["gates"].values()):
        raise SystemExit("frozen fresh-2018 confirmation gate failed")


if __name__ == "__main__":
    main()
