# Core-Majority Regrowth v1

## Scientific question

Can the high-purity Bifiltration Witness Modularity (BWM) cores recover the recall lost by over-segmentation without reopening the oversized support-pruned TopoModal basins?

BWM v1 is a valid frozen zero-label seed generator but failed its hidden-label GMN development gate because recall collapsed while precision improved. This successor does **not** change BWM modularity, rerun community detection, tune a resolution, or use OrbitTrace reveal information. It treats each frozen BWM community as an immutable seed inside its already-frozen support-pruned parent.

## Frozen construction

Inputs are immutable:

- BWM v1 pretruth from run `32292151719`, SHA-256 `2e6eca03f03702c78b36624026e20feb4f081b5d9f9507e0ea3436cc33bb199a`;
- annual-density bifiltration endpoint prelabel from run `32037435314`, SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`;
- promoted support-pruned parent identity SHA-256 `57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f`.

Within each support-pruned parent, rebuild the exact BWM persistence-weighted co-witness graph. A bifiltration witness `B` of size `m` and persistence area `A` contributes `A/(m-1)` to every unordered pair in `B`, preserving the BWM degree-mass identity.

For an original frozen BWM seed core `C` and parent member `v`, let

`d(v)` = total weighted co-witness degree of `v`,

`a(v,C)` = weighted edge mass from `v` directly to members of the **original** core `C`.

Regrow `C` by admitting `v` iff:

`d(v) > 0` and `2 a(v,C) > d(v)`.

This is a strict logical majority. There is no fitted scalar threshold. Regrowth is one-shot: newly admitted events never recruit additional events. Membership can never leave the frozen support-pruned parent.

Exact duplicate grown memberships are deduplicated. Distinct grown candidates may overlap because two independently frozen cores can both have strict-majority support for the same boundary event. Final candidates are ranked by the unchanged exact M2D score, then membership hash.

## What is not allowed

No OrbitTrace canonical IDs, coordinates, protected `[20°,55°]` events, prior rank-84/rank-82/rank-46 target families, SonotaCo truth, or external-survey truth may enter construction or pretruth.

No modularity-resolution search, edge exponent, witness-area transform, affinity coefficient, growth depth, candidate-size cap, score blend, radius/support sweep, target-informed merge, or post-result rescue is authorized for v1.

## Pretruth structural gate

Before GMN shower truth is opened, all must hold on the exact eight target-excluded GMN sparse panels:

1. regrowth is active;
2. mean top-budget family size remains strictly below promoted support-pruned v1;
3. p90 top-budget family size remains strictly below promoted support-pruned v1;
4. maximum top-budget family size remains strictly below promoted support-pruned v1;
5. mean top-budget family size is strictly above BWM seed size, proving the rule actually regrows rather than reproducing BWM.

If any gate fails, GMN truth remains unopened for this method.

## Binding GMN development gate

If the structural gate passes, use the exact frozen PR #1377 comparator-capacity semantics and the byte-frozen BWM hidden-label evaluator logic:

- `k = len(published comparator clusters)` per panel/year/comparator;
- evaluate CMR as the first `k` frozen CMR candidates;
- evaluate promoted support-pruned v1 the same way;
- shortfall is scored naturally and never padded;
- one-to-one Hungarian macro-F1 and `F1 > 0.5` recovery are unchanged.

Promotion requires all ten inherited quality gates: nonlower macro-F1 and recovery versus promoted support-pruned v1 for Sugar route, HDBSCAN route, d=128 scale, and d=1024 scale, plus preservation of both published-configuration literature wins.

This GMN endpoint is explicitly development-exposed. A PASS authorizes a frozen transfer test; it is not untouched external validation and does not by itself establish tuned-HDBSCAN-family superiority.

A valid FAIL freezes exact CMR v1. Do not alter the majority rule after truth and call the altered rule v1.