#!/usr/bin/env python3
from __future__ import annotations

import json
import math

from exposure_lr import exposure_weight


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    totals = (40, 60)
    exact = exposure_weight((4, 6), totals)
    mild = exposure_weight((5, 5), totals)
    severe = exposure_weight((9, 1), totals)
    one_year = exposure_weight((10, 0), totals)

    req(abs(exact.global_probability_year0 - 0.4) < 1e-15, "global exposure probability changed")
    req(abs(exact.node_probability_year0 - 0.4) < 1e-15, "exact node proportion changed")
    req(exact.kl_divergence == 0.0, "exact exposure match must have zero KL")
    req(exact.log_likelihood_ratio == 0.0, "exact exposure match must have log LR zero")
    req(exact.exposure_weight == 1.0, "exact exposure match must have unit weight")
    req(1.0 > mild.exposure_weight > severe.exposure_weight > one_year.exposure_weight >= 0.0,
        "exposure incompatibility ordering changed")

    # Swap year names/counts/totals together: evidence must be invariant.
    swapped = exposure_weight((1, 9), (60, 40))
    req(abs(swapped.kl_divergence - severe.kl_divergence) < 1e-15, "year swap changed KL")
    req(abs(swapped.log_likelihood_ratio - severe.log_likelihood_ratio) < 1e-14, "year swap changed log LR")
    req(abs(swapped.exposure_weight - severe.exposure_weight) < 1e-15, "year swap changed weight")

    # For fixed proportions, evidence strengthens with sample size.
    small = exposure_weight((9, 1), totals)
    large = exposure_weight((90, 10), totals)
    req(large.exposure_weight < small.exposure_weight, "likelihood evidence should strengthen with sample size")
    req(abs(large.log_likelihood_ratio - 10.0 * small.log_likelihood_ratio) < 1e-12,
        "fixed-proportion log likelihood ratio should scale with n")

    req(all(math.isfinite(x.exposure_weight) for x in (exact, mild, severe, one_year, large)),
        "non-finite exposure weight")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EXPOSURE_LR_V1_SYNTHETIC_AUDIT",
        "exact_match": exact.__dict__,
        "mild_mismatch": mild.__dict__,
        "severe_mismatch": severe.__dict__,
        "one_year": one_year.__dict__,
        "assertions": {
            "unit_weight_at_exposure_match": True,
            "monotone_incompatibility_penalty": True,
            "year_swap_invariance": True,
            "sample_size_likelihood_accumulation": True,
            "finite_range": True,
        },
        "scientific_data_access": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
