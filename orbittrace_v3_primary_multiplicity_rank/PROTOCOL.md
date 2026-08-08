# OrbitTrace v3-primary multiplicity-ranked catalogue — pre-result freeze

## Status

This is a **pre-result ranking-layer challenger** frozen while the authoritative repaired v3-primary catalogue development run `31270206927` is still in progress. Its definition may not change in response to that run.

It accesses no OrbitTrace target information and does not restore the excluded solar-longitude interval. The historical target-region result is not an input.

## Scientific motivation

Two already-frozen target-excluded results motivate exactly one architectural question:

1. The v3 factorization diagnostic found that the dimensionless multiplicity term
   `M = (v3_energy / Brown_peak)^2`
   retained independent ranking signal: top-100 known-shower recovery was 60 for multiplicity, 55 for total v3, and 54 for Brown on the exposed recurrent-family diagnostic.
2. Pooled-year-centroid v8 independently established a target-free family-level multiplicity ranking based on pooled same-year family centroids.

The current v3-primary catalogue changes proposal/detection/component construction but ranks primary recurrent families mainly by recurrent v3 significance. This challenger asks whether the established multiplicity statistic is a better **family ranking layer** on the new v3-primary family graph. No new score, weight, threshold, radius, fusion, or membership rule is introduced.

## Immutable upstream architecture

Use the exact repaired v3-primary catalogue architecture represented by repaired scientific-source SHA-256:

`257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`

The repair is exactly the source-audited two-line component-construction completion from PR #490/#491; deleting those two assignments reconstructs frozen source SHA-256:

`a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`

The following remain byte/semantic-identical to the repaired v3-primary method:

- GMN 2022/2023 development years;
- solar longitude 20°–55° excluded before label normalization/storage/candidate generation;
- 10° windows stepped by 5°;
- 512 primary proposals per window;
- exact 128-event v3 rescoring;
- primary detection cutoff `p_v3 <= 0.05`;
- strongest positive-v3 coefficient as representative anchor;
- `r^2 < 3` positive-lobe primary membership;
- v3-only component construction and recurrence graph;
- component gates, centroid link radius, family construction, event membership, and family IDs;
- fixed4 minimum-p rescue queue as a separate output only.

Fixed4 rescue evidence must never alter a v3 primary family score, member set, component graph, recurrence graph, multiplicity score, or rank.

## Sole change: family ranking

After all v3 primary recurrent families are frozen, and before any known-shower label is read, compute an independent multiplicity ranking using the exact pooled-year-centroid v8 family-scoring semantics.

For each primary family and each development year represented in that family:

1. Union the unique event IDs from **all v3 primary components of that family in that year**.
2. Compute the family-year pooled centroid using the exact v8 statistic:
   - solar longitude: circular mean;
   - Sun-centered ecliptic longitude: circular mean;
   - ecliptic latitude: median;
   - geocentric speed: median.
3. Build the exact v8 128-event local episode from the same target-excluded year scan universe using the frozen Brown-family geometry and deterministic nearest-neighbor/tie semantics.
4. Compute the exact frozen multi-anchor-v3 energy and exact Brown peak on that same episode.
5. Compute `M_y = (v3_energy_y / Brown_peak_y)^2`.

Rank primary families by the exact v8 ordering:

1. descending worst-year multiplicity `min_y(M_y)`;
2. descending geometric-mean multiplicity across represented years;
3. stable family ID.

No empirical p-value, fixed4 score, event count, component count, Fisher evidence, support count, or other term may enter this challenger ranking.

The exact reference implementation for the pooled-centroid and ranking semantics is `orbittrace_pooled_year_centroid_v8/run_development.py` at Git blob `f248df78e1258b132b41aecca6a985a5eb782654`, together with its frozen imported multiplicity scorer. A later execution wrapper may adapt interfaces only if source-only equivalence tests prove the resulting pooled centroids, per-year v3/Brown scores, multiplicities, and order are identical on synthetic fixtures.

## Development adjudication

The current repaired v3-primary development result is an **unknown comparator at freeze time**. It may not change this method.

If the repaired v3-primary run fails any upstream structural/integrity gate that this challenger shares (for example insufficient recurrent primary families or calibration support), this challenger is also a no-go without a rerun.

Otherwise, evaluate both rankings on the exact same frozen v3-primary family objects and hidden development truth. Family membership is identical, so qualified-match count must be identical by construction.

Select the multiplicity-ranked challenger for downstream testing only if all of the following hold:

- primary family IDs, components, event memberships, and rescue queue are exactly identical to the repaired v3-primary output;
- qualified known-shower matches are exactly identical to the repaired v3-primary output;
- top-100 dominant precision is at least `0.65`;
- top-100 recovery is **strictly greater** than the repaired v3-primary ranking;
- MRR is not lower than the repaired v3-primary ranking.

Otherwise retain the original repaired v3-primary ranking. Ties retain the original method. There is no threshold/weight search and no third ranking candidate.

This rule deliberately demands an unambiguous top-100 recovery gain rather than selecting on tiny rank fluctuations.

## Downstream claim boundary

A development selection is not literature superiority and not external validation. The selected ranking must still face the already-frozen pairwise exact-row Sugar/HDBSCAN superiority protocol and a no-retuning external/held-out transfer before any final target-containing search.

No OrbitTrace target-containing scan is authorized by this freeze.
