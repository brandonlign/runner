# OrbitTrace TopoModal development freeze v1

## Decision

**FREEZE_GMN_2022_2023_TOPOMODAL_METHOD_DEVELOPMENT_V1**

No further TopoModal selection/ranking architecture is authorized on the exposed target-excluded GMN 2022+2023 development corpus.

This freeze distinguishes two scientifically different conclusions that must not be conflated.

### 1. Candidate-construction conclusion — positive

The fixed-scale #1284 TopoModal hierarchy is the strongest demonstrated novel candidate-construction architecture for the original recovery/generalization objective.

Frozen geometry/topology:

- Sun-centered six-dimensional physical embedding;
- solar-longitude chord scale 5°;
- radiant chord scale 4°;
- log-speed scale `ln(1.1)`;
- exact Euclidean radius-1 graph;
- density `rho_i = |N_i|/n`;
- GUDHI 3.12 manual-graph/manual-density ToMATo hierarchy;
- reportable membership support >=4.

Authoritative #1284 structural result:

- source/result lineage: `agent/orbittrace-topomodal-hierarchy-scale-v1`;
- structural run `31955621864`;
- artifact `9265889512`;
- structural result SHA-256 `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`;
- pooled fine→coarse best-Jaccard approximately `0.8067`, compared with recurrent-EOM approximately `0.6153`;
- strict cross-scale wins in all 4/4 deterministic thinning buckets.

Authoritative sparse-recovery result for the exact #1284 candidate universe and its original intrinsic order:

- branch `agent/orbittrace-topomodal-sparse-recovery-v1`;
- run `31959926804`;
- artifact `9266993487`;
- immutable prelabel SHA-256 `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`.

Fine sparse scale (~677–766 pooled events):

- qualified recovery: recurrent-EOM `20`, TopoModal `31`;
- recovered @25: `20` → `31`;
- mean top-100 dominant precision: `0.3530315709574533` → `0.5886672679172679`;
- mean fragmentation: `1.0` → `1.0`;
- qualified recovery nonlower in 8/8 annual panels, strict win in 6/8.

Coarse sparse scale (~5,567–5,857 pooled events):

- qualified recovery: recurrent-EOM `94`, TopoModal `140`;
- recovered @25: `87` → `129`;
- mean top-100 dominant precision: `0.3396191653933494` → `0.5543714415470113`;
- mean fragmentation: `1.0` → `1.0`;
- qualified recovery nonlower in 8/8 annual panels, strict win in 8/8.

Therefore the candidate generator materially improves known-stream coverage and purity while remaining effective across approximately an eightfold sample-size change. That is a real positive methodological result and may be reported as such.

### 2. Ranked-detector promotion conclusion — negative

The exact #1284 intrinsic ranked successor did **not** satisfy its frozen all-ten-gate promotion contract because mean MRR regressed at both sparse scales:

- fine MRR: recurrent-EOM `0.6959325396825397`, TopoModal `0.5404513888888889`;
- coarse MRR: recurrent-EOM `0.23584530975502274`, TopoModal `0.18702656347669294`.

The exact successor verdict remains `FAIL_TOPOMODAL_SPARSE_RECOVERY_V1` and must not be rewritten as a PASS by changing or deleting the MRR gates after outcome.

Accordingly:

- recurrent-EOM remains the promoted ranked detector under the strict existing all-gate contract;
- #1284 is frozen as the successful novel **candidate-construction / sparse-recovery architecture**, not as an all-metrics promoted replacement for recurrent-EOM;
- no full-GMN, SonotaCo-final, external-validation, or protected-target access is authorized merely by this development freeze.

## Why development stops here

After #1284 established the recovery/generalization gain, a large set of independently frozen attempts targeted the remaining canonical-selection/MRR problem. None produced an all-gate successor.

Binding or pretruth-closed families include, among others:

- support-resolved non-overlapping cut;
- lineage/interleaving variants;
- recurrent-density TopoModal;
- bivariate annual-density topology;
- map-equation candidate ranking;
- rank-density TopoModal;
- significance-pruned TopoModal;
- Bayesian planted-partition/PPMDL graph partitioning;
- relative-neighborhood-graph ToMATo;
- station-support-weighted TopoModal;
- orbital Southworth–Hawkins Fréchet ordering;
- independent annual TopoModal confirmation;
- HDBSCAN-style density-level excess-mass/EOM selection, which is technically invalid on the exact ToMATo hierarchy before truth;
- earlier generic subsample-stability ranking evidence, which had binding verdict `FAIL_SUBSAMPLE_STABILITY_RANKING_FEATURE` and worsened early recovery/MRR despite a later-rank gain.

The repeated pattern is now sufficiently established: the #1284 hierarchy contains substantially more useful stream-bearing candidates than recurrent-EOM, but the exposed GMN 2022+2023 development corpus has not yielded a preregistered, label-free canonical ordering that also matches recurrent-EOM's first-hit MRR.

Continuing to invent ranking features on the same truth-exposed development corpus would increase researcher degrees of freedom and weaken, rather than strengthen, the scientific claim.

## No-more-variants rule

From this commit forward, do not create another GMN-2022/2023 TopoModal ranking/selection successor by:

- changing hierarchy rank scores;
- combining previously failed evidence terms;
- changing root treatment;
- changing support/radius/density/physical scales;
- adding persistence/prominence thresholds;
- introducing another annual/station/orbital/activity/background/coherence feature;
- adding bootstrap/subsample stability as a ranking feature;
- redefining the promotion gates after seeing existing outcomes;
- repackaging a closed lane under a new name.

An implementation-only repair of a frozen result record is allowed. New scientific development is not.

## What would legitimately reopen method development

Only a genuinely new experimental design may reopen ranking-method research, for example a newly preregistered independent development corpus or a fundamentally new benchmark whose objective is fixed before its labels are accessed. Existing GMN 2022+2023 truth outcomes may be used only as historical evidence, not to tune that future method.

## Next authorized work

The methodology-search phase is complete. Authorized next work is synthesis and engineering, not another detector variant:

1. package the exact #1284 candidate generator and reproduce its structural/recovery artifacts from frozen sources;
2. document computational scaling limits and design an exact or provably equivalent implementation path without changing scientific semantics;
3. synthesize the positive recovery/generalization result and the negative MRR/canonicalization result for the paper;
4. keep recurrent-EOM as the promoted ranked control unless a future independently preregistered development program establishes a replacement;
5. maintain the 20°–55° target firewall and all existing external-data role restrictions.

## Claim boundary

Supported claim:

> A fixed-scale physical-graph ToMATo hierarchy substantially increases sparse known-stream candidate recovery and purity relative to recurrent-EOM and remains structurally coherent under an approximately eightfold sample-size change.

Not supported claim:

> The current TopoModal ordering is uniformly superior to recurrent-EOM as a ranked detector.

The second claim must not be made unless new independent evidence establishes it under a prospectively frozen protocol.

## Firewall

- protected solar longitude 20°–55° remains inaccessible;
- OrbitTrace target information/events remain inaccessible;
- no new SonotaCo 2013/2014 scientific access is authorized;
- no MAARSY or DMS scientific access is authorized;
- failures and technical-invalidity records remain permanent.
