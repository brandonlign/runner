# Exact-row correction 1 — blind-safe HDBSCAN 2023 transfer

## Trigger

Exact-row workflow run `31226439736` stopped before any v8 scan after its blindness guard found that the frozen HDBSCAN-2023 assignment universe was not wholly outside the preregistered 20°–55° exclusion.

A source-only audit then decoded the exact successful comparator runners. It established:

- frozen HDBSCAN-2023 runner SHA-256 `2e770252f68f40c7ebab8f072aef18b88246091e40a98673db69d09f7bb1d41b` parses the raw SonotaCo 2023 CSV directly, has no blind-interval logic, and reads the `Shower` field in the same parse block as geometry;
- HDBSCAN-2025 obtains its event objects from the exact SonotaCo-2025 adapter SHA-256 `5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`, which removes 20°–55° immediately after solar longitude is parsed and before the `Shower` token is read;
- Sugar-2025 uses that same blind-safe 2025 event adapter, and Sugar-2023 uses the already-audited 2023 confirmation parser that removes the same interval before label access.

Therefore the original HDBSCAN-2023 transfer remains a valid reproduction of its frozen catalogue method, but it is **not eligible for the final blind-safe pairwise benchmark**.

## Only allowed correction

Rerun the exact frozen HDBSCAN-2023 transfer source with its two already-recorded parser-only repairs (43→46 effective field width and normalized `DictReader.fieldnames`) plus exactly one new pre-label blindness insertion:

Immediately after the existing line

`sol = parse_float(raw["sol(deg)"]) % 360.0`

insert

```python
if 20.0 <= sol <= 55.0:
    continue
```

inside the same `try` block and **before** RA, Dec, speed, uncertainty, orbit, convergence-angle, or `Shower` parsing.

No excluded row may contribute to a quality decision, HDBSCAN feature vector, cluster, or evaluation label.

## Everything else remains frozen

The rerun must preserve without search or modification:

- exact SonotaCo 2023 archive SHA-256 `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`;
- `hdbscan==0.8.44`;
- unstandardized published GEO six-vector;
- `min_cluster_size=100`;
- package-default `min_samples`;
- Euclidean metric;
- `eom` cluster selection;
- the already-recorded 2023 header and field-name parser repairs;
- every quality cut and label mapping already present in the frozen runner;
- the v8 source, all v8 parameters, benchmark bins, metrics, and decision gates.

The HDBSCAN result may improve or worsen. It will be preserved either way.

## Exact-row benchmark continuation rule

If and only if the blind-safe HDBSCAN-2023 rerun completes and its emitted assignment IDs are all outside 20°–55°, its `full_catalogue_assignments.jsonl.gz` replaces the ineligible original HDBSCAN-2023 assignment file **only for the exact-row pairwise benchmark**. HDBSCAN-2025 and Sugar-2023/2025 remain their existing frozen assignments.

The exact-row v8 comparison still uses the already-preregistered `delta >= 0.10` material-advantage rule and the same both-year gates. No decision threshold may change after the HDBSCAN rerun.

No OrbitTrace target coordinate, identity, member, excluded-interval content, or final target result may be accessed.
