# Recurrent-EOM residual TopoModal GMN diagnostic v1 — frozen protocol

## Status and scientific role

**FROZEN BEFORE THE FIRST RESULT FOR THIS DIAGNOSTIC.**

This is a target-excluded GMN 2022/2023 development diagnostic. It is not a catalogue promotion, ranking experiment, protected-region test, or external validation.

The sole question is whether the candidate-generation mechanism that passed as `PhysCore-Residual TopoModal v1` on exposed SonotaCo transfers structurally to the current GMN Recurrent-EOM setting when PhysCore itself is forbidden by its earlier residual-authorization failure.

Specifically: after freezing the exact Recurrent-EOM candidates on each already-frozen sparse GMN panel, remove the union of all Recurrent-EOM candidate member events and run the already-frozen TopoModal hierarchy on only that residual event set. After the residual candidate catalogue is sealed, open only the existing target-excluded GMN development shower labels and ask whether residual TopoModal creates qualifying candidate structure for showers that are true Recurrent-EOM `CANDIDATE_GENERATION_FAILURE`s.

No union ranking is constructed. No Recurrent-EOM ranking changes. Passing this diagnostic does not replace Recurrent-EOM as champion; it only establishes that the residual candidate-generation layer transfers to GMN and therefore leaves a separate selection/surfacing problem scientifically open.

## 1. Immutable parent and sparse panels

Use exact Recurrent-EOM HDBSCAN v1 and the exact frozen TopoModal hierarchy-scale machinery already used by the target-excluded GMN TopoModal scale experiments.

Years: `2022, 2023` only.

Protected solar-longitude exclusion: `[20°,55°]` inclusive, unchanged.

Panel selection is exactly the existing `ORBITTRACE_SCALE_STRESS_V1` deterministic hash selection:

- denominators `128` and `1024`;
- buckets `0,1,2,3`;
- event hash salt `ORBITTRACE_SCALE_STRESS_V1|`;
- same target-excluded GMN event universe and source hashes as the frozen hierarchy-scale experiment.

The 8 panel event universes must reproduce the frozen hierarchy-scale artifact byte-for-byte at the event-universe identity/count level before this diagnostic may proceed.

No SonotaCo, protected target events/information, AMOS, MAARSY, DMS, ASFN/EFN external event-level data, or pristine external endpoint may be accessed.

## 2. Frozen residual candidate construction

For each of the 8 sparse panels independently:

1. Generate the exact Recurrent-EOM candidate family set using its frozen 6D geometry, HDBSCAN parameters, recurrent-stability selection, and memberships.
2. Define `A` as the union of member event IDs across **all** Recurrent-EOM candidates in that panel. No rank cutoff is used.
3. Define residual event set `R = U \ A`, where `U` is the immutable panel event universe.
4. Run the exact frozen TopoModal hierarchy candidate generator on `R` only:
   - physical embedding and scales unchanged;
   - radius `1.0`;
   - manual radius-count density;
   - exact ToMATo hierarchy;
   - minimum candidate support `4`;
   - all unique eligible hierarchy node memberships retained;
   - no truth, shower identity, comparator labels, rank budget, or post-result information enters candidate generation.
5. Store the Recurrent-EOM candidate memberships, accepted-event set identity, residual-event set identity, and all residual TopoModal candidate memberships in a pretruth artifact.

This diagnostic does **not** concatenate, interleave, rerank, quota, blend, or otherwise select between the two candidate sources.

### Structural activation gate

Before any shower labels are opened:

- every one of the 8 panels must have at least one Recurrent-EOM candidate;
- every one of the 8 panels must leave at least 4 residual events;
- every one of the 8 panels must produce at least one residual TopoModal candidate of support >=4;
- the Recurrent-EOM accepted set and residual set must be disjoint and exactly partition the panel universe;
- all firewall and source-identity checks must pass.

