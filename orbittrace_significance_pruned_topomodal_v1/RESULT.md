# Significance-pruned fixed-graph topomodal v1 — binding result

## Verdict

🔴 **FAIL_SIGNIFICANCE_PRUNED_TOPOMODAL_V1 — CLOSED.**

Binding workflow run: `31969105299`

Binding job: `95218621783`

Binding artifact: `9269343581` (`orbittrace-significance-pruned-topomodal-v1`)

Binding artifact ZIP digest:

`sha256:64048af08159ca8423834bee9749648abdc133381ec907eb4c00bba31be15925`

Immutable prelabel SHA-256:

`bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a`

The single binding run completed generation, all 1,592 deterministic label-free permutation-null ToMATo fits, independent prelabel seal, unchanged truth evaluation, and the original 13-gate result contract. No repair or second scientific attempt was used.

## Pretruth significance result

The frozen `B=199`, max-finite-prominence, FWER `alpha=0.05` null produced **zero significant finite modes in all eight sparse panels**.

| scale | bucket | tau | significant finite modes | successor candidates | recurrent candidates |
|---|---:|---:|---:|---:|---:|
| d=128 | 0 | 0.9705459770114943 | 0 | 63 | 29 |
| d=128 | 1 | 0.9652456771100839 | 0 | 70 | 35 |
| d=128 | 2 | 0.9829293274155002 | 0 | 68 | 38 |
| d=128 | 3 | 0.9766202509884820 | 0 | 60 | 33 |
| d=1024 | 0 | 0.8952802359882006 | 0 | 9 | 8 |
| d=1024 | 1 | 0.8513513513513514 | 0 | 5 | 5 |
| d=1024 | 2 | 0.8561736770691994 | 0 | 6 | 6 |
| d=1024 | 3 | 0.8187744458930899 | 0 | 9 | 9 |

Thus every finite mode was merged at the preregistered significance threshold. The remaining candidates are broad connected-component/root classes from the fixed physical graph. No discarded hierarchy node was restored.

## Structural generalization

Despite the aggressive finite-mode collapse, the broad/root classes remained more coherent under ~8x thinning than recurrent-EOM:

- successor pooled fine→coarse mean-best-Jaccard: **0.7479501299505501**
- recurrent-EOM: `0.6152941107471891`
- successor strict bucket wins: **4/4**

Bucket fine→coarse successor/recurrent:

- bucket 0: **0.7424099078057744** / `0.5606150793650793`
- bucket 1: **0.8822900136798906** / `0.7051527695218045`
- bucket 2: **0.7129629629629629** / `0.5504804710843509`
- bucket 3: **0.7021818613485280** / `0.6571853102095039`

Both frozen structural gates PASS. Candidate-budget sufficiency also PASSes all panels.

## Sparse truth result

### Fine sparse scale — denominator 1024

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| qualified total | 20 | **31** |
| recovered @25 | 20 | **31** |
| recovered @50 | 20 | **31** |
| recovered @100 | 20 | **31** |
| recovered @500 | 20 | **31** |
| mean dominant precision | 0.3530315709574533 | **0.5886672679172679** |
| mean MRR | **0.6959325396825397** | 0.5388888888888889 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: **8/8 nonlower, 6/8 strict wins, 0 losses**.

### Coarse sparse scale — denominator 128

| Metric | recurrent-EOM | successor |
|---|---:|---:|
| qualified total | 94 | **139** |
| recovered @25 | 87 | **124** |
| recovered @50 | 94 | **139** |
| recovered @100 | 94 | **139** |
| recovered @500 | 94 | **139** |
| mean dominant precision | 0.3396191653933494 | **0.5463968158500625** |
| mean MRR | **0.23584530975502274** | 0.18061023549254926 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: **8/8 nonlower, 8/8 strict wins, 0 losses**.

## Frozen gates

Passed **11/13**:

- candidate budget sufficient in all panels;
- both structural generalization gates;
- all recovery-count gates;
- both precision gates;
- both fragmentation gates.

Failed only:

- **fine mean MRR not lower**;
- **coarse mean MRR not lower**.

Therefore the exact successor fails promotion.

## Scientific interpretation

This result materially narrows the mechanism. Under the exact graph-permutation max-prominence null, no finite q-density mode is statistically exceptional at familywise 0.05 in any sparse panel. Yet after all finite modes are merged, the remaining broad physical connected components still retain the same large recovery/purity advantage and low fragmentation seen in the complete-hierarchy rank-density successor.

Therefore the unresolved MRR problem is **not** solved by finite-mode prominence significance. The high-recovery signal is carried by broad stable physical families/root components, while the correct known streams inside those families need evidence that distinguishes internal stream-like structure without replacing the family by many fragmented threshold-state candidates.

This exact method is permanently closed. Do not rescue by changing `B`, alpha, null target, max-statistic, q permutation scheme, graph scale, k, support floor, root treatment, finite-mode tie rule, or by reintroducing discarded finite hierarchy nodes.

The pre-frozen SonotaCo transfer protocol is not executed because GMN failed the mandatory MRR gates.

## Firewall

The inclusive protected solar-longitude interval `[20.0,55.0]` remained excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, AMOS scientific data, MAARSY, or DMS entered the GMN experiment.