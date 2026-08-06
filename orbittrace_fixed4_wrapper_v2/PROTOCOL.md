# Fixed4 catalogue-wrapper development v2

## Purpose

Diagnose and improve only the generic catalogue-family wrapper around the already frozen fixed-4° coverage-normalized Mondrian anchored four-clique detector.

The detector, pairwise distance, 4° solar-longitude scale, quartet definition, 128-window Mondrian calibration, and event-quality rules are immutable. This stage may select a generic family-ranking rule, but it cannot tune the detector or inspect OrbitTrace.

## Target blindness

The inherited solar-longitude interval 20°–55° is removed from every year before shower identity is made available to wrapper selection or evaluation. This exclusion contains the full OrbitTrace activity interval and is fixed before this run.

The source may not contain an OrbitTrace identifier, member table, coordinate, radiant, speed, prior family ID, prior blind rank, recovery metric, or artifact identifier.

Outside the excluded interval, native GMN labels have two predeclared roles:

1. rows labelled `SPORADIC` form the background population used by the unchanged Mondrian calibration factory;
2. non-sporadic labels remain hidden until every component, family, score, and ranking is serialized and SHA-256 frozen.

No label enters quartet selection, component construction, cross-year linkage, or any candidate ranking score.

## Development corpus

- official GMN monthly trajectory files;
- complete years 2022–2025;
- finite solar longitude, Sun-centered geocentric radiant geometry, and geocentric speed;
- solar longitude outside 20°–55°;
- duplicate trajectory identifiers removed in chronological order.

All valid events, including labelled showers and sporadics, enter the geometric scan. Calibration uses only the predeclared sporadic subset.

## Fixed geometric wrapper

For every supported year and 10° Mondrian bin:

- generate exactly 128 background calibration windows with an independent fixed seed namespace;
- retain anchored quartets only when their frozen fixed4 score exceeds that bin's calibration maximum;
- require a quartet to be selected by at least two anchors;
- retain at most 512 quartets per year-bin;
- construct within-year event components from overlapping retained quartets;
- require at least four events and two retained quartets;
- link components from different years only when their frozen centroid distance is at most 1.5;
- require at least two represented years.

These rules are not candidates for selection.

## Candidate ranking rules

Exactly five generic rankings are evaluated:

1. `persistence`: years, events, quartets, anchors, best score;
2. `mean_year_strength`: mean support-normalized component strength across years;
3. `sqrt_support_strength`: total year strength divided by square-root support;
4. `min_year_strength`: weakest-year strength multiplied by square-root support;
5. `size_penalized_strength`: square-root support strength divided by log family size.

Each retained quartet receives a within-bin rank strength of `-log10((rank - 0.5) / count)`. Component and family strengths are deterministic functions of these pre-label ranks.

## Frozen family payload

Before any shower label is used for ranking evaluation, the workflow must serialize and hash:

- every family and event identifier;
- every ranking score;
- all five full rank lists;
- source and configuration metadata.

The resulting `wrapper_blind_families.json.gz` and SHA-256 are preserved in the artifact.

## Label benchmark

After the family payload is frozen:

- a shower is eligible when it has at least 12 events total and at least four events in each of at least two years;
- eligible shower codes are split deterministically by SHA-256 into development and validation panels;
- a family-shower match requires at least four exact labelled events and precision at least 0.50;
- for evaluation only, the best family for each shower is the one with maximum F1, then precision, overlap, and stable ID.

For each ranking and panel, report qualified recovery at ranks 100 and 500, mean reciprocal rank, median rank, macro F1, and mean dominant-label precision among the top 100 families.

## Selection and authorization

The ranking winner is selected using the development panel only, lexicographically by:

1. recovered showers at rank 100;
2. recovered showers at rank 500;
3. mean reciprocal rank;
4. top-100 dominant-label precision.

A v2 transfer is authorized only if:

- the winner is not the original persistence ranking;
- development recovery at rank 100 improves by at least one shower;
- validation recovery at ranks 100 and 500 does not decrease;
- validation mean reciprocal rank strictly improves;
- validation top-100 dominant-label precision decreases by no more than 0.10.

Pass verdict: `PASS_SUPPORT_NORMALIZED_WRAPPER_DEVELOPMENT`.

Failure verdict: `FAIL_SUPPORT_NORMALIZED_WRAPPER_DEVELOPMENT`.

A pass authorizes one separately frozen, one-shot OrbitTrace-blind catalogue transfer. It does not authorize threshold changes, another development panel, target-specific reranking, or rewriting any earlier result.
