# Historical CAMS Database 2.0 development-label audit

Status: frozen before opening `CAMS_California_v2.d15`.

## Purpose

Determine whether the native two-character `Sh` field in historical CAMS Database 2.0 provides enough labeled established-shower members and same-survey sporadic background to support a development screen of the unchanged PR #38 coverage-normalized 10-degree Mondrian four-clique method.

This is an aggregate-only interface audit. It computes no detector score, calibration p-value, injection, AUROC, fold result, or GhostStream endpoint.

## Frozen source and partition

- archive URL: `https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_California_v2.zip`
- archive bytes: `18411331`
- archive SHA-256: `4e0e33fec66d3012a2668a7acfd62a0694df191fabf44f3a792b3781785ab313`
- exact member: `CAMS_California_v2.d15`
- uncompressed bytes: `128734222`
- exact parser: the flag/value interface in `reading.f`, SHA-256 `437d9d8f7d68b824751954b51e2caaec69e379912bce3b924acf2292e89acb1c`

The independent published first-year CAMS analysis states that the California sample from 2010-10-21 through 2011-12-31 contains exactly **40,744** meteors. Freeze the first 40,744 complete records in the archive as the development partition.

The parser must stop immediately after the 40,744th record terminator. It must not parse, count, classify, or emit any later California record. The entire BeNeLux archive is also reserved and must not be requested. All later California records plus all BeNeLux records are the untouched historical-CAMS confirmation reservoir.

The development partition must independently verify that every parsed `Yr` is exactly 2010 or 2011 and that both years are represented. Any violation kills this exact partition.

## Frozen record parser

Each record is a sequence of four-character field flags with two-character presence and error indicators, followed by the value line required by the official Fortran reader, and terminated by exact flag `   &`.

For this audit only:

- parse `Yr :` and `LS :` as finite numeric values;
- hold the `Sh :` value line as opaque two-byte data until the record terminator is reached and its solar longitude has passed the blind boundary;
- skip every other value according to the official reader without decoding scientific content;
- require one and only one `Yr`, `LS`, and `Sh` field header per complete development record; `Sh` may be marked absent;
- do not parse or emit `RA`, `DEC`, `Vg`, orbit, uncertainty, identifier, or any other scientific value.

## GhostStream blindness

For each development record:

1. require finite solar longitude in `[0,360)`;
2. if solar longitude is **20 degrees through 55 degrees inclusive**, discard the record before decoding, stripping, classifying, counting, or storing its opaque `Sh` bytes;
3. only after the record passes that boundary may the `Sh` value be decoded and classified.

No GhostStream radiant, speed, orbit, member, event identifier, score, or detailed solar-longitude location is used.

## Frozen native-label rule

The reader defines `Sh` as `CHARACTER*2` and the shower number of the meteor.

After the blind boundary only:

- background: absent `Sh`, or two spaces;
- mapped native label: strip ASCII spaces and require an exact one- or two-character uppercase alphanumeric token matching `^[A-Z0-9]{1,2}$`;
- unsupported: every other nonblank representation.

Tokens are opaque survey-native shower-number labels in this audit. No alias table, IAU-code inference, decimal/base conversion, shower name, fuzzy match, geometry-derived assignment, or token-specific exception is allowed. Identities and token frequency tables must not be emitted.

## Frozen aggregate outputs

The authoritative artifact may contain only:

- source and parser provenance;
- total parsed development records and aggregate counts by year;
- invalid-phase and blind-interval exclusion counts;
- post-boundary background, mapped-label, and unsupported counts/fractions;
- number of distinct mapped tokens, without identities;
- numbers of tokens meeting total support thresholds 4, 8, 12, and 20;
- numbers of tokens meeting 20-degree circular-window support thresholds 4, 6, 8, and 12;
- number of non-blind 10-degree phase bins with at least 128, 256, and 512 background events;
- gates and verdict.

It must not contain individual rows, identifiers, label identities, geometry values, detailed phase-bin counts, or any record after development record 40,744.

## Frozen continuation gates

Every gate must pass:

1. exact archive hash, member name, and uncompressed size;
2. exactly 40,744 complete records parsed, with the parser stopping at that boundary;
3. every parsed year is 2010 or 2011 and both years are represented;
4. no BeNeLux request and no later California record parsed;
5. no blind-interval record reaches `Sh` decoding or classification;
6. unsupported syntax is at most 1% of post-boundary rows;
7. at least 90% of nonblank label-like values map through the single frozen token rule;
8. at least 25,000 post-boundary background events;
9. at least 30 distinct mapped native labels;
10. at least 25 labels with total support >=8 and at least 20 with total support >=12;
11. at least 20 labels with support >=6 inside some circular 20-degree window and at least 15 with support >=8;
12. at least 20 non-blind 10-degree phase bins contain >=256 background events;
13. no scientific geometry, score, SonotaCo 2024 value, CAMSv3 2016 value, or reserved historical-CAMS label is read.

A pass authorizes only a separately frozen historical-CAMS 2010-2011 scientific development screen. Before that screen reads `RA`, `DEC`, or `Vg`, it must freeze the exact token-to-IAU identity snapshot, complex-disjoint grouping, quality filters, phase bins, empirical windows, calibration counts, seeds, folds, comparators, thresholds, and scientific gates. The later California and BeNeLux confirmation reservoir remains untouched unless the complete development screen passes every gate.

A failure kills this exact historical-CAMS native-label interface. No token interpretation, partition boundary, support threshold, or syntax rule may be changed after execution.
