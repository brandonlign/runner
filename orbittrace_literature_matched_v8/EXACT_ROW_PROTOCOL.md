# OrbitTrace v8 exact-event-row pairwise benchmark — preregistered before execution

## Why this secondary benchmark exists

The first preregistered SonotaCo 2023+2025 matched-survey run (`31226030807`) passed all integrity gates but retained each published comparator's own quality filtering. Its negative/positive outcomes remain frozen and are not replaced.

This secondary benchmark removes that remaining input-row asymmetry. It is pairwise rather than forcing one synthetic common filter:

1. **v8 vs catalogue HDBSCAN:** v8 receives exactly the event IDs present in the frozen HDBSCAN all-shower/full-catalogue assignment artifact for each year.
2. **v8 vs full Sugar uncertainty:** v8 receives exactly the event IDs present in the frozen Sugar retained-master assignment artifact for each year.

The competitor outputs are not rerun or retuned. Their exact frozen assignment files define both the row universe and their cluster assignments.

## Immutable competitor assignment inputs

### HDBSCAN

- 2023 workflow `31076062060`, artifact `8957554613`, artifact digest `sha256:cc00d20f0f5e70bd30338755f77567960ea8e600417bd080a7474119ebbdc804`
  - `full_catalogue_assignments.jsonl.gz` SHA-256 `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60`
- 2025 workflow `31071589912`, artifact `8955917326`, artifact digest `sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`
  - `full_catalogue_assignments.jsonl.gz` SHA-256 `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`

The `cluster`/`hdbscan_cluster` field is the frozen HDBSCAN output; negative cluster IDs are noise.

### Sugar uncertainty-aware retained masters

- 2023 workflow `31076789635`, artifact `8957940764`, artifact digest `sha256:ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf`
  - `sugar_uncertainty_assignments.json.gz` SHA-256 `2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389`
- 2025 workflow `31075178517`, artifact `8957263372`, artifact digest `sha256:9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9`
  - `sugar_uncertainty_assignments.json.gz` SHA-256 `77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e`

The `retained_labels` field is the frozen full 1,000-clone retained-master output; negative labels are noise. `strong_labels` is not substituted after seeing results.

## Exact-row geometry construction

For each pairwise panel, the competitor assignment event IDs are the complete allowed scan universe. Geometry is read from the exact immutable SonotaCo archive row indexed by the `SNM<YEAR>:<row-index>` ID.

Before any shower token or mapped shower label is read, the scanner extracts only:

- solar longitude;
- geocentric radiant RA/Dec, converted to ecliptic longitude/latitude using the existing frozen base routine;
- geocentric speed.

Every competitor event ID must resolve to one structurally valid geometry row. Any missing/duplicate/unparseable requested event ID fails the panel rather than silently changing the row universe.

The 20°–55° solar-longitude interval must be absent from every requested competitor row set. If any competitor assignment contains a row in that interval, the pairwise benchmark fails before scanning.

## Common labels/evaluation set

After all v8 proposals, recurrent families, pooled centroids, scores, and rankings for a pairwise panel are frozen, the already-audited SonotaCo label parser is invoked.

For evaluation only:

- IDs mapped by the common mapping audit to a supported shower receive that mapped `complex_key`;
- every other exact-row ID is treated as `SPORADIC` for both v8 and the competitor, including unsupported/unmatched native shower tokens;
- no method-specific truth field embedded in a competitor assignment file is used to give that method a different evaluation universe.

Thus v8 and the comparator use identical event rows, identical labels, identical shower-size denominators, identical size bins, and identical post-hoc cluster/family matching metrics within each pairwise panel.

## Frozen v8 method

Identical to `PROTOCOL.md` and source commit `c9d6c44704013ba0c9430100e98a29a56b453304`. Only the allowed event-ID set differs between the HDBSCAN and Sugar panels. No scientific v8 constant changes.

## Common annual evaluation

For every mapped known shower with at least four members in the exact row set of that year:

- v8: choose the already-frozen recurrent family maximizing annual F1, tie-breaking by precision, overlap, stable family ID;
- competitor: choose the frozen non-noise cluster maximizing annual F1, tie-breaking by precision, overlap, cluster ID.

Report for each year and each size bin `4–9`, `10–24`, `25–49`, `50–99`, `100+`:

- number of reference showers;
- mean F1;
- macro precision and macro recall of the best match;
- showers with F1 > 0.5;
- showers with F1 > 0.8;
- `delta = v8 mean F1 - competitor mean F1`.

Also report the same metrics over all eligible showers so non-sparse behavior is visible.

## V8 recurrent endpoint

The v8-only same-family recurrence endpoint from `PROTOCOL.md` is also reported on each exact-row panel, but it is **not** used as though HDBSCAN or Sugar had an equivalent two-year recurrence stage.

## False-positive burden

Report:

- v8 recurrent family count and top-K dominant-label precision;
- competitor annual non-noise cluster count;
- competitor annual noise fraction;
- the fraction of returned v8 families/competitor clusters whose dominant mapped known-shower precision reaches 0.5, evaluated on the same rows.

These are labelled method-specific burdens; no artificial common catalogue ranking is invented for HDBSCAN or Sugar.

## Decision gates

The numeric gates in `DECISION_GATES.md` remain unchanged despite the already-observed matched-survey result:

- a size-bin advantage is material only for `delta >= 0.10`;
- v8 beats a comparator in the **4–9 sparse regime** only if that material advantage occurs in both 2023 and 2025 exact-row panels;
- v8 beats a comparator across the **broader sparse regime** only if both 4–9 and 10–24 satisfy the material gate in both years;
- all larger bins are mandatory in the report.

If the exact-row result conflicts with the earlier matched-survey result, both are preserved and the exact-row result receives greater weight for pairwise performance claims because its inputs and labels are genuinely identical.

## Claim boundaries

Even a pass against both pairwise comparators would support only the tested SonotaCo optical-catalogue scope. It would not establish superiority to the deferred CMOR radar wavelet method or to every meteor-stream method in the literature.

A failure against Sugar or HDBSCAN is preserved as a scientific negative result. No v8 modification is allowed in this track.

No OrbitTrace target coordinate, member, identity, target-region event, excluded-interval content, or final target-reveal result may be accessed.
