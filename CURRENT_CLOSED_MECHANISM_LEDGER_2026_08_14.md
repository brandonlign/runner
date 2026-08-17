# OrbitTrace current closed-mechanism ledger — 2026-08-15

**Role: evidence/navigation only. No scientific data access, method change, rerun, threshold change, or rescue authorization.**

Purpose: prevent future methodology sessions from rediscovering already-tested mechanisms under new names. This ledger is subordinate to the original frozen protocols/results; if any summary here conflicts with a binding artifact, the binding artifact controls.

## Current full-GMN development champion

**Density-synchronous recurrent-EOM HDBSCAN v1** — PR `#1263` — is the current full-GMN development champion.

Binding target-excluded GMN 2022/2023 run `31852836840`, artifact `9238142199`, digest `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`.

Exact full-data comparison against promoted recurrent-EOM:

- 2022: @50 `45->45`, @100 `89->89`, precision `0.7856486013->0.7873334043`, MRR `0.0224982696->0.0225053732`;
- 2023: @50 `46->46`, @100 `89->90`, precision `0.7867680237->0.7898245986`, MRR `0.0220239289->0.0220302849`;
- fragmentation `1.0->1.0` in both years;
- candidate count `2,097->2,094`.

Exact verdict: `PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT`.

The sole scientific change is the parameter-free density-synchronous node objective

`S_sync(C)=integral min(A_2022^C(lambda),A_2023^C(lambda)) d lambda`

on the same pooled HDBSCAN hierarchy. It rewards annual recurrence at the same density scales rather than merely comparable annual integrated EOM totals.

This is a **development** promotion only, not external validation.

### Robustness limitation — PR #1265

A separately preregistered deterministic 10-fold training-perturbation diagnostic was negative. Binding run `31859724335`, artifact `9240223128`, digest `sha256:75b38fca14d7542f4efa5cb230fa9f2cbb08fead480a80159e8dca50d834e6de`.

Exact verdict: `FAIL_DENSITY_SYNC_GMN_TRAIN_CV_V1`.

Across the 20 year-fold panels:

- total recovered@50 `910->910`;
- total recovered@100 `1761->1761` — no strict improvement;
- mean top-100 precision `0.7781536639->0.7786466016`;
- mean MRR `0.02304596725->0.02308159925`;
- median fragmentation `1.0->1.0`;
- mechanism active in all 10 folds.

Fold 0 improved @100 by +1 in each year, fold 6 regressed by -1 in each year, and all other fold-year panels tied. Therefore #1263's full-data PASS remains binding, but its strict @100 superiority is sample-sensitive and must not be described as robust.

## Prior promoted parent retained for provenance

**recurrent-EOM HDBSCAN v1** remains the direct parent of #1263, not the current champion.

- target-excluded GMN 2022/2023 development: PASS, run `31827903547`;
- exposed SonotaCo 2013/2014 v31/literature benchmark: 4/4 PASS, run `31829200215`;
- exact promoted implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- pristine NASA ASFN 2018/2019 validation subsequently failed;
- EFN 2017/2018 was mechanism-inactive before label opening.

The SonotaCo and ASFN results belong to recurrent-EOM v1 and must not be transferred to #1263.

## Closed successors after recurrent-EOM promotion

### Consensus-EOM HDBSCAN v1 — CLOSED NEGATIVE

PR `#1247`, binding run `31843289411`.

Mechanism active, but regressed frozen recovered@100, top-100 precision, and MRR in both years, plus recovered@50 in 2023.

This already tests a componentwise multi-objective FOSC/EOM extraction over the annual stability vector. Therefore generic vector-EOM, Pareto-EOM, lexicographic annual-EOM, or componentwise consensus extraction is not a fresh mechanism class unless a genuinely different independent architecture is established.

Do not rescue with alternate consensus weights/combiners/thresholds/tie rules.

### Cross-year-core HDBSCAN v1 — CLOSED NEGATIVE

PRs `#1249/#1252`, binding valid run `31848227596`, artifact `9236769577`.

Opposite-year k=10 core-distance geometry changed the hierarchy strongly but reduced recovery:

- 2022 @50 `45->44`, @100 `89->84`;
- 2023 @50 `46->44`, @100 `89->86`.

