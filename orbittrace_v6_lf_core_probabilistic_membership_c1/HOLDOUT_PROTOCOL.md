# C1-LF prospective GMN 2024/2025 temporal holdout

## Eligibility and pristine-data rule

This protocol is frozen before any C1-LF development, literature, or GMN 2024/2025 C1-LF result.

It is dormant unless all earlier C1-LF succession gates pass in order:

1. exact v6-LF development PASS;
2. exact v6-LF matched-literature classification `NO_LITERATURE_SUPERIORITY`, which legitimately activates C1-LF;
3. exact C1-LF development PASS;
4. exact C1-LF matched-literature classification `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against both frozen HDBSCAN and Sugar panels.

The existing v6-LF GMN 2024/2025 executor is already guarded so that it cannot open this holdout after a v6-LF literature no-go. Therefore, on the only branch where C1-LF can become active, GMN 2024/2025 remains prospectively unexposed. Execution must re-audit repository history and block if scientific event-level 2024/2025 exposure is discovered before C1-LF holdout activation.

## Frozen data construction

Use complete target-excluded GMN 2024 and 2025 geometry under the same transport as the already-frozen v6-LF holdout:

- exclusion 20°–55° is applied before any label access;
- geometry-valid stable-ID rows only;
- every scan row is copied into the all-event calibration reservoir;
- no catalogue shower/background designation selects calibration;
- exact repaired-v6 detector scores, proposal budgets, exact rescoring, components, and two-year recurrence are unchanged;
- no null trimming, parameter search, density masking, or holdout-specific tuning.

Before truth, build the exact v6-LF primary recurrent families and their immutable primary order on 2024/2025. Fixed4 rescue remains diagnostic only and cannot seed C1-LF.

Then apply the exact development-frozen C1-LF membership engine jointly across 2024/2025:

- seed-only OAS covariance;
- 99% candidate ellipsoid;
- 99%–99.99% local-background shell;
- one-sided 95% Garwood background bound;
- responsibility strictly >0.5;
- original seeds immutable;
- no refit and no recursive growth;
- no reranking after expansion.

The complete v6-LF seed families/rank, C1-LF model diagnostics, candidate/shell identities, responsibilities, expanded memberships, and final family order must be SHA-256 frozen before the first known-shower label value is read.

## Pretruth integrity and power gates

If any gate below fails, return `POWER_INCONCLUSIVE_C1_LF_GMN_2024_2025_TEMPORAL_HOLDOUT` **without reading known-shower label values**:

- all 12 months are present in each holdout year;
- >=1,000 valid target-excluded scan rows in each year;
- all-event calibration is exact row-for-row in each year;
- >=30 supported calibration bins in each year;
- proposal cap is exactly 512 per window and annual primary budget exactly 36,864 per year;
- >=50 recurrent v6-LF primary families exist before C1-LF membership expansion;
- every evaluated primary family spans both 2024 and 2025;
- exact C1-LF source and membership-engine identities match the frozen development PASS;
- fixed4 rescue never seeds membership;
- parameter search and recursive growth are absent;
- complete C1-LF pretruth membership/rank payload is durably hashed.

Nonvacuous C1-LF expansion is a scientific gate after truth-free model construction, not a reason to change the method.

## Frozen scientific evaluation

After all pretruth integrity/power gates pass, expose known-shower truth exactly once and evaluate both:

- the immutable seed v6-LF primary families/order on the holdout;
- the C1-LF-expanded families in the same immutable order.

The seed v6-LF holdout is a within-run reference only; it does not retroactively expose or authorize the separate dormant v6-LF holdout branch.

C1-LF passes only if **all** of the following hold:

### Absolute transport bars inherited from the v6-LF holdout

- qualified matches >= 90;
- recovery@100 >= 55;
- MRR >= 0.040;
- top-100 dominant precision >= 0.60;
- macro F1 >= 0.15.

### Membership-transfer bars inherited from C1-LF development

- at least one non-seed event is assigned;
- qualified matches do not regress versus the same-holdout seed v6-LF families;
- recovery@100 does not regress versus seed v6-LF;
- top-100 dominant precision >= `max(0.60, seed_v6_lf_precision - 0.02)`;
- macro F1 improves by >= +0.08 absolute versus seed v6-LF;
- MRR >= 0.95 × seed v6-LF MRR.

Using the same +0.08 macro-F1 gain and 0.95 MRR retention as development deliberately avoids choosing an easier external standard after seeing development.

## Verdicts

- `PASS_C1_LF_GMN_2024_2025_TEMPORAL_HOLDOUT` iff every pretruth integrity/power and scientific gate passes.
- `FAIL_C1_LF_GMN_2024_2025_TEMPORAL_HOLDOUT` iff pretruth power is adequate but one or more scientific gates fail.
- `POWER_INCONCLUSIVE_C1_LF_GMN_2024_2025_TEMPORAL_HOLDOUT` iff a pretruth integrity/power gate fails; truth must remain unread.

Only the exact PASS verdict may authorize a final target-containing Stage A for C1-LF. Literature superiority alone is insufficient.

No OrbitTrace target coordinates, members, identity, target-region events, historical target rank, or post-reveal result may be accessed by this protocol or holdout execution.
