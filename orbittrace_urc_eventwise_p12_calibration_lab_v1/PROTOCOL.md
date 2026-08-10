# URC eventwise P12 calibration lab v1

## Motivation

The active catalogue ranking is fixed by PR #839: the exact 4,504-family hard-v8 + P19-soft + P20-soft union ranked by strict same-shower grouped ExtraTrees quality regression with diversity lambda 0.8 / scale 1.0. It reaches recovery@100=75, recovery@50=40, 256 qualified known streams and top-100 dominant precision 0.7645689181 on target-excluded GMN 2022/2023.

Membership remains the main unresolved weakness. Full frozen P12 raises v8 membership macro F1 from 0.173666 to 0.376613 but loses four qualified streams (95 -> 91). PR #821 then showed that whole-family core-vs-full-P12 switching cannot solve this: even the truth-aware family-level oracle loses qualified streams. That result motivates an event-level selector; it does not authorize threshold retuning of P12 itself.

## Frozen candidate/ranking boundary

- Candidate universe remains exactly 226 hard + 1,075 P19-soft + 3,203 P20-soft = 4,504 families.
- Exact #839 rank order must reproduce SHA-256 `ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449`.
- P19/P20 soft memberships are never changed.
- Only already-accepted, pretruth-frozen P12 assignments to the 226 hard families are eligible additions.
- Original members can never be removed.
- Added members never recurse, change centroids, regenerate proposals, or change ranking.

## Event-level model

Development supervision is permitted only from known GMN showers outside the sealed OrbitTrace region. Application features are target-free and contain no shower identity.

Training examples are P12-added events attached to hard cores that are already qualified known showers under the original core membership. The binary target is whether the added event has the same known-shower label as that core during development evaluation.

The complete frozen feature vector is:

1. P12 responsibility;
2. responsibility minus P12 membership floor;
3. responsibility minus seed floor;
4. log(1+odds);
5. drift distance / frozen observation ceiling;
6. orbital distance / frozen orbital ceiling;
7. P11 density score / frozen density threshold;
8. membership floor;
9. seed floor;
10. log(1+original core member count);
11. original core two-year member balance.

No year indicator, shower identity, candidate rank, final-test value, or target-specific field is used.

The sole model is `ExtraTreesRegressor` on the binary correctness target with exactly:

- 512 trees;
- max depth 4;
- min samples leaf 20;
- all features considered at each split;
- random seed 84601;
- one thread.

Every supervised shower is held out as a whole using five-fold `GroupKFold` by known shower. All additions associated with one shower therefore receive out-of-group predictions. Families that provide no supervised training examples receive the all-development model; their own labels never entered that model.

## Frozen threshold family

Exactly six fixed probability thresholds are evaluated: 0.50, 0.60, 0.70, 0.80, 0.90, 0.95. No threshold is inserted after results are seen.

A threshold passes only if, under the unchanged #839 order:

- recovery@100 >= 75;
- recovery@50 >= 40;
- qualified known streams >= 256;
- top-100 dominant precision >= 0.74;
- best-membership macro F1 >= #839 baseline +0.025;
- annual all-shower mean F1 does not regress in either 2022 or 2023 and improves by >=+0.005 on average;
- annual 4–9-member mean F1 regresses by no more than 0.002 in either year and is nonnegative on average;
- at least one of the 25–49, 50–99, or 100+ strata improves by >=+0.02 in both years.

A scientific PASS requires at least two adjacent frozen thresholds to pass. This prevents promotion from an isolated favorable cutoff. Among thresholds belonging to an adjacent passing region, selection is deterministic: maximize membership macro F1, then recovery@100, qualified count, top-100 precision, fewer additions, then the higher threshold.

A failure is permanent for this architecture. The threshold grid or model is not widened after seeing the result.

## Data boundary and pipeline

Only target-excluded GMN 2022/2023 development data and already-frozen P12 development artifacts may be used. Solar longitude 20°–55° remains removed. SonotaCo 2013/2014, MAARSY 2020/2021 scientific values, and all OrbitTrace target information remain inaccessible.

A PASS is still development-only. The integrated URC method may advance toward the one final SonotaCo 2013/2014 literature test only after the independent candidate-generation stress is also resolved and the complete method is frozen. A FAIL leaves #839 with original memberships as the active method unless another already-preregistered development experiment passes.
