# OrbitTrace v6 literature-superiority adjudication — frozen protocol

## Status and activation

This is a comparison/claim protocol only. It is frozen before the repaired v3-primary catalogue v6 development result is known.

It becomes scientifically active only if the exact preregistered v6 development run returns `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`. A development failure leaves this protocol dormant and authorizes no rescue, retuning, or benchmark-driven modification of v6.

This protocol does not access or authorize any OrbitTrace target-containing scan. Solar longitude 20°–55° remains excluded before label access in every matched benchmark.

## Method under test

The candidate is the exact frozen v3-primary dual-output catalogue v6 architecture from PR #221, with only the source-audited implementation repair established in PR #490: the two missing calls to the already-frozen `component_records_track_v6` function. No scientific parameter, proposal rule, calibration rule, membership definition, component algorithm, recurrence rule, ranking rule, or gate may change after the development result.

The fixed4 rescue channel is not part of the v3 primary ranking and cannot be used to satisfy a primary superiority gate.

## Comparator boundary

Use only already-frozen literature implementations and results/parameters. No comparator parameter may be changed after seeing v6 output.

### Catalogue comparators

1. **Sugar et al. uncertainty-aware catalogue reconstruction**
   - exact already-frozen 1,000-clone implementation;
   - `min_samples=5`;
   - frozen 2025 epsilon `0.028705145052265017` transferred unchanged to 2023;
   - retained-master `>=100/1000` recurrence assignment is the primary Sugar catalogue output;
   - deterministic DBSCAN and `>=500/1000` strong-master outputs remain diagnostics, not replacement baselines.

2. **Peña-Asensio–Ferrari catalogue HDBSCAN transfer**
   - published unstandardized GEO six-vector;
   - `hdbscan==0.8.44`;
   - `min_cluster_size=100`, default `min_samples`, Euclidean metric, `eom` selection;
   - exact already-frozen quality filters and matching rules.

3. **Promoted OrbitTrace v8**
   - exact promoted v8 source and ranking;
   - acts as the internal predecessor for ranked-discovery metrics.

### Not catalogue-superiority comparators

- Brown-family/CMOR wavelet remains an episode or survey-wavelet comparator unless a faithful matched catalogue interface is independently justified before execution.
- Southworth–Hawkins and D_N linkage remain targeted/episode comparators, not invented full-catalogue algorithms.
- The deferred CMOR-style catalogue transfer remains deferred under its existing support audit and cannot be weakened to create a convenient comparator.

## Benchmark corpora

### Matched literature benchmark

Use **SonotaCo 2025 and SonotaCo 2023**, because the full frozen Sugar and HDBSCAN comparators already exist there. This is a matched comparison panel, **not fresh external validation**: the underlying v3 episode score has prior SonotaCo development/transfer history.

The v6 transport must be frozen before its first catalogue-scale SonotaCo execution. It may change parser/field plumbing only. Scientific v6 rules are immutable.

For every annual comparison, evaluate only an explicitly frozen common event/reference universe supported by both v6 and the comparator being compared. Report both the common-universe size and any exclusions. Never compare F1 values computed on different event universes as if they were head-to-head.

### Fresh external validation

Literature benchmarking does not authorize OrbitTrace deployment. A separately preregistered scientifically fresh external validation remains required after any successful literature adjudication. CAMSv3 2017/2018 is currently repository-history clean for scientific-value exposure and may be used only under a separately frozen compatible validation protocol. Its lack of a trustworthy native shower-label field means it must not be forced into a label-F1 benchmark; recurrence/coherence endpoints require their own predeclared gates.

## Metrics

### Catalogue membership / population metrics

On exact common rows and common eligible reference showers, report:

- Hungarian-matched per-shower F1;
- macro F1;
- number and fraction of eligible showers with F1 > 0.5;
- number and fraction with F1 > 0.8;
- noise/unassigned fraction where the output semantics permit a direct comparison;
- annual size-stratum mean F1 for `4–9`, `10–24`, `25–49`, `50–99`, and `100+` reference members.

NMI/ARI may be reported only when the two outputs form genuinely comparable partitions on the exact same event universe. They are diagnostics otherwise and cannot determine superiority.

