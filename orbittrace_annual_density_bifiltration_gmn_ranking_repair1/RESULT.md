# OrbitTrace annual-density bifiltration GMN ranking v1 — binding repair1 result

## Verdict

`FAIL_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY`

This is the binding continuation of the frozen GMN truth endpoint. The only post-truth repair was the deterministic interface alias `family_id = "BIF1_" + family_hash`; candidate memberships, persistence-area ordering, budgets, truth, metrics, and gates were unchanged.

## Binding provenance

- Original immutable prelabel artifact: `9291169452`
- Original prelabel SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`
- Repair workflow run: `32040061408`
- Successful attempt/job: attempt 3, job `95418070832`
- Execution commit: `424be5d0bcde7e9fbe9e08c226af618b4dec8d8f`
- Result artifact: `9291858608`
- Artifact digest: `sha256:566424b3a44ce4e192acae8fac010d61a7af5d9cca156d01fb2b91204bc7dfdf`
- Result JSON SHA-256: `67c62ea5562ca53c84a49fcd93df3cf94bd0a940ce794569c66f03e643e24c58`

The first two repair attempts failed only while downloading old frozen support artifacts; neither reached evaluation. Attempt 3 downloaded and verified all frozen inputs, evaluated the unchanged candidate order, enforced the firewall, and uploaded the binding result.

## Scale aggregates

### Fine scale d=1024

Recurrent-EOM:
- qualified total: 20
- recovered@25/@50/@100/@500: 20 / 20 / 20 / 20
- mean MRR: 0.6959325396825397
- mean top-100 dominant precision: 0.3530315709574533
- mean fragmentation: 1.0

Bifiltration persistence-area ordering, equal budget:
- qualified total: 12
- recovered@25/@50/@100/@500: 12 / 12 / 12 / 12
- mean MRR: 0.8229166666666666
- mean top-100 dominant precision: 0.9675401881654546
- mean fragmentation: 4.1875
- qualified nonlower panels: 2/8
- strict-win panels: 1/8

### Coarse scale d=128

Recurrent-EOM:
- qualified total: 94
- recovered@25/@50/@100/@500: 87 / 94 / 94 / 94
- mean MRR: 0.23584530975502274
- mean top-100 dominant precision: 0.3396191653933494
- mean fragmentation: 1.0

Bifiltration persistence-area ordering, equal budget:
- qualified total: 16
- recovered@25/@50/@100/@500: 12 / 16 / 16 / 16
- mean MRR: 0.5272225128523083
- mean top-100 dominant precision: 0.9454592039316351
- mean fragmentation: 16.8125
- qualified nonlower panels: 0/8
- strict-win panels: 0/8

## Gate result

Passed only:
- coarse MRR nonlower
- coarse precision nonlower
- fine MRR nonlower
- fine precision nonlower

Failed:
- coarse fragmentation nonhigher
- coarse qualified nonlower-panel gate
- coarse qualified-total nonlower
- fine fragmentation nonhigher
- fine qualified nonlower-panel gate
- fine qualified-total strict improvement

## Interpretation and closure

The two-density bifiltration generator remains structurally promising, but persistence area is not an acceptable catalogue selector. Its early candidates are exceptionally pure and, for represented showers, early-ranked; however the list is dominated by redundant/nested fragments of too few physical showers. That produces severe coverage loss and fragmentation despite improved MRR/precision.

Therefore **persistence-area scalar ranking is closed**. No persistence-area exponent, support multiplier, blend, alternative tie-break, route-specific rule, budget exception, or score rescue is authorized from this outcome.

Any successor must retain the frozen candidate generator unless separately preregistered, and must attack redundancy at the structural selection level rather than rescore individual candidates. A new successor requires a distinct mechanism and a zero-label structural gate before any further GMN truth evaluation. SonotaCo and protected/external data remain untouched by this endpoint.