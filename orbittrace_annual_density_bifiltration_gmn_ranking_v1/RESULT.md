# Annual-density bifiltration v1 — binding target-excluded GMN ranking/recovery result

## Verdict

🔴 **`FAIL_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY` — CLOSED.**

The first technically valid execution completed after the pre-frozen identity-only evaluator repair. The original frozen persistence-area-ranked bifiltration catalogue therefore now has a binding scientific outcome. Per the original protocol, this exact lane is permanently closed; no alternate ranking, pruning, Pareto layer, score blend, threshold grid, quota, support rule, or post-result rescue is authorized.

## Binding provenance

- original scientific execution commit before repair: `3c309c83186894e4acd63b55b18249476dbffd5c`
- original technical no-result run: `32037435314`
- original successful prelabel artifact: `9291169452`
- original prelabel artifact digest: `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`
- exact original prelabel JSON SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`
- frozen bifiltration candidate-source SHA-256: `63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`
- frozen structural-result SHA-256: `d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7`
- repair protocol record blob: `57f5db7f3849b8ab53cffe0d93d534a30ca05786`
- identity-only repair evaluator blob: `7a7364c2e6a5d361e1906783bfc4780a6e7b0933`
- binding repaired execution head: `92a766b69fad81de86f4d41e2ef36f0d5cd23a18`
- binding workflow run: `32079117460`
- binding job: `95538412311`
- result artifact: `9304552510`
- result artifact digest: `sha256:ac5a3a4c25f686c998b964a82eab57d7ade3a36776a385474c5b938b35d2a89e`
- binding result JSON SHA-256: `80e455afbfcada868031fe5b5a37e620b358af1536c0170281bce6c2e891c4e8`

The repaired run downloaded and hash-verified the exact original successful prelabel artifact; it did not regenerate or reorder candidates. The sole adapter added `family_id = 'BIF/' + family_hash` in memory because the generic evaluator required that inert identity field. The evaluator's truth logic uses only `event_ids`; no scientific quantity depends on `family_id`.

## Binding aggregate result

### Fine sparse scale — denominator 1024

| Metric | recurrent-EOM | bifiltration equal-budget |
|---|---:|---:|
| qualified total | **20** | 12 |
| recovered @25 | **20** | 12 |
| recovered @50 | **20** | 12 |
| recovered @100 | **20** | 12 |
| recovered @500 | **20** | 12 |
| mean MRR | 0.6959325396825397 | **0.8229166666666666** |
| mean top-100 dominant precision | 0.3530315709574533 | **0.9675401881654546** |
| mean fragmentation | **1.0** | 4.1875 |

Panelwise qualified recovery:

- nonlower: **2/8**
- strict wins: **1/8**
- losses: **6/8**

### Coarse sparse scale — denominator 128

| Metric | recurrent-EOM | bifiltration equal-budget |
|---|---:|---:|
| qualified total | **94** | 16 |
| recovered @25 | **87** | 12 |
| recovered @50 | **94** | 16 |
| recovered @100 | **94** | 16 |
| recovered @500 | **94** | 16 |
| mean MRR | 0.23584530975502274 | **0.5272225128523083** |
| mean top-100 dominant precision | 0.3396191653933494 | **0.9454592039316351** |
| mean fragmentation | **1.0** | 16.8125 |

Panelwise qualified recovery:

- nonlower: **0/8**
- strict wins: **0/8**
- losses: **8/8**

## Frozen gates

PASS:

- fine MRR mean not lower;
- fine precision mean not lower;
- coarse MRR mean not lower;
- coarse precision mean not lower.

FAIL:

- fine qualified total strictly greater;
- fine qualified nonlower in at least 6/8 annual panels;
- fine fragmentation mean not higher;
- coarse qualified total not lower;
- coarse qualified nonlower in at least 6/8 annual panels;
- coarse fragmentation mean not higher.

Thus **4/10** mandatory gates pass.

## Scientific interpretation

This failure is mechanistically different from the preceding fixed-scale TopoModal scalar-ranking failures.

The bifiltration persistence-area order is extremely good at putting the few known streams it represents near the front and at producing very pure candidate memberships. That is why both MRR and dominant precision rise dramatically. But it spends the equal-budget catalogue on many repeated/nested representations of a small number of streams rather than covering distinct showers. The consequence is severe redundancy: mean fragmentation rises from `1.0` to `4.1875` at fine scale and to `16.8125` at coarse scale, while qualified coverage collapses from `20 -> 12` and `94 -> 16`.

Therefore the positive zero-label cross-scale bifiltration coherence result remains valid, but **persistence area is not a viable flat-catalogue selection/ranking statistic**. Its apparent MRR advantage is conditional on the much smaller set of represented showers and cannot compensate for the lost catalogue coverage.

This result also clarifies the broader bottleneck. The project has now observed both extremes:

- complete/high-coverage TopoModal catalogues recover many distinct streams but surface first representatives too late;
- persistence-area bifiltration surfaces a few very clean streams very early but repeatedly represents them and destroys distinct-stream coverage.

A future successor, if one exists, must address **set-level allocation across latent stream identities without using truth labels**. It cannot be a tuned rerank of this bifiltration result or a return to previously closed overlap/union/lineage/Pareto/antichain rescues.

## Firewall

Throughout the binding run:

- protected inclusive solar longitude `[20.0,55.0]` remained excluded;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- SonotaCo 2013/2014 was not accessed;
- ASFN/EFN event-level data was not accessed;
- AMOS, MAARSY, and DMS scientific data were not accessed;
- `post_result_parameter_search = false`.
