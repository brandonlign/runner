# OrbitTrace GMN member-exclusivity margin representation v1 — binding result

## Verdict

`FAIL_GMN_MEMBER_EXCLUSIVITY_MARGIN_V1`

This is a clean scientific failure of the sole preregistered two-feature annual member-exclusivity-margin augmentation. It is not a technical failure. The exact #1194 parent reproduced, the 36D successor was constructed successfully, all five strict whole-shower OOF folds completed, all provenance/firewall checks passed, and the binding artifact uploaded successfully.

Importantly, this is the first clean post-governance representation successor in this lineage to improve the primary recovered@100 metric over #1194, but it fails the full preregistered promotion gate because that improvement comes with losses at the earliest budget, top-100 precision, and MRR.

## Frozen provenance

- pre-outcome protocol freeze commit: `4681d42314ac3b3aa20a5bd12513dc644553b944`
- protocol Git blob: `b4b8878247fb1b7fe5a99a0bcfffc707620cde11`
- frozen implementation commit: `ff4638c48f14e533a1717eb41a8c8d7ce6fc89f3`
- implementation Git blob: `ad73df99efb5fa6df1639a023b1c4ce953438b8c`
- execution-plumbing commit / binding run head: `415c3834206f70fe2b33e3f4b95da9ae1d74b43a`
- first technically valid binding run: `31619889472`
- binding job: `94191769290`
- binding artifact: `orbittrace-gmn-member-exclusivity-margin-v1`
- artifact ID: `9150886887`
- artifact digest: `sha256:d76238bc2f1e93891244c2b5a10df89ca6228e5bfa0610139ebefcc9fee90083`

## Sole scientific change

The exact #1194 34D family representation was augmented with exactly two label-free features, one for 2022 and one for 2023.

For every actual member meteor of family F in a year:

- `d_own` = normalized physical distance to F's frozen annual centroid;
- `d_alt` = minimum normalized physical distance to every other one of the 4,503 frozen annual candidate centroids;
- member exclusivity margin = `d_alt - d_own`.

The sole appended feature for each year is the arithmetic mean signed margin across that family's members.

The normalized physical coordinates remained exactly the preregistered inherited scales:

- circular solar-longitude residual / 10 degrees;
- circular Sun-centered ecliptic-longitude residual / 4 degrees;
- ecliptic-latitude residual / 4 degrees;
- log geocentric-speed ratio / log(1.10).

No shared-event competitor was excluded. No nearest-k search, source restriction, threshold, normalization, quantile, membership edit, model change, target change, diversity change, feature selection, or score fusion occurred.

## Feature provenance

Complete annual member-event competition calculation:

- 2022 unique member events: **862,251**
- 2022 membership occurrences: **3,215,773**
- 2022 annual feature SHA-256: `fdb9faf89a80561ea773ab525eadd5c38db4fb0ddc91c906fda732fdc934bd56`
- 2023 unique member events: **1,143,322**
- 2023 membership occurrences: **4,276,161**
- 2023 annual feature SHA-256: `718f81357123d881c897ea418073d12e5cf8800b41f5de77ca15c57d80711033`
- complete 2D exclusivity matrix SHA-256: `0c4eeb7307079606ec2377f51bb40ae0f7a34aef35259d3bd3b4496c0000468`

Annual feature ranges:

- minima: `[-0.6464551758058024, -0.5746822893139415]`
- medians: `[0.062155419783549214, 0.06015920828069815]`
- maxima: `[0.3330234404531875, 0.44473022815888824]`

Binding feature-matrix hashes:

- parent 34D matrix SHA-256: `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`
- successor 36D matrix SHA-256: `cfca2cbe4c0403bf1af1b2907931830ef3996fb9a026f77c43f6fccc820937bc`

## Exact parent reproduction

#1194 representative-share OOF parent:

- recovered@25: **22**
- recovered@50: **43**
- recovered@100: **80**
- recovered@500: **171**
- top-100 dominant precision: **0.8075287489258385**
- MRR: **0.02016666446026534**
- median first rank: **225.0**
- qualified matches: **256**
- order SHA-256: `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`

## Binding successor outcome

36D parent + annual member-exclusivity-margin representation:

- recovered@25: **20**
- recovered@50: **44**
- recovered@100: **82**
- recovered@500: **172**
- top-100 dominant precision: **0.8027484848168005**
- MRR: **0.02005731755806371**
- median first rank: **223.5**
- qualified matches: **256**
- successor order SHA-256: `7775047398fbfafb785a3c6178d09d37da8b421792dc458b16eafdaba46d4c79`

Gate results:

- recovered@100 > 80: **PASS**
- recovered@50 >= 43: **PASS**
- recovered@25 >= 22: **FAIL**
- recovered@500 >= 171: **PASS**
- top-100 precision >= parent: **FAIL**
- MRR >= parent: **FAIL**
- qualified matches == 256: **PASS**

No full successor model was frozen.

## Scientific interpretation

This result provides real evidence that event-level competition against the full candidate catalogue exposes information that the current 34D family summaries do not contain. The new representation improves recovery@100 from 80 to 82, recovery@50 from 43 to 44, and recovery@500 from 171 to 172.

However, the gain is not uniformly better ranking. It loses two labels at @25, lowers top-100 precision from 0.80753 to 0.80275, and lowers MRR. Under the preregistered all-metric promotion gate it therefore fails and cannot replace #1194.

The correct conclusion is **not** to tune the margin summary until those losses disappear. The exact annual-mean own-vs-nearest-competitor margin lane is closed. The result may only be used as mechanism evidence that event-level competitive context can carry additional signal; any successor must introduce a genuinely distinct representation mechanism rather than a post-outcome refinement of this margin.

## Closed rescue space

Do not rescue this result with:

- normalized, relative, ratio, or log distance margins;
- median, quantile, minimum, maximum, positive-fraction, or cross-year summaries;
- nearest-k competing families;
- source-restricted or cross-generator-only competitors;
- excluding competitors that share the member event;
- trajectory-model competitors instead of frozen centroids;
- local-background intrusion variants;
- event-level thresholds or membership deletion;
- combinations/fusion with graph spacing, member scatter, energy distance, thinning stability, or predictive consistency;
- feature subsets/interactions;
- estimator/hyperparameter changes;
- target/diversity changes;
- parent-score fusion;
- post-result parameter or feature searches.

Any later successor must be independently motivated from permitted target-excluded GMN evidence, checked against existing closed lanes, and frozen before its first valid outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar-longitude exclusion `[20.0, 55.0]`;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no threshold search, representation search, feature selection, or post-result second search occurred.
