# OrbitTrace density-synchronous recurrent-EOM HDBSCAN v1

## Status

**PRE-IMPLEMENTATION / PRE-OUTCOME SCIENTIFIC FREEZE.**

This protocol defines one successor to the promoted recurrent-EOM HDBSCAN v1 method before implementation and before any scientific outcome for this successor. It does not authorize SonotaCo, EFN, ASFN, AMOS, MAARSY, DMS, or protected-target access.

The authoritative parent is recurrent-EOM HDBSCAN v1 at commit `e3ad80dd4d685b32917af9e2e6d76cb2b76857d4`:

- parent recurrent-EOM source blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- parent GMN runner blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding parent GMN run: `31827903547`;
- binding parent artifact: `9229646556`;
- binding parent artifact digest: `sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6d`.

## Scientific motivation

The promoted parent leaves the pooled GEO6 HDBSCAN hierarchy unchanged and replaces ordinary HDBSCAN EOM stability by a two-year recurrent objective. For cluster node C it computes annual, accessible-event-normalized excess-of-mass stability

`E_y(C) = integral A_y^C(lambda) d lambda`,

where `A_y^C(lambda)` is the fraction of all accessible year-y events that are still members of C at density level lambda, and then uses

`R(C) = min(E_2022(C), E_2023(C))`.

A label-free descriptive audit of the already-frozen parent prelabel established that the parent primarily reprioritizes a largely shared HDBSCAN candidate universe according to cross-year persistence balance. That audit does not define a numerical parameter or threshold for this successor.

The parent objective can nevertheless assign high recurrent stability when the two years accumulate comparable *total* EOM at different parts of the density hierarchy. For a genuinely recurring physical structure, a stronger and still parameter-free notion is simultaneous persistence: both years should support the cluster at the same density scales.

This motivates one local FOSC quality that preserves the exact hierarchy but changes the order of the minimum and integration operations.

## Sole scientific change: density-synchronous recurrent stability

Let C be a condensed-tree cluster node with birth density `b_C`. For each direct condensed-tree child branch j of C:

- `lambda_j` is that branch's departure density from C;
- `n_{j,y}` is the number of descendant point events in that branch belonging to year y;
- `N_y` is the total number of accessible target-excluded events in year y.

For `lambda >= b_C`, define the normalized annual alive-mass curve

`A_y^C(lambda) = (1 / N_y) * sum_{j: lambda_j > lambda} n_{j,y}`.

The parent annual stability is exactly

`E_y(C) = integral from b_C to infinity of A_y^C(lambda) d lambda`

and the promoted parent quality is

`R(C) = min(E_2022(C), E_2023(C))`.

The **sole successor quality** is

`S_sync(C) = integral from b_C to infinity of min(A_2022^C(lambda), A_2023^C(lambda)) d lambda`.

Thus the parent takes the annual minimum after integration; this successor takes the annual minimum pointwise in density before integration.

No smoothing, interpolation, threshold, exponent, weight, learned calibration, density bandwidth, additional HDBSCAN run, cross-year nearest-neighbor rule, annual matching, event deletion, or geometry change is permitted.

### Exact finite computation

For each node C:

1. Use the exact parent birth lambda and exact parent descendant-year accounting.
2. Initialize the alive year counts to the complete descendant-year counts of C at `b_C`.
3. Traverse C's **direct** child departure rows in strictly increasing unique `lambda_j`.
4. On each interval from the previous lambda to the next unique lambda, add
   `delta_lambda * min(alive_2022 / N_2022, alive_2023 / N_2023)`.
5. After accumulating that interval, subtract the descendant-year counts of **all** direct children departing at that same lambda simultaneously.
6. Tied departure lambdas therefore have no arbitrary within-tie order.
7. The final alive counts after the last direct departure must be exactly zero in both years; otherwise fail closed.

The implementation must additionally reconstruct both parent annual EOM values by separately integrating each annual alive-mass curve and require equality to the exact promoted-parent annual EOM computation within a frozen numerical tolerance of `1e-12` absolute and relative. This is an engineering identity check only, not a tunable scientific parameter.

For every node, the implementation must verify `S_sync(C) <= min(E_2022(C), E_2023(C)) + tolerance`.

## Unchanged hierarchy and flat extraction

Everything upstream of the local cluster-quality map remains exact promoted recurrent-EOM v1:

