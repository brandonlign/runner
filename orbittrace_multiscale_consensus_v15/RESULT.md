# OrbitTrace multiscale-consensus multiplicity v15 — target-excluded development result

## Frozen verdict

`PASS_MULTISCALE_CONSENSUS_V15_TARGET_EXCLUDED_DEVELOPMENT`

v15 passes every preregistered integrity, full-cardinality preservation, and lower-cardinality robustness gate. It is frozen as the surviving successor methodology for later independent external validation.

This is a **target-excluded development pass only**. It is not an external-validation result and does not support a claim of superiority to Sugar, catalogue HDBSCAN, or any other literature method.

## Provenance

- clean pre-external base: `c9d6c44704013ba0c9430100e98a29a56b453304`
- source/protocol PR: `#911`
- frozen source head: `a46ad1c6668d06a3e707cff6a8307f8e0969bb82`
- execution PR: `#912`
- execution trigger commit: `019053ef09e44e8abe9de8bbcdb9c73841aea06e`
- workflow run: `31357633347`
- valid predecessor cap/reference run: v13 r3 workflow `31356056453`

### v15 artifacts

- final development result: artifact `9051358647`, SHA-256 `9029dba033dedd222fc023a8c07fc1862f8489f0c16043df32cd5c39da65a987`
- frozen pretruth consensus orders: artifact `9051352108`, SHA-256 `1ad7cd272eda4fb68bc5614d02d3faca92700d29db8c3773bfbd3fb463f31b42`
- sanitized label-free rank inputs: artifact `9051348966`, SHA-256 `922314029513f72deab4e2a31097ed4c4919e89715f58812c09f225187b5e83d`
- generated cap 16: artifact `9051341062`, SHA-256 `3d89a01d1577fae7b800e1f3e5cbc43fb7a916596da2cb82e0b763828de33c42`
- generated cap 24: artifact `9051329502`, SHA-256 `3f29742eb0bb7d8ca61e8e5dd2b994369f668bbe0c721320e152a9b92de07587`
- generated cap 48: artifact `9051324760`, SHA-256 `519e613ec4829ba98f84669acfe2f8297b8f528c5299e1c5c379889b183c45ad`
- generated cap 72: artifact `9051336710`, SHA-256 `aaa75173fabaa8683b8aaf8b016a4e1323f7752611137c804c7667d8e4262096`

## Frozen v15 rule

For nominal episode cap `K`, use exact multiplicity rankings at:

- `K`;
- `floor(3K/4)`;
- `floor(K/2)`;

with a floor of four events. The nominal stress panels are therefore:

- 128: `[128, 96, 64]`;
- 96: `[96, 72, 48]`;
- 64: `[64, 48, 32]`;
- 32: `[32, 24, 16]`.

For each family, take the zero-based multiplicity ranks `r1`, `r2`, and `r3` from those nested scales and define

`R15 = median(r1, r2, r3)`.

Rank ascending by `R15`, then `r1`, then `r2`, then `r3`, then stable family ID.

No coefficient, nested scale, cap, or threshold is fitted or selected after results.

## Rank-before-label firewall

The execution maintained the frozen firewall:

1. missing nested caps 16/24/48/72 were generated with the frozen v5 post-ranking evaluator replaced **before catalogue access** by a no-label stub;
2. hidden-label values were never consulted for those four generated component rankings;
3. all eight cap inputs were reduced to a strict rank/score metadata whitelist;
4. prior evaluation, holdout, family-label, and truth payloads were excluded from the v15 consensus-rank job;
5. all four v15 consensus orders were frozen successfully under `PASS_V15_PRETRUTH_CONSENSUS_FREEZE`;
6. only afterward did the evaluator download the frozen direct-v5 target-excluded label-evaluation payload.

No SonotaCo 2013/2014 scientific data, MAARSY scientific data, OrbitTrace target information, or OrbitTrace target region was accessed.

## Integrity result

Every preregistered integrity gate passed:

- exact 92-family membership matched across all eight caps 16/24/32/48/64/72/96/128;
- exact-family-membership SHA-256: `695fd71df60f727a99f481553b31958f6a5f306d38036fcf9c6afe8fb4410e2e`;
- all four v15 orders used the same family universe;
- every v15 consensus score was exactly the median of its three component multiplicity ranks;
- all component rankings and all v15 orders were frozen before label evaluation;
- no best-cap selection occurred;
- external/target firewall remained clean.

## Direct frozen-v5 reference

- eligible labels: 297
- qualified matches: 56
- recovered@100: 56
- recovered@500: 56
- MRR: `0.07346150537319665`
- median rank: `37.5`
- macro F1: `0.2109415894913715`
- top-100 dominant precision: `0.6969754706187407`

## v15 nominal-128 result

- eligible labels: 297
- qualified matches: 56
- recovered@100: 56
- recovered@500: 56
- MRR: `0.07347220763246964`
- median rank: `36.5`
- macro F1: `0.2109415894913714`
- top-100 dominant precision: `0.6969754706187407`

Every full-cardinality preservation gate passed:

- recovered@100 did not decrease;
- MRR exceeded the preregistered 95%-of-direct-v5 floor;
- top-100 dominant precision did not decrease;
- qualified count stayed 56.

## Lower-cardinality robustness

Frozen lower-panel MRR threshold relative to v15-128: `0.06612498686922268`.
Frozen recovered@100 threshold: 51.

### Nominal 96 — PASS

- recovered@100: 56
- MRR: `0.07290311744723273`
- median rank: `34.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- every robustness gate passed.

### Nominal 64 — PASS

- recovered@100: 56
- MRR: `0.07435048498468526`
- median rank: `35.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- every robustness gate passed.

### Nominal 32 — PASS

- recovered@100: 56
- MRR: `0.0683412039837563`
- median rank: `38.5`
- top-100 dominant precision: `0.6969754706187407`
- qualified matches: 56
- every robustness gate passed.

## Interpretation

v15 fixes the portability failure mode that defeated frozen #839/v8, v13, and v14 **within target-excluded development**: it no longer requires every survey panel to contain 128 local events, while the multiscale median rank remains robust across the full preregistered cardinality stress range down to nominal 32.

The result is stronger than simply selecting a smaller episode size: every nominal condition uses the same predeclared multiscale rule and all stress panels pass simultaneously. Full-cardinality performance is preserved rather than traded away for low-density robustness.

## Claim boundary and next step

v15 is now frozen. No further tuning on the target-excluded GMN 2020/2021 development result is allowed before external validation.

SonotaCo 2013/2014 must not be reused as an untouched test, because it was exposed during the frozen-#839 applicability attempt. Previously exposed or power-inconclusive external datasets also cannot be relabeled as pristine validation.

The next legitimate step is to preregister v15 unchanged on a **different, genuinely untouched external dataset** with sufficient event density/power, keeping known-shower truth inaccessible until all v15 catalogue outputs and any comparator outputs are frozen.
