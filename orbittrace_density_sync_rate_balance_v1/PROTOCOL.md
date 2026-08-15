# OrbitTrace density-sync rate-balance v1 — frozen protocol

## Purpose

Test one parameter-free final-family recurrence correction on top of the exact density-synchronous recurrent-EOM v1 GMN champion (#1263). This protocol is frozen before implementation and before any scientific outcome.

The mechanism is distinct from the failed year-shift v1. Year-shift tested whether annual labels explain within-family GEO6 geometry. Rate-balance instead tests whether the final selected family is represented at a similar exposure-corrected event rate in both observing years.

Recurrent-EOM already normalizes branchwise EOM contributions by the total accessible event count in each year before taking the annual minimum. It does not explicitly require the final selected membership itself to have comparable annual occurrence rates. This successor adds only that final-family recurrence condition.

## Exact parent

Density-synchronous recurrent-EOM HDBSCAN v1, PR #1263, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Binding GMN run `31852836840`, artifact `9238142199`.

- prelabel SHA-256: `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`
- result SHA-256: `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`
- candidate count: `2,094`

Accessible target-excluded event counts are fixed by the inherited parser:

- 2022: `315,024`
- 2023: `423,658`

Parent total recovered@100 is `179` (`89 + 90`).

## Frozen statistic

For each exact #1263 candidate C, let `n22` and `n23` be its exact final member counts from 2022 and 2023.

Define exposure-corrected annual occurrence rates:

`r22 = n22 / 315024`

`r23 = n23 / 423658`.

Define the symmetric recurrence balance

`B_rate = 2 * min(r22, r23) / (r22 + r23)`

when `r22+r23>0`, otherwise `0`.

Thus `B_rate` is in `[0,1]`, equals `1` only when the exposure-corrected final-family rates are equal, and is `0` if one year contributes no final members. It contains no fitted expectation, threshold, exponent, p-value cutoff, pseudocount, or tunable parameter.

Define successor score

`S_rate(C) = S_sync(C) * B_rate(C)`,

where `S_sync` is the exact frozen density-synchronous stability attached to the #1263 candidate.

Rank descending by:

1. `S_rate`;
2. parent synchronous stability;
3. parent ordinary stability;
4. member count;
5. stable family ID.

No other membership change, normalization, transform, clipping, blending weight, or tie rule is allowed.

## Firewall

Development uses only target-excluded GMN 2022+2023 through the exact frozen #1263-compatible runtime. `[20.0,55.0]` solar longitude remains excluded inclusively before candidate scoring or truth evaluation.

The complete 2,094-candidate successor order and all annual counts/rates/balance values must be persisted before hidden known-shower truth is opened.

The following remain inaccessible during GMN development:

- OrbitTrace target information/events;
- SonotaCo 2013/2014;
- AMOS;
- MAARSY;
- DMS.

The first technically valid outcome is binding.

## Strong GMN gate

PASS requires all of:

1. mechanism active;
2. exact candidate count remains `2,094`;
3. exact membership universe remains identical to #1263;
4. in each year separately, no regression versus #1263 on recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation;
5. total recovered@100 improves by at least `+2`, from `179` to at least `181`.

A one-family gain is insufficient.

## Pre-frozen SonotaCo contingency

Only if the first technically valid GMN result passes may this exact unchanged successor be evaluated on the already-exposed SonotaCo 2013/2014 development-validation benchmark. SonotaCo remains non-pristine.

Promotion requires no macro-F1 or recovered-count regression on any of the four established Sugar/HDBSCAN panels, strict macro-F1 improvement on at least two panels, and continued superiority over the matched frozen literature comparator on all four panels.

A separate frozen robustness diagnostic would still be required before any final-method claim. AMOS remains untouched for development.

## Permanent no-rescue rule

After the first technically valid GMN outcome, do not change the exposure counts, balance formula, multiplicative form, parent score, pseudocount, threshold, exponent, family-size handling, tie order, HDBSCAN settings, metric, gate, or candidate membership. Failure permanently closes this exact version.