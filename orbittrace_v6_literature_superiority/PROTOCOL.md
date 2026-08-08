# OrbitTrace v6 literature-superiority adjudication — frozen protocol

## Status and activation

This is a comparison/claim protocol only, frozen before the repaired v3-primary catalogue-v6 development result is known. It activates only if the exact preregistered repaired v6 run returns `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`. A development failure leaves it dormant and authorizes no rescue, retuning, or benchmark-driven modification.

No target-containing scan is authorized here. Solar longitude 20°–55° remains excluded before scientific evaluation.

## Method under test

The candidate is the exact v3-primary dual-output catalogue-v6 architecture frozen in PR #221, with only the source-audited two-line component-construction repair established by PR #490. No score, proposal rule, calibration rule, membership definition, component algorithm, recurrence rule, ranking rule, or gate may change from any later result.

Fixed4 is a separate rescue channel and may not satisfy a v3-primary superiority gate.

## Comparator boundary

Use only already-frozen literature implementations/results/parameters.

### Catalogue comparators

1. **Sugar et al. uncertainty-aware catalogue reconstruction**
   - frozen 1,000-clone implementation;
   - `min_samples=5`;
   - frozen 2025 epsilon `0.028705145052265017`, transferred unchanged to 2023;
   - retained-master `>=100/1000` assignment is the primary Sugar output;
   - deterministic DBSCAN and `>=500/1000` outputs remain diagnostics.

2. **Peña-Asensio–Ferrari catalogue HDBSCAN transfer**
   - published unstandardized GEO six-vector;
   - `hdbscan==0.8.44`;
   - `min_cluster_size=100`, default `min_samples`, Euclidean metric, `eom` selection;
   - exact frozen quality/matching rules.

3. **Promoted OrbitTrace v8**
   - exact promoted source/ranking;
   - internal predecessor for ranked-discovery metrics only.

### Not catalogue-superiority comparators

Brown-family/CMOR wavelet remains an episode/survey-wavelet comparator unless a faithful catalogue interface is independently justified. Southworth–Hawkins and D_N remain targeted/episode comparators. The deferred CMOR catalogue transfer remains deferred; its support rules may not be weakened to create a convenient comparison.

## Benchmark corpora

### Matched literature benchmark

Use SonotaCo **2025 and 2023**, where frozen full Sugar and HDBSCAN outputs already exist. This is a matched comparison panel, not fresh external validation, because the underlying v3 episode score has prior SonotaCo history.

The exact-row universes for Sugar and HDBSCAN are different. Therefore **no F1 value from the Sugar universe may be directly compared to an HDBSCAN F1 value**. Every v6-vs-literature statement is pairwise on the exact event/reference universe frozen by that comparator's assignments.

For each comparator/year, report the common-universe size and evaluate v6 and that comparator on identical rows and identical post-freeze truth. Never select the more favorable comparator denominator after seeing results.

### External generalization

The earlier proposed CAMSv3 2017/2018 route is invalid: the official CAMSv3 catalogue ends at 2016, so those intended files do not exist. No CAMSv3 2017/2018 result may be used as a validation claim.

A stronger genuinely pristine external panel may be added only under a separately frozen protocol if one becomes available. In the current repository, PR #494 instead freezes a weaker but legitimate **architecture-pre-frozen, no-retuning SonotaCo 2017/2019 transfer**. Those raw archives are not pristine, but catalogue-v6 was frozen before the later score-label attempt and that attempt produced no catalogue ranking/scientific result. A PR #494 pass can therefore support prospective generalization of this fixed architecture, but must not be described as never-seen/pristine validation.

## Metrics

### Catalogue membership / population

On each exact pairwise common universe report:

- per-shower F1 under the frozen best-match/tie rules;
- macro F1;
- F1 > 0.5 and F1 > 0.8 counts/fractions;
- noise/unassigned burden where directly comparable;
- annual mean F1 in `4–9`, `10–24`, `25–49`, `50–99`, and `100+` reference-member strata.

NMI/ARI are diagnostics only when both outputs are genuine comparable partitions of the same rows.

