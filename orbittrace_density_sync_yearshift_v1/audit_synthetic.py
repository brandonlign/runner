#!/usr/bin/env python3
from __future__ import annotations

import json
import math

import numpy as np

from yearshift import METHOD_ID, adjusted_score, compute_year_shift


def geo(rows):
    return np.asarray([row["x"] for row in rows], dtype=float)


def rows_same():
    out=[]
    base=[
        [1,0,0,1,0,0.5],
        [0.99,0.1,0.05,0.99,0.02,0.51],
        [0.98,-0.1,-0.05,0.99,-0.02,0.49],
        [0.97,0.15,0.04,0.98,0.01,0.50],
    ]
    for year in (2022,2023):
        for x in base:
            out.append({"year":year,"x":x})
    return out


def rows_shifted():
    out=[]
    for i in range(4):
        out.append({"year":2022,"x":[1,0,0,1,0,0.4+i*0.001]})
        out.append({"year":2023,"x":[0,1,1,0,0,0.8+i*0.001]})
    return out


def main():
    same=compute_year_shift(rows_same(),geo)
    shifted=compute_year_shift(rows_shifted(),geo)
    swapped=[dict(r,year=2023 if r["year"]==2022 else 2022) for r in rows_shifted()]
    swapped_stat=compute_year_shift(swapped,geo)
    perm=compute_year_shift(list(reversed(rows_shifted())),geo)
    segregated=compute_year_shift([{"year":2022,"x":[1,0,0,0,0,0]} for _ in range(10)],geo)
    tests={
        "method_id": METHOD_ID=="orbittrace_density_sync_yearshift_v1",
        "identical_annual_geometry_has_zero_shift": same.year_shift==0.0 and same.overlap==1.0,
        "shifted_geometry_penalized": shifted.year_shift>0.5 and shifted.overlap<0.5,
        "year_swap_invariant": math.isclose(shifted.year_shift,swapped_stat.year_shift,abs_tol=1e-12,rel_tol=0.0),
        "permutation_invariant": math.isclose(shifted.year_shift,perm.year_shift,abs_tol=1e-12,rel_tol=0.0),
        "missing_year_is_full_shift": segregated.year_shift==1.0 and segregated.overlap==0.0,
        "adjusted_score_identity_when_no_shift": adjusted_score(7.5,same)==7.5,
        "adjusted_score_decreases_under_shift": adjusted_score(7.5,shifted)<7.5,
        "raw_decomposition_valid": 0.0<=shifted.raw_r2<=1.0 and shifted.between_year_ss<=shifted.total_ss+1e-12,
    }
    passed=all(tests.values())
    print(json.dumps({"verdict":"PASS_DENSITY_SYNC_YEARSHIFT_V1_SYNTHETIC_AUDIT" if passed else "FAIL_DENSITY_SYNC_YEARSHIFT_V1_SYNTHETIC_AUDIT","tests":tests,"same":same.__dict__,"shifted":shifted.__dict__},indent=2,sort_keys=True))
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
