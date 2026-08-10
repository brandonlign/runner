#!/usr/bin/env python3
"""Apply the preregistered v13 cardinality-stress gates without model selection."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

CAPS = (32, 64, 96, 128)
LOWER_CAPS = (96, 64, 32)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load(path: Path, cap: int) -> dict[str, Any]:
    value = json.loads(path.read_text())
    require(int(value["stress_cap"]) == cap, f"wrong cap payload for {cap}")
    require(value["sonotaco_2013_2014_access"] is False, "SonotaCo accessed during v13 development")
    require(value["maarsy_access"] is False, "MAARSY accessed during v13 development")
    require(value["target_information_access"] is False, "target information accessed during v13 development")
    require(value["truth_labels_used_only_after_ranking"] is True, "labels entered before ranking")
    require(float(value["max_brown_equivalence_difference"]) <= 1e-10, f"Brown equivalence failed at cap {cap}")
    checks = value["synthetic_cardinality_checks"]
    require(sorted(int(x) for x in checks) == [4, 8, 16, 32, 64, 96, 128], "synthetic size universe changed")
    require(all(bool(row["permutation_invariant"]) for row in checks.values()), "synthetic permutation check failed")
    return value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for cap in CAPS:
        p.add_argument(f"--cap-{cap}", dest=f"cap_{cap}", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    runs = {cap: load(getattr(a, f"cap_{cap}"), cap) for cap in CAPS}
    reference = runs[128]

    universes = {runs[cap]["family_universe_sha256"] for cap in CAPS}
    family_counts = {int(runs[cap]["family_count"]) for cap in CAPS}
    integrity = {
        "same_family_universe_all_caps": len(universes) == 1 and len(family_counts) == 1,
        "all_brown_equivalence_within_1e_10": all(float(runs[c]["max_brown_equivalence_difference"]) <= 1e-10 for c in CAPS),
        "all_synthetic_checks_present": all(len(runs[c]["synthetic_cardinality_checks"]) == 7 for c in CAPS),
        "no_external_or_target_access": all(
            runs[c]["sonotaco_2013_2014_access"] is False
            and runs[c]["maarsy_access"] is False
            and runs[c]["target_information_access"] is False
            for c in CAPS
        ),
        "labels_only_after_ranking": all(runs[c]["truth_labels_used_only_after_ranking"] is True for c in CAPS),
    }

    refm = reference["multiplicity_metrics"]
    ref_recovery = int(refm["recovered_at_100"])
    ref_mrr = float(refm["mrr"])
    ref_precision = float(refm["top100_dominant_precision"])
    ref_qualified = int(refm["qualified_matches"])
    required_recovery = int(math.ceil(0.90 * ref_recovery))

    robustness: dict[str, Any] = {}
    for cap in LOWER_CAPS:
        m = runs[cap]["multiplicity_metrics"]
        gates = {
            "recovered_at_100_at_least_90pct_reference": int(m["recovered_at_100"]) >= required_recovery,
            "mrr_at_least_90pct_reference": float(m["mrr"]) + 1e-15 >= 0.90 * ref_mrr,
            "top100_precision_at_least_050": float(m["top100_dominant_precision"]) >= 0.50,
            "top100_precision_loss_at_most_005": float(m["top100_dominant_precision"]) + 1e-15 >= ref_precision - 0.05,
            "qualified_count_unchanged": int(m["qualified_matches"]) == ref_qualified,
        }
        robustness[str(cap)] = {
            "metrics": m,
            "gates": gates,
            "all_pass": all(gates.values()),
        }

    all_pass = all(integrity.values()) and all(row["all_pass"] for row in robustness.values())
    verdict = (
        "PASS_DENSITY_CAPPED_MULTIPLICITY_V13_TARGET_EXCLUDED_DEVELOPMENT"
        if all_pass
        else "FAIL_DENSITY_CAPPED_MULTIPLICITY_V13_TARGET_EXCLUDED_DEVELOPMENT"
    )
    result = {
        "verdict": verdict,
        "adaptive_rule": "K=min(128,N_local); fail only if N_local<4",
        "stress_caps": list(CAPS),
        "reference_cap": 128,
        "reference_metrics": refm,
        "required_recovery_at_100": required_recovery,
        "family_count": int(reference["family_count"]),
        "family_universe_sha256": reference["family_universe_sha256"],
        "reference_order_sha256": reference["multiplicity_order_sha256"],
        "integrity_gates": integrity,
        "robustness": robustness,
        "no_best_cap_selection": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
        "claim_boundary": (
            "Target-excluded GMN development only. A pass freezes the adaptive-cardinality hypothesis; "
            "it does not authorize SonotaCo reuse, MAARSY access, OrbitTrace target access, or an external claim."
        ),
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