### Ranked discovery

Only compare methods with a frozen meaningful ranking. Against promoted v8 report recovery@25/@50/@100, MRR, top-25/top-50/top-100 dominant-label precision, and qualified matches. Do not invent a ranking for Sugar or HDBSCAN.

## Frozen superiority classifications

Every required annual condition must hold in **both 2025 and 2023**. A tie is not a win.

### A. `BROAD_CATALOGUE_SUPERIORITY`

This is the only matched-benchmark outcome authorizing the broad statement that v6 beat both implemented established catalogue methods.

The following conditions must hold **separately against Sugar on the Sugar exact-row universe and against HDBSCAN on the HDBSCAN exact-row universe**:

1. v6 macro F1 >= comparator macro F1 **+0.05 absolute** in both years;
2. v6 is not below the comparator by >**0.05 absolute mean F1** in any of the five size strata in either year;
3. v6 exceeds the comparator by >=**0.10 absolute mean F1** in at least two size strata in each year;
4. v6 has at least as many eligible showers with F1 >0.5 as the comparator in each year;
5. all source/common-universe/integrity gates pass.

No cross-comparator denominator mixing is allowed.

### B. `SPARSE_STREAM_SUPERIORITY`

This authorizes only a scoped claim of superiority for sparse/small optical populations.

Separately against both Sugar and HDBSCAN on their exact pairwise universes:

1. `4–9` v6 mean F1 >= comparator +**0.10** in both years;
2. combined `4–24` v6 mean F1 >= comparator +**0.10** in both years;
3. v6 macro F1 is no more than **0.10 absolute below that same comparator** in either year;
4. v6 retains at least **80%** of that comparator's F1>0.5 shower count in either year;
5. all integrity/common-universe gates pass.

Any large-shower disadvantage must be stated explicitly.

### C. `IMPROVED_INTERNAL_DISCOVERY_ONLY`

This does not mean v6 beat the literature. It can justify replacing v8 internally only if all non-regression gates hold on the same frozen target-excluded evaluation:

- recovery@100 >= v8;
- MRR >= v8;
- top-100 dominant precision >= v8 minus 0.02 absolute;
- qualified matches >= v8;

and at least one **material** ranked-discovery improvement occurs under this now-frozen rule:

- recovery@25 >= v8 +3 recovered showers; or
- recovery@50 >= v8 +4; or
- recovery@100 >= v8 +5; or
- MRR >= max(v8 MRR +0.005 absolute, 1.10 × v8 MRR).

These thresholds are frozen before the v6 literature/ranking comparison result and cannot be relaxed afterward.

### D. `NO_SUPERIORITY`

If none of A–C passes, v6 must not be described as beating the literature or replacing v8. Preserve it and move to a genuinely new architecture/fresh development panel rather than tuning the exposed result.

## OrbitTrace authorization boundary

A target-containing blind OrbitTrace deployment is authorized only after all of the following are completed without method retuning:

1. exact repaired v6 target-excluded development passes its original gates;
2. this matched literature adjudication completes;
3. v6 achieves at least `SPARSE_STREAM_SUPERIORITY` (or `BROAD_CATALOGUE_SUPERIORITY`);
4. the architecture-pre-frozen SonotaCo 2017/2019 transfer in PR #494 passes, **or** a separately frozen stronger genuinely pristine external validation passes;
5. a final target-deployment protocol freezes the target success threshold, complete ranking output, reveal procedure, and claim boundary before restoring 20°–55°.

If authorization relies on PR #494 rather than a pristine panel, the eventual claim must say **pre-frozen no-retuning external transfer**, not pristine prospective validation.

Historical v8 partial OrbitTrace recovery at rank 59/780 is evidence only and may not choose any v6 parameter, gate, adapter choice, ranking term, or final success cutoff.

## Claim discipline

Even a successful final target deployment would establish a prospective blinded recovery/rediscovery by the frozen successor method. It does not rewrite the historical fact that the original OrbitTrace candidate came from the earlier blind HDBSCAN search, and it does not establish universal superiority across incompatible radar/optical survey regimes.