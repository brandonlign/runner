# Rank-density fixed-graph topomodal v1 — binding result

## Verdict

🔴 **FAIL_RANKDENSITY_TOPOMODAL_V1 — CLOSED.**

Binding evaluator-only repair workflow run: `31968559582`

Binding job: `95217343860`

Binding repair artifact: `9269180387` (`orbittrace-rankdensity-topomodal-v1-evaluator-repair`)

Repair artifact ZIP digest:

`sha256:84a00f1a904430ab8a241fce98a6048c461b3696a4940c5d95cd94253eab92d1`

Immutable prelabel source artifact: `9269121527`

Immutable prelabel SHA-256:

`b6bf31e9add2b9c2e220ccb91d0778859abe86505731d6a0f071ed9eb7c13533`

Run `31968130661` sealed this prelabel and then suffered only an external GMN HTTP disconnect before any complete truth metric/result. Evaluator repair run `31968559582` downloaded and verified that exact prelabel, invoked the original evaluator source blob `b6f25f04e6e81b874ff02b9d89eac96708fa6d34` without candidate generation, loaded the full unchanged target-excluded GMN catalogue successfully, and enforced the original 12-gate contract. This is therefore the first technically valid truth outcome and is binding.

## Structural generalization result

The survey-relative support-4 GEO6 density-rank field on the fixed #1284 physical graph remains strongly sample-size coherent:

- successor pooled fine→coarse mean-best-Jaccard: **0.8009311013016914**
- recurrent-EOM: `0.6152941107471891`
- strict bucket wins: **4/4**

Bucket fine→coarse mean-best-Jaccard:

- bucket 0: **0.9072807791613556** vs recurrent `0.5606150793650793`
- bucket 1: **0.7330207002300025** vs `0.7051527695218045`
- bucket 2: **0.7469841269841270** vs `0.5504804710843509`
- bucket 3: **0.8285317304179198** vs `0.6571853102095039`

Both predeclared structural generalization gates pass.

## Sparse truth result

### Fine sparse scale — denominator 1024 (~0.7k pooled events)

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

### Coarse sparse scale — denominator 128 (~5.8k pooled events)

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

Passed 10/12:

- both structural generalization gates;
- fine qualified total strictly greater;
- fine qualified nonlower in >=6/8 panels;
- fine precision not lower;
- fine fragmentation not higher;
- coarse qualified total not lower;
- coarse qualified nonlower in >=6/8 panels;
- coarse precision not lower;
- coarse fragmentation not higher.

Failed only:

- **fine mean MRR not lower**;
- **coarse mean MRR not lower**.

Because all 12 gates were mandatory, the binding verdict is FAIL.

## Scientific interpretation

This is a strong mechanistic result despite the negative promotion verdict. Replacing #1284's absolute radius-count density with a survey-relative third-neighbor empirical density rank preserves the same broad sample-size stability, sparse recovery advantage, purity advantage, and low fragmentation. Therefore the unresolved failure is not absolute-density scale drift and not candidate availability. It is the complete ToMATo hierarchy's **early extraction/prioritization semantics**: the relevant stream families are present, but the intrinsic prominence ranking does not surface their correct hierarchy levels early enough.

This exact architecture is permanently closed. Do not rescue it by changing k, empirical-rank convention, graph radius, physical bandwidth, support floor, prominence-span formula, root handling, tie rules, ranking blends, recurrence bonuses, or gate thresholds.

The next architecture must change candidate extraction itself rather than rerank this exact complete hierarchy.

## Conditional SonotaCo transfer

The pre-frozen SonotaCo transfer protocol was not executed because GMN did not pass all mandatory gates.

## Firewall

The inclusive protected solar-longitude interval `[20.0,55.0]` remained excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, AMOS scientific data, MAARSY, or DMS entered the GMN experiment.