# OrbitTrace cross-route component recurrence-Bayes diagnostic v1

## Scientific role

Post-v40 exposed-SonotaCo diagnostic only. Binding v40 improved HDB 2013 substantially but failed overall because component best-evidence promotion was not selective enough, especially for the common-order 2014 budget. #1071 independently formalized that a single nested HDB top-9/top-11 order only one/two prefix replacements away from v31 can beat both HDB literature panels, so the remaining problem is choosing the right physical components rather than changing many slots.

This diagnostic tests one new truth-free mechanism: **whether a frozen physical component has stable recurrent support across the two SonotaCo years after accounting for the route-universe year exposure**. It does not evaluate a ranking, selector, threshold, successor, fusion, or replacement rule.

## Frozen pre-truth physical components

Before exposed truth is loaded, reconstruct the exact #1064 radius-1 Sugar↔HDB graph from immutable #950 pretruth centroids and require serialized graph SHA-256
`2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

Freeze the exact #1072 ordinary connected components over all 496 Sugar/HDB vertices and require serialized component SHA-256
`c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`, with 196 components, 113 non-singletons, and 83 singletons.

No graph radius/metric, edge filtering, component pruning/expansion, size threshold, route exception, or component definition search is authorized.

## Pre-truth recurrence-stability statistic

Use only immutable family memberships. SonotaCo event IDs contain their year prefix (`SNT2013:` or `SNT2014:`), so no truth catalogue is needed to count annual support.

1. Form the union of event IDs appearing anywhere in the fixed Sugar or HDB candidate universes. Let `N13` and `N14` be the numbers of unique 2013 and 2014 event IDs and define the fixed exposure fraction
   `p13 = N13 / (N13 + N14)`.
2. For each frozen cross-route component, take the union of event IDs from **all** Sugar and HDB families in that component. Let `k` be its unique 2013 count and `n-k` its unique 2014 count.
3. Define exactly one recurrence-stability statistic, the log Bayes factor

   `logBF = log(n+1) + log C(n,k) + k log(p13) + (n-k) log(1-p13)`.

This compares:
- `H0`: component event years follow the fixed survey-wide exposure fraction `p13`;
- `H1`: the component has an unconstrained Bernoulli year fraction with a uniform `Beta(1,1)` prior, whose beta-binomial marginal count probability is `1/(n+1)`.

Higher `logBF` means stronger evidence that the component's two-year support is compatible with stable recurrence rather than an idiosyncratic year split. The formula, exposure definition, prior, component union, and event de-duplication are frozen before truth. No alternative prior, pseudocount, transform, clipping, year-balance score, count threshold, significance threshold, or statistic search is authorized.

The pre-truth output must be written with `truth_accessed=false` before the truth artifact is downloaded.

## Truth-aware diagnostic only after statistic freeze

After the pre-truth statistic file is frozen, load immutable exposed SonotaCo 2013/2014 truth.

For each route separately, retain the unchanged v22 strict recurrent-label definition. For every fixed family, compute annual F1 for its unchanged best recurrent label exactly as in v24. A frozen component is:
- annual-recoverable in year `y` iff it contains at least one own-route family with `F1_y > 0.5`;
- dual-year-recoverable iff it contains at least one own-route family whose unchanged best label has both `F1_2013 > 0.5` and `F1_2014 > 0.5`.

For Sugar-containing and HDB-containing components separately report:
- component counts and recoverable counts;
- median/mean `logBF` for dual-year-recoverable vs non-dual components;
- median/mean `logBF` for 2014-recoverable vs nonrecoverable components;
- Mann-Whitney rank AUC (`U / (n_positive*n_negative)`) for the one-sided hypothesis that recoverable components have larger `logBF`;
- the corresponding one-sided p-value as descriptive evidence only.

The direction is considered supported only if **both Sugar and HDB** have:
1. dual-year-recoverable median `logBF` strictly above non-dual median and AUC > 0.5; and
2. 2014-recoverable median `logBF` strictly above nonrecoverable median and AUC > 0.5.

No p-value cutoff is used to authorize the direction. No family/component identity, oracle replacement, threshold, rank, or successor is selected.

## Interpretation boundary

A PASS means cross-year recurrence stability is a genuine route-general component-level evidence channel distinct from v40's best-v31-rank evidence and can justify one separately frozen successor architecture. It does **not** justify a particular combination rule, coefficient, threshold, hard filter, budget rule, or oracle substitution.

A FAIL closes recurrence-stability evidence as the next component-selection direction and no successor may be rescued from alternate balance transforms or priors.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Candidate generation and memberships remain unchanged.
- No rank/selector/successor/evaluator-budget search is performed.
- No oracle identity from #1050/#1053/#1071 may enter the statistic or any rule.
