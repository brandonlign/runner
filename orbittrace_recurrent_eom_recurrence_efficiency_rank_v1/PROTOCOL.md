# Recurrent-EOM recurrence-efficiency rank v1 — frozen protocol

## Scientific role

This is one ranking-only successor to exact recurrent-EOM HDBSCAN v1, motivated by the frozen residual-error decomposition in PR #1290. It uses only the already-exposed SonotaCo 2013/2014 development benchmark. It is not external validation.

The residual analysis found ranking/selection to be the largest remaining error class (67/135 pooled panel misses, 49.63%), while membership contamination was only 10/135. This protocol therefore changes ranking only.

## Immutable parent

Parent: exact recurrent-EOM HDBSCAN v1 from `agent/orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`.

Binding parent workflow run: `31829200215`.

Binding parent artifact: `9230008341`, artifact name `orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`.

Expected parent pretruth SHA-256:

`c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef`

Expected parent result SHA-256:

`c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12`

The parent candidate universe, selected HDBSCAN nodes, family IDs, event memberships, GEO6 representation, HDBSCAN settings, recurrence extraction, and family count are immutable. No HDBSCAN fit or candidate membership may be regenerated or changed by this successor.

## Sole scientific change

For each immutable recurrent-EOM family, let:

- `S_rec` = the frozen parent `recurrent_stability`, i.e. the smaller of the two year-normalized annual EOM values;
- `S_ord` = the frozen parent `ordinary_stability`, i.e. pooled HDBSCAN EOM stability.

Define the parameter-free recurrence-efficiency score

`S_eff = S_rec^2 / S_ord` when `S_ord > 0`.

If `S_rec == 0`, define `S_eff = 0`. If `S_ord == 0`, this is permitted only when `S_rec == 0`, and `S_eff = 0`; any `S_ord <= 0` with positive `S_rec`, nonfinite value, or negative `S_rec` fails closed.

Within a route the pooled event count is fixed, so this ordering is equivalent up to a route-wide constant to:

`absolute recurrent evidence × recurrent share of pooled normalized EOM`.

The complete deterministic successor order is:

1. `S_eff` descending;
2. `S_rec` descending;
3. `S_ord` descending;
4. member count descending;
5. family ID ascending.

No learned weight, exponent search, threshold, blend, ECDF transform, route/year-specific rule, candidate subset, diversity rule, or post-result rescue is allowed.

## Immutable evaluation panels

Inherited matched panel budgets are unchanged:

- Sugar 2013: budget 34;
- Sugar 2014: budget 46;
- catalogue-HDBSCAN 2013: budget 11;
- catalogue-HDBSCAN 2014: budget 9.

Eligible truth showers and evaluation semantics are inherited exactly from the parent: non-`SPORADIC` labels with at least four truth members, one-to-one Hungarian assignment, macro-F1 across eligible truth showers, and recovered count defined by assigned `F1 > 0.5`.

Exact parent controls that must reproduce before a successor verdict is accepted:

- Sugar 2013: macro-F1 `0.3752906816276458`, recovered `23`;
- Sugar 2014: macro-F1 `0.43773122295664196`, recovered `24`;
- HDBSCAN 2013: macro-F1 `0.1914598192215768`, recovered `11`;
- HDBSCAN 2014: macro-F1 `0.1685878550176112`, recovered `9`.

## Frozen promotion gate

`PASS_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1` requires all of the following:

1. candidate family IDs and event memberships are exactly identical to the parent on both routes;
2. the complete successor order is non-identical to the parent on at least one route;
3. successor macro-F1 is greater than or equal to parent macro-F1 on all four panels;
4. successor recovered count is greater than or equal to parent recovered count on all four panels;
5. at least one of the four panels has a strict macro-F1 increase or a strict recovered-count increase.

Otherwise the verdict is `FAIL_RECURRENT_EOM_RECURRENCE_EFFICIENCY_RANK_V1` and this exact score family is closed. No alternate power, denominator transform, weighted blend, rank fusion, threshold, route-specific exception, budget-specific exception, or result-informed second attempt is authorized.

## Pretruth barrier

The complete reranked candidate order for both routes must be generated solely from the immutable parent pretruth payload and hash-frozen before SonotaCo shower truth is made available to the evaluation step. The evaluation step accepts the persisted successor pretruth and may not recompute or alter its ranking.

## Firewall

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.

Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY, DMS, and any pristine external endpoint remain inaccessible. No external survey may be opened or used to select, tune, or rescue this ranking rule.
