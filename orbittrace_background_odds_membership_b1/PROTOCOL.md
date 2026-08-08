# OrbitTrace B1 — cross-year background-odds membership

## Status

B1 is a separately named target-free successor architecture, frozen before the scientific verdict of the repaired v3-primary catalogue run `31270206927` / job `93134746182` is known. B1 is dormant unless that challenger produces a scientific failure (or a later frozen comparison/generalization gate establishes a need for a successor). A technical failure of that run does not authorize B1; the audited checkpoint fallback in PR #499 remains the required path.

B1 does **not** change the promoted v8 discovery core. The exact 226 v8 recurrent families, original seed membership, pooled-year centroids, scores, multiplicity ranking, and all discovery-stage outputs remain immutable. B1 changes only final non-recursive membership assignment.

## Why this is a genuinely new architecture

Prior target-excluded membership experiments establish complementary facts without authorizing parameter tuning:

- broad cross-year seed support greatly increases membership F1 but overexpands;
- family-density normalization reduces contamination but still loses qualified matches;
- affine solar-longitude trajectory modeling improves broad annual coverage but also overexpands;
- joint density+trajectory conformal membership still treats only seed conformity, not explicit competition with the local field;
- R1 orbital filtering again showed that much higher membership F1 is possible, but hard acceptance around an orbital medoid still lost qualified matches.

B1 therefore changes the statistical question. It does not ask only whether an event looks sufficiently similar to a family seed set. It asks whether the event is **more probable under a transferred stream model than under the competing local field**, with an explicit conservative prior derived from the observed seed prevalence.

## Frozen target firewall

- Development years are GMN 2022 and 2023 only.
- Solar longitude 20°–55° is removed by the inherited geometry parser before candidate/family construction or labels.
- Raw orbital parsing reads stable event ID and solar longitude first. Orbital fields `q/e/i/peri/node` are decoded only for IDs already present in the exact target-excluded scan universe and only after asserting the raw solar longitude is outside 20°–55°.
- The raw orbit parser never reads the shower-label column.
- No OrbitTrace coordinates, members, identity, prior target rank/family, target-region event, target-containing result, Stage A output, or Stage B output may enter B1 development.
- Expanded membership is hashed before any hidden shower label is evaluated.

## Frozen inputs and ancestry

Discovery core and evaluator are inherited byte-for-byte from the exact v8/v1 development chain. B1 reuses:

- exact v8 226-family discovery universe and multiplicity order;
- exact v8 baseline: 95 qualified matches, recovery@100 58, multiplicity MRR 0.045531138942766655, macro F1 0.1736657194465356, top-100 dominant precision 0.6884631112636006;
- v3 exact geometry and second-neighbor primitive;
- v4 order-1 affine radiant/speed trajectory versus solar longitude;
- inherited activity padding ±6°;
- inherited density hard ceiling 1.5;
- inherited trajectory-residual hard ceiling 1.5;
- exact published Southworth–Hawkins `D_SH` implementation already frozen in the literature-comparator module.

The inherited ceilings are candidate-support bounds only. They are not retuned and they do not decide B1 membership by themselves.

## One B1 membership rule

For target year `y`, each family is modeled using **only original v8 seeds from the other year** `s`.

1. Keep only source seeds with valid target-excluded raw orbital records. At least four are required.
2. Build three source-stream leave-one-out features for every source seed:
   - second-nearest exact v8 geometry distance `d2`;
   - v4 affine-trajectory residual `rT`;
   - median exact `D_SH` to all other source seeds `dO`.
3. Transform the feature vector deterministically as `log1p([d2, rT, dO])`.
4. Fit a 3-D Gaussian stream density with sklearn Ledoit–Wolf covariance. There is no covariance/ridge/shrinkage search.
5. Define the source-year local field as non-family events inside the inherited source activity arc that also satisfy `d2 <= 1.5` and `rT <= 1.5` and have valid orbits. Other v8 families are deliberately left in this field so competing streams are represented as background rather than silently removed.
6. Compute the same three features for that source field and fit one 3-D Ledoit–Wolf Gaussian background density.
7. Set prior odds to `N_original_orbit_valid_source_seeds / N_screened_source_background`. Because the v8 core is incomplete, this observed-seed prevalence is intentionally conservative; no class-prior estimator or prevalence multiplier is fitted.
8. For each target-year non-seed event in the transferred activity arc satisfying the same inherited support ceilings and with a valid orbit, compute the transferred log posterior odds:

   `log prior odds + log p_stream(x) - log p_background(x)`.

9. Add the event only when the log posterior odds are strictly `> 0`. Zero is the parameter-free MAP decision boundary; there is no probability/odds threshold search.
10. If multiple families have positive odds for the same event, assign it once by: larger log posterior odds; then smaller orbital median; then smaller `d2`; then stable family ID.
11. Original seeds have absolute priority. Added events never become training/support points and never alter components, family topology, scores, centroids, or ranking.

There is exactly one B1 variant. No feature subset, weight, posterior threshold, prior multiplier, covariance model, orbit threshold, trajectory order, activity padding, ceiling, recursion, or reranking variant is authorized.

## Development gates

B1 uses the exact already-frozen v1–v5 scientific gate set without relaxation. Every integrity gate and every scientific gate must pass. In particular, relative to exact v8 it must retain at least 95 qualified matches, retain recovery@100 of at least 58, keep top-100 dominant precision at least 0.65, improve macro F1 by at least +0.05, achieve the existing all-shower annual mean-F1 +0.10 gate in both years, avoid the existing sparse 4–9 material-regression gate, and satisfy the existing moderate/large-shower material-gain gate in both years.

A scientific failure is `FAIL_BACKGROUND_ODDS_MEMBERSHIP_B1_DEVELOPMENT` and permanently rejects this exact rule. The result cannot be used to tune B1.

## Pass boundary

A development pass is not a literature-superiority claim and is not external validation. It freezes B1 and authorizes only:

1. a matched exact-row comparison against the already-frozen Sugar/HDBSCAN interfaces under frozen superiority criteria; and
2. a separately frozen prospective external/generalization test without retuning.

Only after those gates pass may a final target-containing OrbitTrace search protocol be frozen. B1 development itself never opens the 20°–55° target interval.
