# OrbitTrace current closed-mechanism ledger — 2026-08-14

**Role: evidence/navigation only. No scientific data access, method change, rerun, threshold change, or rescue authorization.**

Purpose: prevent future methodology sessions from rediscovering already-tested mechanisms under new names. This ledger is subordinate to the original frozen protocols/results; if any summary here conflicts with a binding artifact, the binding artifact controls.

## Current promoted development parent

**recurrent-EOM HDBSCAN v1** remains the promoted methodology parent.

- target-excluded GMN 2022/2023 development: PASS, run `31827903547`;
- exposed SonotaCo 2013/2014 v31/literature benchmark: 4/4 PASS, run `31829200215`;
- exact promoted implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

It is the strongest demonstrated **development** method in the current lineage, not a universally validated method. NASA ASFN 2018/2019 pristine cross-survey validation subsequently failed; EFN 2017/2018 was mechanism-inactive before label opening.

## Closed successors after recurrent-EOM promotion

### Consensus-EOM HDBSCAN v1 — CLOSED NEGATIVE

PR `#1247`, binding run `31843289411`.

Mechanism active, but regressed frozen recovered@100, top-100 precision, and MRR in both years, plus recovered@50 in 2023.

Do not rescue with alternate consensus weights/combiners/thresholds.

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

Parameter-free pooled empirical solar-phase intensity equalization was mechanism-active (2,097 -> 2,014 candidates) but regressed core metrics:

- 2022 @50 `45->42`, @100 `89->81`, precision `0.78565->0.75019`;
- 2023 @50 `46->42`, @100 `89->82`, precision `0.78677->0.75802`.

No partial equalization, raw/equalized blend, smoothing/binning, alternate CDF origin/tie rule, per-year warp, or fusion rescue.

## Older mechanisms that may look untried but are already closed / disfavored

### Mutual-nearest bottleneck recurrence v8 — CLOSED NEGATIVE

Historical workflow run `31216293238`, artifact `9009189672`, digest `sha256:b0e52bab6a822d9c734c8ccdf7b908bf98552e7edc05b2dbd6df20a02b359aac`.

Exact reciprocal-nearest cross-year component matching under fixed radius 1.5 produced 370 families. Binding development verdict:

`FAIL_MUTUAL_NEAREST_RECURRENCE_V8_DEVELOPMENT`

- bottleneck-recurrence recovered@100: `41`;
- plain persistence recovered@100: `48`;
- qualified known showers: `109`.

Therefore generic “mutual-nearest / reciprocal-neighbor recurrence” is not a fresh mechanism class.

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

### NASA ASFN 2018/2019 — PRISTINE NEGATIVE

PR `#1257`, binding run `31850437866`, artifact `9237338312`.

9,227 retained events. Vanilla and recurrent-EOM each produced 34 candidates and selected the same nodes (`mechanism_active=false`). Recovery was identical (13 showers in 2018, 11 in 2019), while recurrent-EOM MRR was slightly lower both years.

Exact verdict: `FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`.

ASFN may not be used to design a rescue successor.

### EFN 2017/2018 — NEUTRAL PRETRUTH

PR `#1254`. On 782 retained events, vanilla/recurrent each selected the same 8 nodes. PASS was impossible before labels, so EFN shower labels remain unopened. EFN geometry/hierarchy is nevertheless exposed and cannot serve as pristine validation for a newly designed successor.

### AMOS 2023/2024 — STILL PRISTINE / ACQUISITION BLOCKED

PRs `#1244`, `#1248`, `#1253`.

Primary recurrent-EOM-vs-vanilla external protocol and optional multi-method comparator benchmark are frozen and zero-data audited. Current public-data recheck found no discoverable compliant complete 2023/2024 reduced-trajectory release. Exact staged provider request is ready but unsent.

Do not substitute alternate AMOS years, selected case-study/spectral/fireball samples, or reconstructed quantities.

## Method-development rule going forward

Before creating any new successor:

1. search this ledger and the live repo for the mechanism class and synonyms;
2. reject any proposal that is merely a prohibited rescue of a closed lane;
3. require an independent physical/statistical/literature motivation that does not depend on ASFN/EFN outcomes;
4. freeze the exact mechanism and promotion gate before the first valid GMN endpoint;
5. compare directly against promoted recurrent-EOM on permanent target-excluded GMN 2022/2023;
6. preserve any technically valid failure permanently.

The protected `[20°,55°]` target region, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
