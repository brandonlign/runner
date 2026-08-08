# OrbitTrace catalogue v6 — SonotaCo 2017/2019 architecture-pre-frozen transfer

## Status

Protocol-only freeze. No SonotaCo 2017/2019 archive is opened by this branch and no detector, label evaluation, target-region scan, or OrbitTrace comparison is executed here.

This stage activates only if the exact source-audited catalogue-v6 development execution returns `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`. If development fails, this protocol remains dormant and cannot be used to rescue or retune v6.

## Claim boundary and chronology

The exact catalogue-v6 architecture was frozen in PR #221 on 2026-08-07 at 05:06 UTC, before the later SonotaCo 2017/2019 locked score-label attempt in PR #272 at 17:45 UTC.

The 2017/2019 raw archives are **not pristine**. They had earlier transport/archive exposure, and PR #272 later entered the 2019 parser deeply enough to evaluate aggregate label-support/parser gates before stopping. Therefore this pair must not be described as a never-seen or pristine external dataset.

However, PR #272 produced **no detector ranking or scientific catalogue result**: it stopped at parser transport with `scientific_ranking_result_available=false`. The catalogue-v6 architecture and every scientific constant were already frozen before that attempt and may not be changed from any 2017/2019 information.

Accordingly, this stage is classified only as an **architecture-pre-frozen, no-retuning transfer test**. It can test whether the already-frozen catalogue architecture generalizes to an older survey pair, but it cannot by itself satisfy a claim requiring a pristine prospective dataset.

## Why the old 2019 failure is not inherited as a v6 eligibility rule

The failed PR #272 reused a parser originating in the fixed4 episode-confirmation chain. Its binding 2019 condition was `at_least_30_supported_native_codes`, where a native code counted as supported only when it had at least 20 matched events.

That condition is not part of the frozen catalogue-v6 protocol. Catalogue v6 instead predeclared:

- at least 30 supported calibration bins in each year;
- recurrent primary-family construction;
- ranked known-shower recovery;
- dominant-label precision;
- qualified-match coverage.

This protocol does **not** retroactively change the old fixed4 result: PR #272 remains an integrity no-result under its own frozen rules. The transfer uses a separately frozen catalogue-v6 transport and catalogue-v6 eligibility standard because it is a different scientific interface.

## Immutable method

The method is the exact v3-primary dual-output catalogue-v6 architecture frozen in PR #221:

- v3 multi-anchor wavelet energy is the primary score;
- fixed4 remains a separate sparse rescue queue and may never alter primary components, recurrence, Fisher evidence, or rank;
- 10-degree windows stepped every 5 degrees;
- 128-event exact episodes;
- 128 null calibration episodes per supported 10-degree solar-longitude bin;
- v3 detection threshold `p_v3 <= 0.05`;
- primary positive-lobe membership `r^2 < 3` around the strongest positive v3 coefficient location;
- component minimum four events and two retained anchors;
- cross-year centroid link radius 1.5;
- proposal budget exactly 512 primary proposals per window, maximum 36,864/year;
- all fixed4 minimum-p rescue proposals retained separately;
- exact primary family ranking: year count, Fisher-style evidence, best v3 score, event support;
- solar longitude 20–55 degrees removed before label normalization/storage/candidate generation.

The source-audited two-line implementation repair from PR #490 is allowed because it only instantiates the already-frozen component-builder calls that the scientific source later reads. No other scientific-source change is allowed.

## Fixed input identity

The transfer pair is SonotaCo 2017 and 2019, using the exact raw archive identities already recorded before this protocol:

- 2017 archive SHA-256 `1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf`;
- 2019 archive SHA-256 `d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4`.

No alternate year, archive revision, subset, or replacement panel may be selected from the transfer outcome.

## Transport rules

A new catalogue-v6 transport wrapper must be frozen and source-audited before either archive is opened in this chain.

It may only:

1. map native SonotaCo fields to the exact geometry/label representation required by v6;
2. reproduce the already-established trailing-empty-header compatibility where applicable;
3. map native shower codes through the already-frozen IAU mapping;
4. apply the same geometry/quality rules used by the matched SonotaCo catalogue benchmark where those fields exist;
5. remove solar longitude 20–55 degrees before any label is normalized or stored;
6. adapt file/year identifiers and deterministic event IDs.

