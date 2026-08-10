# OrbitTrace v25 — strict-group pairwise preference OOF ranking

## Motivation

v22, v23, and v24 all preserve the same fixed SonotaCo candidate universe, memberships, label-free features, and whole-shower OOF firewall but use squared-error regression objectives. v24 produced the strongest HDBSCAN-side result so far (2013 recovered 10/10 at equal budget) yet still underestimated several rare, genuinely excellent held-out showers by large margins. A post-result diagnostic showed that the missing high-quality candidates are mostly different showers, not duplicate fragments, and that simple support size cannot identify them because some have only 16–17 members.

The next admissible question is therefore whether the **loss/objective**, rather than another target transformation, is the bottleneck.

## Frozen data and invariants

v25 preserves exactly:
- the v22/v23/v24 71-dimensional label-free pretruth feature vector;
- exact fixed v19-expanded memberships and candidate universes;
- exact shared Sugar+HDBSCAN exposed-development domain;
- exact deterministic five-fold whole-shower grouping across both routes;
- exact #839 diversity lambda `0.8`, scale `1.0`;
- exact v19 rank-sum order as identity control and optional parameter-free fusion partner;
- exact #854-compatible equal-budget one-to-one maximum-total-F1 evaluation.

The regenerated pretruth payload must pass the same valid-v23/v24 scientific identity gate before truth: memberships and centroids byte-identical; 71-feature arrays identical under the frozen round-to-12-decimal canonical fingerprint.

No feature, membership, candidate, fold, diversity, radius, threshold, comparator-budget, or fusion-weight search is allowed.

## Frozen training quality and strict grouping

`best_label` is determined exactly as in v22–v24 from the combined two-year recurrent-shower comparison. The balanced training quality for a family is the already-tested v23 quantity:

`q = min(F1_2013, F1_2014)`

v25 does **not** change this quality definition. It changes only how the model learns an ordering from it.

All fragments and near-misses associated with the same known shower share the exact same deterministic OOF fold across both route universes. Negative families retain route/family-specific groups.

## Group-balanced pairwise training set

For each OOF fold, only training groups may supply labels.

1. Within each `(route, training_group)` unit, select exactly one training representative: the family with maximum `q`; ties are resolved by stable family ID. This prevents fragment-rich showers from dominating the pairwise training population.
2. Construct every unordered pair of representatives whose underlying shower groups differ and whose `q` values are unequal.
3. For each unordered pair `(i,j)`, emit both orientations:
   - feature difference `X_i - X_j` with label `1` if `q_i > q_j`, else `0`;
   - feature difference `X_j - X_i` with the complementary label.
4. Each orientation receives sample weight `abs(q_i - q_j)`. This is parameter-free and gives negligible influence to scientifically negligible preference differences while emphasizing large quality separations. No pair-difference threshold is introduced.

## Frozen preference model

The pairwise model is `ExtraTreesClassifier` with the exact #839 tree complexity transferred without search:
- `n_estimators=600`
- `max_depth=4`
- `min_samples_leaf=5`
- `max_features=None`
- `random_state=20260809`
- `n_jobs=-1`

No classifier family or hyperparameter grid is evaluated.

For a held-out candidate, the fold model compares it only against the fold's training representatives. For candidate `x` and reference `r`, the antisymmetrized preference is fixed as:

`0.5 * (P(x-r wins) + 1 - P(r-x wins))`

The candidate's OOF preference score is the simple mean of this quantity across all training references. It never uses held-out labels or other held-out targets.

## Frozen output variants and gate

Exactly two successors are evaluated:
1. `pairwise_oof_quality`: exact #839 diversity order applied to the OOF preference score.
2. `pairwise_oof_v19_rank_sum`: parameter-free equal-weight rank-sum between that pairwise order and exact v19 rank-sum.

Exact v19 remains a mandatory identity control and must reproduce all four fixed-membership v19 panel metrics.

PASS requires one frozen successor to win **all four** comparator/year panels: macro-F1 strictly higher than the corresponding literature comparator and recovered F1>0.5 count at least equal to the comparator in every panel. The same robust four-panel lexicographic selector used by v22–v24 chooses between the two frozen successors.

Only an OOF all-panel PASS may fit and fingerprint the identical pairwise model on all exposed SonotaCo training groups. Full-fit in-sample performance is not admissible promotion evidence. A v25 failure is a permanent no-go for this exact pairwise objective and does not authorize a pair threshold, alternate classifier, alternate pair weighting, or fusion search.

## Firewall

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region event, or protected 20°–55° content is authorized. Any protected cross-survey validation requires a separate candidate-specific pretruth protocol after an OOF PASS.
