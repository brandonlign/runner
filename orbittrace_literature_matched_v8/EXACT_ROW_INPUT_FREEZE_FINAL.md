# Final exact-row comparator input freeze — before pairwise execution

This file freezes the four assignment inputs eligible for the final exact-event-row pairwise benchmark. It does not change any method or decision criterion.

## HDBSCAN 2023

Use the comparison-only blind-safe rerun from workflow `31226945294`, artifact `orbittrace-hdbscan-2023-blind-safe-benchmark`:

- full-catalogue assignment SHA-256: `35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761`
- assignment rows: `26460`
- independent assignment verification: workflow `31227148081`
- verification verdict: `PASS_HDBSCAN_2023_BLIND_ASSIGNMENT_VERIFY`
- forbidden 20°–55° assignment rows: `0`
- verifier label access: `false`

The source-method rerun retained `hdbscan==0.8.44`, unstandardized GEO six-vector, `min_cluster_size=100`, package-default `min_samples`, Euclidean distance, and `eom` cluster selection. The only two false legacy runner gates were the obsolete pre-blinding `exact_row_count` and `all_rows_parsed` invariants; all method-relevant execution gates were true.

The original unblinded HDBSCAN-2023 assignment artifact remains preserved but is ineligible for the final blind-safe pairwise benchmark.

## HDBSCAN 2025

Use the already-frozen blind-safe catalogue artifact from workflow `31071589912`:

- full-catalogue assignment SHA-256: `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`
- assignment rows: `19658`

Its event adapter removes 20°–55° before the shower token is read.

## Full Sugar uncertainty pipeline 2023

Use workflow `31076789635`:

- retained-master assignment SHA-256: `2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389`
- assignment rows: `30414`

The exact 2023 parser removes 20°–55° before label access.

## Full Sugar uncertainty pipeline 2025

Use workflow `31075178517`:

- retained-master assignment SHA-256: `77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e`
- assignment rows: `23200`

The exact 2025 adapter removes 20°–55° before the shower token is read.

## Frozen execution rule

The final exact-row runner must use these exact assignment hashes and row counts. For each comparator, v8 receives exactly the same assignment-row universe as that comparator. Both v8 pairwise panel rankings are frozen before the common shower-label parser is called.

The preregistered material-advantage threshold remains `delta >= 0.10`; the 4–9 gate still requires both years, and the broader 4–24 gate still requires both 4–9 and 10–24 in both years. No result may modify those rules, v8, HDBSCAN, Sugar, the size bins, or the label mapping.

No OrbitTrace target coordinate, member, identity, excluded-interval content, or final target result may be accessed.
