# OrbitTrace GMN competitor-identity consistency v1 — binding result

## Verdict

`FAIL_GMN_COMPETITOR_IDENTITY_CONSISTENCY_V1`

This is a clean scientific failure of the sole preregistered categorical nearest-competitor-identity representation. It is not an engineering failure. Exact #1194 parent provenance and metrics reproduced, the full target-excluded two-year collision table completed, strict whole-shower OOF evaluation completed, all firewall checks passed, and the artifact uploaded successfully.

## Frozen provenance

- protocol freeze commit: `dc10f19992e5e8ebb1c0bd56ed4b3e09a8d94d32`
- protocol blob: `0a4a98f99c1f2a3e5f05738af731c9b3ccfde736`
- implementation freeze commit: `d2ab24a90ceac62130581433e123c7280df31f9b`
- implementation blob: `77af55689b5984dfb32d8104b8bf4c2e3a633b33`
- workflow registration / execution head: `f2b09aacb624031f281cb92b6d4e7ab52f10e3a6`
- first technically valid binding run: `31639349882`
- binding job: `94257627042`
- binding artifact: `9158308199`
- artifact digest: `sha256:20f7e916fdfc03e4077c10b1695b629276098a738908bbbca44e0912adfe8b90`

## Sole representation change

Starting from the exact 34D #1194 representative-share parent, append exactly two annual features.

For each actual member event of family F in a given year:

1. compute the inherited four-coordinate physical distance to all 4,504 frozen annual family centroids;
2. exclude only F itself;
3. retain only the deterministic nearest alternative-family identity, not its distance or any margin;
4. within each family-year, compute `sum_j (c_j/n)^2`, the probability that two independent member draws with replacement select the same nearest alternative identity.

No distance-margin value, entropy, threshold, nearest-k, source restriction, graph rule, feature subset, estimator change, target change, or diversity change was used.

## Exact parent reproduction

- recovered@25: `22`
- recovered@50: `43`
- recovered@100: `80`
- recovered@500: `171`
- top-100 dominant precision: `0.8075287489258385`
- MRR: `0.02016666446026534`
- median first rank: `225.0`
- qualified matches: `256`
- parent order SHA-256: `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`

## Binding successor outcome

- recovered@25: `24` — improved by +2
- recovered@50: `45` — improved by +2
- recovered@100: `79` — worsened by -1
- recovered@500: `173` — improved by +2
- top-100 dominant precision: `0.7929562179897718` — worsened
- MRR: `0.020578445161639706` — improved
- median first rank: `226.0` — worsened by 1
- qualified matches: `256` — unchanged
- successor order SHA-256: `4a9400aaabc3a6610b170f5522666795d1319303a23525709f062c9334e0a2bd`

Binding gates:

- @100 > 80: **FAIL**
- @50 >= 43: PASS
- @25 >= 22: PASS
- @500 >= 171: PASS
- top-100 precision >= parent: **FAIL**
- MRR >= parent: PASS
- qualified matches == 256: PASS

## Feature provenance

- 2022 unique member events: `30,576`
- 2022 membership occurrences: `32,998`
- 2022 feature SHA-256: `a0948abfee4c59f14b00d99cac833f9e9eba1e86dc842d16146c18fafbf92849`
- 2023 unique member events: `36,659`
- 2023 membership occurrences: `41,499`
- 2023 feature SHA-256: `bd17d6aa20668b81b7e5ac3ca0743ed0d99059061757bbb94bc834b2b6730a96`
- combined collision matrix SHA-256: `c2fefc8f4bdc830520fed905d61352ec7c5061bfc1b71c94eed0f20ac4626954`
- annual median collision probabilities: `0.625` (2022), `0.68` (2023)

## Scientific interpretation

The exact categorical collision representation is rejected because it fails the primary @100 and precision gates. However, it provides independent target-excluded evidence that event-level competitive context is not merely noise: relative to the same exact #1194 parent, it improves @25, @50, @500 and MRR while changing no candidate identities, memberships, target, learner, OOF folds, or diversity rule.

Together with the earlier member-exclusivity-margin result (which improved @50/@100/@500 but failed @25/precision/MRR), this indicates that competitive context contains real information absent from the 34D family summaries, but the two tested scalar summaries distort different parts of the ranking. This is mechanism evidence only; it does not authorize combining the two failed features.

This exact lane is permanently closed. Do not rescue it with entropy/Gini/Renyi variants, unique competitor count, dominant competitor share, inverse/log collision transforms, without-replacement pair probability, cross-year summaries, nearest-k/soft identities, source restrictions, margin combinations, graph/scatter/energy/thinning/predictive-consistency fusion, feature interactions, estimator changes, parent-score blending, or post-result searches.

A later successor must use a genuinely distinct representation mechanism and be separately frozen before its first outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar longitude `[20.0,55.0]` exclusion;
- SonotaCo 2013/2014 access: false;
- SonotaCo feature access: false;
- OrbitTrace target information/events access: false;
- protected target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
