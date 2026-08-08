# OrbitTrace v6-LF GMN 2024/2025 temporal holdout — frozen protocol

## Purpose

Provide a prospectively frozen, no-retuning temporal generalization test for the fully label-free v6-LF all-event-null architecture.

This protocol is frozen **before any v6-LF development result is available**. The detector may not be changed in response to either the development result or this holdout result.

The holdout complements the external SonotaCo matched Sugar/HDBSCAN benchmark:

- SonotaCo tests cross-instrument / cross-catalogue transport and literature superiority;
- GMN 2024/2025 tests later-year temporal generalization under the native geometry/schema family used for development.

Neither result may be used to retune v6-LF.

## Frozen method identity

The candidate is exactly the v6-LF method frozen in `orbittrace_v6_label_free_all_event_null`:

- exact repaired v3-primary catalogue-v6 detector;
- all-event Mondrian null calibration;
- no shower-label-selected calibration membership;
- no null trimming, masking, stream removal or iterative cleaning;
- exact inherited calibration episode count, score functions, empirical p-values, thresholds, proposal caps, exact rescoring, component rules, cross-year recurrence and primary ranking;
- no parameter search.

Execution fanout/checkpointing is implementation-only.

## Holdout corpus

Years are fixed to **GMN 2024 and GMN 2025**.

All twelve monthly files for each year are requested through the same frozen GMN monthly-data interface used by development.

The holdout remains target-excluded:

- geometrically valid rows are constructed first;
- solar longitude 20°–55° is removed before any shower-label value is read;
- stable IDs are deduplicated deterministically across months;
- `sun_lon = wrap180(lam - sol)` using the exact frozen base helper;
- scan rows receive `iau=0`, `complex_key="HIDDEN"`;
- **every** scan row is copied into the calibration reservoir with only `complex_key="SPORADIC"` changed.

No OrbitTrace target-region event or withheld target reference is accessible.

## Hard label firewall

Pre-truth, only stable ID and geometry may be read. The shower-label column value remains unread through filtering, calibration, proposal generation, exact rescoring, components, 2024/2025 recurrence, ranking, and durable SHA-256 freeze of the complete family payload.

Only after that SHA exists may the same monthly files be re-read and native shower-label values accessed for evaluation. The truth event-ID universe must exactly equal the pre-truth event-ID universe.

## Frozen transport adaptation

The detector is year-agnostic. The only runtime namespace adaptation is:

- `YEARS = (2024, 2025)` wherever the frozen recurrence/evaluation helper requires a two-year universe;
- `MONTH_KEYS` are the 24 fixed monthly keys for 2024/2025;
- a holdout-specific corpus namespace is used only where stable random seeds require a corpus string.

No threshold, bin width, calibration count, shortlist size, proposal cap, score, family-link radius, membership rule, recurrence rule or rank rule changes.

## Integrity / power gates

All must pass before scientific interpretation:

- complete 12-month retrieval for both years;
- exact numeric geometry validity semantics from the frozen parser;
- exact 20°–55° exclusion before label values;
- zero shower-label value access pre-truth;
- calibration count == scan count in both years;
- identical scan/calibration stable-ID order and geometry;
- at least 1,000 target-excluded scan rows in each year;
- at least 30 supported calibration bins in each year;
- proposal cap exactly 512/window and 36,864/year;
- at least 50 recurrent primary families;
- every retained recurrent primary family spans both 2024 and 2025;
- ranked family payload SHA-frozen before truth;
- truth/pre-truth event universes identical;
- no retuning or parameter search.

If an integrity/power gate fails, the panel is `POWER_INCONCLUSIVE` rather than a scientific method failure.

## Scientific generalization gates

A conclusive holdout **PASS** requires all:

- qualified known-shower matches >= 90;
- recovery@100 >= 55;
- MRR >= 0.040;
- top-100 dominant-label precision >= 0.60;
- macro F1 >= 0.15.

These are preservation gates fixed before the result. They require the later-year catalogue to retain most of the established v8-level discovery power while allowing real temporal changes in observing cadence and label support.

Verdicts:

- `PASS_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT`
- `FAIL_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT`
- `POWER_INCONCLUSIVE_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT`

A scientific FAIL rejects v6-LF promotion. No adjustment on GMN 2024/2025 is permitted.

## Promotion rule

Require all:

1. `PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT`;
2. matched SonotaCo classification `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against frozen Sugar/HDBSCAN panels;
3. `PASS_V6_LF_GMN_2024_2025_TEMPORAL_HOLDOUT`.

Only then may the frozen Stage-A/Stage-B exact-ID final OrbitTrace firewall execute v6-LF.

This protocol contains no OrbitTrace target coordinates, target IDs, target identity or prior target ranks.
