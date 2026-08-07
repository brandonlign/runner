# OrbitTrace top-four anchor pooling family — v6 development

## Preservation and scope

All prior OrbitTrace methods and outcomes remain immutable, including failed v1/v2/v4/v5, near-success v3, Brown-family wavelet, fixed4, the earlier dual-channel detector, Sugar, HDBSCAN, catalogue-scale work, and blind-recovery records.

v6 does not alter the underlying matched-filter geometry. Every candidate uses the exact frozen v3/Brown-family leave-one-out 4° angular probe, 10% test-speed probe, radius-4 dimension-3 Mexican-hat coefficients.

The only quantity under development is how the four strongest positive anchor coefficients are pooled into a continuous episode score.

## Scientific motivation

A real four-member stream should elevate several member-centered coefficients at once. Brown's maximum uses only the strongest anchor. v3's top-four L2 energy improved AUROC above Brown in both 2025 and 2023 without retuning, but did not fully match fixed4's four-member recall. Lower-order pooling gives relatively more weight to the secondary coherent anchors and is therefore a targeted, interpretable extension of the successful v3 mechanism.

## Frozen candidate family

Let `c1 >= c2 >= c3 >= c4 >= 0` be the four largest positive leave-one-out coefficients, zero-padded if fewer than four are positive.

The preregistered candidates are:

- `anchor_l1_v6`: `c1 + c2 + c3 + c4`;
- `anchor_l1p5_v6`: `(sum(ci^1.5))^(1/1.5)`;
- frozen v3 reference `anchor_l2_v3`: `(sum(ci^2))^(1/2)`;
- `anchor_l4_v6`: `(sum(ci^4))^(1/4)`;
- `anchor_geomean_v6`: `(c1*c2*c3*c4)^(1/4)` if all four are positive, else 0;
- `anchor_min4_v6`: `c4`.

Brown's single maximum remains the literature comparator, not a selectable v6 candidate.

All candidate scores are computed from the same coefficient vector in one pass. There is no candidate-specific physical scale, threshold, weighting parameter, label input, or target-specific rule.

Each candidate is calibrated independently by the existing frozen bin-wise empirical calibration.

## Development panel

SonotaCo 2025 and SonotaCo 2023 are both fully exposed development corpora. Candidate selection is based only on these two years.

No OrbitTrace coordinate, activity interval, member identity, blind-recovery output, or target-specific exception may enter v6.

## Feasibility gates — each year independently

A candidate is feasible only if, in **both** 2025 and 2023:

- weak-stream AUROC strictly exceeds Brown-family wavelet;
- alpha=.05 k=4 recall is at least fixed4 alpha=.05 recall;
- alpha=.05 k=6/8/12 recall is no more than 0.03 below Brown-family wavelet at each k;
- pooled alpha=.05 FPR <= 0.055;
- worst reporting-sector alpha=.05 FPR <= 0.08;
- every upstream source/parser/comparator reproduction gate passes.

## Frozen selector

If no candidate is feasible, v6 fails.

If one or more candidates are feasible, select deterministically by:

1. largest **minimum annual AUROC margin over Brown** across 2025 and 2023;
2. largest mean annual AUROC margin over Brown;
3. largest minimum annual k=4 recall margin over fixed4;
4. largest mean annual k=4 recall margin over fixed4;
5. fixed method order: `anchor_l1_v6`, `anchor_l1p5_v6`, `anchor_l2_v3`, `anchor_l4_v6`, `anchor_geomean_v6`, `anchor_min4_v6`.

The complete candidate table is preserved regardless of outcome.

## Prospective boundary

A v6 development winner is not validated. The exact winning score, source, empirical calibration, and reporting alpha=.05 must be frozen before any prospective corpus is scored.

The preferred prospective SonotaCo year is **2016**, selected before any v6 access to that year's archive, labels, scores, or episode endpoints. Repository-history inspection found no OrbitTrace SonotaCo-2016 development branch. If a later transport-only audit shows the 2016 archive is unavailable or cannot support the frozen benchmark without scientific rule changes, that is an input-eligibility failure, not permission to inspect its scientific endpoints or silently substitute another year.
