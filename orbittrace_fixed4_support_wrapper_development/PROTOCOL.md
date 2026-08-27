# Fixed4 support-normalized catalogue-wrapper development

## Purpose

Develop a generic catalogue-ranking layer that does not automatically place persistent eight-year families ahead of every shorter episodic family. The immutable fixed-4° coverage-normalized Mondrian anchored four-clique detector remains unchanged.

This stage cannot access or evaluate OrbitTrace. Solar longitude 20°–55° is removed before shower-label normalization, calibration-label selection, family formation, ranking evaluation, or endpoint calculation.

## Immutable detector core

The workflow must decode and verify:

- detector source SHA-256 `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`;
- baseline source SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- Mondrian scorer SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- exact catalogue-scanner source SHA-256 `48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5`.

The exact distance, fixed 4° solar-longitude scale, 128-window calibration, 64-neighbor shortlist, 128-neighbor audit, anchored three-neighbor quartet construction, maximum-pairwise-distance score, anchor multiplicity requirement, 512-quartet bin cap, component gates, and 1.5 family-link radius do not change.

Only these scanner functions may differ from the frozen calibrated scanner: `parse_catalogue`, `scan_year`, `component_records`, `build_families`, and `main`. All reusable detector and geometry helpers must remain AST-identical.

## Data and temporal split

- catalogue years: 2022–2025, all twelve official GMN monthly files per year;
- exclusion: closed solar-longitude interval 20°–55°, applied before labels;
- ranking-selection panel: 2022–2023 only;
- untouched temporal validation panel: 2024–2025 only.

All geometrically valid events outside the exclusion enter the target-free scan. Native shower labels remain hidden until every quartet, component, family, and ranking is complete. Only events labelled `SPORADIC` after the exclusion are eligible for Mondrian background calibration.

## Generic family-strength construction

Within every supported year-bin, retained quartets are ordered by the same fixed anchor multiplicity, score, and identifier ordering used by the calibrated wrapper. A retained quartet receives:

`bin_strength = -log10((rank - 0.5) / retained_count)`.

A component receives:

`component_strength = sum(bin_strength) / sqrt(quartet_count)`.

For each family and represented year, `year_strength` is the maximum component strength in that year.

## Frozen ranking candidates

1. `persistence`: original lexicographic year-count-first ranking;
2. `mean_year_strength`: mean year strength;
3. `sqrt_support_strength`: sum of year strengths divided by square root of represented years;
4. `min_year_strength`: minimum year strength multiplied by square root of represented years;
5. `size_penalized_strength`: square-root-support strength divided by `log2(2 + event_count)`.

Ties use year count, anchor count, smaller family size, and stable family identifier. No formula or tie rule may change after execution begins.

## Known-shower evaluation

Within each temporal panel, an eligible known shower must have at least eight labelled events total and at least four in each of the panel's two years. For evaluation only, the best matching family is selected by F1, then precision, overlap, and stable identifier. A match qualifies only with at least four exact labelled events and precision at least 0.5.

For each ranking, report:

- qualified-shower recall within the top 100 and top 500;
- mean reciprocal rank;
- median rank;
- macro F1;
- mean dominant-label precision of the top 100 families.

## Selection and pass rule

The selected ranking maximizes, lexicographically on 2022–2023 only:

1. recall at 100;
2. recall at 500;
3. mean reciprocal rank;
4. top-100 dominant-label precision.

The 2024–2025 panel cannot influence selection. Development passes only if all conditions hold:

- selected ranking is not `persistence`;
- 2022–2023 recall at 100 improves by at least one shower;
- 2024–2025 recall at 100 does not decline;
- 2024–2025 recall at 500 does not decline;
- 2024–2025 mean reciprocal rank strictly improves;
- 2024–2025 top-100 dominant-label precision declines by no more than 0.10.

A pass authorizes one separately frozen application of the selected ranking to a target-free OrbitTrace catalogue scan. A failure freezes this formulation as unsuccessful. Neither outcome changes the historical HDBSCAN discovery chronology or any earlier fixed4 result.