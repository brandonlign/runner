#!/usr/bin/env python3
from __future__ import annotations

import json
import math

from rate_balance import EXPOSURES, METHOD_ID, adjusted_score, compute_rate_balance


def rows(n22: int, n23: int):
    return ([{"year": 2022}] * n22) + ([{"year": 2023}] * n23)


def main() -> int:
    # Exact equal exposure-corrected rates: choose counts proportional to the
    # fixed catalogue exposures.
    equal = compute_rate_balance(rows(EXPOSURES[2022], EXPOSURES[2023]))
    one_sided = compute_rate_balance(rows(20, 0))
    # Equal raw counts are not equal rates because 2023 has more exposure.
    raw_equal = compute_rate_balance(rows(100, 100))
    # A smaller 2022 count can still have the same rate as a larger 2023 count.
    scale = 1000
    n22 = round(EXPOSURES[2022] / scale)
    n23 = round(EXPOSURES[2023] / scale)
    approx_equal = compute_rate_balance(rows(n22, n23))

    tests = {
        "method_id": METHOD_ID == "orbittrace_density_sync_rate_balance_v1",
        "exposures_frozen": EXPOSURES == {2022: 315024, 2023: 423658},
        "exact_equal_rates_balance_one": equal.balance == 1.0,
        "one_sided_support_balance_zero": one_sided.balance == 0.0,
        "raw_equal_counts_corrected_for_exposure": raw_equal.balance < 1.0,
        "proportional_counts_nearly_balanced": approx_equal.balance > 0.998,
        "balance_symmetric_formula": math.isclose(raw_equal.balance, 2 * min(raw_equal.rate_2022, raw_equal.rate_2023) / (raw_equal.rate_2022 + raw_equal.rate_2023), rel_tol=0.0, abs_tol=1e-15),
        "score_identity_at_balance_one": adjusted_score(3.5, equal) == 3.5,
        "score_zero_for_one_sided": adjusted_score(3.5, one_sided) == 0.0,
    }
    passed = all(tests.values())
    print(json.dumps({
        "verdict": "PASS_DENSITY_SYNC_RATE_BALANCE_V1_SYNTHETIC_AUDIT" if passed else "FAIL_DENSITY_SYNC_RATE_BALANCE_V1_SYNTHETIC_AUDIT",
        "tests": tests,
        "equal": equal.__dict__,
        "raw_equal": raw_equal.__dict__,
        "approx_equal": approx_equal.__dict__,
    }, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