If any structural activation gate fails, truth remains unopened and the diagnostic verdict is `FAIL_PRETRUTH_RESIDUAL_CONSTRUCTION`.

## 3. Frozen truth-side taxonomy

Truth is opened only after the full 8-panel residual catalogue is written and SHA-256 sealed.

For each `(denominator, bucket, year)` panel-year, eligible truth showers are exactly labels with at least four truth members in that annual panel and label != `SPORADIC`.

For each eligible shower, compute against **all** Recurrent-EOM candidates projected to that year:

- `best_all_f1`: maximum F1;
- `best_all_recall`: maximum recall, with ties broken by higher precision, then stable candidate family hash;
- `best_all_precision_at_recall`: precision of that maximum-recall candidate.

Use the already-frozen residual taxonomy thresholds from `Recurrent-EOM residual-error analysis v1`:

- `RECOVERABLE_IN_RECURRENT_UNIVERSE` if `best_all_f1 > 0.5`;
- `MEMBERSHIP_CONTAMINATION` if not recoverable, but `best_all_recall > 0.5` and `best_all_precision_at_recall <= 0.5`;
- `CANDIDATE_GENERATION_FAILURE` otherwise.

For every `CANDIDATE_GENERATION_FAILURE`, compute the maximum F1 over **all residual TopoModal candidates** projected to that year. A complementary recovery is strict `best_residual_topomodal_f1 > 0.5`, matching the existing recovery convention and the frozen SonotaCo complementarity diagnostic.

No one-to-one assignment or catalogue budget is used because this diagnostic asks only candidate existence, not catalogue performance.

## 4. Pre-frozen transfer gates

Aggregate the four hash buckets separately for each scale and year. A panel-level shower occurrence may contribute within its hash bucket; counts are sparse-panel diagnostics, not unique global shower counts.

Four primary gates are frozen before truth access:

1. denominator 128 / year 2022: at least one Recurrent-EOM `CANDIDATE_GENERATION_FAILURE` has a residual TopoModal candidate with F1 > 0.5;
2. denominator 128 / year 2023: same;
3. denominator 1024 / year 2022: same;
4. denominator 1024 / year 2023: same.

Overall verdict:

- `PASS_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1` iff all four transfer gates pass and the pretruth structural activation gate passed;
- otherwise `FAIL_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1`.

These are existence/transfer gates only. No minimum fraction, rank, precision, or candidate quota may be introduced after the result.

## 5. Required reporting

For every panel-year report:

- eligible shower count;
- Recurrent-EOM recoverable-universe count;
- membership-contamination count;
- candidate-generation-failure count;
- number and fraction of candidate-generation failures recovered by residual TopoModal;
- median/max best residual TopoModal F1 among candidate-generation failures;
- Recurrent-EOM candidate count;
- accepted-event count;
- residual-event count;
- residual TopoModal candidate count.

For every `(scale, year)` aggregate report total candidate-generation failures and total complementary recoveries.

Also report source hashes, event-universe hashes, pretruth SHA-256, and explicit access-audit booleans.

## 6. Closure and interpretation

A failure closes this exact residual-Recurrent-EOM → frozen-TopoModal candidate-existence transfer diagnostic. Do not tune TopoModal, residual definition, support threshold, scale, hash panels, or F1 threshold to rescue it.

A pass establishes only that a structurally distinct residual candidate generator finds GMN shower structure absent from the Recurrent-EOM candidate universe. It does **not** authorize arbitrary interleaving, supervised ranking, quotas, or a champion replacement. Any later surfacing/selection mechanism must be separately pre-frozen and must respect all prior closed ranking/union mechanisms.

## Firewall

- `[20°,55°]` protected interval remains excluded.
- `target_information_access = false`.
- `target_region_events_accessed = false`.
- `sonotaco_2013_2014_access = false`.
- `amos_scientific_access = false`.
- `maarsy_scientific_access = false`.
- `dms_scientific_access = false`.
- No post-result parameter search.
