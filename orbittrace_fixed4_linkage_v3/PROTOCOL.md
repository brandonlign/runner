# Fixed4 cross-year family-linkage development v3

## Scientific question

Can the wrapper sensitivity found in the blind OrbitTrace deployments be reduced by changing only the generic cross-year family construction around the immutable fixed-4° coverage-normalized Mondrian anchored four-clique detector?

The preceding target-blinded ranking study in PR #182 showed that support-normalized reranking did not improve held-out recovery. This stage therefore keeps the original persistence ranking fixed and evaluates the next structural layer: how independently detected within-year components are joined across years.

## Immutable stages

The following are unchanged from the calibrated blind catalogue wrapper:

- exact detector source and fixed 4° solar-longitude scale;
- exact pairwise distance and anchored four-clique definition;
- 128-event episodes and ±10° local support;
- 10° Mondrian bins and 128 calibration windows per supported year-bin;
- strict threshold at the maximum calibration score;
- 64-neighbor shortlist with 128-neighbor audit;
- at least two selecting anchors per retained quartet;
- at most 512 retained quartets per year-bin;
- within-year event graph construction;
- at least four events and two quartets per within-year component;
- fixed cross-year centroid radius 1.5;
- minimum two represented years;
- the original persistence ranking: years, events, quartets, anchors, best score.

No detector score, scale, threshold, calibration seed, event-quality rule, component rule, radius, or ranking may change.

## Target blindness

Complete GMN years 2022–2025 are used. Solar longitude 20°–55° is removed before shower labels are normalized or made available to evaluation. This exclusion contains the full OrbitTrace activity interval.

The source may not contain any OrbitTrace member, coordinate, activity window, family identifier, blind rank, prior recovery metric, or OrbitTrace artifact identifier.

All geometrically valid events outside the excluded interval enter component detection. Rows labelled `SPORADIC` have only the predeclared role of supplying background calibration windows. No label enters quartet selection, within-year component construction, cross-year linkage, or persistence ranking.

## Frozen linkage candidates

Exactly three cross-year constructions are compared.

### 1. `single_link`

The existing baseline. Connect every pair of components from different years whose exact frozen centroid distance is at most 1.5. Families are connected components of that graph. Multiple components from the same year may enter through chaining.

### 2. `mutual_nearest`

For every pair of years, connect two components only when each is the other's exact nearest component and their distance is at most 1.5. Connected graph components are then reduced to at most one component per year using only the pre-label component-strength ordering: component strength, event count, quartet count, stable identifier.

### 3. `seed_complete`

Use every within-year component as a seed. Other years are considered in order of their nearest distance to the seed. For each year, choose the component minimizing the maximum exact distance to all already selected components and add it only when that maximum is at most 1.5. This produces at most one component per year and enforces complete-link coherence. Duplicate component sets are consolidated.

No linkage candidate may be added after execution begins.

## Mandatory pre-label freeze

Before known-shower labels are used for comparison, the workflow serializes and SHA-256 freezes:

- every family and event identifier under all three constructions;
- every component identifier in each family;
- every complete persistence ranking;
- source and configuration provenance.

The frozen payload is written as `linkage_blind_families.json.gz` with a separately recorded digest.

## Known-shower benchmark

After the payload is frozen:

- an eligible shower has at least 12 events total and at least four events in each of at least two years;
- shower codes are split deterministically by SHA-256 into development and validation panels, exactly as in PR #182;
- a qualified family-shower match requires at least four exact labelled events and precision at least 0.50;
- the best family for a shower is selected only for evaluation by maximum F1, then precision, overlap, and stable family identifier.

For each linkage and panel, report qualified recovery at ranks 100 and 500, mean reciprocal rank, median rank, macro F1, and mean dominant-label precision among the top 100 families.

## Selection and authorization

The development winner is chosen lexicographically by:

1. recovered showers at rank 100;
2. recovered showers at rank 500;
3. mean reciprocal rank;
4. top-100 dominant-label precision.

A transfer is authorized only if:

- the winner is not `single_link`;
- development recovery at rank 100 improves by at least one shower;
- validation recovery at ranks 100 and 500 does not decrease;
- validation mean reciprocal rank strictly improves;
- validation top-100 dominant-label precision decreases by no more than 0.10.

Pass verdict: `PASS_CROSS_YEAR_LINKAGE_DEVELOPMENT`.

Failure verdict: `FAIL_CROSS_YEAR_LINKAGE_DEVELOPMENT`.

A pass authorizes one separately frozen, one-shot OrbitTrace-blind transfer using the selected linkage. A failure authorizes no OrbitTrace transfer and closes this predefined linkage-development family. Neither outcome changes any earlier blind-deployment record.