### Ranked discovery metrics

Only compare methods that have a frozen, scientifically meaningful ranking. Against promoted v8, report:

- recovery@25, @50, @100;
- MRR over qualified known showers;
- top-25, top-50, and top-100 dominant-label precision;
- qualified known-shower matches.

Do not invent a post-hoc ranking for Sugar or HDBSCAN merely to make them enter a ranked metric.

## Frozen superiority classifications

All required conditions must hold independently in **both 2025 and 2023** unless stated otherwise. A tie within the numerical tolerances below is not a win.

### A. `BROAD_CATALOGUE_SUPERIORITY`

This is the only outcome that authorizes the broad statement that v6 beat the implemented established catalogue methods on the matched benchmark.

Required against the best of the frozen Sugar retained-master and HDBSCAN catalogue outputs on each year/common universe:

1. v6 macro F1 is at least the best comparator macro F1 **plus 0.05 absolute** in both years;
2. v6 is not lower than the best comparator by more than **0.05 absolute mean F1 in any one of the five size strata** in either year;
3. v6 exceeds the best comparator by at least **0.10 absolute mean F1** in at least two size strata in both years;
4. v6 has at least as many eligible showers with F1 > 0.5 as the best comparator in both years;
5. no integrity/common-universe gate fails.

### B. `SPARSE_STREAM_SUPERIORITY`

This authorizes only a scoped claim that v6 is superior for sparse/small optical shower populations, not that it is the best general catalogue method.

Required against both frozen Sugar and HDBSCAN on exact common universes:

1. in `4–9`, v6 mean F1 exceeds each comparator by **>=0.10 absolute** in both years;
2. across the combined `4–24` population, v6 mean F1 exceeds each comparator by **>=0.10 absolute** in both years;
3. v6 macro F1 is no more than **0.10 absolute below** the best catalogue comparator in either year;
4. v6 does not lose more than **20% relative** of the best comparator's count of F1 > 0.5 showers in either year;
5. no integrity/common-universe gate fails.

This classification may coexist with a large-shower disadvantage and must state that limitation explicitly.

### C. `IMPROVED_INTERNAL_DISCOVERY_ONLY`

If v6 does not beat the literature methods under A or B but improves the promoted v8 ranked-discovery layer, it may still replace v8 internally only if all of the following hold on the frozen target-excluded ranked evaluation:

- recovery@100 >= v8;
- MRR >= v8;
- top-100 dominant precision >= v8 minus 0.02 absolute;
- qualified matches >= v8;
- at least one of recovery@25, recovery@50, recovery@100, or MRR improves materially under a threshold frozen before that comparison run.

A separate freeze must define the numeric material-improvement threshold before execution; this document deliberately does not allow selecting it after results.

### D. `NO_SUPERIORITY`

If none of A–C passes, v6 must not be described as beating the literature or replacing v8. Preserve the result and move to a genuinely new architecture/fresh development panel rather than tuning this v6 result.

## OrbitTrace authorization boundary

A successful v6 development result alone is insufficient. A literature benchmark result alone is insufficient.

A new target-containing blind OrbitTrace deployment may be authorized only after:

1. exact repaired v6 development passes its original frozen gates;
2. this literature adjudication is completed without benchmark-driven retuning;
3. the method achieves at least `SPARSE_STREAM_SUPERIORITY` or a separately justified stronger discovery classification frozen before external validation;
4. a scientifically fresh external validation passes its separately frozen gates;
5. the final target-deployment protocol, ranking-success threshold, and reveal procedure are frozen before the 20°–55° target interval is restored.

The previous v8 partial blind recovery at rank 59/780 is historical evidence only. It may not be used to choose any v6 parameter, threshold, ranking term, proposal rule, or success cutoff.

## Claim discipline

Even a successful target deployment would establish a **prospective blinded recovery/rediscovery by the frozen successor method**, not rewrite the historical fact that the original OrbitTrace candidate arose from the earlier blind HDBSCAN search.

No outcome under this protocol licenses the claim that one method is universally best across radar/optical surveys, sparse/dense regimes, or incompatible catalogue interfaces.