- target-excluded GMN 2022+2023 only;
- inclusive protected exclusion `[20 deg, 55 deg]` before clustering;
- exact GEO6 representation `(cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- `cluster_selection_method="eom"`;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- unchanged condensed tree and memberships available to extraction.

The exact HDBSCAN/FOSC extraction routine is then run on the unchanged condensed tree with `S_sync(C)` as the sole local quality map.

The successor candidate order is fixed as:

1. descending `S_sync`;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. deterministic family ID.

No promoted-parent recurrent score is blended back into the successor order.

## Why this is distinct from closed successors

This protocol is not a rescue of any closed successor:

- **consensus-EOM** compared already-integrated annual EOM vectors componentwise during parent-vs-children selection; this method changes the local quality itself by retaining density-level timing information before annual integration;
- **ECDF recurrent-rank** left all memberships fixed and rescaled final annual EOM ranks; this method uses the raw condensed-tree lifetime process and may change selected nodes;
- **cross-year-core** changed mutual-reachability geometry and enforced opposite-year support before the hierarchy existed; this method leaves GEO6, core distances, MST, hierarchy and all events unchanged;
- **reciprocal-transfer** fit separate annual models and hard-matched annual clusters; this method uses one unchanged pooled hierarchy and contains no annual matching or majority threshold;
- **phase equalization** warped solar longitude before HDBSCAN; this method makes no representation or density-geometry transform.

## Mandatory synthetic/source audit before GMN activation

No GMN scientific execution is authorized until a zero-truth synthetic/source audit proves all of the following under the exact implementation bytes:

1. **parent annual identity:** density-curve integration reconstructs both exact parent annual EOM values for every synthetic node within `1e-12` absolute/relative tolerance;
2. **upper bound:** `S_sync <= min(E_2022,E_2023)` for every synthetic node;
3. **identical-curve identity:** when the two normalized annual alive-mass curves are identical, `S_sync = E_2022 = E_2023`;
4. **timing sensitivity:** a preregistered synthetic tree with equal or comparable integrated annual EOM but crossing annual alive-mass curves produces a strict `S_sync < min(E_2022,E_2023)`;
5. **year-swap invariance:** swapping the two annual labels leaves every `S_sync` unchanged;
6. **tie invariance:** permuting direct-child rows that share an identical lambda leaves every result bitwise or numerically identical under the frozen tolerance;
7. **ordinary hierarchy identity:** the successor never changes the condensed tree, ordinary HDBSCAN stability, or raw GEO6;
8. **FOSC locality:** a node's `S_sync` depends only on that node's direct departure rows, descendant-year counts, its birth lambda, and the two fixed annual event totals; no other candidate's score/order may enter it;
9. protected `[20,55]`, target information/events, SonotaCo, EFN, ASFN, AMOS, MAARSY and DMS are inaccessible;
10. no label/truth field is accepted by the synchronous-stability kernel.

Any failed identity audit blocks scientific activation until a semantic-neutral engineering correction is separately documented. Such a correction may not alter this formula.

## Binding target-excluded GMN development comparison

After the mandatory audits pass, the first technically valid GMN 2022+2023 execution is binding.

It must reconstruct promoted recurrent-EOM v1 on the same unchanged tree and require the exact parent metrics before successor truth evaluation:

### 2022 promoted parent

- recovered@50 = `45`;
- recovered@100 = `89`;
- top-100 dominant precision = `0.7856486013` (full stored value checked by implementation);
- MRR = `0.0224982696` (full stored value checked by implementation);
- median top-500 fragmentation = `1.0`.

### 2023 promoted parent

- recovered@50 = `46`;
- recovered@100 = `89`;
- top-100 dominant precision = `0.7867680237` (full stored value checked by implementation);
- MRR = `0.0220239289` (full stored value checked by implementation);
- median top-500 fragmentation = `1.0`.

### Frozen promotion gate

`PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT` requires:

- successor recovered@50 >= parent in **both** years;
- successor recovered@100 >= parent in **both** years;
- successor top-100 dominant precision >= parent in **both** years;
- successor MRR >= parent in **both** years;
- successor median top-500 fragmentation <= parent in **both** years;
- recovered@100 is **strictly higher in at least one year**;
- the synchronous objective is active, meaning either the selected-node set or the complete candidate order differs from promoted recurrent-EOM v1.

Otherwise the binding verdict is `FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT`.

Reporting-only @25, @500, candidate count and full-catalogue qualified matches cannot rescue a failed gate.

## Permanent no-rescue rule

After the first technically valid GMN outcome, this exact method is frozen permanently. A failure does **not** authorize:

- weighted or soft minima;
- harmonic/geometric/arithmetic annual combinations;
- partial blending with parent recurrent stability;
- density-window weighting;
- lambda transforms or normalization;
- smoothing/alignment/warping of annual alive-mass curves;
- lagged density matching;
- annual event reweighting beyond the inherited `1/N_y` normalization;
- thresholding the overlap fraction;
- parent/successor rank fusion;
- HDBSCAN parameter changes;
- geometry changes;
- candidate-budget or source-specific rules;
- SonotaCo-informed repair;
- ASFN/EFN/AMOS-informed repair;
- a second search over variants motivated by this outcome.

Any later successor would require a genuinely new mechanism and a new pre-outcome scientific justification.

## Data governance and claims

- The protected target solar-longitude interval `[20 deg,55 deg]` remains inaccessible.
- OrbitTrace target information and target-region events remain inaccessible.
- SonotaCo 2013/2014 remains exposed development but is **not accessed or authorized by this protocol**.
- EFN and ASFN are not used to tune or evaluate this successor.
- AMOS remains reserved under its already-frozen recurrent-EOM v1 external-validation protocol and is not accessed here.
- MAARSY and DMS remain scientifically inaccessible.
- GMN 2022+2023 is development only.
- A GMN PASS would promote this method only as a stronger development parent; it would not constitute external validation.