No k change, ordinary/cross-year blend, clipping/scaling, min-cluster-size change, or reranking rescue.

### Reciprocal-transfer HDBSCAN v1 — CLOSED NEGATIVE

PR `#1256`, binding run `31849645782`, artifact `9237240523`.

Separate annual HDBSCAN models + reciprocal strict-majority `approximate_predict` transport produced only 103 reciprocal families. Early ranking improved strongly, but broader recovery/precision regressed:

- 2022 @50 `45->47`, @100 `89->84`, MRR `0.02250->0.05817`;
- 2023 @50 `46->49`, @100 `89->87`, MRR `0.02202->0.05687`.

No majority relaxation, probability threshold, orphan/centroid fallback, HDBSCAN retune, or parent fusion.

### ECDF recurrent-rank HDBSCAN v1 — CLOSED NEGATIVE

PR `#1261`, binding run `31851273161`, artifact `9237628549`.

Memberships/nodes remained exact 2,097 parent families; only annual-EOM ECDF ranking changed. @100 stayed `89->89` in both years while MRR fell slightly in both years.

No raw/ECDF blend, alternate percentile/tie rule, year weighting, subset application, or rank fusion.

### Phase-intensity-equalized recurrent-EOM v1 — CLOSED NEGATIVE

PR `#1259`, binding run `31851330153`, artifact `9237680835`.

Parameter-free pooled empirical solar-phase intensity equalization was mechanism-active (`2,097->2,014` candidates) but regressed core metrics:

- 2022 @50 `45->42`, @100 `89->81`, precision `0.78565->0.75019`;
- 2023 @50 `46->42`, @100 `89->82`, precision `0.78677->0.75802`.

No partial equalization, raw/equalized blend, smoothing/binning, alternate CDF origin/tie rule, per-year warp, or fusion rescue.

### Density-synchronous stratified-core HDBSCAN v1 — CLOSED NEGATIVE

PR `#1266`, binding run `31861760176`, artifact `9240971435`, digest `sha256:21663ae010be00117fc659d14a74b6360a5f342745a13707e640cb08d464b431`.

Direct successor to #1263. Sole change: balanced annual `5+5` HDBSCAN core radius `max(d5_2022,d5_2023)` before unchanged density-synchronous extraction.

Mechanism active but too aggressive: candidate count `2,094->1,706` (-388, -18.53%).

- 2022 @50 `45->44`, @100 `89->81`, precision `0.7873334043->0.7628887349`, MRR `0.0225053732->0.0229505931`;
- 2023 @50 `46->44`, @100 `90->78`, precision `0.7898245986->0.7637124161`, MRR `0.0220302849->0.0231845086`.

Exact verdict: `FAIL_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT`.

The higher MRR does not rescue the decisive recovery/precision regressions. No alternate annual k, soft/max/mean/quantile core combination, pooled-core blend, partial stratification, score blend, or reranking rescue is authorized.

This closes the obvious hard annual-balance core-distance lane.

## Older mechanisms that may look untried but are already closed / disfavored

### Mutual-nearest bottleneck recurrence v8 — CLOSED NEGATIVE

Historical workflow run `31216293238`, artifact `9009189672`, digest `sha256:b0e52bab6a822d9c734c8ccdf7b908bf98552e7edc05b2dbd6df20a02b359aac`.

Exact reciprocal-nearest cross-year component matching under fixed radius 1.5 produced 370 families. Binding development verdict:

`FAIL_MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT`

- bottleneck-recurrence recovered@100: `41`;
- plain persistence recovered@100: `48`;
- qualified known showers: `109`.

Therefore generic mutual-nearest / reciprocal-neighbor recurrence is not a fresh mechanism class.

### GMN thinning / subsample family stability — DIAGNOSTIC CLOSED

Binding diagnostic run `31615201183`, artifact `9149007071`.

Deterministic event-thinning persistence count was non-monotone and not specific enough as a family-quality proxy. Maximum stability was especially dominated by low-quality P20 families. The diagnostic explicitly forbids choosing stability=3, excluding stability=4, changing thinning fractions/salts/radius, or fitting a post-result transform.

Therefore do not propose generic bootstrap/subsample persistence ranking as a new successor without a genuinely different independently motivated mechanism.

### Mutual-Proximity local-geometry OOF — CLOSED NEGATIVE

