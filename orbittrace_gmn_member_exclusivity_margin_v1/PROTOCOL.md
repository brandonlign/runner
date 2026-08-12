# OrbitTrace GMN member-exclusivity margin representation v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 representation-level successor before implementation or first scientific evaluation.

## Motivation from permitted GMN evidence only

This candidate is motivated solely by target-excluded GMN development evidence:

1. The clean post-governance #1194 representative-share parent recovers `22/43/80/171` qualified shower labels at @25/@50/@100/@500 with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.
2. The frozen representative-share oracle diagnostic showed that the exact #1194 target and unchanged diversity operator reach `25/50/100/242` when the target is scored perfectly. Therefore the current 80→100 gap is representation/separability rather than candidate coverage or an intrinsic target/diversity ceiling.
3. The separately frozen member-scatter second-moment augmentation and cross-year energy-distance augmentation both failed their binding gates. They are closed and are not being rescued. Those experiments measured only within-family morphology/distribution structure.
4. The exact #1194 34D representation includes scalar member cohesion to the candidate itself and candidate-centroid neighborhood density, but it does not directly measure whether each **member event is explained more closely by its own family than by the nearest competing candidate family**.
5. PR #1221 local-background trajectory contrast is distinct and closed: it measured the fraction of nearby **nonmember background events entering a candidate's predictive tube**, then used a fixed rank fusion. It did not compare each actual member to its own family versus the nearest competing candidate family.
6. The earlier GMN v31-principle relative-margin OOF experiment is also distinct: it measured nearest positive/nonpositive reference-family distances in an existing learned family-feature space, not event-to-candidate geometric exclusivity.
7. P11 density contrast is an upstream candidate-membership veto using held-fold local seed/unlabeled density ratios, not a fixed-family ranking representation.

No SonotaCo 2013/2014 result, identity, rank, literature gap, missed family, or exposed transfer result is used to define or select this successor.

## Immutable parent

Use exactly the #1194 target-excluded GMN union and ranking machinery:

- hard families: 226;
- P19 families: 1,075;
- P20 families: 3,203;
- union: 4,504 unique families;
- eligible recurrent labels: 355;
- qualified labels: 256;
- exact #1194 scientific source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact #839 34-dimensional parent feature matrix;
- exact #1194 representative-share target;
- exact deterministic whole-shower five-fold OOF assignment;
- exact grouped sample weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)`;
- exact diversity operator `lambda=0.8`, `scale=1.0` and unchanged tie semantics.

The exact parent must reproduce before the successor is interpreted:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256;
- parent order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

Any mismatch is a technical no-result.

## Sole new representation

Append exactly **two label-free features** to the exact 34D parent matrix, one for 2022 and one for 2023, yielding a fixed 36D successor matrix.

### Event-to-centroid physical distance

For an event `e` in year `y` and any candidate family `F` with frozen annual centroid `c_{F,y}`, define the normalized four-dimensional residual vector:

1. circular solar-longitude residual `delta_sol / 10 deg`;
2. circular Sun-centered ecliptic-longitude residual `delta_sun_lon / 4 deg`;
3. ecliptic-latitude residual `delta_ecl_lat / 4 deg`;
4. logarithmic geocentric-speed residual `log(vg_e / vg_c) / log(1.10)`.

Define `d(e,F)` as the ordinary Euclidean norm of this four-dimensional vector.

These coordinate scales are exactly the already-inherited physical scales used by the frozen candidate geometry in the current GMN lineage. They are not tuned or searched here.

### Member exclusivity margin

For each member event `e` of family `F` in year `y`:

- `d_own = d(e,F)`;
- `d_alt = min_{G != F} d(e,G)` over **all other 4,503 frozen candidate families** using their centroid for the same year;
- signed member exclusivity margin = `d_alt - d_own`.

No family is excluded from the competing set because it shares events, source class, generator, component, or geometry with `F`. Shared-event/near-duplicate families are legitimate competing explanations and therefore may reduce the exclusivity margin.

The sole two appended features are:

- arithmetic mean signed member exclusivity margin across all 2022 members of `F`;
- arithmetic mean signed member exclusivity margin across all 2023 members of `F`.

The arithmetic mean is fixed before outcome. No median, quantile, minimum, maximum, positive fraction, ratio, normalized margin, clipping, threshold, source-specific aggregation, cross-year minimum/maximum, or alternate summary is evaluated.

Every family must have at least one member in each year and every family must have a finite frozen annual centroid. Otherwise execution fails closed as a technical no-result rather than imputing or dropping a family.

The complete two-feature table must be computed solely from target-excluded event observables, immutable candidate memberships, and immutable candidate centroids **before and independently of GMN shower truth/targets**.

## Scientific question

This successor tests one specific hypothesis: **member-event exclusivity relative to competing candidate families contains predictive information about family quality that is absent from self-cohesion and centroid-neighborhood summaries**.

A high positive margin means, on average, the family's actual members lie closer to their own candidate centroid than to every competing candidate centroid. A small or negative margin indicates geometrically ambiguous membership even if the candidate is internally compact.

This is not background intrusion (#1221): it conditions on the candidate's actual members and asks own-vs-competing-family explanatory separation. It is not a candidate-spacing rule, candidate deletion, membership veto, positive/nonpositive truth margin, or learned metric.

## Binding evaluation

Run exactly the same strict whole-shower OOF evaluation twice in the same binding execution:

1. exact 34D #1194 parent control;
2. sole 36D parent + two annual member-exclusivity-margin features.

The first technically valid execution is binding.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this 36D representation with the unchanged #1194 learning/ranking machinery. It does not authorize thresholding, membership changes, source-specific rules, or SonotaCo execution.

A FAIL permanently closes this exact member-exclusivity-margin augmentation. Do not rescue it with:

- normalized/relative/log distance margins;
- median/quantile/min/max/positive-fraction summaries;
- nearest-k competing families;
- source-restricted or cross-generator-only competitors;
- excluding competitors that share the member event;
- trajectory-model competitors instead of frozen centroids;
- local-background pools or intrusion fractions;
- event-level thresholds or membership deletion;
- combinations with graph spacing, scatter, energy distance, thinning stability, or predictive consistency;
- feature subsets/interactions;
- estimator/hyperparameter changes;
- target or diversity changes;
- score fusion;
- post-result parameter/feature searches.

Any later successor must be genuinely distinct and separately frozen before outcome.

## Required guards

Before scientific interpretation, execution must verify:

- exact #1194 source Git blob and parent metrics/order;
- exact #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- exact v8/P19/P20 input hashes;
- exact 4,504 family IDs and source counts;
- parent feature shape `(4504,34)`;
- exclusivity feature shape `(4504,2)`;
- successor feature shape `(4504,36)`;
- all event-to-centroid distances and exclusivity features finite;
- every nearest competitor excludes only the current family ID and otherwise ranges over the full frozen family universe;
- all exclusivity feature construction completes before family truth/target use;
- strict whole-shower OOF isolation remains exact;
- candidate identities and memberships remain unchanged.

## Protected-data firewall

Throughout execution:

- protected solar longitude `[20.0,55.0]` remains excluded before labels, features, folds, scores and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development.