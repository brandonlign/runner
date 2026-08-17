# OrbitTrace support-cut × bifiltration internal-mass v1 — binding GMN result

## Verdict

`FAIL_SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_GMN`

This is a technically valid binding scientific result under the frozen ten-gate protocol. The exact internal-mass candidate prelabel, order, recurrent budgets, metrics, and gates were frozen before this truth endpoint.

## Binding provenance

- Zero-label structural source run: `32041661731`
- Sealed ranked prelabel artifact: `9292071213`
- Sealed ranked prelabel SHA-256: `7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`
- Truth workflow run: `32041815772`
- First attempt: job `95422350422`, technical GMN HTTPS timeout before result; no metric/verdict emitted.
- Binding valid attempt: attempt 2, job `95423297816`
- Execution commit: `a6d517be194b1a698fb55172b1a9cb1462d96307`
- Binding result artifact: `9292172801`
- Artifact digest: `sha256:73ad350c091ad1f5490210718fcca677310633d9242832437e53ff6925996c52`
- Result JSON SHA-256: `bf34d0e46e7c17b95545923a3d77d67a8ae866e4f34eca0946ca4e7b5736a56b`

The binding attempt reproduced every frozen source/artifact check, parsed all target-excluded GMN 2022/2023 monthly catalogues, evaluated all 16 annual panels, enforced the firewall and verdict, and uploaded the result successfully.

## Fine scale d=1024

Recurrent-EOM at equal budget:
- qualified total: `20`
- recovered@25/@50/@100/@500: `20 / 20 / 20 / 20`
- mean MRR: `0.6959325396825397`
- mean top-100 dominant precision: `0.3530315709574533`
- mean fragmentation: `1.0`

Internal-mass successor at equal budget:
- qualified total: **`31`**
- recovered@25/@50/@100/@500: **`31 / 31 / 31 / 31`**
- mean MRR: `0.5412847222222222`
- mean top-100 dominant precision: **`0.597104767917268`**
- mean fragmentation: `1.0`
- qualified recovery nonlower: **8/8 annual panels**
- strict recovery wins: **6/8 annual panels**

## Coarse scale d=128

Recurrent-EOM at equal budget:
- qualified total: `94`
- recovered@25/@50/@100/@500: `87 / 94 / 94 / 94`
- mean MRR: `0.23584530975502274`
- mean top-100 dominant precision: `0.3396191653933494`
- mean fragmentation: `1.0`

Internal-mass successor at equal budget:
- qualified total: **`126`**
- recovered@25/@50/@100/@500: **`114 / 126 / 126 / 126`**
- mean MRR: `0.20252514798619423`
- mean top-100 dominant precision: **`0.5455715543235427`**
- mean fragmentation: `1.0`
- qualified recovery nonlower: **8/8 annual panels**
- strict recovery wins: **8/8 annual panels**

## Gate result

Passed 8/10:
- fine qualified total strictly greater
- fine qualified nonlower >=6/8
- fine precision nonlower
- fine fragmentation nonhigher
- coarse qualified total nonlower
- coarse qualified nonlower >=6/8
- coarse precision nonlower
- coarse fragmentation nonhigher

Failed exactly 2/10:
- fine mean MRR nonlower (`0.54128 < 0.69593`)
- coarse mean MRR nonlower (`0.20253 < 0.23585`)

## Interpretation

The result strongly validates the **support-resolved candidate architecture**: at equal catalogue budget it finds many more known showers, materially improves purity, never loses a recovery panel, and retains fragmentation `1.0`. However the frozen internal two-density persistence-mass order does not put the first correct representation of each shower early enough, so it fails the preregistered promotion contract.

This failure replicates the central MRR bottleneck seen with recurrent-density TopoModal using a scientifically distinct recurrence signal. It therefore argues against further single-candidate recurrence-score engineering on this candidate set.

## Closure

Internal-mass v1 is closed. Do not rescue it with area/support transforms, ancestor evidence, max-component evidence, modal-contrast blends, alternative tie ordering, positive-score filtering, quotas, budget/gate changes, or sibling score formulas.

Any next successor must be a **distinct catalogue architecture**, not another scalar ranker over the same support-cut candidates. In particular, a justified next mechanism would need to preserve the support-cut recovery/purity advantage while structurally protecting the early-order strength of recurrent-EOM. SonotaCo and all protected/external data remain untouched by this endpoint.