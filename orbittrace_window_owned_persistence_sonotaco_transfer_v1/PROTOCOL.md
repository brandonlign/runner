# OrbitTrace window-owned persistence SonotaCo transfer v1

## Activation

Frozen before the first GMN recovery/ranking v1 outcome. Execute only if `agent/orbittrace-window-owned-persistence-ranking-v1` produces `PASS_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT`. Any GMN FAIL permanently blocks this transfer.

## Role

Direct unchanged transfer to the already-exposed SonotaCo 2013/2014 development/validation benchmark. SonotaCo is not pristine external validation.

Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY and DMS remain inaccessible.

## Exact transferred method

The complete candidate construction and ranking are byte/semantically identical to GMN ranking v1:

- GEO6;
- Persistable `7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`;
- 72 fixed 10° windows stepped by 5°;
- package-default midpoint hierarchy per window;
- conservative flattenings `g=2..min(15,B)`;
- memberships >=4;
- owner = nearest fixed window center to candidate circular-mean solar longitude, tie smaller center;
- exact-membership deduplication;
- ranking: both-year presence desc, `g_first` asc, `g_span` desc, minimum annual count desc, total count desc, family ID asc.

No parameter, ranking field/order, support, window geometry, representation, neighbor policy, or membership rule may change for SonotaCo.

## Frozen input and benchmark

Use exact label-free SonotaCo preparation from run `31354363306`:

- manifest SHA `0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b`;
- Sugar 2013 `47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8`;
- Sugar 2014 `bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912`;
- HDBSCAN 2013 `2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158`;
- HDBSCAN 2014 `206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55`.

Use the exact established direct SonotaCo benchmark/evaluator from PR #1269, source commit `113b951b1ae9f9f9759f5833eb08aecc47cdf4aa`, and its frozen panel budgets:

- Sugar 2013: 34;
- Sugar 2014: 46;
- HDBSCAN 2013: 11;
- HDBSCAN 2014: 9.

The recurrent-EOM control result is exact run `31829200215`, SHA `c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`.
The v31 result SHA is `f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e`.

## Pretruth barrier

For each route (`sugar`, `hdbscan`), pool label-free 2013+2014 rows, construct exact recurrent-EOM candidates and exact transferred successor candidates/ranking, then write and hash the complete pretruth object before any truth, v31 result, historical recurrent result, or matched-literature evaluation artifact is opened.

The pretruth object must assert truth/control access false and target/firewall access false.

## Evaluation

After pretruth freeze only, use the exact PR #1269 assignment evaluator and exact historical candidate budgets. Report for each of four panels:

- macro-F1;
- recovered showers with F1 > 0.5;
- recurrent-EOM control;
- v31 control;
- matched-literature comparator.

Historical recurrent-EOM results must reproduce exactly before successor interpretation.

## Frozen gates

PASS only if all hold:

1. all input/source/pretruth/firewall identities reproduce;
2. on **every** panel, successor macro-F1 >= recurrent-EOM macro-F1;
3. on **every** panel, successor recovered count >= recurrent-EOM recovered count;
4. successor is strictly better than recurrent-EOM in macro-F1 or recovered count on at least one panel;
5. on **every** panel, successor macro-F1 > v31 macro-F1 and recovered count >= v31 recovered count;
6. on **every** panel, successor macro-F1 > matched-literature macro-F1 and recovered count >= matched-literature recovered count.

No averaging can rescue a panel regression. A FAIL is binding and cannot alter the transferred method or benchmark. A PASS establishes exposed cross-survey transfer support only; it does not authorize protected target access or a pristine-external claim.