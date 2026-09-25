# OrbitTrace v17 — broad URC with density-stable hard ranking and fixed membership expansion

## Why this successor exists

The immutable v15 SonotaCo result failed. v16 then proved on the already-exposed SonotaCo panels that full-membership estimation was a major missing layer, improving all four matched panels, but v16 remained constrained to only 19–22 recurrent hard families and still lost to Sugar/HDBSCAN.

Repository history shows the strongest prior candidate architecture, M0/#839, was never scientifically defeated on SonotaCo. Its final run stopped pretruth because the old hard-family multiplicity feature required a fixed 128-event local episode while the matched SonotaCo windows contained only 58/49 events. v13–v15 later solved this density/applicability defect with the fixed multiscale adaptive rule, but only on the narrow hard-family universe.

v17 tests the direct architectural combination implied by those two independent failures. It is a separately named successor; frozen v15/v16 and frozen #839 are not rewritten.

## Frozen architecture

1. Generate the exact pair-portable hard-v8/P19/P20 proposal universe from #862.
2. Do **not** call the density-brittle fixed-128 hard multiplicity stage.
3. Rank the hard-v8 families with the already-promoted v15 adaptive `(128,96,64)` median-rank consensus, using `K=min(cap,N_local)` and the unchanged Brown-equivalent multiplicity score.
4. Feed that hard order into the already-frozen #860 year-portable application of the exact #839/#853 ExtraTrees quality/diversity ranker. The learned model, 34 features, diversity lambda `0.8`, diversity scale `1.0`, and tie rule remain fixed. Application uses no SonotaCo truth.
5. Freeze the full ranked union before truth.
6. Membership for ranks 1–100 only is expanded with the exact pre-SonotaCo joint density+trajectory conformal mathematics inherited by v16/#461: alpha `0.05`, k=2, affine order 1, +/-6 degree activity padding, density/residual ceilings 1.5, equal Fisher weights, empirical joint recalibration, no recursive support. Families lacking four source-year seeds remain unchanged rather than weakening the estimator's source-support requirement.
7. New members never change family existence or rank. Original members are never removed. Additions are assigned exclusively by largest joint p, then smaller Fisher nonconformity, then rank/family ID; pre-existing seed overlap is preserved.

Expanding only the first 100 is a fixed catalogue-definition rule, not comparator-budget tuning; all frozen matched-literature budgets are <=46.

## Development role

SonotaCo 2013/2014 is already exposed and is **development-only** for v17. Candidate outputs are still frozen before the already-exposed truth artifact is loaded so the implementation boundary remains auditable, but this is not prospective external validation.

The exact #854 one-to-one equal-budget F1 semantics are reused unchanged. Report all four Sugar/HDBSCAN year panels against both v15 and v16 and against the literature comparator.

No parameter/model/radius/threshold search is allowed from the v17 result. If v17 fails, preserve it and diagnose the remaining bottleneck rather than tuning the inherited constants.

## Firewalls

No MAARSY scientific values, DMS scientific values, OrbitTrace target information, or target-region event access. The 20°–55° target firewall remains closed. Original OrbitTrace discovery provenance remains historical blind HDBSCAN.
