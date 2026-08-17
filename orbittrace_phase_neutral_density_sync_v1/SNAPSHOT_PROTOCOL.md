# Phase-neutral density-sync v1 — GMN snapshot protocol

## Purpose

The historical density-synchronous recurrent-EOM binding run did not preserve every accessible GMN event coordinate required to build a new hierarchy. The live GMN catalogue has since changed, so this successor must not claim to be evaluated on the historical 738,682-event corpus.

This protocol freezes one new, method-independent GMN 2022+2023 development snapshot before any phase-neutral method outcome is computed.

## Data boundary

Use exactly the same frozen source/parser stack inherited from the density-synchronous recurrent-EOM binding lineage:

- target-excluded GMN years 2022 and 2023 only;
- inclusive protected solar-longitude interval `[20°,55°]` removed by the inherited parser before rows are exported;
- inherited event normalization only (`id`, `year`, solar longitude, Sun-centred ecliptic radiant longitude/latitude, geocentric speed);
- no OrbitTrace target information;
- no SonotaCo, ASFN, EFN, AMOS, MAARSY or DMS scientific data.

The snapshot-preparation code is method-independent: it does not fit HDBSCAN, construct candidates, compute a ranking, evaluate a method, or inspect any performance metric.

## Two-artifact separation

The single preparation run writes two physically separate artifact roots:

1. **label-free rows** — ordered accessible event rows for 2022 and 2023 plus a manifest containing counts, source keys and file hashes; no shower labels;
2. **sealed truth** — the inherited hidden truth mapping plus a minimal manifest; no method output.

The later scientific method workflow must download only the label-free artifact while building and persisting both the GEO6 density-sync champion and GEO4 phase-neutral successor. The sealed-truth artifact may be downloaded only after the complete pretruth payload exists.

## Ordering

Event order is preserved exactly as returned by the inherited parser. No sorting, subsampling, deduplication, filtering beyond the inherited protected-window parser, feature transformation, or label-dependent operation is allowed.

## Snapshot status

This snapshot is a **new exposed GMN development snapshot**, not the historical #1263 corpus and not pristine external validation. Any scientific comparison on it must be reported as a paired within-snapshot comparison.

## No method choice

This preparation does not select GEO4 or any other successor. Its only purpose is to make the current development corpus immutable and auditable before method evaluation.