Binding run `31649753150`, artifact `9162182072`.

Compared with its frozen passed parent:

- recovered@100 `66->63`;
- recovered@50 `41->46`;
- top-100 precision `0.72295->0.66980`;
- MRR `0.05024->0.05112`.

Failed @100 and precision. Its original closure explicitly forbids pseudocount/parametric MP, local-scaling/k rescues, or hybrids of that failed representation mechanism.

### Recurrent Flow Tube / RFT v3 heldout — CLOSED NEGATIVE

PR `#1258`, binding GMN 2023 heldout run `31562188321`.

Only 2/5 frozen numerical gates passed: recovered@50 `32` (<35), recovered@100 `54` (<58), precision `0.6309` (<0.65). No rerank, persistence cutoff, coherence weighting, ownership alteration, or threshold rescue.

## External-validation state — not successor lanes

### NASA ASFN 2018/2019 — historical pristine negative for recurrent-EOM v1

PR `#1257`, binding run `31850437866`, artifact `9237338312`.

9,227 retained events. Vanilla and recurrent-EOM each produced 34 candidates and selected the same nodes (`mechanism_active=false`). Recovery was identical (13 showers in 2018, 11 in 2019), while recurrent-EOM MRR was slightly lower both years.

Exact verdict: `FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`.

ASFN may not be used to design a rescue successor, and its result does not automatically transfer to #1263.

### EFN 2017/2018 — NEUTRAL PRETRUTH / retired diagnostic

PR `#1254`. On 782 retained events, vanilla/recurrent each selected the same 8 nodes. PASS was impossible before labels, so EFN shower labels remain unopened. EFN geometry/hierarchy is nevertheless exposed and cannot serve as pristine validation for a newly designed successor.

### SonotaCo 2013/2014 — permanent exposed validation panel

Under PR `#1264`, SonotaCo 2013/2014 is explicitly **EXPOSED DEVELOPMENT ONLY**, never pristine external validation. Future successors may reach it only after passing a pre-frozen GMN train gate. #1263 does not receive a retroactive SonotaCo benchmark because its original protocol explicitly prohibited one.

### AMOS 2023/2024 — final one-shot external test / acquisition blocked

Under PR `#1264`, untouched AMOS 2023/2024 is the permanent final test after methodology selection closes. Existing recurrent-EOM AMOS protocol work remains historically preserved; no scientific event-level AMOS data have been accessed. Current public-data recheck found no discoverable compliant complete 2023/2024 reduced-trajectory release. Exact staged provider request is ready but unsent.

Do not substitute alternate AMOS years, selected case-study/spectral/fireball samples, or reconstructed quantities. If the eventual final AMOS test fails, external generalization is not established and no replacement-survey hunt is authorized.

## Permanent evaluation structure

PR `#1264` freezes:

1. TRAIN / DEVELOPMENT: target-excluded GMN 2022+2023;
2. VALIDATION: SonotaCo 2013+2014, explicitly exposed development-only;
3. FINAL TEST / EXTERNAL VALIDATION: untouched AMOS 2023+2024, one-shot after methodology selection closes.

GMN 2024/2025 and other exposed GMN years may not be retroactively relabeled as pristine holdouts.

## Method-development rule going forward

Before creating any new successor:

1. search this ledger and the live repo for the mechanism class and synonyms;
2. reject anything that is merely a prohibited rescue of a closed lane;
3. require an independent physical/statistical/literature motivation that does not depend on prior outcomes;
4. start from #1263 unless there is a documented reason not to;
5. freeze exact scientific architecture, implementation and gate before the first technically valid GMN endpoint;
6. compare directly against #1263 on permanent target-excluded GMN 2022/2023;
7. if GMN fails, close permanently and do not access SonotaCo;
8. if GMN passes, freeze the prospective SonotaCo validation before access;
9. preserve every technically valid failure exactly;
10. do not create version sequences merely by changing k, weights, blends, thresholds, score transforms, tie rules or related hyperparameters after seeing outcomes.

Given #1263's modest full-data gain and negative perturbation robustness result, a future successor should ideally produce a structurally clearer gain rather than another one-family rank swap. Absence of such a genuinely distinct architecture is a valid reason to stop expanding methodology rather than overfit the development panel.

The protected `[20°,55°]` target region, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
