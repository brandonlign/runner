# Frozen result — GMN v31 constituent bottleneck diagnostic v1

Binding diagnostic run: `31668962127`

Binding job: `94349514204`

Execution head: `ac10d95f0f2f58a48ae7d79205e9c759d20394ba`

Frozen diagnostic protocol commit: `72b9e9420e9dd950d1780dfa149c4645fc3ed3ee`

Frozen implementation commit: `57dbc08f645332290f317ef9aa077e6dcc82f372`

Artifact:

- ID: `9169001933`
- digest: `sha256:9833b1b805b372d12dd92dcc2c3151386578867aef44aa83d49705915e1143d9`

Verdict: **PASS_GMN_V31_CONSTITUENT_BOTTLENECK_DIAGNOSTIC_V1**

Predeclared top-100 outcome: **CONSTITUENT_DOMINANT**

## Exact parent constituent metrics

Immutable hard order:

- @25 = **21**
- @50 = **38**
- @100 = **59**
- top-100 dominant precision = **0.6884631112636006**
- MRR = **0.04673407605545235**
- qualified labels = **95**

Diversified v31 local order alone:

- @25 = **21**
- @50 = **39**
- @100 = **63**
- top-100 dominant precision = **0.6204548749848309**
- MRR = **0.03662109750246032**
- qualified labels = **95**

Exact equal hard/local v31 fusion:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646695**
- qualified labels = **95**

The tiny displayed MRR difference from the canonical decimal is floating representation only; the workflow's fixed `1e-15` equality check passed against `0.050244164168646674`.

## Predeclared bottleneck result

### Top 100

The fused order recovers 66 and misses 29 of the 95 qualified labels.

Among those 29 fused misses:

- `NEITHER` hard nor local has the label inside 100: **21 / 29 = 72.4138%**;
- `HARD_ONLY`: **4 / 29 = 13.7931%**;
- `LOCAL_ONLY`: **4 / 29 = 13.7931%**;
- `BOTH`: **0 / 29 = 0%**.

Therefore:

- constituent absent = **21 / 29 = 72.4138%**;
- constituent available = **8 / 29 = 27.5862%**.

This satisfies the preregistered `CONSTITUENT_DOMINANT` definition because strictly more than half of fused-missed labels are absent from both same-budget constituents.

Additional frozen context:

- hard→fused: **11 gained, 4 lost** labels at top 100;
- local→fused: **7 gained, 4 lost** labels at top 100;
- among fused misses, local first rank is better than hard for **11**, worse for **18**, equal for **0**;
- median `(local first rank - hard first rank)` among fused misses = **+36**.

### Top 50

Fused misses 54 labels:

- constituent absent = **44 / 54 = 81.4815%**;
- constituent available = **10 / 54 = 18.5185%**.

### Top 25

Fused misses 72 labels:

- constituent absent = **62 / 72 = 86.1111%**;
- constituent available = **10 / 72 = 13.8889%**.

## Scientific interpretation

The diagnostic does **not** evaluate an alternative rank or estimate an achievable oracle score. Its allowed conclusion is narrower:

> For most qualified labels still missed by v31 at each fixed budget—and especially 21 of the 29 top-100 misses—neither frozen constituent already places the label inside that same budget. Therefore equal hard/local fusion is not the dominant remaining bottleneck. Improving fusion alone cannot address the majority of current misses by merely preserving an already-in-budget constituent placement.

The existing equal fusion is also empirically useful on the frozen parent: it raises top-100 label recovery from hard **59** and local **63** to fused **66**, while raising top-100 dominant precision above both constituents.

This result therefore redirects mechanism research toward improving the **constituent scoring/representation** while preserving v31's demonstrated transfer behavior, rather than launching another rank-fusion variant.

## Governance

This diagnostic authorizes no hard/local weight search, RRF constant, confidence function, best-rank/min-rank fusion, budget-specific combiner, or other fusion rescue.

It also does not select a particular new local scorer or representation. Any successor still requires independent mechanism justification and freezing before its first technically valid outcome.

## Firewall

No SonotaCo 2013/2014 scientific data was accessed. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN events, raw event IDs, or hidden event-label mapping were accessed. No new scientific rank was evaluated and no successor was selected by this diagnostic.
