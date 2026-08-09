# Current OrbitTrace v6-family authority

This file records completed results and current routing under the pre-result precedence protocol in `PROTOCOL.md`. It does not change detector science or selection thresholds.

## Ordinary repaired v6 — permanently rejected

Canonical strict semantic-replay development run: `31285583731`.

Exact verdict: `FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`.

Canonical endpoints from the run artifact/log:

- primary v3 families: **12**;
- fixed4 rescue-only families: **25**;
- qualified known-shower matches: **5**;
- recovery@100: **5**;
- recovery@500: **5**;
- MRR: **0.3931818181818182**;
- median rank: **4.0**;
- macro F1 over the five qualified matches: **0.7380195031780808**;
- top-100 dominant precision: **0.469098846991149**;
- rescue-only additional qualified labels: **13**.

Integrity/development-interface gates passed, but all four substantive scientific gates failed:

- `at_least_50_v3_families = false`;
- `top100_recovery_at_least_80pct_fixed4 = false`;
- `top100_precision_at_least_050 = false`;
- `qualified_matches_at_least_60pct_fixed4 = false`.

This supersedes the earlier stale authority summary that incorrectly listed 29 primary families and 77 recovery@100. The canonical artifact/log from run `31285583731` is authoritative.

Ordinary v6 also uses the native catalogue `SPORADIC` designation to select its calibration reservoir, so even a hypothetical performance recovery would not give it the same information-parity claim as v6-LF. No further ordinary-v6 tuning, matched literature, external validation, ordinary-v6 C1, or target deployment is authorized.

## v6-LF — live precedence branch

v6-LF changes exactly one preregistered scientific assumption relative to repaired v6: calibration uses **every geometrically valid target-excluded scan event**, with no shower-label selection, trimming, density masking, or parameter search. All repaired-v6 scores, proposal budgets, exact rescoring, components, recurrence, ranking and gates remain frozen.

Original v6-LF run `31285478837` completed both preexact captures and all 12 exact-rescore shards. Its 2022 replay then hit a technical serialization-equality mismatch before any final scientific evaluation. That run is therefore a technical no-result, not a scientific failure.

Strict semantic-equivalence recovery run `31287635860` reuses those immutable exact artifacts. Both 2022 and 2023 replay jobs have passed; the combined family-freeze/truth/evaluation job is the remaining stage. The semantic fallback preserves exact structure, IDs and order and permits floating differences only within the preregistered 1e-12 tolerance.

Until run `31287635860` produces a final artifact, v6-LF has **no scientific PASS/FAIL verdict**.

## Binding downstream routing

- v6-LF development PASS -> bounded matched-literature equivalence audit, then frozen pairwise Sugar/HDBSCAN comparison.
- v6-LF development PASS + matched `NO_LITERATURE_SUPERIORITY` -> C1-LF.
- v6-LF genuine scientific development FAIL -> P1.
- Technical/integrity failure -> equivalence-preserving repair only; it may not activate P1, C1-LF, or P2.

If v6-LF establishes broad or sparse matched-literature superiority, it must next pass a genuinely independent cross-survey generalization gate before any target-containing Stage A.

## Independent generalization correction

The previously proposed target-excluded GMN 2024/2025 prospective holdout is invalid for this purpose. Repository history shows PR #453 / run `31235104333` already consumed GMN 2024/2025 scientific values, known-shower labels and F1 endpoints. No later workflow may relabel that panel as pristine external evidence.

The replacement v6-LF external gate is frozen prospectively in PR #589 on scientifically event-value-unexposed **MAARSY 2018/2019**. It is dormant unless v6-LF first passes development and matched literature. Both complete v6-LF and promoted-v8 family universes/ranks must freeze before native orbit access, and exact `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` is required before final target-region Stage A.

If v6-LF fails before external activation, MAARSY 2018/2019 remains unopened for the next legitimately active preregistered successor.

## Target firewall

No branch currently authorizes OrbitTrace target access. Solar longitude 20°–55° and all target coordinates, identities, canonical members, historical target ranks, target-containing Stage-A outputs, and Stage-B reveal data remain unavailable to method selection, development, literature and external-validation work.
