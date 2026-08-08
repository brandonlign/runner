# OrbitTrace v6-LF all-event Mondrian null — frozen protocol

## Purpose

This is a scientifically distinct, one-shot repair of the v3-primary catalogue-v6 detector's only discovered dependence on catalogue shower labels.

A source-only audit performed before any v6 development verdict showed that the frozen v6 geometry scan is label-hidden, but `parse_catalogue` selects its empirical null reservoir with `if label == "SPORADIC"`. The downstream `MondrianWindowFactory` itself uses only event geometry. Therefore the detector is target-blinded but not fully label-free as originally implemented.

v6-LF removes that dependency without changing the detector, score, thresholds, proposal budget, recurrence rule, ranking rule, membership rule, or null-sampling algorithm.

## Frozen change

The **only scientific change** relative to exact repaired v6 is the calibration reservoir:

- original v6: target-excluded events whose catalogue label normalizes to `SPORADIC`;
- v6-LF: **all geometrically valid target-excluded scan events**, regardless of shower identity.

Every event enters the calibration reservoir with the same geometry as the scan row and a dummy `complex_key="SPORADIC"` required only by the inherited episode container. No catalogue label is read to decide calibration membership.

All original v6 constants remain exact:

- years 2022 and 2023;
- blind exclusion 20°–55° before any label value is read;
- 10° Mondrian bins;
- 128 calibration episodes per supported bin;
- inherited stable seeds and inherited corpus namespace;
- 128-event episodes;
- 5° scan step;
- 512 primary proposals per scan window / 36,864 annual post-window proposal budget;
- v3 multi-anchor primary score;
- fixed4 rescue channel and threshold;
- exact-rescore logic;
- component construction;
- two-year recurrence;
- primary-family ranking;
- rescue novelty handling.

The use of all observed events makes the empirical null conservatively contaminated by real streams. No attempt may be made to identify, trim, mask, downweight, or iteratively remove stream-like events from the null pool. This is intentional: the fix must not replace one source of label leakage with an unsupervised tuning loop.

## Hard label firewall

Development execution is split into two logical phases.

### Pre-truth phase

The parser may access only the columns needed for geometry and stable event identity. It must:

1. read ID, solar longitude, ecliptic longitude, ecliptic latitude, and geocentric speed;
2. apply numeric validity checks;
3. apply the 20°–55° exclusion;
4. deduplicate stable event IDs;
5. construct scan rows with `iau=0` and `complex_key="HIDDEN"`;
6. construct calibration rows from **every** scan row by copying geometry and replacing only `complex_key` with `"SPORADIC"`;
7. execute both frozen v6 year scans, recurrent-family construction, and primary ranking;
8. serialize and SHA-256 freeze the complete primary and rescue family payloads/rank ordering.

The shower-label column must not be read or normalized before step 8.

### Truth phase

Only after the pre-truth SHA is durable may the same raw monthly files be re-read and the shower-label column accessed. Geometry validity, blind exclusion, and duplicate handling must be replayed identically. The resulting hidden-label mapping may then be passed to the exact frozen v6 evaluator.

The pre-truth event-ID universe and the truth-phase event-ID universe must be identical.

## Why this variant is scientifically admissible

The original null generator selects a center event in the appropriate 10° solar-longitude bin and samples the remainder of the 128-event episode uniformly without replacement from the inherited local solar-longitude window. It does not inspect labels, shower identity, or `complex_key` when selecting events. v6-LF therefore changes only which geometrically valid events are eligible for null sampling.

Real-stream contamination of the all-event pool can make high null scores more common and is expected to reduce, not manufacture, apparent significance. No post-result correction for this power loss is permitted.

## Development gates

The exact method is a one-shot development test. All integrity gates must pass:

- exact repaired-v6 scientific source identity;
- exact target exclusion 20°–55° before label access;
- zero shower-label reads in pre-truth parser/scoring/ranking;
- calibration count exactly equals scan count in each year;
- every calibration event ID equals a scan event ID and no extra IDs exist;
- same event geometry in scan and calibration copies;
- 128 calibration episodes per supported bin;
- at least 30 supported calibration bins in each year;
- proposal cap exactly 512/window and 36,864/year;
- primary and rescue rankings hash-frozen before truth;
- truth-phase event universe exactly equals the frozen pre-truth universe;
- no null trimming, masking, clustering, retuning, or parameter search.

Scientific gates are fixed against the already-promoted fully label-free v8 baseline, not against the still-unknown original-v6 result:

- at least 50 recurrent primary families;
- qualified known-shower matches >= 95;
- recovery@100 >= 58;
- MRR >= 0.045531138942766655;
- top-100 dominant-label precision >= 0.65;
- macro F1 >= 0.1736657194465356.

Passing these gates means only that the label-free calibration repair retains at least the established v8 development floor. It does **not** establish literature superiority.

Pass verdict: `PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT`.

Failure verdict: `FAIL_V6_LABEL_FREE_ALL_EVENT_NULL_NO_GO`.

A failure permanently rejects this exact all-event-null architecture. It does not authorize null trimming, a different bin width, a different number of calibration episodes, altered thresholds, or another nearby calibration-pool variant on the observed result.

## Downstream rule

A development pass must undergo the same exact-row pairwise matched comparison against Sugar and catalogue HDBSCAN, followed by a no-retuning external/held-out test. Only a method that satisfies those gates may be adapted to the already-frozen two-stage exact-ID blind OrbitTrace discovery firewall.