It may not change v6 scores, thresholds, proposal budgets, neighborhood definitions, calibration size, membership radius, component rules, recurrence, ranking, or evaluation definitions.

The old fixed4-specific `>=30 supported native codes with >=20 events/code` condition is neither copied nor weakened; it is simply outside this catalogue-v6 transport because it is not a v6 requirement.

## Pre-scientific transport/eligibility gates

Before any v6 detector score is computed, all of the following must pass for both years:

- exact archive SHA-256 matches the identities above;
- ZIP/member integrity and safe paths pass;
- nonempty input and zero malformed accepted-format records;
- required solar-longitude, radiant, speed, quality, and native-label fields exist;
- target interval is removed before label normalization/storage;
- native label syntax fraction >=0.90;
- mapped non-background label fraction >=0.90;
- at least 10,000 retained background/sporadic events after the frozen exclusion/quality rules;
- at least 30 distinct mapped labelled shower identities across the retained year;
- at least 30 supported v6 calibration bins in each year under the exact frozen 128-null calibration construction.

These gates are frozen before this transfer is executed. Failure is an input/transport ineligibility result, not a v6 scientific failure, and no threshold may be relaxed from it.

## Evaluation universe

Labels remain unavailable to candidate generation, scoring, component construction, recurrence, and ranking.

After the complete primary and rescue outputs are frozen, define eligible known showers exactly as in v6 development: at least eight total labelled events across the two transfer years and at least four labelled events in each year.

Run the exact promoted-v8 catalogue method on the same transported event universe as a fixed predecessor comparator. It may not be tuned on 2017/2019.

## Transfer endpoints

Report for the v3 primary list and exact v8 baseline on the same universe:

- number of recurrent families;
- eligible known-shower count;
- qualified known-shower matches;
- recovery@25, @50, and @100;
- MRR over eligible known showers;
- top-25, top-50, and top-100 dominant-label precision;
- per-shower F1 and macro F1;
- size-stratum mean F1 for 4–9, 10–24, 25–49, 50–99, and 100+ labelled members where nonempty.

Fixed4 rescue results are reported separately and cannot satisfy a primary transfer gate.

## Frozen transfer pass gates

The transfer passes only if every condition below holds:

1. all pre-scientific transport/eligibility gates pass;
2. at least 40 recurrent v3 primary families are produced;
3. v3 primary recovery@100 is at least `floor(0.80 * v8_recovery_at_100)` on the exact same transfer universe;
4. v3 primary qualified matches are at least `floor(0.60 * v8_qualified_matches)` on the same universe;
5. v3 primary top-100 dominant-label precision is at least 0.50;
6. v3 primary MRR is at least 0.80 times v8 MRR;
7. at least one of recovery@25, recovery@50, recovery@100, MRR, or macro F1 strictly exceeds v8 while none of recovery@100, qualified matches, top-100 precision, or MRR violates gates 3–6;
8. all source/provenance/blinding gates pass.

The 0.80 recovery retention, 0.60 qualification retention, and 0.50 precision floor are inherited directly from the original v6 development standard relative to its fixed predecessor; they are not chosen from 2017/2019 outcomes. The MRR retention gate is added here prospectively as an anti-ranking-regression requirement before catalogue-v6 has produced any 2017/2019 ranking.

A pass is labelled:

`PASS_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER`

A scientific failure is labelled:

`FAIL_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER`

An input/transport failure is labelled separately and is not reinterpreted as detector evidence.

## Relationship to literature superiority and OrbitTrace

This transfer does not replace the matched Sugar/HDBSCAN adjudication frozen separately. It also does not by itself authorize a target-containing OrbitTrace run because the raw pair is not pristine.

A future OrbitTrace deployment still requires:

1. v6 target-excluded development pass;
2. frozen literature adjudication under its exact claim boundary;
3. this no-retuning transfer or a stronger external generalization result;
4. an independently justified target-authorization decision that explicitly accounts for the absence or presence of a genuinely pristine validation panel;
5. a final blind target-deployment protocol frozen before restoring the 20–55 degree interval.

No information from the historical v8 partial OrbitTrace recovery may enter any v6 parameter, gate, transport choice, or ranking rule.