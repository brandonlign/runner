# OrbitTrace label-free multiscale-consensus multiplicity v16 — target-excluded development protocol

## Why v16 exists

The frozen v15 multiscale-consensus ranker passed its preregistered low-cardinality development gates, and canonical GMN projection later reproduced its frozen GMN result exactly. Source extraction then exposed a portability limitation in the inherited v5 **proposal** scanner: its empirical fixed4 threshold is calibrated from rows selected by the known `SPORADIC` label before recurrent families are formed. That is not an acceptable common family-generation interface for unlabeled external surveys such as the final MAARSY route.

This limitation does **not** invalidate the v15 multiplicity score or its multiscale consensus result. It means v15 cannot honestly be called a survey-portable label-free end-to-end method merely by renaming survey columns.

v16 is therefore a separately named successor. It changes exactly one upstream architectural element: replace v5's label-dependent calibrated proposal gate with the already-developed and already-passed **label-free sparse-support v6** recurrent-family construction. The downstream multiplicity geometry and v15 multiscale consensus are unchanged.

No SonotaCo, MAARSY, DMS, OrbitTrace target, or target-region scientific result may be used to select or modify v16.

## Frozen v16 architecture

### Canonical event input

Every survey-facing transport must emit only the canonical pretruth event record:

`id, year, sol, sun_lon, ecl_lat, vg, iau=0, complex_key=HIDDEN`.

The closed solar-longitude interval 20°–55° must be removed before a retained row enters v16. Truth-bearing keys are forbidden.

### Recurrent-family construction

Use the exact label-free sparse-support v6 proposal architecture that passed workflow `31207688016`:

- 10° solar-longitude bins across 0°–360°;
- anchors from the active 10° bin;
- local pool within ±15° of bin center;
- first Euclidean shortlist 64;
- audit shortlist 128;
- one anchored four-event quartet per anchor from the exact nearest three neighbors;
- no empirical score threshold and no calibration/null event set;
- deduplicate identical four-event sets;
- require anchor multiplicity ≥2;
- retain at most 512 quartets per bin, ordered exactly by anchor count, quartet score, then event IDs;
- exact frozen component construction;
- exact frozen cross-year family construction;
- family link radius 1.5;
- minimum component support: 4 events and 2 quartets;
- minimum family recurrence: both years of the supplied pair.

There is no survey-conditioned branch, no quality-dependent detector threshold, and no use of shower labels before all rankings are frozen.

### Multiplicity scoring

For each recurrent family and each local episode cap, preserve the exact v5/v13 multiplicity geometry:

- local window: exact frozen ±5° / 10° total window from the frozen catalogue runtime;
- `K = min(cap, N_local)`;
- fail closed only if `N_local < 4`;
- choose the K closest local events using the exact frozen wavelet distance and stable tie handling;
- exact frozen multi-anchor-v3 score;
- exact frozen Brown score;
- multiplicity `M = (v3 / Brown)^2`;
- per-family ordering by worst-year multiplicity descending, then geometric-mean multiplicity descending, then stable family ID.

Brown-equivalence difference must remain ≤1e-10.

### Multiscale consensus

Use the exact v15 rank-consensus rule. For nominal cap K:

- `K1 = K`;
- `K2 = floor(3K/4)`;
- `K3 = floor(K/2)`;
- floor at 4, though all preregistered caps are ≥16.

The required nominal/component sets are fixed:

- nominal 128 → `[128, 96, 64]`;
- nominal 96 → `[96, 72, 48]`;
- nominal 64 → `[64, 48, 32]`;
- nominal 32 → `[32, 24, 16]`.

For each family, compute the median of the three zero-based component ranks. Order by:

1. median rank;
2. full-cap rank;
3. three-quarter-cap rank;
4. half-cap rank;
5. stable family ID.

The final deployable v16 order is nominal 128. The lower nominal caps exist only as preregistered robustness stresses.

## Development panels

