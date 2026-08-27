# Frozen blind catalogue deployment of the fixed-4° detector

## Scientific question

Can the already frozen fixed-4° coverage-normalized Mondrian anchored four-clique detector identify a recurrent sparse structure corresponding to OrbitTrace when deployed without access to the OrbitTrace coordinates, activity interval, canonical members, HDBSCAN assignments, or targeted-recovery result?

This is a new post-freeze application authorized by the user. It does not alter the detector or retroactively change the historical chronology. A positive result may be described as a blind independent detection or rediscovery by the final pipeline; it may not be described as the literal first historical identification.

## Immutable detector

- detector source SHA-256: `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`;
- baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- fixed solar-longitude scale: 4° per distance unit;
- fixed episode size: 128;
- fixed local activity support: ±10°;
- fixed Mondrian bin width: 10°;
- fixed calibration count: 128 background windows per supported year-bin.

No score equation, scale, calibration count, seed after-the-fact, event-quality rule, family-link radius, retention cap, or reveal criterion may change after the workflow begins.

## Search corpus

The exact official GMN monthly trajectory files are frozen as:

- every month from January 2022 through December 2025;
- January through July 2026.

Only rows with finite valid solar longitude, geocentric Sun-centered ecliptic radiant geometry, and geocentric speed in 5–75 km/s are retained. The search pool is the GMN residual population whose shower label maps to `SPORADIC`. Duplicate trajectory identifiers are removed in monthly chronological order.

The blind stage does not retrieve or inspect any OrbitTrace artifact. All source-file hashes and row counts are preserved.

## Mondrian calibration

For each year and every supported 10° solar-longitude bin, the unchanged frozen `MondrianWindowFactory` generates exactly 128 calibration windows using the independent seed namespace:

`orbittrace-blind-calibration | corpus | year | bin | index`.

The fixed-4° score is computed by the immutable detector. The strict catalogue threshold for that year-bin is the largest of the 128 calibration scores, equivalent to the smallest attainable conformal p-value `1/129 = 0.0077519` under the original calibration size.

## Catalogue-wide anchored quartet scan

For every residual event used as an anchor:

1. candidate neighbors are drawn from the full ±10°-supported local catalogue region;
2. a 64-neighbor Euclidean shortlist is formed in a fixed embedding of solar longitude, radiant direction, and speed;
3. the exact frozen 4° distance is applied inside the shortlist;
4. the anchor plus its exact three closest shortlisted neighbors define the anchored quartet;
5. the quartet score is the negative exact maximum pairwise frozen distance;
6. a quartet is retained only if it exceeds the year-bin calibration maximum.

Every retained quartet is recomputed with a 128-neighbor shortlist. Any mismatch is replaced by the 128-neighbor result and recorded. This audit expansion cannot introduce target information or alter the threshold.

Within each year-bin, duplicate quartets are consolidated. A quartet must be selected by at least two anchors. At most the top 512 unique quartets per year-bin are retained, ordered before data access by anchor multiplicity, score, and trajectory identifiers.

## Within-year components and cross-year families

Retained quartets form an undirected event graph. A within-year component must contain at least four events and at least two retained quartets. Component centroids use circular solar-longitude and radiant-longitude means plus median latitude and speed.

Components from different years are linked when their centroid distance under the same fixed 4° geometry is at most `1.5`. Connected cross-year families require at least two years and are ranked lexicographically by:

1. number of distinct years;
2. number of distinct events;
3. number of retained quartets;
4. number of supporting anchors;
5. best quartet score.

The scan artifact freezes every ranked family and its event identifiers before reveal.

## Separately frozen reveal criteria

Only after the blind artifact and its SHA-256 are frozen may a separate workflow retrieve the canonical OrbitTrace member table.

- `FULL_BLIND_ORBITTRACE_REDISCOVERY`: one family ranks within the top 25, spans at least four years, contains at least 16 canonical OrbitTrace members in total, and has at least four canonical members in each of at least three individual years.
- `PARTIAL_BLIND_ORBITTRACE_RECOVERY`: no family passes the full rule, but one family ranks within the top 100, spans at least three years, contains at least 12 canonical members in total, and has at least four canonical members in each of at least two years.
- `NO_BLIND_ORBITTRACE_RECOVERY`: neither rule passes.

The reveal must report exact overlap, family size, rank, year distribution, precision, and a fixed-set enrichment calculation. No family merging, reranking, threshold change, or alternate matching rule is allowed after reveal.

## Claim boundary

A full result would support presenting the final scientific pipeline as:

`frozen novel detector blind rediscovery → independent HDBSCAN corroboration → observational validation`.

It would not erase the exploratory history, establish formal IAU shower status, or resolve the remaining distinct-stream versus branch interpretation.