No panel may be selected after results. **Both** already-exposed, target-excluded GMN pairs must pass:

1. GMN 2020/2021;
2. GMN 2022/2023.

These are development/compatibility panels, not external validation. SonotaCo 2013/2014 remains scientifically exposed and is not used for v16 development. MAARSY remains unopened to v16 scientific execution.

## Strict pretruth boundary

For each GMN panel:

1. a geometry-only parser resolves only event ID, solar longitude, geocentric ecliptic longitude, geocentric ecliptic latitude, and geocentric speed;
2. the 20°–55° exclusion is applied before canonical rows are emitted;
3. no truth column is resolved for the pretruth run;
4. label-free families are built;
5. all eight multiplicity-cap rankings are frozen;
6. all four multiscale-consensus rankings are frozen;
7. direct cap-128 Brown and label-free persistence comparator orders are deterministically frozen from already-frozen pretruth quantities;
8. hashes of all evaluation orders are written to disk;
9. only then may the historical GMN label parser be invoked for evaluation.

The truth-opening phase may evaluate frozen orders only. It may not regenerate families, scores, or rankings.

## Integrity gates — each panel

All must pass:

1. no pretruth truth-column resolution;
2. zero label-dependent calibration events;
3. no fixed4 score threshold in family generation;
4. source labels unused by proposals;
5. at least 24 scannable 10° bins in each year;
6. at least 100 recurrent families;
7. at least 30 qualified known showers after truth opening;
8. all eight caps contain exactly the same family universe;
9. Brown equivalence ≤1e-10 for every cap;
10. the posttruth parser reproduces exactly the pretruth event-ID universe and counts for both years;
11. all comparator/candidate order hashes exist before truth access;
12. no SonotaCo, MAARSY, target-region, or OrbitTrace target information enters development.

## Label-free v6 base gates — each panel

The direct cap-128 multiplicity ranking on the label-free v6 family universe must retain the already-established v6 scientific relationship:

1. recovered@100 ≥ Brown recovered@100 + 1;
2. recovered@100 ≥ `ceil(0.90 × label-free-persistence recovered@100)`;
3. top-100 dominant precision ≥0.50.

These gates ensure v16 is not declared successful merely because its multiscale ranks are internally stable on a scientifically degraded family universe.

## Full-cardinality preservation — each panel

Relative to the direct cap-128 multiplicity ranking on the same label-free family universe:

1. v16 nominal-128 recovered@100 ≥ direct cap-128 recovered@100;
2. v16 nominal-128 MRR ≥0.95 × direct cap-128 MRR;
3. top-100 dominant precision loss ≤0.05 absolute;
4. qualified-known-shower count unchanged.

## Low-cardinality robustness — each panel

For **each** nominal cap 96, 64, and 32 relative to v16 nominal-128 on that same panel:

1. recovered@100 ≥ `ceil(0.90 × v16-128 recovered@100)`;
2. MRR ≥0.90 × v16-128 MRR;
3. top-100 dominant precision ≥0.50;
4. top-100 dominant precision loss ≤0.05 absolute;
5. qualified-known-shower count unchanged.

## Final development decision

- both GMN panels pass every integrity, base, full-cardinality, and low-cardinality gate:
  `PASS_LABEL_FREE_MULTISCALE_CONSENSUS_V16_TARGET_EXCLUDED_DEVELOPMENT`
- otherwise:
  `FAIL_LABEL_FREE_MULTISCALE_CONSENSUS_V16_TARGET_EXCLUDED_DEVELOPMENT`

A failure is preserved as a no-go for this exact combined architecture; the failing panel may not be used to relax these gates.

A pass freezes v16 as a candidate for later external work. It does **not** constitute external validation, literature superiority, OrbitTrace discovery, or permission to expose the target. SonotaCo may only be used later as explicitly non-pristine engineering/literature evidence. MAARSY 2022 remains the separately governed final external-generalization endpoint and requires its own dormant, preregistered v16 runner before scientific access.
